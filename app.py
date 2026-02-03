# =============================================================================
# 🦅 ATHLOS 360 - V17.0 (DISEÑO V16 + FIX ALTIMETRÍA CRISTOBAL)
# =============================================================================
import streamlit as st
import pandas as pd
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="wide")

# ESTILOS CSS (DISEÑO AZUL V16 PRO)
st.markdown("""
<style>
    /* PORTADA & MENÚ */
    .cover-title { font-size: 45px; font-weight: bold; text-align: center; color: #003366; margin-top: 10px; }
    .cover-sub { font-size: 22px; text-align: center; color: #666; margin-bottom: 40px; }
    
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
if 'vista_actual' not in st.session_state: st.session_state['vista_actual'] = 'home'

# PORTADA GLOBAL
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

# MOTOR DE DATOS
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
    if pd.isna(val) or str(val).strip() in ['','-','nan','0','00:00:00']: return 0.0
    s = str(val).strip().split(' ')[-1]
    try:
        if ':' in s:
            p = [float(x) for x in s.split(':')]
            sec = 0
            if len(p)==3: sec = p[0]*3600 + p[1]*60 + p[2]
            elif len(p)==2: sec = p[0]*60 + p[1]
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

# CARGA DE DATOS (CON LA HOJA NUEVA 'Trote Desnivel')
with st.spinner("Cargando base de datos..."):
    data = {
        'Global': {'T': get_df_cache("Tiempo Total"), 'D': get_df_cache("Distancia Total"), 'A': get_df_cache("Altimetría Total")},
        'Nat': {'T': get_df_cache("Nat Tiempo") or get_df_cache("Natación"), 'D': get_df_cache("Nat Distancia"), 'R': get_df_cache("Nat Ritmo")},
        'Bici': {'T': get_df_cache("Ciclismo Tiempo") or get_df_cache("Ciclismo"), 'D': get_df_cache("Ciclismo Distancia"), 'E': get_df_cache("Ciclismo Desnivel")},
        'Trote': {
            'T': get_df_cache("Trote Tiempo") or get_df_cache("Trote"), 
            'D': get_df_cache("Trote Distancia"), 
            'R': get_df_cache("Trote Ritmo"),
            'E': get_df_cache("Trote Desnivel") # ¡Aquí está el fix!
        }
    }

df_base = data['Global']['D']
if df_base is None: st.error("Error crítico: No hay datos."); st.stop()
cols_sem = [c for c in df_base.columns if c.startswith("Sem")]
ultima_sem = cols_sem[-1] if cols_sem else "N/A"

# BARRA NAVEGACIÓN
c1, c2 = st.columns([6,1])
with c1:
    if st.session_state['vista_actual'] != 'menu':
        if st.button("⬅️ Volver al Menú Principal"): st.session_state['vista_actual'] = 'menu'; st.rerun()
with c2:
    if st.button("🏠 Salir"): st.session_state['club_activo'] = None; st.session_state['vista_actual'] = 'home'; st.rerun()
st.markdown("---")

# --- MENÚ ---
if st.session_state['vista_actual'] == 'menu':
    st.markdown(f"<div class='cover-title'>Hola, Equipo {st.session_state['club_activo']}</div>", unsafe_allow_html=True)
    st.markdown("<div class='cover-sub'>¿Qué deseas revisar hoy?</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.info("📊 **Resumen del Club**\n\nTotales y Estadísticas.")
        if st.button("Ver Resumen Equipo", use_container_width=True): st.session_state['vista_actual'] = 'resumen'; st.rerun()
    with c2:
        st.info("👤 **Ficha Personal**\n\nAnálisis individual V25.")
        if st.button("Ver Ficha Personal", use_container_width=True): st.session_state['vista_actual'] = 'ficha'; st.rerun()

# --- RESUMEN ---
elif st.session_state['vista_actual'] == 'resumen':
    st.markdown(f"<div class='main-title'>📊 Resumen Ejecutivo</div>", unsafe_allow_html=True)
    def calc_tot(df, is_t=False):
        if df is None or ultima_sem not in df.columns: return 0
        return sum([clean_time(x) if is_t else clean_num(x) for x in df[ultima_sem]])
    
    tt = calc_tot(data['Global']['T'], True)
    td = calc_tot(data['Global']['D'], False)
    act = sum(1 for x in data['Global']['D'][ultima_sem] if clean_num(x) > 0.1) if data['Global']['D'] is not None else 0
    
    k1, k2, k3 = st.columns(3)
    with k1: st.markdown(f"<div class='kpi-club-box'><div class='kpi-club-val'>{fmt_h_m(tt)}</div><div class='kpi-club-lbl'>Tiempo Total</div></div>", unsafe_allow_html=True)
    with k2: st.markdown(f"<div class='kpi-club-box'><div class='kpi-club-val'>{td:,.0f} km</div><div class='kpi-club-lbl'>Distancia Total</div></div>", unsafe_allow_html=True)
    with k3: st.markdown(f"<div class='kpi-club-box'><div class='kpi-club-val'>{act}</div><div class='kpi-club-lbl'>Atletas Activos</div></div>", unsafe_allow_html=True)

    def top10(df, tit, is_t=False, u=""):
        if df is None: return
        d = df.copy()
        d['v'] = d[ultima_sem].apply(lambda x: clean_time(x) if is_t else clean_num(x))
        d = d[d['v']>0.001].sort_values('v', ascending=False).head(10)
        st.markdown(f"<div class='top10-header'>{tit}</div>", unsafe_allow_html=True)
        h = "<table class='top10-table'>"
        for i, r in enumerate(d.itertuples(), 1):
            val = fmt_h_m(r.v) if is_t else f"{r.v:.1f} {u}"
            h += f"<tr><td class='top10-pos'>#{i}</td><td>{r.Nombre}</td><td style='text-align:right; font-weight:bold;'>{val}</td></tr>"
        st.markdown(h+"</table><br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: top10(data['Global']['T'], "⏱️ Tiempo General", True)
    with c2: top10(data['Global']['D'], "📏 Distancia General", False, "km")
    with c3: top10(data['Global']['A'], "⛰️ Altimetría General", False, "m")

    st.markdown("#### Desglose por Disciplina")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown("**🏊 Natación**"); top10(data['Nat']['D'], "Distancia", False, "km")
    with c2: st.markdown("**🚴 Ciclismo**"); top10(data['Bici']['D'], "Distancia", False, "km")
    with c3: st.markdown("**🏃 Trote**"); top10(data['Trote']['D'], "Distancia", False, "km")

# --- FICHA V25 ---
elif st.session_state['vista_actual'] == 'ficha':
    with st.sidebar:
        st.header(f"🦁 {st.session_state['club_activo']}")
        nombres = sorted([str(x) for x in df_base['Nombre'].unique() if str(x).lower() not in ['nan','0']])
        nombres.insert(0, " Selecciona...")
        sel = st.selectbox("Busca tu perfil:", nombres)

    if sel == " Selecciona...":
        st.info("👈 Selecciona un atleta en el menú lateral.")
    else:
        # Ranking
        def get_rank_val(df_in):
            if df_in is None: return "-"
            df_r = df_in.copy()
            it = ':' in str(df_r[ultima_sem].iloc[0])
            df_r['val'] = df_r[ultima_sem].apply(lambda x: clean_time(x) if it else clean_num(x))
            df_r['rank'] = df_r['val'].rank(ascending=False, method='min')
            mask = df_r['Nombre'].astype(str).str.lower() == str(sel).lower()
            return int(df_r[mask]['rank'].values[0]) if not df_r[mask].empty else "-"

        rd = get_rank_val(data['Global']['D'])
        rt = get_rank_val(data['Global']['T'])

        st.markdown(f"<div class='main-title'>🦅 REPORTE 360°: {sel}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sub-title'>Reporte Semanal: {ultima_sem}</div>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='rank-container'>
            <span class='rank-badge-lg'>#{rd} en Distancia</span>
            <span class='rank-badge-lg'>#{rt} en Tiempo</span>
        </div>""", unsafe_allow_html=True)

        # KPIs Individuales
        def kpi(cat, k, is_t=False):
            df = data[cat].get(k)
            if df is None: return 0,0,0
            vt = [clean_time(x) if is_t else clean_num(x) for x in df[ultima_sem]] if ultima_sem in df.columns else []
            at = sum(vt)/len(vt) if vt else 0
            row = df[df['Nombre'].astype(str).str.lower() == str(sel).lower()]
            val, ah = 0, 0
            if not row.empty:
                val = clean_time(row[ultima_sem].values[0]) if is_t else clean_num(row[ultima_sem].values[0])
                hv = [clean_time(row[c].values[0]) if is_t else clean_num(row[c].values[0]) for c in cols_sem if c in row.columns]
                ah = sum(hv)/len(hv) if hv else 0
            return val, at, ah

        tv, ta, th = kpi('Global', 'T', True)
        dv, da, dh = kpi('Global', 'D', False)
        av, aa, ah = kpi('Global', 'A', False)

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"""<div class='card-box'><div class='stat-label'>⏱️ Tiempo</div><div class='stat-value'>{fmt_h_m(tv)}</div><div class='comp-text'>👥 {fmt_diff(tv-ta, True)} | 📅 {fmt_diff(tv-th, True)}</div></div>""", unsafe_allow_html=True)
        with c2: st.markdown(f"""<div class='card-box'><div class='stat-label'>📏 Distancia</div><div class='stat-value'>{dv:.1f} km</div><div class='comp-text'>👥 {fmt_diff(dv-da)} | 📅 {fmt_diff(dv-dh)}</div></div>""", unsafe_allow_html=True)
        with c3: st.markdown(f"""<div class='card-box'><div class='stat-label'>⛰️ Altimetría</div><div class='stat-value'>{av:.0f} m</div><div class='comp-text'>Acumulado Semanal</div></div>""", unsafe_allow_html=True)

        # Tabla Disciplinas
        def d_row(lbl, v, de, dh):
            ce = "pos" if (float(de.replace('+','').split(' ')[0]) if de!='-' else 0) >= 0 else "neg"
            ch = "pos" if (float(dh.replace('+','').split(' ')[0]) if dh!='-' else 0) >= 0 else "neg"
            return f"<tr><td><b>{lbl}</b></td><td>{v}</td><td class='{ce}'>{de}</td><td class='{ch}'>{dh}</td></tr>"

        def draw_disc(tit, icon, cat, xtype):
            st.markdown(f"<div class='disc-header'>{icon} {tit}</div>", unsafe_allow_html=True)
            t_v, t_a, t_h = kpi(cat, 'T', True)
            d_v, d_a, d_h = kpi(cat, 'D', False)
            
            h = f"<table style='width:100%; font-size:14px;'><tr style='color:#666; border-bottom:1px solid #ddd;'><th>Métrica</th><th>Dato</th><th>Vs Eq</th><th>Vs Hist</th></tr>"
            h += d_row("Tiempo", fmt_h_m(t_v), fmt_diff(t_v-t_a, True), fmt_diff(t_v-t_h, True))
            h += d_row("Distancia", f"{d_v:.1f} km", fmt_diff(d_v-d_a), fmt_diff(d_v-d_h))

            if xtype == 'elev': # BICI
                e_v, e_a, e_h = kpi(cat, 'E', False)
                h += f"<tr><td><b>Desnivel</b></td><td>{e_v:.0f} m</td><td>-</td><td>-</td></tr>"
                sp_v = d_v/(t_v*24) if t_v>0.001 else 0
                sp_a = d_a/(t_a*24) if t_a>0.001 else 0
                h += d_row("Velocidad", f"{sp_v:.1f} km/h", fmt_diff(sp_v-sp_a), "-")
            
            elif xtype == 'run': # TROTE
                r_v, r_a, r_h = kpi(cat, 'R', True)
                h += f"<tr><td><b>Ritmo</b></td><td>{fmt_pace(r_v, 'run')}</td><td>-</td><td>-</td></tr>"
                # FIX: Ahora mostramos desnivel en Trote
                e_v, e_a, e_h = kpi(cat, 'E', False)
                if e_v > 1: # Solo mostrar si hay desnivel real
                    h += f"<tr><td><b>Desnivel</b></td><td>{e_v:.0f} m</td><td>-</td><td>-</td></tr>"
            else:
                r_v, r_a, r_h = kpi(cat, 'R', True)
                h += f"<tr><td><b>Ritmo</b></td><td>{fmt_pace(r_v, 'swim')}</td><td>-</td><td>-</td></tr>"
            
            st.markdown(h+"</table>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1: draw_disc("NATACIÓN", "🏊", "Nat", "swim")
        with c2: draw_disc("CICLISMO", "🚴", "Bici", "elev")
        with c3: draw_disc("TROTE", "🏃", "Trote", "run")
