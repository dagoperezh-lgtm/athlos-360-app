# =============================================================================
# 🦅 ATHLOS 360 - V17.2 (FIX CRÍTICO: MATEMÁTICAS SEGURAS EN VISUALIZACIÓN)
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
</style>
""", unsafe_allow_html=True)

# SESIÓN
if 'club_activo' not in st.session_state: st.session_state['club_activo'] = None
if 'vista_actual' not in st.session_state: st.session_state['vista_actual'] = 'home'

# --- 1. PORTADA ---
if st.session_state['club_activo'] is None:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo_athlos.png"): st.image("logo_athlos.png", use_container_width=True)
        else: st.markdown("<div class='cover-title'>ATHLOS 360</div>", unsafe_allow_html=True)
        st.markdown("<div class='cover-sub'>Plataforma de Alto Rendimiento</div>", unsafe_allow_html=True)
        if st.selectbox("Club:", ["Seleccionar...", "TYM Triathlon"]) == "TYM Triathlon":
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
        'Bici': {'T': get_df_safe("Ciclismo Tiempo") or get_df_safe("Ciclismo"), 'D': get_df_safe("Ciclismo Distancia"), 'E': get_df_safe("Ciclismo Desnivel")},
        'Trote': {'T': get_df_safe("Trote Tiempo") or get_df_safe("Trote"), 'D': get_df_safe("Trote Distancia"), 'R': get_df_safe("Trote Ritmo"), 'E': get_df_safe("Trote Desnivel")}
    }

df_base = data['Global']['D']
if df_base is None:
    st.error("⚠️ No se pudo leer el archivo de datos (Distancia Total). Por favor, regenera el Excel en Colab.")
    st.stop()

cols_sem = [c for c in df_base.columns if c.startswith("Sem")]
ultima_sem = cols_sem[-1] if cols_sem else "N/A"

# --- 3. INTERFAZ ---
c1, c2 = st.columns([6,1])
with c1:
    if st.session_state['vista_actual'] != 'menu':
        if st.button("⬅️ Volver al Menú"): st.session_state['vista_actual'] = 'menu'; st.rerun()
with c2:
    if st.button("🏠 Salir"): st.session_state['club_activo'] = None; st.session_state['vista_actual'] = 'home'; st.rerun()
st.markdown("---")

# MENÚ
if st.session_state['vista_actual'] == 'menu':
    st.markdown(f"<div class='cover-title'>Hola, Equipo {st.session_state['club_activo']}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.info("📊 **Resumen del Club**\n\nEstadísticas Globales")
        if st.button("Ver Resumen", use_container_width=True): st.session_state['vista_actual'] = 'resumen'; st.rerun()
    with c2:
        st.info("👤 **Ficha Personal**\n\nDetalle por Atleta")
        if st.button("Ver Ficha", use_container_width=True): st.session_state['vista_actual'] = 'ficha'; st.rerun()

# RESUMEN
elif st.session_state['vista_actual'] == 'resumen':
    st.markdown(f"<div class='main-title'>📊 Resumen Ejecutivo</div>", unsafe_allow_html=True)
    
    def calc_tot(df, is_t=False):
        if df is None or ultima_sem not in df.columns: return 0
        return sum([clean_time(x) if is_t else clean_num(x) for x in df[ultima_sem]])

    tt = calc_tot(data['Global']['T'], True)
    td = calc_tot(data['Global']['D'], False)
    act = sum(1 for x in data['Global']['D'][ultima_sem] if clean_num(x) > 0.1)
    
    k1, k2, k3 = st.columns(3)
    with k1: st.markdown(f"<div class='kpi-club-box'><div class='kpi-club-val'>{fmt_h_m(tt)}</div><div class='kpi-club-lbl'>Tiempo Total</div></div>", unsafe_allow_html=True)
    with k2: st.markdown(f"<div class='kpi-club-box'><div class='kpi-club-val'>{td:,.0f} km</div><div class='kpi-club-lbl'>Distancia Total</div></div>", unsafe_allow_html=True)
    with k3: st.markdown(f"<div class='kpi-club-box'><div class='kpi-club-val'>{act}</div><div class='kpi-club-lbl'>Activos</div></div>", unsafe_allow_html=True)

    def top10(df, tit, is_t=False, u=""):
        if df is None or ultima_sem not in df.columns: return
        d = df.copy()
        d['v'] = d[ultima_sem].apply(lambda x: clean_time(x) if is_t else clean_num(x))
        d = d[d['v']>0.001].sort_values('v', ascending=False).head(10)
        st.markdown(f"<div class='top10-header'>{tit}</div>", unsafe_allow_html=True)
        h = "<table class='top10-table'>"
        for i, r in enumerate(d.itertuples(), 1):
            val = fmt_h_m(r.v) if is_t else f"{r.v:.1f} {u}"
            h += f"<tr><td style='width:30px; font-weight:bold; color:#003366;'>#{i}</td><td>{r.Nombre}</td><td style='text-align:right; font-weight:bold;'>{val}</td></tr>"
        st.markdown(h+"</table><br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: top10(data['Global']['T'], "⏱️ Tiempo", True)
    with c2: top10(data['Global']['D'], "📏 Distancia", False, "km")
    with c3: top10(data['Global']['A'], "⛰️ Altimetría", False, "m")
    
    st.markdown("#### Por Disciplina")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown("**🏊 Natación**"); top10(data['Nat']['D'], "Distancia", False, "km")
    with c2: st.markdown("**🚴 Ciclismo**"); top10(data['Bici']['D'], "Distancia", False, "km")
    with c3: st.markdown("**🏃 Trote**"); top10(data['Trote']['D'], "Distancia", False, "km")

# FICHA
elif st.session_state['vista_actual'] == 'ficha':
    with st.sidebar:
        nombres = sorted([str(x) for x in df_base['Nombre'].unique() if str(x).lower() not in ['nan','0']])
        nombres.insert(0, " Selecciona...")
        sel = st.selectbox("Atleta:", nombres)

    if sel == " Selecciona...":
        st.info("👈 Selecciona un atleta.")
    else:
        # Ranking
        def get_rank(df):
            if df is None or ultima_sem not in df.columns: return "-"
            d = df.copy()
            it = ':' in str(d[ultima_sem].iloc[0])
            d['v'] = d[ultima_sem].apply(lambda x: clean_time(x) if it else clean_num(x))
            d['r'] = d['v'].rank(ascending=False, method='min')
            mask = d['Nombre'].astype(str).str.lower() == str(sel).lower()
            return int(d[mask]['r'].values[0]) if not d[mask].empty else "-"

        rd = get_rank(data['Global']['D'])
        rt = get_rank(data['Global']['T'])

        st.markdown(f"<div class='main-title'>🦅 REPORTE 360°: {sel}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sub-title'>Semana: {ultima_sem}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='rank-container'><span class='rank-badge-lg'>#{rd} en Distancia</span><span class='rank-badge-lg'>#{rt} en Tiempo</span></div>", unsafe_allow_html=True)

        def kpi(cat, k, is_t=False):
            df = data[cat].get(k)
            if df is None: return 0,0,0
            vt = [clean_time(x) if is_t else clean_num(x) for x in df[ultima_sem]] if ultima_sem in df.columns else []
            at = sum(vt)/len(vt) if vt else 0
            row = df[df['Nombre'].astype(str).str.lower() == str(sel).lower()]
            val, ah = 0, 0
            if not row.empty:
                val = clean_time(row[ultima_sem].values[0]) if is_t else clean_num(row[ultima_sem].values[0])
                h_vals = [clean_time(row[c].values[0]) if is_t else clean_num(row[c].values[0]) for c in cols_sem if c in row.columns]
                ah = sum(h_vals)/len(h_vals) if h_vals else 0
            return val, at, ah

        tv, ta, th = kpi('Global', 'T', True)
        dv, da, dh = kpi('Global', 'D', False)
        av, aa, ah = kpi('Global', 'A', False)

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='card-box'><div class='stat-label'>⏱️ Tiempo</div><div class='stat-value'>{fmt_h_m(tv)}</div><div class='comp-text'>👥 {fmt_diff(tv-ta, True)} | 📅 {fmt_diff(tv-th, True)}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='card-box'><div class='stat-label'>📏 Distancia</div><div class='stat-value'>{dv:.1f} km</div><div class='comp-text'>👥 {fmt_diff(dv-da)} | 📅 {fmt_diff(dv-dh)}</div></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='card-box'><div class='stat-label'>⛰️ Altimetría</div><div class='stat-value'>{av:.0f} m</div><div class='comp-text'>Acumulado Semanal</div></div>", unsafe_allow_html=True)

        def draw_disc(tit, icon, cat, xtype):
            st.markdown(f"<div class='disc-header'>{icon} {tit}</div>", unsafe_allow_html=True)
            t_v, t_a, t_h = kpi(cat, 'T', True)
            d_v, d_a, d_h = kpi(cat, 'D', False)
            
            # --- FIX: LOGICA DE COLOR SEGURA ---
            # Pasamos NUMEROS (diferencias) para decidir color, y TEXTO solo para imprimir
            def row(l, v, diff_eq_num, diff_eq_txt, diff_hist_num, diff_hist_txt):
                ce = "pos" if diff_eq_num >= 0 else "neg"
                ch = "pos" if diff_hist_num >= 0 else "neg"
                # Si el texto es "-", mantenemos el color pero el texto es guión
                te = diff_eq_txt if diff_eq_num != 0 else "-"
                th = diff_hist_txt if diff_hist_num != 0 else "-"
                return f"<tr><td><b>{l}</b></td><td>{v}</td><td class='{ce}'>{te}</td><td class='{ch}'>{th}</td></tr>"

            h = f"<table style='width:100%; font-size:14px;'><tr style='color:#666; border-bottom:1px solid #ddd;'><th>Métrica</th><th>Dato</th><th>Vs Eq</th><th>Vs Hist</th></tr>"
            
            # Tiempo
            h += row("Tiempo", fmt_h_m(t_v), t_v-t_a, fmt_diff(t_v-t_a, True), t_v-t_h, fmt_diff(t_v-t_h, True))
            # Distancia
            h += row("Distancia", f"{d_v:.1f} km", d_v-d_a, fmt_diff(d_v-d_a), d_v-d_h, fmt_diff(d_v-d_h))

            if xtype == 'elev': # BICI
                e_v, e_a, e_h = kpi(cat, 'E', False)
                h += f"<tr><td><b>Desnivel</b></td><td>{e_v:.0f} m</td><td>-</td><td>-</td></tr>"
                
                sp_v = d_v/(t_v*24) if t_v>0.001 else 0
                sp_a = d_a/(t_a*24) if t_a>0.001 else 0
                h += row("Velocidad", f"{sp_v:.1f} km/h", sp_v-sp_a, fmt_diff(sp_v-sp_a), 0, "-")
                
            elif xtype == 'run': # TROTE
                r_v, r_a, r_h = kpi(cat, 'R', True)
                h += f"<tr><td><b>Ritmo</b></td><td>{fmt_pace(r_v, 'run')}</td><td>-</td><td>-</td></tr>"
                e_v, e_a, e_h = kpi(cat, 'E', False)
                if e_v > 0: h += f"<tr><td><b>Desnivel</b></td><td>{e_v:.0f} m</td><td>-</td><td>-</td></tr>"
                
            else: # NATACION
                r_v, r_a, r_h = kpi(cat, 'R', True)
                h += f"<tr><td><b>Ritmo</b></td><td>{fmt_pace(r_v, 'swim')}</td><td>-</td><td>-</td></tr>"
                
            st.markdown(h+"</table>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1: draw_disc("NATACIÓN", "🏊", "Nat", "swim")
        with c2: draw_disc("CICLISMO", "🚴", "Bici", "elev")
        with c3: draw_disc("TROTE", "🏃", "Trote", "run")
