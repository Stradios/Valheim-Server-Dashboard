# Valheim Server Dashboard

Self-hosted control panel for spinning up and supervising multiple Valheim dedicated servers on a single host. The panel is built with Flask, persists state in SQLite (or any SQLAlchemy compatible database), and orchestrates `lloesche/valheim-server` containers through the Docker Engine API.

## Features
- Multi-server orchestration with automatic, non-overlapping UDP port allocation
- First-run guard that requires an admin account before the panel becomes accessible
- Role-based access control (admin and moderator) with invite tokens
- REST API and lightweight dashboard for creating, starting, stopping, restarting, and deleting servers
- Dedicated data folders per world (config, save data, and backups)
- Server log streaming via the API for quick troubleshooting

## Project Layout
- `app/` – Flask application, models, templates, and Dockerfile
- `servers/` – Default location for per-server config/world/backup directories
- `data/` – Default SQLite database location when running in Docker
- `valpanel.yaml` – Example Docker Compose manifest for building and running the panel
- `gpl-3.0.txt` – License text (GNU GPL v3)

## Quick Start (Docker)
1. Ensure Docker Engine is installed and that the daemon can reach the internet to pull `lloesche/valheim-server`.
2. Clone this repository and change into it.
3. Edit `valpanel.yaml` to match your host paths (the example assumes everything lives under `/mnt/apps/valpanel`).
4. Launch the panel:
   ```bash
   docker compose -f valpanel.yaml up -d
   ```
5. Visit `http://<host>:8000/setup` to create the first admin user. Once an admin exists, the login page becomes available.

While running via Docker you must mount:
- `/var/run/docker.sock` (the panel uses the Docker SDK to manage Valheim containers)
- A persistent folder for `/app/data` (SQLite database) and `/servers` (world data/backups)

## Local Development (Python)
1. Install Python 3.12+ and Docker.
2. Create a virtual environment inside `app/` and install dependencies:
   ```bash
   cd app
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Export the environment variables you need (see the next section) and point `DATA_ROOT` somewhere writable on your machine.
4. Start the development server:
   ```bash
   python app.py
   ```
5. In another terminal, create the admin user through `http://localhost:8000/setup` or via `POST /api/setup/admin`.

## Configuration
Most behavior is controlled through environment variables (all optional, sane defaults shown):

| Variable | Default | Description |
| --- | --- | --- |
| `PANEL_PORT` | `8000` | HTTP port exposed by the Flask app |
| `DATABASE_URL` | `sqlite:////app/data/valpanel.db` | SQLAlchemy connection string |
| `SECRET_KEY` | `dev-change-me` | Flask session secret – override in production |
| `VALHEIM_IMAGE` | `lloesche/valheim-server` | Docker image used for each game server |
| `VALHEIM_PORT_RANGE_START` | `24560` | First UDP port available for allocation |
| `VALHEIM_PORT_RANGE_END` | `24660` | Last UDP port in the pool |
| `VALHEIM_PORT_BLOCK_SIZE` | `3` | Number of contiguous ports reserved per server |
| `DATA_ROOT` | `/servers` | Host path mounted into containers to store config/world/backups |
| `TZ` | `Europe/Stockholm` | Time zone propagated to the Valheim containers |
| `PUBLIC_BASE_URL` | _(empty)_ | If set, invite URLs will be absolute using this base |

## First-Time Experience
1. Start the panel (Docker or local).
2. Navigate to `/setup` and create the initial admin account.
3. Use the dashboard to add Valheim worlds. The panel automatically provisions data folders under `DATA_ROOT` and launches a Docker container per world.
4. Invite moderators through `POST /api/invites` or the UI. Invited users finish registration through `/register?token=<token>`.

## API + Dashboard Highlights
- `GET /api/servers` – List servers and their Docker status
- `POST /api/servers` – Create a new server (admin only)
- `POST /api/servers/<id>/(start|stop|restart)` – Control lifecycle
- `DELETE /api/servers/<id>` – Remove server, container, and data (admin only)
- `GET /api/servers/<id>/logs` – Tail recent container logs

Every endpoint enforces authentication and role checks. The bundled Jinja templates (`/setup`, `/login`, `/dashboard`) consume these APIs, so you can either use the built-in UI or integrate the backend with your own frontend.

## License
Released under the GNU General Public License v3.0. See `gpl-3.0.txt` for details.
