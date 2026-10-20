#!/usr/bin/env bash
# Run from a reviewed clean clone on a fresh Ubuntu 24.04 VM. Never source secrets.
set -euo pipefail
task_host= task_env= task_plan=0
while (($#)); do
  case "$1" in
    --hostname) task_host="${2:?hostname required}"; shift 2 ;;
    --env-file) task_env="${2:?env file required}"; shift 2 ;;
    --plan) task_plan=1; shift ;;
    *) echo 'Usage: install.sh --hostname demo.example.org --env-file /root/bb.env [--plan]' >&2; exit 2 ;;
  esac
done
[[ "$task_host" =~ ^[A-Za-z0-9][A-Za-z0-9.-]+\.[A-Za-z]+$ ]] || { echo 'Use a DNS hostname, not a URL or IP' >&2; exit 2; }
[[ -f "$task_env" ]] || { echo 'An external env file is required' >&2; exit 2; }
task_root="$(cd "$(dirname "$0")/../.." && pwd -P)"
[[ "$task_root" != / && "$task_root" =~ ^/[A-Za-z0-9_./-]+$ && -f "$task_root/services/api/pyproject.toml" ]] || exit 2
case "$(uname -m)" in
  x86_64) task_node_arch=x64 ;;
  aarch64|arm64) task_node_arch=arm64 ;;
  *) echo 'Only Linux amd64 and arm64 are supported' >&2; exit 2 ;;
esac
if ((task_plan)); then
  printf 'Plan: Ubuntu native %s; Node 22, uv, FISCO, Watchman, private API sandboxes, Next, Caddy HTTPS for %s. No changes made.\n' "$task_node_arch" "$task_host"
  exit 0
fi
[[ "$EUID" == 0 ]] || { echo 'Run with sudo on the target VM' >&2; exit 2; }
. /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || { echo 'Validated recipe targets Ubuntu 24.04; do not run on another OS' >&2; exit 2; }
[[ ! -f "$task_root/services/api/.env" ]] || { echo 'Remove repo-local .env on the VM; use the external env file' >&2; exit 2; }
task_env="$(realpath "$task_env")"
[[ "$task_env" != "$task_root/"* ]] || { echo 'Keep the input env file outside Git checkout' >&2; exit 2; }
chmod 600 "$task_env"
task_tmp="$(mktemp -d /tmp/bb-deploy.XXXXXXXX)"
[[ "$task_tmp" == /tmp/bb-deploy.* ]] || exit 2
trap 'rm -rf -- "$task_tmp"' EXIT

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y ca-certificates curl gnupg git python3 python3-venv openssl build-essential xz-utils ufw
# Official signed Caddy stable apt repository; supports both target architectures.
curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key -o "$task_tmp/caddy.asc"
gpg --batch --yes --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg "$task_tmp/caddy.asc"
curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt -o /etc/apt/sources.list.d/caddy-stable.list
apt-get update -qq
apt-get install -y caddy

task_node=v22.23.3
task_archive="node-$task_node-linux-$task_node_arch.tar.xz"
curl -fsSL "https://nodejs.org/dist/$task_node/$task_archive" -o "$task_tmp/$task_archive"
curl -fsSL "https://nodejs.org/dist/$task_node/SHASUMS256.txt" -o "$task_tmp/SHASUMS256.txt"
(cd "$task_tmp" && grep "  $task_archive\$" SHASUMS256.txt | sha256sum -c -)
mkdir -p /opt/bursarbridge-node
tar -xJf "$task_tmp/$task_archive" --strip-components=1 -C /opt/bursarbridge-node
ln -sf /opt/bursarbridge-node/bin/node /usr/local/bin/node
ln -sf /opt/bursarbridge-node/bin/npm /usr/local/bin/npm
npm install --global --prefix /usr/local pnpm@10.33.2
python3 -m venv /opt/bursarbridge-tools
/opt/bursarbridge-tools/bin/pip install --disable-pip-version-check uv==0.12.13
ln -sf /opt/bursarbridge-tools/bin/uv /usr/local/bin/uv

id bursarbridge >/dev/null 2>&1 || useradd --system --create-home --home-dir /var/lib/bursarbridge --shell /usr/sbin/nologin bursarbridge
id bursarweb >/dev/null 2>&1 || useradd --system --home-dir /var/lib/bursarweb --create-home --shell /usr/sbin/nologin bursarweb
install -d -m 700 -o bursarbridge -g bursarbridge /var/lib/bursarbridge "$task_root/services/api/runtime"
install -d -m 700 /etc/bursarbridge
# Updates are operator maintenance: stop serving before rebuilding in place.
systemctl stop bursarbridge-api.service bursarbridge-web.service 2>/dev/null || true
chown -R bursarbridge:bursarbridge "$task_root"
chmod 755 "$task_root" /var/lib/bursarweb
chmod 700 /var/lib/bursarbridge "$task_root/services/api/runtime"
runuser -u bursarbridge -- env HOME=/var/lib/bursarbridge PATH=/usr/local/bin:/usr/bin:/bin uv sync --project "$task_root/services/api" --frozen
runuser -u bursarbridge -- env HOME=/var/lib/bursarbridge PATH=/usr/local/bin:/usr/bin:/bin npm --prefix "$task_root/contracts" ci
runuser -u bursarbridge -- env HOME=/var/lib/bursarbridge PATH=/usr/local/bin:/usr/bin:/bin npm --prefix "$task_root/contracts" run compile
runuser -u bursarbridge -- env HOME=/var/lib/bursarbridge PATH=/usr/local/bin:/usr/bin:/bin pnpm --dir "$task_root/apps/web" install --frozen-lockfile
runuser -u bursarbridge -- env HOME=/var/lib/bursarbridge PATH=/usr/local/bin:/usr/bin:/bin NEXT_PUBLIC_API_MODE=live NEXT_PUBLIC_API_URL=/bbapi NEXT_TELEMETRY_DISABLED=1 pnpm --dir "$task_root/apps/web" build
chown -R bursarweb:bursarweb "$task_root/apps/web/.next"

"$task_root/services/api/.venv/bin/python" "$task_root/infra/deploy/render.py" --hostname "$task_host" --env-file "$task_env" --root "$task_root" --output "$task_tmp/rendered"
install -m 600 "$task_tmp/rendered/api.env" /etc/bursarbridge/api.env
install -m 644 "$task_tmp/rendered/web.env" /etc/bursarbridge/web.env
for task_unit in "$task_tmp/rendered/"*.service; do
  install -m 644 "$task_unit" "/etc/systemd/system/$(basename "$task_unit")"
done
install -m 644 "$task_tmp/rendered/Caddyfile" /etc/caddy/Caddyfile
caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
systemd-analyze verify /etc/systemd/system/bursarbridge-{infra,api,web}.service

ufw allow "${SSH_PORT:-22}/tcp"
ufw allow 80/tcp
ufw allow 443/tcp
ufw default deny incoming
ufw --force enable
systemctl daemon-reload
systemctl enable --now bursarbridge-infra.service
# Keep generated node keys inaccessible to the web service account.
chmod 700 "$task_root/infra/fisco/nodes"
systemctl enable --now bursarbridge-api.service bursarbridge-web.service caddy.service
systemctl reload caddy
for task_try in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8000/api/health >/dev/null; then break; fi
  sleep 1
done
curl -fsS http://127.0.0.1:8000/api/health >/dev/null
printf 'Services started. Verify DNS/TLS and the full journey at https://%s. No cloud firewall or DNS was changed.\n' "$task_host"
