# Contributing to ValPanel

Thanks for your interest in improving ValPanel! The project thrives on community feedback, bug reports, and pull requests. This guide explains how to get started, run the app locally, and submit changes.

## Code of Conduct
- Be respectful and constructive in issues, discussions, and PR reviews.
- Assume best intentions and focus on solving problems together.

## Getting Started
1. Fork the repository and clone your fork:
   ```bash
   git clone https://github.com/<you>/Valheim-Server-Dashboard.git
   cd Valheim-Server-Dashboard
   ```
2. Add the upstream repo so you can sync later:
   ```bash
   git remote add upstream https://github.com/stradios/Valheim-Server-Dashboard.git
   ```

## Dev Environment
The Flask backend lives inside `app/`. A lightweight Python + Docker setup is enough:
```bash
cd app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PANEL_PORT=8000
export DATA_ROOT=$PWD/../servers   # or any writable path
python app.py
```

You also need Docker running locally because the app interacts with the Docker Engine API.

### Using Docker Compose
A full-stack environment (panel + Valheim server) can be booted with:
```bash
docker compose -f valpanel.yaml up -d
```
or the minimalist `compose.yaml` if you only need the panel container for UI work.

## Making Changes
1. Create a feature branch off `main`:
   ```bash
   git checkout -b feature/my-awesome-update
   ```
2. Keep changes scoped. Separate unrelated fixes into their own branches/PRs.
3. Follow the existing style:
   - Python: standard library imports first, then third-party, then local. Use clear function names and keep comments concise.
   - HTML/CSS/JS: match the formatting of nearby code. Avoid inline styles unless the file already uses them.
   - Markdown: prefer sentence-case headings and wrap lines at ~100 characters when practical.
4. Add or update documentation when behavior changes (README, this guide, etc.).

## Testing
There is no automated test suite yet, so please verify manually:
- Run the Flask dev server and exercise the relevant API endpoints with `curl` or the dashboard.
- If you change Docker interactions, start/stop/restart a dummy server to confirm behavior.
- Check that the database migrations or schema updates work against a fresh SQLite file.

If you add automated tests in the future, document how to run them here.

## Submitting a Pull Request
1. Ensure your branch is up to date:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```
2. Run through the manual tests above.
3. Commit with clear messages:
   ```bash
   git commit -m "Add server log viewer to dashboard"
   ```
4. Push to your fork and open a PR against `main`.
5. In the PR description, include:
   - What the change does and why
   - How you tested it
   - Screenshots/GIFs for UI tweaks if possible

## Reporting Bugs & Feature Requests
- Search existing issues first to avoid duplicates.
- When filing a bug, include:
  - Environment info (OS, Docker version)
  - How you deployed ValPanel (Docker run, compose, Proxmox, etc.)
  - Steps to reproduce and any logs
- For feature ideas, explain the workflow problem you are trying to solve.

## License
By contributing, you agree that your work will be released under the GNU GPL v3.0 license that covers this repository.

Thanks again for helping ValPanel grow! Reach out via GitHub Issues if you need clarification before opening a PR.
