#!/bin/bash
# Nasi calendar health check. Runs as root every 5 minutes via nasi-health.timer.
#
# It tests the whole chain the way a SUBSCRIBER does -- public DNS, TLS, nginx,
# the proxy hop, and the generator itself -- because each layer has its own way
# of failing while the layer below still looks healthy. systemd's
# Restart=on-failure only catches the process exiting; a wedged worker, a dead
# nginx, or a certificate that quietly failed to renew all leave the unit
# "active" and every feed unreachable.
#
# It also RECOVERS: a failing feed gets the service restarted before anyone is
# told, so the common case fixes itself and the alert only fires for something
# that actually needs a human.
#
# Alerting is opt-in and reads /etc/nasi-health.conf if it exists:
#     TELEGRAM_TOKEN=...
#     TELEGRAM_CHAT_ID=...
# Without that file it logs to the journal and does nothing else. The token is
# fed to curl through --config on stdin, never on the command line, because
# argv is world-readable via ps and that is exactly how a token leaked before.

set -uo pipefail

DOMAIN=nasi.ibrahimabdelrahim.cloud
SITE="https://$DOMAIN/"
FEED="https://$DOMAIN/data/nasi-cairo-full-5y.ics"
MIN_BYTES=1000000          # a real feed is ~2.5 MB raw; far under means broken
CERT=/etc/letsencrypt/live/$DOMAIN/fullchain.pem
CERT_WARN_DAYS=14
STATE_DIR=/var/lib/nasi-health
STATE="$STATE_DIR/state"
LAST_ALERT="$STATE_DIR/last-alert"
REALERT_SECONDS=86400      # while still broken, repeat at most once a day

mkdir -p "$STATE_DIR"
log() { logger -t nasi-health -- "$*"; echo "$(date -u +%FT%TZ) $*"; }

notify() {
  local text="$1"
  [ -r /etc/nasi-health.conf ] || { log "notify: no /etc/nasi-health.conf, logging only"; return 0; }
  # shellcheck disable=SC1091
  . /etc/nasi-health.conf
  if [ -z "${TELEGRAM_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
    log "notify: config present but incomplete, logging only"; return 0
  fi
  # the URL carries the token, so it goes in on stdin rather than in argv
  printf 'url = "https://api.telegram.org/bot%s/sendMessage"\n' "$TELEGRAM_TOKEN" \
    | curl -sS -m 20 -o /dev/null --config - \
        --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
        --data-urlencode "text=${text}" \
    && log "notify: sent" || log "notify: FAILED to send"
}

# ---------------------------------------------------------------- the checks
problems=()

check_site() {
  local code
  code=$(curl -s -o /dev/null -m 20 -w '%{http_code}' "$SITE")
  [ "$code" = "200" ] || { problems+=("site returned HTTP $code"); return 1; }
}

check_feed() {
  local body code size head
  body=$(mktemp)
  code=$(curl -s -m 60 -o "$body" -w '%{http_code}' "$FEED")
  size=$(wc -c < "$body")
  head=$(head -c 15 "$body")
  rm -f "$body"
  if [ "$code" != "200" ]; then problems+=("feed returned HTTP $code"); return 1; fi
  if [ "$size" -lt "$MIN_BYTES" ]; then problems+=("feed is only $size bytes"); return 1; fi
  # a 200 that is not actually a calendar is the failure that would otherwise
  # go unnoticed: subscribers just stop getting updates, silently
  if [ "$head" != "BEGIN:VCALENDAR" ]; then problems+=("feed is not an iCalendar file"); return 1; fi
}

check_cert() {
  [ -r "$CERT" ] || { problems+=("certificate missing at $CERT"); return 1; }
  local end left
  end=$(openssl x509 -enddate -noout -in "$CERT" | cut -d= -f2)
  left=$(( ( $(date -d "$end" +%s) - $(date +%s) ) / 86400 ))
  if [ "$left" -lt "$CERT_WARN_DAYS" ]; then
    problems+=("certificate expires in $left days -- renewal is not happening")
    return 1
  fi
  log "certificate ok, $left days left"
}

# --------------------------------------------------------------- run + repair
check_cert
if ! check_site || ! check_feed; then
  log "first pass failed: ${problems[*]}; restarting nasi-feeds"
  systemctl restart nasi-feeds
  sleep 8
  problems=()
  check_cert
  if ! check_site || ! check_feed; then
    log "still failing after restarting nasi-feeds; reloading nginx"
    systemctl reload nginx 2>/dev/null || systemctl restart nginx
    sleep 5
    problems=()
    check_cert; check_site; check_feed
  fi
fi

# ------------------------------------------------------------------ reporting
now=$(date +%s)
was=$(cat "$STATE" 2>/dev/null || echo unknown)

if [ ${#problems[@]} -eq 0 ]; then
  echo ok > "$STATE"
  if [ "$was" = "fail" ]; then
    notify "Nasi calendar is back up. $DOMAIN is serving feeds again."
    log "RECOVERED"
  else
    log "ok"
  fi
else
  echo fail > "$STATE"
  msg="Nasi calendar is DOWN: ${problems[*]}. Auto-restart did not fix it -- $DOMAIN needs a look."
  last=$(cat "$LAST_ALERT" 2>/dev/null || echo 0)
  # alert on the transition, then at most once a day while it stays broken
  if [ "$was" != "fail" ] || [ $(( now - last )) -ge "$REALERT_SECONDS" ]; then
    notify "$msg"
    echo "$now" > "$LAST_ALERT"
  fi
  log "FAIL: ${problems[*]}"
  exit 1
fi
