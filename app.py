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
        return 50.0  # Tasa de respaldo si falla la API

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
            </style>
            """, unsafe_allow_html=True)
    except:
        pass

agregar_fondo('1000687124.jpg')

# 4. BASE DE DATOS (ESTRUCTURA COMPLETA)
conn = sqlite3.connect('iglesia_pascua_web.db', check_same_thread=False)
curr = conn.cursor()
curr.execute("CREATE TABLE IF NOT EXISTS miembros (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono TEXT, direccion TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS finanzas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, referencia TEXT, monto_ves REAL, tasa REAL, monto_usd REAL, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS materiales (id INTEGER PRIMARY KEY AUTOINCREMENT, donante TEXT, categoria TEXT, descripcion TEXT, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY AUTOINCREMENT, miembro_id INTEGER, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_persona TEXT, tipo TEXT, fecha_evento DATE, telefono TEXT)")
conn.commit()

# 5. CONFIGURACIÓN DE USUARIOS
USUARIOS = {
    "tesorero": {"clave": "finanzas2026", "rol": "finanzas"},
    "secretario": {"clave": "iglesia2026", "rol": "asistencia"},
    "donaciones": {"clave": "pascua2026", "rol": "materiales"},
    "admin": {"clave": "pastor2026", "rol": "todos"}
}

if "sesion" not in st.session_state: st.session_state.sesion = None
if "recuperar" not in st.session_state: st.session_state.recuperar = False

# --- LÓGICA DE LOGIN Y RECUPERACIÓN ---
if st.session_state.sesion is None:
    st.markdown("<h1 style='text-align: center; color: white;'>🔐 Acceso al Sistema</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    
    with col_l2:
        if not st.session_state.recuperar:
            with st.form("login_form"):
                u_log = st.text_input("Usuario", placeholder="Ej: tesorero, secretario, admin")
                p_log = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Entrar"):
                    if u_log in USUARIOS and USUARIOS[u_log]["clave"] == p_log:
                        st.session_state.sesion = USUARIOS[u_log]["rol"]
                        st.rerun()
                    else: st.error("Usuario o clave incorrectos")
            if st.button("Olvidé mi contraseña"):
                st.session_state.recuperar = True
                st.rerun()
        else:
            st.write("### 🛠️ Recuperación de Clave")
            preg = st.text_input("Pregunta de seguridad: ¿Cuál es el nombre de la congregación?")
            if st.button("Ver Claves"):
                if preg.lower() == "cristo el salvador":
                    for user, info in USUARIOS.items():
                        st.code(f"Usuario: {user} | Clave: {info['clave']}")
                else: st.error("Respuesta incorrecta")
            if st.button("Volver al Login"):
                st.session_state.recuperar = False
                st.rerun()
    st.stop()

# --- PANEL PRINCIPAL ---
rol = st.session_state.sesion
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.sesion = None
    st.rerun()

st.title(f"⛪ Gestión - {rol.upper()}")

pestanas_visibles = []
if rol in ["finanzas", "todos"]: pestanas_visibles.extend(["💰 Registro Finanzas", "📊 Informe Tesorería"])
if rol in ["materiales", "todos"]: pestanas_visibles.extend(["📦 Registro Materiales", "📋 Informe Donaciones"])
if rol in ["asistencia", "todos"]: pestanas_visibles.extend(["👥 Registro Miembros", "📅 Tomar Asistencia", "📝 Informe Secretaría", "🎂 Cumpleaños"])
if rol == "todos": pestanas_visibles.extend(["📡 CONSOLIDADOR PASTORAL", "🛠️ Ajustes"])

tabs = st.tabs(pestanas_visibles)
idx = 0

# --- 1. SECCIÓN FINANZAS ---
if rol in ["finanzas", "todos"]:
    with tabs[idx]: # Registro
        st.subheader("Entrada de Diezmos y Ofrendas")
        tasa_val = obtener_tasa_bcv()
        with st.form("f_fin", clear_on_submit=True):
            n_f = st.text_input("Nombre del Hermano/a", placeholder="Nombre completo")
            r_f = st.text_input("Referencia", placeholder="Ej: Pago Móvil / Efectivo")
            mv_f = st.number_input("Monto en Bolívares (VES)", min_value=0.0)
            if st.form_submit_button("💾 Guardar"):
                if n_f and mv_f > 0:
                    curr.execute("INSERT INTO finanzas (nombre, referencia, monto_ves, tasa, monto_usd, fecha) VALUES (?,?,?,?,?,?)", 
                                 (n_f, r_f, mv_f, tasa_val, mv_f/tasa_val, date.today()))
                    conn.commit(); st.success("Registrado correctamente")
    idx += 1
    with tabs[idx]: # Informe
        st.subheader("📊 Informe de Tesorería")
        df_f = pd.read_sql_query("SELECT * FROM finanzas", conn)
        st.dataframe(df_f)
        total_usd = df_f['monto_usd'].sum()
        st.metric("Total en Arca (USD)", f"{total_usd:.2f} $")
        if st.button("📱 Enviar Informe por WhatsApp"):
            msg = urllib.parse.quote(f"📊 *Informe Tesorería*\nTotal: {total_usd:.2f} USD\nFecha: {date.today()}")
            st.link_button("Abrir WhatsApp", f"https://wa.me/?text={msg}")
        with st.expander("🗑️ Borrar Registro (Solo Tesorero/Admin)"):
            id_f = st.number_input("ID a eliminar (Finanzas)", min_value=0, key="del_f")
            if st.button("Confirmar Borrado", key="btn_f"):
                curr.execute("DELETE FROM finanzas WHERE id=?", (id_f,)); conn.commit(); st.rerun()
    idx += 1

# --- 2. SECCIÓN MATERIALES ---
if rol in ["materiales", "todos"]:
    with tabs[idx]: # Registro
        st.subheader("Donaciones de Materiales")
        with st.form("f_mat", clear_on_submit=True):
            don_m = st.text_input("Donante", placeholder="Nombre de quien entrega")
            desc_m = st.text_area("Descripción", placeholder="Ej: 10 kg de harina, medicinas...")
            if st.form_submit_button("💾 Registrar"):
                curr.execute("INSERT INTO materiales (donante, categoria, descripcion, fecha) VALUES (?,?,?,?)", (don_m, "General", desc_m, date.today()))
                conn.commit(); st.success("Donación guardada")
    idx += 1
    with tabs[idx]: # Informe
        st.subheader("📋 Informe de Donaciones")
        df_m = pd.read_sql_query("SELECT * FROM materiales", conn)
        st.dataframe(df_m)
        if st.button("📱 Enviar Informe de Materiales"):
            msg = urllib.parse.quote(f"📦 *Informe Materiales*\nRegistros hoy: {len(df_m)}")
            st.link_button("Abrir WhatsApp", f"https://wa.me/?text={msg}")
        with st.expander("🗑️ Borrar Registro (Solo Donaciones/Admin)"):
            id_m = st.number_input("ID a eliminar (Materiales)", min_value=0, key="del_m")
            if st.button("Confirmar Borrado", key="btn_m"):
                curr.execute("DELETE FROM materiales WHERE id=?", (id_m,)); conn.commit(); st.rerun()
    idx += 1

# --- 3. SECCIÓN ASISTENCIA Y MIEMBROS ---
if rol in ["asistencia", "todos"]:
    with tabs[idx]: # Registro Miembros
        st.subheader("👥 Registro de Miembros")
        with st.form("f_miembro", clear_on_submit=True):
            nom_m = st.text_input("Nombre Completo")
            tel_m = st.text_input("Teléfono (WhatsApp)", placeholder="58412...")
            if st.form_submit_button("➕ Añadir Miembro"):
                curr.execute("INSERT INTO miembros (nombre, telefono) VALUES (?,?)", (nom_m, tel_m))
                conn.commit(); st.success("Miembro añadido a la base de datos")
    idx += 1
    with tabs[idx]: # Tomar Asistencia
        st.subheader("📅 Asistencia por Calendario")
        df_list = pd.read_sql_query("SELECT id, nombre FROM miembros", conn)
        if not df_list.empty:
            with st.form("f_asis_cal", clear_on_submit=True):
                h_asis = st.selectbox("Seleccionar Hermano", df_list['nombre'].tolist())
                f_asis = st.date_input("Fecha de Asistencia")
                if st.form_submit_button("✅ Marcar Asistencia"):
                    m_id = df_list[df_list['nombre'] == h_asis]['id'].values[0]
                    curr.execute("INSERT INTO asistencia (miembro_id, fecha) VALUES (?,?)", (int(m_id), f_asis))
                    conn.commit(); st.success(f"Asistencia marcada para {h_asis}")
        else: st.warning("Debe registrar miembros primero.")
    idx += 1
    with tabs[idx]: # Informe Secretaría
        st.subheader("📝 Informe de Asistencia")
        df_a_full = pd.read_sql_query("""
            SELECT asistencia.id, miembros.nombre, asistencia.fecha 
            FROM asistencia 
            JOIN miembros ON asistencia.miembro_id = miembros.id
        """, conn)
        st.dataframe(df_a_full)
        if st.button("📱 Enviar Informe de Asistencia"):
            msg = urllib.parse.quote(f"📝 *Informe Asistencia*\nFecha: {date.today()}\nTotal registros: {len(df_a_full)}")
            st.link_button("Abrir WhatsApp", f"https://wa.me/?text={msg}")
        with st.expander("🗑️ Borrar Registro de Asistencia"):
            id_a = st.number_input("ID a eliminar (Asistencia)", min_value=0, key="del_a")
            if st.button("Confirmar Borrado", key="btn_a"):
                curr.execute("DELETE FROM asistencia WHERE id=?", (id_a,)); conn.commit(); st.rerun()
    idx += 1
    with tabs[idx]: # Cumpleaños
        st.subheader("🎂 Cumpleaños")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            with st.form("f_cumple", clear_on_submit=True):
                n_c = st.text_input("Nombre del Cumpleañero")
                t_c = st.text_input("Teléfono")
                f_c = st.date_input("Fecha de Nacimiento")
                if st.form_submit_button("Registrar Cumpleaños"):
                    curr.execute("INSERT INTO eventos (nombre_persona, tipo, fecha_evento, telefono) VALUES (?,?,?,?)", (n_c, "Cumpleaños", f_c, t_c))
                    conn.commit(); st.success("Registrado")
        with col_c2:
            hoy = date.today().strftime('%m-%d')
            df_ev = pd.read_sql_query("SELECT * FROM eventos", conn)
            if not df_ev.empty:
                df_ev['fecha_evento'] = pd.to_datetime(df_ev['fecha_evento'])
                df_ev['dia_mes'] = df_ev['fecha_evento'].dt.strftime('%m-%d')
                cumples = df_ev[df_ev['dia_mes'] == hoy]
                for _, r in cumples.iterrows():
                    st.info(f"🎉 ¡Hoy cumple años **{r['nombre_persona']}**!")
                    st.link_button("Felicitar", f"https://wa.me/{r['telefono']}?text=Felicidades")
    idx += 1

# --- 4. SECCIÓN PASTOR ---
if rol == "todos":
    with tabs[idx]:
        st.header("📡 CONSOLIDADOR PASTORAL")
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingresos (USD)", f"{pd.read_sql_query('SELECT SUM(monto_usd) FROM finanzas', conn).iloc[0,0] or 0:.2f}")
        c2.metric("Miembros", len(pd.read_sql_query("SELECT * FROM miembros", conn)))
        c3.metric("Materiales", len(pd.read_sql_query("SELECT * FROM materiales", conn)))
    idx += 1
    with tabs[idx]:
        st.subheader("🛠️ Ajustes de Base de Datos")
        tabla = st.selectbox("Seleccionar Tabla", ["miembros", "finanzas", "materiales", "asistencia", "eventos"])
        st.dataframe(pd.read_sql_query(f"SELECT * FROM {tabla}", conn))

