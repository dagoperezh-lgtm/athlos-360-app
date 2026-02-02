# =============================================================================
# 🏆 ATHLOS 360 - DASHBOARD PRO (V4.1 CON LOGO CORREGIDO)
# =============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from PIL import Image

# --- 1. CONFIGURACIÓN ESTÉTICA ---
st.set_page_config(
    page_title="Athlos 360 Pro",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS para recuperar la "sensación premium"
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES MAESTRAS DE CARGA ---
ARCHIVO_DATOS = "06 Sem (tst).xlsx"

@st.cache_data(ttl=60)
def cargar_hoja(nombre_hoja_clave):
    """Busca una hoja en el Excel que contenga la palabra clave y devuelve el DF limpio"""
    if not os.path.exists(ARCHIVO_DATOS):
        return None
    
    try:
        xls = pd.ExcelFile(ARCHIVO_DATOS, engine='openpyxl')
        # Buscar la hoja que coincida (ej: busca 'Nat' y encuentra 'Nat: Distancia')
        hoja_real = next((h for h in xls.sheet_names if nombre_hoja_clave.lower() in h.lower()), None)
        
        if hoja_real:
            df = pd.read_excel(xls, sheet_name=hoja_real)
            df.columns = [str(c).strip() for c in df.columns] # Limpiar columnas
            return df
        return None
    except:
        return None

def formato_tiempo(valor_excel):
    """Convierte el decimal de Excel (0.5) a texto bonito (12h 00m)"""
    if pd.isna(valor_excel) or valor_excel == 0:
        return "0h 00m"
    try:
        horas_totales = float(valor_excel) * 24
        horas = int(horas_totales)
        minutos = int((horas_totales - horas) * 60)
        return f"{horas}h {minutos:02d}m"
    except:
        return "0h 00m"

# --- 3. BARRA LATERAL (IDENTIDAD) ---
with st.sidebar:
    # Logo (CORREGIDO A TU NOMBRE DE ARCHIVO)
    logo_path = "logo_athlos.png" 
    
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        # Fallback si no encuentra la imagen
        st.title("🏊‍♂️🚴‍♂️🏃‍♂️ ATHLOS 360")
        if not os.path.exists(logo_path):
            st.caption(f"(No encontré '{logo_path}' en GitHub)")
    
    st.markdown("---")
    st.header("📍 Club")
    st.info("🦁 TYM Triathlon") # Club fijo por ahora
    
    # Cargar datos base para la lista de atletas
    df_base = cargar_hoja("Distancia Total")
    
    if df_base is None:
        st.error("❌ Error crítico: No encuentro los datos (06 Sem).")
        st.stop()
        
    # Buscar columna nombre
    col_nombre = next((c for c in ['Nombre', 'Deportista', 'Atleta'] if c in df_base.columns), None)
    
    # Selector Atleta
    nombres = sorted([str(x) for x in df_base[col_nombre].unique() if str(x).lower() not in ['nan', '0', 'none']])
    nombres.insert(0, " Selecciona tu nombre...")
    
    st.markdown("### 👤 Atleta")
    atleta = st.selectbox("Búscate aquí:", nombres)

# --- 4. LOGICA PRINCIPAL ---

if atleta == " Selecciona tu nombre...":
    # PORTADA DE CLUB
    st.title("📊 Resumen del Equipo TYM")
    st.markdown("Bienvenido al centro de alto rendimiento. Selecciona tu perfil para ver tus métricas.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 Top Distancia (Semana Actual)")
        cols_sem = [c for c in df_base.columns if c.startswith("Sem")]
        if cols_sem:
            ultima = cols_sem[-1]
            # Convertir a numérico para ordenar bien
            df_base[ultima] = pd.to_numeric(df_base[ultima], errors='coerce').fillna(0)
            top5 = df_base.nlargest(5, ultima)[[col_nombre, ultima]]
            st.dataframe(top5.style.format({ultima: "{:.1f} km"}), use_container_width=True, hide_index=True)
            
    with col2:
        st.image("https://images.unsplash.com/photo-1552674605-46d531d0696c?q=80&w=2070&auto=format&fit=crop", caption="Athlos Spirit")

else:
    # --- DASHBOARD PERSONAL COMPLETO ---
    st.title(f"🚀 Panel de Rendimiento: {atleta}")
    
    # 1. IDENTIFICAR ÚLTIMA SEMANA
    cols_sem = [c for c in df_base.columns if c.startswith("Sem")]
    ultima_sem = cols_sem[-1] if cols_sem else "N/A"
    
    # 2. CARGAR DATOS DE TODAS LAS DISCIPLINAS
    # Usamos carga inteligente para no bloquear la app
    df_dist = df_base # Ya cargada
    df_tiempo = cargar_hoja("Tiempo Total")
    df_nat = cargar_hoja("Nat: Distancia")
    df_bici = cargar_hoja("Ciclismo: Distancia")
    df_trote = cargar_hoja("Trote: Distancia")
    
    # --- FILA 1: KPIs GLOBALES (RESUMEN MACRO) ---
    st.subheader(f"📅 Resumen Semana: {ultima_sem}")
    kpi1, kpi2, kpi3 = st.columns(3)
    
    # A. Distancia Total
    row_dist = df_dist[df_dist[col_nombre].astype(str) == atleta].iloc[0]
    val_dist = pd.to_numeric(row_dist.get(ultima_sem, 0), errors='coerce') or 0
    # Promedio Club Distancia
    prom_club_dist = pd.to_numeric(df_dist[ultima_sem], errors='coerce').mean()
    delta_dist = val_dist - prom_club_dist
    
    kpi1.metric("Distancia Total", f"{val_dist:.1f} km", delta=f"{delta_dist:.1f} vs Club")
    
    # B. Tiempo Total
    if df_tiempo is not None:
        row_time = df_tiempo[df_tiempo[col_nombre].astype(str) == atleta].iloc[0]
        val_time_raw = row_time.get(ultima_sem, 0)
        # Convertir a texto bonito
        texto_tiempo = formato_tiempo(val_time_raw)
        kpi2.metric("Tiempo Total", texto_tiempo, "Horas de entrenamiento")
    else:
        kpi2.metric("Tiempo Total", "N/A", "Datos no disp.")

    # C. Carga / Consistencia (Simulado con ranking)
    rank = df_dist[ultima_sem].rank(ascending=False, method='min')
    mi_rank = rank[df_dist[col_nombre].astype(str) == atleta].iloc[0]
    kpi3.metric("Ranking Club", f"#{int(mi_rank)}", "Posición por volumen")

    st.markdown("---")

    # --- FILA 2: DETALLE POR DISCIPLINA (NAT, BICI, TROTE) ---
    st.subheader("🏊‍♂️🚴‍♂️🏃‍♂️ Desglose por Disciplina")
    
    tab_nat, tab_bici, tab_trote = st.tabs(["🏊‍♂️ Natación", "🚴‍♂️ Ciclismo", "🏃‍♂️ Trote"])
    
    # --- PESTAÑA NATACIÓN ---
    with tab_nat:
        if df_nat is not None:
            row = df_nat[df_nat[col_nombre].astype(str) == atleta].iloc[0]
            val = pd.to_numeric(row.get(ultima_sem, 0), errors='coerce') or 0
            
            # Gráfico Miniatura Histórico
            historia = [pd.to_numeric(row.get(c, 0), errors='coerce') or 0 for c in cols_sem]
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric("Volumen Natación", f"{val:.1f} km")
                if len(historia) > 0:
                    st.info(f"Promedio personal: {(sum(historia)/len(historia)):.1f} km/sem")
            with c2:
                fig_nat = px.bar(x=cols_sem, y=historia, title="Histórico Natación")
                fig_nat.update_traces(marker_color='#00a8e8')
                fig_nat.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_nat, use_container_width=True)
        else:
            st.warning("Datos de natación no disponibles.")

    # --- PESTAÑA CICLISMO ---
    with tab_bici:
        if df_bici is not None:
            row = df_bici[df_bici[col_nombre].astype(str) == atleta].iloc[0]
            val = pd.to_numeric(row.get(ultima_sem, 0), errors='coerce') or 0
            historia = [pd.to_numeric(row.get(c, 0), errors='coerce') or 0 for c in cols_sem]
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric("Volumen Ciclismo", f"{val:.1f} km")
            with c2:
                fig_bici = px.line(x=cols_sem, y=historia, markers=True, title="Histórico Ciclismo")
                fig_bici.update_traces(line_color='#e85d04')
                fig_bici.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_bici, use_container_width=True)
        else:
            st.warning("Datos de ciclismo no disponibles.")

    # --- PESTAÑA TROTE ---
    with tab_trote:
        if df_trote is not None:
            row = df_trote[df_trote[col_nombre].astype(str) == atleta].iloc[0]
            val = pd.to_numeric(row.get(ultima_sem, 0), errors='coerce') or 0
            historia = [pd.to_numeric(row.get(c, 0), errors='coerce') or 0 for c in cols_sem]
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric("Volumen Trote", f"{val:.1f} km")
            with c2:
                fig_run = px.area(x=cols_sem, y=historia, title="Histórico Trote")
                fig_run.update_traces(line_color='#9d0208')
                fig_run.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_run, use_container_width=True)
        else:
            st.warning("Datos de trote no disponibles.")

    st.markdown("---")
    
    # --- SECCIÓN 4: ANÁLISIS COMPARATIVO (ATLETA VS CLUB) ---
    st.subheader("⚖️ Comparativa vs. El Club")
    
    # Preparar datos para el gráfico
    promedios = {
        "Natación": pd.to_numeric(df_nat[ultima_sem], errors='coerce').mean() if df_nat is not None else 0,
        "Ciclismo": pd.to_numeric(df_bici[ultima_sem], errors='coerce').mean() if df_bici is not None else 0,
        "Trote": pd.to_numeric(df_trote[ultima_sem], errors='coerce').mean() if df_trote is not None else 0
    }
    
    mis_datos = {
        "Natación": pd.to_numeric(df_nat[df_nat[col_nombre].astype(str) == atleta][ultima_sem], errors='coerce').iloc[0] if df_nat is not None else 0,
        "Ciclismo": pd.to_numeric(df_bici[df_bici[col_nombre].astype(str) == atleta][ultima_sem], errors='coerce').iloc[0] if df_bici is not None else 0,
        "Trote": pd.to_numeric(df_trote[df_trote[col_nombre].astype(str) == atleta][ultima_sem], errors='coerce').iloc[0] if df_trote is not None else 0
    }
    
    df_comp = pd.DataFrame({
        "Disciplina": list(mis_datos.keys()),
        "Tú": list(mis_datos.values()),
        "Promedio Club": list(promedios.values())
    })
    
    # Gráfico de Barras Agrupadas
    fig_comp = px.bar(
        df_comp, 
        x="Disciplina", 
        y=["Tú", "Promedio Club"], 
        barmode="group",
        title=f"Tu desempeño vs Promedio del Club ({ultima_sem})",
        color_discrete_map={"Tú": "#2a9d8f", "Promedio Club": "#264653"}
    )
    st.plotly_chart(fig_comp, use_container_width=True)
