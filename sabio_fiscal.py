# ================================================================
# sabio_fiscal.py
# Asesor Fiscal IA — FiscalHub
#
# Arquitectura idéntica a sabio_patrimonial.py de Nolasco Capital.
# Adaptado para análisis de decisiones fiscales proactivas.
#
# USO en fiscalhub_app.py:
#   from sabio_fiscal import render_sabio_fiscal
#   render_sabio_fiscal("ficha", contexto_dict, decisiones_dict)
# ================================================================

import streamlit as st
import anthropic
import os

ACCENT       = "#534AB7"
ACCENT_LIGHT = "#EEEDFE"
TEXT_PRI     = "#0F172A"

# ── SYSTEM PROMPTS ──────────────────────────────────────────────
SYSTEM_PROMPTS = {

    "ficha": """Eres el Asesor Fiscal IA de FiscalHub. Hablas a un asesor fiscal profesional.
Estás analizando un inmueble concreto y las decisiones fiscales que el asesor ha seleccionado.

DATOS DEL INMUEBLE:
{contexto}

DECISIONES ACTIVAS DEL ASESOR:
{decisiones}

IMPACTO CALCULADO:
- Base imponible original: {base_original} €
- Base imponible simulada: {base_simulada} €
- Ahorro estimado: {ahorro} €
- Reducción aplicada: {reduccion_pct}%

TU MISIÓN:
1. Valora si la combinación de decisiones es fiscalmente óptima y prudente ante Hacienda
2. Identifica si hay alguna decisión que pueda generar riesgo de inspección
3. Sugiere si hay alguna palanca adicional no seleccionada que mejoraría el resultado

REGLAS ESTRICTAS:
- Máximo 4 frases. Con números reales del contexto.
- Usa terminología fiscal correcta (casillas, artículos LIRPF si aplica)
- Tono profesional entre colegas. El asesor sabe de fiscalidad.
- Distingue claramente entre lo que es seguro y lo que tiene riesgo
- No inventas datos. Solo analizas lo que se te proporciona.""",

    "proactiva": """Eres el Asesor Fiscal IA de FiscalHub. Análisis proactivo de fin de año.
Estás proyectando la situación fiscal del inmueble si se tomaran acciones antes del 31 de diciembre.

DATOS DEL INMUEBLE:
{contexto}

MESES RESTANTES DEL AÑO: {meses_restantes}
INGRESOS ACUMULADOS A HOY: {ingresos_acumulados} €
RITMO PROYECTADO FIN DE AÑO: {ingresos_proyectados} €

TU MISIÓN:
- Si los ingresos proyectados son altos, sugiere qué gastos o mejoras anticipar antes del 31/12
- Si hay margen de maniobra, indica exactamente cuánto puede gastar sin superar el umbral óptimo
- Menciona plazos concretos (qué hacer en noviembre vs. diciembre)

REGLAS:
- Máximo 3 frases. Con euros y fechas concretas.
- Tono urgente si quedan menos de 3 meses. Preventivo si hay más tiempo.
- Solo lo que es fiscalmente seguro.""",
}

CHIPS = {
    "ficha": [
        "¿Es seguro ante inspección?",
        "¿Hay riesgo en esta combinación?",
        "¿Qué más puedo deducir?",
        "¿Reparación o mejora?",
    ],
    "proactiva": [
        "¿Cuánto puedo gastar antes de diciembre?",
        "¿Qué es mejor anticipar?",
        "¿Cómo reduzco la base ahora?",
    ],
}

LABELS = {
    "ficha":     "◈ Asesor Fiscal IA · Análisis de Decisiones",
    "proactiva": "◈ Asesor Fiscal IA · Fiscalidad Proactiva",
}


# ── API ─────────────────────────────────────────────────────────
def _get_api_key() -> str:
    try:
        return st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")
    except Exception:
        return os.getenv("ANTHROPIC_API_KEY", "")


def _llamar_claude(system: str, pregunta: str, max_tokens: int = 350) -> str:
    api_key = _get_api_key()
    if not api_key:
        return "Configura ANTHROPIC_API_KEY en los secrets para activar el Asesor Fiscal IA."
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": pregunta}]
        )
        return msg.content[0].text
    except Exception as e:
        return f"El Asesor IA no está disponible ({str(e)[:60]})."


def _insight_proactivo(seccion: str, contexto: dict, decisiones: dict,
                        base_original: float, base_simulada: float) -> str:
    """Insight automático al abrir la sección. Cacheado por inmueble+decisiones."""
    ahorro = base_original - base_simulada
    cache_key = f"sabio_fiscal_{seccion}_{hash(str(decisiones))}"

    if cache_key in st.session_state:
        return st.session_state[cache_key]

    ahorro_pct = round((ahorro / base_original * 100) if base_original else 0, 1)
    system = SYSTEM_PROMPTS[seccion].format(
        contexto=contexto,
        decisiones=decisiones,
        base_original=round(base_original, 2),
        base_simulada=round(base_simulada, 2),
        ahorro=round(ahorro, 2),
        reduccion_pct=ahorro_pct,
        meses_restantes=decisiones.get("meses_restantes", "—"),
        ingresos_acumulados=decisiones.get("ingresos_acumulados", "—"),
        ingresos_proyectados=decisiones.get("ingresos_proyectados", "—"),
    )
    resultado = _llamar_claude(system,
        "Analiza esta situación y da tu valoración más importante en 3 frases.",
        max_tokens=200)
    st.session_state[cache_key] = resultado
    return resultado


# ── RENDER PRINCIPAL ────────────────────────────────────────────
def render_sabio_fiscal(seccion: str, contexto: dict, decisiones: dict,
                         base_original: float = 0.0, base_simulada: float = 0.0):
    """
    Asesor Fiscal IA integrado en la ficha del inmueble.

    seccion:       "ficha" | "proactiva"
    contexto:      datos del inmueble (dict)
    decisiones:    decisiones activas del asesor (dict)
    base_original: base imponible sin cambios
    base_simulada: base imponible con las decisiones aplicadas
    """
    hist_key = f"sabio_fiscal_hist_{seccion}"
    if hist_key not in st.session_state:
        st.session_state[hist_key] = []

    label  = LABELS.get(seccion, "◈ Asesor Fiscal IA")
    chips  = CHIPS.get(seccion, [])
    ahorro = base_original - base_simulada

    with st.expander(f"🧠 {label}", expanded=True):

        # Insight proactivo automático
        with st.spinner("El Asesor IA está analizando las decisiones..."):
            insight = _insight_proactivo(seccion, contexto, decisiones,
                                          base_original, base_simulada)

        # Bocadillo insight
        st.markdown(f"""
        <div style="background:{ACCENT_LIGHT};border:1.5px solid {ACCENT};
                    border-radius:12px;padding:14px 18px;margin-bottom:12px;">
            <div style="font-size:10px;font-weight:700;letter-spacing:0.1em;
                        text-transform:uppercase;color:{ACCENT};margin-bottom:6px;">
                {label}
            </div>
            <div style="font-size:13px;color:{TEXT_PRI};line-height:1.65;">
                {insight}
            </div>
        </div>""", unsafe_allow_html=True)

        # Chips rápidos
        if chips:
            chip_html = "".join([
                f'<span style="background:{ACCENT_LIGHT};color:{ACCENT};'
                f'font-size:11px;font-weight:600;padding:5px 12px;'
                f'border-radius:20px;margin-right:6px;margin-bottom:4px;'
                f'display:inline-block;cursor:pointer;">{c}</span>'
                for c in chips
            ])
            st.markdown(f'<div style="margin:6px 0 12px">{chip_html}</div>',
                        unsafe_allow_html=True)

        # Input conversacional
        col_inp, col_btn = st.columns([0.82, 0.18])
        with col_inp:
            pregunta = st.text_input("",
                key=f"sabio_fiscal_input_{seccion}",
                placeholder="Pregunta sobre estas decisiones fiscales...",
                label_visibility="collapsed")
        with col_btn:
            enviar = st.button("Enviar", key=f"sabio_fiscal_btn_{seccion}")

        # Procesar pregunta
        if enviar and pregunta.strip():
            ahorro_pct = round((ahorro / base_original * 100) if base_original else 0, 1)
            system = SYSTEM_PROMPTS[seccion].format(
                contexto=contexto,
                decisiones=decisiones,
                base_original=round(base_original, 2),
                base_simulada=round(base_simulada, 2),
                ahorro=round(ahorro, 2),
                reduccion_pct=ahorro_pct,
                meses_restantes=decisiones.get("meses_restantes", "—"),
                ingresos_acumulados=decisiones.get("ingresos_acumulados", "—"),
                ingresos_proyectados=decisiones.get("ingresos_proyectados", "—"),
            )
            with st.spinner("Analizando..."):
                respuesta = _llamar_claude(system, pregunta.strip())
            st.session_state[hist_key].append(
                {"role": "user",      "content": pregunta.strip()})
            st.session_state[hist_key].append(
                {"role": "assistant", "content": respuesta})

        # Historial
        for msg in st.session_state[hist_key]:
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="text-align:right;margin:8px 0">
                    <span style="background:{ACCENT_LIGHT};color:{TEXT_PRI};
                        padding:8px 14px;border-radius:16px 16px 4px 16px;
                        font-size:12px;display:inline-block;max-width:80%">
                        {msg['content']}
                    </span>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:#F8F9FA;border-radius:12px;
                            padding:12px 14px;font-size:12px;
                            color:{TEXT_PRI};line-height:1.6;margin:8px 0;
                            border-left:3px solid {ACCENT};">
                    {msg['content']}
                </div>""", unsafe_allow_html=True)

        # Botón limpiar
        if st.session_state[hist_key]:
            if st.button("🗑 Limpiar conversación",
                         key=f"sabio_fiscal_clear_{seccion}"):
                st.session_state[hist_key] = []
                st.session_state.pop(f"sabio_fiscal_{seccion}_"
                                     f"{hash(str(decisiones))}", None)
                st.rerun()
