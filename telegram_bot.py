import logging, requests
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token="", chat_id=""):
        self.token=token.strip(); self.chat_id=chat_id.strip()
        self.enabled=bool(self.token and self.chat_id); self.last_error=""

    def update(self, token, chat_id):
        self.token=token.strip(); self.chat_id=chat_id.strip()
        self.enabled=bool(self.token and self.chat_id); self.last_error=""

    def _send(self, text):
        if not self.enabled:
            return False, "Not configured — add token and chat_id in Settings"
        try:
            r=requests.post(f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={"chat_id":self.chat_id,"text":text,"parse_mode":"HTML",
                      "disable_web_page_preview":True},timeout=12)
            d=r.json()
            if r.status_code==200 and d.get("ok"):
                return True,"OK"
            code=d.get("error_code",r.status_code); desc=d.get("description","")
            if code==401: msg="Invalid bot token — revoke and create new one via @BotFather"
            elif code==400 and "chat not found" in desc.lower(): msg="Chat ID not found — send any message to your bot first, then refresh /getUpdates"
            elif code==403: msg="Bot blocked or no conversation started — open bot in Telegram and send /start"
            else: msg=f"Telegram API error {code}: {desc}"
            self.last_error=msg; return False, msg
        except requests.exceptions.ConnectionError: return False,"No internet connection to Telegram"
        except requests.exceptions.Timeout: return False,"Request timed out — try again"
        except Exception as e: return False, f"Error: {e}"

    def test(self):
        return self._send(f"✅ <b>Gold Sniper v4</b> connected!\n<code>{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</code>")

    def send_signal(self, sig):
        d=sig.get("signal","NO_TRADE")
        if d=="NO_TRADE": return False,"No signal"
        icon="🟢" if d=="BUY" else "🔴"
        shap=sig.get("shap",{}); drivers="\n".join(f"  {'+'if v>0 else '-'} {k}: {v:+.4f}" for k,v in list(shap.items())[:3])
        return self._send(f"{icon} <b>GOLD SNIPER — {d}</b>\n━━━━━━━━━━━━━━━━━━━━\nXAUUSD | {sig.get('timestamp','')[:16]} UTC\n\n💰 Entry: <b>${sig.get('close',0):.2f}</b>\n🛑 SL: ${sig.get('sl',0):.2f}\n🎯 TP: ${sig.get('tp',0):.2f}\n📐 R:R: 1:2\n\n📊 Confidence: {sig.get('confidence',0)}%\n🔗 Confluence: {sig.get('confluence',0)}/8\n🌍 Regime: {sig.get('regime_label','—')}\n⏰ Session: {sig.get('session','—')}\n\n{'✅ RISK PASS' if sig.get('risk_passed') else '⚠️ RISK FAIL: '+' | '.join((sig.get('risk_reasons') or [])[:2])}\n\n<b>Top drivers:</b>\n{drivers}\n\n<i>Risk 1% max. Not financial advice.</i>")

    def send_scan(self, sig):
        d=sig.get("signal","NO_TRADE"); icon="🟢" if d=="BUY" else "🔴" if d=="SELL" else "⚪"
        return self._send(f"{icon} <b>Scan</b> — {d} @ <b>${sig.get('close',0):.2f}</b>\nConf:{sig.get('confidence',0)}% | Confl:{sig.get('confluence',0)}/8 | {'✅ PASS' if sig.get('risk_passed') else '❌ FAIL'}")

    def send_chart_analysis(self, a):
        bias=a.get("bias","neutral").upper(); trend=a.get("trend","—").title()
        icon="🟢" if bias=="BUY" else "🔴" if bias=="SELL" else "⚪"
        obs="\n".join(f"  • {o}" for o in a.get("key_observations",[])[:3]); idea=a.get("trade_idea",{})
        return self._send(f"{icon} <b>Chart Analysis</b> — {trend} | {bias}\nMarket: {a.get('premium_discount','—')} | BOS: {a.get('market_structure',{}).get('last_bos','none')}\n\n<b>Observations:</b>\n{obs}\n\n<b>Trade Idea:</b> {(idea.get('direction','wait')).upper()}\n{idea.get('reasoning','—')}")

_bot=TelegramBot()
def get_bot(): return _bot
