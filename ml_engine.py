import logging, numpy as np, pandas as pd, joblib
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.utils.class_weight import compute_class_weight
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)
MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

REGIME_LABELS = {0:"Trending Bull",1:"Trending Bear",2:"Ranging",3:"High Volatility",4:"Crisis"}


class GoldSniperModel:
    def __init__(self):
        self.model = None; self.encoder = LabelEncoder()
        self.feature_cols = []; self.is_trained = False; self.train_meta = {}

    def train(self, df, feature_cols, n_splits=5, oos_pct=0.2):
        logger.info(f"Training: {len(df)} bars, {len(feature_cols)} features")
        self.feature_cols = feature_cols
        df = df.copy()
        df["label"] = df["label"].fillna(0).astype(int)
        fc = [c for c in feature_cols if c in df.columns]
        split = int(len(df)*(1-oos_pct))
        dtr, doos = df.iloc[:split], df.iloc[split:]
        X = dtr[fc].values.astype(np.float32)
        y_raw = dtr["label"].values.astype(int)
        self.encoder.fit(y_raw)
        y = self.encoder.transform(y_raw).astype(int)
        classes = np.unique(y)
        sw = np.array([dict(zip(classes, compute_class_weight("balanced",classes=classes,y=y)))[c] for c in y], dtype=np.float32)
        tscv = TimeSeriesSplit(n_splits=n_splits); folds=[]
        for fold,(tri,vali) in enumerate(tscv.split(X)):
            Xtr,Xv,ytr,yv=X[tri],X[vali],y[tri].astype(int),y[vali].astype(int)
            m = self._cv_model(len(classes))
            m.fit(Xtr,ytr,sample_weight=sw[tri],eval_set=[(Xv,yv)],verbose=False)
            p = m.predict(Xv)
            folds.append({"fold":fold+1,"f1":round(f1_score(yv,p,average="macro",zero_division=0),3),
                          "prec":round(precision_score(yv,p,average="macro",zero_division=0),3)})
            logger.info(f"  Fold {fold+1}: F1={folds[-1]['f1']}")
        logger.info("Training final model...")
        self.model = self._final_model(len(classes))
        self.model.fit(X, y, sample_weight=sw, verbose=False)
        self.is_trained = True
        oos={}
        if len(doos)>20:
            Xo=doos[fc].fillna(0).values.astype(np.float32)
            yo=self.encoder.transform(doos["label"].fillna(0).astype(int).values).astype(int)
            po=self.model.predict(Xo)
            oos={"oos_f1":round(f1_score(yo,po,average="macro",zero_division=0),3),"oos_bars":len(doos)}
            logger.info(f"OOS: {oos}")
        self.train_meta = {"folds":folds,"avg_f1":round(np.mean([f["f1"] for f in folds]),3),
                           "avg_prec":round(np.mean([f["prec"] for f in folds]),3),
                           "oos":oos,"train_bars":len(dtr),"feature_count":len(fc),
                           "trained_at":datetime.utcnow().isoformat()}
        self.save()
        return self.train_meta

    def _cv_model(self, nc):
        return XGBClassifier(n_estimators=300,max_depth=4,learning_rate=0.05,
            subsample=0.8,colsample_bytree=0.8,min_child_weight=5,gamma=0.2,
            reg_alpha=0.1,reg_lambda=1.0,objective="multi:softprob",num_class=nc,
            eval_metric="mlogloss",early_stopping_rounds=20,random_state=42,n_jobs=-1)

    def _final_model(self, nc):
        return XGBClassifier(n_estimators=400,max_depth=4,learning_rate=0.05,
            subsample=0.8,colsample_bytree=0.8,min_child_weight=5,gamma=0.2,
            reg_alpha=0.1,reg_lambda=1.0,objective="multi:softprob",num_class=nc,
            eval_metric="mlogloss",random_state=42,n_jobs=-1)

    def predict(self, df):
        if not self.is_trained: raise RuntimeError("Model not trained")
        fc = [c for c in self.feature_cols if c in df.columns]
        X  = df[fc].fillna(0).values.astype(np.float32)
        prob = self.model.predict_proba(X)
        pred = self.encoder.inverse_transform(np.argmax(prob,axis=1))
        df = df.copy()
        df["signal"]     = pd.array(pred).map(lambda x: {1:"BUY",-1:"SELL",0:"NO_TRADE"}.get(x,"NO_TRADE"))
        df["confidence"] = (prob.max(axis=1)*100).round(1)
        df["confluence"] = self._confluence(df)
        return df

    def _confluence(self, df):
        s = pd.Series(0, index=df.index, dtype=int)
        buy=(df["signal"]=="BUY"); sell=(df["signal"]=="SELL")
        s+=np.where(buy &(df.get("ema_trend",0)==1),1,0)
        s+=np.where(sell&(df.get("ema_trend",0)==-1),1,0)
        s+=np.where(buy &(df.get("sweep_pdl",0)==1),1,0)
        s+=np.where(sell&(df.get("sweep_pdh",0)==1),1,0)
        s+=df.get("in_kz",pd.Series(0,index=df.index)).values
        s+=np.where(buy &(df.get("bos",0)==1),1,0)
        s+=np.where(sell&(df.get("bos",0)==-1),1,0)
        s+=np.where(buy &(df.get("in_bull_ob",0)==1),1,0)
        s+=np.where(sell&(df.get("in_bear_ob",0)==1),1,0)
        s+=np.where(buy &(df.get("in_bull_fvg",0)==1),1,0)
        s+=np.where(sell&(df.get("in_bear_fvg",0)==1),1,0)
        s+=df.get("at_fib618",pd.Series(0,index=df.index)).values
        s+=np.where(buy &(df.get("rsi",50)<40),1,0)
        s+=np.where(sell&(df.get("rsi",50)>60),1,0)
        return s.clip(upper=8)

    def latest_signal(self, df):
        row = df.iloc[-1]
        atr = float(row.get("atr",0)); price = float(row["close"])
        sl_d = atr*1.5; tp_d = sl_d*2.0; direction = row["signal"]
        h = pd.Timestamp(row.name).hour
        session = "London" if 7<=h<10 else "New York" if 12<=h<15 else "Asian" if h<6 else "Off-session"
        return {"datetime":str(row.name),"close":round(price,2),"signal":direction,
                "confidence":round(float(row["confidence"]),1),"confluence":int(row["confluence"]),
                "atr":round(atr,2),"rsi":round(float(row.get("rsi",0)),1),
                "in_kz":bool(row.get("in_kz",0)),"bos":int(row.get("bos",0)),
                "ema_trend":int(row.get("ema_trend",0)),"regime":int(row.get("regime",0)),
                "regime_label":REGIME_LABELS.get(int(row.get("regime",0)),"Unknown"),
                "atr_ratio":round(float(row.get("atr_ratio",1.0)),2),
                "sl":round(price-sl_d if direction=="BUY" else price+sl_d,2),
                "tp":round(price+tp_d if direction=="BUY" else price-tp_d,2),
                "session":session,"timestamp":datetime.utcnow().isoformat()}

    def feature_importances(self):
        if not self.is_trained: return pd.DataFrame()
        return pd.DataFrame({"feature":self.feature_cols,"importance":self.model.feature_importances_})\
               .sort_values("importance",ascending=False).reset_index(drop=True)

    def explain_row(self, df):
        try:
            import shap
            fc=[c for c in self.feature_cols if c in df.columns]
            X=df.iloc[[-1]][fc].fillna(0).values.astype(np.float32)
            expl=shap.TreeExplainer(self.model); sv=expl.shap_values(X)
            if isinstance(sv,list): pc=int(np.argmax(self.model.predict_proba(X))); shap_vals=sv[pc][0]
            else: shap_vals=sv[0]
            items=sorted(zip(fc,shap_vals),key=lambda x:abs(x[1]),reverse=True)[:5]
            return {k:round(float(v),4) for k,v in items}
        except: pass
        imp=self.feature_importances()
        if imp.empty: return {}
        return {r["feature"]:round(r["importance"],4) for _,r in imp.head(5).iterrows()}

    def risk_check(self, row, signal, confidence, confluence):
        reasons=[]
        if signal=="NO_TRADE": return False,["No trade signal"]
        if confidence<70: reasons.append(f"Confidence {confidence:.1f}% < 70%")
        if confluence<4:  reasons.append(f"Confluence {confluence}/8 < 4")
        if not row.get("in_kz",0): reasons.append("Outside kill zone")
        atr_r=float(row.get("atr_ratio",1.0))
        if np.isnan(atr_r): atr_r=1.0
        if atr_r<0.5: reasons.append("Volatility too low")
        if atr_r>3.0: reasons.append("Volatility too high")
        if int(row.get("regime",0))==4: reasons.append("Crisis regime — stand aside")
        return len(reasons)==0, reasons

    def save(self):
        joblib.dump(self.model,       MODELS_DIR/"model.joblib")
        joblib.dump(self.encoder,     MODELS_DIR/"encoder.joblib")
        joblib.dump(self.feature_cols,MODELS_DIR/"features.joblib")
        joblib.dump(self.train_meta,  MODELS_DIR/"meta.joblib")
        logger.info("Model saved")

    def load(self):
        self.model        = joblib.load(MODELS_DIR/"model.joblib")
        self.encoder      = joblib.load(MODELS_DIR/"encoder.joblib")
        self.feature_cols = joblib.load(MODELS_DIR/"features.joblib")
        self.train_meta   = joblib.load(MODELS_DIR/"meta.joblib")
        self.is_trained   = True
        logger.info("Model loaded")
