#!/usr/bin/env bash
#
# Tear down the ATTEST Vultr control plane.
#
#   scripts/destroy.sh [--dry-run] [--yes]
#
# Deletes every Vultr instance tagged `attest-ctrl-plane` (there should be at
# most one -- scripts/deploy.sh is idempotent) and waits until it is gone.
# The API key is read from .env and never echoed; see deploy.sh for the key
# hygiene details. Nothing else on the account is touched.

set -euo pipefail

TAG="attest-ctrl-plane"
VULTR_API="https://api.vultr.com/v2"

err() { printf 'error: %s\n' "$*" >&2; }
log() { printf '==> %s\n' "$*"; }
die() { err "$*"; exit 1; }

DRY_RUN=0 ASSUME_YES=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --yes|-y)  ASSUME_YES=1 ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *)         die "unknown flag: $1 (try --help)" ;;
  esac
  shift
done

command -v curl >/dev/null || die "curl is required"
command -v jq   >/dev/null || die "jq is required"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
[[ -f "$ENV_FILE" ]] || die ".env not found at $ENV_FILE"

hdr_file=""
cleanup() {
  if [[ -n "$hdr_file" ]]; then rm -f "$hdr_file"; fi
}
trap cleanup EXIT
vultr() { # vultr METHOD PATH -> body; a 404 is reported as absence, not an error
  local method="$1" path="$2" out code
  out="$(curl -sS -X "$method" "${VULTR_API}${path}" -H @"$hdr_file" -w '\n%{http_code}')"
  code="${out##*$'\n'}"
  out="${out%$'\n'*}"
  if [[ "$code" == "404" ]]; then
    printf '__404__'
    return 0
  fi
  if [[ "$code" -lt 200 || "$code" -ge 300 ]]; then
    die "Vultr API $method $path -> HTTP $code: ${out:0:300}"
  fi
  printf '%s' "$out"
}

if [[ "$DRY_RUN" != "1" ]]; then
  VULTR_API_KEY="$(sed -n 's/^VULTR_API_KEY=//p' "$ENV_FILE" | tail -1)"
  VULTR_API_KEY="${VULTR_API_KEY%\"}"; VULTR_API_KEY="${VULTR_API_KEY#\"}"
  VULTR_API_KEY="${VULTR_API_KEY%\'}"; VULTR_API_KEY="${VULTR_API_KEY#\'}"
  [[ -n "$VULTR_API_KEY" ]] || die "VULTR_API_KEY is not set in .env"
  hdr_file="$(mktemp)"
  chmod 600 "$hdr_file"
  printf 'Authorization: Bearer %s\nContent-Type: application/json\n' "$VULTR_API_KEY" > "$hdr_file"
else
  log "DRY RUN -- these calls would run, nothing will be deleted:"
  printf '  GET    %s/instances?per_page=200   (find instances tagged %s)\n' "$VULTR_API" "$TAG"
  printf '  DELETE %s/instances/{id}           (for each match, after a y/N prompt)\n' "$VULTR_API"
  printf '  GET    %s/instances/{id}           (poll until 404 = gone)\n' "$VULTR_API"
  log "dry run complete (no API calls were made)"
  exit 0
fi

log "looking for instances tagged '$TAG'"
list="$(vultr GET "/instances?per_page=200")"
targets=()
while IFS= read -r line; do
  [[ -n "$line" ]] && targets+=("$line")
done < <(jq -r --arg t "$TAG" \
  '.instances[] | select((.tags // []) | index($t)) | "\(.id) \(.main_ip) \(.label)"' <<<"$list")

if [[ "${#targets[@]}" -eq 0 ]]; then
  log "nothing to destroy: no instances tagged '$TAG'"
  exit 0
fi

log "found ${#targets[@]} instance(s) tagged '$TAG':"
for t in "${targets[@]}"; do
  read -r id ip label <<<"$t"
  printf '  %s  %s  %s\n' "$id" "$ip" "$label"
done

if [[ "$ASSUME_YES" != "1" ]]; then
  read -r -p "Delete these instance(s)? This cannot be undone. [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]] || die "aborted"
fi

for t in "${targets[@]}"; do
  read -r id ip _label <<<"$t"
  log "deleting instance $id ($ip)"
  vultr DELETE "/instances/$id" >/dev/null
done

log "waiting for instances to disappear (this also stops billing)"
for t in "${targets[@]}"; do
  read -r id _ip _label <<<"$t"
  gone=0
  for ((i = 0; i < 60; i++)); do
    if [[ "$(vultr GET "/instances/$id")" == "__404__" ]]; then
      gone=1
      break
    fi
    sleep 5
  done
  [[ "$gone" == "1" ]] || err "instance $id still listed after 300s -- check the Vultr console"
done

log "destroy complete -- all instances tagged '$TAG' are gone"
