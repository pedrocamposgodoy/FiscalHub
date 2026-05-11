# ================================================================
# kpi_renderer.py
# Renderizador de fichas KPI — usa las clases de nolasco_styles.py
#
# Uso:
#   from kpi_renderer import render_kpi_row, render_kpi_large
#
#   render_kpi_row([
#       {"label": "Ingresos",  "value": "6.101 €", "color": "#185FA5", "subtitle": "Brutos/mes"},
#       {"label": "Beneficio", "value": "3.842 €", "color": "#059669", "subtitle": "Neto/mes"},
#       {"label": "Alertas",   "value": "3",        "color": "#DC2626", "subtitle": "Críticas"},
#   ])
#
# IMPORTANTE: inject_global_css(app) debe haberse llamado antes en main().
# kpi_renderer NO importa nolasco_styles — solo usa sus clases CSS.
# ================================================================

import streamlit as st

# Colores semánticos — alineados con los tokens de nolasco_styles
ACCENT  = "#185FA5"   # azul Capital (por defecto)
ACCENT_I= "#00C9A7"   # verde InmoHub
ACCENT_F= "#534AB7"   # morado FiscalHub
GREEN   = "#059669"
RED     = "#DC2626"
AMBER   = "#D97706"
GREY    = "#475569"


def render_kpi_row(kpis_data: list):
    """
    Renderiza múltiples KPIs en fila.

    kpis_data: lista de dicts con:
        label    (str)  — título en mayúsculas pequeñas
        value    (str)  — número o texto grande
        color    (str)  — color del valor (hex). Default: GREY
        subtitle (str)  — texto pequeño debajo. Opcional.

    Ejemplo:
        render_kpi_row([
            {"label": "Clientes",  "value": "2",       "color": ACCENT_F},
            {"label": "Inmuebles", "value": "9",       "color": ACCENT_F},
            {"label": "Alertas",   "value": "10",      "color": RED, "subtitle": "Antes 30 jun"},
            {"label": "Impacto",   "value": "0 €",     "color": AMBER},
        ])
    """
    cols = st.columns(len(kpis_data))
    for col, kpi in zip(cols, kpis_data):
        label    = kpi.get("label", "")
        value    = kpi.get("value", "")
        color    = kpi.get("color", GREY)
        subtitle = kpi.get("subtitle", "")

        # Borde superior coloreado = acento visual de la ficha
        border_top_color = color

        sub_html = (
            f'<p style="font-size:11px;color:#94A3B8;margin:6px 0 0;font-weight:500;">'
            f'{subtitle}</p>'
        ) if subtitle else ""

        col.markdown(f"""
        <div style="
            background: #FFFFFF;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #E2E8F0;
            border-top: 3px solid {border_top_color};
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            height: 100%;
        ">
            <p style="
                font-size: 10px;
                font-weight: 600;
                color: #94A3B8;
                margin: 0 0 8px;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            ">{label}</p>
            <p style="
                font-family: 'Playfair Display', serif;
                font-size: 28px;
                font-weight: 700;
                color: {color};
                margin: 0;
                line-height: 1;
            ">{value}</p>
            {sub_html}
        </div>
        """, unsafe_allow_html=True)


def render_kpi_large(label: str, value: str,
                     delta: str = None, color: str = ACCENT,
                     subtitle: str = None):
    """
    Renderiza un único KPI grande. Ideal para cabecera principal.

    delta: texto opcional tipo "↑ 2.896 €" o "+ 12%"
           Si empieza con ↑ o + → verde. Si ↓ o - → rojo.
    """
    # Delta badge
    delta_html = ""
    if delta:
        positive  = delta.startswith("↑") or delta.startswith("+")
        d_color   = GREEN if positive else RED
        d_bg      = "rgba(5,150,105,0.1)" if positive else "rgba(220,38,38,0.1)"
        delta_html = f"""
        <div style="margin-top: 12px;">
            <span style="
                background: {d_bg};
                color: {d_color};
                padding: 4px 10px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            ">{delta}</span>
        </div>
        """

    sub_html = (
        f'<p style="font-size:12px;color:#94A3B8;margin:6px 0 0;">{subtitle}</p>'
    ) if subtitle else ""

    st.markdown(f"""
    <div style="
        background: #FFFFFF;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #E2E8F0;
        border-top: 3px solid {color};
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    ">
        <p style="
            font-size: 11px;
            font-weight: 600;
            color: #94A3B8;
            margin: 0 0 10px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        ">{label}</p>
        <p style="
            font-family: 'Playfair Display', serif;
            font-size: 36px;
            font-weight: 700;
            color: {color};
            margin: 0;
            line-height: 1;
        ">{value}</p>
        {sub_html}
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_kpi_mini(label: str, value: str, color: str = GREY):
    """
    KPI compacto para sidebars o espacios reducidos.
    Sin borde superior, más pequeño.
    """
    st.markdown(f"""
    <div style="
        background: rgba(255,255,255,0.06);
        border-radius: 8px;
        padding: 10px 12px;
        border: 1px solid rgba(255,255,255,0.08);
    ">
        <p style="font-size:9px;font-weight:600;color:#94A3B8;margin:0 0 4px;
                  text-transform:uppercase;letter-spacing:0.08em;">{label}</p>
        <p style="font-family:'Playfair Display',serif;font-size:20px;
                  font-weight:700;color:{color};margin:0;line-height:1;">{value}</p>
    </div>
    """, unsafe_allow_html=True)
