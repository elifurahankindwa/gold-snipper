"""
chart_analyser.py
─────────────────
Clean, precise chart analysis with professional SVG overlays and zone filtering.
No external API. Uses PIL + numpy CV only.
"""
import io, logging, numpy as np, base64
logger = logging.getLogger(__name__)

ZONE_LIQUIDITY = "liquidity"
ZONE_SR        = "support_resistance"
ZONE_OB        = "order_block"
ZONE_FVG       = "fvg"
ZONE_CHOCH     = "choch"
ZONE_BOS       = "bos"
ZONE_PREMIUM   = "premium_discount"
ALL_ZONES      = [ZONE_LIQUIDITY, ZONE_SR, ZONE_OB, ZONE_FVG,
                  ZONE_CHOCH, ZONE_BOS, ZONE_PREMIUM]


def analyse_with_model(image_bytes: bytes, model=None) -> dict:
    result = _analyse(image_bytes)
    if model and model.is_trained:
        _enrich(result, model)
    result["overlay_svg"]    = build_overlay_svg(image_bytes, result, ALL_ZONES)
    result["overlay_layers"] = {zt: build_overlay_svg(image_bytes, result, [zt]) for zt in ALL_ZONES}
    return result


def build_overlay_svg(image_bytes: bytes, result: dict, visible_zones: list = None) -> str:
    if visible_zones is None:
        visible_zones = ALL_ZONES
    return _svg(image_bytes, result, set(visible_zones))


def _analyse(image_bytes: bytes) -> dict:
    try:
        from PIL import Image
        img    = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        W0, H0 = img.size
        WA, HA = 900, 500
        img_a  = img.resize((WA, HA), Image.LANCZOS)
        arr    = np.array(img_a, dtype=np.float32)
        H, W   = arr.shape[:2]
        r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

        bright = (r + g + b) / 3
        sat    = (np.maximum(r, np.maximum(g, b)) - np.minimum(r, np.minimum(g, b)))
        candle = (sat > 28) & (bright > 35) & (bright < 235)
        grn    = candle & (g > r + 22)
        red    = candle & (r > g + 22)
        tot    = float(H * W)
        g_pct  = float(np.sum(grn)) / tot * 100
        r_pct  = float(np.sum(red)) / tot * 100

        if   g_pct > r_pct * 1.3 and g_pct > 0.8:  trend = "bullish"
        elif r_pct > g_pct * 1.3 and r_pct > 0.8:  trend = "bearish"
        else:                                         trend = "ranging"

        # Row activity map
        dark        = (bright < 205) & candle
        row_dens    = np.sum(dark, axis=1).astype(float) / W
        kernel      = np.ones(9) / 9
        row_s       = np.convolve(row_dens, kernel, mode='same')
        row_max     = row_s.max()
        thresh      = max(row_max * 0.35, 0.005) if row_max > 0 else 0.005
        active      = np.where(row_s > thresh)[0]

        zones = []
        if len(active):
            cl = [active[0]]
            for i in range(1, len(active)):
                if active[i] - active[i-1] > H * 0.025:
                    _push(zones, cl, H, row_s); cl = []
                cl.append(active[i])
            _push(zones, cl, H, row_s)

        # S/R levels from strongest zones
        sr = []
        for z in sorted(zones, key=lambda x: x["act"], reverse=True)[:10]:
            p = z["mid"]
            if p < 0.07 or p > 0.93: continue
            t = "resistance" if p < 0.47 else "support" if p > 0.53 else "key level"
            s = "major" if z["act"] > thresh * 2 else "minor"
            sr.append({"type":t,"pct_top":z["top"],"pct_bot":z["bot"],
                        "pct_mid":p,"strength":s,"act":z["act"],
                        "description":f"{s.title()} {t}"})
        sr.sort(key=lambda x: x["pct_mid"])

        # Liquidity zones
        mid_avg = float(row_s[int(H*.3):int(H*.7)].mean()) + 1e-6
        liq = []
        if row_s[:int(H*.12)].mean() > mid_avg * 0.45:
            liq.append({"type":"sell_side","pct_top":0.01,"pct_bot":0.12,"pct_mid":0.065,
                         "strength":"strong","swept":False,
                         "description":"Sell-side liquidity (equal highs)"})
        if row_s[int(H*.88):].mean() > mid_avg * 0.45:
            liq.append({"type":"buy_side","pct_top":0.88,"pct_bot":0.99,"pct_mid":0.935,
                         "strength":"strong","swept":False,
                         "description":"Buy-side liquidity (equal lows)"})

        # Order blocks
        obs = _obs(arr, H, W, trend)

        # FVGs
        fvgs = _fvg(sr, row_s, H, trend)

        # Current price position
        rs        = bright[:, int(W*.85):]
        rc        = np.sum(rs < 185, axis=1).astype(float)
        ractive   = np.where(rc > rc.max() * 0.3)[0]
        curr_pct  = float(np.mean(ractive)/H) if len(ractive) else 0.5

        if   curr_pct < 0.38: mkt = "premium"
        elif curr_pct > 0.62: mkt = "discount"
        else:                  mkt = "equilibrium"

        bos = "none"
        if trend=="bullish" and curr_pct < 0.45: bos = "bullish"
        elif trend=="bearish" and curr_pct > 0.55: bos = "bearish"

        choch = []
        rec   = arr[:, int(W*.72):, :]
        rec_g = np.mean(rec, axis=2)
        rec_a = np.sum(rec_g < 185, axis=1).astype(float) / rec.shape[1]
        for s2 in sr[:4]:
            y1 = int(s2["pct_top"]*H); y2 = int(s2["pct_bot"]*H)
            if y2 > y1 and rec_a[y1:y2].mean() > 0.10:
                choch.append({"pct_mid":s2["pct_mid"],"pct_top":s2["pct_top"],
                               "pct_bot":s2["pct_bot"],
                               "type":"bullish" if s2["pct_mid"]>0.5 else "bearish",
                               "description":f"CHOCH at {'support' if s2['pct_mid']>0.5 else 'resistance'}"})

        if trend=="bullish": bias = "buy" if mkt!="premium" else "neutral"
        elif trend=="bearish": bias = "sell" if mkt!="discount" else "neutral"
        else: bias = "neutral"

        obs_list = [
            f"{trend.title()} structure — {g_pct:.1f}% bullish vs {r_pct:.1f}% bearish candle coverage",
            f"Price in {mkt} zone ({(1-curr_pct)*100:.0f}% from bottom of visible range)",
            f"Found {len(sr)} S/R levels · {len(liq)} liquidity zones · {len(obs)} OBs · {len(fvgs)} FVGs",
        ]
        if bos!="none": obs_list.append(f"{bos.title()} break of structure confirmed")
        if choch:       obs_list.append(f"CHOCH detected at {len(choch)} zone(s)")

        entry = "Wait for clearer setup"
        if bias=="buy" and sr:
            sup = [s2 for s2 in sr if s2["pct_mid"]>0.55]
            entry = f"Pullback to {sup[0]['description']}" if sup else "Nearest demand zone"
        elif bias=="sell" and sr:
            res = [s2 for s2 in sr if s2["pct_mid"]<0.45]
            entry = f"Rally into {res[-1]['description']}" if res else "Nearest supply zone"

        return {"trend":trend,"bias":bias,"premium_discount":mkt,
                "current_pct_y":round(curr_pct,3),
                "liquidity_zones":liq,"support_resistance":sr,
                "market_structure":{"last_bos":bos,"last_choch":"none"},
                "order_blocks":obs,"fair_value_gaps":fvgs,"choch_zones":choch,
                "key_observations":obs_list,
                "trade_idea":{"direction":bias if bias!="neutral" else "wait",
                               "entry_zone":entry,
                               "stop_loss":"Beyond nearest liquidity level",
                               "take_profit":"Opposing S/R / liquidity zone",
                               "reasoning":f"CV: {trend}, {mkt}, {len(sr)} zones"},
                "analysis_method":"model_pixel_cv",
                "image_w":W0,"image_h":H0,"green_pct":round(g_pct,1),"red_pct":round(r_pct,1)}
    except Exception as e:
        logger.error(f"Analysis error: {e}"); import traceback; traceback.print_exc()
        return _fallback()


def _push(zones, cl, H, smooth):
    if not cl: return
    mid = int(np.mean(cl))
    zones.append({"top":round(max(0,cl[0]-2)/H,3),"bot":round(min(H-1,cl[-1]+2)/H,3),
                  "mid":round(mid/H,3),"act":float(smooth[mid]) if mid<len(smooth) else 0})


def _obs(arr, H, W, trend):
    r,g = arr[:,:,0], arr[:,:,1]
    rg  = ((g>r+35)&(g>70)).astype(float).mean(axis=1)
    rr  = ((r>g+35)&(r>70)).astype(float).mean(axis=1)
    blocks = []
    def find(density, ob_type):
        for i in range(12, H-12):
            if density[i] < 0.045: continue
            nbr = max(density[max(0,i-18):i].mean(), 0.001)
            if density[i] < nbr*1.8: continue
            p = i/H
            if (ob_type=="bullish" and p>0.42) or (ob_type=="bearish" and p<0.58):
                blocks.append({"type":ob_type,"pct_top":round(max(0,(i-12)/H),3),
                                "pct_bot":round(min(1,(i+12)/H),3),"pct_mid":round(p,3),
                                "valid":True,"description":f"{'Bullish' if ob_type=='bullish' else 'Bearish'} Order Block"})
                return
    find(rg,"bullish"); find(rr,"bearish")
    return blocks


def _fvg(sr, row_s, H, trend):
    fvgs=[]; avg=row_s.mean()+1e-6
    for i in range(len(sr)-1):
        a,b=sr[i],sr[i+1]
        gap=b["pct_top"]-a["pct_bot"]
        if gap<0.035 or gap>0.20: continue
        y1,y2=int(a["pct_bot"]*H),int(b["pct_top"]*H)
        if y2<=y1: continue
        if row_s[y1:y2].mean()<avg*0.52:
            fvgs.append({"type":"bullish" if trend=="bullish" else "bearish",
                          "pct_top":a["pct_bot"],"pct_bot":b["pct_top"],
                          "pct_mid":(a["pct_bot"]+b["pct_top"])/2,"filled":False,
                          "description":f"FVG ({gap*100:.1f}%)"})
    return fvgs[:3]


def _enrich(result, model):
    try:
        imp=model.feature_importances().head(5); names=imp["feature"].tolist() if not imp.empty else []
        meta=model.train_meta or {}
        result["key_observations"].append(f"Model: {meta.get('feature_count',0)} features, top: {', '.join(names[:3])}")
        result["analysis_method"]="model_cv_enriched"; result["model_top_features"]=names
    except Exception as e: logger.debug(f"Enrich: {e}")


# ── Colour palette ──────────────────────────────────────────────────────────
C = {
    "sell_liq": "#FF4757", "buy_liq": "#2ED573",
    "resist":   "#FFA502", "support": "#1E90FF",
    "ob_bull":  "#26de81", "ob_bear": "#FC5C65",
    "fvg":      "#A29BFE", "choch":   "#FDCB6E",
    "bos":      "#6C5CE7", "text":    "#FFFFFF",
    "bg":       "rgba(0,0,0,0.70)",
}


def _svg(image_bytes: bytes, result: dict, visible: set) -> str:
    try:
        from PIL import Image
        img  = Image.open(io.BytesIO(image_bytes))
        W, H = 900, 500
        buf  = io.BytesIO(); img.resize((W,H),Image.LANCZOS).save(buf,format="PNG")
        b64  = base64.b64encode(buf.getvalue()).decode()
        els  = []

        def py(p): return round(p*H)
        def px(p): return round(p*W)

        def zone_rect(y1, y2, fill, stroke, sw, dash=""):
            ht = max(3, y2-y1)
            d  = f'stroke-dasharray="{dash}"' if dash else ""
            els.append(f'<rect x="0" y="{y1}" width="{W}" height="{ht}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {d}/>')

        def lbl_left(y1, ht, text, col, size=9):
            ty = y1 + min(ht-2, 13)
            tw = len(text)*6+8
            els.append(f'<rect x="5" y="{y1+2}" width="{tw}" height="13" fill="{C["bg"]}" rx="2"/>')
            els.append(f'<text x="9" y="{ty}" fill="{col}" font-size="{size}" font-family="monospace" font-weight="700" letter-spacing="0.2">{text}</text>')

        def lbl_right(y1, ht, text, col, size=9):
            tw = len(text)*6+8
            x  = W-tw-5
            ty = y1+min(ht-2,13)
            els.append(f'<rect x="{x}" y="{y1+2}" width="{tw}" height="13" fill="{C["bg"]}" rx="2"/>')
            els.append(f'<text x="{x+4}" y="{ty}" fill="{col}" font-size="{size}" font-family="monospace" font-weight="700" letter-spacing="0.2">{text}</text>')

        def pill(y, text, col, side="right"):
            tw = len(text)*6+12
            if side=="right": x = W-tw-5
            else: x = 5
            els.append(f'<rect x="{x}" y="{y-10}" width="{tw}" height="18" fill="{col}" rx="4"/>')
            els.append(f'<text x="{x+tw//2}" y="{y+3}" fill="white" font-size="9" font-family="monospace" font-weight="700" text-anchor="middle" letter-spacing="0.4">{text}</text>')

        # ── Premium/Discount divider ──────────────────────────────────────
        if ZONE_PREMIUM in visible:
            my = H//2
            els.append(f'<line x1="0" y1="{my}" x2="{W}" y2="{my}" stroke="rgba(255,255,255,0.18)" stroke-width="1" stroke-dasharray="8,5"/>')
            els.append(f'<text x="10" y="{my-5}" fill="rgba(255,180,80,0.5)" font-size="8" font-family="monospace" font-weight="700" letter-spacing="1">PREMIUM</text>')
            els.append(f'<text x="10" y="{my+14}" fill="rgba(80,220,120,0.5)" font-size="8" font-family="monospace" font-weight="700" letter-spacing="1">DISCOUNT</text>')

        # ── FVG (render first so other zones appear on top) ───────────────
        if ZONE_FVG in visible:
            for z in result.get("fair_value_gaps",[]):
                y1,y2 = py(z["pct_top"]),py(z["pct_bot"]); ht=max(4,y2-y1)
                zone_rect(y1,y2,"rgba(162,155,254,0.13)",C["fvg"],"1","5,3")
                lbl_right(y1,ht,"FVG",C["fvg"])

        # ── S/R levels ────────────────────────────────────────────────────
        if ZONE_SR in visible:
            for z in result.get("support_resistance",[]):
                y1,y2 = py(z["pct_top"]),py(z["pct_bot"]); ht=max(3,y2-y1)
                is_r = z["type"]=="resistance"; ismaj = z.get("strength")=="major"
                col  = C["resist"] if is_r else C["support"]
                fill = f"rgba(255,165,2,0.08)" if is_r else "rgba(30,144,255,0.08)"
                sw   = "1.5" if ismaj else "0.8"
                dash = "" if ismaj else "4,3"
                zone_rect(y1,y2,fill,col,sw,dash)
                lbl_left(y1,ht,("R★" if ismaj else "R·") if is_r else ("S★" if ismaj else "S·"),col)

        # ── Liquidity zones ───────────────────────────────────────────────
        if ZONE_LIQUIDITY in visible:
            for z in result.get("liquidity_zones",[]):
                y1,y2 = py(z["pct_top"]),py(z["pct_bot"]); ht=max(5,y2-y1)
                is_s = z["type"]=="sell_side"
                col  = C["sell_liq"] if is_s else C["buy_liq"]
                fill = "rgba(255,71,87,0.11)" if is_s else "rgba(46,213,115,0.11)"
                zone_rect(y1,y2,fill,col,"1.5","6,3")
                els.append(f'<rect x="0" y="{y1}" width="5" height="{ht}" fill="{col}"/>')
                lbl_left(y1,ht,"SSL" if is_s else "BSL",col)

        # ── Order Blocks ──────────────────────────────────────────────────
        if ZONE_OB in visible:
            for z in result.get("order_blocks",[]):
                y1,y2 = py(z["pct_top"]),py(z["pct_bot"]); ht=max(6,y2-y1)
                is_b = z["type"]=="bullish"
                col  = C["ob_bull"] if is_b else C["ob_bear"]
                fill = "rgba(38,222,129,0.15)" if is_b else "rgba(252,92,101,0.15)"
                zone_rect(y1,y2,fill,col,"2")
                els.append(f'<rect x="0" y="{y1}" width="6" height="{ht}" fill="{col}"/>')
                lbl_left(y1,ht,"Bull OB" if is_b else "Bear OB",col)

        # ── CHOCH ─────────────────────────────────────────────────────────
        if ZONE_CHOCH in visible:
            for z in result.get("choch_zones",[]):
                y = py(z["pct_mid"])
                els.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{C["choch"]}" stroke-width="1.5" stroke-dasharray="9,4"/>')
                pill(y,"CHOCH",C["choch"])

        # ── BOS ───────────────────────────────────────────────────────────
        if ZONE_BOS in visible:
            bos = result.get("market_structure",{}).get("last_bos","none")
            if bos!="none":
                by = py(0.36 if bos=="bullish" else 0.64)
                els.append(f'<line x1="0" y1="{by}" x2="{W}" y2="{by}" stroke="{C["bos"]}" stroke-width="1.5" stroke-dasharray="7,4"/>')
                pill(by,f"BOS {bos[:4].upper()}",C["bos"])

        # ── Current price marker ──────────────────────────────────────────
        cy = py(result.get("current_pct_y",0.5))
        els.append(f'<line x1="{int(W*0.6)}" y1="{cy}" x2="{W-58}" y2="{cy}" stroke="rgba(255,255,255,0.55)" stroke-width="1.2" stroke-dasharray="3,2"/>')
        els.append(f'<rect x="{W-56}" y="{cy-8}" width="52" height="15" fill="rgba(255,255,255,0.88)" rx="3"/>')
        els.append(f'<text x="{W-30}" y="{cy+3}" fill="#000000" font-size="8" font-family="monospace" font-weight="700" text-anchor="middle" letter-spacing="0.3">PRICE</text>')

        # ── Bias badge ────────────────────────────────────────────────────
        bias = result.get("bias","neutral")
        bc   = C["ob_bull"] if bias=="buy" else C["ob_bear"] if bias=="sell" else "rgba(255,255,255,0.4)"
        els.append(f'<rect x="{W-88}" y="7" width="80" height="22" fill="{bc}" rx="4" opacity="0.92"/>')
        els.append(f'<text x="{W-48}" y="21" fill="white" font-size="10" font-family="monospace" font-weight="700" text-anchor="middle" letter-spacing="0.4">BIAS:{bias.upper()}</text>')

        # ── Trend label ───────────────────────────────────────────────────
        trend = result.get("trend","—").upper()
        els.append(f'<rect x="{W-88}" y="33" width="80" height="18" fill="{C["bg"]}" rx="3"/>')
        els.append(f'<text x="{W-48}" y="45" fill="{C["choch"]}" font-size="8" font-family="monospace" font-weight="600" text-anchor="middle" letter-spacing="0.5">{trend}</text>')

        # ── Legend ────────────────────────────────────────────────────────
        _legend(els, visible, result, H)

        body = "\n  ".join(els)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
                f'style="width:100%;height:auto;display:block;border-radius:8px">\n'
                f'  <image href="data:image/png;base64,{b64}" x="0" y="0" '
                f'width="{W}" height="{H}" preserveAspectRatio="xMidYMid meet"/>\n'
                f'  {body}\n</svg>')

    except Exception as e:
        logger.error(f"SVG error: {e}"); import traceback; traceback.print_exc()
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 80">'
                f'<rect width="500" height="80" fill="#0d1117"/>'
                f'<text x="250" y="45" fill="#ff4757" font-size="13" text-anchor="middle" '
                f'font-family="monospace">SVG overlay error: {str(e)[:60]}</text></svg>')


def _legend(els, visible, result, H):
    items = []
    if ZONE_LIQUIDITY in visible and result.get("liquidity_zones"):
        items += [(C["sell_liq"],"SSL — Sell-Side Liq."),(C["buy_liq"],"BSL — Buy-Side Liq.")]
    if ZONE_SR in visible and result.get("support_resistance"):
        items += [(C["resist"],"Resistance"),(C["support"],"Support")]
    if ZONE_OB in visible and result.get("order_blocks"):
        items += [(C["ob_bull"],"Bull OB"),(C["ob_bear"],"Bear OB")]
    if ZONE_FVG in visible and result.get("fair_value_gaps"):
        items.append((C["fvg"],"Fair Value Gap"))
    if ZONE_CHOCH in visible and result.get("choch_zones"):
        items.append((C["choch"],"CHOCH"))
    if ZONE_BOS in visible and result.get("market_structure",{}).get("last_bos","none")!="none":
        items.append((C["bos"],"BOS"))
    if not items: return

    rh = 14; pw = 8; bh = len(items)*rh+pw*2+14; bw = 150
    by = H-bh-7
    els.append(f'<rect x="5" y="{by}" width="{bw}" height="{bh}" fill="{C["bg"]}" rx="5"/>')
    els.append(f'<text x="13" y="{by+pw+6}" fill="rgba(255,255,255,0.4)" font-size="7" font-family="monospace" font-weight="700" letter-spacing="1">ZONES</text>')
    for i,(col,lbl) in enumerate(items):
        y=by+pw+14+i*rh
        els.append(f'<rect x="12" y="{y}" width="9" height="7" fill="{col}" rx="1" opacity="0.9"/>')
        els.append(f'<text x="25" y="{y+7}" fill="rgba(255,255,255,0.75)" font-size="8.5" font-family="monospace">{lbl}</text>')


def _fallback() -> dict:
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 120">'
           '<rect width="400" height="120" fill="#0d1117"/>'
           '<text x="200" y="55" fill="#ff4757" font-size="14" text-anchor="middle" font-family="monospace">Analysis failed</text>'
           '<text x="200" y="78" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">Upload a valid chart screenshot</text>'
           '</svg>')
    return {"trend":"unknown","bias":"neutral","premium_discount":"equilibrium",
            "current_pct_y":0.5,"liquidity_zones":[],"support_resistance":[],
            "market_structure":{"last_bos":"none","last_choch":"none"},
            "order_blocks":[],"fair_value_gaps":[],"choch_zones":[],
            "key_observations":["Analysis failed — upload a valid chart image"],
            "trade_idea":{"direction":"wait","entry_zone":"—","stop_loss":"—",
                          "take_profit":"—","reasoning":"Analysis could not complete"},
            "analysis_method":"failed","image_w":0,"image_h":0,
            "green_pct":0.0,"red_pct":0.0,"overlay_svg":svg,"overlay_layers":{}}
