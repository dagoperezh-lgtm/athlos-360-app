import streamlit as st
import pandas as pd
import io
import datetime
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Athlos 360 | Generator",
    page_icon="🦅",
    layout="centered"
)

# --- ESTILOS CSS (Para que se vea Pro) ---
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stButton>button {width: 100%; border-radius: 5px; background-color: #003366; color: white;}
    .stButton>button:hover {background-color: #004080; color: white;}
    h1 {color: #003366;}
    </style>
""", unsafe_allow_html=True)

# --- TÍTULO ---
st.title("🦅 Athlos 360")
st.markdown("**Generador de Reportes de Rendimiento Deportivo**")
st.write("---")

# --- BARRA LATERAL (Carga de Archivos) ---
with st.sidebar:
    st.header("📂 Carga de Datos")
    f_hist = st.file_uploader("1. Sube el Histórico Anual (.xlsx)", type=["xlsx"])
    f_sem = st.file_uploader("2. Sube la Semana Actual (.xlsx)", type=["xlsx"])
    
    st.info("💡 Asegúrate de que los archivos tengan el formato correcto del Club TYM.")

# --- LÓGICA DE PROCESAMIENTO (Funciones V25 Adaptadas) ---
def clean_time(val):
    if pd.isna(val) or val in ['NC', '0', '', 'NAN', '-']: return pd.Timedelta(0)
    s = str(val).strip()
    try:
        if isinstance(val, (datetime.time, datetime.datetime)):
            return pd.Timedelta(hours=val.hour, minutes=val.minute, seconds=val.second)
        parts = list(map(int, s.split(':')))
        if len(parts) == 3: return pd.Timedelta(hours=parts[0], minutes=parts[1], seconds=parts[2])
    except: pass
    return pd.Timedelta(0)

def clean_float(val):
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def fmt_val(val, tipo):
    if val is None: return "-"
    if tipo == 'tiempo':
        if val.total_seconds() == 0: return "-"
        s = int(val.total_seconds())
        if s < 3600: return f"{s//60}m {s%60}s"
        return f"{s//3600}h {(s%3600)//60}m"
    else: return f"{val:.1f}" if val > 0 else "-"

def generar_word_en_memoria(lista_atletas, nombre_semana, team_avg_sem, team_avg_hist):
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(10.5)
    style.paragraph_format.space_after = Pt(2)

    # --- CARÁTULA ---
    h1 = doc.add_heading("🦅 RESUMEN GLOBAL DEL EQUIPO", level=1)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER; h1.runs[0].font.color.rgb = RGBColor(0, 51, 102)
    p = doc.add_paragraph(f"Reporte: {nombre_semana}"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("")

    table = doc.add_table(rows=1, cols=3); table.style = 'Table Grid'
    hdr = table.rows[0].cells; hds = ["MÉTRICA", "PROMEDIO SEMANA", "PROMEDIO ANUAL"]
    for i, txt in enumerate(hds): 
        r=hdr[i].paragraphs[0].add_run(txt); r.bold=True; hdr[i].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER

    keys_cov = ['tot_tiempo', 'tot_dist', 'tot_elev', 'cv', 'nat_tiempo', 'bike_tiempo', 'run_tiempo']
    labels_cov = ['Tiempo Total', 'Distancia Total', 'Desnivel Total', 'Consistencia (CV)', 'Tiempo Natación', 'Tiempo Ciclismo', 'Tiempo Trote']

    for k, lbl in zip(keys_cov, labels_cov):
        tipo = 'tiempo' if 'tiempo' in k or 'ritmo' in k else 'float'
        unit = 'km' if 'dist' in k else ('m' if 'elev' in k else '')
        r = table.add_row().cells
        r[0].text = lbl; r[0].paragraphs[0].runs[0].bold=True
        r[1].text = f"{fmt_val(team_avg_sem.get(k), tipo)} {unit}"; r[1].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
        r[2].text = f"{fmt_val(team_avg_hist.get(k), tipo)} {unit}"; r[2].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER

    doc.add_page_break()

    # --- FICHAS ---
    for s in doc.sections: s.top_margin = Cm(1.27); s.bottom_margin = Cm(1.27); s.left_margin = Cm(1.5); s.right_margin = Cm(1.5)

    for i, d in enumerate(lista_atletas):
        if i > 0: doc.add_page_break()
        h = doc.add_heading(level=1); run = h.add_run(f"🦅 REPORTE 360°: {d['name']}")
        run.font.color.rgb = RGBColor(0, 51, 102); run.font.bold = True; h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph("─" * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER

        m = d['metrics']
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"⏱️ {fmt_val(m['tot_tiempo']['val'], 'tiempo')}  |  📏 {fmt_val(m['tot_dist']['val'], 'float')} km  |  ⛰️ {fmt_val(m['tot_elev']['val'], 'float')} m").bold=True; p.runs[0].font.size=Pt(13)

        p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        val=m['tot_tiempo']['val']; avg=m['tot_tiempo']['avg']; hist=m['tot_tiempo']['hist']
        
        # Vs Equipo
        if val.total_seconds()>0 and avg:
            diff=val-avg; sign="+" if diff.total_seconds()>=0 else "-"
            c=RGBColor(0,100,0) if diff.total_seconds()>=0 else RGBColor(180,0,0)
            p2.add_run(f"👥 Vs Equipo: {sign}{fmt_val(abs(diff),'tiempo')}   ").font.color.rgb=c
        
        # Vs Histórico
        if hist:
            diff=val-hist; sign="+" if diff.total_seconds()>=0 else "-"
            c=RGBColor(0,100,0) if diff.total_seconds()>=0 else RGBColor(180,0,0)
            p2.add_run(f"📅 Vs Promedio Anual: {sign}{fmt_val(abs(diff),'tiempo')}").font.color.rgb=c
        else: p2.add_run("📅 Vs Promedio Anual: 🆕 1er Reg").font.color.rgb=RGBColor(0,0,128)
        
        doc.add_paragraph("").paragraph_format.space_after = Pt(12)

        def tabla_sin_bordes(titulo, keys):
            act = any((m[k]['meta']['tipo']=='tiempo' and m[k]['val'].total_seconds()>0) or (m[k]['meta']['tipo']!='tiempo' and m[k]['val']>0) for k in keys)
            p=doc.add_paragraph(); t=p.add_run(titulo); t.bold=True; t.font.size=Pt(12); t.font.color.rgb=RGBColor(0,51,102)
            if not act: p.add_run(" (Sin actividad)").font.color.rgb=RGBColor(150,150,150); return

            tbl = doc.add_table(rows=1, cols=4)
            hdr = tbl.rows[0].cells; hds=["Métrica","Dato","Vs Equipo","Vs Prom. Anual"]
            for j,txt in enumerate(hds): 
                r=hdr[j].paragraphs[0].add_run(txt); r.bold=True; r.font.color.rgb=RGBColor(100,100,100); hdr[j].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
            
            for k in keys:
                item=m[k]; meta=item['meta']; val=item['val']; avg=item['avg']; h_val=item['hist']
                if (meta['tipo']=='tiempo' and val.total_seconds()==0) or (meta['tipo']!='tiempo' and val==0): continue
                row=tbl.add_row().cells
                row[0].text=meta['label']; row[0].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
                row[1].text=f"{fmt_val(val,meta['tipo'])} {meta.get('unit','')}"; row[1].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER; row[1].paragraphs[0].runs[0].bold=True
                
                pe=row[2].paragraphs[0]; pe.alignment=WD_ALIGN_PARAGRAPH.CENTER
                if avg