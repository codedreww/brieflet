# Brieflet

A personal reading feed that collects recent arXiv papers and matches them to my interests.

**v1.0p is complete.** The **p** stands for **prototype**. This version has been run on macOS and includes:

- A Streamlit web interface for browsing papers.
- Keyword matching against paper titles and descriptions.
- Scheduled arXiv collection using macOS `launchd`.

The project is under ongoing development. **v2 is in progress:** Brieflet now builds a stored **daily digest** of the papers that best match my saved keywords, and never sends the same paper twice. Next up is delivering that digest to Discord every morning, then natural-language preferences, semantic ranking, and more sources (news, Hacker News and others). The full plan is in [docs/adr/0001-brieflet-architecture.md](docs/adr/0001-brieflet-architecture.md).

## Setup

The project's dependencies are defined in `pyproject.toml`. Create and activate a virtual environment, then install the project:

```sh
python3.15 -m venv .venv
source .venv/bin/activate
```

```sh
pip install -e ".[dev]"
```

This installs the `brieflet` command into the virtual environment. Run every command below from the repository root, with the virtual environment active.

## Using the CLI

**Quick start:** save your interests, build today's digest, and read it.

```sh
brieflet prefs set "LLM, agents, security"
brieflet run-daily
brieflet digest
```

| Command | What it does |
| --- | --- |
| `brieflet run-daily` | Collects new papers, then builds and stores today's digest from papers you haven't been sent yet, and prints it. Safe to run more than once a day: a second run returns the same digest. |
| `brieflet digest` | Prints today's stored digest. |
| `brieflet digest --date 2026-11-14` | Prints the digest for a past day (`YYYY-MM-DD`). |
| `brieflet prefs show` | Prints your saved keywords, or the defaults (`AI, Security`) if none are saved. |
| `brieflet prefs set "LLM, agents"` | Saves comma-separated keywords for future digests. |
| `brieflet collect` | Only fetches the arXiv feed and stores new papers. |
| `brieflet status` | Shows recent collection runs: when they ran, how many papers were fetched and new, and any error. |
| `brieflet search` | Asks for keywords and scores all stored papers against them, without saving a digest. Also writes `output/result.md`. |

Every command has its own help, for example `brieflet --help`, `brieflet prefs --help` or `brieflet digest --help`.

**How a digest is built:**
- Each paper scores **5** per keyword found in its title and **2** per keyword found in its description.
- The top **10** become the digest, ranked by score, then by how recently they were collected.
- Each digest stores a copy of its papers and the keywords used, so past digests stay readable after old papers are pruned (papers are kept for 7 days).
- A paper that has appeared in any digest is never picked again.

## Run Streamlit

Before opening the interface for the first time, collect papers:

```sh
brieflet collect
```

Then start Streamlit:

```sh
streamlit run src/brieflet/app.py
```

The Streamlit app still scores papers live against the keywords you pick on the page. Reading stored digests and saved keywords there is planned (Phase 1 of the ADR).

## Scheduled collection (macOS)

The scheduler runs `brieflet collect` from the project's virtual environment; Streamlit runs separately. The included configuration runs collection daily at **08:00 in the Mac's local timezone**. Once Discord delivery is added, the schedule will switch to `brieflet run-daily` so the morning run also sends the digest.

For a new setup, first create the virtual environment and install the project (see above), so `.venv/bin/brieflet` exists. Then edit `config/pscript.plist` so the `brieflet` path, project directory, and log paths match where you cloned the repository. launchd doesn't activate virtual environments, so these must be absolute paths. From the repository root, copy the configuration into LaunchAgents:

```sh
mkdir -p ~/Library/LaunchAgents output
cp config/pscript.plist ~/Library/LaunchAgents/com.andrewtan.pscript.collect.plist
```

**Start / load the schedule** — use when unloaded:

```sh
launchctl bootstrap "gui/$(id -u)" \
  ~/Library/LaunchAgents/com.andrewtan.pscript.collect.plist
```

**Stop / unload the schedule:**

```sh
launchctl bootout "gui/$(id -u)/com.andrewtan.pscript.collect"
```

**Restart / reload configuration** — after updating the installed plist:

```sh
launchctl bootout "gui/$(id -u)/com.andrewtan.pscript.collect"

launchctl bootstrap "gui/$(id -u)" \
  ~/Library/LaunchAgents/com.andrewtan.pscript.collect.plist
```

**Run collection immediately** — the schedule must be loaded:

```sh
launchctl kickstart "gui/$(id -u)/com.andrewtan.pscript.collect"
```

**Check status:**

```sh
launchctl print "gui/$(id -u)/com.andrewtan.pscript.collect"
```

**See what recent collection runs did** (when they ran, how many items were fetched and new, and any error):

```sh
brieflet status
```

| Command     | Purpose                                                  |
| ----------- | -------------------------------------------------------- |
| `bootstrap` | Loads the job definition.                                |
| `kickstart` | Starts a loaded job immediately.                         |
| `bootout`   | Unloads the job and stops its running instance, if any.  |
| `disable`   | Persistently disables the job across logins and reboots. |
| `enable`    | Removes that persistent restriction.                     |
| `print`     | Shows the job's status.                                  |

## Development

Run the tests and the linter from the repository root:

```sh
pytest
```

```sh
ruff check src tests
```

Tests never touch `data/storage.db` or the network: each one uses a temporary database, and any real HTTP request fails the test. Code in `src/brieflet/core/` must not import `cli.py` or `app.py`; `tests/test_architecture.py` enforces this.
