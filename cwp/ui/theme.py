"""cwp.ui.theme — feuille de style globale de la plateforme (charte CWP)."""
from __future__ import annotations

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=Share+Tech+Mono&display=swap');
:root{--bg:#050b14;--card:#0a1a2a;--cy:#00d4ff;--gr:#00ff88;--pu:#a855f7;--rd:#ff4d6d;--gold:#f5c542}
.stApp{background:var(--bg);color:#cfe3f5;font-family:'Rajdhani',sans-serif}
[data-testid=stSidebar]{background:#060e1a;border-right:1px solid #12263a}
h1,h2,h3{font-family:'Rajdhani';letter-spacing:.15em;text-transform:uppercase}
h1{color:var(--gr);text-shadow:0 0 14px #00ff8866}
h2,h3{color:var(--cy)}
.brand{font-size:2.6rem;color:var(--gr);text-align:center;letter-spacing:.4em;text-shadow:0 0 18px #00ff88aa;font-weight:700}
.sub{font-family:'Share Tech Mono';font-size:.7rem;color:#3a5870;text-align:center;letter-spacing:.3em;margin-bottom:1rem}
.card{background:linear-gradient(135deg,#0a1f33,#0d1530);border:1px solid #13405e;border-radius:12px;padding:14px 18px;margin-bottom:10px}
.card a{color:var(--cy);text-decoration:none}
.tag{font-family:'Share Tech Mono';font-size:.7rem;padding:2px 8px;border:1px solid var(--pu);color:var(--pu);border-radius:4px;margin-right:8px;white-space:nowrap}
.new{border-color:var(--gr);color:var(--gr)}
.lang{border-color:#52708a;color:#8aa4ba}
.meta{font-family:'Share Tech Mono';font-size:.72rem;color:#52708a}
.meta a{color:#7fa6c4}
.kpi{font-family:'Share Tech Mono';font-size:2rem;color:var(--gr)}
.hero{border:1px solid #f5c54255;border-radius:14px;padding:18px 24px;margin-bottom:14px;background:linear-gradient(90deg,#1a1405,#0a1a2a 65%)}
.hero-t{font-size:2.1rem;font-weight:700;color:var(--gold);letter-spacing:.06em;text-shadow:0 0 14px #f5c54244}
.hero-t span{color:#cfe3f5;font-weight:500;font-size:1.35rem}
.hero-s{font-family:'Share Tech Mono';font-size:.8rem;color:#8aa4ba;letter-spacing:.08em;margin-top:4px}
.wwrap{overflow-x:auto;border:1px solid #13405e;border-radius:12px;background:linear-gradient(135deg,#0a1f33,#0d1530);margin-bottom:8px}
.wtable{width:100%;border-collapse:collapse;font-size:.98rem}
.wtable th{font-family:'Share Tech Mono';font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);text-align:left;padding:11px 12px;border-bottom:1px solid #f5c54266;background:#081626;white-space:nowrap}
.wtable td{padding:10px 12px;border-bottom:1px solid #12263a;vertical-align:top;color:#cfe3f5}
.wtable tr:hover td{background:#0e2238}
.wtable a{color:#e3f1fc;text-decoration:none}
.wtable a:hover{color:var(--cy)}
.ent{color:var(--cy);font-weight:700;min-width:140px}
.mz{font-family:'Share Tech Mono';font-size:.7rem;padding:2px 8px;border-radius:4px;border:1px solid;white-space:nowrap}
.chip{display:inline-block;font-family:'Share Tech Mono';font-size:.75rem;padding:4px 11px;margin:0 6px 6px 0;border:1px solid #13405e;border-radius:20px;color:#cfe3f5;background:#0a1a2a}
.chip b{color:var(--gr);margin-left:5px}
header[data-testid=stHeader]{background:transparent}
.stButton>button,.stDownloadButton>button,.stFormSubmitButton>button{background:#0a1f33;color:#cfe3f5;border:1px solid #13405e;border-radius:10px}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--cy);color:var(--cy)}
.stButton>button[kind=primary],.stFormSubmitButton>button[kind=primaryFormSubmit]{background:linear-gradient(90deg,#00a3c4,#00c98a);color:#04121f;border:0;font-weight:700}
/* ---- Mentions légales (petits caractères) ---- */
.cwp-legal{margin-top:2.2rem;padding-top:.7rem;border-top:1px solid #12263a;font-family:'Rajdhani',sans-serif;
           font-size:.72rem;line-height:1.35;color:#52708a;text-align:center}
.cwp-legal b{color:#6f8ca5;font-weight:600}
.cwp-legal-inline{font-size:.68rem;color:#52708a;margin:2px 0 12px 0;line-height:1.3}
</style>"""


def apply() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
