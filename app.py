
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Iglesia Pascua", layout="wide")

# Conexión limpia a la base de datos
conn = sqlite3.connect("iglesia_pascua.db", check_same_thread=False)
curr = conn.cursor()

# Creación de tablas base
curr.execute("CREATE TABLE IF NOT EXISTS miembros (id INTEGER PRIMARY KEY, nombre TEXT, telefono TEXT, direccion TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY, miembro_id INTEGER, fecha TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY, nombre_persona TEXT, tipo TEXT, fecha_evento TEXT, telefono TEXT)")
conn.commit()

# --- 2. SISTEMA DE LOGIN ---
st.sidebar.title("⛪ Acceso Iglesia")
USUARIOS = {"asistencia": "1234", "todos": "admin"} 

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

# --- 3. DEFINICIÓN DE PESTAÑAS (Sincronizadas) ---
if rol == "asistencia":
    pestanas_v = ["👥 Registro Miembros", "📅 Tomar Asistencia", "📝 Informe Asistencia", "🎂 Cumpleaños"]
else:
    pestanas_v = ["👥 Registro Miembros", "📅 Tomar Asistencia", "📝 Informe Asistencia", "🎂 Cumpleaños", "🛡️ Admin Pastor"]

tabs = st.tabs(pestanas_v)
idx = 0

# --- PESTAÑA: REGISTRO DE MIEMBROS ---
with tabs[idx]:
    st.subheader("👥 Registro de Miembros")
    with st.form("f_mie", clear_on_submit=True):
        nm = st.text_input("Nombre Completo")
        tm = st.text_input("Teléfono")
        dm = st.text_input("Dirección")
        if st.form_submit_button("➕ Añadir Miembro"):
            if nm.strip():
                curr.execute("INSERT INTO miembros (nombre, telefono, direccion) VALUES (?,?,?)", (nm.strip(), tm, dm))
                conn.commit()
                st.success(f"✅ {nm} añadido correctamente")
                st.rerun()
            else:
                st.warning("⚠️ El nombre es obligatorio")
idx += 1

# --- PESTAÑA: TOMAR ASISTENCIA (LISTA DINÁMICA) ---
with tabs[idx]:
    st.subheader("📅 Pase de Lista")
    fec_asist = st.date_input("Fecha del Culto", format="DD/MM/YYYY", key="fecha_asist_key")
    
    # Cargar miembros para la lista de checkboxes
    df_m = pd.read_sql_query("SELECT id, nombre FROM miembros ORDER BY nombre ASC", conn)
    
    if not df_m.empty:
        with st.form("form_asistencia_grupal"):
            st.write("Marque a los hermanos presentes:")
            asist_dict = {}
            for _, fila in df_m.iterrows():
                # El ID del miembro se usa para la lógica, el Nombre para la etiqueta
                asist_dict[fila['id']] = st.checkbox(fila['nombre'], key=f"chk_{fila['id']}")
            
            if st.form_submit_button("💾 Guardar Asistencia"):
                total = 0
                for m_id, asistio in asist_dict.items():
                    if asistio:
                        curr.execute("INSERT INTO asistencia (miembro_id, fecha) VALUES (?,?)", (int(m_id), fec_asist))
                        total += 1
                conn.commit()
                st.success(f"✅ Asistencia guardada: {total} presentes.")
                st.rerun()
    else:
        st.info("No hay miembros registrados aún.")
idx += 1

# --- PESTAÑA: INFORME ASISTENCIA ---
with tabs[idx]:
    st.subheader("📝 Historial de Asistencia")
    query_inf = """
        SELECT asistencia.id, miembros.nombre, asistencia.fecha 
        FROM asistencia 
        JOIN miembros ON asistencia.miembro_id = miembros.id
        ORDER BY asistencia.fecha DESC
    """
    df_rep = pd.read_sql_query(query_inf, conn)
    if not df_rep.empty:
        df_rep['fecha'] = pd.to_datetime(df_rep['fecha']).dt.strftime('%d/%m/%Y')
        st.data_editor(df_rep, use_container_width=True, key="tabla_asist_final")
    else:
        st.info("Sin registros de asistencia.")
idx += 1

# --- PESTAÑA: CUMPLEAÑOS ---
with tabs[idx]:
    st.subheader("🎂 Registro de Cumpleaños")
    with st.form("f_cumple_v2", clear_on_submit=True):
        n_c = st.text_input("Nombre")
        f_c = st.date_input("Fecha", min_value=date(1900, 1, 1), format="DD/MM/YYYY")
        t_c = st.text_input("WhatsApp")
        if st.form_submit_button("💾 Guardar"):
            if n_c:
                curr.execute("INSERT INTO eventos (nombre_persona, tipo, fecha_evento, telefono) VALUES (?,?,?,?)", (n_c, "Cumpleaños", f_c, t_c))
                conn.commit()
                st.success("✅ Guardado")
                st.rerun()
    
    st.divider()
    df_ev = pd.read_sql_query("SELECT * FROM eventos WHERE tipo='Cumpleaños'", conn)
    if not df_ev.empty:
        df_ev['fecha_evento'] = pd.to_datetime(df_ev['fecha_evento']).dt.strftime('%d/%m/%Y')
        st.data_editor(df_ev, use_container_width=True, key="tabla_cumples_final")
idx += 1

# --- PESTAÑA: ADMIN PASTOR ---
if rol == "todos":
    with tabs[idx]:
        st.subheader("🛡️ Panel Administrativo")
        st.write("Lista Maestra de Miembros")
        df_all = pd.read_sql_query("SELECT * FROM miembros", conn)
        st.data_editor(df_all, use_container_width=True, key="master_m")
