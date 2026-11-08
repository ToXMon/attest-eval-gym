#!/usr/bin/env bash
# Fresh Vultr control-plane deployment. --dry-run is strictly offline.
set -euo pipefail
TAG=attest-ctrl-plane
VULTR_API=https://api.vultr.com/v2
VM_APP_DIR=/opt/attest
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSH_KEY_FILE="${ATTEST_SSH_KEY_FILE:-$HOME/.ssh/attest_vultr}"
SSH_KEY_ID="${ATTEST_SSH_KEY_ID:-}"
EXPECTED_EMAIL="${ATTEST_EXPECTED_ACCOUNT_EMAIL-contact@bullynothub.com}"
REGION="${ATTEST_REGION:-ewr}"
PLAN="${ATTEST_PLAN:-vc2-2c-4gb}"
DRY_RUN=0
OPEN_PUBLIC=0
REUSE_ID=""
hdr_file=""
inference_file=""
die() { printf 'error: %s\n' "$*" >&2; exit 1; }
log() { printf '==> %s\n' "$*"; }
cleanup() {
  [[ -z "$hdr_file" ]] || rm -f "$hdr_file"
  [[ -z "$inference_file" ]] || rm -f "$inference_file"
  return 0
}
trap cleanup EXIT
SSH_OPTS=(-o "IdentityFile=$SSH_KEY_FILE" -o IdentitiesOnly=yes
          -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)
# Source allowlist plus state exclusions. No local database or run is uploaded.
EXCLUDES=(.git .venv .env '.env.*' .agents runs quarantine screenshots
          '*.db' '*.db-*' '*.sqlite*' '__pycache__' '*.pyc' '*cache*'
          '*.png' '*.jpg' '*.jpeg' '*.webp' '*.gif' '*.tmp' '*.temp' '*.swp'
          '*.log' '.DS_Store' '*.pem' '*.key' 'id_*')
RSYNC_ARGS=(-az --delete --no-links)
for pattern in "${EXCLUDES[@]}"; do RSYNC_ARGS+=(--exclude "$pattern"); done
RSYNC_ARGS+=(--include /attest/ --include '/attest/***'
             --include /scripts/ --include '/scripts/***'
             --include /requirements.txt --exclude '*')

vultr() {
  local method="$1" path="$2" body="${3-}" out code
  local args=(-fsS --connect-timeout 10 --max-time 60 -X "$method"
              "$VULTR_API$path" -H "@$hdr_file" -w $'\n%{http_code}')
  [[ -z "$body" ]] || args+=(-d "$body")
  out="$(curl "${args[@]}")" || die "Vultr request failed (response suppressed)"
  code="${out##*$'\n'}"
  [[ "$code" =~ ^2[0-9][0-9]$ ]] || die "Vultr request failed"
  printf '%s' "${out%$'\n'*}"
}
verify_expected_account() {
  [[ "${EXPECTED_EMAIL:-}" == "contact@bullynothub.com" ]] \
    || die "expected account must be contact@bullynothub.com; empty or different values are forbidden"
}
# Both requests use the same immutable header file/current key.
preflight() {
  local account key remote_public local_public
  verify_expected_account
  [[ -n "$SSH_KEY_ID" && "$SSH_KEY_ID" =~ ^[a-zA-Z0-9-]+$ ]] || die "explicit --ssh-key-id is required"
  [[ -f "$SSH_KEY_FILE" ]] || die "ATTEST_SSH_KEY_FILE is missing"
  account="$(vultr GET /account)"
  jq -e --arg expected "$EXPECTED_EMAIL" '.account.email == $expected' >/dev/null <<<"$account" \
    || die "account email missing or mismatched; required contact@bullynothub.com"
  key="$(vultr GET "/ssh-keys/$SSH_KEY_ID")"
  [[ "$(jq -r '.ssh_key.id' <<<"$key")" == "$SSH_KEY_ID" ]] || die "SSH key ID is not in the current account"
  remote_public="$(jq -er '.ssh_key.ssh_key' <<<"$key" | awk '{print $1 " " $2}')"
  # BatchMode prevents an encrypted private key from hanging unattended.
  local_public="$(ssh-keygen -y -P '' -f "$SSH_KEY_FILE" 2>/dev/null | awk '{print $1 " " $2}')" || die "cannot derive public key (use an unencrypted dedicated deploy key)"
  [[ -n "$local_public" && "$local_public" == "$remote_public" ]] || die "SSH public key mismatch"
}
# shellcheck disable=SC2029
vm() { ssh "${SSH_OPTS[@]}" "root@$VM_IP" "$@"; }
rsync_ssh() {
  local arg
  printf 'ssh'
  for arg in "${SSH_OPTS[@]}"; do printf ' %q' "$arg"; done
}
wait_health() {
  local i status
  for ((i=0; i<30; i++)); do
    status="$(vm "curl -fsS --max-time 5 http://127.0.0.1:8000/api/health" 2>/dev/null)" || status=""
    if jq -e '.ok == true and .runtime == "runsc"' >/dev/null 2>&1 <<<"$status"; then return 0; fi
    sleep 2
  done
  die "local health/runtime check failed; tunnel remains stopped"
}
verify_bootstrap() {
  vm "timeout 900 cloud-init status --wait --long" >/dev/null || die "cloud-init failed"
  vm "cloud-init status --format json" | jq -e '.status == "done"' >/dev/null || die "cloud-init is not done"
  vm "docker info --format '{{json .Runtimes}}'" | jq -e 'has("runsc")' >/dev/null || die "Docker does not advertise runsc"
}
public_health() {
  [[ "$1" =~ ^https://[a-zA-Z0-9-]+\.trycloudflare\.com$ ]] || return 1
  curl -fsS --max-time 10 "$1/api/health" | jq -e '.ok == true and .runtime == "runsc"' >/dev/null
}
verify_reuse() {
  local matches="$1" detail
  [[ -n "$REUSE_ID" && "$REUSE_ID" =~ ^[a-zA-Z0-9-]+$ ]] || die "existing tagged instance requires explicit --reuse-instance-id"
  [[ "$(jq length <<<"$matches")" == 1 ]] || die "ambiguous tagged instances"
  [[ "$(jq -r '.[0].id' <<<"$matches")" == "$REUSE_ID" ]] || die "reuse ID not owned by current account/tag"
  detail="$(vultr GET "/instances/$REUSE_ID")"
  [[ "$(jq -r '.instance.id' <<<"$detail")" == "$REUSE_ID" ]] || die "fresh instance ownership verification failed"
  [[ "$(jq -r '.instance.main_ip' <<<"$detail")" == "$(jq -r '.[0].main_ip' <<<"$matches")" ]] || die "instance IP mismatch"
  jq -e --arg t "$TAG" '(.instance.tags // []) | index($t) != null' >/dev/null <<<"$detail" || die "instance tag mismatch"
}
verify_seed() {
  local status
  status="$(vm "curl -fsS --max-time 5 http://127.0.0.1:8000/api/leaderboard")"
  jq -e '.rows | length >= 6' >/dev/null <<<"$status" || die "six baseline leaderboard rows required before public tunnel"
  # Verify loaded records have valid chains in the exact deployed ledger.
  vm "cd /opt/attest && ATTEST_DB=/var/lib/attest/attest.db ATTEST_RUNS_DIR=/var/lib/attest/runs .venv/bin/python -c 'from attest.server import RUNS, LEDGER; assert len(RUNS) >= 6; assert all(r.chain_valid and LEDGER.verify(r.run_id) for r in RUNS.values())'"
}
CLOUD_INIT="$(cat <<'YAML'
#cloud-config
package_update: true
packages: [docker.io, jq, curl, rsync, python3-venv, ca-certificates, ufw]
runcmd:
  - ufw default deny incoming
  - ufw allow OpenSSH
  - ufw --force enable
  - curl -fsSL https://storage.googleapis.com/gvisor/releases/release/latest/x86_64/runsc -o /usr/local/bin/runsc
  - chmod 755 /usr/local/bin/runsc
  - runsc install
  - systemctl restart docker
  - curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
  - chmod 755 /usr/local/bin/cloudflared
YAML
)"
main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run) DRY_RUN=1 ;;
      --open-public) OPEN_PUBLIC=1 ;;
      --reuse-instance-id) REUSE_ID="${2:?}"; shift ;;
      --ssh-key-id) SSH_KEY_ID="${2:?}"; shift ;;
      --region) REGION="${2:?}"; shift ;;
      --plan) PLAN="${2:?}"; shift ;;
      --help|-h)
        printf '%s\n' 'deploy.sh [--dry-run] --ssh-key-id ID [--reuse-instance-id ID] [--open-public]'
        return ;;
      *) die "unknown option" ;;
    esac
    shift
  done
  cd "$REPO_ROOT"
  verify_expected_account
  if [[ "$DRY_RUN" == 1 ]]; then
    log "OFFLINE manifest: no credentials read, no API/SSH/inference calls"
    printf '%s\n' 'Preflight: GET /v2/account must return email exactly contact@bullynothub.com (mandatory); explicit SSH ID membership; derive and match SSH public key.'
    printf '%s\n' 'Reuse: explicit instance ID must match fresh current-account list AND detail; ambiguous tags refused.'
    printf 'Exclusions: %s\n' "${EXCLUDES[*]}"
    # rsync locally lists only paths, never file contents or secret values.
    rsync "${RSYNC_ARGS[@]}" --dry-run --out-format='%n' ./ /tmp/attest-deploy-manifest/
    printf '%s\n' 'Upload: allowlisted source only; inference key via separate 0600 file; compute key never uploaded.'
    printf '%s\n' 'Gates: cloud-init done; Docker runsc; actual sandbox; loopback health; manual seed verification; HTTPS public health.'
    manual_seed
    return
  fi
  for cmd in curl jq rsync ssh ssh-keygen python3; do command -v "$cmd" >/dev/null || die "$cmd is required"; done
  [[ -n "$SSH_KEY_ID" ]] || die "explicit --ssh-key-id is required"
  [[ -n "${VULTR_API_KEY:-}" && -n "${VULTR_INFERENCE_API_KEY:-}" ]] || die "provide compute and inference keys in caller environment; .env is never read"
  umask 077
  hdr_file="$(mktemp)"
  printf 'Authorization: Bearer %s\nContent-Type: application/json\n' "$VULTR_API_KEY" >"$hdr_file"
  export -n VULTR_INFERENCE_API_KEY
  unset VULTR_API_KEY
  preflight
  local list matches os_id created body i row
  list="$(vultr GET '/instances?per_page=200')"
  # Refuse truncated inventories rather than guessing ownership.
  [[ "$(jq -r '.meta.links.next // empty' <<<"$list")" == "" ]] || die "paginated inventory requires manual review"
  matches="$(jq -c --arg tag "$TAG" '[.instances[] | select((.tags // []) | index($tag))]' <<<"$list")"
  if [[ "$(jq length <<<"$matches")" != 0 ]]; then
    verify_reuse "$matches"
    VM_ID="$REUSE_ID"
  else
    [[ -z "$REUSE_ID" ]] || die "reuse ID not found in current account"
    os_id="$(vultr GET '/os?per_page=500' | jq -er '[.os[] | select(.name | test("^Ubuntu 24\\.04.*x64$"))][0].id')"
    body="$(jq -n --arg r "$REGION" --arg p "$PLAN" --arg t "$TAG" --arg k "$SSH_KEY_ID" --argjson os "$os_id" --arg ud "$(printf '%s' "$CLOUD_INIT" | base64 | tr -d '\n')" '{region:$r,plan:$p,label:$t,tags:[$t],sshkey_id:[$k],os_id:$os,user_data:$ud,backups:"disabled"}')"
    created="$(vultr POST /instances "$body")"
    VM_ID="$(jq -er '.instance.id' <<<"$created")"
  fi
  VM_IP=""
  for ((i=0; i<60; i++)); do
    row="$(vultr GET "/instances/$VM_ID")"
    if jq -e '.instance.status == "active" and .instance.power_status == "running"' >/dev/null <<<"$row"; then
      VM_IP="$(jq -er '.instance.main_ip' <<<"$row")"; break
    fi
    sleep 5
  done
  [[ "$VM_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "instance readiness/IP failed"
  for ((i=0; i<30; i++)); do
    if vm true 2>/dev/null; then break; fi
    sleep 4
  done
  vm "systemctl disable --now attest-cloudflared.service 2>/dev/null || { test ! -f /etc/systemd/system/attest-cloudflared.service; }" || die "could not stop existing tunnel"
  verify_bootstrap
  # Stop any old tunnel before code/secret changes and all subsequent checks.
  vm "systemctl stop attest-cloudflared.service 2>/dev/null || true; mkdir -p /opt/attest /etc/attest /var/lib/attest/runs; chmod 700 /etc/attest /var/lib/attest"
  rsync "${RSYNC_ARGS[@]}" -e "$(rsync_ssh)" ./ "root@$VM_IP:$VM_APP_DIR/"
  inference_file="$(mktemp)"
  # Validate a single opaque value before writing a systemd EnvironmentFile.
  [[ "$VULTR_INFERENCE_API_KEY" =~ ^[a-zA-Z0-9._:/+=-]+$ ]] || die "unsupported inference key encoding"
  printf 'VULTR_INFERENCE_API_KEY=%s\n' "$VULTR_INFERENCE_API_KEY" >"$inference_file"
  vm "umask 077; cat > /etc/attest/inference.env" <"$inference_file"
  vm "test ! -e /opt/attest/.env" || die "legacy remote .env requires manual removal/rotation before deployment"
  vm "cd /opt/attest && python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt"
  vm "docker image inspect python:3.12-slim >/dev/null 2>&1 || docker pull python:3.12-slim >/dev/null"
  vm "cd /opt/attest && REQUIRE_GVISOR=1 .venv/bin/python -c 'from attest.sandbox import run_code; r=run_code(\"print(123)\"); assert r.runtime == \"runsc\" and r.ok and \"123\" in r.stdout'"
  cat <<'UNIT' | vm "cat > /etc/systemd/system/attest.service"
[Unit]
Description=ATTEST control plane
After=network-online.target docker.service
Requires=docker.service
[Service]
WorkingDirectory=/opt/attest
EnvironmentFile=/etc/attest/inference.env
Environment=ATTEST_DB=/var/lib/attest/attest.db
Environment=ATTEST_RUNS_DIR=/var/lib/attest/runs
Environment=REQUIRE_GVISOR=1
Environment=ATTEST_TRUST_LOCAL_TUNNEL=1
UnsetEnvironment=VULTR_API_KEY
ExecStart=/opt/attest/.venv/bin/python -m uvicorn attest.server:app --host 127.0.0.1 --port 8000 --no-proxy-headers --workers 1
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
ProtectSystem=full
ProtectHome=true
UMask=0077
[Install]
WantedBy=multi-user.target
UNIT
  cat <<'UNIT' | vm "cat > /etc/systemd/system/attest-cloudflared.service"
[Unit]
Description=ATTEST public tunnel
After=attest.service
Requires=attest.service
[Service]
ExecStart=/usr/local/bin/cloudflared tunnel --url http://127.0.0.1:8000 --no-autoupdate
Restart=on-failure
RestartSec=5
[Install]
WantedBy=multi-user.target
UNIT
  vm "systemctl daemon-reload && systemctl enable attest.service && systemctl restart attest.service"
  wait_health
  manual_seed
  if [[ "$OPEN_PUBLIC" != 1 ]]; then
    log "Private service ready. Tunnel remains stopped until manual seed and --open-public verification."
    return
  fi
  verify_seed
  local since tunnel=""
  since="$(vm "date +%s")"
  vm "systemctl start attest-cloudflared.service"
  for ((i=0; i<30; i++)); do
    tunnel="$(vm "journalctl -u attest-cloudflared --since=@$since -o cat --no-pager" | grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' | head -1 || true)"
    if [[ -n "$tunnel" ]] && public_health "$tunnel"; then
      printf 'Deploy verified: %s\n' "$tunnel"; return
    fi
    sleep 2
  done
  vm "systemctl stop attest-cloudflared.service"
  die "HTTPS tunnel health failed"
}
manual_seed() {
  printf '%s\n' 'Manual post-deploy step (paid, NOT run by deploy):'
  printf '%s\n' '  systemd-run --wait --pipe --collect -p WorkingDirectory=/opt/attest -p EnvironmentFile=/etc/attest/inference.env -p Environment=ATTEST_DB=/var/lib/attest/attest.db -p Environment=ATTEST_RUNS_DIR=/var/lib/attest/runs -p Environment=REQUIRE_GVISOR=1 /opt/attest/.venv/bin/python /opt/attest/scripts/seed_baselines.py'
  printf '%s\n' 'Then restart attest.service to load records. Re-run deploy with explicit --reuse-instance-id and --open-public; seed records and chains must verify before the tunnel starts.'
}
# Sourcing permits offline unit tests to replace API/SSH functions.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi
