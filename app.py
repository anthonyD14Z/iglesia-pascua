import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURACIÓN INICIAL Y SESIÓN ---
# Estos valores son los "de fábrica" si la app se reinicia.
USUARIO_BASE = "admin"
CLAVE_BASE = "pascua2026"
PREGUNTA_SEGURIDAD = "¿Cuál es el nombre de la iglesia?"
RESPUESTA_CORRECTA = "Llamados a ser Diferentes"

# Inicializar estados globales si no existen
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = USUARIO_BASE
if 'clave_actual' not in st.session_state:
    st.session_state.clave_actual = CLAVE_BASE
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'mostrar_recuperacion' not in st.session_state:
    st.session_state.mostrar_recuperacion = False
if 'datos' not in st.session_state:
    st.session_state.datos = []

# --- 2. FUNCIÓN DE LOGIN ---
def login():
    if not st.session_state.autenticado:
        st.title("🔒 Acceso Privado - Iglesia")
        
        usuario_input = st.text_input("Usuario")
        clave_input = st.text_input("Contraseña", type="password")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Entrar"):
                if usuario_input == st.session_state.usuario_actual and clave_input == st.session_state.clave_actual:
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
        
        with col2:
            if st.button("¿Olvidaste tus datos?"):
                st.session_state.mostrar_recuperacion = not st.session_state.mostrar_recuperacion

        # Sección de recuperación (se activa al olvidar datos)
        if st.session_state.mostrar_recuperacion:
            st.divider()
            st.warning(f"**Recuperación:** {PREGUNTA_SEGURIDAD}")
            respuesta = st.text_input("Escribe la respuesta secreta")
            
            if st.button("Verificar Respuesta"):
                if respuesta.lower().strip() == RESPUESTA_CORRECTA.lower().strip():
                    st.info(f"✅ Credenciales actuales:\n- Usuario: **{st.session_state.usuario_actual}**\n- Clave: **{st.session_state.clave_actual}**")
                else:
                    st.error("Respuesta incorrecta")
        return False
    return True

# --- 3. CUERPO PRINCIPAL DE LA APP ---
if login():
    st.set_page_config(page_title="Iglesia - Gestión", layout="wide")
    
    st.sidebar.title("Menú")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    st.title("⛪ Llamados a ser Diferentes")
    st.subheader("Gestión de Diezmos y Ofrendas - Valle de la Pascua")

    # Definición de pestañas (Tabs)
    tab1, tab2, tab3 = st.tabs(["📝 Registro Nuevo", "📊 Reporte del Día", "⚙️ Configuración"])

    # TAB 1: REGISTRO
    with tab1:
        st.markdown("### Ingrese los datos del aporte")
        col_a, col_b = st.columns(2)
        
        with col_a:
            nombre = st.text_input("Nombre del Hermano/a")
            tipo = st.selectbox("Tipo de Aporte", ["Diezmo", "Ofrenda", "Donación Especial"])
            metodo = st.selectbox("Método de Pago", ["Efectivo $", "Efectivo Bs", "Transferencia", "Pago Móvil"])
        
        with col_b:
            monto_bs = st.number_input("Monto en Bolívares (Bs)", min_value=0.0, step=0.1)
            tasa = st.number_input("Tasa BCV del día", min_value=1.0, value=45.0)
            referencia = st.text_input("Número de Referencia", help="Últimos dígitos de la transferencia")

        if st.button("💾 Guardar Registro"):
            if nombre and monto_bs > 0:
                monto_usd = round(monto_bs / tasa, 2)
                nuevo = {
                    "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Hermano": nombre,
                    "Tipo": tipo,
                    "Método": metodo,
                    "Referencia": referencia if referencia else "N/A",
                    "Monto Bs": monto_bs,
                    "Tasa": tasa,
                    "Monto USD": monto_usd
                }
                st.session_state.datos.append(nuevo)
                st.success(f"✅ Registro de {nombre} guardado.")
            else:
                st.warning("⚠️ Complete nombre y monto.")

    # TAB 2: REPORTE
    with tab2:
        st.markdown("### Reporte Detallado")
        if st.session_state.datos:
            df = pd.DataFrame(st.session_state.datos)
            st.dataframe(df, use_container_width=True)
            
            t_bs = df["Monto Bs"].sum()
            t_usd = df["Monto USD"].sum()
            
            m1, m2 = st.columns(2)
            m1.metric("Total Bs", f"{t_bs:,.2f}")
            m2.metric("Total USD", f"{t_usd:,.2f}")
            
            texto_wa = f"Resumen Iglesia: Total {t_bs} Bs ({t_usd} $)."
            link_wa = f"https://wa.me/?text={texto_wa.replace(' ', '%20')}"
            st.markdown(f'[📲 Enviar por WhatsApp]({link_wa})')
        else:
            st.info("No hay registros hoy.")

    # TAB 3: CONFIGURACIÓN (CAMBIO DE CLAVE)
    with tab3:
        st.markdown("### 🔐 Cambiar Credenciales")
        new_user = st.text_input("Nuevo Usuario Admin", value=st.session_state.usuario_actual)
        new_pass = st.text_input("Nueva Contraseña", type="password")
        conf_pass = st.text_input("Confirmar Contraseña", type="password")
        
        if st.button("Guardar Nuevas Credenciales"):
            if new_pass == conf_pass and new_pass != "":
                st.session_state.usuario_actual = new_user
                st.session_state.clave_actual = new_pass
                st.success("✅ Datos actualizados. Se usarán en su próximo inicio de sesión.")
            else:
                st.error("Las contraseñas no coinciden o están vacías.")

