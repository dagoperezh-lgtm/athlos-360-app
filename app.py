# =============================================================================
# 🦅 ATHLOS 360 - V14.0 (SIN CV EN FICHA + FIX NOMBRES)
# =============================================================================
import streamlit as st
import pandas as pd
import os
import math

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="wide")

# ESTILOS CSS
st.markdown("""
<style>
    .cover-title { font-size: 40px; font-weight: bold; text-align: center; color: #1E1E1E; margin-top: 10px; }
    .cover-sub { font-size: 20px; text-align: center; color: #666; margin-bottom: 40px; }
    .main-title { font-size: 28px; font-weight: bold; color: #000; margin-bottom: 5px; }
    .sub-title { font-size: 18px; color: #666; margin-bottom: 20px; border-bottom: 2px solid #FF4B4B; }
    .card-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 15px; }
    .stat-label { font-size: 14px; font-weight: bold; color: #555; }
    .stat-value { font-size: 22px; font-weight: bold; color: #000; }
    .comp-text { font-size: 13px; margin-top: 5px; }
    .pos { color: #008000; font-weight: bold; }
    .neg { color: #D00000; font-weight: bold; }
    .disc-header { background-color: #eee; padding: 8px; font-weight: bold; border-radius: 5px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. GESTIÓN DE SESIÓN ---
if 'club_activo' not in st.session_state:
    st.session_state['club_activo'] = None

# =============================================================================
# 🚪 FASE 1: PORTADA (INSTANTÁNEA)
# =============================================================================
if st.session_state['club_activo'] is None:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo_athlos.png"):
            st.image("logo_athlos.png", use_container_width=True)
        else:
            st.markdown("<div class='cover-title'>ATHLOS 360</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='cover-sub'>Plataforma de Alto Rendimiento</div>", unsafe_allow_html=True)
        
        club_sel = st.selectbox("Selecciona tu Club:", ["Seleccionar...", "TYM Triathlon"])
        
        if club_sel == "TYM Triathlon":
            if st.button("INGRESAR AL DASHBOARD 🚀", type="primary", use_container_width=True):
                st.session_state['club_activo'] = "TYM Triathlon"
                st.rerun()
    st.stop()

# =============================================================================
# 📊 FASE 2: MOTOR DE DATOS
# =============================================================================

ARCHIVO = "06 Sem (tst).xlsx"

@st.cache_data(ttl=60, show_spinner=False)
def get_df_cache(nombre_hoja):
    if not os.path.exists(ARCHIVO): return None
    try:
        with pd.ExcelFile(ARCHIVO, engine='openpyxl') as xls:
            target = next((h for h in xls.sheet_names if nombre_hoja.lower() in h.lower().replace(":","")), None)
            if target:
                df = pd.read_excel(xls, sheet_name=target, dtype=str)
                df.columns = [str(c).strip() for c in df.columns]
                col = next((c for c in df.columns if c.lower() in ['nombre','deportista','atleta']), None)
                if col: df.rename(columns={col: 'Nombre'}, inplace=True)
                return df
    except: return None
    return None

def clean_time(val):
    if pd.isna(val) or str(val).strip() in ['','-','nan','0','00:00:00','None']: return 0.0
    s = str(val).strip().split(' ')[-1]
    try:
        if ':' in s:
            p = [float(x) for x in s.split(':')]
            sec = 0
            if len(p)==3: sec = p[0]*3600 + p[1]*60 + p[2]
            elif len(p)==2: sec = p[0]*60 + p[1]
            return sec / 86400.0
        f = float(s)
        return 0.0 if f > 100 else f
    except: return 0.0

def clean_num(val):
    try: return float(str(val).replace(',','.'))
    except: return 0.0

def fmt_h_m(v):
    if v <= 0.0001: return "-"
    try:
        tot = v * 24
        h = int(tot); m = int((tot - h) * 60)
        return f"{h}h {m}m"
    except: return "-"

def fmt_pace(v, sport):
    if v <= 0.00001: return "-"
    try:
        mins = v * 24 * 60
        m = int(mins); s = int((mins - m) * 60)
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

# =============================================================================
# 🖥️ FASE 3: INTERFAZ DEL CLUB
# =============================================================================

with st.sidebar:
    if os.path.exists("logo_athlos.png"): st.image("logo_athlos.png")
    st.markdown("### 🦁 TYM Triathlon")
    if st.button("🏠 Cerrar Sesión"):
        st.session_state['club_activo'] = None
        st.rerun()
    st.markdown("---")
    
    with st.spinner("Cargando datos..."):
        df_base = get_df_cache("Distancia Total")
    
    if df_base is None:
        st.error("⚠️ Error cargando datos.")
        st.stop()
        
    nombres = sorted([str(x) for x in df_base['Nombre'].unique() if str(x).lower() not in ['nan','0']])
    nombres.insert(0, " Selecciona tu nombre...")
    
    atleta_sel = st.selectbox("Busca tu perfil:", nombres)

if atleta_sel == " Selecciona tu nombre...":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<div class='cover-title'>Bienvenido al {st.session_state['club_activo']}</div>", unsafe_allow_html=True)
    st.markdown("<div class='cover-sub'>Panel de Análisis de Rendimiento V25</div>", unsafe_allow_html=True)
    c1,c2,c3=st.columns([1,2,1])
    with c2:
        st.info("👈 **Para comenzar:** Selecciona un atleta en el menú de la izquierda.")
        if os.path.exists("logo_athlos.png"): st.image("logo_athlos.png", use_container_width=True)

else:
    # --- REPORTE INDIVIDUAL ---
    cols_sem = [c for c in df_base.columns if c.startswith("Sem")]
    ultima_sem = cols_sem[-1] if cols_sem else "N/A"
    
    st.markdown(f"<div class='main-title'>🦅 REPORTE 360°: {atleta_sel}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-title'>Reporte Semanal: {ultima_sem}</div>", unsafe_allow_html=True)

    data = {
        'Global': {'T': get_df_cache("Tiempo Total"), 'D': get_df_cache("Distancia Total"), 'A': get_df_cache("Altimetría Total")},
        'Nat': {'T': get_df_cache("Nat Tiempo") or get_df_cache("Natación"), 'D': get_df_cache("Nat Distancia"), 'R': get_df_cache("Nat Ritmo")},
        'Bici': {'T': get_df_cache("Ciclismo Tiempo") or get_df_cache("Ciclismo"), 'D': get_df_cache("Ciclismo Distancia"), 'E': get_df_cache("Ciclismo Desnivel")},
        'Trote': {'T': get_df_cache("Trote Tiempo") or get_df_cache("Trote"), 'D': get_df_cache("Trote Distancia"), 'R': get_df_cache("Trote Ritmo")}
    }

    # CALCULADORA BLINDADA
    def get_kpi(cat, key, is_t=False):
        df = data[cat][key]
        if df is None: return 0,0,0
        
        # Avg Team
        vals_team = []
        if ultima_sem in df.columns:
            for x in df[ultima_sem]:
                vals_team.append(clean_time(x) if is_t else clean_num(x))
        avg_team = sum(vals_team)/len(vals_team) if vals_team else 0
        
        # Atleta (Case Insensitive)
        mask = df['Nombre'].astype(str).str.lower() == str(atleta_sel).lower()
        row = df[mask]
        
        val_now = 0; avg_hist = 0
        if not row.empty:
            raw = row[ultima_sem].values[0] if ultima_sem in row.columns else 0
            val_now = clean_time(raw) if is_t else clean_num(raw)
            # Hist
            h_vals = []
            for c in cols_sem:
                if c in row.columns:
                    h_vals.append(clean_time(row[c].values[0]) if is_t else clean_num(row[c].values[0]))
            avg_hist = sum(h_vals)/len(h_vals) if h_vals else 0
            
        return val_now, avg_team, avg_hist

    # RENDER
    tv, ta, th = get_kpi('Global', 'T', True)
    dv, da, dh = get_kpi('Global', 'D', False)
    av, aa, ah = get_kpi('Global', 'A', False)
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="card-box"><div class="stat-label">⏱️ Tiempo Total</div><div class="stat-value">{fmt_h_m(tv)}</div><div class="comp-text">👥 Vs Eq: <span class="{ 'pos' if (tv-ta)>=0 else 'neg' }">{fmt_diff(tv-ta, True)}</span><br>📅 Vs Hist: <span class="{ 'pos' if (tv-th)>=0 else 'neg' }">{fmt_diff(tv-th, True)}</span></div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="card-box"><div class="stat-label">📏 Distancia</div><div class="stat-value">{dv:.1f} km</div><div class="comp-text">👥 Vs Eq: <span class="{ 'pos' if (dv-da)>=0 else 'neg' }">{fmt_diff(dv-da)} km</span><br>📅 Vs Hist: <span class="{ 'pos' if (dv-dh)>=0 else 'neg' }">{fmt_diff(dv-dh)} km</span></div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="card-box"><div class="stat-label">⛰️ Altimetría</div><div class="stat-value">{av:.0f} m</div><div class="comp-text">Acumulado Semanal</div></div>""", unsafe_allow_html=True)

    def draw_disc(tit, icon, cat, x_type):
        st.markdown(f"<div class='disc-header'>{icon} {tit}</div>", unsafe_allow_html=True)
        t_v, t_a, t_h = get_kpi(cat, 'T', True)
        d_v, d_a, d_h = get_kpi(cat, 'D', False)
        if x_type == 'elev':
            e_v, e_a, e_h = get_kpi(cat, 'E', False)
            e_lbl, e_fmt = "Desnivel", f"{e_v:.0f} m"
        else:
            e_v, e_a, e_h = get_kpi(cat, 'R', True)
            e_lbl, e_fmt = "Ritmo", fmt_pace(e_v, 'swim' if x_type=='swim' else 'run')
        st.markdown(f"""<table style="width:100%; font-size:14px;"><tr style="color:#666; border-bottom:1px solid #ddd;"><th style="text-align:left">Métrica</th><th style="text-align:left">Dato</th><th style="text-align:left">Vs Equipo</th><th style="text-align:left">Vs Histórico</th></tr><tr><td><b>Tiempo</b></td><td>{fmt_h_m(t_v)}</td><td class="{ 'pos' if (t_v-t_a)>=0 else 'neg' }">{fmt_diff(t_v-t_a, True)}</td><td class="{ 'pos' if (t_v-t_h)>=0 else 'neg' }">{fmt_diff(t_v-t_h, True)}</td></tr><tr><td><b>Distancia</b></td><td>{d_v:.1f} km</td><td class="{ 'pos' if (d_v-d_a)>=0 else 'neg' }">{fmt_diff(d_v-d_a)}</td><td class="{ 'pos' if (d_v-d_h)>=0 else 'neg' }">{fmt_diff(d_v-d_h)}</td></tr><tr><td><b>{e_lbl}</b></td><td>{e_fmt}</td><td>-</td><td>-</td></tr></table>""", unsafe_allow_html=True)

    c_n, c_b, c_r = st.columns(3)
    with c_n: draw_disc("NATACIÓN", "🏊", "Nat", "swim")
    with c_b: draw_disc("CICLISMO", "🚴", "Bici", "elev")
    with c_r: draw_disc("TROTE", "🏃", "Trote", "run")
