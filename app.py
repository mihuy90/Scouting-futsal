import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import base64

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN Y ESTILOS CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Scouting Futsal Pro - Análisis Táctico",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para interfaz profesional
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
    }
    .metric-card {
        background-color: #1e222d;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #2e3440;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. INICIALIZACIÓN DE VARIABLES DE SESIÓN (SESSION STATE)
# -----------------------------------------------------------------------------
if "datos" not in st.session_state:
    st.session_state.datos = pd.DataFrame(columns=[
        "Jornada", "Rival", "Fase", "Elemento", "Resultado", "X", "Y", "Jugador", "Minuto", "Notas"
    ])

if "plantilla" not in st.session_state:
    st.session_state.plantilla = ["Jugador 1", "Jugador 2", "Jugador 3", "Jugador 4", "Jugador 5"]

# -----------------------------------------------------------------------------
# 3. MOTOR GRÁFICO - PISTA DE FÚTBOL SALA (40x20m)
# -----------------------------------------------------------------------------
def dibujar_pista_futsal(df_puntos=None, modo="puntos", titulo=""):
    fig = go.Figure()

    ANCHO, ALTO = 40, 20

    # Superficie de juego
    fig.add_shape(type="rect", x0=0, y0=0, x1=ANCHO, y1=ALTO,
                  line=dict(color="white", width=2), fillcolor="#004d25")
    
    # Línea de medio campo
    fig.add_shape(type="line", x0=ANCHO/2, y0=0, x1=ANCHO/2, y1=ALTO,
                  line=dict(color="white", width=2))
    
    # Círculo central (3m de radio)
    fig.add_shape(type="circle", x0=ANCHO/2 - 3, y0=ALTO/2 - 3, x1=ANCHO/2 + 3, y1=ALTO/2 + 3,
                  line=dict(color="white", width=2))

    # Áreas de 6m
    fig.add_shape(type="path",
                  path=f"M 0,{ALTO/2 - 6} A 6 6 0 0 1 6,{ALTO/2} A 6 6 0 0 1 0,{ALTO/2 + 6}",
                  line=dict(color="white", width=2))
    fig.add_shape(type="path",
                  path=f"M {ANCHO},{ALTO/2 - 6} A 6 6 0 0 0 {ANCHO-6},{ALTO/2} A 6 6 0 0 0 {ANCHO},{ALTO/2 + 6}",
                  line=dict(color="white", width=2))

    # Marcas de penalti (6m) y doble penalti (10m)
    fig.add_trace(go.Scatter(
        x=[6, 10, 30, 34], y=[10, 10, 10, 10], mode="markers",
        marker=dict(color="white", size=5), showlegend=False, hoverinfo="skip"
    ))

    # Porterías
    fig.add_shape(type="rect", x0=-1.5, y0=ALTO/2 - 1.5, x1=0, y1=ALTO/2 + 1.5,
                  line=dict(color="white", width=2), fillcolor="rgba(255,255,255,0.2)")
    fig.add_shape(type="rect", x0=ANCHO, y0=ALTO/2 - 1.5, x1=ANCHO + 1.5, y1=ALTO/2 + 1.5,
                  line=dict(color="white", width=2), fillcolor="rgba(255,255,255,0.2)")

    # REPRESENTACIÓN DE DATOS
    if df_puntos is not None and not df_puntos.empty:
        if modo == "calor":
            fig.add_trace(go.Histogram2dContour(
                x=df_puntos["X"],
                y=df_puntos["Y"],
                colorscale="YlOrRd",
                reversescale=False,
                showscale=False,
                ncontours=20,
                opacity=0.65
            ))
            # Dibujar marcas numeradas encima del mapa de calor
            fig.add_trace(go.Scatter(
                x=df_puntos["X"],
                y=df_puntos["Y"],
                mode="markers+text",
                marker=dict(color="#00ffff", size=10, line=dict(color="black", width=1.5)),
                text=[f"#{i}" for i in df_puntos.index],
                textposition="top center",
                textfont=dict(color="white", size=10),
                hoverinfo="text",
                hovertext=[
                    f"ID: #{i} | {row['Jugador']}<br>{row['Elemento']} - {row['Resultado']}<br>Pos: ({row['X']}m, {row['Y']}m)"
                    for i, row in df_puntos.iterrows()
                ],
                showlegend=False
            ))
        else:
            colores = {"Gol": "#00ff00", "Parada": "#0099ff", "Fuera": "#ff3333", "Bloqueado": "#ff9900"}
            for res, color in colores.items():
                df_sub = df_puntos[df_puntos["Resultado"] == res]
                if not df_sub.empty:
                    fig.add_trace(go.Scatter(
                        x=df_sub["X"],
                        y=df_sub["Y"],
                        mode="markers",
                        name=res,
                        marker=dict(color=color, size=13, line=dict(color="black", width=1)),
                        text=[f"{r['Jugador']} ({r['Elemento']})" for _, r in df_sub.iterrows()],
                        hoverinfo="text"
                    ))

    fig.update_xaxes(range=[-3, ANCHO + 3], showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(range=[-2, ALTO + 2], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1)
    
    fig.update_layout(
        title=dict(text=titulo, font=dict(color="white", size=16)),
        margin=dict(l=5, r=5, t=30, b=5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(color="white"))
    )
    return fig

# -----------------------------------------------------------------------------
# 4. GENERADOR DE REPORTES COMPLETO EN PDF
# -----------------------------------------------------------------------------
class PDFReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 15)
        self.cell(0, 10, "INFORME TÁCTICO DE SCOUTING - FÚTBOL SALA", ln=True, align="C")
        self.set_font("Arial", "I", 10)
        self.cell(0, 5, "Análisis de rendimiento y mapas de tiro", ln=True, align="C")
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

def generar_pdf_completo(df):
    pdf = PDFReport()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "1. Resumen General del Partido", ln=True)
    pdf.set_font("Arial", size=10)
    
    total_tiros = len(df)
    goles = len(df[df["Resultado"] == "Gol"])
    efectividad = (goles / total_tiros * 100) if total_tiros > 0 else 0
    
    pdf.cell(0, 6, f"Total de acciones registradas: {total_tiros}", ln=True)
    pdf.cell(0, 6, f"Goles marcados: {goles}", ln=True)
    pdf.cell(0, 6, f"Efectividad de tiro: {efectividad:.1f}%", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2. Desglose por Resultado", ln=True)
    pdf.set_font("Arial", size=10)
    
    resumen_res = df["Resultado"].value_counts()
    for k, v in resumen_res.items():
        pdf.cell(0, 6, f" - {k}: {v} ({v/total_tiros*100:.1f}%)", ln=True)
        
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "3. Registro Detallado de Acciones", ln=True)
    pdf.set_font("Arial", "B", 9)
    
    # Encabezados de tabla
    pdf.cell(20, 6, "Min", 1)
    pdf.cell(35, 6, "Jugador", 1)
    pdf.cell(40, 6, "Fase", 1)
    pdf.cell(45, 6, "Elemento", 1)
    pdf.cell(30, 6, "Resultado", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=8)
    for _, row in df.iterrows():
        pdf.cell(20, 5, str(row["Minuto"]), 1)
        pdf.cell(35, 5, str(row["Jugador"])[:18], 1)
        pdf.cell(40, 5, str(row["Fase"])[:20], 1)
        pdf.cell(45, 5, str(row["Elemento"])[:22], 1)
        pdf.cell(30, 5, str(row["Resultado"]), 1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# -----------------------------------------------------------------------------
# 5. BARRA LATERAL (CONFIGURACIÓN DE PLANTILLA)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/futsal.png", width=60)
    st.title("Configuración")
    
    st.subheader("👥 Plantilla de Jugadores")
    nuevos_jugadores = st.text_area(
        "Introduce la lista de jugadores (uno por línea):",
        value="\n".join(st.session_state.plantilla),
        height=150
    )
    st.session_state.plantilla = [j.strip() for j in nuevos_jugadores.split("\n") if j.strip()]
    
    st.write("---")
    st.markdown("**Versión:** 2.5 Pro")
    st.markdown("**Motor gráfico:** Plotly Futsal Engine")

# -----------------------------------------------------------------------------
# 6. PANEL PRINCIPAL Y PESTAÑAS DE TRABAJO
# -----------------------------------------------------------------------------
st.title("⚽ Scouting & Análisis Táctico de Fútbol Sala")

tab1, tab2, tab3, tab4 = st.tabs([
    "📌 Registro de Acciones", 
    "🔥 Mapas de Calor y Borrado", 
    "📈 Estadísticas Avanzadas", 
    "📄 Reportes y PDF"
])

# -----------------------------------------------------------------------------
# PESTAÑA 1: REGISTRO DE ACCIONES EN TIEMPO REAL
# -----------------------------------------------------------------------------
with tab1:
    st.header("Registrar Acción de Juego")
    
    col_form, col_vis = st.columns([1, 2])
    
    with col_form:
        jornada = st.text_input("Partido / Jornada:", value="Jornada 1")
        rival = st.text_input("Rival:", value="Rival A")
        
        c1, c2 = st.columns(2)
        with c1:
            jugador = st.selectbox("Jugador:", st.session_state.plantilla)
            minuto = st.number_input("Minuto:", min_value=1, max_value=50, value=10)
        with c2:
            fase = st.selectbox("Fase de Juego:", ["Ataque Posicional", "Contraataque", "Balón Parado", "Portero Jugador"])
            elemento = st.selectbox("Elemento Táctico:", ["Tiro exterior", "1vs1", "Juego con Pívot", "Estrategia", "Transición", "Rechace"])
            
        resultado = st.selectbox("Resultado de la acción:", ["Gol", "Parada", "Fuera", "Bloqueado"])
        notas = st.text_input("Notas adicionales:", value="")
        
        st.write("---")
        st.markdown("**Ubicación en Pista (metros):**")
        pos_x = st.slider("Coordenada X (Largo 0-40m):", 0.0, 40.0, 20.0, step=0.5)
        pos_y = st.slider("Coordenada Y (Ancho 0-20m):", 0.0, 20.0, 10.0, step=0.5)
        
        if st.button("💾 Registrar Acción", type="primary", use_container_width=True):
            nueva_accion = pd.DataFrame([{
                "Jornada": jornada,
                "Rival": rival,
                "Fase": fase,
                "Elemento": elemento,
                "Resultado": resultado,
                "X": pos_x,
                "Y": pos_y,
                "Jugador": jugador,
                "Minuto": minuto,
                "Notas": notas
            }])
            st.session_state.datos = pd.concat([st.session_state.datos, nueva_accion], ignore_index=True)
            st.success("¡Acción guardada correctamente!")

    with col_vis:
        st.subheader("Previsualización de Posición")
        df_prev = pd.DataFrame([{"X": pos_x, "Y": pos_y, "Resultado": resultado, "Elemento": elemento, "Jugador": jugador}])
        fig_prev = dibujar_pista_futsal(df_prev, modo="puntos", titulo="Ubicación exacta")
        st.plotly_chart(fig_prev, use_container_width=True)

# -----------------------------------------------------------------------------
# PESTAÑA 2: MAPAS DE CALOR Y GESTOR INTEGRADO DE BORRADO
# -----------------------------------------------------------------------------
with tab2:
    st.header("🔥 Mapas de Densidad Táctica y Borrado")
    
    if not st.session_state.datos.empty:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            rivales = ["Todos"] + list(st.session_state.datos["Rival"].unique())
            riv_sel = st.selectbox("Filtrar por Rival:", rivales, key="f_riv")
        with col_f2:
            elementos = ["Todos"] + list(st.session_state.datos["Elemento"].unique())
            elem_sel = st.selectbox("Filtrar por Elemento:", elementos, key="f_elem")
        with col_f3:
            jugadores = ["Todos"] + list(st.session_state.datos["Jugador"].unique())
            jug_sel = st.selectbox("Filtrar por Jugador:", jugadores, key="f_jug")
            
        df_filtrado = st.session_state.datos.copy()
        if riv_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Rival"] == riv_sel]
        if elem_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Elemento"] == elem_sel]
        if jug_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Jugador"] == jug_sel]

        if not df_filtrado.empty:
            fig_calor = dibujar_pista_futsal(df_filtrado, modo="calor", titulo="Concentración de Zonas de Tiro")
            st.plotly_chart(fig_calor, use_container_width=True)
            
            # --- SECCIÓN DE BORRADO INTEGRADA ---
            st.markdown("---")
            st.subheader("🗑️ Gestor de Borrado de Puntos de la Pista")
            st.caption("Los ID con `#` coinciden con los números cian que ves en el mapa de arriba.")

            # Lista interactiva con botón de borrado directo
            for idx, row in df_filtrado.iterrows():
                with st.container():
                    col_info, col_btn = st.columns([5, 1])
                    with col_info:
                        st.markdown(
                            f"🔹 **ID #{idx}** | **{row['Jugador']}** (Min {row['Minuto']}') | "
                            f"**{row['Elemento']}** - *{row['Resultado']}* | "
                            f"Ubicación: (X: {row['X']}m, Y: {row['Y']}m) | Rival: {row['Rival']}"
                        )
                    with col_btn:
                        if st.button("🗑️ Eliminar", key=f"btn_delete_{idx}", type="secondary"):
                            st.session_state.datos = st.session_state.datos.drop(index=idx).reset_index(drop=True)
                            st.success(f"Registro #{idx} eliminado con éxito.")
                            st.rerun()
                    st.divider()

        else:
            st.warning("No hay registros que coincidan con los filtros aplicados.")
    else:
        st.info("Aún no se han registrado datos.")

# -----------------------------------------------------------------------------
# PESTAÑA 3: ESTADÍSTICAS AVANZADAS Y GRÁFICOS
# -----------------------------------------------------------------------------
with tab3:
    st.header("📈 Análisis Estadístico Avanzado")
    
    if not st.session_state.datos.empty:
        m1, m2, m3, m4 = st.columns(4)
        total_tiros = len(st.session_state.datos)
        goles = len(st.session_state.datos[st.session_state.datos["Resultado"] == "Gol"])
        paradas = len(st.session_state.datos[st.session_state.datos["Resultado"] == "Parada"])
        efectividad = (goles / total_tiros * 100) if total_tiros > 0 else 0
        
        m1.metric("Total Tiros", total_tiros)
        m2.metric("Goles", goles)
        m3.metric("Paradas Rival", paradas)
        m4.metric("Efectividad", f"{efectividad:.1f}%")
        
        st.write("---")
        g1, g2 = st.columns(2)
        
        with g1:
            st.subheader("Efectividad por Fase de Juego")
            fig_fase = px.histogram(
                st.session_state.datos, x="Fase", color="Resultado", 
                barmode="group", color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_fase.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_fase, use_container_width=True)
            
        with g2:
            st.subheader("Acciones por Jugador")
            fig_jug = px.bar(
                st.session_state.datos["Jugador"].value_counts().reset_index(),
                x="Jugador", y="count", color="Jugador"
            )
            fig_jug.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_jug, use_container_width=True)

    else:
        st.info("Registra acciones para generar analíticas automáticas.")

# -----------------------------------------------------------------------------
# PESTAÑA 4: REPORTE Y EXPORTACIÓN COMPLETA
# -----------------------------------------------------------------------------
with tab4:
    st.header("📊 Exportación y Tabla de Datos")
    
    if not st.session_state.datos.empty:
        st.dataframe(st.session_state.datos, use_container_width=True)
        
        c_exp1, c_exp2 = st.columns(2)
        
        with c_exp1:
            csv_data = st.session_state.datos.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Base de Datos (CSV)",
                data=csv_data,
                file_name="scouting_futsal_datos.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with c_exp2:
            pdf_bytes = generar_pdf_completo(st.session_state.datos)
            st.download_button(
                label="📄 Descargar Informe Completo (PDF)",
                data=pdf_bytes,
                file_name="informe_scouting_futsal.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        st.write("---")
        if st.button("⚠️ Resetear y borrar TODOS los datos acumulados", type="primary"):
            st.session_state.datos = pd.DataFrame(columns=[
                "Jornada", "Rival", "Fase", "Elemento", "Resultado", "X", "Y", "Jugador", "Minuto", "Notas"
            ])
            st.rerun()
    else:
        st.info("No hay datos cargados para exportar.")
