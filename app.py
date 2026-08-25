import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import tempfile
import os
import unicodedata

st.set_page_config(page_title="Scouting Futsal Pro", layout="wide")
st.title("⚽ Scouting & Análisis Táctico - Fútbol Sala")

# Función auxiliar para sanitizar textos y evitar errores de codificación en FPDF
def limpiar_texto(texto):
    if not isinstance(texto, str):
        return str(texto)
    texto = texto.replace("🔹", "-> ").replace("•", "-").replace("—", "-")
    texto_normalizado = unicodedata.normalize('NFKD', texto).encode('latin-1', 'ignore').decode('latin-1')
    return texto_normalizado

# 1. Base de datos local de acciones
if "datos" not in st.session_state:
    st.session_state.datos = pd.DataFrame(columns=[
        "Rival", "Jornada", "Elemento", "Zona", "Resultado", "X", "Y"
    ])

# 2. Base de datos local de observaciones/notas por rival y elemento
if "observaciones" not in st.session_state:
    st.session_state.observaciones = {}

# DICCIONARIO DE COLORES PISTA / PANTALLA
COLOR_MAP = {
    "Gol": "#ef4444",               # Rojo vivo
    "Remate a Puerta": "#facc15",    # Amarillo potente
    "Remate Fuera": "#e2e8f0",      # Blanco/Gris clarito visible en pista azul
    "Pérdida / Bloqueado": "#fb923c" # Naranja brillante
}

# DICCIONARIO DE COLORES PARA PDF (Fondo Blanco)
COLOR_MAP_PDF = {
    "Gol": "#ef4444",               # Rojo
    "Remate a Puerta": "#eab308",    # Amarillo oscuro/Dorado
    "Remate Fuera": "#64748b",      # Gris azulado visible sobre folio blanco
    "Pérdida / Bloqueado": "#f97316" # Naranja
}

AURA_MAP = {
    "Gol": "rgba(239, 68, 68, 0.35)",
    "Remate a Puerta": "rgba(250, 204, 21, 0.35)",
    "Remate Fuera": "rgba(226, 232, 240, 0.3)",
    "Pérdida / Bloqueado": "rgba(251, 146, 60, 0.3)"
}

SYMBOL_ELEMENTO_MAP = {
    "Córner": "triangle-up",
    "Banda": "diamond",
    "Contraataque": "x",
    "Falta Directa": "circle-open-dot",
    "Doble Penalti": "circle-open-dot",
    "Penalti": "circle-open-dot",
    "Juego Continuo / Tiro": "circle"
}

SIZE_MAP = {
    "Gol": 15,
    "Remate a Puerta": 13,
    "Remate Fuera": 11,
    "Pérdida / Bloqueado": 11
}

ELEMENTOS_LISTA = [
    "Córner", 
    "Banda", 
    "Contraataque", 
    "Falta Directa", 
    "Doble Penalti", 
    "Penalti", 
    "Juego Continuo / Tiro"
]

def dibujar_pista(df_puntos=None, modo="limpio"):
    fig = go.Figure()

    fig.add_shape(
        type="rect", x0=0, y0=0, x1=40, y1=20, 
        line=dict(color="white", width=3), 
        fillcolor="#1e3a8a", 
        layer="below"
    )

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

    if modo == "calor" and df_puntos is not None and not df_puntos.empty:
        for res in ["Gol", "Remate a Puerta", "Remate Fuera", "Pérdida / Bloqueado"]:
            df_sub = df_puntos[df_puntos["Resultado"] == res]
            if not df_sub.empty:
                simbolos = [SYMBOL_ELEMENTO_MAP.get(elem, "circle") for elem in df_sub["Elemento"]]
                
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
elemento = st.sidebar.radio("Elemento:", ELEMENTOS_LISTA, index=0)

st.sidebar.markdown("---")
st.sidebar.subheader("2. Resultado")
resultado = st.sidebar.radio("Resultado", ["Gol", "Remate a Puerta", "Remate Fuera", "Pérdida / Bloqueado"])

st.sidebar.markdown("---")
st.sidebar.header("📂 Gestión de Partidos")

if not st.session_state.datos.empty:
    csv_data = st.session_state.datos.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="💾 Guardar Partido Actual (CSV)",
        data=csv_data,
        file_name=f"Partido_{rival}_Jornada_{jornada}.csv",
        mime="text/csv",
        use_container_width=True
    )

archivos_cargados = st.sidebar.file_uploader("📥 Cargar / Fusionar CSVs de Partidos", type=["csv"], accept_multiple_files=True)
if archivos_cargados:
    if st.sidebar.button("🔄 Fusionar Datos Cargados", use_container_width=True):
        nuevos_dfs = []
        for arch in archivos_cargados:
            df_temp = pd.read_csv(arch)
            nuevos_dfs.append(df_temp)
        if nuevos_dfs:
            st.session_state.datos = pd.concat([st.session_state.datos] + nuevos_dfs, ignore_index=True).drop_duplicates()
            st.sidebar.success("¡Datos fusionados con éxito!")
            st.rerun()

if st.sidebar.button("🗑️ Empezar Nuevo Partido (Limpiar)", type="secondary", use_container_width=True):
    st.session_state.datos = pd.DataFrame(columns=[
        "Rival", "Jornada", "Elemento", "Zona", "Resultado", "X", "Y"
    ])
    st.sidebar.success("Pista vacía para el nuevo partido.")
    st.rerun()

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3, tab_obs, tab4 = st.tabs([
    "🎯 Registrador Interactivo", 
    "🔥 Mapa de Precisión", 
    "📊 Estadísticas", 
    "📝 Observaciones Tácticas",
    "📄 Exportar PDF"
])

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

# PESTAÑA 2: MAPA DE CALOR
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

# PESTAÑA 3: ESTADÍSTICAS
with tab3:
    st.header("📊 Estadísticas Acumuladas & Efectividad")
    if not df_totales.empty:
        rival_sel2 = st.selectbox("Seleccionar Rival para Análisis:", df_totales["Rival"].unique(), key="acum_rival")
        df_rival2 = df_totales[df_totales["Rival"] == rival_sel2]
        
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
        
        col_pie1, col_pie2 = st.columns(2)
        
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
        st.subheader("📋 Registro Detallado")
        df_ordenado = df_rival2.sort_values(by=["Elemento", "Resultado"], ascending=True)
        st.dataframe(df_ordenado, use_container_width=True)
    else:
        st.info("No hay datos estadísticos acumulados.")

# PESTAÑA OBSERVACIONES TÁCTICAS
with tab_obs:
    st.header("📝 Observaciones y Anotaciones Tácticas por Acción")
    st.markdown("Escribe tus notas de scouting desglosadas para que salgan perfectamente organizadas en el PDF final.")
    
    lista_rivales_obs = df_totales["Rival"].unique().tolist() if not df_totales.empty else [rival]
    rival_obs_sel = st.selectbox("Seleccionar Rival para añadir notas:", lista_rivales_obs, key="obs_rival_select")
    
    if rival_obs_sel not in st.session_state.observaciones:
        st.session_state.observaciones[rival_obs_sel] = {}

    st.markdown("---")
    
    for elem in ELEMENTOS_LISTA:
        val_previo = st.session_state.observaciones[rival_obs_sel].get(elem, "")
        
        texto_nota = st.text_area(
            label=f"📌 Notas sobre: **{elem}**",
            value=val_previo,
            placeholder=f"Ej: Suelen buscar bloqueo al primer palo en los {elem.lower()}s. Ojo con la llegada desde atrás...",
            key=f"obs_input_{rival_obs_sel}_{elem}",
            height=100
        )
        st.session_state.observaciones[rival_obs_sel][elem] = texto_nota

    st.success("💾 ¡Notas guardadas automáticamente en tiempo real!")

# PESTAÑA 4: EXPORTAR PDF
with tab4:
    st.header("📄 Exportar Informe Completo en PDF")
    if not df_totales.empty:
        rival_export = st.selectbox("Seleccionar Rival para Exportar PDF:", df_totales["Rival"].unique(), key="pdf_rival_sel")
        
        if st.button("🚀 Generar PDF con Observaciones Tácticas", type="primary", use_container_width=True):
            with st.spinner("Procesando gráficos en alta definición y maquetando PDF..."):
                df_pdf = df_totales[df_totales["Rival"] == rival_export]
                obs_rival = st.session_state.observaciones.get(rival_export, {})
                
                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=15)
                
                # PÁGINA 1: PORTADA Y MAPA DE PISTA GENERAL
                pdf.add_page()
                pdf.set_font("Helvetica", 'B', 18)
                pdf.cell(190, 10, text=limpiar_texto("INFORME TACTICO Y DE SCOUTING"), new_x="LMARGIN", new_y="NEXT", align='C')
                pdf.set_font("Helvetica", 'B', 14)
                pdf.cell(190, 8, text=limpiar_texto(f"Rival Analizado: {rival_export}"), new_x="LMARGIN", new_y="NEXT", align='C')
                pdf.set_font("Helvetica", size=10)
                pdf.cell(190, 6, text=limpiar_texto(f"Total de acciones registradas: {len(df_pdf)}"), new_x="LMARGIN", new_y="NEXT", align='C')
                pdf.ln(5)
                
                with tempfile.TemporaryDirectory() as tmpdir:
                    # Mapa Pista General
                    fig_pista_pdf = dibujar_pista(df_puntos=df_pdf, modo="calor")
                    fig_pista_pdf.update_layout(paper_bgcolor="white", plot_bgcolor="#0f172a")
                    img_pista_path = os.path.join(tmpdir, "mapa_pista.png")
                    fig_pista_pdf.write_image(img_pista_path, width=1000, height=550, scale=2)
                    
                    pdf.set_font("Helvetica", 'B', 12)
                    pdf.cell(190, 8, text=limpiar_texto("1. Mapa de Calor General (Todas las acciones)"), new_x="LMARGIN", new_y="NEXT")
                    pdf.image(img_pista_path, x=10, w=190)
                    pdf.ln(5)
                    
                    # PÁGINA 2: GRÁFICOS GENERALES
                    pdf.add_page()
                    pdf.set_font("Helvetica", 'B', 14)
                    pdf.cell(190, 10, text=limpiar_texto("2. Analisis de Efectividad General y Distribucion"), new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(2)
                    
                    # 1. Efectividad Global (% Resultados)
                    df_res = df_pdf["Resultado"].value_counts().reset_index()
                    df_res.columns = ["Resultado", "Cantidad"]
                    fig_res = px.pie(
                        df_res, 
                        values="Cantidad", 
                        names="Resultado", 
                        color="Resultado", 
                        color_discrete_map=COLOR_MAP_PDF, 
                        hole=0.4
                    )
                    fig_res.update_traces(
                        textposition='inside', 
                        textinfo='percent+value', 
                        textfont_size=14
                    )
                    fig_res.update_layout(
                        title_text="Efectividad Global (% Resultados)", 
                        paper_bgcolor="white", 
                        font=dict(size=13),
                        legend=dict(
                            orientation="h", 
                            yanchor="top", 
                            y=-0.08, 
                            xanchor="center", 
                            x=0.5,
                            font=dict(size=12)
                        ),
                        margin=dict(l=30, r=30, t=50, b=60)
                    )
                    img_res_path = os.path.join(tmpdir, "efectividad_general.png")
                    fig_res.write_image(img_res_path, width=900, height=480, scale=2)
                    
                    # 2. Distribución Global por Elemento
                    df_elem = df_pdf["Elemento"].value_counts().reset_index()
                    df_elem.columns = ["Elemento", "Cantidad"]
                    df_elem = df_elem.sort_values(by="Cantidad", ascending=True)

                    max_val = df_elem["Cantidad"].max() if not df_elem.empty else 10

                    fig_elem = px.bar(
                        df_elem, 
                        x="Cantidad", 
                        y="Elemento", 
                        orientation='h',
                        text="Cantidad",
                        color="Elemento",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )

                    fig_elem.update_traces(
                        texttemplate=' %{text} acciones', 
                        textposition='outside',
                        textfont_size=12
                    )

                    fig_elem.update_layout(
                        title_text="Distribucion Global por Elemento de Juego", 
                        paper_bgcolor="white", 
                        plot_bgcolor="white",
                        showlegend=False,
                        xaxis=dict(
                            showgrid=True, 
                            gridcolor="#f0f0f0", 
                            title="Nº de Acciones",
                            range=[0, max_val * 1.25]
                        ),
                        yaxis=dict(title="", tickfont=dict(size=12)),
                        font=dict(size=13),
                        margin=dict(l=180, r=80, t=50, b=50)
                    )

                    img_elem_path = os.path.join(tmpdir, "distribucion_elementos.png")
                    fig_elem.write_image(img_elem_path, width=900, height=480, scale=2)
                    
                    pdf.image(img_res_path, x=15, y=30, w=180)
                    pdf.image(img_elem_path, x=15, y=145, w=180)
                    
                    # PÁGINA 3 EN ADELANTE: DISPOSICIÓN VERTICAL DE ALTO IMPACTO
                    elementos_unicos = [e for e in ELEMENTOS_LISTA if e in df_pdf["Elemento"].unique()]
                    
                    for idx, elem_nombre in enumerate(elementos_unicos):
                        pdf.add_page()
                        
                        pdf.set_font("Helvetica", 'B', 15)
                        pdf.cell(190, 8, text=limpiar_texto(f"3.{idx+1} Analisis Tactico: {elem_nombre.upper()}"), new_x="LMARGIN", new_y="NEXT")
                        pdf.ln(2)
                        
                        df_sub = df_pdf[df_pdf["Elemento"] == elem_nombre]
                        
                        # 1. Mapa de Pista Grande (Superior Centrado)
                        fig_pista_elem = dibujar_pista(df_puntos=df_sub, modo="calor")
                        fig_pista_elem.update_layout(
                            paper_bgcolor="white", 
                            plot_bgcolor="#0f172a",
                            margin=dict(l=10, r=10, t=20, b=10),
                            showlegend=False
                        )
                        img_pista_sub_path = os.path.join(tmpdir, f"pista_sub_{idx}.png")
                        fig_pista_elem.write_image(img_pista_sub_path, width=1000, height=480, scale=2)
                        
                        # 2. Quesito de Efectividad MÁS GRANDE y centrado
                        df_sub_counts = df_sub["Resultado"].value_counts().reset_index()
                        df_sub_counts.columns = ["Resultado", "Cantidad"]
                        
                        fig_sub = px.pie(
                            df_sub_counts, 
                            values="Cantidad", 
                            names="Resultado", 
                            color="Resultado", 
                            color_discrete_map=COLOR_MAP_PDF, 
                            hole=0.35
                        )
                        fig_sub.update_traces(textposition='auto', textinfo='percent+label+value', textfont_size=14)
                        fig_sub.update_layout(
                            title=dict(text=limpiar_texto(f"Efectividad: {elem_nombre}"), x=0.5, font=dict(size=14)),
                            paper_bgcolor="white", 
                            font=dict(size=13),
                            margin=dict(l=20, r=20, t=30, b=40),
                            legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5, font=dict(size=12))
                        )
                        img_sub_path = os.path.join(tmpdir, f"sub_{idx}.png")
                        # Subimos resolución a 900x520 px para que al agrandarlo no pierda nitidez
                        fig_sub.write_image(img_sub_path, width=900, height=520, scale=2)
                        
                        # --- RENDERIZADO VERTICAL OPTIMIZADO ---
                        
                        # A) Pista (Ancho 170mm, centrada a x=20)
                        y_pista = pdf.get_y()
                        pdf.image(img_pista_sub_path, x=20, y=y_pista, w=170)
                        
                        # B) Quesito AMPLIADO (Ancho 145mm, centrado a x=32.5)
                        y_quesito = y_pista + 84
                        pdf.image(img_sub_path, x=32.5, y=y_quesito, w=145)
                        
                        # C) Bloque de Notas al final de la hoja llenando el espacio restante
                        pdf.set_y(y_quesito + 88)
                        pdf.set_font("Helvetica", 'B', 11)
                        pdf.cell(190, 7, text=limpiar_texto("Notas y Conclusiones Tácticas:"), new_x="LMARGIN", new_y="NEXT")
                        
                        pdf.set_font("Helvetica", size=10)
                        nota_texto = obs_rival.get(elem_nombre, "").strip()
                        if not nota_texto:
                            nota_texto = "Sin observaciones registradas para este tipo de accion."
                            
                        pdf.multi_cell(190, 6, text=limpiar_texto(nota_texto), border=1)

                    # PÁGINA FINAL: TABLA DETALLADA DE REGISTROS
                    pdf.add_page()
                    pdf.set_font("Helvetica", 'B', 14)
                    pdf.cell(190, 10, text=limpiar_texto("4. Tabla Registro Detallado de Acciones"), new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(3)
                    
                    pdf.set_font("Helvetica", 'B', 10)
                    pdf.cell(40, 8, limpiar_texto("Elemento"), border=1)
                    pdf.cell(40, 8, limpiar_texto("Resultado"), border=1)
                    pdf.cell(35, 8, limpiar_texto("Posición (X, Y)"), border=1)
                    pdf.cell(35, 8, limpiar_texto("Jornada"), border=1)
                    pdf.cell(40, 8, limpiar_texto("Zona"), border=1)
                    pdf.ln()
                    
                    pdf.set_font("Helvetica", size=9)
                    df_ordenado_pdf = df_pdf.sort_values(by=["Elemento", "Resultado"], ascending=True)
                    for _, row in df_ordenado_pdf.iterrows():
                        pdf.cell(40, 7, limpiar_texto(row['Elemento']), border=1)
                        pdf.cell(40, 7, limpiar_texto(row['Resultado']), border=1)
                        pdf.cell(35, 7, limpiar_texto(f"{row['X']}m, {row['Y']}m"), border=1)
                        pdf.cell(35, 7, limpiar_texto(row['Jornada']), border=1)
                        pdf.cell(40, 7, limpiar_texto(row['Zona']), border=1)
                        pdf.ln()

                    pdf_bytes = bytes(pdf.output())
                    
                    st.success("✅ ¡PDF optimizado generado con éxito!")
                    st.download_button(
                        label="📥 Descargar Reporte Técnico Completo en PDF",
                        data=pdf_bytes,
                        file_name=f"Informe_Scouting_{rival_export}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
    else:
        st.info("No hay datos para exportar a PDF.")
