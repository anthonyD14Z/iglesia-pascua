
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import os
from PIL import Image
import io

# --- 1. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="Iglesia Pascua - Sistema Integral", layout="wide")

# --- 2. BASE DE DATOS (ESTRUCTURA COMPLETA) ---
conn = sqlite3.connect("iglesia_pascua.db", check_same_thread=False)
curr = conn.cursor()

# Tablas de todas las áreas
curr.execute("CREATE TABLE IF NOT EXISTS miembros (id INTEGER PRIMARY KEY, nombre TEXT, telefono TEXT, direccion TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY, miembro_id INTEGER, fecha TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY, nombre_persona TEXT, tipo TEXT, fecha_evento TEXT, telefono TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS finanzas (id INTEGER PRIMARY KEY, tipo TEXT, categoria TEXT, monto REAL, fecha TEXT, descripcion TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS materiales (id INTEGER PRIMARY KEY, nombre TEXT, cantidad INTEGER, estado TEXT)")
conn.commit()

# --- 3. LOGIN ---
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
    st.info("Ingrese credenciales en el menú lateral para activar los módulos.")
    st.stop()

# --- 4. GESTIÓN DINÁMICA DE PESTAÑAS ---
titulos = []
if rol in ["asistencia", "todos"]:
    titulos += ["👥 Miembros", "📅 Asistencia", "📝 Informe Asist.", "🎂 Cumpleaños"]
if rol in ["tesoreria", "todos"]:
    titulos += ["💰 Finanzas"]
if rol in ["inventario", "todos"]:
    titulos += ["📦 Inventario"]
if rol == "todos":
    titulos += ["🛡️ Panel Pastor"]

tabs = st.tabs(titulos)
idx = 0

# --- MODULO: SECRETARÍA (ASISTENCIA) ---
if rol in ["asistencia", "todos"]:
    # Registro
    with tabs[idx]:
        st.subheader("👥 Registro de Miembros")
        with st.form("f_reg", clear_on_submit=True):
            n = st.text_input("Nombre Completo")
            t = st.text_input("Teléfono")
            if st.form_submit_button("Añadir"):
                if n.strip():
                    curr.execute("INSERT INTO miembros (nombre, telefono) VALUES (?,?)", (n.strip(), t))
                    conn.commit()
                    st.rerun()
    idx += 1

    # Pase de Lista Grupal
    with tabs[idx]:
        st.subheader("📅 Pase de Lista")
        f_asist = st.date_input("Fecha", key="f_asist_key")
        df_m = pd.read_sql_query("SELECT id, nombre FROM miembros ORDER BY nombre ASC", conn)
        if not df_m.empty:
            with st.form("f_asist_grp"):
                checks = {}
                for _, fila in df_m.iterrows():
                    checks[fila['id']] = st.checkbox(fila['nombre'], key=f"c_{fila['id']}")
                if st.form_submit_button("Guardar Asistencia"):
                    for m_id, marcando in checks.items():
                        if marcando:
                            curr.execute("INSERT INTO asistencia (miembro_id, fecha) VALUES (?,?)", (int(m_id), f_asist))
                    conn.commit()
                    st.success("Guardado")
                    st.rerun()
    idx += 1

    # Informe
    with tabs[idx]:
        st.subheader("📝 Historial de Asistencia")
        df_rep = pd.read_sql_query("SELECT a.id, m.nombre, a.fecha FROM asistencia a JOIN miembros m ON a.miembro_id = m.id", conn)
        st.data_editor(df_rep, use_container_width=True, key="ed_asist")
    idx += 1

    # Cumpleaños
    with tabs[idx]:
        st.subheader("🎂 Cumpleaños")
        with st.form("f_cum"):
            nc = st.text_input("Nombre")
            fc = st.date_input("Fecha", min_value=date(1900,1,1))
            if st.form_submit_button("Guardar Cumple"):
                curr.execute("INSERT INTO eventos (nombre_persona, tipo, fecha_evento) VALUES (?,?,?)", (nc, "Cumpleaños", fc))
                conn.commit()
                st.rerun()
    idx += 1

# --- MODULO: TESORERÍA ---
if rol in ["tesoreria", "todos"]:
    with tabs[idx]:
        st.subheader("💰 Gestión Financiera")
        col1, col2 = st.columns(2)
        with col1:
            with st.form("f_fin"):
                t_f = st.selectbox("Tipo", ["Ingreso", "Egreso"])
                cat = st.text_input("Categoría (Diezmo, Ofrenda, Gasto)")
                mon = st.number_input("Monto", min_value=0.0)
                if st.form_submit_button("Registrar Movimiento"):
                    curr.execute("INSERT INTO finanzas (tipo, categoria, monto, fecha) VALUES (?,?,?,?)", (t_f, cat, mon, date.today()))
                    conn.commit()
                    st.rerun()
        with col2:
            df_fin = pd.read_sql_query("SELECT * FROM finanzas ORDER BY id DESC", conn)
            st.write("Últimos Movimientos")
            st.dataframe(df_fin, use_container_width=True)
    idx += 1

# --- MODULO: INVENTARIO ---
if rol in ["inventario", "todos"]:
    with tabs[idx]:
        st.subheader("📦 Inventario de Materiales")
        with st.form("f_inv"):
            nom_m = st.text_input("Nombre del Material")
            can_m = st.number_input("Cantidad", min_value=0)
            if st.form_submit_button("Agregar al Inventario"):
                curr.execute("INSERT INTO materiales (nombre, cantidad, estado) VALUES (?,?,?)", (nom_m, can_m, "Bueno"))
                conn.commit()
                st.rerun()
        df_inv = pd.read_sql_query("SELECT * FROM materiales", conn)
        st.data_editor(df_inv, use_container_width=True, key="ed_inv")
    idx += 1

# --- MODULO: PASTOR ---
if rol == "todos":
    with tabs[idx]:
        st.subheader("🛡️ Panel de Control Pastoral")
        res_m = pd.read_sql_query("SELECT COUNT(*) as total FROM miembros", conn)
        res_f = pd.read_sql_query("SELECT SUM(monto) as total FROM finanzas WHERE tipo='Ingreso'", conn)
        c1, c2 = st.columns(2)
        c1.metric("Total Miembros", res_m['total'][0])
        c2.metric("Total Ingresos", f"${res_f['total'][0]:,.2f}")

