import logging, warnings, numpy as np, pandas as pd
from datetime import datetime, timezone, timedelta
import yfinance as yf

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

MACRO_TICKERS = {"dxy":"DX-Y.NYB","oil":"CL=F","spx":"^GSPC","tnx":"^TNX","vix":"^VIX"}
REGIME_LABELS = {0:"Trending Bull",1:"Trending Bear",2:"Ranging",3:"High Volatility",4:"Crisis"}


def fetch_gold(period="2y", interval="1h"):
    logger.info(f"Fetching gold data period={period} interval={interval}")
    try:
        df = yf.Ticker("GC=F").history(period=period, interval=interval, auto_adjust=True)
        if df.empty: raise ValueError("Empty")
        df.index = pd.to_datetime(df.index, utc=True)
        df.columns = [c.lower() for c in df.columns]
        df = df[["open","high","low","close","volume"]].dropna()
        logger.info(f"Gold: {len(df)} bars")
        return df
    except Exception as e:
        logger.warning(f"Gold fetch failed: {e} — using synthetic data")
        return _synthetic()


def _synthetic():
    n = 3000
    np.random.seed(42)
    end = datetime.now(timezone.utc)
    times = [end - timedelta(hours=i) for i in range(n,0,-1)]
    p = 2050.0
    rows = []
    for i,t in enumerate(times):
        p *= (1 + np.random.normal(0.00003, 0.0009))
        p = max(p, 1500)
        sp = np.random.uniform(0.5,2.5)
        rows.append({"open":round(p*(1+np.random.normal(0,0.0002)),2),
                     "high":round(p+np.random.uniform(0,sp*2),2),
                     "low": round(p-np.random.uniform(0,sp*2),2),
                     "close":round(p,2),"volume":int(np.random.uniform(800,8000))})
    return pd.DataFrame(rows, index=pd.DatetimeIndex(times, tz="UTC"))


def fetch_macro(period="2y"):
    frames = {}
    for name, ticker in MACRO_TICKERS.items():
        try:
            df = yf.Ticker(ticker).history(period=period, interval="1d", auto_adjust=True)
            if not df.empty:
                df.index = pd.to_datetime(df.index, utc=True)
                frames[name] = df["Close"].rename(name)
                logger.info(f"  {name.upper()}: {len(df)} bars")
        except Exception as e:
            logger.debug(f"  {name} failed: {e}")
    return pd.concat(frames.values(), axis=1) if frames else pd.DataFrame()


def detect_regime(df):
    c = df["close"]
    ema50  = c.ewm(span=50,  adjust=False).mean()
    ema200 = c.ewm(span=200, adjust=False).mean()
    tr = pd.concat([(df["high"]-df["low"]),
                    (df["high"]-c.shift(1)).abs(),
                    (df["low"] -c.shift(1)).abs()],axis=1).max(axis=1)
    atr    = tr.ewm(span=14,adjust=False).mean()
    atr_ma = atr.rolling(100).mean()
    vix_crisis = df["vix"]>35 if "vix" in df.columns else pd.Series(False,index=df.index)
    high_vol = (atr > atr_ma*2.5) | vix_crisis
    regime = pd.Series(2, index=df.index)
    regime[(ema50>ema200) & ~high_vol] = 0
    regime[(ema50<ema200) & ~high_vol] = 1
    regime[high_vol & ~vix_crisis]     = 3
    regime[vix_crisis]                 = 4
    return regime


def build_dataset(period="2y", interval="1h"):
    gold  = fetch_gold(period=period, interval=interval)
    macro = fetch_macro(period=period)
    if not macro.empty:
        macro_r = macro.reindex(gold.index, method="ffill")
        df = pd.concat([gold, macro_r], axis=1)
        if "dxy" in df.columns:
            df["dxy_trend"] = np.where(df["dxy"] > df["dxy"].ewm(span=20,adjust=False).mean(),1,-1)
        if "tnx" in df.columns:
            df["rates_rising"] = (df["tnx"].diff(5)>0).astype(int)
        if "vix" in df.columns:
            df["fear_high"] = (df["vix"]>25).astype(int)
    else:
        df = gold.copy()
    df["regime"]       = detect_regime(df)
    df["regime_label"] = df["regime"].map(REGIME_LABELS)
    df.dropna(subset=["close"], inplace=True)
    logger.info(f"Dataset: {len(df)} bars | Regimes: {df['regime'].value_counts().to_dict()}")
    return df


def get_live_price():
    try:
        info = yf.Ticker("GC=F").fast_info
        price = float(info.last_price or 0)
        if price < 100: raise ValueError("bad price")
        prev  = float(info.previous_close or price)
        chg   = price - prev
        return {"price":round(price,2),"change":round(chg,2),
                "change_pct":round(chg/prev*100 if prev else 0,3),
                "high":round(float(info.day_high or price),2),
                "low": round(float(info.day_low  or price),2),
                "timestamp":datetime.now(timezone.utc).isoformat(),"fresh":True}
    except Exception as e:
        logger.debug(f"Live price failed: {e}")
        return {"price":0,"change":0,"change_pct":0,"high":0,"low":0,
                "timestamp":datetime.now(timezone.utc).isoformat(),"fresh":False}
