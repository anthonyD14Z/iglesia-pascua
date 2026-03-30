import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import urllib.parse

# Configuración visual de la pestaña del navegador
st.set_page_config(page_title="Iglesia - Llamados a ser Diferentes", page_icon="⛪")

# --- CONEXIÓN A BASE DE DATOS ---
# Creamos la base de datos en el servidor de la nube
def conectar():
    conn = sqlite3.connect('iglesia_pascua_web.db', check_same_thread=False)
    return conn

conn = conectar()
curr = conn.cursor()
# Creamos la tabla de finanzas si no existe
curr.execute('''CREATE TABLE IF NOT EXISTS finanzas 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, 
                 monto_ves REAL, tasa REAL, monto_usd REAL, fecha DATE)''')
conn.commit()

# --- ESTILOS Y TÍTULO ---
st.title("⛪ Llamados a ser Diferentes")
st.markdown("### Gestión de Diezmos y Ofrendas - Valle de la Pascua")
st.divider()

# Creamos pestañas para organizar la app
tab1, tab2 = st.tabs(["💰 Registro Nuevo", "📊 Reporte del Día"])

with tab1:
    st.write("#### Ingrese los datos del aporte")
    
    nombre = st.text_input("Nombre del Hermano/a")
    
    col1, col2 = st.columns(2)
    with col1:
        monto_ves = st.number_input("Monto en Bolívares (VES)", min_value=0.0, step=10.0, format="%.2f")
    with col2:
        tasa = st.number_input("Tasa BCV del día", min_value=1.0, value=45.0, step=0.1)
    
    if st.button("💾 Guardar en Base de Datos", use_container_width=True):
        if nombre and monto_ves > 0:
            monto_usd = monto_ves / tasa
            curr.execute("INSERT INTO finanzas (nombre, monto_ves, tasa, monto_usd, fecha) VALUES (?,?,?,?,?)",
                         (nombre, monto_ves, tasa, monto_usd, date.today()))
            conn.commit()
            st.success(f"¡Excelente! Se registró a **{nombre}** con un total de **${monto_usd:.2f}**")
            st.balloons() # ¡Efecto de celebración!
        else:
            st.error("⚠️ Por favor, escribe el nombre y el monto antes de guardar.")

with tab2:
    st.write(f"#### Movimientos de hoy: {date.today()}")
    
    # Leemos los datos guardados hoy
    query = f"SELECT nombre as 'Nombre', monto_ves as 'Bolívares', monto_usd as 'Dólares' FROM finanzas WHERE fecha = '{date.today()}'"
    df = pd.read_sql_query(query, conn)
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        # Cálculos de totales
        total_ves = df['Bolívares'].sum()
        total_usd = df['Dólares'].sum()
        
        st.divider()
        st.metric(label="Total Recaudado (VES)", value=f"{total_ves:,.2f} BS")
        st.metric(label="Total Recaudado (USD)", value=f"${total_usd:,.2f}")
        
        # --- BOTÓN DE WHATSAPP ---
        mensaje = (f"⛪ *REPORTE LLAMADOS A SER DIFERENTES*\n"
                   f"📅 *Fecha:* {date.today()}\n"
                   f"--------------------------\n"
                   f"💰 *Total VES:* {total_ves:,.2f}\n"
                   f"💵 *Total USD:* ${total_usd:,.2f}\n"
                   f"--------------------------\n"
                   f"¡Dios bendiga cada siembra! 🙌")
        
        # Codificamos el mensaje para que WhatsApp lo entienda
        texto_url = urllib.parse.quote(mensaje)
        url_wa = f"https://wa.me/?text={texto_url}"
        
        st.link_button("📲 Enviar Reporte por WhatsApp", url_wa, use_container_width=True)
    else:
        st.info("Aún no hay registros guardados el día de hoy.")

# Cerramos conexión al final
conn.close()
