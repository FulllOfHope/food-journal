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
_BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
WEB_DIR = _BASE_DIR / "web"
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
<meta name="viewport" content="width=device-width,initial-scale=1,
  viewport-fit=cover">
<title>Mess Ledger</title>
<link rel="manifest" href="/manifest.webmanifest">
<link rel="apple-touch-icon" href="/icon-180.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Mess Ledger">
<meta name="theme-color" content="__TINT__">
<style>
:root { color-scheme: light; --tint: __TINT__; --ink: #212121;
  --soft: #4a4843; --pencil: #8a867e; --rule: #ddd5c2;
  --rule-dk: #c0b797; --card: #faf8f2; --miss: #b3402e; }
* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
html, body { margin: 0; background: #f4f1ea; color: var(--ink);
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia,
    serif; overscroll-behavior-y: none; }
body { padding: env(safe-area-inset-top) env(safe-area-inset-right)
  env(safe-area-inset-bottom) env(safe-area-inset-left); }
.wrap { max-width: 480px; margin: 0 auto;
  padding: 14px 16px calc(30px + env(safe-area-inset-bottom)); }
.mono { font-family: ui-monospace, "DejaVu Sans Mono", Menlo, Consolas,
  monospace; }

/* --- top bar ---------------------------------------------------- */
.topbar { display: flex; align-items: center; justify-content: space-between;
  gap: 10px; }
.brand { font-family: ui-monospace, "DejaVu Sans Mono", Menlo, monospace;
  font-size: 10px; letter-spacing: .18em; text-transform: uppercase;
  color: var(--pencil); }
.icon { -webkit-appearance: none; appearance: none; width: 40px; height: 40px;
  margin: -10px -8px -10px 0; border: 0; background: none; border-radius: 50%;
  color: var(--pencil); font-size: 21px; line-height: 1; cursor: pointer; }
.icon:active { background: #e9e3d5; color: var(--ink); }
.icon.spin { animation: spin .7s linear; }
@keyframes spin { to { transform: rotate(360deg); } }

/* --- sync pill -------------------------------------------------- */
.sync { display: flex; align-items: center; gap: 7px; margin: 9px 0 16px;
  padding: 8px 12px; border-radius: 999px; border: 1px solid var(--rule);
  background: var(--card); font-family: ui-monospace, Menlo, monospace;
  font-size: 11.5px; color: var(--soft); }
.sync .dot { width: 8px; height: 8px; border-radius: 50%; flex: none;
  background: var(--rule-dk); }
.sync.pending { border-color: var(--tint); color: var(--tint);
  background: #fdf6f3; }
.sync.pending .dot { background: var(--tint); animation: pulse 1.5s ease-in-out infinite; }
.sync.ok .dot { background: #6d8f5e; }
.sync.off { color: var(--pencil); }
@keyframes pulse { 50% { opacity: .35; } }
.sync button { margin-left: auto; border: 0; background: none; padding: 4px 2px;
  font: inherit; font-size: 11px; color: var(--tint); cursor: pointer;
  text-decoration: underline; }

/* --- heading ---------------------------------------------------- */
h1 { font-size: 29px; font-weight: 500; margin: 0 0 5px;
  letter-spacing: -.015em; line-height: 1.12; }
.sub { font-size: 14px; color: var(--soft); margin: 0;
  font-family: ui-monospace, Menlo, monospace; }

/* --- week strip ------------------------------------------------- */
.week { display: flex; align-items: stretch; gap: 5px; margin: 18px 0 4px; }
.week .nav { flex: none; width: 34px; border: 1px solid var(--rule-dk);
  border-radius: 3px; background: var(--card); color: var(--soft);
  font-size: 15px; cursor: pointer; }
.week .nav:disabled { opacity: .3; }
.week .days { display: flex; flex: 1; gap: 3px; }
.day { flex: 1; min-width: 0; border: 1px solid transparent; border-radius: 3px;
  background: none; padding: 6px 1px 7px; cursor: pointer; text-align: center;
  font: inherit; color: var(--soft); position: relative; }
.day .dw { display: block; font-family: ui-monospace, Menlo, monospace;
  font-size: 9px; letter-spacing: .06em; color: var(--pencil);
  text-transform: uppercase; }
.day .dd { display: block; font-size: 16px; margin-top: 1px; }
.day .mk { display: block; height: 4px; margin: 3px 5px 0; border-radius: 2px;
  background: transparent; }
.day.has .mk { background: var(--rule-dk); }
.day.full .mk { background: var(--tint); }
.day.today .dw { color: var(--tint); }
.day.sel { border-color: var(--ink); background: var(--card); }
.day.future { opacity: .34; cursor: default; }

/* --- meal cards ------------------------------------------------- */
.cards { margin: 14px 0 0; }
.meal { display: block; width: 100%; margin: 0 0 9px; padding: 15px 16px;
  min-height: 64px; font: inherit; text-align: left; border-radius: 4px;
  cursor: pointer; border: 1.5px solid var(--rule-dk); background: var(--card);
  color: var(--ink); transition: background .14s, border-color .14s;
  position: relative; overflow: hidden; }
.meal:active { background: #f1ece0; transform: scale(.995); }
.meal .row { display: flex; align-items: baseline; justify-content: space-between;
  gap: 10px; }
.meal .lab { font-size: 19px; }
.meal .amt { font-family: ui-monospace, Menlo, monospace; font-size: 13px;
  color: var(--soft); flex: none; }
.meal .meta { display: block; margin-top: 5px; font-family: ui-monospace,
  Menlo, monospace; font-size: 11.5px; color: var(--pencil); }
.meal .chip { display: inline-block; width: 15px; height: 15px; margin-left: 7px;
  vertical-align: 3px; border: 1px solid var(--rule-dk); border-radius: 2px;
  font-family: ui-monospace, Menlo, monospace; font-size: 9px; line-height: 13px;
  text-align: center; color: var(--pencil); }
.meal.eaten { border-color: var(--tint); background: #fdfaf5; }
.meal.eaten .lab { color: var(--tint); text-decoration: underline;
  text-decoration-thickness: 1.5px; text-underline-offset: 4px; }
.meal.eaten .chip { border-color: var(--tint); color: var(--tint); }
.meal.eaten::after { content: ""; position: absolute; inset: 0;
  background: var(--tint); opacity: 0; pointer-events: none; }
.meal.pop::after { animation: pop .34s ease-out; }
@keyframes pop { 0% { opacity: .14; } 100% { opacity: 0; } }
.meal:disabled { opacity: .45; cursor: default; }

/* --- panels ----------------------------------------------------- */
.panel { margin: 22px 0 0; padding: 15px 16px; border: 1px solid var(--rule);
  border-radius: 4px; background: var(--card); }
.phead { display: flex; align-items: baseline; justify-content: space-between;
  gap: 12px; font-family: ui-monospace, Menlo, monospace; font-size: 10px;
  letter-spacing: .15em; text-transform: uppercase; color: var(--pencil); }
.pv { font-size: 15px; letter-spacing: 0; text-transform: none;
  color: var(--ink); font-weight: 700; }
.bar { height: 7px; margin: 12px 0 9px; border-radius: 4px; overflow: hidden;
  background: var(--rule); }
.bar i { display: block; height: 100%; background: var(--rule-dk);
  border-radius: 4px; transition: width .3s ease; }
.bar i.hot { background: var(--miss); }
.note { margin: 0; font-family: ui-monospace, Menlo, monospace; font-size: 12px;
  color: var(--soft); line-height: 1.65; }
.over { color: var(--miss); font-weight: 700; }

/* --- recent days ----------------------------------------------- */
.recent { list-style: none; margin: 12px 0 0; padding: 0; }
.recent li { display: flex; align-items: center; gap: 10px; padding: 9px 0;
  border-top: 1px solid var(--rule); font-family: ui-monospace, Menlo,
  monospace; font-size: 12.5px; }
.recent li:first-child { border-top: 0; }
.recent .rd { flex: none; width: 92px; color: var(--soft); }
.recent .rd.today { color: var(--tint); font-weight: 700; }
.recent .dots { flex: 1; display: flex; gap: 4px; }
.recent .dots i { width: 13px; height: 13px; border-radius: 2px; flex: none;
  border: 1px solid var(--rule-dk); background: transparent; }
.recent .dots i.on { background: var(--tint); border-color: var(--tint); }
.recent .dots i.off { background: none; border-color: var(--miss);
  border-style: dashed; }
.recent .rc { flex: none; color: var(--pencil); }

.foot { margin: 26px 0 0; padding-top: 13px; border-top: 1px solid var(--rule);
  font-family: ui-monospace, Menlo, monospace; font-size: 10.5px;
  color: var(--pencil); line-height: 1.7; }
</style></head>
<body><div class="wrap">
<div class="topbar">
  <span class="brand">Mess&nbsp;Ledger</span>
  <button class="icon" id="refresh" aria-label="Sync now">&#8635;</button>
</div>
<div class="sync" id="sync"><span class="dot"></span><span id="synctxt">connecting</span></div>
<h1 id="dtitle">__DATE_FULL__</h1>
<p class="sub" id="dsub">__SUMMARY__</p>
<nav class="week" aria-label="Days">
  <button class="nav" id="prevw" aria-label="Previous week">&#8249;</button>
  <div class="days" id="days"></div>
  <button class="nav" id="nextw" aria-label="Next week">&#8250;</button>
</nav>
<div class="cards" id="cards">__CARDS__</div>
<section class="panel">
  <div class="phead"><span>Allowance</span><span class="pv" id="allowv">__ALLOWV__</span></div>
  <div class="bar"><i id="allowbar" style="width:__ALLOWPCT__%"></i></div>
  <p class="note" id="allownote">__ALLOWNOTE__</p>
</section>
<section class="panel">
  <div class="phead"><span>Cycle bill</span><span class="pv">__CYCLE__</span></div>
  <p class="note" id="cyclenote">__CYCLEDETAIL__</p>
</section>
<section class="panel">
  <div class="phead"><span>Recent days</span><span class="pv" id="todayv"></span></div>
  <ul class="recent" id="recent"></ul>
</section>
<p class="foot">Same journal as the desktop app, on your own network.
Tap &#8635; to sync. Add to your home screen to run it as an app.</p>
</div>
<script>window.__STATE__ = __STATE_JSON__;</script>
<script>
const LS = "ml_state_v1", LQ = "ml_queue_v1";
const $ = id => document.getElementById(id);

const load = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; }
                         catch (e) { return d; } };
const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); }
                         catch (e) {} };

// ---- dates ---------------------------------------------------------
// The day a meal was actually eaten, taken when the tap happens. A date
// baked in at render time would file everything under the last day the
// phone managed to reach the laptop.
const todayISO = () => {
  const d = new Date();
  return d.getFullYear() + "-" +
         String(d.getMonth() + 1).padStart(2, "0") + "-" +
         String(d.getDate()).padStart(2, "0");
};
const parseISO = s => new Date(s + "T00:00:00");
const isoOf = d => d.getFullYear() + "-" +
  String(d.getMonth() + 1).padStart(2, "0") + "-" +
  String(d.getDate()).padStart(2, "0");

const DAY_SHORT = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
const DAY_LONG = ["Sunday","Monday","Tuesday","Wednesday","Thursday",
                  "Friday","Saturday"];
const MONTH_LONG = ["January","February","March","April","May","June","July",
                    "August","September","October","November","December"];

// Which day the user is looking at. Starts on today and moves when they
// tap around, so an older day can be corrected from the sofa.
let viewDate = todayISO();

// The mess rules, mirrored from meal_common.py so the phone can work out
// a past day without asking the laptop: breakfast 0.5, lunch 2 on
// Saturday, dinner closed on Saturday.
const isSat = s => parseISO(s).getDay() === 6;
const MEALS = ["breakfast", "lunch", "dinner"];
// What a meal is worth on a given day: breakfast 0.5, lunch double on
// Saturday, dinner closed on Saturday.
const weightOf = (s, meal) => meal === "breakfast" ? 0.5
                       : meal === "lunch" ? (isSat(s) ? 2 : 1)
                       : (isSat(s) ? 0 : 1);
const expectedOf = s => MEALS.reduce((a, m) => a + weightOf(s, m), 0);
const entryFor = s => (state && state.history && state.history[s]) || null;
const eatenOf = e => (e && typeof e.meals_counted === "number")
                       ? e.meals_counted : 0;

function mealsOf(s) {
  const e = entryFor(s);
  return { breakfast: !!(e && e.breakfast), lunch: !!(e && e.lunch),
           dinner: !!(e && e.dinner) };
}

// Saturday dinner is closed, and the phone must not offer a meal the
// kitchen is not serving.
function closedOn(s, meal) {
  return meal === "dinner" && isSat(s);
}

// ---- state ---------------------------------------------------------
let state = load(LS, null);
if (window.__STATE__) { save(LS, window.__STATE__); state = window.__STATE__; }
state = state || { history: {} };
let checkedAt = 0;

// The billing cycle runs from the 3rd of a month to the 2nd of the next.
// Mirrors meal_common.cycle_start/cycle_end; keeping this in step with
// Python is the whole reason the two agree.
const CYCLE_START_DAY = 3;
function cycleStart(s) {
  const d = parseISO(s);
  let a = new Date(d.getFullYear(), d.getMonth(), CYCLE_START_DAY);
  if (d < a) a = new Date(d.getFullYear(), d.getMonth() - 1, CYCLE_START_DAY);
  return isoOf(a);
}

// Allowance to date, mirroring meal_common.allowance_status: counting
// starts at the first day there is any record for, and a day with no
// entry at all counts as fully missed rather than as zero.
function allowanceOn(s) {
  const h = state.history || {};
  const keys = Object.keys(h).sort();
  const allowed = 25;
  let start = cycleStart(s);
  if (keys.length && keys[0] > start) start = keys[0];
  let missed = 0;
  if (s >= start) {
    const d = parseISO(start);
    for (;;) {
      const k = isoOf(d);
      if (k > s) break;
      const e = h[k];
      let exp = 0, got = 0;
      for (const m of MEALS) {
        const w = weightOf(k, m);
        exp += w;
        if (e && e[m]) got += w;
      }
      missed += Math.max(0, exp - got);
      d.setDate(d.getDate() + 1);
    }
  }
  missed = Math.round(missed * 100) / 100;
  const r2 = v => Math.round(v * 100) / 100;
  return { missed: missed, allowed: allowed,
           remaining: r2(allowed - missed),
           over: r2(Math.max(0, missed - allowed)),
           pct: Math.min(100, Math.round(missed / allowed * 100)) };
}

// ---- rendering -----------------------------------------------------
function renderWeek() {
  const host = $("days");
  host.innerHTML = "";
  const base = parseISO(viewDate);
  const dow = base.getDay();
  const weekStart = new Date(base);
  weekStart.setDate(base.getDate() - dow);
  const today = todayISO();
  for (let i = 0; i < 7; i++) {
    const d = new Date(weekStart);
    d.setDate(weekStart.getDate() + i);
    const s = isoOf(d);
    const e = entryFor(s);
    const exp = expectedOf(s);
    const got = eatenOf(e);
    const future = s > today;
    const b = document.createElement("button");
    b.className = "day";
    if (s === today) b.classList.add("today");
    if (s === viewDate) b.classList.add("sel");
    if (future) b.classList.add("future");
    if (!future) {
      if (got >= exp - 0.01) b.classList.add("full");
      else if (got > 0) b.classList.add("has");
    }
    b.innerHTML = '<span class="dw">' + DAY_SHORT[d.getDay()] +
      '</span><span class="dd">' + d.getDate() + '</span><span class="mk"></span>';
    if (!future) b.onclick = () => { viewDate = s; renderAll(); };
    host.appendChild(b);
  }
  $("prevw").disabled = false;
  $("nextw").disabled = isoOf(new Date(weekStart.getTime() + 6 * 864e5)) >= today;
}

function renderCards() {
  const s = viewDate;
  const e = entryFor(s);
  const dt = parseISO(s);
  const sat = dt.getDay() === 6;
  const host = $("cards");
  const rows = [["breakfast","B","Breakfast"],
                ["lunch","L","Lunch"], ["dinner","D","Dinner"]];
  host.innerHTML = "";
  for (const [meal, chip, label] of rows) {
    const shut = closedOn(s, meal);
    const v = weightOf(s, meal);
    const eaten = !shut && !!(e && e[meal]);
    const f = document.createElement("form");
    f.method = "post"; f.action = "/toggle"; f.dataset.meal = meal;
    const inp = document.createElement("input");
    inp.type = "hidden"; inp.name = "meal"; inp.value = meal;
    const b = document.createElement("button");
    b.className = "meal" + (eaten ? " eaten" : "");
    b.type = "submit";
    if (shut) b.disabled = true;
    const cost = meal === "lunch" ? (sat ? 2 : 1)
               : meal === "dinner" ? (sat ? 0 : 1) : 1;
    const meta = shut ? "kitchen closed · no meal to miss"
      : v + " meal" + (v > 1 ? "s" : "") + (v === 2 ? " · double" : "") +
        " · " + cost + (cost === 1 ? " portion" : " portions");
    b.innerHTML = '<span class="row"><span class="lab">' + label +
      '<span class="chip">' + chip + '</span></span>' +
      '<span class="amt">' + (shut ? "—" : (eaten ? "eaten" : "not yet")) +
      '</span></span><small class="meta">' + meta + '</small>';
    f.appendChild(inp); f.appendChild(b); host.appendChild(f);
  }
}

function renderHead() {
  const s = viewDate;
  const dt = parseISO(s);
  const e = entryFor(s);
  const got = eatenOf(e);
  const offered = expectedOf(s);
  const fmt = dt.getDate() + " " + MONTH_LONG[dt.getMonth()] +
              (dt.getFullYear() !== new Date().getFullYear()
                ? " " + dt.getFullYear() : "");
  $("dtitle").textContent = DAY_LONG[dt.getDay()] + ", " + fmt;
  $("dsub").textContent = got + " of " + offered + " meals · " +
    (s === todayISO() ? "today" : s);
}

function renderAllow() {
  const a = allowanceOn(viewDate);
  $("allowv").textContent = a.missed + " / " + a.allowed + " missed";
  const bar = $("allowbar");
  bar.style.width = a.pct + "%";
  bar.className = a.over > 0 ? "hot" : "";
  $("allownote").innerHTML = a.over > 0
    ? '<span class="over">Over by ' + a.over + '</span> · ' +
      a.missed + ' missed this cycle'
    : a.remaining + ' left before the allowance runs out · ' +
      a.missed + ' missed so far';
}

function renderRecent() {
  const host = $("recent");
  host.innerHTML = "";
  const today = todayISO();
  const t = parseISO(today);
  $("todayv").textContent = "today " + t.getDate();
  for (let i = 0; i < 7; i++) {
    const d = new Date(t);
    d.setDate(t.getDate() - i);
    const s = isoOf(d);
    const e = entryFor(s);
    const li = document.createElement("li");
    const rd = document.createElement("span");
    rd.className = "rd" + (i === 0 ? " today" : "");
    rd.textContent = (i === 0 ? "today" : DAY_SHORT[d.getDay()]) +
      " " + d.getDate();
    const dots = document.createElement("span");
    dots.className = "dots";
    const sat = d.getDay() === 6;
    const rows = [["breakfast", !sat], ["lunch", true], ["dinner", !sat]];
    for (const [meal, served] of rows) {
      const i2 = document.createElement("i");
      if (!served) { i2.style.visibility = "hidden"; }
      else if (e && e[meal]) i2.className = "on";
      else if (e) i2.className = "off";
      dots.appendChild(i2);
    }
    const rc = document.createElement("span");
    rc.className = "rc";
    rc.textContent = e ? eatenOf(e) + " meals" : "—";
    li.appendChild(rd); li.appendChild(dots); li.appendChild(rc);
    host.appendChild(li);
  }
}

function renderAll() {
  renderHead(); renderWeek(); renderCards(); renderAllow(); renderRecent();
}

// ---- pushing a tap --------------------------------------------------
function queueDelta(meal, value) {
  const d = viewDate;
  const q = load(LQ, []);
  q.push({ d: d, m: meal, v: value ? 1 : 0, t: Date.now() });
  save(LQ, q);
  // Show the tap at once. Until the laptop confirms, the tile should
  // reflect what you meant rather than pretending nothing happened -
  // otherwise you tap it twice and log it twice.
  const e = (state.history = state.history || {})[d] ||
            (state.history[d] = { date: d, weekday: "", meals_counted: 0 });
  e[meal] = !!value;
  e.meals_counted = MEALS.reduce((a, m) =>
      a + (closedOn(d, m) ? 0 : (e[m] ? weightOf(d, m) : 0)), 0);
  save(LS, state);
  renderAll();
  paintSync();
  flush();
}

let sending = false;
async function flush() {
  const q = load(LQ, []);
  if (!q.length || sending || !navigator.onLine) { paintSync(); return; }
  sending = true; paintSync();
  try {
    const r = await fetch("/sync", { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ deltas: q }) });
    if (!r.ok) throw new Error("sync failed");
    const out = await r.json();
    adopt(out.state);
    save(LQ, []);              // cleared only once the laptop confirms
    checkedAt = Date.now();
  } catch (e) {
    /* laptop unreachable: the queue stays put and goes again later */
  } finally { sending = false; paintSync(); }
}

// ---- pulling: what the laptop has -----------------------------------
async function pull() {
  if (sending || !navigator.onLine) return;
  sending = true;
  try {
    const r = await fetch("/state");
    if (r.ok) { adopt(await r.json()); checkedAt = Date.now(); }
  } catch (e) { /* offline */ }
  finally { sending = false; paintSync(); }
}

function adopt(next) {
  if (!next || !next.history) return;
  state = next;
  save(LS, state);
  renderAll();
}

function ago(ms) {
  if (!ms) return "not yet";
  const s = Math.round((Date.now() - ms) / 1000);
  if (s < 45) return "just now";
  if (s < 3600) return Math.round(s / 60) + "m ago";
  if (s < 86400) return Math.round(s / 3600) + "h ago";
  return Math.round(s / 86400) + "d ago";
}

function paintSync() {
  const box = $("sync"), txt = $("synctxt");
  const n = load(LQ, []).length;
  box.className = "sync";
  if (navigator.onLine === false) {
    box.classList.add("off");
    txt.textContent = "offline · " + (n ? n + " waiting" : "nothing queued");
  } else if (n) {
    box.classList.add("pending");
    txt.textContent = n + (n === 1 ? " meal" : " meals") + " waiting to sync";
  } else if (checkedAt) {
    box.classList.add("ok");
    txt.textContent = "synced " + ago(checkedAt);
  } else {
    txt.textContent = "connecting";
  }
}

// ---- wiring ---------------------------------------------------------
document.addEventListener("click", ev => {
  const btn = ev.target.closest("button.meal");
  if (!btn || btn.disabled) return;
  btn.classList.add("pop");
  if (navigator.vibrate) try { navigator.vibrate(8); } catch (e) {}
});
document.addEventListener("submit", ev => {
  const f = ev.target;
  if (!f.dataset || !f.dataset.meal) return;
  ev.preventDefault();
  const b = f.querySelector("button.meal");
  queueDelta(f.dataset.meal, !(b && b.classList.contains("eaten")));
});
$("prevw").onclick = () => { const d = parseISO(viewDate);
  d.setDate(d.getDate() - 7); viewDate = isoOf(d); renderAll(); };
$("nextw").onclick = () => { const d = parseISO(viewDate);
  d.setDate(d.getDate() + 7); viewDate = isoOf(d); renderAll(); };
$("refresh").onclick = ev => { const i = ev.currentTarget;
  i.classList.add("spin"); setTimeout(() => i.classList.remove("spin"), 700);
  flush(); pull(); };

// The service worker is the whole reason this can be opened with the
// laptop shut. Without it the app is a web page on a machine that isn't
// there, and every icon tap needs the server awake.
if ("serviceWorker" in navigator) {
  addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js")
      .then(reg => reg.update().catch(() => {}))
      .catch(() => {});
  });
}

renderAll();
paintSync();
flush(); pull();
setInterval(() => { if (viewDate === todayISO()) renderHead(); flush(); pull(); }, 15000);
setInterval(paintSync, 5000);
addEventListener("online", () => { flush(); pull(); });
addEventListener("focus", () => { flush(); pull(); });
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) { flush(); pull(); }
});
</script>
</body></html>
"""

CARD = """<form method="post" action="/toggle" data-meal="{meal}">
<input type="hidden" name="meal" value="{meal}">
<button class="meal{eaten}" type="submit"{disabled}><span class="row">
<span class="lab">{label}<span class="chip">{chip}</span></span>
<span class="amt">{amt}</span></span><small class="meta">{meta}</small>
</button></form>"""

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
// '/' is behind the token. The browser sends the session cookie with
// the service worker's own fetches, so it usually caches the real page -
// but if it does not, install must still succeed. Promise.allSettled
// keeps one 401 from throwing away the icons along with it.
const SHELL = ['/', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png',
               '/icon-180.png', '/icon-maskable-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => Promise.allSettled(SHELL.map(u => c.add(u))))
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
        if closed:
            meta = "kitchen closed \u00b7 no meal to miss"
            amt = "\u2014"
        else:
            note = " \u00b7 double" if v == 2.0 else ""
            meta = (f"{v:.1f} meal{'s' if v > 1 else ''}{note} \u00b7 "
                    f"{n} portion{'s' if n > 1 else ''}")
            amt = "eaten" if eaten else "not yet"
        cards.append(CARD.format(
            meal=meal, chip=chip, label=html.escape(label), meta=meta, amt=amt,
            eaten=" eaten" if eaten else "",
            disabled=" disabled" if closed else ""))
    a = mc.allowance_status()
    pct = min(100, round(a["missed"] / a["allowed"] * 100)) if a["allowed"] else 0
    if a["over"] > 0:
        allow_note = (f'<span class="over">Over by {a["over"]:g}</span> '
                      f'\u00b7 {a["missed"]:g} missed this cycle')
    else:
        allow_note = (f"{a['remaining']:g} left before the allowance runs out "
                      f"\u00b7 {a['missed']:g} missed so far")
    cycle = mc.bill_between(mc.cycle_start(now), mc.cycle_end(now))
    cs, ce = mc.cycle_start(now), mc.cycle_end(now)
    offered = sum(mc.meal_value(m, now) for m in mc.MEALS)
    page = PAGE
    for token, value in (
            ("__TINT__", TINT),
            ("__DATE_FULL__", html.escape(now.strftime("%A, %d %B %Y"))),
            ("__SUMMARY__", f"{e['meals_counted']:g} of {offered:g}"
                            " meals \u00b7 today"),
            ("__CARDS__", "\n".join(cards)),
            ("__ALLOWV__", f"{a['missed']:g} / {a['allowed']:g} missed"),
            ("__ALLOWPCT__", str(pct)),
            ("__ALLOWNOTE__", allow_note),
            ("__CYCLE__", rupees(cycle["total"])),
            ("__CYCLEDETAIL__",
             f"{html.escape(cs.strftime('%d %b'))} \u2013 "
             f"{html.escape(ce.strftime('%d %b %Y'))}"),
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