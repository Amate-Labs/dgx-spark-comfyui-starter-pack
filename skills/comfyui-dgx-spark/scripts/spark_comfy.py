#!/usr/bin/env python3
"""Inspect and prepare a DGX Spark ComfyUI environment."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SKILL_ROOT = Path(__file__).resolve().parents[1]
CONFIG = SKILL_ROOT / "config" / "defaults.toml"
REQUIREMENTS_EXCLUSIONS = re.compile(
    r"(^|[/_.-])(test|tests|dev|development)([/_.-]|$)", re.I
)
IGNORED_REQUIREMENTS_DIRS = {".git", ".venv", "venv", "__pycache__", "models", "output"}


def settings() -> tuple[dict[str, Any], dict[str, Path]]:
    with CONFIG.open("rb") as stream:
        data = tomllib.load(stream)
    paths = data["paths"]
    overrides = {
        "venv": "VENV",
        "comfy": "COMFY",
        "helper": "COMFYUI_DGX_SPARK_ROOT",
        "starter_pack": "DGX_SPARK_STARTER_PACK_ROOT",
    }
    resolved = {
        key: Path(os.path.expandvars(os.path.expanduser(os.environ.get(env, value))))
        for key, value in paths.items()
        for env in [overrides[key]]
    }
    return data, resolved


def run(
    args: list[str], cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def github_repo(remote: str | None) -> str | None:
    """Return a normalized GitHub owner/repository for HTTPS or SSH URLs."""
    if not remote:
        return None
    match = re.fullmatch(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?/?", remote, re.I)
    if match:
        owner, repo = match.groups()
    else:
        parsed = urlparse(remote)
        supported_schemes = {"https", "http", "ssh", "git"}
        if (
            parsed.hostname
            and parsed.hostname.lower() == "github.com"
            and parsed.scheme in supported_schemes
        ):
            parts = parsed.path.strip("/").split("/")
            if len(parts) != 2:
                return None
            owner, repo = parts
            if repo.endswith(".git"):
                repo = repo[:-4]
        else:
            return None
    if not owner or not repo:
        return None
    return f"{owner}/{repo}".casefold()


def git_info(path: Path) -> dict[str, Any]:
    if not path.is_dir():
        return {"path": str(path), "exists": False}
    top = run(["git", "rev-parse", "--show-toplevel"], path)
    if top.returncode:
        return {"path": str(path), "exists": True, "git": False}
    root = Path(top.stdout.strip())

    def git(*args: str) -> str | None:
        result = run(["git", *args], root)
        return result.stdout.strip() if result.returncode == 0 else None
    info: dict[str, Any] = {
        "path": str(root),
        "exists": True,
        "git": True,
        "branch": git("branch", "--show-current"),
        "upstream": git("rev-parse", "--abbrev-ref", "@{upstream}"),
        "commit": git("rev-parse", "HEAD"),
        "origin": git("remote", "get-url", "origin"),
        "status": git("status", "--short"),
    }
    return info


def requirements(comfy: Path) -> list[str]:
    found: list[str] = []
    if comfy.is_dir():
        for root, directories, filenames in os.walk(comfy):
            directories[:] = sorted(
                name for name in directories if name not in IGNORED_REQUIREMENTS_DIRS
            )
            for filename in filenames:
                if (
                    "requirements" not in filename.lower()
                    or not filename.lower().endswith(".txt")
                ):
                    continue
                item = Path(root) / filename
                rel = item.relative_to(comfy).as_posix()
                if not REQUIREMENTS_EXCLUSIONS.search(rel):
                    found.append(str(item))
    return sorted(found)


def inspect(_: argparse.Namespace) -> int:
    data, paths = settings()
    repos: list[dict[str, Any]] = [git_info(paths["comfy"])]
    custom_nodes = paths["comfy"] / "custom_nodes"
    if custom_nodes.is_dir():
        for child in sorted(custom_nodes.iterdir()):
            if child.is_dir() and (child / ".git").exists():
                repos.append(git_info(child))
    report = {
        "paths": {key: str(value) for key, value in paths.items()},
        "repositories": repos,
        "requirements": requirements(paths["comfy"]),
        "constraints": str(paths["starter_pack"] / "constraints.txt"),
        "python": sys.version.split()[0],
        "config": str(CONFIG),
        "repository_urls": data["repositories"],
    }
    python = paths["venv"] / "bin" / "python"
    if python.is_file():
        probe_code = (
            "import torch; print(torch.__version__); print(torch.version.cuda); "
            "print(torch.cuda.get_device_name(0)); "
            "print(torch.cuda.get_device_capability(0))"
        )
        probe = run([str(python), "-c", probe_code])
        report["torch_probe"] = {
            "ok": probe.returncode == 0,
            "stdout": probe.stdout.strip(),
            "stderr": probe.stderr.strip(),
        }
    else:
        report["torch_probe"] = {"ok": False, "error": f"Missing {python}"}
    print(json.dumps(report, indent=2))
    return 0 if report["torch_probe"]["ok"] else 1


def sync_support(args: argparse.Namespace) -> int:
    data, paths = settings()
    specs: list[tuple[str, str]] = [
        ("helper", data["repositories"]["helper_url"]),
        ("starter_pack", data["repositories"]["starter_pack_url"]),
    ]
    failed: bool = False
    for name, expected in specs:
        path = paths[name]
        if not path.exists():
            print(f"PLAN clone {expected} -> {path}")
            if args.apply:
                path.parent.mkdir(parents=True, exist_ok=True)
                result = run(["git", "clone", expected, str(path)])
                if result.returncode:
                    print(result.stderr.strip(), file=sys.stderr)
                    failed = True
            continue
        info = git_info(path)
        if not info.get("git") or Path(info["path"]) != path.resolve():
            print(f"STOP {path}: not the expected Git checkout")
            failed = True
            continue
        if github_repo(info.get("origin")) != github_repo(expected):
            print(
                f"STOP {path}: origin is {info.get('origin')!r}, "
                f"expected repository {expected!r}"
            )
            failed = True
            continue
        if not info.get("branch") or info.get("upstream") != f"origin/{info['branch']}":
            print(
                f"STOP {path}: branch {info.get('branch')!r} "
                "does not track its origin branch"
            )
            failed = True
            continue
        if info.get("status"):
            print(f"STOP {path}: worktree is dirty")
            failed = True
            continue
        if info.get("status") is None:
            print(f"STOP {path}: could not inspect Git status")
            failed = True
            continue
        print(f"PLAN fast-forward {path}")
        if args.apply:
            result = run(["git", "pull", "--ff-only"], path)
            if result.returncode:
                print(result.stderr.strip(), file=sys.stderr)
                failed = True
            else:
                print(result.stdout.strip())
    return 1 if failed else 0


def install_requirements(args: argparse.Namespace) -> int:
    _, paths = settings()
    files = requirements(paths["comfy"])
    constraints = paths["starter_pack"] / "constraints.txt"
    python = paths["venv"] / "bin" / "python"
    if not files:
        print(
            f"No runtime requirements files found under {paths['comfy']}",
            file=sys.stderr,
        )
        return 1
    if not constraints.is_file() or not python.is_file():
        print(f"Need both {constraints} and {python}", file=sys.stderr)
        return 1
    for item in files:
        command = [
            str(python), "-m", "pip", "install", "-c", str(constraints), "-r", item
        ]
        print(json.dumps({"file": item, "command": command, "apply": args.apply}))
        if args.apply:
            result = run(command)
            if result.returncode:
                print(result.stdout, end="", file=sys.stderr)
                print(result.stderr, end="", file=sys.stderr)
                return result.returncode
    return 0


def aimdo(_: argparse.Namespace) -> int:
    _, paths = settings()
    python = paths["venv"] / "bin" / "python"
    code = (
        "import torch; torch.cuda.init(); _ = torch.zeros(1, device='cuda'); "
        "import comfy_aimdo.control as control; "
        "result = control.init(); print('AIMDO initialized:', result); "
        "raise SystemExit(0 if result else 1)"
    )
    result = run([str(python), "-c", code])
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "inspect", help="Report paths, Git checkouts, requirements, and torch details"
    ).set_defaults(func=inspect)
    sync = commands.add_parser(
        "sync-support", help="Clone or fast-forward the helper and starter pack"
    )
    sync.add_argument(
        "--apply", action="store_true", help="Perform the printed clone/pull operations"
    )
    sync.set_defaults(func=sync_support)
    install = commands.add_parser(
        "requirements", help="List constrained pip installs; add --apply to run them"
    )
    install.add_argument(
        "--apply",
        action="store_true",
        help="Install each discovered runtime requirements file",
    )
    install.set_defaults(func=install_requirements)
    commands.add_parser(
        "aimdo", help="Test AIMDO initialization in a fresh Python process"
    ).set_defaults(func=aimdo)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
