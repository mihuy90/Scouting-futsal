import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF

st.set_page_config(page_title="Scouting Futsal Pro", layout="wide")
st.title("⚽ Scouting & Análisis Táctico - Fútbol Sala")

# 1. Base de datos local
if "datos" not in st.session_state:
    st.session_state.datos = pd.DataFrame(columns=[
        "Rival", "Jornada", "Elemento", "Zona", "Resultado", "X", "Y"
    ])

# DICCIONARIO DE COLORES SEGÚN RESULTADO
COLOR_MAP = {
    "Gol": "#ef4444",               # Rojo vivo
    "Remate a Puerta": "#facc15",    # Amarillo potente
    "Remate Fuera": "#ffffff",     # Blanco puro
    "Pérdida / Bloqueado": "#fb923c" # Naranja brillante
}

# Aura / Halo translúcido
AURA_MAP = {
    "Gol": "rgba(239, 68, 68, 0.35)",
    "Remate a Puerta": "rgba(250, 204, 21, 0.35)",
    "Remate Fuera": "rgba(255, 255, 255, 0.25)",
    "Pérdida / Bloqueado": "rgba(251, 146, 60, 0.3)"
}

# FORMA DEL ICONO SEGÚN EL ELEMENTO (Símbolos válidos de Plotly)
SYMBOL_ELEMENTO_MAP = {
    "Córner": "triangle-up",
    "Banda": "diamond",
    "Contraataque": "x",
    "Falta Directa": "circle-open-dot",
    "Doble Penalti": "circle-open-dot",
    "Penalti": "circle-open-dot",
    "Juego Continuo / Tiro": "circle"
}

# Tamaños equilibrados
SIZE_MAP = {
    "Gol": 15,
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

    # 4. CAPA DE PUNTOS TÁCTICOS
    if modo == "calor" and df_puntos is not None and not df_puntos.empty:
        for res in ["Gol", "Remate a Puerta", "Remate Fuera", "Pérdida / Bloqueado"]:
            df_sub = df_puntos[df_puntos["Resultado"] == res]
            if not df_sub.empty:
                simbolos = [SYMBOL_ELEMENTO_MAP.get(elem, "circle") for elem in df_sub["Elemento"]]
                
                # Capa A: Aura translúcida
                fig.add_trace(go.Scatter(
                    x=df_sub["X"],
                    y=df_sub["Y"],
                    mode="markers",
                    marker=dict(
                        size=SIZE_MAP.get(res, 12) * 2.3,
                        color=AURA_MAP.get(res, "rgba(255,255,255,0.2)"),
                        symbol="circle"
                    ),
                    hoverinfo="none",
                    showlegend=False
                ))

                # Capa B: Punto / Icono táctico preciso
                fig.add_trace(go.Scatter(
                    x=df_sub["X"],
                    y=df_sub["Y"],
                    mode="markers",
                    name=res,
                    marker=dict(
                        size=SIZE_MAP.get(res, 12),
                        color=COLOR_MAP.get(res, "#ffffff"),
                        symbol=simbolos,
                        line=dict(width=1.5, color="black")
                    ),
                    text=[f"{row['Elemento']} | {row['Resultado']} ({row['Jornada']})" for _, row in df_sub.iterrows()],
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
        "Córner", 
        "Banda", 
        "Contraataque", 
        "Falta Directa", 
        "Doble Penalti", 
        "Penalti", 
        "Juego Continuo / Tiro"
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("2. Resultado")
resultado = st.sidebar.radio("Resultado", ["Gol", "Remate a Puerta", "Remate Fuera", "Pérdida / Bloqueado"])

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Registrador Interactivo", "🔥 Mapa de Precisión / Calor", "📊 Estadísticas Acumuladas", "📄 Exportar PDF"])

df_totales = st.session_state.datos

# PESTAÑA 1: REGISTRADOR LIMPIO
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

# PESTAÑA 2: MAPA DE CALOR CON ICONOS SEGÚN ELEMENTO
with tab2:
    st.header("🔥 Mapa de Calor y Origen del Golpeo")
    if not df_totales.empty:
        col_riv, col_filt = st.columns([2, 2])
        with col_riv:
            rivales_disponibles = df_totales["Rival"].unique().tolist()
            rival_sel = st.selectbox("Seleccionar Rival:", rivales_disponibles, key="mapa_rival")
        with col_filt:
            elementos_disp = ["Todos"] + df_totales["Elemento"].unique().tolist()
            filtro_elem = st.selectbox("Filtrar por Elemento de Juego:", elementos_disp, key="filtro_elem")
            
        df_mapa = df_totales[df_totales["Rival"] == rival_sel]
        if filtro_elem != "Todos":
            df_mapa = df_mapa[df_mapa["Elemento"] == filtro_elem]
        
        if not df_mapa.empty:
            fig_calor = dibujar_pista(df_puntos=df_mapa, modo="calor")
            st.plotly_chart(fig_calor, use_container_width=True)
            
            st.markdown("""
            **Leyenda de Formas (Origen de la acción):**
            * 🔺 **Triángulo:** Córner
            * 🔷 **Diamante:** Banda
            * ✖️ **Cruz:** Contraataque
            * 🎯 **Diana (círculo con punto):** Falta / Penalti
            * 🟡🔴⚪ **Círculo:** Juego Continuo / Tiro Libre
            """)
        else:
            st.warning("No hay datos para este filtro.")
    else:
        st.info("Aún no has registrado ningún tiro.")

# PESTAÑA 3: ESTADÍSTICAS AVANZADAS Y GRÁFICOS CIRCULARES SIMÉTRICOS
with tab3:
    st.header("📊 Estadísticas Acumuladas & Efectividad")
    if not df_totales.empty:
        rival_sel2 = st.selectbox("Seleccionar Rival para Análisis:", df_totales["Rival"].unique(), key="acum_rival")
        df_rival2 = df_totales[df_totales["Rival"] == rival_sel2]
        
        # MÉTRICAS TOP
        c1, c2, c3, c4 = st.columns(4)
        total_acc = len(df_rival2)
        goles_cnt = len(df_rival2[df_rival2["Resultado"] == "Gol"])
        puerta_cnt = len(df_rival2[df_rival2["Resultado"] == "Remate a Puerta"])
        
        efectividad_gol = round((goles_cnt / total_acc) * 100, 1) if total_acc > 0 else 0
        efectividad_puerta = round(((goles_cnt + puerta_cnt) / total_acc) * 100, 1) if total_acc > 0 else 0
        
        c1.metric("Total Acciones", total_acc)
        c2.metric("Goles Convertidos", goles_cnt, f"{efectividad_gol}% del total")
        c3.metric("Tiros Entre Palos", goles_cnt + puerta_cnt, f"{efectividad_puerta}% del total")
        c4.metric("% Remate a Puerta", f"{efectividad_puerta}%")
        
        st.markdown("---")
        
        # COLUMNAS SIMÉTRICAS
        col_pie1, col_pie2 = st.columns(2)
        
        # IZQUIERDA: EFECTIVIDAD GENERAL (CON DESPLEGABLE DE FILTRO DE JORNADA)
        with col_pie1:
            st.subheader("🎯 % Efectividad General")
            jornadas_disponibles = ["Todas las Jornadas"] + sorted(df_rival2["Jornada"].unique().tolist())
            jornada_sel_pie = st.selectbox("Filtrar por Jornada / Partido:", jornadas_disponibles, key="jornada_pie_izq")
            
            df_izq = df_rival2.copy()
            if jornada_sel_pie != "Todas las Jornadas":
                df_izq = df_izq[df_izq["Jornada"] == jornada_sel_pie]
                
            df_res_counts = df_izq["Resultado"].value_counts().reset_index()
            df_res_counts.columns = ["Resultado", "Cantidad"]
            
            fig_pie_res = px.pie(
                df_res_counts, 
                values="Cantidad", 
                names="Resultado",
                color="Resultado",
                color_discrete_map=COLOR_MAP,
                hole=0.45
            )
            fig_pie_res.update_traces(textposition='inside', textinfo='percent+label+value')
            fig_pie_res.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_pie_res, use_container_width=True)
            
        # DERECHA: ANALIZAR ELEMENTO ESPECÍFICO (CON DESPLEGABLE DE ELEMENTO)
        with col_pie2:
            st.subheader("🔍 Analizar Elemento Específico")
            elementos_disponibles_rival = ["Todos los Elementos"] + df_rival2["Elemento"].unique().tolist()
            elem_filtrado_pie = st.selectbox("Selecciona para ver su efectividad:", elementos_disponibles_rival, key="elem_pie_derecha")
            
            if elem_filtrado_pie == "Todos los Elementos":
                df_elem_counts = df_rival2["Elemento"].value_counts().reset_index()
                df_elem_counts.columns = ["Elemento", "Cantidad"]
                
                fig_pie_elem = px.pie(
                    df_elem_counts, 
                    values="Cantidad", 
                    names="Elemento",
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    hole=0.45
                )
                fig_pie_elem.update_traces(textposition='inside', textinfo='percent+label+value')
                fig_pie_elem.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_pie_elem, use_container_width=True)
            else:
                df_sub_elem = df_rival2[df_rival2["Elemento"] == elem_filtrado_pie]
                df_sub_counts = df_sub_elem["Resultado"].value_counts().reset_index()
                df_sub_counts.columns = ["Resultado", "Cantidad"]
                
                fig_pie_elem = px.pie(
                    df_sub_counts, 
                    values="Cantidad", 
                    names="Resultado",
                    color="Resultado",
                    color_discrete_map=COLOR_MAP,
                    hole=0.45
                )
                fig_pie_elem.update_traces(textposition='inside', textinfo='percent+label+value')
                fig_pie_elem.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_pie_elem, use_container_width=True)

        st.markdown("---")
        
        # TABLA DE REGISTROS ORDENADA POR ACCIONES
        st.subheader("📋 Registro Detallado (Ordenado por Frecuencia de Acción)")
        
        df_ordenado = df_rival2.sort_values(by=["Elemento", "Resultado"], ascending=True)
        st.dataframe(df_ordenado, use_container_width=True)
        
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
