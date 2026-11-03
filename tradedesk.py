"""
TradeDesk - a mock NSE trading terminal (front end only).
21CSC203P Advanced Programming Practice - Tkinter GUI demo.

Only the Python standard library is used: tkinter, random, datetime, sys.
All market data is fake and generated locally. Nothing is sent anywhere.

Paradigms shown:
  * Object-oriented : Stock, MarketData, FlatButton, TradeDesk classes
  * Event-driven    : button clicks, key/trace callbacks, root.after() timers
  * Functional      : filter / sorted / lambda / map for watchlist and movers
  * Procedural      : small formatting helpers (inr, pct_text)
  * State machine   : the active tab decides which page is built
"""
import random
import sys
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

# ----------------------------------------------------------------- settings
FONT = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"

THEMES = {
    "dark": dict(bg="#0b0f14", panel="#131a22", panel2="#1a232e", border="#26313d",
                 text="#e6edf3", muted="#8b98a5", accent="#3b82f6", up="#22c55e",
                 down="#ef4444", hover="#1f2a37", select="#1e3a5f"),
    "light": dict(bg="#eef1f5", panel="#ffffff", panel2="#f3f5f8", border="#d5dbe3",
                  text="#111827", muted="#6b7280", accent="#2563eb", up="#16a34a",
                  down="#dc2626", hover="#eaf0f7", select="#dbeafe"),
}

TABS = ["Markets", "Watchlist", "Portfolio", "Orders", "News"]

# timeframe -> (number of candles, volatility per candle)
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


# ----------------------------------------------------------------- helpers
def inr(x):
    return f"₹{x:,.2f}"


def pct_text(x):
    return f"{'+' if x >= 0 else ''}{x:.2f}%"


def market_open(now):
    minutes = now.hour * 60 + now.minute
    return now.weekday() < 5 and 9 * 60 + 15 <= minutes <= 15 * 60 + 30


# ----------------------------------------------------------------- model
class Stock:
    """One instrument (a stock or an index) with fake daily numbers."""

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
    """All demo data lives here: prices, holdings, orders, chart candles."""

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
        """Random-walk candles that end exactly at today's price."""
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
        """Open limit and stop-loss orders execute once the price reaches them."""
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
        """Five simulated bid and ask levels: (bid, bid qty, ask, ask qty)."""
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
        """Move an executed order into holdings and cash."""
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


# ----------------------------------------------------------------- widgets
class FlatButton(tk.Label):
    """Label-based button. tk.Button ignores bg colours on macOS, a Label doesn't."""

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


# ----------------------------------------------------------------- app
class TradeDesk:
    def __init__(self, root):
        self.root = root
        self.data = MarketData()
        self.theme, self.tab, self.symbol = "dark", "Markets", "RELIANCE"
        self.tf, self.chart_type, self.sort_key = "1D", "Candle", "Symbol"
        self.show_gainers, self.live, self.show_ma = True, False, False
        self.order_state = dict(side="BUY", kind="Market", qty="1")
        root.title("TradeDesk")
        root.geometry("1360x860")
        root.minsize(1180, 760)
        self.build()
        self._clock()
        self._live_loop()

    # ---------- shell (top bar, ticker strip, content, status bar)
    @property
    def c(self):
        return THEMES[self.theme]

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
        tk.Label(bar, text="▣ TradeDesk", bg=c["panel"], fg=c["accent"],
                 font=(FONT, 16, "bold"), padx=18).pack(side="left")
        self.tab_btns = {}
        for name in TABS:
            b = FlatButton(bar, self, name, lambda n=name: self.show_tab(n),
                           active=(name == self.tab), size=11, padx=16, pady=14)
            b.pack(side="left", fill="y")
            self.tab_btns[name] = b
        theme_txt = "☀ Light" if self.theme == "dark" else "☾ Dark"
        FlatButton(bar, self, theme_txt, self.toggle_theme, size=10, padx=14,
                   pady=14).pack(side="right", fill="y")
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

    # ---------- timers (event-driven)
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

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.build()

    # ---------- navigation (simple state machine on self.tab)
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

    # ---------- building blocks
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
        """columns: list of (id, heading, width, anchor)."""
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
            tree.tag_configure(tag, foreground=c[tag])
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

    # =========================================================== MARKETS
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

    # ---- chart
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
            cv.create_line(*pts, fill="#f59e0b", width=2)

        last = data[-1][3]
        col = c["up"] if last >= data[0][0] else c["down"]
        cv.create_line(left, y(last), left + pw, y(last), fill=col, dash=(4, 3))
        cv.create_rectangle(left + pw + 2, y(last) - 10, w, y(last) + 10, fill=col, outline=col)
        cv.create_text(left + pw + 10, y(last), text=f"{last:,.2f}", anchor="w",
                       fill="#ffffff", font=(FONT, 9, "bold"))

    # ---- watchlist (compact)
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

    # ---- order ticket
    def order_tile(self, page, r, col):
        c, st = self.c, self.order_state
        head, body = self.tile(page, "Place order", r, col)
        sym_lbl = self.label(head, fg="accent", size=10, bold=True)
        sym_lbl.pack(side="right")
        body.columnconfigure(1, weight=1)

        qty_var = tk.StringVar(value=st["qty"])
        price_var = tk.StringVar(value=f"{self.data.stocks[self.symbol].price:.2f}")
        place_btn = FlatButton(body, self, "", None, color=c["up"], size=11, pady=8)

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
            place_btn.set_color(c["up"] if st["side"] == "BUY" else c["down"])
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
        ok = messagebox.askyesno(
            "Confirm order",
            f"{st['side']} {qty} × {s.sym}\nType: {st['kind']}\n"
            f"Price: {inr(price)}\nValue: {inr(qty * price)}\n\nPlace this demo order?")
        if not ok:
            return
        status = "Executed" if st["kind"] == "Market" else "Open"
        self.data.place(dict(time=datetime.now().strftime("%H:%M:%S"), sym=s.sym, side=st["side"],
                             qty=qty, kind=st["kind"], price=price, status=status))
        messagebox.showinfo("Order placed", f"{st['side']} {qty} {s.sym} — {status}.")
        self.refresh()

    # ---- portfolio summary
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

    # ---- gainers / losers
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

    # ---- headlines
    def news_tile(self, page, r, col):
        c = self.c
        head, body = self.tile(page, "Market news", r, col)
        FlatButton(head, self, "All ›", lambda: self.show_tab("News"), size=9,
                   padx=8, pady=2).pack(side="right")
        for cat, title, _ in NEWS[:4]:
            self.label(body, cat.upper(), fg="accent", size=8, bold=True).pack(anchor="w", pady=(4, 0))
            self.label(body, title, size=10, justify="left", anchor="w",
                       wraplength=250).pack(anchor="w", fill="x")

    # =========================================================== WATCHLIST
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
            FlatButton(btns, self, "BUY", lambda: self.trade_from_quote("BUY"), color=c["up"],
                       pady=8).grid(row=0, column=0, sticky="ew", padx=(0, 4))
            FlatButton(btns, self, "SELL", lambda: self.trade_from_quote("SELL"), color=c["down"],
                       pady=8).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        render()
        self.refreshers.append(render)
        self.sym_listeners.append(render)

    def trade_from_quote(self, side):
        self.order_state["side"] = side
        self.show_tab("Markets")

    # =========================================================== PORTFOLIO
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
        palette = [c["accent"], c["up"], "#f59e0b", "#a855f7", "#14b8a6", "#ec4899", c["muted"]]
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

    # =========================================================== ORDERS
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

    # =========================================================== NEWS
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
            self.label(body, f"{when} IST", fg="accent", size=9, bold=True).pack(side="bottom", anchor="w")


if __name__ == "__main__":
    root = tk.Tk()
    TradeDesk(root)
    root.mainloop()
