import math
import random
import sys
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

FONT = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"

COLORS = dict(bg="#e9e9e9", panel="#ffffff", panel2="#f6f6f6", border="#e9e9e9",
              text="#111111", muted="#777777", accent="#111111", up="#15803d",
              down="#b91c1c", warn="#b45309", hover="#f4f4f4", select="#ececec")

TABS = ["Markets", "Insights", "Watchlist", "Portfolio", "Orders", "News"]

SECTORS = {"RELIANCE": "Energy", "TCS": "IT", "HDFCBANK": "Banking", "INFY": "IT",
           "ICICIBANK": "Banking", "SBIN": "Banking", "BHARTIARTL": "Telecom", "ITC": "FMCG",
           "LT": "Infra", "TATAMOTORS": "Auto", "WIPRO": "IT", "ADANIENT": "Infra",
           "MARUTI": "Auto", "SUNPHARMA": "Pharma"}

CHARGES = dict(brokerage=0.0, stt=0.001, exchange=0.0000297, sebi=0.000001, stamp=0.00015, gst=0.18)

MOODS = ((25, "Fearful"), (45, "Cautious"), (55, "Neutral"), (75, "Optimistic"), (101, "Greedy"))

TIMEFRAMES = {"1D": (75, 0.0015), "1W": (35, 0.004), "1M": (22, 0.012), "1Y": (52, 0.028)}

STOCKS = [
    ("RELIANCE", "Reliance Industries", 2945.30), ("TCS", "Tata Consultancy Services", 4110.55),
    ("HDFCBANK", "HDFC Bank", 1682.40), ("INFY", "Infosys", 1874.10),
    ("ICICIBANK", "ICICI Bank", 1265.75), ("SBIN", "State Bank of India", 812.60),
    ("BHARTIARTL", "Bharti Airtel", 1598.20), ("ITC", "ITC Ltd", 498.35),
    ("LT", "Larsen & Toubro", 3620.00), ("TATAMOTORS", "Tata Motors", 982.45),
    ("WIPRO", "Wipro", 562.80), ("ADANIENT", "Adani Enterprises", 3105.90),
    ("MARUTI", "Maruti Suzuki", 12480.00), ("SUNPHARMA", "Sun Pharma", 1788.65),
]

INDICES = [("NIFTY 50", 25840.15), ("SENSEX", 84210.60), ("BANK NIFTY", 54120.30),
           ("NIFTY IT", 41250.80), ("USD/INR", 83.95), ("GOLD 10g", 76450.00)]

HOLDINGS = [("RELIANCE", 10, 2810.00), ("TCS", 5, 3950.00), ("INFY", 12, 1790.00),
            ("ITC", 50, 455.00), ("SBIN", 25, 845.00)]

NEWS = [
    ("Markets", "Nifty ends higher as banks lead a broad rally",
     "Private lenders added the most points while midcaps outperformed the benchmark."),
    ("Economy", "Inflation print comes in below estimates",
     "Softer food prices pulled the headline number down, raising rate-cut hopes."),
    ("IT", "IT stocks climb ahead of quarterly results",
     "Analysts expect steady deal wins and improving margins across large caps."),
    ("Banking", "Credit growth stays strong for the third month",
     "Retail and MSME loans continue to drive balance-sheet expansion."),
    ("Auto", "Festive demand lifts passenger vehicle sales",
     "Dealers report record bookings for SUVs and entry-level EVs."),
    ("Energy", "Crude slips on supply concerns easing",
     "Oil marketing companies gain as input costs move lower."),
    ("Global", "Asian markets mixed after overnight Wall Street move",
     "Investors weigh central bank commentary and bond yields."),
    ("Commodities", "Gold holds near record as dollar softens",
     "Safe-haven buying keeps bullion firm through the session."),
    ("IPO", "Three mainboard IPOs open for subscription this week",
     "Grey-market premiums suggest healthy retail interest."),
]

SORTS = {
    "Symbol": (lambda s: s.sym, False),
    "Price": (lambda s: s.price, True),
    "Change %": (lambda s: s.pct, True),
    "Volume": (lambda s: s.volume, True),
}


def inr(x):
    return f"₹{x:,.2f}"


def pct_text(x):
    return f"{'+' if x >= 0 else ''}{x:.2f}%"


def market_open(now):
    minutes = now.hour * 60 + now.minute
    return now.weekday() < 5 and 9 * 60 + 15 <= minutes <= 15 * 60 + 30


def blend(a, b, t):
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


class UpDownGame:
    def __init__(self):
        self.rng = random.Random()
        self.score = self.rounds = self.streak = self.best = 0
        self.new_round()

    def new_round(self):
        self.sym = self.rng.choice(STOCKS)[0]
        trend = self.rng.choice((-1, 1)) * self.rng.uniform(0.002, 0.006)
        price, out = 1000.0, []
        for i in range(41):
            follow = self.rng.random() < 0.68
            move = abs(self.rng.gauss(0, 0.008)) * (1 if (trend > 0) == follow else -1) + trend * 0.3
            op, cl = price, price * (1 + move)
            out.append([op, max(op, cl) * (1 + abs(self.rng.gauss(0, 0.003))),
                        min(op, cl) * (1 - abs(self.rng.gauss(0, 0.003))), cl])
            price = cl
        self.candles, self.revealed, self.last = out, False, None

    def recent_trend(self):
        closes = [x[3] for x in self.candles[30:40]]
        return "up" if closes[-1] >= closes[0] else "down"

    def guess(self, up):
        if self.revealed:
            return None
        nxt = self.candles[40]
        actual_up = nxt[3] >= nxt[0]
        correct = up == actual_up
        self.rounds += 1
        self.score += correct
        self.streak = self.streak + 1 if correct else 0
        self.best = max(self.best, self.streak)
        self.revealed, self.last = True, (correct, actual_up)
        return self.last


class Stock:
    def __init__(self, sym, name, price, rng):
        self.sym, self.name = sym, name
        self.prev = price
        self.price = round(price * (1 + rng.uniform(-0.025, 0.025)), 2)
        self.open = round(self.prev * (1 + rng.uniform(-0.006, 0.006)), 2)
        self.high = round(max(self.open, self.price) * (1 + rng.uniform(0, 0.008)), 2)
        self.low = round(min(self.open, self.price) * (1 - rng.uniform(0, 0.008)), 2)
        self.volume = rng.randint(800_000, 12_000_000)

    @property
    def change(self):
        return self.price - self.prev

    @property
    def pct(self):
        return self.change / self.prev * 100

    def move(self, rng):
        self.price = round(self.price * (1 + rng.gauss(0, 0.0015)), 2)
        self.high = max(self.high, self.price)
        self.low = min(self.low, self.price)
        self.volume += rng.randint(1_000, 40_000)


class MarketData:
    def __init__(self):
        self.rng = random.Random(7)
        self.stocks = {s: Stock(s, n, p, self.rng) for s, n, p in STOCKS}
        self.indices = [Stock(n, n, v, self.rng) for n, v in INDICES]
        self.holdings = {s: [q, avg] for s, q, avg in HOLDINGS}
        now = datetime.now()
        self.orders = [
            dict(time=(now - timedelta(minutes=42)).strftime("%H:%M:%S"), sym="TCS", side="BUY",
                 qty=5, kind="Market", price=3950.00, status="Executed"),
            dict(time=(now - timedelta(minutes=18)).strftime("%H:%M:%S"), sym="WIPRO", side="BUY",
                 qty=20, kind="Limit", price=550.00, status="Open"),
        ]
        self.cash = 250000.0
        self.alerts = []
        self.events = []
        self._candles = {}

    def candles(self, sym, tf):
        key = (sym, tf)
        if key not in self._candles:
            count, vol = TIMEFRAMES[tf]
            rng = random.Random(sym + tf)
            close = self.stocks[sym].price
            out = []
            for _ in range(count):
                op = close * (1 + rng.gauss(0, vol))
                hi = max(op, close) * (1 + abs(rng.gauss(0, vol / 2)))
                lo = min(op, close) * (1 - abs(rng.gauss(0, vol / 2)))
                out.append([op, hi, lo, close])
                close = op
            out.reverse()
            self._candles[key] = out
        return self._candles[key]

    def tick(self):
        for s in list(self.stocks.values()) + self.indices:
            s.move(self.rng)
        for (sym, _), data in self._candles.items():
            last, p = data[-1], self.stocks[sym].price
            last[3], last[1], last[2] = p, max(last[1], p), min(last[2], p)
        self._fill_open_orders()
        self._check_alerts()

    def _fill_open_orders(self):
        for o in filter(lambda o: o["status"] == "Open", self.orders):
            price, buy = self.stocks[o["sym"]].price, o["side"] == "BUY"
            if o["kind"] == "Limit":
                hit = price <= o["price"] if buy else price >= o["price"]
            else:
                hit = price >= o["price"] if buy else price <= o["price"]
            if not hit:
                continue
            short = o["qty"] > self.holdings.get(o["sym"], [0, 0])[0]
            if (buy and o["qty"] * o["price"] > self.cash) or (not buy and short):
                o["status"] = "Rejected"
            else:
                o["status"] = "Executed"
                self._settle(o)
            self.events.append(f"{o['kind']} {o['side']} {o['sym']}: {o['status'].lower()}")

    def add_alert(self, sym, price):
        self.alerts.append(dict(sym=sym, price=price, above=price > self.stocks[sym].price))
        self.events.append(f"Alert set: {sym} at {price:,.2f}")

    def _check_alerts(self):
        for a in list(self.alerts):
            price = self.stocks[a["sym"]].price
            if (price >= a["price"]) if a["above"] else (price <= a["price"]):
                self.alerts.remove(a)
                self.events.append(f"Alert: {a['sym']} reached {a['price']:,.2f}")

    def depth(self, sym):
        price = self.stocks[sym].price
        rng = random.Random(f"{sym}{price}")
        step = max(0.05, round(price * 0.0002, 2))
        return [(price - step * i, rng.randint(50, 5000), price + step * i, rng.randint(50, 5000))
                for i in range(1, 6)]

    def filtered(self, query="", sort="Symbol"):
        q = query.strip().lower()
        match = filter(lambda s: q in s.sym.lower() or q in s.name.lower(), self.stocks.values())
        key, rev = SORTS[sort]
        return sorted(match, key=key, reverse=rev)

    def movers(self, gainers=True, n=5):
        return sorted(self.stocks.values(), key=lambda s: s.pct, reverse=gainers)[:n]

    def summary(self):
        rows = [(self.stocks[s], q, avg) for s, (q, avg) in self.holdings.items()]
        invested = sum(q * avg for _, q, avg in rows)
        current = sum(q * s.price for s, q, _ in rows)
        day = sum(q * s.change for s, q, _ in rows)
        pnl = current - invested
        return dict(invested=invested, current=current, pnl=pnl, day=day,
                    pct=(pnl / invested * 100) if invested else 0.0)

    def place(self, order):
        self.orders.insert(0, order)
        if order["status"] == "Executed":
            self._settle(order)

    def ma20(self, sym, back=0):
        closes = [x[3] for x in self.candles(sym, "1M")]
        end = len(closes) - back
        return sum(closes[end - 20:end]) / 20

    def has_stop(self, sym):
        return any(o["status"] == "Open" and o["sym"] == sym and o["kind"] == "Stop-loss"
                   and o["side"] == "SELL" for o in self.orders)

    def charges(self, side, qty, price):
        value = qty * price
        brokerage = value * CHARGES["brokerage"]
        stt = value * CHARGES["stt"]
        exchange = value * CHARGES["exchange"]
        sebi = value * CHARGES["sebi"]
        stamp = value * CHARGES["stamp"] if side == "BUY" else 0.0
        gst = (brokerage + exchange + sebi) * CHARGES["gst"]
        rows = [("Brokerage (delivery)", brokerage), ("STT 0.1%", stt), ("Exchange charges", exchange),
                ("SEBI fee", sebi), ("Stamp duty 0.015%", stamp), ("GST 18%", gst)]
        return rows, sum(v for _, v in rows)

    def break_even(self, qty, price):
        _, buy_cost = self.charges("BUY", qty, price)
        _, sell_cost = self.charges("SELL", qty, price)
        return price + (buy_cost + sell_cost) / qty

    def coach(self, side, qty, price, kind, sym):
        s, notes = self.stocks[sym], []
        value = qty * price
        capital = self.cash + self.summary()["current"]
        share = value / capital * 100 if capital else 0
        ma = self.ma20(sym)
        if side == "BUY":
            if share > 25:
                notes.append(("risk", f"This order is {share:.0f}% of your capital. Keep one trade under 10%."))
            elif share > 10:
                notes.append(("warn", f"This order is {share:.0f}% of your capital. Most traders stay under 10%."))
            else:
                notes.append(("ok", f"Position size is {share:.1f}% of your capital."))
            if price < ma:
                notes.append(("warn", f"Price is below its 20-day average ({ma:,.2f}), so the trend is down."))
            else:
                notes.append(("ok", f"Price is above its 20-day average ({ma:,.2f}), so the trend is up."))
            if s.pct <= -2:
                notes.append(("warn", f"{sym} is falling {s.pct:.1f}% today. Buying a falling stock is risky."))
            elif s.pct >= 3:
                notes.append(("warn", f"{sym} is already up {s.pct:.1f}% today. You may be chasing the move."))
            else:
                notes.append(("ok", f"Today's move ({pct_text(s.pct)}) is normal."))
            held = self.holdings.get(sym, [0, 0])[0] * s.price + value
            conc = held / (self.summary()["current"] + value) * 100
            if conc > 40:
                notes.append(("risk", f"{sym} would be {conc:.0f}% of your holdings. Spread across more stocks."))
            if not self.has_stop(sym):
                notes.append(("warn", "No stop-loss is set for this stock. Plan your exit before you enter."))
        else:
            q, avg = self.holdings.get(sym, [0, 0.0])
            pnl = (price - avg) * qty
            if pnl < 0:
                notes.append(("warn", f"You are selling at a loss of {inr(-pnl)} (you bought at {avg:,.2f})."))
            else:
                notes.append(("ok", f"You are booking a profit of {inr(pnl)} before charges."))
            if s.pct <= -3:
                notes.append(("warn", f"{sym} is down {s.pct:.1f}% today. Make sure this is not a panic sale."))
            if price > ma:
                notes.append(("ok", f"Price is still above its 20-day average ({ma:,.2f})."))
        if kind == "Market" and not market_open(datetime.now()):
            notes.append(("warn", "The market is closed. A real market order would wait for the next open."))
        levels = [lvl for lvl, _ in notes]
        verdict = "Risky" if "risk" in levels else ("Caution" if "warn" in levels else "Safe")
        return verdict, notes

    def mood(self):
        stocks = list(self.stocks.values())
        up = len([s for s in stocks if s.change >= 0])
        avg = sum(s.pct for s in stocks) / len(stocks)
        nifty = self.indices[0].pct
        score = max(0, min(100, round(50 + avg * 12 + (up / len(stocks) - 0.5) * 60 + nifty * 8)))
        label = next(name for limit, name in MOODS if score < limit)
        return dict(score=score, label=label, up=up, down=len(stocks) - up, avg=avg, nifty=nifty)

    def sectors(self):
        groups = {}
        for s in self.stocks.values():
            groups.setdefault(SECTORS[s.sym], []).append(s)
        rows = [(name, sum(s.pct for s in ss) / len(ss), ss) for name, ss in groups.items()]
        return sorted(rows, key=lambda t: t[1], reverse=True)

    def health(self):
        if not self.holdings:
            return dict(score=0, label="No holdings", notes=[("warn", "Buy a few stocks to see your portfolio health.")])
        p = self.summary()
        notes, score = [], 100
        values = {sym: q * self.stocks[sym].price for sym, (q, _) in self.holdings.items()}
        top_sym, top_val = max(values.items(), key=lambda kv: kv[1])
        top_share = top_val / p["current"] * 100
        if top_share > 40:
            score -= 25
            notes.append(("risk", f"{top_sym} is {top_share:.0f}% of your holdings."))
        else:
            notes.append(("ok", f"Largest holding is {top_sym} at {top_share:.0f}%."))
        sectors = {SECTORS[sym] for sym in self.holdings}
        if len(sectors) < 3:
            score -= 15
            notes.append(("warn", f"Only {len(sectors)} sector(s). Add stocks from other sectors."))
        else:
            notes.append(("ok", f"Spread across {len(sectors)} sectors."))
        losers = [sym for sym, (q, avg) in self.holdings.items() if self.stocks[sym].price < avg]
        if losers:
            score -= 8 * len(losers)
            notes.append(("warn", f"Below buy price: {', '.join(losers)}."))
        else:
            notes.append(("ok", "Every holding is above its buy price."))
        cash_share = self.cash / (self.cash + p["current"]) * 100
        if cash_share < 10:
            score -= 10
            notes.append(("warn", f"Only {cash_share:.0f}% in cash. Keep some ready."))
        else:
            notes.append(("ok", f"{cash_share:.0f}% of your money is in cash."))
        no_stop = [sym for sym in self.holdings if not self.has_stop(sym)]
        if no_stop:
            score -= min(20, 4 * len(no_stop))
            notes.append(("warn", f"{len(no_stop)} of {len(self.holdings)} holdings have no stop-loss."))
        score = max(0, min(100, score))
        label = "Healthy" if score >= 75 else ("Needs attention" if score >= 50 else "At risk")
        return dict(score=score, label=label, notes=notes)

    def signals(self):
        out = []
        for s in self.stocks.values():
            now_ma, prev_ma = self.ma20(s.sym), self.ma20(s.sym, back=1)
            closes = [x[3] for x in self.candles(s.sym, "1M")]
            span = (s.high - s.low) or 1
            if closes[-2] < prev_ma and s.price >= now_ma:
                out.append((5, s.sym, "Crossed above its 20-day average", "up"))
            elif closes[-2] > prev_ma and s.price <= now_ma:
                out.append((5, s.sym, "Fell below its 20-day average", "down"))
            elif abs(s.pct) >= 2:
                out.append((4, s.sym, f"Big move today: {pct_text(s.pct)}", "up" if s.pct > 0 else "down"))
            elif (s.high - s.price) / span <= 0.15:
                out.append((3, s.sym, "Trading near today's high", "up"))
            elif (s.price - s.low) / span <= 0.15:
                out.append((3, s.sym, "Trading near today's low", "down"))
            elif abs(s.open - s.prev) / s.prev >= 0.004:
                gap = "up" if s.open > s.prev else "down"
                out.append((2, s.sym, f"Opened with a gap {gap}", gap))
            else:
                side = "above" if s.price >= now_ma else "below"
                out.append((1, s.sym, f"Steady, {side} its 20-day average", "up" if side == "above" else "down"))
        out.sort(key=lambda t: (-t[0], t[1]))
        return [(sym, text, tone) for _, sym, text, tone in out]

    def _settle(self, order):
        sym = order["sym"]
        value = order["qty"] * order["price"]
        self.cash += -value if order["side"] == "BUY" else value
        q, avg = self.holdings.get(sym, [0, 0.0])
        if order["side"] == "BUY":
            new_q = q + order["qty"]
            avg = (q * avg + order["qty"] * order["price"]) / new_q
            q = new_q
        else:
            q -= order["qty"]
        if q > 0:
            self.holdings[sym] = [q, avg]
        else:
            self.holdings.pop(sym, None)


class FlatButton(tk.Label):
    def __init__(self, parent, app, text, command=None, active=False, color=None,
                 size=10, bold=False, padx=12, pady=6, base="panel"):
        self.app, self.command, self.active, self.color, self.base = app, command, active, color, base
        super().__init__(parent, text=text, padx=padx, pady=pady, cursor="hand2",
                         font=(FONT, size, "bold" if bold or color else "normal"))
        self.bind("<Enter>", lambda e: self._paint(hover=True))
        self.bind("<Leave>", lambda e: self._paint())
        self.bind("<Button-1>", lambda e: self.command and self.command())
        self._paint()

    def _paint(self, hover=False):
        c = self.app.c
        if self.color:
            bg, fg = self.color, "#ffffff"
        elif self.active:
            bg, fg = c["select"], c["text"]
        elif hover:
            bg, fg = c["hover"], c["text"]
        else:
            bg, fg = c[self.base], c["muted"]
        self.configure(bg=bg, fg=fg)

    def set_active(self, value):
        self.active = value
        self._paint()

    def set_color(self, color):
        self.color = color
        self._paint()


class TradeDesk:
    def __init__(self, root):
        self.root = root
        self.data = MarketData()
        self.tab, self.symbol = "Markets", "RELIANCE"
        self.tf, self.chart_type, self.sort_key = "1D", "Candle", "Symbol"
        self.show_gainers, self.live, self.show_ma = True, False, False
        self.order_state = dict(side="BUY", kind="Market", qty="1")
        self.game = UpDownGame()
        root.title("TradeDesk")
        root.geometry("1360x860")
        root.minsize(1180, 760)
        self.build()
        self._clock()
        self._live_loop()

    @property
    def c(self):
        return COLORS

    def build(self):
        for w in self.root.winfo_children():
            w.destroy()
        c = self.c
        self.root.configure(bg=c["border"])
        self.style_ttk()
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)
        self.build_topbar()
        self.build_ticker()
        self.content = tk.Frame(self.root, bg=c["border"])
        self.content.grid(row=2, column=0, sticky="nsew", pady=(0, 1))
        self.build_statusbar()
        self.show_tab(self.tab)

    def style_ttk(self):
        c, st = self.c, ttk.Style(self.root)
        st.theme_use("clam")
        st.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        st.configure("Treeview", background=c["panel"], fieldbackground=c["panel"],
                     foreground=c["text"], bordercolor=c["panel"], lightcolor=c["panel"],
                     darkcolor=c["panel"], rowheight=28, font=(FONT, 11))
        st.configure("Treeview.Heading", background=c["panel2"], foreground=c["muted"],
                     relief="flat", bordercolor=c["panel2"], lightcolor=c["panel2"],
                     darkcolor=c["panel2"], font=(FONT, 10, "bold"))
        st.map("Treeview", background=[("selected", c["select"])],
               foreground=[("selected", c["text"])])
        st.map("Treeview.Heading", background=[("active", c["hover"])])
        st.configure("Vertical.TScrollbar", background=c["panel2"], troughcolor=c["panel"],
                     bordercolor=c["panel"], arrowcolor=c["muted"], lightcolor=c["panel2"],
                     darkcolor=c["panel2"])

    def build_topbar(self):
        c = self.c
        bar = tk.Frame(self.root, bg=c["panel"])
        bar.grid(row=0, column=0, sticky="nsew", pady=(0, 1))
        tk.Label(bar, text="TradeDesk", bg=c["panel"], fg=c["accent"],
                 font=(FONT, 16, "bold"), padx=18).pack(side="left")
        self.tab_btns = {}
        for name in TABS:
            b = FlatButton(bar, self, name, lambda n=name: self.show_tab(n),
                           active=(name == self.tab), size=11, padx=16, pady=14)
            b.pack(side="left", fill="y")
            self.tab_btns[name] = b
        self.live_btn = FlatButton(bar, self, "", self.toggle_live, size=10, padx=14, pady=14)
        self.live_btn.pack(side="right", fill="y")
        self._paint_live()

    def build_ticker(self):
        c = self.c
        strip = tk.Frame(self.root, bg=c["border"])
        strip.grid(row=1, column=0, sticky="nsew", pady=(0, 1))
        self.ticker_cells = []
        for i, idx in enumerate(self.data.indices):
            strip.columnconfigure(i, weight=1, uniform="ticker")
            cell = tk.Frame(strip, bg=c["panel"])
            cell.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 1, 0))
            tk.Label(cell, text=idx.name, bg=c["panel"], fg=c["muted"],
                     font=(FONT, 9, "bold")).pack(anchor="w", padx=16, pady=(9, 0))
            line = tk.Frame(cell, bg=c["panel"])
            line.pack(anchor="w", padx=16, pady=(0, 9))
            val = tk.Label(line, bg=c["panel"], fg=c["text"], font=(FONT, 14, "bold"))
            val.pack(side="left")
            chg = tk.Label(line, bg=c["panel"], font=(FONT, 10, "bold"))
            chg.pack(side="left", padx=(8, 0))
            self.ticker_cells.append((idx, val, chg))
        self.refresh_ticker()

    def refresh_ticker(self):
        c = self.c
        for idx, val, chg in self.ticker_cells:
            arrow = "▲" if idx.change >= 0 else "▼"
            val.config(text=f"{idx.price:,.2f}")
            chg.config(text=f"{arrow} {pct_text(idx.pct)}",
                       fg=c["up"] if idx.change >= 0 else c["down"])

    def build_statusbar(self):
        c = self.c
        bar = tk.Frame(self.root, bg=c["panel"])
        bar.grid(row=3, column=0, sticky="nsew")
        self.market_lbl = tk.Label(bar, bg=c["panel"], font=(FONT, 10, "bold"), padx=16, pady=6)
        self.market_lbl.pack(side="left")
        tk.Label(bar, text="Demo mode · simulated data · no real orders are sent",
                 bg=c["panel"], fg=c["muted"], font=(FONT, 10)).pack(side="left")
        self.clock_lbl = tk.Label(bar, bg=c["panel"], fg=c["muted"], font=(FONT, 10), padx=16)
        self.clock_lbl.pack(side="right")
        self.funds_lbl = tk.Label(bar, bg=c["panel"], fg=c["text"], font=(FONT, 10, "bold"))
        self.funds_lbl.pack(side="right")
        self.notice_lbl = tk.Label(bar, bg=c["panel"], fg=c["accent"], font=(FONT, 10, "bold"), padx=16)
        self.notice_lbl.pack(side="left")
        self.refresh_status()

    def refresh_status(self):
        self.funds_lbl.config(text=f"Funds {inr(self.data.cash)}")
        self.notice_lbl.config(text=self.data.events[-1] if self.data.events else "")

    def _clock(self):
        now = datetime.now()
        if self.clock_lbl.winfo_exists():
            self.clock_lbl.config(text=now.strftime("%a %d %b %Y   %H:%M:%S IST"))
            is_open = market_open(now)
            self.market_lbl.config(text="● Market Open" if is_open else "● Market Closed",
                                   fg=self.c["up"] if is_open else self.c["down"])
        self.root.after(1000, self._clock)

    def _live_loop(self):
        if self.live:
            self.data.tick()
            self.refresh()
        self.root.after(2000, self._live_loop)

    def refresh(self):
        self.refresh_ticker()
        self.refresh_status()
        for fn in self.refreshers:
            fn()

    def toggle_live(self):
        self.live = not self.live
        self._paint_live()

    def _paint_live(self):
        self.live_btn.config(text="● Live prices: ON" if self.live else "○ Live prices: OFF")
        self.live_btn.set_active(self.live)

    def show_tab(self, name):
        self.tab = name
        for n, b in self.tab_btns.items():
            b.set_active(n == name)
        for w in self.content.winfo_children():
            w.destroy()
        self.refreshers, self.sym_listeners = [], []
        page = tk.Frame(self.content, bg=self.c["border"])
        page.pack(fill="both", expand=True)
        getattr(self, "page_" + name.lower())(page)

    def select_symbol(self, sym):
        self.symbol = sym
        for fn in self.sym_listeners:
            fn()

    def tile(self, parent, title, row, col, rowspan=1, colspan=1):
        c = self.c
        outer = tk.Frame(parent, bg=c["panel"])
        outer.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan,
                   sticky="nsew", padx=(0, 1), pady=(0, 1))
        head = tk.Frame(outer, bg=c["panel"])
        head.pack(fill="x", padx=14, pady=(10, 6))
        tk.Label(head, text=title.upper(), bg=c["panel"], fg=c["muted"],
                 font=(FONT, 9, "bold")).pack(side="left")
        body = tk.Frame(outer, bg=c["panel"])
        body.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        return head, body

    def label(self, parent, text="", fg="text", size=11, bold=False, **kw):
        c = self.c
        return tk.Label(parent, text=text, bg=kw.pop("bg", c["panel"]), fg=c.get(fg, fg),
                        font=(FONT, size, "bold" if bold else "normal"), **kw)

    def segmented(self, parent, options, current, on_pick, size=9):
        frame = tk.Frame(parent, bg=self.c["border"])
        btns = {}

        def pick(opt):
            for k, b in btns.items():
                b.set_active(k == opt)
            on_pick(opt)

        for i, opt in enumerate(options):
            frame.columnconfigure(i, weight=1, uniform="seg")
            b = FlatButton(frame, self, opt, lambda o=opt: pick(o), active=(opt == current),
                           size=size, padx=10, pady=3, base="panel2")
            b.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 1, 0))
            btns[opt] = b
        return frame

    def entry(self, parent, var, width=10, size=11):
        c = self.c
        return tk.Entry(parent, textvariable=var, width=width, bg=c["panel2"], fg=c["text"],
                        insertbackground=c["text"], relief="flat", highlightthickness=1,
                        highlightbackground=c["border"], highlightcolor=c["accent"],
                        disabledbackground=c["panel2"], disabledforeground=c["muted"],
                        font=(FONT, size))

    def search_box(self, parent, var):
        c = self.c
        box = tk.Frame(parent, bg=c["panel2"], highlightthickness=1,
                       highlightbackground=c["border"])
        self.label(box, "Search", fg="muted", size=9, bold=True, bg=c["panel2"],
                   padx=8).pack(side="left")
        tk.Entry(box, textvariable=var, bg=c["panel2"], fg=c["text"], insertbackground=c["text"],
                 relief="flat", highlightthickness=0, font=(FONT, 11)).pack(
            side="left", fill="x", expand=True, ipady=4)
        return box

    def table(self, parent, columns):
        c = self.c
        frame = tk.Frame(parent, bg=c["panel"])
        tree = ttk.Treeview(frame, columns=[col[0] for col in columns], show="headings",
                            selectmode="browse")
        for cid, head, width, anchor in columns:
            tree.heading(cid, text=head, anchor=anchor)
            tree.column(cid, width=width, minwidth=40, anchor=anchor, stretch=True)
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        for tag in ("up", "down"):
            tree.tag_configure(tag, foreground=c["text"])
        tree.tag_configure("muted", foreground=c["muted"])
        return frame, tree

    def fill_stocks(self, tree, getters, query):
        rows = self.data.filtered(query, self.sort_key)
        same = list(tree.get_children()) == [s.sym for s in rows]
        if not same:
            tree.delete(*tree.get_children())
        for s in rows:
            values = [g(s) for g in getters]
            tag = ("up" if s.change >= 0 else "down",)
            if same:
                tree.item(s.sym, values=values, tags=tag)
            else:
                tree.insert("", "end", iid=s.sym, values=values, tags=tag)
        if not same and tree.exists(self.symbol):
            tree.selection_set(self.symbol)
            tree.see(self.symbol)

    def stat_tile(self, parent, row, col, title, value, sub="", sub_color="muted"):
        _, body = self.tile(parent, title, row, col)
        self.label(body, value, size=20, bold=True).pack(anchor="w")
        if sub:
            self.label(body, sub, fg=sub_color, size=10, bold=True).pack(anchor="w")

    def pnl_color(self, x):
        return "up" if x >= 0 else "down"

    def page_markets(self, page):
        for col in range(4):
            page.columnconfigure(col, weight=1, uniform="m")
        page.rowconfigure(0, weight=3, uniform="r")
        page.rowconfigure(1, weight=2, uniform="r")
        self.chart_tile(page, 0, 0, colspan=3)
        self.watch_tile(page, 0, 3)
        self.order_tile(page, 1, 0)
        self.portfolio_tile(page, 1, 1)
        self.movers_tile(page, 1, 2)
        self.news_tile(page, 1, 3)

    def chart_tile(self, page, r, col, colspan):
        c = self.c
        head, body = self.tile(page, "Price chart", r, col, colspan=colspan)
        self.segmented(head, ["Candle", "Line"], self.chart_type, self.set_chart_type).pack(side="right")
        self.segmented(head, list(TIMEFRAMES), self.tf, self.set_tf).pack(side="right", padx=(0, 10))
        ma_btn = FlatButton(head, self, "MA 20", active=self.show_ma, size=9, padx=10, pady=3, base="panel2")

        def toggle_ma():
            self.show_ma = not self.show_ma
            ma_btn.set_active(self.show_ma)
            self.draw_chart()

        ma_btn.command = toggle_ma
        ma_btn.pack(side="right", padx=(0, 10))

        info = tk.Frame(body, bg=c["panel"])
        info.pack(fill="x")
        self.ch_sym = self.label(info, size=20, bold=True)
        self.ch_sym.pack(side="left")
        self.ch_name = self.label(info, fg="muted", size=11)
        self.ch_name.pack(side="left", padx=(10, 0), pady=(6, 0))
        self.ch_chg = self.label(info, size=12, bold=True)
        self.ch_chg.pack(side="right", pady=(6, 0))
        self.ch_px = self.label(info, size=20, bold=True)
        self.ch_px.pack(side="right", padx=(0, 10))

        ohlc = tk.Frame(body, bg=c["panel"])
        ohlc.pack(fill="x", pady=(2, 0))
        self.ch_ohlc = self.label(ohlc, fg="muted", size=10)
        self.ch_ohlc.pack(side="left")

        self.canvas = tk.Canvas(body, bg=c["panel"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, pady=(8, 0))
        self.canvas.bind("<Configure>", lambda e: self.draw_chart())
        self.update_chart()
        self.refreshers.append(self.update_chart)
        self.sym_listeners.append(self.update_chart)

    def set_tf(self, tf):
        self.tf = tf
        self.draw_chart()

    def set_chart_type(self, kind):
        self.chart_type = kind
        self.draw_chart()

    def update_chart(self):
        s = self.data.stocks[self.symbol]
        self.ch_sym.config(text=s.sym)
        self.ch_name.config(text=s.name)
        self.ch_px.config(text=inr(s.price))
        self.ch_chg.config(text=f"{s.change:+,.2f}  ({pct_text(s.pct)})",
                           fg=self.c[self.pnl_color(s.change)])
        self.ch_ohlc.config(text=f"O {s.open:,.2f}    H {s.high:,.2f}    L {s.low:,.2f}    "
                                 f"Prev {s.prev:,.2f}    Vol {s.volume:,}")
        self.draw_chart()

    def x_label(self, i, n):
        now = datetime.now()
        if self.tf == "1D":
            t = 9 * 60 + 15 + 5 * i
            return f"{t // 60:02d}:{t % 60:02d}"
        if self.tf == "1W":
            return ["Mon", "Tue", "Wed", "Thu", "Fri"][min(i * 5 // n, 4)]
        if self.tf == "1M":
            return (now - timedelta(days=round((n - 1 - i) * 1.4))).strftime("%d %b")
        return (now - timedelta(weeks=n - 1 - i)).strftime("%b %y")

    def draw_chart(self):
        cv, c = self.canvas, self.c
        if not cv.winfo_exists():
            return
        cv.delete("all")
        w, h = cv.winfo_width(), cv.winfo_height()
        if w < 80 or h < 80:
            return
        data = self.data.candles(self.symbol, self.tf)
        left, right, top, bottom = 4, 78, 8, 24
        pw, ph = w - left - right, h - top - bottom
        hi, lo = max(x[1] for x in data), min(x[2] for x in data)
        pad = (hi - lo) * 0.06 or 1
        hi, lo = hi + pad, lo - pad

        def y(p):
            return top + (hi - p) / (hi - lo) * ph

        for i in range(6):
            p = lo + (hi - lo) * i / 5
            cv.create_line(left, y(p), left + pw, y(p), fill=c["border"], dash=(2, 4))
            cv.create_text(left + pw + 10, y(p), text=f"{p:,.2f}", anchor="w",
                           fill=c["muted"], font=(FONT, 9))

        n = len(data)
        step = pw / n
        for i in range(0, n, max(1, n // 6)):
            cx = left + step * i + step / 2
            cv.create_text(max(cx, left + 18), top + ph + 6, text=self.x_label(i, n), anchor="n",
                           fill=c["muted"], font=(FONT, 9))

        if self.chart_type == "Candle":
            bw = max(1.0, step * 0.32)
            for i, (o, hh, ll, cl) in enumerate(data):
                cx = left + step * i + step / 2
                col = c["up"] if cl >= o else c["down"]
                cv.create_line(cx, y(hh), cx, y(ll), fill=col)
                y1, y2 = y(o), y(cl)
                if abs(y1 - y2) < 1:
                    y2 = y1 + 1
                cv.create_rectangle(cx - bw, y1, cx + bw, y2, fill=col, outline=col)
        else:
            pts = []
            for i, candle in enumerate(data):
                pts += [left + step * i + step / 2, y(candle[3])]
            cv.create_line(*pts, fill=c["accent"], width=2, smooth=False)

        if self.show_ma and n >= 20:
            closes = [x[3] for x in data]
            pts = []
            for i in range(19, n):
                pts += [left + step * i + step / 2, y(sum(closes[i - 19:i + 1]) / 20)]
            cv.create_line(*pts, fill=c["muted"], width=1)

        last = data[-1][3]
        col = c["up"] if last >= data[0][0] else c["down"]
        cv.create_line(left, y(last), left + pw, y(last), fill=col, dash=(4, 3))
        cv.create_rectangle(left + pw + 2, y(last) - 10, w, y(last) + 10, fill=col, outline=col)
        cv.create_text(left + pw + 10, y(last), text=f"{last:,.2f}", anchor="w",
                       fill="#ffffff", font=(FONT, 9, "bold"))

    def watch_tile(self, page, r, col):
        head, body = self.tile(page, "Watchlist", r, col)
        query = tk.StringVar()
        getters = [lambda s: s.sym, lambda s: f"{s.price:,.2f}", lambda s: pct_text(s.pct)]
        frame, tree = self.table(body, [("sym", "Symbol", 100, "w"), ("ltp", "LTP", 80, "e"),
                                        ("chg", "Chg %", 70, "e")])

        def fill():
            self.fill_stocks(tree, getters, query.get())

        sort_btn = FlatButton(head, self, f"Sort: {self.sort_key}", size=9, padx=8, pady=2)

        def cycle():
            keys = list(SORTS)
            self.sort_key = keys[(keys.index(self.sort_key) + 1) % len(keys)]
            sort_btn.config(text=f"Sort: {self.sort_key}")
            fill()

        sort_btn.command = cycle
        sort_btn.pack(side="right")
        self.search_box(body, query).pack(fill="x", pady=(0, 8))
        frame.pack(fill="both", expand=True)
        query.trace_add("write", lambda *a: fill())
        tree.bind("<<TreeviewSelect>>",
                  lambda e: tree.selection() and self.select_symbol(tree.selection()[0]))
        fill()
        self.refreshers.append(fill)

    def order_tile(self, page, r, col):
        c, st = self.c, self.order_state
        head, body = self.tile(page, "Place order", r, col)
        sym_lbl = self.label(head, fg="accent", size=10, bold=True)
        sym_lbl.pack(side="right")
        body.columnconfigure(1, weight=1)

        qty_var = tk.StringVar(value=st["qty"])
        price_var = tk.StringVar(value=f"{self.data.stocks[self.symbol].price:.2f}")
        place_btn = FlatButton(body, self, "", None, color=c["accent"], size=11, pady=8)

        def pick_side(side):
            st["side"] = side
            update()

        def pick_kind(kind):
            st["kind"] = kind
            price_lbl.config(text="Trigger" if kind == "Stop-loss" else "Price")
            if kind != "Market":
                price_var.set(f"{self.data.stocks[self.symbol].price:.2f}")
            update()

        self.segmented(body, ["BUY", "SELL"], st["side"], pick_side, size=10).grid(
            row=0, column=0, columnspan=2, sticky="ew")

        self.label(body, "Quantity", fg="muted", size=10).grid(row=1, column=0, sticky="w", pady=(10, 0))
        qrow = tk.Frame(body, bg=c["panel"])
        qrow.grid(row=1, column=1, sticky="e", pady=(10, 0))

        def bump(d):
            try:
                qty_var.set(str(max(1, int(qty_var.get()) + d)))
            except ValueError:
                qty_var.set("1")

        FlatButton(qrow, self, "−", lambda: bump(-1), size=11, padx=8, pady=1,
                   base="panel2").pack(side="left")
        self.entry(qrow, qty_var, width=6).pack(side="left", padx=1, ipady=2)
        FlatButton(qrow, self, "+", lambda: bump(1), size=11, padx=8, pady=1,
                   base="panel2").pack(side="left")

        self.segmented(body, ["Market", "Limit", "Stop-loss"], st["kind"], pick_kind).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        price_lbl = self.label(body, "Trigger" if st["kind"] == "Stop-loss" else "Price", fg="muted", size=10)
        price_lbl.grid(row=3, column=0, sticky="w", pady=(10, 0))
        price_entry = self.entry(body, price_var, width=12)
        price_entry.grid(row=3, column=1, sticky="e", pady=(10, 0), ipady=2)

        self.label(body, "Est. value", fg="muted", size=10).grid(row=4, column=0, sticky="w", pady=(8, 0))
        total_lbl = self.label(body, size=11, bold=True)
        total_lbl.grid(row=4, column=1, sticky="e", pady=(8, 0))
        place_btn.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        def update_total(*_):
            st["qty"] = qty_var.get()
            try:
                total_lbl.config(text=inr(int(qty_var.get()) * float(price_var.get())), fg=c["text"])
            except ValueError:
                total_lbl.config(text="invalid", fg=c["down"])

        def update():
            s = self.data.stocks[self.symbol]
            sym_lbl.config(text=f"{s.sym}  {s.price:,.2f}")
            if st["kind"] == "Market":
                price_var.set(f"{s.price:.2f}")
                price_entry.config(state="disabled")
            else:
                price_entry.config(state="normal")
            place_btn.config(text=f"{st['side']}  {s.sym}")
            update_total()

        place_btn.command = lambda: self.place_order(qty_var.get(), price_var.get())
        qty_var.trace_add("write", update_total)
        price_var.trace_add("write", update_total)
        update()
        self.refreshers.append(update)

        def on_symbol():
            price_var.set(f"{self.data.stocks[self.symbol].price:.2f}")
            update()

        self.sym_listeners.append(on_symbol)

    def place_order(self, qty_txt, price_txt):
        st, s = self.order_state, self.data.stocks[self.symbol]
        try:
            qty = int(qty_txt)
            price = float(price_txt)
            if qty <= 0 or price <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid order", "Quantity and price must be positive numbers.")
            return
        held = self.data.holdings.get(s.sym, [0, 0])[0]
        if st["side"] == "SELL" and qty > held:
            messagebox.showerror("Not enough shares", f"You hold {held} shares of {s.sym}.")
            return
        if st["side"] == "BUY" and qty * price > self.data.cash:
            messagebox.showerror("Not enough funds", f"Available funds: {inr(self.data.cash)}.")
            return
        if not self.review_order(st["side"], qty, price, st["kind"], s.sym):
            return
        status = "Executed" if st["kind"] == "Market" else "Open"
        self.data.place(dict(time=datetime.now().strftime("%H:%M:%S"), sym=s.sym, side=st["side"],
                             qty=qty, kind=st["kind"], price=price, status=status))
        messagebox.showinfo("Order placed", f"{st['side']} {qty} {s.sym} — {status}.")
        self.refresh()

    def review_order(self, side, qty, price, kind, sym):
        c = self.c
        verdict, notes = self.data.coach(side, qty, price, kind, sym)
        rows, total = self.data.charges(side, qty, price)
        value = qty * price
        result = {"ok": False}
        win = tk.Toplevel(self.root)
        win.title("Review order")
        win.configure(bg=c["panel"])
        win.transient(self.root)
        win.resizable(False, False)
        box = tk.Frame(win, bg=c["panel"])
        box.pack(fill="both", expand=True, padx=24, pady=20)

        top = tk.Frame(box, bg=c["panel"])
        top.pack(fill="x")
        self.label(top, f"{side} {qty} × {sym}", size=20, bold=True).pack(side="left")
        tone = {"Safe": "up", "Caution": "warn", "Risky": "down"}[verdict]
        tk.Label(top, text=verdict.upper(), bg=c[tone], fg="#ffffff", font=(FONT, 11, "bold"),
                 padx=12, pady=4).pack(side="right")
        self.label(box, f"{kind} order at {inr(price)}  ·  value {inr(value)}", fg="muted",
                   size=11).pack(anchor="w", pady=(2, 14))

        self.label(box, "TRADE COACH", fg="muted", size=9, bold=True).pack(anchor="w", pady=(0, 6))
        for level, text in notes:
            row = tk.Frame(box, bg=c["panel"])
            row.pack(fill="x", pady=2)
            icon, col = {"ok": ("✓", "up"), "warn": ("!", "warn"), "risk": ("✗", "down")}[level]
            self.label(row, icon, fg=col, size=12, bold=True, width=2).pack(side="left", anchor="n")
            self.label(row, text, size=11, wraplength=440, justify="left").pack(side="left", anchor="w")

        tk.Frame(box, bg=c["border"], height=1).pack(fill="x", pady=14)
        self.label(box, "TRUE COST IN INDIA (DELIVERY TRADE)", fg="muted", size=9, bold=True).pack(
            anchor="w", pady=(0, 6))
        lines = [(name, inr(v), "muted", False) for name, v in rows]
        lines.append(("Total charges", inr(total), "text", True))
        if side == "BUY":
            lines.append(("You pay", inr(value + total), "text", True))
            lines.append(("Break-even price", inr(self.data.break_even(qty, price)), "warn", True))
        else:
            q, avg = self.data.holdings.get(sym, [0, 0.0])
            lines.append(("You receive", inr(value - total), "text", True))
            net = (price - avg) * qty - total
            lines.append(("Profit after charges", f"{net:+,.2f}", self.pnl_color(net), True))
        for name, text, col, bold in lines:
            row = tk.Frame(box, bg=c["panel"])
            row.pack(fill="x", pady=1)
            self.label(row, name, fg="text" if bold else "muted", size=11, bold=bold).pack(side="left")
            self.label(row, text, fg=col, size=11, bold=bold).pack(side="right")
        if side == "BUY":
            self.label(box, "The price has to rise above the break-even price before you make any profit.",
                       fg="muted", size=9, wraplength=460, justify="left").pack(anchor="w", pady=(6, 0))

        def close(ok):
            result["ok"] = ok
            win.destroy()

        buttons = tk.Frame(box, bg=c["panel"])
        buttons.pack(fill="x", pady=(18, 0))
        buttons.columnconfigure((0, 1), weight=1, uniform="rb")
        FlatButton(buttons, self, "Cancel", lambda: close(False), size=11, pady=9,
                   base="panel2").grid(row=0, column=0, sticky="ew", padx=(0, 6))
        FlatButton(buttons, self, f"Place {side.lower()} order", lambda: close(True), color=c["accent"],
                   size=11, pady=9).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        win.bind("<Escape>", lambda e: close(False))
        win.bind("<Return>", lambda e: close(True))
        win.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - win.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - win.winfo_height()) // 3
        win.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        win.grab_set()
        win.focus_set()
        self.root.wait_window(win)
        return result["ok"]

    def page_insights(self, page):
        for col in range(4):
            page.columnconfigure(col, weight=1, uniform="i")
        page.rowconfigure(0, weight=1, uniform="ir")
        page.rowconfigure(1, weight=1, uniform="ir")
        self.mood_tile(page, 0, 0)
        self.sector_tile(page, 0, 1, 2)
        self.health_tile(page, 0, 3)
        self.signals_tile(page, 1, 0, 2)
        self.game_tile(page, 1, 2, 2)

    def mood_tile(self, page, r, col):
        c = self.c
        _, body = self.tile(page, "Market mood", r, col)
        cv = tk.Canvas(body, bg=c["panel"], highlightthickness=0, height=140)
        cv.pack(fill="x")
        score_lbl = self.label(body, size=22, bold=True)
        score_lbl.pack(anchor="center")
        info = tk.Frame(body, bg=c["panel"])
        info.pack(fill="x", pady=(8, 0))
        bands = [(0, 25, c["down"]), (25, 45, blend(c["down"], "#ffffff", 0.55)), (45, 55, "#cfcfcf"),
                 (55, 75, blend(c["up"], "#ffffff", 0.55)), (75, 100, c["up"])]

        def render():
            if not cv.winfo_exists():
                return
            m = self.data.mood()
            cv.delete("all")
            w = max(cv.winfo_width(), 200)
            radius = min(w / 2 - 14, 118)
            cx, cy = w / 2, radius + 14
            for a, b, colour in bands:
                cv.create_arc(cx - radius, cy - radius, cx + radius, cy + radius, start=180 - b * 1.8,
                              extent=(b - a) * 1.8, style="arc", width=18, outline=colour)
            angle = math.radians(180 - m["score"] * 1.8)
            cv.create_line(cx, cy, cx + (radius - 26) * math.cos(angle), cy - (radius - 26) * math.sin(angle),
                           width=3, fill=c["text"])
            cv.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill=c["text"], outline="")
            cv.configure(height=cy + 8)
            score_lbl.config(text=f"{m['score']}  ·  {m['label']}")
            for wdg in info.winfo_children():
                wdg.destroy()
            for name, text, tone in (("Advancing / declining", f"{m['up']} / {m['down']}", "text"),
                                     ("Average move", pct_text(m["avg"]), self.pnl_color(m["avg"])),
                                     ("NIFTY 50", pct_text(m["nifty"]), self.pnl_color(m["nifty"]))):
                row = tk.Frame(info, bg=c["panel"])
                row.pack(fill="x", pady=1)
                self.label(row, name, fg="muted", size=10).pack(side="left")
                self.label(row, text, fg=tone, size=10, bold=True).pack(side="right")

        cv.bind("<Configure>", lambda e: render())
        self.refreshers.append(render)

    def heat(self, pct):
        base = self.c["up"] if pct >= 0 else self.c["down"]
        return blend("#ffffff", base, 0.12 + min(abs(pct) / 2.5, 1) * 0.83)

    def sector_tile(self, page, r, col, span):
        c = self.c
        head, body = self.tile(page, "Sector heatmap", r, col, colspan=span)
        self.label(head, "Green is up today, red is down. Darker means a bigger move.", fg="muted",
                   size=9).pack(side="right")

        def render():
            for w in body.winfo_children():
                w.destroy()
            for i, (name, pct, stocks) in enumerate(self.data.sectors()):
                body.columnconfigure(i % 4, weight=1, uniform="s")
                body.rowconfigure(i // 4, weight=1, uniform="sr")
                bg = self.heat(pct)
                fg = "#ffffff" if abs(pct) >= 1.0 else c["text"]
                cell = tk.Frame(body, bg=bg)
                cell.grid(row=i // 4, column=i % 4, sticky="nsew", padx=3, pady=3)
                tk.Label(cell, text=name, bg=bg, fg=fg, font=(FONT, 12, "bold")).pack(anchor="w", padx=12,
                                                                                      pady=(10, 0))
                tk.Label(cell, text=pct_text(pct), bg=bg, fg=fg, font=(FONT, 18, "bold")).pack(anchor="w",
                                                                                               padx=12)
                tk.Label(cell, text=", ".join(s.sym for s in stocks), bg=bg, fg=fg, font=(FONT, 9),
                         wraplength=180, justify="left").pack(anchor="w", padx=12, pady=(0, 10))

        render()
        self.refreshers.append(render)

    def note_rows(self, parent, notes, wrap=260):
        c = self.c
        for level, text in notes:
            row = tk.Frame(parent, bg=c["panel"])
            row.pack(fill="x", pady=2)
            icon, col = {"ok": ("✓", "up"), "warn": ("!", "warn"), "risk": ("✗", "down")}[level]
            self.label(row, icon, fg=col, size=11, bold=True, width=2).pack(side="left", anchor="n")
            self.label(row, text, size=10, wraplength=wrap, justify="left").pack(side="left", anchor="w")

    def health_tile(self, page, r, col):
        c = self.c
        _, body = self.tile(page, "Portfolio health", r, col)

        def render():
            for w in body.winfo_children():
                w.destroy()
            h = self.data.health()
            tone = "up" if h["score"] >= 75 else ("warn" if h["score"] >= 50 else "down")
            line = tk.Frame(body, bg=c["panel"])
            line.pack(fill="x")
            self.label(line, str(h["score"]), size=28, bold=True).pack(side="left")
            self.label(line, " / 100", fg="muted", size=12).pack(side="left", anchor="s", pady=(0, 6))
            self.label(line, h["label"], fg=tone, size=12, bold=True).pack(side="right", anchor="s", pady=(0, 6))
            bar = tk.Canvas(body, height=8, bg=c["panel2"], highlightthickness=0)
            bar.pack(fill="x", pady=(4, 10))
            bar.bind("<Configure>", lambda e: (bar.delete("all"), bar.create_rectangle(
                0, 0, e.width * h["score"] / 100, 8, fill=c[tone], outline="")))
            self.note_rows(body, h["notes"])

        render()
        self.refreshers.append(render)

    def signals_tile(self, page, r, col, span):
        c = self.c
        head, body = self.tile(page, "Signals", r, col, colspan=span)
        self.label(head, "Rule-based checks on every stock. Click one to open its chart.", fg="muted",
                   size=9).pack(side="right")

        def open_chart(sym):
            self.symbol = sym
            self.show_tab("Markets")

        def render():
            for w in body.winfo_children():
                w.destroy()
            for sym, text, tone in self.data.signals()[:8]:
                row = tk.Frame(body, bg=c["panel"], cursor="hand2")
                row.pack(fill="x", pady=1)
                dot = self.label(row, "▲" if tone == "up" else "▼", fg=tone, size=10)
                dot.pack(side="left")
                name = self.label(row, sym, size=11, bold=True, width=12, anchor="w")
                name.pack(side="left", padx=(6, 0))
                desc = self.label(row, text, size=11)
                desc.pack(side="left")
                s = self.data.stocks[sym]
                px = self.label(row, f"{s.price:,.2f}  {pct_text(s.pct)}", fg=self.pnl_color(s.pct), size=10)
                px.pack(side="right")
                for wdg in (row, dot, name, desc, px):
                    wdg.bind("<Button-1>", lambda e, sy=sym: open_chart(sy))

        render()
        self.refreshers.append(render)

    def game_tile(self, page, r, col, span):
        c, g = self.c, self.game
        head, body = self.tile(page, "Practice: up or down?", r, col, colspan=span)
        score = self.label(head, fg="muted", size=10, bold=True)
        score.pack(side="right")
        cv = tk.Canvas(body, bg=c["panel"], highlightthickness=0)
        controls = tk.Frame(body, bg=c["panel"])
        controls.pack(side="bottom", fill="x", pady=(8, 0))
        cv.pack(fill="both", expand=True)
        feedback = self.label(controls, size=10, wraplength=330, justify="left")
        feedback.pack(side="left", fill="x", expand=True, anchor="w")

        def draw():
            if not cv.winfo_exists():
                return
            cv.delete("all")
            w, h = cv.winfo_width(), cv.winfo_height()
            if w < 80 or h < 60:
                return
            shown = g.candles[:41 if g.revealed else 40]
            hi, lo = max(x[1] for x in g.candles), min(x[2] for x in g.candles)
            step = (w - 20) / 41

            def y(p):
                return 6 + (hi - p) / ((hi - lo) or 1) * (h - 12)

            for i, (o, hh, ll, cl) in enumerate(shown):
                cx = 10 + step * i + step / 2
                colour = c["up"] if cl >= o else c["down"]
                cv.create_line(cx, y(hh), cx, y(ll), fill=colour)
                y1, y2 = y(o), y(cl)
                cv.create_rectangle(cx - step * 0.3, min(y1, y2), cx + step * 0.3, max(y1, y2) + 1,
                                    fill=colour, outline=colour)
            nx = 10 + step * 40 + step / 2
            if g.revealed:
                cv.create_rectangle(nx - step * 0.6, 2, nx + step * 0.6, h - 2, outline=c["text"], dash=(3, 2))
            else:
                cv.create_text(nx, h / 2, text="?", font=(FONT, 20, "bold"), fill=c["muted"])
            score.config(text=f"Score {g.score}/{g.rounds}   Streak {g.streak}   Best {g.best}")
            if not g.revealed:
                feedback.config(text="Will the next candle close higher or lower? Read the trend, then guess.",
                                fg=c["text"])
            else:
                correct, actual_up = g.last
                trend = g.recent_trend()
                tip = (f"The last 10 candles were trending {trend}. Trends often continue."
                       if (trend == "up") == actual_up else
                       f"The last 10 candles were trending {trend}, but this one went against it.")
                feedback.config(text=f"{'Correct' if correct else 'Wrong'}: it went {'up' if actual_up else 'down'}. {tip}",
                                fg=c["up"] if correct else c["down"])

        def guess(up):
            g.guess(up)
            draw()

        def next_round():
            g.new_round()
            draw()

        FlatButton(controls, self, "Next chart", next_round, size=10, padx=12, pady=6,
                   base="panel2").pack(side="right")
        FlatButton(controls, self, "▼ Down", lambda: guess(False), color=c["down"], size=10,
                   padx=14, pady=6).pack(side="right", padx=6)
        FlatButton(controls, self, "▲ Up", lambda: guess(True), color=c["up"], size=10,
                   padx=14, pady=6).pack(side="right")
        cv.bind("<Configure>", lambda e: draw())

    def portfolio_tile(self, page, r, col):
        c = self.c
        head, body = self.tile(page, "Portfolio", r, col)
        FlatButton(head, self, "Open ›", lambda: self.show_tab("Portfolio"), size=9,
                   padx=8, pady=2).pack(side="right")

        def render():
            for w in body.winfo_children():
                w.destroy()
            p = self.data.summary()
            self.label(body, "Current value", fg="muted", size=10).pack(anchor="w")
            self.label(body, inr(p["current"]), size=20, bold=True).pack(anchor="w")
            self.label(body, f"{p['pnl']:+,.2f}  ({pct_text(p['pct'])})  overall",
                       fg=self.pnl_color(p["pnl"]), size=10, bold=True).pack(anchor="w")
            tk.Frame(body, bg=c["border"], height=1).pack(fill="x", pady=8)
            for sym, (q, avg) in list(self.data.holdings.items())[:5]:
                s = self.data.stocks[sym]
                row = tk.Frame(body, bg=c["panel"])
                row.pack(fill="x", pady=1)
                self.label(row, sym, size=10, bold=True).pack(side="left")
                self.label(row, f" ×{q}", fg="muted", size=10).pack(side="left")
                gain = (s.price - avg) * q
                self.label(row, f"{gain:+,.0f}", fg=self.pnl_color(gain), size=10,
                           bold=True).pack(side="right")

        render()
        self.refreshers.append(render)

    def movers_tile(self, page, r, col):
        c = self.c
        head, body = self.tile(page, "Top movers", r, col)

        def render():
            for w in body.winfo_children():
                w.destroy()
            for s in self.data.movers(self.show_gainers):
                row = tk.Frame(body, bg=c["panel"], cursor="hand2")
                row.pack(fill="x", pady=2)
                a = self.label(row, s.sym, size=11, bold=True)
                a.pack(side="left")
                b = self.label(row, pct_text(s.pct), fg=self.pnl_color(s.pct), size=11, bold=True)
                b.pack(side="right")
                d = self.label(row, f"{s.price:,.2f}", fg="muted", size=10)
                d.pack(side="right", padx=10)
                for wdg in (row, a, b, d):
                    wdg.bind("<Button-1>", lambda e, sym=s.sym: self.select_symbol(sym))

        def pick(opt):
            self.show_gainers = opt == "Gainers"
            render()

        self.segmented(head, ["Gainers", "Losers"],
                       "Gainers" if self.show_gainers else "Losers", pick).pack(side="right")
        render()
        self.refreshers.append(render)

    def news_tile(self, page, r, col):
        c = self.c
        head, body = self.tile(page, "Market news", r, col)
        FlatButton(head, self, "All ›", lambda: self.show_tab("News"), size=9,
                   padx=8, pady=2).pack(side="right")
        for cat, title, _ in NEWS[:4]:
            self.label(body, cat.upper(), fg="accent", size=8, bold=True).pack(anchor="w", pady=(4, 0))
            self.label(body, title, size=10, justify="left", anchor="w",
                       wraplength=250).pack(anchor="w", fill="x")

    def page_watchlist(self, page):
        page.columnconfigure(0, weight=3, uniform="w")
        page.columnconfigure(1, weight=1, uniform="w")
        page.rowconfigure(0, weight=1)
        head, body = self.tile(page, "All instruments", 0, 0)
        query = tk.StringVar()
        cols = [("sym", "Symbol", 110, "w"), ("name", "Company", 210, "w"), ("ltp", "LTP", 90, "e"),
                ("chg", "Change", 80, "e"), ("pct", "Chg %", 80, "e"), ("open", "Open", 90, "e"),
                ("high", "High", 90, "e"), ("low", "Low", 90, "e"), ("vol", "Volume", 110, "e")]
        getters = [lambda s: s.sym, lambda s: s.name, lambda s: f"{s.price:,.2f}",
                   lambda s: f"{s.change:+,.2f}", lambda s: pct_text(s.pct),
                   lambda s: f"{s.open:,.2f}", lambda s: f"{s.high:,.2f}",
                   lambda s: f"{s.low:,.2f}", lambda s: f"{s.volume:,}"]
        frame, tree = self.table(body, cols)

        def fill():
            self.fill_stocks(tree, getters, query.get())

        def pick_sort(key):
            self.sort_key = key
            fill()

        self.segmented(head, list(SORTS), self.sort_key, pick_sort).pack(side="right")
        self.label(head, "Sort by", fg="muted", size=9).pack(side="right", padx=8)
        self.search_box(body, query).pack(fill="x", pady=(0, 8))
        frame.pack(fill="both", expand=True)
        query.trace_add("write", lambda *a: fill())
        tree.bind("<<TreeviewSelect>>",
                  lambda e: tree.selection() and self.select_symbol(tree.selection()[0]))
        fill()
        self.refreshers.append(fill)
        self.quote_tile(page, 0, 1)

    def quote_tile(self, page, r, col):
        c = self.c
        _, body = self.tile(page, "Quote", r, col)
        alert_var = tk.StringVar()

        def set_alert():
            try:
                price = float(alert_var.get())
                if price <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Price alert", "Enter a positive price.")
                return
            self.data.add_alert(self.symbol, price)
            alert_var.set("")
            self.refresh_status()

        alert_row = tk.Frame(body, bg=c["panel"])
        alert_row.pack(side="bottom", fill="x", pady=(8, 0))
        self.label(alert_row, "Price alert", fg="muted", size=10).pack(side="left")
        FlatButton(alert_row, self, "Set", set_alert, size=10, padx=10, pady=2,
                   base="panel2").pack(side="right")
        self.entry(alert_row, alert_var, width=9).pack(side="right", padx=(0, 4), ipady=2)
        top = tk.Frame(body, bg=c["panel"])
        top.pack(fill="both", expand=True)

        def render():
            for w in top.winfo_children():
                w.destroy()
            s = self.data.stocks[self.symbol]
            self.label(top, s.sym, size=20, bold=True).pack(anchor="w")
            self.label(top, s.name, fg="muted", size=10).pack(anchor="w")
            self.label(top, inr(s.price), size=24, bold=True).pack(anchor="w", pady=(6, 0))
            self.label(top, f"{s.change:+,.2f}  ({pct_text(s.pct)})", fg=self.pnl_color(s.change),
                       size=11, bold=True).pack(anchor="w")
            tk.Frame(top, bg=c["border"], height=1).pack(fill="x", pady=8)
            for k, v in [("Open", s.open), ("High", s.high), ("Low", s.low), ("Prev close", s.prev)]:
                row = tk.Frame(top, bg=c["panel"])
                row.pack(fill="x", pady=2)
                self.label(row, k, fg="muted", size=10).pack(side="left")
                self.label(row, f"{v:,.2f}", size=10, bold=True).pack(side="right")
            row = tk.Frame(top, bg=c["panel"])
            row.pack(fill="x", pady=2)
            self.label(row, "Volume", fg="muted", size=10).pack(side="left")
            self.label(row, f"{s.volume:,}", size=10, bold=True).pack(side="right")

            self.label(top, "Day range", fg="muted", size=10).pack(anchor="w", pady=(8, 4))
            bar = tk.Canvas(top, height=10, bg=c["panel2"], highlightthickness=0)
            bar.pack(fill="x")

            def draw(e, s=s):
                bar.delete("all")
                frac = (s.price - s.low) / ((s.high - s.low) or 1)
                bar.create_rectangle(0, 0, e.width * frac, 10, fill=c["accent"], outline="")

            bar.bind("<Configure>", draw)
            self.label(top, "Market depth", fg="muted", size=10).pack(anchor="w", pady=(8, 2))
            depth = tk.Frame(top, bg=c["panel"])
            depth.pack(fill="x")
            depth.columnconfigure((0, 1, 2, 3), weight=1, uniform="d")
            for i, text in enumerate(("Bid", "Qty", "Ask", "Qty")):
                self.label(depth, text, fg="muted", size=9, bold=True).grid(row=0, column=i, sticky="e")
            for r_i, (bid, bid_q, ask, ask_q) in enumerate(self.data.depth(s.sym), 1):
                for i, (val, fg) in enumerate(((f"{bid:,.2f}", "up"), (f"{bid_q:,}", "text"),
                                               (f"{ask:,.2f}", "down"), (f"{ask_q:,}", "text"))):
                    self.label(depth, val, fg=fg, size=9).grid(row=r_i, column=i, sticky="e")
            btns = tk.Frame(top, bg=c["panel"])
            btns.pack(fill="x", pady=(8, 0))
            btns.columnconfigure((0, 1), weight=1, uniform="b")
            FlatButton(btns, self, "BUY", lambda: self.trade_from_quote("BUY"), color=c["accent"],
                       pady=8).grid(row=0, column=0, sticky="ew", padx=(0, 4))
            FlatButton(btns, self, "SELL", lambda: self.trade_from_quote("SELL"), color=c["accent"],
                       pady=8).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        render()
        self.refreshers.append(render)
        self.sym_listeners.append(render)

    def trade_from_quote(self, side):
        self.order_state["side"] = side
        self.show_tab("Markets")

    def page_portfolio(self, page):
        for col in range(4):
            page.columnconfigure(col, weight=1, uniform="p")
        page.rowconfigure(1, weight=1)
        p = self.data.summary()
        self.stat_tile(page, 0, 0, "Invested", inr(p["invested"]),
                       f"{len(self.data.holdings)} holdings")
        self.stat_tile(page, 0, 1, "Current value", inr(p["current"]), "marked to market")
        self.stat_tile(page, 0, 2, "Total P&L", f"{p['pnl']:+,.2f}", pct_text(p["pct"]),
                       self.pnl_color(p["pnl"]))
        self.stat_tile(page, 0, 3, "Today's P&L", f"{p['day']:+,.2f}", "since previous close",
                       self.pnl_color(p["day"]))

        _, body = self.tile(page, "Holdings", 1, 0, colspan=3)
        cols = [("sym", "Symbol", 110, "w"), ("qty", "Qty", 60, "e"), ("avg", "Avg cost", 100, "e"),
                ("ltp", "LTP", 100, "e"), ("inv", "Invested", 120, "e"), ("cur", "Current", 120, "e"),
                ("pnl", "P&L", 110, "e"), ("pct", "P&L %", 80, "e")]
        frame, tree = self.table(body, cols)
        frame.pack(fill="both", expand=True)
        for sym, (q, avg) in self.data.holdings.items():
            s = self.data.stocks[sym]
            pnl = (s.price - avg) * q
            tree.insert("", "end", values=(sym, q, f"{avg:,.2f}", f"{s.price:,.2f}",
                                           f"{q * avg:,.2f}", f"{q * s.price:,.2f}",
                                           f"{pnl:+,.2f}", pct_text((s.price - avg) / avg * 100)),
                        tags=(self.pnl_color(pnl),))
        self.allocation_tile(page, 1, 3)

    def allocation_tile(self, page, r, col):
        c = self.c
        _, body = self.tile(page, "Allocation", r, col)
        total = self.data.summary()["current"] or 1
        rows = sorted(((sym, q * self.data.stocks[sym].price) for sym, (q, _) in
                       self.data.holdings.items()), key=lambda t: t[1], reverse=True)
        palette = ["#111111", "#444444", "#666666", "#888888", "#a3a3a3", "#bdbdbd", "#d4d4d4"]
        for i, (sym, value) in enumerate(rows):
            share = value / total
            line = tk.Frame(body, bg=c["panel"])
            line.pack(fill="x", pady=(8, 2))
            self.label(line, sym, size=10, bold=True).pack(side="left")
            self.label(line, f"{share * 100:.1f}%", fg="muted", size=10).pack(side="right")
            bar = tk.Canvas(body, height=8, bg=c["panel2"], highlightthickness=0)
            bar.pack(fill="x")
            bar.bind("<Configure>", lambda e, b=bar, f=share, col=palette[i % len(palette)]:
                     (b.delete("all"), b.create_rectangle(0, 0, e.width * f, 8, fill=col, outline="")))

    def page_orders(self, page):
        for col in range(4):
            page.columnconfigure(col, weight=1, uniform="o")
        page.rowconfigure(1, weight=1)
        orders = self.data.orders
        count = lambda status: len(list(filter(lambda o: o["status"] == status, orders)))
        buy_value = sum(map(lambda o: o["qty"] * o["price"],
                            filter(lambda o: o["side"] == "BUY" and o["status"] == "Executed", orders)))
        self.stat_tile(page, 0, 0, "Total orders", str(len(orders)), "this session")
        self.stat_tile(page, 0, 1, "Executed", str(count("Executed")), "filled", "up")
        self.stat_tile(page, 0, 2, "Open", str(count("Open")), "pending limit orders", "accent")
        self.stat_tile(page, 0, 3, "Bought today", inr(buy_value), "executed buy value")

        head, body = self.tile(page, "Order book", 1, 0, colspan=4)
        cols = [("time", "Time", 100, "w"), ("sym", "Symbol", 120, "w"), ("side", "Side", 80, "w"),
                ("qty", "Qty", 80, "e"), ("kind", "Type", 90, "w"), ("price", "Price", 110, "e"),
                ("value", "Value", 130, "e"), ("status", "Status", 110, "w")]
        frame, tree = self.table(body, cols)
        frame.pack(fill="both", expand=True)
        for i, o in enumerate(orders):
            tag = "muted" if o["status"] in ("Cancelled", "Rejected") else ("up" if o["side"] == "BUY" else "down")
            tree.insert("", "end", iid=str(i), tags=(tag,), values=(
                o["time"], o["sym"], o["side"], o["qty"], o["kind"], f"{o['price']:,.2f}",
                f"{o['qty'] * o['price']:,.2f}", o["status"]))

        def cancel():
            sel = tree.selection()
            if not sel or orders[int(sel[0])]["status"] != "Open":
                messagebox.showinfo("Cancel order", "Select an open order to cancel.")
                return
            if messagebox.askyesno("Cancel order", "Cancel the selected open order?"):
                orders[int(sel[0])]["status"] = "Cancelled"
                self.show_tab("Orders")

        FlatButton(head, self, "Cancel selected", cancel, size=9, padx=8, pady=2).pack(side="right")

    def page_news(self, page):
        c = self.c
        for col in range(3):
            page.columnconfigure(col, weight=1, uniform="n")
        for row in range(3):
            page.rowconfigure(row, weight=1, uniform="nr")
        now = datetime.now()
        for i, (cat, title, summary) in enumerate(NEWS):
            _, body = self.tile(page, cat, i // 3, i % 3)
            self.label(body, title, size=15, bold=True, justify="left", anchor="w",
                       wraplength=380).pack(anchor="w", fill="x")
            self.label(body, summary, fg="muted", size=11, justify="left", anchor="w",
                       wraplength=380).pack(anchor="w", fill="x", pady=(6, 0))
            when = (now - timedelta(minutes=12 * i + 5)).strftime("%H:%M")
            self.label(body, f"{when} IST", fg="muted", size=9).pack(side="bottom", anchor="w")


if __name__ == "__main__":
    root = tk.Tk()
    TradeDesk(root)
    root.mainloop()
