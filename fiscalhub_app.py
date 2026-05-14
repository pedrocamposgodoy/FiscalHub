# ================================================================
# fiscalhub_app.py — FiscalHub · Portal Asesoría Fiscal
# Nolasco Capital ecosystem
# Diseño: degradados azul/gris pastel · sidebar azul marino
# ================================================================

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import io
import html as _html
from nolasco_styles import inject_global_css
from kpi_renderer import render_kpi_row, render_kpi_grid, ACCENT_F, RED, AMBER, GREEN

# Paleta determinista por cliente — 8 colores profesionales
# Siempre el mismo color para el mismo cliente_id
_PALETA_CLI = [
    "#1E3A5F",  # azul marino
    "#3D2B6B",  # morado oscuro
    "#1A4731",  # verde oscuro
    "#7A2D1A",  # rojo ladrillo
    "#1A3A4A",  # azul petróleo
    "#4A3000",  # marrón dorado
    "#2D1A4A",  # índigo oscuro
    "#3B3B3B",  # gris antracita
]

def _color_cli(cliente_id: str) -> str:
    """Color determinista para un cliente — siempre el mismo."""
    return _PALETA_CLI[abs(hash(str(cliente_id))) % len(_PALETA_CLI)]

def _e(s):
    """Escapar caracteres HTML especiales en datos de usuario."""
    return _html.escape(str(s)) if s else ""

st.set_page_config(
    page_title="FiscalHub · Nolasco Capital",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

SUPABASE_URL = "https://odxixtgqcyddfqaapqgi.supabase.co"
SUPABASE_KEY = "sb_publishable_Obgti7yMfXw8wCUL2FbTtA_EWeyHuM9"

def _h(token=None):
    t = token or st.session_state.get("fh_token") or SUPABASE_KEY
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {t}",
            "Content-Type": "application/json", "Prefer": "return=representation"}

def _hd():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"}

# ── INYECTAR ESTILO GLOBAL ──────────────────────────────────────
# El CSS completo se gestiona desde nolasco_styles.py (único fuente de verdad)
# Esto se llama UNA VEZ al inicio de la app


# ── Helpers ──────────────────────────────────────────────────────
def sf(v, d=0):
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)): return float(d)
        return float(v)
    except: return float(d)

def _gv(row, *keys, d=0):
    for k in keys:
        v = row.get(k)
        if v is not None:
            try:
                f = float(v)
                if not pd.isna(f): return f
            except: pass
    return float(d)

def fmt_eur(n, sign=False):
    n = float(n or 0)
    s = f"{abs(n):,.0f}".replace(",",".")
    prefix = "−" if n < 0 else ("+" if sign else "")
    return f"{prefix}{s} €"

def days_to_irpf():
    hoy = date.today()
    cierre = date(hoy.year, 6, 30)
    if hoy > cierre: cierre = date(hoy.year+1, 6, 30)
    return (cierre - hoy).days

# ── Auth ─────────────────────────────────────────────────────────
def login_asesor(email, password):
    r = requests.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
        json={"email": email, "password": password})
    if r.status_code == 200:
        d = r.json()
        return {"ok": True, "user_id": d["user"]["id"],
                "email": d["user"]["email"], "token": d["access_token"]}
    return {"ok": False, "error": r.json().get("error_description", "Error de acceso")}

def registrar_asesor(email, password, nombre, despacho):
    r = requests.post(f"{SUPABASE_URL}/auth/v1/signup",
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
        json={"email": email, "password": password})
    if r.status_code == 200:
        uid = r.json().get("id") or r.json().get("user", {}).get("id")
        if uid:
            requests.post(f"{SUPABASE_URL}/rest/v1/asesores", headers=_h(),
                json={"user_id": uid, "nombre": nombre, "despacho": despacho, "email": email})
        return {"ok": True}
    return {"ok": False, "error": r.json().get("error_description", "Error de registro")}

def get_asesor_info(user_id):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/asesores?user_id=eq.{user_id}&select=*", headers=_h())
    if r.status_code == 200 and r.json(): return r.json()[0]
    return {"nombre": "Asesor", "despacho": "Despacho Fiscal", "email": ""}

# ── Supabase data ─────────────────────────────────────────────────
def get_clientes_vinculados(asesor_user_id):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/accesos_asesor"
        f"?asesor_user_id=eq.{asesor_user_id}&activo=eq.true&select=*", headers=_h())
    return r.json() if r.status_code == 200 else []

def get_inmuebles_propietario(pid):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/inmuebles?user_id=eq.{pid}&select=*", headers=_hd())
    return pd.DataFrame(r.json()) if r.status_code == 200 and r.json() else pd.DataFrame()

def get_movimientos_propietario(pid):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/movimientos?user_id=eq.{pid}&select=*", headers=_hd())
    return pd.DataFrame(r.json()) if r.status_code == 200 and r.json() else pd.DataFrame()

def vincular_propietario(asesor_user_id, codigo):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/accesos_asesor"
        f"?codigo=eq.{codigo.upper()}&activo=eq.true&select=*", headers=_h())
    if r.status_code == 200 and r.json():
        acc = r.json()[0]
        pid = acc.get("propietario_id")
        nombre = acc.get("nombre") or acc.get("nombre_propietario", "Propietario")
        if not pid: return {"ok": False, "error": "Código sin propietario"}
        requests.patch(f"{SUPABASE_URL}/rest/v1/accesos_asesor?id=eq.{acc['id']}",
            headers={**_h(), "Prefer": "return=minimal"}, json={"asesor_user_id": asesor_user_id})
        return {"ok": True, "propietario_id": pid, "nombre": nombre}
    return {"ok": False, "error": "Código no válido o ya utilizado"}

# ── Análisis fiscal ───────────────────────────────────────────────
def calcular_semaforo_inmueble(row):
    """Evalúa un inmueble — devuelve problemas detectados y estado semáforo."""
    problemas = []
    renta     = _gv(row,"renta","Renta")
    ibi       = _gv(row,"ibi_anual","IBI_Anual")
    amort     = _gv(row,"amortizacion_fiscal","Amortizacion_Fiscal")
    seguro    = _gv(row,"seguro_anual","Seguro_Anual")
    comunidad = _gv(row,"comunidad","Comunidad")
    catastral = _gv(row,"valor_catastral","Valor_Catastral")
    precio    = _gv(row,"precio_compra","Precio_Compra")
    tipo      = str(row.get("tipo_arrendamiento") or row.get("Tipo_Arrendamiento","")).lower()
    fecha_str = str(row.get("fecha_inicio_contrato") or row.get("Fecha_Inicio_Contrato","") or "")
    ingresos  = renta * 12

    if amort == 0 and renta > 0:
        if catastral == 0 and precio == 0:
            problemas.append({"tipo":"crit","titulo":"Amortización sin calcular",
                "desc":"Falta valor catastral y precio de compra.","accion":"Solicitar escritura o consultar catastro"})
        else:
            problemas.append({"tipo":"crit","titulo":"Amortización a 0 — revisar",
                "desc":f"Catastral: {fmt_eur(catastral)} · Precio compra: {fmt_eur(precio)}",
                "accion":"Calcular 3% s/ MAX(precio compra, catastral) × % construcción"})

    if ibi == 0 and renta > 0:
        problemas.append({"tipo":"crit","titulo":"IBI no registrado",
            "desc":"Casilla 0106 a cero.","accion":"Solicitar recibo IBI 2024 al propietario"})

    if seguro == 0 and renta > 0:
        problemas.append({"tipo":"warn","titulo":"Seguro de hogar no registrado",
            "desc":"Puede ser deducible.","accion":"Verificar si el propietario tiene póliza"})

    if comunidad == 0 and renta > 0:
        problemas.append({"tipo":"warn","titulo":"Comunidad de propietarios a 0",
            "desc":"Revisar si tiene gastos de comunidad.","accion":"Confirmar con propietario"})

    gastos_total = ibi + seguro + comunidad*12 + amort
    if ingresos > 0 and gastos_total > ingresos * 0.70:
        problemas.append({"tipo":"warn","titulo":"Gastos > 70% de los ingresos",
            "desc":f"Gastos: {fmt_eur(gastos_total)} · Ingresos: {fmt_eur(ingresos)}",
            "accion":"Revisar si hay gastos duplicados o importes incorrectos"})

    es_larga = "larga" in tipo or "habitual" in tipo or tipo == ""
    if es_larga:
        try:
            anyo = int(fecha_str[:4]) if fecha_str and len(fecha_str) >= 4 else 0
            if 0 < anyo <= 2023:
                problemas.append({"tipo":"warn","titulo":"Posible reducción 60% — confirmar",
                    "desc":f"Contrato desde {anyo}. Verificar condiciones Art. 23.2 LIRPF.",
                    "accion":"Confirmar fecha y condiciones antes de aplicar"})
        except: pass

    if any(p["tipo"] == "crit" for p in problemas):   estado = "cr"
    elif any(p["tipo"] == "warn" for p in problemas):  estado = "wn"
    else:                                               estado = "ok"

    return {"problemas": problemas, "estado": estado}

def calcular_modelo100_inmueble(row, df_mov):
    nombre    = str(row.get("nombre") or row.get("Nombre",""))
    renta     = _gv(row,"renta","Renta")
    dias      = int(_gv(row,"dias_arrendados_anio","Dias_Arrendados_Anio",d=365))
    factor    = min(dias,365)/365
    ingresos  = renta * 12 * factor
    intereses = _gv(row,"intereses_hipoteca","Intereses_Hipoteca") * factor
    ibi       = _gv(row,"ibi_anual","IBI_Anual") * factor
    comunidad = _gv(row,"comunidad","Comunidad") * 12 * factor
    seguro_h  = _gv(row,"seguro_anual","Seguro_Anual") * factor
    seguro_v  = _gv(row,"seguro_vida","Seguro_Vida") * factor
    ascensor  = _gv(row,"gasto_ascensor","Gasto_Ascensor") * factor
    com_seg   = comunidad + seguro_h + seguro_v + ascensor
    suministros = _gv(row,"servicios_suministros","Servicios_Suministros") * factor
    gastos_jur  = _gv(row,"gastos_juridicos","Gastos_Juridicos") * factor
    retenciones = _gv(row,"retenciones_irpf","Retenciones_IRPF")
    precio   = _gv(row,"precio_compra","Precio_Compra")
    imptos   = _gv(row,"impuestos_compra","Impuestos_Compra")
    gastos_c = _gv(row,"gastos_compra","Gastos_Compra")
    catastral= _gv(row,"valor_catastral","Valor_Catastral")
    pct_c    = _gv(row,"pct_construccion","Pct_Construccion",d=0.75)
    base_amort = max(precio+imptos+gastos_c, catastral)
    amort    = base_amort * pct_c * 0.03 * factor
    reparaciones = 0.0
    if not df_mov.empty:
        ca = "apartamento" if "apartamento" in df_mov.columns else "Apartamento"
        ct = "tipo" if "tipo" in df_mov.columns else "Tipo"
        cc = "categoria" if "categoria" in df_mov.columns else "Categoría"
        ci = "importe" if "importe" in df_mov.columns else "Importe"
        mask = ((df_mov.get(ca,pd.Series())==nombre) &
                (df_mov.get(ct,pd.Series())=="Gasto") &
                (df_mov.get(cc,pd.Series()).isin(["Mantenimiento","Reparación"])))
        reparaciones = float(df_mov[mask][ci].sum()) * factor if mask.any() else 0
    total_gastos = intereses+reparaciones+ibi+com_seg+suministros+gastos_jur+amort
    rend_neto    = ingresos - total_gastos
    tipo  = str(row.get("tipo_arrendamiento") or row.get("Tipo_Arrendamiento","")).lower()
    fecha = str(row.get("fecha_inicio_contrato") or row.get("Fecha_Inicio_Contrato","") or "")
    es_larga = "larga" in tipo or "habitual" in tipo or tipo == ""
    red_pct = 0
    if es_larga:
        try:
            anyo = int(fecha[:4]) if fecha and len(fecha)>=4 else 0
            red_pct = 60 if 0<anyo<=2023 else 50
        except: red_pct = 50
    reduccion = rend_neto * red_pct/100 if rend_neto > 0 else 0
    rend_final = rend_neto - reduccion
    return {
        "ingresos": round(ingresos,2), "intereses": round(intereses,2),
        "reparaciones": round(reparaciones,2), "ibi": round(ibi,2),
        "comunidad_seguros": round(com_seg,2), "suministros": round(suministros,2),
        "gastos_juridicos": round(gastos_jur,2), "amortizacion": round(amort,2),
        "total_gastos": round(total_gastos,2), "rend_neto": round(rend_neto,2),
        "red_pct": red_pct, "reduccion": round(reduccion,2),
        "rend_final": round(rend_final,2), "retenciones": round(retenciones,2), "dias": dias,
    }

def calcular_modelo100_global(df_inm, df_mov):
    if df_inm.empty: return {}
    total = {k:0 for k in ["ingresos","intereses","reparaciones","ibi","comunidad_seguros",
             "suministros","gastos_juridicos","amortizacion","total_gastos","rend_neto",
             "reduccion","rend_final","retenciones"]}
    for _, row in df_inm.iterrows():
        m = calcular_modelo100_inmueble(row, df_mov)
        for k in total: total[k] += m.get(k,0)
    return {k: round(v,2) for k,v in total.items()}

def calcular_alertas_cliente(df_inm, df_mov):
    alertas = []
    if df_inm.empty: return alertas
    for _, row in df_inm.iterrows():
        nombre = str(row.get("nombre") or row.get("Nombre",""))
        sem = calcular_semaforo_inmueble(row)
        for p in sem["problemas"]:
            alertas.append({**p, "inmueble": nombre, "categoria": "Fiscal"})
    return alertas

def construir_cartera(clientes_vinculados):
    cartera = []
    for acc in clientes_vinculados:
        pid = acc.get("propietario_id") or acc.get("user_id")
        nombre_raw = acc.get("nombre") or acc.get("nombre_propietario","")
        email_raw  = acc.get("email","")
        if nombre_raw and " " not in nombre_raw and "@" not in nombre_raw:
            nombre = nombre_raw
        elif email_raw:
            nombre = email_raw.split("@")[0].replace("."," ").title()
        else:
            nombre = nombre_raw or "Propietario"
        if not pid: continue
        df_inm = get_inmuebles_propietario(pid)
        df_mov = get_movimientos_propietario(pid)
        alertas = calcular_alertas_cliente(df_inm, df_mov)
        modelo  = calcular_modelo100_global(df_inm, df_mov)
        criticas = len([a for a in alertas if a["tipo"]=="crit"])
        medias   = len([a for a in alertas if a["tipo"]=="warn"])
        impacto  = sum(a.get("impacto",0) for a in alertas)
        estado   = "critico" if criticas>0 else "medio" if medias>0 else "ok"
        cartera.append({
            "id": pid, "nombre": nombre,
            "inmuebles": len(df_inm), "criticas": criticas, "medias": medias,
            "impacto": impacto, "estado": estado,
            "alertas": alertas, "df_inm": df_inm, "df_mov": df_mov, "modelo100": modelo,
        })
    cartera.sort(key=lambda x:({"critico":0,"medio":1,"ok":2}[x["estado"]],-x["criticas"]))
    return cartera

# ── Sidebar ───────────────────────────────────────────────────────
def render_sidebar():
    asesor   = st.session_state.get("fh_asesor", {})
    nombre   = asesor.get("nombre","Asesor")
    despacho = asesor.get("despacho","Despacho Fiscal")
    iniciales= "".join(p[0].upper() for p in nombre.split()[:2])
    dias     = days_to_irpf()
    pct      = max(0, min(100, int((90-dias)/90*100)))
    color    = "#DC2626" if dias<30 else "#D97706" if dias<60 else "#059669"

    st.markdown(f"""
    <div class="sb-brand">
      <div style="display:flex;align-items:center;gap:10px;">
        <div class="sb-logo">NC</div>
        <div class="sb-wordmark">FiscalHub</div>
      </div>
      <div class="sb-tag">Portal asesoría fiscal</div>
    </div>
    <div class="sb-advisor">
      <div class="sb-avatar">{iniciales}</div>
      <div>
        <div class="sb-advisor-name">{nombre}</div>
        <div class="sb-advisor-desc">{despacho}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    for label, key in [("🗂 Cartera","cartera"),("⚠️ Alertas","alertas"),
                        ("📥 Exportar","exportar"),("🔗 Vincular","vincular")]:
        if st.sidebar.button(label, key=f"sb_{key}", use_container_width=True):
            for k in ["fh_cliente_sel","fh_inmueble_sel"]:
                st.session_state.pop(k, None)
            st.session_state.fh_menu = key
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div class="sb-irpf">
      <div class="sb-irpf-label">Cierre IRPF 2025</div>
      <div class="sb-irpf-num" style="color:{color};">{dias}
        <span style="font-size:14px;font-weight:600;margin-left:4px;opacity:0.7;">días</span>
      </div>
      <div class="sb-irpf-sub">30 jun · campaña 2025</div>
      <div class="sb-bar"><div class="sb-fill" style="width:{pct}%;background:{color};"></div></div>
      <div class="sb-bar-labels"><span>hoy</span><span>30 jun</span></div>
    </div>""", unsafe_allow_html=True)

    if st.sidebar.button("🚪 Cerrar sesión", use_container_width=True):
        for k in ["fh_logged","fh_user_id","fh_token","fh_asesor","fh_menu",
                  "fh_cliente_sel","fh_inmueble_sel","fh_cartera","fh_validaciones"]:
            st.session_state.pop(k, None)
        st.rerun()

# ── LOGIN ─────────────────────────────────────────────────────────
def pantalla_login():
    inject_global_css("ficahub")
    st.markdown("<div style='height:12vh;'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;margin-bottom:22px;">
          <div style="display:inline-flex;align-items:center;gap:10px;margin-bottom:6px;">
            <div style="width:32px;height:32px;border:2px solid #534AB7;border-radius:6px;display:flex;align-items:center;justify-content:center;font-family:'Playfair Display',serif;font-size:13px;color:#534AB7;font-weight:700;">NC</div>
            <span style="font-family:'Playfair Display',serif;font-size:24px;color:#1e293b;font-weight:700;">FiscalHub</span>
          </div>
          <div style="font-size:9px;letter-spacing:0.18em;text-transform:uppercase;color:#94A3B8;margin-top:4px;">Portal Asesoría Fiscal · Nolasco Capital</div>
        </div>
        <div style="background:#FFFFFF;border:1px solid rgba(83,74,183,0.12);border-radius:12px;padding:24px 22px 20px;box-shadow:0 4px 24px rgba(83,74,183,0.08);">
        """, unsafe_allow_html=True)

        tab_li, tab_re = st.tabs(["Acceder", "Registrarse"])
        with tab_li:
            em = st.text_input("", key="li_em", placeholder="email@despacho.es", label_visibility="collapsed")
            pw = st.text_input("", type="password", key="li_pw", placeholder="Contraseña", label_visibility="collapsed")
            if st.button("Entrar →", key="li_btn", use_container_width=True, type="primary"):
                if em and pw:
                    with st.spinner("Verificando..."):
                        res = login_asesor(em, pw)
                    if res["ok"]:
                        st.session_state.update({"fh_logged":True,"fh_user_id":res["user_id"],
                            "fh_token":res["token"],"fh_asesor":get_asesor_info(res["user_id"]),"fh_menu":"cartera"})
                        st.rerun()
                    else: st.error(res.get("error","Credenciales incorrectas"))
                else: st.warning("Introduce email y contraseña")

        with tab_re:
            c1,c2 = st.columns(2)
            with c1: nm = st.text_input("",key="rg_nm",placeholder="Nombre completo",label_visibility="collapsed")
            with c2: ds = st.text_input("",key="rg_ds",placeholder="Despacho",label_visibility="collapsed")
            em_r = st.text_input("",key="rg_em",placeholder="email@despacho.es",label_visibility="collapsed")
            pw_r = st.text_input("",type="password",key="rg_pw",placeholder="Contraseña (mín. 8 car.)",label_visibility="collapsed")
            if st.button("Crear cuenta →",key="rg_btn",use_container_width=True,type="primary"):
                if all([nm,ds,em_r,pw_r]):
                    if len(pw_r)<8: st.error("Mínimo 8 caracteres")
                    else:
                        with st.spinner("Creando..."): res = registrar_asesor(em_r,pw_r,nm,ds)
                        if res["ok"]: st.success("✅ Cuenta creada. Revisa tu email y accede.")
                        else: st.error(res.get("error","Error"))
                else: st.warning("Completa todos los campos")
        st.markdown("</div>", unsafe_allow_html=True)

# ── CARTERA ───────────────────────────────────────────────────────
def pantalla_cartera():
    cartera = st.session_state.get("fh_cartera", [])
    if not cartera:
        st.markdown("""<div style="text-align:center;padding:60px 20px;">
          <div style="font-size:36px;margin-bottom:14px;">🔗</div>
          <div style="font-family:'DM Serif Display',serif;font-size:22px;color:#1E2A3A;margin-bottom:8px;">Sin clientes vinculados</div>
          <div style="font-size:13px;color:#5A6A7E;">Ve a Vincular e introduce el código que te dé el propietario desde Nolasco Capital.</div>
        </div>""", unsafe_allow_html=True)
        return

    total_inm  = sum(c["inmuebles"] for c in cartera)
    total_crit = sum(c["criticas"]  for c in cartera)
    total_imp  = sum(c["impacto"]   for c in cartera)
    n_crit = sum(1 for c in cartera if c["estado"]=="critico")
    n_med  = sum(1 for c in cartera if c["estado"]=="medio")
    n_ok   = sum(1 for c in cartera if c["estado"]=="ok")

    st.markdown(f"""<div style="margin-bottom:20px;">
      <div class="nc-page-label">Granada · Despacho fiscal</div>
      <div class="nc-page-title">Cartera de clientes</div>
      <div class="nc-page-sub">{len(cartera)} propietarios · {total_inm} inmuebles · campaña IRPF 2025</div>
    </div>""", unsafe_allow_html=True)

    render_kpi_row([
        {"label":"👥 Clientes",        "value":str(len(cartera)),
         "color":ACCENT_F,
         "subtitle":f"{n_crit} críticos · {n_med} revisar · {n_ok} OK"},
        {"label":"🏠 Inmuebles",       "value":str(total_inm),
         "color":ACCENT_F,             "subtitle":"Activos patrimoniales"},
        {"label":"🚨 Alertas críticas","value":str(total_crit),
         "color":RED,                  "subtitle":"Antes del 30 jun"},
        {"label":"💶 Impacto fiscal",  "value":fmt_eur(total_imp),
         "color":AMBER,                "subtitle":"Recuperable · cartera"},
    ])


    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    cf1,cf2 = st.columns([3,1])
    with cf1: filtro = st.radio("",["Todos","Críticos","A revisar","OK"],horizontal=True,key="fh_filtro",label_visibility="collapsed")
    with cf2: busqueda = st.text_input("",placeholder="🔍 Buscar...",key="fh_busqueda",label_visibility="collapsed")

    rows = [c for c in cartera if
            (filtro=="Todos" or (filtro=="Críticos" and c["estado"]=="critico") or
             (filtro=="A revisar" and c["estado"]=="medio") or (filtro=="OK" and c["estado"]=="ok")) and
            (not busqueda or busqueda.lower() in c["nombre"].lower())]

    # Colores header por estado
    # Estado semántico para badge
    _ECOL  = {"critico":"#DC2626","medio":"#D97706","ok":"#059669"}
    _ELBL  = {"critico":"⚠ Crítico","medio":"◔ Revisar","ok":"✓ OK"}
    _BADGE = {"critico":"rgba(220,38,38,0.12)",
              "medio":"rgba(217,119,6,0.12)","ok":"rgba(5,150,105,0.12)"}

    def _cli_icon(nombre):
        n = nombre.lower()
        if any(x in n for x in ["bufete","abogad","juríd","legal"]): return "⚖️","Bufete"
        if any(x in n for x in ["inmo","piso","alquil"]): return "🏢","Inmobiliaria"
        if any(x in n for x in ["médic","clínic","salud"]): return "🏥","Clínica"
        if any(x in n for x in ["restaur","hostel","bar","café"]): return "🍽️","Hostelería"
        if any(x in n for x in ["sl","slu","s.l","s.a"]): return "🏛️","Empresa"
        return "👤","Particular"

    MAX_COLS = 4
    for fila_start in range(0, len(rows), MAX_COLS):
        fila_rows = rows[fila_start:fila_start+MAX_COLS]
        cols = st.columns(MAX_COLS)
        for col_idx, c in enumerate(fila_rows):
            estado   = c["estado"]
            hdr      = _color_cli(c["id"])  # color único por cliente
            txt      = _ECOL[estado]
            lbl      = _ELBL[estado]
            badge_bg = _BADGE[estado]
            icon, tipo = _cli_icon(c["nombre"])
            imp_v    = fmt_eur(abs(c["impacto"])) if c["impacto"] else "—"
            cr_col   = "#DC2626" if c["criticas"]>0 else "#64748B"
            med_col  = "#D97706" if c["medias"]>0   else "#64748B"
            modelo   = c.get("modelo100",{})
            ingresos = fmt_eur(modelo.get("ingresos",0))
            base_imp = fmt_eur(modelo.get("rend_final",0))
            with cols[col_idx]:
                hdr_html = (
                    f'<div style="background:{hdr};border-radius:12px 12px 0 0;' +
                    f'padding:14px 16px 12px;display:flex;align-items:center;gap:10px;margin-bottom:-1px;">' +
                    f'<span style="font-size:22px;">{icon}</span>' +
                    f'<div style="flex:1;min-width:0;">' +
                    f'<div style="font-size:18px;font-weight:800;color:#FFF;line-height:1.2;' +
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{c["nombre"]}</div>' +
                    f'<div style="font-size:10px;color:rgba(255,255,255,0.65);margin-top:2px;">' +
                    f'<span style="font-size:13px;opacity:0.75;">{tipo} · {c["inmuebles"]} inmuebles</span></div></div>' +
                    f'<span style="background:rgba(255,255,255,0.15);color:#FFF;font-size:9px;' +
                    f'font-weight:700;padding:3px 8px;border-radius:6px;">{lbl}</span></div>'
                )
                body_html = (
                    '<div style="background:#FFF;border:2px solid #E2E8F0;border-top:none;' +
                    'border-radius:0 0 12px 12px;padding:14px 16px 12px;">' +
                    '<div style="display:flex;justify-content:space-between;margin-bottom:8px;' +
                    'padding-bottom:8px;border-bottom:1px solid #F1F5F9;">' +
                    f'<span style="font-size:14px;color:#94A3B8;font-weight:600;">Tipo</span>' +
                    f'<span style="font-size:14px;color:#1e293b;font-weight:700;">{tipo}</span></div>' +
                    f'<div style="display:flex;justify-content:space-between;margin-bottom:5px;">' +
                    f'<span style="font-size:14px;color:#94A3B8;">📥 0102 Ingresos</span>' +
                    f'<span style="font-size:16px;font-weight:800;color:#059669;">{ingresos}</span></div>' +
                    f'<div style="display:flex;justify-content:space-between;margin-bottom:5px;">' +
                    f'<span style="font-size:14px;color:#94A3B8;">🚨 Alertas críticas</span>' +
                    f'<span style="font-size:16px;font-weight:800;color:{cr_col};">{c["criticas"]}</span></div>' +
                    f'<div style="display:flex;justify-content:space-between;margin-bottom:10px;">' +
                    f'<span style="font-size:14px;color:#94A3B8;">⚡ A revisar</span>' +
                    f'<span style="font-size:16px;font-weight:800;color:{med_col};">{c["medias"]}</span></div>' +
                    f'<div style="background:{badge_bg};border-radius:6px;padding:5px 10px;' +
                    f'text-align:center;font-size:14px;font-weight:700;color:{txt};">' +
                    f'Base imp. est.: {base_imp}</div></div>'
                )
                st.markdown(hdr_html + body_html, unsafe_allow_html=True)
                if st.button("→ Ver expediente completo",
                             key=f"cli_{c['id']}_{fila_start}_{col_idx}",
                             use_container_width=True):
                    st.session_state.fh_cliente_sel = c["id"]
                    st.session_state.fh_menu = "cliente"
                    st.rerun()
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)



# ── PANTALLA CLIENTE ──────────────────────────────────────────────
def pantalla_cliente():
    cliente_id = st.session_state.get("fh_cliente_sel")
    cartera    = st.session_state.get("fh_cartera", [])
    cliente    = next((c for c in cartera if c["id"]==cliente_id), None)
    if not cliente: st.warning("Selecciona un cliente."); return

    df_inm  = cliente["df_inm"]
    df_mov  = cliente["df_mov"]
    modelo  = cliente["modelo100"]
    nombre  = cliente["nombre"]
    vlds    = st.session_state.get("fh_validaciones", {}).get(cliente_id, {})

    if st.button("← Volver a cartera", key="cli_back"):
        st.session_state.fh_menu = "cartera"
        st.session_state.pop("fh_cliente_sel", None)
        st.session_state.pop("fh_inmueble_sel", None)
        st.rerun()

    st.markdown(f"""<div style="margin-bottom:14px;">
      <div class="nc-page-label">Revisión IRPF 2025</div>
      <div class="nc-page-title">{nombre}</div>
      <div class="nc-page-sub">{cliente["inmuebles"]} inmuebles · Campaña IRPF 2025</div>
    </div>""", unsafe_allow_html=True)

    _cc = _color_cli(cliente_id)  # color único del cliente — se usa en border-top
    # Número semántico + border-top con color del cliente
    render_kpi_grid([
        {"label":"📥 0102 Ingresos",
         "value":fmt_eur(modelo.get("ingresos",0)),
         "color":GREEN,   "border_color":_cc, "subtitle":"Rendimiento íntegro"},
        {"label":"📤 Gastos deducibles",
         "value":f"−{fmt_eur(modelo.get('total_gastos',0))}",
         "color":RED,     "border_color":_cc, "subtitle":"Total deducible"},
        {"label":"⚖️ 0149 Rend. neto",
         "value":fmt_eur(modelo.get("rend_neto",0)),
         "color":ACCENT_F,"border_color":_cc, "subtitle":"Antes de reducción"},
        {"label":"🧾 0156 Base imp. est.",
         "value":fmt_eur(modelo.get("rend_final",0)),
         "color":AMBER,   "border_color":_cc, "subtitle":"⚠️ Orientativa"},
    ])


    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # Verificar si todos validados
    col_n = "nombre" if "nombre" in df_inm.columns else "Nombre"
    nombres_inm = [str(r.get(col_n,"")) for _,r in df_inm.iterrows()] if not df_inm.empty else []
    todos_ok = all(
        vlds.get(nm,{}).get("estado") in ("ok","vl") or
        calcular_semaforo_inmueble(df_inm[df_inm[col_n]==nm].iloc[0])["estado"] == "ok"
        for nm in nombres_inm
    ) if nombres_inm else False

    if todos_ok:
        st.markdown("""<div class="nc-callout pos" style="margin-bottom:8px;">
          <strong>✅ Todos los inmuebles revisados</strong> — listo para el resumen global y exportar.
        </div>""", unsafe_allow_html=True)
        if st.button("📊 Resumen global → Exportar", type="primary", key="cli_global"):
            st.session_state.fh_menu = "resumen_global"
            st.rerun()

    st.markdown('<div class="nc-section">Inmuebles</div>', unsafe_allow_html=True)
    if df_inm.empty:
        st.info("Sin inmuebles registrados para este cliente."); return

    # Color del cliente — mismo para todos sus inmuebles
    _cc = _color_cli(cliente_id)

    # Grid de 4 columnas — mismo patrón que cards de cliente
    MAX_COLS = 4
    inm_list = list(df_inm.iterrows())
    for fila_start in range(0, len(inm_list), MAX_COLS):
        fila_rows = inm_list[fila_start:fila_start+MAX_COLS]
        cols = st.columns(MAX_COLS)
        for col_idx, (_, row) in enumerate(fila_rows):
            idx        = fila_start + col_idx
            nombre_inm = str(row.get(col_n,""))
            sem        = calcular_semaforo_inmueble(row)
            vld        = vlds.get(nombre_inm,{})
            vld_estado = vld.get("estado","")
            vld_manual = vld.get("manual", False)

            # Métricas
            renta     = _gv(row,"renta","Renta")
            ibi       = _gv(row,"ibi_anual","IBI_Anual")
            amort     = _gv(row,"amortizacion_fiscal","Amortizacion_Fiscal")
            seguro    = _gv(row,"seguro_anual","Seguro_Anual")
            comunidad = _gv(row,"comunidad","Comunidad")*12
            gastos    = ibi+amort+seguro+comunidad
            neto      = renta*12 - gastos
            tipo_arr  = str(row.get("tipo_arrendamiento") or row.get("Tipo_Arrendamiento","Larga Duración"))
            inquilino = str(row.get("inquilino") or row.get("Inquilino","—"))[:28]

            # Estado visual
            if vld_estado in ("ok","vl"):
                est_lbl = "✓ Validado" if vld_manual else "✓ Correcto"
                est_bg  = "rgba(5,150,105,0.10)"
                est_col = "#059669"
            elif sem["estado"] in ("cr","critico"):
                n_cr    = len([p for p in sem["problemas"] if p["tipo"]=="crit"])
                est_lbl = f"⚠ {n_cr} crítico{'s' if n_cr>1 else ''}"
                est_bg  = "rgba(220,38,38,0.10)"
                est_col = "#DC2626"
            elif sem["estado"] in ("wn","advertencia"):
                n_wn    = len([p for p in sem["problemas"] if p["tipo"]=="warn"])
                est_lbl = f"◔ {n_wn} aviso{'s' if n_wn>1 else ''}"
                est_bg  = "rgba(217,119,6,0.10)"
                est_col = "#D97706"
            else:
                est_lbl = "✓ Correcto"
                est_bg  = "rgba(5,150,105,0.10)"
                est_col = "#059669"

            # Primera alerta
            alerta_txt = ""
            if sem["problemas"] and vld_estado not in ("ok","vl"):
                p0 = sem["problemas"][0]["titulo"]
                mas = f" +{len(sem['problemas'])-1} más" if len(sem["problemas"])>1 else ""
                alerta_txt = f"⚠ {p0}{mas}"
            elif vld_manual:
                alerta_txt = "✓ Validado manualmente"

            neto_col = "#059669" if neto >= 0 else "#DC2626"

            with cols[col_idx]:
                # Header con color del cliente
                hdr = (
                    f'<div style="background:{_cc};border-radius:12px 12px 0 0;' +
                    f'padding:12px 14px 10px;margin-bottom:-1px;">' +
                    f'<div style="font-size:15px;font-weight:800;color:#FFF;' +
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' +
                    f'{nombre_inm}</div>' +
                    f'<div style="font-size:11px;color:rgba(255,255,255,0.65);margin-top:2px;">' +
                    f'{inquilino} · {tipo_arr}</div>' +
                    f'</div>'
                )
                body = (
                    f'<div style="background:#FFF;border:2px solid #E2E8F0;' +
                    f'border-top:none;border-radius:0 0 12px 12px;' +
                    f'padding:12px 14px 10px;">' +
                    # alerta
                    (f'<div style="font-size:12px;color:{est_col};font-weight:600;' +
                     f'margin-bottom:8px;padding:4px 8px;background:{est_bg};' +
                     f'border-radius:6px;">{alerta_txt}</div>' if alerta_txt else
                     f'<div style="height:4px;"></div>') +
                    # métricas
                    f'<div style="display:flex;justify-content:space-between;margin-bottom:5px;">' +
                    f'<span style="font-size:12px;color:#94A3B8;">📈 Renta/mes</span>' +
                    f'<span style="font-size:13px;font-weight:800;color:#059669;">{fmt_eur(renta)}</span></div>' +
                    f'<div style="display:flex;justify-content:space-between;margin-bottom:5px;">' +
                    f'<span style="font-size:12px;color:#94A3B8;">📉 Gastos/año</span>' +
                    f'<span style="font-size:13px;font-weight:800;color:#DC2626;">−{fmt_eur(gastos)}</span></div>' +
                    f'<div style="display:flex;justify-content:space-between;margin-bottom:8px;">' +
                    f'<span style="font-size:12px;color:#94A3B8;">⚖️ Neto/año</span>' +
                    f'<span style="font-size:13px;font-weight:800;color:{neto_col};">{fmt_eur(neto)}</span></div>' +
                    # badge estado
                    f'<div style="background:{est_bg};border-radius:6px;padding:4px 10px;' +
                    f'text-align:center;font-size:12px;font-weight:700;color:{est_col};">' +
                    f'{est_lbl}</div></div>'
                )
                st.markdown(hdr + body, unsafe_allow_html=True)

                # Botones — Revisar y Validar
                b1, b2 = st.columns(2)
                with b1:
                    if st.button(f"🔍 Revisar",
                                 key=f"rev_{cliente_id[:8]}_{idx}",
                                 use_container_width=True):
                        st.session_state.fh_inmueble_sel = nombre_inm
                        st.session_state.fh_menu = "ficha"
                        st.rerun()
                with b2:
                    if vld_manual:
                        if st.button("↩ Desvalidar",
                                     key=f"dvl_{cliente_id[:8]}_{idx}",
                                     use_container_width=True):
                            st.session_state.fh_validaciones[cliente_id].pop(nombre_inm, None)
                            st.rerun()
                    elif vld_estado not in ("ok","vl") and sem["estado"] not in ("ok",""):
                        if st.button("✅ Validar",
                                     key=f"vld_{cliente_id[:8]}_{idx}",
                                     use_container_width=True):
                            if "fh_validaciones" not in st.session_state:
                                st.session_state.fh_validaciones = {}
                            if cliente_id not in st.session_state.fh_validaciones:
                                st.session_state.fh_validaciones[cliente_id] = {}
                            st.session_state.fh_validaciones[cliente_id][nombre_inm] = {
                                "estado":"vl","manual":True,
                                "fecha":date.today().strftime("%d/%m/%Y")}
                            st.rerun()
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── FICHA INMUEBLE ────────────────────────────────────────────────
def pantalla_ficha_inmueble():
    cliente_id  = st.session_state.get("fh_cliente_sel")
    nombre_inm  = st.session_state.get("fh_inmueble_sel","")
    cartera     = st.session_state.get("fh_cartera", [])
    cliente     = next((c for c in cartera if c["id"]==cliente_id), None)
    if not cliente or not nombre_inm: st.warning("Selecciona un inmueble."); return

    df_inm = cliente["df_inm"]
    df_mov = cliente["df_mov"]
    col_n  = "nombre" if "nombre" in df_inm.columns else "Nombre"
    rows   = df_inm[df_inm[col_n]==nombre_inm]
    if rows.empty: st.warning(f"No se encontró: {nombre_inm}"); return
    row = rows.iloc[0]

    sem    = calcular_semaforo_inmueble(row)
    modelo = calcular_modelo100_inmueble(row, df_mov)
    vlds   = st.session_state.get("fh_validaciones",{}).get(cliente_id,{})

    c_back, c_vld = st.columns([3,1])
    with c_back:
        if st.button("← Volver al cliente", key="fic_back"):
            st.session_state.fh_menu = "cliente"
            st.session_state.pop("fh_inmueble_sel", None)
            st.session_state.pop("fh_pdf_export", None)
            st.rerun()
    with c_vld:
        if vlds.get(nombre_inm,{}).get("estado") != "vl" and sem["estado"] in ("cr","wn"):
            if st.button("✅ Validar manualmente", key="fic_vld", use_container_width=True):
                if "fh_validaciones" not in st.session_state: st.session_state.fh_validaciones = {}
                if cliente_id not in st.session_state.fh_validaciones: st.session_state.fh_validaciones[cliente_id] = {}
                st.session_state.fh_validaciones[cliente_id][nombre_inm] = {
                    "estado":"vl","manual":True,"fecha":date.today().strftime("%d/%m/%Y")}
                st.rerun()

    ROOF = {"Casa":("#6B2737","#8B3547"),"Despacho":("#185FA5","#1A6FBF"),
            "Garaje":("#4A5568","#5A6580"),"Apartamento":("#B8924A","#CFA55A")}
    def _rtype(tipo,nombre):
        t=(str(tipo)+" "+str(nombre)).lower()
        if any(x in t for x in ["despacho","oficina","salon"]): return "Despacho"
        if any(x in t for x in ["casa","chalet","abarqueros"]): return "Casa"
        if any(x in t for x in ["cochera","garaje"]): return "Garaje"
        return "Apartamento"
    rt   = _rtype(row.get("tipo_arrendamiento",""),nombre_inm)
    c1,c2= ROOF[rt]
    sem_color = {"cr":"var(--cr)","wn":"var(--wn)","ok":"var(--ok)"}[sem["estado"]]
    sem_label = {"cr":"🔴 Requiere acción","wn":"🟡 Revisar","ok":"🟢 Correcto"}[sem["estado"]]

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#FFFFFF 0%,#F4F8FC 100%);border:0.5px solid rgba(74,122,181,0.2);border-radius:14px;overflow:hidden;margin-bottom:14px;box-shadow:0 2px 16px rgba(30,58,95,0.08);">
      <svg viewBox="0 0 600 52" style="display:block;width:100%;margin-bottom:-1px;" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
        <defs><linearGradient id="rh" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/>
        </linearGradient></defs>
        <rect width="600" height="52" fill="url(#rh)"/>
        <text x="300" y="32" text-anchor="middle" font-family="DM Serif Display,serif" font-size="17" fill="white" opacity="0.95">{nombre_inm}</text>
        <text x="300" y="47" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="10" fill="white" opacity="0.6">{rt} · {row.get("tipo_arrendamiento") or row.get("Tipo_Arrendamiento","Larga Duración")}</text>
      </svg>
      <div style="padding:10px 16px;display:flex;align-items:center;justify-content:space-between;">
        <div>
          <span style="font-size:13px;font-weight:500;color:#1E2A3A;">{row.get("inquilino") or row.get("Inquilino","Sin inquilino")}</span>
          <span style="font-size:11px;color:#8A9BB0;margin-left:10px;">CP {row.get("cp") or row.get("CP","—")}</span>
        </div>
        <span style="font-size:12px;font-weight:500;color:{sem_color};">{sem_label}</span>
      </div>
    </div>""", unsafe_allow_html=True)

    if sem["problemas"]:
        for p in sem["problemas"]:
            cls = "cr" if p["tipo"]=="crit" else "wn"
            st.markdown(f"""<div class="callout {cls}" style="margin-bottom:6px;">
              <strong>{"🔴" if p["tipo"]=="crit" else "🟡"} {p["titulo"]}</strong><br>
              <span style="font-size:12px;">{p["desc"]}</span><br>
              <span style="font-size:11px;opacity:0.8;">→ {p["accion"]}</span>
            </div>""", unsafe_allow_html=True)


    # ── LABORATORIO FISCAL — 3 CAPAS ─────────────────────────────

    def _simular_tabla(row_, d_):
        """Recalcula Modelo 100 según estados de los radio buttons de la tabla."""
        def _inc(dk, val):
            """Incluir valor si acc_{dk} == 'incluir', excluir si 'excluir'."""
            return val if d_.get(f"acc_{dk}", "incluir") == "incluir" else 0

        renta_m   = sf(row_.get("renta") or row_.get("Renta",0))
        ing       = renta_m * 12
        intereses = _inc("intereses", sf(row_.get("intereses_hipoteca",0)))
        ibi_v     = _inc("ibi",       sf(row_.get("ibi_anual",0)))
        com       = _inc("comunidad", sf(row_.get("comunidad",0))*12)
        seg       = _inc("seguro",    sf(row_.get("seguro_anual",0)))
        jur       = _inc("juridicos", sf(row_.get("gastos_juridicos_anual",0)))
        sumi      = _inc("suministros",sf(row_.get("suministros_anual",0)))

        # Reparaciones: gasto=100%, inversion=5%/año, excluir=0
        rep_tot   = sf(row_.get("reparaciones_anual",0))
        acc_rep   = d_.get("acc_rep","gasto")
        if acc_rep == "gasto":
            rep_ded = rep_tot
        elif acc_rep == "inversion":
            rep_ded = rep_tot * 0.05
        else:
            rep_ded = 0

        # Amortización 3%: aplicar=calculado, excluir=0
        _precio_c  = sf(row_.get("precio_compra",0))
        _catastral = sf(row_.get("valor_catastral",0))
        _pct_c     = sf(row_.get("porcentaje_construccion",0.7))
        _amort_c   = max(_precio_c, _catastral) * _pct_c * 0.03
        acc_amort  = d_.get("acc_amort","aplicar")
        amort_3    = _amort_c if (acc_amort=="aplicar" and _precio_c>0 and _catastral>0) else 0

        total_g = intereses + ibi_v + com + seg + jur + sumi + rep_ded + amort_3
        rend_n  = ing - total_g

        tipo_arr_ = str(row_.get("tipo_arrendamiento") or "").lower()
        es_temp   = any(x in tipo_arr_ for x in ["temporada","habitacion","turistic"])
        red_pct   = 0 if es_temp else d_.get("reduccion_pct", 50)
        reduccion = max(rend_n, 0) * red_pct / 100
        return dict(ingresos=round(ing,2), total_gastos=round(total_g,2),
                    rend_neto=round(rend_n,2), red_pct=red_pct,
                    reduccion=round(reduccion,2), rend_final=round(rend_n-reduccion,2))

    dec_key = f"dec_{cliente_id[:8]}_{nombre_inm[:10]}"
    if dec_key not in st.session_state:
        st.session_state[dec_key] = {}
    dec = st.session_state[dec_key]

    m         = modelo
    TIPO_MARG = 0.30
    from datetime import date as _date_
    hoy        = _date_.today()
    mes_actual = hoy.month
    meses_rest = 12 - mes_actual
    renta_mes  = sf(row.get("renta") or row.get("Renta", 0))
    ing_acum   = renta_mes * mes_actual
    ing_proy   = renta_mes * 12
    precio_c   = sf(row.get("precio_compra", 0))
    catastral  = sf(row.get("valor_catastral", 0))
    pct_const  = sf(row.get("porcentaje_construccion", 0.7))
    amort_calc = max(precio_c, catastral) * pct_const * 0.03
    tipo_arr_str = str(row.get("tipo_arrendamiento") or "").lower()
    es_temporada = any(x in tipo_arr_str for x in ["temporada","habitacion","turistic"])

    m_base     = _simular_tabla(row, {})
    base_orig  = m_base["rend_final"]
    cuota_orig = max(base_orig * TIPO_MARG, 0)

    st.markdown(
        '<div class="nc-section" style="margin-top:20px;">📋 Laboratorio Fiscal</div>',
        unsafe_allow_html=True)

    col_tabla, col_impacto = st.columns([6, 4])

    with col_tabla:
        # ── TABLA DE AUDITORÍA ESTRATÉGICA ───────────────────────
        # Cabecera
        st.markdown("""
        <div style="display:grid;grid-template-columns:32px 1fr 90px 1fr;
                    gap:0;background:#F1F5F9;border-radius:8px 8px 0 0;
                    padding:8px 12px;font-size:17px;font-weight:800;
                    color:#64748B;text-transform:uppercase;letter-spacing:0.08em;
                    margin-bottom:2px;">
            <div></div><div>Concepto</div>
            <div style="text-align:right;">Importe</div>
            <div style="padding-left:12px;">Acción</div>
        </div>""", unsafe_allow_html=True)

        def _sem_dot(color, tooltip=""):
            colors = {"verde":"#059669","amarillo":"#D97706","rojo":"#DC2626"}
            c = colors.get(color, "#94A3B8")
            return (f'<span title="{tooltip}" style="display:inline-block;' +
                    f'width:10px;height:10px;border-radius:50%;' +
                    f'background:{c};flex-shrink:0;"></span>')

        def _fila_header(titulo, color="#534AB7"):
            st.markdown(
                f'<div style="font-size:17px;font-weight:800;color:{color};' +
                f'text-transform:uppercase;letter-spacing:0.06em;' +
                f'padding:10px 12px 4px;border-bottom:1px solid #E2E8F0;' +
                f'margin-bottom:4px;">{titulo}</div>',
                unsafe_allow_html=True)

        # ── INGRESOS (solo informativo) ───────────────────────────
        _fila_header("📥 Ingresos")
        renta_mes_ = sf(row.get("renta") or row.get("Renta",0))
        st.markdown(
            f'<div style="display:grid;grid-template-columns:32px 1fr 90px 1fr;' +
            f'gap:0;padding:8px 12px;border-bottom:1px solid #F8FAFC;' +
            f'align-items:center;">' +
            f'<div>{_sem_dot("verde","Ingresos registrados")}</div>' +
            f'<div style="font-size:16px;color:#1e293b;font-weight:500;">0102 · Renta anual</div>' +
            f'<div style="font-size:17px;font-weight:800;color:#059669;text-align:right;">' +
            f'{fmt_eur(renta_mes_*12)}</div>' +
            f'<div style="padding-left:12px;font-size:17px;color:#94A3B8;">' +
            f'{fmt_eur(renta_mes_)}/mes</div></div>',
            unsafe_allow_html=True)

        # ── GASTOS FIJOS: Incluir / Excluir ──────────────────────
        _fila_header("📤 Gastos deducibles fijos")

        gastos_fijos = [
            ("0105", "Intereses hipoteca",
             sf(row.get("intereses_hipoteca",0)),
             "intereses"),
            ("0106", "IBI y tributos",
             sf(row.get("ibi_anual",0)),
             "ibi"),
            ("0107", "Comunidad propietarios",
             sf(row.get("comunidad",0))*12,
             "comunidad"),
            ("0110", "Seguro hogar + vida",
             sf(row.get("seguro_anual",0)),
             "seguro"),
            ("0111", "Suministros",
             sf(row.get("suministros_anual",0)),
             "suministros"),
            ("0112", "Gastos jurídicos",
             sf(row.get("gastos_juridicos_anual",0)),
             "juridicos"),
        ]

        for cas, label, valor, dk in gastos_fijos:
            sem  = "verde"  if valor > 0 else "rojo"
            tip  = "Registrado" if valor > 0 else "Sin registrar — revisar"
            default = dec.get(f"acc_{dk}", "incluir" if valor > 0 else "excluir")

            col_s, col_l, col_v, col_a = st.columns([0.4, 2.5, 1.1, 2.2])
            with col_s:
                st.markdown(_sem_dot(sem, tip), unsafe_allow_html=True)
            with col_l:
                st.markdown(
                    f'<div style="font-size:16px;color:#1e293b;">' +
                    f'<span style="color:#94A3B8;font-size:17px;">{cas} </span>' +
                    f'{label}</div>',
                    unsafe_allow_html=True)
            with col_v:
                color_v = "#059669" if valor > 0 else "#DC2626"
                st.markdown(
                    f'<div style="font-size:17px;font-weight:700;' +
                    f'color:{color_v};text-align:right;">' +
                    f'{fmt_eur(valor)}</div>',
                    unsafe_allow_html=True)
            with col_a:
                opc = st.radio("",
                    options=["incluir","excluir"],
                    format_func=lambda x: "✅ Incluir" if x=="incluir" else "❌ Excluir",
                    index=0 if default=="incluir" else 1,
                    horizontal=True,
                    key=f"acc_{dk}_{dec_key}",
                    label_visibility="collapsed")
                dec[f"acc_{dk}"] = opc

            st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)

        # ── REPARACIONES: Gasto / Inversión / Excluir ─────────────
        _fila_header("🔧 Mantenimiento e inversiones")
        rep_v   = sf(row.get("reparaciones_anual",0))
        rep_sem = "verde" if 0 < rep_v <= 2000 else ("amarillo" if rep_v > 2000 else "rojo")
        rep_tip = ("Importe alto — revisar clasificación" if rep_v > 2000
                   else ("Sin reparaciones registradas" if rep_v == 0
                         else "Registrado"))
        rep_def = dec.get("acc_rep", "gasto")

        col_s, col_l, col_v, col_a = st.columns([0.4, 2.5, 1.1, 2.2])
        with col_s:
            st.markdown(_sem_dot(rep_sem, rep_tip), unsafe_allow_html=True)
        with col_l:
            st.markdown(
                f'<div style="font-size:16px;color:#1e293b;">' +
                f'<span style="color:#94A3B8;font-size:17px;">0104 </span>' +
                f'Reparaciones</div>',
                unsafe_allow_html=True)
        with col_v:
            color_r = "#059669" if rep_v > 0 else "#94A3B8"
            st.markdown(
                f'<div style="font-size:17px;font-weight:700;' +
                f'color:{color_r};text-align:right;">' +
                f'{fmt_eur(rep_v)}</div>',
                unsafe_allow_html=True)
        with col_a:
            rep_opc = st.radio("",
                options=["gasto","inversion","excluir"],
                format_func=lambda x: {
                    "gasto":"🛠️ Gasto",
                    "inversion":"📈 Inversión",
                    "excluir":"❌ Excluir"}[x],
                index=["gasto","inversion","excluir"].index(rep_def),
                horizontal=True,
                key=f"acc_rep_{dec_key}",
                label_visibility="collapsed")
            dec["acc_rep"] = rep_opc

        if rep_opc == "inversion" and rep_v > 0:
            st.caption(f"→ Amortizable: {fmt_eur(rep_v*0.05)}/año × 20 años")

        # ── AMORTIZACIÓN 3% (cálculo automático) ──────────────────
        _fila_header("⚡ Amortización construcción (0109)", color="#DC2626")
        amort_actual = sf(row.get("amortizacion_fiscal",0))
        datos_ok     = precio_c > 0 and catastral > 0

        if not datos_ok:
            sem_a = "rojo"
            tip_a = "Faltan precio compra o valor catastral"
        elif amort_actual == 0:
            sem_a = "amarillo"
            tip_a = "No aplicada — calcular ahora"
        else:
            sem_a = "verde"
            tip_a = "Amortización registrada"

        col_s, col_l, col_v, col_a = st.columns([0.4, 2.5, 1.1, 2.2])
        with col_s:
            st.markdown(_sem_dot(sem_a, tip_a), unsafe_allow_html=True)
        with col_l:
            st.markdown(
                '<div style="font-size:16px;color:#1e293b;">' +
                '<span style="color:#94A3B8;font-size:17px;">0109 </span>' +
                'Amort. 3% construcción</div>',
                unsafe_allow_html=True)
            if datos_ok:
                st.markdown(
                    f'<div style="font-size:17px;color:#94A3B8;">' +
                    f'MAX({fmt_eur(precio_c)},{fmt_eur(catastral)}) × {pct_const*100:.0f}% × 3%' +
                    f' = {fmt_eur(amort_calc)}</div>',
                    unsafe_allow_html=True)
        with col_v:
            color_am = "#059669" if amort_actual > 0 else "#D97706" if datos_ok else "#DC2626"
            st.markdown(
                f'<div style="font-size:17px;font-weight:700;' +
                f'color:{color_am};text-align:right;">' +
                f'{fmt_eur(amort_actual)}</div>',
                unsafe_allow_html=True)
        with col_a:
            if not datos_ok:
                st.markdown(
                    '<div style="font-size:14px;color:#DC2626;padding-left:8px;">' +
                    '🔴 Faltan datos</div>',
                    unsafe_allow_html=True)
                dec["acc_amort"] = "excluir"
            else:
                am_def = dec.get("acc_amort", "aplicar")
                am_opc = st.radio("",
                    options=["aplicar","excluir"],
                    format_func=lambda x: (
                        f"✅ Aplicar ({fmt_eur(amort_calc)})"
                        if x=="aplicar" else "❌ Excluir"),
                    index=0 if am_def=="aplicar" else 1,
                    horizontal=True,
                    key=f"acc_amort_{dec_key}",
                    label_visibility="collapsed")
                dec["acc_amort"] = am_opc

        # ── REDUCCIÓN (automática, solo informativa) ───────────────
        _fila_header("📋 Reducción arrendamiento")
        red_pct_v = 0 if es_temporada else 50
        red_label = "Temporada/Habitaciones — 0%" if es_temporada else "Vivienda habitual — 50% (Art. 23.2 LIRPF)"
        st.markdown(
            f'<div style="display:grid;grid-template-columns:32px 1fr;' +
            f'gap:0;padding:8px 12px;align-items:center;">' +
            f'<div>{_sem_dot("verde" if not es_temporada else "amarillo")}</div>' +
            f'<div style="font-size:16px;color:#475569;">{red_label}</div></div>',
            unsafe_allow_html=True)
        dec["reduccion_pct"] = red_pct_v

        if st.button("↺ Restablecer decisiones", key=f"rst_{dec_key}"):
            st.session_state.pop(dec_key, None)
            st.rerun()

        st.session_state[dec_key] = dec

    with col_impacto:
        m_opt      = _simular_tabla(row, st.session_state.get(dec_key,{}))
        base_opt   = m_opt["rend_final"]
        cuota_opt  = max(base_opt * TIPO_MARG, 0)
        ahorro_c   = cuota_orig - cuota_opt
        ahorro_b   = base_orig  - base_opt
        color_ok   = "#059669" if ahorro_c >= 0 else "#DC2626"
        color_ko   = "#DC2626"

        st.markdown(f"""
        <div style="background:#FFF;border-radius:12px;border:2px solid #94A3B8;
                    padding:16px;margin-bottom:12px;
                    box-shadow:0 4px 12px rgba(0,0,0,0.08);">
          <div style="font-size:10px;font-weight:800;color:#94A3B8;
                      text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px;">
              ⚖️ Impacto fiscal comparado</div>
          <div style="display:grid;grid-template-columns:1fr 20px 1fr;align-items:center;">
            <div style="background:#FFF5F5;border-radius:8px;padding:10px;">
              <div style="font-size:9px;font-weight:700;color:{color_ko};
                          text-transform:uppercase;margin-bottom:4px;">Sin optimizar</div>
              <div style="font-size:11px;color:#475569;">Base imponible</div>
              <div style="font-size:1.3rem;font-weight:900;color:{color_ko};">
                  {fmt_eur(base_orig)}</div>
              <div style="font-size:11px;color:#475569;margin-top:6px;">Cuota est.</div>
              <div style="font-size:1.1rem;font-weight:800;color:{color_ko};">
                  {fmt_eur(cuota_orig)}</div>
            </div>
            <div style="text-align:center;font-size:18px;color:#94A3B8;">→</div>
            <div style="background:#F0FDF4;border-radius:8px;padding:10px;
                        border:1.5px solid {color_ok};">
              <div style="font-size:9px;font-weight:700;color:{color_ok};
                          text-transform:uppercase;margin-bottom:4px;">Con tu asesor</div>
              <div style="font-size:11px;color:#475569;">Base fin ejercicio</div>
              <div style="font-size:1.3rem;font-weight:900;color:{color_ok};">
                  {fmt_eur(base_opt)}</div>
              <div style="font-size:11px;color:#475569;margin-top:6px;">Cuota est.</div>
              <div style="font-size:1.1rem;font-weight:800;color:{color_ok};">
                  {fmt_eur(cuota_opt)}</div>
            </div>
          </div>
          <div style="margin-top:10px;padding:10px;background:{'#F0FDF4' if ahorro_c>=0 else '#FFF5F5'};
                      border-radius:8px;border:1.5px solid {color_ok};
                      display:flex;justify-content:space-between;align-items:center;">
            <div>
              <div style="font-size:9px;font-weight:700;color:#475569;
                          text-transform:uppercase;">💶 Ahorro fiscal</div>
              <div style="font-size:1.4rem;font-weight:900;color:{color_ok};">
                  {fmt_eur(ahorro_c)}</div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:10px;color:#475569;">Base reducida</div>
              <div style="font-size:1rem;font-weight:800;color:{color_ok};">
                  {fmt_eur(ahorro_b)}</div>
              <div style="font-size:9px;color:#94A3B8;margin-top:2px;">
                  ⚠️ Estimación · Año en curso</div>
            </div>
          </div>
        </div>
        <div style="background:#F8F9FA;border-radius:10px;padding:12px;
                    border:1px solid #E2E8F0;margin-bottom:12px;">
          <div style="font-size:9px;font-weight:800;color:#94A3B8;
                      text-transform:uppercase;margin-bottom:8px;">
              📅 Proyección a 31 dic {hoy.year}</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">
            <div><div style="font-size:10px;color:#94A3B8;">Acumulado a hoy</div>
                 <div style="font-size:1rem;font-weight:800;color:#059669;">
                     {fmt_eur(ing_acum)}</div></div>
            <div><div style="font-size:10px;color:#94A3B8;">Proyección anual</div>
                 <div style="font-size:1rem;font-weight:800;color:#1e293b;">
                     {fmt_eur(ing_proy)}</div></div>
            <div><div style="font-size:10px;color:#94A3B8;">Meses restantes</div>
                 <div style="font-size:1rem;font-weight:800;color:#534AB7;">
                     {meses_rest}</div></div>
            <div><div style="font-size:10px;color:#94A3B8;">Reducción aplicada</div>
                 <div style="font-size:1rem;font-weight:800;color:#534AB7;">
                     {m_opt["red_pct"]}%</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # SABIO IA — solo al pulsar botón
        ROBOT_B64 = "data:image/png;base64,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"
        robot_img = (f'<img src="{ROBOT_B64}" style="width:36px;height:36px;'
             f'border-radius:50%;object-fit:cover;margin-right:8px;">'
             ) if ROBOT_B64 else ""
        st.markdown(
            f'<div style="display:flex;align-items:center;margin-bottom:8px;">'
            f'{robot_img}'
            f'<span style="font-size:13px;font-weight:700;color:#534AB7;">'
            f'Sabio IA · Análisis Fiscal</span></div>',
            unsafe_allow_html=True)

        analisis_key = f"ia_{dec_key}_{int(ahorro_b*10)}"
        if st.button("🔬 Generar análisis fiscal",
                     key=f"btn_ia_{dec_key}",
                     use_container_width=True, type="primary"):
            # Leer estados actuales de la tabla
            _sem_local  = calcular_semaforo_inmueble(row)
            _alertas    = "; ".join([p.get("titulo","")
                          for p in _sem_local.get("problemas",[])])
            _acc_rep    = dec.get("acc_rep","gasto")
            _acc_amort  = dec.get("acc_amort","aplicar")
            _rep_v      = sf(row.get("reparaciones_anual",0))
            _amort_v    = amort_calc if _acc_amort=="aplicar" else 0
            # Gastos incluidos/excluidos
            _gastos_inc = []
            _gastos_exc = []
            for _dk, _lbl in [("intereses","Intereses"),("ibi","IBI"),
                               ("comunidad","Comunidad"),("seguro","Seguro"),
                               ("suministros","Suministros"),("juridicos","Jurídicos")]:
                if dec.get(f"acc_{_dk}","incluir") == "incluir":
                    _gastos_inc.append(_lbl)
                else:
                    _gastos_exc.append(_lbl)

            prompt = (
                f"Inmueble: {nombre_inm} · "
                f"{row.get('tipo_arrendamiento','Larga Duración')} · "
                f"Renta {fmt_eur(renta_mes)}/mes\n\n"
                f"SIN OPTIMIZAR: Base {fmt_eur(base_orig)} · "
                f"Cuota {fmt_eur(cuota_orig)}\n\n"
                f"DECISIONES DEL ASESOR:\n"
                f"  Gastos incluidos: {', '.join(_gastos_inc) or 'ninguno'}\n"
                f"  Gastos excluidos: {', '.join(_gastos_exc) or 'ninguno'}\n"
                f"  Reparaciones ({fmt_eur(_rep_v)}): {_acc_rep} — "
                f"{'deducción 100%' if _acc_rep=='gasto' else 'amort. 5%/año' if _acc_rep=='inversion' else 'excluido'}\n"
                f"  Amortización 3%: {'aplicada ' + fmt_eur(_amort_v) if _acc_amort=='aplicar' else 'excluida'} "
                f"(correcta: {fmt_eur(amort_calc)})\n"
                f"  Reducción: {m_opt['red_pct']}%\n\n"
                f"RESULTADO: Base fin ejercicio {fmt_eur(base_opt)} · "
                f"Cuota {fmt_eur(cuota_opt)} · "
                f"Ahorro fiscal {fmt_eur(ahorro_c)}\n\n"
                f"ALERTAS SEMÁFORO: {_alertas or 'ninguna'}\n\n"
                f"4 frases: (1) valoración de las decisiones tomadas, "
                f"(2) algo más que optimizar o corregir, "
                f"(3) riesgo ante inspección de Hacienda, "
                f"(4) acción concreta antes del 31/12."
            )
            system = (
                "Eres el Asesor Fiscal IA de FiscalHub. Hablas con un asesor "
                "fiscal profesional. Terminología fiscal española. "
                "Máximo 4 frases con euros reales. "
                "Distingue lo seguro de lo arriesgado."
            )
            from sabio_fiscal import _llamar_claude
            with st.spinner("Analizando..."):
                resultado = _llamar_claude(system, prompt, max_tokens=400)
            st.session_state[analisis_key] = resultado

        if st.session_state.get(analisis_key):
            st.markdown(
                f'<div style="background:#F0EEFF;border-radius:10px;'
                f'padding:14px 16px;margin-top:8px;'
                f'border-left:4px solid #534AB7;'
                f'font-size:13px;color:#1e293b;line-height:1.7;">'
                f'{st.session_state[analisis_key]}'
                f'</div>', unsafe_allow_html=True)
            cr1, cr2 = st.columns(2)
            with cr1:
                if st.button("↺ Regenerar", key=f"regen_{dec_key}"):
                    st.session_state.pop(analisis_key, None)
                    st.rerun()
            with cr2:
                if st.button("🗑 Borrar", key=f"del_ia_{dec_key}"):
                    st.session_state.pop(analisis_key, None)
                    st.rerun()

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    e1, e2, _ = st.columns([1, 1, 2])
    with e1:
        gen_pdf = st.button("📄 Generar PDF", key="fic_pdf",
                            use_container_width=True, type="primary")
    with e2:
        if st.button("← Volver", key="ficha_volver", use_container_width=True):
            st.session_state.fh_menu = "cliente"
            st.rerun()

    if gen_pdf:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                Table, TableStyle, HRFlowable, Image as RLImage, KeepTogether)
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
            import io, os, base64, tempfile
            from datetime import date as _d

            # ── Logo ──────────────────────────────────────────────
            _logo_path = "/mnt/user-data/uploads/Gemini_Generated_Image___2_.png"
            _logo_el   = None
            if os.path.exists(_logo_path):
                try:
                    _logo_el = RLImage(_logo_path, width=1.2*cm, height=1.2*cm)
                except Exception:
                    _logo_el = None

            buf = io.BytesIO()
            W, H = A4
            doc = SimpleDocTemplate(buf, pagesize=A4,
                leftMargin=2*cm, rightMargin=2*cm,
                topMargin=1.8*cm, bottomMargin=2*cm)

            PURPLE = colors.HexColor("#534AB7")
            DARK   = colors.HexColor("#0F172A")
            GRAY   = colors.HexColor("#64748B")
            GREEN_ = colors.HexColor("#059669")
            RED_   = colors.HexColor("#DC2626")
            LGRAY  = colors.HexColor("#F1F5F9")
            LPURP  = colors.HexColor("#F0EEFF")
            WHITE  = colors.white

            st_ = getSampleStyleSheet()
            def _ps(name, size, color=DARK, bold=False, align=TA_LEFT,
                    space_before=0, space_after=4, leading=None):
                return ParagraphStyle(name, parent=st_["Normal"],
                    fontSize=size,
                    textColor=color,
                    fontName="Helvetica-Bold" if bold else "Helvetica",
                    alignment=align,
                    spaceBefore=space_before,
                    spaceAfter=space_after,
                    leading=leading or size*1.4)

            p_brand  = _ps("brand",  18, PURPLE, bold=True, space_after=2)
            p_sub    = _ps("sub",     9, GRAY,   space_after=2)
            p_meta   = _ps("meta",    8, GRAY,   align=TA_RIGHT, space_after=0)
            p_h2     = _ps("h2",     11, DARK,   bold=True, space_before=14, space_after=5)
            p_body   = _ps("body",    9, DARK,   space_after=3)
            p_small  = _ps("small",   7, GRAY,   space_after=0)
            p_alert  = _ps("alert",   8, DARK,   space_after=3)

            # ── Función helper: tabla estilo ─────────────────────
            def _tbl_style(header_bg=PURPLE, stripe=LGRAY):
                return TableStyle([
                    ("BACKGROUND",    (0,0),(-1,0),  header_bg),
                    ("TEXTCOLOR",     (0,0),(-1,0),  WHITE),
                    ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
                    ("FONTSIZE",      (0,0),(-1,-1),  8),
                    ("ROWBACKGROUNDS",(0,1),(-1,-1), [stripe, WHITE]),
                    ("GRID",          (0,0),(-1,-1),  0.3,
                     colors.HexColor("#E2E8F0")),
                    ("ALIGN",         (0,0),(-1,0),  "CENTER"),
                    ("ALIGN",         (1,1),(-1,-1), "RIGHT"),
                    ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                    ("PADDING",       (0,0),(-1,-1),  5),
                    ("ROWHEIGHT",     (0,0),(-1,-1),  14),
                ])

            elems = []

            # ── CABECERA con logo ─────────────────────────────────
            hdr_data = [[
                _logo_el or Paragraph("FH", p_brand),
                [Paragraph("FiscalHub", p_brand),
                 Paragraph("Informe Fiscal de Arrendamiento", p_sub)],
                [Paragraph(f"Generado: {_d.today().strftime('%d/%m/%Y')}", p_meta),
                 Paragraph(f"Asesor: {st.session_state.get('fh_nombre_asesor') or st.session_state.get('fh_asesor',{}).get('nombre','—')}", p_meta)]
            ]]
            hdr_tbl = Table(hdr_data, colWidths=[1.5*cm, 10*cm, 5*cm])
            hdr_tbl.setStyle(TableStyle([
                ("VALIGN",  (0,0),(-1,-1), "MIDDLE"),
                ("PADDING", (0,0),(-1,-1), 0),
                ("LINEBELOW",(0,0),(-1,0), 1.5, PURPLE),
            ]))
            elems.append(hdr_tbl)
            elems.append(Spacer(1, 10))

            # ── Datos del inmueble ────────────────────────────────
            inq_str = str(row.get("inquilino") or row.get("Inquilino","—"))
            tipo_str= str(row.get("tipo_arrendamiento","Larga Duracion"))
            inm_data = [[
                Paragraph("<b>Inmueble</b>", p_body),
                Paragraph(nombre_inm, p_body),
                Paragraph("<b>Tipo contrato</b>", p_body),
                Paragraph(tipo_str, p_body),
            ],[
                Paragraph("<b>Inquilino</b>", p_body),
                Paragraph(inq_str, p_body),
                Paragraph("<b>Renta mensual</b>", p_body),
                Paragraph(fmt_eur(renta_mes), p_body),
            ]]
            inm_tbl = Table(inm_data, colWidths=[3*cm,5.5*cm,3*cm,5*cm])
            inm_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0,0),(0,-1), LGRAY),
                ("BACKGROUND", (2,0),(2,-1), LGRAY),
                ("FONTNAME",   (0,0),(0,-1), "Helvetica-Bold"),
                ("FONTNAME",   (2,0),(2,-1), "Helvetica-Bold"),
                ("FONTSIZE",   (0,0),(-1,-1), 8),
                ("GRID",       (0,0),(-1,-1), 0.3,
                 colors.HexColor("#E2E8F0")),
                ("PADDING",    (0,0),(-1,-1), 5),
                ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
            ]))
            elems.append(inm_tbl)
            elems.append(Spacer(1, 10))

            # ── Comparativa fiscal ────────────────────────────────
            m_opt_pdf = _simular_tabla(row, dec)
            base_o  = m_base["rend_final"]
            base_s  = m_opt_pdf["rend_final"]
            cuota_o = round(max(base_o * 0.30, 0), 2)
            cuota_s = round(max(base_s * 0.30, 0), 2)
            ahorro_pdf = round(cuota_o - cuota_s, 2)

            elems.append(Paragraph("Impacto Fiscal: Sin optimizar vs. Con asesor", p_h2))

            cmp_data = [
                ["Concepto", "Sin optimizar", "Con asesor", "Diferencia"],
                ["Ingresos anuales (0102)",
                 fmt_eur(m_base["ingresos"]),
                 fmt_eur(m_opt_pdf["ingresos"]), "—"],
                ["Gastos deducibles",
                 fmt_eur(m_base["total_gastos"]),
                 fmt_eur(m_opt_pdf["total_gastos"]),
                 fmt_eur(m_opt_pdf["total_gastos"]-m_base["total_gastos"])],
                ["Rendimiento neto (0149)",
                 fmt_eur(m_base["rend_neto"]),
                 fmt_eur(m_opt_pdf["rend_neto"]), "—"],
                [f"Reduccion {m_base['red_pct']}% / {m_opt_pdf['red_pct']}%",
                 fmt_eur(m_base["reduccion"]),
                 fmt_eur(m_opt_pdf["reduccion"]), "—"],
                ["BASE IMPONIBLE (0156)",
                 fmt_eur(base_o),
                 fmt_eur(base_s),
                 fmt_eur(base_s-base_o)],
                ["Cuota est. IRPF (30%)",
                 fmt_eur(cuota_o),
                 fmt_eur(cuota_s),
                 fmt_eur(cuota_s-cuota_o)],
            ]
            cmp_tbl = Table(cmp_data, colWidths=[6*cm,3*cm,3.5*cm,4*cm])
            cmp_style = _tbl_style()
            # Fila BASE IMPONIBLE en negrita
            cmp_style.add("FONTNAME",   (0,5),(-1,5), "Helvetica-Bold")
            cmp_style.add("BACKGROUND", (0,5),(-1,5), LPURP)
            cmp_style.add("TEXTCOLOR",  (0,5),(-1,5), PURPLE)
            cmp_tbl.setStyle(cmp_style)
            elems.append(cmp_tbl)

            # Caja de ahorro destacada
            ahorro_color = GREEN_ if ahorro_pdf >= 0 else RED_
            ahorro_data  = [[
                Paragraph("AHORRO FISCAL CONSEGUIDO", _ps("ak",9,WHITE,bold=True)),
                Paragraph(fmt_eur(ahorro_pdf),
                          _ps("av",14,WHITE,bold=True,align=TA_RIGHT)),
            ]]
            ahorro_tbl = Table(ahorro_data, colWidths=[12*cm,4.5*cm])
            ahorro_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0,0),(-1,0), ahorro_color),
                ("VALIGN",     (0,0),(-1,0), "MIDDLE"),
                ("PADDING",    (0,0),(-1,0), 8),
                ("ROUNDEDCORNERS", [4,4,4,4]),
            ]))
            elems.append(Spacer(1,4))
            elems.append(ahorro_tbl)
            elems.append(Spacer(1,10))

            # ── Decisiones del asesor ─────────────────────────────
            elems.append(Paragraph("Decisiones aplicadas por el asesor", p_h2))
            dec_data = [["Casilla","Concepto","Importe","Accion"]]
            for _dk, _cas, _lbl in [
                ("intereses","0105","Intereses hipoteca"),
                ("ibi",      "0106","IBI y tributos"),
                ("comunidad","0107","Comunidad propietarios"),
                ("seguro",   "0110","Seguro hogar y vida"),
                ("suministros","0111","Suministros"),
                ("juridicos","0112","Gastos juridicos"),
            ]:
                _val = {"intereses":sf(row.get("intereses_hipoteca",0)),
                        "ibi":sf(row.get("ibi_anual",0)),
                        "comunidad":sf(row.get("comunidad",0))*12,
                        "seguro":sf(row.get("seguro_anual",0)),
                        "suministros":sf(row.get("suministros_anual",0)),
                        "juridicos":sf(row.get("gastos_juridicos_anual",0)),
                       }.get(_dk,0)
                _acc = dec.get(f"acc_{_dk}","incluir")
                dec_data.append([_cas, _lbl, fmt_eur(_val),
                                  "Incluido" if _acc=="incluir" else "Excluido"])
            # Reparaciones
            _ra  = dec.get("acc_rep","gasto")
            _rv  = sf(row.get("reparaciones_anual",0))
            dec_data.append(["0104","Reparaciones y mantenimiento",fmt_eur(_rv),
                {"gasto":"Gasto directo 100%",
                 "inversion":"Inversion 5%/anio",
                 "excluir":"Excluido"}.get(_ra,"—")])
            # Amortizacion
            _aa  = dec.get("acc_amort","aplicar")
            dec_data.append(["0109","Amortizacion 3% construccion",
                fmt_eur(amort_calc) if _aa=="aplicar" else "0 EUR",
                "Aplicada (calculo auto)" if _aa=="aplicar" else "No aplicada"])

            dec_tbl = Table(dec_data, colWidths=[1.8*cm,6*cm,2.5*cm,6.2*cm])
            dec_tbl.setStyle(_tbl_style())
            elems.append(dec_tbl)
            elems.append(Spacer(1,10))

            # ── Alertas semaforo ──────────────────────────────────
            _sem_pdf = calcular_semaforo_inmueble(row)
            _probs   = _sem_pdf.get("problemas",[])
            if _probs:
                elems.append(Paragraph("Alertas detectadas por el semaforo fiscal", p_h2))
                al_data = [["Nivel","Concepto","Descripcion"]]
                for p_ in _probs:
                    nivel = "CRITICO" if p_.get("tipo")=="crit" else "REVISION"
                    al_data.append([nivel,
                        p_.get("titulo",""),
                        p_.get("descripcion","") or "Verificar"])
                al_tbl = Table(al_data, colWidths=[2*cm,5*cm,9.5*cm])
                al_style = _tbl_style(header_bg=RED_)
                # Colorear celdas CRITICO
                for ri_, row_ in enumerate(al_data[1:],1):
                    if row_[0]=="CRITICO":
                        al_style.add("TEXTCOLOR",(0,ri_),(0,ri_),RED_)
                        al_style.add("FONTNAME", (0,ri_),(0,ri_),"Helvetica-Bold")
                    else:
                        al_style.add("TEXTCOLOR",(0,ri_),(0,ri_),
                                     colors.HexColor("#D97706"))
                al_tbl.setStyle(al_style)
                elems.append(al_tbl)
                elems.append(Spacer(1,10))

            # ── Analisis IA si existe ─────────────────────────────
            ia_txt = st.session_state.get(analisis_key)
            if ia_txt:
                elems.append(Paragraph("Analisis del Sabio IA", p_h2))
                ia_data = [[Paragraph(ia_txt, p_body)]]
                ia_tbl  = Table(ia_data, colWidths=[16.5*cm])
                ia_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0,0),(-1,-1), LPURP),
                    ("LINERIGHT",  (0,0),(0,-1),  3, PURPLE),
                    ("PADDING",    (0,0),(-1,-1),  8),
                ]))
                elems.append(ia_tbl)
                elems.append(Spacer(1,10))

            # ── Pie de pagina ─────────────────────────────────────
            elems.append(HRFlowable(width="100%", thickness=0.5,
                color=GRAY, spaceAfter=4))
            elems.append(Paragraph(
                "Documento orientativo generado por FiscalHub. "
                "Cuotas IRPF estimadas al tipo marginal del 30%. "
                "Verificar con software oficial AEAT antes de presentar.",
                p_small))

            doc.build(elems)
            buf.seek(0)
            st.download_button(
                "Descargar PDF",
                data=buf,
                file_name=f"FiscalHub_{nombre_inm.replace(' ','_').replace('/','_')}.pdf",
                mime="application/pdf",
                key="fic_pdf_dl")

        except ImportError:
            st.error("ReportLab no instalado. Añade reportlab a requirements.txt")
        except Exception as e_pdf:
            st.error(f"Error PDF: {str(e_pdf)[:200]}")


def pantalla_resumen_global():
    cliente_id = st.session_state.get("fh_cliente_sel")
    cartera    = st.session_state.get("fh_cartera", [])
    cliente    = next((c for c in cartera if c["id"]==cliente_id), None)
    if not cliente: st.warning("Selecciona un cliente."); return

    df_inm = cliente["df_inm"]; df_mov = cliente["df_mov"]; nombre = cliente["nombre"]
    vlds   = st.session_state.get("fh_validaciones",{}).get(cliente_id,{})
    modelo = calcular_modelo100_global(df_inm, df_mov)
    col_n  = "nombre" if "nombre" in df_inm.columns else "Nombre"
    nombres= [str(r.get(col_n,"")) for _,r in df_inm.iterrows()] if not df_inm.empty else []
    n_manual = sum(1 for nm in nombres if vlds.get(nm,{}).get("manual",False))

    if st.button("← Volver al cliente", key="gl_back"):
        st.session_state.fh_menu = "cliente"; st.rerun()

    st.markdown(f"""<div style="margin-bottom:14px;">
      <div class="nc-page-label">Resumen global IRPF 2025</div>
      <div class="nc-page-title">{nombre}</div>
      <div class="nc-page-sub">{len(nombres)} inmuebles · Modelo 100 consolidado</div>
    </div>""", unsafe_allow_html=True)

    if n_manual > 0:
        st.markdown(f"""<div class="nc-callout warn">
          <strong>⚠️ {n_manual} inmueble{"s" if n_manual>1 else ""} con validación manual</strong> —
          Verificar antes de presentar a la AEAT.
        </div>""", unsafe_allow_html=True)

    _cc_gl = _color_cli(cliente_id)
    render_kpi_grid([
        {"label":"📥 0102 Ingresos",
         "value":fmt_eur(modelo.get("ingresos",0)),
         "color":GREEN,    "border_color":_cc_gl, "subtitle":f"{len(nombres)} inmuebles"},
        {"label":"📤 Gastos deducibles",
         "value":f"−{fmt_eur(modelo.get('total_gastos',0))}",
         "color":RED,      "border_color":_cc_gl, "subtitle":"Total deducible"},
        {"label":"⚖️ 0149 Rend. neto",
         "value":fmt_eur(modelo.get("rend_neto",0)),
         "color":ACCENT_F, "border_color":_cc_gl, "subtitle":"Antes de reducción"},
        {"label":"🧾 0156 Base imp.",
         "value":fmt_eur(modelo.get("rend_final",0)),
         "color":AMBER,    "border_color":_cc_gl, "subtitle":"⚠️ Orientativa"},
    ])

    st.markdown('<div class="nc-section">Desglose por inmueble</div>', unsafe_allow_html=True)
    if not df_inm.empty:
        # Grid 3 columnas — mismo patrón de cards que pantalla_cliente
        cols_grid = st.columns(3)
        for idx_, (_, row_g) in enumerate(df_inm.iterrows()):
            nm_g   = str(row_g.get(col_n,""))
            m_g    = calcular_modelo100_inmueble(row_g, df_mov)
            manual = vlds.get(nm_g,{}).get("manual",False)
            tipo_g = str(row_g.get("tipo_arrendamiento") or
                         row_g.get("Tipo_Arrendamiento","Larga Duración"))
            inq_g  = str(row_g.get("inquilino") or row_g.get("Inquilino","—"))
            hdr_c  = _color_cli(cliente_id)
            badge  = ("✎ Manual" if manual else "✓ Auto")
            badge_c= ("#D97706" if manual else "#059669")
            rend_c = "#059669" if m_g["rend_final"] >= 0 else "#DC2626"

            hdr_html = f"""
            <div style="background:{hdr_c};border-radius:10px 10px 0 0;
                        padding:12px 14px 10px;">
              <div style="font-size:15px;font-weight:800;color:#FFF;
                          line-height:1.2;margin-bottom:4px;">{nm_g}</div>
              <div style="font-size:11px;color:rgba(255,255,255,0.8);">
                {inq_g[:22]} · {tipo_g}</div>
              <div style="margin-top:6px;">
                <span style="background:rgba(255,255,255,0.18);color:#FFF;
                             font-size:10px;font-weight:700;padding:2px 8px;
                             border-radius:12px;">{badge}</span>
              </div>
            </div>"""
            body_html = f"""
            <div style="background:#FFF;border:1px solid #E2E8F0;
                        border-top:none;border-radius:0 0 10px 10px;
                        padding:12px 14px;margin-bottom:4px;">
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                <div>
                  <div style="font-size:10px;color:#94A3B8;margin-bottom:2px;">
                    0102 Ingresos</div>
                  <div style="font-size:15px;font-weight:800;color:#059669;">
                    {fmt_eur(m_g["ingresos"])}</div>
                </div>
                <div>
                  <div style="font-size:10px;color:#94A3B8;margin-bottom:2px;">
                    Gastos totales</div>
                  <div style="font-size:15px;font-weight:800;color:#DC2626;">
                    −{fmt_eur(m_g["total_gastos"])}</div>
                </div>
                <div>
                  <div style="font-size:10px;color:#94A3B8;margin-bottom:2px;">
                    0149 Rend. neto</div>
                  <div style="font-size:14px;font-weight:700;color:#534AB7;">
                    {fmt_eur(m_g["rend_neto"])}</div>
                </div>
                <div>
                  <div style="font-size:10px;color:#94A3B8;margin-bottom:2px;">
                    Reducción {m_g["red_pct"]}%</div>
                  <div style="font-size:14px;font-weight:700;color:#475569;">
                    −{fmt_eur(m_g["reduccion"])}</div>
                </div>
              </div>
              <div style="margin-top:10px;padding-top:8px;
                          border-top:1px solid #F1F5F9;
                          display:flex;justify-content:space-between;
                          align-items:center;">
                <div>
                  <div style="font-size:10px;color:#94A3B8;">0156 Base imp. est.</div>
                  <div style="font-size:1.3rem;font-weight:900;color:{rend_c};">
                    {fmt_eur(m_g["rend_final"])}</div>
                </div>
              </div>
            </div>"""
            with cols_grid[idx_ % 3]:
                st.markdown(hdr_html + body_html, unsafe_allow_html=True)


    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    asesor = st.session_state.get("fh_asesor",{})
    nombre_asesor = asesor.get("despacho", asesor.get("nombre",""))
    e1,e2 = st.columns(2)
    with e1:
        if st.button("📄 Exportar PDF completo", type="primary", use_container_width=True, key="gl_pdf"):
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.lib import colors
                from reportlab.lib.units import cm
                from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                    Spacer, Table, TableStyle, HRFlowable)
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.enums import TA_RIGHT
                import io
                from datetime import date as _d2

                _buf = io.BytesIO()
                _doc = SimpleDocTemplate(_buf, pagesize=A4,
                    leftMargin=2*cm, rightMargin=2*cm,
                    topMargin=2*cm, bottomMargin=2*cm)
                _st  = getSampleStyleSheet()
                _PU  = colors.HexColor("#534AB7")
                _DK  = colors.HexColor("#0F172A")
                _GR  = colors.HexColor("#64748B")
                _h1  = ParagraphStyle("gh1", parent=_st["Normal"],
                    fontSize=18, textColor=_PU, fontName="Helvetica-Bold", spaceAfter=4)
                _h2  = ParagraphStyle("gh2", parent=_st["Normal"],
                    fontSize=11, textColor=_DK, fontName="Helvetica-Bold",
                    spaceBefore=12, spaceAfter=4)
                _bd  = ParagraphStyle("gbd", parent=_st["Normal"],
                    fontSize=9, textColor=_DK, leading=14)
                _sm  = ParagraphStyle("gsm", parent=_st["Normal"],
                    fontSize=8, textColor=_GR, leading=12)
                _rt  = ParagraphStyle("grt", parent=_st["Normal"],
                    fontSize=9, textColor=_GR, alignment=TA_RIGHT)

                _el = []
                _el.append(Paragraph("FiscalHub · Resumen Global IRPF", _h1))
                _el.append(Paragraph(
                    f"<b>{nombre}</b> &nbsp;·&nbsp; "
                    f"{len(nombres)} inmuebles &nbsp;·&nbsp; "
                    f"Ejercicio 2025", _bd))
                _el.append(Paragraph(
                    f"Generado el {_d2.today().strftime('%d/%m/%Y')} &nbsp;·&nbsp; "
                    f"Asesor: {nombre_asesor or '—'}", _rt))
                _el.append(HRFlowable(width="100%", thickness=1,
                    color=_PU, spaceAfter=8))

                # KPIs globales
                _el.append(Paragraph("Modelo 100 consolidado", _h2))
                _gl_rows = [
                    ["Casilla", "Concepto", "Importe"],
                    ["0102", "Ingresos totales",
                     fmt_eur(modelo.get("ingresos",0))],
                    ["0105-0112", "Gastos deducibles totales",
                     f"−{fmt_eur(modelo.get('total_gastos',0))}"],
                    ["0149", "Rendimiento neto",
                     fmt_eur(modelo.get("rend_neto",0))],
                    ["0150", "Reducción aplicada",
                     f"−{fmt_eur(modelo.get('reduccion',0))}"],
                    ["0156", "BASE IMPONIBLE ESTIMADA",
                     fmt_eur(modelo.get("rend_final",0))],
                ]
                _gl_tbl = Table(_gl_rows, colWidths=[3*cm, 9*cm, 4*cm])
                _gl_tbl.setStyle(TableStyle([
                    ("BACKGROUND",  (0,0), (-1,0), _PU),
                    ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
                    ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
                    ("FONTSIZE",    (0,0), (-1,-1), 8),
                    ("ROWBACKGROUNDS",(0,1),(-1,-2),
                     [colors.HexColor("#F8FAFC"), colors.white]),
                    ("BACKGROUND",  (0,-1),(-1,-1), colors.HexColor("#F0EEFF")),
                    ("FONTNAME",    (0,-1),(-1,-1), "Helvetica-Bold"),
                    ("TEXTCOLOR",   (0,-1),(-1,-1), _PU),
                    ("GRID",        (0,0), (-1,-1), 0.3,
                     colors.HexColor("#E2E8F0")),
                    ("ALIGN",       (2,0), (2,-1), "RIGHT"),
                    ("PADDING",     (0,0), (-1,-1), 5),
                ]))
                _el.append(_gl_tbl)

                # Desglose por inmueble
                _el.append(Paragraph("Desglose por inmueble", _h2))
                _inm_rows = [["Inmueble","Ingresos","Gastos","Rend. neto","Base imp."]]
                for _, _r in df_inm.iterrows():
                    _nm = str(_r.get(col_n,""))
                    _mi = calcular_modelo100_inmueble(_r, df_mov)
                    _inm_rows.append([
                        _nm[:28],
                        fmt_eur(_mi.get("ingresos",0)),
                        fmt_eur(_mi.get("total_gastos",0)),
                        fmt_eur(_mi.get("rend_neto",0)),
                        fmt_eur(_mi.get("rend_final",0)),
                    ])
                _inm_tbl = Table(_inm_rows,
                    colWidths=[5.5*cm,3*cm,3*cm,3*cm,3*cm])
                _inm_tbl.setStyle(TableStyle([
                    ("BACKGROUND",  (0,0),(-1,0), colors.HexColor("#F1F5F9")),
                    ("FONTNAME",    (0,0),(-1,0), "Helvetica-Bold"),
                    ("FONTSIZE",    (0,0),(-1,-1), 8),
                    ("ROWBACKGROUNDS",(0,1),(-1,-1),
                     [colors.HexColor("#F8FAFC"), colors.white]),
                    ("GRID",        (0,0),(-1,-1), 0.3,
                     colors.HexColor("#E2E8F0")),
                    ("ALIGN",       (1,0),(-1,-1), "RIGHT"),
                    ("PADDING",     (0,0),(-1,-1), 5),
                ]))
                _el.append(_inm_tbl)

                _el.append(Spacer(1, 16))
                _el.append(HRFlowable(width="100%", thickness=0.5,
                    color=_GR, spaceAfter=4))
                _el.append(Paragraph(
                    "Documento orientativo. Base imponible estimada. "
                    "Verificar con software oficial AEAT antes de presentar.", _sm))

                _doc.build(_el)
                _buf.seek(0)
                st.session_state["fh_gl_pdf"] = _buf.read()
            except Exception as _e:
                st.error(f"Error generando PDF: {str(_e)[:150]}")
        if "fh_gl_pdf" in st.session_state:
            st.download_button("⬇️ Descargar PDF",data=st.session_state["fh_gl_pdf"],
                file_name=f"IRPF_{nombre.replace(' ','_')}_2025_global.pdf",
                mime="application/pdf",use_container_width=True,key="gl_pdf_dl")
    with e2:
        if st.button("📊 Exportar Excel", use_container_width=True, key="gl_xlsx"):
            try:
                import openpyxl
                from openpyxl.styles import (Font, PatternFill, Alignment,
                                              Border, Side)
                from openpyxl.utils import get_column_letter
                import io as _io2

                wb  = openpyxl.Workbook()
                ws  = wb.active
                ws.title = "Modelo 100"

                _PU_xl = "FF534AB7"
                _GN_xl = "FF059669"
                _RD_xl = "FFDC2626"
                _LG_xl = "FFF0EEFF"
                _GR_xl = "FFF1F5F9"

                def _hdr_cell(cell, txt, bg=_PU_xl):
                    cell.value = txt
                    cell.font  = Font(bold=True, color="FFFFFFFF", size=10)
                    cell.fill  = PatternFill("solid", fgColor=bg)
                    cell.alignment = Alignment(horizontal="center",
                                               vertical="center", wrap_text=True)

                def _data_cell(cell, val, bold=False, color="FF0F172A", align="left"):
                    cell.value = val
                    cell.font  = Font(bold=bold, color=color, size=9)
                    cell.alignment = Alignment(horizontal=align, vertical="center")

                thin = Side(style="thin", color="FFE2E8F0")
                brd  = Border(left=thin, right=thin, top=thin, bottom=thin)

                # ── Cabecera ──────────────────────────────────────
                ws.merge_cells("A1:G1")
                c = ws["A1"]
                c.value = f"FiscalHub · Resumen IRPF 2025 — {nombre}"
                c.font  = Font(bold=True, size=13, color="FF534AB7")
                c.alignment = Alignment(horizontal="center")
                ws.row_dimensions[1].height = 22

                ws.merge_cells("A2:G2")
                ws["A2"].value = (f"Asesor: {nombre_asesor or '—'} · "
                                  f"Generado: {_d2.today().strftime('%d/%m/%Y')}")
                ws["A2"].font  = Font(size=8, color="FF64748B")
                ws["A2"].alignment = Alignment(horizontal="center")
                ws.row_dimensions[2].height = 14

                # ── Cabecera columnas ─────────────────────────────
                hdrs = ["Inmueble","Tipo","Inquilino",
                        "Ingresos €","Gastos €","Rend. neto €",
                        "Base imp. €"]
                for ci, h in enumerate(hdrs, 1):
                    _hdr_cell(ws.cell(4, ci), h)
                ws.row_dimensions[4].height = 18

                # ── Filas por inmueble ────────────────────────────
                totales_i = totales_g = totales_n = totales_b = 0
                for ri, (_, row_x) in enumerate(df_inm.iterrows(), 5):
                    nm_x  = str(row_x.get(col_n,""))
                    m_x   = calcular_modelo100_inmueble(row_x, df_mov)
                    tp_x  = str(row_x.get("tipo_arrendamiento") or "—")
                    iq_x  = str(row_x.get("inquilino") or "—")
                    bg_row = _GR_xl if ri % 2 == 0 else "FFFFFFFF"
                    for ci_ in range(1, 8):
                        ws.cell(ri, ci_).fill = PatternFill("solid", fgColor=bg_row)
                        ws.cell(ri, ci_).border = brd

                    _data_cell(ws.cell(ri,1), nm_x, bold=True)
                    _data_cell(ws.cell(ri,2), tp_x)
                    _data_cell(ws.cell(ri,3), iq_x)
                    _data_cell(ws.cell(ri,4), m_x["ingresos"],
                               color=_GN_xl, align="right")
                    _data_cell(ws.cell(ri,5), -m_x["total_gastos"],
                               color=_RD_xl, align="right")
                    _data_cell(ws.cell(ri,6), m_x["rend_neto"], align="right")
                    _data_cell(ws.cell(ri,7), m_x["rend_final"],
                               bold=True, color="FF534AB7", align="right")
                    totales_i += m_x["ingresos"]
                    totales_g += m_x["total_gastos"]
                    totales_n += m_x["rend_neto"]
                    totales_b += m_x["rend_final"]
                    ws.row_dimensions[ri].height = 16

                # ── Fila totales ──────────────────────────────────
                tr = len(list(df_inm.iterrows())) + 5
                _hdr_cell(ws.cell(tr,1), "TOTAL", bg=_PU_xl)
                for ci_ in range(2,4):
                    ws.cell(tr,ci_).fill = PatternFill("solid", fgColor=_PU_xl)
                _data_cell(ws.cell(tr,4), totales_i,
                           bold=True, color="FFFFFFFF", align="right")
                ws.cell(tr,4).fill = PatternFill("solid", fgColor=_PU_xl)
                _data_cell(ws.cell(tr,5), -totales_g,
                           bold=True, color="FFFFFFFF", align="right")
                ws.cell(tr,5).fill = PatternFill("solid", fgColor=_PU_xl)
                _data_cell(ws.cell(tr,6), totales_n,
                           bold=True, color="FFFFFFFF", align="right")
                ws.cell(tr,6).fill = PatternFill("solid", fgColor=_PU_xl)
                _data_cell(ws.cell(tr,7), totales_b,
                           bold=True, color="FFFFFFFF", align="right")
                ws.cell(tr,7).fill = PatternFill("solid", fgColor=_PU_xl)
                ws.row_dimensions[tr].height = 18

                # Ancho columnas
                for ci_, w_ in enumerate([28,18,18,14,14,14,14], 1):
                    ws.column_dimensions[get_column_letter(ci_)].width = w_

                ws.freeze_panes = "A5"

                _xbuf = _io2.BytesIO()
                wb.save(_xbuf)
                _xbuf.seek(0)
                st.session_state["fh_gl_xlsx"] = _xbuf.read()
            except Exception as _ex:
                st.error(f"Error Excel: {str(_ex)[:150]}")
        if "fh_gl_xlsx" in st.session_state:
            st.download_button("⬇️ Descargar Excel",
                data=st.session_state["fh_gl_xlsx"],
                file_name=f"IRPF_{nombre.replace(' ','_')}_2025.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, key="gl_xlsx_dl")


# ── ALERTAS ───────────────────────────────────────────────────────
def pantalla_alertas():
    cartera = st.session_state.get("fh_cartera", [])
    todas = []
    for c in cartera:
        for a in c.get("alertas",[]):
            todas.append({**a, "cliente_nombre": c["nombre"], "cliente_id": c["id"]})
    todas.sort(key=lambda x:(0 if x["tipo"]=="crit" else 1))
    n_cr = len([a for a in todas if a["tipo"]=="crit"])
    n_wn = len([a for a in todas if a["tipo"]=="warn"])

    st.markdown(f"""<div style="margin-bottom:16px;">
      <div class="nc-page-label">Cartera completa · por urgencia</div>
      <div class="nc-page-title">Alertas fiscales</div>
      <div class="nc-page-sub">{len(todas)} alertas · {n_cr} críticas · {n_wn} a revisar</div>
    </div>""", unsafe_allow_html=True)

    imp = sum(a.get("impacto",0) for a in todas if a.get("impacto",0)>0)
    render_kpi_row([
        {"label":"🚨 Críticas",   "value":str(n_cr),
         "color":RED,    "subtitle":"Antes del 30 jun"},
        {"label":"⚡ A revisar",  "value":str(n_wn),
         "color":AMBER,  "subtitle":"Esta semana"},
        {"label":"💶 Impacto",    "value":fmt_eur(imp),
         "color":ACCENT_F, "subtitle":"Recuperable"},
    ])

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    if not todas: st.success("✅ Sin alertas activas."); return

    # Separar críticas y medias
    criticas = [a for a in todas if a["tipo"] == "crit"]
    medias   = [a for a in todas if a["tipo"] == "warn"]

    def _render_alertas_grid(lista, seccion_key):
        """Cards de alerta con patrón header coloreado + body + botón clicable."""
        MAX_COLS = 4
        for fila_start in range(0, len(lista), MAX_COLS):
            fila_rows = lista[fila_start:fila_start+MAX_COLS]
            cols = st.columns(MAX_COLS)
            for col_idx, a in enumerate(fila_rows):
                es_crit = a["tipo"] == "crit"
                tipo_lbl = "⚠️ Crítica" if es_crit else "◔ Revisar"
                # Color header: color del cliente (determinista)
                cli_id  = a.get("cliente_id", a.get("cliente_nombre",""))
                hdr_col = _color_cli(cli_id)
                # Badge color por tipo
                badge_bg = "rgba(220,38,38,0.12)" if es_crit else "rgba(217,119,6,0.12)"
                badge_col= "#DC2626" if es_crit else "#D97706"
                nm      = _e(a.get("cliente_nombre",""))
                inm     = _e(a.get("inmueble","")[:40])
                titulo  = _e(a.get("titulo",""))
                desc    = _e(a.get("desc","")[:120])
                accion  = _e(a.get("accion","")[:80])

                with cols[col_idx]:
                    html = (
                        f'<div style="background:{hdr_col};border-radius:12px 12px 0 0;'
                        f'padding:12px 14px 10px;margin-bottom:-1px;">'
                        f'<div style="font-size:11px;color:rgba(255,255,255,0.65);'
                        f'font-weight:600;letter-spacing:0.05em;margin-bottom:3px;">'
                        f'{tipo_lbl}</div>'
                        f'<div style="font-size:15px;font-weight:800;color:#FFF;'
                        f'line-height:1.2;">{nm}</div>'
                        f'<div style="font-size:11px;color:rgba(255,255,255,0.65);'
                        f'margin-top:2px;">📍 {inm}</div>'
                        f'</div>'
                        f'<div style="background:#FFF;border:2px solid #E2E8F0;'
                        f'border-top:none;border-radius:0 0 12px 12px;'
                        f'padding:12px 14px 10px;">'
                        f'<div style="font-size:14px;font-weight:700;color:#1e293b;'
                        f'margin-bottom:4px;">{titulo}</div>'
                        f'<div style="font-size:12px;color:#64748B;margin-bottom:8px;'
                        f'line-height:1.4;">{desc}</div>'
                        f'<div style="background:{badge_bg};border-radius:6px;'
                        f'padding:5px 10px;font-size:11px;font-weight:700;'
                        f'color:{badge_col};">→ {accion}</div>'
                        f'</div>'
                    )
                    st.markdown(html, unsafe_allow_html=True)
                    # Botón clicable — navega al cliente
                    cli_obj = next((c for c in cartera
                                    if c["nombre"]==a.get("cliente_nombre","")), None)
                    if st.button("🔍 Ir al cliente",
                                 key=f"alt_{seccion_key}_{fila_start}_{col_idx}",
                                 use_container_width=True):
                        if cli_obj:
                            st.session_state.fh_cliente_sel = cli_obj["id"]
                            st.session_state.fh_menu = "cliente"
                            st.rerun()
                    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if criticas:
        st.markdown('<div class="nc-section">🔴 Críticas — acción urgente</div>',
                    unsafe_allow_html=True)
        _render_alertas_grid(criticas, "cr")

    if medias:
        st.markdown('<div class="nc-section" style="margin-top:20px;">🟡 A revisar esta semana</div>',
                    unsafe_allow_html=True)
        _render_alertas_grid(medias, "wn")

# ── EXPORTAR ──────────────────────────────────────────────────────
def pantalla_exportar():
    cartera = st.session_state.get("fh_cartera",[])
    st.markdown("""<div style="margin-bottom:20px;">
      <div class="nc-page-label">Generación de entregables</div>
      <div class="nc-page-title">Exportar documentos</div>
      <div class="nc-page-sub">Revisa y exporta el modelo 100 de cada cliente.</div>
    </div>""", unsafe_allow_html=True)

    if not cartera:
        st.info("Sin clientes vinculados.")
        return

    _HDR = {"critico":"#7F1D1D","medio":"#78350F","ok":"#14532D"}
    _COL = {"critico":"#DC2626","medio":"#D97706","ok":"#059669"}
    _LBL = {"critico":"⚠ Crítico","medio":"◔ Revisar","ok":"✓ OK"}

    MAX_COLS = 4
    for fila_start in range(0, len(cartera), MAX_COLS):
        fila_rows = cartera[fila_start:fila_start+MAX_COLS]
        cols = st.columns(MAX_COLS)
        for col_idx, c in enumerate(fila_rows):
            estado  = c["estado"]
            hdr     = _HDR[estado]
            txt     = _COL[estado]
            lbl     = _LBL[estado]
            modelo  = c.get("modelo100",{})
            ingresos= fmt_eur(modelo.get("ingresos",0))
            base    = fmt_eur(modelo.get("rend_final",0))
            gastos  = fmt_eur(modelo.get("total_gastos",0))
            rend    = fmt_eur(modelo.get("rend_neto",0))
            criticas= c["criticas"]
            badge_bg= {"critico":"rgba(220,38,38,0.10)",
                       "medio":"rgba(217,119,6,0.10)",
                       "ok":"rgba(5,150,105,0.10)"}[estado]
            chk = "✅" if criticas == 0 else "⚠️"

            with cols[col_idx]:
                st.markdown(
                    f'<div style="background:{hdr};border-radius:12px 12px 0 0;' +
                    f'padding:14px 16px 12px;display:flex;align-items:center;' +
                    f'gap:10px;margin-bottom:-1px;">' +
                    f'<span style="font-size:22px;">📋</span>' +
                    f'<div style="flex:1;min-width:0;">' +
                    f'<div style="font-size:16px;font-weight:800;color:#FFF;' +
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' +
                    f'{c["nombre"]}</div>' +
                    f'<div style="font-size:12px;color:rgba(255,255,255,0.65);margin-top:2px;">' +
                    f'{c["inmuebles"]} inmuebles · campaña 2025</div></div>' +
                    f'<span style="background:rgba(255,255,255,0.15);color:#FFF;' +
                    f'font-size:11px;font-weight:700;padding:3px 8px;' +
                    f'border-radius:6px;">{lbl}</span></div>' +
                    f'<div style="background:#FFF;border:2px solid #E2E8F0;' +
                    f'border-top:none;border-radius:0 0 12px 12px;' +
                    f'padding:14px 16px 12px;">' +
                    f'<div style="display:flex;justify-content:space-between;' +
                    f'margin-bottom:6px;">' +
                    f'<span style="font-size:13px;color:#94A3B8;">📥 0102 Ingresos</span>' +
                    f'<span style="font-size:14px;font-weight:800;color:#059669;">{ingresos}</span></div>' +
                    f'<div style="display:flex;justify-content:space-between;' +
                    f'margin-bottom:6px;">' +
                    f'<span style="font-size:13px;color:#94A3B8;">📤 Gastos deducibles</span>' +
                    f'<span style="font-size:14px;font-weight:800;color:#DC2626;">-{gastos}</span></div>' +
                    f'<div style="display:flex;justify-content:space-between;' +
                    f'margin-bottom:6px;">' +
                    f'<span style="font-size:13px;color:#94A3B8;">⚖️ 0149 Rend. neto</span>' +
                    f'<span style="font-size:14px;font-weight:800;color:#534AB7;">{rend}</span></div>' +
                    f'<div style="display:flex;justify-content:space-between;' +
                    f'margin-bottom:10px;">' +
                    f'<span style="font-size:13px;color:#94A3B8;">{chk} Alertas</span>' +
                    f'<span style="font-size:14px;font-weight:800;color:{txt};">{criticas}</span></div>' +
                    f'<div style="background:{badge_bg};border-radius:6px;' +
                    f'padding:6px 10px;text-align:center;' +
                    f'font-size:13px;font-weight:700;color:{txt};">' +
                    f'🧾 Base imp. est.: {base}</div></div>',
                    unsafe_allow_html=True)

                if st.button("📄 Ir a revisión completa",
                             key=f"exp_{c['id']}_{col_idx}",
                             use_container_width=True, type="primary"):
                    st.session_state.fh_cliente_sel = c["id"]
                    st.session_state.fh_menu = "cliente"
                    st.rerun()
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── VINCULAR ──────────────────────────────────────────────────────
def pantalla_vincular():
    st.markdown("""<div style="margin-bottom:16px;">
      <div class="nc-page-label">Conectar con Nolasco Capital</div>
      <div class="nc-page-title">Vincular cliente</div>
      <div class="nc-page-sub">Introduce el código de 6 dígitos del propietario.</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("""<div class="nc-callout info" style="max-width:560px;margin-bottom:20px;">
      <strong>¿Cómo funciona?</strong> El propietario entra en Nolasco Capital →
      Privacidad → "Compartir con Asesor" → genera un código. Te lo envía y lo introduces aquí.
    </div>""", unsafe_allow_html=True)
    codigo = st.text_input("Código:", max_chars=10, placeholder="Ej: 628410", key="vincular_codigo")
    if st.button("🔗 Vincular", use_container_width=True, type="primary", key="vincular_btn"):
        if codigo.strip():
            with st.spinner("Verificando..."):
                res = vincular_propietario(st.session_state.fh_user_id, codigo.strip().upper())
            if res["ok"]:
                st.success(f"✅ Vinculado — {res.get('nombre','Propietario')} en tu cartera.")
                vinculos = get_clientes_vinculados(st.session_state.fh_user_id)
                st.session_state.fh_cartera = construir_cartera(vinculos)
                st.rerun()
            else: st.error(f"❌ {res.get('error','Código no válido')}")
        else: st.warning("Introduce un código")


# ── MOCK DATA — activar con ?demo=1 en la URL ─────────────────────
def _mock_cartera():
    """Cartera de demostración con 6 clientes ficticios + los reales."""
    import pandas as pd
    from datetime import date, timedelta

    def _inm(nombre, inquilino, tipo, renta, ibi, amort, seguro, comunidad,
             hipoteca=0, tiene_alerta=False, alerta_tipo="crit", alerta_txt=""):
        return {
            "nombre": nombre, "inquilino": inquilino,
            "tipo_arrendamiento": tipo, "renta": renta,
            "ibi_anual": ibi, "amortizacion_fiscal": amort,
            "seguro_anual": seguro, "comunidad": comunidad,
            "intereses_hipoteca": hipoteca,
            "tiene_alerta": tiene_alerta,
            "alerta_tipo": alerta_tipo, "alerta_txt": alerta_txt,
            "fecha_vencimiento_contrato": str(date.today() + timedelta(days=30)) if tiene_alerta else "",
            "precio_compra": 180000, "valor_catastral": 95000,
            "porcentaje_construccion": 0.7,
        }

    clientes_mock = [
        {
            "id": "mock-001", "nombre": "García Martínez, Ana",
            "estado": "critico", "criticas": 3, "medias": 1,
            "inmuebles": 3, "impacto": -2400,
            "alertas": [
                {"tipo":"crit","titulo":"Amortización a 0 — revisar","desc":"Catastral: 95.000 € · Precio compra: 180.000 €","accion":"Calcular 3% s/ MAX(precio compra, catastral) × % construcción","inmueble":"Calle Mayor 12","cliente_nombre":"García Martínez, Ana"},
                {"tipo":"crit","titulo":"Contrato próximo a vencer","desc":"Vence en 28 días sin renovar","accion":"Notificar al inquilino y preparar nuevo contrato","inmueble":"Av. Constitución 4","cliente_nombre":"García Martínez, Ana"},
                {"tipo":"crit","titulo":"ROE negativo","desc":"La hipoteca consume el 110% de los ingresos netos","accion":"Revisar si refinanciar o vender el activo","inmueble":"Plaza Nueva 8","cliente_nombre":"García Martínez, Ana"},
                {"tipo":"warn","titulo":"Rentabilidad por debajo de mercado","desc":"Rendimiento actual 3.2% vs 6.8% de media en CP 18001","accion":"Evaluar subida de renta en próxima renovación","inmueble":"Calle Mayor 12","cliente_nombre":"García Martínez, Ana"},
            ],
            "modelo100": {"ingresos":28800,"total_gastos":22400,"rend_neto":6400,"reduccion":3200,"rend_final":3200,"retenciones":5472,"intereses":4200,"reparaciones":800,"ibi":1240,"comunidad_seguros":3600,"suministros":0,"gastos_juridicos":0,"amortizacion":12560,"red_pct":50},
            "df_inm": pd.DataFrame([
                _inm("Calle Mayor 12","Luisa Fernández","Larga Duración",900,620,3800,380,1200,1800,True,"crit","Amortización a 0"),
                _inm("Av. Constitución 4","Roberto Sanz","Larga Duración",750,480,2900,290,900,0,True,"crit","Contrato vence 28 días"),
                _inm("Plaza Nueva 8","Carmen López","Larga Duración",550,390,2100,210,720,1600,True,"crit","ROE negativo"),
            ]),
            "df_mov": pd.DataFrame(),
        },
        {
            "id": "mock-002", "nombre": "López Ruiz, Carlos",
            "estado": "critico", "criticas": 2, "medias": 2,
            "inmuebles": 4, "impacto": -1800,
            "alertas": [
                {"tipo":"crit","titulo":"Amortización a 0 — revisar","desc":"Catastral: 112.000 € · Precio compra: 210.000 €","accion":"Calcular 3% s/ MAX","inmueble":"Gran Vía 33","cliente_nombre":"López Ruiz, Carlos"},
                {"tipo":"crit","titulo":"Gastos sin justificar","desc":"3 recibos de reparaciones sin factura adjunta","accion":"Solicitar facturas al propietario antes del 30/06","inmueble":"Recogidas 18","cliente_nombre":"López Ruiz, Carlos"},
                {"tipo":"warn","titulo":"IBI pendiente de actualizar","desc":"El IBI declarado no coincide con el recibo 2024","accion":"Verificar con el Ayuntamiento","inmueble":"Gran Vía 33","cliente_nombre":"López Ruiz, Carlos"},
                {"tipo":"warn","titulo":"Seguro infradeducido","desc":"Seguro hogar+vida deducible al 100% — solo se declaró el 50%","accion":"Corregir casilla 0110","inmueble":"Recogidas 18","cliente_nombre":"López Ruiz, Carlos"},
            ],
            "modelo100": {"ingresos":42000,"total_gastos":31200,"rend_neto":10800,"reduccion":5400,"rend_final":5400,"retenciones":7980,"intereses":6800,"reparaciones":1200,"ibi":1820,"comunidad_seguros":4800,"suministros":0,"gastos_juridicos":0,"amortizacion":16580,"red_pct":50},
            "df_inm": pd.DataFrame([
                _inm("Gran Vía 33","Marcos Vega","Larga Duración",1200,820,5200,480,1560,2400,True,"crit","Amortización a 0"),
                _inm("Recogidas 18","Sofía Moreno","Larga Duración",950,640,3900,360,1200,0,True,"crit","Gastos sin justificar"),
                _inm("Camino Ronda 5","Pedro Jiménez","Temporada",700,420,2800,260,840,0,False),
                _inm("Arabial 22","Nuria Castro","Larga Duración",650,380,2400,220,720,0,False),
            ]),
            "df_mov": pd.DataFrame(),
        },
        {
            "id": "mock-003", "nombre": "Martínez Peña, Isabel",
            "estado": "medio", "criticas": 0, "medias": 2,
            "inmuebles": 2, "impacto": 0,
            "alertas": [
                {"tipo":"warn","titulo":"Contrato vence en 45 días","desc":"Arrendamiento de larga duración próximo a expirar","accion":"Iniciar proceso de renovación o búsqueda de nuevo inquilino","inmueble":"Paseo Colón 7","cliente_nombre":"Martínez Peña, Isabel"},
                {"tipo":"warn","titulo":"Rentabilidad por debajo de mercado","desc":"Renta 4.1% vs 6.5% de media en CP 18002","accion":"Evaluar incremento según IRAV 2026 (2.47%)","inmueble":"San Juan de Dios 14","cliente_nombre":"Martínez Peña, Isabel"},
            ],
            "modelo100": {"ingresos":19200,"total_gastos":12800,"rend_neto":6400,"reduccion":3200,"rend_final":3200,"retenciones":3648,"intereses":2400,"reparaciones":400,"ibi":980,"comunidad_seguros":2400,"suministros":0,"gastos_juridicos":0,"amortizacion":6620,"red_pct":50},
            "df_inm": pd.DataFrame([
                _inm("Paseo Colón 7","Alberto García","Larga Duración",900,680,3200,300,960,0,True,"warn","Contrato vence 45 días"),
                _inm("San Juan de Dios 14","Elena Ruiz","Larga Duración",700,520,2400,240,720,0,True,"warn","Rentabilidad baja"),
            ]),
            "df_mov": pd.DataFrame(),
        },
        {
            "id": "mock-004", "nombre": "Sánchez Torres, Miguel",
            "estado": "ok", "criticas": 0, "medias": 0,
            "inmuebles": 2, "impacto": 0,
            "alertas": [],
            "modelo100": {"ingresos":22800,"total_gastos":14600,"rend_neto":8200,"reduccion":4100,"rend_final":4100,"retenciones":4332,"intereses":0,"reparaciones":600,"ibi":1100,"comunidad_seguros":3200,"suministros":0,"gastos_juridicos":0,"amortizacion":9700,"red_pct":50},
            "df_inm": pd.DataFrame([
                _inm("Alhambra 3","Rosa Blanco","Larga Duración",1100,760,4200,420,1320,0,False),
                _inm("Zaidín Norte 8","Jesús Molina","Larga Duración",800,580,3100,300,960,0,False),
            ]),
            "df_mov": pd.DataFrame(),
        },
        {
            "id": "mock-005", "nombre": "Fernández Gómez, Laura",
            "estado": "ok", "criticas": 0, "medias": 0,
            "inmuebles": 1, "impacto": 0,
            "alertas": [],
            "modelo100": {"ingresos":9600,"total_gastos":6200,"rend_neto":3400,"reduccion":1700,"rend_final":1700,"retenciones":1824,"intereses":0,"reparaciones":200,"ibi":480,"comunidad_seguros":1200,"suministros":0,"gastos_juridicos":0,"amortizacion":4320,"red_pct":50},
            "df_inm": pd.DataFrame([
                _inm("Neptuno 5","Diana Prieto","Larga Duración",800,480,2400,240,720,0,False),
            ]),
            "df_mov": pd.DataFrame(),
        },
        {
            "id": "mock-006", "nombre": "Romero Díaz, Antonio",
            "estado": "critico", "criticas": 1, "medias": 0,
            "inmuebles": 1, "impacto": -600,
            "alertas": [
                {"tipo":"crit","titulo":"Amortización a 0 — revisar","desc":"Catastral: 78.000 € · Precio compra: 145.000 €","accion":"Calcular 3% s/ MAX","inmueble":"Genil 12","cliente_nombre":"Romero Díaz, Antonio"},
            ],
            "modelo100": {"ingresos":9600,"total_gastos":7800,"rend_neto":1800,"reduccion":900,"rend_final":900,"retenciones":1824,"intereses":0,"reparaciones":300,"ibi":560,"comunidad_seguros":1440,"suministros":0,"gastos_juridicos":0,"amortizacion":5500,"red_pct":50},
            "df_inm": pd.DataFrame([
                _inm("Genil 12","Francisco Ruiz","Larga Duración",800,560,2800,280,840,0,True,"crit","Amortización a 0"),
            ]),
            "df_mov": pd.DataFrame(),
        },
    ]
    return sorted(clientes_mock, key=lambda x:({"critico":0,"medio":1,"ok":2}[x["estado"]],-x["criticas"]))


# ── MAIN ──────────────────────────────────────────────────────────
def main():
    inject_global_css("ficahub")
    if "fh_logged" not in st.session_state: st.session_state.fh_logged = False
    if "fh_menu"   not in st.session_state: st.session_state.fh_menu   = "cartera"

    if not st.session_state.fh_logged:
        pantalla_login(); return

    # Demo mode — añade ?demo=1 a la URL para ver mock data
    demo_mode = st.query_params.get("demo", "0") == "1"

    if "fh_cartera" not in st.session_state:
        with st.spinner("Cargando cartera..."):
            if demo_mode:
                # Cargar reales + mock
                vinculos = get_clientes_vinculados(st.session_state.fh_user_id)
                cartera_real = construir_cartera(vinculos)
                cartera_mock = _mock_cartera()
                # Evitar duplicados por nombre
                nombres_reales = {c["nombre"] for c in cartera_real}
                extra = [c for c in cartera_mock if c["nombre"] not in nombres_reales]
                st.session_state.fh_cartera = cartera_real + extra
            else:
                vinculos = get_clientes_vinculados(st.session_state.fh_user_id)
                st.session_state.fh_cartera = construir_cartera(vinculos)

    if demo_mode:
        st.sidebar.markdown(
            '<div style="background:#FFC107;color:#795548;font-size:10px;font-weight:700;'
            'padding:4px 10px;border-radius:6px;margin:4px 10px;text-align:center;'
            'letter-spacing:0.06em;">🎭 MODO DEMO</div>',
            unsafe_allow_html=True
        )

    with st.sidebar:
        render_sidebar()

    menu = st.session_state.get("fh_menu","cartera")
    st.markdown('<div class="nc-page">', unsafe_allow_html=True)
    if   menu == "cartera":        pantalla_cartera()
    elif menu == "cliente":        pantalla_cliente()
    elif menu == "ficha":          pantalla_ficha_inmueble()
    elif menu == "resumen_global": pantalla_resumen_global()
    elif menu == "alertas":        pantalla_alertas()
    elif menu == "exportar":       pantalla_exportar()
    elif menu == "vincular":       pantalla_vincular()
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
