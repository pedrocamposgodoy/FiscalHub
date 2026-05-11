"""
nolasco_styles.py
=================
Módulo compartido para Nolasco Capital, InmoHub y FiscalHub.
Copia este archivo IDÉNTICO en los 3 repositorios.

Uso en cada app — una sola línea:
    from nolasco_styles import inject_global_css
    inject_global_css("capital")   # o "inmohub" o "ficahub"

Las apps NO necesitan ningún CSS propio. Todo vive aquí.
"""

import os
import streamlit as st
import anthropic

# ─────────────────────────────────────────────────────────────────
# 1. TOKENS POR APP
# ─────────────────────────────────────────────────────────────────

_POS  = "#059669"
_NEG  = "#DC2626"
_WARN = "#D97706"
_TX   = "#0F172A"
_TXM  = "#475569"
_TXD  = "#94A3B8"
_BD   = "#E2E8F0"

APP_TOKENS = {

    # ── NOLASCO CAPITAL — sidebar blanco, acento azul
    "capital": {
        "sidebar_bg":        "#E2E8F0",
        "sidebar_border":    _BD,
        "sidebar_txt":       _TXM,
        "sidebar_txt_hover": "#185FA5",
        "sidebar_bg_hover":  "#EAF1FB",
        "body_bg":           "#F1F5F9",
        "card_bg":           "#FFFFFF",
        "card_border":       _BD,
        "accent":            "#185FA5",
        "accent_light":      "#EAF1FB",
        "accent_pastel":     "#BDDAF5",
        "text_primary":      _TX,
        "text_secondary":    _TXM,
        "text_muted":        _TXD,
        "positive":          _POS,
        "negative":          _NEG,
        "warning":           _WARN,
        "font_display":      "'Playfair Display', serif",
        "font_body":         "'DM Sans', sans-serif",
        "bocadillo_bg":      "#FFFFFF",
        "bocadillo_border":  "#185FA5",
        "bocadillo_header":  "#185FA5",
        "bocadillo_response":"#EAF1FB",
        "bocadillo_shadow":  "0 4px 6px -1px rgba(0,0,0,0.05)",
        "ia_label":          "✦ Asesor Patrimonial IA",
        "ia_placeholder":    "¿Qué quieres saber sobre tu patrimonio?",
        "ia_tone":           "amigable",
        "sidebar_items": [
            ("🏠", "Torre de Control"), ("📊", "Benchmark"),
            ("💰", "Escudo Fiscal"),    ("⚡", "Simuladores"),
            ("🤖", "Asesor IA"),        ("🔒", "Privacidad"),
        ],
    },

    # ── INMOHUB — sidebar oscuro, acento verde (identidad B2B diferencial)
    "inmohub": {
        "sidebar_bg":        "#0F2744",
        "sidebar_border":    "rgba(255,255,255,0.06)",
        "sidebar_txt":       "#8899AA",
        "sidebar_txt_hover": "#FFFFFF",
        "sidebar_bg_hover":  "rgba(255,255,255,0.06)",
        "body_bg":           "#0D1B2A",
        "card_bg":           "#1A2F4A",
        "card_border":       "rgba(255,255,255,0.08)",
        "accent":            "#00C9A7",
        "accent_light":      "#0D3A2A",
        "accent_pastel":     "#00C9A730",
        "text_primary":      "#FFFFFF",
        "text_secondary":    "#8899AA",
        "text_muted":        "#5A6A7A",
        "positive":          "#00C9A7",
        "negative":          "#FF4B4B",
        "warning":           "#FFB347",
        "font_display":      "'DM Sans', sans-serif",
        "font_body":         "'DM Sans', sans-serif",
        "bocadillo_bg":      "#0F2744",
        "bocadillo_border":  "#00C9A7",
        "bocadillo_header":  "#00C9A7",
        "bocadillo_response":"#0D3A2A",
        "bocadillo_shadow":  "none",
        "ia_label":          "⬡ AI Advisory",
        "ia_placeholder":    "¿Qué zona o lead quieres analizar?",
        "ia_tone":           "analítico",
        "sidebar_items": [
            ("🏠", "Dashboard"),        ("📡", "Radar Mercado"),
            ("🛒", "Lead Marketplace"), ("👥", "Fidelización"),
            ("🤖", "AI Advisory"),      ("⚙️", "Configuración"),
        ],
    },

    # ── FISCALHUB — sidebar blanco, acento morado
    "ficahub": {
        "sidebar_bg":        "#FFFFFF",
        "sidebar_border":    _BD,
        "sidebar_txt":       _TXM,
        "sidebar_txt_hover": "#534AB7",
        "sidebar_bg_hover":  "#EEEDFE",
        "body_bg":           "#F8FAFC",
        "card_bg":           "#FFFFFF",
        "card_border":       _BD,
        "accent":            "#534AB7",
        "accent_light":      "#EEEDFE",
        "accent_pastel":     "#D8D5F8",
        "text_primary":      _TX,
        "text_secondary":    _TXM,
        "text_muted":        _TXD,
        "positive":          _POS,
        "negative":          _NEG,
        "warning":           _WARN,
        "font_display":      "'Playfair Display', serif",
        "font_body":         "'DM Sans', sans-serif",
        "bocadillo_bg":      "#FFFFFF",
        "bocadillo_border":  "#534AB7",
        "bocadillo_header":  "#534AB7",
        "bocadillo_response":"#EEEDFE",
        "bocadillo_shadow":  "0 4px 6px -1px rgba(0,0,0,0.05)",
        "ia_label":          "◈ Asesor Fiscal IA",
        "ia_placeholder":    "¿Qué cliente o deducción quieres revisar?",
        "ia_tone":           "profesional",
        "sidebar_items": [
            ("📊", "Panel Global"), ("👤", "Clientes"),
            ("📋", "IRPF 2025"),   ("⚠️", "Alertas"),
            ("🤖", "Asesor IA"),   ("⚙️", "Config"),
        ],
    },
}


# ─────────────────────────────────────────────────────────────────
# 2. CSS GLOBAL — TODO EL DISEÑO VIVE AQUÍ
#    Las apps llaman inject_global_css("app") y no tocan CSS nunca.
# ─────────────────────────────────────────────────────────────────

def inject_global_css(app: str):
    t = APP_TOKENS[app]

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    /* RESET */
    * {{ box-sizing: border-box; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{ padding-top: 2rem !important; max-width: 100% !important; }}

    /* BODY */
    .stApp {{
        background-color: {t['body_bg']} !important;
        font-family: {t['font_body']} !important;
        color: {t['text_primary']} !important;
    }}

    /* SIDEBAR — fondo */
    [data-testid="stSidebar"] {{
        background-color: {t['sidebar_bg']} !important;
        border-right: 1px solid {t['sidebar_border']} !important;
    }}

    /* SIDEBAR — texto: selectores amplios para cubrir toda la jerarquía Streamlit */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label {{
        color: {t['sidebar_txt']} !important;
    }}

    /* SIDEBAR — botones */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stButton > button *,
    [data-testid="stSidebar"] .stButton > button span {{
        background: transparent !important;
        color: {t['sidebar_txt']} !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 8px 14px !important;
        text-align: left !important;
        width: 100% !important;
        justify-content: flex-start !important;
        box-shadow: none !important;
        transition: all 0.15s !important;
    }}

    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] .stButton > button:hover *,
    [data-testid="stSidebar"] .stButton > button:hover span {{
        background: {t['sidebar_bg_hover']} !important;
        color: {t['sidebar_txt_hover']} !important;
    }}

    /* SIDEBAR — radio nav */
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stRadio label span,
    [data-testid="stSidebar"] .stRadio label * {{
        color: {t['sidebar_txt']} !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        padding: 2px 0 !important;
    }}

    [data-testid="stSidebar"] .stRadio label:hover {{
        background: {t['sidebar_bg_hover']} !important;
        color: {t['sidebar_txt_hover']} !important;
    }}

    /* INPUTS */
    .stTextInput > div > div > input {{
        border-radius: 10px !important;
        border: 1px solid {t['card_border']} !important;
        font-family: {t['font_body']} !important;
        font-size: 13px !important;
        background: {t['card_bg']} !important;
        color: {t['text_primary']} !important;
        padding: 10px 14px !important;
        transition: border-color 0.15s !important;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: {t['accent']} !important;
        box-shadow: 0 0 0 3px {t['accent_light']} !important;
    }}
    .stTextInput > div > div > input::placeholder {{
        color: {t['text_muted']} !important;
    }}

    /* SELECTBOX */
    .stSelectbox > div > div {{
        background: {t['card_bg']} !important;
        border: 1px solid {t['card_border']} !important;
        border-radius: 10px !important;
        color: {t['text_primary']} !important;
    }}

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {{
        background: transparent !important;
        border-bottom: 1px solid {t['card_border']} !important;
        gap: 0 !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background: transparent !important;
        color: {t['text_muted']} !important;
        border-bottom: 2px solid transparent !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 10px 18px !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {t['accent']} !important;
        border-bottom-color: {t['accent']} !important;
    }}

    /* RADIO horizontal */
    .stRadio > div {{ flex-direction: row !important; gap: 8px !important; }}

    /* BOTONES MAIN */
    .main .stButton > button,
    [data-testid="stMainBlockContainer"] .stButton > button {{
        background: {t['card_bg']} !important;
        color: {t['accent']} !important;
        border: 1px solid {t['card_border']} !important;
        border-radius: 10px !important;
        font-family: {t['font_body']} !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 8px 16px !important;
        transition: all 0.15s !important;
    }}
    .main .stButton > button:hover,
    [data-testid="stMainBlockContainer"] .stButton > button:hover {{
        background: {t['accent_light']} !important;
        border-color: {t['accent']} !important;
    }}
    button[kind="primary"] {{
        background: {t['accent']} !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
    }}
    button[kind="primary"]:hover {{ opacity: 0.88 !important; }}

    /* NC-CARDS */
    .nc-card {{
        background: {t['card_bg']};
        border-radius: 12px;
        padding: 24px;
        border: 1px solid {t['card_border']};
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .nc-card-sm {{
        background: {t['card_bg']};
        border-radius: 12px;
        padding: 16px;
        border: 1px solid {t['card_border']};
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}

    /* TIPOGRAFÍA */
    .nc-number {{
        font-family: {t['font_display']};
        font-size: 2.25rem;
        font-weight: 700;
        color: {t['text_primary']};
        line-height: 1;
    }}
    .nc-number-lg {{
        font-family: {t['font_display']};
        font-size: 2.75rem;
        font-weight: 700;
        color: {t['accent']};
        line-height: 1;
    }}
    .nc-label {{
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: {t['text_muted']};
    }}
    .nc-title {{
        font-family: {t['font_display']};
        font-size: 1.1rem;
        font-weight: 600;
        color: {t['text_primary']};
        margin-bottom: 4px;
    }}
    .nc-subtitle {{
        font-size: 12px;
        color: {t['text_secondary']};
    }}

    /* DELTAS */
    .nc-delta-pos {{
        display:inline-flex; align-items:center; gap:3px;
        font-size:11px; font-weight:600;
        color:{t['positive']}; background:rgba(5,150,105,0.1);
        padding:3px 8px; border-radius:6px;
    }}
    .nc-delta-neg {{
        display:inline-flex; align-items:center; gap:3px;
        font-size:11px; font-weight:600;
        color:{t['negative']}; background:rgba(220,38,38,0.1);
        padding:3px 8px; border-radius:6px;
    }}
    .nc-delta-warn {{
        display:inline-flex; align-items:center; gap:3px;
        font-size:11px; font-weight:600;
        color:{t['warning']}; background:rgba(217,119,6,0.1);
        padding:3px 8px; border-radius:6px;
    }}

    /* PILLS */
    .nc-pill-pos  {{ display:inline-flex;align-items:center;gap:4px;font-size:10px;font-weight:600;padding:3px 10px;border-radius:6px;background:rgba(5,150,105,0.1);color:{t['positive']}; }}
    .nc-pill-neg  {{ display:inline-flex;align-items:center;gap:4px;font-size:10px;font-weight:600;padding:3px 10px;border-radius:6px;background:rgba(220,38,38,0.1);color:{t['negative']}; }}
    .nc-pill-warn {{ display:inline-flex;align-items:center;gap:4px;font-size:10px;font-weight:600;padding:3px 10px;border-radius:6px;background:rgba(217,119,6,0.1);color:{t['warning']}; }}
    .nc-pill-acc  {{ display:inline-flex;align-items:center;gap:4px;font-size:10px;font-weight:600;padding:3px 10px;border-radius:6px;background:{t['accent_light']};color:{t['accent']}; }}
    .dot {{ width:5px;height:5px;border-radius:50%;background:currentColor;display:inline-block; }}

    /* CALLOUTS */
    .nc-callout {{ padding:12px 14px;border-radius:8px;border-left:3px solid;margin:10px 0;font-size:13px; }}
    .nc-callout.pos  {{ background:rgba(5,150,105,0.08);  border-color:{t['positive']}; color:{t['text_primary']}; }}
    .nc-callout.neg  {{ background:rgba(220,38,38,0.08);  border-color:{t['negative']}; color:{t['text_primary']}; }}
    .nc-callout.warn {{ background:rgba(217,119,6,0.08);  border-color:{t['warning']};  color:{t['text_primary']}; }}
    .nc-callout.info {{ background:{t['accent_light']};   border-color:{t['accent']};   color:{t['text_primary']}; }}

    /* DIVIDER */
    .nc-divider {{ height:1px; background:{t['card_border']}; margin:16px 0; }}

    /* METRIC ROW */
    .nc-metric-row {{ display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid {t['card_border']}; }}
    .nc-metric-row:last-child {{ border-bottom:none; }}

    /* TABLA UNIVERSAL */
    .nc-table {{ width:100%;background:{t['card_bg']};border:1px solid {t['card_border']};border-radius:12px;border-collapse:separate;border-spacing:0;font-size:12px;box-shadow:0 1px 3px rgba(0,0,0,0.05); }}
    .nc-table thead th {{ background:{t['accent_light']};color:{t['accent']};font-size:9px;letter-spacing:0.10em;text-transform:uppercase;font-weight:600;padding:10px 14px;border-bottom:1px solid {t['card_border']};text-align:left; }}
    .nc-table thead th:first-child {{ border-radius:12px 0 0 0; }}
    .nc-table thead th:last-child  {{ border-radius:0 12px 0 0; }}
    .nc-table tbody td {{ padding:11px 14px;border-bottom:1px solid {t['card_border']};color:{t['text_primary']};vertical-align:middle; }}
    .nc-table tbody tr:last-child td {{ border-bottom:none; }}
    .nc-table tbody tr:hover td {{ background:{t['accent_light']}; }}
    .nc-table tr.row-neg  td {{ box-shadow:inset 3px 0 0 {t['negative']}; }}
    .nc-table tr.row-warn td {{ box-shadow:inset 3px 0 0 {t['warning']}; }}
    .nc-table tr.row-pos  td {{ box-shadow:inset 3px 0 0 {t['positive']}; }}

    /* PANEL */
    .nc-panel {{ background:{t['card_bg']};border:1px solid {t['card_border']};border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.05); }}
    .nc-panel-head {{ padding:10px 14px;border-bottom:1px solid {t['card_border']};background:{t['accent_light']};border-radius:12px 12px 0 0;display:flex;justify-content:space-between;align-items:center; }}
    .nc-panel-title {{ font-size:11px;letter-spacing:0.10em;text-transform:uppercase;color:{t['accent']};font-weight:600; }}

    /* PAGE HEADER */
    .nc-section     {{ font-family:{t['font_display']};font-size:17px;font-weight:600;color:{t['text_primary']};border-left:3px solid {t['accent']};padding-left:12px;margin:24px 0 16px;line-height:1.1; }}
    .nc-page-label  {{ font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:{t['text_muted']};margin-bottom:4px;font-weight:600; }}
    .nc-page-title  {{ font-family:{t['font_display']};font-size:28px;font-weight:700;color:{t['text_primary']};margin-bottom:4px;line-height:1.1; }}
    .nc-page-sub    {{ font-size:13px;color:{t['text_secondary']};margin-bottom:0; }}

    /* SIDEBAR BLOCKS (avatar, IRPF counter, brand) */
    .sb-brand {{ padding:16px 14px 12px;border-bottom:1px solid {t['sidebar_border']}; }}
    .sb-logo  {{ width:28px;height:28px;border:1.5px solid {t['accent']};color:{t['accent']} !important;display:inline-flex;align-items:center;justify-content:center;font-family:{t['font_display']};font-size:12px;border-radius:4px;font-weight:700; }}
    .sb-wordmark {{ font-family:{t['font_display']};font-size:18px;color:{t['text_primary']} !important;font-weight:700; }}
    .sb-tag {{ font-size:9px;letter-spacing:0.18em;text-transform:uppercase;color:{t['text_muted']} !important;margin-top:4px;padding-left:38px; }}
    .sb-advisor {{ padding:10px 14px;border-bottom:1px solid {t['sidebar_border']}; }}
    .sb-avatar {{ width:32px;height:32px;border-radius:50%;background:{t['accent_light']};border:1.5px solid {t['accent_pastel']};display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:{t['accent']} !important; }}
    .sb-irpf {{ margin:8px 10px 12px;padding:12px;background:{t['accent_light']};border:1px solid {t['accent_pastel']};border-radius:8px; }}
    .sb-irpf-num {{ font-family:{t['font_display']};font-size:24px;font-weight:700;line-height:1.1; }}
    .sb-bar  {{ height:3px;background:{t['card_border']};border-radius:2px;margin-top:8px;overflow:hidden; }}
    .sb-fill {{ height:100%;border-radius:2px; }}

    /* INMUEBLE ROWS */
    .nc-inm-row {{ display:flex;align-items:center;background:{t['card_bg']};border:1px solid {t['card_border']};border-radius:12px;margin-bottom:8px;overflow:hidden;transition:box-shadow 0.15s;box-shadow:0 1px 3px rgba(0,0,0,0.04); }}
    .nc-inm-row:hover {{ box-shadow:0 4px 12px rgba(0,0,0,0.08); }}
    .nc-inm-rail {{ width:4px;align-self:stretch;flex-shrink:0; }}
    .nc-inm-rail.neg  {{ background:{t['negative']}; }}
    .nc-inm-rail.warn {{ background:{t['warning']}; }}
    .nc-inm-rail.pos  {{ background:{t['positive']}; }}
    .nc-inm-rail.acc  {{ background:{t['accent']}; }}
    .nc-inm-body {{ flex:1;padding:10px 14px; }}
    .nc-inm-name {{ font-size:13px;font-weight:600;color:{t['text_primary']}; }}
    .nc-inm-meta {{ font-size:10px;color:{t['text_muted']};margin-top:1px; }}

    /* ALERT CARDS (FiscalHub) */
    .nc-alert-grid {{ display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;margin-top:4px; }}
    .nc-alert-card {{ background:{t['card_bg']};border:1px solid {t['card_border']};border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.05);transition:box-shadow 0.15s,transform 0.15s; }}
    .nc-alert-card:hover {{ box-shadow:0 6px 20px rgba(0,0,0,0.1);transform:translateY(-2px); }}
    .nc-alert-top {{ height:4px;width:100%; }}
    .nc-alert-top.neg  {{ background:{t['negative']}; }}
    .nc-alert-top.warn {{ background:{t['warning']}; }}
    .nc-alert-body {{ padding:14px 16px 16px; }}
    .nc-alert-header {{ display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px; }}
    .nc-alert-tipo {{ font-size:9px;letter-spacing:0.1em;text-transform:uppercase;font-weight:600;padding:3px 8px;border-radius:6px; }}
    .nc-alert-tipo.neg  {{ background:rgba(220,38,38,0.08);color:{t['negative']}; }}
    .nc-alert-tipo.warn {{ background:rgba(217,119,6,0.08); color:{t['warning']}; }}
    .nc-alert-imp    {{ font-size:11px;font-weight:600;color:{t['accent']}; }}
    .nc-alert-client {{ font-size:12px;font-weight:600;color:{t['text_primary']};margin-bottom:1px; }}
    .nc-alert-inm    {{ font-size:10px;color:{t['text_muted']};margin-bottom:10px; }}
    .nc-alert-title  {{ font-size:13px;font-weight:600;color:{t['text_primary']};margin-bottom:4px;line-height:1.3; }}
    .nc-alert-desc   {{ font-size:11px;color:{t['text_secondary']};line-height:1.4;margin-bottom:10px; }}
    .nc-alert-action {{ display:flex;align-items:center;gap:6px;font-size:10px;color:{t['accent']};font-weight:600;padding-top:8px;border-top:1px solid {t['card_border']}; }}

    /* MODELO 100 / CHECKS */
    .nc-m100 {{ width:100%;background:{t['card_bg']};border:1px solid {t['card_border']};border-radius:12px;border-collapse:separate;border-spacing:0;font-size:12px;box-shadow:0 1px 3px rgba(0,0,0,0.05); }}
    .nc-m100 thead th {{ background:{t['accent_light']};font-size:9px;letter-spacing:0.10em;text-transform:uppercase;color:{t['accent']};font-weight:600;padding:10px 12px;border-bottom:1px solid {t['card_border']}; }}
    .nc-m100 thead th:first-child {{ border-radius:12px 0 0 0; }}
    .nc-m100 thead th:last-child  {{ border-radius:0 12px 0 0;text-align:right; }}
    .nc-m100 tbody td {{ padding:9px 12px;border-bottom:1px solid {t['card_border']};color:{t['text_primary']}; }}
    .nc-m100 tbody td.r {{ text-align:right; }}
    .nc-m100 tbody tr:nth-child(even) td {{ background:{t['accent_light']};opacity:0.6; }}
    .nc-m100 tbody tr.sum   td {{ background:{t['accent_light']};font-weight:600;border-top:1px solid {t['card_border']}; }}
    .nc-m100 tbody tr.final td {{ background:{t['accent_pastel']};font-weight:700;color:{t['accent']}; }}
    .nc-chk-item {{ display:flex;align-items:center;gap:10px;padding:8px 14px;border-bottom:1px solid {t['card_border']};font-size:12px; }}
    .nc-chk-item:last-child {{ border-bottom:none; }}
    .nc-chk-on  {{ width:14px;height:14px;background:{t['positive']};border-radius:3px;display:inline-flex;align-items:center;justify-content:center;color:white;font-size:10px;flex-shrink:0; }}
    .nc-chk-off {{ width:14px;height:14px;border:1px solid {t['negative']};border-radius:3px;display:inline-flex;align-items:center;justify-content:center;color:{t['negative']};font-size:10px;flex-shrink:0; }}

    /* BOCADILLO IA */
    .nc-bocadillo {{ background:{t['bocadillo_bg']};border:1.5px solid {t['bocadillo_border']};border-radius:20px;padding:18px 20px;position:relative;box-shadow:{t['bocadillo_shadow']};margin-bottom:12px; }}
    .nc-bocadillo-label {{ font-size:10px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{t['bocadillo_header']};margin-bottom:8px; }}
    .nc-bocadillo-text  {{ font-size:13px;color:{t['text_primary']};line-height:1.65; }}
    .nc-bocadillo-response {{ background:{t['bocadillo_response']};border-radius:12px;padding:12px 14px;font-size:12px;color:{t['text_primary']};line-height:1.6;margin-top:12px;border-left:3px solid {t['accent']}; }}
  /* --- FORZAR COLORES EN FISCAL HUB --- */
    .stApp, .main, .fh-page {{
        background-color: var(--body-bg) !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background-color: var(--sidebar-bg) !important;
    }}
    .fh-card, .fh-tbl {{
        background-color: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
     
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# 3. CLAUDE API
# ─────────────────────────────────────────────────────────────────

def chat_with_claude(app: str, pregunta: str, contexto: dict) -> str:
    api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    client  = anthropic.Anthropic(api_key=api_key)
    prompts = {
        "capital": f"Eres el Asesor Patrimonial IA de Nolasco Capital. Tono cálido y útil. Patrimonio: {contexto}. Máximo 3 frases. Si hay acción: [ACCIÓN: nombre | param=valor]",
        "inmohub": f"Eres el AI Advisory de InmoHub. Tono analítico. Datos: {contexto}. Máximo 3 frases. Si hay acción: [ACCIÓN: nombre | param=valor]",
        "ficahub": f"Eres el Asesor Fiscal IA de FiscalHub. Tono formal. Datos: {contexto}. Máximo 3 frases. Si hay acción: [ACCIÓN: nombre | param=valor]",
    }
    msg = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=300,
        system=prompts[app],
        messages=[{"role": "user", "content": pregunta}]
    )
    return msg.content[0].text


def parse_response_and_action(respuesta: str) -> tuple:
    if "[ACCIÓN:" in respuesta:
        partes = respuesta.split("[ACCIÓN:")
        texto  = partes[0].strip()
        raw    = partes[1].replace("]", "").strip()
        lineas = [x.strip() for x in raw.split("|")]
        params = {}
        for l in lineas[1:]:
            if "=" in l:
                k, v = l.split("=", 1)
                params[k.strip()] = v.strip()
        return texto, {"accion": lineas[0], "params": params}
    return respuesta.strip(), None


def generar_insight_proactivo(app: str, contexto: dict) -> str:
    key = f"nc_insight_{app}"
    if key not in st.session_state:
        intros = {
            "capital": "Detecta el problema patrimonial más urgente. Una frase accionable.",
            "inmohub": "Identifica la oportunidad de captación más relevante. Máximo 2 frases.",
            "ficahub": "Detecta la alerta fiscal más urgente. Una frase precisa con números.",
        }
        api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        client  = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=120,
            system=intros[app],
            messages=[{"role": "user", "content": str(contexto)}]
        )
        st.session_state[key] = msg.content[0].text
    return st.session_state[key]


def bocadillo_ia_interactivo(app: str, contexto: dict, proactive_text: str = None):
    t           = APP_TOKENS[app]
    session_key = f"nc_chat_{app}"
    action_key  = f"nc_action_{app}"

    if session_key not in st.session_state: st.session_state[session_key] = []
    if action_key  not in st.session_state: st.session_state[action_key]  = None

    if proactive_text:
        st.markdown(f"""
        <div class="nc-bocadillo">
            <p class="nc-bocadillo-label">{t['ia_label']}</p>
            <p class="nc-bocadillo-text">{proactive_text}</p>
        </div>
        <div style="height:20px"></div>
        """, unsafe_allow_html=True)

    col_input, col_btn = st.columns([0.82, 0.18])
    with col_input:
        pregunta = st.text_input("", key=f"nc_input_{app}",
                                 placeholder=t['ia_placeholder'],
                                 label_visibility="collapsed")
    with col_btn:
        enviar = st.button("Enviar", key=f"nc_btn_{app}")

    sugerencias = {
        "capital": ["¿Cuál es mi mejor activo?", "¿Debo renegociar?", "Informe fiscal"],
        "inmohub": ["CP con mayor oportunidad", "Leads score >80%",   "Analizar CP 18005"],
        "ficahub": ["Deducciones pendientes",   "Clientes IRPF alto", "Alertas urgentes"],
    }
    chips = "".join([
        f'<span style="background:{t["accent_light"]};color:{t["accent"]};'
        f'font-size:10px;font-weight:500;padding:4px 10px;border-radius:20px;'
        f'margin-right:6px;display:inline-block;margin-bottom:4px">{s}</span>'
        for s in sugerencias.get(app, [])
    ])
    st.markdown(f'<div style="margin:6px 0 14px">{chips}</div>', unsafe_allow_html=True)

    if enviar and pregunta.strip():
        with st.spinner("Pensando..."):
            raw = chat_with_claude(app, pregunta.strip(), contexto)
            texto, accion = parse_response_and_action(raw)
        st.session_state[session_key].append({"role": "user",      "content": pregunta.strip()})
        st.session_state[session_key].append({"role": "assistant", "content": texto})
        if accion: st.session_state[action_key] = accion

    for msg in st.session_state[session_key]:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="text-align:right;margin:8px 0">
                <span style="background:{t['accent_light']};color:{t['text_primary']};
                    padding:8px 14px;border-radius:16px 16px 4px 16px;
                    font-size:12px;display:inline-block;max-width:80%">
                    {msg['content']}
                </span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="nc-bocadillo-response">{msg["content"]}</div>',
                unsafe_allow_html=True)

    accion_p = st.session_state.get(action_key)
    if accion_p:
        if st.button(f"✓ Ejecutar: {accion_p.get('accion','')}", key=f"nc_exec_{app}"):
            st.success("✅ Acción ejecutada")
            st.session_state[action_key] = None
