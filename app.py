import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import urllib.parse
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Iglesia Cristo El Salvador", page_icon="⛪", layout="wide")

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
    except FileNotFoundError:
        st.warning("⚠️ No se encontró el archivo de imagen. Asegúrate de que se llame '1000687124.jpg'.")

# Aplicamos el fondo
agregar_fondo('1000687124.jpg')

# --- CONEXIÓN A BASE DE DATOS ---
@st.cache_resource
def conectar_db():
    conn = sqlite3.connect('iglesia_pascua_web.db', check_same_thread=False)
    return conn

conn = conectar_db()
curr = conn.cursor()

# Inicialización de tablas
curr.execute("CREATE TABLE IF NOT EXISTS finanzas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, monto_ves REAL, tasa REAL, monto_usd REAL, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS materiales (id INTEGER PRIMARY KEY AUTOINCREMENT, donante TEXT, categoria TEXT, descripcion TEXT, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono TEXT, fecha DATE)")
conn.commit()

# --- SISTEMA DE LOGIN ---
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
                if user == "admin" and pw == "pascua2026": # Puedes cambiar tu clave aquí
                    st.session_state.logueado = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
    st.stop()

# --- PANEL PRINCIPAL ---
st.title("⛪ Gestión Administrativa")
tabs = st.tabs(["💰 Finanzas", "📦 Materiales", "👥 Asistencia", "📊 Reportes y Gestión"])

# --- PESTAÑA 1: FINANZAS ---
with tabs[0]:
    st.subheader("Registro de Diezmos y Ofrendas")
    with st.form("f_dinero", clear_on_submit=True):
        nombre = st.text_input("Nombre del Hermano/a")
        c1, c2 = st.columns(2)
        m_ves = c1.number_input("Monto en VES", min_value=0.0)
        tasa = c2.number_input("Tasa BCV", value=50.0)
        if st.form_submit_button("💾 Guardar Aporte"):
            if nombre and m_ves > 0:
                m_usd = m_ves / tasa
                curr.execute("INSERT INTO finanzas (nombre, monto_ves, tasa, monto_usd, fecha) VALUES (?,?,?,?,?)", 
                             (nombre, m_ves, tasa, m_usd, date.today()))
                conn.commit()
                st.success(f"¡Registrado! Total: ${m_usd:.2f}")
                st.balloons()

# --- PESTAÑA 2: MATERIALES ---
with tabs[1]:
    st.subheader("Donaciones de Objetos/Insumos")
    with st.form("f_material", clear_on_submit=True):
        donante = st.text_input("Nombre del Donante")
        cat = st.selectbox("Categoría", ["Cocina", "Medicina", "Decoración", "Jóvenes", "Otros"])
        desc = st.text_area("Descripción de lo donado")
        if st.form_submit_button("💾 Registrar Material"):
            curr.execute("INSERT INTO materiales (donante, categoria, descripcion, fecha) VALUES (?,?,?,?)", 
                         (donante, cat, desc, date.today()))
            conn.commit()
            st.success("Donación registrada exitosamente.")

# --- PESTAÑA 3: ASISTENCIA ---
with tabs[2]:
    st.subheader("Paso de Asistencia")
    with st.form("f_asistencia", clear_on_submit=True):
        nom_asis = st.text_input("Nombre Completo")
        tel_asis = st.text_input("WhatsApp (ej: 584121234567)")
        if st.form_submit_button("✅ Registrar Entrada"):
            curr.execute("INSERT INTO asistencia (nombre, telefono, fecha) VALUES (?,?,?)", 
                         (nom_asis, tel_asis, date.today()))
            conn.commit()
            st.success(f"¡Bienvenido/a {nom_asis}!")

# --- PESTAÑA 4: REPORTES Y GESTIÓN ---
with tabs[3]:
    st.subheader(f"Resumen del día: {date.today()}")
    
    # Reporte de Dinero
    df_f = pd.read_sql_query(f"SELECT * FROM finanzas WHERE fecha = '{date.today()}'", conn)
    if not df_f.empty:
        st.write("💵 **Aportes Económicos**")
        st.dataframe(df_f[['nombre', 'monto_ves', 'monto_usd']])
        total_usd = df_f['monto_usd'].sum()
        st.metric("Total Recaudado", f"${total_usd:.2f}")
    
    # Reporte de Asistencia Mensual y Felicitaciones
    st.divider()
    st.write("🏆 **Fidelidad y Asistencia (Mes Actual)**")
    mes = date.today().strftime('%m')
    df_m = pd.read_sql_query(f"SELECT nombre, telefono, COUNT(*) as total FROM asistencia WHERE strftime('%m', fecha) = '{mes}' GROUP BY nombre", conn)
    
    if not df_m.empty:
        max_asist = df_m['total'].max()
        constantes = df_m[df_m['total'] == max_asist]
        for _, row in constantes.iterrows():
            col_a, col_b = st.columns([0.7, 0.3])
            col_a.write(f"🌟 **{row['nombre']}** ({row['total']} asistencias)")
            
            # Mensaje bonito de felicitación
            txt = f"⛪ *IGLESIA CRISTO EL SALVADOR*\n¡Felicidades *{row['nombre']}*! Has tenido asistencia perfecta este mes. ¡Dios te bendiga! 🙌"
            url = f"https://wa.me/{row['telefono']}?text={urllib.parse.quote(txt)}"
            col_b.link_button("🎁 Felicitar", url)

    # Botón para borrar errores del día
    st.divider()
    if st.button("🗑️ Limpiar registros de hoy (CUIDADO)"):
        curr.execute(f"DELETE FROM finanzas WHERE fecha = '{date.today()}'")
        curr.execute(f"DELETE FROM materiales WHERE fecha = '{date.today()}'")
        curr.execute(f"DELETE FROM asistencia WHERE fecha = '{date.today()}'")
        conn.commit()
        st.warning("Registros de hoy eliminados.")
        st.rerun()

conn.close()

