
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import os
import io
from PIL import Image

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Iglesia Pascua - Sistema Integral", layout="wide")

# --- 2. CONEXIÓN A BASE DE DATOS ---
conn = sqlite3.connect("iglesia_pascua.db", check_same_thread=False)
curr = conn.cursor()

# Crear todas las tablas necesarias para que nada falle
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

user = st.sidebar.text_input("Usuario", key="login_user")
pw = st.sidebar.text_input("Contraseña", type="password", key="login_pw")

if user in USUARIOS and USUARIOS[user] == pw:
    rol = user
    st.sidebar.success(f"Conectado: {rol}")
    if st.sidebar.button("Cerrar Sesión"):
        st.rerun()
else:
    st.info("Por favor, ingrese sus credenciales en el menú lateral.")
    st.stop()

# --- 4. DEFINICIÓN DINÁMICA DE PESTAÑAS ---
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
    # Registro de Miembros
    with tabs[idx]:
        st.subheader("👥 Registro de Miembros")
        with st.form("form_registro", clear_on_submit=True):
            n_m = st.text_input("Nombre Completo")
            t_m = st.text_input("Teléfono")
            d_m = st.text_input("Dirección")
            if st.form_submit_button("➕ Añadir"):
                if n_m.strip():
                    curr.execute("INSERT INTO miembros (nombre, telefono, direccion) VALUES (?,?,?)", (n_m.strip(), t_m, d_m))
                    conn.commit()
                    st.success(f"✅ {n_m} registrado")
                    st.rerun()
                else:
                    st.warning("El nombre es obligatorio")
    idx += 1

    # Pase de Lista Grupal
    with tabs[idx]:
        st.subheader("📅 Pase de Lista")
        f_hoy = st.date_input("Fecha del Culto", key="fecha_asist")
        df_miembros = pd.read_sql_query("SELECT id, nombre FROM miembros ORDER BY nombre ASC", conn)
        
        if not df_miembros.empty:
            with st.form("form_asistencia"):
                st.write("Seleccione a los presentes:")
                asist_dict = {}
                for _, fila in df_miembros.iterrows():
                    asist_dict[fila['id']] = st.checkbox(fila['nombre'], key=f"miembro_{fila['id']}")
                
                if st.form_submit_button("💾 Guardar Asistencia"):
                    for m_id, presente in asist_dict.items():
                        if presente:
                            curr.execute("INSERT INTO asistencia (miembro_id, fecha) VALUES (?,?)", (int(m_id), f_hoy))
                    conn.commit()
                    st.success("✅ Asistencia guardada correctamente")
                    st.rerun()
        else:
            st.info("No hay miembros. Regístrelos en la pestaña anterior.")
    idx += 1

    # Informe de Asistencia
    with tabs[idx]:
        st.subheader("📝 Historial")
        df_informe = pd.read_sql_query("SELECT a.id, m.nombre, a.fecha FROM asistencia a JOIN miembros m ON a.miembro_id = m.id ORDER BY a.id DESC", conn)
        st.data_editor(df_informe, use_container_width=True, key="ed_informe_asist")
    idx += 1

    # Cumpleaños
    with tabs[idx]:
        st.subheader("🎂 Cumpleaños")
        with st.form("form_cumple"):
            c_nom = st.text_input("Nombre")
            c_fec = st.date_input("Fecha", min_value=date(1900, 1, 1))
            if st.form_submit_button("Guardar"):
                curr.execute("INSERT INTO eventos (nombre_persona, tipo, fecha_evento) VALUES (?,?,?)", (c_nom, "Cumpleaños", c_fec))
                conn.commit()
                st.rerun()
        df_cumples = pd.read_sql_query("SELECT * FROM eventos WHERE tipo='Cumpleaños'", conn)
        st.data_editor(df_cumples, use_container_width=True, key="ed_cumples")
    idx += 1

# --- MÓDULO: TESORERÍA ---
if rol in ["tesoreria", "todos"]:
    with tabs[idx]:
        st.subheader("💰 Gestión Financiera")
        with st.form("form_finanzas"):
            t_f = st.selectbox("Tipo", ["Ingreso", "Egreso"])
            c_f = st.text_input("Categoría")
            m_f = st.number_input("Monto", min_value=0.0)
            if st.form_submit_button("Registrar Movimiento"):
                curr.execute("INSERT INTO finanzas (tipo, categoria, monto, fecha) VALUES (?,?,?,?)", (t_f, c_f, m_f, date.today()))
                conn.commit()
                st.rerun()
        df_fin = pd.read_sql_query("SELECT * FROM finanzas", conn)
        st.dataframe(df_fin, use_container_width=True)
    idx += 1

# --- MÓDULO: INVENTARIO ---
if rol in ["inventario", "todos"]:
    with tabs[idx]:
        st.subheader("📦 Inventario")
        with st.form("form_inv"):
            mat = st.text_input("Material")
            can = st.number_input("Cantidad", min_value=0)
            if st.form_submit_button("Agregar"):
                curr.execute("INSERT INTO materiales (nombre, cantidad, estado) VALUES (?,?,?)", (mat, can, "Bueno"))
                conn.commit()
                st.rerun()
        df_inv = pd.read_sql_query("SELECT * FROM materiales", conn)
        st.data_editor(df_inv, use_container_width=True, key="ed_inv_final")
    idx += 1

# --- MÓDULO: PASTOR ---
if rol == "todos":
    with tabs[idx]:
        st.subheader("🛡️ Administración General")
        col1, col2 = st.columns(2)
        m_count = pd.read_sql_query("SELECT COUNT(*) as total FROM miembros", conn)['total'][0]
        f_sum = pd.read_sql_query("SELECT SUM(monto) as total FROM finanzas WHERE tipo='Ingreso'", conn)['total'][0]
        col1.metric("Miembros Totales", m_count)
        col2.metric("Ingresos Totales", f"${f_sum:,.2f}")
        st.write("Edición Maestra")
        df_master = pd.read_sql_query("SELECT * FROM miembros", conn)
        st.data_editor(df_master, use_container_width=True, key="ed_pastor_miembros")

