# =============================================================================
# 🦅 ATHLOS 360 - V21.1 (FIX LOGO GIGANTE EN MÓVIL)
# =============================================================================
import streamlit as st
import pandas as pd
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="wide")

# ESTILOS CSS
st.markdown("""
<style>
    .cover-title { font-size: 45px; font-weight: bold; text-align: center; color: #003366; margin-top: 10px; }
    .cover-sub { font-size: 22px; text-align: center; color: #666; margin-bottom: 40px; }
    .main-title { font-size: 32px; font-weight: bold; color: #000; margin-bottom: 5px; }
    .sub-title { font-size: 18px; color: #666; margin-bottom: 15px; }
    .rank-section-title { font-size: 16px; font-weight: bold; color: #003366; text-transform: uppercase; margin-bottom: 8px; }
    .rank-badge-lg { background-color: #003366; color: white; padding: 10px 20px; border-radius: 10px; font-size: 22px; font-weight: bold; margin-right: 15px; display: inline-block; box-shadow: 0 3px 6px rgba(0,0,0,0.2); border-left: 5px solid #FF4B4B; }
    .rank-container { margin-bottom: 25px; padding-bottom: 15px; border-bottom: 3px solid #003366; }
    .card-box { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border: 1px solid #e0e0e0; border-left: 5px solid #003366; margin-bottom: 15px; }
    .stat-label { font-size: 15px; font-weight: bold; color: #555; text-transform: uppercase; }
    .stat-value { font-size: 26px; font-weight: bold; color: #000; }
    .comp-text { font-size: 14px; margin-top: 5px; color: #444; }
    .pos { color: #008000; font-weight: bold; }
    .neg { color: #B22222; font-weight: bold; }
    .disc-header { background-color: #E6F0FA; padding: 10px 15px; font-weight: bold; font-size: 18px; border-radius: 8px; margin-top: 15px; color: #003366; }
    .kpi-club-box { background-color: #eef; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
    .kpi-club-val { font-size: 32px; font-weight: bold; color: #003366; }
    .kpi-club-lbl { font-size: 14px; color: #666; font-weight: bold; text-transform: uppercase; }
    .top10-header { background-color: #003366; color: white; padding: 10px; border-radius: 5px 5px 0 0; font-weight: bold; }
    .top10-table { width: 100%; border-collapse: collapse; background-color: white; border: 1px solid #ddd; }
    .top10-table td, .top10-table th { padding: 8px; border-bottom: 1px solid #eee; text-align: left; font-size: 14px; }
    .alert-box { padding: 10px; border-radius: 5px; margin-bottom: 5px; font-size: 13px; font-weight: bold; }
    .alert-red { background-color: #ffebee; color: #c62828; border: 1px solid #ffcdd2; }
    .coach-section { margin-top: 30px; border-top: 2px dashed #ccc; padding-top: 20px; }
</style>
""", unsafe_allow_html=True)

# SESIÓN
if 'club_activo' not in st.session_state: st.session_state['club_activo'] = None
if 'vista_actual' not in st.session_state: st.session_state['vista_actual'] = 'home'

# --- 📌 IMÁGENES ---
LOGO_ATHLOS = "logo_athlos.png"
LOGO_TYM    = "Tym Logo.jpg"

# --- HELPER: RENDERIZADOR DE LOGOS SIDEBAR ---
def render_logos_sidebar():
    """Dibuja los logos en el sidebar con control de tamaño móvil."""
    if os.path.exists(LOGO_ATHLOS): 
        st.sidebar.image(LOGO_ATHLOS, use_container_width=True)
    
    if st.session_state['club_activo'] == "TYM Triathlon":
        st.sidebar.markdown("---")
        if os.path.exists(LOGO_TYM):
            # FIX: Usamos width=150 en lugar de use_container_width
            # Esto evita que en el celular se estire al 100% de la pantalla
            c1,c2,c3 = st.sidebar.columns([1,2,1])
            with c2: st.image(LOGO_TYM, width=150)
        st.sidebar.markdown("<h3 style='text-align: center; color: #003366;'>TYM Triathlon</h3>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

# --- 1. PORTADA GLOBAL ---
if st.session_state['club_activo'] is None:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists(LOGO_ATHLOS): st.image(LOGO_ATHLOS, use_container_width=True)
        else: st.markdown("<div class='cover-title'>ATHLOS 360</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='cover-sub'>Plataforma de Alto Rendimiento</div>", unsafe_allow_html=True)
        
        club_sel = st.selectbox("Selecciona tu Club:", ["Seleccionar...", "TYM Triathlon"])
        
        if club_sel == "TYM Triathlon":
            if os.path.exists(LOGO_TYM):
                # En portada también aplicamos width fijo para evitar sorpresas
                cc1, cc2, cc3 = st.columns([1,1,1])
                with cc2: st.image(LOGO_TYM, width=150)
            else:
                st.warning(f"⚠️ Sube el archivo '{LOGO_TYM}'")

            if st.button("INGRESAR 🚀", type="primary", use_container_width=True):
                st.session_state['club_activo'] = "TYM Triathlon"
                st.session_state['vista_actual'] = 'menu'
                st.rerun()
    st.stop()

# --- 2. MOTOR DE DATOS (SAFE MODE) ---
ARCHIVO = "06 Sem (tst).xlsx"

@st.cache_data(ttl=60, show_spinner=False)
def get_df_safe(nombre_hoja):
    if not os.path.exists(ARCHIVO): return None
    try:
        with pd.ExcelFile(ARCHIVO, engine='openpyxl') as xls:
            key = next((k for k in xls.sheet_names if nombre_hoja.lower() in k.lower().replace(":","")), None)
            if key:
                d = pd.read_excel(xls, sheet_name=key, dtype=str)
                d.columns = [str(c).strip() for c in d.columns]
                col = next((c for c in d.columns if c.lower() in ['nombre','deportista','atleta']), None)
                if col: d.rename(columns={col: 'Nombre'}, inplace=True)
                return d
    except: return None
    return None

def clean_time(val):
    if pd.isna(val): return 0.0
    s = str(val).strip().split(' ')[-1]
    try:
        if ':' in s:
            p = [float(x) for x in s.split(':')]
            sec = p[0]*3600 + p[1]*60 + (p[2] if len(p)>2 else 0)
            return sec / 86400.0
        return 0.0 if float(s) > 100 else float(s)
    except: return 0.0

def clean_num(val):
    try: return float(str(val).replace(',','.'))
    except: return 0.0

def fmt_h_m(v):
    if v <= 0.0001: return "-"
    try:
        tot = v * 24; h = int(tot); m = int((tot - h) * 60)
        return f"{h}h {m:02d}m"
    except: return "-"

def fmt_pace(v, sport):
    if v <= 0.00001: return "-"
    try:
        tot = v * 24 * 60; m = int(tot); s = int((tot - m) * 60)
        u = "/100m" if sport=='swim' else "/km"
        return f"{m}:{s:02d} {u}"
    except: return "-"

def fmt_diff(v, is_t=False):
    if abs(v) < 0.0001: return "-"
    signo = "+" if v > 0 else "-"
    v = abs(v)
    if is_t:
        h = int(v * 24); m = int((v * 24 * 60) % 60)
        return f"{signo}{h}h {m}m"
    return f"{signo}{v:.1f}"

# CARGA DE DATOS
with st.spinner("Cargando datos..."):
    data = {
        'Global': {'T': get_df_safe("Tiempo Total"), 'D': get_df_safe("Distancia Total"), 'A': get_df_safe("Altimetría Total")},
        'Nat': {'T': get_df_safe("Nat Tiempo") or get_df_safe("Natación"), 'D': get_df_safe("Nat Distancia"), 'R': get_df_safe("Nat Ritmo")},
        'Bici': {
            'T': get_df_safe("Ciclismo Tiempo") or get_df_safe("Ciclismo"), 
            'D': get_df_safe("Ciclismo Distancia"), 
            'E': get_df_safe("Ciclismo Desnivel"),
            'Max': get_df_safe("Ciclismo Max")
        },
        'Trote': {
            'T': get_df_safe("Trote Tiempo") or get_df_safe("Trote"), 
            'D': get_df_safe("Trote Distancia"), 
            'R': get_df_safe("Trote Ritmo"), 
            'E': get_df_safe("Trote Desnivel"),
            'Max': get_df_safe("Trote Max")
        }
    }

df_base = data['Global']['D']
if df_base is None:
    st.error("⚠️ No se pudo leer el archivo de datos. Por favor, regenera el Excel en Colab.")
    st.stop()

cols_sem = [c for c in df_base.columns if c.startswith("Sem")]
ultima_sem = cols_sem[-1] if cols_sem else "N/A"

# HEADER DE NAVEGACIÓN (GLOBAL)
if st.session_state['vista_actual'] != 'home' and st.session
