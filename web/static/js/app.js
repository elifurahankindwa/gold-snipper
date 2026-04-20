'use strict';
const socket=io({transports:['websocket','polling']});
const $=id=>document.getElementById(id);
const f2=n=>(n==null||n==='—')?'—':parseFloat(n).toFixed(2);
const fUSD=n=>{if(n==null)return'—';const v=parseFloat(n);return(v>=0?'+ $':'- $')+Math.abs(v).toFixed(2);};
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const ago=s=>{if(!s)return'';const d=Math.floor((Date.now()-new Date(s))/1000);return d<60?d+'s ago':d<3600?Math.floor(d/60)+'m ago':Math.floor(d/3600)+'h ago';};

// Clock
setInterval(()=>{if($('sb-time'))$('sb-time').textContent='UTC '+new Date().toUTCString().slice(17,25);},1000);

// Panel navigation
function goPanel(el){
  if(!el||!el.dataset)return;
  document.querySelectorAll('.nt').forEach(n=>n.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  el.classList.add('active');
  const p=$(el.dataset.panel);
  if(p)p.classList.add('active');
  if(el.dataset.panel==='p-settings'){loadRiskRules();loadLogs();}
}

// Toast
function toast(msg,type='info'){
  const icons={success:'fa-circle-check',error:'fa-circle-xmark',info:'fa-bolt',warning:'fa-triangle-exclamation'};
  const el=document.createElement('div');
  el.className=`toast ${type}`;
  el.innerHTML=`<i class="fa-solid ${icons[type]||'fa-bolt'}"></i><span>${esc(msg)}</span>`;
  $('toasts').appendChild(el);
  setTimeout(()=>el.remove(),5000);
}
const showOv=m=>{$('ov-msg').textContent=m;$('overlay').style.display='flex';};
const hideOv=()=>{$('overlay').style.display='none';};

// Status
async function refreshStatus(){
  try{
    const d=await fetch('/api/status').then(r=>r.json());
    setPill('st-model',d.model_loaded?'ok':'off',d.model_loaded?'Loaded':'None');
    setPill('st-live', d.live_running?'ok':'off',d.live_running?'ON':'OFF');
    setPill('st-tg',   d.telegram_ok ?'ok':'off',d.telegram_ok ?'ON':'OFF');
  }catch(e){}
}
function setPill(id,cls,txt){const e=$(id);if(!e)return;e.className='status-pill '+cls;e.textContent=txt;}

// Price update
socket.on('price_update',tick=>{
  if(!tick||!tick.price)return;
  const p=tick.price,ch=tick.change||0,cp=tick.change_pct||0,up=ch>=0;
  if($('nav-price'))$('nav-price').textContent='$'+p.toFixed(2);
  const nc=$('nav-chg');if(nc){nc.textContent=(up?'+':'')+cp.toFixed(2)+'%';nc.className='lpb-chg '+(up?'up':'down');}
  if($('pb-price'))$('pb-price').textContent='$'+p.toFixed(2);
  const pc=$('pb-chg');if(pc){pc.textContent=(up?'+ ':'- ')+'$'+Math.abs(ch).toFixed(2)+' ('+(up?'+':'')+cp.toFixed(2)+'%)';pc.style.color=up?'var(--green)':'var(--red)';}
  if($('pb-high')&&tick.high)$('pb-high').textContent='$'+tick.high.toFixed(2);
  if($('pb-low') &&tick.low) $('pb-low').textContent ='$'+tick.low.toFixed(2);
  const h=new Date().getUTCHours();
  const sess=h>=7&&h<10?'London':h>=12&&h<15?'New York':h>=0&&h<6?'Asian':'Off-session';
  if($('pb-sess'))$('pb-sess').textContent=sess;
  if($('sb-msg'))$('sb-msg').innerHTML=`<i class="fa-solid fa-circle-check" style="color:var(--green)"></i> XAUUSD $${p.toFixed(2)} · ${up?'+':''}${cp.toFixed(2)}% · ${sess}`;
});

// Signal cards
let histData=[],histFilter='all';

function filterSigs(f,btn){
  histFilter=f;
  document.querySelectorAll('.ftab').forEach(b=>b.classList.remove('active'));
  if(btn)btn.classList.add('active');
  renderCards(histData);
}

function renderCards(items){
  histData=items;
  const c=$('sig-list');if(!c)return;
  const sc=$('sig-count');if(sc)sc.innerHTML=`<i class="fa-solid fa-signal"></i> <span>${items.length} signals</span>`;
  let filtered=items;
  if(histFilter==='BUY')  filtered=items.filter(s=>s.signal==='BUY');
  if(histFilter==='SELL') filtered=items.filter(s=>s.signal==='SELL');
  if(histFilter==='pass') filtered=items.filter(s=>s.risk_passed);
  if(!filtered.length){
    c.innerHTML=`<div class="empty-card"><i class="fa-solid fa-bolt-lightning"></i><h3>No ${histFilter==='all'?'':histFilter} signals</h3><p>Click <strong>Scan Now</strong> in the sidebar to analyse the current XAUUSD market</p></div>`;
    return;
  }
  c.innerHTML=filtered.slice(0,20).map(s=>{
    const dir=s.signal||'NO_TRADE',dc=dir==='BUY'?'buy':dir==='SELL'?'sell':'none';
    const price=s.live_price||s.close||0,pass=s.risk_passed;
    const reasons=(s.risk_reasons||[]).slice(0,2).join(' · ');
    return`<div class="sig-result-card" onclick="clickCard(this)" data-sig='${JSON.stringify({signal:dir,close:price,sl:s.sl,tp:s.tp,confidence:s.confidence,confluence:s.confluence,regime_label:s.regime_label,session:s.session,risk_passed:pass,timestamp:s.timestamp})}'>
<div class="src-top"><div class="src-stripe ${dc}"></div><div class="src-body">
<div class="src-row1">
  <span class="src-dir ${dc}"><i class="fa-solid ${dir==='BUY'?'fa-arrow-trend-up':dir==='SELL'?'fa-arrow-trend-down':'fa-minus'}"></i>${dir==='NO_TRADE'?'NONE':dir}</span>
  <span class="src-price">$${parseFloat(price).toFixed(2)}</span>
  <span class="src-regime">${s.regime_label||'—'}</span>
  <span class="src-time">${ago(s.timestamp)}</span>
</div>
<div class="src-row2">
  <div class="src-stat"><div class="src-lbl">Stop Loss</div><div class="src-val" style="color:var(--red)">${s.sl?'$'+parseFloat(s.sl).toFixed(2):'—'}</div></div>
  <div class="src-stat"><div class="src-lbl">Take Profit</div><div class="src-val" style="color:var(--green)">${s.tp?'$'+parseFloat(s.tp).toFixed(2):'—'}</div></div>
  <div class="src-stat"><div class="src-lbl">Confidence</div><div class="src-val">${s.confidence||'—'}%</div></div>
  <div class="src-stat"><div class="src-lbl">Confluence</div><div class="src-val">${s.confluence||'—'}/8</div></div>
  <div class="src-stat"><div class="src-lbl">Session</div><div class="src-val">${s.session||'—'}</div></div>
</div></div></div>
<div class="src-bottom">
  <span class="src-tag ${pass?'pass':'fail'}"><i class="fa-solid ${pass?'fa-shield-check':'fa-triangle-exclamation'}"></i> ${pass?'Risk PASS':'Risk FAIL'}</span>
  ${!pass&&reasons?`<span class="src-tag info">${esc(reasons)}</span>`:''}
  ${dir!=='NO_TRADE'&&pass?'<button class="src-view" onclick="event.stopPropagation();goAnalytics()"><i class="fa-solid fa-chart-candlestick"></i> View Analysis</button>':''}
</div></div>`;
  }).join('');
}

function clickCard(el){try{const s=JSON.parse(el.dataset.sig);renderSummary(s);goAnalytics();}catch(e){}}
function goAnalytics(){const n=document.querySelector('[data-panel="p-analytics"]');if(n)goPanel(n);}

// Sidebar signal widget
function updateWidget(sig){
  const dir=sig.signal||'NO_TRADE';
  const d=$('sw-dir');if(d){d.textContent=dir;d.className='sw-direction '+(dir==='BUY'?'buy':dir==='SELL'?'sell':'');}
  if($('sw-price'))$('sw-price').textContent='$'+parseFloat(sig.live_price||sig.close||0).toFixed(2);
  if($('sw-meta'))$('sw-meta').textContent=(sig.confidence||0)+'% confidence · '+(sig.confluence||0)+'/8';
  const r=$('sw-risk');
  if(r){r.textContent=sig.risk_passed?'✓ Risk PASS':'✗ Risk FAIL';r.className='sw-risk '+(sig.risk_passed?'pass':'fail');}
  if($('pb-regime'))$('pb-regime').textContent=sig.regime_label||'—';
}

// Scan
let scanning=false;
async function triggerScan(){
  if(scanning)return;
  const modelOk=$('st-model')&&$('st-model').textContent==='Loaded';
  if(!modelOk){toast('Train the model first','warning');return;}
  scanning=true;setScanBtns(true);setScanChip('scanning','Scanning...');
  try{
    const r=await fetch('/api/scan',{method:'POST'});
    const d=await r.json();
    if(d.error){toast(d.error,'error');scanning=false;setScanBtns(false);setScanChip('','');}
    else toast('Scan started — analysing XAUUSD...','info');
  }catch(e){toast('Scan request failed','error');scanning=false;setScanBtns(false);setScanChip('','');}
}
function setScanBtns(b){
  ['scan-sb','scan-an'].forEach(id=>{const e=$(id);if(!e)return;e.disabled=b;
    e.innerHTML=b?'<i class="fa-solid fa-spinner fa-spin"></i> Scanning...':'<i class="fa-solid fa-bolt"></i> Scan Now';});
}
function setScanChip(cls,txt){const e=$('scan-chip');if(!e)return;e.className='scan-status-chip '+cls;e.textContent=txt;}

// Analytics
function renderSummary(sig){
  const dir=sig.signal||'NO_TRADE',price=sig.live_price||sig.close||0;
  const sv=(id,v,cls)=>{const e=$(id);if(!e)return;e.textContent=v;if(cls)e.className='ss-val '+cls;};
  sv('a-sig',dir,dir==='BUY'?'success':dir==='SELL'?'danger':'');
  sv('a-price','$'+f2(price),'gold');sv('a-sl','$'+f2(sig.sl),'danger');sv('a-tp','$'+f2(sig.tp),'success');
  sv('a-rr','1:2','gold');sv('a-conf',(sig.confidence||0)+'%');sv('a-confl',(sig.confluence||0)+'/8');
  sv('a-regime',sig.regime_label||'—');
  updateWidget(sig);
}

function renderAnalytics(sig){
  const bars=sig.analytics_bars||[];if(!bars.length)return;
  renderSummary(sig);
  drawPrice(bars,sig);drawRSI(bars);drawMACD(bars);drawADX(bars);
  const last=bars[bars.length-1]||{};
  const rsi=parseFloat(last.rsi||50),macd=parseFloat(last.macd_hist||0),adx=parseFloat(last.adx||0);
  if($('a-rsi'))$('a-rsi').textContent=rsi.toFixed(1);
  const rt=$('a-rsi-tag');if(rt){rt.textContent=rsi>70?'Overbought':rsi<30?'Oversold':'Neutral';rt.className='pill '+(rsi>70?'err':rsi<30?'ok':'off');}
  if($('a-macd'))$('a-macd').textContent=(macd>=0?'+':'')+macd.toFixed(3);
  if($('a-adx'))$('a-adx').textContent=adx.toFixed(1);
  const at=$('a-adx-tag');if(at){at.textContent=adx>25?'Strong':adx>15?'Moderate':'Weak';at.className='pill '+(adx>25?'ok':'off');}
  renderSMC(last,sig);renderFeatDrivers(sig.shap||{},sig.top_features||[]);renderTradePlan(sig);
}

// Canvas drawing
const C={bg:'#fafafa',grid:'#e2e6ea',text:'#6B7384',textH:'#1A1D23',
  green:'#00B85C',red:'#FF3D57',blue:'#3366FF',gold:'#E67E00',purple:'#6C3EFF',amber:'#FF8C00'};

function setupC(id,H){
  const cv=$(id);if(!cv)return null;
  const dpr=window.devicePixelRatio||1,W=cv.parentElement.clientWidth||600;
  cv.width=W*dpr;cv.height=H*dpr;cv.style.width=W+'px';cv.style.height=H+'px';
  const ctx=cv.getContext('2d');ctx.scale(dpr,dpr);
  return{ctx,W,H};
}

function drawPrice(bars,sig){
  const c=setupC('c-price',290);if(!c)return;
  const{ctx,W,H}=c;
  const ph=$('price-ph');if(ph){ph.style.display='none';}
  const pad={l:56,r:14,t:16,b:28};const cw=W-pad.l-pad.r,ch=H-pad.t-pad.b,n=bars.length;
  const bw=Math.max(2,cw/n-1);
  const hv=bars.map(b=>parseFloat(b.high||b.close||0));
  const lv=bars.map(b=>parseFloat(b.low ||b.close||0));
  let minP=Math.min(...lv)*.9996,maxP=Math.max(...hv)*1.0004;
  if(maxP===minP){maxP+=1;minP-=1;}
  const sy=v=>pad.t+ch-((v-minP)/(maxP-minP))*ch;
  const sx=i=>pad.l+(i+.5)*(cw/n);
  ctx.fillStyle='#fff';ctx.fillRect(0,0,W,H);
  // Grid lines
  ctx.strokeStyle=C.grid;ctx.lineWidth=.5;
  for(let i=0;i<=4;i++){
    const y=pad.t+ch/4*i;ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(W-pad.r,y);ctx.stroke();
    const pr=maxP-(maxP-minP)/4*i;ctx.fillStyle=C.text;ctx.font='9px JetBrains Mono,monospace';ctx.textAlign='right';
    ctx.fillText('$'+pr.toFixed(0),pad.l-4,y+3);
  }
  // Kill zones
  bars.forEach((b,i)=>{if(b.in_kz){ctx.fillStyle='rgba(230,126,0,.07)';ctx.fillRect(sx(i)-bw/2-1,pad.t,bw+2,ch);}});
  // FVG
  bars.forEach((b,i)=>{
    if(b.bull_fvg&&i>=2){const lo=parseFloat(bars[i].low||0),hi=parseFloat(bars[i-2].high||0);if(lo>hi){ctx.fillStyle='rgba(108,62,255,.1)';ctx.fillRect(sx(i-2),sy(lo),sx(i)-sx(i-2)+bw,sy(hi)-sy(lo));}}
    if(b.bear_fvg&&i>=2){const lo=parseFloat(bars[i].high||0),hi=parseFloat(bars[i-2].low||0);if(hi>lo){ctx.fillStyle='rgba(255,61,87,.08)';ctx.fillRect(sx(i-2),sy(hi),sx(i)-sx(i-2)+bw,sy(lo)-sy(hi));}}
  });
  // OB zones
  bars.forEach((b,i)=>{
    const x=sx(i),bhi=parseFloat(b.high||0),blo=parseFloat(b.low||0);
    if(b.bull_ob){ctx.fillStyle='rgba(51,102,255,.15)';ctx.fillRect(x-bw/2,sy(bhi),bw,sy(blo)-sy(bhi));ctx.strokeStyle=C.blue;ctx.lineWidth=.8;ctx.strokeRect(x-bw/2,sy(bhi),bw,sy(blo)-sy(bhi));}
    if(b.bear_ob){ctx.fillStyle='rgba(255,61,87,.12)';ctx.fillRect(x-bw/2,sy(bhi),bw,sy(blo)-sy(bhi));ctx.strokeStyle=C.red;ctx.lineWidth=.8;ctx.strokeRect(x-bw/2,sy(bhi),bw,sy(blo)-sy(bhi));}
  });
  // EMAs
  const dEMA=(k,col,lw)=>{ctx.strokeStyle=col;ctx.lineWidth=lw;ctx.setLineDash([]);ctx.beginPath();let s=false;bars.forEach((b,i)=>{const v=parseFloat(b[k]||0);if(!v)return;const x=sx(i),y=sy(v);if(!s){ctx.moveTo(x,y);s=true;}else ctx.lineTo(x,y);});ctx.stroke();};
  dEMA('ema_20',C.blue,1.3);dEMA('ema_50',C.gold,1.3);dEMA('ema_200',C.red,1.6);
  // PDH/PDL
  const last=bars[bars.length-1]||{};const pdh=parseFloat(last.pdh||0),pdl=parseFloat(last.pdl||0);
  ctx.setLineDash([4,3]);ctx.lineWidth=.8;
  if(pdh>minP&&pdh<maxP){ctx.strokeStyle='rgba(230,126,0,.5)';ctx.beginPath();ctx.moveTo(pad.l,sy(pdh));ctx.lineTo(W-pad.r,sy(pdh));ctx.stroke();ctx.fillStyle=C.gold;ctx.setLineDash([]);ctx.font='9px JetBrains Mono';ctx.textAlign='left';ctx.fillText('PDH',W-pad.r-26,sy(pdh)-3);}
  if(pdl>minP&&pdl<maxP){ctx.setLineDash([4,3]);ctx.strokeStyle='rgba(230,126,0,.5)';ctx.beginPath();ctx.moveTo(pad.l,sy(pdl));ctx.lineTo(W-pad.r,sy(pdl));ctx.stroke();ctx.fillStyle=C.gold;ctx.setLineDash([]);ctx.fillText('PDL',W-pad.r-26,sy(pdl)+10);}
  ctx.setLineDash([]);
  // Swing dots
  bars.forEach((b,i)=>{
    if(b.swing_high){ctx.fillStyle=C.red;ctx.beginPath();ctx.arc(sx(i),sy(parseFloat(b.high||0))-4,3,0,Math.PI*2);ctx.fill();}
    if(b.swing_low) {ctx.fillStyle=C.green;ctx.beginPath();ctx.arc(sx(i),sy(parseFloat(b.low||0))+4,3,0,Math.PI*2);ctx.fill();}
  });
  // Bollinger bands
  ctx.strokeStyle='rgba(51,102,255,.2)';ctx.lineWidth=.8;
  ['bb_upper','bb_lower'].forEach(k=>{ctx.beginPath();let s=false;bars.forEach((b,i)=>{const v=parseFloat(b[k]||0);if(!v)return;const x=sx(i),y=sy(v);if(!s){ctx.moveTo(x,y);s=true;}else ctx.lineTo(x,y);});ctx.stroke();});
  // Candles
  bars.forEach((b,i)=>{
    const x=sx(i),o=parseFloat(b.open||b.close||0),cl=parseFloat(b.close||0);
    const bhi=parseFloat(b.high||cl),blo=parseFloat(b.low||cl);
    const bull=cl>=o,col=bull?C.green:C.red;
    ctx.strokeStyle=col;ctx.lineWidth=.9;ctx.beginPath();ctx.moveTo(x,sy(bhi));ctx.lineTo(x,sy(blo));ctx.stroke();
    ctx.fillStyle=col;ctx.fillRect(x-bw/2,sy(Math.max(o,cl)),bw,Math.max(1,Math.abs(sy(o)-sy(cl))));
  });
  // BOS labels
  bars.forEach((b,i)=>{if(b.bos!==0){ctx.fillStyle=b.bos>0?C.green:C.red;ctx.font='bold 8px JetBrains Mono';ctx.textAlign='center';ctx.fillText(b.bos>0?'BOS▲':'BOS▼',sx(i),pad.t+10);}});
  // Signal arrow
  const li=bars.length-1,latr=parseFloat(last.atr||2),lc=parseFloat(last.close||0);
  if(sig.signal==='BUY'){const ay=sy(lc-latr*2.2);ctx.fillStyle=C.green;ctx.beginPath();ctx.moveTo(sx(li),ay-12);ctx.lineTo(sx(li)-8,ay);ctx.lineTo(sx(li)+8,ay);ctx.closePath();ctx.fill();ctx.fillStyle=C.green;ctx.font='bold 11px JetBrains Mono';ctx.textAlign='center';ctx.fillText('BUY',sx(li),ay-16);}
  else if(sig.signal==='SELL'){const ay=sy(lc+latr*2.2);ctx.fillStyle=C.red;ctx.beginPath();ctx.moveTo(sx(li),ay+12);ctx.lineTo(sx(li)-8,ay);ctx.lineTo(sx(li)+8,ay);ctx.closePath();ctx.fill();ctx.fillStyle=C.red;ctx.font='bold 11px JetBrains Mono';ctx.textAlign='center';ctx.fillText('SELL',sx(li),ay+24);}
  // SL/TP lines
  if(sig.sl&&sig.signal!=='NO_TRADE'){
    const slP=parseFloat(sig.sl),tpP=parseFloat(sig.tp||0);
    ctx.setLineDash([5,3]);ctx.lineWidth=1.3;
    if(slP>minP&&slP<maxP){ctx.strokeStyle=C.red;ctx.beginPath();ctx.moveTo(pad.l,sy(slP));ctx.lineTo(W-pad.r,sy(slP));ctx.stroke();ctx.fillStyle=C.red;ctx.setLineDash([]);ctx.font='9px JetBrains Mono';ctx.textAlign='right';ctx.fillText('SL $'+slP.toFixed(1),W-pad.r-2,sy(slP)-3);}
    if(tpP>minP&&tpP<maxP){ctx.setLineDash([5,3]);ctx.strokeStyle=C.green;ctx.beginPath();ctx.moveTo(pad.l,sy(tpP));ctx.lineTo(W-pad.r,sy(tpP));ctx.stroke();ctx.fillStyle=C.green;ctx.setLineDash([]);ctx.textAlign='right';ctx.fillText('TP $'+tpP.toFixed(1),W-pad.r-2,sy(tpP)-3);}
    ctx.setLineDash([]);
  }
  // X labels + legend
  ctx.fillStyle=C.text;ctx.font='9px JetBrains Mono';ctx.textAlign='center';
  const step=Math.max(1,Math.floor(n/8));
  bars.forEach((b,i)=>{if(i%step===0)ctx.fillText((b.datetime||'').slice(11,16),sx(i),H-8);});
  [['EMA20',C.blue],['EMA50',C.gold],['EMA200',C.red]].forEach(([l,col],i)=>{ctx.fillStyle=col;ctx.fillRect(pad.l+i*60,pad.t+4,14,2);ctx.fillStyle=C.text;ctx.font='9px JetBrains Mono';ctx.textAlign='left';ctx.fillText(l,pad.l+i*60+18,pad.t+8);});
}

function drawRSI(bars){
  const c=setupC('c-rsi',140);if(!c)return;
  const{ctx,W,H}=c;const pad={l:26,r:8,t:8,b:18};
  const cw=W-pad.l-pad.r,ch=H-pad.t-pad.b,n=bars.length;
  const sx=i=>pad.l+(i+.5)*(cw/n),sy=v=>pad.t+ch-(v/100)*ch;
  ctx.fillStyle='#fff';ctx.fillRect(0,0,W,H);
  ctx.fillStyle='rgba(255,61,87,.05)';ctx.fillRect(pad.l,sy(100),cw,sy(70)-sy(100));
  ctx.fillStyle='rgba(0,184,92,.05)';ctx.fillRect(pad.l,sy(30),cw,sy(0)-sy(30));
  [70,50,30].forEach(v=>{ctx.strokeStyle=v===50?C.grid:'rgba(160,170,187,.4)';ctx.lineWidth=.5;ctx.setLineDash(v===50?[]:[2,2]);ctx.beginPath();ctx.moveTo(pad.l,sy(v));ctx.lineTo(W-pad.r,sy(v));ctx.stroke();ctx.fillStyle=C.text;ctx.font='8px JetBrains Mono';ctx.textAlign='right';ctx.setLineDash([]);ctx.fillText(v,pad.l-2,sy(v)+3);});
  ctx.strokeStyle=C.blue;ctx.lineWidth=1.5;ctx.beginPath();let s=false;
  bars.forEach((b,i)=>{const v=parseFloat(b.rsi||50);const x=sx(i),y=sy(v);if(!s){ctx.moveTo(x,y);s=true;}else ctx.lineTo(x,y);});ctx.stroke();
  ctx.beginPath();s=false;bars.forEach((b,i)=>{const v=parseFloat(b.rsi||50);const x=sx(i),y=sy(v);if(!s){ctx.moveTo(x,y);s=true;}else ctx.lineTo(x,y);});
  ctx.lineTo(sx(n-1),sy(0));ctx.lineTo(pad.l,sy(0));
  const g=ctx.createLinearGradient(0,pad.t,0,pad.t+ch);g.addColorStop(0,'rgba(51,102,255,.12)');g.addColorStop(1,'rgba(51,102,255,0)');ctx.fillStyle=g;ctx.fill();
}

function drawMACD(bars){
  const c=setupC('c-macd',140);if(!c)return;
  const{ctx,W,H}=c;const pad={l:34,r:8,t:8,b:18};
  const cw=W-pad.l-pad.r,ch=H-pad.t-pad.b,n=bars.length;
  const vals=bars.map(b=>parseFloat(b.macd_hist||0));
  const maxV=Math.max(Math.abs(Math.min(...vals)),Math.abs(Math.max(...vals)),.1);
  const sx=i=>pad.l+(i+.5)*(cw/n),sy=v=>pad.t+ch/2-(v/maxV)*(ch/2);
  const bw=Math.max(1,cw/n-1);
  ctx.fillStyle='#fff';ctx.fillRect(0,0,W,H);
  ctx.strokeStyle=C.grid;ctx.lineWidth=.5;ctx.beginPath();ctx.moveTo(pad.l,sy(0));ctx.lineTo(W-pad.r,sy(0));ctx.stroke();
  vals.forEach((v,i)=>{ctx.fillStyle=v>=0?C.green:C.red;const y=sy(v),bh=Math.abs(sy(0)-sy(v));ctx.fillRect(sx(i)-bw/2,Math.min(y,sy(0)),bw,Math.max(1,bh));});
  const dL=(k,col)=>{ctx.strokeStyle=col;ctx.lineWidth=1;ctx.beginPath();let s=false;bars.forEach((b,i)=>{const v=parseFloat(b[k]||0);if(Math.abs(v)>maxV*3)return;const x=sx(i),y=sy(v);if(!s){ctx.moveTo(x,y);s=true;}else ctx.lineTo(x,y);});ctx.stroke();};
  dL('macd',C.blue);dL('macd_signal',C.amber);
}

function drawADX(bars){
  const c=setupC('c-adx',140);if(!c)return;
  const{ctx,W,H}=c;const pad={l:26,r:8,t:8,b:18};
  const cw=W-pad.l-pad.r,ch=H-pad.t-pad.b,n=bars.length;
  const sx=i=>pad.l+(i+.5)*(cw/n),sy=v=>pad.t+ch-(Math.min(v,80)/80)*ch;
  ctx.fillStyle='#fff';ctx.fillRect(0,0,W,H);
  ctx.setLineDash([3,2]);ctx.strokeStyle='rgba(230,126,0,.4)';ctx.lineWidth=.7;ctx.beginPath();ctx.moveTo(pad.l,sy(25));ctx.lineTo(W-pad.r,sy(25));ctx.stroke();
  ctx.fillStyle=C.gold;ctx.font='8px JetBrains Mono';ctx.textAlign='right';ctx.setLineDash([]);ctx.fillText('25',pad.l-2,sy(25)+3);
  ctx.strokeStyle=C.purple;ctx.lineWidth=1.5;ctx.beginPath();let s=false;
  bars.forEach((b,i)=>{const v=parseFloat(b.adx||0);const x=sx(i),y=sy(v);if(!s){ctx.moveTo(x,y);s=true;}else ctx.lineTo(x,y);});ctx.stroke();
  ctx.beginPath();s=false;bars.forEach((b,i)=>{const v=parseFloat(b.adx||0);const x=sx(i),y=sy(v);if(!s){ctx.moveTo(x,y);s=true;}else ctx.lineTo(x,y);});
  ctx.lineTo(sx(n-1),sy(0));ctx.lineTo(pad.l,sy(0));
  const g=ctx.createLinearGradient(0,pad.t,0,pad.t+ch);g.addColorStop(0,'rgba(108,62,255,.14)');g.addColorStop(1,'rgba(108,62,255,0)');ctx.fillStyle=g;ctx.fill();
}

// SMC analysis
function renderSMC(bar,sig){
  const el=$('smc-list');if(!el)return;
  const dir=sig.signal||'NO_TRADE';
  const checks=[
    {l:'EMA trend aligned',ok:bar.ema_trend===1&&dir==='BUY'||bar.ema_trend===-1&&dir==='SELL',v:bar.ema_trend===1?'Bullish stack':bar.ema_trend===-1?'Bearish stack':'Mixed'},
    {l:'PDH/PDL swept',ok:bar.sweep_pdl||bar.sweep_pdh,v:bar.sweep_pdh?'PDH swept':bar.sweep_pdl?'PDL swept':'Not swept'},
    {l:'Kill zone active',ok:bar.in_kz,v:bar.in_kz?'London or NY':'Outside'},
    {l:'Break of Structure',ok:bar.bos!==0,v:bar.bos>0?'Bullish BOS':bar.bos<0?'Bearish BOS':'No BOS'},
    {l:'Order Block entry',ok:bar.in_bull_ob||bar.in_bear_ob,v:bar.in_bull_ob?'Bullish OB':bar.in_bear_ob?'Bearish OB':'Not in OB'},
    {l:'Fair Value Gap',ok:bar.bull_fvg||bar.bear_fvg,v:bar.bull_fvg?'Bull FVG':bar.bear_fvg?'Bear FVG':'No FVG'},
    {l:'ML confidence ≥ 70%',ok:sig.confidence>=70,v:(sig.confidence||0)+'%'},
    {l:'Confluence ≥ 4/8',ok:sig.confluence>=4,v:(sig.confluence||0)+'/8'},
  ];
  el.innerHTML=checks.map(ch=>`<div class="smc-row"><div class="smc-dot ${ch.ok?'yes':'no'}"></div><span class="smc-lbl">${ch.l}</span><span class="smc-val">${esc(ch.v)}</span></div>`).join('');
}

// Feature drivers
function renderFeatDrivers(shap,topFeats){
  const el=$('fd-list');if(!el)return;
  const combined={};
  Object.entries(shap).forEach(([k,v])=>{combined[k]={shap:v};});
  (topFeats||[]).forEach(f=>{if(!combined[f.feature])combined[f.feature]={};combined[f.feature].importance=f.importance;});
  const items=Object.entries(combined).sort((a,b)=>Math.abs(b[1].shap||0)-Math.abs(a[1].shap||0)).slice(0,10);
  if(!items.length){el.innerHTML='<div class="placeholder-msg"><i class="fa-solid fa-brain"></i> SHAP values load after scan</div>';return;}
  const maxV=Math.max(...items.map(([,v])=>Math.abs(v.shap||0)),.001);
  el.innerHTML=items.map(([name,vals],i)=>{
    const v=vals.shap||0,pct=(Math.abs(v)/maxV*100).toFixed(0),cls=v>=0?'pos':'neg';
    return`<div class="fd-item"><div class="fd-rank">${i+1}</div><span class="fd-name">${esc(name)}</span><div class="fd-bar-wrap"><div class="fd-bar ${cls}" style="width:${pct}%"></div></div><span class="fd-val">${v>=0?'+':''}${v.toFixed(4)}</span></div>`;
  }).join('');
}

// Trade plan
function renderTradePlan(sig){
  const card=$('trade-plan');if(!card)return;card.style.display='block';
  const dir=sig.signal||'NO_TRADE',pass=sig.risk_passed,confl=sig.confluence||0;
  const acc=10000,risk=acc*.01,rwd=risk*2;
  const sv=(id,v,cls)=>{const e=$(id);if(!e)return;e.textContent=v;if(cls)e.className='tpc-v '+cls;};
  sv('tp-dir',dir,dir==='BUY'?'success':dir==='SELL'?'danger':'');
  sv('tp-entry','$'+f2(sig.live_price||sig.close),'gold');
  sv('tp-sl','$'+f2(sig.sl),'danger');sv('tp-tp','$'+f2(sig.tp),'success');
  sv('tp-risk','$'+risk.toFixed(0)+' (1%)');sv('tp-reward','$'+rwd.toFixed(0),'success');
  sv('tp-sess',sig.session||'—');
  const v=$('tp-verdict');if(!v)return;
  if(dir==='NO_TRADE'){v.textContent='No trade setup detected.';v.className='tpc-verdict wait';card.className='trade-plan-card';$('tp-title').textContent='No Trade';}
  else if(pass&&confl>=4){v.textContent=`✓ TAKE TRADE — ${confl}/8 conditions met. Risk $${risk.toFixed(0)}, target $${rwd.toFixed(0)}.`;v.className='tpc-verdict go';card.className='trade-plan-card go';$('tp-title').textContent=dir+' Trade Setup';}
  else if(!pass){v.textContent='✗ SKIP — '+(sig.risk_reasons||[]).slice(0,2).join(' · ');v.className='tpc-verdict skip';card.className='trade-plan-card skip';$('tp-title').textContent='Trade Blocked';}
  else{v.textContent=`⏳ WAIT — Only ${confl}/8 conditions. Need at least 4.`;v.className='tpc-verdict wait';card.className='trade-plan-card';$('tp-title').textContent='Partial Setup';}
}

// Backtest
async function runBacktest(){
  showOv('Running 2-year backtest...');
  const r=await fetch('/api/backtest/run',{method:'POST'});const d=await r.json();
  if(d.error){toast(d.error,'error');hideOv();}
  else toast('Backtest started — this takes 2-3 minutes','info');
}

function renderBacktest(s){
  if(!s||s.error)return;
  const sv=(id,v,cls)=>{const e=$(id);if(!e)return;e.textContent=v;if(cls)e.className='kpi-v '+cls;};
  sv('b-trades',s.total_trades||'—');sv('b-wr',s.win_rate_pct!=null?s.win_rate_pct+'%':'—','green');
  sv('b-pf',s.profit_factor||'—');sv('b-net',s.net_profit!=null?fUSD(s.net_profit):'—',s.net_profit>=0?'green':'danger');
  sv('b-ret',s.return_pct!=null?s.return_pct+'%':'—',s.return_pct>=0?'green':'danger');
  sv('b-dd',s.max_drawdown_pct!=null?s.max_drawdown_pct+'%':'—','danger');
  sv('b-rr',s.avg_rr?'1:'+s.avg_rr:'—','gold');sv('b-ev',s.expected_value!=null?s.expected_value+'R':'—');
  const rBD=(id,key)=>{
    const el=$(id);if(!el)return;const obj=s[key]||{};
    if(!Object.keys(obj).length){el.innerHTML='<div class="placeholder-msg">No data.</div>';return;}
    el.innerHTML=Object.entries(obj).map(([name,st])=>`<div class="bd-label">${esc(name)}</div><div class="bd-row"><span>Trades</span><span>${st.trades}</span></div><div class="bd-row"><span>Win Rate</span><span style="color:${st.win_rate>=50?'var(--green)':'var(--red)'}">${st.win_rate}%</span></div><div class="bd-row"><span>Net P&L</span><span style="color:${st.net_pnl>=0?'var(--green)':'var(--red)'}">${fUSD(st.net_pnl)}</span></div>`).join('');
  };
  rBD('sess-bd','session_stats');rBD('regime-bd','regime_stats');
}

function renderTrades(trades){
  if(!trades||!trades.length)return;
  $('trade-body').innerHTML=trades.slice(0,50).map(t=>`<tr>
    <td>${(t.entry_time||'').slice(0,16)}</td>
    <td style="color:${t.direction==='BUY'?'var(--green)':'var(--red)'};font-weight:800">${t.direction}</td>
    <td>$${f2(t.entry_price)}</td><td style="color:var(--red)">$${f2(t.sl)}</td>
    <td style="color:var(--green)">$${f2(t.tp)}</td>
    <td class="${(t.outcome||'').toLowerCase()}">${t.outcome}</td>
    <td class="${t.pnl_usd>=0?'pos':'neg'}">${fUSD(t.pnl_usd)}</td>
    <td>${t.confidence||'—'}</td><td>${t.session||'—'}</td>
  </tr>`).join('');
}

// Load backtest charts with cache-busting
function loadCharts(){
  const ts=Date.now();
  const chartMap=[
    {imgId:'img-equity',  phId:'ph-equity',  name:'equity_curve'},
    {imgId:'img-signals', phId:'ph-signals',  name:'signals'},
    {imgId:'img-monthly', phId:'ph-monthly',  name:'monthly_heatmap'},
    {imgId:'img-regime',  phId:'ph-regime',   name:'regime_breakdown'},
  ];
  chartMap.forEach(({imgId,phId,name})=>{
    const img=$(imgId),ph=$(phId);if(!img)return;
    img.onload =()=>{img.style.display='block';if(ph)ph.style.display='none';};
    img.onerror=()=>{img.style.display='none';if(ph)ph.style.display='flex';};
    img.src=`/api/chart/${name}?t=${ts}`;
  });
}

// Train
async function trainModel(){
  const btn=$('train-btn');if(btn){btn.disabled=true;btn.innerHTML='<i class="fa-solid fa-spinner fa-spin"></i> Training...';}
  showOv('Fetching 2 years XAUUSD + macro data...');
  const tc=$('train-card');if(tc)tc.innerHTML='<div class="ts-prog">Connecting to Yahoo Finance...</div>';
  try{await fetch('/api/train',{method:'POST'});toast('Training started','info');}
  catch(e){toast('Failed to start training','error');if(btn){btn.disabled=false;btn.innerHTML='<i class="fa-solid fa-microchip"></i> Train Model';}hideOv();}
}

// Live loop
async function startLive(){
  showOv('Starting auto live loop...');
  const r=await fetch('/api/start_live',{method:'POST'});const d=await r.json();
  d.error?toast(d.error,'error'):toast('Auto loop started — scans every 15 min','success');
  refreshStatus();hideOv();
}

// Chart upload
async function uploadChart(input){
  const file=input.files[0];if(!file)return;
  showOv('Analysing chart image...');
  const fd=new FormData();fd.append('image',file);
  try{const r=await fetch('/api/analyse_chart',{method:'POST',body:fd});const d=await r.json();if(d.error)toast(d.error,'error');else toast('Chart analysis started','info');}
  catch(e){toast('Upload failed','error');hideOv();}
  input.value='';
}

function renderChartAnalysis(a){
  const panel=$('car');if(!panel)return;panel.style.display='block';
  const m=$('car-method');if(m)m.textContent=a.analysis_method||'—';
  const img=$('car-img');if(img&&a.image_b64){img.src='data:image/jpeg;base64,'+a.image_b64;img.style.display='block';}
  const info=$('car-info');if(!info)return;
  const lz=a.liquidity_zones||[],sr=a.support_resistance||[],obs=a.key_observations||[],idea=a.trade_idea||{};
  const bias=a.bias||'neutral',trend=a.trend||'—';
  let html=`<div style="display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px">
    <span class="pill ${bias==='buy'?'ok':bias==='sell'?'err':'off'}"><i class="fa-solid fa-chart-line"></i> ${bias.toUpperCase()}</span>
    <span class="pill off">${trend}</span>
    <span class="pill off">${a.premium_discount||'—'}</span>
    <span class="pill blue">BOS: ${(a.market_structure||{}).last_bos||'none'}</span>
  </div>`;
  if(lz.length){html+='<div style="font-size:11px;font-weight:700;color:var(--t4);margin-bottom:5px;text-transform:uppercase;letter-spacing:.07em"><i class="fa-solid fa-water"></i> Liquidity Zones</div>';lz.forEach(z=>{html+=`<div class="ca-zone"><div class="caz-dot ${z.type==='buy_side'?'buy':'sell'}"></div><span>${esc(z.description||z.type)}</span><span class="pill off" style="margin-left:auto">${z.strength}</span></div>`;});}
  if(sr.length){html+='<div style="font-size:11px;font-weight:700;color:var(--t4);margin:8px 0 5px;text-transform:uppercase;letter-spacing:.07em"><i class="fa-solid fa-layer-group"></i> S/R Levels</div>';sr.forEach(z=>{html+=`<div class="ca-zone"><div class="caz-dot sr"></div><span>${z.type} ${z.level_pct!=null?'('+Math.round(z.level_pct*100)+'% of chart)':''} — ${z.description||''}</span><span class="pill off" style="margin-left:auto">${z.strength}</span></div>`;});}
  if(obs.length){html+='<div style="font-size:11px;font-weight:700;color:var(--t4);margin:8px 0 5px;text-transform:uppercase;letter-spacing:.07em"><i class="fa-solid fa-circle-info"></i> Observations</div>';obs.forEach(o=>{html+=`<div style="font-size:12.5px;color:var(--t2);padding:4px 0;border-bottom:1px solid var(--bdr);font-weight:500">• ${esc(o)}</div>`;});}
  if(idea.direction)html+=`<div style="margin-top:10px;padding:12px;background:var(--bl);border-radius:var(--r);border:1.5px solid var(--blm)"><div style="font-size:12px;font-weight:800;color:var(--blue);margin-bottom:4px"><i class="fa-solid fa-crosshairs"></i> Trade Idea: ${(idea.direction||'').toUpperCase()}</div><div style="font-size:13px;color:var(--t2);line-height:1.6;font-weight:500">${esc(idea.reasoning||'—')}</div></div>`;
  info.innerHTML=html;
  goAnalytics();
}

// Telegram
async function connectTelegram(){
  const token=($('tg-tok')||{}).value||'',chat_id=($('tg-cid')||{}).value||'';
  if(!token||!chat_id){toast('Enter both token and chat_id','warning');return;}
  showOv('Connecting to Telegram...');
  const r=await fetch('/api/telegram/connect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,chat_id})});
  const d=await r.json();hideOv();
  const st=$('tg-st');if(st){st.textContent=d.success?'✓ '+d.msg:'✗ '+d.msg;st.className='tg-status '+(d.success?'ok':'err');}
  toast(d.success?'Telegram connected! Test message sent.':'Failed: '+d.msg,d.success?'success':'error');
  if(d.success)refreshStatus();
}
async function testTelegram(){
  const r=await fetch('/api/telegram/test',{method:'POST'});const d=await r.json();
  toast(d.success?'Test message sent to Telegram!':'Failed: '+d.msg,d.success?'success':'error');
}

// Risk rules
async function loadRiskRules(){
  try{
    const d=await fetch('/api/risk_rules').then(r=>r.json());
    const el=$('rl-list');if(!el)return;
    const icons={'Max risk per trade':'fa-shield-halved','Max trades per day':'fa-list-ol','Stop after consecutive losses':'fa-ban','Min ML confidence':'fa-brain','Min confluence':'fa-layer-group','Min R:R':'fa-scale-balanced','Sessions':'fa-clock','Volatility filter':'fa-chart-area','Crisis regime':'fa-triangle-exclamation'};
    el.innerHTML=(d.rules||[]).map(r=>{
      const ic=icons[r.rule]||'fa-circle-check';
      return`<div class="rl-row"><span class="rl-name"><i class="fa-solid ${ic}"></i> ${esc(r.rule)}</span><span class="rl-val">${esc(r.value)}</span></div>`;
    }).join('');
  }catch(e){}
}

// Logs
async function loadLogs(){
  try{
    const d=await fetch('/api/logs?lines=80').then(r=>r.json());
    const el=$('log-box');if(!el)return;
    el.innerHTML=(d.lines||[]).map(l=>{
      const cls=l.includes('ERROR')?'log-err':l.includes('WARNING')?'log-warn':'';
      return`<div class="${cls}">${esc(l)}</div>`;
    }).join('');
    el.scrollTop=el.scrollHeight;
  }catch(e){}
}
setInterval(loadLogs,15000);

// WebSocket
socket.on('connect',()=>refreshStatus());

socket.on('signal_update',sig=>{
  scanning=false;setScanBtns(false);
  setScanChip('done','Scanned '+new Date().toUTCString().slice(17,22)+' UTC');
  histData.unshift(sig);renderCards(histData);
  if(sig.analytics_bars&&sig.analytics_bars.length)renderAnalytics(sig);
  if(sig.signal!=='NO_TRADE'&&sig.risk_passed){
    const pd=$('bell-dot');if(pd)pd.style.display='block';
    toast(`${sig.signal} @ $${parseFloat(sig.live_price||sig.close||0).toFixed(2)} — Risk PASS`,'success');
  }
});

socket.on('sys',d=>{
  hideOv();
  const btn=$('train-btn');
  if(d.s==='training'){showOv(d.m||'Training...');const tc=$('train-card');if(tc)tc.innerHTML=`<div class="ts-prog"><i class="fa-solid fa-spinner fa-spin"></i> ${esc(d.m||'')}</div>`;}
  else if(d.s==='ready'&&d.metrics){
    if(btn){btn.disabled=false;btn.innerHTML='<i class="fa-solid fa-microchip"></i> Train Model';}
    const m=d.metrics,oos=m.oos||{};
    const tc=$('train-card');if(tc)tc.innerHTML=`<div class="ts-prog"><i class="fa-solid fa-circle-check" style="color:var(--green)"></i> Training complete
<div class="ts-metrics">
<div class="tsm"><div class="tsm-l">Avg F1 (CV)</div><div class="tsm-v">${m.avg_f1||'—'}</div></div>
<div class="tsm"><div class="tsm-l">OOS F1</div><div class="tsm-v" style="color:${(oos.oos_f1||0)>=0.35?'var(--green)':'var(--red)'}">${oos.oos_f1||'—'}</div></div>
<div class="tsm"><div class="tsm-l">Features</div><div class="tsm-v">${m.feature_count||'—'}</div></div>
</div></div>`;
    toast('Model trained successfully','success');refreshStatus();
  }
  else if(d.s==='scanning'){if($('sb-msg'))$('sb-msg').innerHTML='<i class="fa-solid fa-spinner fa-spin"></i> Scanning...';}
  else if(d.s==='backtesting'){showOv(d.m||'Running backtest...');}
  else if(d.s==='analysing'){showOv(d.m||'Analysing chart...');}
  else if(d.s==='ready'){
    if(btn){btn.disabled=false;btn.innerHTML='<i class="fa-solid fa-microchip"></i> Train Model';}
    refreshStatus();
  }
  else if(d.s==='error'){
    if(btn){btn.disabled=false;btn.innerHTML='<i class="fa-solid fa-microchip"></i> Train Model';}
    scanning=false;setScanBtns(false);setScanChip('','');
    toast('Error: '+(d.m||'Unknown'),'error');
  }
});

socket.on('backtest_complete',summary=>{
  hideOv();renderBacktest(summary);
  setTimeout(loadCharts,500); // slight delay to ensure files are written
  fetch('/api/backtest/result').then(r=>r.json()).then(d=>{
    if(d.trades)renderTrades(d.trades);
    const el=$('bt-run-at');if(el&&d.run_at)el.textContent='Run at '+d.run_at.slice(0,16).replace('T',' ')+' UTC';
  });
  toast('Backtest complete — charts generated','success');
  const bn=document.querySelector('[data-panel="p-backtest"]');if(bn)goPanel(bn);
});

socket.on('chart_analysis_done',a=>{hideOv();renderChartAnalysis(a);toast('Chart analysis complete','success');});

// Init
(async()=>{
  await refreshStatus();
  try{const d=await fetch('/api/price').then(r=>r.json());if(d&&d.price){if($('nav-price'))$('nav-price').textContent='$'+d.price.toFixed(2);if($('pb-price'))$('pb-price').textContent='$'+d.price.toFixed(2);}}catch(e){}
  try{const d=await fetch('/api/history?limit=50').then(r=>r.json());renderCards(d);if(d.length){renderSummary(d[0]);if(d[0].analytics_bars)renderAnalytics(d[0]);}}catch(e){}
  try{const d=await fetch('/api/backtest/result').then(r=>r.json());if(!d.error){renderBacktest(d.summary);if(d.trades)renderTrades(d.trades);if(d.run_at){const el=$('bt-run-at');if(el)el.textContent='Run at '+d.run_at.slice(0,16).replace('T',' ')+' UTC';}loadCharts();}}catch(e){}
  try{const d=await fetch('/api/chart_analysis').then(r=>r.json());if(!d.error&&d.bias)renderChartAnalysis(d);}catch(e){}
  loadRiskRules();
})();

/* ═══ FIXES & NEW FEATURES ═══════════════════════════════════════════════ */

// Override renderChartAnalysis to display SVG overlay
function renderChartAnalysis(a) {
  const panel=$('car'); if(!panel)return; panel.style.display='block';
  const m=$('car-method'); if(m) m.textContent = a.analysis_method || '—';

  // Bias pill
  const bp=$('car-bias-pill');
  if(bp){
    const bias=a.bias||'neutral';
    bp.textContent=`BIAS: ${bias.toUpperCase()}`;
    bp.className='pill '+(bias==='buy'?'ok':bias==='sell'?'err':'off');
  }

  // SVG overlay
  const wrap=$('svg-overlay-wrap');
  if(wrap && a.overlay_svg){
    wrap.innerHTML=a.overlay_svg;
  }

  // Zone summary grid
  const zsg=$('zone-summary');
  if(zsg){
    const lz=a.liquidity_zones||[], sr=a.support_resistance||[];
    const ob=a.order_blocks||[], fvg=a.fair_value_gaps||[];
    zsg.innerHTML=`
      <div class="zsg-cell"><div class="zsg-lbl"><i class="fa-solid fa-water"></i> Liquidity</div><div class="zsg-val">${lz.length}</div><div class="zsb-badge" style="background:rgba(255,61,87,.1);color:#ff3d57">${lz.filter(z=>z.type==='sell_side').length} sell · ${lz.filter(z=>z.type==='buy_side').length} buy</div></div>
      <div class="zsg-cell"><div class="zsg-lbl"><i class="fa-solid fa-layer-group"></i> S / R Zones</div><div class="zsg-val">${sr.length}</div><div class="zsb-badge" style="background:rgba(51,102,255,.1);color:#3366FF">${sr.filter(z=>z.type==='resistance').length}R · ${sr.filter(z=>z.type==='support').length}S</div></div>
      <div class="zsg-cell"><div class="zsg-lbl"><i class="fa-solid fa-cube"></i> Order Blocks</div><div class="zsg-val">${ob.length}</div><div class="zsb-badge" style="background:rgba(230,126,0,.1);color:#E67E00">${ob.filter(z=>z.type==='bullish').length} bull · ${ob.filter(z=>z.type==='bearish').length} bear</div></div>
      <div class="zsg-cell"><div class="zsg-lbl"><i class="fa-solid fa-gap"></i> FVGs</div><div class="zsg-val">${fvg.length}</div><div class="zsb-badge" style="background:rgba(108,62,255,.1);color:#6C3EFF">${fvg.filter(z=>!z.filled).length} open</div></div>
    `;
  }

  // Observations and trade idea
  const info=$('car-info'); if(!info)return;
  const obs=a.key_observations||[], idea=a.trade_idea||{};
  const bias=a.bias||'neutral', trend=a.trend||'—';
  const bos=(a.market_structure||{}).last_bos||'none';
  const choch=(a.choch_zones||[]).length;

  let html=`
    <div style="display:flex;gap:7px;flex-wrap:wrap;margin-bottom:12px">
      <span class="pill ${bias==='buy'?'ok':bias==='sell'?'err':'off'}"><i class="fa-solid fa-chart-line"></i> ${bias.toUpperCase()}</span>
      <span class="pill off"><i class="fa-solid fa-arrow-trend-up"></i> ${trend}</span>
      <span class="pill off"><i class="fa-solid fa-coins"></i> ${a.premium_discount||'—'}</span>
      <span class="pill ${bos!=='none'?'blue':'off'}">BOS: ${bos}</span>
      ${choch>0?`<span class="pill warn">CHOCH: ${choch}</span>`:''}
    </div>
    <div style="font-size:11px;font-weight:700;color:var(--t4);margin-bottom:6px;text-transform:uppercase;letter-spacing:.07em">
      <i class="fa-solid fa-circle-info"></i> Key Observations
    </div>
  `;
  obs.forEach(o=>{html+=`<div style="font-size:13px;color:var(--t2);padding:5px 0;border-bottom:1px solid var(--bdr);font-weight:500;display:flex;gap:6px"><i class="fa-solid fa-angle-right" style="color:var(--blue);margin-top:2px;flex-shrink:0"></i><span>${esc(o)}</span></div>`;});

  if(idea.direction && idea.direction!=='wait'){
    const ic=idea.direction==='buy'?'#00b85c':'#ff3d57';
    html+=`<div style="margin-top:12px;padding:14px;background:var(--bg2);border-radius:var(--r);border:1.5px solid var(--bdr)">
      <div style="font-size:12px;font-weight:800;color:${ic};margin-bottom:8px"><i class="fa-solid fa-crosshairs"></i> Trade Idea: ${(idea.direction||'').toUpperCase()}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px">
        <div><span style="color:var(--t4);font-weight:600">Entry Zone</span><br><span style="font-weight:700">${esc(idea.entry_zone||'—')}</span></div>
        <div><span style="color:var(--t4);font-weight:600">Stop Loss</span><br><span style="font-weight:700;color:#ff3d57">${esc(idea.stop_loss||'—')}</span></div>
        <div><span style="color:var(--t4);font-weight:600">Take Profit</span><br><span style="font-weight:700;color:#00b85c">${esc(idea.take_profit||'—')}</span></div>
        <div><span style="color:var(--t4);font-weight:600">R:R</span><br><span style="font-weight:700;color:#E67E00">1 : 2</span></div>
      </div>
      <div style="margin-top:8px;font-size:12px;color:var(--t3);font-style:italic">${esc(idea.reasoning||'')}</div>
    </div>`;
  }
  info.innerHTML = html;
  goAnalytics();
}

// Notification test
async function testNotifications(){
  showOv('Sending test notifications...');
  try{
    const r=await fetch('/api/notify/test',{method:'POST'});
    const d=await r.json();
    hideOv();
    const nst=$('notify-st');
    if(d.telegram){
      const t=d.telegram; setPill('st-tg-cfg', t.ok?'ok':'err', t.ok?'Configured':'Not set');
      if(nst) nst.textContent = t.ok?'✓ Telegram sent':'✗ '+t.msg;
      if(nst) nst.className = 'tg-status '+(t.ok?'ok':'err');
      toast(t.ok?'Telegram test sent!':'Telegram: '+t.msg, t.ok?'success':'error');
    }
    if(d.gmail){
      const g=d.gmail; setPill('st-gm-cfg', g.ok?'ok':'off', g.ok?'Configured':'Not set');
      if(g.ok) toast('Gmail test sent!','success');
    }
  }catch(e){hideOv();toast('Test failed: '+e,'error');}
}

// Update status to also check notification config
const _origRefreshStatus = refreshStatus;
refreshStatus = async function(){
  await _origRefreshStatus();
  try{
    const d=await fetch('/api/status').then(r=>r.json());
    setPill('st-tg-cfg', d.telegram_configured?'ok':'off', d.telegram_configured?'Configured':'Not set');
    setPill('st-gm-cfg', d.gmail_configured?'ok':'off',    d.gmail_configured?'Configured':'Not set');
  }catch(e){}
};

// Override connectTelegram and testTelegram to use new system
function connectTelegram(){ testNotifications(); }
function testTelegram(){     testNotifications(); }

/* ══════════════════════════════════════════════════════════════════════════
   FEATURE 1 — URL HASH ROUTING
   Maps: #dashboard, #analytics, #backtest, #model, #settings
   ══════════════════════════════════════════════════════════════════════════ */

const ROUTE_MAP = {
  'dashboard': 'p-dash',
  'analytics': 'p-analytics',
  'backtest':  'p-backtest',
  'model':     'p-model',
  'settings':  'p-settings',
};
const PANEL_TO_ROUTE = Object.fromEntries(Object.entries(ROUTE_MAP).map(([r,p])=>[p,r]));

// Override goPanel to also update URL
function goPanel(el) {
  if (!el) return;
  // Accept string (panel id) or element
  if (typeof el === 'string') {
    el = document.querySelector(`[data-panel="${el}"]`) || el;
  }
  if (typeof el === 'string') return; // panel not found

  const panelId = el.dataset ? el.dataset.panel : el.id;

  document.querySelectorAll('.nt').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));

  // Activate the nav link
  const navEl = document.querySelector(`[data-panel="${panelId}"]`);
  if (navEl) navEl.classList.add('active');

  // Activate the panel
  const panel = $(panelId);
  if (panel) panel.classList.add('active');

  // Update URL hash without triggering popstate
  const route = PANEL_TO_ROUTE[panelId];
  if (route && window.location.hash !== '#' + route) {
    history.pushState({ panel: panelId }, '', '#' + route);
  }

  if (panelId === 'p-settings') { loadRiskRules(); loadLogs(); }
}

// Handle browser back/forward
window.addEventListener('popstate', e => {
  const hash = window.location.hash.replace('#', '') || 'dashboard';
  const panelId = ROUTE_MAP[hash] || 'p-dash';
  // Navigate without pushing to history again
  document.querySelectorAll('.nt').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  const navEl = document.querySelector(`[data-panel="${panelId}"]`);
  if (navEl) navEl.classList.add('active');
  const panel = $(panelId);
  if (panel) panel.classList.add('active');
  if (panelId === 'p-settings') { loadRiskRules(); loadLogs(); }
});

// Handle direct link navigation (click on <a href="#route">)
document.addEventListener('click', e => {
  const a = e.target.closest('a[href^="#"]');
  if (!a) return;
  const hash = a.getAttribute('href').replace('#', '');
  if (!ROUTE_MAP[hash]) return;
  e.preventDefault();
  goPanel(document.querySelector(`[data-panel="${ROUTE_MAP[hash]}"]`));
});

// On load, navigate to hash
function initRouting() {
  const hash = window.location.hash.replace('#', '') || 'dashboard';
  const panelId = ROUTE_MAP[hash] || 'p-dash';
  document.querySelectorAll('.nt').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  const navEl = document.querySelector(`[data-panel="${panelId}"]`);
  if (navEl) navEl.classList.add('active');
  const panel = $(panelId);
  if (panel) panel.classList.add('active');
  // Set initial hash without adding to history
  if (!window.location.hash) {
    history.replaceState({ panel: panelId }, '', '#dashboard');
  }
}


/* ══════════════════════════════════════════════════════════════════════════
   FEATURE 2 — NOTIFICATION CENTRE
   ══════════════════════════════════════════════════════════════════════════ */

const notifications = [];
let unreadCount = 0;

const NOTIF_ICONS = {
  success: { icon:'fa-circle-check',  cls:'green'  },
  error:   { icon:'fa-circle-xmark',  cls:'red'    },
  warning: { icon:'fa-triangle-exclamation', cls:'amber' },
  info:    { icon:'fa-circle-info',   cls:'blue'   },
  signal:  { icon:'fa-bolt-lightning',cls:'blue'   },
  scan:    { icon:'fa-crosshairs',    cls:'purple' },
  price:   { icon:'fa-coins',         cls:'amber'  },
  train:   { icon:'fa-microchip',     cls:'blue'   },
  chart:   { icon:'fa-chart-candlestick', cls:'green' },
};

function pushNotification(title, msg, type='info') {
  const n = {
    id:    Date.now(),
    title, msg, type,
    time:  new Date().toUTCString().slice(17,25) + ' UTC',
    read:  false,
  };
  notifications.unshift(n);
  if (notifications.length > 50) notifications.pop();

  unreadCount++;
  _updateBellBadge();
  _renderNotifList();
  return n;
}

function _updateBellBadge() {
  const dot = $('bell-dot');
  const btn = $('bell-btn');
  if (!dot || !btn) return;

  // Remove old badge
  const oldBadge = btn.querySelector('.np-badge');
  if (oldBadge) oldBadge.remove();

  if (unreadCount > 0) {
    dot.style.display = 'block';
    const badge = document.createElement('span');
    badge.className = 'np-badge';
    badge.textContent = unreadCount > 9 ? '9+' : unreadCount;
    btn.appendChild(badge);
  } else {
    dot.style.display = 'none';
  }
}

function _renderNotifList() {
  const list = $('np-list');
  if (!list) return;
  if (!notifications.length) {
    list.innerHTML = '<div class="np-empty"><i class="fa-regular fa-bell-slash"></i><span>No notifications yet</span></div>';
    return;
  }
  const cfg = NOTIF_ICONS;
  list.innerHTML = notifications.map(n => {
    const ic = cfg[n.type] || cfg.info;
    return `<div class="np-item ${n.type} ${n.read ? '' : 'unread'}" onclick="markRead(${n.id})">
      <div class="np-icon ${ic.cls}"><i class="fa-solid ${ic.icon}"></i></div>
      <div class="np-body">
        <div class="np-title">${esc(n.title)}</div>
        <div class="np-msg">${esc(n.msg)}</div>
        <div class="np-time"><i class="fa-regular fa-clock"></i> ${n.time}</div>
      </div>
    </div>`;
  }).join('');
}

function markRead(id) {
  const n = notifications.find(x => x.id === id);
  if (n && !n.read) { n.read = true; unreadCount = Math.max(0, unreadCount-1); _updateBellBadge(); _renderNotifList(); }
}

function markAllRead() {
  notifications.forEach(n => { n.read = true; });
  unreadCount = 0; _updateBellBadge(); _renderNotifList();
}

function clearNotifications() {
  notifications.length = 0; unreadCount = 0; _updateBellBadge(); _renderNotifList();
}

function toggleNotifPanel() {
  const panel   = $('notif-panel');
  const overlay = $('notif-overlay');
  if (!panel) return;
  const isOpen = panel.classList.contains('open');
  if (!isOpen) {
    panel.classList.add('open');
    overlay.classList.add('open');
    markAllRead();
  } else {
    closeNotifPanel();
  }
}

function closeNotifPanel() {
  const panel   = $('notif-panel');
  const overlay = $('notif-overlay');
  if (panel)   panel.classList.remove('open');
  if (overlay) overlay.classList.remove('open');
}

// Intercept toast to also push to notification centre
const _origToast = toast;
toast = function(msg, type='info') {
  _origToast(msg, type);
  const titles = { success:'Success', error:'Error', info:'Info', warning:'Warning' };
  pushNotification(titles[type] || 'Notice', msg, type);
};


/* ══════════════════════════════════════════════════════════════════════════
   FEATURE 3 — TRADE LOG PAGINATION + SORT + FILTER
   ══════════════════════════════════════════════════════════════════════════ */

let _allTrades    = [];
let _filteredTrades = [];
let _currentPage  = 1;
let _pageSize     = 20;
let _sortKey      = 'entry_time';
let _sortDir      = 'desc';
let _searchQuery  = '';

function renderTrades(trades) {
  _allTrades = trades || [];
  _currentPage = 1;
  _applyFilterSort();
}

function _applyFilterSort() {
  // Filter
  const q = _searchQuery.toLowerCase();
  _filteredTrades = q
    ? _allTrades.filter(t =>
        Object.values(t).some(v => String(v).toLowerCase().includes(q)))
    : [..._allTrades];

  // Sort
  _filteredTrades.sort((a, b) => {
    let va = a[_sortKey] ?? '', vb = b[_sortKey] ?? '';
    if (typeof va === 'number' && typeof vb === 'number') {
      return _sortDir === 'asc' ? va - vb : vb - va;
    }
    va = String(va); vb = String(vb);
    return _sortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
  });

  _renderPage();
}

function _renderPage() {
  const tbody = $('trade-body');
  if (!tbody) return;

  const total = _filteredTrades.length;
  const totalPages = Math.max(1, Math.ceil(total / _pageSize));
  _currentPage = Math.min(_currentPage, totalPages);

  const start = (_currentPage - 1) * _pageSize;
  const end   = Math.min(start + _pageSize, total);
  const pageData = _filteredTrades.slice(start, end);

  // Update info
  const info = $('tbl-info');
  if (info) info.textContent = total ? `${start+1}–${end} of ${total} trades` : '';

  // Render rows
  if (!pageData.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="ph-td">
      ${_searchQuery ? 'No trades match your filter.' : 'No data — run backtest first.'}
    </td></tr>`;
  } else {
    tbody.innerHTML = pageData.map(t => {
      const isWin = t.outcome === 'WIN';
      return `<tr>
        <td style="font-family:var(--mono);font-size:11px">${(t.entry_time||'').slice(0,16)}</td>
        <td>
          <span style="display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:800;background:${t.direction==='BUY'?'var(--gl)':'var(--rl)'};color:${t.direction==='BUY'?'var(--green)':'var(--red)'}">
            <i class="fa-solid ${t.direction==='BUY'?'fa-arrow-trend-up':'fa-arrow-trend-down'}"></i>
            ${t.direction}
          </span>
        </td>
        <td style="font-family:var(--mono);font-weight:700">$${f2(t.entry_price)}</td>
        <td style="font-family:var(--mono);color:var(--red);font-weight:600">$${f2(t.sl)}</td>
        <td style="font-family:var(--mono);color:var(--green);font-weight:600">$${f2(t.tp)}</td>
        <td>
          <span style="display:inline-flex;align-items:center;gap:4px;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:800;background:${isWin?'var(--gl)':'var(--rl)'};color:${isWin?'var(--green)':'var(--red)'}">
            <i class="fa-solid ${isWin?'fa-check':'fa-xmark'}"></i>${t.outcome}
          </span>
        </td>
        <td style="font-family:var(--mono);font-weight:800;color:${t.pnl_usd>=0?'var(--green)':'var(--red)'}">${fUSD(t.pnl_usd)}</td>
        <td style="font-family:var(--mono)">${t.confidence||'—'}%</td>
        <td style="font-size:12px;color:var(--t3)">${t.session||'—'}</td>
      </tr>`;
    }).join('');
  }

  // Pagination bar
  const pgBar = $('pagination-bar');
  if (pgBar) pgBar.style.display = total > _pageSize ? 'flex' : 'none';

  _renderPaginationButtons(totalPages);

  // Update sort icons
  document.querySelectorAll('.sortable').forEach(th => {
    th.classList.remove('asc','desc');
    const icon = th.querySelector('i');
    if (icon) icon.className = 'fa-solid fa-sort';
  });
  const sortMap = { entry_time:'sort-time', direction:'sort-dir',
    entry_price:'sort-entry', outcome:'sort-result',
    pnl_usd:'sort-pnl', confidence:'sort-conf' };
  const activeIcon = $(sortMap[_sortKey]);
  if (activeIcon) {
    activeIcon.className = `fa-solid fa-sort-${_sortDir === 'asc' ? 'up' : 'down'}`;
    activeIcon.closest('th').classList.add(_sortDir);
  }
}

function _renderPaginationButtons(totalPages) {
  const container = $('pg-pages');
  if (!container) return;

  const prev = $('pg-prev');
  const next = $('pg-next');
  if (prev) prev.disabled = _currentPage <= 1;
  if (next) next.disabled = _currentPage >= totalPages;

  // Build smart page number list
  const pages = [];
  const delta = 2;
  let left  = Math.max(1, _currentPage - delta);
  let right = Math.min(totalPages, _currentPage + delta);

  // Always show first
  if (left > 1) { pages.push(1); if (left > 2) pages.push('...'); }
  for (let i = left; i <= right; i++) pages.push(i);
  // Always show last
  if (right < totalPages) { if (right < totalPages-1) pages.push('...'); pages.push(totalPages); }

  container.innerHTML = pages.map(p => {
    if (p === '...') return `<span class="pg-num ellipsis">…</span>`;
    return `<button class="pg-num ${p===_currentPage?'active':''}" onclick="jumpPage(${p})">${p}</button>`;
  }).join('');
}

function changePage(delta) {
  const total = Math.ceil(_filteredTrades.length / _pageSize);
  _currentPage = Math.max(1, Math.min(_currentPage + delta, total));
  _renderPage();
  // Smooth scroll to top of table
  const card = $('trade-body')?.closest('.info-card');
  if (card) card.scrollIntoView({ behavior:'smooth', block:'nearest' });
}

function jumpPage(n) {
  _currentPage = n;
  _renderPage();
}

function changePageSize(size) {
  _pageSize = parseInt(size);
  _currentPage = 1;
  _renderPage();
}

function sortTrades(key) {
  if (_sortKey === key) {
    _sortDir = _sortDir === 'asc' ? 'desc' : 'asc';
  } else {
    _sortKey = key;
    _sortDir = key === 'pnl_usd' || key === 'entry_price' ? 'desc' : 'asc';
  }
  _applyFilterSort();
}

function filterTrades(query) {
  _searchQuery = query;
  _currentPage = 1;
  _applyFilterSort();
}


/* ══════════════════════════════════════════════════════════════════════════
   HOOK INTO EXISTING EVENTS — push to notification centre
   ══════════════════════════════════════════════════════════════════════════ */

// Intercept socket sys events for notification centre
const _origSys = socket.listeners('sys')[0];
socket.on('sys', d => {
  if (d.s === 'ready' && d.m && d.m.includes('Scan done')) {
    pushNotification('Scan Complete', d.m, 'scan');
  } else if (d.s === 'ready' && d.m && d.m.includes('Training complete')) {
    pushNotification('Model Trained', d.m, 'train');
  } else if (d.s === 'ready' && d.m && d.m.includes('Backtest complete')) {
    pushNotification('Backtest Done', d.m, 'chart');
  } else if (d.s === 'error') {
    pushNotification('System Error', d.m || 'Unknown error', 'error');
  } else if (d.s === 'ready' && d.m && d.m.includes('Analysis complete')) {
    pushNotification('Chart Analysed', d.m, 'chart');
  }
});

// Intercept price updates for big moves
let _lastPrice = 0;
const _origPriceListener = socket.listeners('price_update')[0];
socket.on('price_update', tick => {
  if (_lastPrice && tick.price) {
    const move = Math.abs((tick.price - _lastPrice) / _lastPrice * 100);
    if (move > 0.5) {
      pushNotification(
        `XAUUSD ${tick.change >= 0 ? '📈' : '📉'} Big Move`,
        `Price ${tick.change >= 0 ? 'surged' : 'dropped'} ${move.toFixed(2)}% → $${tick.price.toFixed(2)}`,
        'price'
      );
    }
  }
  _lastPrice = tick.price;
});

// Intercept signal updates
const _origSignalListener = socket.listeners('signal_update')[0];
socket.on('signal_update', sig => {
  if (sig.signal !== 'NO_TRADE') {
    const type = sig.risk_passed ? 'success' : 'warning';
    pushNotification(
      `Signal: ${sig.signal} @ $${parseFloat(sig.live_price||sig.close||0).toFixed(2)}`,
      `Confidence ${sig.confidence}% · Confluence ${sig.confluence}/8 · ${sig.risk_passed?'Risk PASS':'Risk FAIL'}`,
      type
    );
  }
});


/* ══════════════════════════════════════════════════════════════════════════
   INIT — run routing on page load
   ══════════════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  initRouting();
  _renderNotifList();
  // Push a welcome notification
  pushNotification('Gold Sniper v4 Ready', 'System loaded. Train the model then click Scan Now.', 'info');
});

/* ══════════════════════════════════════════════════════════════════════════
   CHART ANALYSIS — Zone filter toggles + SVG overlay rendering
   ══════════════════════════════════════════════════════════════════════════ */

let _lastAnalysis  = null;   // cached full result
let _activeZones   = new Set(['liquidity','support_resistance','order_block',
                               'fvg','choch','bos','premium_discount']);

// Toggle a zone type on/off and redraw overlay
function toggleZone(btn) {
  const zone = btn.dataset.zone;
  if (_activeZones.has(zone)) {
    _activeZones.delete(zone);
    btn.classList.remove('active');
  } else {
    _activeZones.add(zone);
    btn.classList.add('active');
  }
  _redrawOverlay();
}

function selectAllZones() {
  _activeZones = new Set(['liquidity','support_resistance','order_block',
                           'fvg','choch','bos','premium_discount']);
  document.querySelectorAll('.zone-toggle').forEach(b => b.classList.add('active'));
  _redrawOverlay();
}

function clearAllZones() {
  _activeZones.clear();
  document.querySelectorAll('.zone-toggle').forEach(b => b.classList.remove('active'));
  _redrawOverlay();
}

function _redrawOverlay() {
  if (!_lastAnalysis) return;
  const layers = _lastAnalysis.overlay_layers || {};
  const wrap   = $('svg-overlay-wrap');
  if (!wrap) return;

  // If only one zone selected, use its pre-built layer
  const active = [..._activeZones];
  if (active.length === 1 && layers[active[0]]) {
    wrap.innerHTML = layers[active[0]];
    return;
  }

  // For "all" zones use the pre-built full overlay
  if (active.length === 7 && _lastAnalysis.overlay_svg) {
    wrap.innerHTML = _lastAnalysis.overlay_svg;
    return;
  }

  // For mixed selection, we compose SVGs client-side using the base image
  // and individual layer elements — simplest approach: request a rebuild
  // Since we store layers server-side we can compose them by stacking SVGs
  // For now: use full SVG and hide layers via CSS opacity based on active set
  // We use the pre-built full SVG if available
  if (_lastAnalysis.overlay_svg) {
    wrap.innerHTML = _lastAnalysis.overlay_svg;
    // Apply visibility per zone (the SVG uses data-zone-type attributes we add)
  }
}

// Override renderChartAnalysis with new clean version
function renderChartAnalysis(a) {
  _lastAnalysis = a;
  const panel = $('car'); if (!panel) return;
  panel.style.display = 'block';

  // Bias pill
  const bias = a.bias || 'neutral';
  const bp   = $('car-bias-pill');
  if (bp) {
    bp.textContent = `BIAS: ${bias.toUpperCase()}`;
    bp.className   = 'pill ' + (bias==='buy'?'ok':bias==='sell'?'err':'off');
  }
  const meth = $('car-method');
  if (meth) meth.textContent = (a.analysis_method||'—').replace(/_/g,' ');

  // SVG overlay
  const wrap = $('svg-overlay-wrap');
  const ph   = $('svg-ph');
  if (wrap && a.overlay_svg) {
    if (ph) ph.style.display = 'none';
    wrap.innerHTML = a.overlay_svg;
  }

  // Zone summary stats
  const zsg = $('zone-summary');
  if (zsg) {
    const lz = a.liquidity_zones||[], sr = a.support_resistance||[];
    const ob = a.order_blocks||[], fvg = a.fair_value_gaps||[];
    zsg.innerHTML = `
      <div class="zsg-cell">
        <div class="zsg-lbl"><i class="fa-solid fa-water"></i> Liquidity</div>
        <div class="zsg-val" style="color:#FF4757">${lz.length}</div>
        <div class="zsg-sub">${lz.filter(z=>z.type==='sell_side').length} sell · ${lz.filter(z=>z.type==='buy_side').length} buy</div>
      </div>
      <div class="zsg-cell">
        <div class="zsg-lbl"><i class="fa-solid fa-layer-group"></i> S/R Levels</div>
        <div class="zsg-val" style="color:#1E90FF">${sr.length}</div>
        <div class="zsg-sub">${sr.filter(z=>z.strength==='major').length} major · ${sr.filter(z=>z.strength==='minor').length} minor</div>
      </div>
      <div class="zsg-cell">
        <div class="zsg-lbl"><i class="fa-solid fa-cube"></i> Order Blocks</div>
        <div class="zsg-val" style="color:#26de81">${ob.length}</div>
        <div class="zsg-sub">${ob.filter(z=>z.type==='bullish').length} bull · ${ob.filter(z=>z.type==='bearish').length} bear</div>
      </div>
      <div class="zsg-cell">
        <div class="zsg-lbl"><i class="fa-solid fa-gap"></i> FVGs</div>
        <div class="zsg-val" style="color:#A29BFE">${fvg.length}</div>
        <div class="zsg-sub">${fvg.filter(z=>!z.filled).length} open · ${fvg.filter(z=>z.filled).length} filled</div>
      </div>`;
  }

  // Observations and trade idea
  const info = $('car-info'); if (!info) return;
  const obs  = a.key_observations||[], idea = a.trade_idea||{};
  const bos  = (a.market_structure||{}).last_bos||'none';
  const choch = (a.choch_zones||[]).length;
  const mkt  = a.premium_discount||'—';

  let html = `<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;padding:14px 14px 0">
    <span class="pill ${bias==='buy'?'ok':bias==='sell'?'err':'off'}">${bias.toUpperCase()}</span>
    <span class="pill off">${(a.trend||'—')}</span>
    <span class="pill off">${mkt}</span>
    <span class="pill ${bos!=='none'?'blue':'off'}">BOS: ${bos}</span>
    ${choch>0?`<span class="pill warn"><i class="fa-solid fa-rotate"></i> CHOCH: ${choch}</span>`:''}
    ${a.green_pct!=null?`<span class="pill ok">${a.green_pct}% bullish</span>`:''}
    ${a.red_pct!=null?`<span class="pill err">${a.red_pct}% bearish</span>`:''}
  </div>`;

  html += `<div style="padding:0 14px 12px">
    <div style="font-size:11px;font-weight:700;color:var(--t4);margin-bottom:8px;
                text-transform:uppercase;letter-spacing:.07em">
      <i class="fa-solid fa-circle-info"></i> Key Observations
    </div>`;
  obs.forEach(o => {
    html += `<div style="font-size:12.5px;color:var(--t2);padding:5px 0;
                         border-bottom:1px solid var(--bdr);line-height:1.5;
                         display:flex;gap:7px;font-weight:500">
      <i class="fa-solid fa-angle-right" style="color:var(--blue);margin-top:2px;flex-shrink:0;font-size:11px"></i>
      <span>${esc(o)}</span></div>`;
  });
  html += '</div>';

  if (idea.direction && idea.direction !== 'wait') {
    const ic = idea.direction==='buy'?'#26de81':'#FF4757';
    html += `<div style="margin:0 14px 14px;padding:14px;
                          background:var(--bg2);border-radius:var(--r);
                          border:1.5px solid var(--bdr)">
      <div style="font-size:12px;font-weight:800;color:${ic};margin-bottom:10px">
        <i class="fa-solid fa-crosshairs"></i> Trade Idea: ${(idea.direction||'').toUpperCase()}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:12px">
        <div><div style="color:var(--t4);font-weight:600;margin-bottom:2px">Entry Zone</div>
          <div style="font-weight:700;color:var(--t1)">${esc(idea.entry_zone||'—')}</div></div>
        <div><div style="color:var(--t4);font-weight:600;margin-bottom:2px">Stop Loss</div>
          <div style="font-weight:700;color:#FF4757">${esc(idea.stop_loss||'—')}</div></div>
        <div><div style="color:var(--t4);font-weight:600;margin-bottom:2px">Take Profit</div>
          <div style="font-weight:700;color:#26de81">${esc(idea.take_profit||'—')}</div></div>
        <div><div style="color:var(--t4);font-weight:600;margin-bottom:2px">R:R</div>
          <div style="font-weight:700;color:#FFA502">1 : 2</div></div>
      </div>
      <div style="margin-top:10px;font-size:12px;color:var(--t3);line-height:1.5;
                  font-style:italic;border-top:1px solid var(--bdr);padding-top:8px">
        ${esc(idea.reasoning||'')}
      </div>
    </div>`;
  }
  info.innerHTML = html;
  goAnalytics();
}
