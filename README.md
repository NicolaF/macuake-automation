# macuake-automation

Automatically provisions Macuake terminal tabs at login: creates named tabs with specific working directories and optional startup commands, then cleans up pre-existing tabs.

## What it does

1. Waits for the Macuake Unix socket (`/tmp/macuake.sock`) to be available.
2. Reads a TSV config file listing the tabs to create.
4. Creates each configured tab (with its working directory), waits for them to initialize, then sets titles and runs optional commands.
5. Creates one extra generic tab (home directory, no title).
6. Closes all pre-existing tabs.
7. Focuses the generic tab.

The result is a clean, reproducible Macuake workspace every time you log in.

## Setup

### Requirements

- Python ≥ 3.13
- Macuake running (exposes `/tmp/macuake.sock`)

### Install

```bash
# Clone the repo and create a venv
git clone https://github.com/NicolaF/macuake-automation.git
cd macuake-automation
uv sync          # or: python -m venv .venv && .venv/bin/pip install .

# Install the Launch Agent + mreset command
python setup.py
```

This will:
- Create a **Launch Agent** (`~/Library/LaunchAgents/com.macuake-automation.plist`) that runs `main.py` at login.
- Symlink **`mreset`** into `~/.bin/` so you can re-run the setup manually from any tab.

Then load the agent:

```bash
launchctl load ~/Library/LaunchAgents/com.macuake-automation.plist
```

Make sure `~/.bin` is in your `PATH` (add to `.zshrc` if needed):

```bash
export PATH="$HOME/.bin:$PATH"
```

You can then run `mreset` from any terminal tab to re-provision all tabs. The command detaches from the calling terminal, so it keeps running even if the tab it was launched from gets closed.

### Uninstall

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.macuake-automation.plist
python setup.py uninstall
```

### Logs

- stdout: `/tmp/macuake-automation.log`
- stderr: `/tmp/macuake-automation.err.log`

## Configuration

Create a TSV file at `~/.macuake-automation.conf` with three columns:

| Column | Required | Description |
|--------|----------|-------------|
| `name` | yes | Tab title |
| `cwd` | yes | Working directory |
| `command` | no | Command to execute on startup |

No header row — the file is parsed directly as data. Lines starting with `#` are treated as comments and ignored.

### Example

```tsv
# name	cwd	command
api	~/dev/api	make serve
frontend	~/dev/frontend	npm run dev
logs	~/var/log	tail -f app.log
```
