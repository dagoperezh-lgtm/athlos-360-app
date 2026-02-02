# =============================================================================
# 🦅 ATHLOS 360 - APP V7.0 (LA RECONSTRUCCIÓN TOTAL)
# =============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(
    page_title="Athlos 360",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed" # Barra lateral oculta al inicio (Efecto Portada)
)

# Estilo CSS para recuperar la elegancia del V25
st.markdown("""
<style>
    .big-font { font-size: 20px !important; font-weight: bold; }
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        height: 50px;
        font-size: 18px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. GESTIÓN DE ESTADO (Para la Portada) ---
if 'club_seleccionado' not in st.session_state:
    st.session_state['club_seleccionado'] = None

# --- 3. FUNCIONES DE DATOS (BLINDADAS) ---
ARCHIVO = "06 Sem (tst).xlsx"

@st.cache_data(ttl=60)
def cargar_datos(nombre_hoja):
    if not os.path.exists(ARCHIVO): return None
    try:
        df = pd.read_excel(ARCHIVO, sheet_name=nombre_hoja, engine='openpyxl')
        df.columns = [str(c).strip() for c in df.columns]
        # Normalizar nombre de columna principal
        col = next((c for c in df.columns if c.lower() in ['nombre','deportista','atleta']), None)
        if col: df.rename(columns={col: 'Nombre'}, inplace=True)
        return df
    except: return None

def fmt_tiempo(val_excel):
    """Convierte 0.5 -> 12h 00m"""
    if pd.isna(val_excel) or val_excel == 0: return "0h 0m"
    try:
        tot = float(val_excel) * 24
        h = int(tot)
        m = int((tot - h) * 60)
        return f"{h}h {m}m"
    except: return "0h 0m"

# --- 4. PORTADA (RECEPCIÓN) ---
if st.session_state['club_seleccionado'] is None:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if os.path.exists("logo_athlos.png"):
            st.image("logo_athlos.png", use_container_width=True)
        else:
            st.title("🦅 ATHLOS 360")
        
        st.markdown("<h3 style='text-align: center;'>Plataforma de Alto Rendimiento</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        club = st.selectbox("Selecciona tu Club para ingresar:", ["Seleccionar...", "TYM Triathlon", "Demo Team"])
        
        if club == "TYM Triathlon":
            if st.button("INGRESAR AL DASHBOARD 🚀"):
                st.session_state['club_seleccionado'] = club
                st.rerun()
        elif club == "Demo Team":
            st.warning("Acceso restringido.")

# --- 5. DASHBOARD PRINCIPAL (SOLO SI HAY CLUB) ---
else:
    # Habilitar barra lateral ahora sí
    with st.sidebar:
        if os.path.exists("logo_athlos.png"): st.image("logo_athlos.png")
        st.header(f"📍 {st.session_state['club_seleccionado']}")
        
        if st.button("🏠 Cambiar Club"):
            st.session_state['club_seleccionado'] = None
            st.rerun()
        
        st.markdown("---")
        
        # Cargar Base
        df_dist = cargar_datos("Distancia Total")
        if df_dist is None:
            st.error("⚠️ Error cargando datos.")
            st.stop()
            
        # Selector Atleta
        lista_atletas = sorted([str(x) for x in df_dist['Nombre'].unique() if str(x).lower() not in ['nan','0']])
        lista_atletas.insert(0, "📊 Visión General del Club")
        
        atleta = st.selectbox("Selecciona Atleta:", lista_atletas)

    # --- LÓGICA DE VISTAS ---
    
    # A. VISTA DE CLUB
    if atleta == "📊 Visión General del Club":
        st.title("🦅 Resumen del Equipo")
        
        cols_sem = [c for c in df_dist.columns if c.startswith("Sem")]
        if cols_sem:
            ultima = cols_sem[-1]
            # Convertir a numérico seguro
            df_dist[ultima] = pd.to_numeric(df_dist[ultima], errors='coerce').fillna(0)
            
            # KPIs Club
            total_km = df_dist[ultima].sum()
            prom_km = df_dist[ultima].mean()
            
            k1, k2 = st.columns(2)
            k1.metric("Volumen Total del Equipo", f"{total_km:,.0f} km")
            k2.metric("Promedio por Atleta", f"{prom_km:.1f} km")
            
            st.subheader(f"🏆 Top 10 Distancia ({ultima})")
            top10 = df_dist.nlargest(10, ultima)[['Nombre', ultima]].set_index('Nombre')
            st.bar_chart(top10)
        else:
            st.info("No hay datos históricos disponibles.")

    # B. VISTA DE ATLETA (RECONSTRUCCIÓN REPORTE V25)
    else:
        st.title(f"👤 {atleta}")
        
        # Cargar resto de datos
        df_tiempo = cargar_datos("Tiempo Total")
        df_nat = cargar_datos("Nat Distancia")
        df_bici = cargar_datos("Ciclismo Distancia")
        df_run = cargar_datos("Trote Distancia")
        df_alt = cargar_datos("Altimetría Total") # Recuperamos altimetría
        
        # Identificar semana
        cols_sem = [c for c in df_dist.columns if c.startswith("Sem")]
        ultima_sem = cols_sem[-1] if cols_sem else "N/A"
        
        # --- CÁLCULOS V25 (VS EQUIPO, VS HISTÓRICO) ---
        
        # 1. Distancia
        row_d = df_dist[df_dist['Nombre']==atleta]
        val_d = pd.to_numeric(row_d[ultima_sem].values[0], errors='coerce') if not row_d.empty else 0
        avg_club_d = df_dist[ultima_sem].mean()
        # Histórico personal (promedio de todas las semanas)
        hist_d = row_d[cols_sem].mean(axis=1).values[0] if not row_d.empty else 0
        
        # 2. Tiempo
        val_t = 0
        txt_t = "0h 0m"
        if df_tiempo is not None:
            row_t = df_tiempo[df_tiempo['Nombre']==atleta]
            if not row_t.empty:
                val_t = pd.to_numeric(row_t[ultima_sem].values[0], errors='coerce')
                txt_t = fmt_tiempo(val_t)
        
        # 3. Altimetría
        val_alt = 0
        if df_alt is not None:
            row_a = df_alt[df_alt['Nombre']==atleta]
            if not row_a.empty:
                val_alt = pd.to_numeric(row_a[ultima_sem].values[0], errors='coerce')

        # --- TARJETAS PRINCIPALES ---
        st.markdown(f"### 📅 Reporte Semanal: {ultima_sem}")
        
        c1, c2, c3 = st.columns(3)
        
        c1.metric("⏱️ Tiempo Total", txt_t)
        c2.metric("📏 Distancia Total", f"{val_d:.1f} km", delta=f"{val_d - avg_club_d:.1f} vs Club")
        c3.metric("⛰️ Altimetría", f"{val_alt:.0f} m")
        
        st.info(f"📊 **Análisis V25:** Tu promedio histórico es **{hist_d:.1f} km/sem**. Estás {'por encima' if val_d > hist_d else 'por debajo'} de tu media anual.")
        
        st.markdown("---")
        
        # --- DESGLOSE POR DISCIPLINA (TABLAS Y GRÁFICOS) ---
        t1, t2, t3 = st.tabs(["🏊‍♂️ Natación", "🚴‍♂️ Ciclismo", "🏃‍♂️ Trote"])
        
        def render_discipline(df_disc, titulo, color, icono):
            if df_disc is None: return
            row = df_disc[df_disc['Nombre']==atleta]
            if row.empty:
                st.warning("Sin datos")
                return
            
            # Datos actuales
            val_now = pd.to_numeric(row[ultima_sem].values[0], errors='coerce')
            avg_club = pd.to_numeric(df_disc[ultima_sem], errors='coerce').mean()
            
            # Historial para gráfico
            y_vals = []
            for c in cols_sem:
                v = pd.to_numeric(row[c].values[0], errors='coerce')
                y_vals.append(v if pd.notnull(v) else 0)
                
            col_a, col_b = st.columns([1, 2])
            
            with col_a:
                st.metric(f"{icono} Distancia {titulo}", f"{val_now:.1f} km", delta=f"{val_now - avg_club:.1f} vs Club")
                st.write(f"**Promedio Club:** {avg_club:.1f} km")
                
            with col_b:
                fig = px.area(x=cols_sem, y=y_vals, title=f"Evolución {titulo}")
                fig.update_traces(line_color=color)
                st.plotly_chart(fig, use_container_width=True)

        with t1: render_discipline(df_nat, "Natación", "#00a8e8", "🏊")
        with t2: render_discipline(df_bici, "Ciclismo", "#e85d04", "🚴")
        with t3: render_discipline(df_run, "Trote", "#d90429", "🏃")
        
        # --- INSIGHT FINAL (RECUPERADO DEL REPORTE V25) ---
        st.markdown("---")
        st.success("💡 **Insight:** La consistencia es el camino al éxito. Mantén el foco en tus objetivos a largo plazo.")
