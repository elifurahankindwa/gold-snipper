import logging, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Always save charts relative to THIS file's location (the project root)
ROOT       = Path(__file__).parent
CHARTS_DIR = ROOT / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

BG="#f9fafb"; PANEL="#ffffff"; GRID="#e5e7eb"
GOLD="#B45309"; GREEN="#16A34A"; RED="#DC2626"; BLUE="#2563EB"
TEXT="#374151"; TEXT2="#9CA3AF"; PURPLE="#7C3AED"; AMBER="#D97706"

plt.rcParams.update({
    "figure.facecolor":BG,"axes.facecolor":PANEL,"axes.edgecolor":GRID,
    "axes.labelcolor":TEXT,"text.color":TEXT,"xtick.color":TEXT2,"ytick.color":TEXT2,
    "grid.color":GRID,"grid.linestyle":"--","grid.linewidth":0.4,
    "font.family":"monospace","legend.facecolor":PANEL,
    "legend.edgecolor":GRID,"legend.fontsize":8
})

def _ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _save(fig, name):
    path = CHARTS_DIR / f"{name}_{_ts()}.png"
    fig.savefig(path, dpi=140, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    logger.info(f"Chart saved: {path}")
    return str(path)

def plot_equity_curve(eq, trades, summary):
    eq   = np.array(eq)
    peak = np.maximum.accumulate(eq)
    dd   = (eq - peak) / peak * 100
    idx  = np.arange(len(eq))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 7),
        gridspec_kw={"height_ratios":[3,1]}, sharex=True)
    fig.suptitle("Gold Sniper — Equity Curve", color=GOLD, fontsize=13, fontweight="bold")
    ax1.plot(idx, eq, color=GOLD, lw=1.5)
    ax1.fill_between(idx, summary["start_equity"], eq,
        where=(eq >= summary["start_equity"]), alpha=.1, color=GREEN)
    ax1.fill_between(idx, summary["start_equity"], eq,
        where=(eq < summary["start_equity"]),  alpha=.1, color=RED)
    ax1.axhline(summary["start_equity"], color=TEXT2, lw=.6, ls=":")
    ax1.set_ylabel("Equity ($)", color=TEXT)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_:f"${x:,.0f}"))
    ax1.grid(True, alpha=.3)
    stats = (f"Trades:{summary['total_trades']}  WR:{summary['win_rate_pct']}%  "
             f"PF:{summary['profit_factor']}  Net:${summary['net_profit']:,.0f}  "
             f"Return:{summary['return_pct']}%  MaxDD:{summary['max_drawdown_pct']}%")
    ax1.set_title(stats, color=TEXT2, fontsize=8)
    ax2.fill_between(idx, 0, dd, color=RED, alpha=.5)
    ax2.axhline(summary["max_drawdown_pct"], color=RED, lw=.7, ls="--",
                label=f"Max DD: {summary['max_drawdown_pct']:.1f}%")
    ax2.set_ylabel("Drawdown %", color=TEXT)
    ax2.legend(); ax2.grid(True, alpha=.3)
    fig.tight_layout()
    return _save(fig, "equity_curve")

def plot_signals(df, last_n=200):
    df  = df.tail(last_n).copy()
    n   = len(df); x = np.arange(n)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 9),
        gridspec_kw={"height_ratios":[3,1]}, sharex=True)
    fig.suptitle(f"Signal Map — Last {n} Bars", color=GOLD, fontsize=13, fontweight="bold")
    bw = max(1.5, 120/n)
    for i, (_, r) in enumerate(df.iterrows()):
        col = GREEN if r["close"] >= r["open"] else RED
        ax1.plot([i,i],[r["low"],r["high"]], color=col, lw=.8, alpha=.7)
        ax1.add_patch(plt.Rectangle((i-bw/2, min(r["open"],r["close"])),
            bw, abs(r["close"]-r["open"])+.01, facecolor=col, linewidth=0, alpha=.85))
    ax1.plot(x, df["ema_20"],  color=BLUE, lw=1,   label="EMA20",  alpha=.8)
    ax1.plot(x, df["ema_50"],  color=GOLD, lw=1,   label="EMA50",  alpha=.8)
    ax1.plot(x, df["ema_200"], color=RED,  lw=1.2, label="EMA200", alpha=.8)
    il = list(df.index)
    buys  = df[df["signal"]=="BUY"]; sells = df[df["signal"]=="SELL"]
    bxi = [il.index(i) for i in buys.index  if i in il]
    sxi = [il.index(i) for i in sells.index if i in il]
    if bxi: ax1.scatter(bxi, buys["low"].values  - buys["atr"].values*.5,  marker="^", color=GREEN, s=60, zorder=5, label="BUY")
    if sxi: ax1.scatter(sxi, sells["high"].values + sells["atr"].values*.5, marker="v", color=RED,   s=60, zorder=5, label="SELL")
    for i in range(n):
        if df.iloc[i].get("in_kz",0): ax1.axvspan(i-.5, i+.5, alpha=.05, color=AMBER)
    ax1.set_ylabel("Price USD", color=TEXT)
    ax1.legend(loc="upper left", ncol=5, fontsize=7)
    ax1.grid(True, alpha=.25)
    ax2.plot(x, df["rsi"], color=BLUE, lw=1)
    ax2.axhline(70, color=RED,   lw=.7, ls="--", alpha=.7)
    ax2.axhline(30, color=GREEN, lw=.7, ls="--", alpha=.7)
    ax2.fill_between(x, 70, df["rsi"], where=(df["rsi"]>70), alpha=.15, color=RED)
    ax2.fill_between(x, 30, df["rsi"], where=(df["rsi"]<30), alpha=.15, color=GREEN)
    ax2.set_ylabel("RSI", color=TEXT); ax2.set_ylim(0,100); ax2.grid(True, alpha=.25)
    step = max(1, n//10)
    ax2.set_xticks(x[::step])
    ax2.set_xticklabels([str(df.index[i])[:13] for i in range(0,n,step)], rotation=30, fontsize=7)
    fig.tight_layout()
    return _save(fig, "signals")

def plot_feature_importance(imp_df):
    top = imp_df.head(20)
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.suptitle("Feature Importance", color=GOLD, fontsize=13, fontweight="bold")
    cols = [GOLD if i<5 else BLUE if i<12 else TEXT2 for i in range(len(top))]
    bars = ax.barh(top["feature"][::-1], top["importance"][::-1],
                   color=cols[::-1], edgecolor=GRID, linewidth=.3)
    for bar, val in zip(bars, top["importance"][::-1]):
        ax.text(val+.001, bar.get_y()+bar.get_height()/2,
                f"{val:.3f}", va="center", ha="left", fontsize=8, color=TEXT)
    ax.set_xlabel("Importance", color=TEXT); ax.grid(True, axis="x", alpha=.3)
    fig.tight_layout()
    return _save(fig, "feature_importance")

def plot_monthly_heatmap(trades):
    if trades.empty: return ""
    t = trades.copy()
    t["entry_time"] = pd.to_datetime(t["entry_time"])
    t["year"]  = t["entry_time"].dt.year
    t["month"] = t["entry_time"].dt.month
    monthly = t.groupby(["year","month"])["pnl_usd"].sum().unstack(fill_value=0)
    data = monthly.reindex(columns=range(1,13), fill_value=0).values
    vmax = max(abs(data.max()), abs(data.min()), 1)
    fig, ax = plt.subplots(figsize=(12, max(3, len(monthly))))
    fig.suptitle("Monthly P&L Heatmap (USD)", color=GOLD, fontsize=13, fontweight="bold")
    im = ax.imshow(data, cmap="RdYlGn", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(12))
    ax.set_xticklabels(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], fontsize=9)
    ax.set_yticks(range(len(monthly))); ax.set_yticklabels(monthly.index, fontsize=9)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i,j]
            ax.text(j, i, f"${v:,.0f}", ha="center", va="center",
                    fontsize=8, color="white" if abs(v)>vmax*.5 else TEXT)
    plt.colorbar(im, ax=ax, label="P&L USD"); fig.tight_layout()
    return _save(fig, "monthly_heatmap")

def plot_regime_breakdown(summary):
    rs = summary.get("regime_stats", {})
    if not rs: return ""
    names = list(rs.keys())
    wrs   = [rs[n]["win_rate"] for n in names]
    pnls  = [rs[n]["net_pnl"]  for n in names]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Performance by Regime", color=GOLD, fontsize=13, fontweight="bold")
    ax1.barh(names, wrs, color=[GREEN if w>=50 else RED for w in wrs], edgecolor=GRID, linewidth=.3)
    ax1.axvline(50, color=TEXT2, lw=.8, ls="--")
    ax1.set_xlabel("Win Rate %", color=TEXT); ax1.grid(True, axis="x", alpha=.3)
    ax2.barh(names, pnls, color=[GREEN if p>=0 else RED for p in pnls], edgecolor=GRID, linewidth=.3)
    ax2.axvline(0, color=TEXT2, lw=.8, ls="--")
    ax2.set_xlabel("Net P&L (USD)", color=TEXT); ax2.grid(True, axis="x", alpha=.3)
    fig.tight_layout()
    return _save(fig, "regime_breakdown")
