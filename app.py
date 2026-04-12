import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import base64
import requests
import urllib.parse

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Iglesia Cristo El Salvador", page_icon="⛪", layout="wide")

# 2. API DE TASA AUTOMÁTICA (BCV)
def obtener_tasa_bcv():
    try:
        # Usamos una API confiable para la tasa oficial en Venezuela
        url = "https://ve.dolarapi.com/v1/dolares/oficial"
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data['promedio'])
    except:
        return 50.0  # Valor manual de respaldo si la API falla

# 3. FUNCIÓN PARA EL FONDO PERSONALIZADO
def agregar_fondo(nombre_archivo):
    try:
        with open(nombre_archivo, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpg;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            [data-testid="stForm"], .stTabs, .stMetric, div.stAlert, .stDataFrame, .stTable {{
                background-color: rgba(255, 255, 255, 0.94) !important;
                padding: 20px !important;
                border-radius: 15px !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }}
            h1, h2, h3 {{ color: #1a1a1a !important; text-shadow: 1px 1px 2px white; }}
            </style>
            """, unsafe_allow_html=True)
    except:
        pass

# Aplicar fondo
agregar_fondo('1000687124.jpg')

# 4. BASE DE DATOS
conn = sqlite3.connect('iglesia_pascua_web.db', check_same_thread=False)
curr = conn.cursor()
curr.execute("CREATE TABLE IF NOT EXISTS finanzas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, monto_ves REAL, tasa REAL, monto_usd REAL, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS materiales (id INTEGER PRIMARY KEY AUTOINCREMENT, donante TEXT, categoria TEXT, descripcion TEXT, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono TEXT, fecha DATE)")
conn.commit()

# 5. SISTEMA DE LOGIN
if "logueado" not in st.session_state:
    st.session_state.logueado = False

if not st.session_state.logueado:
    st.markdown("<h1 style='text-align: center;'>Iglesia Cristo El Salvador</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login"):
            st.write("### 🔐 Acceso al Sistema")
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                if u == "admin" and p == "pascua2026":
                    st.session_state.logueado = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
    st.stop()

# 6. PANEL PRINCIPAL (TODAS LAS PESTAÑAS)
st.title("⛪ Panel de Gestión Integral")
t1, t2, t3, t4, t5 = st.tabs(["💰 Finanzas", "📦 Materiales/Donaciones", "👥 Asistencia", "📡 Seguimiento Pastoral", "🛠️ Ajustes"])

# --- PESTAÑA 1: FINANZAS CON API ---
with t1:
    if 'tasa_dia' not in st.session_state:
        st.session_state.tasa_dia = obtener_tasa_bcv()
    
    st.subheader(f"Registro Económico - Tasa BCV Hoy: {st.session_state.tasa_dia} VES")
    with st.form("f_dinero", clear_on_submit=True):
        nombre_f = st.text_input("Nombre del Hermano/a")
        col_a, col_b = st.columns(2)
        m_ves = col_a.number_input("Monto en VES", min_value=0.0)
        tasa_f = col_b.number_input("Confirmar Tasa", value=st.session_state.tasa_dia)
        if st.form_submit_button("💾 Guardar"):
            if nombre_f and m_ves > 0:
                m_usd = m_ves / tasa_f
                curr.execute("INSERT INTO finanzas (nombre, monto_ves, tasa, monto_usd, fecha) VALUES (?,?,?,?,?)", 
                             (nombre_f, m_ves, tasa_f, m_usd, date.today()))
                conn.commit()
                st.success(f"Guardado: ${m_usd:.2f}")

# --- PESTAÑA 2: MATERIALES (DONACIONES) ---
with t2:
    st.subheader("Registro de Donaciones de Materiales")
    with st.form("f_mate", clear_on_submit=True):
        donante = st.text_input("Nombre del Donante")
        tipo = st.selectbox("Categoría", ["Medicinas", "Alimentos", "Limpieza", "Construcción", "Otros"])
        detalle = st.text_area("Descripción de lo donado")
        if st.form_submit_button("💾 Registrar Donación"):
            curr.execute("INSERT INTO materiales (donante, categoria, descripcion, fecha) VALUES (?,?,?,?)", 
                         (donante, tipo, detalle, date.today()))
            conn.commit()
            st.success("Donación guardada correctamente.")

# --- PESTAÑA 3: ASISTENCIA ---
with t3:
    st.subheader("Control de Asistencia")
    col1, col2 = st.columns([1, 1.2])
    with col1:
        with st.form("f_asis", clear_on_submit=True):
            nom_a = st.text_input("Nombre Completo")
            tel_a = st.text_input("WhatsApp (Ej: 584120000000)")
            if st.form_submit_button("✅ Marcar"):
                if nom_a:
                    curr.execute("INSERT INTO asistencia (nombre, telefono, fecha) VALUES (?,?,?)", (nom_a, tel_a, date.today()))
                    conn.commit()
                    st.success("Registrado")
    with col2:
        st.write("Hermanos hoy:")
        df_h = pd.read_sql_query(f"SELECT nombre FROM asistencia WHERE fecha='{date.today()}'", conn)
        st.table(df_h)

# --- PESTAÑA 4: SEGUIMIENTO PASTORAL ---
with t4:
    st.header("Seguimiento Mensual (WhatsApp)")
    hace_30_dias = (date.today() - timedelta(days=30)).isoformat()
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🌟 Fieles (Mes completo)")
        df_f = pd.read_sql_query(f"SELECT nombre, telefono, COUNT(*) as t FROM asistencia WHERE fecha >= '{hace_30_dias}' GROUP BY nombre HAVING t >= 4", conn)
        for i, r in df_f.iterrows():
            msg = urllib.parse.quote(f"¡Bendiciones {r['nombre']}! Le felicitamos por su constancia ininterrumpida este mes. ¡Gloria a Dios! 🙌")
            st.info(f"✅ {r['nombre']}")
            st.link_button("Felicitar", f"https://wa.me/{r['telefono']}?text={msg}")

    with c2:
        st.subheader("📉 Ausentes (Más de un mes)")
        df_a = pd.read_sql_query(f"SELECT nombre, telefono, MAX(fecha) as u FROM asistencia GROUP BY nombre HAVING u < '{hace_30_dias}'", conn)
        for i, r in df_a.iterrows():
            msg = urllib.parse.quote(f"Hola {r['nombre']}, le extrañamos este último mes. Esperamos verlo pronto. ¡Bendiciones! 🙏")
            st.warning(f"⚠️ {r['nombre']}")
            st.link_button("Animar", f"https://wa.me/{r['telefono']}?text={msg}")

# --- PESTAÑA 5: AJUSTES (EDITAR/BORRAR) ---
with t5:
    st.subheader("🛠️ Corregir Errores")
    tabla = st.selectbox("Tabla", ["finanzas", "materiales", "asistencia"])
    df_ver = pd.read_sql_query(f"SELECT * FROM {tabla} ORDER BY id DESC LIMIT 10", conn)
    st.dataframe(df_ver)
    id_borrar = st.number_input("ID a borrar", min_value=0)
    if st.button("🗑️ Eliminar"):
        curr.execute(f"DELETE FROM {tabla} WHERE id=?", (id_borrar,))
        conn.commit()
        st.rerun()
