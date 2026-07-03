# Sanctum Hub

One front door to every local **[Sanctum Suite](https://github.com/TheAIHorizon)** app. See them all in one place, tell at a glance which are running, and open or launch any of them with a click.

Local-first and dependency-free: a single static page driven by a small Python stdlib backend. Binds to `127.0.0.1` only.

![categories: Core · Sanctum Suite · Educator Tools](https://img.shields.io/badge/apps-12-3fd6c4)

## Run

```bash
python3 server.py
# → http://127.0.0.1:7080
```

That's it — no `pip install`, no build step. The page reads [`apps.json`](apps.json) live, so edits show up on refresh.

You can also open `index.html` directly as a file, but status and one-click launch need the backend.

## How it works

- **[`apps.json`](apps.json)** is the registry. Each entry has a `name`, `description`, `repo`, the local `dir` it's cloned to, its `port`, and the `start` command. **Edit `dir` to match where you cloned each app.**
- **`server.py`** serves the UI and adds two endpoints:
  - `GET /api/status` — TCP-probes each app's port and reports running/stopped.
  - `POST /api/launch {id}` — runs that app's `start` command in its `dir` (logs to `logs/<id>.log`).
- **`index.html`** renders the tiles, groups them by category, polls status every 15 s, and wires up Open / Launch / Copy-command.

Because the hub just runs the `start` commands from `apps.json`, treat that file as trusted config — it executes on your machine.

## Adding an app

Append an object to `apps.json`:

```json
{
  "id": "my-tool",
  "name": "My Tool",
  "category": "Sanctum Suite",
  "description": "What it does.",
  "repo": "https://github.com/TheAIHorizon/MyTool",
  "dir": "~/sanctum/MyTool",
  "port": 4000,
  "url": "http://127.0.0.1:4000",
  "start": "npm run dev"
}
```

Refresh the page. No rebuild.

## Roadmap

- [ ] **Self-bootstrapping install.** Install the Hub first; it then **clones each app on demand** the first time you launch it (`git clone <repo> <dir>`), runs the app's install step, and starts it — so a fresh machine goes from "just the Hub" to "any app running" without manual cloning.
- [ ] Per-app **model routing** through the Sanctum Engine (pick which local model an app uses, from the Hub).
- [ ] **Stop / status detail** (PID tracking, tail logs in the UI).
- [ ] Health beyond port-open (hit each app's real health route).
- [ ] Confirm each app's real `port` / `start` against its README (current values are best-effort defaults).

## License

**Polyform Noncommercial License 1.0.0** — see [LICENSE](LICENSE). Source-available; free for personal, educational, research, and other noncommercial use. Standard across the Sanctum suite.
