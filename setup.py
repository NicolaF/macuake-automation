"""Generate and install macuake-automation Launch Agent + Automator shortcut."""

import plistlib
import sys
from pathlib import Path

LABEL = "com.macuake-automation"
SERVICE_NAME = "Macuake Automation"
PROJECT_DIR = Path(__file__).resolve().parent
PYTHON = str(PROJECT_DIR / ".venv" / "bin" / "python")
SCRIPT = str(PROJECT_DIR / "main.py")
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
WORKFLOW_DIR = (
    Path.home() / "Library" / "Services" / f"{SERVICE_NAME}.workflow"
)


def generate_plist() -> dict:
    return {
        "Label": LABEL,
        "ProgramArguments": [PYTHON, SCRIPT],
        "RunAtLoad": True,
        "KeepAlive": False,
        "StandardOutPath": "/tmp/macuake-automation.log",
        "StandardErrorPath": "/tmp/macuake-automation.err.log",
    }


def generate_workflow():
    """Create an Automator Quick Action that runs main.py."""
    contents_dir = WORKFLOW_DIR / "Contents"
    contents_dir.mkdir(parents=True, exist_ok=True)

    info_plist = {
        "NSServices": [
            {
                "NSMenuItem": {"default": SERVICE_NAME},
                "NSMessage": "runWorkflowAsService",
            }
        ],
    }
    with (contents_dir / "Info.plist").open("wb") as f:
        plistlib.dump(info_plist, f)

    document_plist = {
        "AMCanTabToFirstAction": True,
        "AMApplicationBuild": "523",
        "AMApplicationVersion": "2.10",
        "AMDocumentVersion": "2",
        "AMIsActionList": True,
        "AMWorkflowSchemeVersion": "2.0",
        "actions": [
            {
                "action": {
                    "AMAccepts": {
                        "Container": "List",
                        "Optional": True,
                        "Types": ["com.apple.cocoa.string"],
                    },
                    "AMActionVersion": "2.0.3",
                    "AMApplication": ["Automator"],
                    "AMBundleIdentifier": "com.apple.RunShellScript",
                    "AMName": "Run Shell Script",
                    "AMParameterProperties": {
                        "COMMAND_STRING": {},
                        "CheckedForUserDefaultShell": {},
                        "inputMethod": {},
                        "shell": {},
                        "source": {},
                    },
                    "AMProvides": {
                        "Container": "List",
                        "Types": ["com.apple.cocoa.string"],
                    },
                    "ActionBundlePath": "/System/Library/Automator/Run Shell Script.action",
                    "ActionName": "Run Shell Script",
                    "BundleIdentifier": "com.apple.RunShellScript",
                    "CFBundleVersion": "2.0.3",
                    "CanShowSelectedItemsWhenRun": True,
                    "CanShowWhenRun": False,
                    "Category": ["AMCategoryUtilities"],
                    "Class Name": "RunShellScriptAction",
                    "InputUUID": "0",
                    "Keywords": ["Shell", "Script", "Command", "Run", "Unix"],
                    "OutputUUID": "0",
                    "UUID": "0",
                    "UnlocalizedApplications": ["Automator"],
                    "arguments": {
                        "0": {
                            "default value": "",
                            "name": "COMMAND_STRING",
                            "required": "0",
                            "type": "0",
                            "uuid": "0",
                            "value": f"{PYTHON} {SCRIPT}",
                        },
                        "1": {
                            "default value": "/bin/zsh",
                            "name": "shell",
                            "required": "0",
                            "type": "0",
                            "uuid": "1",
                            "value": "/bin/zsh",
                        },
                        "2": {
                            "default value": "0",
                            "name": "inputMethod",
                            "required": "0",
                            "type": "0",
                            "uuid": "2",
                            "value": "0",
                        },
                        "3": {
                            "default value": "",
                            "name": "CheckedForUserDefaultShell",
                            "required": "0",
                            "type": "0",
                            "uuid": "3",
                            "value": True,
                        },
                        "4": {
                            "default value": "",
                            "name": "source",
                            "required": "0",
                            "type": "0",
                            "uuid": "4",
                            "value": "",
                        },
                    },
                    "isViewVisible": True,
                },
            },
        ],
        "connectors": {},
        "workflowMetaData": {
            "workflowTypeIdentifier": "com.apple.Automator.servicesMenu",
        },
    }
    with (contents_dir / "document.wflow").open("wb") as f:
        plistlib.dump(document_plist, f)


def install():
    # Launch Agent
    plist = generate_plist()
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PLIST_PATH.open("wb") as f:
        plistlib.dump(plist, f)
    print(f"✓ Launch Agent: {PLIST_PATH}")

    # Automator service
    generate_workflow()
    print(f"✓ Service: {WORKFLOW_DIR}")

    print()
    print("To enable the Launch Agent:")
    print(f"  launchctl load {PLIST_PATH}")
    print()
    print("To assign a keyboard shortcut:")
    print("  System Settings → Keyboard → Keyboard Shortcuts → Services")
    print(f'  → Find "{SERVICE_NAME}" → Set a shortcut')


def uninstall():
    removed = False
    if PLIST_PATH.exists():
        PLIST_PATH.unlink()
        print(f"✓ Removed {PLIST_PATH}")
        removed = True
    if WORKFLOW_DIR.exists():
        import shutil
        shutil.rmtree(WORKFLOW_DIR)
        print(f"✓ Removed {WORKFLOW_DIR}")
        removed = True
    if not removed:
        print("Not installed.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall()
    else:
        install()
