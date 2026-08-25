import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import base64

# Configuración de página
st.set_page_config(page_title="Scouting Futsal Pro", layout="wide")
st.title("⚽ Scouting & Análisis Táctico - Fútbol Sala")

# Inicialización de la base de datos
if "datos" not in st.session_state:
    st.session_state.datos = pd.DataFrame(columns=[
        "Rival", "Jornada", "Elemento", "Zona", "Resultado", "X", "Y"
    ])

# Función para dibujar una pista de fútbol sala profesional en Plotly (40m x 20m)
def dibujar_pista():
    fig = go.Figure()
    
    # Líneas del campo (40m largo x 20m ancho)
    lines = [
        # Perímetro
        dict(type="rect", x0=0, y0=0, x1=40, y1=20, line=dict(color="white", width=2)),
        # Línea central
        dict(type="line", x0=20, y0=0, x1=20, y1=20, line=dict(color="white", width=2)),
        # Círculo central (radio 3m)
        dict(type="circle", x0=17, y0=7, x1=23, y1=13, line=dict(color="white", width=2)),
        # Área 6m Izquierda (Defensa)
        dict(type="rect", x0=0, y0=4, x1=6, y1=16, line=dict(color="white", width=1.5, dash="dash")),
        # Área 6m Derecha (Ataque)
        dict(type="rect", x0=34, y0=4, x1=40, y1=16, line=dict(color="white", width=1.5, dash="dash")),
        # Porterías (3m de ancho)
        dict(type="rect", x0=-1.5, y0=8.5, x1=0, y1=11.5, line=dict(color="yellow", width=3), fillcolor="rgba(255,255,0,0.2)"),
        dict(type="rect", x0=40, y0=8.5, x1=41.5, y1=11.5, line=dict(color="yellow", width=3), fillcolor="rgba(255,255,0,0.2)"),
    ]
    
    fig.update_layout(
        shapes=lines,
        xaxis=dict(range=[-2, 42], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[-1, 21], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
        plot_bgcolor="#1e3a8a", # Fondo azul pista
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        height=420,
        title="Pista Táctica (40m x 20m)"
    )
    return fig

# --- BARRA LATERAL: REGISTRO RÁPIDO ---
st.sidebar.header("📋 Registro Rápido de Partido")
rival = st.sidebar.text_input("Equipo Rival", "Poio")
jornada = st.sidebar.number_input("Número de Partido / Jornada", min_value=1, max_value=30, value=1)

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
st.sidebar.subheader("2. Ubicación en Pista (Metros)")
col_x, col_y = st.sidebar.columns(2)
x_pos = col_x.slider("Distancia Largo (X)", 0.0, 40.0, 32.0, help="40m es la portería a la que tiran")
y_pos = col_y.slider("Ancho Pista (Y)", 0.0, 20.0, 10.0, help="10m es el centro exacto")

st.sidebar.markdown("---")
st.sidebar.subheader("3. Resultado de la Acción")
resultado = st.sidebar.radio("Resultado", ["Gol", "Remate a Puerta", "Remate Fuera", "Pérdida / Bloqueado"])

st.sidebar.markdown("---")
if st.sidebar.button("➕ Registrar Accion y Tiro", use_container_width=True):
    zona_auto = "Centro"
    if y_pos < 6.5: zona_auto = "Derecha"
    elif y_pos > 13.5: zona_auto = "Izquierda"
    
    nueva_accion = pd.DataFrame([{
        "Rival": rival,
        "Jornada": f"Partido {jornada}",
        "Elemento": elemento,
        "Zona": zona_auto,
        "Resultado": resultado,
        "X": x_pos,
        "Y": y_pos
    }])
    st.session_state.datos = pd.concat([st.session_state.datos, nueva_accion], ignore_index=True)
    st.sidebar.success(f"¡Tiro registrado a {x_pos}m de distancia!")

# --- PANEL PRINCIPAL DE VISUALIZACIÓN ---
tab1, tab2, tab3, tab4 = st.tabs(["🔥 Mapa de Calor & Tiros", "📊 Estadísticas Acumuladas", "🔍 Partido a Partido", "📄 Exportar PDF"])

df = st.session_state.datos

# PESTAÑA 1: MAPA DE CALOR Y TIROS
with tab1:
    st.header("🎯 Mapa de Calor y Ubicación de Disparos")
    if not df.empty:
        rival_sel = st.selectbox("Seleccionar Rival para el Mapa", df["Rival"].unique(), key="mapa_rival")
        df_rival = df[df["Rival"] == rival_sel]
        
        tipo_mapa = st.radio("Modo de Visualización", ["Mapa de Calor (Densidad)", "Puntos de Tiro por Resultado"], horizontal=True)
        
        fig_pista = dibujar_pista()
        
        if tipo_mapa == "Mapa de Calor (Densidad)":
            fig_pista.add_trace(go.Histogram2dContour(
                x=df_rival["X"],
                y=df_rival["Y"],
                colorscale="Hot",
                reversescale=True,
                showscale=True,
                opacity=0.75,
                name="Frecuencia"
            ))
        else:
            color_map = {"Gol": "#22c55e", "Remate a Puerta": "#3b82f6", "Remate Fuera": "#f97316", "Pérdida / Bloqueado": "#ef4444"}
            for res in df_rival["Resultado"].unique():
                df_sub = df_rival[df_rival["Resultado"] == res]
                fig_pista.add_trace(go.Scatter(
                    x=df_sub["X"],
                    y=df_sub["Y"],
                    mode="markers",
                    name=res,
                    marker=dict(size=14, color=color_map.get(res, "white"), symbol="circle", line=dict(width=1, color="black")),
                    hovertext=df_sub["Elemento"]
                ))
        
        st.plotly_chart(fig_pista, use_container_width=True)
    else:
        st.info("Utiliza el panel izquierdo para añadir tiros y se generará el mapa sobre la pista automáticamente.")

# PESTAÑA 2: ACUMULADO
with tab2:
    st.header("Análisis Acumulado por Rival")
    if not df.empty:
        rival_sel2 = st.selectbox("Seleccionar Rival", df["Rival"].unique(), key="acum_rival")
        df_rival2 = df[df["Rival"] == rival_sel2]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Acciones Analizadas", len(df_rival2))
        c2.metric("Goles Totales", len(df_rival2[df_rival2["Resultado"] == "Gol"]))
        
        tot_remates = len(df_rival2[df_rival2["Resultado"].isin(["Gol", "Remate a Puerta"])])
        efectividad = round((tot_remates / len(df_rival2)) * 100, 1) if len(df_rival2) > 0 else 0
        c3.metric("% Efectividad en Tiro", f"{efectividad}%")
        
        st.subheader("Registro de Datos")
        st.dataframe(df_rival2, use_container_width=True)

# PESTAÑA 3: PARTIDO INDIVIDUAL
with tab3:
    st.header("Estadísticas Individuales por Encuentro")
    if not df.empty:
        partido_sel = st.selectbox("Seleccionar Partido a Filtrar", df["Jornada"].unique())
        df_partido = df[df["Jornada"] == partido_sel]
        st.table(df_partido)

# PESTAÑA 4: PDF
with tab4:
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
            
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(45, 8, "Elemento", 1)
            pdf.cell(40, 8, "Resultado", 1)
            pdf.cell(30, 8, "Ubicación (X,Y)", 1)
            pdf.cell(35, 8, "Jornada", 1)
            pdf.ln()
            
            pdf.set_font("Arial", size=9)
            for _, row in df.iterrows():
                pdf.cell(45, 8, str(row['Elemento']), 1)
                pdf.cell(40, 8, str(row['Resultado']), 1)
                pdf.cell(30, 8, f"{row['X']}m, {row['Y']}m", 1)
                pdf.cell(35, 8, str(row['Jornada']), 1)
                pdf.ln()
                
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="Informe_Scouting_{rival}.pdf" style="font-size:16px; font-weight:bold; color:#2563eb;">👉 Pincha aquí para guardar el PDF</a>'
            st.markdown(href, unsafe_allow_html=True)
