# ================================================================
# kpi_renderer.py
# Renderizador de fichas KPI — estilo cuadrado compacto
# Coherente con nolasco_styles.py
#
# Uso:
#   from kpi_renderer import render_kpi_row, render_kpi_large
#
# inject_global_css(app) debe haberse llamado antes en main().
# ================================================================

import streamlit as st

ACCENT  = "#185FA5"
ACCENT_F= "#534AB7"
ACCENT_I= "#00C9A7"
GREEN   = "#059669"
RED     = "#DC2626"
AMBER   = "#D97706"
GREY    = "#475569"

_FONT = "'Plus Jakarta Sans', 'DM Sans', sans-serif"


def render_kpi_row(kpis_data: list):
    """
    Renderiza KPIs en fila — estilo cuadrado compacto.

    kpis_data: lista de dicts:
        label    (str)  — label uppercase pequeño
        value    (str)  — número grande
        color    (str)  — color del valor y borde superior
        subtitle (str)  — texto pequeño debajo. Opcional.

    Ejemplo:
        render_kpi_row([
            {"label": "Clientes",  "value": "2",   "color": ACCENT_F},
            {"label": "Alertas",   "value": "10",  "color": RED, "subtitle": "Antes 30 jun"},
            {"label": "Impacto",   "value": "0 €", "color": AMBER},
        ])
    """
    cols = st.columns(len(kpis_data))
    for col, kpi in zip(cols, kpis_data):
        label    = kpi.get("label", "")
        value    = kpi.get("value", "")
        color    = kpi.get("color", GREY)
        subtitle = kpi.get("subtitle", "")

        sub_html = (
            f'''<p style="font-size:11px;color:#94A3B8;margin:4px 0 0;font-weight:500;">'''
            + subtitle + "</p>"
        ) if subtitle else ""

        col.markdown(f"""
        <div style="
            background: #FFFFFF;
            border-radius: 12px;
            padding: 20px 22px;
            border: 1px solid #D8D5F8;
            border-top: 3px solid {color};
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
            min-height: 110px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            height: 100%;
        ">
            <p style="
                font-family: {_FONT};
                font-size: 10px;
                font-weight: 700;
                color: #94A3B8;
                margin: 0;
                text-transform: uppercase;
                letter-spacing: 0.10em;
            ">{label}</p>
            <p style="
                font-family: {_FONT};
                font-size: 1.9rem;
                font-weight: 800;
                color: {color};
                margin: 6px 0 4px;
                line-height: 1;
                letter-spacing: -0.02em;
            ">{value}</p>
            {sub_html}
        </div>
        """, unsafe_allow_html=True)


def render_kpi_large(label: str, value: str,
                     delta: str = None, color: str = ACCENT,
                     subtitle: str = None):
    """KPI grande para cabecera principal."""
    delta_html = ""
    if delta:
        positive  = delta.startswith("↑") or delta.startswith("+")
        d_color   = GREEN if positive else RED
        d_bg      = "rgba(5,150,105,0.1)" if positive else "rgba(220,38,38,0.1)"
        delta_html = f"""
        <div style="margin-top: 10px;">
            <span style="background:{d_bg};color:{d_color};
                padding:4px 10px;border-radius:6px;
                font-size:12px;font-weight:700;
                font-family:{_FONT};">{delta}</span>
        </div>"""

    sub_html = (
        f'''<p style="font-size:12px;color:#94A3B8;margin:4px 0 0;font-family:{_FONT};">'''
        + subtitle + "</p>"
    ) if subtitle else ""

    st.markdown(f"""
    <div style="
        background: #FFFFFF;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #D8D5F8;
        border-top: 3px solid {color};
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    ">
        <p style="font-family:{_FONT};font-size:10px;font-weight:700;
                  color:#94A3B8;margin:0 0 8px;
                  text-transform:uppercase;letter-spacing:0.10em;">{label}</p>
        <p style="font-family:{_FONT};font-size:2.4rem;font-weight:800;
                  color:{color};margin:0;line-height:1;letter-spacing:-0.02em;">{value}</p>
        {sub_html}
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_kpi_mini(label: str, value: str, color: str = GREY):
    """KPI compacto para espacios reducidos."""
    st.markdown(f"""
    <div style="
        background: rgba(255,255,255,0.12);
        border-radius: 8px;
        padding: 10px 12px;
        border: 1px solid rgba(255,255,255,0.15);
    ">
        <p style="font-family:{_FONT};font-size:9px;font-weight:700;
                  color:#94A3B8;margin:0 0 4px;
                  text-transform:uppercase;letter-spacing:0.08em;">{label}</p>
        <p style="font-family:{_FONT};font-size:1.3rem;font-weight:800;
                  color:{color};margin:0;line-height:1;">{value}</p>
    </div>
    """, unsafe_allow_html=True)
