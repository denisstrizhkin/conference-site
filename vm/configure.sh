#!/bin/sh
# This script runs inside the Alpine chroot during image build.
# Environment variables injected by the workflow (via sudo -E + --script-chroot):
#   ADMIN_PASSWORD_HASH  – pre-computed bcrypt hash of the admin password
#                          consumed by the default_admin_user alembic migration
#
# settings.toml is already present at /app/settings.toml, placed there by
# the rootfs skeleton step in the workflow (from GitHub Secrets).

set -eu

# ---------------------------------------------------------------------------
# Setup environment
# ---------------------------------------------------------------------------
export HOME=/root
APP_DIR=/app

# ---------------------------------------------------------------------------
# Install uv
# ---------------------------------------------------------------------------
export UV_INSTALL_DIR="/usr/local/bin"
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="/usr/local/bin:$PATH"

# ---------------------------------------------------------------------------
# Sync Python dependencies.
# Include dev group so alembic (a dev dependency) is available for migrations.
# ---------------------------------------------------------------------------
cd "$APP_DIR"
uv sync --frozen
uv cache clean

# ---------------------------------------------------------------------------
# Run Alembic migrations (includes admin user migration).
# ADMIN_PASSWORD_HASH is consumed by deac2e879b0d_default_admin_user.py
# ---------------------------------------------------------------------------
uv run alembic upgrade head

# ---------------------------------------------------------------------------
# Install the app as an OpenRC service
# ---------------------------------------------------------------------------
cat > /etc/init.d/conference-site <<'SERVICE'
#!/sbin/openrc-run

name="conference-site"
description="Conference site FastAPI application"
command="/app/.venv/bin/fastapi"
command_args="run /app/src/main.py --port 80 --host 0.0.0.0"
command_background=true
pidfile="/run/${RC_SVCNAME}.pid"
output_log="/var/log/${RC_SVCNAME}.log"
error_log="/var/log/${RC_SVCNAME}.err"
directory="/app"

depend() {
    need net
    after firewall
}
SERVICE

chmod +x /etc/init.d/conference-site
rc-update add conference-site default
# ---------------------------------------------------------------------------
# Enable SSH
# ---------------------------------------------------------------------------
rc-update add sshd default

# Allow root login with password (convenient for initial setup/debugging)
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Set root password if ROOT_PASSWORD is provided
if [ -n "${ROOT_PASSWORD:-}" ]; then
    echo "root:$ROOT_PASSWORD" | chpasswd
fi

# ---------------------------------------------------------------------------
# Final Cleanup
# ---------------------------------------------------------------------------
# Remove the uv cache and any accidental runner home directory inherited from host
rm -rf /root/.cache/uv
rm -rf /home/runner
