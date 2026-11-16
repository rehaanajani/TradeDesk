import random
import sys
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

FONT = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"

COLORS = dict(bg="#e9e9e9", panel="#ffffff", panel2="#f6f6f6", border="#e9e9e9",
              text="#111111", muted="#777777", accent="#111111", up="#15803d",
              down="#b91c1c", hover="#f4f4f4", select="#ececec")

TABS = ["Markets", "Watchlist", "Portfolio", "Orders", "News"]

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
            tree.colu
