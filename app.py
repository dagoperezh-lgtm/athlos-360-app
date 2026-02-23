# =============================================================================
# 🏃 METRI KM - V28.2 (FUSIÓN AUTOMÁTICA + ANTI-DUPLICADOS + NOTA EXPLICATIVA)
# =============================================================================
import streamlit as st
import pandas as pd
import os
import base64
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Metri KM", page_icon="⏱️", layout="wide")

# --- BASE DE DATOS PRINCIPAL ---
ARCHIVO = "historico.xlsx"

# --- LÓGICA INTELIGENTE DE LOGOS ---
def encontrar_logo():
    candidatos = ["logo_metrikm.png", "logo_metrikm.jpg", "logo_metrikm.jpeg"]
    for archivo in candidatos:
        if os.path.exists(archivo): return archivo
    return None

LOGO_ACTIVO = encontrar_logo()
LOGO_TYM_FILE = "Tym Logo.jpg"

def get_img_as_base64(file_path):
    with open(file_path, "rb") as f: data = f.read()
    return base64.b64encode(data).decode()

# --- ESTILOS CSS ---
st.markdown("""
<style>
    :root { --primary-orange: #FF6600; --secondary-black: #111111; }
    h1, h2, h3, .main-title, .cover-title, .sub-title { color: var(--text-color) !important; }
    .cover-title { font-size: 50px; font-weight: 800; text-align: center; margin-top: 10px; color: var(--secondary-black); }
    .cover-sub { font-size: 22px; text-align: center; margin-bottom: 40px; opacity: 0.8; }
    .main-title { font-size: 32px; font-weight: bold; margin-bottom: 5px; border-bottom: 3px solid var(--primary-orange); display: inline-block; padding-bottom: 5px; }
    .sub-title { font-size: 18px; margin-bottom: 15px; opacity: 0.8; }
    .card-box { background-color: white !important; padding: 18px; border-radius: 12px; border: 1px solid #e0e0e0; border-left: 6px solid var(--primary-orange); margin-bottom: 15px; }
    .kpi-club-box { background-color: #FFF3E0 !important; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; border: 1px solid #FFE0B2; }
    .stat-label { font-size: 14px; font-weight: bold; color: #666 !important; text-transform: uppercase; }
    .stat-value { font-size: 28px; font-weight: 800; color: var(--secondary-black) !important; }
    .comp-text { font-size: 13px; margin-top: 5px; color: #555 !important; }
    .kpi-club-val { font-size: 36px; font-weight: 800; color: var(--primary-orange) !important; }
    .kpi-club-lbl { font-size: 14px; color: #444 !important; font-weight: bold; text-transform: uppercase; }
    .rank-badge-lg { background-color: var(--secondary-black); color: white !important; padding: 10px 20px; border-radius: 8px; font-size: 20px; font-weight: bold; margin-right: 15px; display: inline-block; border-left: 5px solid var(--primary-orange); }
    .top10-header { background-color: var(--secondary-black) !important; color: white !important; padding: 12px; border-radius: 8px 8px 0 0; font-weight: bold; text-transform: uppercase; }
    .top10-table { width: 100%; border-collapse: collapse; background-color: white !important; border: 1px solid #ddd; }
    .top10-table td, .top10-table th { padding: 10px; border-bottom: 1px solid #eee; text-align: left; font-size: 14px; color: #333 !important; }
    .disc-header { background-color: #FFF3E0 !important; padding: 10px 15px; font-weight: bold; font-size: 18px; border-radius: 8px; margin-top: 15px; color: var(--primary-orange) !important; border: 1px solid #FFE0B2; }
    .rank-section-title { font-size: 16px; font-weight: bold; text-transform: uppercase; margin-bottom: 8px; color: var(--text-color) !important; }
    .pos { color: #2E7D32 !important; font-weight: bold; }
    .neg { color: #C62828 !important; font-weight: bold; }
    .alert-box { padding: 10px; border-radius: 5px; margin-bottom: 5px; font-size: 13px; font-weight: bold; color: #333 !important; }
    .alert-red { background-color: #ffebee !important; color: #c62828 !important; border: 1px solid #ffcdd2; }
    .coach-section { margin-top: 30px; border-top: 2px dashed #ccc; padding-top: 20px; }
    .stSelectbox label { text-align: center; width: 100%; font-size: 18px !important; color: #555 !important; }
</style>
""", unsafe_allow_html=True)

# SESIÓN
if 'club_activo' not in st.session_state: st.session_state['club_activo'] = None
if 'vista_actual' not in st.session_state: st.session_state['vista_actual'] = 'home'

# --- HELPER SIDEBAR ---
def render_logos_sidebar():
    if LOGO_ACTIVO: st.sidebar.image(LOGO_ACTIVO, width=220)
    else: st.sidebar.markdown("## 🟠 Metri KM")

    if st.session_state['club_activo'] == "TYM Triathlon":
        st.sidebar.markdown("---")
        if os.path.exists(LOGO_TYM_FILE):
            c1,c2,c3 = st.sidebar.columns([1,2,1])
            with c2: st.image(LOGO_TYM_FILE, width=150)
        st.sidebar.markdown("<h3 style='text-align: center; color: inherit; font-size: 16px;'>TYM Triathlon</h3>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

# --- MOTOR DE PROCESAMIENTO DE DATOS ---
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
                if col: 
                    d.rename(columns={col: 'Nombre'}, inplace=True)
                    # 🔥 FILTRO ANTI-DUPLICADOS: Elimina espacios ocultos y convierte a Formato Título ("Claudio Correa")
                    d['Nombre'] = d['Nombre'].astype(str).str.strip().str.title()
                return d
    except: return None
    return None

def clean_time(val):
    if pd.isna(val) or val == 'NC': return 0.0
    s = str(val).strip().split(' ')[-1]
    try:
        if ':' in s:
            p = [float(x) for x in s.split(':')]
            return (p[0]*3600 + p[1]*60 + (p[2] if len(p)>2 else 0)) / 86400.0
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
        return f"{m}:{s:02d} {'/100m' if sport=='swim' else '/km'}"
    except: return "-"

def fmt_diff(v, is_t=False):
    if abs(v) < 0.0001: return "-"
    signo = "+" if v > 0 else "-"
    v = abs(v)
    if is_t:
        h = int(v * 24); m = int((v * 24 * 60) % 60)
        return f"{signo}{h}h {m}m"
    return f"{signo}{v:.1f}"

# CARGA GLOBAL DE VISTAS (Solo si existe el archivo)
data = {}
df_base = None
ultima_sem = "N/A"
cols_sem = []

if os.path.exists(ARCHIVO):
    with st.spinner("Cargando datos..."):
        data = {
            'Global': {'T': get_df_safe("Tiempo Total"), 'D': get_df_safe("Distancia Total"), 'A': get_df_safe("Altimetría Total")},
            'Nat': {'T': get_df_safe("Natación"), 'D': get_df_safe("Nat Distancia"), 'R': get_df_safe("Nat Ritmo")},
            'Bici': {'T': get_df_safe("Ciclismo"), 'D': get_df_safe("Ciclismo Distancia"), 'E': get_df_safe("Ciclismo Desnivel"), 'Max': get_df_safe("Ciclismo Max")},
            'Trote': {'T': get_df_safe("Trote"), 'D': get_df_safe("Trote Distancia"), 'R': get_df_safe("Trote Ritmo"), 'E': get_df_safe("Trote Desnivel"), 'Max': get_df_safe("Trote Max")}
        }
    try:
        df_base = data['Global']['D']
        if df_base is not None:
            cols_sem = [c for c in df_base.columns if c.startswith("Sem")]
            if cols_sem: ultima_sem = cols_sem[-1] 
    except:
        pass

# --- 1. PORTADA ---
if st.session_state['club_activo'] is None:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if LOGO_ACTIVO: 
            img_b64 = get_img_as_base64(LOGO_ACTIVO)
            st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{img_b64}" width="300"></div>', unsafe_allow_html=True)
        else: 
            st.markdown("<div class='cover-title'>Metri KM</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='cover-sub'>Plataforma de Alto Rendimiento</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        club_sel = st.selectbox("Selecciona tu Club:", ["Seleccionar...", "TYM Triathlon"])
        
        if club_sel == "TYM Triathlon":
            if os.path.exists(LOGO_TYM_FILE):
                img_tym_b64 = get_img_as_base64(LOGO_TYM_FILE)
                st.markdown(f'<div style="text-align: center; margin: 20px 0;"><img src="data:image/png;base64,{img_tym_b64}" width="150"></div>', unsafe_allow_html=True)
            
            if st.button("INGRESAR 🚀", type="primary", use_container_width=True):
                st.session_state['club_activo'] = "TYM Triathlon"
                st.session_state['vista_actual'] = 'menu'
                st.rerun()
    st.stop()

# ENCABEZADO DE NAVEGACIÓN
if st.session_state['vista_actual'] != 'home' and st.session_state['vista_actual'] != 'menu':
    if st.button("⬅️ Volver al Menú Principal"):
        st.session_state['vista_actual'] = 'menu'
        st.rerun()
    st.markdown("---")

# --- VISTAS DEL SISTEMA ---

# 1. MENÚ PRINCIPAL
if st.session_state['vista_actual'] == 'menu':
    render_logos_sidebar()
    if st.sidebar.button("🏠 Cerrar Sesión"):
        st.session_state['club_activo'] = None; st.session_state['vista_actual'] = 'home'; st.rerun()

    st.markdown(f"<div class='cover-title'>Hola, Equipo {st.session_state['club_activo']}</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("📊 **Resumen del Club**\n\nEstadísticas Globales")
        if st.button("Ver Resumen", use_container_width=True): st.session_state['vista_actual'] = 'resumen'; st.rerun()
    with c2:
        st.info("👤 **Ficha Personal**\n\nDetalle por Atleta")
        if st.button("Ver Ficha", use_container_width=True): st.session_state['vista_actual'] = 'ficha'; st.rerun()
    with c3:
        st.warning("⚙️ **Cargar Semana**\n\nActualizar Base de Datos")
        if st.button("Zona Admin", use_container_width=True): st.session_state['vista_actual'] = 'admin'; st.rerun()

# 2. ZONA ADMIN (MOTOR DE FUSIÓN AUTOMÁTICA)
elif st.session_state['vista_actual'] == 'admin':
    st.markdown("<div class='main-title'>⚙️ Cargar Nueva Semana</div>", unsafe_allow_html=True)
    st.write("Sube el Excel con los datos de la semana (con todas las columnas) para actualizar el Histórico automáticamente.")
    
    if not os.path.exists(ARCHIVO):
        st.error(f"⚠️ No se detecta el archivo base '{ARCHIVO}' en el sistema. Asegúrate de tenerlo en la carpeta de GitHub.")
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            nombre_sem = st.text_input("Nombre de la Semana (Ej: Sem 06)", placeholder="Sem 06")
        with col2:
            archivo_subido = st.file_uploader("Sube el Excel Semanal", type=["xlsx", "csv"])
            
        if archivo_subido and nombre_sem:
            if st.button("🔄 Fusionar y Actualizar Histórico", type="primary"):
                with st.spinner("Cocinando datos..."):
                    try:
                        # 1. Leer Semana Nueva
                        if archivo_subido.name.endswith('.csv'):
                            df_sem = pd.read_csv(archivo_subido)
                        else:
                            df_sem = pd.read_excel(archivo_subido)
                            
                        df_sem.columns = [str(c).strip() for c in df_sem.columns]
                        
                        # 2. Mapeo Inteligente (Hoja Histórica -> Columna de Semana)
                        mapeo_columnas = {
                            'Tiempo Total': 'Tiempo Total (hh:mm:ss)',
                            'Distancia Total': 'Distancia Total (km)',
                            'Altimetría Total': 'Altimetría Total (m)',
                            'Natación': 'Nat: Tiempo (hh:mm:ss)',
                            'Nat Distancia': 'Nat: Distancia (km)',
                            'Nat Ritmo': 'Nat: Ritmo (min/100m)',
                            'Ciclismo': 'Ciclismo: Tiempo (hh:mm:ss)',
                            'Ciclismo Distancia': 'Ciclismo: Distancia (km)',
                            'Ciclismo Desnivel': 'Ciclismo: KOM/Desnivel (m)',
                            'Ciclismo Max': 'Ciclismo: Más larga (km)',
                            'Trote': 'Trote: Tiempo (hh:mm:ss)',
                            'Trote Distancia': 'Trote: Distancia (km)',
                            'Trote Desnivel': 'Trote: KOM/Desnivel (m)',
                            'Trote Ritmo': 'Trote: Ritmo (min/km)',
                            'Trote Max': 'Trote: Más larga (km)',
                            'CV': 'CV (Equilibrio)'
                        }
                        
                        # 3. Leer Histórico y Fusionar
                        xls_hist = pd.ExcelFile(ARCHIVO, engine='openpyxl')
                        output = io.BytesIO()
                        
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            for sheet in xls_hist.sheet_names:
                                df_h = pd.read_excel(xls_hist, sheet_name=sheet)
                                
                                # Si la hoja coincide con nuestro mapeo y tiene nombres
                                if sheet in mapeo_columnas and 'Nombre' in df_h.columns:
                                    col_origen = mapeo_columnas[sheet]
                                    
                                    if col_origen in df_sem.columns:
                                        # Crear diccionario {atleta_minuscula: valor_nuevo}
                                        dict_vals = dict(zip(df_sem['Deportista'].astype(str).str.lower().str.strip(), df_sem[col_origen]))
                                        # Insertar nueva columna
                                        df_h[nombre_sem] = df_h['Nombre'].astype(str).str.lower().str.strip().map(dict_vals)
                                        
                                        # Rellenar vacíos
                                        if any(x in sheet for x in ['Tiempo', 'Natación', 'Ciclismo', 'Trote', 'Ritmo']) and sheet not in ['Ciclismo Distancia', 'Ciclismo Desnivel', 'Ciclismo Max', 'Trote Distancia', 'Trote Desnivel', 'Trote Max']:
                                            df_h[nombre_sem] = df_h[nombre_sem].fillna('00:00:00')
                                        else:
                                            df_h[nombre_sem] = df_h[nombre_sem].fillna(0)
                                            
                                df_h.to_excel(writer, sheet_name=sheet, index=False)
                        
                        st.success("✅ ¡Fusión completada con éxito!")
                        st.download_button(
                            label="📥 Descargar historico.xlsx Actualizado",
                            data=output.getvalue(),
                            file_name="historico.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
                        st.info("👆 Descarga el archivo y súbelo a tu GitHub reemplazando el antiguo. Luego refresca la página.")
                        
                    except Exception as e:
                        st.error(f"❌ Error al procesar: {str(e)}")

# 3. RESUMEN DEL CLUB
elif st.session_state['vista_actual'] == 'resumen':
    render_logos_sidebar()
    if st.sidebar.button("🏠 Cerrar Sesión"):
        st.session_state['club_activo'] = None; st.session_state['vista_actual'] = 'home'; st.rerun()

    if df_base is None: st.warning("No hay datos cargados."); st.stop()
    st.markdown(f"<div class='main-title'>📊 Resumen Ejecutivo ({ultima_sem})</div>", unsafe_allow_html=True)
    
    def calc_tot(df, is_t=False):
        if df is None or ultima_sem not in df.columns: return 0
        return sum([clean_time(x) if is_t else clean_num(x) for x in df[ultima_sem]])

    tt = calc_tot(data['Global']['T'], True); td = calc_tot(data['Global']['D'], False)
    act = sum(1 for x in data['Global']['D'][ultima_sem] if clean_num(x) > 0.1)
    
    k1, k2, k3 = st.columns(3)
    with k1: st.markdown(f"<div class='kpi-club-box'><div class='kpi-club-val'>{fmt_h_m(tt)}</div><div class='kpi-club-lbl'>Tiempo Total</div></div>", unsafe_allow_html=True)
    with k2: st.markdown(f"<div class='kpi-club-box'><div class='kpi-club-val'>{td:,.0f} km</div><div class='kpi-club-lbl'>Distancia Total</div></div>", unsafe_allow_html=True)
    with k3: st.markdown(f"<div class='kpi-club-box'><div class='kpi-club-val'>{act}</div><div class='kpi-club-lbl'>Activos</div></div>", unsafe_allow_html=True)

    st.markdown("<h3 style='margin-top:20px;'>🏆 Top 10: Mejores Desempeños</h3>", unsafe_allow_html=True)
    def top10(df, tit, is_t=False, u=""):
        if df is None or ultima_sem not in df.columns: return
        d = df.copy(); d['v'] = d[ultima_sem].apply(lambda x: clean_time(x) if is_t else clean_num(x))
        d = d[d['v']>0.001].sort_values('v', ascending=False).head(10)
        st.markdown(f"<div class='top10-header'>{tit}</div>", unsafe_allow_html=True)
        h = "<table class='top10-table'>"
        for i, r in enumerate(d.itertuples(), 1): h += f"<tr><td style='width:30px; font-weight:bold; color:var(--primary-orange);'>#{i}</td><td>{r.Nombre}</td><td style='text-align:right; font-weight:bold; color:#333 !important;'>{fmt_h_m(r.v) if is_t else f'{r.v:.1f} {u}'}</td></tr>"
        st.markdown(h+"</table><br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: top10(data['Global']['T'], "⏱️ Tiempo Total", True)
    with c2: top10(data['Global']['D'], "📏 Distancia Total", False, "km")
    with c3: top10(data['Global']['A'], "⛰️ Altimetría Total", False, "m")

    st.markdown("#### Desglose por Disciplina")
    c1, c2 = st.columns(2)
    with c1: top10(data['Nat']['D'], "🏊 Distancia Natación", False, "km")
    with c2: top10(data['Nat']['T'], "🏊 Tiempo Natación", True)
    c1, c2, c3 = st.columns(3)
    with c1: top10(data['Bici']['D'], "🚴 Distancia Ciclismo", False, "km")
    with c2: top10(data['Bici']['T'], "🚴 Tiempo Ciclismo", True)
    with c3: top10(data['Bici']['E'], "🚴 Altimetría Ciclismo", False, "m")
    c1, c2, c3 = st.columns(3)
    with c1: top10(data['Trote']['D'], "🏃 Distancia Trote", False, "km")
    with c2: top10(data['Trote']['T'], "🏃 Tiempo Trote", True)
    with c3: top10(data['Trote']['E'], "🏃 Altimetría Trote", False, "m")

    # ZONA COACH Y PODIOS
    st.markdown("<div class='coach-section'><h3 style='color:inherit;'>🧠 ZONA COACH</h3></div>", unsafe_allow_html=True)
    cc1, cc2 = st.columns([1, 2])
    with cc1:
        with st.expander("🚨 Ver Semáforo de Desbalance", expanded=False):
            st.caption("Atletas activos sin disciplina.")
            alertas_html = ""
            df_act = data['Global']['D']
            if df_act is not None:
                for _, row in df_act.iterrows():
                    nom = row['Nombre']
                    if clean_num(row[ultima_sem]) > 0: 
                        nat_val = 0; bici_val = 0; trote_val = 0
                        if data['Nat']['D'] is not None:
                            r = data['Nat']['D'][data['Nat']['D']['Nombre']==nom]
                            if not r.empty: nat_val = clean_num(r[ultima_sem].values[0])
                        if data['Bici']['D'] is not None:
                            r = data['Bici']['D'][data['Bici']['D']['Nombre']==nom]
                            if not r.empty: bici_val = clean_num(r[ultima_sem].values[0])
                        if data['Trote']['D'] is not None:
                            r = data['Trote']['D'][data['Trote']['D']['Nombre']==nom]
                            if not r.empty: trote_val = clean_num(r[ultima_sem].values[0])

                        missing = []
                        if nat_val == 0: missing.append("Agua")
                        if bici_val == 0: missing.append("Bici")
                        if trote_val == 0: missing.append("Trote")
                        
                        if missing:
                            alertas_html += f"<div class='alert-box alert-red'>{nom}: Sin {' / '.join(missing)}</div>"
            
            if alertas_html == "": alertas_html = "<div style='color:green;'>✅ Todos cumplieron.</div>"
            st.markdown(alertas_html, unsafe_allow_html=True)

    with cc2:
        st.markdown("**🔥 El Podio de Resistencia (Sesión Más Larga)**")
        c_sub1, c_sub2 = st.columns(2)
        with c_sub1: top10(data['Bici']['Max'], "🚴 Fondo Ciclismo", False, "km")
        with c_sub2: top10(data['Trote']['Max'], "🏃 Fondo Trote", False, "km")

# 4. FICHA INDIVIDUAL
elif st.session_state['vista_actual'] == 'ficha':
    st.markdown(f"<div class='main-title'>REPORTE INDIVIDUAL</div>", unsafe_allow_html=True)
    if df_base is None: st.warning("No hay datos cargados."); st.stop()
    
    with st.container():
        st.info("👇 **Busca tu nombre aquí:**")
        nombres = sorted([str(x) for x in df_base['Nombre'].unique() if str(x).lower() not in ['nan','0']])
        nombres.insert(0, " Selecciona...")
        sel = st.selectbox("Atleta:", nombres, key="atleta_selector", label_visibility="collapsed")
    
    render_logos_sidebar()
    if st.sidebar.button("🏠 Cerrar Sesión"):
        st.session_state['club_activo'] = None; st.session_state['vista_actual'] = 'home'; st.rerun()
    st.markdown("---")

    if sel == " Selecciona...":
        st.info("👈 Selecciona tu nombre en el buscador de arriba.")
    else:
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

        st.markdown(f"<div class='sub-title'>Atleta: {sel} | Semana: {ultima_sem}</div>", unsafe_allow_html=True)
        st.markdown("<div class='rank-section-title'>🏆 RANKING EN EL CLUB</div>", unsafe_allow_html=True)
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
            
            def row(l, v, d_eq, d_eq_txt, d_hi, d_hi_txt):
                ce = "pos" if d_eq >= 0 else "neg"
                ch = "pos" if d_hi >= 0 else "neg"
                te = d_eq_txt if d_eq != 0 else "-"
                th = d_hi_txt if d_hi != 0 else "-"
                return f"<tr><td><b>{l}</b></td><td>{v}</td><td class='{ce}'>{te}</td><td class='{ch}'>{th}</td></tr>"

            h = f"<table style='width:100%; font-size:14px;'><tr style='color:#666; border-bottom:1px solid #ddd;'><th>Métrica</th><th>Dato</th><th>Vs Eq</th><th>Vs Hist</th></tr>"
            
            h += row("Tiempo", fmt_h_m(t_v), t_v-t_a, fmt_diff(t_v-t_a, True), t_v-t_h, fmt_diff(t_v-t_h, True))
            h += row("Distancia", f"{d_v:.1f} km", d_v-d_a, fmt_diff(d_v-d_a), d_v-d_h, fmt_diff(d_v-d_h))

            if xtype == 'elev': 
                e_v, e_a, e_h = kpi(cat, 'E', False)
                h += f"<tr><td><b>Desnivel</b></td><td>{e_v:.0f} m</td><td>-</td><td>-</td></tr>"
                sp_v = d_v/(t_v*24) if t_v>0.001 else 0
                sp_a = d_a/(t_a*24) if t_a>0.001 else 0
                h += row("Velocidad", f"{sp_v:.1f} km/h", sp_v-sp_a, fmt_diff(sp_v-sp_a), 0, "-")
            elif xtype == 'run': 
                r_v, r_a, r_h = kpi(cat, 'R', True)
                h += f"<tr><td><b>Ritmo</b></td><td>{fmt_pace(r_v, 'run')}</td><td>-</td><td>-</td></tr>"
                e_v, e_a, e_h = kpi(cat, 'E', False)
                if e_v > 0: h += f"<tr><td><b>Desnivel</b></td><td>{e_v:.0f} m</td><td>-</td><td>-</td></tr>"
            else:
                r_v, r_a, r_h = kpi(cat, 'R', True)
                h += f"<tr><td><b>Ritmo</b></td><td>{fmt_pace(r_v, 'swim')}</td><td>-</td><td>-</td></tr>"
            st.markdown(h+"</table>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1: draw_disc("NATACIÓN", "🏊", "Nat", "swim")
        with c2: draw_disc("CICLISMO", "🚴", "Bici", "elev")
        with c3: draw_disc("TROTE", "🏃", "Trote", "run")

        # --- NOTA EXPLICATIVA DE MÉTRICAS ---
        st.markdown("""
        <div style='background-color: #F8F9FA; padding: 15px; border-radius: 8px; border-left: 5px solid var(--primary-orange); margin-top: 30px; font-size: 14px; color: #555;'>
            <b>💡 Guía de lectura:</b><br>
            <span style='color: #333;'><b>• Vs Eq (Equipo):</b></span> Compara tu registro de esta semana con el promedio general del club en esta misma semana.<br>
            <span style='color: #333;'><b>• Vs Hist (Histórico):</b></span> Compara tu registro de esta semana con tu propio promedio de las semanas anteriores.
        </div>
        """, unsafe_allow_html=True)
