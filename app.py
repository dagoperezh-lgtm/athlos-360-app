# =============================================================================
# 🦅 ATHLOS 360 - APP V8.0 (REPLICA EXACTA DEL REPORTE V25)
# =============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Athlos 360 Report", page_icon="🦅", layout="wide", initial_sidebar_state="collapsed")

# Estilos para imitar el reporte de Word
st.markdown("""
<style>
    .big-metric { font-size: 26px !important; font-weight: bold; color: #1E1E1E; }
    .sub-metric { font-size: 14px !important; color: #666; }
    .card { background-color: #f9f9f9; padding: 15px; border-radius: 10px; border-left: 5px solid #FF4B4B; margin-bottom: 10px; }
    .header-discipline { background-color: #e0e0e0; padding: 5px 10px; border-radius: 5px; font-weight: bold; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
ARCHIVO = "06 Sem (tst).xlsx"

@st.cache_data(ttl=60)
def get_data(hoja_keyword):
    """Busca y carga la hoja correcta (ej: busca 'Ritmo' encuentra 'Nat Ritmo')"""
    if not os.path.exists(ARCHIVO): return None
    try:
        xls = pd.ExcelFile(ARCHIVO, engine='openpyxl')
        # Buscar coincidencia flexible
        target = next((h for h in xls.sheet_names if hoja_keyword.lower() in h.lower()), None)
        if target:
            df = pd.read_excel(xls, sheet_name=target)
            df.columns = [str(c).strip() for c in df.columns]
            # Normalizar nombre
            c_nom = next((c for c in df.columns if c.lower() in ['nombre','deportista','atleta']), None)
            if c_nom: df.rename(columns={c_nom: 'Nombre'}, inplace=True)
            return df
    except: pass
    return None

# --- 3. FORMATTERS (TRADUCTORES DE NÚMEROS RAROS) ---
def fmt_tiempo(val):
    """0.52 -> 12h 30m"""
    if pd.isna(val) or val == 0: return "-"
    try:
        horas = float(val) * 24
        h = int(horas)
        m = int((horas - h) * 60)
        return f"{h}h {m}m"
    except: return "-"

def fmt_ritmo(val, tipo="run"):
    """0.0034 -> 5:00 min/km"""
    if pd.isna(val) or val == 0: return "-"
    try:
        # Excel tiempo es fracción de día. 
        # Ritmo = minutos por km (o 100m)
        total_min = float(val) * 24 * 60
        m = int(total_min)
        s = int((total_min - m) * 60)
        suffix = "min/100m" if tipo == "swim" else "min/km"
        return f"{m}:{s:02d} {suffix}"
    except: return "-"

def fmt_num(val, decimales=1):
    try: return f"{float(val):.{decimales}f}"
    except: return "-"

# --- 4. CARGA DE TODOS LOS DATOS (EL CEREBRO DE LA V25) ---
# Aquí cargamos lo que faltaba: Ritmos, Desnivel, CV
dfs = {
    "Dist": get_data("Distancia Total"),
    "Time": get_data("Tiempo Total"),
    "Alt":  get_data("Altimetría Total"), # ¡Recuperado!
    "CV":   get_data("CV"),               # ¡Recuperado!
    
    # Natación
    "N_Dist": get_data("Nat Distancia"),
    "N_Time": get_data("Nat: Tiempo"),    # A veces es Nat Tiempo o Nat: Tiempo
    "N_Pace": get_data("Nat Ritmo"),      # ¡Recuperado!
    
    # Ciclismo
    "B_Dist": get_data("Ciclismo Distancia"),
    "B_Time": get_data("Ciclismo Tiempo"),
    "B_Elev": get_data("Ciclismo Desnivel"), # ¡Recuperado!
    
    # Trote
    "R_Dist": get_data("Trote Distancia"),
    "R_Time": get_data("Trote Tiempo"),
    "R_Pace": get_data("Trote Ritmo"),       # ¡Recuperado!
}

# Fix para Nat Tiempo si falla el nombre exacto
if dfs["N_Time"] is None: dfs["N_Time"] = get_data("Natación") 
if dfs["B_Time"] is None: dfs["B_Time"] = get_data("Ciclismo")
if dfs["R_Time"] is None: dfs["R_Time"] = get_data("Trote")

# --- 5. LÓGICA DE SELECCIÓN ---
if "club_ok" not in st.session_state: st.session_state["club_ok"] = False

if not st.session_state["club_ok"]:
    # --- PORTADA DE RECEPCIÓN ---
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if os.path.exists("logo_athlos.png"): st.image("logo_athlos.png", use_container_width=True)
        st.title("🦅 ATHLOS 360")
        st.markdown("---")
        club = st.selectbox("Selecciona tu Club:", ["Seleccionar...", "TYM Triathlon"])
        if club == "TYM Triathlon":
            if st.button("INGRESAR"):
                st.session_state["club_ok"] = True
                st.rerun()
else:
    # --- DASHBOARD PRINCIPAL ---
    with st.sidebar:
        if os.path.exists("logo_athlos.png"): st.image("logo_athlos.png")
        if st.button("🏠 Salir"): 
            st.session_state["club_ok"] = False
            st.rerun()
        
        st.markdown("---")
        
        # Selector Atleta
        base = dfs["Dist"]
        if base is None: st.error("Sin datos base"); st.stop()
        
        nombres = sorted([str(x) for x in base['Nombre'].unique() if str(x).lower() not in ['nan','0']])
        atleta = st.selectbox("Selecciona Atleta:", nombres)

    # --- PANTALLA REPORTE V25 ---
    st.title(f"👤 {atleta}")
    
    # Identificar Semanas
    cols_sem = [c for c in base.columns if c.startswith("Sem")]
    if not cols_sem: st.error("No hay historia"); st.stop()
    ultima = cols_sem[-1]
    st.markdown(f"**Reporte Semanal: {ultima}**")
    st.markdown("---")

    # FUNCIÓN AUXILIAR PARA EXTRAER DATOS V25
    def get_val(df_dict, key, col):
        if df_dict[key] is None: return 0
        row = df_dict[key][df_dict[key]['Nombre'] == atleta]
        if row.empty: return 0
        return pd.to_numeric(row[col].values[0], errors='coerce') or 0

    def get_avg_team(df_dict, key, col):
        if df_dict[key] is None: return 0
        return pd.to_numeric(df_dict[key][col], errors='coerce').mean()

    def get_avg_hist(df_dict, key):
        if df_dict[key] is None: return 0
        row = df_dict[key][df_dict[key]['Nombre'] == atleta]
        if row.empty: return 0
        # Promedio de todas las semanas históricas
        vals = [pd.to_numeric(row[c].values[0], errors='coerce') or 0 for c in cols_sem]
        return sum(vals)/len(vals) if vals else 0

    # --- SECCIÓN 1: RESUMEN GLOBAL (Encabezado V25) ---
    val_t = get_val(dfs, "Time", ultima)
    val_d = get_val(dfs, "Dist", ultima)
    val_a = get_val(dfs, "Alt", ultima)
    
    # Comparativas Globales (Distancia)
    avg_team_d = get_avg_team(dfs, "Dist", ultima)
    avg_hist_d = get_avg_hist(dfs, "Dist")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("⏱️ Tiempo Total", fmt_tiempo(val_t))
    col2.metric("📏 Distancia", f"{val_d:.1f} km", delta=f"{val_d - avg_team_d:.1f} vs Equipo")
    col3.metric("⛰️ Altimetría", f"{val_a:.0f} m", delta=f"{val_d - avg_hist_d:.1f} vs Histórico (Dist)")
    
    st.markdown("---")

    # --- SECCIÓN 2: DESGLOSE POR DISCIPLINA (TABLAS V25) ---
    
    # Función para crear la "Ficha Técnica" por deporte
    def ficha_tecnica(titulo, icono, keys, tipo_ritmo=None):
        st.markdown(f"### {icono} {titulo}")
        
        # Extraer valores actuales
        t = get_val(dfs, keys['t'], ultima) # Tiempo
        d = get_val(dfs, keys['d'], ultima) # Distancia
        
        # Ritmo o Altitud
        extra_val = 0
        extra_lbl = ""
        extra_fmt = ""
        
        if 'p' in keys: # Pace
            extra_val = get_val(dfs, keys['p'], ultima)
            extra_lbl = "Ritmo"
            extra_fmt = lambda x: fmt_ritmo(x, tipo_ritmo)
        elif 'e' in keys: # Elevation (Cycling)
            extra_val = get_val(dfs, keys['e'], ultima)
            extra_lbl = "Desnivel"
            extra_fmt = lambda x: f"{x:.0f} m"

        # Comparativas (Usamos Distancia como proxy de carga)
        avg_team = get_avg_team(dfs, keys['d'], ultima)
        avg_hist = get_avg_hist(dfs, keys['d'])
        
        # Layout de Tarjeta
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tiempo", fmt_tiempo(t))
        c2.metric("Distancia", f"{d:.1f} km")
        if extra_lbl:
            c3.metric(extra_lbl, extra_fmt(extra_val))
        
        # Comparativa Texto
        diff_team = d - avg_team
        diff_hist = d - avg_hist
        
        color_team = "green" if diff_team >= 0 else "red"
        color_hist = "blue" if diff_hist >= 0 else "orange"
        
        c4.markdown(f"""
        <div style="font-size:12px">
        👥 <b>Vs Equipo:</b> <span style='color:{color_team}'>{diff_team:+.1f} km</span><br>
        📅 <b>Vs Histórico:</b> <span style='color:{color_hist}'>{diff_hist:+.1f} km</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Mini Gráfico Histórico
        row = dfs[keys['d']][dfs[keys['d']]['Nombre'] == atleta]
        if not row.empty:
            y = [pd.to_numeric(row[c].values[0], errors='coerce') or 0 for c in cols_sem]
            fig = px.area(x=cols_sem, y=y, height=150)
            fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False, xaxis_visible=False, yaxis_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
        st.markdown("---")

    # 1. NATACIÓN
    ficha_tecnica("NATACIÓN", "🏊", {'t': 'N_Time', 'd': 'N_Dist', 'p': 'N_Pace'}, "swim")
    
    # 2. CICLISMO (Aquí mostramos Desnivel en vez de Ritmo)
    ficha_tecnica("CICLISMO", "🚴", {'t': 'B_Time', 'd': 'B_Dist', 'e': 'B_Elev'})
    
    # 3. TROTE
    ficha_tecnica("TROTE", "🏃", {'t': 'R_Time', 'd': 'R_Dist', 'p': 'R_Pace'}, "run")

    # --- SECCIÓN 3: CONSISTENCIA (CV) ---
    val_cv = get_val(dfs, "CV", ultima)
    avg_cv = get_avg_team(dfs, "CV", ultima)
    
    st.subheader("⚖️ CONSISTENCIA (CV)")
    col_cv, col_insight = st.columns([1, 2])
    
    with col_cv:
        st.metric("CV Actual", f"{val_cv:.2f}", delta=f"{val_cv - avg_cv:.2f} vs Promedio")
    
    with col_insight:
        st.info("💡 **Insight:** La consistencia es la clave del rendimiento. Un CV cercano a 1.0 indica un equilibrio óptimo entre disciplinas.")
