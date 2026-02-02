# =============================================================================
# 🏆 ATHLOS 360 - APP MAESTRA (DISEÑO + DATOS)
# =============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from PIL import Image

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Athlos 360",
    page_icon="🏅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. BARRA LATERAL (LOGO Y CLUB) ---
with st.sidebar:
    # A. LOGO (Intenta cargar 'logo.png', si no existe pone texto)
    logo_path = "logo.png"  # <--- ASEGÚRATE QUE TU LOGO SE LLAME ASÍ EN GITHUB
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.header("🏊‍♂️🚴‍♂️🏃‍♂️ ATHLOS 360")
        st.caption("Rendimiento Deportivo")

    st.markdown("---")
    
    # B. SELECTOR DE CLUB (La Portada)
    st.header("📍 Tu Club")
    club = st.selectbox("Selecciona tu equipo:", ["TYM Triathlon", "Demo Team"])
    
    if club != "TYM Triathlon":
        st.warning("⚠️ Módulo en desarrollo para otros clubes.")
        st.stop() # Detiene la app aquí si no es TYM

    # C. CARGA DE DATOS (Solo si es TYM)
    archivo_datos = "06 Sem (tst).xlsx"
    
    if not os.path.exists(archivo_datos):
        st.error(f"❌ Error: No encuentro '{archivo_datos}'.")
        st.stop()

# --- 3. LÓGICA DE DATOS ---
# Diccionario de Métricas (Hojas del Excel)
METRICAS = {
    "🏃‍♂️ Distancia Total": "Distancia Total",
    "⏱️ Tiempo Total": "Tiempo Total",
    "🏊‍♂️ Natación (Distancia)": "Nat: Distancia",
    "🚴‍♂️ Ciclismo (Distancia)": "Ciclismo: Distancia",
    "🏃‍♂️ Trote (Distancia)": "Trote: Distancia"
}

try:
    # Detectar hojas reales para no fallar
    xl = pd.ExcelFile(archivo_datos, engine='openpyxl')
    hojas_disponibles = xl.sheet_names
    
    # Filtrar las opciones que sí existen en el excel
    opciones_validas = {k: v for k, v in METRICAS.items() if v in hojas_disponibles}
    
    # Si no encuentra las hojas estándar, muestra las que haya (modo seguro)
    if not opciones_validas:
        opciones_validas = {h: h for h in hojas_disponibles}

except Exception as e:
    st.error(f"Error leyendo el archivo Excel: {e}")
    st.stop()

# --- 4. PANEL DE CONTROL (Debajo del Club) ---
with st.sidebar:
    st.markdown("---")
    st.header("📊 Configuración")
    
    # Selector de Métrica
    metrica_label = st.selectbox("¿Qué quieres analizar?", list(opciones_validas.keys()))
    hoja_seleccionada = opciones_validas[metrica_label]
    
    # Cargar Dataframe de la hoja elegida
    df = pd.read_excel(archivo_datos, sheet_name=hoja_seleccionada, engine='openpyxl')
    df.columns = [str(c).strip() for c in df.columns] # Limpiar espacios
    
    # Buscar columna de Nombres
    col_nombre = next((c for c in ['Nombre', 'Deportista', 'Atleta'] if c in df.columns), None)
    
    if not col_nombre:
        st.error(f"La hoja '{hoja_seleccionada}' no tiene columna de nombres.")
        st.stop()
        
    # Selector de Atleta
    nombres = sorted([str(x) for x in df[col_nombre].unique() if str(x).lower() not in ['nan', '0', 'none']])
    nombres.insert(0, " Selecciona tu nombre...") # Espacio al inicio para que quede primero
    
    st.markdown("### 👤 Atleta")
    atleta = st.selectbox("Búscate aquí:", nombres)

# --- 5. PANTALLA PRINCIPAL ---

# A. PORTADA (Si no ha seleccionado atleta)
if atleta == " Selecciona tu nombre...":
    st.title(f"Bienvenido al Dashboard de {club}")
    st.markdown(f"""
    Estás viendo los datos globales de: **{metrica_label}**
    
    👈 **Para ver tu evolución personal, selecciona tu nombre en la barra lateral.**
    """)
    
    # Mostrar Ranking Top 5 Global de la última semana disponible
    cols_sem = [c for c in df.columns if c.startswith("Sem")]
    if cols_sem:
        ultima_sem = cols_sem[-1]
        
        # Limpieza rápida para el ranking
        df_rank = df.copy()
        df_rank[ultima_sem] = pd.to_numeric(df_rank[ultima_sem], errors='coerce').fillna(0)
        
        # Si es tiempo, convertimos a horas para que se entienda
        es_tiempo = "Tiempo" in metrica_label
        if es_tiempo:
            # Los datos vienen en decimal de día (0.5 = 12h). Multiplicamos por 24 si parecen días.
            # Si ya son horas grandes, se dejan.
            mask = df_rank[ultima_sem] < 5 # Umbral heurístico
            df_rank.loc[mask, ultima_sem] *= 24
            
        top_5 = df_rank.nlargest(5, ultima_sem)[[col_nombre, ultima_sem]]
        
        st.subheader(f"🏆 Top 5 - {ultima_sem}")
        
        # Formatear la tabla para que se vea bonita
        st.dataframe(
            top_5.style.format({ultima_sem: "{:.2f}"}), 
            use_container_width=True,
            hide_index=True
        )
        
    st.image("https://images.unsplash.com/photo-1517649763962-0c623066013b?q=80&w=2070&auto=format&fit=crop", caption="Athlos 360", use_container_width=True)

# B. DASHBOARD PERSONAL (Si seleccionó atleta)
else:
    st.title(f"Resultados: {atleta}")
    st.markdown(f"Analizando: **{metrica_label}**")
    
    # Filtrar datos
    fila = df[df[col_nombre].astype(str) == atleta].iloc[0]
    cols_sem = [c for c in df.columns if c.startswith("Sem")]
    
    if not cols_sem:
        st.warning("No hay datos históricos disponibles.")
    else:
        # Preparar datos para gráfico
        eje_x = []
        eje_y = []
        
        es_tiempo = "Tiempo" in metrica_label
        
        for c in cols_sem:
            raw_val = fila[c]
            try:
                val = float(raw_val)
            except:
                val = 0.0
            
            # Conversión inteligente de Tiempo (Excel Float -> Horas)
            if es_tiempo and val > 0:
                # Si es un número pequeño (ej: 0.5), es fracción de día -> pasar a horas
                if val < 5: 
                    val = val * 24 
            
            eje_x.append(c)
            eje_y.append(val)
            
        # Crear DataFrame Gráfico
        df_chart = pd.DataFrame({'Semana': eje_x, 'Valor': eje_y})
        
        # --- TARJETAS DE RESUMEN (KPIs) ---
        col1, col2, col3 = st.columns(3)
        
        total = sum(eje_y)
        promedio = total / len(eje_y) if eje_y else 0
        ultimo = eje_y[-1] if eje_y else 0
        
        suffix = " hrs" if es_tiempo else " km"
        
        col1.metric("Total Acumulado", f"{total:.1f}{suffix}")
        col2.metric("Promedio Semanal", f"{promedio:.1f}{suffix}")
        col3.metric(f"Última ({eje_x[-1]})", f"{ultimo:.1f}{suffix}", delta_color="normal")
        
        st.markdown("---")
        
        # --- GRÁFICO ---
        fig = px.line(
            df_chart, 
            x='Semana', 
            y='Valor', 
            markers=True,
            title=f"Evolución - {metrica_label}",
            labels={'Valor': 'Horas' if es_tiempo else 'Kilómetros'}
        )
        # Mejorar diseño del gráfico
        fig.update_traces(line_color='#FF4B4B', line_width=3)
        fig.update_layout(xaxis_title=None, height=400)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de datos crudos (oculta por defecto)
        with st.expander("Ver detalle de datos"):
            st.dataframe(df_chart.T)
