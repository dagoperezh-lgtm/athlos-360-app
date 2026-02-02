# =============================================================================
# 🦅 ATHLOS 360 - V15.1 (ESTILO PRO: AZUL + RANKINGS GRANDES)
# =============================================================================
import streamlit as st
import pandas as pd
import os
import math

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="wide")

# ESTILOS CSS (DISEÑO MEJORADO)
st.markdown("""
<style>
    /* PORTADA */
    .cover-title { font-size: 45px; font-weight: bold; text-align: center; color: #003366; margin-top: 10px; }
    .cover-sub { font-size: 22px; text-align: center; color: #666; margin-bottom: 40px; }
    
    /* ENCABEZADOS */
    .main-title { font-size: 32px; font-weight: bold; color: #000; margin-bottom: 5px; }
    .sub-title { font-size: 18px; color: #666; margin-bottom: 15px; }
    
    /* RANKINGS (NUEVO DISEÑO) */
    .rank-container { 
        margin-bottom: 25px; 
        padding-bottom: 15px; 
        border-bottom: 3px solid #003366; /* Línea Azul Marino */
    }
    .rank-badge { 
        background-color: #003366; /* Azul Marino Institucional */
        color: white; 
        padding: 8px 18px; 
        border-radius: 8px; 
        font-size: 20px; /* TEXTO MÁS GRANDE */
        font-weight: bold; 
        margin-right: 15px; 
        display: inline-block;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    /* TARJETAS DE DATOS */
    .card-box { 
        background-color: #f8f9fa; 
        padding: 18px; 
        border-radius: 10px; 
        border: 1px solid #e0e0e0; 
        border-left: 5px solid #003366; /* Borde Azul */
        margin-bottom: 15px; 
    }
    .stat-label { font-size: 15px; font-weight: bold; color: #555; text-transform: uppercase; }
    .stat-value { font-size: 26px; font-weight: bold; color: #000; }
    .comp-text { font-size: 14px; margin-top: 5px; color: #444; }
    
    /* COLORES DE COMPARATIVA */
    .pos { color: #008000; font-weight: bold; } /* Verde */
    .neg { color: #B22222; font-weight: bold; } /* Rojo oscuro discreto para negativos */
    
    /* ENCABEZADO DE DISCIPLINA */
    .disc-header { 
        background-color: #E6F0FA; /* Azul muy suave */
        padding: 10px 15px; 
        font-weight: bold; 
        font-size: 18px;
        border-radius: 8px; 
        margin-top: 15px; 
        color: #003366;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. GESTIÓN DE SESIÓN ---
if 'club_activo' not in st.session_state:
    st.session_state['club_activo'] = None

# =============================================================================
# 🚪 FASE 1: PORTADA
# =============================================================================
if st.session_state['club_activo'] is None:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo_athlos.png"): st.image("logo_athlos.png", use_container_width=True)
        else: st.markdown("<div class='cover-title'>ATHLOS 360</div>", unsafe_allow_html=True)
        st.markdown("<div class='cover-sub'>Plataforma de Alto Rendimiento</div>", unsafe_allow_html=True)
        
        if st.selectbox("Selecciona tu Club:", ["Seleccionar...", "TYM Triathlon"]) == "TYM Triathlon":
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

# --- HERRAMIENTAS DE LIMPIEZA ---
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
# 🖥️ FASE 3: INTERFAZ
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
    
    if df_base is None: st.error("⚠️ Error cargando datos."); st.stop()
        
    nombres = sorted([str(x) for x in df_base['Nombre'].unique() if str(x).lower() not in ['nan','0']])
    nombres.insert(0, " Selecciona tu nombre...")
    atleta_sel = st.selectbox("Busca tu perfil:", nombres)

if atleta_sel == " Selecciona tu nombre...":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<div class='cover-title'>Bienvenido al {st.session_state['club_activo']}</div>", unsafe_allow_html=True)
    st.markdown("<div class='cover-sub'>Panel de Análisis de Rendimiento V25</div>", unsafe_allow_html=True)
    c1,c2,c3=st.columns([1,2,1])
    with c2: st.info("👈 **Para comenzar:** Selecciona un atleta en el menú de la izquierda.")

else:
    # --- REPORTE DEL ATLETA ---
    cols_sem = [c for c in df_base.columns if c.startswith("Sem")]
    ultima_sem = cols_sem[-1] if cols_sem else "N/A"
    
    # 1. CARGA DE DATOS COMPLETOS
    data = {
        'Global': {'T': get_df_cache("Tiempo Total"), 'D': get_df_cache("Distancia Total"), 'A': get_df_cache("Altimetría Total")},
        'Nat': {'T': get_df_cache("Nat Tiempo") or get_df_cache("Natación"), 'D': get_df_cache("Nat Distancia"), 'R': get_df_cache("Nat Ritmo")},
        'Bici': {'T': get_df_cache("Ciclismo Tiempo") or get_df_cache("Ciclismo"), 'D': get_df_cache("Ciclismo Distancia"), 'E': get_df_cache("Ciclismo Desnivel")},
        'Trote': {'T': get_df_cache("Trote Tiempo") or get_df_cache("Trote"), 'D': get_df_cache("Trote Distancia"), 'R': get_df_cache("Trote Ritmo")}
    }

    # 2. CÁLCULO DE RANKINGS (Globales)
    def get_rank(df_in):
        if df_in is None or ultima_sem not in df_in.columns: return "-"
        df_rank = df_in.copy()
        sample = str(df_rank[ultima_sem].iloc[0])
        is_time = ':' in sample
        df_rank['sort_val'] = df_rank[ultima_sem].apply(lambda x: clean_time(x) if is_time else clean_num(x))
        df_rank['rank'] = df_rank['sort_val'].rank(ascending=False, method='min')
        mask = df_rank['Nombre'].astype(str).str.lower() == str(atleta_sel).lower()
        if not df_rank[mask].empty:
            r = int(df_rank[mask]['rank'].values[0])
            return f"#{r}"
        return "-"

    rank_dist = get_rank(data['Global']['D'])
    rank_time = get_rank(data['Global']['T'])

    # 3. HEADER CON RANKINGS (ESTILO AZUL Y GRANDE)
    st.markdown(f"<div class='main-title'>🦅 REPORTE 360°: {atleta_sel}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-title'>Reporte Semanal: {ultima_sem}</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class='rank-container'>
        <span class='rank-badge'>🏆 Posición (Km): {rank_dist}</span>
        <span class='rank-badge'>⏱️ Posición (Tiempo): {rank_time}</span>
    </div>
    """, unsafe_allow_html=True)

    # 4. CALCULADORA KPIs
    def get_kpi(cat, key, is_t=False):
        df = data[cat][key]
        if df is None: return 0,0,0
        vals_t = [clean_time(x) if is_t else clean_num(x) for x in df[ultima_sem]] if ultima_sem in df.columns else []
        avg_t = sum(vals_t)/len(vals_t) if vals_t else 0
        row = df[df['Nombre'].astype(str).str.lower() == str(atleta_sel).lower()]
        val, avg_h = 0, 0
        if not row.empty:
            val = clean_time(row[ultima_sem].values[0]) if is_t else clean_num(row[ultima_sem].values[0])
            h_vals = [clean_time(row[c].values[0]) if is_t else clean_num(row[c].values[0]) for c in cols_sem if c in row.columns]
            avg_h = sum(h_vals)/len(h_vals) if h_vals else 0
        return val, avg_t, avg_h

    # 5. CÁLCULO VELOCIDAD CICLISMO
    def get_cycling_speed():
        t_now, t_avg_team, _ = get_kpi('Bici', 'T', True)
        d_now, d_avg_team, _ = get_kpi('Bici', 'D', False)
        
        df_t = data['Bici']['T']; df_d = data['Bici']['D']
        hist_speeds = []
        if df_t is not None and df_d is not None:
            row_t = df_t[df_t['Nombre'].astype(str).str.lower() == str(atleta_sel).lower()]
            row_d = df_d[df_d['Nombre'].astype(str).str.lower() == str(atleta_sel).lower()]
            if not row_t.empty and not row_d.empty:
                for c in cols_sem:
                    if c in row_t.columns and c in row_d.columns:
                        t = clean_time(row_t[c].values[0])
                        d = clean_num(row_d[c].values[0])
                        if t > 0.001: hist_speeds.append(d / (t*24))
        
        spd_now = d_now / (t_now*24) if t_now > 0.001 else 0
        spd_team = d_avg_team / (t_avg_team*24) if t_avg_team > 0.001 else 0
        spd_hist = sum(hist_speeds)/len(hist_speeds) if hist_speeds else 0
        return spd_now, spd_team, spd_hist

    # --- RENDERIZADO ---
    
    tv, ta, th = get_kpi('Global', 'T', True)
    dv, da, dh = get_kpi('Global', 'D', False)
    av, aa, ah = get_kpi('Global', 'A', False)
    
    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="card-box"><div class="stat-label">⏱️ Tiempo Total</div><div class="stat-value">{fmt_h_m(tv)}</div><div class="comp-text">👥 Vs Eq: <span class="{ 'pos' if (tv-ta)>=0 else 'neg' }">{fmt_diff(tv-ta, True)}</span><br>📅 Vs Hist: <span class="{ 'pos' if (tv-th)>=0 else 'neg' }">{fmt_diff(tv-th, True)}</span></div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="card-box"><div class="stat-label">📏 Distancia</div><div class="stat-value">{dv:.1f} km</div><div class="comp-text">👥 Vs Eq: <span class="{ 'pos' if (dv-da)>=0 else 'neg' }">{fmt_diff(dv-da)} km</span><br>📅 Vs Hist: <span class="{ 'pos' if (dv-dh)>=0 else 'neg' }">{fmt_diff(dv-dh)} km</span></div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="card-box"><div class="stat-label">⛰️ Altimetría</div><div class="stat-value">{av:.0f} m</div><div class="comp-text">Acumulado Semanal</div></div>""", unsafe_allow_html=True)

    def draw_disc(tit, icon, cat, x_type):
        st.markdown(f"<div class='disc-header'>{icon} {tit}</div>", unsafe_allow_html=True)
        t_v, t_a, t_h = get_kpi(cat, 'T', True)
        d_v, d_a, d_h = get_kpi(cat, 'D', False)
        
        rows_html = ""
        rows_html += f"<tr><td><b>Tiempo</b></td><td>{fmt_h_m(t_v)}</td><td class='{ 'pos' if t_v>=t_a else 'neg'}'>{fmt_diff(t_v-t_a,True)}</td><td class='{ 'pos' if t_v>=t_h else 'neg'}'>{fmt_diff(t_v-t_h,True)}</td></tr>"
        rows_html += f"<tr><td><b>Distancia</b></td><td>{d_v:.1f} km</td><td class='{ 'pos' if d_v>=d_a else 'neg'}'>{fmt_diff(d_v-d_a)}</td><td class='{ 'pos' if d_v>=d_h else 'neg'}'>{fmt_diff(d_v-d_h)}</td></tr>"

        if x_type == 'elev':
            e_v, e_a, e_h = get_kpi(cat, 'E', False)
            rows_html += f"<tr><td><b>Desnivel</b></td><td>{e_v:.0f} m</td><td>-</td><td>-</td></tr>"
            
            s_v, s_a, s_h = get_cycling_speed()
            s_diff_eq = s_v - s_a
            s_diff_hi = s_v - s_h
            rows_html += f"<tr><td><b>Velocidad</b></td><td>{s_v:.1f} km/h</td><td class='{ 'pos' if s_diff_eq>=0 else 'neg'}'>{fmt_diff(s_diff_eq)}</td><td class='{ 'pos' if s_diff_hi>=0 else 'neg'}'>{fmt_diff(s_diff_hi)}</td></tr>"
            
        else:
            e_v, e_a, e_h = get_kpi(cat, 'R', True)
            rows_html += f"<tr><td><b>Ritmo</b></td><td>{fmt_pace(e_v, 'swim' if x_type=='swim' else 'run')}</td><td>-</td><td>-</td></tr>"

        st.markdown(f"<table style='width:100%; font-size:14px;'><tr style='color:#666; border-bottom:1px solid #ddd;'><th style='text-align:left'>Métrica</th><th style='text-align:left'>Dato</th><th style='text-align:left'>Vs Equipo</th><th style='text-align:left'>Vs Histórico</th></tr>{rows_html}</table>", unsafe_allow_html=True)

    c_n, c_b, c_r = st.columns(3)
    with c_n: draw_disc("NATACIÓN", "🏊", "Nat", "swim")
    with c_b: draw_disc("CICLISMO", "🚴", "Bici", "elev")
    with c_r: draw_disc("TROTE", "🏃", "Trote", "run")
