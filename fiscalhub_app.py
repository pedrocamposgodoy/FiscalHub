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
from nolasco_styles import inject_global_css

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
        <div class="sb-nc">NC</div><div class="sb-wordmark">FiscalHub</div>
      </div>
      <div class="sb-tag">Portal asesoría fiscal</div>
    </div>
    <div class="sb-advisor">
      <div style="display:flex;gap:10px;align-items:center;">
        <div class="sb-avatar">{iniciales}</div>
        <div>
          <div style="font-size:12px;color:#F1F5F9;font-weight:500;">{nombre}</div>
          <div style="font-size:10px;color:#94A3B8;">{despacho}</div>
        </div>
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
      <div style="font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:#94A3B8;font-weight:600;">Cierre IRPF</div>
      <div class="sb-irpf-num" style="color:{color};">{dias}<span style="font-size:11px;font-weight:400;color:#94A3B8;margin-left:4px;">días</span></div>
      <div style="font-size:10px;color:#94A3B8;margin-top:2px;">30 jun · campaña 2025</div>
      <div class="sb-bar"><div class="sb-fill" style="width:{pct}%;background:{color};"></div></div>
      <div style="display:flex;justify-content:space-between;font-size:9px;color:#64748B;margin-top:5px;"><span>hoy</span><span>30 jun</span></div>
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
      <div class="fh-ey">Granada · Despacho fiscal</div>
      <div class="fh-title">Cartera de clientes</div>
      <div class="fh-sub">{len(cartera)} propietarios · {total_inm} inmuebles · campaña IRPF 2025</div>
    </div>""", unsafe_allow_html=True)

    k1,k2,k3,k4 = st.columns(4)
    with k1: st.markdown(f"""<div class="kpi"><div class="kpi-lbl">Clientes</div>
      <div class="kpi-val ac">{len(cartera)}</div>
      <div class="kpi-sub">{n_crit} críticos · {n_med} revisar · {n_ok} OK</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="kpi"><div class="kpi-lbl">Inmuebles gestionados</div>
      <div class="kpi-val ac">{total_inm}</div><div class="kpi-sub">Activos patrimoniales</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="kpi red"><div class="kpi-lbl">Alertas críticas</div>
      <div class="kpi-val cr">{total_crit}</div><div class="kpi-sub">Antes del 30 jun</div></div>""", unsafe_allow_html=True)
    with k4: st.markdown(f"""<div class="kpi gold"><div class="kpi-lbl">Impacto fiscal</div>
      <div class="kpi-val" style="color:var(--wn);">{fmt_eur(total_imp)}</div><div class="kpi-sub">Recuperable · cartera</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    cf1,cf2 = st.columns([3,1])
    with cf1: filtro = st.radio("",["Todos","Críticos","A revisar","OK"],horizontal=True,key="fh_filtro",label_visibility="collapsed")
    with cf2: busqueda = st.text_input("",placeholder="🔍 Buscar...",key="fh_busqueda",label_visibility="collapsed")

    rows = [c for c in cartera if
            (filtro=="Todos" or (filtro=="Críticos" and c["estado"]=="critico") or
             (filtro=="A revisar" and c["estado"]=="medio") or (filtro=="OK" and c["estado"]=="ok")) and
            (not busqueda or busqueda.lower() in c["nombre"].lower())]

    def _pill(e):
        if e=="critico": return '<span class="pill-cr"><span class="dot"></span>Crítico</span>'
        if e=="medio":   return '<span class="pill-wn"><span class="dot"></span>Revisar</span>'
        return '<span class="pill-ok"><span class="dot"></span>OK</span>'

    filas = ""
    for c in rows:
        rc  = "pr" if c["estado"]=="critico" else ("wn" if c["estado"]=="medio" else "")
        imp = fmt_eur(c["impacto"]) if c["impacto"] else "—"
        bcrit = f"<span class='bc'>{c['criticas']}</span>" if c['criticas'] else "<span class='bz'>0</span>"
        bmed  = f"<span class='bw'>{c['medias']}</span>" if c['medias'] else "<span class='bz'>0</span>"
        filas += f"""<tr class="{rc}">
          <td><div class="nm">{c["nombre"]}</div></td>
          <td style="text-align:right;" class="mono">{c["inmuebles"]}</td>
          <td style="text-align:center;">{bcrit}</td>
          <td style="text-align:center;">{bmed}</td>
          <td style="text-align:right;" class="mono">{imp}</td>
          <td>{_pill(c["estado"])}</td>
        </tr>"""

    st.markdown(f"""<table class="fh-tbl">
      <thead><tr>
        <th>Cliente</th><th style="text-align:right;">Inm.</th>
        <th style="text-align:center;">⚠ Críticas</th><th style="text-align:center;">◔ Medias</th>
        <th style="text-align:right;">Impacto IRPF</th><th>Estado</th>
      </tr></thead><tbody>{filas}</tbody></table>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="fh-ey" style="margin-bottom:6px;">Abrir cliente</div>', unsafe_allow_html=True)
    MAX_COLS = 4
    for i in range(0, len(rows), MAX_COLS):
        batch = rows[i:i+MAX_COLS]
        cols  = st.columns(MAX_COLS)
        for j, c in enumerate(batch):
            icon = "🔴" if c["estado"]=="critico" else "🟡" if c["estado"]=="medio" else "🟢"
            with cols[j]:
                if st.button(f"{icon} {c['nombre'][:22]}", key=f"sel_{c['id']}", use_container_width=True):
                    st.session_state.fh_cliente_sel = c["id"]
                    st.session_state.fh_menu = "cliente"
                    st.rerun()

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
      <div class="fh-ey">Revisión IRPF 2025</div>
      <div class="fh-title">{nombre}</div>
      <div class="fh-sub">{cliente["inmuebles"]} inmuebles · Campaña IRPF 2025</div>
    </div>""", unsafe_allow_html=True)

    k1,k2,k3,k4 = st.columns(4)
    with k1: st.markdown(f"""<div class="kpi grn"><div class="kpi-lbl">0102 Ingresos</div>
      <div class="kpi-val ok">{fmt_eur(modelo.get("ingresos",0))}</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="kpi red"><div class="kpi-lbl">Gastos deducibles</div>
      <div class="kpi-val cr">−{fmt_eur(modelo.get("total_gastos",0))}</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="kpi"><div class="kpi-lbl">0149 Rend. neto</div>
      <div class="kpi-val ac">{fmt_eur(modelo.get("rend_neto",0))}</div></div>""", unsafe_allow_html=True)
    with k4: st.markdown(f"""<div class="kpi gold"><div class="kpi-lbl">0156 Base imp. est.</div>
      <div class="kpi-val" style="color:var(--wn);">{fmt_eur(modelo.get("rend_final",0))}</div>
      <div class="kpi-sub">⚠️ Orientativa</div></div>""", unsafe_allow_html=True)

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
        st.markdown("""<div class="callout ok" style="margin-bottom:8px;">
          <strong>✅ Todos los inmuebles revisados</strong> — listo para el resumen global y exportar.
        </div>""", unsafe_allow_html=True)
        if st.button("📊 Resumen global → Exportar", type="primary", key="cli_global"):
            st.session_state.fh_menu = "resumen_global"
            st.rerun()

    st.markdown('<div class="fh-section">Inmuebles</div>', unsafe_allow_html=True)
    if df_inm.empty:
        st.info("Sin inmuebles registrados para este cliente."); return

    for idx, (_, row) in enumerate(df_inm.iterrows()):
        nombre_inm = str(row.get(col_n,""))
        sem        = calcular_semaforo_inmueble(row)
        vld        = vlds.get(nombre_inm,{})
        vld_estado = vld.get("estado","")
        vld_manual = vld.get("manual", False)

        if vld_estado in ("ok","vl"):
            rail_cls  = "vl" if vld_manual else "ok"
            pill_html = '<span class="pill-vl"><span class="dot"></span>Validado</span>' if vld_manual else \
                        '<span class="pill-ok"><span class="dot"></span>Correcto</span>'
        else:
            rail_cls  = sem["estado"]
            n_cr = len([p for p in sem["problemas"] if p["tipo"]=="crit"])
            n_wn = len([p for p in sem["problemas"] if p["tipo"]=="warn"])
            if sem["estado"]=="cr":
                pill_html = f'<span class="pill-cr"><span class="dot"></span>{n_cr} crítico{"s" if n_cr>1 else ""}</span>'
            elif sem["estado"]=="wn":
                pill_html = f'<span class="pill-wn"><span class="dot"></span>{n_wn} aviso{"s" if n_wn>1 else ""}</span>'
            else:
                pill_html = '<span class="pill-ok"><span class="dot"></span>Correcto</span>'

        renta    = _gv(row,"renta","Renta")
        ibi      = _gv(row,"ibi_anual","IBI_Anual")
        amort    = _gv(row,"amortizacion_fiscal","Amortizacion_Fiscal")
        seguro   = _gv(row,"seguro_anual","Seguro_Anual")
        comunidad= _gv(row,"comunidad","Comunidad")*12
        gastos   = ibi+amort+seguro+comunidad
        neto     = renta*12 - gastos

        if sem["problemas"] and vld_estado not in ("ok","vl"):
            p0 = sem["problemas"][0]["titulo"]
            mas = f' <span style="color:var(--txd);">+{len(sem["problemas"])-1} más</span>' if len(sem["problemas"])>1 else ""
            alertas_txt = f'<div class="inm-alerts">⚠ {p0}{mas}</div>'
        elif vld_manual:
            alertas_txt = '<div class="inm-alerts" style="color:var(--acc);">✓ Validado manualmente</div>'
        else:
            alertas_txt = '<div class="inm-alerts" style="color:var(--ok);">✓ Sin problemas detectados</div>'

        tipo_arr  = str(row.get("tipo_arrendamiento") or row.get("Tipo_Arrendamiento",""))
        inquilino = str(row.get("inquilino") or row.get("Inquilino","—"))

        st.markdown(f"""
        <div class="inm-row">
          <div class="inm-rail {rail_cls}"></div>
          <div class="inm-body">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div>
                <div class="inm-name">{nombre_inm}</div>
                <div class="inm-meta">{inquilino[:25]} · {tipo_arr}</div>
                {alertas_txt}
              </div>
              <div style="display:flex;align-items:center;gap:16px;flex-shrink:0;">
                <div class="inm-metrics">
                  <div style="text-align:center;">
                    <div class="inm-metric-lbl">Renta/mes</div>
                    <div class="inm-metric-val" style="color:var(--ok);">{fmt_eur(renta)}</div>
                  </div>
                  <div style="text-align:center;">
                    <div class="inm-metric-lbl">Gastos/año</div>
                    <div class="inm-metric-val" style="color:var(--cr);">−{fmt_eur(gastos)}</div>
                  </div>
                  <div style="text-align:center;">
                    <div class="inm-metric-lbl">Neto/año</div>
                    <div class="inm-metric-val">{fmt_eur(neto)}</div>
                  </div>
                </div>
                {pill_html}
              </div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        bc1,bc2,bc3 = st.columns([2,1,1])
        with bc1:
            if st.button(f"🔍 Revisar — {nombre_inm[:22]}",
                         key=f"rev_{cliente_id[:8]}_{idx}", use_container_width=True):
                st.session_state.fh_inmueble_sel = nombre_inm
                st.session_state.fh_menu = "ficha"
                st.rerun()
        with bc2:
            if vld_estado not in ("ok","vl") and sem["estado"] != "ok":
                if st.button("✅ Forzar validación",
                             key=f"vld_{cliente_id[:8]}_{idx}", use_container_width=True):
                    if "fh_validaciones" not in st.session_state: st.session_state.fh_validaciones = {}
                    if cliente_id not in st.session_state.fh_validaciones: st.session_state.fh_validaciones[cliente_id] = {}
                    st.session_state.fh_validaciones[cliente_id][nombre_inm] = {
                        "estado":"vl","manual":True,"fecha":date.today().strftime("%d/%m/%Y")}
                    st.rerun()
        with bc3:
            if vld_manual:
                if st.button("↩ Desvalidar",
                             key=f"dvl_{cliente_id[:8]}_{idx}", use_container_width=True):
                    st.session_state.fh_validaciones[cliente_id].pop(nombre_inm, None)
                    st.rerun()

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

    left, right = st.columns([1, 1])
    with left:
        renta     = _gv(row,"renta","Renta")
        ibi       = _gv(row,"ibi_anual","IBI_Anual")
        amort     = _gv(row,"amortizacion_fiscal","Amortizacion_Fiscal")
        seguro    = _gv(row,"seguro_anual","Seguro_Anual")
        comunidad = _gv(row,"comunidad","Comunidad")*12
        hipoteca  = _gv(row,"intereses_hipoteca","Intereses_Hipoteca")
        gastos_jur= _gv(row,"gastos_juridicos","Gastos_Juridicos")
        suministros=_gv(row,"servicios_suministros","Servicios_Suministros")
        gastos_items = [
            ("0102","Ingresos íntegros",  renta*12,    True,  "Renta anual"),
            ("0105","Intereses hipoteca", hipoteca,    hipoteca>0,   "Préstamo vinculado"),
            ("0106","IBI y tributos",      ibi,         ibi>0,        "Recibo IBI 2024"),
            ("0107","Comunidad propiet.", comunidad,   comunidad>0,  "Cuota anual"),
            ("0109","Amortización 3%",    amort,       amort>0,      "3% s/ valor construcción"),
            ("0110","Seguro hogar+vida",  seguro,      seguro>0,     "Póliza hogar/vida"),
            ("0111","Suministros",        suministros, suministros>0,"Servicios incluidos"),
            ("0112","Gastos jurídicos",   gastos_jur,  gastos_jur>0, "Honorarios, gestión"),
        ]
        chk_html = ""
        for cas, label, amt, on, hint in gastos_items:
            box = '<div class="chk-on">✓</div>' if on else '<div class="chk-off">✗</div>'
            amt_str = fmt_eur(amt) if amt else "Pendiente"
            amc = "" if on else "miss"
            chk_html += f"""<div class="chk-item">
              {box}<div class="chk-cas">{cas}</div>
              <div class="chk-lbl">{label}<div class="chk-hint">{hint}</div></div>
              <div class="chk-amt {amc}">{amt_str}</div>
            </div>"""
        faltan = sum(1 for _,_,a,on,_ in gastos_items[1:] if not on)
        st.markdown(f"""<div class="panel">
          <div class="panel-head"><span class="panel-title">Gastos deducibles</span>
            <span style="font-size:11px;color:var(--txm);">{len(gastos_items)-faltan-1}/{len(gastos_items)-1} registrados</span>
          </div>{chk_html}</div>""", unsafe_allow_html=True)

    with right:
        m = modelo
        casillas = [
            ("0102","Rendimiento íntegro","Ingresos anuales",m["ingresos"],False,False),
            ("0105","Intereses hipoteca","Préstamo vinculado",-m["intereses"],False,False),
            ("0106","IBI y tributos","Recibo IBI",-m["ibi"],False,False),
            ("0107","Comunidad + Seguros","Cuota + pólizas",-m["comunidad_seguros"],False,False),
            ("0104","Reparaciones","Del diario contable",-m["reparaciones"],False,False),
            ("0109","Amortización 3%","MAX(compra,catastral)×%c×3%",-m["amortizacion"],False,False),
            ("0111","Otros deducibles","Jurídicos, suministros",-(m["gastos_juridicos"]+m["suministros"]),False,False),
            ("0149","RENDIMIENTO NETO","",m["rend_neto"],True,False),
            (f"0150",f"Reducción {m['red_pct']}% (orient.)","⚠️ Validar",-m["reduccion"],False,False),
            ("0156","BASE IMPONIBLE EST.","Orientativa",m["rend_final"],False,True),
            ("0153","Retenciones pract.","",  -m["retenciones"],False,False),
        ]
        filas_m = ""
        for cas, label, sub, val, is_sum, is_final in casillas:
            tr_cls = "final" if is_final else ("sum" if is_sum else "")
            vc = ""
            if is_final: vc = "style='color:var(--acc2);'"
            elif is_sum: vc = "style='color:var(--tx2);'"
            elif val < 0: vc = "style='color:var(--cr);'"
            elif val > 0: vc = "style='color:var(--ok);'"
            sub_html = f'<div class="l-sub">{sub}</div>' if sub else ""
            filas_m += f"""<tr class="{tr_cls}">
              <td><span class="cas">{cas}</span></td>
              <td>{label}{sub_html}</td>
              <td class="r" {vc}>{fmt_eur(val)}</td>
            </tr>"""
        st.markdown(f"""<table class="m100">
          <thead><tr><th style="width:55px;">Casilla</th><th>Descripción</th><th class="r">Importe</th></tr></thead>
          <tbody>{filas_m}</tbody></table>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    e1,e2,_ = st.columns([1,1,2])
    with e1:
        gen_pdf = st.button("📄 Generar PDF", key="fic_pdf", use_container_width=True, type="primary")
        if gen_pdf or "fh_pdf_export" in st.session_state:
            if gen_pdf:
                try:
                    import reportlab
                    from fiscal_export import generar_pdf_global
                    fila = _build_fila_export(row, df_mov, modelo)
                    pdf  = generar_pdf_global([fila], _build_totales_export([fila]),
                        nombre_propietario=cliente["nombre"],
                        nombre_asesoria=st.session_state.get("fh_asesor",{}).get("despacho",""),
                        año_fiscal=2025)
                    st.session_state["fh_pdf_export"] = pdf.getvalue() if pdf else _pdf_simple(nombre_inm, cliente["nombre"], modelo)
                except:
                    st.session_state["fh_pdf_export"] = _pdf_simple(nombre_inm, cliente["nombre"], modelo)
            if "fh_pdf_export" in st.session_state:
                st.download_button("⬇️ Descargar PDF", data=st.session_state["fh_pdf_export"],
                    file_name=f"IRPF_{nombre_inm[:20].replace(' ','_')}_2025.pdf",
                    mime="application/pdf", use_container_width=True, key="fic_pdf_dl")
    with e2:
        if st.button("✅ Marcar revisado", key="fic_ok", use_container_width=True):
            if "fh_validaciones" not in st.session_state: st.session_state.fh_validaciones = {}
            if cliente_id not in st.session_state.fh_validaciones: st.session_state.fh_validaciones[cliente_id] = {}
            st.session_state.fh_validaciones[cliente_id][nombre_inm] = {
                "estado":"ok","manual":False,"fecha":date.today().strftime("%d/%m/%Y")}
            st.session_state.fh_menu = "cliente"
            st.session_state.pop("fh_inmueble_sel", None)
            st.session_state.pop("fh_pdf_export", None)
            st.rerun()

def _pdf_simple(nombre_inm, nombre_cliente, modelo):
    from reportlab.pdfgen import canvas as rlc
    from reportlab.lib.pagesizes import A4
    buf = io.BytesIO()
    c = rlc.Canvas(buf, pagesize=A4); w,h = A4
    c.setFont("Helvetica-Bold",14); c.drawString(50,h-60,f"FiscalHub — IRPF 2025 · {nombre_cliente}")
    c.setFont("Helvetica-Bold",12); c.drawString(50,h-90,f"Inmueble: {nombre_inm}")
    c.setFont("Helvetica",11); y = h-130
    for lbl,val in [("0102 Ingresos:",fmt_eur(modelo.get("ingresos",0))),
                    ("0149 Rend. neto:",fmt_eur(modelo.get("rend_neto",0))),
                    (f"0150 Reducción {modelo.get('red_pct',50)}%:",fmt_eur(-modelo.get("reduccion",0))),
                    ("0156 Base imp. est.:",fmt_eur(modelo.get("rend_final",0))),
                    ("0153 Retenciones:",fmt_eur(-modelo.get("retenciones",0)))]:
        c.drawString(50,y,f"{lbl}  {val}"); y-=22
    c.setFont("Helvetica-Oblique",9)
    c.drawString(50,50,"Documento informativo — validar con asesor fiscal")
    c.save(); buf.seek(0)
    return buf.getvalue()

def _build_fila_export(row, df_mov, modelo):
    return {
        "inmueble": str(row.get("nombre") or row.get("Nombre","")),
        "ref_catastral": str(row.get("ref_catastral") or "N/A"),
        "tipo": str(row.get("tipo_arrendamiento") or "Larga Duración"),
        "inquilino": str(row.get("inquilino") or ""),
        "nif_inquilino": str(row.get("nif_inquilino") or ""),
        "dias": modelo.get("dias",365),
        "ingresos": modelo["ingresos"],"intereses": modelo["intereses"],
        "reparaciones": modelo["reparaciones"],"ibi": modelo["ibi"],
        "comunidad_seguros": modelo["comunidad_seguros"],"suministros": modelo["suministros"],
        "gastos_juridicos": modelo["gastos_juridicos"],"amortizacion": modelo["amortizacion"],
        "amort_detalle":"","total_gastos": modelo["total_gastos"],
        "rend_neto": modelo["rend_neto"],"reduccion_pct": modelo["red_pct"],
        "reduccion_imp": modelo["reduccion"],"rend_final": modelo["rend_final"],
        "retenciones": modelo["retenciones"],"nota_reduccion":"Orientativa","ahorro_potencial":0,
    }

def _build_totales_export(filas):
    keys=["ingresos","intereses","reparaciones","ibi","comunidad_seguros","suministros",
          "gastos_juridicos","amortizacion","total_gastos","rend_neto","reduccion_imp","rend_final","retenciones"]
    t={k:sum(f.get(k,0) for f in filas) for k in keys}
    t.update({"n_inmuebles":len(filas),"año_fiscal":2025})
    return t

# ── RESUMEN GLOBAL ────────────────────────────────────────────────
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
      <div class="fh-ey">Resumen global IRPF 2025</div>
      <div class="fh-title">{nombre}</div>
      <div class="fh-sub">{len(nombres)} inmuebles · Modelo 100 consolidado</div>
    </div>""", unsafe_allow_html=True)

    if n_manual > 0:
        st.markdown(f"""<div class="callout wn">
          <strong>⚠️ {n_manual} inmueble{"s" if n_manual>1 else ""} con validación manual</strong> —
          Verificar antes de presentar a la AEAT.
        </div>""", unsafe_allow_html=True)

    k1,k2,k3,k4 = st.columns(4)
    with k1: st.markdown(f"""<div class="kpi grn"><div class="kpi-lbl">0102 Ingresos</div>
      <div class="kpi-val ok">{fmt_eur(modelo.get("ingresos",0))}</div>
      <div class="kpi-sub">{len(nombres)} inmuebles</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="kpi red"><div class="kpi-lbl">Gastos deducibles</div>
      <div class="kpi-val cr">−{fmt_eur(modelo.get("total_gastos",0))}</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="kpi"><div class="kpi-lbl">0149 Rend. neto</div>
      <div class="kpi-val">{fmt_eur(modelo.get("rend_neto",0))}</div></div>""", unsafe_allow_html=True)
    with k4: st.markdown(f"""<div class="kpi gold"><div class="kpi-lbl">0156 Base imp. est.</div>
      <div class="kpi-val ac">{fmt_eur(modelo.get("rend_final",0))}</div>
      <div class="kpi-sub">⚠️ Orientativa</div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="fh-section">Desglose por inmueble</div>', unsafe_allow_html=True)
    if not df_inm.empty:
        cards_html = '<div class="global-grid">'
        for _,row in df_inm.iterrows():
            nm     = str(row.get(col_n,""))
            m      = calcular_modelo100_inmueble(row, df_mov)
            manual = vlds.get(nm,{}).get("manual",False)
            tipo   = str(row.get("tipo_arrendamiento") or row.get("Tipo_Arrendamiento","Larga Duración"))
            inq    = str(row.get("inquilino") or row.get("Inquilino","—"))
            roof_cls  = "manual" if manual else ""
            badge_html = f'<span class="global-card-badge manual">✎ Manual</span>' if manual else \
                         f'<span class="global-card-badge">✓ Automático</span>'
            cards_html += f"""
            <div class="global-card">
              <div class="global-card-roof {roof_cls}"></div>
              <div class="global-card-body">
                <div class="global-card-name">{nm}</div>
                <div class="global-card-meta">{inq[:20]} · {tipo}</div>
                <div class="global-card-metrics">
                  <div class="global-metric">
                    <div class="global-metric-lbl">0102 Ingresos</div>
                    <div class="global-metric-val ok">{fmt_eur(m["ingresos"])}</div>
                  </div>
                  <div class="global-metric">
                    <div class="global-metric-lbl">Gastos totales</div>
                    <div class="global-metric-val cr">−{fmt_eur(m["total_gastos"])}</div>
                  </div>
                  <div class="global-metric">
                    <div class="global-metric-lbl">0149 Rend. neto</div>
                    <div class="global-metric-val tx">{fmt_eur(m["rend_neto"])}</div>
                  </div>
                  <div class="global-metric">
                    <div class="global-metric-lbl">Reducción {m["red_pct"]}%</div>
                    <div class="global-metric-val tx">−{fmt_eur(m["reduccion"])}</div>
                  </div>
                </div>
                <div class="global-card-footer">
                  <div>
                    <div class="global-card-base-lbl">0156 Base imp. estimada</div>
                    <div class="global-card-base-val">{fmt_eur(m["rend_final"])}</div>
                  </div>
                  {badge_html}
                </div>
              </div>
            </div>"""
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    asesor = st.session_state.get("fh_asesor",{})
    nombre_asesor = asesor.get("despacho", asesor.get("nombre",""))
    e1,e2 = st.columns(2)
    with e1:
        if st.button("📄 Exportar PDF completo", type="primary", use_container_width=True, key="gl_pdf"):
            try:
                import reportlab; from fiscal_export import generar_pdf_global
                filas = [_build_fila_export(row,df_mov,calcular_modelo100_inmueble(row,df_mov)) for _,row in df_inm.iterrows()]
                totales = _build_totales_export(filas)
                pdf = generar_pdf_global(filas,totales,nombre_propietario=nombre,nombre_asesoria=nombre_asesor,año_fiscal=2025)
                st.session_state["fh_gl_pdf"] = pdf.getvalue() if pdf else _pdf_simple(f"Global ({len(nombres)} inm.)",nombre,modelo)
            except: st.session_state["fh_gl_pdf"] = _pdf_simple(f"Global ({len(nombres)} inm.)",nombre,modelo)
        if "fh_gl_pdf" in st.session_state:
            st.download_button("⬇️ Descargar PDF",data=st.session_state["fh_gl_pdf"],
                file_name=f"IRPF_{nombre.replace(' ','_')}_2025_global.pdf",
                mime="application/pdf",use_container_width=True,key="gl_pdf_dl")
    with e2:
        if st.button("📊 Exportar Excel", use_container_width=True, key="gl_xlsx"):
            try:
                from fiscal_export import generar_excel_asesor
                filas = [_build_fila_export(row,df_mov,calcular_modelo100_inmueble(row,df_mov)) for _,row in df_inm.iterrows()]
                xlsx = generar_excel_asesor(_build_totales_export(filas),_build_totales_export(filas),
                    nombre_propietario=nombre,nombre_asesoria=nombre_asesor,año_fiscal=2025)
                if xlsx: st.session_state["fh_gl_xlsx"] = xlsx.getvalue()
            except Exception as e: st.error(f"Error Excel: {e}")
        if "fh_gl_xlsx" in st.session_state:
            st.download_button("⬇️ Descargar Excel",data=st.session_state["fh_gl_xlsx"],
                file_name=f"IRPF_{nombre.replace(' ','_')}_2025.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,key="gl_xlsx_dl")

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
      <div class="fh-ey">Cartera completa · por urgencia</div>
      <div class="fh-title">Alertas fiscales</div>
      <div class="fh-sub">{len(todas)} alertas · {n_cr} críticas · {n_wn} a revisar</div>
    </div>""", unsafe_allow_html=True)

    k1,k2,k3 = st.columns(3)
    with k1: st.markdown(f"""<div class="kpi red"><div class="kpi-lbl">Críticas</div>
      <div class="kpi-val cr">{n_cr}</div><div class="kpi-sub">Antes del 30 jun</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="kpi"><div class="kpi-lbl">A revisar</div>
      <div class="kpi-val" style="color:var(--wn);">{n_wn}</div></div>""", unsafe_allow_html=True)
    with k3:
        imp = sum(a.get("impacto",0) for a in todas if a.get("impacto",0)>0)
        st.markdown(f"""<div class="kpi gold"><div class="kpi-lbl">Impacto</div>
          <div class="kpi-val ac">{fmt_eur(imp)}</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    if not todas: st.success("✅ Sin alertas activas."); return

    # Separar críticas y medias
    criticas = [a for a in todas if a["tipo"] == "crit"]
    medias   = [a for a in todas if a["tipo"] == "warn"]

    def _render_cards(lista):
        cards_html = '<div class="alert-grid">'
        for a in lista:
            tc   = "cr" if a["tipo"]=="crit" else "wn"
            tipo_label = "⚠️ Crítica" if a["tipo"]=="crit" else "◔ Revisar"
            imp  = fmt_eur(a["impacto"]) if a.get("impacto",0)>0 else ""
            nm   = a["cliente_nombre"]
            inm  = a.get("inmueble","")[:35]
            titulo = a["titulo"]
            desc   = a.get("desc","")[:100]
            accion = a.get("accion","")[:60]
            cards_html += f"""
            <div class="alert-card">
              <div class="alert-card-top {tc}"></div>
              <div class="alert-card-body">
                <div class="alert-card-header">
                  <span class="alert-card-tipo {tc}">{tipo_label}</span>
                  {f'<span class="alert-card-imp">{imp}</span>' if imp else ''}
                </div>
                <div class="alert-card-client">{nm}</div>
                <div class="alert-card-inm">📍 {inm}</div>
                <div class="alert-card-title">{titulo}</div>
                <div class="alert-card-desc">{desc}</div>
                <div class="alert-card-action">→ {accion}</div>
              </div>
            </div>"""
        cards_html += '</div>'
        return cards_html

    if criticas:
        st.markdown('<div class="fh-section">🔴 Críticas — acción urgente</div>', unsafe_allow_html=True)
        st.markdown(_render_cards(criticas), unsafe_allow_html=True)

    if medias:
        st.markdown('<div class="fh-section" style="margin-top:20px;">🟡 A revisar esta semana</div>', unsafe_allow_html=True)
        st.markdown(_render_cards(medias), unsafe_allow_html=True)

# ── EXPORTAR ──────────────────────────────────────────────────────
def pantalla_exportar():
    cartera = st.session_state.get("fh_cartera",[])
    st.markdown("""<div style="margin-bottom:16px;">
      <div class="fh-ey">Generación de entregables</div>
      <div class="fh-title">Exportar</div>
      <div class="fh-sub">Selecciona un cliente para generar sus documentos IRPF.</div>
    </div>""", unsafe_allow_html=True)
    if cartera:
        sel = st.selectbox("Cliente:", [c["nombre"] for c in cartera], key="exp_sel")
        c_sel = next((c for c in cartera if c["nombre"]==sel), None)
        if c_sel and st.button("🔍 Ir a revisión", type="primary", use_container_width=True, key="exp_go"):
            st.session_state.fh_cliente_sel = c_sel["id"]
            st.session_state.fh_menu = "cliente"; st.rerun()
    else: st.info("Sin clientes vinculados.")

# ── VINCULAR ──────────────────────────────────────────────────────
def pantalla_vincular():
    st.markdown("""<div style="margin-bottom:16px;">
      <div class="fh-ey">Conectar con Nolasco Capital</div>
      <div class="fh-title">Vincular cliente</div>
      <div class="fh-sub">Introduce el código de 6 dígitos del propietario.</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("""<div class="callout inf" style="max-width:560px;margin-bottom:20px;">
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

# ── MAIN ──────────────────────────────────────────────────────────
def main():
    inject_global_css("ficahub")
    if "fh_logged" not in st.session_state: st.session_state.fh_logged = False
    if "fh_menu"   not in st.session_state: st.session_state.fh_menu   = "cartera"

    if not st.session_state.fh_logged:
        pantalla_login(); return

    if "fh_cartera" not in st.session_state:
        with st.spinner("Cargando cartera..."):
            vinculos = get_clientes_vinculados(st.session_state.fh_user_id)
            st.session_state.fh_cartera = construir_cartera(vinculos)

    with st.sidebar:
        render_sidebar()

    menu = st.session_state.get("fh_menu","cartera")
    st.markdown('<div class="fh-page">', unsafe_allow_html=True)
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
