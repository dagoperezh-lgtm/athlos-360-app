# =============================================================================
# 🦅 ATHLOS 360 - V16.0 (RESUMEN CLUB + RANKING DESTACADO + DOBLE PORTADA)
# =============================================================================
import streamlit as st
import pandas as pd
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="wide")

# ESTILOS CSS (MEJORADOS)
st.markdown("""
<style>
    /* PORTADA & MENÚ */
    .cover-title { font-size: 45px; font-weight: bold; text-align: center; color: #003366; margin-top: 10px; }
    .cover-sub { font-size: 22px; text-align: center; color: #666; margin-bottom: 40px; }
    .menu-card { 
        background-color: white; padding: 30px; border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; 
        border: 2px solid #eee; transition: transform 0.2s;
        cursor: pointer;
    }
    .menu-card:hover { transform: scale(1.02); border-color: #003366; }
    
    /* RANKING DESTACADO (FICHA) */
    .rank-section-title { font-size: 16px; font-weight: bold; color: #003366; text-transform: uppercase; margin-bottom: 8px; }
    .rank-badge-lg { 
        background-color: #003366; color: white; padding: 10px 20px; border-radius: 10px; 
        font-size: 22px; font-weight: bold; margin-right: 15px; display: inline-block;
        box-shadow: 0 3px 6px rgba(0,0,0,0.2); border-left: 5px solid #FF4B4B;
    }
    
    /* TABLAS TOP 10 */
    .top10-header { background-color: #003366; color: white; padding: 10px; border-radius: 5px 5px 0 0; font-weight: bold; }
    .top10-table { width: 100%; border-collapse: collapse; background-color: white; border: 1px solid #ddd; }
    .top10-table td, .top10-table th { padding: 8px; border-bottom: 1px solid #eee; text-align: left; font-size: 14px; }
    .top10-pos { font-weight: bold; color: #003366; width: 30px; }
    
    /* GENERALES */
    .kpi-club-box { background-color: #eef; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
    .kpi-club-val { font-size: 32px; font-weight: bold; color: #003366; }
    .kpi-club-lbl { font-size: 14px; color: #666; font-weight: bold; text-transform: uppercase; }
    
    .card-box { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border: 1px solid #e0e0e0; border-left: 5px solid #003366; margin-bottom: 15px; }
    .stat-label { font-size: 15px; font-weight: bold; color: #555; text-transform: uppercase; }
    .stat-value { font-size: 26px; font-weight: bold; color: #000; }
    .comp-text { font-size: 14px; margin-top: 5px; color: #444; }
    .pos { color: #008000; font-weight: bold; }
    .neg { color: #B22222; font-weight: bold; }
    .disc-header { background-color: #E6F0FA; padding: 10px 15px; font-weight: bold; font-size: 18px; border-radius: 8px; margin-top: 15px; color: #003366; }
    .main-title { font-size: 32px; font-weight: bold; color: #000; margin-bottom: 5px; }
    .sub-title { font-size: 18px; color: #666; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 2. GESTIÓN DE SESIÓN ---
if 'club_activo' not in st.session_state: st.session_state['club_activo'] = None
if 'vista_actual' not in st.session_state: st.session_state['vista_actual'] = 'home' # home, menu, resumen, ficha

# =============================================================================
# 🚪 FASE 1: PORTADA GLOBAL
# =============================================================================
if st.session_state['club_activo'] is None:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo_athlos.png"): st.image("logo_athlos.png", use_container_width=True)
        else: st.markdown("<div class='cover-title'>ATHLOS 360</div>", unsafe_allow_html=True)
        st.markdown("<div class='cover-sub'>Plataforma de Alto Rendimiento</div>", unsafe_allow_html=True)
        
        if st.selectbox("Selecciona tu Club:", ["Seleccionar...", "TYM Triathlon"]) == "TYM Triathlon":
            if st.button("INGRESAR 🚀", type="primary", use_container_width=True):
                st.session_state['club_activo'] = "TYM Triathlon"
                st.session_state['vista_actual'] = 'menu'
                st.rerun()
    st.stop()

# =============================================================================
# 📊 FASE 2: MOTOR DE DATOS (BLINDADO)
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
        return f"{h}h {m:02d}s" if h==0 else f"{h}h {m}m"
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

# CARGA DE DATOS CENTRALIZADA
with st.spinner("Cargando base de datos..."):
    data = {
        'Global': {'T': get_df_cache("Tiempo Total"), 'D': get_df_cache("Distancia Total"), 'A': get_df_cache("Altimetría Total")},
        'Nat': {'T': get_df_cache("Nat Tiempo") or get_df_cache("Natación"), 'D': get_df_cache("Nat Distancia"), 'R': get_df_cache("Nat Ritmo")},
        'Bici': {'T': get_df_cache("Ciclismo Tiempo") or get_df_cache("Ciclismo"), 'D': get_df_cache("Ciclismo Distancia"), 'E': get_df_cache("Ciclismo Desnivel")},
        'Trote': {'T': get_df_cache("Trote Tiempo") or get_df_cache("Trote"), 'D': get_df_cache("Trote Distancia"), 'R': get_df_cache("Trote Ritmo")}
    }

# IDENTIFICAR SEMANA
df_base = data['Global']['D']
if df_base is None: st.error("Error crítico: No hay datos."); st.stop()
cols_sem = [c for c in df_base.columns if c.startswith("Sem")]
ultima_sem = cols_sem[-1] if cols_sem else "N/A"

# =============================================================================
# 🚦 FASE 3: LÓGICA DE NAVEGACIÓN (MENÚ PRINCIPAL)
# =============================================================================

# BARRA SUPERIOR (HEADER)
c1, c2 = st.columns([6,1])
with c1:
    if st.session_state['vista_actual'] != 'menu':
        if st.button("⬅️ Volver al Menú Principal"):
            st.session_state['vista_actual'] = 'menu'
            st.rerun()
with c2:
    if st.button("🏠 Salir"):
        st.session_state['club_activo'] = None
        st.session_state['vista_actual'] = 'home'
        st.rerun()

st.markdown("---")

# --- VISTA: MENÚ DE SELECCIÓN ---
if st.session_state['vista_actual'] == 'menu':
    st.markdown(f"<div class='cover-title'>Hola, Equipo {st.session_state['club_activo']}</div>", unsafe_allow_html=True)
    st.markdown("<div class='cover-sub'>¿Qué deseas revisar hoy?</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="text-align:center; padding:20px; border:2px solid #ddd; border-radius:15px; cursor:pointer;">
            <h2 style="color:#003366;">📊 Resumen del Club</h2>
            <p style="color:#666;">Totales, Estadísticas y Top 10</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Ver Resumen Equipo", use_container_width=True):
            st.session_state['vista_actual'] = 'resumen'
            st.rerun()
            
    with col2:
        st.markdown(f"""
        <div style="text-align:center; padding:20px; border:2px solid #ddd; border-radius:15px; cursor:pointer;">
            <h2 style="color:#003366;">👤 Ficha por Triatleta</h2>
            <p style="color:#666;">Análisis Individual Detallado (V25)</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Ver Ficha Personal", use_container_width=True):
            st.session_state['vista_actual'] = 'ficha'
            st.rerun()

# =============================================================================
# 📈 VISTA: RESUMEN DEL CLUB (NUEVO REQUERIMIENTO)
# =============================================================================
elif st.session_state['vista_actual'] == 'resumen':
    st.markdown(f"<div class='main-title'>📊 Resumen Ejecutivo: {st.session_state['club_activo']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-title'>Semana Analizada: {ultima_sem}</div>", unsafe_allow_html=True)
    
    # A. CÁLCULO DE TOTALES
    def calc_total_club(df_in, is_time=False):
        if df_in is None or ultima_sem not in df_in.columns: return 0
        vals = [clean_time(x) if is_time else clean_num(x) for x in df_in[ultima_sem]]
        return sum(vals)
    
    # Activos: Personas con Distancia > 0
    activos = 0
    if data['Global']['D'] is not None:
        for x in data['Global']['D'][ultima_sem]:
            if clean_num(x) > 0.1: activos += 1
            
    total_time_club = calc_total_club(data['Global']['T'], True)
    total_dist_club = calc_total_club(data['Global']['D'], False)
    
    # KPIs Club
    k1, k2, k3 = st.columns(3)
    with k1: st.markdown(f"<div class='kpi-club-box'><div class='kpi-club-val'>{fmt_h_m(total_time_club)}</div><div class='kpi-club-lbl'>Tiempo Total Equipo</div></div>", unsafe_allow_html=True)
    with k2: st.markdown(f"<div class='kpi-club-box'><div class='kpi-club-val'>{total_dist_club:,.0f} km</div><div class='kpi-club-lbl'>Distancia Acumulada</div></div>", unsafe_allow_html=True)
    with k3: st.markdown(f"<div class='kpi-club-box'><div class='kpi-club-val'>{activos}</div><div class='kpi-club-lbl'>Atletas Activos</div></div>", unsafe_allow_html=True)
    
    st.markdown("### 🏆 Top 10 por Categoría")

    # FUNCIÓN GENERADORA DE TABLAS TOP 10
    def render_top10(df_in, titulo, col_val, is_time=False, unit=""):
        if df_in is None: return
        # Crear copia limpia
        df_clean = df_in.copy()
        df_clean['clean_val'] = df_clean[ultima_sem].apply(lambda x: clean_time(x) if is_time else clean_num(x))
        df_clean = df_clean[df_clean['clean_val'] > 0.001].sort_values('clean_val', ascending=False).head(10)
        
        st.markdown(f"<div class='top10-header'>{titulo}</div>", unsafe_allow_html=True)
        html = "<table class='top10-table'>"
        for idx, row in enumerate(df_clean.itertuples(), 1):
            val_fmt = fmt_h_m(row.clean_val) if is_time else f"{row.clean_val:.1f} {unit}"
            html += f"<tr><td class='top10-pos'>#{idx}</td><td>{row.Nombre}</td><td style='text-align:right; font-weight:bold;'>{val_fmt}</td></tr>"
        html += "</table><br>"
        st.markdown(html, unsafe_allow_html=True)

    # FILA 1: GENERALES
    c1, c2, c3 = st.columns(3)
    with c1: render_top10(data['Global']['T'], "⏱️ Clasif. Tiempo General", ultima_sem, True)
    with c2: render_top10(data['Global']['D'], "📏 Clasif. Distancia General", ultima_sem, False, "km")
    with c3: render_top10(data['Global']['A'], "⛰️ Clasif. Altimetría General", ultima_sem, False, "m")
    
    # FILA 2: NATACIÓN
    st.markdown("#### 🏊 Natación")
    c1, c2 = st.columns(2)
    with c1: render_top10(data['Nat']['D'], "Distancia Natación", ultima_sem, False, "km")
    with c2: render_top10(data['Nat']['T'], "Tiempo Natación", ultima_sem, True)
    
    # FILA 3: CICLISMO
    st.markdown("#### 🚴 Ciclismo")
    c1, c2, c3 = st.columns(3)
    with c1: render_top10(data['Bici']['D'], "Distancia Ciclismo", ultima_sem, False, "km")
    with c2: render_top10(data['Bici']['T'], "Tiempo Ciclismo", ultima_sem, True)
    with c3: render_top10(data['Bici']['E'], "Altimetría Ciclismo", ultima_sem, False, "m")
    
    # FILA 4: TROTE
    st.markdown("#### 🏃 Trote")
    c1, c2, c3 = st.columns(3)
    with c1: render_top10(data['Trote']['D'], "Distancia Trote", ultima_sem, False, "km")
    with c2: render_top10(data['Trote']['T'], "Tiempo Trote", ultima_sem, True)
    # Nota: Si no hay hoja de Altimetría Trote específica, usamos Altimetría Global como fallback visual o mostramos vacío
    with c3: st.info("Altimetría específica de trote no disponible en datos.")

# =============================================================================
# 👤 VISTA: FICHA POR TRIATLETA (V25 PRESERVADA)
# =============================================================================
elif st.session_state['vista_actual'] == 'ficha':
    
    # SIDEBAR SELECTOR
    with st.sidebar:
        st.header(f"🦁 {st.session_state['club_activo']}")
        nombres = sorted([str(x) for x in df_base['Nombre'].unique() if str(x).lower() not in ['nan','0']])
        nombres.insert(0, " Selecciona tu nombre...")
        atleta_sel = st.selectbox("Busca tu perfil:", nombres)
        st.markdown("---")
        st.caption("Ficha Individual V25")

    if atleta_sel == " Selecciona tu nombre...":
        st.info("👈 Por favor, selecciona un atleta en la barra lateral para ver su ficha detallada.")
    else:
        # CÁLCULO DE RANKINGS PARA HEADER (MODIFICADO PARA DESTACARLO)
        def get_rank_val(df_in):
            if df_in is None: return "-"
            df_r = df_in.copy()
            # Detectar si es tiempo
            sample = str(df_r[ultima_sem].iloc[0])
            is_t = ':' in sample
            df_r['val'] = df_r[ultima_sem].apply(lambda x: clean_time(x) if is_t else clean_num(x))
            df_r['rank'] = df_r['val'].rank(ascending=False, method='min')
            
            mask = df_r['Nombre'].astype(str).str.lower() == str(atleta_sel).lower()
            if not df_r[mask].empty:
                return int(df_r[mask]['rank'].values[0])
            return "-"

        r_dist = get_rank_val(data['Global']['D'])
        r_time = get_rank_val(data['Global']['T'])

        # --- FICHA V25 (INTACTA + RANKING DESTACADO) ---
        st.markdown(f"<div class='main-title'>🦅 REPORTE 360°: {atleta_sel}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sub-title'>Reporte Semanal: {ultima_sem}</div>", unsafe_allow_html=True)
        
        # RANKING DESTACADO (Nuevo Requerimiento)
        st.markdown("<div class='rank-section-title'>🏆 RANKING EN EL CLUB</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="margin-bottom:25px; border-bottom:3px solid #003366; padding-bottom:15px;">
            <span class='rank-badge-lg'>#{r_dist} en Distancia</span>
            <span class='rank-badge-lg'>#{r_time} en Tiempo</span>
        </div>
        """, unsafe_allow_html=True)
        
        # --- (AQUÍ COMIENZA EL MOTOR V25 PRESERVADO) ---
        
        # Calculadora KPI Individual
        def get_kpi_ind(cat, key, is_t=False):
            df = data[cat][key]
            if df is None: return 0,0,0
            # Team
            vals_t = [clean_time(x) if is_t else clean_num(x) for x in df[ultima_sem]] if ultima_sem in df.columns else []
            avg_t = sum(vals_t)/len(vals_t) if vals_t else 0
            # Atleta
            row = df[df['Nombre'].astype(str).str.lower() == str(atleta_sel).lower()]
            val, avg_h = 0, 0
            if not row.empty:
                val = clean_time(row[ultima_sem].values[0]) if is_t else clean_num(row[ultima_sem].values[0])
                h_vals = [clean_time(row[c].values[0]) if is_t else clean_num(row[c].values[0]) for c in cols_sem if c in row.columns]
                avg_h = sum(h_vals)/len(h_vals) if h_vals else 0
            return val, avg_t, avg_h

        # Render Global
        tv, ta, th = get_kpi_ind('Global', 'T', True)
        dv, da, dh = get_kpi_ind('Global', 'D', False)
        av, aa, ah = get_kpi_ind('Global', 'A', False)
        
        c1,c2,c3 = st.columns(3)
        with c1: st.markdown(f"""<div class="card-box"><div class="stat-label">⏱️ Tiempo Total</div><div class="stat-value">{fmt_h_m(tv)}</div><div class="comp-text">👥 Vs Eq: <span class="{ 'pos' if (tv-ta)>=0 else 'neg' }">{fmt_diff(tv-ta, True)}</span><br>📅 Vs Hist: <span class="{ 'pos' if (tv-th)>=0 else 'neg' }">{fmt_diff(tv-th, True)}</span></div></div>""", unsafe_allow_html=True)
        with c2: st.markdown(f"""<div class="card-box"><div class="stat-label">📏 Distancia</div><div class="stat-value">{dv:.1f} km</div><div class="comp-text">👥 Vs Eq: <span class="{ 'pos' if (dv-da)>=0 else 'neg' }">{fmt_diff(dv-da)} km</span><br>📅 Vs Hist: <span class="{ 'pos' if (dv-dh)>=0 else 'neg' }">{fmt_diff(dv-dh)} km</span></div></div>""", unsafe_allow_html=True)
        with c3: st.markdown(f"""<div class="card-box"><div class="stat-label">⛰️ Altimetría</div><div class="stat-value">{av:.0f} m</div><div class="comp-text">Acumulado Semanal</div></div>""", unsafe_allow_html=True)

        # Render Disciplinas
        def get_cycling_speed():
            t_now, t_avg_team, _ = get_kpi_ind('Bici', 'T', True)
            d_now, d_avg_team, _ = get_kpi_ind('Bici', 'D', False)
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

        def draw_disc(tit, icon, cat, x_type):
            st.markdown(f"<div class='disc-header'>{icon} {tit}</div>", unsafe_allow_html=True)
            t_v, t_a, t_h = get_kpi_ind(cat, 'T', True)
            d_v, d_a, d_h = get_kpi_ind(cat, 'D', False)
            
            rows_html = ""
            rows_html += f"<tr><td><b>Tiempo</b></td><td>{fmt_h_m(t_v)}</td><td class='{ 'pos' if t_v>=t_a else 'neg'}'>{fmt_diff(t_v-t_a,True)}</td><td class='{ 'pos' if t_v>=t_h else 'neg'}'>{fmt_diff(t_v-t_h,True)}</td></tr>"
            rows_html += f"<tr><td><b>Distancia</b></td><td>{d_v:.1f} km</td><td class='{ 'pos' if d_v>=d_a else 'neg'}'>{fmt_diff(d_v-d_a)}</td><td class='{ 'pos' if d_v>=d_h else 'neg'}'>{fmt_diff(d_v-d_h)}</td></tr>"

            if x_type == 'elev':
                e_v, e_a, e_h = get_kpi_ind(cat, 'E', False)
                rows_html += f"<tr><td><b>Desnivel</b></td><td>{e_v:.0f} m</td><td>-</td><td>-</td></tr>"
                s_v, s_a, s_h = get_cycling_speed()
                s_diff_eq = s_v - s_a
                s_diff_hi = s_v - s_h
                rows_html += f"<tr><td><b>Velocidad</b></td><td>{s_v:.1f} km/h</td><td class='{ 'pos' if s_diff_eq>=0 else 'neg'}'>{fmt_diff(s_diff_eq)}</td><td class='{ 'pos' if s_diff_hi>=0 else 'neg'}'>{fmt_diff(s_diff_hi)}</td></tr>"
            else:
                e_v, e_a, e_h = get_kpi_ind(cat, 'R', True)
                rows_html += f"<tr><td><b>Ritmo</b></td><td>{fmt_pace(e_v, 'swim' if x_type=='swim' else 'run')}</td><td>-</td><td>-</td></tr>"

            st.markdown(f"<table style='width:100%; font-size:14px;'><tr style='color:#666; border-bottom:1px solid #ddd;'><th style='text-align:left'>Métrica</th><th style='text-align:left'>Dato</th><th style='text-align:left'>Vs Equipo</th><th style='text-align:left'>Vs Histórico</th></tr>{rows_html}</table>", unsafe_allow_html=True)

        c_n, c_b, c_r = st.columns(3)
        with c_n: draw_disc("NATACIÓN", "🏊", "Nat", "swim")
        with c_b: draw_disc("CICLISMO", "🚴", "Bici", "elev")
        with c_r: draw_disc("TROTE", "🏃", "Trote", "run")
