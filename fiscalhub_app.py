# ================================================================
# fiscalhub_app.py — FiscalHub · Portal Asesoría Fiscal
# Nolasco Capital ecosystem · Repo: pedrocamposgodoy/FiscalHub
#
# Stack: Python + Streamlit + Supabase
# Diseño: basado en Portal_Asesor.html (Claude Design)
# Colores: #111318 fondo · #C8A96E acento dorado
# ================================================================

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import io

# ── Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="FiscalHub · Nolasco Capital",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Supabase ─────────────────────────────────────────────────────
SUPABASE_URL = "https://odxixtgqcyddfqaapqgi.supabase.co"
SUPABASE_KEY = "sb_publishable_Obgti7yMfXw8wCUL2FbTtA_EWeyHuM9"

def _h(token=None):
    t = token or st.session_state.get("fh_token") or SUPABASE_KEY
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {t}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

# ── CSS completo basado en Portal_Asesor.html ────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=DM+Serif+Display&display=swap');

:root{
  --pa-bg:#111318; --pa-bg-deep:#0B0D11; --pa-surface:#1C1F26;
  --pa-surface-2:#23272F; --pa-surface-hover:#272B34;
  --pa-border:#2A2F39; --pa-border-strong:#3A4150;
  --pa-text:#E8E8E8; --pa-text-strong:#F5F5F5;
  --pa-text-mute:#8B92A0; --pa-text-dim:#5C6371;
  --pa-accent:#C8A96E; --pa-accent-dim:#8E7848;
  --pa-accent-faint:rgba(200,169,110,0.10);
  --pa-critical:#E05252; --pa-critical-bg:rgba(224,82,82,0.10);
  --pa-warn:#D4914A; --pa-warn-bg:rgba(212,145,74,0.10);
  --pa-ok:#5C9E6E; --pa-ok-bg:rgba(92,158,110,0.10);
  --pa-info:#5B8AB8;
  --pa-font-ui:'IBM Plex Sans','Inter',sans-serif;
  --pa-font-mono:'IBM Plex Mono',monospace;
  --pa-font-display:'DM Serif Display',Georgia,serif;
}

/* ── Reset Streamlit ── */
.stApp { background: var(--pa-bg) !important; color: var(--pa-text) !important; font-family: var(--pa-font-ui) !important; }
section[data-testid="stSidebar"] { background: var(--pa-bg-deep) !important; border-right: 1px solid var(--pa-border) !important; }
section[data-testid="stSidebar"] * { color: var(--pa-text) !important; font-family: var(--pa-font-ui) !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
div[data-testid="stVerticalBlock"] { gap: 0 !important; }
.stButton > button {
  background: var(--pa-surface) !important; border: 1px solid var(--pa-border) !important;
  color: var(--pa-text) !important; font-family: var(--pa-font-ui) !important;
  font-size: 12px !important; border-radius: 4px !important; padding: 6px 12px !important;
  transition: background .12s, border-color .12s !important;
}
.stButton > button:hover { background: var(--pa-surface-hover) !important; border-color: var(--pa-border-strong) !important; }
.stTextInput > div > div > input, .stSelectbox > div > div {
  background: var(--pa-surface) !important; border: 1px solid var(--pa-border) !important;
  color: var(--pa-text) !important; font-family: var(--pa-font-ui) !important;
  border-radius: 4px !important;
}
.stTextInput > div > div > input:focus { border-color: var(--pa-accent-dim) !important; }
.stDataFrame { background: var(--pa-surface) !important; }
hr { border-color: var(--pa-border) !important; }
h1,h2,h3 { font-family: var(--pa-font-display) !important; color: var(--pa-text-strong) !important; }
p, li { color: var(--pa-text) !important; }
label { color: var(--pa-text-mute) !important; }
.stTabs [data-baseweb="tab-list"] { background: var(--pa-surface) !important; border-bottom: 1px solid var(--pa-border) !important; gap: 0 !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: var(--pa-text-mute) !important; border-bottom: 2px solid transparent !important; font-family: var(--pa-font-ui) !important; font-size: 12px !important; padding: 10px 18px !important; }
.stTabs [aria-selected="true"] { color: var(--pa-accent) !important; border-bottom-color: var(--pa-accent) !important; background: transparent !important; }
.stMetric { background: var(--pa-surface) !important; border: 1px solid var(--pa-border) !important; border-radius: 4px !important; padding: 14px 16px !important; }
.stMetric label { font-size: 10px !important; letter-spacing: 0.14em !important; text-transform: uppercase !important; color: var(--pa-text-dim) !important; }
.stMetric [data-testid="stMetricValue"] { font-family: var(--pa-font-mono) !important; font-size: 26px !important; font-weight: 600 !important; color: var(--pa-text-strong) !important; }
div[data-testid="stSidebarUserContent"] { padding: 0 !important; }

/* ── Componentes custom ── */
.fh-brand { padding: 18px 20px 16px; border-bottom: 1px solid var(--pa-border); }
.fh-nc { width: 28px; height: 28px; border: 1px solid var(--pa-accent); color: var(--pa-accent);
  display: inline-flex; align-items: center; justify-content: center;
  font-family: var(--pa-font-display); font-size: 14px; letter-spacing: -1px; }
.fh-wordmark { font-family: var(--pa-font-display); font-size: 18px; color: var(--pa-text-strong); }
.fh-sub { font-size: 9px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--pa-text-mute); margin-top: 6px; padding-left: 38px; }
.fh-advisor { padding: 14px 20px; border-bottom: 1px solid var(--pa-border); }
.fh-avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--pa-surface-2);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 600; color: var(--pa-accent); border: 1px solid var(--pa-border-strong); }

.fh-page { padding: 24px 28px 60px; }
.fh-page-title { font-family: var(--pa-font-display); font-size: 26px; color: var(--pa-text-strong); line-height: 1.1; letter-spacing: -0.01em; margin: 0 0 4px; }
.fh-eyebrow { font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--pa-text-dim); margin-bottom: 4px; }
.fh-sub-text { font-size: 12px; color: var(--pa-text-mute); margin: 0; }
.fh-section-title { font-family: var(--pa-font-display); font-size: 18px; color: var(--pa-text-strong);
  border-left: 2px solid var(--pa-accent); padding-left: 10px; margin: 24px 0 14px; line-height: 1.1; }

/* KPI cards */
.fh-kpi { background: var(--pa-surface); border: 1px solid var(--pa-border); border-radius: 4px; padding: 14px 16px; }
.fh-kpi-label { font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--pa-text-dim); }
.fh-kpi-value { font-family: var(--pa-font-mono); font-size: 26px; font-weight: 600; color: var(--pa-text-strong); margin-top: 6px; line-height: 1; }
.fh-kpi-value.crit { color: var(--pa-critical); }
.fh-kpi-value.ok { color: var(--pa-ok); }
.fh-kpi-value.accent { color: var(--pa-accent); }
.fh-kpi-sub { font-size: 11px; color: var(--pa-text-mute); margin-top: 6px; }

/* Tabla clientes */
.fh-table { width: 100%; background: var(--pa-surface); border: 1px solid var(--pa-border);
  border-radius: 4px; border-collapse: collapse; font-size: 13px; }
.fh-table thead th { background: var(--pa-bg-deep); text-align: left; font-size: 10px;
  letter-spacing: 0.10em; text-transform: uppercase; color: var(--pa-text-dim);
  font-weight: 500; padding: 10px 14px; border-bottom: 1px solid var(--pa-border); white-space: nowrap; }
.fh-table tbody td { padding: 12px 14px; border-bottom: 1px solid var(--pa-border); color: var(--pa-text); vertical-align: middle; }
.fh-table tbody tr { cursor: pointer; transition: background .08s; }
.fh-table tbody tr:hover { background: var(--pa-surface-hover); }
.fh-table tbody tr:last-child td { border-bottom: 0; }
.fh-table tr.is-priority { box-shadow: inset 2px 0 0 var(--pa-critical); }
.fh-table tr.is-warn { box-shadow: inset 2px 0 0 var(--pa-warn); }
.name-cell { font-weight: 500; color: var(--pa-text-strong); }
.nif-cell { font-size: 10px; color: var(--pa-text-dim); font-family: var(--pa-font-mono); margin-top: 1px; }

/* Badges */
.badge-crit { display: inline-block; min-width: 22px; padding: 2px 6px; border-radius: 3px;
  font-family: var(--pa-font-mono); font-size: 11px; font-weight: 600; text-align: center;
  background: var(--pa-critical-bg); color: var(--pa-critical); }
.badge-warn { display: inline-block; min-width: 22px; padding: 2px 6px; border-radius: 3px;
  font-family: var(--pa-font-mono); font-size: 11px; font-weight: 600; text-align: center;
  background: var(--pa-warn-bg); color: var(--pa-warn); }
.badge-zero { display: inline-block; min-width: 22px; padding: 2px 6px; border-radius: 3px;
  font-family: var(--pa-font-mono); font-size: 11px; color: var(--pa-text-dim); text-align: center; }

/* Pills estado */
.pill-crit { display: inline-flex; align-items: center; gap: 5px; font-size: 10px; font-weight: 500;
  padding: 2px 7px; border-radius: 10px; background: var(--pa-critical-bg); color: var(--pa-critical); border: 1px solid rgba(224,82,82,0.25); }
.pill-warn { display: inline-flex; align-items: center; gap: 5px; font-size: 10px; font-weight: 500;
  padding: 2px 7px; border-radius: 10px; background: var(--pa-warn-bg); color: var(--pa-warn); border: 1px solid rgba(212,145,74,0.25); }
.pill-ok { display: inline-flex; align-items: center; gap: 5px; font-size: 10px; font-weight: 500;
  padding: 2px 7px; border-radius: 10px; background: var(--pa-ok-bg); color: var(--pa-ok); border: 1px solid rgba(92,158,110,0.25); }
.dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; display: inline-block; }

/* Checks */
.chk-ok { color: var(--pa-ok); font-size: 13px; }
.chk-no { color: var(--pa-critical); font-size: 13px; }
.chk-na { color: var(--pa-text-dim); font-size: 13px; }
.mono { font-family: var(--pa-font-mono); }
.impact-neg { font-family: var(--pa-font-mono); color: var(--pa-critical); font-weight: 500; }
.impact-pos { font-family: var(--pa-font-mono); color: var(--pa-ok); font-weight: 500; }

/* Alertas */
.fh-alert { display: grid; grid-template-columns: 4px 140px 1fr 180px 100px; gap: 0;
  align-items: center; border-bottom: 1px solid var(--pa-border);
  background: var(--pa-surface); cursor: pointer; transition: background .1s; }
.fh-alert:hover { background: var(--pa-surface-hover); }
.fh-alert-rail-crit { background: var(--pa-critical); align-self: stretch; }
.fh-alert-rail-warn { background: var(--pa-warn); align-self: stretch; }
.fh-alert-client { padding: 14px 14px 14px 16px; font-size: 12px; }
.fh-alert-name { color: var(--pa-text-strong); font-weight: 500; }
.fh-alert-prop { font-size: 11px; color: var(--pa-text-dim); margin-top: 2px; }
.fh-alert-main { padding: 14px 0; }
.fh-alert-type { font-size: 10px; letter-spacing: 0.06em; color: var(--pa-text-dim); text-transform: uppercase; margin-bottom: 3px; }
.fh-alert-title { font-size: 13px; font-weight: 500; color: var(--pa-text-strong); }
.fh-alert-desc { font-size: 12px; color: var(--pa-text-mute); margin-top: 2px; }
.fh-alert-action { padding: 14px; text-align: right; }
.fh-alert-cta { padding: 14px 16px 14px 0; }

/* Wizard */
.wz-steps { display: flex; align-items: center; background: var(--pa-surface);
  border: 1px solid var(--pa-border); border-radius: 4px; padding: 12px 14px; margin-bottom: 18px; gap: 0; }
.wz-step-num { width: 22px; height: 22px; border-radius: 50%; border: 1px solid var(--pa-border-strong);
  display: inline-flex; align-items: center; justify-content: center;
  font-family: var(--pa-font-mono); font-size: 11px; font-weight: 600; flex-shrink: 0; color: var(--pa-text-mute); }
.wz-step-num.done { background: var(--pa-accent); border-color: var(--pa-accent); color: #1A1206; }
.wz-step-num.current { background: var(--pa-bg-deep); border-color: var(--pa-accent); color: var(--pa-accent); box-shadow: 0 0 0 3px var(--pa-accent-faint); }
.wz-step-label { font-size: 12px; font-weight: 500; color: var(--pa-text-mute); margin-left: 8px; }
.wz-step-label.current { color: var(--pa-text-strong); font-weight: 600; }
.wz-step-label.done { color: var(--pa-text); }
.wz-line { flex: 1; height: 1px; background: var(--pa-border); margin: 0 8px; }
.wz-line.done { background: var(--pa-accent-dim); }

.wz-card { background: var(--pa-surface); border: 1px solid var(--pa-border); border-radius: 6px; }
.wz-body { padding: 28px 32px 20px; }
.wz-title { font-family: var(--pa-font-display); font-size: 24px; color: var(--pa-text-strong); margin: 0 0 6px; line-height: 1.1; }
.wz-sub { font-size: 13px; color: var(--pa-text-mute); margin: 0 0 24px; }
.wz-foot { display: flex; justify-content: space-between; align-items: center;
  padding: 16px 32px; border-top: 1px solid var(--pa-border);
  background: var(--pa-bg-deep); border-radius: 0 0 6px 6px; }

.wz-field { padding: 12px 14px; background: var(--pa-bg-deep); border: 1px solid var(--pa-border); border-radius: 4px; }
.wz-field-label { font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--pa-text-dim); margin-bottom: 6px; }
.wz-field-value { font-size: 13px; color: var(--pa-text-strong); }

.wz-callout { padding: 14px 16px; border-radius: 4px; border-left: 3px solid; margin-top: 16px; font-size: 13px; }
.wz-callout.warn { background: var(--pa-warn-bg); border-color: var(--pa-warn); }
.wz-callout.crit { background: var(--pa-critical-bg); border-color: var(--pa-critical); }
.wz-callout.ok { background: var(--pa-ok-bg); border-color: var(--pa-ok); }
.wz-callout.info { background: rgba(91,138,184,0.08); border-color: var(--pa-info); }
.wz-callout.accent { background: var(--pa-accent-faint); border-color: var(--pa-accent); }

/* Panel */
.fh-panel { background: var(--pa-surface); border: 1px solid var(--pa-border); border-radius: 4px; }
.fh-panel-head { padding: 12px 16px; border-bottom: 1px solid var(--pa-border);
  display: flex; justify-content: space-between; align-items: center; }
.fh-panel-title { font-size: 12px; letter-spacing: 0.10em; text-transform: uppercase; color: var(--pa-text); font-weight: 600; }
.fh-panel-body { padding: 14px 16px; }

/* Checklist gastos */
.chk-item { display: flex; align-items: center; gap: 12px; padding: 9px 16px;
  border-bottom: 1px solid var(--pa-border); font-size: 13px; }
.chk-item:last-child { border-bottom: 0; }
.chk-box-on { width: 14px; height: 14px; background: var(--pa-ok); border-radius: 2px;
  display: inline-flex; align-items: center; justify-content: center; color: #0B0D11; font-size: 10px; flex-shrink: 0; }
.chk-box-off { width: 14px; height: 14px; border: 1px solid var(--pa-critical); border-radius: 2px;
  display: inline-flex; align-items: center; justify-content: center; color: var(--pa-critical); font-size: 10px; flex-shrink: 0; }
.chk-box-na { width: 14px; height: 14px; border: 1px solid var(--pa-border-strong); border-radius: 2px;
  display: inline-flex; align-items: center; justify-content: center; color: var(--pa-text-dim); font-size: 10px; flex-shrink: 0; }
.chk-lbl { flex: 1; }
.chk-hint { font-size: 11px; color: var(--pa-text-dim); }
.chk-cas { font-family: var(--pa-font-mono); font-size: 10px; color: var(--pa-text-dim); min-width: 42px; }
.chk-amount { font-family: var(--pa-font-mono); font-size: 12px; color: var(--pa-text-strong); min-width: 90px; text-align: right; }
.chk-amount.missing { color: var(--pa-critical); }

/* Modelo 100 */
.m100-table { width: 100%; background: var(--pa-surface); border: 1px solid var(--pa-border);
  border-radius: 4px; border-collapse: collapse; font-size: 13px; }
.m100-table thead th { background: var(--pa-bg-deep); text-align: left; font-size: 10px;
  letter-spacing: 0.10em; text-transform: uppercase; color: var(--pa-text-dim);
  font-weight: 500; padding: 10px 14px; border-bottom: 1px solid var(--pa-border); }
.m100-table thead th.r { text-align: right; }
.m100-table tbody td { padding: 11px 14px; border-bottom: 1px solid var(--pa-border); color: var(--pa-text); }
.m100-table tbody td.r { text-align: right; font-family: var(--pa-font-mono); }
.m100-table tbody tr:last-child td { border-bottom: 0; }
.m100-table tr.sum td { background: var(--pa-bg-deep); font-weight: 600; border-top: 1px solid var(--pa-border-strong); }
.m100-table tr.final td { background: rgba(200,169,110,0.05); font-weight: 600; color: var(--pa-accent); }
.cas { font-family: var(--pa-font-mono); color: var(--pa-accent); font-size: 11px; letter-spacing: 0.04em; }
.l-sub { font-size: 10px; color: var(--pa-text-dim); margin-top: 1px; }

/* IRPF countdown */
.irpf-box { margin: 14px 16px 18px; padding: 12px; background: var(--pa-surface); border: 1px solid var(--pa-border); border-radius: 6px; }
.irpf-num { font-family: var(--pa-font-mono); font-size: 24px; font-weight: 600; line-height: 1.05; margin-top: 6px; }
.irpf-bar { height: 3px; background: var(--pa-bg-deep); border-radius: 2px; margin-top: 10px; overflow: hidden; }
.irpf-fill { height: 100%; border-radius: 2px; }

/* Vinculación código */
.code-box { background: var(--pa-bg-deep); border: 1px solid var(--pa-accent); border-radius: 4px;
  padding: 18px 24px; text-align: center; font-family: var(--pa-font-mono);
  font-size: 32px; font-weight: 600; color: var(--pa-accent); letter-spacing: 0.2em; }

/* Done screen */
.wz-done { max-width: 680px; margin: 60px auto; text-align: center;
  background: var(--pa-surface); border: 1px solid var(--pa-border);
  border-radius: 6px; padding: 48px 40px; }
.wz-done-seal { width: 64px; height: 64px; border-radius: 50%;
  background: var(--pa-ok-bg); color: var(--pa-ok);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 30px; border: 2px solid var(--pa-ok); margin-bottom: 18px; }

/* Login */
.fh-login { max-width: 400px; margin: 80px auto; }
.fh-login-card { background: var(--pa-surface); border: 1px solid var(--pa-border); border-radius: 6px; padding: 36px 32px; }
.fh-login-logo { display: flex; align-items: center; gap: 12px; margin-bottom: 28px; }
.fh-btn-accent { background: var(--pa-accent) !important; color: #1A1206 !important;
  border-color: var(--pa-accent) !important; font-weight: 500 !important; width: 100% !important; }
</style>
"""

# ── Helpers ──────────────────────────────────────────────────────
def sf(v, d=0):
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)): return float(d)
        return float(v)
    except: return float(d)

def fmt_eur(n, sign=False):
    n = float(n or 0)
    s = f"{abs(n):,.0f}".replace(",", ".")
    prefix = "−" if n < 0 else ("+" if sign else "")
    return f"{prefix}{s} €"

def days_to_irpf():
    hoy = date.today()
    cierre = date(hoy.year, 6, 30)
    if hoy > cierre: cierre = date(hoy.year + 1, 6, 30)
    return (cierre - hoy).days

# ── Supabase Auth ────────────────────────────────────────────────
def login_asesor(email, password):
    r = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
        json={"email": email, "password": password}
    )
    if r.status_code == 200:
        d = r.json()
        return {"ok": True, "user_id": d["user"]["id"],
                "email": d["user"]["email"], "token": d["access_token"]}
    return {"ok": False, "error": r.json().get("error_description", "Error de acceso")}

def registrar_asesor(email, password, nombre, despacho):
    r = requests.post(
        f"{SUPABASE_URL}/auth/v1/signup",
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
        json={"email": email, "password": password}
    )
    if r.status_code == 200:
        user_id = r.json().get("id") or r.json().get("user", {}).get("id")
        if user_id:
            requests.post(
                f"{SUPABASE_URL}/rest/v1/asesores",
                headers=_h(),
                json={"user_id": user_id, "nombre": nombre,
                      "despacho": despacho, "email": email}
            )
        return {"ok": True}
    return {"ok": False, "error": r.json().get("error_description", "Error de registro")}

def get_asesor_info(user_id):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/asesores?user_id=eq.{user_id}&select=*",
        headers=_h()
    )
    if r.status_code == 200 and r.json():
        return r.json()[0]
    return {"nombre": "Asesor", "despacho": "Despacho Fiscal", "email": ""}

# ── Datos de clientes vinculados ─────────────────────────────────
def get_clientes_vinculados(asesor_user_id):
    """Obtiene propietarios que han compartido código con este asesor."""
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/accesos_asesor"
        f"?asesor_user_id=eq.{asesor_user_id}&activo=eq.true&select=*",
        headers=_h()
    )
    if r.status_code != 200:
        return []
    return r.json() or []

def get_inmuebles_propietario(propietario_id):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/inmuebles?user_id=eq.{propietario_id}&select=*",
        headers=_h()
    )
    if r.status_code == 200 and r.json():
        return pd.DataFrame(r.json())
    return pd.DataFrame()

def get_movimientos_propietario(propietario_id):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/movimientos?user_id=eq.{propietario_id}&select=*",
        headers=_h()
    )
    if r.status_code == 200 and r.json():
        return pd.DataFrame(r.json())
    return pd.DataFrame()

def vincular_propietario(asesor_user_id, codigo):
    """Vincula un propietario al asesor mediante código de 6 dígitos."""
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/accesos_asesor?codigo=eq.{codigo.upper()}&activo=eq.true&select=*",
        headers=_h()
    )
    if r.status_code == 200 and r.json():
        acc = r.json()[0]
        propietario_id = acc.get("propietario_id")
        nombre = acc.get("nombre") or acc.get("nombre_propietario", "Propietario")
        if not propietario_id:
            return {"ok": False, "error": "Código sin propietario asociado"}
        # Registrar asesor_user_id en el registro
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/accesos_asesor?id=eq.{acc['id']}",
            headers={**_h(), "Prefer": "return=minimal"},
            json={"asesor_user_id": asesor_user_id}
        )
        return {"ok": True, "propietario_id": propietario_id, "nombre": nombre}
    return {"ok": False, "error": "Código no válido o ya utilizado"}

# ── Análisis fiscal ───────────────────────────────────────────────
def calcular_alertas_cliente(df_inm, df_mov):
    """Calcula alertas fiscales para un propietario."""
    alertas = []
    if df_inm.empty:
        return alertas

    for _, row in df_inm.iterrows():
        nombre = row.get("nombre") or row.get("Nombre", "")
        tipo = str(row.get("tipo_arrendamiento") or row.get("Tipo_Arrendamiento", "")).lower()
        fecha_str = str(row.get("fecha_inicio_contrato") or row.get("Fecha_Inicio_Contrato", "") or "")
        ibi = sf(row.get("ibi_anual") or row.get("IBI_Anual", 0))
        amort = sf(row.get("amortizacion_fiscal") or row.get("Amortizacion_Fiscal", 0))
        seguro = sf(row.get("seguro_anual") or row.get("Seguro_Anual", 0))
        renta = sf(row.get("renta") or row.get("Renta", 0))
        renta_mer = sf(row.get("renta_mercado") or row.get("Renta_Mercado", 0))

        # Reducción 60% no aplicada (solo larga duración)
        es_habitual = "larga" in tipo or "habitual" in tipo
        if es_habitual:
            try:
                anyo = int(str(fecha_str)[:4]) if fecha_str and len(fecha_str) >= 4 else 0
                reduccion_pct = 60 if (anyo > 0 and anyo <= 2023) else 50
            except:
                reduccion_pct = 50
            if reduccion_pct == 60:
                alertas.append({
                    "inmueble": nombre, "tipo": "crit",
                    "categoria": "Fiscal",
                    "titulo": "Reducción 60% — verificar aplicación",
                    "impacto": round(renta * 12 * 0.6 * 0.19, 0),
                    "accion": "Confirmar en casilla 0150 del Modelo 100"
                })

        # Gastos incompletos
        gastos_faltantes = []
        if ibi == 0: gastos_faltantes.append("IBI")
        if amort == 0: gastos_faltantes.append("Amortización 3%")
        if seguro == 0: gastos_faltantes.append("Seguro hogar")
        if gastos_faltantes:
            alertas.append({
                "inmueble": nombre, "tipo": "crit" if "Amortización 3%" in gastos_faltantes else "warn",
                "categoria": "Fiscal",
                "titulo": f"Gastos sin registrar: {', '.join(gastos_faltantes)}",
                "impacto": 0,
                "accion": "Solicitar justificantes al propietario"
            })

        # Renta bajo mercado
        if renta_mer > 0 and renta < renta_mer * 0.90:
            lucro = (renta_mer - renta) * 12
            alertas.append({
                "inmueble": nombre, "tipo": "warn",
                "categoria": "Renta",
                "titulo": f"Renta {round((1 - renta/renta_mer)*100)}% bajo mercado",
                "impacto": lucro,
                "accion": "Aplicar IRAV en próximo aniversario"
            })

    return alertas

def calcular_modelo100_global(df_inm, df_mov):
    """Calcula casillas Modelo 100 sumando todos los inmuebles."""
    if df_inm.empty:
        return {}

    ingresos = 0
    intereses = 0
    reparaciones = 0
    ibi = 0
    comunidad_seguros = 0
    suministros = 0
    gastos_juridicos = 0
    amortizacion = 0
    retenciones = 0

    for _, row in df_inm.iterrows():
        nombre = row.get("nombre") or row.get("Nombre", "")
        dias = sf(row.get("dias_arrendados_anio") or row.get("Dias_Arrendados_Anio", 365))
        factor = min(dias, 365) / 365

        renta = sf(row.get("renta") or row.get("Renta", 0))
        ingresos += renta * 12 * factor
        intereses += sf(row.get("intereses_hipoteca") or row.get("Intereses_Hipoteca", 0)) * factor
        ibi += sf(row.get("ibi_anual") or row.get("IBI_Anual", 0)) * factor

        comunidad = sf(row.get("comunidad") or row.get("Comunidad", 0)) * 12
        seguro_h = sf(row.get("seguro_anual") or row.get("Seguro_Anual", 0))
        seguro_v = sf(row.get("seguro_vida") or row.get("Seguro_Vida", 0))
        ascensor = sf(row.get("gasto_ascensor") or row.get("Gasto_Ascensor", 0))
        comunidad_seguros += (comunidad + seguro_h + seguro_v + ascensor) * factor

        suministros += sf(row.get("servicios_suministros") or row.get("Servicios_Suministros", 0)) * factor
        gastos_juridicos += sf(row.get("gastos_juridicos") or row.get("Gastos_Juridicos", 0)) * factor
        retenciones += sf(row.get("retenciones_irpf") or row.get("Retenciones_IRPF", 0))

        # Amortización
        precio = sf(row.get("precio_compra") or row.get("Precio_Compra", 0))
        impuestos = sf(row.get("impuestos_compra") or row.get("Impuestos_Compra", 0))
        gastos_c = sf(row.get("gastos_compra") or row.get("Gastos_Compra", 0))
        catastral = sf(row.get("valor_catastral") or row.get("Valor_Catastral", 0))
        pct_c = sf(row.get("pct_construccion") or row.get("Pct_Construccion", 0.75))
        base = max(precio + impuestos + gastos_c, catastral)
        amortizacion += base * pct_c * 0.03 * factor

        # Reparaciones del diario
        if not df_mov.empty:
            col_apt = "apartamento" if "apartamento" in df_mov.columns else "Apartamento"
            col_tipo = "tipo" if "tipo" in df_mov.columns else "Tipo"
            col_cat = "categoria" if "categoria" in df_mov.columns else "Categoría"
            col_imp = "importe" if "importe" in df_mov.columns else "Importe"
            mask = (
                (df_mov.get(col_apt, pd.Series()) == nombre) &
                (df_mov.get(col_tipo, pd.Series()) == "Gasto") &
                (df_mov.get(col_cat, pd.Series()).isin(["Mantenimiento", "Reparación"]))
            )
            reparaciones += df_mov[mask][col_imp].sum() * factor if mask.any() else 0

    total_gastos = intereses + reparaciones + ibi + comunidad_seguros + suministros + gastos_juridicos + amortizacion
    rend_neto = ingresos - total_gastos
    reduccion = rend_neto * 0.55  # estimación mixta
    rend_final = rend_neto - reduccion

    return {
        "ingresos": round(ingresos, 2),
        "intereses": round(intereses, 2),
        "reparaciones": round(reparaciones, 2),
        "ibi": round(ibi, 2),
        "comunidad_seguros": round(comunidad_seguros, 2),
        "suministros": round(suministros, 2),
        "gastos_juridicos": round(gastos_juridicos, 2),
        "amortizacion": round(amortizacion, 2),
        "total_gastos": round(total_gastos, 2),
        "rend_neto": round(rend_neto, 2),
        "reduccion": round(reduccion, 2),
        "rend_final": round(rend_final, 2),
        "retenciones": round(retenciones, 2),
    }

def construir_cartera(clientes_vinculados):
    """Construye la lista de clientes con sus métricas fiscales."""
    cartera = []
    for acc in clientes_vinculados:
        pid = acc.get("propietario_id") or acc.get("user_id")
        nombre = acc.get("nombre") or acc.get("nombre_propietario", "Propietario")
        if not pid:
            continue
        df_inm = get_inmuebles_propietario(pid)
        df_mov = get_movimientos_propietario(pid)
        alertas = calcular_alertas_cliente(df_inm, df_mov)
        modelo = calcular_modelo100_global(df_inm, df_mov)

        criticas = len([a for a in alertas if a["tipo"] == "crit"])
        medias   = len([a for a in alertas if a["tipo"] == "warn"])
        impacto  = sum(a.get("impacto", 0) for a in alertas)

        checks = {
            "red60":  not any(a["categoria"] == "Fiscal" and "60%" in a["titulo"] for a in alertas),
            "gastos": not any("Gastos sin registrar" in a["titulo"] for a in alertas),
            "irav":   not any("mercado" in a["titulo"] for a in alertas),
        }

        if criticas > 0:   estado = "critico"
        elif medias > 0:   estado = "medio"
        else:               estado = "ok"

        cartera.append({
            "id": pid, "nombre": nombre,
            "nif": acc.get("nif_propietario", ""),
            "inmuebles": len(df_inm),
            "criticas": criticas, "medias": medias,
            "impacto": impacto, "estado": estado,
            "checks": checks, "alertas": alertas,
            "df_inm": df_inm, "df_mov": df_mov,
            "modelo100": modelo,
            "activity_days": 0,
        })

    cartera.sort(key=lambda x: ({"critico": 0, "medio": 1, "ok": 2}[x["estado"]], -x["criticas"]))
    return cartera

# ── CSS sidebar FiscalHub ────────────────────────────────────────
def render_sidebar():
    asesor = st.session_state.get("fh_asesor", {})
    nombre = asesor.get("nombre", "Asesor")
    despacho = asesor.get("despacho", "Despacho Fiscal")
    iniciales = "".join(p[0].upper() for p in nombre.split()[:2])
    dias = days_to_irpf()
    pct = max(0, min(100, int((90 - dias) / 90 * 100)))
    color_irpf = "#E05252" if dias < 30 else "#D4914A" if dias < 60 else "#5C9E6E"

    st.markdown(f"""
    <div class="fh-brand">
      <div style="display:flex;align-items:center;gap:10px;">
        <div class="fh-nc">NC</div>
        <div class="fh-wordmark">FiscalHub</div>
      </div>
      <div class="fh-sub">Portal asesoría fiscal</div>
    </div>
    <div class="fh-advisor">
      <div style="display:flex;gap:10px;align-items:center;">
        <div class="fh-avatar">{iniciales}</div>
        <div>
          <div style="font-size:12px;color:var(--pa-text-strong);font-weight:500;">{nombre}</div>
          <div style="font-size:10px;color:var(--pa-text-dim);font-family:var(--pa-font-mono);">{despacho}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    menu_opts = {
        "🗂 Cartera": "cartera",
        "⚠️ Alertas": "alertas",
        "📥 Exportar": "exportar",
        "🔗 Vincular cliente": "vincular",
    }
    for label, key in menu_opts.items():
        if st.sidebar.button(label, key=f"sb_{key}", use_container_width=True):
            st.session_state.fh_menu = key
            st.session_state.pop("fh_cliente_sel", None)
            st.session_state.pop("fh_wizard_step", None)
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div class="irpf-box">
      <div class="fh-eyebrow">Cierre IRPF</div>
      <div class="irpf-num" style="color:{color_irpf};">{dias}<span style="font-size:13px;font-weight:400;color:var(--pa-text-mute);margin-left:6px;">días</span></div>
      <div style="font-size:11px;color:var(--pa-text-mute);margin-top:2px;">30 jun · campaña IRPF 2025</div>
      <div class="irpf-bar"><div class="irpf-fill" style="width:{pct}%;background:{color_irpf};"></div></div>
      <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--pa-text-dim);font-family:var(--pa-font-mono);margin-top:6px;">
        <span>hoy</span><span>30 jun</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪 Cerrar sesión", use_container_width=True):
        for k in ["fh_logged", "fh_user_id", "fh_token", "fh_asesor",
                  "fh_menu", "fh_cliente_sel", "fh_wizard_step", "fh_cartera"]:
            st.session_state.pop(k, None)
        st.rerun()

# ── PANTALLA: Login / Registro ───────────────────────────────────
def pantalla_login():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="fh-login">
      <div class="fh-login-card">
        <div class="fh-login-logo">
          <div class="fh-nc">NC</div>
          <div>
            <div class="fh-wordmark">FiscalHub</div>
            <div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--pa-text-mute);">Portal Asesoría Fiscal</div>
          </div>
        </div>
    """, unsafe_allow_html=True)

    tab_login, tab_reg = st.tabs(["Acceder", "Registrarse"])

    with tab_login:
        email = st.text_input("Email", key="li_email", placeholder="tu@despacho.es")
        pwd   = st.text_input("Contraseña", type="password", key="li_pwd")
        if st.button("Entrar →", key="li_btn", use_container_width=True, type="primary"):
            if email and pwd:
                with st.spinner("Verificando..."):
                    res = login_asesor(email, pwd)
                if res["ok"]:
                    st.session_state.fh_logged   = True
                    st.session_state.fh_user_id  = res["user_id"]
                    st.session_state.fh_token    = res["token"]
                    st.session_state.fh_asesor   = get_asesor_info(res["user_id"])
                    st.session_state.fh_menu     = "cartera"
                    st.rerun()
                else:
                    st.error(res.get("error", "Credenciales incorrectas"))
            else:
                st.warning("Introduce email y contraseña")

    with tab_reg:
        nombre   = st.text_input("Nombre completo", key="rg_nombre")
        despacho = st.text_input("Nombre del despacho", key="rg_despacho")
        email_r  = st.text_input("Email profesional", key="rg_email")
        pwd_r    = st.text_input("Contraseña (mín. 8 caracteres)", type="password", key="rg_pwd")
        if st.button("Crear cuenta →", key="rg_btn", use_container_width=True, type="primary"):
            if all([nombre, despacho, email_r, pwd_r]):
                if len(pwd_r) < 8:
                    st.error("La contraseña debe tener al menos 8 caracteres")
                else:
                    with st.spinner("Creando cuenta..."):
                        res = registrar_asesor(email_r, pwd_r, nombre, despacho)
                    if res["ok"]:
                        st.success("✅ Cuenta creada. Revisa tu email para confirmar y luego accede.")
                    else:
                        st.error(res.get("error", "Error al registrar"))
            else:
                st.warning("Completa todos los campos")

    st.markdown("</div></div>", unsafe_allow_html=True)

# ── PANTALLA: Cartera ────────────────────────────────────────────
def pantalla_cartera():
    cartera = st.session_state.get("fh_cartera", [])

    if not cartera:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;">
          <div style="font-size:40px;margin-bottom:16px;">🔗</div>
          <div class="fh-page-title" style="margin-bottom:8px;">Sin clientes vinculados</div>
          <div class="fh-sub-text">Ve a "Vincular cliente" e introduce el código que te dé el propietario desde Nolasco Capital.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    total_inm = sum(c["inmuebles"] for c in cartera)
    total_crit = sum(c["criticas"] for c in cartera)
    total_imp = sum(c["impacto"] for c in cartera)
    n_crit = sum(1 for c in cartera if c["estado"] == "critico")
    n_med  = sum(1 for c in cartera if c["estado"] == "medio")
    n_ok   = sum(1 for c in cartera if c["estado"] == "ok")

    # Header
    st.markdown(f"""
    <div style="margin-bottom:18px;">
      <div class="fh-eyebrow">Granada · Despacho fiscal</div>
      <div class="fh-page-title">Cartera de clientes</div>
      <div class="fh-sub-text">{len(cartera)} propietarios · {total_inm} inmuebles · campaña IRPF 2025 en curso</div>
    </div>
    """, unsafe_allow_html=True)

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="fh-kpi">
          <div class="fh-kpi-label">Clientes en cartera</div>
          <div class="fh-kpi-value mono">{len(cartera)}</div>
          <div class="fh-kpi-sub">{n_crit} críticos · {n_med} a revisar · {n_ok} OK</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="fh-kpi">
          <div class="fh-kpi-label">Inmuebles bajo gestión</div>
          <div class="fh-kpi-value mono">{total_inm}</div>
          <div class="fh-kpi-sub">Todos en larga duración</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="fh-kpi">
          <div class="fh-kpi-label">Alertas críticas abiertas</div>
          <div class="fh-kpi-value mono crit">{total_crit}</div>
          <div class="fh-kpi-sub">Requieren acción antes del 30 jun</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="fh-kpi">
          <div class="fh-kpi-label">Impacto fiscal a recuperar</div>
          <div class="fh-kpi-value mono accent">{fmt_eur(total_imp)}</div>
          <div class="fh-kpi-sub">Lucro fiscal pendiente · cartera completa</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Filtros
    filtro = st.radio("Filtrar:", ["Todos", "Críticos", "A revisar", "OK"],
                      horizontal=True, key="fh_filtro", label_visibility="collapsed")
    busqueda = st.text_input("🔍 Buscar cliente...", key="fh_busqueda",
                              label_visibility="collapsed")

    # Tabla
    rows_filtradas = [c for c in cartera if
        (filtro == "Todos" or
         (filtro == "Críticos" and c["estado"] == "critico") or
         (filtro == "A revisar" and c["estado"] == "medio") or
         (filtro == "OK" and c["estado"] == "ok")) and
        (not busqueda or busqueda.lower() in c["nombre"].lower())
    ]

    def _pill(estado):
        if estado == "critico": return '<span class="pill-crit"><span class="dot"></span>Crítico</span>'
        if estado == "medio":   return '<span class="pill-warn"><span class="dot"></span>Revisar</span>'
        return '<span class="pill-ok"><span class="dot"></span>OK</span>'

    def _chk(v):
        if v is True:  return '<span class="chk-ok">✓</span>'
        if v is False: return '<span class="chk-no">✗</span>'
        return '<span class="chk-na">–</span>'

    def _badge_crit(n):
        if n == 0: return f'<span class="badge-zero">{n}</span>'
        return f'<span class="badge-crit">{n}</span>'

    def _badge_warn(n):
        if n == 0: return f'<span class="badge-zero">{n}</span>'
        return f'<span class="badge-warn">{n}</span>'

    filas_html = ""
    for c in rows_filtradas:
        row_cls = "is-priority" if c["estado"] == "critico" else ("is-warn" if c["estado"] == "medio" else "")
        imp_str = fmt_eur(c["impacto"]) if c["impacto"] else "—"
        imp_cls = "impact-neg" if c["impacto"] > 0 else ""
        filas_html += f"""
        <tr class="{row_cls}" onclick="window.parent.postMessage({{type:'streamlit:setComponentValue',value:'{c["id"]}'}}, '*')">
          <td><div class="name-cell">{c["nombre"]}</div><div class="nif-cell">{c.get("nif","")}</div></td>
          <td style="text-align:right;" class="mono">{c["inmuebles"]}</td>
          <td style="text-align:center;">{_badge_crit(c["criticas"])}</td>
          <td style="text-align:center;">{_badge_warn(c["medias"])}</td>
          <td style="text-align:right;" class="{imp_cls} mono">{imp_str}</td>
          <td style="text-align:center;">{_chk(c["checks"]["red60"])}</td>
          <td style="text-align:center;">{_chk(c["checks"]["gastos"])}</td>
          <td style="text-align:center;">{_chk(c["checks"]["irav"])}</td>
          <td>{_pill(c["estado"])}</td>
        </tr>"""

    st.markdown(f"""
    <table class="fh-table">
      <thead><tr>
        <th>Cliente</th>
        <th style="text-align:right;">Inmuebles</th>
        <th style="text-align:center;">⚠ Críticas</th>
        <th style="text-align:center;">◔ Medias</th>
        <th style="text-align:right;">Impacto IRPF</th>
        <th style="text-align:center;" title="Reducción 60%">Red. 60%</th>
        <th style="text-align:center;" title="Gastos deducibles">Gastos</th>
        <th style="text-align:center;" title="IRAV">IRAV</th>
        <th>Estado</th>
      </tr></thead>
      <tbody>{filas_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    # Selección via botones (alternativa al onclick del HTML)
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="fh-eyebrow" style="margin-bottom:8px;">Seleccionar cliente para revisión IRPF</div>',
                unsafe_allow_html=True)

    cols_sel = st.columns(min(len(rows_filtradas), 4))
    for i, c in enumerate(rows_filtradas):
        with cols_sel[i % 4]:
            estado_icon = "🔴" if c["estado"] == "critico" else "🟡" if c["estado"] == "medio" else "🟢"
            if st.button(f"{estado_icon} {c['nombre'].split()[0]} {c['nombre'].split()[-1]}",
                         key=f"sel_{c['id']}", use_container_width=True):
                st.session_state.fh_cliente_sel = c["id"]
                st.session_state.fh_wizard_step = 1
                st.session_state.fh_menu = "wizard"
                st.rerun()

# ── PANTALLA: Wizard ─────────────────────────────────────────────
def pantalla_wizard():
    cliente_id = st.session_state.get("fh_cliente_sel")
    cartera = st.session_state.get("fh_cartera", [])
    cliente = next((c for c in cartera if c["id"] == cliente_id), None)

    if not cliente:
        st.warning("Selecciona un cliente desde la cartera.")
        return

    step = st.session_state.get("fh_wizard_step", 1)
    STEPS = [
        (1, "Resumen del cliente",    "Ingresos, gastos y rentabilidad global"),
        (2, "Gastos deducibles",      "Verificar que todos están registrados"),
        (3, "Modelo 100",             "Casillas pre-rellenadas para la AEAT"),
        (4, "Exportar",               "PDF y Excel listos para el cliente"),
    ]

    # Breadcrumb
    if st.button("← Volver a cartera", key="wz_back"):
        st.session_state.fh_menu = "cartera"
        st.session_state.pop("fh_cliente_sel", None)
        st.session_state.pop("fh_wizard_step", None)
        st.rerun()

    # Barra de pasos
    steps_html = ""
    for i, (n, nombre, desc) in enumerate(STEPS):
        if n < step:   cls = "done"
        elif n == step: cls = "current"
        else:           cls = "future"

        num_html = f'<div class="wz-step-num {cls}">{"✓" if n < step else n}</div>'
        lbl_cls  = cls if cls != "future" else ""
        label_html = f'<span class="wz-step-label {lbl_cls}">{nombre}</span>'

        steps_html += f'<div style="display:flex;align-items:center;gap:8px;">{num_html}{label_html}</div>'
        if i < len(STEPS) - 1:
            line_cls = "done" if n < step else ""
            steps_html += f'<div class="wz-line {line_cls}"></div>'

    st.markdown(f'<div class="wz-steps">{steps_html}</div>', unsafe_allow_html=True)

    df_inm  = cliente["df_inm"]
    df_mov  = cliente["df_mov"]
    modelo  = cliente["modelo100"]
    alertas = cliente["alertas"]

    # ── PASO 1: Resumen ──────────────────────────────────────────
    if step == 1:
        st.markdown(f"""
        <div class="wz-card">
          <div class="wz-body">
            <div class="wz-title">{cliente['nombre']}</div>
            <div class="wz-sub">{cliente['inmuebles']} inmueble{'s' if cliente['inmuebles'] != 1 else ''} en cartera · Revisión IRPF 2025</div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""<div class="wz-field">
              <div class="wz-field-label">Ingresos íntegros</div>
              <div class="wz-field-value mono" style="color:var(--pa-ok);">{fmt_eur(modelo.get('ingresos',0))}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="wz-field">
              <div class="wz-field-label">Total gastos deducibles</div>
              <div class="wz-field-value mono" style="color:var(--pa-critical);">−{fmt_eur(modelo.get('total_gastos',0))}</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="wz-field">
              <div class="wz-field-label">Rendimiento neto</div>
              <div class="wz-field-value mono">{fmt_eur(modelo.get('rend_neto',0))}</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="wz-field">
              <div class="wz-field-label">Base imponible estimada</div>
              <div class="wz-field-value mono" style="color:var(--pa-accent);">{fmt_eur(modelo.get('rend_final',0))}</div>
            </div>""", unsafe_allow_html=True)

        if alertas:
            n_crit = len([a for a in alertas if a["tipo"] == "crit"])
            msg = f"Este cliente tiene {len(alertas)} alerta{'s' if len(alertas)>1 else ''}" + \
                  (f", de las cuales {n_crit} son críticas" if n_crit else "") + \
                  ". Revísalas en los siguientes pasos."
            tipo_callout = "crit" if n_crit else "warn"
            st.markdown(f'<div class="wz-callout {tipo_callout}">{msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="wz-callout ok">✓ Sin alertas fiscales detectadas para este cliente.</div>',
                        unsafe_allow_html=True)

        # Inmuebles
        if not df_inm.empty:
            st.markdown('<div class="fh-section-title" style="margin-top:24px;">Inmuebles</div>',
                        unsafe_allow_html=True)
            col_nombre = "nombre" if "nombre" in df_inm.columns else "Nombre"
            col_renta  = "renta"  if "renta"  in df_inm.columns else "Renta"
            col_tipo   = "tipo_arrendamiento" if "tipo_arrendamiento" in df_inm.columns else "Tipo_Arrendamiento"
            col_ref    = "ref_catastral" if "ref_catastral" in df_inm.columns else "Ref_Catastral"

            filas = ""
            for _, row in df_inm.iterrows():
                n = row.get(col_nombre, "—")
                r = sf(row.get(col_renta, 0))
                t = str(row.get(col_tipo, "—"))
                ref = str(row.get(col_ref, "—"))
                filas += f"""<tr>
                  <td>{n}</td>
                  <td>{ref}</td>
                  <td>{t}</td>
                  <td style="text-align:right;" class="mono" style="color:var(--pa-ok);">{fmt_eur(r * 12)}/año</td>
                </tr>"""

            st.markdown(f"""
            <table class="fh-table" style="margin-bottom:8px;">
              <thead><tr>
                <th>Inmueble</th><th>Ref. Catastral</th>
                <th>Modalidad</th><th style="text-align:right;">Ingresos anuales</th>
              </tr></thead>
              <tbody>{filas}</tbody>
            </table>""", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)  # wz-body

        # Footer wizard
        st.markdown('<div class="wz-foot">', unsafe_allow_html=True)
        col_l, col_r = st.columns([1, 1])
        with col_r:
            if st.button("Siguiente → Gastos deducibles", key="wz1_next",
                         use_container_width=True, type="primary"):
                st.session_state.fh_wizard_step = 2
                st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

    # ── PASO 2: Gastos deducibles ────────────────────────────────
    elif step == 2:
        col_nombre = "nombre" if "nombre" in df_inm.columns else "Nombre"

        gastos_check = []
        for _, row in df_inm.iterrows():
            nombre_inm = row.get(col_nombre, "—")
            gastos_check.extend([
                {"cas": "0106", "label": "IBI y tributos",
                 "hint": f"{nombre_inm}",
                 "amount": sf(row.get("ibi_anual") or row.get("IBI_Anual", 0)),
                 "on": sf(row.get("ibi_anual") or row.get("IBI_Anual", 0)) > 0},
                {"cas": "0107", "label": "Comunidad de propietarios",
                 "hint": f"{nombre_inm}",
                 "amount": sf(row.get("comunidad") or row.get("Comunidad", 0)) * 12,
                 "on": sf(row.get("comunidad") or row.get("Comunidad", 0)) > 0},
                {"cas": "0111", "label": "Seguro de hogar",
                 "hint": f"{nombre_inm}",
                 "amount": sf(row.get("seguro_anual") or row.get("Seguro_Anual", 0)),
                 "on": sf(row.get("seguro_anual") or row.get("Seguro_Anual", 0)) > 0},
                {"cas": "0109", "label": "Amortización del inmueble (3%)",
                 "hint": f"3% s/ valor construcción · {nombre_inm}",
                 "amount": sf(row.get("amortizacion_fiscal") or row.get("Amortizacion_Fiscal", 0)),
                 "on": sf(row.get("amortizacion_fiscal") or row.get("Amortizacion_Fiscal", 0)) > 0},
                {"cas": "0105", "label": "Intereses hipoteca",
                 "hint": f"{nombre_inm}",
                 "amount": sf(row.get("intereses_hipoteca") or row.get("Intereses_Hipoteca", 0)),
                 "on": sf(row.get("intereses_hipoteca") or row.get("Intereses_Hipoteca", 0)) > 0},
            ])

        chk_html = ""
        for g in gastos_check:
            if g["on"] is True:
                box = '<div class="chk-box-on">✓</div>'
                amt_cls = ""
            elif g["on"] is False:
                box = '<div class="chk-box-off">✗</div>'
                amt_cls = "missing"
            else:
                box = '<div class="chk-box-na">–</div>'
                amt_cls = ""

            amt_str = fmt_eur(g["amount"]) if g["amount"] else "Pendiente"
            chk_html += f"""
            <div class="chk-item">
              {box}
              <div class="chk-cas">{g["cas"]}</div>
              <div class="chk-lbl">{g["label"]}<div class="chk-hint">{g["hint"]}</div></div>
              <div class="chk-amount {amt_cls}">{amt_str}</div>
            </div>"""

        faltan = sum(1 for g in gastos_check if g["on"] is False)

        st.markdown(f"""
        <div class="wz-card">
          <div class="wz-body">
            <div class="wz-title">Gastos deducibles</div>
            <div class="wz-sub">Verifica que todos los gastos están registrados. Los marcados en rojo están pendientes.</div>
        """, unsafe_allow_html=True)

        if faltan:
            st.markdown(f"""<div class="wz-callout crit">
              <strong>⚠️ {faltan} gasto{'s' if faltan > 1 else ''} sin registrar</strong><br>
              Solicita los justificantes al propietario y añádelos desde Nolasco Capital.
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="wz-callout ok"><strong>✓ Todos los gastos registrados</strong></div>',
                        unsafe_allow_html=True)

        st.markdown(f"""
        <div class="fh-panel" style="margin-top:20px;">
          <div class="fh-panel-head">
            <span class="fh-panel-title">Checklist gastos deducibles</span>
            <span style="font-size:11px;color:var(--pa-text-mute);">{len(gastos_check) - faltan} de {len(gastos_check)} completados</span>
          </div>
          <div class="chk-list">{chk_html}</div>
        </div>
        </div>""", unsafe_allow_html=True)  # wz-body

        st.markdown('<div class="wz-foot">', unsafe_allow_html=True)
        c_l, c_r = st.columns(2)
        with c_l:
            if st.button("← Resumen cliente", key="wz2_prev", use_container_width=True):
                st.session_state.fh_wizard_step = 1
                st.rerun()
        with c_r:
            if st.button("Siguiente → Modelo 100", key="wz2_next",
                         use_container_width=True, type="primary"):
                st.session_state.fh_wizard_step = 3
                st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

    # ── PASO 3: Modelo 100 ───────────────────────────────────────
    elif step == 3:
        m = modelo
        casillas = [
            ("0102", "Rendimiento íntegro del capital inmobiliario", "Suma rentas declaradas",
             m.get("ingresos", 0), False, False),
            ("0104", "Gastos de reparación y conservación", "Del diario contable",
             -m.get("reparaciones", 0), False, False),
            ("0105", "Intereses de capitales ajenos", "Hipotecas vinculadas",
             -m.get("intereses", 0), False, False),
            ("0106", "Tributos y recargos no estatales (IBI)", "IBI anual",
             -m.get("ibi", 0), False, False),
            ("0107", "Servicios y suministros (comunidad + seguros)", "Comunidad + seguros + ascensor",
             -m.get("comunidad_seguros", 0), False, False),
            ("0109", "Amortización del inmueble", "3% s/ valor construcción",
             -m.get("amortizacion", 0), False, False),
            ("0111", "Otros gastos deducibles", "Jurídicos, agencia",
             -m.get("gastos_juridicos", 0), False, False),
            ("0146", "RENDIMIENTO NETO", "Suma casillas anteriores",
             m.get("rend_neto", 0), True, False),
            ("0150", "Reducción rendimiento neto (orientativa)",
             "⚠️ VALIDAR — 60% ant. 26/05/2023 · 50% posterior",
             -m.get("reduccion", 0), False, False),
            ("0156", "RENDIMIENTO NETO REDUCIDO A INTEGRAR", "Base imponible estimada",
             m.get("rend_final", 0), False, True),
            ("0153", "Retenciones practicadas", "",
             -m.get("retenciones", 0), False, False),
        ]

        filas_m100 = ""
        for cas, label, sub, val, is_sum, is_final in casillas:
            tr_cls = "final" if is_final else ("sum" if is_sum else "")
            val_color = ""
            if is_final: val_color = "color:var(--pa-accent);"
            elif is_sum: val_color = "color:var(--pa-text-strong);"
            elif val < 0: val_color = "color:var(--pa-critical);"
            elif val > 0: val_color = "color:var(--pa-ok);"

            sub_html = f'<div class="l-sub">{sub}</div>' if sub else ""
            filas_m100 += f"""<tr class="{tr_cls}">
              <td><span class="cas">{cas}</span></td>
              <td>{label}{sub_html}</td>
              <td class="r" style="{val_color}">{fmt_eur(val)}</td>
            </tr>"""

        st.markdown(f"""
        <div class="wz-card">
          <div class="wz-body">
            <div class="wz-title">Modelo 100 · Pre-relleno automático</div>
            <div class="wz-sub">Casillas calculadas desde Nolasco Capital. Validar reducción con criterio profesional antes de presentar.</div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="wz-callout warn" style="margin-bottom:20px;">
          <strong>⚠️ Reducción (casilla 0150)</strong><br>
          Orientativa. Contratos anteriores al 26/05/2023 → 60%. Posteriores → 50% general.
          Verificar si aplica 70% (zona tensionada + joven) o 90% (rebaja &gt;5% sobre contrato anterior).
        </div>
        <table class="m100-table">
          <thead><tr>
            <th style="width:60px;">Casilla</th>
            <th>Descripción</th>
            <th class="r">Importe</th>
          </tr></thead>
          <tbody>{filas_m100}</tbody>
        </table>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="wz-foot">', unsafe_allow_html=True)
        c_l, c_r = st.columns(2)
        with c_l:
            if st.button("← Gastos deducibles", key="wz3_prev", use_container_width=True):
                st.session_state.fh_wizard_step = 2
                st.rerun()
        with c_r:
            if st.button("Siguiente → Exportar", key="wz3_next",
                         use_container_width=True, type="primary"):
                st.session_state.fh_wizard_step = 4
                st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

    # ── PASO 4: Exportar ─────────────────────────────────────────
    elif step == 4:
        st.markdown(f"""
        <div class="wz-card">
          <div class="wz-body">
            <div class="wz-title">Exportar documentos</div>
            <div class="wz-sub">Genera el PDF y el Excel para {cliente['nombre']}.</div>
        """, unsafe_allow_html=True)

        asesor = st.session_state.get("fh_asesor", {})
        nombre_asesor = asesor.get("despacho", asesor.get("nombre", ""))

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📄 Generar PDF Modelo 100", use_container_width=True, type="primary"):
                try:
                    from fiscal_export import generar_pdf_global, calcular_resumen_global
                    from app import calcular_modelo_100, safe_float as sf2
                    filas, totales = calcular_resumen_global(
                        df_inm, df_mov, sf2, calcular_modelo_100)
                    pdf = generar_pdf_global(filas, totales,
                                             nombre_propietario=cliente["nombre"],
                                             nombre_asesoria=nombre_asesor)
                    if pdf:
                        st.download_button(
                            "⬇️ Descargar PDF",
                            data=pdf,
                            file_name=f"ModeloIRPF_{cliente['nombre'].replace(' ','_')}_2025.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                except Exception as e:
                    st.error(f"Error generando PDF: {e}")

        with c2:
            if st.button("📊 Generar Excel", use_container_width=True):
                try:
                    from fiscal_export import generar_excel_asesor, calcular_resumen_global
                    from app import calcular_modelo_100, safe_float as sf2
                    filas, totales = calcular_resumen_global(
                        df_inm, df_mov, sf2, calcular_modelo_100)
                    xlsx = generar_excel_asesor(filas, totales,
                                                nombre_propietario=cliente["nombre"],
                                                nombre_asesoria=nombre_asesor)
                    if xlsx:
                        st.download_button(
                            "⬇️ Descargar Excel",
                            data=xlsx,
                            file_name=f"IRPF_{cliente['nombre'].replace(' ','_')}_2025.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )
                except Exception as e:
                    st.error(f"Error generando Excel: {e}")

        st.markdown(f"""
        <div class="wz-callout accent" style="margin-top:20px;">
          <strong>Documentos listos para entregar al cliente o presentar a la AEAT.</strong><br>
          Recuerda validar la reducción del 60% antes de la presentación definitiva.
        </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="wz-foot">', unsafe_allow_html=True)
        c_l, c_r = st.columns(2)
        with c_l:
            if st.button("← Modelo 100", key="wz4_prev", use_container_width=True):
                st.session_state.fh_wizard_step = 3
                st.rerun()
        with c_r:
            if st.button("✓ Marcar como revisado", key="wz4_done",
                         use_container_width=True, type="primary"):
                st.session_state.fh_menu = "cartera"
                st.session_state.pop("fh_cliente_sel", None)
                st.session_state.pop("fh_wizard_step", None)
                st.success(f"✅ {cliente['nombre']} marcado como revisado")
                st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

# ── PANTALLA: Alertas ────────────────────────────────────────────
def pantalla_alertas():
    cartera = st.session_state.get("fh_cartera", [])
    todas = []
    for c in cartera:
        for a in c.get("alertas", []):
            todas.append({**a, "cliente_nombre": c["nombre"], "cliente_id": c["id"]})

    todas.sort(key=lambda x: (0 if x["tipo"] == "crit" else 1))
    n_crit = len([a for a in todas if a["tipo"] == "crit"])
    n_warn = len([a for a in todas if a["tipo"] == "warn"])

    st.markdown(f"""
    <div style="margin-bottom:18px;">
      <div class="fh-eyebrow">Cartera completa · ordenadas por urgencia</div>
      <div class="fh-page-title">Alertas fiscales</div>
      <div class="fh-sub-text">{len(todas)} alertas activas · {n_crit} críticas · {n_warn} a revisar</div>
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f"""<div class="fh-kpi">
          <div class="fh-kpi-label">Críticas abiertas</div>
          <div class="fh-kpi-value mono crit">{n_crit}</div>
          <div class="fh-kpi-sub">Acción inmediata antes del 30 jun</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="fh-kpi">
          <div class="fh-kpi-label">A revisar</div>
          <div class="fh-kpi-value mono" style="color:var(--pa-warn);">{n_warn}</div>
          <div class="fh-kpi-sub">Esta semana</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        impacto_total = sum(a.get("impacto", 0) for a in todas if a.get("impacto", 0) > 0)
        st.markdown(f"""<div class="fh-kpi">
          <div class="fh-kpi-label">Impacto fiscal recuperable</div>
          <div class="fh-kpi-value mono accent">{fmt_eur(impacto_total)}</div>
          <div class="fh-kpi-sub">Suma de impactos cuantificables</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    if not todas:
        st.success("✅ Sin alertas activas en la cartera.")
        return

    alertas_html = '<div class="fh-panel">'
    for a in todas:
        rail_cls = "fh-alert-rail-crit" if a["tipo"] == "crit" else "fh-alert-rail-warn"
        tipo_label = "Crítica" if a["tipo"] == "crit" else "Revisar"
        imp = fmt_eur(a["impacto"]) if a.get("impacto", 0) > 0 else "—"
        alertas_html += f"""
        <div class="fh-alert">
          <div class="{rail_cls}"></div>
          <div class="fh-alert-client">
            <div class="fh-alert-name">{a["cliente_nombre"].split()[0]} {a["cliente_nombre"].split()[-1]}</div>
            <div class="fh-alert-prop">{a["inmueble"]}</div>
          </div>
          <div class="fh-alert-main">
            <div class="fh-alert-type">{tipo_label} · {a["categoria"]}</div>
            <div class="fh-alert-title">{a["titulo"]}</div>
          </div>
          <div class="fh-alert-action">
            <div style="font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--pa-text-dim);">Acción</div>
            <div style="margin-top:3px;font-size:12px;">{a["accion"]}</div>
            <div style="margin-top:3px;font-size:11px;color:var(--pa-accent);font-family:var(--pa-font-mono);">{imp}</div>
          </div>
          <div class="fh-alert-cta"></div>
        </div>"""
    alertas_html += "</div>"
    st.markdown(alertas_html, unsafe_allow_html=True)

# ── PANTALLA: Exportar ───────────────────────────────────────────
def pantalla_exportar():
    cartera = st.session_state.get("fh_cartera", [])

    st.markdown("""
    <div style="margin-bottom:18px;">
      <div class="fh-eyebrow">Generación de entregables</div>
      <div class="fh-page-title">Exportar</div>
      <div class="fh-sub-text">PDFs Modelo 100 y resúmenes Excel para presentar al cliente o a la AEAT.</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""<div class="fh-panel">
          <div class="fh-panel-head"><span class="fh-panel-title">Exportar por cliente</span></div>
          <div class="fh-panel-body">""", unsafe_allow_html=True)

        if cartera:
            cliente_names = [c["nombre"] for c in cartera]
            sel = st.selectbox("Selecciona cliente:", cliente_names, key="exp_sel")
            cliente_sel = next((c for c in cartera if c["nombre"] == sel), None)
            if cliente_sel and st.button("📄 Generar PDF + Excel", use_container_width=True, type="primary"):
                st.info(f"Generando documentos para {sel}... Usa el wizard del cliente para exportar.")
        else:
            st.info("Sin clientes vinculados.")
        st.markdown("</div></div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""<div class="fh-panel">
          <div class="fh-panel-head"><span class="fh-panel-title">Historial de exportaciones</span></div>
          <div class="fh-panel-body">""", unsafe_allow_html=True)
        st.markdown('<div style="color:var(--pa-text-mute);font-size:12px;">Sin exportaciones registradas.</div>',
                    unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

# ── PANTALLA: Vincular ───────────────────────────────────────────
def pantalla_vincular():
    st.markdown("""
    <div style="margin-bottom:18px;">
      <div class="fh-eyebrow">Conectar con Nolasco Capital</div>
      <div class="fh-page-title">Vincular cliente</div>
      <div class="fh-sub-text">Introduce el código de 6 dígitos que el propietario genera desde Nolasco Capital → Privacidad → Compartir con Asesor.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""<div class="wz-callout info" style="max-width:600px;margin-bottom:24px;">
      <strong>¿Cómo funciona?</strong><br>
      El propietario entra en Nolasco Capital → pestaña Privacidad → "Compartir con Asesor" → genera un código de 6 caracteres.
      Ese código te lo manda a ti. Introdúcelo aquí y sus datos aparecerán en tu cartera automáticamente.
    </div>""", unsafe_allow_html=True)

    codigo = st.text_input("Código del propietario:", max_chars=10,
                            placeholder="Ej: AQ-2847", key="vincular_codigo")
    if st.button("🔗 Vincular propietario", use_container_width=True,
                 type="primary", key="vincular_btn"):
        if codigo.strip():
            with st.spinner("Verificando código..."):
                res = vincular_propietario(
                    st.session_state.fh_user_id,
                    codigo.strip().upper()
                )
            if res["ok"]:
                st.success(f"✅ Vinculado correctamente. {res.get('nombre', 'El propietario')} aparecerá en tu cartera.")
                # Recargar cartera
                vinculos = get_clientes_vinculados(st.session_state.fh_user_id)
                st.session_state.fh_cartera = construir_cartera(vinculos)
                st.rerun()
            else:
                st.error(f"❌ {res.get('error', 'Código no válido')}")
        else:
            st.warning("Introduce un código")

# ── APP PRINCIPAL ────────────────────────────────────────────────
def main():
    st.markdown(CSS, unsafe_allow_html=True)

    # Estado inicial
    if "fh_logged" not in st.session_state:
        st.session_state.fh_logged = False
    if "fh_menu" not in st.session_state:
        st.session_state.fh_menu = "cartera"

    # Login
    if not st.session_state.fh_logged:
        pantalla_login()
        return

    # Cargar cartera si no está en sesión
    if "fh_cartera" not in st.session_state:
        with st.spinner("Cargando cartera..."):
            vinculos = get_clientes_vinculados(st.session_state.fh_user_id)
            st.session_state.fh_cartera = construir_cartera(vinculos)

    # Sidebar
    with st.sidebar:
        render_sidebar()

    # Contenido principal
    menu = st.session_state.get("fh_menu", "cartera")

    st.markdown('<div class="fh-page">', unsafe_allow_html=True)

    if menu == "cartera":
        pantalla_cartera()
    elif menu == "wizard":
        pantalla_wizard()
    elif menu == "alertas":
        pantalla_alertas()
    elif menu == "exportar":
        pantalla_exportar()
    elif menu == "vincular":
        pantalla_vincular()

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
