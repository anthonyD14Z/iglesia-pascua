
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Iglesia Pascua", layout="wide")

# --- CONEXIÓN A BASE DE DATOS ---
conn = sqlite3.connect("iglesia_pascua.db", check_same_thread=False)
curr = conn.cursor()

# Crear tablas si no existen (Estructura base)
curr.execute("CREATE TABLE IF NOT EXISTS miembros (id INTEGER PRIMARY KEY, nombre TEXT, telefono TEXT, direccion TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY, miembro_id INTEGER, fecha TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY, nombre_persona TEXT, tipo TEXT, fecha_evento TEXT, telefono TEXT)")
conn.commit()

# --- LOGIN ---
st.sidebar.title("⛪ Acceso Iglesia")
USUARIOS = {"asistencia": "1234", "todos": "admin"} 

user = st.sidebar.text_input("Usuario")
pw = st.sidebar.text_input("Contraseña", type="password")

if user in USUARIOS and USUARIOS[user] == pw:
    rol = user
    st.sidebar.success(f"Conectado como: {rol}")
    if st.sidebar.button("Cerrar Sesión"):
        st.rerun()
else:
    st.info("Por favor, ingrese sus credenciales en el menú lateral.")
    st.stop()

# --- DEFINICIÓN DE PESTAÑAS (Sincronizadas para evitar IndexError) ---
if rol == "asistencia":
    pestanas_v = ["👥 Registro Miembros", "📅 Tomar Asistencia", "📝 Informe Asistencia", "🎂 Cumpleaños"]
else:
    pestanas_v = ["👥 Registro Miembros", "📅 Tomar Asistencia", "📝 Informe Asistencia", "🎂 Cumpleaños", "🛡️ Admin Pastor"]

tabs = st.tabs(pestanas_v)
idx = 0

# --- 1. REGISTRO DE MIEMBROS ---
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
                st.rerun() # Para que aparezca de inmediato en la lista de asistencia
            else:
                st.warning("⚠️ El nombre es obligatorio")
idx += 1

# --- 2. TOMAR ASISTENCIA (TODA LA MEMBRESÍA CON CHECKBOX) ---
with tabs[idx]:
    st.subheader("📅 Pase de Lista - Asistencia Grupal")
    fec_asist = st.date_input("Fecha del Culto", format="DD/MM/YYYY", key="fecha_asist_key")
    
    # Buscamos a todos los miembros registrados
    df_m = pd.read_sql_query("SELECT id, nombre FROM miembros ORDER BY nombre ASC", conn)
    
    if not df_m.empty:
        with st.form("form_asistencia_grupal"):
            st.write("Seleccione a los hermanos presentes hoy:")
            asist_dict = {}
            # Generamos un checkbox por cada persona en la base de datos
            for _, fila in df_m.iterrows():
                asist_dict[fila['id']] = st.checkbox(fila['nombre'], key=f"chk_{fila['id']}")
            
            if st.form_submit_button("💾 Guardar Asistencia del Día"):
                total_asistentes = 0
                for m_id, asistio in asist_dict.items():
                    if asistio:
                        curr.execute("INSERT INTO asistencia (miembro_id, fecha) VALUES (?,?)", (int(m_id), fec_asist))
                        total_asistentes += 1
                conn.commit()
                if total_asistentes > 0:
                    st.success(f"✅ Se registró la asistencia de {total_asistentes} personas.")
                else:
                    st.warning("⚠️ No seleccionaste a nadie.")
                st.rerun()
    else:
        st.info("No hay miembros registrados aún. Ve a la primera pestaña.")
idx += 1

# --- 3. INFORME DE ASISTENCIA ---
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
        # Convertir fecha para que se vea bien en el reporte
        df_rep['fecha'] = pd.to_datetime(df_rep['fecha']).dt.strftime('%d/%m/%Y')
        st.data_editor(df_rep, use_container_width=True, num_rows="dynamic", key="tabla_asist_edit")
    else:
        st.info("No hay registros de asistencia en la base de datos.")
idx += 1

# --- 4. CUMPLEAÑOS ---
with tabs[idx]:
    st.subheader("🎂 Registro de Cumpleaños")
    with st.form("f_cumple", clear_on_submit=True):
        n_c = st.text_input("Nombre del Cumpleañero")
        f_c = st.date_input("Fecha de Nacimiento", min_value=date(1900, 1, 1), format="DD/MM/YYYY")
        t_c = st.text_input("WhatsApp")
        if st.form_submit_button("💾 Guardar Cumpleaños"):
            if n_c:
                curr.execute("INSERT INTO eventos (nombre_persona, tipo, fecha_evento, telefono) VALUES (?,?,?,?)", 
                            (n_c, "Cumpleaños", f_c, t_c))
                conn.commit()
                st.success("✅ Cumpleaños guardado")
                st.rerun()
    
    st.divider()
    df_ev = pd.read_sql_query("SELECT * FROM eventos WHERE tipo='Cumpleaños'", conn)
    if not df_ev.empty:
        df_ev['fecha_evento'] = pd.to_datetime(df_ev['fecha_evento']).dt.strftime('%d/%m/%Y')
        st.data_editor(df
