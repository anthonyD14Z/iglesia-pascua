import streamlit as st
import pandas as pd
from datetime import datetime
import pybcv  # <--- Librería para la tasa oficial

# --- INICIO DEL PROGRAMA ---
st.set_page_config(page_title="Iglesia")
bcv = pybcv.PyBCV() #linea 8 corregida

# Función para obtener la tasa automáticamente
def obtener_tasa_bcv():
    try:
        # Obtenemos la tasa del Dólar directamente del BCV
        tasa = bcv.get_rate(currency_code='USD')
        return float(tasa)
    except:
        return 45.0  # Valor por defecto si falla el internet

# Guardamos la tasa en el estado de la sesión para que no consulte la web a cada segundo
if 'tasa_dia' not in st.session_state:
    st.session_state.tasa_dia = obtener_tasa_bcv()

# ... (Aquí va tu lógica de login que ya tenemos) ...

# --- DENTRO DE LA PESTAÑA DE REGISTRO ---
with tab1:
    st.subheader("📝 Nuevo Registro")
    
    # Indicador visual de la tasa actual
    st.success(f"📌 **Tasa BCV del día:** {st.session_state.tasa_dia} Bs/$")
    
    with st.form("registro"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del Hermano/a")
            tipo = st.selectbox("Tipo", ["Diezmo", "Ofrenda", "Donación"])
        with col2:
            monto_bs = st.number_input("Monto en Bolívares", min_value=0.0)
            # La tasa ya viene precargada pero se puede editar si es necesario
            tasa_usada = st.number_input("Confirmar Tasa", value=st.session_state.tasa_dia)
            
        if st.form_submit_button("Guardar"):
            # Lógica de guardado...
            pass
