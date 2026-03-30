import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Cambia esto por la contraseña que quieras
USUARIO_ADMIN = "admin"
CLAVE_ADMIN = "pascua2026" 

def login():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.title("🔒 Acceso Privado - Iglesia")
        usuario = st.text_input("Usuario")
        clave = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if usuario == USUARIO_ADMIN and clave == CLAVE_ADMIN:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
        return False
    return True

# --- INICIO DE LA APP SI ESTÁ LOGUEADO ---
if login():
    st.set_page_config(page_title="Iglesia - Gestión", layout="wide")
    
    st.title("⛪ Llamados a ser Diferentes")
    st.subheader("Gestión de Diezmos y Ofrendas - Valle de la Pascua")

    # Inicializar base de datos en la memoria
    if 'datos' not in st.session_state:
        st.session_state.datos = []

    tab1, tab2 = st.tabs(["📝 Registro Nuevo", "📊 Reporte del Día"])

    with tab1:
        st.markdown("### Ingrese los datos del aporte")
        
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del Hermano/a")
            tipo = st.selectbox("Tipo de Aporte", ["Diezmo", "Ofrenda", "Donación Especial"])
            metodo = st.selectbox("Método de Pago", ["Efectivo $", "Efectivo Bs", "Transferencia", "Pago Móvil"])
        
        with col2:
            monto_bs = st.number_input("Monto en Bolívares (Bs)", min_value=0.0, step=0.1)
            tasa = st.number_input("Tasa BCV del día", min_value=1.0, value=45.0)
            # --- NUEVO CAMPO DE REFERENCIA ---
            referencia = st.text_input("Número de Referencia (Si aplica)", help="Últimos 4 o 6 dígitos de la transferencia")

        if st.button("💾 Guardar en Base de Datos"):
            if nombre and monto_bs > 0:
                monto_usd = round(monto_bs / tasa, 2)
                nuevo_registro = {
                    "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Hermano": nombre,
                    "Tipo": tipo,
                    "Método": metodo,
                    "Referencia": referencia if referencia else "N/A",
                    "Monto Bs": monto_bs,
                    "Tasa": tasa,
                    "Monto USD": monto_usd
                }
                st.session_state.datos.append(nuevo_registro)
                st.success(f"✅ Registro de {nombre} guardado con éxito.")
            else:
                st.warning("⚠️ Por favor ingrese el nombre y el monto.")

    with tab2:
        st.markdown("### Reporte Detallado")
        if st.session_state.datos:
            df = pd.DataFrame(st.session_state.datos)
            st.table(df)
            
            total_bs = df["Monto Bs"].sum()
            total_usd = df["Monto USD"].sum()
            
            st.metric("Total Recaudado (Bs)", f"{total_bs:,.2f} Bs")
            st.metric("Total Recaudado (USD)", f"{total_usd:,.2f} $")
            
            # Botón de WhatsApp
            texto_wa = f"Resumen de Iglesia: Total {total_bs} Bs ({total_usd} $). Referencias registradas."
            link_wa = f"https://wa.me/?text={texto_wa.replace(' ', '%20')}"
            st.markdown(f'[📲 Enviar Reporte por WhatsApp]({link_wa})')
        else:
            st.info("Aún no hay registros el día de hoy.")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()
