import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import base64
import requests
import urllib.parse

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Iglesia Cristo El Salvador", page_icon="⛪", layout="wide")

# 2. FUNCIÓN API TASA BCV (ACTUALIZADA)
def obtener_tasa_bcv():
    try:
        url = "https://ve.dolarapi.com/v1/dolares/oficial"
        response = requests.get(url, timeout=10)
        return float(response.json()['promedio'])
    except:
        return 50.0

# 3. FUNCIÓN PARA EL FONDO PERSONALIZADO
def agregar_fondo(nombre_archivo):
    try:
        with open(nombre_archivo, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpg;base64,{encoded_string}");
                background-size: cover; background-position: center; background-attachment: fixed;
            }}
            [data-testid="stForm"], .stTabs, .stMetric, div.stAlert, .stDataFrame, .stTable {{
                background-color: rgba(255, 255, 255, 0.96) !important;
                padding: 20px !important; border-radius: 15px !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }}
            h1, h2, h3 {{ color: #1a1a1a !important; text-shadow: 1px 1px 2px white; }}
            </style>
            """, unsafe_allow_html=True)
    except:
        pass

# Llamada al fondo (Asegúrate que el nombre coincida en GitHub)
agregar_fondo('1000687124.jpg')

# 4. BASE DE DATOS (ESTRUCTURA COMPLETA)
conn = sqlite3.connect('iglesia_pascua_web.db', check_same_thread=False)
curr = conn.cursor()
curr.execute("""CREATE TABLE IF NOT EXISTS finanzas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, referencia TEXT, monto_ves REAL, tasa REAL, monto_usd REAL, fecha DATE)""")
curr.execute("CREATE TABLE IF NOT EXISTS materiales (id INTEGER PRIMARY KEY AUTOINCREMENT, donante TEXT, categoria TEXT, descripcion TEXT, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono TEXT, fecha DATE)")
conn.commit()

# 5. CONFIGURACIÓN DE USUARIOS Y ROLES
USUARIOS = {
    "tesorero": {"clave": "finanzas2026", "rol": "finanzas"},
    "secretario": {"clave": "iglesia2026", "rol": "asistencia"},
    "donaciones": {"clave": "pascua2026", "rol": "materiales"},
    "admin": {"clave": "pastor2026", "rol": "todos"}
}

if "sesion" not in st.session_state: st.session_state.sesion = None
if "recuperar" not in st.session_state: st.session_state.recuperar = False

# --- LÓGICA DE LOGIN Y RECUPERACIÓN ---
if st.session_state.sesion is None:
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso al Sistema</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    
    with col_l2:
        if not st.session_state.recuperar:
            with st.form("login_form"):
                u_log = st.text_input("Usuario")
                p_log = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Entrar"):
                    if u_log in USUARIOS and USUARIOS[u_log]["clave"] == p_log:
                        st.session_state.sesion = USUARIOS[u_log]["rol"]
                        st.rerun()
                    else: st.error("Usuario o clave incorrectos")
            if st.button("Olvidé mi contraseña"):
                st.session_state.recuperar = True
                st.rerun()
        else:
            st.write("### 🛠️ Recuperación de Clave")
            preg = st.text_input("Pregunta de seguridad: ¿Cuál es el nombre de la congregación?")
            if st.button("Ver Claves"):
                if preg.lower() == "cristo el salvador":
                    for user, info in USUARIOS.items():
                        st.code(f"Usuario: {user} | Clave: {info['clave']}")
                else: st.error("Respuesta incorrecta")
            if st.button("Volver"):
                st.session_state.recuperar = False
                st.rerun()
    st.stop()

# --- PANEL PRINCIPAL ---
rol = st.session_state.sesion
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.sesion = None
    st.rerun()

st.title(f"⛪ Panel de Gestión - {rol.upper()}")
pestanas_visibles = []
if rol in ["finanzas", "todos"]: pestanas_visibles.append("💰 Diezmos/Ofrendas")
if rol in ["materiales", "todos"]: pestanas_visibles.append("📦 Materiales")
if rol in ["asistencia", "todos"]: pestanas_visibles.append("👥 Asistencia")
if rol == "todos": 
    pestanas_visibles.append("📡 Seguimiento")
    pestanas_visibles.append("🛠️ Ajustes")

tabs = st.tabs(pestanas_visibles)
idx = 0

# --- 1. SECCIÓN FINANZAS ---
if rol in ["finanzas", "todos"]:
    with tabs[idx]:
        st.subheader("Registro de Finanzas")
        tasa_val = obtener_tasa_bcv()
        with st.form("f_din", clear_on_submit=True):
            n_f = st.text_input("Nombre del Hermano/a")
            r_f = st.text_input("Referencia (Banco / Concepto)")
            c1, c2 = st.columns(2)
            mv_f = c1.number_input("Monto VES", min_value=0.0)
            ts_f = c2.number_input("Tasa Aplicada", value=tasa_val)
            if st.form_submit_button("💾 Guardar"):
                if n_f and mv_f > 0:
                    curr.execute("INSERT INTO finanzas (nombre, referencia, monto_ves, tasa, monto_usd, fecha) VALUES (?,?,?,?,?,?)", 
                                 (n_f, r_f, mv_f, ts_f, mv_f/ts_f, date.today()))
                    conn.commit(); st.success("Registrado correctamente")
    idx += 1

# --- 2. SECCIÓN MATERIALES ---
if rol in ["materiales", "todos"]:
    with tabs[idx]:
        st.subheader("Donaciones de Materiales")
        with st.form("f_mat", clear_on_submit=True):
            don_m = st.text_input("Donante")
            cat_m = st.selectbox("Categoría", ["Alimentos", "Medicinas", "Construcción", "Limpieza", "Otros"])
            desc_m = st.text_area("Descripción")
            if st.form_submit_button("💾 Registrar"):
                curr.execute("INSERT INTO materiales (donante, categoria, descripcion, fecha) VALUES (?,?,?,?)", (don_m, cat_m, desc_m, date.today()))
                conn.commit(); st.success("Donación guardada")
    idx += 1

# --- 3. SECCIÓN ASISTENCIA ---
if rol in ["asistencia", "todos"]:
    with tabs[idx]:
        st.subheader("Control de Asistencia")
        with st.form("f_asis", clear_on_submit=True):
            nom_a = st.text_input("Nombre Completo")
            tel_a = st.text_input("WhatsApp (Ej: 584120000000)")
            if st.form_submit_button("✅ Marcar"):
                if nom_a:
                    curr.execute("INSERT INTO asistencia (nombre, telefono, fecha) VALUES (?,?,?)", (nom_a, tel_a, date.today()))
                    conn.commit(); st.success("Asistencia registrada")
    idx += 1

# --- 4. SECCIÓN SEGUIMIENTO PASTORAL (WHATSAPP) ---
if rol == "todos":
    with tabs[idx]:
        st.header("📡 Seguimiento Mensual WhatsApp")
        hace_30 = (date.today() - timedelta(days=30)).isoformat()
        col_f, col_a = st.columns(2)
        with col_f:
            st.subheader("🌟 Fidelidad (Ininterrumpida)")
            df_f = pd.read_sql_query(f"SELECT nombre, telefono, COUNT(*) as t FROM asistencia WHERE fecha >= '{hace_30}' GROUP BY nombre HAVING t >= 4", conn)
            for i, r in df_f.iterrows():
                msg = urllib.parse.quote(f"¡Bendiciones {r['nombre']}! Le felicitamos por su constancia ininterrumpida este mes. 🙌")
                st.info(f"✅ {r['nombre']}")
                st.link_button(f"Felicitar", f"https://wa.me/{r['telefono']}?text={msg}")
        with col_a:
            st.subheader("📉 Ausentes (Más de 1 mes)")
            df_a = pd.read_sql_query(f"SELECT nombre, telefono, MAX(fecha) as u FROM asistencia GROUP BY nombre HAVING u < '{hace_30}'", conn)
            for i, r in df_a.iterrows():
                msg = urllib.parse.quote(f"Hola {r['nombre']}, le extrañamos este último mes en la congregación. ¡Dios le bendiga! 🙏")
                st.warning(f"⚠️ {r['nombre']}")
                st.link_button(f"Enviar Ánimo", f"https://wa.me/{r['telefono']}?text={msg}")
    idx += 1

# --- 5. SECCIÓN AJUSTES ---
if rol == "todos":
    with tabs[idx]:
        st.subheader("🛠️ Administración de Datos")
        tab_v = st.selectbox("Seleccionar Tabla", ["finanzas", "materiales", "asistencia"])
        df_ver = pd.read_sql_query(f"SELECT * FROM {tab_v} ORDER BY id DESC", conn)
        st.dataframe(df_ver)
        id_b = st.number_input("ID para borrar", min_value=0)
        if st.button("🗑️ Eliminar"):
            curr.execute(f"DELETE FROM {tab_v} WHERE id=?", (id_b,))
            conn.commit(); st.rerun()

