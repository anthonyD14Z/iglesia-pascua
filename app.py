import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import base64
import requests
import urllib.parse

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Iglesia Cristo El Salvador", page_icon="⛪", layout="wide")

# 2. FUNCIÓN API TASA BCV
def obtener_tasa_bcv():
    try:
        url = "https://ve.dolarapi.com/v1/dolares/oficial"
        response = requests.get(url, timeout=10)
        return float(response.json()['promedio'])
    except:
        return 50.0  # Valor manual si la API falla

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
            [data-testid="stForm"], .stTabs, .stMetric, div.stAlert, .stDataFrame {{
                background-color: rgba(255, 255, 255, 0.96) !important;
                padding: 20px !important; border-radius: 15px !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }}
            h1, h2, h3 {{ color: #1a1a1a !important; text-shadow: 1px 1px 2px white; }}
            </style>
            """, unsafe_allow_html=True)
    except:
        pass

agregar_fondo('1000687124.jpg')

# 4. BASE DE DATOS
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

if "sesion" not in st.session_state:
    st.session_state.sesion = None

# --- PANTALLA DE LOGIN ---
if st.session_state.sesion is None:
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso al Sistema</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            user_input = st.text_input("Usuario")
            pass_input = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                if user_input in USUARIOS and USUARIOS[user_input]["clave"] == pass_input:
                    st.session_state.sesion = USUARIOS[user_input]["rol"]
                    st.rerun()
                else:
                    st.error("Usuario o clave incorrectos")
    st.stop()

# --- PANEL DE CONTROL SEGÚN ROL ---
rol = st.session_state.sesion
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.sesion = None
    st.rerun()

st.title(f"⛪ Panel de Gestión - {rol.upper()}")

# Definir pestañas permitidas
pestanas_visibles = []
if rol in ["finanzas", "todos"]: pestanas_visibles.append("💰 Diezmos/Ofrendas")
if rol in ["materiales", "todos"]: pestanas_visibles.append("📦 Materiales/Donaciones")
if rol in ["asistencia", "todos"]: pestanas_visibles.append("👥 Asistencia")
if rol == "todos": 
    pestanas_visibles.append("📡 Seguimiento Pastoral")
    pestanas_visibles.append("🛠️ Ajustes de Admin")

tabs = st.tabs(pestanas_visibles)
idx = 0

# --- LÓGICA DE CADA PESTAÑA ---

# 1. FINANZAS
if rol in ["finanzas", "todos"]:
    with tabs[idx]:
        st.subheader("Registro de Finanzas")
        tasa_actual = obtener_tasa_bcv()
        with st.form("f_din", clear_on_submit=True):
            n = st.text_input("Nombre del Hermano/a")
            r = st.text_input("Referencia / Concepto")
            col_a, col_b = st.columns(2)
            mv = col_a.number_input("Monto VES", min_value=0.0)
            ts = col_b.number_input("Tasa Aplicada", value=tasa_actual)
            if st.form_submit_button("💾 Guardar"):
                if n and mv > 0:
                    mu = mv / ts
                    curr.execute("INSERT INTO finanzas (nombre, referencia, monto_ves, tasa, monto_usd, fecha) VALUES (?,?,?,?,?,?)", (n, r, mv, ts, mu, date.today()))
                    conn.commit()
                    st.success(f"Registrado: ${mu:.2f}")
    idx += 1

# 2. MATERIALES
if rol in ["materiales", "todos"]:
    with tabs[idx]:
        st.subheader("Donaciones de Materiales")
        with st.form("f_mat", clear_on_submit=True):
            d = st.text_input("Donante")
            c = st.selectbox("Categoría", ["Alimentos", "Medicinas", "Construcción", "Limpieza", "Otros"])
            desc = st.text_area("Descripción")
            if st.form_submit_button("💾 Registrar"):
                curr.execute("INSERT INTO materiales (donante, categoria, descripcion, fecha) VALUES (?,?,?,?)", (d, c, desc, date.today()))
                conn.commit()
                st.success("Guardado")
    idx += 1

# 3. ASISTENCIA
if rol in ["asistencia", "todos"]:
    with tabs[idx]:
        st.subheader("Control de Asistencia")
        with st.form("f_asis", clear_on_submit=True):
            na = st.text_input("Nombre Completo")
            wa = st.text_input("WhatsApp (Ej: 584120000000)")
            if st.form_submit_button("✅ Marcar"):
                curr.execute("INSERT INTO asistencia (nombre, telefono, fecha) VALUES (?,?,?)", (na, wa, date.today()))
                conn.commit()
                st.success("Asistencia marcada")
    idx += 1

# 4. SEGUIMIENTO (SOLO ADMIN)
if rol == "todos":
    with tabs[idx]:
        st.subheader("📡 Seguimiento Mensual WhatsApp")
        hace_mes = (date.today() - timedelta(days=30)).isoformat()
        col_f, col_a = st.columns(2)
        
        with col_f:
            st.write("🌟 **Fieles Ininterrumpidos**")
            df_f = pd.read_sql_query(f"SELECT nombre, telefono, COUNT(*) as t FROM asistencia WHERE fecha >= '{hace_mes}' GROUP BY nombre HAVING t >= 4", conn)
            for i, row in df_f.iterrows():
                txt = urllib.parse.quote(f"¡Bendiciones {row['nombre']}! Le felicitamos por su constancia este mes. 🙌")
                st.link_button(f"Felicitar a {row['nombre']}", f"https://wa.me/{row['telefono']}?text={txt}")
        
        with col_a:
            st.write("📉 **Ausentes (Más de 1 mes)**")
            df_a = pd.read_sql_query(f"SELECT nombre, telefono, MAX(fecha) as u FROM asistencia GROUP BY nombre HAVING u < '{hace_mes}'", conn)
            for i, row in df_a.iterrows():
                txt = urllib.parse.quote(f"Hola {row['nombre']}, le extrañamos este último mes. 🙏")
                st.link_button(f"Animar a {row['nombre']}", f"https://wa.me/{row['telefono']}?text={txt}")
    idx += 1

# 5. AJUSTES (SOLO ADMIN)
if rol == "todos":
    with tabs[idx]:
        st.subheader("🛠️ Panel Administrativo")
        t_ver = st.selectbox("Tabla a gestionar", ["finanzas", "materiales", "asistencia"])
        df_edit = pd.read_sql_query(f"SELECT * FROM {t_ver} ORDER BY id DESC", conn)
        st.dataframe(df_edit)
        id_borrar = st.number_input("ID para borrar", min_value=0)
        if st.button("🗑️ Eliminar Registro"):
            curr.execute(f"DELETE FROM {t_ver} WHERE id=?", (id_borrar,))
            conn.commit()
            st.rerun()
