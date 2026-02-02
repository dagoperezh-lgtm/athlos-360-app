# =============================================================================
# 🏆 ATHLOS 360 - VISUALIZADOR (SOLO LECTURA)
# =============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Athlos 360", layout="wide")
st.title("🏊‍♂️🚴‍♂️🏃‍♂️ Athlos 360 - Dashboard")

# --- 1. CARGA DEL ARCHIVO FINAL ---
archivo = "06 Sem (tst).xlsx"

if not os.path.exists(archivo):
    st.error(f"❌ No encuentro el archivo '{archivo}'. Asegúrate de haber corrido las celdas en Colab y subido el resultado.")
    st.stop()

try:
    # Leemos el archivo generado por Colab. 
    # Como Colab ya lo dejó en números puros, aquí solo leemos.
    df = pd.read_excel(archivo, sheet_name="Distancia Total", engine='openpyxl')
    df.columns = [c.strip() for c in df.columns] # Limpiar espacios en columnas
except Exception as e:
    st.error(f"Error leyendo el Excel: {e}")
    st.stop()

# --- 2. IDENTIFICAR COLUMNA DE NOMBRES ---
col_nombre = None
for c in ['Nombre', 'Deportista', 'Atleta']:
    if c in df.columns:
        col_nombre = c
        break

if not col_nombre:
    st.error("No encuentro la columna de nombres en el Excel.")
    st.stop()

# --- 3. SELECTOR DE ATLETAS ---
# Convertimos a string y filtramos vacíos
lista = sorted([str(x) for x in df[col_nombre].unique() if str(x).lower() not in ['nan', '0', 'none']])
lista.insert(0, "Selecciona un triatleta...")

st.sidebar.header("Panel de Control")
atleta = st.sidebar.selectbox("Busca tu nombre:", lista)

# --- 4. VISUALIZACIÓN ---
if atleta != "Selecciona un triatleta...":
    st.header(f"Resultados de: {atleta}")
    
    # Obtener fila del atleta
    fila = df[df[col_nombre].astype(str) == atleta].iloc[0]
    
    # Buscar columnas de semanas
    cols_sem = [c for c in df.columns if c.startswith("Sem")]
    
    if cols_sem:
        # Extraer datos para el gráfico
        datos_grafico = {'Semana': [], 'Km': []}
        for c in cols_sem:
            datos_grafico['Semana'].append(c)
            # Asegurar que sea número
            val = pd.to_numeric(fila[c], errors='coerce')
            datos_grafico['Km'].append(val if pd.notnull(val) else 0)
            
        df_chart = pd.DataFrame(datos_grafico)
        
        # Gráfico
        fig = px.line(df_chart, x='Semana', y='Km', markers=True, title="Distancia Acumulada")
        st.plotly_chart(fig, use_container_width=True)
        
        # KPI Total
        total = df_chart['Km'].sum()
        st.metric("Total Acumulado", f"{total:.1f} km")
    else:
        st.warning("No hay datos de semanas aún.")
else:
    st.info("👈 Selecciona un nombre en el menú lateral para ver tu rendimiento.")
    # Tabla resumen opcional
    if len(df) > 0:
        cols_sem = [c for c in df.columns if c.startswith("Sem")]
        if cols_sem:
            ultima = cols_sem[-1]
            df[ultima] = pd.to_numeric(df[ultima], errors='coerce').fillna(0)
            st.subheader(f"Top 5 - {ultima}")
            st.table(df.nlargest(5, ultima)[[col_nombre, ultima]])
