import streamlit as st
import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, TapTool, CustomJS, HoverTool
from fpdf import FPDF

st.set_page_config(page_title="Scouting Futsal Pro", layout="wide")
st.title("⚽ Scouting & Análisis Táctico - Fútbol Sala")

# 1. Base de datos local
if "datos" not in st.session_state:
    st.session_state.datos = pd.DataFrame(columns=[
        "Rival", "Jornada", "Elemento", "Zona", "Resultado", "X", "Y"
    ])

# Detectar guardado vía click
query_params = st.query_params
if "click_x" in query_params and "click_y" in query_params:
    cx = float(query_params["click_x"])
    cy = float(query_params["click_y"])
    
    # Obtener temporalmente las opciones del sidebar
    r_elem = st.session_state.get("temp_elem", "Juego Continuo / Tiro")
    r_res = st.session_state.get("temp_res", "Gol")
    r_rival = st.session_state.get("temp_rival", "Poio")
    r_jornada = st.session_state.get("temp_jornada", 1)

    zona_auto = "Centro"
    if cy < 6.5: zona_auto = "Derecha"
    elif cy > 13.5: zona_auto = "Izquierda"

    nueva_accion = pd.DataFrame([{
        "Rival": r_rival,
        "Jornada": f"Partido {r_jornada}",
        "Elemento": r_elem,
        "Zona": zona_auto,
        "Resultado": r_res,
        "X": round(cx, 1),
        "Y": round(cy, 1)
    }])

    st.session_state.datos = pd.concat([st.session_state.datos, nueva_accion], ignore_index=True)
    # Limpiar parámetros de URL
    st.query_params.clear()
    st.rerun()

# --- PANEL LATERAL ---
st.sidebar.header("📋 Opciones de Registro")
rival = st.sidebar.text_input("Equipo Rival", "Poio", key="temp_rival")
jornada = st.sidebar.number_input("Partido / Jornada", min_value=1, max_value=30, value=1, key="temp_jornada")

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
    index=0,
    key="temp_elem"
)

st.sidebar.markdown("---")
st.sidebar.subheader("2. Resultado")
resultado = st.sidebar.radio("Resultado", ["Gol", "Remate a Puerta", "Remate Fuera", "Pérdida / Bloqueado"], key="temp_res")

st.sidebar.info("💡 **Instrucción:** Elige las opciones de arriba y **Haz Clic Izquierdo** sobre el campo.")

# --- DIBUJO DE PISTA EN BOKEH ---
def crear_pista(df_puntos=None):
    p = figure(
        x_range=(0, 40), y_range=(0, 20),
        width=850, height=425,
        tools="tap", toolbar_location=None,
        active_tap="tap"
    )
    
    # Estilo Pista
    p.background_fill_color = "#1e3a8a"
    p.xgrid.visible = False
    p.ygrid.visible = False
    p.axis.visible = False

    # Marcas Oficiales
    p.rect(x=20, y=10, width=40, height=20, fill_alpha=0, line_color="white", line_width=3) # Fondo
    p.line(x=[20, 20], y=[0, 20], line_color="white", line_width=2) # Centro
    p.circle(x=20, y=10, radius=3, fill_alpha=0, line_color="white", line_width=2) # Círculo Central
    p.circle(x=20, y=10, radius=0.2, fill_color="white", line_color="white") # Punto Central
    p.rect(x=3, y=10, width=6, height=12, fill_alpha=0, line_color="white", line_width=1.5, line_dash="dashed") # Área Izq
    p.rect(x=37, y=10, width=6, height=12, fill_alpha=0, line_color="white", line_width=1.5, line_dash="dashed") # Área Der
    p.rect(x=0.4, y=10, width=0.8, height=3, fill_color="yellow", fill_alpha=0.3, line_color="yellow", line_width=2) # Port Izq
    p.rect(x=39.6, y=10, width=0.8, height=3, fill_color="yellow", fill_alpha=0.3, line_color="yellow", line_width=2) # Port Der

    # Dibujar puntos guardados sobre la pista
    if df_puntos is not None and not df_puntos.empty:
        color_dict = {"Gol": "#22c55e", "Remate a Puerta": "#3b82f6", "Remate Fuera": "#f97316", "Pérdida / Bloqueado": "#ef4444"}
        df_puntos["color"] = df_puntos["Resultado"].map(color_dict)
        source = ColumnDataSource(df_puntos)
        p.circle(x="X", y="Y", size=14, color="color", line_color="black", line_width=1.5, source=source)

    # JavaScript para detectar clic del ratón e interactuar con Streamlit
    code = """
        const x = cb_obj.x;
        const y = cb_obj.y;
        const url = new URL(window.location.href);
        url.searchParams.set('click_x', x.toFixed(1));
        url.searchParams.set('click_y', y.toFixed(1));
        window.location.href = url.href;
    """
    p.js_on_event('tap', CustomJS(code=code))
    return p

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Registrador Interactivo", "🔥 Mapa de Calor", "📊 Estadísticas Acumuladas", "📄 Exportar PDF"])

df_totales = st.session_state.datos

# TAB 1: REGISTRO CON CLIC DIRECTO
with tab1:
    st.header(f"🎯 Registro de tiros contra: {rival}")
    df_rival = df_totales[df_totales["Rival"] == rival] if not df_totales.empty else pd.DataFrame()
    pista_bokeh = crear_pista(df_rival)
    st.bokeh_chart(pista_bokeh, use_container_width=True)

# TAB 2: MAPA DE CALOR
with tab2:
    st.header("🔥 Mapa de Calor / Distribución de Tiros")
    if not df_totales.empty:
        rival_sel = st.selectbox("Seleccionar Rival para visualizar:", df_totales["Rival"].unique(), key="mapa_r")
        df_m = df_totales[df_totales["Rival"] == rival_sel]
        pista_mapa = crear_pista(df_m)
        st.bokeh_chart(pista_mapa, use_container_width=True)
    else:
        st.info("No hay puntos registrados aún. Haz clic en el campo de la primera pestaña.")

# TAB 3: ESTADÍSTICAS
with tab3:
    st.header("📊 Estadísticas Acumuladas")
    if not df_totales.empty:
        rival_sel2 = st.selectbox("Seleccionar Rival:", df_totales["Rival"].unique(), key="acum_r")
        df_r = df_totales[df_totales["Rival"] == rival_sel2]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Acciones", len(df_r))
        c2.metric("Goles", len(df_r[df_r["Resultado"] == "Gol"]))
        tot_remates = len(df_r[df_r["Resultado"].isin(["Gol", "Remate a Puerta"])])
        efectividad = round((tot_remates / len(df_r)) * 100, 1) if len(df_r) > 0 else 0
        c3.metric("% Efectividad Tiro", f"{efectividad}%")
        
        st.dataframe(df_r, use_container_width=True)
    else:
        st.info("No hay datos estadísticos acumulados.")

# TAB 4: PDF
with tab4:
    st.header("📄 Exportar Reporte")
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
        st.download_button("📥 Descargar Reporte PDF", data=pdf_bytes, file_name=f"Scouting_{rival}.pdf", mime="application/pdf")
