# =============================================================================
# 🦅 ATHLOS 360 - REPORTE DE RENDIMIENTO (MODELO V25)
# =============================================================================
import streamlit as st
import pandas as pd
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Athlos 360 Report", page_icon="🦅", layout="wide", initial_sidebar_state="collapsed")

# Estilos CSS (Idénticos al DOCX)
st.markdown("""
<style>
    .report-title { font-size: 28px; font-weight: bold; color: #111; margin-bottom: 5px; }
    .report-subtitle { font-size: 16px; color: #555; margin-bottom: 20px; border-bottom: 2px solid #FF4B4B; padding-bottom: 10px; }
    .discipline-header { 
        background-color: #f0f2f6; 
        padding: 8px 15px; 
        border-radius: 5px; 
        font-weight: bold; 
        color: #333; 
        margin-top: 20px; 
        margin-bottom: 10px;
    }
    .metric-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
    .metric-label { font-weight: bold; color: #444; }
    .metric-value { font-size: 18px; font-weight: bold; }
    .metric-comp { font-size: 13px; margin-left: 10px; }
    .pos { color: green; }
    .neg { color: red; }
</style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
ARCHIVO = "06 Sem (tst).xlsx"

@st.cache_data(ttl=60)
def cargar_hoja(nombre_clave):
    if not os.path.exists(ARCHIVO): return None
    try:
        xls = pd.ExcelFile(ARCHIVO, engine='openpyxl')
        hoja = next((h for h in xls.sheet_names if nombre_clave.lower() in h.lower()), None)
        if hoja:
            df = pd.read_excel(xls, sheet_name=hoja)
            df.columns = [str(c).strip() for c in df.columns]
            col_nom = next((c for c in df.columns if c.lower() in ['nombre','deportista','atleta']), None)
            if col_nom: df.rename(columns={col_nom: 'Nombre'}, inplace=True)
            return df
    except: pass
    return None

# --- FORMATTERS (Los traductores de números) ---
def fmt_time(val): # 0.5 -> 12h 00m
    if pd.isna(val) or val == 0: return "-"
    try:
        h = int(val * 24)
        m = int((val * 24 * 60) % 60)
        return f"{h}h {m}m"
    except: return "-"

def fmt_pace(val, sport="run"): # 0.003 -> 5:00 min/km
    if pd.isna(val) or val == 0: return "-"
    try:
        total_min = val * 24 * 60
        m = int(total_min)
        s = int((total_min - m) * 60)
        u = "min/100m" if sport == "swim" else "min/km"
        return f"{m}:{s:02d} {u}"
    except: return "-"

def fmt_diff_time(val): # +0.1 -> +2h 24m
    if val == 0: return "-"
    signo = "+" if val > 0 else "-"
    val = abs(val)
    h = int(val * 24)
    m = int((val * 24 * 60) % 60)
    return f"{signo}{h}h {m}m"

# --- DATOS COMPLETOS ---
# Cargamos TODAS las hojas necesarias para el reporte V25
dfs = {
    'Dist': cargar_hoja("Distancia Total"),
    'Time': cargar_hoja("Tiempo Total"),
    'Alt': cargar_hoja("Altimetría Total"),
    'CV': cargar_hoja("CV"),
    
    'N_Dist': cargar_hoja("Nat Distancia"),
    'N_Time': cargar_hoja("Natación"), # A veces se llama Natación a secas
    'N_Pace': cargar_hoja("Nat Ritmo"),
    
    'B_Dist': cargar_hoja("Ciclismo Distancia"),
    'B_Time': cargar_hoja("Ciclismo"),
    'B_Elev': cargar_hoja("Ciclismo Desnivel"),
    
    'R_Dist': cargar_hoja("Trote Distancia"),
    'R_Time': cargar_hoja("Trote"),
    'R_Pace': cargar_hoja("Trote Ritmo")
}
# Fallback nombres
if dfs['N_Time'] is None: dfs['N_Time'] = cargar_hoja("Nat: Tiempo")
if dfs['B_Time'] is None: dfs['B_Time'] = cargar_hoja("Ciclismo: Tiempo")
if dfs['R_Time'] is None: dfs['R_Time'] = cargar_hoja("Trote: Tiempo")

# --- PORTADA ---
if 'ingreso' not in st.session_state: st.session_state['ingreso'] = False

if not st.session_state['ingreso']:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if os.path.exists("logo_athlos.png"): st.image("logo_athlos.png")
        st.markdown("<h1 style='text-align:center'>ATHLOS 360</h1>", unsafe_allow_html=True)
        club = st.selectbox("Club", ["Seleccionar...", "TYM Triathlon"])
        if club == "TYM Triathlon":
            if st.button("VER REPORTE"): st.session_state['ingreso'] = True; st.rerun()
else:
    # --- REPORTE ---
    with st.sidebar:
        if os.path.exists("logo_athlos.png"): st.image("logo_athlos.png")
        if st.button("🏠 Salir"): st.session_state['ingreso'] = False; st.rerun()
        st.markdown("---")
        base = dfs['Dist']
        if base is not None:
            nombres = sorted([str(x) for x in base['Nombre'].unique() if str(x).lower() not in ['nan','0']])
            atleta = st.selectbox("Selecciona Atleta", nombres)
    
    if base is not None:
        # Semana Actual
        cols_sem = [c for c in base.columns if c.startswith("Sem")]
        ultima = cols_sem[-1] if cols_sem else "N/A"
        
        # --- FUNCIONES DE CÁLCULO V25 ---
        def get_data_row(key, col):
            if dfs[key] is None: return 0
            r = dfs[key][dfs[key]['Nombre'] == atleta]
            if r.empty: return 0
            val = pd.to_numeric(r[col].values[0], errors='coerce')
            return val if pd.notnull(val) else 0

        def get_avgs(key):
            if dfs[key] is None: return 0, 0
            # Promedio Equipo (Semana Actual)
            avg_team = pd.to_numeric(dfs[key][ultima], errors='coerce').mean()
            # Promedio Histórico Personal
            r = dfs[key][dfs[key]['Nombre'] == atleta]
            if r.empty: return avg_team, 0
            hist_vals = [pd.to_numeric(r[c].values[0], errors='coerce') or 0 for c in cols_sem]
            avg_hist = sum(hist_vals) / len(hist_vals) if hist_vals else 0
            return avg_team, avg_hist

        # --- CABECERA REPORTE ---
        st.markdown(f"<div class='report-title'>🦅 REPORTE 360°: {atleta}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='report-subtitle'>Reporte Semanal: {ultima}</div>", unsafe_allow_html=True)

        # DATOS GLOBALES
        v_time = get_data_row('Time', ultima)
        v_dist = get_data_row('Dist', ultima)
        v_alt = get_data_row('Alt', ultima)
        
        # Comparativas Globales
        avg_tm_t, avg_hi_t = get_avgs('Time')
        diff_tm = v_time - avg_tm_t
        diff_hi = v_time - avg_hi_t
        
        # Tarjetas Principales
        k1, k2, k3 = st.columns(3)
        k1.metric("⏱️ Tiempo Total", fmt_time(v_time))
        k2.metric("📏 Distancia", f"{v_dist:.1f} km")
        k3.metric("⛰️ Altimetría", f"{v_alt:.0f} m")
        
        # Línea de Comparativa V25
        cls_tm = "pos" if diff_tm >= 0 else "neg"
        cls_hi = "pos" if diff_hi >= 0 else "neg"
        
        st.markdown(f"""
        <div style='background-color:#f9f9f9; padding:10px; border-radius:5px; margin-bottom:20px'>
            <b>👥 Vs Equipo:</b> <span class='{cls_tm}'>{fmt_diff_time(diff_tm)}</span> &nbsp;|&nbsp;
            <b>📅 Vs Promedio Anual:</b> <span class='{cls_hi}'>{fmt_diff_time(diff_hi)}</span>
        </div>
        """, unsafe_allow_html=True)

        # --- SECCIONES POR DISCIPLINA ---
        
        def render_section(title, icon, keys, is_swim=False):
            st.markdown(f"<div class='discipline-header'>{icon} {title}</div>", unsafe_allow_html=True)
            
            # Datos
            t = get_data_row(keys['t'], ultima)
            d = get_data_row(keys['d'], ultima)
            
            # Extra (Ritmo o Desnivel)
            if 'p' in keys:
                e_val = get_data_row(keys['p'], ultima)
                e_lbl = "Ritmo"
                e_fmt = fmt_pace(e_val, "swim" if is_swim else "run")
            elif 'e' in keys:
                e_val = get_data_row(keys['e'], ultima)
                e_lbl = "Desnivel"
                e_fmt = f"{e_val:.0f} m"
                
            # Comparativas (Usando Tiempo como base del esfuerzo)
            av_tm, av_hi = get_avgs(keys['t'])
            d_tm = t - av_tm
            d_hi = t - av_hi
            
            c_tm = "green" if d_tm >= 0 else "red"
            c_hi = "blue" if d_hi >= 0 else "orange"

            # Tabla HTML manual para control total
            st.markdown(f"""
            <table style="width:100%">
                <tr>
                    <td style="width:30%"><b>Tiempo:</b> {fmt_time(t)}</td>
                    <td style="width:30%"><b>Distancia:</b> {d:.1f} km</td>
                    <td style="width:40%"><b>{e_lbl}:</b> {e_fmt}</td>
                </tr>
                <tr>
                    <td colspan="3" style="font-size:13px; color:#666; padding-top:5px">
                        Vs Equipo: <span style='color:{c_tm}'><b>{fmt_diff_time(d_tm)}</b></span> &nbsp; 
                        Vs Histórico: <span style='color:{c_hi}'><b>{fmt_diff_time(d_hi)}</b></span>
                    </td>
                </tr>
            </table>
            """, unsafe_allow_html=True)

        render_section("NATACIÓN", "🏊", {'t':'N_Time', 'd':'N_Dist', 'p':'N_Pace'}, True)
        render_section("CICLISMO", "🚴", {'t':'B_Time', 'd':'B_Dist', 'e':'B_Elev'})
        render_section("TROTE", "🏃", {'t':'R_Time', 'd':'R_Dist', 'p':'R_Pace'})

        # --- CONSISTENCIA ---
        st.markdown("---")
        v_cv = get_data_row('CV', ultima)
        avg_cv_team, _ = get_avgs('CV')
        diff_cv = v_cv - avg_cv_team
        
        st.markdown(f"**⚖️ CONSISTENCIA (CV):** {v_cv:.2f} "
                    f"<span style='color:{'green' if diff_cv >=0 else 'red'}'>({diff_cv:+.2f} vs Promedio)</span>", 
                    unsafe_allow_html=True)
        
        st.info("💡 **Insight:** La consistencia es el camino al éxito.")
