"""Gold Sniper v4 — Flask App (fixed: datetime, notifications, chart analysis)"""
import os, sys, time, logging, threading, traceback, base64
from pathlib import Path
from datetime import datetime, timezone
from collections import deque
import pandas as pd

from flask import Flask, jsonify, render_template, send_file, request
from flask_socketio import SocketIO, emit

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
(ROOT/"logs").mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[logging.FileHandler(ROOT/"logs"/"app.log"), logging.StreamHandler()])
logger = logging.getLogger("app")

from data_engine    import build_dataset, get_live_price
from feature_engine import build_features
from ml_engine      import GoldSniperModel
from backtester     import Backtester
from charts         import (plot_equity_curve, plot_signals,
                             plot_feature_importance, plot_monthly_heatmap,
                             plot_regime_breakdown, CHARTS_DIR)
from chart_analyser import analyse_with_model
import notifier

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = "goldsniper-v4"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading",
                    max_http_buffer_size=10_000_000)

model          = GoldSniperModel()
signal_history = deque(maxlen=200)
last_analytics = {}
last_backtest  = {}
last_chart_ana = {}
live_thread    = None
is_training = is_backtesting = is_scanning = False


def _price_worker():
    while True:
        try:
            tick = get_live_price()
            if tick["price"] > 0:
                socketio.emit("price_update", tick)
        except Exception: pass
        time.sleep(15)


def _run_scan():
    global last_analytics
    socketio.emit("sys", {"s":"scanning","m":"Scanning XAUUSD..."})
    try:
        df_raw = build_dataset(period="30d", interval="1h")
        df, fc = build_features(df_raw, label=False)
        df_p   = model.predict(df)
        sig    = model.latest_signal(df_p)
        sig["timestamp"] = datetime.now(timezone.utc).isoformat()

        last_row = df_p.iloc[-1]
        passed, reasons = model.risk_check(
            last_row, sig["signal"], sig["confidence"], sig["confluence"])
        sig["risk_passed"]  = passed
        sig["risk_reasons"] = reasons
        sig["shap"]         = model.explain_row(df_p)

        tick = get_live_price()
        if tick["price"] > 0:
            sig["live_price"]       = tick["price"]
            sig["price_change"]     = tick["change"]
            sig["price_change_pct"] = tick["change_pct"]

        # ── Analytics bars (FIXED: rename index col to 'datetime') ────────
        tail    = df_p.tail(100).copy()
        acols   = ["open","high","low","close","volume","ema_20","ema_50","ema_200",
                   "rsi","macd","macd_signal","macd_hist","bb_upper","bb_lower","bb_pct",
                   "atr","adx","signal","confidence","confluence","regime","pdh","pdl",
                   "bull_ob","bear_ob","in_bull_ob","in_bear_ob","bull_fvg","bear_fvg",
                   "sweep_pdh","sweep_pdl","bos","swing_high","swing_low","in_kz",
                   "stoch_k","stoch_d","ema_trend","choch"]
        present = [c for c in acols if c in tail.columns]
        tail_r  = tail[present].fillna(0).reset_index()
        # FIX: always rename first column (the index) to 'datetime'
        tail_r.columns = ["datetime"] + list(tail_r.columns[1:])
        tail_r["datetime"] = pd.to_datetime(tail_r["datetime"]).astype(str)

        sig["analytics_bars"] = tail_r.to_dict(orient="records")

        imp = model.feature_importances()
        if not imp.empty:
            sig["top_features"] = imp.head(15).to_dict(orient="records")

        signal_history.appendleft(sig)
        last_analytics = sig
        socketio.emit("signal_update", sig)
        socketio.emit("sys", {
            "s":"ready",
            "m": f"Scan done — {sig['signal']} @ ${sig.get('live_price',sig['close']):.2f}"
        })

        # Notify
        result = notifier.send_signal(sig) if (passed and sig["signal"]!="NO_TRADE") \
                 else notifier.send_scan(sig)
        logger.info(f"Notification: {result}")
        logger.info(f"Scan: {sig['signal']} Conf:{sig['confidence']}% "
                    f"Risk:{'PASS' if passed else 'FAIL'}")
        return sig
    except Exception as e:
        logger.error(f"Scan error: {e}\n{traceback.format_exc()}")
        socketio.emit("sys", {"s":"error","m":str(e)})
        return None


def _live_loop():
    logger.info("Auto live loop started")
    while True:
        if model.is_trained: _run_scan()
        time.sleep(900)


@app.route("/")
def index(): return render_template("index.html")

@app.route("/api/status")
def api_status():
    tg_ok = bool(notifier.TELEGRAM_BOT_TOKEN.strip() and notifier.TELEGRAM_CHAT_ID.strip())
    gm_ok = bool(notifier.GMAIL_SENDER.strip() and notifier.GMAIL_PASSWORD.strip())
    return jsonify({
        "model_loaded":   model.is_trained,
        "live_running":   live_thread is not None and live_thread.is_alive(),
        "is_training":    is_training,
        "is_backtesting": is_backtesting,
        "is_scanning":    is_scanning,
        "train_meta":     model.train_meta if model.is_trained else {},
        "server_time":    datetime.now(timezone.utc).isoformat(),
        "telegram_configured": tg_ok,
        "gmail_configured":    gm_ok,
    })

@app.route("/api/price")
def api_price(): return jsonify(get_live_price())

@app.route("/api/signal")
def api_signal():
    if not signal_history: return jsonify({"signal":"NO_TRADE","msg":"No scan yet"})
    return jsonify(signal_history[0])

@app.route("/api/history")
def api_history():
    return jsonify(list(signal_history)[:int(request.args.get("limit",50))])

@app.route("/api/analytics")
def api_analytics():
    if not last_analytics: return jsonify({"error":"No scan yet"}), 404
    return jsonify(last_analytics)

@app.route("/api/scan", methods=["POST"])
def api_scan():
    global is_scanning
    if is_scanning: return jsonify({"error":"Scan in progress"}), 409
    if not model.is_trained: return jsonify({"error":"Train the model first"}), 400
    def _do():
        global is_scanning
        is_scanning = True
        try: _run_scan()
        finally: is_scanning = False
    threading.Thread(target=_do, daemon=True).start()
    return jsonify({"msg":"Scan started"})

@app.route("/api/train", methods=["POST"])
def api_train():
    global is_training
    if is_training: return jsonify({"error":"Already training"}), 409
    def _do():
        global is_training
        is_training = True
        try:
            socketio.emit("sys",{"s":"training","m":"Fetching XAUUSD + macro data..."})
            df_raw = build_dataset(period="2y", interval="1h")
            socketio.emit("sys",{"s":"training","m":"Engineering features..."})
            df, fc = build_features(df_raw)
            socketio.emit("sys",{"s":"training","m":"Training XGBoost (5-fold WF-CV)..."})
            meta = model.train(df, fc, n_splits=5, oos_pct=0.2)
            socketio.emit("sys",{"s":"ready","m":"Training complete","metrics":meta})
        except Exception as e:
            logger.error(f"Train: {e}"); socketio.emit("sys",{"s":"error","m":str(e)})
        finally: is_training = False
    threading.Thread(target=_do, daemon=True).start()
    return jsonify({"msg":"Training started"})

@app.route("/api/backtest/run", methods=["POST"])
def api_backtest_run():
    global is_backtesting, last_backtest
    if is_backtesting: return jsonify({"error":"Already running"}), 409
    def _do():
        global is_backtesting, last_backtest
        is_backtesting = True
        try:
            for msg in ["Fetching 2y data...","Building features...","Simulating trades..."]:
                socketio.emit("sys",{"s":"backtesting","m":msg}); time.sleep(0.2)
            df_raw = build_dataset(period="2y", interval="1h")
            df, fc = build_features(df_raw)
            df_p   = model.predict(df)
            bt     = Backtester(10000,1.0,2.0,4,70.0,3,2)
            result = bt.run(df_p)
            last_backtest = {
                "summary": result["summary"],
                "trades":  result["trades"].to_dict(orient="records")[:100],
                "run_at":  datetime.now(timezone.utc).isoformat(),
            }
            socketio.emit("sys",{"s":"backtesting","m":"Generating charts..."})
            plot_equity_curve(result["equity_curve"],result["trades"],result["summary"])
            plot_signals(df_p, last_n=300)
            plot_feature_importance(model.feature_importances())
            plot_monthly_heatmap(result["trades"])
            plot_regime_breakdown(result["summary"])
            socketio.emit("backtest_complete", last_backtest["summary"])
            socketio.emit("sys",{"s":"ready","m":"Backtest complete"})
        except Exception as e:
            logger.error(f"Backtest: {e}\n{traceback.format_exc()}")
            socketio.emit("sys",{"s":"error","m":str(e)})
        finally: is_backtesting = False
    threading.Thread(target=_do, daemon=True).start()
    return jsonify({"msg":"Backtest started"})

@app.route("/api/backtest/result")
def api_backtest_result():
    if not last_backtest: return jsonify({"error":"No backtest yet"}), 404
    return jsonify(last_backtest)

# Chart serving — route var = function param (both 'chart_name')
@app.route("/api/chart/<chart_name>")
def api_chart(chart_name):
    charts = sorted(CHARTS_DIR.glob(f"{chart_name}*.png"))
    if not charts: return "", 404
    return send_file(str(charts[-1]), mimetype="image/png")

# Chart image analysis
@app.route("/api/analyse_chart", methods=["POST"])
def api_analyse_chart():
    global last_chart_ana
    if "image" not in request.files:
        return jsonify({"error":"No image uploaded"}), 400
    img_bytes = request.files["image"].read()
    def _do():
        global last_chart_ana
        socketio.emit("sys",{"s":"analysing","m":"Analysing chart image — detecting zones..."})
        try:
            result = analyse_with_model(img_bytes, model if model.is_trained else None)
            result["analysed_at"] = datetime.now(timezone.utc).isoformat()
            result["image_b64"]   = base64.b64encode(img_bytes).decode()
            last_chart_ana = result
            socketio.emit("chart_analysis_done", result)
            socketio.emit("sys",{"s":"ready","m":"Chart analysis complete"})
            notif = notifier.send_chart_analysis(result)
            logger.info(f"Chart analysis notification: {notif}")
        except Exception as e:
            logger.error(f"Chart analyse: {e}\n{traceback.format_exc()}")
            socketio.emit("sys",{"s":"error","m":str(e)})
    threading.Thread(target=_do, daemon=True).start()
    return jsonify({"msg":"Analysis started"})

@app.route("/api/chart_analysis")
def api_chart_analysis():
    if not last_chart_ana: return jsonify({"error":"No analysis yet"}), 404
    return jsonify({k:v for k,v in last_chart_ana.items() if k not in ("image_b64","overlay_svg")})

# Notification test
@app.route("/api/notify/test", methods=["POST"])
def api_notify_test():
    result = notifier.test_connection()
    return jsonify(result)

@app.route("/api/start_live", methods=["POST"])
def api_start_live():
    global live_thread
    if live_thread and live_thread.is_alive(): return jsonify({"msg":"Already running"})
    if not model.is_trained: return jsonify({"error":"Train the model first"}), 400
    live_thread = threading.Thread(target=_live_loop, daemon=True); live_thread.start()
    return jsonify({"msg":"Live loop started"})

@app.route("/api/logs")
def api_logs():
    lf    = ROOT/"logs"/"app.log"
    lines = int(request.args.get("lines",100))
    if not lf.exists(): return jsonify({"lines":[]})
    with open(lf) as f: all_lines = f.readlines()
    return jsonify({"lines":[l.rstrip() for l in all_lines[-lines:]]})

@app.route("/api/risk_rules")
def api_risk_rules():
    return jsonify({"rules":[
        {"rule":"Max risk per trade","value":"1%"},
        {"rule":"Max trades per day","value":"3"},
        {"rule":"Stop after consecutive losses","value":"2"},
        {"rule":"Min ML confidence","value":"70%"},
        {"rule":"Min confluence","value":"4 / 8"},
        {"rule":"Min R:R","value":"1 : 2"},
        {"rule":"Sessions","value":"London + NY only"},
        {"rule":"Volatility filter","value":"ATR 0.5× – 3.0× median"},
        {"rule":"Crisis regime","value":"No trades"},
    ]})

@socketio.on("connect")
def on_connect():
    emit("sys",{
        "s":"connected","model_loaded":model.is_trained,
        "live_running": live_thread is not None and live_thread.is_alive(),
    })
    tick = get_live_price()
    if tick["price"] > 0: emit("price_update", tick)

def startup():
    try: model.load(); logger.info("Model loaded")
    except: logger.info("No saved model — train via dashboard")
    threading.Thread(target=_price_worker, daemon=True).start()
    logger.info(f"CHARTS_DIR: {CHARTS_DIR}")
    logger.info(f"Telegram configured: {bool(notifier.TELEGRAM_BOT_TOKEN.strip() and notifier.TELEGRAM_CHAT_ID.strip())}")

if __name__ == "__main__":
    startup()
    port = int(os.environ.get("PORT",5000))
    logger.info(f"Gold Sniper v4 → http://localhost:{port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)
