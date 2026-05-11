"""
nolasco_styles.py
=================
Módulo compartido para Nolasco Capital, InmoHub y FicaHub.
Copia este archivo idéntico en los 3 repositorios.

Uso:
    from nolasco_styles import inject_global_css, bocadillo_ia_interactivo, chat_with_claude

    APP = "capital"   # o "inmohub" o "ficahub"
    inject_global_css(APP)
    bocadillo_ia_interactivo(APP, contexto)
"""

import os
import streamlit as st
import anthropic

# ─────────────────────────────────────────────
# 1. TOKENS POR APP
# ─────────────────────────────────────────────

APP_TOKENS = {
    "capital": {
        # Colores
        "sidebar_bg":         "#FFFFFF",
        "sidebar_accent":     "#185FA5",
        "body_bg":            "#F0F2F5",
        "card_bg":            "#FFFFFF",
        "accent":             "#185FA5",
        "accent_light":       "#EAF1FB",
        "accent_pastel":      "#BDDAF5",
        "text_primary":       "#1A1A2E",
        "text_secondary":     "#6B7280",
        "text_muted":         "#9CA3AF",
        "positive":           "#10B981",
        "negative":           "#EF4444",
        "warning":            "#F59E0B",
        # Bocadillo IA
        "bocadillo_shadow":   "5px 5px 0px #BDDAF5",
        "bocadillo_border":   "#185FA5",
        "bocadillo_header":   "#185FA5",
        "bocadillo_bg":       "#FFFFFF",
        "bocadillo_btn":      "#185FA5",
        "bocadillo_response": "#EAF1FB",
        # Tipografía
        "font_display":       "'Playfair Display', serif",
        "font_body":          "'DM Sans', sans-serif",
        # IA
        "ia_tone":            "amigable",
        "ia_placeholder":     "¿Qué quieres saber sobre tu patrimonio?",
        "ia_label":           "✦ Asesor Patrimonial IA",
        # Sidebar
        "sidebar_items": [
            ("🏠", "Torre de Control"),
            ("📊", "Benchmark"),
            ("💰", "Escudo Fiscal"),
            ("⚡", "Simuladores"),
            ("🤖", "Asesor IA"),
            ("🔒", "Privacidad"),
        ],
    },

    "inmohub": {
        # Colores
        "sidebar_bg":         "#0F2744",
        "sidebar_accent":     "#00C9A7",
        "body_bg":            "#0D1B2A",
        "card_bg":            "#1A2F4A",
        "accent":             "#00C9A7",
        "accent_light":       "#0D3A2A",
        "accent_pastel":      "#00C9A730",
        "text_primary":       "#FFFFFF",
        "text_secondary":     "#8899AA",
        "text_muted":         "#5A6A7A",
        "positive":           "#00C9A7",
        "negative":           "#FF4B4B",
        "warning":            "#FFB347",
        # Bocadillo IA
        "bocadillo_shadow":   "none",
        "bocadillo_border":   "#00C9A7",
        "bocadillo_header":   "#00C9A7",
        "bocadillo_bg":       "#0F2744",
        "bocadillo_btn":      "#00C9A7",
        "bocadillo_response": "#0D3A2A",
        # Tipografía
        "font_display":       "'DM Sans', sans-serif",
        "font_body":          "'DM Sans', sans-serif",
        # IA
        "ia_tone":            "analítico",
        "ia_placeholder":     "¿Qué zona o lead quieres analizar?",
        "ia_label":           "⬡ AI Advisory",
        # Sidebar
        "sidebar_items": [
            ("🏠", "Dashboard"),
            ("📡", "Radar Mercado"),
            ("🛒", "Lead Marketplace"),
            ("👥", "Fidelización"),
            ("🤖", "AI Advisory"),
            ("⚙️", "Configuración"),
        ],
    },

    "ficahub": {
        # Colores
        "sidebar_bg":         "#1e293b",
        "sidebar_accent":     "#bc84ee",
        "body_bg":            "#F8F7FF",
        "card_bg":            "#FFFFFF",
        "accent":             "#534AB7",
        "accent_light":       "#EEEDFE",
        "accent_pastel":      "#D8D5F8",
        "text_primary":       "#1e293b",
        "text_secondary":     "#64748B",
        "text_muted":         "#94A3B8",
        "positive":           "#059669",
        "negative":           "#DC2626",
        "warning":            "#D97706",
        # Bocadillo IA
        "bocadillo_shadow":   "none",
        "bocadillo_border":   "#bc84ee",
        "bocadillo_header":   "#534AB7",
        "bocadillo_bg":       "#FFFFFF",
        "bocadillo_btn":      "#534AB7",
        "bocadillo_response": "#EEEDFE",
        # Tipografía
        "font_display":       "'Playfair Display', serif",
        "font_body":          "'DM Sans', sans-serif",
        # IA
        "ia_tone":            "profesional",
        "ia_placeholder":     "¿Qué cliente o deducción quieres revisar?",
        "ia_label":           "◈ Asesor Fiscal IA",
        # Sidebar
        "sidebar_items": [
            ("📊", "Panel Global"),
            ("👤", "Clientes"),
            ("📋", "IRPF 2025"),
            ("⚠️", "Alertas"),
            ("🤖", "Asesor IA"),
            ("⚙️", "Config"),
        ],
    },
}


# ─────────────────────────────────────────────
# 2. GOOGLE FONTS + CSS BASE
# ─────────────────────────────────────────────

def inject_global_css(app: str):
    """
    Inyecta el CSS completo en Streamlit.
    Llama una vez al inicio del app.py.
    """
    t = APP_TOKENS[app]
    is_dark = app == "inmohub"

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    /* ── RESET ── */
    * {{ box-sizing: border-box; }}

    /* ── BODY ── */
    .stApp {{
        background-color: {t['body_bg']} !important;
        font-family: {t['font_body']};
        color: {t['text_primary']} !important;
    }}

    /* Garantizar visibilidad de texto en todo el body */
    .stApp * {{
        color: {t['text_primary']} !important;
    }}

    .stApp p, .stApp span, .stApp div, .stApp label {{
        color: {t['text_primary']} !important;
    }}

    /* ── SIDEBAR ── */
    [data-testid="stSidebar"] {{
        background-color: {t['sidebar_bg']} !important;
        border-right: 0.5px solid {'rgba(255,255,255,0.08)' if is_dark else 'rgba(0,0,0,0.06)'};
    }}

    /* Texto del sidebar: blanco si es dark, gris si es light */
    [data-testid="stSidebar"] {{
        color: {'#8899AA' if is_dark else '#64748B'} !important;
    }}

    [data-testid="stSidebar"] * {{
        color: {'#8899AA' if is_dark else '#64748B'} !important;
    }}

    /* Texto del sidebar sin !important global para no romper nav */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {{
        color: {'#8899AA' if is_dark else '#4B5563'};
    }}

    /* Botones sidebar: transparentes con texto legible */
    [data-testid="stSidebar"] .stButton > button {{
        background: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        font-weight: 400 !important;
        padding: 8px 14px !important;
        text-align: left !important;
        width: 100% !important;
        justify-content: flex-start !important;
        box-shadow: none !important;
    }}

    /* Texto del botón sidebar - CRÍTICO para ficahub */
    [data-testid="stSidebar"] .stButton > button {{
        color: {'#FFFFFF' if is_dark else '#64748B'} !important;
    }}

    [data-testid="stSidebar"] .stButton > button span {{
        color: {'#FFFFFF' if is_dark else '#64748B'} !important;
    }}

    [data-testid="stSidebar"] .stButton > button p {{
        color: {'#FFFFFF' if is_dark else '#64748B'} !important;
    }}

    [data-testid="stSidebar"] .stButton > button:hover {{
        background: {'rgba(255,255,255,0.06)' if is_dark else 'rgba(83,74,183,0.08)'} !important;
        color: {'#ffffff' if is_dark else '#534AB7'} !important;
    }}

    [data-testid="stSidebar"] .stButton > button:hover span {{
        color: {'#ffffff' if is_dark else '#534AB7'} !important;
    }}

    [data-testid="stSidebar"] .stRadio label {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        border-radius: 10px;
        cursor: pointer;
        transition: background 0.15s;
        font-size: 13px;
        font-family: {t['font_body']};
        color: {'#8899AA' if is_dark else '#64748B'} !important;
    }}

    [data-testid="stSidebar"] .stRadio label:hover {{
        background: {'rgba(255,255,255,0.06)' if is_dark else 'rgba(83,74,183,0.08)'};
        color: {'#ffffff' if is_dark else '#534AB7'} !important;
    }}

    /* ── CARDS ── */
    .nc-card {{
        background: {t['card_bg']};
        border-radius: 20px;
        padding: 24px;
        box-shadow: {'0 2px 12px rgba(0,0,0,0.2)' if is_dark else '0 4px 24px rgba(0,0,0,0.06)'};
        border: {'0.5px solid rgba(255,255,255,0.06)' if is_dark else '0.5px solid rgba(0,0,0,0.04)'};
        height: 100%;
    }}

    .nc-card-sm {{
        background: {t['card_bg']};
        border-radius: 16px;
        padding: 16px;
        box-shadow: {'0 2px 8px rgba(0,0,0,0.2)' if is_dark else '0 2px 12px rgba(0,0,0,0.05)'};
        border: {'0.5px solid rgba(255,255,255,0.06)' if is_dark else '0.5px solid rgba(0,0,0,0.04)'};
    }}

    /* ── TIPOGRAFÍA ── */
    .nc-number {{
        font-family: {t['font_display']};
        font-size: 2.25rem;
        font-weight: 700;
        color: {t['text_primary']};
        line-height: 1;
        letter-spacing: -0.02em;
    }}

    .nc-number-lg {{
        font-family: {t['font_display']};
        font-size: 2.75rem;
        font-weight: 700;
        color: {t['accent']};
        line-height: 1;
        letter-spacing: -0.03em;
    }}

    .nc-label {{
        font-family: {t['font_body']};
        font-size: 11px;
        font-weight: 500;
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
        font-family: {t['font_body']};
        font-size: 12px;
        color: {t['text_secondary']};
    }}

    /* ── DELTA BADGES ── */
    .nc-delta-pos {{
        display: inline-flex;
        align-items: center;
        gap: 3px;
        font-size: 11px;
        font-weight: 500;
        color: {t['positive']};
        background: {'rgba(16,185,129,0.1)' if not is_dark else 'rgba(0,201,167,0.1)'};
        padding: 2px 8px;
        border-radius: 20px;
    }}

    .nc-delta-neg {{
        display: inline-flex;
        align-items: center;
        gap: 3px;
        font-size: 11px;
        font-weight: 500;
        color: {t['negative']};
        background: rgba(239,68,68,0.1);
        padding: 2px 8px;
        border-radius: 20px;
    }}

    /* ── BOCADILLO IA ── */
    .nc-bocadillo {{
        background: {t['bocadillo_bg']};
        border: 1.5px solid {t['bocadillo_border']};
        border-radius: 20px;
        padding: 18px 20px;
        position: relative;
        box-shadow: {t['bocadillo_shadow']};
        margin-bottom: 12px;
    }}

    .nc-bocadillo::after {{
        content: '';
        position: absolute;
        bottom: -12px;
        left: 24px;
        width: 0;
        height: 0;
        border-left: 10px solid transparent;
        border-right: 10px solid transparent;
        border-top: 12px solid {t['bocadillo_border']};
    }}

    .nc-bocadillo-label {{
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: {t['bocadillo_header']};
        margin-bottom: 8px;
    }}

    .nc-bocadillo-text {{
        font-family: {t['font_body']};
        font-size: 13px;
        color: {t['text_primary']};
        line-height: 1.65;
    }}

    .nc-bocadillo-response {{
        background: {t['bocadillo_response']};
        border-radius: 12px;
        padding: 12px 14px;
        font-size: 12px;
        color: {t['text_primary']};
        line-height: 1.6;
        margin-top: 12px;
        border-left: 3px solid {t['accent']};
    }}

    /* ── INPUTS ── */
    .stTextInput > div > div > input {{
        border-radius: 12px !important;
        border: 1.5px solid {t['accent_pastel']} !important;
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

    /* ── BUTTONS GLOBALES (fuera del sidebar) ── */
    /* Solo afecta botones en el main content, no en sidebar */
    .main .stButton > button,
    [data-testid="stMainBlockContainer"] .stButton > button {{
        background: {t['bocadillo_btn']} !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-family: {t['font_body']} !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 10px 20px !important;
        cursor: pointer !important;
        transition: opacity 0.15s !important;
    }}

    .main .stButton > button:hover,
    [data-testid="stMainBlockContainer"] .stButton > button:hover {{
        opacity: 0.85 !important;
    }}

    /* Botón primary explícito (type=primary) — siempre acento */
    button[kind="primary"] {{
        background: {t['accent']} !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
    }}

    /* Botón secondary — outline */
    button[kind="secondary"] {{
        background: transparent !important;
        color: {t['accent']} !important;
        border: 1.5px solid {t['accent_pastel']} !important;
        border-radius: 12px !important;
    }}

    /* ── PILLS ── */
    .nc-pill {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.05em;
    }}

    .nc-pill-accent {{
        background: {t['accent_light']};
        color: {t['accent']};
    }}

    /* ── IMAGEN EN CARD ── */
    .nc-card-img {{
        width: 100%;
        height: 120px;
        object-fit: cover;
        border-radius: 12px;
        margin-bottom: 12px;
    }}

    /* ── SEPARADOR ── */
    .nc-divider {{
        height: 0.5px;
        background: {'rgba(255,255,255,0.08)' if is_dark else 'rgba(0,0,0,0.06)'};
        margin: 16px 0;
    }}

    /* ── METRIC ROW ── */
    .nc-metric-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 0.5px solid {'rgba(255,255,255,0.05)' if is_dark else 'rgba(0,0,0,0.04)'};
    }}

    .nc-metric-row:last-child {{
        border-bottom: none;
    }}

    /* ── HIDE STREAMLIT DEFAULTS ── */
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{ padding-top: 2rem !important; }}
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 3. COMPONENTES HTML REUTILIZABLES
# ─────────────────────────────────────────────

def card_kpi(app: str, label: str, value: str, delta: str = None, delta_pos: bool = True, subtitle: str = None):
    """KPI card estilo imagen: número serif grande + label + delta."""
    t = APP_TOKENS[app]
    delta_html = ""
    if delta:
        cls = "nc-delta-pos" if delta_pos else "nc-delta-neg"
        arrow = "↑" if delta_pos else "↓"
        delta_html = f'<span class="{cls}">{arrow} {delta}</span>'

    subtitle_html = f'<p class="nc-subtitle" style="margin-top:6px">{subtitle}</p>' if subtitle else ""

    html = f"""
    <div class="nc-card">
        <p class="nc-label">{label}</p>
        <p class="nc-number" style="margin: 8px 0 6px; color:{t['accent']}">{value}</p>
        {delta_html}
        {subtitle_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def card_metric_list(app: str, title: str, items: list[tuple]):
    """
    Card con lista de métricas.
    items = [("Inmueble", "€2.200/mes", "+3%", True), ...]
    """
    t = APP_TOKENS[app]
    rows = ""
    for item in items:
        name, value, delta, pos = item
        delta_cls = "nc-delta-pos" if pos else "nc-delta-neg"
        arrow = "↑" if pos else "↓"
        rows += f"""
        <div class="nc-metric-row">
            <span style="font-size:13px; color:{t['text_primary']}">{name}</span>
            <span style="font-size:13px; font-weight:600; color:{t['text_primary']}">{value}</span>
            <span class="{delta_cls}">{arrow} {delta}</span>
        </div>
        """

    html = f"""
    <div class="nc-card">
        <p class="nc-title">{title}</p>
        <div class="nc-divider"></div>
        {rows}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def card_image_editorial(app: str, label: str, title: str, subtitle: str,
                          value: str = None, cta: str = None,
                          bg_color: str = None):
    """
    Card editorial estilo imagen de referencia:
    label pequeño + título serif + subtítulo + valor grande.
    Sin imágenes reales (Streamlit Cloud no tiene assets).
    Se simula con fondo de color pastel.
    """
    t = APP_TOKENS[app]
    bg = bg_color or t['accent_light']

    value_html = f'<p class="nc-number-lg" style="margin: 10px 0 4px">{value}</p>' if value else ""
    cta_html = f'<p style="font-size:11px;font-weight:600;color:{t["accent"]};cursor:pointer;margin-top:10px">{cta} →</p>' if cta else ""

    html = f"""
    <div class="nc-card" style="background:{bg};border:none">
        <p class="nc-label">{label}</p>
        <p class="nc-title" style="margin-top:8px">{title}</p>
        <p class="nc-subtitle">{subtitle}</p>
        {value_html}
        {cta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 4. BOCADILLO IA INTERACTIVO
# ─────────────────────────────────────────────

def bocadillo_ia_interactivo(app: str, contexto: dict, proactive_text: str = None):
    """
    Renderiza bocadillo IA interactivo con:
    - Mensaje proactivo inicial (insight automático)
    - Input text para preguntar
    - Respuesta de Claude con posible acción
    - Botón "Ejecutar" si hay acción

    contexto: dict con datos de la app para que Claude responda con contexto real.
    """
    t = APP_TOKENS[app]
    session_key = f"nc_chat_{app}"
    action_key  = f"nc_action_{app}"

    # Inicializar session state
    if session_key not in st.session_state:
        st.session_state[session_key] = []
    if action_key not in st.session_state:
        st.session_state[action_key] = None

    # Bocadillo proactivo (mensaje inicial de Claude)
    if proactive_text:
        st.markdown(f"""
        <div class="nc-bocadillo">
            <p class="nc-bocadillo-label">{t['ia_label']}</p>
            <p class="nc-bocadillo-text">{proactive_text}</p>
        </div>
        <div style="height:20px"></div>
        """, unsafe_allow_html=True)

    # Input del usuario
    col_input, col_btn = st.columns([0.82, 0.18])
    with col_input:
        pregunta = st.text_input(
            "",
            key=f"nc_input_{app}",
            placeholder=t['ia_placeholder'],
            label_visibility="collapsed"
        )
    with col_btn:
        enviar = st.button("Enviar", key=f"nc_btn_{app}")

    # Sugerencias rápidas según app
    _render_quick_suggestions(app)

    # Procesar pregunta
    if enviar and pregunta.strip():
        with st.spinner("Pensando..."):
            respuesta_raw = chat_with_claude(app, pregunta.strip(), contexto)
            respuesta_texto, accion = parse_response_and_action(respuesta_raw)

        st.session_state[session_key].append({"role": "user",      "content": pregunta.strip()})
        st.session_state[session_key].append({"role": "assistant", "content": respuesta_texto})
        if accion:
            st.session_state[action_key] = accion

    # Historial de conversación
    for msg in st.session_state[session_key]:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="text-align:right; margin: 8px 0">
                <span style="
                    background:{t['accent_light']};
                    color:{t['text_primary']};
                    padding:8px 14px;
                    border-radius:16px 16px 4px 16px;
                    font-size:12px;
                    display:inline-block;
                    max-width:80%">{msg['content']}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="nc-bocadillo-response">{msg['content']}</div>
            """, unsafe_allow_html=True)

    # Botón ejecutar si hay acción pendiente
    accion_pendiente = st.session_state.get(action_key)
    if accion_pendiente:
        nombre = accion_pendiente.get("accion", "Acción")
        if st.button(f"✓ Ejecutar: {nombre}", key=f"nc_exec_{app}"):
            resultado = _execute_action(app, accion_pendiente)
            st.success(f"✅ {resultado}")
            st.session_state[action_key] = None


def _render_quick_suggestions(app: str):
    """Chips de sugerencias rápidas debajo del input."""
    suggestions = {
        "capital": [
            "¿Cuál es mi mejor activo?",
            "¿Debo renegociar Abarqueros?",
            "Generar informe fiscal",
        ],
        "inmohub": [
            "CP con mayor oportunidad",
            "Leads con score >80%",
            "Analizar CP 18005",
        ],
        "ficahub": [
            "Deducciones pendientes",
            "Clientes con IRPF alto",
            "Alertas antes de diciembre",
        ],
    }

    t = APP_TOKENS[app]
    chips = suggestions.get(app, [])
    chips_html = "".join([
        f'<span style="'
        f'background:{t["accent_light"]};'
        f'color:{t["accent"]};'
        f'font-size:10px;'
        f'font-weight:500;'
        f'padding:4px 10px;'
        f'border-radius:20px;'
        f'cursor:pointer;'
        f'margin-right:6px;'
        f'display:inline-block;'
        f'margin-bottom:4px'
        f'">{s}</span>'
        for s in chips
    ])
    st.markdown(
        f'<div style="margin: 6px 0 14px">{chips_html}</div>',
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────
# 5. CLAUDE API
# ─────────────────────────────────────────────

def chat_with_claude(app: str, pregunta: str, contexto: dict) -> str:
    """
    Llama a Claude con system prompt adaptado por app.

    En MVP usa ANTHROPIC_API_KEY de secrets.toml (la tuya).
    En producción: each client has their own key in Supabase.

    El system prompt instruye a Claude a terminar con:
    [ACCIÓN: nombre_accion | param=valor] si hay algo ejecutable.
    """

    # API Key: MVP = la tuya, producción = la del cliente
    api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    system_prompts = {
        "capital": f"""Eres el Asesor Patrimonial IA de Nolasco Capital.
Hablas directamente al propietario. Tono cálido, directo y útil.
Conoces su patrimonio real: {contexto}

Reglas:
- Responde en máximo 3 frases. Sin jerga técnica.
- Usa números reales del contexto.
- Si propones una acción ejecutable, termina con:
  [ACCIÓN: nombre_accion | param1=valor1 | param2=valor2]

Acciones disponibles:
  - generar_contrato | inmueble=nombre | tipo=larga/temporada
  - crear_alerta | inmueble=nombre | motivo=texto
  - calcular_renta_mercado | inmueble=nombre
  - exportar_irpf | ejercicio=2025
""",

        "inmohub": f"""Eres el AI Advisory de InmoHub. Hablas a profesionales inmobiliarios.
Datos de mercado disponibles: {contexto}

Reglas:
- Tono analítico y directo. Prioriza métricas.
- Máximo 3 frases. Datos concretos.
- Si hay acción ejecutable:
  [ACCIÓN: nombre_accion | param1=valor1]

Acciones disponibles:
  - filtrar_leads | cp=18005 | brecha_min=20
  - exportar_leads | formato=csv
  - generar_informe_zona | cp=18001
  - crear_alerta_cp | cp=18005 | condicion=brecha>20
""",

        "ficahub": f"""Eres el Asesor Fiscal IA de FicaHub.
Hablas a asesores fiscales profesionales. Tono formal y preciso.
Datos disponibles: {contexto}

Reglas:
- Responde en máximo 3 frases. Menciona casillas del modelo 100 si aplica.
- Si hay acción ejecutable:
  [ACCIÓN: nombre_accion | param1=valor1]

Acciones disponibles:
  - generar_modelo_100 | cliente_id=id | ejercicio=2025
  - crear_alerta_fiscal | cliente_id=id | motivo=texto
  - exportar_checklist | ejercicio=2025
  - calcular_deduccion | cliente_id=id | tipo=eficiencia_energetica
""",
    }

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=system_prompts[app],
        messages=[{"role": "user", "content": pregunta}]
    )

    return message.content[0].text


def parse_response_and_action(respuesta: str) -> tuple:
    """
    Extrae texto limpio y acción estructurada de la respuesta de Claude.

    Returns:
        (texto_para_mostrar, {"accion": "nombre", "params": {...}}) o (texto, None)
    """
    if "[ACCIÓN:" in respuesta:
        partes = respuesta.split("[ACCIÓN:")
        texto = partes[0].strip()
        accion_raw = partes[1].replace("]", "").strip()

        lineas = [x.strip() for x in accion_raw.split("|")]
        accion_name = lineas[0]
        params = {}
        for linea in lineas[1:]:
            if "=" in linea:
                k, v = linea.split("=", 1)
                params[k.strip()] = v.strip()

        return texto, {"accion": accion_name, "params": params}

    return respuesta.strip(), None


# ─────────────────────────────────────────────
# 6. EJECUTAR ACCIONES
# ─────────────────────────────────────────────

def _execute_action(app: str, accion: dict) -> str:
    """
    Ejecuta la acción que Claude sugirió.
    Retorna string de resultado para mostrar al usuario.

    Amplía cada bloque según las funciones reales de supabase_db.py.
    """
    nombre = accion.get("accion", "")
    params = accion.get("params", {})

    if app == "capital":
        if nombre == "generar_contrato":
            # from supabase_db import generar_contrato_pdf
            # generar_contrato_pdf(params["inmueble"], params.get("tipo", "larga"))
            return f"Contrato generado para {params.get('inmueble', 'inmueble')} (PDF listo para descargar)"

        elif nombre == "crear_alerta":
            # from supabase_db import crear_alerta_inmueble
            # crear_alerta_inmueble(params["inmueble"], params["motivo"])
            return f"Alerta creada para {params.get('inmueble', 'inmueble')}"

        elif nombre == "exportar_irpf":
            return f"Borrador IRPF {params.get('ejercicio', '2025')} generado"

        elif nombre == "calcular_renta_mercado":
            return f"Cálculo de renta mercado completado para {params.get('inmueble', 'inmueble')}"

    elif app == "inmohub":
        if nombre == "filtrar_leads":
            # from supabase_db import filtrar_leads_por_cp
            # filtrar_leads_por_cp(params["cp"], float(params.get("brecha_min", 0)))
            return f"Mostrando leads CP {params.get('cp', '')} con brecha >{params.get('brecha_min', 0)}%"

        elif nombre == "exportar_leads":
            return "CSV de leads exportado"

        elif nombre == "generar_informe_zona":
            return f"Informe de zona CP {params.get('cp', '')} generado"

    elif app == "ficahub":
        if nombre == "generar_modelo_100":
            return f"Modelo 100 generado para cliente {params.get('cliente_id', '')} — ejercicio {params.get('ejercicio', '2025')}"

        elif nombre == "crear_alerta_fiscal":
            return f"Alerta fiscal creada: {params.get('motivo', '')}"

        elif nombre == "calcular_deduccion":
            return f"Deducción calculada para cliente {params.get('cliente_id', '')}"

    return "Acción ejecutada correctamente"


# ─────────────────────────────────────────────
# 7. INSIGHT PROACTIVO (se llama al cargar la página)
# ─────────────────────────────────────────────

def generar_insight_proactivo(app: str, contexto: dict) -> str:
    """
    Genera el texto inicial del bocadillo IA al cargar la página.
    Corto: 1-2 frases máximo.

    Usa caché de session_state para no llamar a la API en cada rerender.
    """
    cache_key = f"nc_insight_{app}"

    if cache_key not in st.session_state:
        intros = {
            "capital": "Analiza brevemente la situación patrimonial del usuario y detecta el problema más urgente. Una frase accionable. Usa los datos concretos.",
            "inmohub": "Identifica la oportunidad de captación más relevante en este momento. Máximo 2 frases con datos concretos.",
            "ficahub": "Detecta la alerta fiscal más urgente entre los clientes. Una frase precisa con números.",
        }

        api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=120,
            system=intros[app],
            messages=[{"role": "user", "content": str(contexto)}]
        )
        st.session_state[cache_key] = message.content[0].text

    return st.session_state[cache_key]


# ─────────────────────────────────────────────
# 8. SIDEBAR ESTILIZADO
# ─────────────────────────────────────────────

def render_sidebar(app: str, active_item: str = None) -> str:
    """
    Renderiza el sidebar con el estilo de la imagen de referencia.
    Retorna el item seleccionado.
    """
    t = APP_TOKENS[app]
    items = t["sidebar_items"]
    labels = [f"{icon}  {label}" for icon, label in items]

    with st.sidebar:
        # Logo
        st.markdown(f"""
        <div style="padding: 20px 0 30px; text-align: left">
            <p style="
                font-family: {t['font_display']};
                font-size: 1.3rem;
                font-weight: 700;
                color: {'#FFFFFF' if app == 'inmohub' else t['accent']};
                margin: 0;
                letter-spacing: -0.02em
            ">{'InmoHub' if app == 'inmohub' else 'Nolasco' if app == 'capital' else 'FicaHub'}</p>
            <p style="
                font-size: 10px;
                font-weight: 500;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                color: {t['text_muted']};
                margin: 2px 0 0
            ">{'Real Estate Intelligence' if app == 'inmohub' else 'Gestión Patrimonial' if app == 'capital' else 'Asesoría Fiscal IA'}</p>
        </div>
        """, unsafe_allow_html=True)

        selected = st.radio(
            "",
            labels,
            label_visibility="collapsed",
            key=f"nc_nav_{app}"
        )

    return selected
