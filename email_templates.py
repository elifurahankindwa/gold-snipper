"""
email_templates.py — Professional HTML email templates for Gold Sniper v4
Styled like a premium fintech/trading platform (BabyPips-inspired).
All CSS is inlined for maximum email client compatibility.
"""

from datetime import datetime, timezone


# ── Shared design tokens ────────────────────────────────────────────────────
GOLD   = "#C9A84C"
DARK   = "#0D1117"
DARK2  = "#161B22"
DARK3  = "#21262D"
WHITE  = "#FFFFFF"
GREY   = "#8B949E"
GREY2  = "#C9D1D9"
GREEN  = "#2EA043"
RED    = "#F85149"
BLUE   = "#388BFD"
AMBER  = "#E3B341"
BORDER = "#30363D"

LOGO_SVG = """
<svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="18" cy="18" r="17" stroke="#C9A84C" stroke-width="1.5" fill="#0D1117"/>
  <circle cx="18" cy="18" r="10" stroke="#C9A84C" stroke-width="1" fill="none"/>
  <circle cx="18" cy="18" r="5"  stroke="#C9A84C" stroke-width="1" fill="none"/>
  <circle cx="18" cy="18" r="2"  fill="#C9A84C"/>
  <line x1="18" y1="4"  x2="18" y2="8"  stroke="#C9A84C" stroke-width="1.5" stroke-linecap="round"/>
  <line x1="18" y1="28" x2="18" y2="32" stroke="#C9A84C" stroke-width="1.5" stroke-linecap="round"/>
  <line x1="4"  y1="18" x2="8"  y2="18" stroke="#C9A84C" stroke-width="1.5" stroke-linecap="round"/>
  <line x1="28" y1="18" x2="32" y2="18" stroke="#C9A84C" stroke-width="1.5" stroke-linecap="round"/>
</svg>
"""

CANDLESTICK_IMG = """
<svg width="120" height="60" viewBox="0 0 120 60" xmlns="http://www.w3.org/2000/svg">
  <!-- Candles -->
  <line x1="10" y1="8"  x2="10" y2="52" stroke="#30363D" stroke-width="1"/>
  <rect x="6"  y="22" width="8" height="20" fill="#2EA043" rx="1"/>
  <line x1="25" y1="5"  x2="25" y2="48" stroke="#30363D" stroke-width="1"/>
  <rect x="21" y="18" width="8" height="22" fill="#F85149" rx="1"/>
  <line x1="40" y1="12" x2="40" y2="50" stroke="#30363D" stroke-width="1"/>
  <rect x="36" y="24" width="8" height="18" fill="#2EA043" rx="1"/>
  <line x1="55" y1="6"  x2="55" y2="44" stroke="#30363D" stroke-width="1"/>
  <rect x="51" y="16" width="8" height="20" fill="#2EA043" rx="1"/>
  <line x1="70" y1="10" x2="70" y2="52" stroke="#30363D" stroke-width="1"/>
  <rect x="66" y="28" width="8" height="18" fill="#F85149" rx="1"/>
  <line x1="85" y1="4"  x2="85" y2="46" stroke="#30363D" stroke-width="1"/>
  <rect x="81" y="12" width="8" height="24" fill="#2EA043" rx="1"/>
  <line x1="100" y1="8" x2="100" y2="50" stroke="#30363D" stroke-width="1"/>
  <rect x="96" y="20" width="8" height="22" fill="#2EA043" rx="1"/>
  <!-- EMA line -->
  <polyline points="6,42 21,36 36,42 51,34 66,46 81,28 96,32" stroke="#C9A84C" stroke-width="1.5" fill="none" stroke-linecap="round"/>
</svg>
"""


def _now():
    return datetime.now(timezone.utc).strftime("%A, %d %B %Y · %H:%M UTC")


def _base_email(preheader: str, header_icon: str, header_title: str,
                header_subtitle: str, body_html: str, cta_text: str = "",
                cta_url: str = "#") -> str:
    """Base HTML email layout — professional dark fintech theme."""

    cta_block = f"""
      <table cellpadding="0" cellspacing="0" width="100%" style="margin-top:28px">
        <tr>
          <td align="center">
            <a href="{cta_url}"
               style="display:inline-block;background:{GOLD};color:{DARK};
                      font-family:'Helvetica Neue',Arial,sans-serif;
                      font-size:14px;font-weight:700;letter-spacing:.5px;
                      padding:13px 36px;border-radius:6px;text-decoration:none">
              {cta_text}
            </a>
          </td>
        </tr>
      </table>
    """ if cta_text else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>{header_title}</title>
  <!--[if mso]><style>table{{border-collapse:collapse}}</style><![endif]-->
</head>
<body style="margin:0;padding:0;background-color:#0A0D12;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif">

  <!-- Preheader (hidden preview text) -->
  <div style="display:none;max-height:0;overflow:hidden;font-size:1px;color:#0A0D12">
    {preheader}&nbsp;&#847;&nbsp;&#847;&nbsp;&#847;
  </div>

  <!-- Outer wrapper -->
  <table cellpadding="0" cellspacing="0" width="100%" bgcolor="#0A0D12">
    <tr><td align="center" style="padding:32px 16px 48px">

      <!-- Email card -->
      <table cellpadding="0" cellspacing="0" width="600"
             style="max-width:600px;width:100%;background:{DARK};
                    border-radius:12px;overflow:hidden;
                    border:1px solid {BORDER}">

        <!-- ─── HEADER ─────────────────────────────────────────── -->
        <tr>
          <td style="background:linear-gradient(135deg,{DARK} 0%,{DARK3} 100%);
                     border-bottom:1px solid {BORDER};padding:0">
            <!-- Top accent bar -->
            <div style="height:3px;background:linear-gradient(90deg,{GOLD} 0%,#A07830 50%,{GOLD} 100%)"></div>
            <table cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td style="padding:28px 36px 22px">
                  <!-- Brand row -->
                  <table cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                      <td width="44" valign="middle" style="padding-right:12px">
                        {LOGO_SVG}
                      </td>
                      <td valign="middle">
                        <div style="color:{GOLD};font-size:18px;font-weight:700;
                                    letter-spacing:.5px;line-height:1">
                          GOLD SNIPER
                        </div>
                        <div style="color:{GREY};font-size:11px;letter-spacing:1px;
                                    text-transform:uppercase;margin-top:2px">
                          XAUUSD Intelligence Platform
                        </div>
                      </td>
                      <td align="right" valign="middle">
                        {CANDLESTICK_IMG}
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>

            <!-- Hero band -->
            <table cellpadding="0" cellspacing="0" width="100%"
                   style="background:{DARK2};border-top:1px solid {BORDER};
                          border-bottom:1px solid {BORDER}">
              <tr>
                <td style="padding:22px 36px;text-align:center">
                  <div style="font-size:28px;margin-bottom:6px">{header_icon}</div>
                  <div style="color:{WHITE};font-size:20px;font-weight:700;
                              letter-spacing:-.3px;line-height:1.3">
                    {header_title}
                  </div>
                  <div style="color:{GREY};font-size:13px;margin-top:6px">
                    {header_subtitle}
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ─── BODY ──────────────────────────────────────────── -->
        <tr>
          <td style="padding:32px 36px;background:{DARK}">
            {body_html}
            {cta_block}
          </td>
        </tr>

        <!-- ─── DIVIDER ───────────────────────────────────────── -->
        <tr>
          <td style="padding:0 36px">
            <div style="height:1px;background:{BORDER}"></div>
          </td>
        </tr>

        <!-- ─── MARKET TICKER STRIP ───────────────────────────── -->
        <tr>
          <td style="background:{DARK3};padding:14px 36px">
            <table cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td style="color:{GREY};font-size:11px;text-transform:uppercase;
                           letter-spacing:.8px;font-weight:600">
                  Live Market Context
                </td>
              </tr>
              <tr>
                <td style="padding-top:8px">
                  <table cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="padding-right:24px">
                        <div style="color:{GREY};font-size:10px;text-transform:uppercase;
                                    letter-spacing:.6px">XAUUSD</div>
                        <div style="color:{GOLD};font-size:14px;font-weight:700;
                                    font-family:'Courier New',monospace">Gold</div>
                      </td>
                      <td style="padding-right:24px;border-left:1px solid {BORDER};
                                 padding-left:24px">
                        <div style="color:{GREY};font-size:10px;text-transform:uppercase;
                                    letter-spacing:.6px">Sessions</div>
                        <div style="color:{WHITE};font-size:12px;font-weight:600">
                          London · New York
                        </div>
                      </td>
                      <td style="border-left:1px solid {BORDER};padding-left:24px">
                        <div style="color:{GREY};font-size:10px;text-transform:uppercase;
                                    letter-spacing:.6px">Strategy</div>
                        <div style="color:{WHITE};font-size:12px;font-weight:600">
                          SMC · ICT Concepts
                        </div>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ─── FOOTER ────────────────────────────────────────── -->
        <tr>
          <td style="background:{DARK2};padding:24px 36px;
                     border-top:1px solid {BORDER}">
            <table cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td align="center">
                  <!-- Footer logo text -->
                  <div style="color:{GOLD};font-size:14px;font-weight:700;
                              letter-spacing:.5px;margin-bottom:8px">
                    GOLD SNIPER v4
                  </div>
                  <!-- Footer links -->
                  <div style="margin-bottom:14px">
                    <a href="http://localhost:5000/#dashboard"
                       style="color:{GREY};font-size:12px;text-decoration:none;
                              margin:0 10px">Dashboard</a>
                    <span style="color:{BORDER}">|</span>
                    <a href="http://localhost:5000/#analytics"
                       style="color:{GREY};font-size:12px;text-decoration:none;
                              margin:0 10px">Analytics</a>
                    <span style="color:{BORDER}">|</span>
                    <a href="http://localhost:5000/#settings"
                       style="color:{GREY};font-size:12px;text-decoration:none;
                              margin:0 10px">Settings</a>
                  </div>
                  <!-- Disclaimer -->
                  <div style="color:{GREY};font-size:11px;line-height:1.6;
                              max-width:460px;margin:0 auto">
                    This message was generated automatically by Gold Sniper v4.
                    Past performance is not indicative of future results.
                    <strong style="color:{AMBER}">Risk only what you can afford to lose.</strong>
                  </div>
                  <!-- Timestamp -->
                  <div style="color:#484F58;font-size:10px;margin-top:14px;
                              font-family:'Courier New',monospace;letter-spacing:.5px">
                    {_now()}
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Bottom accent bar -->
        <tr>
          <td style="height:3px;background:linear-gradient(90deg,{GOLD} 0%,#A07830 50%,{GOLD} 100%)"></td>
        </tr>

      </table>
      <!-- END email card -->

    </td></tr>
  </table>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
def _stat_cell(label: str, value: str, colour: str = WHITE) -> str:
    return f"""
      <td align="center" style="padding:14px 10px;border-right:1px solid {BORDER}">
        <div style="color:{GREY};font-size:10px;text-transform:uppercase;
                    letter-spacing:.7px;font-weight:600;margin-bottom:5px">{label}</div>
        <div style="color:{colour};font-size:18px;font-weight:700;
                    font-family:'Courier New',monospace">{value}</div>
      </td>"""


def _signal_bar(direction: str) -> str:
    is_buy  = direction == "BUY"
    colour  = GREEN if is_buy else RED
    bg      = "rgba(46,160,67,0.12)" if is_buy else "rgba(248,81,73,0.12)"
    arrow   = "▲" if is_buy else "▼"
    label   = "LONG · BUY" if is_buy else "SHORT · SELL"
    return f"""
    <table cellpadding="0" cellspacing="0" width="100%"
           style="background:{bg};border:1px solid {colour};
                  border-radius:8px;margin-bottom:24px">
      <tr>
        <td style="padding:18px 24px">
          <table cellpadding="0" cellspacing="0" width="100%">
            <tr>
              <td>
                <div style="color:{colour};font-size:28px;font-weight:700;
                            letter-spacing:1px;line-height:1">
                  {arrow} {label}
                </div>
                <div style="color:{GREY};font-size:12px;margin-top:4px">
                  XAUUSD · Spot Gold
                </div>
              </td>
              <td align="right">
                <div style="background:{colour};color:{DARK};font-size:11px;
                            font-weight:800;padding:5px 14px;border-radius:20px;
                            letter-spacing:.8px;text-transform:uppercase">
                  {"BUY" if is_buy else "SELL"} SIGNAL
                </div>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>"""


def _risk_badge(passed: bool, reasons: list) -> str:
    if passed:
        return f"""
    <table cellpadding="0" cellspacing="0" width="100%"
           style="background:rgba(46,160,67,0.08);border:1px solid {GREEN};
                  border-radius:8px;margin-top:20px">
      <tr>
        <td style="padding:14px 20px">
          <div style="color:{GREEN};font-size:14px;font-weight:700">
            ✅ ALL RISK FILTERS PASSED
          </div>
          <div style="color:{GREY};font-size:12px;margin-top:4px">
            Confluence · Confidence · Session · Volatility · Regime — all clear
          </div>
        </td>
      </tr>
    </table>"""
    reasons_html = "".join(
        f'<div style="color:{GREY};font-size:12px;padding:3px 0">⚠ {r}</div>'
        for r in (reasons or [])[:3]
    )
    return f"""
    <table cellpadding="0" cellspacing="0" width="100%"
           style="background:rgba(248,81,73,0.08);border:1px solid {RED};
                  border-radius:8px;margin-top:20px">
      <tr>
        <td style="padding:14px 20px">
          <div style="color:{RED};font-size:14px;font-weight:700">
            ❌ RISK FILTER FAILED — DO NOT TRADE
          </div>
          <div style="margin-top:8px">{reasons_html}</div>
        </td>
      </tr>
    </table>"""


def _shap_drivers(shap: dict) -> str:
    if not shap:
        return ""
    items = sorted(shap.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
    max_v = max(abs(v) for _, v in items) or 1
    rows  = ""
    for feat, val in items:
        pct = int(abs(val) / max_v * 100)
        col = GREEN if val > 0 else RED
        dir_lbl = "Bullish" if val > 0 else "Bearish"
        bar = f'<div style="height:6px;width:{pct}%;background:{col};border-radius:3px"></div>'
        rows += f"""
        <tr>
          <td style="padding:7px 0;border-bottom:1px solid {BORDER}">
            <table cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td width="180">
                  <div style="color:{GREY2};font-size:12px;font-family:'Courier New',monospace">
                    {feat}
                  </div>
                </td>
                <td>
                  <div style="background:{DARK3};border-radius:3px;height:6px;margin:0 12px">
                    {bar}
                  </div>
                </td>
                <td width="100" align="right">
                  <span style="color:{col};font-size:11px;font-family:'Courier New',monospace;
                               font-weight:700">{dir_lbl} {abs(val):.4f}</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>"""
    return f"""
    <div style="margin-top:24px">
      <div style="color:{GREY};font-size:11px;text-transform:uppercase;
                  letter-spacing:.8px;font-weight:600;margin-bottom:10px">
        AI Feature Drivers (SHAP)
      </div>
      <table cellpadding="0" cellspacing="0" width="100%">
        {rows}
      </table>
    </div>"""


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC TEMPLATE BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def build_signal_email(sig: dict) -> tuple[str, str]:
    """Returns (subject, html_body) for a trade signal."""
    direction = sig.get("signal", "NO_TRADE")
    price     = sig.get("live_price", sig.get("close", 0))
    passed    = sig.get("risk_passed", False)
    conf      = sig.get("confidence", 0)
    confl     = sig.get("confluence", 0)
    regime    = sig.get("regime_label", "—")
    session   = sig.get("session", "—")
    sl        = sig.get("sl", 0)
    tp        = sig.get("tp", 0)
    atr       = sig.get("atr", 0)
    ts        = sig.get("timestamp", "")[:16].replace("T", " ")

    subject = f"Gold Sniper {'🟢' if direction=='BUY' else '🔴'} {direction} Signal — XAUUSD @ ${price:.2f}"

    icon     = "🟢" if direction == "BUY" else "🔴"
    col_dir  = GREEN if direction == "BUY" else RED

    rr = 0
    if price and sl and tp:
        rr = abs(tp - price) / max(abs(sl - price), 0.01)

    body = f"""
    {_signal_bar(direction)}

    <!-- Stats grid -->
    <table cellpadding="0" cellspacing="0" width="100%"
           style="background:{DARK3};border:1px solid {BORDER};
                  border-radius:8px;margin-bottom:20px">
      <tr>
        {_stat_cell("Entry Price",  f"${price:.2f}",   GOLD)}
        {_stat_cell("Stop Loss",    f"${sl:.2f}",      RED)}
        {_stat_cell("Take Profit",  f"${tp:.2f}",      GREEN)}
        <td align="center" style="padding:14px 10px">
          <div style="color:{GREY};font-size:10px;text-transform:uppercase;
                      letter-spacing:.7px;font-weight:600;margin-bottom:5px">R:R Ratio</div>
          <div style="color:{AMBER};font-size:18px;font-weight:700;
                      font-family:'Courier New',monospace">1:{rr:.1f}</div>
        </td>
      </tr>
    </table>

    <!-- Details row -->
    <table cellpadding="0" cellspacing="0" width="100%"
           style="background:{DARK3};border:1px solid {BORDER};
                  border-radius:8px;margin-bottom:4px">
      <tr>
        {_stat_cell("Confidence",  f"{conf}%",   AMBER)}
        {_stat_cell("Confluence",  f"{confl}/8", AMBER)}
        {_stat_cell("ATR",         f"${atr:.2f}", GREY2)}
        {_stat_cell("Session",     session,       GREY2)}
      </tr>
    </table>
    <table cellpadding="0" cellspacing="0" width="100%"
           style="background:{DARK3};border:1px solid {BORDER};border-top:none;
                  border-radius:0 0 8px 8px;margin-bottom:8px">
      <tr>
        {_stat_cell("Regime",      regime,        BLUE)}
        {_stat_cell("Time",        ts + " UTC",   GREY2)}
        {_stat_cell("Strategy",    "SMC + XGBoost", GREY2)}
        {_stat_cell("Instrument",  "XAU/USD",     GOLD)}
      </tr>
    </table>

    {_risk_badge(passed, sig.get("risk_reasons", []))}
    {_shap_drivers(sig.get("shap", {}))}

    <!-- Risk warning box -->
    <table cellpadding="0" cellspacing="0" width="100%"
           style="background:{DARK3};border:1px solid {BORDER};
                  border-radius:8px;margin-top:24px">
      <tr>
        <td style="padding:16px 20px">
          <div style="color:{AMBER};font-size:12px;font-weight:700;margin-bottom:6px">
            ⚠ RISK MANAGEMENT REMINDER
          </div>
          <div style="color:{GREY};font-size:12px;line-height:1.7">
            Risk maximum <strong style="color:{WHITE}">1%</strong> of account per trade.
            Maximum <strong style="color:{WHITE}">3 trades</strong> per session.
            Stop trading after <strong style="color:{WHITE}">2 consecutive losses</strong>.
            This is not financial advice.
          </div>
        </td>
      </tr>
    </table>
    """

    html = _base_email(
        preheader  = f"XAUUSD {direction} @ ${price:.2f} — Conf:{conf}% Confl:{confl}/8",
        header_icon = icon,
        header_title = f"XAUUSD {direction} SIGNAL DETECTED",
        header_subtitle = f"Gold Sniper AI has identified a high-probability {direction.lower()} setup",
        body_html   = body,
        cta_text    = "View Full Analysis",
        cta_url     = "http://localhost:5000/#analytics",
    )
    return subject, html


def build_scan_email(sig: dict) -> tuple[str, str]:
    """Returns (subject, html_body) for a scan result (no tradeable signal)."""
    direction = sig.get("signal", "NO_TRADE")
    price     = sig.get("live_price", sig.get("close", 0))
    conf      = sig.get("confidence", 0)
    confl     = sig.get("confluence", 0)
    regime    = sig.get("regime_label", "—")
    passed    = sig.get("risk_passed", False)

    subject = f"Gold Sniper Scan Complete — XAUUSD {direction} ({conf}% confidence)"

    body = f"""
    <!-- Scan result banner -->
    <table cellpadding="0" cellspacing="0" width="100%"
           style="background:{DARK3};border:1px solid {BORDER};
                  border-radius:8px;margin-bottom:24px">
      <tr>
        <td style="padding:20px 24px">
          <div style="color:{GREY};font-size:12px;text-transform:uppercase;
                      letter-spacing:.8px;margin-bottom:8px">Scan Result</div>
          <div style="color:{WHITE};font-size:22px;font-weight:700">
            {direction}
            <span style="color:{GREY};font-size:14px;font-weight:400;margin-left:8px">
              @ ${price:.2f}
            </span>
          </div>
          <div style="color:{'#2EA043' if passed else '#F85149'};font-size:13px;
                      margin-top:8px;font-weight:600">
            {"✅ Risk filters passed — setup is tradeable" if passed
              else "⚠️ Risk filters failed — do not trade this setup"}
          </div>
        </td>
      </tr>
    </table>

    <table cellpadding="0" cellspacing="0" width="100%"
           style="background:{DARK3};border:1px solid {BORDER};border-radius:8px">
      <tr>
        {_stat_cell("Signal",     direction, GOLD)}
        {_stat_cell("Confidence", f"{conf}%", AMBER)}
        {_stat_cell("Confluence", f"{confl}/8", AMBER)}
        {_stat_cell("Regime",     regime, BLUE)}
      </tr>
    </table>

    <div style="color:{GREY};font-size:13px;line-height:1.7;margin-top:24px;
                padding:16px 20px;border-left:3px solid {GOLD};background:{DARK3};
                border-radius:0 8px 8px 0">
      The system completed a full market scan. To view the complete chart analysis,
      SHAP feature drivers, and trade plan, open the dashboard.
    </div>
    """

    html = _base_email(
        preheader    = f"Scan: {direction} @ ${price:.2f} | Conf:{conf}% | {'PASS' if passed else 'FAIL'}",
        header_icon  = "🔍",
        header_title = "MARKET SCAN COMPLETE",
        header_subtitle = f"XAUUSD analysed at {sig.get('timestamp','')[:16].replace('T',' ')} UTC",
        body_html    = body,
        cta_text     = "Open Dashboard",
        cta_url      = "http://localhost:5000/#dashboard",
    )
    return subject, html


def build_chart_analysis_email(a: dict) -> tuple[str, str]:
    """Returns (subject, html_body) for a chart image analysis."""
    bias   = a.get("bias", "neutral")
    trend  = a.get("trend", "unknown")
    mkt    = a.get("premium_discount", "equilibrium")
    bos    = a.get("market_structure", {}).get("last_bos", "none")
    lz     = a.get("liquidity_zones", [])
    sr     = a.get("support_resistance", [])
    ob     = a.get("order_blocks", [])
    fvg    = a.get("fair_value_gaps", [])
    choch  = a.get("choch_zones", [])
    obs    = a.get("key_observations", [])
    idea   = a.get("trade_idea", {})
    method = a.get("analysis_method", "—")

    bias_col  = GREEN if bias=="buy" else RED if bias=="sell" else GREY
    bias_lbl  = "BUY" if bias=="buy" else "SELL" if bias=="sell" else "NEUTRAL"

    subject = f"Gold Sniper Chart Analysis — {trend.title()} | {bias_lbl} Bias"

    def _zone_rows(zones, name, dot_col):
        if not zones: return ""
        rows = "".join(
            f'<tr><td style="padding:5px 0;border-bottom:1px solid {BORDER}">'
            f'<table cellpadding="0" cellspacing="0"><tr>'
            f'<td style="padding-right:10px"><div style="width:10px;height:10px;border-radius:2px;background:{dot_col}"></div></td>'
            f'<td style="color:{GREY2};font-size:12px">{z.get("description","—")} '
            f'<span style="color:{GREY};font-size:11px">({z.get("strength",z.get("type",""))})</span>'
            f'</td></tr></table></td></tr>'
            for z in zones[:4]
        )
        return f"""
        <div style="margin-bottom:16px">
          <div style="color:{GREY};font-size:10px;text-transform:uppercase;
                      letter-spacing:.8px;font-weight:600;margin-bottom:8px">{name}</div>
          <table cellpadding="0" cellspacing="0" width="100%">{rows}</table>
        </div>"""

    obs_html = "".join(
        f'<div style="color:{GREY2};font-size:13px;padding:6px 0;'
        f'border-bottom:1px solid {BORDER};line-height:1.5">'
        f'<span style="color:{GOLD};margin-right:8px">›</span>{o}</div>'
        for o in obs[:5]
    )

    idea_dir  = (idea.get("direction","wait") or "wait").upper()
    idea_col  = GREEN if idea_dir=="BUY" else RED if idea_dir=="SELL" else GREY

    choch_section = ""
    if choch:
        rows_c = "".join(
            f'<div style="color:{GREY2};font-size:12px;padding:4px 0">' +
            z.get("description", "—") + "</div>"
            for z in choch[:2]
        )
        choch_section = (
            f'<div style="margin-bottom:16px">' +
            f'<div style="color:{GREY};font-size:10px;text-transform:uppercase;' +
            f'letter-spacing:.8px;font-weight:600;margin-bottom:8px">CHOCH Zones</div>' +
            rows_c + "</div>"
        )
    body = f"""
    <!-- Bias hero -->
    <table cellpadding="0" cellspacing="0" width="100%"
           style="background:{'rgba(46,160,67,0.08)' if bias=='buy' else 'rgba(248,81,73,0.08)' if bias=='sell' else DARK3};
                  border:1px solid {bias_col};border-radius:8px;margin-bottom:24px">
      <tr>
        <td style="padding:20px 24px">
          <table cellpadding="0" cellspacing="0" width="100%">
            <tr>
              <td>
                <div style="color:{GREY};font-size:11px;text-transform:uppercase;
                            letter-spacing:.8px;margin-bottom:4px">Overall Bias</div>
                <div style="color:{bias_col};font-size:26px;font-weight:700">
                  {bias_lbl}
                </div>
                <div style="color:{GREY};font-size:13px;margin-top:4px">
                  {trend.title()} structure · Price in {mkt} zone
                </div>
              </td>
              <td align="right" style="vertical-align:top">
                <div style="background:{bias_col};color:{DARK};font-size:11px;
                            font-weight:800;padding:5px 14px;border-radius:20px">
                  {bias_lbl} SETUP
                </div>
                <div style="color:{GREY};font-size:11px;margin-top:8px;text-align:right">
                  BOS: {bos.title()} &nbsp;|&nbsp; Method: {method.replace("_"," ").title()}
                </div>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>

    <!-- Zone stats row -->
    <table cellpadding="0" cellspacing="0" width="100%"
           style="background:{DARK3};border:1px solid {BORDER};
                  border-radius:8px;margin-bottom:24px">
      <tr>
        {_stat_cell("Liquidity Zones", str(len(lz)), GOLD)}
        {_stat_cell("S/R Levels",      str(len(sr)), BLUE)}
        {_stat_cell("Order Blocks",    str(len(ob)), AMBER)}
        {_stat_cell("Fair Value Gaps", str(len(fvg)), "#7C3AED")}
      </tr>
    </table>

    <!-- Zone details -->
    <table cellpadding="0" cellspacing="0" width="100%">
      <tr>
        <td width="48%" valign="top">
          {_zone_rows(lz,   "Liquidity Zones",    RED   if bias=="sell" else GREEN)}
          {_zone_rows(ob,   "Order Blocks",       BLUE)}
        </td>
        <td width="4%"></td>
        <td width="48%" valign="top">
          {_zone_rows(sr,   "Support / Resistance", AMBER)}
          {_zone_rows(fvg,  "Fair Value Gaps",    "#7C3AED")}
        </td>
      </tr>
    </table>

    {choch_section}

    <!-- Observations -->
    <div style="margin-top:20px;margin-bottom:20px">
      <div style="color:{GREY};font-size:11px;text-transform:uppercase;
                  letter-spacing:.8px;font-weight:600;margin-bottom:10px">
        Key Observations
      </div>
      {obs_html}
    </div>

    <!-- Trade idea -->
    <table cellpadding="0" cellspacing="0" width="100%"
           style="background:{'rgba(46,160,67,0.08)' if idea_dir=='BUY' else 'rgba(248,81,73,0.08)' if idea_dir=='SELL' else DARK3};
                  border:1px solid {idea_col};border-radius:8px">
      <tr>
        <td style="padding:18px 22px">
          <div style="color:{idea_col};font-size:13px;font-weight:700;margin-bottom:12px">
            🎯 TRADE IDEA: {idea_dir}
          </div>
          <table cellpadding="0" cellspacing="0" width="100%">
            <tr>
              <td width="50%" valign="top" style="padding-right:12px">
                <div style="color:{GREY};font-size:11px;margin-bottom:3px">Entry Zone</div>
                <div style="color:{WHITE};font-size:13px;font-weight:600">{idea.get("entry_zone","—")}</div>
                <div style="color:{GREY};font-size:11px;margin-top:10px;margin-bottom:3px">Stop Loss</div>
                <div style="color:{RED};font-size:13px;font-weight:600">{idea.get("stop_loss","—")}</div>
              </td>
              <td width="50%" valign="top" style="padding-left:12px;border-left:1px solid {BORDER}">
                <div style="color:{GREY};font-size:11px;margin-bottom:3px">Take Profit</div>
                <div style="color:{GREEN};font-size:13px;font-weight:600">{idea.get("take_profit","—")}</div>
                <div style="color:{GREY};font-size:11px;margin-top:10px;margin-bottom:3px">R:R</div>
                <div style="color:{AMBER};font-size:13px;font-weight:600">1 : 2</div>
              </td>
            </tr>
          </table>
          <div style="color:{GREY};font-size:12px;margin-top:14px;line-height:1.6;
                      padding-top:12px;border-top:1px solid {BORDER}">
            <em>{idea.get("reasoning","—")}</em>
          </div>
        </td>
      </tr>
    </table>
    """

    html = _base_email(
        preheader    = f"Chart Analysis: {trend.title()} | {bias_lbl} | {len(lz)} liq zones, {len(sr)} S/R",
        header_icon  = "📊",
        header_title = "CHART ANALYSIS COMPLETE",
        header_subtitle = f"AI identified {len(lz)+len(sr)+len(ob)+len(fvg)} zones — {trend.title()} structure detected",
        body_html    = body,
        cta_text     = "View Annotated Chart",
        cta_url      = "http://localhost:5000/#analytics",
    )
    return subject, html


def build_test_email() -> tuple[str, str]:
    """Returns (subject, html_body) for a connection test."""
    subject = "Gold Sniper v4 — Email Notification Test ✅"
    body = f"""
    <table cellpadding="0" cellspacing="0" width="100%"
           style="background:rgba(46,160,67,0.08);border:1px solid {GREEN};
                  border-radius:8px;margin-bottom:24px">
      <tr>
        <td style="padding:22px 24px;text-align:center">
          <div style="font-size:40px;margin-bottom:10px">✅</div>
          <div style="color:{GREEN};font-size:18px;font-weight:700">
            Email notifications are working!
          </div>
          <div style="color:{GREY};font-size:13px;margin-top:8px">
            Your Gold Sniper v4 system will send professional HTML alerts
            for trade signals, scan results, and chart analysis.
          </div>
        </td>
      </tr>
    </table>

    <div style="color:{GREY};font-size:13px;line-height:1.8">
      You will receive emails for:
      <ul style="margin:12px 0;padding-left:20px">
        <li style="margin-bottom:6px"><strong style="color:{WHITE}">Trade Signals</strong> — BUY/SELL setups with entry, SL, TP, and SHAP analysis</li>
        <li style="margin-bottom:6px"><strong style="color:{WHITE}">Scan Results</strong> — Every 15-minute auto-scan summary</li>
        <li style="margin-bottom:6px"><strong style="color:{WHITE}">Chart Analysis</strong> — Detected zones when you upload a chart image</li>
      </ul>
    </div>

    <table cellpadding="0" cellspacing="0" width="100%"
           style="background:{DARK3};border:1px solid {BORDER};
                  border-radius:8px;margin-top:20px">
      <tr>
        {_stat_cell("Strategy", "SMC + ICT", GOLD)}
        {_stat_cell("Model", "XGBoost v2", BLUE)}
        {_stat_cell("Risk", "1% max", AMBER)}
        {_stat_cell("R:R", "1 : 2 min", GREEN)}
      </tr>
    </table>
    """

    html = _base_email(
        preheader    = "Gold Sniper email notifications are configured and working.",
        header_icon  = "✅",
        header_title = "CONNECTION TEST SUCCESSFUL",
        header_subtitle = "Gold Sniper v4 · XAUUSD Intelligence Platform",
        body_html    = body,
        cta_text     = "Open Dashboard",
        cta_url      = "http://localhost:5000/#dashboard",
    )
    return subject, html
