import streamlit as st
import pandas as pd
import logic  # Tu cerebro matemático

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="wide")

# Estilos CSS
st.markdown("""
    <style>
    .main {background-color: #f4f6f9;}
    h1, h2, h3 {color: #003366;}
    .stDataFrame {background-color: white; border-radius: 10px; padding: 10px;}
    .stButton>button {width: 100%; border-radius: 8px; font-weight: bold; background-color: #003366; color: white;}
    /* Centrar imagen */
    div[data-testid="stImage"] {display: block; margin-left: auto; margin-right: auto;}
    </style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO (NAVEGACIÓN) ---
if 'club_seleccionado' not in st.session_state:
    st.session_state['club_seleccionado'] = None

# =============================================================================
# VISTA 1: PORTADA (LOGIN/SELECCIÓN)
# =============================================================================
if st.session_state['club_seleccionado'] is None:
    
    # 1. Logo Central
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            # Intenta cargar el logo. Si no está, muestra texto.
            st.image("logo_athlos.png", use_container_width=True) 
        except:
            st.title("🦅 ATHLOS 360")
            st.caption("Por favor sube 'logo_athlos.png' a GitHub")

    st.markdown("<h3 style='text-align: center; color: #666;'>Portal de Alto Rendimiento</h3>", unsafe_allow_html=True)
    st.markdown("---")

    # 2. Selector de Club (Centrado)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.write("### Selecciona tu Club para ingresar:")
        club = st.selectbox("Clubes Disponibles", ["Seleccionar...", "TYM Triathlon", "Triatlon B"])

        if club == "TYM Triathlon":
            st.success("✅ Club encontrado. Base de datos conectada.")
            if st.button("🚀 INGRESAR AL DASHBOARD"):
                st.session_state['club_seleccionado'] = "TYM"
                st.rerun()
        
        elif club == "Triatlon B":
            st.warning("⚠️ Sin datos: Este club no tiene reportes activos esta semana.")

# =============================================================================
# VISTA 2: DASHBOARD (LA APP PRINCIPAL)
# =============================================================================
elif st.session_state['club_seleccionado'] == "TYM":
    
    # Botón para salir (En la barra lateral)
    with st.sidebar:
        st.image("logo_athlos.png", use_container_width=True) # Logo pequeño en menú
        if st.button("⬅️ Salir / Cambiar Club"):
            st.session_state['club_seleccionado'] = None
            st.rerun()
        st.markdown("---")

    # --- TUS ENLACES DE DATOS (TYM) ---
    URL_HISTORICO = "https://raw.githubusercontent.com/dagoperezh-lgtm/athlos-360-app/main/00%20Estadi%CC%81sticas%20TYM_ACTUALIZADO_V21%20(1).xlsx"
    URL_SEMANA    = "https://raw.githubusercontent.com/dagoperezh-lgtm/athlos-360-app/main/06%20Sem%20(tst).xlsx"

    # Título Principal
    st.title("🦅 Athlos 360 | TYM Triathlon")
    st.caption("Análisis de Rendimiento y Reportes")

    if st.button("🔄 Refrescar Datos"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("Procesando métricas del club..."):
        # LLAMADA A LOGIC.PY
        datos, avs_team, avs_hist, err = logic.cargar_procesar_datos(URL_HISTORICO, URL_SEMANA)

    if err:
        st.error(f"Error de conexión: {err}")
    else:
        # PESTAÑAS
        tab1, tab2 = st.tabs(["📊 Buscador & Dashboard", "📄 Reporte Word"])
        
        # --- TAB 1: BUSCADOR DE ATLETA ---
        with tab1:
            st.markdown("### 🔍 Busca tu Resultado")
            names = [d['name'] for d in datos]
            sel = st.selectbox("Escribe o selecciona tu nombre:", names, index=None, placeholder="Ej: Juan Pérez...")
            
            if sel:
                # Buscar datos del seleccionado
                atleta = next((d for d in datos if d['name'] == sel), None)
                if atleta:
                    m = atleta['metrics']
                    
                    st.divider()
                    st.markdown(f"## Hola, **{sel}** 👋")
                    
                    # KPI Header
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Tiempo Total", m['tot_tiempo']['val'], delta=m['tot_tiempo']['eq_txt'])
                    c2.metric("Distancia Total", m['tot_dist']['val'], delta=m['tot_dist']['eq_txt'])
                    c3.metric("Desnivel", m['tot_elev']['val'], delta=m['tot_elev']['eq_txt'])
                    c4.metric("Consistencia", m['cv']['val'], delta=m['cv']['eq_txt'])
                    
                    st.divider()

                    # FUNCIÓN VISUALIZACIÓN TABLAS
                    def mostrar_tabla_web(titulo, keys):
                        st.markdown(f"#### {titulo}")
                        rows = []
                        for k in keys:
                            item = m[k]
                            # Filtro ceros
                            if (item['raw_type']=='time' and item['raw_val'].total_seconds()==0) or (item['raw_type']!='time' and item['raw_val']==0): continue
                            
                            rows.append({
                                "Métrica": item['meta']['l'],
                                "Dato": item['val'],
                                "Vs Promedio del Equipo": item['eq_txt'],
                                "Vs tu Promedio Histórico": item['hist_txt']
                            })
                        
                        if not rows:
                            st.info("Sin actividad registrada.")
                            return

                        df = pd.DataFrame(rows)
                        
                        # Colores condicionales
                        def color_col(val):
                            c = 'black'
                            if '+' in str(val): c = 'green'
                            elif '-' in str(val): c = 'red'
                            elif 'New' in str(val): c = 'blue'
                            return f'color: {c}; font-weight: bold;'

                        st.dataframe(
                            df.style.map(color_col, subset=['Vs Promedio del Equipo', 'Vs tu Promedio Histórico']),
                            hide_index=True,
                            use_container_width=True
                        )

                    # Mostrar Tablas
                    mostrar_tabla_web("🏊 Natación", ['nat_tiempo','nat_dist','nat_ritmo'])
                    mostrar_tabla_web("🚴 Ciclismo", ['bike_tiempo','bike_dist','bike_elev','bike_vel'])
                    mostrar_tabla_web("🏃 Trote", ['run_tiempo','run_dist','run_elev','run_ritmo'])
            
            else:
                st.info("👈 Selecciona un atleta arriba para ver su dashboard detallado.")

        # --- TAB 2: DESCARGAS ---
        with tab2:
            st.success("Reporte generado correctamente.")
            if st.button("Generar Word (V35)", type="primary"):
                doc_io = logic.generar_word_v35(datos, avs_team, avs_hist)
                st.download_button("📥 Descargar Reporte Completo", doc_io, "Reporte_Athlos_V35.docx")
