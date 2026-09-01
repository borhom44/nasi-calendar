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
MIN_EVENTS=1000            # a real 5-year feed has 1,826 days in it
# There was a MIN_BYTES=1000000 here, and it was the same mistake as the one in
# .github/workflows/uptime.yml: a byte floor written when a feed was 2.5 MB,
# left behind when the feeds were simplified to one entry per day (700 KB). It
# then declared a healthy feed broken and RESTARTED the server every five
# minutes, and every restart was a 502 window for whoever was fetching. Worse
# than the workflow version, which only sent email -- this one was degrading
# the thing it was supposed to protect.
#
# Size was always a proxy for "not truncated". Check that directly instead: a
# complete calendar ends with END:VCALENDAR and has events in it. Both survive
# any future change to how verbose an entry is.
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
  # Everything is measured from the file BEFORE it is deleted. The first
  # version of this fix put the new checks after the rm and every run then
  # reported "feed is truncated" against a file that no longer existed -- which
  # restarted the server just as reliably as the stale byte floor it replaced.
  local body code size head tail_ok events
  body=$(mktemp)
  code=$(curl -s -m 60 -o "$body" -w '%{http_code}' "$FEED")
  size=$(wc -c < "$body" 2>/dev/null || echo 0)
  head=$(head -c 15 "$body" 2>/dev/null)
  tail_ok=no
  tail -c 200 "$body" 2>/dev/null | grep -q "END:VCALENDAR" && tail_ok=yes
  events=$(grep -c "^BEGIN:VEVENT" "$body" 2>/dev/null)
  events=${events:-0}
  rm -f "$body"

  if [ "$code" != "200" ]; then problems+=("feed returned HTTP $code"); return 1; fi
  # a 200 that is not actually a calendar is the failure that would otherwise
  # go unnoticed: subscribers just stop getting updates, silently
  if [ "$head" != "BEGIN:VCALENDAR" ]; then
    problems+=("feed is not an iCalendar file"); return 1
  fi
  if [ "$tail_ok" != "yes" ]; then
    problems+=("feed is truncated at $size bytes"); return 1
  fi
  if [ "$events" -lt "$MIN_EVENTS" ]; then
    problems+=("feed has only $events events"); return 1
  fi
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
#
# nginx on this box is SHARED with Personal OS, which binds its own vhost to
# the Tailscale address. So the repair escalates by blame, not by desperation:
#
#   - nasi-feeds is mine alone, so restarting it is always safe.
#   - The site itself is served by nginx DIRECTLY (try_files, no proxy), while
#     a feed goes through the proxy to the generator. A 200 on the site is
#     therefore proof that nginx is healthy. If only the feed is failing, the
#     fault is downstream and reloading nginx would disturb a service shared
#     with someone else's work to fix something it is not causing.
#
# Personal OS also runs an autonomous loop overnight that git-commits on the
# server; that is the process most likely to be caught out by a needless
# restart of a shared service.

run_checks() {
  problems=()
  site_ok=1; check_site || site_ok=0
  feed_ok=1; check_feed || feed_ok=0
}

check_cert
run_checks

if [ "$site_ok" -eq 0 ] || [ "$feed_ok" -eq 0 ]; then
  log "first pass failed: ${problems[*]}"

  if [ "$feed_ok" -eq 0 ]; then
    log "restarting nasi-feeds (my service, always safe to bounce)"
    systemctl restart nasi-feeds
    sleep 8
    check_cert
    run_checks
  fi

  if [ "$site_ok" -eq 0 ]; then
    log "the static site is down too, so nginx is implicated; reloading nginx"
    systemctl reload nginx 2>/dev/null || systemctl restart nginx
    sleep 5
    check_cert
    run_checks
  elif [ "$feed_ok" -eq 0 ]; then
    log "nginx is serving the site fine, so the fault is downstream of it -- leaving shared nginx alone"
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
