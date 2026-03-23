import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time, json
from datetime import datetime, timedelta
import numpy as np

DB_PATH  = "monitoring.db"
IST_ZONE = "Asia/Kolkata"

st.set_page_config(page_title="Enterprise Monitoring", layout="wide", initial_sidebar_state="expanded")

# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');

/* ═══════════════════════════════════════════════
   THEME: Clean Charcoal — high-contrast, readable
   BG: #1c1c1e  CARD: #2c2c2e  TEXT: #f2f2f7
   ACCENT: #0a84ff  BORDER: #3a3a3c
   ═══════════════════════════════════════════════ */

html,body,[class*="css"]{
  font-family:'Inter',sans-serif !important;
  font-size:15px !important;
  color:#f2f2f7 !important;
}
.stApp{ background:#1c1c1e !important; color:#f2f2f7 !important; }
[data-testid="stSidebar"]{
  background:#2c2c2e !important;
  border-right:2px solid #3a3a3c !important;
}
[data-testid="stSidebar"] *{ color:#f2f2f7 !important; }
[data-testid="stSidebar"] .block-container{ padding-top:1rem; }

/* ── sticky top nav ── */
.top-nav{
  position:sticky; top:0; z-index:1000;
  background:#2c2c2e; border-bottom:2px solid #3a3a3c;
  padding:10px 0 8px; margin-bottom:20px;
}
.nav-links{ display:flex; gap:6px; flex-wrap:wrap; }
.nav-link{
  font-family:'JetBrains Mono',monospace; font-size:.82rem; font-weight:600;
  text-transform:uppercase; letter-spacing:.05em; color:#aeaeb2;
  background:#3a3a3c; border:1px solid #48484a; border-radius:6px;
  padding:6px 14px; text-decoration:none; transition:all .15s;
}
.nav-link:hover{ color:#f2f2f7; border-color:#0a84ff; background:#48484a; }
.nav-link.active{ color:#fff; border-color:#0a84ff; background:#0a84ff; }

/* ── section headers ── */
.sec-hdr{
  font-size:1rem; font-weight:700; text-transform:uppercase;
  letter-spacing:.1em; color:#f2f2f7; margin:32px 0 14px;
  display:flex; align-items:center; gap:10px;
  border-left:4px solid #0a84ff; padding-left:12px;
}
.sec-hdr .num{
  font-family:'JetBrains Mono',monospace; color:#0a84ff;
  font-size:.9rem; background:#1c1c1e; padding:2px 8px;
  border-radius:4px; border:1px solid #0a84ff;
}
.sec-hdr::after{ content:''; flex:1; height:1px; background:#3a3a3c; }

/* ── KPI cards ── */
.kpi{
  background:#2c2c2e; border:1px solid #3a3a3c; border-radius:12px;
  padding:18px 20px; position:relative; overflow:hidden;
}
.kpi:hover{ border-color:#0a84ff; }
.kpi .bar{ position:absolute; top:0; left:0; right:0; height:3px; }
.kpi-lbl{
  font-size:.82rem; font-weight:700; text-transform:uppercase;
  letter-spacing:.08em; color:#aeaeb2; margin-bottom:8px;
}
.kpi-val{
  font-family:'JetBrains Mono',monospace; font-size:2rem;
  font-weight:700; line-height:1; color:#f2f2f7;
}
.kpi-sub{ font-family:'JetBrains Mono',monospace; font-size:.82rem; margin-top:5px; color:#aeaeb2; }
.du{ color:#ff453a !important; } .dd{ color:#30d158 !important; } .df{ color:#aeaeb2 !important; }

/* ── server table ── */
.srv-wrap{ background:#2c2c2e; border:1px solid #3a3a3c; border-radius:12px; overflow:hidden; }
.srv-th{
  display:grid; grid-template-columns:2fr 1.8fr 1fr 1fr 1fr 1fr 1fr;
  background:#3a3a3c; padding:10px 16px; border-bottom:2px solid #48484a;
  font-size:.8rem; font-weight:700; text-transform:uppercase;
  letter-spacing:.08em; color:#f2f2f7;
}
.srv-row{
  display:grid; grid-template-columns:2fr 1.8fr 1fr 1fr 1fr 1fr 1fr;
  align-items:center; padding:12px 16px; border-bottom:1px solid #3a3a3c;
  font-family:'JetBrains Mono',monospace; font-size:.88rem; transition:background .12s;
  color:#e5e5ea;
}
.srv-row:last-child{ border-bottom:none; }
.srv-row:hover{ background:#3a3a3c; }
.sn{ color:#f2f2f7; font-weight:700; font-size:.92rem; }
.srv-host{ color:#aeaeb2; font-size:.82rem; }
.si{ color:#64d2ff; font-size:.82rem; }
.pill{
  display:inline-flex; align-items:center; gap:4px; padding:4px 10px;
  border-radius:20px; font-size:.8rem; font-weight:700; letter-spacing:.03em;
}
.pill::before{ content:'●'; font-size:.55rem; }
.p-ok  { background:#0d3320; color:#30d158; border:1px solid #30d158; }
.p-warn{ background:#332600; color:#ffd60a; border:1px solid #ffd60a; }
.p-crit{ background:#330d0a; color:#ff453a; border:1px solid #ff453a; }
.mb{ background:#48484a; border-radius:4px; height:5px; margin-top:5px; overflow:hidden; width:72px; }
.mf{ height:100%; border-radius:4px; }

/* ══ INCIDENT PANEL ══ */
.inc-panel{ background:#2c2c2e; border:1px solid #3a3a3c; border-radius:12px; overflow:hidden; }
.inc-toolbar{
  display:flex; align-items:center; gap:10px; padding:12px 16px;
  background:#3a3a3c; border-bottom:2px solid #48484a; flex-wrap:wrap;
}
.inc-count-badge{
  font-family:'JetBrains Mono',monospace; font-size:.82rem; font-weight:700;
  padding:4px 12px; border-radius:14px; letter-spacing:.04em;
}
.badge-crit{ background:#4a0000; color:#ff6b6b; border:1px solid #ff453a; }
.badge-warn{ background:#3d2e00; color:#ffd60a; border:1px solid #ffd60a; }
.badge-ok  { background:#0d3320; color:#30d158; border:1px solid #30d158; }
.badge-info{ background:#002a4a; color:#64d2ff; border:1px solid #0a84ff; }

/* scrollable list */
.inc-list{
  max-height:560px; overflow-y:auto; padding:12px 12px 6px;
  scrollbar-width:thin; scrollbar-color:#48484a #2c2c2e;
}
.inc-list::-webkit-scrollbar{ width:5px; }
.inc-list::-webkit-scrollbar-track{ background:#2c2c2e; }
.inc-list::-webkit-scrollbar-thumb{ background:#48484a; border-radius:4px; }
.inc-list-empty{ text-align:center; padding:40px; color:#aeaeb2; font-size:1rem; }

/* incident card */
.ic{
  background:#1c1c1e; border:1px solid #3a3a3c; border-radius:10px;
  margin-bottom:10px; overflow:hidden; transition:border-color .15s;
}
.ic:hover{ border-color:#0a84ff; }
.ic.c-crit{ border-left:4px solid #ff453a; }
.ic.c-err { border-left:4px solid #ff9f0a; }
.ic.c-warn{ border-left:4px solid #ffd60a; }

/* card header row */
.ic-hdr{
  display:flex; align-items:center; gap:10px;
  padding:12px 14px; background:#2c2c2e; border-bottom:1px solid #3a3a3c;
}
.ic-icon{ font-size:1.1rem; flex-shrink:0; }
.ic-meta-left{ flex:1; min-width:0; }
.ic-id{ font-family:'JetBrains Mono',monospace; font-size:.85rem; font-weight:700; color:#64d2ff; }
.ic-type{ font-size:.95rem; font-weight:600; color:#f2f2f7;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; margin-top:2px; }
.ic-badges{ display:flex; gap:6px; flex-shrink:0; align-items:center; }
.sev-b{ font-family:'JetBrains Mono',monospace; font-size:.78rem; font-weight:700;
  letter-spacing:.05em; padding:4px 10px; border-radius:5px; }
.b-crit{ background:#4a0000; color:#ff6b6b; border:1px solid #ff453a; }
.b-err { background:#3d1f00; color:#ffb340; border:1px solid #ff9f0a; }
.b-warn{ background:#3d2e00; color:#ffd60a; border:1px solid #ffd60a; }
.b-info{ background:#002a4a; color:#64d2ff; border:1px solid #0a84ff; }
.dur-b{ font-family:'JetBrains Mono',monospace; font-size:.78rem; font-weight:600;
  padding:4px 10px; border-radius:5px; background:#3a3a3c; color:#e5e5ea; }

/* card body — 2-col grid */
.ic-body{ display:grid; grid-template-columns:1fr 1fr; gap:0; padding:14px; }
.ic-field{ margin-bottom:10px; padding-right:12px; }
.ic-field.full{ grid-column:1/-1; padding-right:0; }
.ifl{
  font-size:.78rem; font-weight:700; text-transform:uppercase;
  letter-spacing:.08em; color:#aeaeb2; margin-bottom:4px;
}
.ifv{ font-size:.92rem; color:#e5e5ea; line-height:1.55; }
.ifv.highlight{ color:#f2f2f7; font-weight:600; }

/* card footer strip */
.ic-foot{
  display:flex; gap:16px; padding:10px 14px;
  background:#2c2c2e; border-top:1px solid #3a3a3c;
  font-family:'JetBrains Mono',monospace; font-size:.8rem;
  color:#aeaeb2; flex-wrap:wrap;
}
.ic-foot span{ color:#e5e5ea; font-weight:500; }

/* timeline bar inside card */
.tbar-bg{ background:#3a3a3c; border-radius:3px; height:4px; margin-top:4px; }
.tbar-fill{ height:4px; border-radius:3px; background:linear-gradient(90deg,#0a84ff,#64d2ff); }

/* ── prediction cards ── */
.pred{
  background:#2c2c2e; border:1px solid #3a3a3c; border-radius:10px;
  padding:14px 16px; margin-bottom:10px; display:flex;
  align-items:flex-start; gap:14px;
}
.pred:hover{ border-color:#0a84ff; }
.ring{
  min-width:54px; height:54px; border-radius:50%; border:2px solid;
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  font-family:'JetBrains Mono',monospace; flex-shrink:0;
}
.rv{ font-size:.95rem; font-weight:700; line-height:1; }
.rl{ font-size:.62rem; color:#aeaeb2; margin-top:2px; }
.pb{ flex:1; }
.pi{ font-size:.95rem; font-weight:600; color:#f2f2f7; margin-bottom:4px; }
.pm{ font-family:'JetBrains Mono',monospace; font-size:.82rem; color:#aeaeb2; margin-bottom:6px; }
.pr{ font-size:.88rem; color:#e5e5ea; line-height:1.5; }
.ttf{
  font-family:'JetBrains Mono',monospace; font-size:.82rem; font-weight:700;
  padding:4px 10px; border-radius:5px; background:#002a4a; color:#64d2ff;
  border:1px solid #0a84ff; white-space:nowrap;
}

/* ── log viewer ── */
.logv{
  background:#1c1c1e; border:1px solid #3a3a3c; border-radius:10px;
  padding:12px 16px; max-height:320px; overflow-y:auto;
  font-family:'JetBrains Mono',monospace; font-size:.88rem;
  scrollbar-width:thin; scrollbar-color:#48484a #1c1c1e;
}
.logv::-webkit-scrollbar{ width:4px; }
.logv::-webkit-scrollbar-thumb{ background:#48484a; border-radius:3px; }
.ll{ padding:4px 0; border-bottom:1px solid #2c2c2e; line-height:1.65; }
.ll:last-child{ border-bottom:none; }
.lts{ color:#8e8e93; margin-right:8px; }
.lc{ margin-right:6px; font-weight:700; }
.lc-c{ color:#ff453a; } .lc-e{ color:#ff9f0a; } .lc-w{ color:#ffd60a; } .lc-i{ color:#64d2ff; }
.lsrv{ color:#aeaeb2; margin-right:6px; font-weight:600; }
.lm{ color:#e5e5ea; }

/* ── alert banners ── */
.alert{
  border-radius:10px; padding:12px 16px; margin-bottom:10px;
  display:flex; align-items:center; gap:10px; font-size:.92rem; font-weight:500;
}
.a-crit{ background:#2d0a08; border:1px solid #ff453a; color:#ff9d9a; }
.a-warn{ background:#2d2200; border:1px solid #ffd60a; color:#ffe566; }

/* ── SLA gauge ── */
.sla-card{
  background:#2c2c2e; border:1px solid #3a3a3c; border-radius:10px;
  padding:18px 20px; text-align:center;
}
.sla-val{ font-family:'JetBrains Mono',monospace; font-size:2.4rem; font-weight:700; line-height:1; color:#f2f2f7; }
.sla-lbl{ font-size:.82rem; text-transform:uppercase; letter-spacing:.1em; color:#aeaeb2; margin-top:6px; }

/* ── uptime timeline ── */
.upt-wrap{ background:#2c2c2e; border:1px solid #3a3a3c; border-radius:10px; padding:12px 16px; }
.upt-bar{ display:flex; gap:3px; margin:8px 0 5px; height:24px; }
.upt-seg{ flex:1; border-radius:3px; }

/* ── misc ── */
hr{ border-color:#3a3a3c !important; }
[data-testid="metric-container"]{
  background:#2c2c2e !important; border:1px solid #3a3a3c !important;
  border-radius:10px !important; padding:14px !important;
}
[data-testid="metric-container"] *{ color:#f2f2f7 !important; }
.stDataFrame{ border:1px solid #3a3a3c !important; border-radius:8px; }
[data-testid="stExpander"]{
  background:#2c2c2e !important; border:1px solid #3a3a3c !important; border-radius:10px !important;
}
[data-testid="stExpander"] summary{ color:#f2f2f7 !important; font-weight:600 !important; }
.stTabs [data-baseweb="tab-list"]{
  background:#2c2c2e; border-radius:8px; border:1px solid #3a3a3c; padding:4px;
}
.stTabs [data-baseweb="tab"]{ color:#aeaeb2 !important; font-size:.9rem !important; font-weight:500; padding:8px 16px !important; }
.stTabs [aria-selected="true"]{ color:#f2f2f7 !important; background:#0a84ff !important; border-radius:6px !important; }
p, span, div, label{ color:#f2f2f7; }
h1,h2,h3,h4,h5,h6{ color:#f2f2f7 !important; font-weight:700 !important; }
::-webkit-scrollbar{ width:6px; height:6px; }
::-webkit-scrollbar-track{ background:#1c1c1e; }
::-webkit-scrollbar-thumb{ background:#48484a; border-radius:4px; }
.back-top{
  position:fixed; bottom:24px; right:24px; z-index:9999;
  background:#0a84ff; color:#fff; border:none;
  border-radius:8px; padding:8px 16px;
  font-family:'JetBrains Mono',monospace; font-size:.82rem;
  text-decoration:none; font-weight:700;
  box-shadow:0 4px 16px rgba(10,132,255,.4);
}
.back-top:hover{ background:#0066cc; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# AUTO-REFRESH
# ══════════════════════════════════════════════════════════════
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
if time.time() - st.session_state.last_refresh > 10:
    st.session_state.last_refresh = time.time()
    st.rerun()

# ══════════════════════════════════════════════════════════════
# DB HELPERS
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=10)
def qry(sql):
    try:
        conn = sqlite3.connect(DB_PATH)
        df   = pd.read_sql_query(sql, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def to_ist(df, col):
    if col in df.columns and not df.empty:
        df[col] = pd.to_datetime(df[col], format="mixed", utc=True, errors="coerce")
        df[col] = df[col].dt.tz_convert(IST_ZONE)
    return df

def pc(v,w,c):
    return "#ef4444" if v>=c else "#f59e0b" if v>=w else "#10b981"

def pill_cls(v,w,c):
    if v>=c: return "p-crit","Critical"
    if v>=w: return "p-warn","Warning"
    return "p-ok","Online"

def mbar(v, color):
    return f"<div class='mb'><div class='mf' style='width:{min(v,100):.0f}%;background:{color};'></div></div>"

CHART = dict(
    plot_bgcolor="#1c1c1e", paper_bgcolor="#2c2c2e", font_color="#f2f2f7",
    xaxis=dict(gridcolor="#3a3a3c", tickfont=dict(size=12, color="#e5e5ea"), title_font=dict(color="#f2f2f7", size=13)),
    yaxis=dict(gridcolor="#3a3a3c", tickfont=dict(size=12, color="#e5e5ea"), title_font=dict(color="#f2f2f7", size=13)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=13, color="#f2f2f7")),
    title_font=dict(size=15, color="#f2f2f7", family="Inter"),
    margin=dict(l=12,r=12,t=44,b=12),
    hoverlabel=dict(bgcolor="#3a3a3c", font_size=13, font_family="JetBrains Mono", font_color="#f2f2f7"),
)

# ══════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════
m1h   = qry("SELECT * FROM metrics WHERE timestamp>datetime('now','-1 hour') ORDER BY timestamp DESC")
m6h   = qry("SELECT * FROM metrics WHERE timestamp>datetime('now','-6 hours') ORDER BY timestamp")
m24h  = qry("SELECT * FROM metrics WHERE timestamp>datetime('now','-24 hours') ORDER BY timestamp")
msrv  = qry("SELECT m.* FROM metrics m INNER JOIN (SELECT server_name,MAX(timestamp) mt FROM metrics GROUP BY server_name) l ON m.server_name=l.server_name AND m.timestamp=l.mt")
inc   = qry("SELECT * FROM incidents ORDER BY start_time DESC LIMIT 150")
pred  = qry("SELECT * FROM predictions WHERE timestamp>datetime('now','-2 hours') ORDER BY confidence DESC")
evraw = qry("SELECT * FROM events WHERE timestamp>datetime('now','-1 hour') ORDER BY timestamp DESC LIMIT 300")
evagg = qry("SELECT severity,COUNT(*) cnt FROM events WHERE timestamp>datetime('now','-1 hour') GROUP BY severity")
ev24h = qry("SELECT strftime('%H',timestamp) hr,severity,COUNT(*) cnt FROM events WHERE timestamp>datetime('now','-24 hours') GROUP BY hr,severity")
http  = qry("SELECT * FROM http_metrics WHERE timestamp>datetime('now','-1 hour') ORDER BY timestamp DESC")
# SLA data: per-server uptime in 24h (segments of 5min)
sla_raw = qry("SELECT server_name,strftime('%Y-%m-%dT%H:%M',timestamp,'start of minute','-' || (strftime('%M',timestamp)%5) || ' minutes') bucket,AVG(cpu_percent) cpu,AVG(memory_percent) mem FROM metrics WHERE timestamp>datetime('now','-24 hours') GROUP BY server_name,bucket ORDER BY bucket")

for df,col in [(m1h,"timestamp"),(m6h,"timestamp"),(m24h,"timestamp"),(msrv,"timestamp"),
               (inc,"start_time"),(pred,"timestamp"),(evraw,"timestamp"),(http,"timestamp"),(sla_raw,"bucket")]:
    to_ist(df, col)

# ── derived ──
all_servers = sorted(m6h["server_name"].unique().tolist()) if not m6h.empty else []
tot_srv   = len(msrv) if not msrv.empty else 0
open_inc  = (len(inc[inc["status"]=="open"]) if not inc.empty and "status" in inc.columns else 0)
hi_pred   = (len(pred[pred["confidence"]>0.75]) if not pred.empty else 0)
crit_ev   = int(evagg[evagg["severity"]=="critical"]["cnt"].sum()) if not evagg.empty else 0
avg_cpu   = msrv["cpu_percent"].mean()   if not msrv.empty else 0
avg_mem   = msrv["memory_percent"].mean()if not msrv.empty else 0
avg_disk  = msrv["disk_percent"].mean()  if not msrv.empty else 0
avg_cpu24 = m24h["cpu_percent"].mean()   if not m24h.empty else avg_cpu
avg_mem24 = m24h["memory_percent"].mean()if not m24h.empty else avg_mem
evt_1h    = int(evagg["cnt"].sum())      if not evagg.empty else 0

def health():
    s=100
    if not msrv.empty:
        if avg_cpu>95:s-=25
        elif avg_cpu>80:s-=10
        if avg_mem>95:s-=25
        elif avg_mem>85:s-=10
        if avg_disk>98:s-=20
        elif avg_disk>90:s-=8
    s-=min(open_inc*15,30)
    s-=min(hi_pred*10,20)
    return max(0,s)

H=health(); HC="#ef4444" if H<50 else "#f59e0b" if H<75 else "#10b981"
HL="CRITICAL" if H<50 else "DEGRADED" if H<75 else "HEALTHY"

def dlt(now,prev):
    d=now-prev
    if abs(d)<0.5: return "<span class='df'>→ stable</span>"
    return f"<span class='{'du' if d>0 else 'dd'}'>{'▲' if d>0 else '▼'} {abs(d):.1f}% vs 24h</span>"

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center;padding:12px 0 16px;border-bottom:1px solid #0d1e3a;margin-bottom:13px;'>
      <div style='font-family:JetBrains Mono,monospace;font-size:.56rem;text-transform:uppercase;
           letter-spacing:.15em;color:#1e3a5f;margin-bottom:6px;'>System Health</div>
      <div style='font-family:JetBrains Mono,monospace;font-size:2.8rem;font-weight:700;
           color:{HC};line-height:1;'>{H}</div>
      <div style='font-family:JetBrains Mono,monospace;font-size:.6rem;color:{HC};
           margin-top:2px;letter-spacing:.1em;'>{HL}</div>
    </div>""", unsafe_allow_html=True)

    for lbl,val,clr in [("Servers Online",tot_srv,"#10b981"),
                         ("Active Incidents",open_inc,"#ef4444" if open_inc else "#10b981"),
                         ("High-Risk Predictions",hi_pred,"#f59e0b" if hi_pred else "#10b981"),
                         ("Critical Events (1h)",crit_ev,"#ef4444" if crit_ev else "#10b981")]:
        st.markdown(f"""
        <div style='display:flex;justify-content:space-between;align-items:center;
             padding:6px 9px;background:#091525;border:1px solid #0d1e3a;
             border-radius:6px;margin-bottom:4px;'>
          <span style='font-size:.68rem;color:#334155;'>{lbl}</span>
          <span style='font-family:JetBrains Mono,monospace;font-size:.82rem;font-weight:700;color:{clr};'>{val}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:.56rem;text-transform:uppercase;letter-spacing:.1em;color:#1e3a5f;margin-bottom:6px;font-weight:700;'>Navigate</div>", unsafe_allow_html=True)
    for anchor,icon,label in [("#overview","📊","Overview"),("#servers","🖥️","Servers"),
        ("#resources","📈","Resources"),("#sla","🟢","Uptime / SLA"),
        ("#incidents","🚨","Incidents"),("#predictions","🔮","Predictions"),
        ("#logs","📋","Live Logs"),("#http","🌐","HTTP/API"),("#events","📊","Events")]:
        st.markdown(f"""
        <a href='{anchor}' style='display:block;font-size:.71rem;color:#334155;
           padding:5px 9px;border-radius:5px;text-decoration:none;margin-bottom:2px;'>
           {icon} {label}</a>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='margin-top:18px;padding-top:12px;border-top:1px solid #0d1e3a;
         font-family:JetBrains Mono,monospace;font-size:.58rem;color:#1e3a5f;text-align:center;'>
      🔄 refresh 10s &nbsp;·&nbsp; {datetime.now().strftime('%H:%M:%S')} IST
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# STICKY NAV
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class='top-nav'><div class='nav-links'>
  <a class='nav-link' href='#overview'>Overview</a>
  <a class='nav-link' href='#servers'>Servers</a>
  <a class='nav-link' href='#resources'>Resources</a>
  <a class='nav-link' href='#sla'>Uptime/SLA</a>
  <a class='nav-link' href='#incidents'>Incidents</a>
  <a class='nav-link' href='#predictions'>Predictions</a>
  <a class='nav-link' href='#logs'>Live Logs</a>
  <a class='nav-link' href='#http'>HTTP/API</a>
  <a class='nav-link' href='#events'>Events</a>
</div></div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# PAGE HEADER
# ══════════════════════════════════════════════════════════════
hA,hB=st.columns([4,1])
with hA:
    st.markdown("""
    <div style='font-family:Inter,sans-serif;font-size:1.5rem;font-weight:800;
         background:linear-gradient(135deg,#60a5fa,#06b6d4,#818cf8);
         -webkit-background-clip:text;-webkit-text-fill-color:transparent;
         letter-spacing:-.02em;margin-bottom:1px;'>⬡ Enterprise Monitoring Platform</div>
    <div style='font-size:.7rem;color:#1e3a5f;font-family:JetBrains Mono,monospace;'>
      Real-time infrastructure observability &nbsp;·&nbsp; All times in IST
    </div>""", unsafe_allow_html=True)
with hB:
    st.markdown(f"""
    <div style='text-align:right;'>
      <div style='font-family:JetBrains Mono,monospace;font-size:.6rem;color:#1e3a5f;'>LAST UPDATED</div>
      <div style='font-family:JetBrains Mono,monospace;font-size:.8rem;color:#60a5fa;font-weight:700;'>
        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST</div>
    </div>""", unsafe_allow_html=True)

# alert banners
if not inc.empty and "status" in inc.columns and "severity" in inc.columns:
    for _,i in inc[(inc["status"]=="open")&(inc["severity"]=="critical")].head(2).iterrows():
        st.markdown(f"""
        <div class='alert a-crit'>🚨 <strong>CRITICAL:</strong> {i.get('incident_id','?')} —
          {str(i.get('incident_type','?')).replace('_',' ').title()}
          &nbsp;|&nbsp; {str(i.get('start_time','—'))[:19]} IST</div>""", unsafe_allow_html=True)
if not pred.empty:
    hp=pred[pred["confidence"]>0.85]
    if not hp.empty:
        p=hp.iloc[0]
        st.markdown(f"""
        <div class='alert a-warn'>⚠️ <strong>HIGH-RISK:</strong>
          {p.get('predicted_issue','?')} on {p.get('server_name','?')}
          &nbsp;|&nbsp; {p.get('confidence',0)*100:.0f}% conf
          &nbsp;|&nbsp; ETA {p.get('time_to_failure_minutes','?')} min</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# §01  OVERVIEW KPI CARDS
# ══════════════════════════════════════════════════════════════
st.markdown('<div id="overview"></div>', unsafe_allow_html=True)
st.markdown('<div class="sh"><span class="num">01</span> Overview — Key Metrics</div>', unsafe_allow_html=True)

kpis=[
  ("🖥️ Servers",    str(tot_srv),       "",                    "#10b981","#10b981,#06b6d4"),
  ("⚡ Avg CPU",    f"{avg_cpu:.1f}%",   dlt(avg_cpu,avg_cpu24),pc(avg_cpu,80,95),   f"{pc(avg_cpu,80,95)},#0d1e3a"),
  ("🧠 Avg Memory", f"{avg_mem:.1f}%",   dlt(avg_mem,avg_mem24),pc(avg_mem,85,95),   f"{pc(avg_mem,85,95)},#0d1e3a"),
  ("💾 Avg Disk",   f"{avg_disk:.1f}%",  "",                    pc(avg_disk,90,98),  "#60a5fa,#3b82f6"),
  ("🚨 Incidents",  str(open_inc),       "",                    "#ef4444" if open_inc else "#10b981","#ef4444,#f97316" if open_inc else "#10b981,#06b6d4"),
  ("🔮 Predictions",str(hi_pred),        "",                    "#f59e0b" if hi_pred else "#10b981","#f59e0b,#eab308" if hi_pred else "#10b981,#06b6d4"),
  ("📋 Events (1h)",str(evt_1h),         "",                    "#60a5fa","#3b82f6,#818cf8"),
  ("🏥 Health",     str(H),              HL,                    HC,                  f"{HC},#0d1e3a"),
]
for col,(lbl,val,sub,vc,grad) in zip(st.columns(8), kpis):
    with col:
        st.markdown(f"""
        <div class='kpi'>
          <div class='bar' style='background:linear-gradient(90deg,{grad});'></div>
          <div class='kpi-lbl'>{lbl}</div>
          <div class='kpi-val' style='color:{vc};'>{val}</div>
          <div class='kpi-sub'>{sub}</div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# §02  MULTI-SERVER PANEL
# ══════════════════════════════════════════════════════════════
st.markdown('<div id="servers"></div>', unsafe_allow_html=True)
st.markdown('<div class="sh"><span class="num">02</span> Multi-Server Infrastructure</div>', unsafe_allow_html=True)

if not msrv.empty:
    crit_c=sum(1 for _,r in msrv.iterrows() if r.get("cpu_percent",0)>=95 or r.get("memory_percent",0)>=95)
    warn_c=sum(1 for _,r in msrv.iterrows() if (r.get("cpu_percent",0)>=80 or r.get("memory_percent",0)>=85) and not(r.get("cpu_percent",0)>=95 or r.get("memory_percent",0)>=95))
    ok_c  =tot_srv-crit_c-warn_c
    for col,(lbl,v,clr) in zip(st.columns(4),[("Total",tot_srv,"#60a5fa"),("Healthy",ok_c,"#10b981"),("Warning",warn_c,"#f59e0b"),("Critical",crit_c,"#ef4444")]):
        with col:
            st.markdown(f"""
            <div style='background:#091525;border:1px solid #0d1e3a;border-radius:8px;
                 padding:10px 14px;display:flex;justify-content:space-between;align-items:center;'>
              <span style='font-size:.68rem;color:#334155;'>{lbl}</span>
              <span style='font-family:JetBrains Mono,monospace;font-size:1.1rem;font-weight:700;color:{clr};'>{v}</span>
            </div>""", unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    rows=""
    for _,row in msrv.iterrows():
        cpu=row.get("cpu_percent",0) or 0; mem=row.get("memory_percent",0) or 0; dsk=row.get("disk_percent",0) or 0
        ts=row.get("timestamp","—"); ts_s=ts.strftime("%H:%M:%S") if hasattr(ts,"strftime") else str(ts)[:19]
        pc_cls,pc_lbl=pill_cls(max(cpu,mem*0.9,dsk*0.85),80,95)
        cc=pc(cpu,80,95); mc=pc(mem,85,95); dc=pc(dsk,90,98)
        rows+=f"""
        <tr style='border-bottom:1px solid rgba(13,30,58,.5);transition:background .12s;'>
          <td style='padding:9px 13px;font-family:JetBrains Mono,monospace;font-size:.73rem;color:#e2e8f0;font-weight:600;'>{row.get('server_name','—')}</td>
          <td style='padding:9px 13px;'>
            <div style='font-family:JetBrains Mono,monospace;font-size:.68rem;color:#475569;'>{row.get('hostname','—')}</div>
            <div style='font-family:JetBrains Mono,monospace;font-size:.64rem;color:#3b82f6;'>{row.get('ip_address','—')}</div>
          </td>
          <td style='padding:9px 13px;'><span class='pill {pc_cls}'>{pc_lbl}</span></td>
          <td style='padding:9px 13px;font-family:JetBrains Mono,monospace;font-size:.73rem;'>
            <span style='color:{cc};font-weight:600;'>{cpu:.1f}%</span>
            <div style='background:#0d1e3a;border-radius:3px;height:3px;margin-top:3px;width:68px;overflow:hidden;'>
              <div style='width:{min(cpu,100):.0f}%;height:100%;border-radius:3px;background:{cc};'></div></div>
          </td>
          <td style='padding:9px 13px;font-family:JetBrains Mono,monospace;font-size:.73rem;'>
            <span style='color:{mc};font-weight:600;'>{mem:.1f}%</span>
            <div style='background:#0d1e3a;border-radius:3px;height:3px;margin-top:3px;width:68px;overflow:hidden;'>
              <div style='width:{min(mem,100):.0f}%;height:100%;border-radius:3px;background:{mc};'></div></div>
          </td>
          <td style='padding:9px 13px;font-family:JetBrains Mono,monospace;font-size:.73rem;'>
            <span style='color:{dc};font-weight:600;'>{dsk:.1f}%</span>
            <div style='background:#0d1e3a;border-radius:3px;height:3px;margin-top:3px;width:68px;overflow:hidden;'>
              <div style='width:{min(dsk,100):.0f}%;height:100%;border-radius:3px;background:{dc};'></div></div>
          </td>
          <td style='padding:9px 13px;font-family:JetBrains Mono,monospace;font-size:.66rem;color:#1e3a5f;'>{ts_s}</td>
        </tr>"""
    st.markdown(f"""
    <div style='background:#091525;border:1px solid #0d1e3a;border-radius:10px;overflow:hidden;'>
      <table style='width:100%;border-collapse:collapse;'>
        <thead>
          <tr style='background:#060b14;border-bottom:1px solid #0d1e3a;'>
            <th style='padding:7px 13px;font-size:.57rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#1e3a5f;text-align:left;'>SERVER</th>
            <th style='padding:7px 13px;font-size:.57rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#1e3a5f;text-align:left;'>HOSTNAME / IP</th>
            <th style='padding:7px 13px;font-size:.57rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#1e3a5f;text-align:left;'>STATUS</th>
            <th style='padding:7px 13px;font-size:.57rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#1e3a5f;text-align:left;'>CPU</th>
            <th style='padding:7px 13px;font-size:.57rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#1e3a5f;text-align:left;'>MEMORY</th>
            <th style='padding:7px 13px;font-size:.57rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#1e3a5f;text-align:left;'>DISK</th>
            <th style='padding:7px 13px;font-size:.57rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#1e3a5f;text-align:left;'>LAST SEEN (IST)</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)
else:
    st.info("No server data available")

# ══════════════════════════════════════════════════════════════
# §03  RESOURCE MONITOR
# ══════════════════════════════════════════════════════════════
st.markdown('<div id="resources"></div>', unsafe_allow_html=True)
st.markdown('<div class="sh"><span class="num">03</span> Resource Monitor</div>', unsafe_allow_html=True)

sel=st.multiselect("Servers",all_servers,default=all_servers,label_visibility="collapsed",key="res_sel")
if sel and not m6h.empty:
    flt=m6h[m6h["server_name"].isin(sel)]
    for res,col_n,w,c,icon in [("CPU","cpu_percent",80,95,"⚡"),("Memory","memory_percent",85,95,"🧠"),("Disk","disk_percent",90,98,"💾")]:
        st.markdown(f"<div style='font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#1e3a5f;margin:14px 0 8px;'>{icon} {res}</div>", unsafe_allow_html=True)
        rcols=st.columns(len(sel))
        for i,srv in enumerate(sel):
            sd=flt[flt["server_name"]==srv][col_n]
            if sd.empty: continue
            live=sd.iloc[-1]; mn=sd.min(); mx=sd.max(); avg_v=sd.mean()
            clr=pc(live,w,c)
            with rcols[i]:
                st.markdown(f"""
                <div style='background:#091525;border:1px solid #0d1e3a;border-radius:8px;
                     padding:11px;border-top:2px solid {clr};'>
                  <div style='font-size:.58rem;text-transform:uppercase;letter-spacing:.07em;color:#1e3a5f;
                       margin-bottom:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'
                       title='{srv}'>{srv}</div>
                  <div style='font-family:JetBrains Mono,monospace;font-size:1.5rem;
                       font-weight:700;color:{clr};line-height:1;'>{live:.1f}%</div>
                  <div class='mb' style='width:100%;margin:6px 0 4px;height:4px;'>
                    <div class='mf' style='width:{min(live,100):.0f}%;background:{clr};'></div></div>
                  <div style='font-family:JetBrains Mono,monospace;font-size:.58rem;color:#1e3a5f;
                       display:flex;justify-content:space-between;'>
                    <span>↓{mn:.0f}%</span><span>∼{avg_v:.0f}%</span><span>↑{mx:.0f}%</span>
                  </div>
                </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    t1,t2,t3,t4=st.tabs(["⚡ CPU","🧠 Memory","💾 Disk","📊 Combined"])
    palettes=[["#3b82f6","#06b6d4","#10b981","#a78bfa"],["#a78bfa","#f472b6","#fb923c","#34d399"],["#fb923c","#34d399","#60a5fa","#e879f9"]]
    for tab,(y,title,wl,cl,cs) in zip([t1,t2,t3],[
        ("cpu_percent","CPU (6h)",80,95,palettes[0]),
        ("memory_percent","Memory (6h)",85,95,palettes[1]),
        ("disk_percent","Disk (6h)",90,98,palettes[2])]):
        with tab:
            fig=px.line(flt,x="timestamp",y=y,color="server_name",title=title,color_discrete_sequence=cs,
                labels={y:y.split('_')[0].title()+" %","timestamp":"Time (IST)","server_name":"Server"})
            fig.add_hline(y=wl,line_dash="dot",line_color="#f59e0b",annotation_font_size=10)
            fig.add_hline(y=cl,line_dash="dot",line_color="#ef4444",annotation_font_size=10)
            fig.update_layout(**CHART); st.plotly_chart(fig,use_container_width=True)
    with t4:
        slist=sel[:4]
        if slist:
            fig=make_subplots(rows=len(slist),cols=3,
                subplot_titles=[f"{s} — {r}" for s in slist for r in ["CPU","MEM","DISK"]],
                shared_xaxes=True,vertical_spacing=.06,horizontal_spacing=.04)
            pals=[("#3b82f6","#a78bfa","#fb923c"),("#06b6d4","#f472b6","#34d399"),("#10b981","#e879f9","#60a5fa"),("#60a5fa","#fbbf24","#f87171")]
            for ri,srv in enumerate(slist,1):
                sd=flt[flt["server_name"]==srv].sort_values("timestamp")
                for ci,(cn,clr) in enumerate(zip(["cpu_percent","memory_percent","disk_percent"],pals[ri-1]),1):
                    fig.add_trace(go.Scatter(x=sd["timestamp"],y=sd[cn],mode="lines",line=dict(color=clr,width=1.5),showlegend=False),row=ri,col=ci)
            fig.update_layout(height=200*len(slist),showlegend=False,
                plot_bgcolor="#1c1c1e",paper_bgcolor="#2c2c2e",font_color="#f2f2f7",margin=dict(l=8,r=8,t=30,b=8))
            st.plotly_chart(fig,use_container_width=True)
    if not m24h.empty:
        s24=m24h[m24h["server_name"].isin(sel)].groupby("server_name").agg(
            CPU_Min=("cpu_percent","min"),CPU_Avg=("cpu_percent","mean"),CPU_Max=("cpu_percent","max"),
            RAM_Min=("memory_percent","min"),RAM_Avg=("memory_percent","mean"),RAM_Max=("memory_percent","max"),
            Disk_Min=("disk_percent","min"),Disk_Avg=("disk_percent","mean"),Disk_Max=("disk_percent","max"),
        ).round(1).reset_index().rename(columns={"server_name":"Server"})
        st.markdown("##### 📋 24h Resource Statistics")
        st.dataframe(s24,use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════════
# §04  UPTIME / SLA  ← NEW FEATURE
# ══════════════════════════════════════════════════════════════
st.markdown('<div id="sla"></div>', unsafe_allow_html=True)
st.markdown('<div class="sh"><span class="num">04</span> Uptime & SLA (24h)</div>', unsafe_allow_html=True)

if not sla_raw.empty and "server_name" in sla_raw.columns:
    sla_cols = st.columns(len(all_servers) if all_servers else 1)
    for i,srv in enumerate(all_servers[:6]):
        sd = sla_raw[sla_raw["server_name"]==srv].copy()
        if sd.empty: continue
        # compute uptime: bucket is "up" if cpu<95 and mem<95
        sd["up"] = ((sd["cpu"]<95)&(sd["mem"]<95)).astype(int)
        uptime_pct = sd["up"].mean()*100 if not sd.empty else 100
        sla_clr = "#ef4444" if uptime_pct<95 else "#f59e0b" if uptime_pct<99 else "#10b981"
        # build 288 slot bar (5min × 288 = 24h), color per slot
        segs = ""
        for _,row in sd.tail(48).iterrows():  # last 48 slots = 4h visual
            clr = "#10b981" if row["up"] else "#ef4444"
            bucket_label = str(row.get("bucket",""))[:16]
            segs += f"<div class='upt-seg' style='background:{clr};' title='{bucket_label}'></div>"
        with sla_cols[i % len(sla_cols)]:
            st.markdown(f"""
            <div class='upt-wrap'>
              <div style='font-size:.6rem;text-transform:uppercase;letter-spacing:.08em;
                   color:#1e3a5f;margin-bottom:4px;overflow:hidden;text-overflow:ellipsis;
                   white-space:nowrap;' title='{srv}'>{srv}</div>
              <div style='font-family:JetBrains Mono,monospace;font-size:1.5rem;
                   font-weight:700;color:{sla_clr};line-height:1;'>{uptime_pct:.2f}%</div>
              <div style='font-size:.56rem;color:#1e3a5f;margin-bottom:3px;'>uptime (24h)</div>
              <div class='upt-bar'>{segs if segs else "<div style='font-size:.6rem;color:#1e3a5f;'>no data</div>"}</div>
              <div style='font-family:JetBrains Mono,monospace;font-size:.54rem;color:#1e3a5f;
                   display:flex;justify-content:space-between;margin-top:2px;'>
                <span>-4h</span><span>now</span></div>
            </div>""", unsafe_allow_html=True)
    # SLA summary table
    sla_summary = []
    for srv in all_servers:
        sd=sla_raw[sla_raw["server_name"]==srv].copy()
        if sd.empty: continue
        sd["up"]=((sd["cpu"]<95)&(sd["mem"]<95)).astype(int)
        up_pct=sd["up"].mean()*100
        total_min=len(sd)*5
        down_min=int((1-sd["up"].mean())*total_min)
        sla_summary.append({"Server":srv,"Uptime %":round(up_pct,3),"Down (min)":down_min,"Samples":len(sd),"SLA":("✅ Met" if up_pct>=99 else "⚠️ At Risk" if up_pct>=95 else "❌ Breached")})
    if sla_summary:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(sla_summary),use_container_width=True,hide_index=True)
else:
    st.info("No uptime data available yet")

# ══════════════════════════════════════════════════════════════
# §05  ACTIVE INCIDENTS  — redesigned scrollable panel
# ══════════════════════════════════════════════════════════════
st.markdown('<div id="incidents"></div>', unsafe_allow_html=True)
st.markdown('<div class="sh"><span class="num">05</span> Active Incidents</div>', unsafe_allow_html=True)

def duration_str(start_ts):
    """Return human-readable duration since start_ts."""
    try:
        now_ts = datetime.now(tz=start_ts.tzinfo)
        diff   = now_ts - start_ts
        mins   = int(diff.total_seconds()//60)
        if mins < 60: return f"{mins}m"
        h,m    = divmod(mins,60)
        return f"{h}h {m}m"
    except:
        return "—"

def render_inc_panel(df, show_scroll=True):
    if df.empty:
        st.markdown("<div class='inc-list-empty'>✅ No incidents in this category</div>", unsafe_allow_html=True)
        return

    cards=""
    for _,row in df.iterrows():
        sev      = str(row.get("severity","info")).lower()
        inc_id   = row.get("incident_id","—")
        inc_type = str(row.get("incident_type","Unknown")).replace("_"," ").title()
        root     = str(row.get("root_cause","—"))[:250]
        solution = str(row.get("solution","—"))[:300]
        summary  = str(row.get("summary","—"))[:250]
        servers  = row.get("affected_servers","—")
        if isinstance(servers,str) and servers.startswith("["):
            try: servers=", ".join(json.loads(servers))
            except: pass
        start    = row.get("start_time","—")
        start_s  = start.strftime("%d %b %H:%M") if hasattr(start,"strftime") else str(start)[:16]
        dur      = duration_str(start) if hasattr(start,"tzinfo") else "—"
        status   = str(row.get("status","—")).upper()

        icon  = {"critical":"🔴","error":"🟠","warning":"🟡"}.get(sev,"🔵")
        ccls  = {"critical":"c-crit","error":"c-err","warning":"c-warn"}.get(sev,"")
        bcls  = {"critical":"b-crit","error":"b-err","warning":"b-warn"}.get(sev,"b-info")
        sev_u = sev.upper()

        cards += f"""
        <div class='ic {ccls}'>
          <div class='ic-hdr'>
            <span class='ic-icon'>{icon}</span>
            <div class='ic-meta-left'>
              <div class='ic-id'>{inc_id}</div>
              <div class='ic-type'>{inc_type}</div>
            </div>
            <div class='ic-badges'>
              <span class='sev-b {bcls}'>{sev_u}</span>
              <span class='dur-b'>⏱ {dur}</span>
            </div>
          </div>
          <div class='ic-body'>
            <div class='ic-field full'>
              <div class='ifl'>🔍 Root Cause</div>
              <div class='ifv highlight'>{root}</div>
            </div>
            <div class='ic-field'>
              <div class='ifl'>📋 Summary</div>
              <div class='ifv' style='max-height:52px;overflow:hidden;'>{summary}</div>
            </div>
            <div class='ic-field'>
              <div class='ifl'>🛠️ Action</div>
              <div class='ifv' style='max-height:52px;overflow:hidden;'>{solution}</div>
            </div>
          </div>
          <div class='ic-foot'>
            <div>📅 <span>{start_s} IST</span></div>
            <div>🖥️ <span>{servers}</span></div>
            <div>📌 <span>{status}</span></div>
          </div>
        </div>"""

    wrap = "inc-list" if show_scroll else "inc-list-noscroll"
    st.markdown(f"<div class='{wrap}'>{cards}</div>", unsafe_allow_html=True)

if not inc.empty and "status" in inc.columns:
    open_df   = inc[inc["status"]=="open"]
    closed_df = inc[inc["status"]!="open"]

    # Toolbar summary
    c_c=len(open_df[open_df["severity"]=="critical"]) if "severity" in open_df.columns else 0
    c_w=len(open_df[open_df["severity"]=="warning"])  if "severity" in open_df.columns else 0
    c_e=len(open_df[open_df["severity"]=="error"])    if "severity" in open_df.columns else 0

    st.markdown(f"""
    <div class='inc-panel'>
      <div class='inc-toolbar'>
        <span style='font-size:.68rem;font-weight:700;color:#475569;'>OPEN INCIDENTS</span>
        <span class='inc-count-badge badge-crit'>{c_c} Critical</span>
        <span class='inc-count-badge badge-warn' style='background:#1c0d03;color:#f97316;border-color:rgba(249,115,22,.3);'>{c_e} Error</span>
        <span class='inc-count-badge badge-warn'>{c_w} Warning</span>
        <span style='margin-left:auto;font-family:JetBrains Mono,monospace;font-size:.6rem;color:#1e3a5f;'>
          scroll to see all &nbsp;↓</span>
      </div>
    """, unsafe_allow_html=True)
    render_inc_panel(open_df)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander(f"✅ Resolved Incidents ({len(closed_df)})", expanded=False):
        render_inc_panel(closed_df.head(10), show_scroll=False)
else:
    st.markdown("<div class='inc-panel'><div class='inc-list-empty'>✅ No active incidents</div></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# §06  PREDICTIONS
# ══════════════════════════════════════════════════════════════
st.markdown('<div id="predictions"></div>', unsafe_allow_html=True)
st.markdown('<div class="sh"><span class="num">06</span> Failure Predictions (Next 2 Hours)</div>', unsafe_allow_html=True)

if not pred.empty:
    for _,p in pred.head(8).iterrows():
        conf=p.get("confidence",0)*100; ttf=p.get("time_to_failure_minutes",0)
        rc="#ef4444" if conf>75 else "#f59e0b" if conf>50 else "#10b981"
        ts_p=str(p.get("timestamp",""))[:19]
        st.markdown(f"""
        <div class='pred'>
          <div class='ring' style='border-color:{rc};color:{rc};'>
            <div class='rv'>{conf:.0f}%</div><div class='rl'>CONF</div>
          </div>
          <div class='pb'>
            <div class='pi'>{p.get('predicted_issue','Unknown')}</div>
            <div class='pm'>🖥️ {p.get('server_name','—')} &nbsp;|&nbsp;
              🏷️ {str(p.get('prediction_type','—')).replace('_',' ').title()} &nbsp;|&nbsp;
              🕐 {ts_p} IST</div>
            <div class='pr'>{str(p.get('recommendation','—'))[:190]}</div>
          </div>
          <div class='ttf'>⏳ {ttf} min</div>
        </div>""", unsafe_allow_html=True)
else:
    st.markdown("<div style='text-align:center;padding:22px;background:#091525;border:1px dashed #0d1e3a;border-radius:9px;color:#10b981;'>✅ No imminent failures predicted</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# §07  LIVE EVENT LOG VIEWER  ← improved with search
# ══════════════════════════════════════════════════════════════
st.markdown('<div id="logs"></div>', unsafe_allow_html=True)
st.markdown('<div class="sh"><span class="num">07</span> Live Event Log Viewer</div>', unsafe_allow_html=True)

lA,lB=st.columns([3,1])
with lB:
    sev_f=st.multiselect("Severity",["critical","error","warning","info"],default=["critical","error","warning"],key="lsev")
    srv_f=st.multiselect("Server",all_servers,default=all_servers,key="lsrv")
    search_kw=st.text_input("Search message","",placeholder="keyword…",key="lsrch")
with lA:
    if not evraw.empty:
        fl=evraw.copy()
        if sev_f: fl=fl[fl["severity"].isin(sev_f)]
        if srv_f: fl=fl[fl["server_name"].isin(srv_f)]
        if search_kw: fl=fl[fl["message"].str.contains(search_kw,case=False,na=False)]
        lh="<div class='logv'>"
        for _,ev in fl.head(150).iterrows():
            sev=str(ev.get("severity","info")).lower()
            ts=str(ev.get("timestamp",""))[:19]
            src=str(ev.get("source",""))[:10]
            msg=str(ev.get("message",""))[:140]
            srv=str(ev.get("server_name",""))[:16]
            sc={"critical":"lc-c","error":"lc-e","warning":"lc-w","info":"lc-i"}.get(sev,"lc-i")
            lh+=f"<div class='ll'><span class='lts'>{ts}</span><span class='lc {sc}'>[{sev[:4].upper()}]</span><span class='lsrv'>{src}</span><span style='color:#0d1e3a;margin-right:4px;font-size:.65rem;'>{srv}</span><span class='lm'>{msg}</span></div>"
        lh+="</div>"
        st.markdown(lh,unsafe_allow_html=True)
        st.caption(f"Showing {min(len(fl),150)} / {len(fl)} events · last 1h · all times IST")
    else:
        st.info("No events in the last hour")

# ══════════════════════════════════════════════════════════════
# §08  HTTP / API MONITOR
# ══════════════════════════════════════════════════════════════
st.markdown('<div id="http"></div>', unsafe_allow_html=True)
st.markdown('<div class="sh"><span class="num">08</span> HTTP / API Response Monitor</div>', unsafe_allow_html=True)

if not http.empty and "response_time_ms" in http.columns:
    tot=len(http); suc=(http["is_success"].sum()/tot*100) if tot else 0
    avrt=http["response_time_ms"].mean(); mnrt=http["response_time_ms"].min()
    mxrt=http["response_time_ms"].max(); p95=http["response_time_ms"].quantile(.95)
    errs=int((http["is_success"]==0).sum())

    hk=[("📊 Requests",f"{tot:,}","#60a5fa","#3b82f6,#818cf8"),
        ("✅ Success",f"{suc:.1f}%",pc(100-suc,5,10),"#10b981,#06b6d4"),
        ("⚡ Avg RT",f"{avrt:.0f}ms",pc(avrt,200,500),"#3b82f6,#06b6d4"),
        ("📈 P95 RT",f"{p95:.0f}ms",pc(p95,500,1000),"#a78bfa,#818cf8"),
        ("↓ Min",f"{mnrt:.0f}ms","#10b981","#10b981,#06b6d4"),
        ("↑ Max",f"{mxrt:.0f}ms",pc(mxrt,500,1000),"#fb923c,#ef4444"),
        ("❌ Errors",f"{errs:,}","#ef4444" if errs else "#10b981","#ef4444,#f97316" if errs else "#10b981,#06b6d4")]
    for col,(lbl,val,vc,grad) in zip(st.columns(7),hk):
        with col:
            st.markdown(f"""
            <div class='kpi'>
              <div class='bar' style='background:linear-gradient(90deg,{grad});'></div>
              <div class='kpi-lbl'>{lbl}</div>
              <div class='kpi-val' style='font-size:1.3rem;color:{vc};'>{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:9px'></div>", unsafe_allow_html=True)
    hc1,hc2=st.columns(2)
    with hc1:
        ht=http.copy(); ht["bucket"]=ht["timestamp"].dt.floor("5min")
        ha=ht.groupby("bucket").agg(avg=("response_time_ms","mean"),mn=("response_time_ms","min"),mx=("response_time_ms","max")).reset_index()
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=ha["bucket"],y=ha["mx"],fill=None,mode="lines",line=dict(color="rgba(239,68,68,.2)",width=1),name="Max"))
        fig.add_trace(go.Scatter(x=ha["bucket"],y=ha["avg"],fill="tonexty",mode="lines",line=dict(color="#3b82f6",width=2),fillcolor="rgba(59,130,246,.06)",name="Avg"))
        fig.add_trace(go.Scatter(x=ha["bucket"],y=ha["mn"],fill="tonexty",mode="lines",line=dict(color="#10b981",width=1),fillcolor="rgba(16,185,129,.04)",name="Min"))
        fig.add_hline(y=500,line_dash="dot",line_color="#ef4444")
        fig.add_hline(y=200,line_dash="dot",line_color="#f59e0b")
        fig.update_layout(title="Response Time Min/Avg/Max (5min bins)",**CHART)
        st.plotly_chart(fig,use_container_width=True)
    with hc2:
        if "status_code" in http.columns:
            sc=http["status_code"].value_counts().reset_index(); sc.columns=["code","count"]; sc["code"]=sc["code"].astype(str)
            cmap={"200":"#10b981","201":"#34d399","301":"#60a5fa","302":"#a78bfa","400":"#f59e0b","401":"#fb923c","403":"#f97316","404":"#ef4444","500":"#dc2626","503":"#991b1b"}
            fig=go.Figure(go.Bar(x=sc["code"],y=sc["count"],marker_color=[cmap.get(c,"#334155") for c in sc["code"]],text=sc["count"],textposition="auto",textfont=dict(family="JetBrains Mono",color="#e2e8f0",size=11)))
            fig.update_layout(title="HTTP Status Distribution",**CHART)
            st.plotly_chart(fig,use_container_width=True)
    if "endpoint" in http.columns:
        st.markdown("##### 🏆 Top 10 Endpoints")
        ep=http.groupby("endpoint").agg(Requests=("endpoint","count"),Avg_ms=("response_time_ms","mean"),
            Min_ms=("response_time_ms","min"),Max_ms=("response_time_ms","max"),
            P95_ms=("response_time_ms",lambda x:np.percentile(x,95)),
            Success=("is_success","mean"),Errors=("is_success",lambda x:(x==0).sum()),
        ).reset_index().sort_values("Requests",ascending=False).head(10)
        ep["Success"]=(ep["Success"]*100).round(1)
        for c in ["Avg_ms","Min_ms","Max_ms","P95_ms"]: ep[c]=ep[c].round(0).astype(int)
        ep.index=range(1,len(ep)+1)
        st.dataframe(ep.rename(columns={"endpoint":"Endpoint","Avg_ms":"Avg(ms)","Min_ms":"Min(ms)","Max_ms":"Max(ms)","P95_ms":"P95(ms)","Success":"Success%"}),use_container_width=True)
else:
    st.markdown("<div style='text-align:center;padding:26px;background:#091525;border:1px dashed #0d1e3a;border-radius:9px;color:#1e3a5f;'>🌐 No HTTP metrics. Configure IIS/Tomcat log collection in config.py.</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# §09  EVENT STATS + HEATMAP + TIMELINE  ← new timeline chart
# ══════════════════════════════════════════════════════════════
st.markdown('<div id="events"></div>', unsafe_allow_html=True)
st.markdown('<div class="sh"><span class="num">09</span> Event Statistics & Analysis</div>', unsafe_allow_html=True)

ev1,ev2,ev3=st.columns(3)
with ev1:
    if not evagg.empty:
        cmap={"critical":"#ef4444","error":"#f97316","warning":"#f59e0b","info":"#3b82f6"}
        fig=go.Figure(go.Bar(x=evagg["severity"],y=evagg["cnt"],
            marker_color=[cmap.get(s,"#334155") for s in evagg["severity"]],
            text=evagg["cnt"],textposition="auto",textfont=dict(family="JetBrains Mono",color="#e2e8f0",size=11)))
        fig.update_layout(title="Events by Severity (1h)",**CHART)
        st.plotly_chart(fig,use_container_width=True)
with ev2:
    if not m1h.empty:
        sc2=m1h.groupby("server_name").size().reset_index(name="count")
        fig=go.Figure(go.Pie(labels=sc2["server_name"],values=sc2["count"],hole=0.55,
            marker=dict(colors=["#3b82f6","#06b6d4","#10b981","#a78bfa"],line=dict(color="#060b14",width=2))))
        fig.update_layout(title="Metrics by Server",paper_bgcolor="#2c2c2e",font_color="#f2f2f7",legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=13, color="#f2f2f7")),margin=dict(l=10,r=10,t=44,b=10))
        st.plotly_chart(fig,use_container_width=True)
with ev3:
    if not ev24h.empty:
        pivot=ev24h.pivot_table(index="severity",columns="hr",values="cnt",aggfunc="sum",fill_value=0)
        fig=go.Figure(go.Heatmap(
            z=pivot.values,x=[f"{h}:00" for h in pivot.columns],y=pivot.index.tolist(),
            colorscale=[[0,"#060b14"],[0.3,"#0d1e3a"],[0.6,"#1e3a5f"],[1,"#ef4444"]],
            showscale=False,text=pivot.values,texttemplate="%{text}",
            textfont=dict(family="JetBrains Mono",size=9,color="#e2e8f0")))
        fig.update_layout(title="Event Heatmap — 24h × Severity",**CHART,xaxis_nticks=12)
        st.plotly_chart(fig,use_container_width=True)
    else:
        st.info("No 24h event data")

# Event timeline (stacked area)
if not ev24h.empty:
    pivot_t=ev24h.pivot_table(index="hr",columns="severity",values="cnt",aggfunc="sum",fill_value=0).reset_index()
    fig=go.Figure()
    sev_colors={"critical":"#ef4444","error":"#f97316","warning":"#f59e0b","info":"#3b82f6"}
    sev_fill  ={"critical":"rgba(239,68,68,0.15)","error":"rgba(249,115,22,0.15)",
                "warning":"rgba(245,158,11,0.15)","info":"rgba(59,130,246,0.15)"}
    for sev_col in [c for c in ["info","warning","error","critical"] if c in pivot_t.columns]:
        fig.add_trace(go.Scatter(
            x=[f"{h}:00" for h in pivot_t["hr"]],
            y=pivot_t[sev_col],
            mode="lines", fill="tozeroy",
            name=sev_col.title(),
            line=dict(color=sev_colors.get(sev_col,"#334155"), width=1.5),
            fillcolor=sev_fill.get(sev_col,"rgba(51,65,85,0.15)")
        ))
    fig.update_layout(title="Event Volume Timeline — 24h by Hour & Severity",**{
        **CHART,
        "legend": dict(orientation="h", y=1.08, bgcolor="rgba(0,0,0,0)", font=dict(size=13, color="#f2f2f7")),
    }, xaxis_title="Hour (IST)", yaxis_title="Event Count", height=280)
    st.plotly_chart(fig,use_container_width=True)

# ══════════════════════════════════════════════════════════════
# FOOTER + BACK TO TOP
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(f"""
<div style='text-align:center;font-family:JetBrains Mono,monospace;font-size:.58rem;color:#0d1e3a;padding:7px 0 3px;'>
  🔄 AUTO-REFRESH 10s &nbsp;·&nbsp; ALL TIMES IN IST &nbsp;·&nbsp; ENTERPRISE MONITORING v4.0
  &nbsp;·&nbsp; {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST
</div>""", unsafe_allow_html=True)

st.markdown("<a href='#overview' class='back-top'>↑ TOP</a>", unsafe_allow_html=True)