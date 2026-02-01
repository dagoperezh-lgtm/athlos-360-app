import streamlit as st
import pandas as pd
import logic  # Importamos tu cerebro V35

# --- CONFIGURACIÓN ---
URL_HISTORICO = "https://raw.githubusercontent.com/dagoperezh-lgtm/athlos-360-app/main/00%20Estadi%CC%81sticas%20TYM_ACTUALIZADO_V21%20(1).xlsx"
URL_SEMANA    = "https://raw.githubusercontent.com/dagoperezh-lgtm/athlos-360-app/main/06%20Sem%20(tst).xlsx"

st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="wide")
st.markdown("""<style>.main{background-color:#f4f6f9;} h1,h2,h3{color:#003366;} .stDataFrame{background-color:white;border-radius:10px;padding:10px;}</style>""", unsafe_allow_html=True)

# --- INTERFAZ ---
st.title("🦅 Athlos 360")
st.caption("Sistema V35 - Encapsulado y Protegido")

if st.button("🔄 Refrescar Datos"):
    st.cache_data.clear()
    st.experimental_rerun()

with st.spinner("Procesando datos con Logic V35..."):
    # Llamamos al archivo logic.py
    datos, avs_team, avs_hist, err = logic.cargar_procesar_datos(URL_HISTORICO, URL_SEMANA)

if err:
    st.error(f"Error Crítico: {err}")
else:
    tab1, tab2 = st.tabs(["📊 Dashboard Atleta", "📄 Reporte Word"])
    
    with tab1:
        names = [d['name'] for d in datos]
        sel = st.selectbox("Seleccionar Atleta:", names)
        atleta = next((d for d in datos if d['name'] == sel), None)
        
        if atleta:
            m = atleta['metrics']
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Tiempo Total", m['tot_tiempo']['val'], delta=m['tot_tiempo']['eq_txt'])
            c2.metric("Distancia Total", m['tot_dist']['val'], delta=m['tot_dist']['eq_txt'])
            c3.metric("Desnivel", m['tot_elev']['val'], delta=m['tot_elev']['eq_txt'])
            c4.metric("Consistencia", m['cv']['val'], delta=m['cv']['eq_txt'])
            st.divider()

            def mostrar_tabla_web(titulo, keys):
                st.markdown(f"#### {titulo}")
                rows = []
                for k in keys:
                    item = m[k]
                    if (item['raw_type']=='time' and item['raw_val'].total_seconds()==0) or (item['raw_type']!='time' and item['raw_val']==0): continue
                    rows.append({
                        "Métrica": item['meta']['l'],
                        "Dato": item['val'],
                        "Vs Promedio del Equipo": item['eq_txt'],
                        "Vs tu Promedio Histórico": item['hist_txt']
                    })
                if not rows:
                    st.caption("Sin actividad registrada.")
                    return
                
                # Pintar tabla
                def color_col(val):
                    c = 'black'
                    if '+' in str(val): c = 'green'
                    elif '-' in str(val): c = 'red'
                    elif 'New' in str(val): c = 'blue'
                    return f'color: {c}; font-weight: bold;'

                st.dataframe(pd.DataFrame(rows).style.map(color_col, subset=['Vs Promedio del Equipo', 'Vs tu Promedio Histórico']), hide_index=True, use_container_width=True)

            mostrar_tabla_web("🏊 Natación", ['nat_tiempo','nat_dist','nat_ritmo'])
            mostrar_tabla_web("🚴 Ciclismo", ['bike_tiempo','bike_dist','bike_elev','bike_vel'])
            mostrar_tabla_web("🏃 Trote", ['run_tiempo','run_dist','run_elev','run_ritmo'])

    with tab2:
        st.success("Reporte generado con el motor V35.")
        if st.button("Generar Word", type="primary"):
            # Llamamos al generador en logic.py
            doc_io = logic.generar_word_v35(datos, avs_team, avs_hist)
            st.download_button("📥 Descargar Reporte", doc_io, "Reporte_Athlos_V35.docx")
