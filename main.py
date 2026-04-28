import csv
import logging
import sys
from pathlib import Path
from time import sleep, time

from client import MacuakeClient, MacuakeError

# Maximum time (in seconds) to wait for the Macuake Unix socket to become available.
SOCKET_TIMEOUT = 60

# Maximum time (in seconds) to wait for a single tab to be ready.
TAB_READY_TIMEOUT = 30
# Interval (in seconds) between read polls while waiting for a tab.
TAB_READY_POLL_INTERVAL = 0.3
# Minimum number of terminal lines to consider a tab ready.
TAB_READY_MIN_LINES = 2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path.home() / ".macuake-automation.conf"


def read_config(path: Path) -> list[dict]:
    """Read TSV config file. Columns: name, cwd, command (optional)."""
    if not path.exists():
        logger.error("Config file not found: %s", path)
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


def wait_for_tab_ready(
    client: MacuakeClient,
    session_id: str,
    *,
    min_lines: int = TAB_READY_MIN_LINES,
    timeout: float = TAB_READY_TIMEOUT,
    poll_interval: float = TAB_READY_POLL_INTERVAL,
) -> None:
    """Poll client.read until the terminal has at least *min_lines* lines."""
    deadline = time() + timeout
    while time() < deadline:
        result = client.read(session_id=session_id)
        non_empty = [l for l in result.lines if l.strip()]
        if len(non_empty) >= min_lines:
            return
        sleep(poll_interval)
    logger.warning(
        "Tab %s did not reach %d lines within %.1fs – proceeding anyway",
        session_id, min_lines, timeout,
    )


def main() -> None:
    client = MacuakeClient()
    
    logger.info("Waiting for Macuake socket...")
    if client.wait_for_socket(timeout=SOCKET_TIMEOUT):
        logger.info("Macuake socket ready")
    else:
        logger.error("Macuake socket not available")
        sys.exit(1)

    logger.info("Reading config from %s", CONFIG_PATH)
    config_tabs = read_config(CONFIG_PATH)
    logger.info("Loaded %d tab(s) from config", len(config_tabs))

    # 1. Remember existing tabs so we can close them later
    old_tabs = client.list_tabs()
    old_session_ids = {t.session_id for t in old_tabs}
    logger.info("Found %d existing tab(s) to clean up later", len(old_session_ids))

    # 2. Create tabs from config
    logger.info("Creating tabs from config...")
    created_tabs = []
    for tab in config_tabs:
        sid = client.new_tab(directory=tab["cwd"])
        client.focus(session_id=sid)
        created_tabs.append((sid, tab))
        logger.info("  Created tab '%s' (session=%s, cwd=%s)", tab["name"], sid, tab["cwd"])

    # 3. Set titles and execute commands
    logger.info("Setting titles and executing commands...")
    for sid, tab in created_tabs:
        if tab["name"] or "command" in tab:
            wait_for_tab_ready(client, sid)
        if tab["name"]:
            client.set_tab_title(tab["name"], sid)
        if "command" in tab:
            logger.info("  Executing command in '%s': %s", tab["name"], tab["command"])
            client.execute_silent(tab["command"], session_id=sid)

    # 4. Create generic tab (no name)
    logger.info("Creating generic tab...")
    generic_sid = client.new_tab(directory=Path.home().as_posix())

    # 5. Close all pre-existing tabs
    logger.info("Closing %d pre-existing tab(s)...", len(old_session_ids))
    for sid in old_session_ids:
        try:
            client.close_session(session_id=sid)
        except MacuakeError:
            logger.warning("Failed to close session %s", sid)



    # 6. Focus the generic tab
    client.focus(session_id=generic_sid)
    logger.info("Done – focused generic tab")


if __name__ == "__main__":
    main()
