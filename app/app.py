import os
import re
import secrets
from pathlib import Path
from functools import wraps

from flask import (
    Flask,
    jsonify,
    request,
    session,
    render_template,
    redirect,
    url_for,
)
from docker import from_env as docker_from_env
from docker.errors import NotFound, APIError

from config import Config
from models import db, Server, User, Invite  # make sure models.py has User + Invite


docker_client = docker_from_env()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def current_user():
        uid = session.get("user_id")
        if not uid:
            return None
        return User.query.get(uid)

    def login_required(role=None):
        """
        Decorator for routes that require login.
        If role is set (e.g. 'admin'), it must match user.role.
        """

        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                user = current_user()
                if not user:
                    # For JSON API: return 401
                    if request.path.startswith("/api/"):
                        return jsonify({"error": "Authentication required"}), 401
                    # For HTML: redirect to login
                    return redirect(url_for("login_page"))

                if role and user.role != role:
                    if request.path.startswith("/api/"):
                        return (
                            jsonify({"error": "Insufficient permissions"}),
                            403,
                        )
                    return redirect(url_for("dashboard_page"))
                return f(*args, **kwargs)

            return wrapper

        return decorator

    # ------------------------------------------------------------------
    # Global guards (first-time setup)
    # ------------------------------------------------------------------

    @app.before_request
    def ensure_admin_setup():
        """
        If no admin exists yet, only allow:
          - /api/setup
          - /api/setup/admin
          - /setup (HTML)
          - static files
        Everything else returns setup-required.
        """
        open_endpoints = {"setup_info", "setup_create_admin", "setup_page", "static"}

        # If an admin exists, do nothing
        if User.query.filter_by(role="admin").count() > 0:
            return

        # If no admin yet, allow only the setup endpoints/static
        if request.endpoint in open_endpoints:
            return

        # API requests get JSON error
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "error": "No admin account exists yet. Use /api/setup/admin to create one."
                    }
                ),
                403,
            )

        # HTML requests get redirected to /setup
        return redirect(url_for("setup_page"))

    # ------------------------------------------------------------------
    # Helper functions (Valheim + Docker)
    # ------------------------------------------------------------------

    def slugify(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        return slug or "server"

    def allocate_port_block() -> int:
        """Find a free base port in the configured pool."""
        used_ports = {s.base_port for s in Server.query.all()}
        start = app.config["VALHEIM_PORT_RANGE_START"]
        end = app.config["VALHEIM_PORT_RANGE_END"]
        step = app.config["VALHEIM_PORT_BLOCK_SIZE"]

        for base in range(start, end, step):
            if base not in used_ports:
                return base
        raise RuntimeError("No free ports left in pool")

    def server_data_dir(slug: str) -> str:
        root = Path(app.config["DATA_ROOT"])
        return str(root.joinpath(slug))

    def get_container(container_name: str):
        try:
            return docker_client.containers.get(container_name)
        except NotFound:
            return None

    def create_valheim_container(server: Server):
        """
        Create (or recover) a Valheim server container using lloesche/valheim-server.

        Each server gets:
          - its own data directory under DATA_ROOT/<slug>
          - config folder   -> /config
          - server folder   -> /opt/valheim
          - backups folder  -> /backups
          - 3-port block: base_port, base_port+1, base_port+2 (UDP)

        If a container with the same name already exists:
          - If it's running, we reuse it.
          - If it's stale (created/exited/dead), we remove and recreate it.
        """
        image = app.config["VALHEIM_IMAGE"]

        # Check for existing container
        existing = get_container(server.container_name)
        if existing is not None:
            try:
                existing.reload()
            except APIError:
                app.logger.warning(
                    f"Failed to reload container {server.container_name}, removing it."
                )
                try:
                    existing.remove(force=True)
                except APIError as e:
                    app.logger.error(
                        f"Could not remove existing container {server.container_name}: {e.explanation}"
                    )
                    raise
            else:
                if existing.status in ("created", "exited", "dead"):
                    app.logger.warning(
                        f"Removing stale container {server.container_name} (status={existing.status})"
                    )
                    try:
                        existing.remove(force=True)
                    except APIError as e:
                        app.logger.error(
                            f"Could not remove stale container {server.container_name}: {e.explanation}"
                        )
                        raise
                else:
                    app.logger.info(
                        f"Container {server.container_name} exists and is running; reusing it."
                    )
                    return existing

        # Allocate ports
        ports = {
            f"{server.base_port}/udp": server.base_port,
            f"{server.base_port + 1}/udp": server.base_port + 1,
            f"{server.base_port + 2}/udp": server.base_port + 2,
        }

        # Host directory structure
        root = Path(server_data_dir(server.slug))
        config_dir = root / "config"
        server_dir = root / "server"
        backups_dir = root / "backups"

        config_dir.mkdir(parents=True, exist_ok=True)
        server_dir.mkdir(parents=True, exist_ok=True)
        backups_dir.mkdir(parents=True, exist_ok=True)

        volumes = {
            str(config_dir): {"bind": "/config", "mode": "rw"},
            str(server_dir): {"bind": "/opt/valheim", "mode": "rw"},
            str(backups_dir): {"bind": "/backups", "mode": "rw"},
        }

        env = {
            "SERVER_NAME": server.name,
            "WORLD_NAME": server.world_name,
            "SERVER_PASS": server.password,
            "SERVER_PORT": server.base_port,
            "TZ": os.getenv("TZ", "Europe/Stockholm"),
            "PUBLIC": "1",
            "CROSSPLAY": "true",
            "SERVER_ARGS": "-crossplay",
        }

        try:
            container = docker_client.containers.run(
                image=image,
                name=server.container_name,
                detach=True,
                environment=env,
                volumes=volumes,
                ports=ports,
                restart_policy={"Name": "unless-stopped"},
            )
            return container
        except APIError as e:
            app.logger.error(f"Error creating container: {e.explanation}")
            raise



    # ------------------------------------------------------------------
    # Context processor (for templates)
    # ------------------------------------------------------------------

    @app.context_processor
    def inject_current_user():
        return {"current_user": current_user()}

    # ------------------------------------------------------------------
    # Root / health
    # ------------------------------------------------------------------

    @app.route("/")
    def index():
        user = current_user()
        has_admin = User.query.filter_by(role="admin").count() > 0
        return jsonify(
            {
                "status": "ok",
                "message": "ValPanel backend running",
                "has_admin": has_admin,
                "current_user": user.to_dict() if user else None,
            }
        )

    # ------------------------------------------------------------------
    # Setup (first admin)
    # ------------------------------------------------------------------

    @app.route("/api/setup", methods=["GET"])
    def setup_info():
        has_admin = User.query.filter_by(role="admin").count() > 0
        return jsonify({"has_admin": has_admin})

    @app.route("/api/setup/admin", methods=["POST"])
    def setup_create_admin():
        from werkzeug.security import generate_password_hash

        if User.query.filter_by(role="admin").count() > 0:
            return jsonify({"error": "Admin already exists"}), 400

        data = request.get_json(force=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "email and password are required"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "User with this email already exists"}), 400

        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            role="admin",
        )
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id

        return jsonify({"message": "Admin created", "user": user.to_dict()}), 201

    # ------------------------------------------------------------------
    # Auth: login / logout
    # ------------------------------------------------------------------

    @app.route("/api/auth/login", methods=["POST"])
    def api_login():
        from werkzeug.security import check_password_hash

        data = request.get_json(force=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "email and password are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid credentials"}), 401

        session["user_id"] = user.id
        return jsonify({"message": "Logged in", "user": user.to_dict()})

    @app.route("/api/auth/logout", methods=["POST"])
    def api_logout():
        session.pop("user_id", None)
        return jsonify({"message": "Logged out"})

    # ------------------------------------------------------------------
    # Invites: admin creates, moderators register
    # ------------------------------------------------------------------

    @app.route("/api/invites", methods=["POST"])
    @login_required(role="admin")
    def create_invite():
        """
        Admin creates an invite for a moderator (or another admin if you want).
        Body: { "email": "...", "role": "moderator", "expires_in_hours": 48 }
        """
        data = request.get_json(force=True) or {}
        email = (data.get("email") or "").strip().lower()
        role = (data.get("role") or "moderator").strip().lower()
        expires_in_hours = int(data.get("expires_in_hours", 48))

        if role not in ("admin", "moderator"):
            return jsonify({"error": "Invalid role"}), 400

        if not email:
            return jsonify({"error": "email is required"}), 400

        token = secrets.token_urlsafe(32)

        invite = Invite(
            email=email,
            role=role,
            token=token,
        )
        if expires_in_hours > 0:
            from datetime import datetime, timedelta

            invite.expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

        db.session.add(invite)
        db.session.commit()

        base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
        if not base_url:
            invite_url = f"/register?token={token}"
        else:
            invite_url = f"{base_url}/register?token={token}"

        return jsonify({"invite": invite.to_dict(), "invite_url": invite_url}), 201

    @app.route("/api/invites/<token>", methods=["GET"])
    def get_invite(token):
        invite = Invite.query.filter_by(token=token).first()
        if not invite or not invite.is_valid():
            return jsonify({"valid": False}), 404
        return jsonify(
            {
                "valid": True,
                "email": invite.email,
                "role": invite.role,
                "expires_at": invite.expires_at.isoformat()
                if invite.expires_at
                else None,
            }
        )

    @app.route("/api/register/<token>", methods=["POST"])
    def register_with_invite(token):
        from werkzeug.security import generate_password_hash

        invite = Invite.query.filter_by(token=token).first()
        if not invite or not invite.is_valid():
            return jsonify({"error": "Invalid or expired invite"}), 400

        data = request.get_json(force=True) or {}
        password = data.get("password")

        if not password:
            return jsonify({"error": "password is required"}), 400

        email = invite.email.strip().lower()

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "User with this email already exists"}), 400

        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            role=invite.role,
        )
        invite.used = True
        db.session.add(user)
        db.session.add(invite)
        db.session.commit()

        session["user_id"] = user.id

        return jsonify({"message": "Account created", "user": user.to_dict()})

    # ------------------------------------------------------------------
    # Server management API
    # ------------------------------------------------------------------

    @app.route("/api/servers", methods=["GET"])
    @login_required()
    def list_servers():
        servers = Server.query.order_by(Server.id).all()
        result = []
        for s in servers:
            container = get_container(s.container_name)
            status = container.status if container else "missing"
            info = s.to_dict()
            info["container_status"] = status
            result.append(info)
        return jsonify(result)

    @app.route("/api/servers", methods=["POST"])
    @login_required(role="admin")
    def create_server():
        data = request.get_json(force=True) or {}

        name = data.get("name")
        world_name = data.get("world_name")
        password = data.get("password")

        if not name or not world_name or not password:
            return (
                jsonify(
                    {
                        "error": "Missing required fields: name, world_name, password",
                    }
                ),
                400,
            )

        slug = slugify(name)
        existing = Server.query.filter_by(slug=slug).first()
        if existing:
            return jsonify({"error": "Server with this name already exists"}), 400

        try:
            base_port = allocate_port_block()
        except RuntimeError as e:
            return jsonify({"error": str(e)}), 400

        container_name = f"valpanel_{slug}"

        server = Server(
            name=name,
            slug=slug,
            world_name=world_name,
            password=password,
            base_port=base_port,
            container_name=container_name,
        )
        db.session.add(server)
        db.session.commit()

        # Create and start the container
        try:
            create_valheim_container(server)
        except APIError as e:
            # Roll back DB entry if container creation fails
            db.session.delete(server)
            db.session.commit()
            return (
                jsonify(
                    {
                        "error": "Docker error while creating container",
                        "details": e.explanation,
                    }
                ),
                500,
            )

        return jsonify(server.to_dict()), 201

    @app.route("/api/servers/<int:server_id>/start", methods=["POST"])
    @login_required()
    def start_server(server_id):
        server = Server.query.get_or_404(server_id)
        container = get_container(server.container_name)
        if not container:
            # Container missing – try to recreate it
            try:
                container = create_valheim_container(server)
            except APIError as e:
                return (
                    jsonify(
                        {
                            "error": "Failed to create container",
                            "details": e.explanation,
                        }
                    ),
                    500,
                )

        if container.status != "running":
            container.start()
        return jsonify({"status": "started"})

    @app.route("/api/servers/<int:server_id>/stop", methods=["POST"])
    @login_required()
    def stop_server(server_id):
        server = Server.query.get_or_404(server_id)
        container = get_container(server.container_name)
        if not container:
            return jsonify({"error": "Container not found"}), 404
        if container.status == "running":
            container.stop()
        return jsonify({"status": "stopped"})

    @app.route("/api/servers/<int:server_id>/restart", methods=["POST"])
    @login_required()
    def restart_server(server_id):
        server = Server.query.get_or_404(server_id)
        container = get_container(server.container_name)
        if not container:
            return jsonify({"error": "Container not found"}), 404
        container.restart()
        return jsonify({"status": "restarted"})

    # ------------------------------------------------------------------
    # DELETE SERVER
    # ------------------------------------------------------------------
    @app.route("/api/servers/<int:server_id>", methods=["DELETE"])
    @login_required(role="admin")
    def delete_server(server_id):
        """
        Completely remove a Valheim server:
          - Stop & remove its Docker container
          - Delete its data directory
          - Remove DB entry
        """
        import shutil

        server = Server.query.get_or_404(server_id)

        # Remove container
        container = get_container(server.container_name)
        if container:
            app.logger.info(f"Removing container {server.container_name}")
            try:
                container.remove(force=True)
            except APIError as e:
                app.logger.error(
                    f"Failed to remove container {server.container_name}: {e.explanation}"
                )

        # Delete folder
        server_root = Path(server_data_dir(server.slug))
        if server_root.exists():
            app.logger.info(f"Deleting directory: {server_root}")
            try:
                shutil.rmtree(server_root)
            except Exception as e:
                app.logger.error(f"Failed to delete directory {server_root}: {e}")

        # Remove DB entry
        db.session.delete(server)
        db.session.commit()

        return jsonify({"status": "deleted", "server_id": server_id}), 200

    @app.route("/api/servers/<int:server_id>/logs", methods=["GET"])
    @login_required()
    def get_server_logs(server_id):
        """
        Return recent Docker logs for the given server.
        Optional `tail` query param (default 500, max 5000) controls how many lines to fetch.
        """
        tail = request.args.get("tail", default=500, type=int)
        tail = max(1, min(tail, 5000))

        server = Server.query.get_or_404(server_id)
        container = get_container(server.container_name)
        if not container:
            return jsonify({"error": "Container not found"}), 404

        try:
            logs = container.logs(tail=tail).decode("utf-8", errors="replace")
        except Exception as e:
            return jsonify({"error": f"Failed to read logs: {str(e)}"}), 500

        return jsonify({"logs": logs, "tail": tail})



    # ------------------------------------------------------------------
    # HTML pages (Jinja templates)
    # ------------------------------------------------------------------

    @app.route("/setup")
    def setup_page():
        # If admin already exists, skip to dashboard
        if User.query.filter_by(role="admin").count() > 0:
            return redirect(url_for("dashboard_page"))
        return render_template("setup_admin.html")

    @app.route("/login")
    def login_page():
        if current_user():
            return redirect(url_for("dashboard_page"))
        return render_template("login.html")

    @app.route("/dashboard")
    @login_required()
    def dashboard_page():
        return render_template("dashboard.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PANEL_PORT", "8000")))
