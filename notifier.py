"""
notifier.py — Telegram + Gmail fallback notification system
Credentials are hardcoded here for security (not exposed in web UI).
"""
import logging, smtplib, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email_templates as tmpl

logger = logging.getLogger(__name__)

# ── CONFIGURE YOUR CREDENTIALS HERE ────────────────────────────────────────
TELEGRAM_BOT_TOKEN = ""   # e.g. "8695234248:AAFSu2_SD6..."
TELEGRAM_CHAT_ID   = ""   # e.g. "987654321"

GMAIL_SENDER    = ""      # e.g. "you@gmail.com"
GMAIL_PASSWORD  = ""      # Gmail App Password (Google Account → Security → App passwords)
GMAIL_RECIPIENT = ""      # who receives alerts — can be same as sender
# ───────────────────────────────────────────────────────────────────────────


def _tg_send(text: str) -> tuple[bool, str]:
    token   = TELEGRAM_BOT_TOKEN.strip()
    chat_id = TELEGRAM_CHAT_ID.strip()
    if not token or not chat_id:
        return False, "Telegram not configured in notifier.py"
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text,
                  "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=12,
        )
        d = r.json()
        if r.status_code == 200 and d.get("ok"):
            return True, "OK"
        code = d.get("error_code", r.status_code)
        desc = d.get("description", "")
        if code == 401:
            return False, "Invalid token — create a new one via @BotFather"
        if code == 400 and "chat not found" in desc.lower():
            return False, "Chat ID not found — send any message to your bot first"
        if code == 403:
            return False, "Bot blocked — open bot in Telegram and send /start"
        return False, f"Telegram {code}: {desc}"
    except requests.exceptions.ConnectionError:
        return False, "No internet connection to Telegram"
    except Exception as e:
        return False, f"Telegram error: {e}"


def _gmail_send(subject: str, html_body: str) -> tuple[bool, str]:
    sender = GMAIL_SENDER.strip()
    pw     = GMAIL_PASSWORD.strip()
    rcpt   = (GMAIL_RECIPIENT or sender).strip()
    if not sender or not pw:
        return False, "Gmail not configured in notifier.py"
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"Gold Sniper <{sender}>"
        msg["To"]      = rcpt
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(sender, pw)
            s.sendmail(sender, rcpt, msg.as_string())
        logger.info(f"Gmail sent to {rcpt}")
        return True, f"Email sent to {rcpt}"
    except smtplib.SMTPAuthenticationError:
        return False, "Gmail auth failed — use an App Password, not your regular password"
    except Exception as e:
        return False, f"Gmail error: {e}"


def _notify(subject: str, html_body: str, tg_text: str = "") -> dict:
    """Try Telegram first, fall back to Gmail."""
    # Telegram (plain text version)
    tg_ok, tg_msg = _tg_send(tg_text or _html_to_tg(html_body))
    if tg_ok:
        return {"method": "telegram", "ok": True, "msg": "Telegram OK"}
    logger.warning(f"Telegram failed: {tg_msg} — trying Gmail")

    # Gmail (full HTML)
    gm_ok, gm_msg = _gmail_send(subject, html_body)
    if gm_ok:
        return {"method": "gmail", "ok": True, "msg": gm_msg}

    logger.error("Both Telegram and Gmail failed")
    return {"method": "none", "ok": False,
            "msg": f"Telegram: {tg_msg} | Gmail: {gm_msg}"}


def _html_to_tg(html: str) -> str:
    """Strip HTML to Telegram-safe plain text (keeps <b> and <i>)."""
    import re
    text = re.sub(r'<(?!/?(?:b|i|strong|em|code)\b)[^>]+>', '', html)
    text = text.replace('<strong>', '<b>').replace('</strong>', '</b>')
    text = text.replace('<em>', '<i>').replace('</em>', '</i>')
    return text[:4000]


# ── PUBLIC API ────────────────────────────────────────────────────────────

def send_signal(sig: dict) -> dict:
    if sig.get("signal") == "NO_TRADE":
        return {"method": "none", "ok": False, "msg": "No signal"}
    subject, html = tmpl.build_signal_email(sig)
    tg = _tg_plain_signal(sig)
    return _notify(subject, html, tg)


def send_scan(sig: dict) -> dict:
    subject, html = tmpl.build_scan_email(sig)
    tg = (f"🔍 Scan: {sig.get('signal','—')} @ ${sig.get('live_price',sig.get('close',0)):.2f} | "
          f"Conf:{sig.get('confidence',0)}% | {'PASS' if sig.get('risk_passed') else 'FAIL'}")
    return _notify(subject, html, tg)


def send_chart_analysis(a: dict) -> dict:
    subject, html = tmpl.build_chart_analysis_email(a)
    bias  = a.get("bias","neutral").upper()
    trend = a.get("trend","—").title()
    icon  = "🟢" if bias=="BUY" else "🔴" if bias=="SELL" else "⚪"
    tg = (f"{icon} Chart Analysis — {trend} | {bias}\n"
          f"Zones: {len(a.get('liquidity_zones',[]))} liq, "
          f"{len(a.get('support_resistance',[]))} S/R, "
          f"{len(a.get('order_blocks',[]))} OB")
    return _notify(subject, html, tg)


def test_connection() -> dict:
    subject, html = tmpl.build_test_email()
    tg_ok, tg_msg = _tg_send("✅ <b>Gold Sniper v4</b> — Telegram connected!")
    result = {"telegram": {"ok": tg_ok, "msg": tg_msg}}
    gm_ok, gm_msg = _gmail_send(subject, html)
    result["gmail"] = {"ok": gm_ok, "msg": gm_msg}
    return result


# ── Private Telegram plain text (short) ──────────────────────────────────

def _tg_plain_signal(sig: dict) -> str:
    d    = sig.get("signal","NO_TRADE")
    p    = sig.get("live_price", sig.get("close",0))
    icon = "🟢" if d=="BUY" else "🔴"
    shap = sig.get("shap",{})
    drivers = "\n".join(
        f"  {'+'if v>0 else '-'} {k}: {v:+.4f}"
        for k,v in list(shap.items())[:3]
    )
    return (
        f"{icon} <b>GOLD SNIPER — {d}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"XAUUSD | {sig.get('timestamp','')[:16]} UTC\n\n"
        f"💰 Entry:  <b>${p:.2f}</b>\n"
        f"🛑 SL:     ${sig.get('sl',0):.2f}\n"
        f"🎯 TP:     ${sig.get('tp',0):.2f}\n"
        f"📐 R:R:    1:2\n\n"
        f"📊 Confidence: {sig.get('confidence',0)}%\n"
        f"🔗 Confluence: {sig.get('confluence',0)}/8\n"
        f"🌍 Regime: {sig.get('regime_label','—')}\n"
        f"⏰ Session: {sig.get('session','—')}\n\n"
        f"{'✅ RISK PASS' if sig.get('risk_passed') else '⚠️ RISK FAIL: '+' | '.join((sig.get('risk_reasons') or [])[:2])}\n\n"
        f"<b>Top drivers:</b>\n{drivers}\n\n"
        f"<i>Risk 1% max. Not financial advice.</i>"
    )
