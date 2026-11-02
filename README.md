# Brieflet

A personal reading feed that collects recent arXiv papers and matches them to my interests.

**v1.0p is complete.** The **p** stands for **prototype**. This version has been run on macOS and includes:

- A Streamlit web interface for browsing papers.
- Keyword matching against paper titles and descriptions.
- Scheduled arXiv collection using macOS `launchd`.

The project is under ongoing development. I'm currently exploring ways to make it scale better and support more sources. Future versions will deliver news through a Telegram or Discord bot, alongside a web interface, with more sources including hackerrank, and others.

## Run Streamlit

The project requires Python with `streamlit`, `httpx`, and `feedparser` installed. I've made the install definition inside pyproject.toml, do run the command below to run the virtual environment and install the dependencies:

To create and activate the virtual environment:

```sh
python3.15 -m venv .venv
source .venv/bin/activate
```

Then install the packages with this command:

```sh
pip install -e ".[dev]"
```

Before opening the interface for the first time, collect papers from the repository root:

```sh
brieflet collect
```

Then run Streamlit from the repository root:

```sh
streamlit run src/brieflet/app.py
```

## Scheduled collection (macOS)

The scheduler runs `brieflet collect` from the project's virtual environment; Streamlit runs separately. The included configuration runs collection daily at **08:00 in the Mac's local timezone**.

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

| Command     | Purpose                                                  |
| ----------- | -------------------------------------------------------- |
| `bootstrap` | Loads the job definition.                                |
| `kickstart` | Starts a loaded job immediately.                         |
| `bootout`   | Unloads the job and stops its running instance, if any.  |
| `disable`   | Persistently disables the job across logins and reboots. |
| `enable`    | Removes that persistent restriction.                     |
| `print`     | Shows the job's status.                                  |
