import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
from fpdf import FPDF

st.set_page_config(page_title="Scouting Futsal Pro", layout="wide")
st.title("⚽ Scouting & Análisis Táctico - Fútbol Sala")

# 1. Base de datos local en la sesión
if "datos" not in st.session_state:
    st.session_state.datos = pd.DataFrame(columns=[
        "Rival", "Jornada", "Elemento", "Zona", "Resultado", "X", "Y"
    ])

# Función para dibujar la pista de fútbol sala (40m x 20m)
def dibujar_pista(df_puntos=None, mostrar_calor=False):
    fig = go.Figure()
    
    # Capa de Mapa de Calor (Si aplica)
    if mostrar_calor and df_puntos is not None and not df_puntos.empty:
        fig.add_trace(go.Histogram2dContour(
            x=df_puntos["X"],
            y=df_puntos["Y"],
            colorscale="Hot",
            reversescale=True,
            showscale=True,
            opacity=0.75,
            ncontours=15,
            contours=dict(coloring='heatmap')
        ))

    # Formas de la pista
    shapes = [
        # Perímetro / Fondo del campo
        dict(type="rect", x0=0, y0=0, x1=40, y1=20, line=dict(color="white", width=3), fillcolor="#1e3a8a" if not mostrar_calor else "rgba(30,58,138,0.3)"),
        # Línea central
        dict(type="line", x0=20, y0=0, x1=20, y1=20, line=dict(color="white", width=2)),
        # Círculo central
        dict(type="circle", x0=17, y0=7, x1=23, y1=13, line=dict(color="white", width=2)),
        # Punto central
        dict(type="circle", x0=19.8, y0=9.8, x1=20.2, y1=10.2, line=dict(color="white"), fillcolor="white"),
        # Área 6m Izquierda
        dict(type="rect", x0=0, y0=4, x1=6, y1=16, line=dict(color="white", width=2, dash="dash")),
        # Área 6m Derecha
        dict(type="rect", x0=34, y0=4, x1=40, y1=16, line=dict(color="white", width=2, dash="dash")),
        # Portería Izquierda
        dict(type="rect", x0=0, y0=8.5, x1=0.8, y1=11.5, line=dict(color="yellow", width=2), fillcolor="rgba(255,255,0,0.3)"),
        # Portería Derecha
        dict(type="rect", x0=39.2, y0=8.5, x1=40, y1=11.5, line=dict(color="yellow", width=2), fillcolor="rgba(255,255,0,0.3)"),
    ]
    
    # Añadir puntos registrados si existen y NO es solo mapa de calor
    if df_puntos is not None and not df_puntos.empty and not mostrar_calor:
        color_map = {
            "Gol": "#22c55e", 
            "Remate a Puerta": "#3b82f6", 
            "Remate Fuera": "#f97316", 
            "Pérdida / Bloqueado": "#ef4444"
        }
        for res in df_puntos["Resultado"].unique():
            df_sub = df_puntos[df_puntos["Resultado"] == res]
            fig.add_trace(go.Scatter(
                x=df_sub["X"],
                y=df_sub["Y"],
                mode="markers",
                name=res,
                marker=dict(size=14, color=color_map.get(res, "white"), symbol="circle", line=dict(width=1.5, color="black")),
                hovertext=df_sub["Elemento"]
            ))

    fig.update_layout(
        shapes=shapes,
        xaxis=dict(range=[0, 40], showgrid=False, zeroline=False, visible=False, fixedrange=True),
        yaxis=dict(range=[0, 20], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1, fixedrange=True),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=420,
        showlegend=not mostrar_calor
    )
    return fig

# --- PANEL LATERAL ---
st.sidebar.header("📋 Opciones de Registro")
rival = st.sidebar.text_input("Equipo Rival", "Poio")
jornada = st.sidebar.number_input("Partido / Jornada", min_value=1, max_value=30, value=1)

st.sidebar.markdown("---")
st.sidebar.subheader("1. Elemento de Juego")
elemento = st.sidebar.radio(
    "Elemento:",
    [
        "Córner a Favor", "Córner en Contra", 
        "Banda a Favor", "Banda en Contra", 
        "Contraataque", "Falta Directa", 
        "Doble Penalti", "Penalti", "Juego Continuo / Tiro"
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("2. Resultado")
resultado = st.sidebar.radio("Resultado", ["Gol", "Remate a Puerta", "Remate Fuera", "Pérdida / Bloqueado"])

st.sidebar.info("💡 **Instrucción:** Elige las opciones de la izquierda y **HAZ CLIC en el campo** para guardar la posición.")

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Registrador Interactivo", "🔥 Mapa de Calor", "📊 Estadísticas Acumuladas", "📄 Exportar PDF"])

# PESTAÑA 1: REGISTRO INTERACTIVO CON CLIC
with tab1:
    st.header(f"🎯 Registro de tiros contra: {rival}")
    
    # Obtener eventos guardados para el rival actual
    df_actual = st.session_state.datos
    df_rival = df_actual[df_actual["Rival"] == rival] if not df_actual.empty else pd.DataFrame()
    
    fig_pista = dibujar_pista(df_puntos=df_rival, mostrar_calor=False)

    # Capturar el clic del usuario sobre el gráfico
    selected_points = plotly_events(fig_pista, click_event=True, key="pista_clicks")
    
    if selected_points:
        click_x = round(selected_points[0]["x"], 1)
        click_y = round(selected_points[0]["y"], 1)
        
        # Determinar zona cualitativa según coordenada Y
        zona_auto = "Centro"
        if click_y < 6.5: 
            zona_auto = "Derecha"
        elif click_y > 13.5: 
            zona_auto = "Izquierda"
        
        # Crear nuevo registro
        nueva_accion = pd.DataFrame([{
            "Rival": rival,
            "Jornada": f"Partido {jornada}",
            "Elemento": elemento,
            "Zona": zona_auto,
            "Resultado": resultado,
            "X": click_x,
            "Y": click_y
        }])
        
        # Añadir al estado global y recargar la app
        st.session_state.datos = pd.concat([st.session_state.datos, nueva_accion], ignore_index=True)
        st.success(f"✅ Accion guardada: {elemento} ({resultado}) en [{click_x}m, {click_y}m]")
        st.rerun()

# PESTAÑA 2: MAPA DE CALOR ACUMULADO
with tab2:
    st.header("🔥 Mapa de Calor Acumulado")
    df_totales = st.session_state.datos
    
    if not df_totales.empty:
        rivales_disponibles = df_totales["Rival"].unique()
        rival_sel = st.selectbox("Seleccionar Rival para visualizar:", rivales_disponibles, key="mapa_rival")
        
        df_mapa = df_totales[df_totales["Rival"] == rival_sel]
        
        if not df_mapa.empty:
            fig_calor = dibujar_pista(df_puntos=df_mapa, mostrar_calor=True)
            st.plotly_chart(fig_calor, use_container_width=True)
        else:
            st.warning("No hay datos registrados para este rival.")
    else:
        st.info("Aún no se ha registrado ningún tiro. Ve a la pestaña 'Registrador Interactivo' y haz clic en el campo.")

# PESTAÑA 3: ESTADÍSTICAS
with tab3:
    st.header("📊 Estadísticas Acumuladas")
    df_totales = st.session_state.datos
    
    if not df_totales.empty:
        rival_sel2 = st.selectbox("Seleccionar Rival:", df_totales["Rival"].unique(), key="acum_rival")
        df_rival2 = df_totales[df_totales["Rival"] == rival_sel2]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Acciones", len(df_rival2))
        c2.metric("Goles", len(df_rival2[df_rival2["Resultado"] == "Gol"]))
        
        tot_remates = len(df_rival2[df_rival2["Resultado"].isin(["Gol", "Remate a Puerta"])])
        efectividad = round((tot_remates / len(df_rival2)) * 100, 1) if len(df_rival2) > 0 else 0
        c3.metric("% Efectividad Tiro", f"{efectividad}%")
        
        st.markdown("### Tabla detallada de acciones")
        st.dataframe(df_rival2, use_container_width=True)
    else:
        st.info("No hay datos estadísticos aún.")

# PESTAÑA 4: PDF
with tab4:
    st.header("📄 Generar PDF")
    df_totales = st.session_state.datos
    
    if not df_totales.empty:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, txt="Informe Táctico de Scouting - Fútbol Sala", ln=True, align='C')
        pdf.set_font("Arial", size=11)
        pdf.ln(5)
        pdf.cell(190, 8, txt=f"Equipo Analizado: {rival}", ln=True)
        pdf.cell(190, 8, txt=f"Total Acciones Registradas: {len(df_totales)}", ln=True)
        pdf.ln(8)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(45, 8, "Elemento", 1)
        pdf.cell(40, 8, "Resultado", 1)
        pdf.cell(30, 8, "Posicion (X,Y)", 1)
        pdf.cell(35, 8, "Jornada", 1)
        pdf.ln()
        
        pdf.set_font("Arial", size=9)
        for _, row in df_totales.iterrows():
            pdf.cell(45, 8, str(row['Elemento']), 1)
            pdf.cell(40, 8, str(row['Resultado']), 1)
            pdf.cell(30, 8, f"{row['X']}m, {row['Y']}m", 1)
            pdf.cell(35, 8, str(row['Jornada']), 1)
            pdf.ln()
            
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        
        st.download_button(
            label="📥 Descargar Reporte en PDF",
            data=pdf_bytes,
            file_name=f"Informe_Scouting_{rival}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.info("No hay datos para exportar a PDF.")
