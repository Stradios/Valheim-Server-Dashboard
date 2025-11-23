📘 ValPanel – Valheim Server Dashboard

ValPanel is a lightweight, modern web dashboard for deploying and managing multiple Valheim dedicated servers using the lloesche/valheim-server Docker image.

It is built for CasaOS, TrueNAS SCALE, Docker, and Proxmox users who want a simple but powerful web interface to control servers, assign ports, manage configs, and restart crashed instances — all without SSH.


(optional – add your own banner image later)

🚀 Features (v0.3 Stable)
✔ Multi-Server Management

Create and run multiple Valheim servers simultaneously using the same host.

✔ Auto Port Allocation

Automatically assigns ports from a configurable range with 3-port blocks.

✔ Start / Stop / Restart Controls

Manage each instance directly from the dashboard.

✔ Crash-Safe Restarts

If a server becomes unresponsive, ValPanel lets admins restart it instantly.

✔ SQLite Database

Panel settings and server entries are saved persistently.

✔ No SSH Needed

Everything is controlled through Docker from the web UI.

✔ Built for CasaOS, TrueNAS, Unraid, Proxmox & Linux Hosts

Fully compatible with /var/run/docker.sock communication.

✔ Roles: Admin & Moderator

Admin: Full control (create, delete, restart servers)

Moderator: Manage permissions & restart servers

🧩 Architecture

ValPanel runs as a single Docker container containing:

Python 3.11

Flask

SQLAlchemy

Docker SDK for Python

HTML/CSS dashboard

SQLite DB

REST API for future expansion

Valheim servers are created as separate containers, each fully isolated.

📦 Installation (Docker)
Quick Start
docker run -d \
  --name valpanel \
  -p 8000:8000 \
  -e TZ=Europe/Stockholm \
  -e PANEL_PORT=8000 \
  -e VALHEIM_IMAGE=lloesche/valheim-server \
  -e VALHEIM_PORT_RANGE_START=24560 \
  -e VALHEIM_PORT_RANGE_END=24660 \
  -e VALHEIM_PORT_BLOCK_SIZE=3 \
  -e DATA_ROOT=/mnt/apps/valpanel/servers \
  -v /mnt/apps/valpanel/data:/app/data \
  -v /mnt/apps/valpanel/servers:/mnt/apps/valpanel/servers \
  -v /var/run/docker.sock:/var/run/docker.sock \
  stradios/valpanel:latest


Then open:

👉 http://localhost:8000

🐳 docker-compose.yml example
version: "3.8"

services:
  valpanel:
    image: stradios/valpanel:latest
    container_name: valpanel
    restart: unless-stopped

    ports:
      - "8000:8000"

    environment:
      - TZ=Europe/Stockholm
      - PANEL_PORT=8000
      - VALHEIM_IMAGE=lloesche/valheim-server
      - VALHEIM_PORT_RANGE_START=24560
      - VALHEIM_PORT_RANGE_END=24660
      - VALHEIM_PORT_BLOCK_SIZE=3
      - DATA_ROOT=/mnt/apps/valpanel/servers

    volumes:
      - /mnt/apps/valpanel/data:/app/data
      - /mnt/apps/valpanel/servers:/mnt/apps/valpanel/servers
      - /var/run/docker.sock:/var/run/docker.sock

📁 Project Structure
valpanel/
│
├── app/
│   ├── app.py               # Main Flask app
│   ├── config.py            # Config + port ranges
│   ├── models.py            # SQLAlchemy database models
│   ├── docker_manager.py    # Docker API wrapper
│   ├── templates/           # HTML views
│   ├── static/              # CSS/JS
│   ├── Dockerfile           # Build instructions
│
├── data/                    # SQLite database (bind-mounted)
├── servers/                 # Server definitions + world configs
│
├── valpanel-compose.yml     # Example compose
├── LICENSE                  # GPL-3.0 License
└── README.md                # This file

🔒 License (GPL-3.0)

ValPanel is released under the GNU General Public License v3.0, which means:

✔ You may use it
✔ You may modify it
✔ You may contribute to it
❗You may NOT rebrand it into closed-source paid software

This protects the community and ensures ValPanel stays open-source.

🤝 Contributing

Contributions are very welcome!

If you'd like to help:

Fork the repo

Create a feature branch

Commit + push changes

Open a Pull Request

You can also join discussions under Issues.

🗂 Roadmap
v0.4 (Next)

Server logs tab

Real-time server status polling

Player count detection (UDP query research ongoing)

Delete/Restart modals (UI polish)

Automated backups from Panel

v1.0

Full admin/moderator role system

World auto-install presets

Plugin and mods support

Cloud storage backups

REST API for external tools

Theme system (dark/light mode)

❤️ Credits

ValPanel is created and maintained by:

Theodor Veres (Stradios)
Founder of Nort-Sun Gaming Community
Creator of ValPanel
https://www.nort-sun.com