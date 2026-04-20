import logging, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
REGIME_LABELS = {0:"Trending Bull",1:"Trending Bear",2:"Ranging",3:"High Volatility",4:"Crisis"}


class Backtester:
    def __init__(self, account_size=10000, risk_pct=1.0, min_rr=2.0,
                 min_confluence=4, min_confidence=70.0,
                 max_trades_per_day=3, stop_after_losses=2):
        self.account_size=account_size; self.risk_pct=risk_pct/100
        self.min_rr=min_rr; self.min_confluence=min_confluence
        self.min_confidence=min_confidence
        self.max_trades_per_day=max_trades_per_day; self.stop_after_losses=stop_after_losses

    def run(self, df):
        logger.info(f"Backtesting {len(df)} bars...")
        trades=[]; equity=self.account_size; eq=[equity]
        consec_loss=0; trades_today=0; last_date=None; in_trade=False

        for i in range(len(df)-1):
            row=df.iloc[i]
            today=pd.Timestamp(row.name).date()
            if today!=last_date: trades_today=0; last_date=today
            eq.append(equity)
            if in_trade or row["signal"]=="NO_TRADE": continue
            if row["confidence"]<self.min_confidence: continue
            if row["confluence"]<self.min_confluence: continue
            if not row.get("in_kz",0): continue
            if trades_today>=self.max_trades_per_day: continue
            if consec_loss>=self.stop_after_losses:
                if trades_today==0: consec_loss=0
                else: continue
            atr_r=float(row.get("atr_ratio",1.0))
            if np.isnan(atr_r): atr_r=1.0
            if atr_r<0.5 or atr_r>3.0: continue
            if int(row.get("regime",0))==4: continue

            entry=float(row["close"]); atr=float(row.get("atr",1.0)); sl_d=atr*1.5; tp_d=sl_d*self.min_rr
            direction=row["signal"]
            sl=entry-sl_d if direction=="BUY" else entry+sl_d
            tp=entry+tp_d if direction=="BUY" else entry-tp_d
            risk_usd=equity*self.risk_pct; reward_usd=risk_usd*self.min_rr
            session="London" if row.get("london_kz",0) else "New York" if row.get("ny_kz",0) else "Other"
            regime=int(row.get("regime",0))

            outcome="OPEN"; exit_price=None; pnl=0.0
            for j in range(i+1,min(i+49,len(df))):
                fut=df.iloc[j]
                if direction=="BUY":
                    if fut["low"]<=sl:  outcome="LOSS"; exit_price=sl;  pnl=-risk_usd;  break
                    if fut["high"]>=tp: outcome="WIN";  exit_price=tp;  pnl=reward_usd; break
                else:
                    if fut["high"]>=sl: outcome="LOSS"; exit_price=sl;  pnl=-risk_usd;  break
                    if fut["low"]<=tp:  outcome="WIN";  exit_price=tp;  pnl=reward_usd; break
            if outcome=="OPEN": continue

            equity+=pnl
            if outcome=="WIN": consec_loss=0
            else: consec_loss+=1
            trades_today+=1

            trades.append({"entry_time":str(row.name)[:16],"direction":direction,
                "entry_price":round(entry,2),"sl":round(sl,2),"tp":round(tp,2),
                "exit_price":round(exit_price,2),"outcome":outcome,
                "pnl_usd":round(pnl,2),"risk_usd":round(risk_usd,2),
                "rr_actual":round(abs(exit_price-entry)/sl_d,2),
                "confidence":row["confidence"],"confluence":row["confluence"],
                "regime":regime,"session":session,"equity":round(equity,2)})

        while len(eq)<len(df): eq.append(equity)
        df["equity_curve"]=eq[:len(df)]
        trades_df=pd.DataFrame(trades)
        summary=self._summary(trades_df, eq)
        self._save(trades_df, summary)
        logger.info(f"Backtest: {summary.get('total_trades',0)} trades | WR:{summary.get('win_rate_pct',0)}%")
        return {"trades":trades_df,"summary":summary,"equity_curve":eq}

    def _summary(self, t, eq):
        if t.empty: return {"total_trades":0,"error":"No trades passed filters"}
        wins=t[t["outcome"]=="WIN"]; losses=t[t["outcome"]=="LOSS"]; total=len(t)
        gp=float(wins["pnl_usd"].sum()); gl=abs(float(losses["pnl_usd"].sum()))
        pf=round(gp/gl,2) if gl>0 else float("inf")
        ea=np.array(eq); peak=np.maximum.accumulate(ea); dd=(ea-peak)/peak*100
        wr=len(wins)/total; avg_rr=float(t["rr_actual"].mean()); ev=round(wr*avg_rr-(1-wr)*1,3)
        regime_stats={}
        for r in t["regime"].unique():
            sub=t[t["regime"]==r]; sw=sub[sub["outcome"]=="WIN"]
            lbl=REGIME_LABELS.get(int(r),str(r))
            regime_stats[lbl]={"trades":len(sub),"win_rate":round(len(sw)/len(sub)*100,1),"net_pnl":round(float(sub["pnl_usd"].sum()),2)}
        sess_stats={}
        for s in ["London","New York"]:
            sub=t[t["session"]==s]
            if not sub.empty:
                sw=sub[sub["outcome"]=="WIN"]
                sess_stats[s]={"trades":len(sub),"win_rate":round(len(sw)/len(sub)*100,1),"net_pnl":round(float(sub["pnl_usd"].sum()),2)}
        return {"total_trades":total,"wins":len(wins),"losses":len(losses),
                "win_rate_pct":round(wr*100,1),"avg_rr":round(avg_rr,2),"profit_factor":pf,
                "net_profit":round(gp-gl,2),"return_pct":round((eq[-1]-self.account_size)/self.account_size*100,2),
                "max_drawdown_pct":round(float(dd.min()),2),"start_equity":self.account_size,
                "end_equity":round(eq[-1],2),"expected_value":ev,
                "regime_stats":regime_stats,"session_stats":sess_stats}

    def _save(self, t, s):
        ts=datetime.now().strftime("%Y%m%d_%H%M%S")
        t.to_csv(REPORTS_DIR/f"trades_{ts}.csv",index=False)
        with open(REPORTS_DIR/f"summary_{ts}.txt","w") as f:
            f.write("GOLD SNIPER BACKTEST\n"+"="*40+"\n")
            for k,v in s.items():
                if k not in ("regime_stats","session_stats"): f.write(f"  {k}: {v}\n")
