#!/usr/bin/env python3
"""
CI guard: any change to the model (engine/ or config/value_pools.py or
config/questions.py) MUST bump ENGINE_VERSION in storage/audit.py.

Why: plans are logged per engine version; an auditor must be able to ask
"which engine produced this number for this client". A formula change that
ships under an old version number breaks that reproducibility silently.

Usage: check_engine_version.py <base_ref>   (e.g. origin/main or HEAD^)
Exits 1 with an explanation when the rule is violated.
"""
import subprocess
import sys

MODEL_PATHS = ("engine/", "config/value_pools.py", "config/questions.py")
VERSION_FILE = "storage/audit.py"


def changed_files(base: str) -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        capture_output=True, text=True, check=True)
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def version_at(ref: str) -> str:
    out = subprocess.run(["git", "show", f"{ref}:{VERSION_FILE}"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        return ""
    for line in out.stdout.splitlines():
        if line.strip().startswith("ENGINE_VERSION"):
            return line.split("=")[1].split("#")[0].strip().strip('"\'')
    return ""


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    files = changed_files(base)
    model_changed = [f for f in files if f.startswith(MODEL_PATHS)]
    if not model_changed:
        print("engine-version guard: no model files changed; OK")
        return 0
    old, new = version_at(base), version_at("HEAD")
    if old and new and old != new:
        print(f"engine-version guard: model changed and version bumped "
              f"{old} -> {new}; OK")
        return 0
    print("engine-version guard: FAILED")
    print(f"  Model files changed: {model_changed}")
    print(f"  but ENGINE_VERSION is still '{new}' (was '{old}').")
    print(f"  Bump ENGINE_VERSION in {VERSION_FILE} so logged runs remain "
          f"attributable to the engine that produced them.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
