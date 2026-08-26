"""Add or remove a single DNS record through the Hostinger API.

Used as certbot's DNS-01 hook so a certificate can be issued for
nasi.ibrahimabdelrahim.cloud BEFORE the domain points at this box -- which is
what makes the cutover zero-downtime. The alternative, HTTP-01, requires the
name to already resolve here, so the site would serve an invalid certificate
between the DNS flip and the certificate landing. Google silently stops
fetching a feed whose certificate does not validate, so that window is not
cosmetic: it breaks every subscriber.

    python3 hostinger_dns.py add    _acme-challenge.nasi TXT "<value>"
    python3 hostinger_dns.py remove _acme-challenge.nasi TXT
    python3 hostinger_dns.py get

The token lives at ~/.hostinger_api_token, mode 600, and is never passed on a
command line -- an argv is visible to every process on the box.

SAFETY. Writes always use overwrite=false so the call MERGES. With true it
would replace the entire zone, taking the os record with it and cutting the
tailnet name the Personal OS answers on.
"""
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

DOMAIN = "ibrahimabdelrahim.cloud"
API = "https://developers.hostinger.com/api/dns/v1/zones/" + DOMAIN
# certbot runs its hooks as ROOT, so Path.home() would look in /root and the
# certificate request would fail with a confusing 401. The location is
# explicit, with an env override for anything that keeps it elsewhere.
TOKEN_FILE = Path(os.environ.get("HOSTINGER_TOKEN_FILE",
                                 "/home/personal/.hostinger_api_token"))


def _token():
    return TOKEN_FILE.read_text(encoding="utf-8").strip()


def _request(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + _token())
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    # Cloudflare fronts this API and rejects urllib's default agent with
    # error 1010 (browser_signature_banned). curl gets through; python does
    # not, unless it says who it is.
    req.add_header("User-Agent", "nasi-calendar/1.0 (+https://nasi.ibrahimabdelrahim.cloud)")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            body = r.read().decode()
            return r.status, (json.loads(body) if body.strip() else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]


def get_zone():
    status, body = _request("GET", API)
    if status != 200:
        raise SystemExit(f"GET failed {status}: {body}")
    return body if isinstance(body, list) else body.get("data", body)


def add(name, rtype, content, ttl=300):
    """Merge one record in. name is relative to the domain."""
    payload = {
        "overwrite": False,          # MERGE. true would replace the whole zone.
        "zone": [{
            "name": name,
            "type": rtype,
            "ttl": ttl,
            "records": [{"content": content}],
        }],
    }
    status, body = _request("PUT", API, payload)
    if status not in (200, 201, 204):
        raise SystemExit(f"add failed {status}: {body}")
    return status


def remove(name, rtype):
    payload = {"filters": [{"name": name, "type": rtype}]}
    status, body = _request("DELETE", API, payload)
    if status not in (200, 204):
        raise SystemExit(f"remove failed {status}: {body}")
    return status


def _print_zone():
    for r in get_zone() or []:
        if isinstance(r, dict):
            vals = [x.get("content") for x in r.get("records", [])] or [r.get("content")]
            print(f"  {r.get('name'):<36} {r.get('type'):<6} {vals}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "get":
        _print_zone()
    elif sys.argv[1] == "add":
        print(add(sys.argv[2], sys.argv[3], sys.argv[4]))
    elif sys.argv[1] == "remove":
        print(remove(sys.argv[2], sys.argv[3]))
    elif sys.argv[1] == "certbot-auth":
        # certbot --manual-auth-hook: name and value arrive in the environment.
        print(add("_acme-challenge." + os.environ["CERTBOT_DOMAIN"].split("." + DOMAIN)[0],
                  "TXT", os.environ["CERTBOT_VALIDATION"]))
    elif sys.argv[1] == "certbot-cleanup":
        print(remove("_acme-challenge." + os.environ["CERTBOT_DOMAIN"].split("." + DOMAIN)[0],
                     "TXT"))
    else:
        raise SystemExit(__doc__)
