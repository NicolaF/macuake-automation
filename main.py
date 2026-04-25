import csv
import sys
from pathlib import Path

from client import MacuakeClient, MacuakeError

CONFIG_PATH = Path.home() / ".macuake-automation.conf"


def read_config(path: Path) -> list[dict]:
    """Read TSV config file. Columns: name, cwd, command (optional)."""
    if not path.exists():
        print(f"Config file not found: {path}", file=sys.stderr)
        sys.exit(1)
    tabs = []
    with path.open() as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if not row or row[0].startswith("#"):
                continue
            if len(row) < 2:
                continue
            entry = {
                "name": row[0].strip(),
                "cwd": row[1].strip(),
            }
            if len(row) >= 3 and row[2].strip():
                entry["command"] = row[2].strip()
            tabs.append(entry)
    return tabs


def main() -> None:
    client = MacuakeClient()

    config_tabs = read_config(CONFIG_PATH)

    # 1. Remember existing tabs so we can close them later
    old_tabs = client.list_tabs()
    old_session_ids = {t.session_id for t in old_tabs}

    # 2. Create tabs from config
    for tab in config_tabs:
        sid = client.new_tab(directory=tab["cwd"])
        #client.set_tab_title(tab["name"], sid)
        if "command" in tab:
            client.execute_silent(tab["command"], session_id=sid)

    # 3. Create generic tab (no name)
    generic_sid = client.new_tab(directory=Path.home().as_posix())

    # 4. Close all pre-existing tabs
    for sid in old_session_ids:
        try:
            client.close_session(session_id=sid)
        except MacuakeError:
            pass

    # 5. Focus the generic tab
    client.focus(session_id=generic_sid)


if __name__ == "__main__":
    main()
