import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import base64
import requests
import urllib.parse

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Iglesia Cristo El Salvador", page_icon="⛪", layout="wide")

# 2. FUNCIÓN DE TASA BCV (CON PLAN B MANUAL)
def obtener_tasa_bcv():
    urls = [
        "https://ve.dolarapi.com/v1/dolares/oficial",
        "https://pydolarve.org/api/v1/dollar?page=bcv"
    ]
    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                datos = response.json()
                # Dependiendo de la API, el campo puede llamarse 'promedio' o 'price'
                return float(datos.get('promedio', datos.get('price', None)))
        except:
            continue
    return None

# 3. FONDO Y ESTILO PROFESIONAL
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
                padding: 25px !important; border-radius: 15px !important;
                box-shadow: 0 8px 16px rgba(0,0,0,0.4);
                color: #1e1e1e !important;
            }}
            h1, h2, h3 {{ color: #ffffff !important; text-shadow: 2px 2px 4px #000000; }}
            .stButton>button {{ width: 100%; border-radius: 10px; font-weight: bold; }}
            </style>
            """, unsafe_allow_html=True)
    except:
        st.warning("No se encontró la imagen de fondo.")

agregar_fondo('1000687124.jpg')

# 4. BASE DE DATOS (AUTO-REPARACIÓN)
conn = sqlite3.connect('iglesia_pascua_web.db', check_same_thread=False)
curr = conn.cursor()
curr.execute("CREATE TABLE IF NOT EXISTS miembros (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono TEXT, direccion TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS finanzas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, referencia TEXT, monto_ves REAL, tasa REAL, monto_usd REAL, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS materiales (id INTEGER PRIMARY KEY AUTOINCREMENT, donante TEXT, categoria TEXT, descripcion TEXT, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY AUTOINCREMENT, miembro_id INTEGER, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_persona TEXT, tipo TEXT, fecha_evento DATE, telefono TEXT)")
conn.commit()

# 5. SEGURIDAD
USUARIOS = {
    "tesorero": {"clave": "finanzas2026", "rol": "finanzas"},
    "secretario": {"clave": "iglesia2026", "rol": "asistencia"},
    "donaciones": {"clave": "pascua2026", "rol": "materiales"},
    "admin": {"clave": "pastor2026", "rol": "todos"}
}

if "sesion" not in st.session_state: st.session_state.sesion = None
if "recuperar" not in st.session_state: st.session_state.recuperar = False

if st.session_state.sesion is None:
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso al Sistema</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        if not st.session_state.recuperar:
            with st.form("login_form"):
                u_log = st.text_input("Usuario")
                p_log = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Entrar"):
                    if u_log in USUARIOS and USUARIOS[u_log]["clave"] == p_log:
                        st.session_state.sesion = USUARIOS[u_log]["rol"]; st.rerun()
                    else: st.error("Clave incorrecta")
            if st.button("Olvidé mi contraseña"): st.session_state.recuperar = True; st.rerun()
        else:
            preg = st.text_input("Pregunta de seguridad: ¿Nombre de la congregación?")
            if st.button("Ver Claves"):
                if preg.lower() == "cristo el salvador":
                    for k, v in USUARIOS.items(): st.code(f"{k}: {v['clave']}")
                else: st.error("Incorrecto")
            if st.button("Volver"): st.session_state.recuperar = False; st.rerun()
    st.stop()

# --- PANEL DE CONTROL ---
rol = st.session_state.sesion
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.sesion = None; st.rerun()

st.title(f"⛪ Panel de Control - {rol.upper()}")

pestanas_v = []
if rol in ["finanzas", "todos"]: pestanas_v.extend(["💰 Registro Finanzas", "📊 Informe Tesorería"])
if rol in ["materiales", "todos"]: pestanas_v.extend(["📦 Registro Materiales", "📋 Informe Donaciones"])
if rol in ["asistencia", "todos"]: pestanas_v.extend(["👥 Registro Miembros", "📅 Tomar Asistencia", "📝 Informe Secretaría", "🎂 Cumpleaños"])
if rol == "todos": pestanas_v.extend(["📡 PASTORAL", "🛠️ Ajustes"])

tabs = st.tabs(pestanas_v)
idx = 0

# --- FINANZAS (CON ARREGLO DE TASA) ---
if rol in ["finanzas", "todos"]:
    with tabs[idx]:
        st.subheader("Entrada de Diezmos y Ofrendas")
        t_auto = obtener_tasa_bcv()
        if t_auto:
            t_final = st.number_input("Tasa BCV (Detectada automáticamente)", value=t_auto)
        else:
            st.warning("⚠️ No se pudo conectar con el BCV. Ingrese la tasa manualmente.")
            t_final = st.number_input("Tasa BCV Manual", min_value=1.0, value=55.0)

        with st.form("f_fin", clear_on_submit=True):
            n_f = st.text_input("Nombre del Hermano/a")
            r_f = st.text_input("Referencia")
            mv_f = st.number_input("Monto en Bolívares (VES)", min_value=0.0)
            if st.form_submit_button("💾 Guardar Registro"):
                if n_f and mv_f > 0:
                    m_usd = mv_f / t_final
                    curr.execute("INSERT INTO finanzas (nombre, referencia, monto_ves, tasa, monto_usd, fecha) VALUES (?,?,?,?,?,?)", (n_f, r_f, mv_f, t_final, m_usd, date.today()))
                    conn.commit()
                    st.success(f"Guardado: {m_usd:.2f} USD")
                else: st.error("Complete todos los campos")
    idx += 1
    with tabs[idx]:
        df_f = pd.read_sql_query("SELECT * FROM finanzas", conn)
        st.dataframe(df_f)
        if st.button("📱 Enviar Reporte WhatsApp"):
            msg = urllib.parse.quote(f"📊 Informe Tesorería\nTotal: {df_f['monto_usd'].sum():.2f} USD")
            st.link_button("Enviar", f"https://wa.me/?text={msg}")
        with st.expander("🗑️ Borrar"):
            id_f = st.number_input("ID a borrar", min_value=0, key="df")
            if st.button("Confirmar Borrado", key="bf"):
                curr.execute("DELETE FROM finanzas WHERE id=?", (id_f,)); conn.commit(); st.rerun()
    idx += 1

# --- MATERIALES ---
if rol in ["materiales", "todos"]:
    with tabs[idx]:
        with st.form("f_mat", clear_on_submit=True):
            d_m = st.text_input("Donante")
            desc_m = st.text_area("Descripción")
            if st.form_submit_button("Registrar Material"):
                curr.execute("INSERT INTO materiales (donante, categoria, descripcion, fecha) VALUES (?,?,?,?)", (d_m, "General", desc_m, date.today()))
                conn.commit(); st.success("Registrado")
    idx += 1
    with tabs[idx]:
        df_m = pd.read_sql_query("SELECT * FROM materiales", conn)
        st.dataframe(df_m)
        with st.expander("🗑️ Borrar"):
            id_m = st.number_input("ID a borrar", min_value=0, key="dm")
            if st.button("Eliminar", key="bm"):
                curr.execute("DELETE FROM materiales WHERE id=?", (id_m,)); conn.commit(); st.rerun()
    idx += 1

# --- ASISTENCIA / SECRETARÍA ---
if rol in ["asistencia", "todos"]:
    with tabs[idx]:
        st.subheader("Directorio de Miembros")
        with st.form("f_mie", clear_on_submit=True):
            nm = st.text_input("Nombre Completo")
            tm = st.text_input("WhatsApp (Ej: 58412...)")
            if st.form_submit_button("Añadir Miembro"):
                curr.execute("INSERT INTO miembros (nombre, telefono) VALUES (?,?)", (nm, tm))
                conn.commit(); st.success("Añadido")
    idx += 1
    with tabs[idx]:
        st.subheader("Control por Calendario")
        df_l = pd.read_sql_query("SELECT id, nombre FROM miembros", conn)
        if not df_l.empty:
            with st.form("f_as_c"):
                herm = st.selectbox("Seleccionar Hermano", df_l['nombre'].tolist())
                fec = st.date_input("Fecha del Culto")
                if st.form_submit_button("✅ Marcar Asistencia"):
                    m_id = df_l[df_l['nombre'] == herm]['id'].values[0]
                    curr.execute("INSERT INTO asistencia (miembro_id, fecha) VALUES (?,?)", (int(m_id), fec))
                    conn.commit(); st.success(f"Asistencia marcada para {herm}")
        else: st.error("Primero debe registrar miembros")
    idx += 1
    with tabs[idx]:
        st.subheader("Reporte de Asistencia")
        try:
            df_as = pd.read_sql_query("SELECT asistencia.id, miembros.nombre, asistencia.fecha FROM asistencia JOIN miembros ON asistencia.miembro_id = miembros.id", conn)
            st.dataframe(df_as)
            with st.expander("🗑️ Borrar"):
                id_as = st.number_input("ID a borrar", min_value=0, key="da")
                if st.button("Eliminar", key="ba"):
                    curr.execute("DELETE FROM asistencia WHERE id=?", (id_as,)); conn.commit(); st.rerun()
        except: st.info("No hay registros")
    idx += 1
    with tabs[idx]:
        st.subheader("🎂 Cumpleaños")
        with st.form("f_cu"):
            n_c = st.text_input("Nombre")
            f_c = st.date_input("Fecha")
            t_c = st.text_input("Telf")
            if st.form_submit_button("Guardar Cumpleaños"):
                curr.execute("INSERT INTO eventos (nombre_persona, tipo, fecha_evento, telefono) VALUES (?,?,?,?)", (n_c, "Cumpleaños", f_c, t_c))
                conn.commit(); st.success("Guardado")
        df_ev = pd.read_sql_query("SELECT * FROM eventos", conn)
        st.dataframe(df_ev)
    idx += 1

# --- PASTOR ---
if rol == "todos":
    with tabs[idx]:
        st.header("📡 RESUMEN PASTORAL")
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingresos Totales (USD)", f"{pd.read_sql_query('SELECT SUM(monto_usd) FROM finanzas', conn).iloc[0,0] or 0:.2f}")
        c2.metric("Total Miembros", len(pd.read_sql_query("SELECT * FROM miembros", conn)))
        c3.metric("Eventos Próximos", len(pd.read_sql_query("SELECT * FROM eventos", conn)))
    idx += 1
    with tabs[idx]:
        st.subheader("🛠️ Administración de Datos")
        t_sel = st.selectbox("Seleccionar Tabla", ["miembros", "finanzas", "materiales", "asistencia", "eventos"])
        st.dataframe(pd.read_sql_query(f"SELECT * FROM {t_sel}", conn))

