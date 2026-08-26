#!/bin/bash
# Nasi calendar -- the one-time root install, exactly as set out in DEPLOY.md.
#
# Staged as a file rather than pasted line by line: a web terminal that drops
# one character inside a heredoc writes a subtly broken config instead of
# failing, and an nginx vhost or a systemd unit corrupted that way can be very
# hard to spot afterwards.
#
# Idempotent -- safe to re-run. Everything it touches is rewritten from source,
# and certbot leaves an existing certificate alone until it is due for renewal.
#
#   run as root:  bash /home/personal/nasi-calendar/vps/root-install.sh
#
set -uo pipefail

REPO=/home/personal/nasi-calendar
DOMAIN=nasi.ibrahimabdelrahim.cloud
PUBIP=186.240.155.88
EMAIL=borhom44@gmail.com
LOG=/tmp/nasi-deploy.log

: >"$LOG"; chmod 644 "$LOG"
exec > >(tee -a "$LOG") 2>&1

die() { echo; echo "FAILED: $*"; echo "--- see $LOG ---"; exit 1; }

echo "=== nasi deploy $(date -u +%FT%TZ) ==="
[ "$(id -u)" = 0 ] || die "must run as root"

# ---------------------------------------------------------------- 0. inputs
for f in "$REPO/vps/feed_server.py" "$REPO/vps/hostinger_dns.py" \
         "$REPO/docs/index.html" /home/personal/.hostinger_api_token; do
  [ -f "$f" ] || die "missing prerequisite: $f"
done
echo "[0/4] prerequisites present"

# ------------------------------------- 1. feed generator, unprivileged, loopback
cat >/etc/systemd/system/nasi-feeds.service <<'UNIT'
[Unit]
Description=Nasi calendar feed generator
After=network.target

[Service]
Type=simple
User=personal
Group=personal
WorkingDirectory=/home/personal/nasi-calendar
ExecStart=/usr/bin/python3 /home/personal/nasi-calendar/vps/feed_server.py --host 127.0.0.1 --port 8971
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload || die "daemon-reload"
systemctl enable --now nasi-feeds >/dev/null 2>&1 || true
systemctl restart nasi-feeds || die "could not start nasi-feeds"

ok=
for i in $(seq 1 15); do
  sleep 1
  if curl -sf http://127.0.0.1:8971/healthz >/dev/null; then ok=1; break; fi
done
if [ -z "$ok" ]; then
  echo "--- systemctl status ---"; systemctl status nasi-feeds --no-pager -l | head -30
  echo "--- journal ---";          journalctl -u nasi-feeds -n 40 --no-pager
  die "feed service did not come up on 127.0.0.1:8971"
fi
echo "[1/4] feed service up on 127.0.0.1:8971"

# ------------------------------------------------ 2. certificate, before DNS
# DNS-01, so the name does not have to resolve here yet. That is what makes the
# cutover zero-downtime: HTTP-01 would need DNS flipped first, leaving a window
# serving an invalid certificate -- and Google would silently stop fetching
# every subscriber's feed.
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
  echo "[2/4] certificate already present, leaving it alone"
else
  certbot certonly --non-interactive --agree-tos \
    --manual --preferred-challenges dns \
    --manual-auth-hook    "/usr/bin/python3 $REPO/vps/hostinger_dns.py certbot-auth" \
    --manual-cleanup-hook "/usr/bin/python3 $REPO/vps/hostinger_dns.py certbot-cleanup" \
    -m "$EMAIL" -d "$DOMAIN" || die "certbot could not issue a certificate"
  [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ] || die "certbot reported success but no cert on disk"
  echo "[2/4] certificate issued"
fi

# ------------------------------------------------------------------ 3. vhost
# 443 is bound to the PUBLIC IP only. Personal OS keeps its own server block on
# 100.126.157.23:443, so the two never share a listen address -- a structural
# separation rather than a firewall rule that could later be edited wrong.
cat >/etc/nginx/sites-available/nasi <<'CONF'
server {
    listen 186.240.155.88:80;
    server_name nasi.ibrahimabdelrahim.cloud;
    return 301 https://$host$request_uri;
}

server {
    listen 186.240.155.88:443 ssl http2;
    server_name nasi.ibrahimabdelrahim.cloud;

    ssl_certificate     /etc/letsencrypt/live/nasi.ibrahimabdelrahim.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/nasi.ibrahimabdelrahim.cloud/privkey.pem;

    root /home/personal/nasi-calendar/docs;
    index index.html;

    # Feeds are generated per request, never stored. The service is on
    # loopback, so it is reachable only through this proxy.
    location /data/ {
        proxy_pass http://127.0.0.1:8971;
        proxy_set_header Host $host;
        proxy_read_timeout 60s;
    }

    location / { try_files $uri $uri/ =404; }
}
CONF

ln -sf /etc/nginx/sites-available/nasi /etc/nginx/sites-enabled/nasi
nginx -t || die "nginx rejected the vhost"
systemctl reload nginx || die "nginx reload"
echo "[3/4] nginx reloaded"

# ---------------------------------------- 3b. let nginx reach the docroot
# nginx workers run as www-data. /home/personal is mode 750, so www-data cannot
# traverse into it and try_files returns 404 for every static file. Grant the
# traverse bit to www-data alone via ACL where available -- narrower than
# chmod o+x, which would open the path to every local user. Nothing below needs
# changing: docs/ is already 755 and its files 644.
if command -v setfacl >/dev/null 2>&1; then
  setfacl -m u:www-data:--x /home/personal || die "setfacl on /home/personal"
  echo "[3b] traverse granted to www-data alone (ACL)"
else
  chmod o+x /home/personal || die "chmod o+x /home/personal"
  echo "[3b] traverse granted via chmod o+x (acl package not installed)"
fi
sudo -u www-data test -r "$REPO/docs/index.html" || die "www-data still cannot read the docroot"
echo "     www-data can read the docroot"

# ------------------------------------------------- 3c. open 80/443 inbound
# ufw is active and has never needed public web ports -- Personal OS is
# reachable only over Tailscale. ONLY these two ports are added; no existing
# rule is removed and nothing else is touched.
if systemctl is-active --quiet ufw; then
  ufw allow 80/tcp  >/dev/null || die "ufw allow 80"
  ufw allow 443/tcp >/dev/null || die "ufw allow 443"
  echo "[3c] ufw: 80/tcp and 443/tcp allowed"
  ufw status | sed 's/^/     /'
else
  echo "[3c] ufw inactive, nothing to open"
fi

# ------------------------------- 4. prove it serves BEFORE any DNS change
for i in $(seq 1 10); do ss -ltn | grep -q "$PUBIP:443" && break; sleep 1; done
R=$(curl -sI --resolve "$DOMAIN:443:$PUBIP" "https://$DOMAIN/" | head -1 | tr -d '\r')
echo "[4/4] site:  $R"
curl -s -o /dev/null -w "      feed:  HTTP %{http_code}, %{size_download} bytes, %{time_total}s\n" \
  --resolve "$DOMAIN:443:$PUBIP" "https://$DOMAIN/data/nasi-cairo-full-5y.ics"
curl -s -o /dev/null -w "      feed:  HTTP %{http_code}, %{size_download} bytes  (english)\n" \
  --resolve "$DOMAIN:443:$PUBIP" "https://$DOMAIN/data/nasi-cairo-full-5y-en.ics"

echo
echo "=== done. DNS still points at GitHub Pages -- nothing is live yet. ==="
