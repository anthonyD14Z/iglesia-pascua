import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import urllib.parse
import base64
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Iglesia Cristo El Salvador", page_icon="⛪", layout="wide")

# --- FUNCIÓN PARA LA TASA AUTOMÁTICA ---
def obtener_tasa_bcv():
    try:
        url = "https://pydolarve.org/api/v1/engine?currency=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        tasa = data['monitors']['bcv']['price']
        return float(tasa)
    except Exception:
        return 45.0

# --- FUNCIÓN PARA EL FONDO ---
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
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except:
        pass

# Aplicamos fondo (Asegúrate de que el nombre sea exacto)
agregar_fondo('1000687124.jpg')

# --- BASE DE DATOS ---
conn = sqlite3.connect('iglesia_pascua_web.db', check_same_thread=False)
curr = conn.cursor()
curr.execute("CREATE TABLE IF NOT EXISTS finanzas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, monto_ves REAL, tasa REAL, monto_usd REAL, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS materiales (id INTEGER PRIMARY KEY AUTOINCREMENT, donante TEXT, categoria TEXT, descripcion TEXT, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono TEXT, fecha DATE)")
conn.commit()

# --- LOGIN ---
if "logueado" not in st.session_state:
    st.session_state.logueado = False

if not st.session_state.logueado:
    st.title("Iglesia Cristo El Salvador")
    with st.form("login"):
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("Entrar"):
            if u == "admin" and p == "pascua2026":
                st.session_state.logueado = True
                st.rerun()
    st.stop()

# --- APP PRINCIPAL ---
st.title("⛪ Panel de Control")
t1, t2, t3 = st.tabs(["💰 Finanzas", "👥 Asistencia", "📊 Reportes"])

with t1:
    if 'tasa' not in st.session_state:
        st.session_state.tasa = obtener_tasa_bcv()
    
    with st.form("f1", clear_on_submit=True):
        nom = st.text_input("Hermano/a")
        m = st.number_input("Bolívares", min_value=0.0)
        ts = st.number_input("Tasa BCV", value=st.session_state.tasa)
        if st.form_submit_button("Guardar"):
            usd = m / ts
            curr.execute("INSERT INTO finanzas (nombre, monto_ves, tasa, monto_usd, fecha) VALUES (?,?,?,?,?)", (nom, m, ts, usd, date.today()))
            conn.commit()
            st.success(f"Registrado: ${usd:.2f}")

with t2:
    with st.form("f2", clear_on_submit=True):
        n = st.text_input("Nombre")
        tel = st.text_input("WhatsApp")
        if st.form_submit_button("Registrar Asistencia"):
            curr.execute("INSERT INTO asistencia (nombre, telefono, fecha) VALUES (?,?,?)", (n, tel, date.today()))
            conn.commit()
            st.success("¡Bienvenido!")



