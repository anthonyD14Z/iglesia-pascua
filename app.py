import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import base64
import requests
import urllib.parse

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Iglesia Cristo El Salvador", layout="wide")

# 2. API TASA BCV
def obtener_tasa_bcv():
    try:
        url = "https://ve.dolarapi.com/v1/dolares/oficial"
        return float(requests.get(url, timeout=10).json()['promedio'])
    except: return 50.0

# 3. FONDO PERSONALIZADO
def agregar_fondo(archivo):
    try:
        with open(archivo, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        st.markdown(f"""<style>.stApp {{ background-image: url("data:image/jpg;base64,{data}"); background-size: cover; background-attachment: fixed; }}
        [data-testid="stForm"], .stTabs, .stMetric, div.stAlert, .stDataFrame {{ background-color: rgba(255, 255, 255, 0.96) !important; padding: 20px; border-radius: 15px; }}
        </style>""", unsafe_allow_html=True)
    except: pass

agregar_fondo('1000687124.jpg')

# 4. BASE DE DATOS
conn = sqlite3.connect('iglesia_pascua_web.db', check_same_thread=False)
curr = conn.cursor()
curr.execute("CREATE TABLE IF NOT EXISTS finanzas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, referencia TEXT, monto_ves REAL, tasa REAL, monto_usd REAL, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS materiales (id INTEGER PRIMARY KEY AUTOINCREMENT, donante TEXT, categoria TEXT, descripcion TEXT, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono TEXT, fecha DATE)")
conn.commit()

# 5. USUARIOS Y ROLES
USUARIOS = {
    "tesorero": {"clave": "finanzas2026", "rol": "finanzas"},
    "secretario": {"clave": "iglesia2026", "rol": "asistencia"},
    "donaciones": {"clave": "pascua2026", "rol": "materiales"},
    "admin": {"clave": "pastor2026", "rol": "todos"}
}

if "sesion" not in st.session_state: st.session_state.sesion = None
if "recuperar" not in st.session_state: st.session_state.recuperar = False

# --- LOGIN Y RECUPERACIÓN ---
if st.session_state.sesion is None:
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso al Sistema</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if not st.session_state.recuperar:
            with st.form("login"):
                u = st.text_input("Usuario", placeholder="Ej: tesorero, donaciones...")
                p = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Entrar"):
                    if u in USUARIOS and USUARIOS[u]["clave"] == p:
                        st.session_state.sesion = USUARIOS[u]["rol"]; st.rerun()
                    else: st.error("Clave incorrecta")
            if st.button("Olvidé mi contraseña"): st.session_state.recuperar = True; st.rerun()
        else:
            preg = st.text_input("Seguridad: ¿Nombre de la congregación?", placeholder="Escribe el nombre de la iglesia")
            if st.button("Revelar Claves"):
                if preg.lower() == "cristo el salvador":
                    for k, v in USUARIOS.items(): st.code(f"{k}: {v['clave']}")
                else: st.error("Incorrecto")
            if st.button("Volver"): st.session_state.recuperar = False; st.rerun()
    st.stop()

# --- PANEL PRINCIPAL ---
rol = st.session_state.sesion
if st.sidebar.button("🚪 Cerrar Sesión"): st.session_state.sesion = None; st.rerun()

st.title(f"⛪ Gestión - {rol.upper()}")
pestanas = []
if rol in ["finanzas", "todos"]: 
    pestanas.extend(["💰 Diezmos/Ofrendas", "📊 Informe Tesorería"])
if rol in ["materiales", "todos"]: 
    pestanas.extend(["📦 Registro Materiales", "📋 Informe Donaciones"])
if rol in ["asistencia", "todos"]: 
    pestanas.extend(["👥 Asistencia", "📝 Informe Secretaría"])
if rol == "todos": 
    pestanas.extend(["📡 CONSOLIDADOR PASTORAL", "🛠️ Ajustes"])

tabs = st.tabs(pestanas)
idx = 0

# --- LÓGICA DE SECCIONES ---

# FINANZAS
if rol in ["finanzas", "todos"]:
    with tabs[idx]:
        st.subheader("Registro de Ingresos")
        tasa = obtener_tasa_bcv()
        with st.form("f_fin", clear_on_submit=True):
            n = st.text_input("Nombre del Hermano", placeholder="Quién aporta")
            r = st.text_input("Referencia", placeholder="Ej: Pago Móvil / Referencia Bancaria")
            m = st.number_input("Monto en VES", min_value=0.0)
            if st.form_submit_button("Guardar"):
                curr.execute("INSERT INTO finanzas (nombre, referencia, monto_ves, tasa, monto_usd, fecha) VALUES (?,?,?,?,?,?)", (n, r, m, tasa, m/tasa, date.today()))
                conn.commit(); st.success("Registrado")
    idx += 1
    with tabs[idx]:
        st.subheader("Informe de Tesorería")
        st.dataframe(pd.read_sql_query("SELECT * FROM finanzas", conn))
    idx += 1

# MATERIALES (Ahora con Informe)
if rol in ["materiales", "todos"]:
    with tabs[idx]:
        st.subheader("Registro de Donaciones")
        with st.form("f_mat", clear_on_submit=True):
            d = st.text_input("Donante", placeholder="Nombre de quien dona")
            c = st.selectbox("Categoría", ["Alimentos", "Medicinas", "Limpieza", "Otros"])
            desc = st.text_area("Descripción", placeholder="Detalle de lo entregado")
            if st.form_submit_button("Registrar"):
                curr.execute("INSERT INTO materiales (donante, categoria, descripcion, fecha) VALUES (?,?,?,?)", (d, c, desc, date.today()))
                conn.commit(); st.success("Donación guardada")
    idx += 1
    with tabs[idx]:
        st.subheader("📋 Informe de Donaciones e Insumos")
        st.dataframe(pd.read_sql_query("SELECT * FROM materiales", conn))
    idx += 1

# ASISTENCIA
if rol in ["asistencia", "todos"]:
    with tabs[idx]:
        st.subheader("Registro de Asistencia")
        with st.form("f_asis", clear_on_submit=True):
            na = st.text_input("Nombre Completo", placeholder="Escriba el nombre")
            te = st.text_input("WhatsApp", placeholder="Ej: 584120000000")
            if st.form_submit_button("Marcar"):
                curr.execute("INSERT INTO asistencia (nombre, telefono, fecha) VALUES (?,?,?)", (na, te, date.today()))
                conn.commit(); st.success("Asistencia marcada")
    idx += 1
    with tabs[idx]:
        st.subheader("Informe de Secretaría")
        st.dataframe(pd.read_sql_query("SELECT * FROM asistencia", conn))
    idx += 1

# PASTOR (ADMIN)
if rol == "todos":
    with tabs[idx]:
        st.header("📡 CONSOLIDADOR PASTORAL")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_usd = pd.read_sql_query("SELECT SUM(monto_usd) as t FROM finanzas", conn)['t'][0] or 0
            st.metric("Total Tesorería", f"{total_usd:.2f} USD")
        with col2:
            total_mat = pd.read_sql_query("SELECT COUNT(*) as t FROM materiales", conn)['t'][0]
            st.metric("Donaciones Recibidas", total_mat)
        with col3:
            total_asis = pd.read_sql_query("SELECT COUNT(*) as t FROM asistencia", conn)['t'][0]
            st.metric("Total Asistencias", total_asis)
        
        st.write("---")
        st.subheader("Resumen de Fieles (WhatsApp)")
        h30 = (date.today() - timedelta(days=30)).isoformat()
        df_f = pd.read_sql_query(f"SELECT nombre, telefono, COUNT(*) as t FROM asistencia WHERE fecha >= '{h30}' GROUP BY nombre HAVING t >= 4", conn)
        for i, r in df_f.iterrows():
            msg = urllib.parse.quote(f"Bendiciones {r['nombre']}, gracias por su fidelidad. 🙌")
            st.link_button(f"Felicitar a {r['nombre']}", f"https://wa.me/{r['telefono']}?text={msg}")
    idx += 1
    with tabs[idx]:
        st.subheader("Ajustes")
        t_el = st.selectbox("Tabla", ["finanzas", "materiales", "asistencia"])
        st.dataframe(pd.read_sql_query(f"SELECT * FROM {t_el}", conn))
        id_b = st.number_input("ID a eliminar", min_value=0)
        if st.button("Eliminar"):
            curr.execute(f"DELETE FROM {t_el} WHERE id=?", (id_b,))
            conn.commit(); st.rerun()

