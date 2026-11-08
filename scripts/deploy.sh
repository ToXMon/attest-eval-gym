#!/usr/bin/env bash
#
# ATTEST control-plane deploy on Vultr (Track 01 demo).
#
#   scripts/deploy.sh [--dry-run] [--region R] [--plan P] [--ssh-key-id ID]
#
# What it does:
#   1. Reuses the existing Vultr instance tagged `attest-ctrl-plane`, or
#      creates one: vc2-2c-4gb, Ubuntu 24.04 x64, cloud-init installs
#      Docker + gVisor (runsc) + cloudflared and locks the firewall to SSH.
#   2. Uploads the repo (rsync), writes .env on the VM only (never printed,
#      never committed), builds the venv.
#   3. Installs systemd units: attest.service (uvicorn :8000) and
#      attest-cloudflared.service (Quick Tunnel), then prints the public
#      trycloudflare.com URL.
#
# Secrets: the Vultr API key is read from .env, passed to curl via a 0600
# header file (never in argv, never echoed, never committed). VULTR_* vars
# live only in the control-plane process on the VM; attest/sandbox.py spawns
# containers with no inherited environment, so they never reach a sandbox.
#
# Idempotent: safe to re-run; an existing tagged instance is reused and only
# the upload + service refresh happens.
#
# See also: scripts/destroy.sh (tear everything down).

set -euo pipefail

# --- constants ------------------------------------------------------------------

TAG="attest-ctrl-plane"
DEFAULT_REGION="${ATTEST_REGION:-ewr}"
DEFAULT_PLAN="${ATTEST_PLAN:-vc2-2c-4gb}"
VULTR_API="https://api.vultr.com/v2"
VM_APP_DIR="/opt/attest"
# SSH key for the control-plane VM. The identity file is explicit because the
# deploy host may have several keys loaded in the agent; IdentitiesOnly stops
# ssh from offering (and burning attempts on) the wrong ones. Override the
# path with ATTEST_SSH_KEY_FILE.
SSH_KEY_FILE="${ATTEST_SSH_KEY_FILE:-$HOME/.ssh/attest_vultr}"
SSH_OPTS=(-o IdentityFile="$SSH_KEY_FILE" -o IdentitiesOnly=yes \
          -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)

# --- helpers --------------------------------------------------------------------

err()  { printf 'error: %s\n' "$*" >&2; }
log()  { printf '==> %s\n' "$*"; }
die()  { err "$*"; exit 1; }

hdr_file=""
cleanup() {
  if [[ -n "$hdr_file" ]]; then rm -f "$hdr_file"; fi
}
trap cleanup EXIT

# Load the API key from .env WITHOUT sourcing it (never execute .env content).
load_api_key() {
  local root
  root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  [[ -f "$root/.env" ]] || die ".env not found at $root/.env (see spec: secrets live there only)"
  VULTR_API_KEY="$(sed -n 's/^VULTR_API_KEY=//p' "$root/.env" | tail -1)"
  # strip optional surrounding quotes, never echo the value
  VULTR_API_KEY="${VULTR_API_KEY%\"}"; VULTR_API_KEY="${VULTR_API_KEY#\"}"
  VULTR_API_KEY="${VULTR_API_KEY%\'}"; VULTR_API_KEY="${VULTR_API_KEY#\'}"
  if [[ -z "$VULTR_API_KEY" ]]; then
    die "VULTR_API_KEY is not set in .env"
  fi
  # Header file keeps the key out of process listings; removed by the exit trap.
  hdr_file="$(mktemp)"
  chmod 600 "$hdr_file"
  printf 'Authorization: Bearer %s\nContent-Type: application/json\n' "$VULTR_API_KEY" > "$hdr_file"
}

usage() {
  sed -n '2,12p' "$0"; exit 0
}

# --- Vultr API -------------------------------------------------------------------

vultr() { # vultr METHOD PATH [JSON_BODY] -> response body (fails on non-2xx)
  local method="$1" path="$2" body="${3-}" out code
  local args=(-sS -X "$method" "${VULTR_API}${path}" -H @"$hdr_file" -w '\n%{http_code}')
  [[ -n "$body" ]] && args+=(-d "$body")
  out="$(curl "${args[@]}")"
  code="${out##*$'\n'}"
  out="${out%$'\n'*}"
  if [[ "$code" -lt 200 || "$code" -ge 300 ]]; then
    die "Vultr API $method $path -> HTTP $code: ${out:0:300}"
  fi
  printf '%s' "$out"
}

call() { # call METHOD PATH [JSON_BODY] -- honour --dry-run
  if [[ "$DRY_RUN" == "1" ]]; then
    printf '  %s %s%s\n' "$1" "$VULTR_API" "$2"
    [[ -n "${3-}" ]] && printf '    body: %s\n' "$3"
    return 0
  fi
  vultr "$1" "$2" "${3-}"
}

# --- cloud-init -------------------------------------------------------------------

CLOUD_INIT="$(cat <<'YAML'
#cloud-config
package_update: true
packages:
  - docker.io
  - jq
  - curl
  - rsync
  - python3-venv
  - ca-certificates
  - ufw
runcmd:
  # firewall: SSH only -- the app is reachable through the Cloudflare tunnel
  - ufw default deny incoming
  - ufw allow OpenSSH
  - ufw --force enable
  # gVisor runsc runtime, registered with Docker
  - curl -fsSL https://storage.googleapis.com/gvisor/releases/release/latest/x86_64/runsc -o /usr/local/bin/runsc
  - chmod 755 /usr/local/bin/runsc
  - runsc install
  - systemctl restart docker
  # Cloudflare tunnel client
  - curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
  - chmod 755 /usr/local/bin/cloudflared
YAML
)"

base64_cloud_init() { base64 <<<"$CLOUD_INIT" | tr -d '\n'; }

# --- instance lifecycle ------------------------------------------------------------

find_instance() { # -> "id ip status power", or empty when none exists
  local list json
  list="$(call GET "/instances?per_page=200")"
  json="$(jq -r --arg t "$TAG" \
    '.instances[] | select((.tags // []) | index($t)) |
     "\(.id) \(.main_ip) \(.status) \(.power_status)"' <<<"$list" | head -1)"
  [[ -n "$json" ]] && printf '%s' "$json"
  return 0
}

wait_active() { # wait_active INSTANCE_ID -> prints IP
  local id="$1" row ip
  for ((i = 0; i < 60; i++)); do
    row="$(vultr GET "/instances/$id")"
    if [[ "$(jq -r '.instance.status' <<<"$row")" == "active" ]] \
       && [[ "$(jq -r '.instance.power_status' <<<"$row")" == "running" ]]; then
      ip="$(jq -r '.instance.main_ip' <<<"$row")"
      [[ -n "$ip" && "$ip" != "null" ]] && { printf '%s' "$ip"; return 0; }
    fi
    sleep 5
  done
  die "instance $id did not become active within 300s"
}

wait_ssh() { # wait_ssh IP
  local ip="$1"
  for ((i = 0; i < 30; i++)); do
    if ssh "${SSH_OPTS[@]}" "root@$ip" true 2>/dev/null; then return 0; fi
    sleep 4
  done
  die "could not SSH to $ip (key: $SSH_KEY_FILE; override with ATTEST_SSH_KEY_FILE)"
}

# $VM_IP must expand client side -- it IS the target host.
# shellcheck disable=SC2029
vm() { ssh "${SSH_OPTS[@]}" "root@$VM_IP" "$@"; }

rsync_ssh() { # the SSH_OPTS as one string for rsync's -e flag
  local cmd="ssh" o
  for o in "${SSH_OPTS[@]}"; do
    cmd="$cmd '$o'"
  done
  printf '%s' "$cmd"
}

# --- main ---------------------------------------------------------------------------

DRY_RUN=0 REGION="$DEFAULT_REGION" PLAN="$DEFAULT_PLAN" SSH_KEY_ID="${ATTEST_SSH_KEY_ID:-}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)    DRY_RUN=1 ;;
    --region)     REGION="${2:?}"; shift ;;
    --plan)       PLAN="${2:?}"; shift ;;
    --ssh-key-id) SSH_KEY_ID="${2:?}"; shift ;;
    -h|--help)    usage ;;
    *)            die "unknown flag: $1 (try --help)" ;;
  esac
  shift
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

command -v curl >/dev/null || die "curl is required"
command -v jq   >/dev/null || die "jq is required"
command -v rsync >/dev/null || die "rsync is required"

if [[ "$DRY_RUN" != "1" ]]; then
  [[ -f "$SSH_KEY_FILE" ]] \
    || die "SSH key '$SSH_KEY_FILE' not found (set ATTEST_SSH_KEY_FILE to override)"
fi

if [[ "$DRY_RUN" == "1" ]]; then
  log "DRY RUN -- printing API calls, nothing will be executed"
  [[ -f .env ]] || log "note: .env not found yet (fine for a dry run)"
else
  load_api_key
fi

# 1. Idempotency: reuse the tagged instance if it exists.
log "looking for an existing instance tagged '$TAG'"
row=""
if [[ "$DRY_RUN" == "1" ]]; then
  printf '  GET  %s/instances?per_page=200   (reuse check: instance tagged %s)\n' "$VULTR_API" "$TAG"
else
  row="$(find_instance)"
fi
if [[ -n "$row" ]]; then
  read -r VM_ID VM_IP _st _pw <<<"$row"
  log "reusing instance $VM_ID ($VM_IP)"
else
  if [[ "$DRY_RUN" == "1" ]]; then
    log "cannot check for an existing instance in dry-run; assuming none -- these calls would follow:"
    printf '  GET  %s/os?per_page=500    (resolve "Ubuntu 24.04 x64" os_id at runtime)\n' "$VULTR_API"
    printf '  GET  %s/ssh-keys           (resolve ssh_key_id at runtime)\n' "$VULTR_API"
    body="$(jq -n \
      --arg region "$REGION" --arg plan "$PLAN" \
      --arg label "$TAG" --arg tag "$TAG" \
      '{region:$region, plan:$plan, os_id:"<resolved at runtime>", label:$label, tags:[$tag],
        sshkey_id:["<resolved at runtime>"], user_data:"<base64 of the cloud-init below>",
        backups:"disabled", enable_ipv6:true}')"
    call POST /instances "$body"
    printf '  GET  %s/instances/{id}     (poll until status=active)\n' "$VULTR_API"
    echo
    log "cloud-init that would be base64'd into user_data:"
    printf '%s\n' "$CLOUD_INIT" | sed 's/^/    /'
    VM_ID="<new-instance-id>" VM_IP="<instance-ip>"
  else
    log "no instance tagged '$TAG' -- creating one"

    # Resolve the OS id for Ubuntu 24.04 x64 and the SSH key to attach.
    os_json="$(vultr GET "/os?per_page=500")"
    OS_ID="$(jq -r '.os[] | select(.name | test("^Ubuntu 24\\.04.*x64$")) | .id' <<<"$os_json" | head -1)"
    [[ -n "$OS_ID" ]] || die "could not resolve an Ubuntu 24.04 x64 OS id from /v2/os"
    if [[ -z "$SSH_KEY_ID" ]]; then
      SSH_KEY_ID="$(vultr GET "/ssh-keys" | jq -r '.ssh_keys[0].id // empty')"
      [[ -n "$SSH_KEY_ID" ]] || die "no SSH key on the Vultr account (add one, or pass --ssh-key-id)"
    fi
    log "os_id=$OS_ID ssh_key_id=$SSH_KEY_ID region=$REGION plan=$PLAN"

    body="$(jq -n \
      --arg region "$REGION" --arg plan "$PLAN" --argjson os "$OS_ID" \
      --arg label "$TAG" --arg tag "$TAG" --arg ssh "$SSH_KEY_ID" \
      --arg ud "$(base64_cloud_init)" \
      '{region:$region, plan:$plan, os_id:$os, label:$label, tags:[$tag],
        sshkey_id:[$ssh], user_data:$ud, backups:"disabled", enable_ipv6:true}')"
    created="$(vultr POST /instances "$body")"
    VM_ID="$(jq -r '.instance.id' <<<"$created")"
    log "created instance $VM_ID -- waiting for it to become active"
    VM_IP="$(wait_active "$VM_ID")"
    log "instance active at $VM_IP"
  fi
fi

# 2. Upload the repo and write .env on the VM only.
log "uploading repo to $VM_IP:$VM_APP_DIR (rsync)"
if [[ "$DRY_RUN" != "1" ]]; then
  wait_ssh "$VM_IP"
  vm "mkdir -p $VM_APP_DIR"
  rsync -az --delete -e "$(rsync_ssh)" \
    --exclude .git --exclude .venv --exclude runs --exclude __pycache__ \
    --exclude '*.pyc' --exclude .env --exclude '*.db' --exclude .agents \
    ./ "root@$VM_IP:$VM_APP_DIR/"
  # .env is copied, never printed, never logged.
  scp -q "${SSH_OPTS[@]}" .env "root@$VM_IP:$VM_APP_DIR/.env"
  vm "chmod 600 $VM_APP_DIR/.env"
  log "wrote $VM_APP_DIR/.env on the VM (contents not displayed)"

  # 3. Environment + systemd services.
  log "building venv and installing services"
  vm "cd $VM_APP_DIR && python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt"
else
  printf '  rsync -az --delete ./ root@%s:%s/ (excludes: .git .venv runs __pycache__ .env *.db .agents)\n' "$VM_IP" "$VM_APP_DIR"
  printf '  scp .env -> root@%s:%s/.env  (chmod 600; contents never displayed)\n' "$VM_IP" "$VM_APP_DIR"
  printf '  ssh: python3 -m venv .venv && pip install -r requirements.txt\n'
fi

ATTEST_UNIT="[Unit]
Description=ATTEST control plane (uvicorn)
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=$VM_APP_DIR
EnvironmentFile=$VM_APP_DIR/.env
ExecStart=$VM_APP_DIR/.venv/bin/python -m uvicorn attest.server:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target"

CLOUDFLARED_UNIT="[Unit]
Description=ATTEST Cloudflare Quick Tunnel
After=attest.service
Wants=attest.service

[Service]
ExecStart=/usr/local/bin/cloudflared tunnel --url http://127.0.0.1:8000 --no-autoupdate
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target"

if [[ "$DRY_RUN" != "1" ]]; then
  log "installing systemd units (attest + attest-cloudflared)"
  printf '%s' "$ATTEST_UNIT"     | vm "cat > /etc/systemd/system/attest.service"
  printf '%s' "$CLOUDFLARED_UNIT" | vm "cat > /etc/systemd/system/attest-cloudflared.service"
  vm "systemctl daemon-reload && systemctl enable --now attest.service"

  log "waiting for uvicorn on :8000"
  for ((i = 0; i < 30; i++)); do
    vm "curl -sf http://127.0.0.1:8000/api/health >/dev/null" && break
    sleep 2
  done

  log "starting Cloudflare Quick Tunnel"
  vm "systemctl enable --now attest-cloudflared.service"
  TUNNEL_URL=""
  for ((i = 0; i < 30; i++)); do
    TUNNEL_URL="$(vm "journalctl -u attest-cloudflared -o cat 2>/dev/null | grep -oE 'https://[a-zA-Z0-9-]+\\.trycloudflare\\.com' | head -1 || true")"
    [[ -n "$TUNNEL_URL" ]] && break
    sleep 2
  done
  [[ -n "$TUNNEL_URL" ]] || die "tunnel started but no URL appeared in the journal yet; check: ssh root@$VM_IP journalctl -u attest-cloudflared"

  echo
  log "deploy complete"
  printf '  instance      : %s (%s)\n' "$VM_ID" "$VM_IP"
  printf '  ssh           : ssh root@%s\n' "$VM_IP"
  printf '  public URL    : %s\n' "$TUNNEL_URL"
  printf '  note          : Quick Tunnel URLs are ephemeral (they change if the\n'
  printf '                  service restarts); scripts/destroy.sh tears it all down.\n'
else
  printf '  systemd units : attest.service (uvicorn 127.0.0.1:8000, EnvironmentFile=.env)\n'
  printf '                  attest-cloudflared.service (cloudflared tunnel --url http://127.0.0.1:8000)\n'
  printf '  final step    : print the https://<random>.trycloudflare.com URL from the tunnel journal\n'
  log "dry run complete (no API calls were made, nothing was provisioned)"
fi
