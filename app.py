# =============================================================================
# 🏆 ATHLOS 360 - APP DE VISUALIZACIÓN DE TRIATLÓN (VERSIÓN DEFINITIVA)
# =============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Athlos 360",
    page_icon="🏊‍♂️",
    layout="wide"
)

# Título Principal
st.title("🏊‍♂️🚴‍♂️🏃‍♂️ Athlos 360 - Dashboard de Rendimiento")
st.markdown("---")

# 2. FUNCIÓN DE CARGA DE DATOS (BLINDADA)
@st.cache_data(ttl=60)
def load_data():
    file_path = "06 Sem (tst).xlsx"
    try:
        # Cargamos la hoja de Distancia para sacar la lista de atletas y datos generales
        df = pd.read_excel(file_path, sheet_name="Distancia Total")
        
        # Limpieza básica de columnas (quitar espacios extra)
        df.columns = [str(c).strip() for c in df.columns]
        
        return df
    except Exception as e:
        st.error(f"❌ Error crítico al leer el archivo: {e}")
        return pd.DataFrame()

# Cargar los datos
df = load_data()

# 3. BARRA LATERAL (SELECTOR INTELIGENTE)
st.sidebar.header("👤 Panel del Atleta")

if df.empty:
    st.sidebar.warning("Esperando datos...")
    st.stop()

# Buscar la columna de nombre (puede ser 'Nombre', 'Deportista', etc.)
posibles_nombres = ['Nombre', 'Deportista', 'Atleta', 'Nombre ']
col_nombre = next((c for c in df.columns if c in posibles_nombres), None)

if not col_nombre:
    st.error("⚠️ No se encontró la columna de 'Nombre' en el Excel.")
    st.stop()

# Crear lista de atletas limpia
lista_atletas = sorted([x for x in df[col_nombre].unique() if str(x) != 'nan' and str(x) != '0'])
lista_atletas.insert(0, "Selecciona tu nombre...")

# El Selector
atleta = st.sidebar.selectbox("Búscate aquí:", lista_atletas)

# 4. LÓGICA PRINCIPAL (MOSTRAR DATOS)
if atleta == "Selecciona tu nombre...":
    st.info("👈 ¡Hola! Por favor selecciona tu nombre en el menú de la izquierda para ver tus estadísticas.")
    
    # Mostrar un Top 5 general para que no se vea vacío
    st.subheader("🏆 Top 5 - Distancia Acumulada (Km)")
    
    # Buscar última semana disponible para el ranking
    cols_sem = [c for c in df.columns if c.startswith("Sem")]
    if cols_sem:
        # Ordenar por la última semana o acumulado si existe
        ultima_sem = cols_sem[-1]
        top_5 = df.nlargest(5, ultima_sem)[[col_nombre, ultima_sem]]
        st.table(top_5)
    
    st.stop()

# --- SI HAY ATLETA SELECCIONADO ---

# Filtrar datos del atleta
datos_atleta = df[df[col_nombre] == atleta].iloc[0]

st.subheader(f"📊 Estadísticas de: {atleta}")

# 5. PREPARAR DATOS PARA EL GRÁFICO
# Extraer solo las columnas que son semanas ("Sem 01", "Sem 02"...)
columnas_semanas = [c for c in df.columns if c.startswith("Sem")]

# Crear un DataFrame pequeñito solo para el gráfico
historia = {
    'Semana': columnas_semanas,
    'Distancia (km)': [datos_atleta.get(c, 0) for c in columnas_semanas]
}
df_grafico = pd.DataFrame(historia)

# Limpiar datos (convertir a número y ceros si hay error)
df_grafico['Distancia (km)'] = pd.to_numeric(df_grafico['Distancia (km)'], errors='coerce').fillna(0)

# 6. DIBUJAR GRÁFICOS
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📈 Evolución Semanal (Distancia)")
    if not df_grafico.empty:
        fig = px.line(
            df_grafico, 
            x='Semana', 
            y='Distancia (km)', 
            markers=True,
            title=f"Kilómetros semanales de {atleta}"
        )
        fig.update_layout(yaxis_title="Km Totales")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos históricos para graficar.")

with col2:
    st.markdown("### 🏅 Resumen")
    
    # Calcular totales
