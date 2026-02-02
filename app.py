# =============================================================================
# 🏆 ATHLOS 360 - APP V6.0 (LECTOR DE DATOS NORMALIZADOS)
# =============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Athlos 360", layout="wide", page_icon="🦅")

# --- 1. CARGA DE DATOS INTELIGENTE ---
ARCHIVO = "06 Sem (tst).xlsx"

@st.cache_data(ttl=60)
def get_data(hoja):
    if not os.path.exists(ARCHIVO): return None
    try:
        # Leemos con openpyxl para asegurar compatibilidad
        df = pd.read_excel(ARCHIVO, sheet_name=hoja, engine='openpyxl')
        df.columns = [str(c).strip() for c in df.columns] # Limpiar espacios
        # Normalizar nombre
        col_nom = next((c for c in df.columns if c.lower() in ['nombre','deportista','atleta']), None)
        if col_nom: df.rename(columns={col_nom: 'Nombre'}, inplace=True)
        return df
    except: return None

def fmt_time(val):
    """Convierte float de Excel a texto legible"""
    if pd.isna(val) or val == 0: return "0h 0m"
    try:
        horas = val * 24
        h = int(horas)
        m = int((horas - h) * 60)
        return f"{h}h {m}m"
    except: return "0h 0m"

# --- 2. INTERFAZ ---
with st.sidebar:
    if os.path.exists("logo_athlos.png"): st.image("logo_athlos.png")
    else: st.header("ATHLOS 360")
    
    st.header("Club: TYM Triathlon")
    
    # Cargar base para lista de nombres
    df_base = get_data("Distancia Total")
    if df_base is None:
        st.error("⚠️ Esperando datos...")
        st.stop()
        
    nombres = sorted([str(x) for x in df_base['Nombre'].unique() if str(x).lower() not in ['nan', '0', 'none']])
    nombres.insert(0, "🏠 Ver Resumen del Club")
    atleta = st.selectbox("Selecciona Atleta:", nombres)

# --- 3. DASHBOARD ---
if atleta == "🏠 Ver Resumen del Club":
    st.title("🦅 Resumen Semanal del Club")
    
    # KPIs Club
    cols_sem = [c for c in df_base.columns if c.startswith("Sem")]
    if cols_sem:
        ultima = cols_sem[-1]
        df_base[ultima] = pd.to_numeric(df_base[ultima], errors='coerce').fillna(0)
        
        total = df_base[ultima].sum()
        top = df_base.nlargest(1, ultima).iloc[0]
        
        c1, c2 = st.columns(2)
        c1.metric("Km Totales (Club)", f"{total:,.0f} km")
        c2.metric("Mayor Distancia", f"{top['Nombre']} ({top[ultima]:.1f} km)")
        
        st.subheader(f"🏆 Top 10 - {ultima}")
        st.table(df_base.nlargest(10, ultima)[['Nombre', ultima]])
    else:
        st.info("No hay datos de semanas aún.")

else:
    st.title(f"📊 {atleta}")
    
    # Cargar Hojas Clave (Nombres corregidos y verificados)
    df_t = get_data("Tiempo Total")
    df_n = get_data("Nat Distancia")
    df_b = get_data("Ciclismo Distancia")
    df_r = get_data("Trote Distancia")
    
    cols_sem = [c for c in df_base.columns if c.startswith("Sem")]
    ultima = cols_sem[-1] if cols_sem else "N/A"
    
    # --- TARJETAS ---
    c1, c2, c3 = st.columns(3)
    
    # 1. Distancia
    row = df_base[df_base['Nombre']==atleta]
    val_d = row[ultima].values[0] if not row.empty else 0
    c1.metric("Distancia Total", f"{float(val_d):.1f} km")
    
    # 2. Tiempo
    val_t_txt = "0h 0m"
    if df_t is not None:
        row_t = df_t[df_t['Nombre']==atleta]
        if not row_t.empty:
            val_t = row_t[ultima].values[0]
            val_t_txt = fmt_time(val_t)
    c2.metric("Tiempo Total", val_t_txt)
    
    # 3. Disciplina Top
    vals = {'Nat':0, 'Bici':0, 'Trote':0}
    if df_n is not None and not df_n[df_n['Nombre']==atleta].empty: vals['Nat'] = df_n[df_n['Nombre']==atleta][ultima].values[0]
    if df_b is not None and not df_b[df_b['Nombre']==atleta].empty: vals['Bici'] = df_b[df_b['Nombre']==atleta][ultima].values[0]
    if df_r is not None and not df_r[df_r['Nombre']==atleta].empty: vals['Trote'] = df_r[df_r['Nombre']==atleta][ultima].values[0]
    
    top_disc = max(vals, key=vals.get)
    c3.metric("Enfoque", top_disc, f"{vals[top_disc]:.1f} km")
    
    st.markdown("---")
    
    # --- GRÁFICOS HISTÓRICOS ---
    t1, t2, t3 = st.tabs(["🏊‍♂️ Natación", "🚴‍♂️ Ciclismo", "🏃‍♂️ Trote"])
    
    def graficar(df_in, color, titulo):
        if df_in is None: return
        r = df_in[df_in['Nombre']==atleta]
        if r.empty: 
            st.warning("Sin datos")
            return
            
        # Extraer historia
        y = []
        x = []
        for c in cols_sem:
            val = pd.to_numeric(r[c].values[0], errors='coerce')
            y.append(val if pd.notnull(val) else 0)
            x.append(c)
            
        fig = px.area(x=x, y=y, title=titulo)
        fig.update_traces(line_color=color)
        st.plotly_chart(fig, use_container_width=True)

    with t1: graficar(df_n, "#00a8e8", "Histórico Natación")
    with t2: graficar(df_b, "#e85d04", "Histórico Ciclismo")
    with t3: graficar(df_r, "#d90429", "Histórico Trote")
