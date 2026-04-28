"""Install macuake-automation: Launch Agent + mreset symlink."""

import plistlib
import sys
from pathlib import Path

LABEL = "com.macuake-automation"
PROJECT_DIR = Path(__file__).resolve().parent
PYTHON = str(PROJECT_DIR / ".venv" / "bin" / "python")
SCRIPT = str(PROJECT_DIR / "main.py")
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
MRESET_SRC = PROJECT_DIR / "mreset"
BIN_DIR = Path.home() / ".bin"
MRESET_LINK = BIN_DIR / "mreset"


def generate_plist() -> dict:
    return {
        "Label": LABEL,
        "ProgramArguments": [PYTHON, SCRIPT],
        "RunAtLoad": True,
        "KeepAlive": False,
        "StandardOutPath": "/tmp/macuake-automation.log",
        "StandardErrorPath": "/tmp/macuake-automation.err.log",
    }


def install():
    # Launch Agent
    plist = generate_plist()
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PLIST_PATH.open("wb") as f:
        plistlib.dump(plist, f)
    print(f"✓ Launch Agent: {PLIST_PATH}")

    # mreset symlink
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    if MRESET_LINK.is_symlink() or MRESET_LINK.exists():
        MRESET_LINK.unlink()
    MRESET_LINK.symlink_to(MRESET_SRC)
    print(f"✓ Symlinked {MRESET_LINK} → {MRESET_SRC}")

    print()
    print("To enable the Launch Agent:")
    print(f"  launchctl load {PLIST_PATH}")
    print()
    print("Make sure ~/.bin is in your PATH (add to .zshrc if needed):")
    print('  export PATH="$HOME/.bin:$PATH"')


def uninstall():
    removed = False
    if PLIST_PATH.exists():
        PLIST_PATH.unlink()
        print(f"✓ Removed {PLIST_PATH}")
        removed = True
    if MRESET_LINK.is_symlink() or MRESET_LINK.exists():
        MRESET_LINK.unlink()
        print(f"✓ Removed {MRESET_LINK}")
        removed = True
    if not removed:
        print("Not installed.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall()
    else:
        install()
