import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime
import urllib.parse
import base64
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Iglesia Cristo El Salvador", page_icon="⛪", layout="wide")

# --- FUNCIÓN PARA LA TASA AUTOMÁTICA (API) ---
def obtener_tasa_bcv():
    try:
        # Consultamos una API que provee la tasa oficial del BCV
        url = "https://pydolarve.org/api/v1/engine?currency=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        # Extraemos el valor del BCV
        tasa = data['monitors']['bcv']['price']
        return float(tasa)
    except Exception:
        # Si la API falla, devolvemos un valor base para no detener la app
        return 45.0

# --- FUNCIÓN PARA EL FONDO PERSONALIZADO ---
def agregar_fondo(nombre_archivo):
    try:
        with open(nombre_archivo, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpg;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            [data-testid="stForm"], .stTabs, .stMetric, div.stAlert, .stDataFrame {{
                background-color: rgba(255, 255, 255, 0.92) !important;
                padding: 20px !important;
                border-radius: 15px !important;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            }}
            h1, h2, h3 {{ color: #1a1a1a !important; text-shadow: 1px 1px 2px white; }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except Exception:
        st.warning("⚠️ No se encontró la imagen de fondo.")

# Aplicamos fondo
agregar_fondo('1000687124.jpg')

# --- CONEXIÓN A BASE DE DATOS ---
@st.cache_resource
def conectar_db():
    conn = sqlite3.connect('iglesia_pascua_web.db', check_same_thread=False)
    return conn

conn = conectar_db()
curr = conn.cursor()
curr.execute("CREATE TABLE IF NOT EXISTS finanzas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, monto_ves REAL, tasa REAL, monto_usd REAL, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS materiales (id INTEGER PRIMARY KEY AUTOINCREMENT, donante TEXT, categoria TEXT, descripcion TEXT, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono TEXT, fecha DATE)")
conn.commit()

# --- LÓGICA DE LOGIN ---
if "logueado" not in st.session_state:
    st.session_state.logueado = False

if not st.session_state.logueado:
    st.markdown("<h1 style='text-align: center;'>Iglesia Cristo El Salvador</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Llamados a ser Diferentes</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login"):
            st.write("### 🔐 Acceso Administrativo")
            user = st.text_input("Usuario")
            pw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                if user == "admin" and pw == "pascua2026":
                    st.session_state.logueado = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
    st.stop()

# --- PANEL PRINCIPAL ---
st.title("⛪ Gestión Administrativa")
tabs = st.tabs(["💰 Finanzas", "📦 Materiales", "👥 Asistencia", "📊 Reportes"])

# PESTAÑA 1: FINANZAS CON TASA AUTO
with tabs[0]:
    st.subheader("Registro de Diezmos y Ofrendas")
    
    # Obtener tasa solo una vez por sesión para no saturar la API
    if 'tasa_bcv' not in st.session_state:
        with st.spinner('Consultando tasa oficial del BCV...'):
            st.session_state.tasa_bcv = obtener_tasa_bcv()

    with st.form("f_dinero", clear_on_submit=True):
        nombre = st.text_input("Nombre del Hermano/a")
        c1, c2 = st.columns(2)
        m_ves = c1.number_input("Monto en VES", min_value=0.0)
        # Se llena automáticamente con lo que trajo la API
        tasa_oficial = c2.number_input("Tasa BCV (Actualizada)", value=st.session_state.tasa_bcv)
        
        if st.form_submit_button("💾 Guardar Aporte"):
            if nombre and m_ves > 0:
                m_usd = m_ves / tasa_oficial
                curr.execute("INSERT INTO finanzas (nombre, monto_ves, tasa, monto_usd, fecha) VALUES (?,?,?,?,?)", 
                             (nombre, m_ves, tasa_oficial, m_usd, date.today()))
                conn.commit()
                st.success(f"¡Guardado! Monto: ${m_usd:.2f}")

# PESTAÑA 2: MATERIALES
with tabs[1]:
    st.subheader("Donaciones de Materiales")
    with st.form("f_material", clear_on_submit=True):
        donante = st.text_input("Donante")
        cat = st.selectbox("Categoría", ["Cocina", "Medicina", "Limpieza", "Otros"])
        desc = st.text_area("Descripción")
        if st.form_submit_button("💾 Guardar Material"):
            curr.execute("INSERT INTO materiales (donante, categoria, descripcion, fecha) VALUES (?,?,?,?)", 
                         (donante, cat, desc, date.today()))
            conn.commit()
            st.success("Registrado correctamente")

# PESTAÑA 3: ASISTENCIA
with tabs[2]:
    st.subheader("Control de Asistencia")
    with st.form("f_asistencia", clear_on_submit=True):
        nom_asis = st.text_input("Nombre")
        tel_asis = st.text_input("WhatsApp (ej: 58412...)")
        if st.form_submit_button("✅ Registrar"):
            curr.execute("INSERT INTO asistencia (nombre, telefono, fecha) VALUES (?,?,?)", 
                         (nom_asis, tel_asis, date.today()))
            conn.commit()
            st.success(f"Asistencia marcada para {nom_asis}")

# PESTAÑA 4: REPORTES
with tabs[3]:
    st.subheader("Resumen General")
    df_hoy = pd.read_sql_query(f"SELECT * FROM finanzas WHERE fecha = '{date.today()}'", conn)
    if not df_hoy.empty:
        st.write("💰 Dinero hoy:")
        st.table(df_hoy[['nombre', 'monto_usd']])
        st.metric("Total USD", f"${df_hoy['monto_usd'].sum():.2f}")


---------- Forwarded message ---------
De: anthony daniel diaz <anthonydanieldiaz.15@gmail.com>
Date: dom, 12 de abr de 2026, 3:38 p. m.
Subject:
To: anthony daniel diaz <anthonydanieldiaz.15@gmail.com>


import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime
import urllib.parse
import base64
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Iglesia Cristo El Salvador", page_icon="⛪", layout="wide")

# --- FUNCIÓN PARA LA TASA AUTOMÁTICA (API) ---
def obtener_tasa_bcv():
    try:
        # Consultamos una API que provee la tasa oficial del BCV
        url = "https://pydolarve.org/api/v1/engine?currency=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        # Extraemos el valor del BCV
        tasa = data['monitors']['bcv']['price']
        return float(tasa)
    except Exception:
        # Si la API falla, devolvemos un valor base para no detener la app
        return 45.0

# --- FUNCIÓN PARA EL FONDO PERSONALIZADO ---
def agregar_fondo(nombre_archivo):
    try:
        with open(nombre_archivo, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpg;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            [data-testid="stForm"], .stTabs, .stMetric, div.stAlert, .stDataFrame {{
                background-color: rgba(255, 255, 255, 0.92) !important;
                padding: 20px !important;
                border-radius: 15px !important;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            }}
            h1, h2, h3 {{ color: #1a1a1a !important; text-shadow: 1px 1px 2px white; }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except Exception:
        st.warning("⚠️ No se encontró la imagen de fondo.")

# Aplicamos fondo
agregar_fondo('1000687124.jpg')

# --- CONEXIÓN A BASE DE DATOS ---
@st.cache_resource
def conectar_db():
    conn = sqlite3.connect('iglesia_pascua_web.db', check_same_thread=False)
    return conn

conn = conectar_db()
curr = conn.cursor()
curr.execute("CREATE TABLE IF NOT EXISTS finanzas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, monto_ves REAL, tasa REAL, monto_usd REAL, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS materiales (id INTEGER PRIMARY KEY AUTOINCREMENT, donante TEXT, categoria TEXT, descripcion TEXT, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono TEXT, fecha DATE)")
conn.commit()

# --- LÓGICA DE LOGIN ---
if "logueado" not in st.session_state:
    st.session_state.logueado = False

if not st.session_state.logueado:
    st.markdown("<h1 style='text-align: center;'>Iglesia Cristo El Salvador</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Llamados a ser Diferentes</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login"):
            st.write("### 🔐 Acceso Administrativo")
            user = st.text_input("Usuario")
            pw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                if user == "admin" and pw == "pascua2026":
                    st.session_state.logueado = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
    st.stop()

# --- PANEL PRINCIPAL ---
st.title("⛪ Gestión Administrativa")
tabs = st.tabs(["💰 Finanzas", "📦 Materiales", "👥 Asistencia", "📊 Reportes"])

# PESTAÑA 1: FINANZAS CON TASA AUTO
with tabs[0]:
    st.subheader("Registro de Diezmos y Ofrendas")
    
    # Obtener tasa solo una vez por sesión para no saturar la API
    if 'tasa_bcv' not in st.session_state:
        with st.spinner('Consultando tasa oficial del BCV...'):
            st.session_state.tasa_bcv = obtener_tasa_bcv()

    with st.form("f_dinero", clear_on_submit=True):
        nombre = st.text_input("Nombre del Hermano/a")
        c1, c2 = st.columns(2)
        m_ves = c1.number_input("Monto en VES", min_value=0.0)
        # Se llena automáticamente con lo que trajo la API
        tasa_oficial = c2.number_input("Tasa BCV (Actualizada)", value=st.session_state.tasa_bcv)
        
        if st.form_submit_button("💾 Guardar Aporte"):
            if nombre and m_ves > 0:
                m_usd = m_ves / tasa_oficial
                curr.execute("INSERT INTO finanzas (nombre, monto_ves, tasa, monto_usd, fecha) VALUES (?,?,?,?,?)", 
                             (nombre, m_ves, tasa_oficial, m_usd, date.today()))
                conn.commit()
                st.success(f"¡Guardado! Monto: ${m_usd:.2f}")

# PESTAÑA 2: MATERIALES
with tabs[1]:
    st.subheader("Donaciones de Materiales")
    with st.form("f_material", clear_on_submit=True):
        donante = st.text_input("Donante")
        cat = st.selectbox("Categoría", ["Cocina", "Medicina", "Limpieza", "Otros"])
        desc = st.text_area("Descripción")
        if st.form_submit_button("💾 Guardar Material"):
            curr.execute("INSERT INTO materiales (donante, categoria, descripcion, fecha) VALUES (?,?,?,?)", 
                         (donante, cat, desc, date.today()))
            conn.commit()
            st.success("Registrado correctamente")

# PESTAÑA 3: ASISTENCIA
with tabs[2]:
    st.subheader("Control de Asistencia")
    with st.form("f_asistencia", clear_on_submit=True):
        nom_asis = st.text_input("Nombre")
        tel_asis = st.text_input("WhatsApp (ej: 58412...)")
        if st.form_submit_button("✅ Registrar"):
            curr.execute("INSERT INTO asistencia (nombre, telefono, fecha) VALUES (?,?,?)", 
                         (nom_asis, tel_asis, date.today()))
            conn.commit()
            st.success(f"Asistencia marcada para {nom_asis}")

# PESTAÑA 4: REPORTES
with tabs[3]:
    st.subheader("Resumen General")
    df_hoy = pd.read_sql_query(f"SELECT * FROM finanzas WHERE fecha = '{date.today()}'", conn)
    if not df_hoy.empty:
        st.write("💰 Dinero hoy:")
        st.table(df_hoy[['nombre', 'monto_usd']])
        st.metric("Total USD", f"${df_hoy['monto_usd'].sum():.2f}")
()

