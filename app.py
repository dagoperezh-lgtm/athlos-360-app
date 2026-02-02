# =============================================================================
# 🦅 ATHLOS 360 - REPORTE V25 (V11.0 FINAL FIX: CACHE + TIEMPOS)
# =============================================================================
import streamlit as st
import pandas as pd
import os
import math

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Reporte V25", page_icon="🦅", layout="wide")

st.markdown("""
<style>
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

# --- 2. MOTOR DE DATOS CACHEABLE (CORREGIDO) ---
ARCHIVO = "06 Sem (tst).xlsx"

@st.cache_data(ttl=60)
def get_df(nombre_hoja):
    """Lee una hoja específica y devuelve un DataFrame (Cache Safe)"""
    if not os.path.exists(ARCHIVO): return None
    try:
        # Abrimos el motor solo para leer nombres de hojas
        xls = pd.ExcelFile(ARCHIVO, engine='openpyxl')
        
        # Buscar el nombre real de la hoja (flexible)
        target = next((h for h in xls.sheet_names if nombre_hoja.lower() in h.lower().replace(":","")), None)
        
        if target:
            # Leer datos como string para controlar la conversión manualmente
            df = pd.read_excel(xls, sheet_name=target, dtype=str)
            df.columns = [str(c).strip() for c in df.columns]
            col = next((c for c in df.columns if c.lower() in ['nombre','deportista','atleta']), None)
            if col: df.rename(columns={col: 'Nombre'}, inplace=True)
            return df
    except: return None
    return None

# --- 3. SANITIZADORES (FIX "TIEMPOS INFINITOS") ---
def clean_time_val(val):
    """
    Recibe: "1900-01-01 12:30:00" o "0.52"
    Devuelve: 0.52 (float)
    """
    if pd.isna(val) or str(val).strip() in ['','-','nan','0','00:00:00','None']: return 0.0
    
    s = str(val).strip()
    
    # ✂️ TIJERA: Si hay fecha y hora, cortar la fecha
    if ' ' in s:
        s = s.split(' ')[-1] # Se queda con "12:30:00"
        
    try:
        # Caso A: Formato Horas "HH:MM:SS"
        if ':' in s:
            parts = [float(x) for x in s.split(':')]
            sec = 0
            if len(parts) == 3: sec = parts[0]*3600 + parts[1]*60 + parts[2]
            elif len(parts) == 2: sec = parts[0]*60 + parts[1]
            return sec / 86400.0 # Retorna fracción de día
            
        # Caso B: Es un número directo
        f = float(s)
        # SANITY CHECK: Si es mayor a 100 días, es basura. Reset a 0.
        if f > 100: return 0.0 
        return f
    except:
        return 0.0

def clean_num_val(val):
    """Limpia distancias y altimetrías"""
    if pd.isna(val): return 0.0
    try: return float(str(val).replace(',','.'))
    except: return 0.0

# --- 4. FORMATTERS (VISUALIZACIÓN) ---
def fmt_h_m(val_float):
    """0.5 -> 12h 00m"""
    if val_float <= 0.0001: return "-"
    try:
        tot = val_float * 24
        h = int(tot)
        m = int((tot - h) * 60)
        return f"{h}h {m}m"
    except: return "-"

def fmt_pace(val_float, sport):
    """0.0034 -> 5:00 min/km"""
    if val_float <= 0.00001: return "-"
    try:
        mins = val_float * 24 * 60
        m = int(mins)
        s = int((mins - m) * 60)
        u = "/100m" if sport == 'swim' else "/km"
        return f"{m}:{s:02d} {u}"
    except: return "-"

def fmt_diff(val, es_tiempo=False):
    if abs(val) < 0.0001: return "-"
    signo = "+" if val > 0 else "-"
    val = abs(val)
    if es_tiempo:
        h = int(val * 24)
        m = int((val * 24 * 60) % 60)
        return f"{signo}{h}h {m}m"
    else:
        return f"{signo}{val:.1f}"

# --- 5. GESTIÓN DE PORTADA ---
if 'club_ok' not in st.session_state: st.session_state['club_ok'] = False

if not st.session_state['club_ok']:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if os.path.exists("logo_athlos.png"): st.image("logo_athlos.png", use_container_width=True)
        else: st.title("ATHLOS 360")
        st.markdown("---")
        if st.button("INGRESAR AL CLUB TYM", type="primary", use_container_width=True):
            st.session_state['club_ok'] = True
            st.rerun()

else:
    # --- DASHBOARD ---
    with st.sidebar:
        if os.path.exists("logo_athlos.png"): st.image("logo_athlos.png")
        if st.button("🏠 Inicio"): 
            st.session_state['club_ok'] = False
            st.rerun()
        st.markdown("---")
        
        # Cargar Base
        df_base = get_df("Distancia Total")
        if df_base is None: st.error("⚠️ Error leyendo datos."); st.stop()
        
        nombres = sorted([str(x) for x in df_base['Nombre'].unique() if str(x).lower() not in ['nan','0']])
        atleta = st.selectbox("Atleta:", nombres)

    # DATOS
    cols_sem = [c for c in df_base.columns if c.startswith("Sem")]
    ultima_sem = cols_sem[-1] if cols_sem else "N/A"
    
    st.markdown(f"<div class='main-title'>🦅 REPORTE 360°: {atleta}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-title'>Reporte Semanal: {ultima_sem}</div>", unsafe_allow_html=True)

    # CARGA DATOS
    data = {
        'Global': {'T': get_df("Tiempo Total"), 'D': get_df("Distancia Total"), 'A': get_df("Altimetría Total"), 'CV': get_df("CV")},
        'Nat': {'T': get_df("Nat Tiempo") or get_df("Natación"), 'D': get_df("Nat Distancia"), 'R': get_df("Nat Ritmo")},
        'Bici': {'T': get_df("Ciclismo Tiempo") or get_df("Ciclismo"), 'D': get_df("Ciclismo Distancia"), 'E': get_df("Ciclismo Desnivel")},
        'Trote': {'T': get_df("Trote Tiempo") or get_df("Trote"), 'D': get_df("Trote Distancia"), 'R': get_df("Trote Ritmo")}
    }

    def get_metrics(cat, key, is_time=False):
        df = data[cat][key]
        if df is None: return 0,0,0
        
        # Limpieza masiva de la columna actual para el promedio del equipo
        curr_col_vals = []
        if ultima_sem in df.columns:
            for x in df[ultima_sem]:
                v = clean_time_val(x) if is_time else clean_num_val(x)
                curr_col_vals.append(v)
        avg_team = sum(curr_col_vals)/len(curr_col_vals) if curr_col_vals else 0
        
        # Datos del atleta
        row = df[df['Nombre']==atleta]
        val_now = 0
        avg_hist = 0
        
        if not row.empty:
            raw = row[ultima_sem].values[0] if ultima_sem in row.columns else 0
            val_now = clean_time_val(raw) if is_time else clean_num_val(raw)
            
            # Histórico
            hist_vals = []
            for c in cols_sem:
                if c in row.columns:
                    raw_h = row[c].values[0]
                    v_h = clean_time_val(raw_h) if is_time else clean_num_val(raw_h)
                    hist_vals.append(v_h)
            avg_hist = sum(hist_vals)/len(hist_vals) if hist_vals else 0
            
        return val_now, avg_team, avg_hist

    # RENDER GLOBAL
    tv, ta, th = get_metrics('Global', 'T', True)
    dv, da, dh = get_metrics('Global', 'D', False)
    av, aa, ah = get_metrics('Global', 'A', False)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="card-box">
            <div class="stat-label">⏱️ Tiempo Total</div>
            <div class="stat-value">{fmt_h_m(tv)}</div>
            <div class="comp-text">
                👥 Vs Eq: <span class="{ 'pos' if (tv-ta)>=0 else 'neg' }">{fmt_diff(tv-ta, True)}</span><br>
                📅 Vs Hist: <span class="{ 'pos' if (tv-th)>=0 else 'neg' }">{fmt_diff(tv-th, True)}</span>
            </div>
        </div>""", unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""
        <div class="card-box">
            <div class="stat-label">📏 Distancia</div>
            <div class="stat-value">{dv:.1f} km</div>
            <div class="comp-text">
                👥 Vs Eq: <span class="{ 'pos' if (dv-da)>=0 else 'neg' }">{fmt_diff(dv-da)} km</span><br>
                📅 Vs Hist: <span class="{ 'pos' if (dv-dh)>=0 else 'neg' }">{fmt_diff(dv-dh)} km</span>
            </div>
        </div>""", unsafe_allow_html=True)
        
    with c3:
        st.markdown(f"""
        <div class="card-box">
            <div class="stat-label">⛰️ Altimetría</div>
            <div class="stat-value">{av:.0f} m</div>
            <div class="comp-text">Acumulado Semanal</div>
        </div>""", unsafe_allow_html=True)

    # DISCIPLINAS
    def render_disc(title, icon, cat, xtra_type):
        st.markdown(f"<div class='disc-header'>{icon} {title}</div>", unsafe_allow_html=True)
        t_v, t_a, t_h = get_metrics(cat, 'T', True)
        d_v, d_a, d_h = get_metrics(cat, 'D', False)
        
        # Extra
        if xtra_type == 'elev':
            e_v, e_a, e_h = get_metrics(cat, 'E', False)
            e_lbl, e_fmt = "Desnivel", f"{e_v:.0f} m"
        else:
            e_v, e_a, e_h = get_metrics(cat, 'R', True)
            e_lbl, e_fmt = "Ritmo", fmt_pace(e_v, 'swim' if xtra_type=='swim' else 'run')
            
        # Tabla HTML
        st.markdown(f"""
        <table style="width:100%; font-size:14px;">
            <tr style="color:#666; border-bottom:1px solid #ddd;">
                <th style="text-align:left">Métrica</th>
                <th style="text-align:left">Dato</th>
                <th style="text-align:left">Vs Equipo</th>
                <th style="text-align:left">Vs Histórico</th>
            </tr>
            <tr>
                <td><b>Tiempo</b></td>
                <td>{fmt_h_m(t_v)}</td>
                <td class="{ 'pos' if (t_v-t_a)>=0 else 'neg' }">{fmt_diff(t_v-t_a, True)}</td>
                <td class="{ 'pos' if (t_v-t_h)>=0 else 'neg' }">{fmt_diff(t_v-t_h, True)}</td>
            </tr>
            <tr>
                <td><b>Distancia</b></td>
                <td>{d_v:.1f} km</td>
                <td class="{ 'pos' if (d_v-d_a)>=0 else 'neg' }">{fmt_diff(d_v-d_a)}</td>
                <td class="{ 'pos' if (d_v-d_h)>=0 else 'neg' }">{fmt_diff(d_v-d_h)}</td>
            </tr>
            <tr>
                <td><b>{e_lbl}</b></td>
                <td>{e_fmt}</td>
                <td>-</td>
                <td>-</td>
            </tr>
        </table>
        """, unsafe_allow_html=True)

    c_n, c_b, c_r = st.columns(3)
    with c_n: render_disc("NATACIÓN", "🏊", "Nat", "swim")
    with c_b: render_disc("CICLISMO", "🚴", "Bici", "elev")
    with c_r: render_disc("TROTE", "🏃", "Trote", "run")

    st.markdown("---")
    cv, cva, _ = get_metrics('Global', 'CV', False)
    diff_cv = cv - cva
    msg = "Mejor que prom." if diff_cv >= 0 else "Bajo el prom."
    st.info(f"⚖️ **CONSISTENCIA (CV):** {cv:.2f} ({msg})")
