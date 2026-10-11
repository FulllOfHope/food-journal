#!/usr/bin/env python3
"""Mess Ledger on your phone, over your own Wi-Fi.

Installable: it is a PWA, so "Add to Home Screen" gives a standalone
app with its own icon, no browser chrome, and an offline shell. The same
history file as the desktop app, so a tap on the phone shows up on the
laptop instantly and the other way round.

Guard: a shared token. Anyone who has the URL can open the page, so the
token is generated once, stored with your data, and printed in the URL
at startup. Everything else about the LAN is unchanged.

Same caveat as ever: never expose this port to the internet. It speaks
plain HTTP and expects to be reached only from your own network.
"""
import hashlib
import hmac
import html
import json
import os
import secrets
import socket
import sys
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meal_common as mc

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8137
WEB_DIR = Path(__file__).resolve().parent / "web"
COOKIE = "ml_session"
SESSION_MAX = 60 * 60 * 24 * 30  # 30 days

TINT = "#b3402e"      # the one accent: stamp red
PAPER = "#f4f1ea"


def secret():
    """A per-install token, created once, kept beside your history."""
    mc.ensure_dirs()
    path = mc.DATA_DIR / "lan_token"
    try:
        tok = path.read_text().strip()
        if tok:
            return tok
    except OSError:
        pass
    tok = secrets.token_urlsafe(18)
    try:
        path.write_text(tok)
        os.chmod(path, 0o600)
    except OSError:
        pass
    return tok


TOKEN = secret()


def _hash(value):
    return hmac.new(TOKEN.encode(), value.encode(), hashlib.sha256).hexdigest()


def authorised(handler):
    """Cookie first, so the URL can drop the key once it is set."""
    raw = handler.headers.get("Cookie", "")
    for part in raw.split(";"):
        name, _, val = part.strip().partition("=")
        if name == COOKIE and hmac.compare_digest(val, _hash("session")):
            return True
    return False


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1,
  viewport-fit=cover">
<title>Mess Ledger</title>
<link rel="manifest" href="/manifest.webmanifest">
<link rel="apple-touch-icon" href="/icon-180.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Mess Ledger">
<meta name="theme-color" content="__TINT__">
<style>
:root { color-scheme: light; --tint: __TINT__; --ink: #212121;
  --soft: #4a4843; --pencil: #8a867e; --rule: #ddd5c2;
  --rule-dk: #c0b797; --card: #faf8f2; }
* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
html, body { margin: 0; background: #f4f1ea; color: var(--ink);
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia,
    serif; }
body { padding: env(safe-area-inset-top) env(safe-area-inset-right)
  env(safe-area-inset-bottom) env(safe-area-inset-left); }
.wrap { max-width: 460px; margin: 0 auto;
  padding: 22px 18px calc(28px + env(safe-area-inset-bottom)); }
h1 { font-size: 30px; font-weight: 500; margin: 2px 0 6px;
  letter-spacing: -.01em; }
.eyebrow, .sub, .foot, .small { font-family: ui-monospace, "DejaVu Sans Mono",
  Menlo, Consolas, monospace; }
.eyebrow { font-size: 10px; letter-spacing: .16em; color: var(--pencil);
  text-transform: uppercase; }
.sub { font-size: 13px; color: var(--soft); margin: 0 0 4px; }
.rule { height: 1px; background: var(--rule); margin: 16px 0 14px; }
.meal { display: block; width: 100%; margin: 0 0 12px; padding: 18px 18px;
  font: inherit; font-size: 19px; text-align: left; border-radius: 3px;
  cursor: pointer; border: 1.5px solid var(--rule-dk); background: var(--card);
  color: var(--ink); transition: background .16s, border-color .16s; }
.meal:active { background: #f1ece0; }
.meal small { display: block; font-family: ui-monospace, "DejaVu Sans Mono",
  Menlo, Consolas, monospace; font-size: 11.5px; color: var(--pencil);
  margin-top: 5px; }
.meal.eaten { border-color: var(--tint); border-width: 2px;
  background: #fdfaf5; }
.meal.eaten .lab { color: var(--tint); text-decoration: underline;
  text-decoration-thickness: 1.5px; text-underline-offset: 4px; }
.meal:disabled { opacity: .42; cursor: default; }
.summary { font-family: ui-monospace, "DejaVu Sans Mono", Menlo, Consolas,
  monospace; font-size: 12px; color: var(--soft); line-height: 1.9; }
.foot { font-size: 10.5px; color: var(--pencil); margin-top: 26px;
  padding-top: 12px; border-top: 1px solid var(--rule); line-height: 1.7; }
.over { color: var(--tint); font-weight: 700; }
.sync { font-family: ui-monospace, monospace; font-size: 11px;
  color: var(--pencil); margin: 0 0 14px; display: flex; gap: 8px;
  align-items: baseline; }
.sync .dot { width: 7px; height: 7px; border-radius: 50%;
  background: var(--rule-dk); display: inline-block; }
.sync.pending .dot { background: var(--tint); }
.sync.pending { color: var(--tint); }
.meal.saving { opacity: .6; }
</style></head>
<body><div class="wrap">
<div class="sync" id="sync"><span class="dot"></span><span id="synctxt">syncing</span></div>
<h1>__DATE_FULL__</h1>
<p class="sub">__SUMMARY__</p>
<div class="rule"></div>
__CARDS__
<div class="summary">__STATS__<br>__BILL__</div>
<p class="foot">Same journal as the desktop app, over your own Wi-Fi.
Add to your home screen to run it as an app.</p>
</div>
<script>window.__STATE__ = __STATE_JSON__;</script>
<script>
const DATE = "__DATE__";
const LS = "ml_state_v1", LQ = "ml_queue_v1";
const $ = id => document.getElementById(id);

const load = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; }
                         catch (e) { return d; } };
const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); }
                         catch (e) {} };

// --- the mirror -------------------------------------------------------
// The phone keeps its own copy of every day, so it works with the
// laptop switched off and knows what it already knows.
let state = load(LS, null) || window.__STATE__ || null;
if (window.__STATE__) { save(LS, window.__STATE__); }
let lastSeen = load(LS + "_at", 0);
let checkedAt = 0;

function entryFor(date) {
  return (state && state.history && state.history[date]) || null;
}

function mealsOf(date) {
  const e = entryFor(date);
  return { breakfast: !!(e && e.breakfast), lunch: !!(e && e.lunch),
           dinner: !!(e && e.dinner) };
}

// Saturday dinner is closed. That one fact is cheap to restate, and the
// phone must not offer a meal the kitchen is not serving.
function closed(meal) {
  const d = new Date(DATE + "T00:00:00");
  return meal === "dinner" && d.getDay() === 6;
}

function render() {
  if (!state) return;          // nothing mirrored yet: trust the server's own markup
  const m = mealsOf(DATE);
  document.querySelectorAll("form[data-meal]").forEach(form => {
    const meal = form.dataset.meal;
    const btn = form.querySelector("button");
    btn.classList.toggle("eaten", m[meal]);
    btn.disabled = closed(meal);
  });
}

function ago(t) {
  if (!t) return "";
  const s = Math.round((Date.now() - t) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return Math.round(s / 60) + " min ago";
  return Math.round(s / 3600) + " h ago";
}

function paintSync() {
  const n = load(LQ, []).length, el = $("sync");
  el.classList.toggle("pending", n > 0);
  let msg;
  if (n) msg = n + (n === 1 ? " meal waiting to sync" : " meals waiting to sync");
  else if (!navigator.onLine)
    msg = lastSeen ? "offline - last synced " + ago(lastSeen) : "offline";
  else if (!checkedAt) msg = "checking with your laptop";
  else msg = "in sync - checked " + ago(checkedAt);
  $("synctxt").textContent = msg;
}

// --- push: your taps --------------------------------------------------
function queueDelta(meal, value) {
  const q = load(LQ, []);
  q.push({ d: DATE, m: meal, v: value ? 1 : 0, t: Date.now() });
  save(LQ, q);
  render();
  paintSync();
  flush();
}

let sending = false;
async function flush() {
  const q = load(LQ, []);
  if (!q.length || sending || !navigator.onLine) return;
  sending = true; paintSync();
  try {
    const r = await fetch("/sync", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ deltas: q })
    });
    if (!r.ok) throw new Error("sync failed");
    const out = await r.json();
    adopt(out.state);
    save(LQ, []);                 // cleared only once the laptop confirms
  } catch (e) {
    /* laptop unreachable: the queue stays put and goes again later */
  } finally { sending = false; paintSync(); }
}

// --- pull: what the laptop has ---------------------------------------
// Runs whether or not anything is queued, so a meal logged on the
// laptop still reaches the phone on its own.
async function pull() {
  if (sending || !navigator.onLine) return;
  sending = true;
  try {
    const r = await fetch("/state");
    if (r.ok) adopt((await r.json()));
  } catch (e) { /* offline */ }
  finally { sending = false; checkedAt = Date.now(); paintSync(); }
}

function adopt(next) {
  if (!next || !next.history) return;
  const before = entryFor(DATE);
  const after = next.history[DATE];
  const changed = JSON.stringify(before || null) !==
                  JSON.stringify(after || null);
  state = next;
  lastSeen = checkedAt = Date.now();
  save(LS, next);
  if (changed) render();
  paintSync();
}

document.querySelectorAll("form[data-meal]").forEach(form => {
  form.addEventListener("submit", ev => {
    ev.preventDefault();
    const meal = form.dataset.meal;
    const btn = form.querySelector("button");
    queueDelta(meal, !btn.classList.contains("eaten"));
  });
});

addEventListener("online", () => { flush(); pull(); });
addEventListener("visibilitychange", () => {
  if (!document.hidden) { flush(); pull(); }
});
setInterval(() => { flush(); pull(); }, 15000);
render(); paintSync(); flush(); pull();
</script>
</body></html>"""

CARD = """<form method="post" action="/toggle" data-meal="{meal}">
<input type="hidden" name="meal" value="{meal}">
<button class="meal{eaten}" type="submit"{disabled}><span class="lab">{label}</span>
<small>{meta}</small></button></form>"""

LOCKED = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mess Ledger &mdash; locked</title>
<style>body{{background:#f4f1ea;color:#212121;font-family:Georgia,serif;
margin:0;padding:12vh 24px;text-align:center}}
h1{{font-weight:500;font-size:22px}}p{{color:#8a867e;font-size:14px;
line-height:1.7}}</style></head><body>
<h1>Mess Ledger</h1>
<p>This journal is locked to its owner.<br>
Open the full link your laptop printed, once.</p>
</body></html>"""

MANIFEST = {
    "name": "Mess Ledger",
    "short_name": "Ledger",
    "description": "Meal journal, on your own Wi-Fi",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": PAPER,
    "theme_color": TINT,
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "/icon-maskable-512.png", "sizes": "512x512",
         "type": "image/png", "purpose": "maskable"},
    ],
}

SW = """const CACHE = 'mess-ledger-v1';
// '/' is deliberately absent: it is behind the token, so precaching it
// would store the "locked" page and break the app offline for good.
// It gets cached at runtime instead, on the first real load.
const SHELL = ['/manifest.webmanifest', '/icon-192.png', '/icon-512.png',
               '/icon-180.png', '/icon-maskable-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL))
    .then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

// fresh data when the laptop is reachable; last known copy when it is not
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).then(r => {
      const copy = r.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy)).catch(() => {});
      return r;
    }).catch(() => caches.match(e.request)
      .then(r => r || caches.match('/')))
  );
});
"""


def rupees(v):
    return f"\u20b9{v:,.2f}"


def _state_payload(now):
    """The whole ledger, for the phone to keep its own copy of."""
    return {"now": now.isoformat(), "history": mc.load_history()}


def render():
    now = mc.today()
    e = mc.peek_day(now)
    is_sat = now.weekday() == 5
    cards = []
    for meal, chip, label in (("breakfast", "B", "Breakfast"),
                              ("lunch", "L", "Lunch"),
                              ("dinner", "D", "Dinner")):
        closed = meal == "dinner" and is_sat
        eaten = bool(e.get(meal, False)) and not closed
        v = mc.meal_value(meal, now)
        n = mc.servings(meal, now)
        unit = mc.unit_price(meal)
        if closed:
            meta = "kitchen closed &middot; 0.0 meal"
        else:
            note = " &middot; double" if v == 2.0 else ""
            meta = (f"{v:.1f} meal{'s' if v > 1 else ''}{note} &middot; "
                    f"{rupees(unit * n)}")
        cards.append(CARD.format(
            meal=meal, label=f"{html.escape(label)} &nbsp;[{chip}]",
            meta=meta, eaten=" eaten" if eaten else "",
            disabled=" disabled" if closed else ""))
    bill, _ = mc.day_bill(e, now)
    offered = sum(mc.meal_value(m, now) for m in mc.MEALS)
    a = mc.allowance_status()
    over = a["over"] > 0
    stats = (f"Misses {a['missed']:g} / {a['allowed']:g}"
             + (f' &mdash; <span class="over">OVER BY {a["over"]:g}</span>'
                if over else f" &middot; {a['remaining']:g} left"))
    cycle = mc.bill_between(mc.cycle_start(now), mc.cycle_end(now))
    page = PAGE
    for token, value in (
            ("__TINT__", TINT),
            ("__DATE__", now.isoformat()),
            ("__DATE_FULL__", html.escape(now.strftime("%A, %d %B %Y"))),
            ("__SUMMARY__", f"{e['meals_counted']:g} meals / "
                            f"{offered:g} offered &middot; {rupees(bill)}"),
            ("__CARDS__", "\n".join(cards)),
            ("__STATS__", stats),
            ("__BILL__", f"Cycle bill {rupees(cycle['total'])}"),
            ("__STATE_JSON__", json.dumps(_state_payload(now)))):
        page = page.replace(token, value)
    return page


class Handler(BaseHTTPRequestHandler):
    server_version = "MessLedger/2"
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _send(self, body, code=200, ctype="text/html; charset=utf-8",
              extra=None):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}):
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _file(self, name, ctype):
        p = WEB_DIR / name
        if not p.is_file():
            return self._send("not found", 404, "text/plain")
        self._send(p.read_bytes(), 200, ctype)

    def do_GET(self):
        route = urlparse(self.path)
        if route.path == "/manifest.webmanifest":
            return self._send(json.dumps(MANIFEST), 200,
                              "application/manifest+json")
        if route.path == "/sw.js":
            return self._send(SW, 200, "application/javascript",
                              [("Service-Worker-Allowed", "/")])
        if route.path.startswith("/icon-"):
            return self._file(route.path.lstrip("/"), "image/png")
        if route.path == "/apple-touch-icon.png":
            return self._file("icon-180.png", "image/png")
        if route.path == "/favicon.ico":
            return self._file("icon-192.png", "image/png")

        key = (parse_qs(route.query).get("k") or [""])[0]
        if hmac.compare_digest(key, TOKEN):
            cookie = (f"{COOKIE}={_hash('session')}; Path=/; Max-Age="
                      f"{SESSION_MAX}; SameSite=Lax")
            self.send_response(302)
            self.send_header("Set-Cookie", cookie)
            self.send_header("Location", "/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if not authorised(self):
            return self._send(LOCKED, 401)
        if route.path == "/state":
            return self._send(json.dumps(self._state_json()), 200,
                              "application/json")
        self._send(render())

    def _state_json(self):
        return _state_payload(mc.today())

    def _apply_deltas(self, deltas):
        """Replay queued edits from the phone, oldest first.

        Each delta is an absolute set for one meal on one day, not a
        toggle, so replaying five days of offline edits can never invert
        a meal the user already corrected on the laptop."""
        applied = 0
        for item in deltas[:5000]:
            try:
                day = datetime.strptime(item["d"], "%Y-%m-%d")
                meal = item["m"]
                if meal not in mc.MEALS:
                    continue
                if meal == "dinner" and day.weekday() == 5:
                    continue           # closed, never a miss
                mc.toggle_meal(day, meal, bool(item["v"]))
                applied += 1
            except Exception:
                continue
        return applied

    def do_POST(self):
        if not authorised(self):
            return self._send(LOCKED, 401)
        path = urlparse(self.path).path
        if path == "/sync":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                body = {}
            applied = self._apply_deltas(body.get("deltas") or [])
            return self._send(json.dumps(
                {"applied": applied, "state": self._state_json()}),
                200, "application/json")
        if path != "/toggle":
            return self._send("not found", 404, "text/plain")
        try:
            length = int(self.headers.get("Content-Length", 0))
            form = parse_qs(self.rfile.read(length).decode())
            meal = (form.get("meal") or [""])[0]
            if meal in mc.MEALS:
                now = mc.today()
                if not (meal == "dinner" and now.weekday() == 5):
                    e = mc.peek_day(now)
                    mc.toggle_meal(now, meal, not e.get(meal, False))
        except Exception:
            pass
        self.send_response(303)
        self.send_header("Location", "/")
        self.send_header("Content-Length", "0")
        self.end_headers()


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    ip = lan_ip()
    print("Mess Ledger, on your own Wi-Fi")
    print(f"  http://{ip}:{PORT}/?k={TOKEN}")
    print()
    print("Open that full link once on your phone, then use "
          "'Add to Home Screen'.")
    print("Keep it private: anyone with the link can log your meals.")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()