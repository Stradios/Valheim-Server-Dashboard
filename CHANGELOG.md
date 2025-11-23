# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) once a stable API is published.

## [Unreleased]
### Added
- `GET /api/servers/<id>/logs` endpoint exposed inside `create_app`, allowing both the API and dashboard to stream recent Docker logs.
- New `README.md` overhaul with badges, architecture notes, Docker guidance, and configuration tables to improve GitHub presentation.
- Contributor onboarding guide in `CONTRIBUTING.md`.
- Initial project changelog.

### Changed
- Documentation now references multiple deployment options (`valpanel.yaml`, `compose.yaml`, `compose.debug.yaml`) for clarity.

## [0.3.0] - 2024-02-01
### Added
- Multi-server orchestration backed by SQLite + SQLAlchemy.
- Admin onboarding guard (`/setup`) and invite-based moderator registration.
- Dashboard controls for creating, starting, stopping, restarting, and deleting Valheim worlds.
- Automatic 3-port allocation with configurable ranges.
- Docker Compose example (`valpanel.yaml`) for CasaOS/TrueNAS/Proxmox deployments.

### Fixed
- Crash-safe server restart logic that recreates missing containers and purges stale data directories.

[Unreleased]: https://github.com/stradios/Valheim-Server-Dashboard/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/stradios/Valheim-Server-Dashboard/releases/tag/v0.3.0
