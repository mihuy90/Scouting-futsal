import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from fpdf import FPDF
import io

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Scouting Futsal - Análisis Táctico",
    page_icon="⚽",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. INICIALIZACIÓN DE LA SESIÓN (STATE)
# -----------------------------------------------------------------------------
if "datos" not in st.session_state:
    st.session_state.datos = pd.DataFrame(columns=[
        "Jornada", "Rival", "Fase", "Elemento", "Resultado", "X", "Y"
    ])

# -----------------------------------------------------------------------------
# 3. FUNCIONES AUXILIARES Y DIBUJO DE PISTA
# -----------------------------------------------------------------------------
def dibujar_pista(df_puntos=None, modo="puntos"):
    """
    Dibuja la pista de fútbol sala (40x20m) con Plotly.
    Modos: 'puntos' (para registro/marcadore) o 'calor' (mapa de densidad).
    """
    fig = go.Figure()

    # Dimensiones pista
    ANCHO, ALTO = 40, 20

    # Fondo y líneas principales
    fig.add_shape(type="rect", x0=0, y0=0, x1=ANCHO, y1=ALTO,
                  line=dict(color="white", width=2), fillcolor="#1e3d59")
    
    # Línea central
    fig.add_shape(type="line", x0=ANCHO/2, y0=0, x1=ANCHO/2, y1=ALTO,
                  line=dict(color="white", width=2))
    
    # Círculo central
    fig.add_shape(type="circle", x0=ANCHO/2 - 3, y0=ALTO/2 - 3, x1=ANCHO/2 + 3, y1=ALTO/2 + 3,
                  line=dict(color="white", width=2))

    # Áreas de 6 metros
    # Izquierda
    fig.add_shape(type="path",
                  path=f"M 0,{ALTO/2 - 6} A 6 6 0 0 1 6,{ALTO/2} A 6 6 0 0 1 0,{ALTO/2 + 6}",
                  line=dict(color="white", width=2))
    # Derecha
    fig.add_shape(type="path",
                  path=f"M {ANCHO},{ALTO/2 - 6} A 6 6 0 0 0 {ANCHO-6},{ALTO/2} A 6 6 0 0 0 {ANCHO},{ALTO/2 + 6}",
                  line=dict(color="white", width=2))

    # Puntos de doble penalti (10m) y penalti (6m)
    fig.add_trace(go.Scatter(x=[6, 10, 30, 34], y=[10, 10, 10, 10], mode="markers",
                             marker=dict(color="white", size=4), showlegend=False, hoverinfo="skip"))

    # DIBUJO DE DATOS
    if df_puntos is not None and not df_puntos.empty:
        if modo == "calor":
            fig.add_trace(go.Histogram2dContour(
                x=df_puntos["X"],
                y=df_puntos["Y"],
                colorscale="Hot",
                reversescale=True,
                showscale=False,
                ncontours=15,
                opacity=0.6
            ))
            # Puntos encima de la densidad
            fig.add_trace(go.Scatter(
                x=df_puntos["X"],
                y=df_puntos["Y"],
                mode="markers",
                marker=dict(color="black", size=8, line=dict(color="white", width=1)),
                text=df_puntos["Elemento"] + " - " + df_puntos["Resultado"],
                hoverinfo="text+x+y",
                showlegend=False
            ))
        else:
            # Modo puntos simples por resultado
            colores = {"Gol": "green", "Parada": "blue", "Fuera": "red", "Bloqueado": "orange"}
            for res, color in colores.items():
                df_sub = df_puntos[df_puntos["Resultado"] == res]
                if not df_sub.empty:
                    fig.add_trace(go.Scatter(
                        x=df_sub["X"],
                        y=df_sub["Y"],
                        mode="markers",
                        name=res,
                        marker=dict(color=color, size=12, line=dict(color="black", width=1)),
                        text=df_sub["Elemento"],
                        hoverinfo="text"
                    ))

    # Configuración de ejes y aspecto
    fig.update_xaxes(range=[-1, ANCHO + 1], showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(range=[-1, ALTO + 1], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1)
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def generar_pdf(df):
    """Genera un reporte básico en PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Informe de Scouting - Fútbol Sala", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Total de acciones registradas: {len(df)}", ln=True)
    pdf.ln(5)
    
    # Resumen por Resultado
    resumen = df["Resultado"].value_counts()
    for k, v in resumen.items():
        pdf.cell(0, 8, f"- {k}: {v}", ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

# -----------------------------------------------------------------------------
# 4. ESTRUCTURA DE LA APLICACIÓN (PESTAÑAS)
# -----------------------------------------------------------------------------
st.title("⚽ Scouting & Análisis Táctico de Fútbol Sala")

tab1, tab2, tab3 = st.tabs(["📌 Registrar Acciones", "🔥 Mapa de Calor y Borrado", "📊 Informe y PDF"])

# -----------------------------------------------------------------------------
# PESTAÑA 1: REGISTRO DE ACCIONES
# -----------------------------------------------------------------------------
with tab1:
    st.header("Registrar Nueva Acción en Pista")
    
    col_inputs, col_pista = st.columns([1, 2])
    
    with col_inputs:
        jornada = st.text_input("Jornada / Partido:", value="Jornada 1")
        rival = st.text_input("Rival:", value="Rival A")
        fase = st.selectbox("Fase de Juego:", ["Ataque Posicional", "Contraataque", "Balón Parado", "Portero Jugador"])
        elemento = st.selectbox("Elemento Táctico:", ["Tiro exterior", "1vs1", "Juego con Pívot", "Estrategia", "Transición"])
        resultado = st.selectbox("Resultado:", ["Gol", "Parada", "Fuera", "Bloqueado"])
        
        st.write("---")
        st.markdown("**Coordenadas de la Acción (metros):**")
        pos_x = st.slider("Posición X (Largo: 0 a 40m):", 0.0, 40.0, 20.0, step=0.5)
        pos_y = st.slider("Posición Y (Ancho: 0 a 20m):", 0.0, 20.0, 10.0, step=0.5)
        
        if st.button("💾 Guardar Acción", type="primary", use_container_width=True):
            nueva_fila = pd.DataFrame([{
                "Jornada": jornada,
                "Rival": rival,
                "Fase": fase,
                "Elemento": elemento,
                "Resultado": resultado,
                "X": pos_x,
                "Y": pos_y
            }])
            st.session_state.datos = pd.concat([st.session_state.datos, nueva_fila], ignore_index=True)
            st.success("¡Acción guardada correctamente!")

    with col_pista:
        st.subheader("Ubicación previa en la pista")
        # Mostrar vista previa con el punto actual
        df_preview = pd.DataFrame([{"X": pos_x, "Y": pos_y, "Resultado": resultado, "Elemento": elemento}])
        fig_preview = dibujar_pista(df_preview, modo="puntos")
        st.plotly_chart(fig_preview, use_container_width=True)

# -----------------------------------------------------------------------------
# PESTAÑA 2: MAPA DE CALOR Y ELIMINACIÓN DE PUNTOS
# -----------------------------------------------------------------------------
with tab2:
    st.header("🔥 Mapa de Densidad y Gestor de Registros")
    df_totales = st.session_state.datos

    if not df_totales.empty:
        col_riv, col_filt = st.columns([2, 2])
        with col_riv:
            rivales_disponibles = df_totales["Rival"].unique().tolist()
            rival_sel = st.selectbox("Seleccionar Rival:", rivales_disponibles, key="mapa_rival")
        with col_filt:
            elementos_disp = ["Todos"] + list(df_totales["Elemento"].unique())
            filtro_elem = st.selectbox("Filtrar por Elemento:", elementos_disp, key="filtro_elem")
            
        df_mapa = df_totales[df_totales["Rival"] == rival_sel]
        if filtro_elem != "Todos":
            df_mapa = df_mapa[df_mapa["Elemento"] == filtro_elem]
        
        if not df_mapa.empty:
            st.info("💡 **Para borrar un punto:** Haz clic sobre él en la pista o selecciónalo directamente en el menú de abajo.")
            
            fig_calor = dibujar_pista(df_puntos=df_mapa, modo="calor")
            
            # Gráfico interactivo con captura de eventos de selección
            evento_mapa = st.plotly_chart(
                fig_calor, 
                use_container_width=True, 
                on_select="rerun", 
                selection_mode="points", 
                key="pista_borrado"
            )
            
            # --- BORRADO INTERACTIVO ---
            st.markdown("---")
            st.subheader("🗑️ Eliminar Puntos de la Pista")
            
            col_del1, col_del2 = st.columns([3, 1])
            indice_a_borrar = None
            
            # Detectar si el usuario hizo clic en un punto del gráfico Plotly
            if evento_mapa and "points" in evento_mapa.get("selection", {}) and len(evento_mapa["selection"]["points"]) > 0:
                punto_sel = evento_mapa["selection"]["points"][0]
                x_sel, y_sel = punto_sel.get("x"), punto_sel.get("y")
                
                # Búsqueda de coincidencia por coordenadas aproximadas
                coincidencias = st.session_state.datos[
                    (st.session_state.datos["Rival"] == rival_sel) & 
                    (np.isclose(st.session_state.datos["X"], x_sel, atol=0.4)) & 
                    (np.isclose(st.session_state.datos["Y"], y_sel, atol=0.4))
                ]
                if not coincidencias.empty:
                    indice_a_borrar = coincidencias.index[0]

            with col_del1:
                opciones_puntos = {
                    idx: f"ID {idx} | {row['Elemento']} - {row['Resultado']} (X: {row['X']}m, Y: {row['Y']}m) [{row['Jornada']}]"
                    for idx, row in df_mapa.iterrows()
                }
                
                idx_defecto = list(opciones_puntos.keys()).index(indice_a_borrar) if indice_a_borrar in opciones_puntos else 0
                
                id_seleccionado = st.selectbox(
                    "Punto seleccionado para eliminar:",
                    options=list(opciones_puntos.keys()),
                    format_func=lambda x: opciones_puntos[x],
                    index=idx_defecto,
                    key="selector_borrado"
                )

            with col_del2:
                st.write("")
                st.write("")
                if st.button("❌ Borrar Punto", type="primary", use_container_width=True):
                    st.session_state.datos = st.session_state.datos.drop(index=id_seleccionado).reset_index(drop=True)
                    st.success("Registro eliminado con éxito.")
                    st.rerun()

        else:
            st.warning("No hay registros disponibles para los filtros seleccionados.")
    else:
        st.info("Aún no se ha registrado ninguna acción en la Pestaña 1.")

# -----------------------------------------------------------------------------
# PESTAÑA 3: RESUMEN DE DATOS Y EXPORTACIÓN
# -----------------------------------------------------------------------------
with tab3:
    st.header("📊 Tabla de Datos e Informes")
    
    if not st.session_state.datos.empty:
        st.dataframe(st.session_state.datos, use_container_width=True)
        
        col_down1, col_down2 = st.columns(2)
        
        with col_down1:
            # Descargar CSV
            csv = st.session_state.datos.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Datos en CSV",
                data=csv,
                file_name="scouting_futsal.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with col_down2:
            # Descargar PDF
            pdf_bytes = generar_pdf(st.session_state.datos)
            st.download_button(
                label="📄 Exportar Informe PDF",
                data=pdf_bytes,
                file_name="informe_scouting.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        st.write("---")
        if st.button("⚠️ Borrar TODOS los datos acumulados"):
            st.session_state.datos = pd.DataFrame(columns=["Jornada", "Rival", "Fase", "Elemento", "Resultado", "X", "Y"])
            st.rerun()
    else:
        st.info("No hay datos para mostrar.")
