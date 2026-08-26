# Moving the calendar to the VPS

**The URL does not change.** `https://nasi.ibrahimabdelrahim.cloud/` and every
`.ics` under it keep working exactly as they do today. That is the whole point:
an `.ics` URL, once in someone's calendar, can never be redirected or recalled,
and a subscriber cannot be found, warned or migrated.

---

## Already done and verified (no privileges needed)

The app is on the box at `/home/personal/nasi-calendar` and the feed generator
has been tested there:

| Check | Result |
|---|---|
| Python | 3.12.3, **no dependencies** — standard library only |
| City registry validates on Linux | 33 cities, 6 regions, all IANA zones resolve |
| String table validates | 168 rows, both languages present |
| `nasi-cairo-full-5y.ics` served | 200, `text/calendar`, 2,529,771 bytes |
| Byte-identical to the committed static file | **yes** (ignoring `DTSTAMP`) |
| CRLF line endings preserved | 86,958 CRLF, **0 bare LF** |
| A city with no static file (`jakarta`) | 200 — works only here |
| Unknown city (`atlantis`) | 404, not a guess |
| Cached refetch | 2.6 ms |
| Listening address | `127.0.0.1:8971` — **not reachable from the internet** |

The Hostinger DNS hook was also round-tripped: a throwaway TXT record was
added, confirmed present alongside every existing record, then removed, leaving
the zone exactly as found. `overwrite: false` merges — **never pass true**, it
replaces the whole zone and would take the `os` record with it.

---

## The one thing that needs root

Everything below is a single paste, run once as root. Nothing standing is
granted and `sudo` keeps its password.

Two notes before you run it:

- **Change the email** on the certbot line if `borhom44@gmail.com` is not the
  address you want expiry warnings sent to.
- The vhost binds 443 to the **public IP only**. The Personal OS keeps its own
  nginx server block on `100.126.157.23:443`, so the two never share a listen
  address. That separation is structural rather than a firewall rule that could
  later be edited wrong.

```bash
set -e

# 1. the feed generator, as an unprivileged service on loopback
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
RestrictAddressFamilies=AF_INET AF_INET6

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now nasi-feeds
sleep 2
curl -sf http://127.0.0.1:8971/healthz && echo "  feed service up"

# 2. a certificate, BEFORE the domain points here -- DNS-01, so the name does
#    not need to resolve to this box yet. That is what makes the cutover
#    zero-downtime: HTTP-01 would need DNS flipped first, leaving a window
#    where the site serves an invalid certificate and Google silently stops
#    fetching every subscriber's feed.
certbot certonly --non-interactive --agree-tos \
  --manual --preferred-challenges dns \
  --manual-auth-hook    "/usr/bin/python3 /home/personal/nasi-calendar/vps/hostinger_dns.py certbot-auth" \
  --manual-cleanup-hook "/usr/bin/python3 /home/personal/nasi-calendar/vps/hostinger_dns.py certbot-cleanup" \
  -m borhom44@gmail.com \
  -d nasi.ibrahimabdelrahim.cloud

# 3. the vhost
cat >/etc/nginx/sites-available/nasi <<'CONF'
server {
    listen 186.240.155.88:80;
    server_name nasi.ibrahimabdelrahim.cloud;
    return 301 https://$host$request_uri;
}

server {
    listen 186.240.155.88:443 ssl;
    http2 on;
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
nginx -t && systemctl reload nginx
echo "  nginx reloaded"

# 4. prove it serves correctly BEFORE any DNS change, by forcing resolution
curl -sI --resolve nasi.ibrahimabdelrahim.cloud:443:186.240.155.88 \
  https://nasi.ibrahimabdelrahim.cloud/ | head -1
curl -s -o /dev/null -w "  feed: %{http_code} %{size_download} bytes\n" \
  --resolve nasi.ibrahimabdelrahim.cloud:443:186.240.155.88 \
  https://nasi.ibrahimabdelrahim.cloud/data/nasi-cairo-full-5y.ics
```

If step 4 prints `HTTP/2 200` and a feed of about 2.5 MB, the box is ready and
the domain still points at GitHub Pages. Nothing is live yet.

---

## Then the cutover

Tell me once the block above has run and I will:

1. Change `nasi` from `CNAME borhom44.github.io.` to `A 186.240.155.88`
2. Watch propagation and re-verify the site and both feeds over the real name
3. Confirm the Arabic feed is byte-identical to what subscribers had

**Rollback is one DNS change.** GitHub Pages stays configured and untouched, so
putting the CNAME back restores the old site immediately. Do not delete the
`_github-pages-challenge-borhom44` TXT record — it is what stops anyone else
claiming a subdomain of yours on GitHub Pages.

---

## After the cutover

- Flip `feed: true` for the remaining 31 cities in `data/cities.json`; they need
  no files, only the flag, and the subscribe picker will offer them.
- `docs/data/*.ics` can then be deleted from the repo — the server generates
  them and the static copies would only go stale.
- nginx access logs finally answer how many people subscribe, which GitHub
  Pages never could.
