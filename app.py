# =============================================================================
# 🦅 ATHLOS 360 - REPORTE TÉCNICO V25 (ESTRICTO)
# =============================================================================
import streamlit as st
import pandas as pd
import os
import math

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Reporte V25", page_icon="🦅", layout="wide")

# ESTILOS CSS (Réplica Visual del Word)
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

# --- 2. MOTOR DE DATOS (LECTURA SEGURA) ---
ARCHIVO = "06 Sem (tst).xlsx"

@st.cache_data(ttl=60)
def cargar_excel():
    if not os.path.exists(ARCHIVO): return None
    try:
        return pd.ExcelFile(ARCHIVO, engine='openpyxl')
    except: return None

@st.cache_data(ttl=60)
def get_df(nombre_hoja):
    xl = cargar_excel()
    if xl is None: return None
    # Buscar hoja flexible (ej: "Nat Ritmo" o "Nat: Ritmo")
    target = next((h for h in xl.sheet_names if nombre_hoja.lower() in h.lower().replace(":","")), None)
    if target:
        df = pd.read_excel(xl, sheet_name=target)
        df.columns = [str(c).strip() for c in df.columns]
        # Normalizar columna nombre
        col = next((c for c in df.columns if c.lower() in ['nombre','deportista','atleta']), None)
        if col: df.rename(columns={col: 'Nombre'}, inplace=True)
        return df
    return None

# --- 3. SANITIZADORES (FIX "NÚMEROS INFINITOS") ---
def clean_float(val):
    """Fuerza cualquier cosa a ser un float o 0.0"""
    if pd.isna(val): return 0.0
    try:
        # Si es texto con hora "12:30:00"
        s = str(val).strip()
        if ':' in s:
            p = [float(x) for x in s.split(':')]
            sec = 0
            if len(p)==3: sec = p[0]*3600 + p[1]*60 + p[2]
            elif len(p)==2: sec = p[0]*60 + p[1]
            return sec / 86400.0
        return float(val)
    except: return 0.0

def fmt_h_m(val_float):
    """0.52341 -> 12h 33m"""
    if val_float <= 0.0001: return "-"
    try:
        tot_h = val_float * 24
        h = int(tot_h)
        m = int((tot_h - h) * 60)
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
        return f"{m}m {s}s {u}"
    except: return "-"

def fmt_diff(val, es_tiempo=False):
    """Formato comparativo: +1h 20m o +5.2 km"""
    if abs(val) < 0.001: return "-"
    signo = "+" if val > 0 else "-"
    val = abs(val)
    
    if es_tiempo:
        h = int(val * 24)
        m = int((val * 24 * 60) % 60)
        return f"{signo}{h}h {m}m"
    else:
        return f"{signo}{val:.1f}"

# --- 4. GESTIÓN DE ESTADO (PORTADA) ---
if 'club_ok' not in st.session_state: st.session_state['club_ok'] = False

# =============================================================================
# VISTA 1: PORTADA (Recepción)
# =============================================================================
if not st.session_state['club_ok']:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if os.path.exists("logo_athlos.png"):
            st.image("logo_athlos.png", use_container_width=True)
        else:
            st.markdown("<h1 style='text-align:center'>ATHLOS 360</h1>", unsafe_allow_html=True)
            
        st.markdown("---")
        st.write("### Bienvenido al Portal de Rendimiento")
        club = st.selectbox("Selecciona tu Club:", ["Seleccionar...", "TYM Triathlon"])
        
        if club == "TYM Triathlon":
            if st.button("INGRESAR AL DASHBOARD", type="primary"):
                st.session_state['club_ok'] = True
                st.rerun()

# =============================================================================
# VISTA 2: REPORTE (El contenido real)
# =============================================================================
else:
    # --- BARRA LATERAL ---
    with st.sidebar:
        if os.path.exists("logo_athlos.png"): st.image("logo_athlos.png")
        if st.button("🏠 Salir"): 
            st.session_state['club_ok'] = False
            st.rerun()
        st.markdown("---")
        
        # Cargar Base para Nombres
        df_base = get_df("Distancia Total")
        if df_base is None:
            st.error("⚠️ Error: No se encuentra el archivo de datos.")
            st.stop()
            
        nombres = sorted([str(x) for x in df_base['Nombre'].unique() if str(x).lower() not in ['nan','0']])
        atleta = st.selectbox("Selecciona Atleta:", nombres)

    # --- DATOS DEL ATLETA ---
    # Identificar última semana (la columna más a la derecha que empiece con Sem)
    cols_sem = [c for c in df_base.columns if c.startswith("Sem")]
    ultima_sem = cols_sem[-1] if cols_sem else "N/A"
    
    st.markdown(f"<div class='main-title'>🦅 REPORTE 360°: {atleta}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-title'>Reporte Semanal: {ultima_sem}</div>", unsafe_allow_html=True)

    # --- CARGA DE DATOS ESPECÍFICOS (V25) ---
    # Usamos diccionarios para agrupar las hojas necesarias
    data = {
        'Global': {
            'T': get_df("Tiempo Total"),
            'D': get_df("Distancia Total"),
            'A': get_df("Altimetría Total"),
            'CV': get_df("CV")
        },
        'Nat': {
            'T': get_df("Nat Tiempo") or get_df("Natación"),
            'D': get_df("Nat Distancia"),
            'R': get_df("Nat Ritmo")
        },
        'Bici': {
            'T': get_df("Ciclismo Tiempo") or get_df("Ciclismo"),
            'D': get_df("Ciclismo Distancia"),
            'E': get_df("Ciclismo Desnivel")
        },
        'Trote': {
            'T': get_df("Trote Tiempo") or get_df("Trote"),
            'D': get_df("Trote Distancia"),
            'R': get_df("Trote Ritmo")
        }
    }

    # FUNCIÓN EXTRACTORA MAESTRA
    def get_kpis(categoria, key_tipo, es_tiempo=False):
        """Devuelve: (Valor Actual, Promedio Equipo, Promedio Histórico Atleta)"""
        df = data[categoria][key_tipo]
        if df is None: return 0.0, 0.0, 0.0
        
        # 1. Valor Actual
        row = df[df['Nombre'] == atleta]
        val_now = 0.0
        hist_avg = 0.0
        
        if not row.empty:
            val_now = clean_float(row[ultima_sem].values[0])
            # Histórico: Promedio de todas las semanas
            vals = [clean_float(row[c].values[0]) for c in cols_sem]
            hist_avg = sum(vals) / len(vals) if vals else 0.0
            
        # 2. Promedio Equipo (Semana Actual)
        # Limpiar toda la columna antes de promediar
        team_vals = [clean_float(x) for x in df[ultima_sem]]
        team_avg = sum(team_vals) / len(team_vals) if team_vals else 0.0
        
        return val_now, team_avg, hist_avg

    # === SECCIÓN 1: RESUMEN GLOBAL ===
    t_val, t_avg, t_hist = get_kpis('Global', 'T', True)
    d_val, d_avg, d_hist = get_kpis('Global', 'D', False)
    a_val, a_avg, a_hist = get_kpis('Global', 'A', False)
    
    # Calcular Diferencias
    dff_eq_t = t_val - t_avg
    dff_hi_t = t_val - t_hist
    
    # Renderizar Tarjetas
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div class="card-box">
            <div class="stat-label">⏱️ Tiempo Total</div>
            <div class="stat-value">{fmt_h_m(t_val)}</div>
            <div class="comp-text">
                👥 Vs Eq: <span class="{ 'pos' if dff_eq_t>=0 else 'neg' }">{fmt_diff(dff_eq_t, True)}</span><br>
                📅 Vs Hist: <span class="{ 'pos' if dff_hi_t>=0 else 'neg' }">{fmt_diff(dff_hi_t, True)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class="card-box">
            <div class="stat-label">📏 Distancia Total</div>
            <div class="stat-value">{d_val:.1f} km</div>
            <div class="comp-text">
                👥 Vs Eq: <span class="{ 'pos' if (d_val - d_avg)>=0 else 'neg' }">{fmt_diff(d_val - d_avg)} km</span><br>
                📅 Vs Hist: <span class="{ 'pos' if (d_val - d_hist)>=0 else 'neg' }">{fmt_diff(d_val - d_hist)} km</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card-box">
            <div class="stat-label">⛰️ Altimetría</div>
            <div class="stat-value">{a_val:.0f} m</div>
            <div class="comp-text" style="color:#888;">
                Acumulado semanal
            </div>
        </div>
        """, unsafe_allow_html=True)

    # === SECCIÓN 2: DESGLOSE POR DISCIPLINA (TABLAS) ===
    
    def render_row(label, val_fmt, val_raw, diff_eq, diff_hi, is_time=False):
        c_eq = "pos" if diff_eq >= 0 else "neg"
        c_hi = "pos" if diff_hi >= 0 else "neg"
        fmt_d_eq = fmt_diff(diff_eq, is_time)
        fmt_d_hi = fmt_diff(diff_hi, is_time)
        
        return f"""
        <tr>
            <td style="padding:8px;"><b>{label}</b></td>
            <td style="font-size:16px; font-weight:bold;">{val_fmt}</td>
            <td><span class="{c_eq}">{fmt_d_eq}</span></td>
            <td><span class="{c_hi}">{fmt_d_hi}</span></td>
        </tr>
        """

    def discipline_card(title, icon, key_cat, extra_type):
        st.markdown(f"<div class='disc-header'>{icon} {title}</div>", unsafe_allow_html=True)
        
        # Datos
        tv, ta, th = get_kpis(key_cat, 'T', True)
        dv, da, dh = get_kpis(key_cat, 'D', False)
        
        # Extra (Ritmo o Desnivel)
        if extra_type == 'elev':
            ev, ea, eh = get_kpis(key_cat, 'E', False)
            e_lbl = "Desnivel"
            e_fmt = f"{ev:.0f} m"
            e_is_t = False
        else: # pace
            ev, ea, eh = get_kpis(key_cat, 'R', True) # Ritmo es tiempo
            e_lbl = "Ritmo"
            e_fmt = fmt_pace(ev, 'swim' if extra_type=='swim' else 'run')
            e_is_t = True

        # HTML Tabla
        rows = ""
        rows += render_row("Tiempo", fmt_h_m(tv), tv, tv-ta, tv-th, True)
        rows += render_row("Distancia", f"{dv:.1f} km", dv, dv-da, dv-dh, False)
        rows += render_row(e_lbl, e_fmt, ev, ev-ea, ev-eh, e_is_t)
        
        st.markdown(f"""
        <table style="width:100%; background-color:white; border-radius:8px; border-collapse:collapse;">
            <tr style="border-bottom:1px solid #eee; font-size:12px; color:#888;">
                <th style="text-align:left; padding:8px;">Métrica</th>
                <th style="text-align:left;">Dato</th>
                <th style="text-align:left;">Vs Equipo</th>
                <th style="text-align:left;">Vs Histórico</th>
            </tr>
            {rows}
        </table>
        <br>
        """, unsafe_allow_html=True)

    c_nat, c_bici, c_run = st.columns(3)
    
    with c_nat: discipline_card("NATACIÓN", "🏊", "Nat", "swim")
    with c_bici: discipline_card("CICLISMO", "🚴", "Bici", "elev")
    with c_run: discipline_card("TROTE", "🏃", "Trote", "run")

    # === SECCIÓN 3: CONSISTENCIA ===
    cv_v, cv_a, _ = get_kpis('Global', 'CV', False)
    diff_cv = cv_v - cv_a
    msg = "Mejor que prom." if diff_cv >= 0 else "Bajo el prom."
    color_cv = "#008000" if diff_cv >= 0 else "#D00000"
    
    st.markdown("---")
    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; background-color:#eef; padding:15px; border-radius:8px;">
        <div>
            <span style="font-size:18px; font-weight:bold;">⚖️ CONSISTENCIA (CV): {cv_v:.2f}</span>
            <span style="font-size:14px; margin-left:10px; color:{color_cv};">({diff_cv:+.2f} Vs Equipo)</span>
        </div>
        <div style="font-style:italic; color:#555;">
            "{msg}"
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.success("💡 **Insight:** La consistencia es el camino al éxito.")
