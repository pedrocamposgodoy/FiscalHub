# ================================================================
# kpi_renderer.py — KPIs con estilos 100% inline
# Altura fija garantizada. Marco oscuro. Relieve real.
# Sin dependencia de clases CSS externas.
# ================================================================

import streamlit as st

ACCENT_F = "#534AB7"
ACCENT_C = "#185FA5"
ACCENT_I = "#00C9A7"
GREEN    = "#059669"
RED      = "#DC2626"
AMBER    = "#D97706"
GREY     = "#475569"

_FONT   = "'Plus Jakarta Sans','DM Sans',system-ui,sans-serif"
_H      = "130px"   # Altura fija de todos los KPIs
_BORDER = "2px solid #94A3B8"   # Marco oscuro visible siempre
_SHADOW = ("0 6px 16px rgba(0,0,0,0.14),"
           "0 2px 6px rgba(0,0,0,0.10),"
           "inset 0 1px 0 rgba(255,255,255,0.85)")
_SHADOW_HOVER = ("0 10px 28px rgba(0,0,0,0.18),"
                 "0 4px 10px rgba(0,0,0,0.12),"
                 "inset 0 1px 0 rgba(255,255,255,0.85)")


def _kpi_html(label: str, value: str, color: str,
              subtitle: str = "", nav_label: str = "") -> str:
    """Genera el HTML de un KPI con todos los estilos inline."""
    sub = (f'<p style="font-size:11px;color:#94A3B8;margin:4px 0 0;'
           f'font-weight:500;font-family:{_FONT};">{subtitle}</p>'
           ) if subtitle else ""
    nav = (f'<p style="font-size:10px;color:{color};margin:6px 0 0;'
           f'font-weight:700;font-family:{_FONT};">{nav_label} →</p>'
           ) if nav_label else ""
    return f"""
    <div style="
        position:relative;
        background:#FFFFFF;
        border-radius:12px;
        border:{_BORDER};
        border-top:5px solid {color};
        box-shadow:{_SHADOW};
        padding-top:55%;
        overflow:hidden;
        box-sizing:border-box;
    ">
        <div style="
            position:absolute;
            top:0;left:0;right:0;bottom:0;
            padding:16px 20px;
            display:flex;
            flex-direction:column;
            justify-content:center;
        ">
            <p style="font-family:{_FONT};font-size:10px;font-weight:800;
                      color:#94A3B8;margin:0;text-transform:uppercase;
                      letter-spacing:0.10em;">{label}</p>
            <p style="font-family:{_FONT};font-size:2rem;font-weight:900;
                      color:{color};margin:6px 0 0;line-height:1;
                      letter-spacing:-0.02em;">{value}</p>
            {sub}{nav}
        </div>
    </div>"""


def render_kpi_row(kpis_data: list):
    """
    Renderiza KPIs en fila. Altura fija 130px garantizada.

    kpis_data: lista de dicts:
        label    (str)  — etiqueta uppercase
        value    (str)  — número o texto grande
        color    (str)  — color del valor y borde superior
        subtitle (str)  — subtexto pequeño. Opcional.
        nav      (str)  — si se pasa, el KPI es clicable y navega
                          a st.session_state.fh_menu = nav

    Ejemplo:
        render_kpi_row([
            {"label": "👥 Clientes",  "value": "2",
             "color": ACCENT_F, "subtitle": "2 críticos"},
            {"label": "🚨 Alertas",   "value": "10",
             "color": RED, "subtitle": "Antes 30 jun",
             "nav": "alertas"},
        ])
    """
    cols = st.columns(len(kpis_data))
    for col, kpi in zip(cols, kpis_data):
        label    = kpi.get("label", "")
        value    = str(kpi.get("value", ""))
        color    = kpi.get("color", GREY)
        subtitle = kpi.get("subtitle", "")
        nav      = kpi.get("nav", "")

        nav_label = "Ver →" if nav else ""
        html = _kpi_html(label, value, color, subtitle, nav_label)

        col.markdown(html, unsafe_allow_html=True)

        # Si tiene nav: botón invisible superpuesto
        if nav:
            col.markdown(
                f'<style>'
                f'.kpi-nav-{nav} button{{'
                f'position:absolute;top:-{_H};left:0;'
                f'width:100%;height:{_H};'
                f'background:transparent!important;'
                f'border:none!important;box-shadow:none!important;'
                f'color:transparent!important;font-size:0!important;'
                f'cursor:pointer!important;z-index:10;'
                f'}}</style>',
                unsafe_allow_html=True
            )
            col.markdown(
                f'<div class="kpi-nav-{nav}">',
                unsafe_allow_html=True
            )
            if col.button(" ", key=f"kpi_nav_{nav}_{label[:4]}",
                          use_container_width=True):
                st.session_state.fh_menu = nav
                st.rerun()
            col.markdown('</div>', unsafe_allow_html=True)


def render_kpi_large(label: str, value: str,
                     delta: str = None, color: str = ACCENT_F,
                     subtitle: str = None):
    """KPI grande para cabecera principal."""
    delta_html = ""
    if delta:
        pos    = delta.startswith("↑") or delta.startswith("+")
        dc     = GREEN if pos else RED
        dbg    = "rgba(5,150,105,0.1)" if pos else "rgba(220,38,38,0.1)"
        delta_html = (f'<div style="margin-top:10px;">'
                      f'<span style="background:{dbg};color:{dc};'
                      f'padding:4px 10px;border-radius:6px;'
                      f'font-size:12px;font-weight:700;">{delta}</span>'
                      f'</div>')
    sub_html = (f'<p style="font-size:12px;color:#94A3B8;margin:4px 0 0;">'
                f'{subtitle}</p>') if subtitle else ""

    st.markdown(f"""
    <div style="background:#FFFFFF;border-radius:12px;padding:24px;
                border:{_BORDER};border-top:5px solid {color};
                box-shadow:{_SHADOW};">
        <p style="font-family:{_FONT};font-size:10px;font-weight:800;
                  color:#94A3B8;margin:0 0 8px;text-transform:uppercase;
                  letter-spacing:0.10em;">{label}</p>
        <p style="font-family:{_FONT};font-size:2.4rem;font-weight:900;
                  color:{color};margin:0;line-height:1;
                  letter-spacing:-0.02em;">{value}</p>
        {sub_html}{delta_html}
    </div>""", unsafe_allow_html=True)
