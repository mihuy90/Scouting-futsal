import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF

st.set_page_config(page_title="Scouting Futsal Pro", layout="wide")
st.title("⚽ Scouting & Análisis Táctico - Fútbol Sala")

# 1. Base de datos local
if "datos" not in st.session_state:
    st.session_state.datos = pd.DataFrame(columns=[
        "Rival", "Jornada", "Elemento", "Zona", "Resultado", "X", "Y"
    ])

# DICCIONARIO DE COLORES Y ESTILOS
COLOR_MAP = {
    "Gol": "#ef4444",               # Rojo vivo
    "Remate a Puerta": "#facc15",    # Amarillo potente
    "Remate Fuera": "#ffffff",     # Blanco puro
    "Pérdida / Bloqueado": "#fb923c" # Naranja brillante
}

# Colores con transparencia para el aura/halo de calor
AURA_MAP = {
    "Gol": "rgba(239, 68, 68, 0.35)",
    "Remate a Puerta": "rgba(250, 204, 21, 0.35)",
    "Remate Fuera": "rgba(255, 255, 255, 0.25)",
    "Pérdida / Bloqueado": "rgba(251, 146, 60, 0.3)"
}

SYMBOL_MAP = {
    "Gol": "star",
    "Remate a Puerta": "circle",
    "Remate Fuera": "circle",
    "Pérdida / Bloqueado": "x"
}

# Tamaños ajustados (un poco más pequeños y estilizados)
SIZE_MAP = {
    "Gol": 16,
    "Remate a Puerta": 13,
    "Remate Fuera": 11,
    "Pérdida / Bloqueado": 11
}

# Función para dibujar la pista oficial
def dibujar_pista(df_puntos=None, modo="limpio"):
    fig = go.Figure()

    # 1. CAPA BASE DE LA PISTA (Rectángulo Azul)
    fig.add_shape(
        type="rect", x0=0, y0=0, x1=40, y1=20, 
        line=dict(color="white", width=3), 
        fillcolor="#1e3a8a", 
        layer="below"
    )

    # 2. REJILLA INVISIBLE PARA CAPTURAR EL CLIC DEL RATÓN
    grid_x = [x * 0.5 for x in range(81)]
    grid_y = [y * 0.5 for y in range(41)]
    x_mesh, y_mesh = [], []
    for gx in grid_x:
        for gy in grid_y:
            x_mesh.append(gx)
            y_mesh.append(gy)
            
    fig.add_trace(go.Scatter(
        x=x_mesh, y=y_mesh,
        mode="markers",
        marker=dict(size=10, color="rgba(0,0,0,0)"),
        hoverinfo="none",
        showlegend=False
    ))

    # 3. LÍNEAS OFICIALES DE LA PISTA (40m x 20m)
    lineas = [
        dict(type="line", x0=20, y0=0, x1=20, y1=20, line=dict(color="white", width=2)),
        dict(type="circle", x0=17, y0=7, x1=23, y1=13, line=dict(color="white", width=2)),
        dict(type="circle", x0=19.8, y0=9.8, x1=20.2, y1=10.2, line=dict(color="white"), fillcolor="white"),
        dict(type="rect", x0=0, y0=4, x1=6, y1=16, line=dict(color="white", width=2, dash="dash")),
        dict(type="rect", x0=34, y0=4, x1=40, y1=16, line=dict(color="white", width=2, dash="dash")),
        dict(type="rect", x0=0, y0=8.5, x1=0.8, y1=11.5, line=dict(color="yellow", width=2), fillcolor="rgba(255,255,0,0.3)"),
        dict(type="rect", x0=39.2, y0=8.5, x1=40, y1=11.5, line=dict(color="yellow", width=2), fillcolor="rgba(255,255,0,0.3)"),
    ]
    for l in lineas:
        fig.add_shape(l)

    # 4. CAPA DE PUNTOS TÁCTICOS CON AURA (Solo si no es modo limpio)
    if modo == "calor" and df_puntos is not None and not df_puntos.empty:
        for res in ["Gol", "Remate a Puerta", "Remate Fuera", "Pérdida / Bloqueado"]:
            df_sub = df_puntos[df_puntos["Resultado"] == res]
            if not df_sub.empty:
                # Capa A: Aura de calor alrededor del punto (más grande y difusa)
                fig.add_trace(go.Scatter(
                    x=df_sub["X"],
                    y=df_sub["Y"],
                    mode="markers",
                    marker=dict(
                        size=SIZE_MAP.get(res, 12) * 2.4, # Halo expansivo
                        color=AURA_MAP.get(res, "rgba(255,255,255,0.2)"),
                        symbol="circle"
                    ),
                    hoverinfo="none",
                    showlegend=False
                ))

                # Capa B: Punto preciso central
                fig.add_trace(go.Scatter(
                    x=df_sub["X"],
                    y=df_sub["Y"],
                    mode="markers",
                    name=res,
                    marker=dict(
                        size=SIZE_MAP.get(res, 12),
                        color=COLOR_MAP.get(res, "#ffffff"),
                        symbol=SYMBOL_MAP.get(res, "circle"),
                        line=dict(width=1.5, color="black")
                    ),
                    text=[f"{row['Elemento']} ({row['Jornada']})" for _, row in df_sub.iterrows()],
                    hoverinfo="text+x+y"
                ))

    fig.update_layout(
        xaxis=dict(range=[-0.5, 40.5], showgrid=False, zeroline=False, visible=False, fixedrange=True),
        yaxis=dict(range=[-0.5, 20.5], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1, fixedrange=True),
        plot_bgcolor="#0f172a",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=10),
        height=430,
        clickmode='event+select',
        showlegend=(modo == "calor"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1) if modo == "calor" else None
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

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Registrador Interactivo", "🔥 Mapa de Precisión / Calor", "📊 Estadísticas Acumuladas", "📄 Exportar PDF"])

df_totales = st.session_state.datos

# PESTAÑA 1: REGISTRADOR LIMPIO (SIN PUNTOS PREVIOS)
with tab1:
    st.header(f"🎯 Registro de acciones contra: {rival}")
    
    fig_pista = dibujar_pista(modo="limpio")
    
    evento_clic = st.plotly_chart(fig_pista, on_select="rerun", selection_mode="points", key="pista_interactiva")
    
    x_capturada = 20.0
    y_capturada = 10.0
    
    if evento_clic and "points" in evento_clic.get("selection", {}) and len(evento_clic["selection"]["points"]) > 0:
        punto = evento_clic["selection"]["points"][0]
        x_capturada = round(punto["x"], 1)
        y_capturada = round(punto["y"], 1)

    st.markdown("### 📍 Posición Detectada del Ratón")
    col_x, col_y, col_btn = st.columns([2, 2, 2])
    
    with col_x:
        pos_x = st.number_input("Distancia Largo - X (0 a 40m)", min_value=0.0, max_value=40.0, value=float(x_capturada), step=0.1)
    with col_y:
        pos_y = st.number_input("Ancho Pista - Y (0 a 20m)", min_value=0.0, max_value=20.0, value=float(y_capturada), step=0.1)
        
    with col_btn:
        st.write("")
        st.write("") 
        if st.button("➕ Registrar Acción Ahora", type="primary", use_container_width=True):
            zona_auto = "Centro"
            if pos_y < 6.5: zona_auto = "Derecha"
            elif pos_y > 13.5: zona_auto = "Izquierda"
            
            nueva_accion = pd.DataFrame([{
                "Rival": rival,
                "Jornada": f"Partido {jornada}",
                "Elemento": elemento,
                "Zona": zona_auto,
                "Resultado": resultado,
                "X": pos_x,
                "Y": pos_y
            }])
            
            st.session_state.datos = pd.concat([st.session_state.datos, nueva_accion], ignore_index=True)
            st.success(f"📌 ¡Guardado! {elemento} ({resultado}) en X:{pos_x}m, Y:{pos_y}m")
            st.rerun()

# PESTAÑA 2: MAPA DE CALOR Y PRECISIÓN CON AURA
with tab2:
    st.header("🔥 Mapa de Calor y Precisión de Tiros")
    if not df_totales.empty:
        rivales_disponibles = df_totales["Rival"].unique().tolist()
        rival_sel = st.selectbox("Seleccionar Rival para visualizar:", rivales_disponibles, key="mapa_rival")
            
        df_mapa = df_totales[df_totales["Rival"] == rival_sel]
        
        if not df_mapa.empty:
            fig_calor = dibujar_pista(df_puntos=df_mapa, modo="calor")
            st.plotly_chart(fig_calor, use_container_width=True)
            
            st.info("🔴 **Estrella Roja** = Gol | 🟡 **Círculo Amarillo** = Remate a Puerta | ⚪ **Círculo Blanco** = Remate Fuera | 🟠 **X Naranja** = Pérdida / Bloqueado")
        else:
            st.warning("No hay datos registrados para este rival.")
    else:
        st.info("Aún no has registrado ningún tiro.")

# PESTAÑA 3: ESTADÍSTICAS ACUMULADAS
with tab3:
    st.header("📊 Estadísticas Acumuladas")
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
        st.info("No hay datos estadísticos acumulados.")

# PESTAÑA 4: EXPORTAR PDF
with tab4:
    st.header("📄 Exportar PDF")
    if not df_totales.empty:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(190, 10, text="Informe Tactico de Scouting - Futbol Sala", new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.set_font("Helvetica", size=11)
        pdf.ln(5)
        pdf.cell(190, 8, text=f"Equipo Analizado: {rival}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(190, 8, text=f"Total Acciones Registradas: {len(df_totales)}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(8)
        
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(45, 8, "Elemento", border=1)
        pdf.cell(40, 8, "Resultado", border=1)
        pdf.cell(30, 8, "Posicion (X,Y)", border=1)
        pdf.cell(35, 8, "Jornada", border=1)
        pdf.ln()
        
        pdf.set_font("Helvetica", size=9)
        for _, row in df_totales.iterrows():
            pdf.cell(45, 8, str(row['Elemento']), border=1)
            pdf.cell(40, 8, str(row['Resultado']), border=1)
            pdf.cell(30, 8, f"{row['X']}m, {row['Y']}m", border=1)
            pdf.cell(35, 8, str(row['Jornada']), border=1)
            pdf.ln()
            
        pdf_bytes = bytes(pdf.output())
        
        st.download_button(
            label="📥 Descargar Reporte en PDF",
            data=pdf_bytes,
            file_name=f"Informe_Scouting_{rival}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.info("No hay datos para exportar a PDF.")
