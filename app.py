import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import base64

# Configuración de página
st.set_page_config(page_title="Scouting Futsal Pro", layout="wide")
st.title("⚽ Scouting & Análisis Táctico - Fútbol Sala")

# Inicialización de la base de datos en la sesión activa
if "datos" not in st.session_state:
    st.session_state.datos = pd.DataFrame(columns=[
        "Rival", "Jornada", "Elemento", "Zona", "Resultado"
    ])

# --- BARRA LATERAL: ENTRADA DE DATOS MEDIANTE BOTONES ---
st.sidebar.header("📋 Registro Rápido de Partido")
rival = st.sidebar.text_input("Equipo Rival", "Rival A")
jornada = st.sidebar.number_input("Número de Partido / Jornada", min_value=1, max_value=30, value=1)

st.sidebar.subheader("Añadir Acción con 1-Clic")
elemento = st.sidebar.selectbox("Elemento de Juego", [
    "Córner a Favor", "Córner en Contra", 
    "Banda a Favor", "Banda en Contra", 
    "Contraataque", "Falta / Doble Penalti"
])

zona = st.sidebar.radio("Zona de Finalización", ["Izquierda", "Centro", "Derecha"], horizontal=True)
resultado = st.sidebar.radio("Resultado", ["Gol", "Remate a Puerta", "Remate Fuera", "Pérdida / Bloqueado"], horizontal=True)

if st.sidebar.button("➕ Registrar Acción", use_container_width=True):
    nueva_accion = pd.DataFrame([{
        "Rival": rival,
        "Jornada": f"Partido {jornada}",
        "Elemento": elemento,
        "Zona": zona,
        "Resultado": resultado
    }])
    st.session_state.datos = pd.concat([st.session_state.datos, nueva_accion], ignore_index=True)
    st.sidebar.success("¡Acción guardada correctamente!")

# --- PANEL PRINCIPAL DE VISUALIZACIÓN ---
tab1, tab2, tab3 = st.tabs(["📊 Estadísticas Acumuladas", "🔍 Partido a Partido", "📄 Exportar PDF"])

df = st.session_state.datos

# PESTAÑA 1: ACUMULADO GLOBAL
with tab1:
    st.header("Análisis Acumulado por Rival")
    if not df.empty:
        rival_sel = st.selectbox("Seleccionar Rival", df["Rival"].unique())
        df_rival = df[df["Rival"] == rival_sel]
        
        # Tarjetas Métrica
        c1, c2, c3 = st.columns(3)
        c1.metric("Acciones Analizadas", len(df_rival))
        c2.metric("Goles Totales", len(df_rival[df_rival["Resultado"] == "Gol"]))
        
        tot_remates = len(df_rival[df_rival["Resultado"].isin(["Gol", "Remate a Puerta"])])
        efectividad = round((tot_remates / len(df_rival)) * 100, 1) if len(df_rival) > 0 else 0
        c3.metric("% Efectividad en Tiro", f"{efectividad}%")
        
        # Gráficos Dinámicos
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig1 = px.histogram(df_rival, x="Elemento", color="Resultado", 
                                title="Eficiencia por Elemento de Juego", barmode="group",
                                color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_g2:
            fig2 = px.histogram(df_rival, x="Zona", color="Resultado", 
                                title="Peligro por Zonas de la Pista", barmode="group",
                                color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig2, use_container_width=True)
            
        st.subheader("Registro Completo de Datos")
        st.dataframe(df_rival, use_container_width=True)
    else:
        st.info("Aún no has introducido datos. Utiliza el panel izquierdo para añadir acciones.")

# PESTAÑA 2: PARTIDO INDIVIDUAL
with tab2:
    st.header("Estadísticas Individuales por Encuentro")
    if not df.empty:
        partido_sel = st.selectbox("Seleccionar Partido a Filtrar", df["Jornada"].unique())
        df_partido = df[df["Jornada"] == partido_sel]
        
        fig_p = px.bar(df_partido, x="Elemento", color="Resultado", title=f"Rendimiento en {partido_sel}")
        st.plotly_chart(fig_p, use_container_width=True)
        st.table(df_partido)
    else:
        st.info("No hay datos para mostrar.")

# PESTAÑA 3: DESCARGA PDF
with tab3:
    st.header("Generar Reporte Completo en PDF")
    if not df.empty:
        if st.button("📥 Descargar Reporte en PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, txt="Informe Táctico de Scouting - Fútbol Sala", ln=True, align='C')
            pdf.set_font("Arial", size=11)
            pdf.ln(5)
            pdf.cell(190, 8, txt=f"Equipo Analizado: {rival}", ln=True)
            pdf.cell(190, 8, txt=f"Total Acciones Registradas: {len(df)}", ln=True)
            pdf.ln(8)
            
            # Encabezado Tabla PDF
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(45, 8, "Elemento", 1)
            pdf.cell(35, 8, "Zona", 1)
            pdf.cell(50, 8, "Resultado", 1)
            pdf.cell(40, 8, "Jornada", 1)
            pdf.ln()
            
            # Datos
            pdf.set_font("Arial", size=9)
            for _, row in df.iterrows():
                pdf.cell(45, 8, str(row['Elemento']), 1)
                pdf.cell(35, 8, str(row['Zona']), 1)
                pdf.cell(50, 8, str(row['Resultado']), 1)
                pdf.cell(40, 8, str(row['Jornada']), 1)
                pdf.ln()
                
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="Informe_Scouting_{rival}.pdf" style="font-size:16px; font-weight:bold; color:#2563eb;">👉 Pincha aquí para guardar el PDF</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.warning("Necesitas añadir al menos una acción para poder exportar el PDF.")
