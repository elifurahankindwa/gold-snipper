"""
feature_engine.py — builds exactly the 45 features the trained model expects,
plus extra cols used for chart rendering (ema_20/50/200, macd, bb, atr, pdh/pdl etc.)
"""
import numpy as np, pandas as pd, logging
logger = logging.getLogger(__name__)

# These MUST match model/features.joblib exactly
MODEL_FEATURES = [
    'equal_highs','equal_lows','sweep_pdh','sweep_pdl','sweep_wkh','sweep_wkl',
    'dist_pdh_atr','dist_pdl_atr','swing_high','swing_low','bos','choch',
    'bull_ob','bear_ob','in_bull_ob','in_bear_ob','bull_fvg','bear_fvg',
    'in_bull_fvg','in_bear_fvg','at_fib_618','at_fib_786',
    'ema_trend','atr_pct','atr_ratio','adx','close_vs_ema200',
    'rsi','rsi_ob','rsi_os','macd_hist','macd_cross',
    'stoch_k','stoch_d','bb_pct','bb_width','bb_squeeze',
    'body_ratio','vol_ratio','london_kz','ny_kz','in_kz','dow','is_friday','regime',
]

def _ema(s,n): return s.ewm(span=n,adjust=False).mean()

def _atr(df,n=14):
    h,l,c=df['high'],df['low'],df['close']
    tr=pd.concat([h-l,(h-c.shift(1)).abs(),(l-c.shift(1)).abs()],axis=1).max(axis=1)
    return tr.ewm(span=n,adjust=False).mean()

def _rsi(s,n=14):
    d=s.diff(); g=d.clip(lower=0).ewm(span=n,adjust=False).mean()
    l=(-d.clip(upper=0)).ewm(span=n,adjust=False).mean()
    return 100-100/(1+g/l.replace(0,np.nan))

def _adx(df,n=14):
    h,l,c=df['high'],df['low'],df['close']
    pdm=h.diff().clip(lower=0); mdm=(-l.diff()).clip(lower=0)
    atr=_atr(df,n)
    pdi=100*pdm.ewm(span=n,adjust=False).mean()/atr.replace(0,np.nan)
    mdi=100*mdm.ewm(span=n,adjust=False).mean()/atr.replace(0,np.nan)
    dx=100*(pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan)
    return dx.ewm(span=n,adjust=False).mean()

def build_features(df, forward_bars=24, min_rr=2.0, label=True):
    logger.info("Building features...")
    df=df.copy(); n=len(df)
    c,h,l,o=df['close'],df['high'],df['low'],df['open']

    # ── ATR (needed for many calculations) ─────────────────────────────
    atr=_atr(df); df['atr']=atr

    # ── Daily high/low (PDH/PDL) ────────────────────────────────────────
    try:
        pdh=h.resample('D').max().shift(1).reindex(df.index,method='ffill')
        pdl=l.resample('D').min().shift(1).reindex(df.index,method='ffill')
    except Exception:
        pdh=pd.Series(h.rolling(24).max().shift(1).values, index=df.index)
        pdl=pd.Series(l.rolling(24).min().shift(1).values, index=df.index)
    df['pdh']=pdh; df['pdl']=pdl

    # ── Weekly high/low ────────────────────────────────────────────────
    try:
        wkh=h.resample('W').max().shift(1).reindex(df.index,method='ffill')
        wkl=l.resample('W').min().shift(1).reindex(df.index,method='ffill')
    except Exception:
        wkh=pd.Series(h.rolling(120).max().shift(1).values,index=df.index)
        wkl=pd.Series(l.rolling(120).min().shift(1).values,index=df.index)

    # ── Liquidity ───────────────────────────────────────────────────────
    def _eq(s,w=8,tol=0.0015):
        out=np.zeros(n); arr=s.values
        for i in range(w,n):
            ch=arr[i-w:i]; mid=ch.mean()
            if mid>0 and (ch.max()-ch.min())/mid<tol: out[i]=1
        return out
    df['equal_highs']=_eq(h); df['equal_lows']=_eq(l)
    df['sweep_pdh']=((h>pdh)&(c<pdh)).astype(int)
    df['sweep_pdl']=((l<pdl)&(c>pdl)).astype(int)
    df['sweep_wkh']=((h>wkh)&(c<wkh)).astype(int)
    df['sweep_wkl']=((l<wkl)&(c>wkl)).astype(int)
    df['dist_pdh_atr']=(c-pdh)/atr.replace(0,np.nan)
    df['dist_pdl_atr']=(c-pdl)/atr.replace(0,np.nan)

    # ── Structure ───────────────────────────────────────────────────────
    sw=8; sh=np.zeros(n); sl=np.zeros(n)
    hv=h.values; lv=l.values
    for i in range(sw,n-sw):
        if hv[i]==max(hv[i-sw:i+sw+1]): sh[i]=1
        if lv[i]==min(lv[i-sw:i+sw+1]): sl[i]=1
    df['swing_high']=sh; df['swing_low']=sl

    cv=c.values; bos=np.zeros(n,dtype=int)
    last_sh=last_sl=np.nan
    for i in range(n):
        if sh[i]: last_sh=hv[i]
        if sl[i]: last_sl=lv[i]
        if not np.isnan(last_sh) and cv[i]>last_sh and (i>0 and cv[i-1]<=last_sh): bos[i]=1
        if not np.isnan(last_sl) and cv[i]<last_sl and (i>0 and cv[i-1]>=last_sl): bos[i]=-1
    df['bos']=bos; df['choch']=(bos!=0).astype(int)

    # ── Order Blocks ────────────────────────────────────────────────────
    ov=o.values; bull_ob=np.zeros(n); bear_ob=np.zeros(n)
    for i in range(5,n):
        fut=min(i+5,n-1)
        if cv[fut]>hv[i]*1.002:
            for j in range(i,max(i-5,0),-1):
                if cv[j]<ov[j]: bull_ob[j]=1; break
        if cv[fut]<lv[i]*0.998:
            for j in range(i,max(i-5,0),-1):
                if cv[j]>ov[j]: bear_ob[j]=1; break
    df['bull_ob']=bull_ob; df['bear_ob']=bear_ob
    in_bull=np.zeros(n,dtype=int); in_bear=np.zeros(n,dtype=int)
    for i in range(10,n):
        for j in range(max(0,i-20),i):
            if bull_ob[j] and lv[j]<=cv[i]<=hv[j]: in_bull[i]=1
            if bear_ob[j] and lv[j]<=cv[i]<=hv[j]: in_bear[i]=1
    df['in_bull_ob']=in_bull; df['in_bear_ob']=in_bear

    # ── FVG ─────────────────────────────────────────────────────────────
    bfvg=np.zeros(n); befvg=np.zeros(n); ibfvg=np.zeros(n); ibefvg=np.zeros(n)
    for i in range(2,n):
        if hv[i-2]<lv[i]: bfvg[i]=1; ibfvg[i]=int(lv[i]<=cv[i]<=hv[i-2]+(lv[i]-hv[i-2]))
        if lv[i-2]>hv[i]: befvg[i]=1; ibefvg[i]=int(hv[i]<=cv[i]<=lv[i-2])
    df['bull_fvg']=bfvg; df['bear_fvg']=befvg
    df['in_bull_fvg']=ibfvg; df['in_bear_fvg']=ibefvg

    # ── Fibonacci ────────────────────────────────────────────────────────
    fib618=np.zeros(n); fib786=np.zeros(n)
    for i in range(50,n):
        w=df.iloc[i-50:i]; rng=w['high'].max()-w['low'].min()
        if rng<0.5: continue
        lo=w['low'].min(); r618=lo+0.618*rng; r786=lo+0.786*rng; tol=atr.iloc[i]*0.4
        fib618[i]=int(abs(cv[i]-r618)<tol); fib786[i]=int(abs(cv[i]-r786)<tol)
    df['at_fib_618']=fib618; df['at_fib_786']=fib786

    # ── Technical ────────────────────────────────────────────────────────
    df['ema_20']=_ema(c,20); df['ema_50']=_ema(c,50); df['ema_200']=_ema(c,200)
    df['ema_trend']=np.where((df['ema_20']>df['ema_50'])&(df['ema_50']>df['ema_200']),1,
                    np.where((df['ema_20']<df['ema_50'])&(df['ema_50']<df['ema_200']),-1,0))
    df['atr_pct']=atr/c*100
    atr_ma=df['atr_pct'].rolling(50).mean()
    df['atr_ratio']=df['atr_pct']/atr_ma.replace(0,np.nan)
    df['adx']=_adx(df)
    df['close_vs_ema200']=(c-df['ema_200'])/df['ema_200']*100
    df['rsi']=_rsi(c); df['rsi_ob']=(df['rsi']>70).astype(int); df['rsi_os']=(df['rsi']<30).astype(int)
    ema12=_ema(c,12); ema26=_ema(c,26); df['macd']=ema12-ema26
    df['macd_signal']=_ema(df['macd'],9); df['macd_hist']=df['macd']-df['macd_signal']
    df['macd_cross']=((df['macd']>df['macd_signal'])&(df['macd'].shift(1)<=df['macd_signal'].shift(1))).astype(int)
    lo14=l.rolling(14).min(); hi14=h.rolling(14).max()
    df['stoch_k']=100*(c-lo14)/(hi14-lo14).replace(0,np.nan)
    df['stoch_d']=df['stoch_k'].rolling(3).mean()
    bb_mid=c.rolling(20).mean(); bb_std=c.rolling(20).std()
    df['bb_upper']=bb_mid+2*bb_std; df['bb_lower']=bb_mid-2*bb_std
    df['bb_pct']=(c-df['bb_lower'])/(df['bb_upper']-df['bb_lower']).replace(0,np.nan)
    df['bb_width']=(df['bb_upper']-df['bb_lower'])/bb_mid
    df['bb_squeeze']=(df['bb_width']<df['bb_width'].rolling(50).mean()*.8).astype(int)
    df['body_ratio']=(c-o).abs()/(h-l).replace(0,np.nan)
    df['vol_ratio']=df['volume']/df['volume'].rolling(20).mean().replace(0,np.nan)

    # ── Session / Calendar ───────────────────────────────────────────────
    hr=df.index.hour
    df['london_kz']=((hr>=7)&(hr<10)).astype(int)
    df['ny_kz']    =((hr>=12)&(hr<15)).astype(int)
    df['in_kz']    =((df['london_kz']==1)|(df['ny_kz']==1)).astype(int)
    df['dow']      =df.index.dayofweek
    df['is_friday']=(df.index.dayofweek==4).astype(int)

    # ── Labels ───────────────────────────────────────────────────────────
    if label:
        labels=np.zeros(n,dtype=int); av=atr.values
        for i in range(n-forward_bars):
            sl_d=av[i]*1.5
            if sl_d<0.5: continue
            tp_d=sl_d*min_rr
            bsl=cv[i]-sl_d; btp=cv[i]+tp_d; ssl=cv[i]+sl_d; stp=cv[i]-tp_d
            bh=sh2=False
            for j in range(i+1,min(i+forward_bars+1,n)):
                if lv[j]<=bsl: break
                if hv[j]>=btp: bh=True; break
            for j in range(i+1,min(i+forward_bars+1,n)):
                if hv[j]>=ssl: break
                if lv[j]<=stp: sh2=True; break
            if bh and not sh2: labels[i]=1
            elif sh2 and not bh: labels[i]=-1
        df['label']=labels.astype(int)

    # ── Macro passthrough ────────────────────────────────────────────────
    macro_extra=[c2 for c2 in ['dxy','oil','spx','tnx','vix','dxy_trend','rates_rising','fear_high'] if c2 in df.columns]

    # Final cleanup
    feat_cols = MODEL_FEATURES + [m for m in macro_extra if m not in MODEL_FEATURES]
    feat_cols  = [c2 for c2 in feat_cols if c2 in df.columns]
    df.replace([np.inf,-np.inf],np.nan,inplace=True)
    for col in feat_cols:
        if df[col].isna().any(): df[col]=df[col].fillna(0)
    if label and 'label' in df.columns:
        df['label']=df['label'].fillna(0).astype(int)
    df.dropna(subset=['open','high','low','close'],inplace=True)
    logger.info(f"Features: {len(df)} bars × {len(feat_cols)} cols")
    return df, feat_cols
