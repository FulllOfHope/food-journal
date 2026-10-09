#!/usr/bin/env python3
"""Mess Ledger on your phone, over your own Wi-Fi. No cloud, no account,
no personal server: run this on your laptop, open the printed URL on
your phone's browser (same Wi-Fi), tap meals.

Same history file as the desktop app, so both stay in sync instantly.

Caveat, stated plainly: anyone on your Wi-Fi can open the page and tap.
Fine for home; never expose this port to the internet.
"""
import html
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meal_common as mc

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8137

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mess Ledger &mdash; today</title>
<style>
:root {{ color-scheme: light; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: #f4f1ea; color: #212121;
  font-family: Georgia, 'DejaVu Serif', serif; }}
.wrap {{ max-width: 520px; margin: 0 auto; padding: 28px 20px 40px; }}
.eyebrow {{ font-family: monospace; font-size: 11px; letter-spacing: .12em;
  color: #8a867e; text-transform: uppercase; }}
h1 {{ font-size: 34px; font-weight: 500; margin: 6px 0 4px; }}
.sub {{ font-family: monospace; font-size: 13px; color: #4a4843;
  margin-bottom: 22px; }}
.meal {{ display: block; width: 100%; margin: 0 0 14px; padding: 22px;
  font-size: 20px; border-radius: 12px; cursor: pointer;
  border: 1.5px solid #c0b797; background: #faf8f2; color: #212121; }}
.meal small {{ display: block; font-family: monospace; font-size: 13px;
  color: #4a4843; margin-top: 6px; }}
.meal.eaten {{ background: #212121; border-color: #212121; color: #faf8f2; }}
.meal.eaten small {{ color: #d1d1de; }}
.meal:disabled {{ opacity: .45; cursor: default; }}
.summary {{ margin-top: 20px; font-family: monospace; font-size: 13px;
  color: #4a4843; line-height: 1.9; border-top: 1px solid #ddd5c2;
  padding-top: 14px; }}
.over {{ color: #b3402e; font-weight: bold; }}
.foot {{ margin-top: 26px; font-family: monospace; font-size: 11px;
  color: #8a867e; }}
</style></head><body><div class="wrap">
<div class="eyebrow">Mess Ledger &mdash; entry</div>
<h1>{date}</h1>
<div class="sub">{summary}</div>
{cards}
<div class="summary">{stats}<br>{bill}</div>
<div class="foot">Same journal as the desktop app. LAN only &mdash; never expose this port.</div>
</div></body></html>"""

CARD = """<form method="post" action="/toggle">
<input type="hidden" name="meal" value="{meal}">
<button class="meal{eaten}" type="submit"{disabled}>{label}
<small>{meta}</small></button></form>"""


def rupees(v):
    return f"\u20b9{v:,.2f}"


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
    a = mc.allowance_status()
    over = a["over"] > 0
    stats = (f"Misses {a['missed']:g} / {a['allowed']:g}"
             + (f' &mdash; <span class="over">OVER BY {a["over"]:g}</span>'
                if over else f" &middot; {a['remaining']:g} left"))
    return PAGE.format(
        date=html.escape(now.strftime("%A, %d %B %Y")),
        summary=(f"Today &mdash; {e['meals_counted']:g} meals &middot; "
                 f"{rupees(bill)}"),
        cards="\n".join(cards),
        stats=stats,
        bill=f"Bill so far {rupees(mc.bill_between(mc.cycle_start(now), mc.cycle_end(now))['total'])}")


class Handler(BaseHTTPRequestHandler):
    server_version = "MessLedger/1"

    def log_message(self, *args):
        pass

    def _send(self, body, code=200, ctype="text/html; charset=utf-8"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if urlparse(self.path).path != "/":
            return self._send("not found", 404, "text/plain")
        self._send(render())

    def do_POST(self):
        if urlparse(self.path).path != "/toggle":
            return self._send("not found", 404, "text/plain")
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        meal = parse_qs(self.rfile.read(length).decode()).get("meal", [""])[0]
        if meal in mc.MEALS:
            d = mc.today()
            if not (meal == "dinner" and d.weekday() == 5):
                e = mc.peek_day(d)
                mc.toggle_meal(d, meal, not e.get(meal, False))
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except Exception:
        return "localhost"
    finally:
        try:
            s.close()
        except Exception:
            pass


if __name__ == "__main__":
    mc.ensure_dirs()
    print(f"Mess Ledger on your phone:  http://{lan_ip()}:{PORT}/")
    print("Same Wi-Fi, same journal. Ctrl-C to stop.")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
