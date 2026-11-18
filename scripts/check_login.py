#!/usr/bin/env python3
"""Smoke-check login against a running server (includes CSRF)."""

from __future__ import annotations

import re
import sys
import urllib.parse
import urllib.request
import http.cookiejar

base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5303"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_url = f"{base}/login"
html = opener.open(login_url).read().decode()
m = re.search(r'name="csrf_token" value="([^"]+)"', html)
if not m:
    raise SystemExit("No CSRF token found — is this our app?")
token = m.group(1)

data = urllib.parse.urlencode(
    {
        "csrf_token": token,
        "username": "admin",
        "password": "admin123",
    }
).encode()
req = urllib.request.Request(login_url, data=data, method="POST")
try:
    resp = opener.open(req)
    final = resp.geturl()
    body = resp.read().decode()
    print("status", getattr(resp, "status", 200), "url", final)
except urllib.error.HTTPError as e:
    print("http_error", e.code, e.read()[:300])
    raise SystemExit(1)

dash = opener.open(f"{base}/").read().decode()
ok = "CPU" in dash and "Sign in" not in dash
print("dashboard_ok", ok)
if not ok:
    raise SystemExit(1)
print("login_works admin/admin123 against", base)
