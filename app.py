
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import os
import io

# --- 1. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="Iglesia Pascua - Sistema Integral", layout="wide")

# --- 2. CONEXIÓN A BASE DE DATOS ---
conn = sqlite3.connect("iglesia_pascua.db", check_same_thread=False)
curr = conn.cursor()

# Creación de todas las tablas necesarias
curr.execute("CREATE TABLE IF NOT EXISTS miembros (id INTEGER PRIMARY KEY, nombre TEXT, telefono TEXT, direccion TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY, miembro_id INTEGER, fecha TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY, nombre_persona TEXT, tipo TEXT, fecha_evento TEXT, telefono TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS finanzas (id INTEGER PRIMARY KEY, tipo TEXT, categoria TEXT, monto REAL, fecha TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS materiales (id INTEGER PRIMARY KEY, nombre TEXT, cantidad INTEGER, estado TEXT)")
conn.commit()

# --- 3. SISTEMA DE ACCESO (LOGIN) ---
st.sidebar.title("⛪ Acceso Iglesia")
USUARIOS = {
    "asistencia": "1234",
    "tesoreria": "5678",
    "inventario": "9012",
    "todos": "admin"
}

user = st.sidebar.text_input("Usuario")
pw = st.sidebar.text_input("Contraseña", type="password")

if user in USUARIOS and USUARIOS[user] == pw:
    rol = user
    st.sidebar.success(f"Conectado: {rol}")
    if st.sidebar.button("Cerrar Sesión"):
        st.rerun()
else:
    st.info("Ingrese credenciales en el menú lateral.")
    st.stop()

# --- 4. GESTIÓN DINÁMICA DE PESTAÑAS ---
titulos = []
if rol in ["asistencia", "todos"]:
    titulos += ["👥 Registro", "📅 Pase de Lista", "📝 Informe Asist.", "🎂 Cumpleaños"]
if rol in ["tesoreria", "todos"]:
    titulos += ["💰 Tesorería"]
if rol in ["inventario", "todos"]:
    titulos += ["📦 Inventario"]
if rol == "todos":
    titulos += ["🛡️ Panel Pastor"]

tabs = st.tabs(titulos)
idx = 0

# --- MÓDULO: SECRETARÍA (ASISTENCIA) ---
if rol in ["asistencia", "todos"]:
    with tabs[idx]:
        st.subheader("👥 Registro de Miembros")
        with st.form("f_reg", clear_on_submit=True):
            n = st.text_input("Nombre Completo")
            t = st.text_input("Teléfono")
            d = st.text_input("Dirección")
            if st.form_submit_button("➕ Añadir Miembro"):
                if n.strip():
                    curr.execute("INSERT INTO miembros (nombre, telefono, direccion) VALUES (?,?,?)", (n.strip(), t, d))
                    conn.commit()
                    st.success("✅ Miembro registrado")
                    st.rerun()
    idx += 1

    with tabs[idx]:
        st.subheader("📅 Pase de Lista")
        f_asist = st.date_input("Fecha del Culto", format="DD/MM/YYYY")
        df_m = pd.read_sql_query("SELECT id, nombre FROM miembros ORDER BY nombre ASC", conn)
        if not df_m.empty:
            with st.form("f_lista_grupal"):
                st.write("Seleccione a los presentes:")
                asist_marcada = {}
                for _, fila in df_m.iterrows():
                    asist_marcada[fila['id']] = st.checkbox(fila['nombre'], key=f"c_{fila['id']}")
                if st.form_submit_button("💾 Guardar Asistencia"):
                    for m_id, check in asist_marcada.items():
                        if check:
                            curr.execute("INSERT INTO asistencia (miembro_id, fecha) VALUES (?,?)", (int(m_id), f_asist))
                    conn.commit()
                    st.success("✅ Asistencia guardada")
                    st.rerun()
    idx += 1

    with tabs[idx]:
        st.subheader("📝 Historial de Asistencia")
        q_asist = "SELECT a.id, m.nombre, a.fecha FROM asistencia a JOIN miembros m ON a.miembro_id = m.id"
        df_a = pd.read_sql_query(q_asist, conn)
        st.data_editor(df_a, use_container_width=True, key="ed_asist_hist")
    idx += 1

    with tabs[idx]:
        st.subheader("🎂 Registro de Cumpleaños")
        with st.form("f_cum"):
            nc = st.text_input("Nombre del Cumpleañero")
            fc = st.date_input("Fecha", min_value=date(1900,1,1))
            tc = st.text_input("WhatsApp")
            if st.form_submit_button("💾 Guardar"):
                curr.execute("INSERT INTO eventos (nombre_persona, tipo, fecha_evento, telefono) VALUES (?,?,?,?)", (nc, "Cumpleaños", fc, tc))
                conn.commit()
                st.rerun()
        st.divider()
        df_c = pd.read_sql_query("SELECT * FROM eventos WHERE tipo='Cumpleaños'", conn)
        st.data_editor(df_c, use_container_width=True, key="ed_cumples")
    idx += 1

# --- MÓDULO: TESORERÍA ---
if rol in ["tesoreria", "todos"]:
    with tabs[idx]:
        st.subheader("💰 Finanzas")
        with st.form("f_fin"):
            tipo_f = st.selectbox("Tipo", ["Ingreso", "Egreso"])
            cat_f = st.text_input("Categoría")
            mon_f = st.number_input("Monto", min_value=0.0)
            if st.form_submit_button("Registrar"):
                curr.execute("INSERT INTO finanzas (tipo, categoria, monto, fecha) VALUES (?,?,?,?)", (tipo_f, cat_f, mon_f, date.today()))
                conn.commit()
                st.rerun()
        df_f = pd.read_sql_query("SELECT * FROM finanzas", conn)
        st.dataframe(df_f, use_container_width=True)
    idx += 1

# --- MÓDULO: INVENTARIO ---
if rol in ["inventario", "todos"]:
    with tabs[idx]:
        st.subheader("📦 Inventario")
        with st.form("f_inv"):
            nom_i = st.text_input("Material")
            can_i = st.number_input("Cantidad", min_value=0)
            if st.form_submit_button("Agregar"):
                curr.execute("INSERT INTO materiales (nombre, cantidad, estado) VALUES (?,?,?)", (nom_i, can_i, "Bueno"))
                conn.commit()
                st.rerun()
        df_i = pd.read_sql_query("SELECT * FROM materiales", conn)
        st.data_editor(df_i, use_container_width=True, key="ed_inv_final")
    idx += 1

# --- MÓDULO: PASTOR ---
if rol == "todos":
    with tabs[idx]:
        st.subheader("🛡️ Panel Administrativo")
        col1, col2 = st.columns(2)
        res_m = pd.read_sql_query("SELECT COUNT(*) as t FROM miembros", conn)['t'][0]
        res_i = pd.read_sql_query("SELECT SUM(monto) as t FROM finanzas WHERE tipo='Ingreso'", conn)['t'][0]
        col1.metric("Total Miembros", res_m)
        col2.metric("Total Ingresos", f"${res_i:,.2f}")
        st.write("Edición Maestra de Miembros")
        df_master = pd.read_sql_query("SELECT * FROM miembros", conn)
        st.data_editor(df_master, use_container_width=True, key="ed_master")
