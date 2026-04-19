
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime
import base64
import requests
import urllib.parse

# 1. CONFIGURACIÓN DE PÁGINA (DEBE SER LO PRIMERO)
st.set_page_config(page_title="Iglesia Cristo El Salvador", page_icon="⛪", layout="wide")

# 2. FUNCIÓN DE TASA BCV (SISTEMA DE TRIPLE INTENTO)
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
                # Intenta obtener de 'promedio' o 'price' según la API que responda
                return float(datos.get('promedio', datos.get('price', 0)))
        except: continue
    return None

# 3. FONDO Y ESTILO CSS
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
            [data-testid="stForm"], .stTabs, .stMetric, div.stAlert, [data-testid="stDataFrameResizer"] {{
                background-color: rgba(255, 255, 255, 0.95) !important;
                padding: 20px !important; border-radius: 15px !important;
                box-shadow: 0 8px 16px rgba(0,0,0,0.4);
            }}
            label, .stMarkdown p {{
                color: #000000 !important; 
                font-weight: 800 !important;
                font-size: 1.05rem !important;
            }}
            h1, h2, h3 {{ color: #ffffff !important; text-shadow: 2px 2px 4px #000000; }}
            .stButton>button {{ width: 100%; border-radius: 10px; font-weight: bold; background-color: #2e7d32; color: white; }}
            </style>
            """, unsafe_allow_html=True)
    except: pass

agregar_fondo('1000687124.jpg')

# 4. BASE DE DATOS
conn = sqlite3.connect('iglesia_pascua_web.db', check_same_thread=False)
curr = conn.cursor()
curr.execute("CREATE TABLE IF NOT EXISTS miembros (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono TEXT, direccion TEXT)")
curr.execute("CREATE TABLE IF NOT EXISTS finanzas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, referencia TEXT, monto_ves REAL, tasa REAL, monto_usd REAL, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS materiales (id INTEGER PRIMARY KEY AUTOINCREMENT, donante TEXT, categoria TEXT, descripcion TEXT, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY AUTOINCREMENT, miembro_id INTEGER, fecha DATE)")
curr.execute("CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_persona TEXT, tipo TEXT, fecha_evento DATE, telefono TEXT)")
conn.commit()

# 5. SEGURIDAD Y SESIÓN
USUARIOS = {
    "tesorero": {"clave": "finanzas2026", "rol": "finanzas"},
    "secretario": {"clave": "iglesia2026", "rol": "asistencia"},
    "donaciones": {"clave": "pascua2026", "rol": "materiales"},
    "admin": {"clave": "pastor2026", "rol": "todos"}
}

if "sesion" not in st.session_state: st.session_state.sesion = None
if "recuperar" not in st.session_state: st.session_state.recuperar = False

# --- LOGIN ---
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
                        st.session_state.sesion = USUARIOS[u_log]["rol"]
                        st.rerun()
                    else: st.error("Usuario o clave incorrectos")
            if st.button("Olvidé mi contraseña"): 
                st.session_state.recuperar = True
                st.rerun()
        else:
            st.warning("Seguridad: ¿Nombre de la congregación?")
            preg = st.text_input("Respuesta")
            if st.button("Revelar Claves"):
                if preg.lower() == "cristo el salvador":
                    for k, v in USUARIOS.items(): st.code(f"{k}: {v['clave']}")
                else: st.error("Respuesta incorrecta")
            if st.button("Volver"): 
                st.session_state.recuperar = False
                st.rerun()
    st.stop()

# --- PANEL PRINCIPAL ---
rol = st.session_state.sesion
st.sidebar.title(f"⛪ Menú - {rol.upper()}")
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.sesion = None
    st.rerun()

# Definición dinámica de pestañas
pestanas_v = []
if rol in ["finanzas", "todos"]: pestanas_v.extend(["💰 Diezmos", "📊 Informe Tesorería"])
if rol in ["materiales", "todos"]: pestanas_v.extend(["📦 Materiales", "📋 Informe Materiales"])
if rol in ["asistencia", "todos"]: pestanas_v.extend(["👥 Registro Miembros", "📅 Tomar Asistencia", "📝 Informe Asistencia", "🎂 Cumpleaños"])
if rol == "todos": pestanas_v.extend(["📡 PASTORAL", "🛠️ Ajustes"])

tabs = st.tabs(pestanas_v)
idx = 0

# --- LÓGICA DE PESTAÑAS ---

# 1. FINANZAS
if rol in ["finanzas", "todos"]:
    with tabs[idx]:
        st.subheader("Entrada de Diezmos")
        t_auto = obtener_tasa_bcv()
        t_final = st.number_input("Tasa BCV", value=t_auto if t_auto else 55.0)
        
        with st.form("f_fin", clear_on_submit=True):
            n_f = st.text_input("Nombre del Hermano/a")
            r_f = st.text_input("Referencia")
            mv_f = st.number_input("Monto en Bolívares (VES)", min_value=0.0)
            if st.form_submit_button("💾 Guardar"):
                if n_f and mv_f > 0:
                    m_usd = mv_f / t_final
                    curr.execute("INSERT INTO finanzas (nombre, referencia, monto_ves, tasa, monto_usd, fecha) VALUES (?,?,?,?,?,?)", 
                                (n_f, r_f, mv_f, t_final, m_usd, date.today()))
                    conn.commit()
                    st.success(f"Registrado correctamente ({m_usd:.2f} USD)")
                else: st.warning("Complete los datos")
    idx += 1
    with tabs[idx]:
        st.subheader("Reporte de Finanzas")
        df_f = pd.read_sql_query("SELECT * FROM finanzas", conn)
        df_f_edit = st.data_editor(df_f, use_container_width=True, key="edit_fin", num_rows="dynamic")
        if st.button("Guardar Cambios en Reporte"):
            df_f_edit.to_sql('finanzas', conn, if_exists='replace', index=False)
            st.success("Base de datos actualizada")
        
        msg = urllib.parse.quote(f"📊 Informe: Total {df_f['monto_usd'].sum():.2f} USD")
        st.link_button("📱 Enviar por WhatsApp", f"https://wa.me/?text={msg}")
    idx += 1

# 2. MATERIALES
if rol in ["materiales", "todos"]:
    with tabs[idx]:
        st.subheader("Donaciones de Materiales")
        with st.form("f_mat", clear_on_submit=True):
            d_m = st.text_input("Nombre del Donante")
            desc_m = st.text_area("Descripción")
            if st.form_submit_button("Registrar"):
                curr.execute("INSERT INTO materiales (donante, categoria, descripcion, fecha) VALUES (?,?,?,?)", (d_m, "General", desc_m, date.today()))
                conn.commit(); st.success("Guardado")
    idx += 1
    with tabs[idx]:
        df_m = pd.read_sql_query("SELECT * FROM materiales", conn)
        st.data_editor(df_m, use_container_width=True, num_rows="dynamic")
    idx += 1

# 3. ASISTENCIA Y MIEMBROS
if rol in ["asistencia", "todos"]:
    with tabs[idx]:
        st.subheader("👥 Registro de Miembros")
        with st.form("f_mie", clear_on_submit=True):
            nm = st.text_input("Nombre Completo")
            tm = st.text_input("Teléfono")
            dm = st.text_input("Dirección")
            if st.form_submit_button("➕ Añadir"):
                curr.execute("INSERT INTO miembros (nombre, telefono, direccion) VALUES (?,?,?)", (nm, tm, dm))
                conn.commit(); st.success("Añadido")
    idx += 1
    with tabs[idx]:
        st.subheader("📅 Marcar Asistencia")
        df_l = pd.read_sql_query("SELECT id, nombre FROM miembros", conn)
        if not df_l.empty:
            with st.form("f_as", clear_on_submit=True):
                herm = st.selectbox("Hermano/a", df_l['nombre'].tolist())
                fec = st.date_input("Fecha")
                if st.form_submit_button("✅ Marcar"):
                    m_id = df_l[df_l['nombre'] == herm]['id'].values[0]
                    curr.execute("INSERT INTO asistencia (miembro_id, fecha) VALUES (?,?)", (int(m_id), fec))
                    conn.commit(); st.success("Asistencia marcada")
    idx += 1
    with tabs[idx]:
        st.subheader("📝 Reporte de Asistencia")
        df_as = pd.read_sql_query("SELECT asistencia.id, miembros.nombre, asistencia.fecha FROM asistencia JOIN miembros ON asistencia.miembro_id = miembros.id", conn)
        st.data_editor(df_as, use_container_width=True, num_rows="dynamic")
    idx += 1
 with tabs[idx]:
        st.subheader("🎂 Registro de Cumpleaños")
        
        # Formulario que se limpia solo al guardar
        with st.form("f_cu", clear_on_submit=True):
            n_c = st.text_input("Nombre del Cumpleañero")
            # Formato visual DD/MM/YYYY y rango de fecha corregido
            f_c = st.date_input("Fecha de Nacimiento", 
                               min_value=date(1900, 1, 1), 
                               max_value=date.today(),
                               format="DD/MM/YYYY") 
            t_c = st.text_input("WhatsApp para Felicitación")
            
            if st.form_submit_button("💾 Guardar"):
                if n_c:
                    curr.execute("INSERT INTO eventos (nombre_persona, tipo, fecha_evento, telefono) VALUES (?,?,?,?)", 
                                (n_c, "Cumpleaños", f_c, t_c))
                    conn.commit()
                    st.success(f"✅ ¡{n_c} registrado con éxito!")
                    st.rerun()
                else:
                    st.warning("⚠️ Por favor, introduce el nombre.")

        st.divider()
        st.subheader("📋 Lista de Cumpleaños (Selecciona y borra filas)")
        
        # Leemos los datos de la base de datos
        df_ev = pd.read_sql_query("SELECT * FROM eventos WHERE tipo='Cumpleaños'", conn)
        
        if not df_ev.empty:
            # Convertimos la fecha al formato Día/Mes/Año para que se vea bien en la tabla
            df_ev['fecha_evento'] = pd.to_datetime(df_ev['fecha_evento']).dt.strftime('%d/%m/%Y')
            
            # Editor de tabla con opción de borrar filas (num_rows="dynamic")
            df_ev_edit = st.data_editor(df_ev, use_container_width=True, num_rows="dynamic", key="editor_cumples")
            
            if st.button("🗑️ Confirmar Eliminación / Cambios"):
                # Para eliminar, el editor devuelve el dataframe sin las filas borradas
                # Guardamos de nuevo convirtiendo las fechas al formato que entiende la base de datos
                df_ev_edit['fecha_evento'] = pd.to_datetime(df_ev_edit['fecha_evento'], dayfirst=True).dt.strftime('%Y-%m-%d')
                df_ev_edit.to_sql('eventos', conn, if_exists='replace', index=False)
                st.success("✨ Base de datos actualizada correctamente.")
                st.rerun()
        else:
            st.info("No hay cumpleaños registrados aún.")


# 4. PASTOR / ADMIN
if rol == "todos":
    with tabs[idx]:
        st.header("📡 RESUMEN PASTORAL")
        c1, c2, c3 = st.columns(3)
        ing_usd = pd.read_sql_query('SELECT SUM(monto_usd) FROM finanzas', conn).iloc[0,0] or 0
        c1.metric("Ingresos (USD)", f"{ing_usd:.2f}")
        c2.metric("Total Miembros", len(pd.read_sql_query("SELECT * FROM miembros", conn)))
        c3.metric("Materiales", len(pd.read_sql_query("SELECT * FROM materiales", conn)))
    idx += 1
    with tabs[idx]:
        t_sel = st.selectbox("Gestión de Tablas", ["miembros", "finanzas", "materiales", "asistencia", "eventos"])
        df_aj = pd.read_sql_query(f"SELECT * FROM {t_sel}", conn)
        st.data_editor(df_aj, use_container_width=True, num_rows="dynamic")

