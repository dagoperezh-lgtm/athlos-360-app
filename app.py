# ==============================================================================
# 🧠 CLUB TYM V120 - LA SOLUCIÓN DEFINITIVA (LIMPIEZA Y FORMATO)
# ==============================================================================
import pandas as pd
import numpy as np
import os
import re
from datetime import datetime, time
from openpyxl import load_workbook
from openpyxl.styles import NamedStyle

# --- CONFIGURACIÓN DE ARCHIVOS ---
ARCHIVO_HISTORICO = "historico.xlsx"
ARCHIVO_SEMANA    = "semana.xlsx"
# ---------------------------------

print(f"🚀 Iniciando Cerebro V120 (Reinicio Total)...")

# 1. VERIFICACIÓN DE SEGURIDAD
if not os.path.exists(ARCHIVO_HISTORICO):
    raise SystemExit(f"❌ ERROR CRÍTICO: No encuentro '{ARCHIVO_HISTORICO}'. Súbelo a la carpeta.")
if not os.path.exists(ARCHIVO_SEMANA):
    raise SystemExit(f"❌ ERROR CRÍTICO: No encuentro '{ARCHIVO_SEMANA}'. Súbelo a la carpeta.")

# 2. FUNCIONES DE CONVERSIÓN (MATEMÁTICA PURA)
def convertir_a_numero_excel(valor):
    """
    Convierte cualquier cosa (texto '12:00:00', objeto tiempo, etc.) 
    a un número decimal de Excel (ej: 0.5 para mediodía).
    """
    if pd.isna(valor) or valor == '' or str(valor).strip() in ['-', 'nan', 'NC', '0', '00:00:00']: 
        return 0.0
    
    try:
        # Si ya es número, devolverlo tal cual
        if isinstance(valor, (int, float)):
            return float(valor)
        
        # Si es un objeto de tiempo de Python
        if isinstance(valor, (datetime, time)):
            if isinstance(valor, datetime): valor = valor.time()
            segundos = valor.hour*3600 + valor.minute*60 + valor.second
            return segundos / 86400.0
        
        # Si es texto "HH:MM:SS"
        s = str(valor).strip()
        parts = list(map(int, s.split(':')))
        
        segundos = 0
        if len(parts) == 3: # HH:MM:SS
            segundos = parts[0]*3600 + parts[1]*60 + parts[2]
        elif len(parts) == 2: # MM:SS
            segundos = parts[0]*60 + parts[1]
            
        if segundos > 0:
            return segundos / 86400.0
            
    except:
        return 0.0
    return 0.0

def limpiar_numero(val):
    """Limpia textos de números con comas, etc."""
    if pd.isna(val) or str(val).strip() in ['-', 'nan', '']: return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

# 3. MAPA DE TRABAJO (QUE BUSCAR Y COMO TRATARLO)
MAPA = {
    'Tiempo Total':     {'col': 'Tiempo Total (hh:mm:ss)',   'tipo': 'tiempo'},
    'Distancia Total':  {'col': 'Distancia Total (km)',      'tipo': 'num'},
    'Altimetría Total': {'col': 'Altimetría Total (m)',      'tipo': 'num'},
    'Natación':         {'col': 'Nat: Tiempo (hh:mm:ss)',    'tipo': 'tiempo'},
    'Nat Distancia':    {'col': 'Nat: Distancia (km)',       'tipo': 'num'},
    'Nat Ritmo':        {'col': 'Nat: Ritmo (min/100m)',     'tipo': 'tiempo'},
    'Ciclismo':         {'col': 'Ciclismo: Tiempo (hh:mm:ss)','tipo': 'tiempo'},
    'Ciclismo Distancia':{'col': 'Ciclismo: Distancia (km)',  'tipo': 'num'},
    'Ciclismo Desnivel':{'col': 'Ciclismo: KOM/Desnivel (m)','tipo': 'num'},
    'Trote':            {'col': 'Trote: Tiempo (hh:mm:ss)',  'tipo': 'tiempo'},
    'Trote Distancia':  {'col': 'Trote: Distancia (km)',     'tipo': 'num'},
    'Trote Ritmo':      {'col': 'Trote: Ritmo (min/km)',     'tipo': 'tiempo'},
    'CV':               {'col': 'CV (Equilibrio)',           'tipo': 'num'}
}

try:
    # 4. CARGA DE DATOS
    xls = pd.ExcelFile(ARCHIVO_HISTORICO)
    df_semana_raw = pd.read_excel(ARCHIVO_SEMANA)
    # Limpiar nombres de columnas del semanal por si acaso tienen espacios
    df_semana_proc = df_semana_raw.copy()
    df_semana_proc.columns = [str(c).strip() for c in df_semana_proc.columns]

    # 5. DETECTAR SEMANA AUTOMÁTICAMENTE
    hojas_existentes = xls.sheet_names
    numeros = []
    for h in hojas_existentes:
        m = re.search(r'Sem.*?(\d+)', h, re.IGNORECASE)
        if m: numeros.append(int(m.group(1)))
    
    numeros.sort()
    # Ignorar semanas antiguas (ej: 50, 51 del año pasado) para la serie nueva
    serie_actual = [n for n in numeros if n < 40]
    max_sem = max(serie_actual) if serie_actual else 0
    
    nuevo_num = max_sem + 1
    nombre_hoja_nueva = f"Sem {nuevo_num:02d}"
    print(f"🎯 Última semana detectada: {max_sem}. Generando: {nombre_hoja_nueva}")

    # Preparar el archivo de salida
    fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
    nombre_salida = f"HISTORICO_NUEVO_{fecha_str}.xlsx"
    writer = pd.ExcelWriter(nombre_salida, engine='openpyxl')

    hojas_procesadas = []
    
    # 6. PROCESAMIENTO DE CADA HOJA DEL HISTÓRICO
    for hoja in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=hoja)
        df.columns = [str(c).strip() for c in df.columns] 
        
        if hoja in MAPA:
            print(f"  ... Procesando hoja: {hoja}")
            cfg = MAPA[hoja]
            tipo = cfg['tipo']

            # A. INSERTAR COLUMNA NUEVA (Sem XX)
            cols_sem = [c for c in df.columns if re.search(r'Sem.*?(\d+)', c, re.IGNORECASE)]
            col_ancla = None
            if cols_sem:
                # Buscar la última semana válida para insertar después
                for c in reversed(cols_sem):
                    m = re.search(r'(\d+)', c)
                    if m and int(m.group(1)) == max_sem: col_ancla = c; break
                
                if col_ancla: 
                    idx = df.columns.get_loc(col_ancla) + 1
                else: 
                    idx = len(df.columns)
            else:
                idx = df.columns.get_loc("Promedio") if "Promedio" in df.columns else len(df.columns)

            if nombre_hoja_nueva not in df.columns:
                df.insert(idx, nombre_hoja_nueva, 0.0)

            # B. LLENAR DATOS DE LA SEMANA ACTUAL
            col_target = cfg['col']
            # Buscar columna de nombre en semanal
            col_nom = next((c for c in df_semana_proc.columns if str(c).lower() in ['nombre', 'deportista']), None)
            
            if col_nom and col_target in df_semana_proc.columns:
                datos = dict(zip(df_semana_proc[col_nom].astype(str).str.strip().str.lower(), df_semana_proc[col_target]))
                # Buscar columna de nombre en histórico
                col_hist = next((c for c in df.columns if str(c).lower() in ['nombre', 'deportista', 'atleta']), None)
                
                if col_hist:
                    # Estandarizar nombre de columna a 'Nombre' para evitar problemas en la App
                    df.rename(columns={col_hist: 'Nombre'}, inplace=True)
                    
                    for i, row in df.iterrows():
                        n = str(row['Nombre']).strip().lower()
                        raw = datos.get(n, 0)
                        if tipo == 'tiempo': 
                            df.at[i, nombre_hoja_nueva] = convertir_a_numero_excel(raw)
                        else: 
                            df.at[i, nombre_hoja_nueva] = limpiar_numero(raw)

            # C. NORMALIZACIÓN TOTAL (TODO A NÚMEROS)
            # Convertimos TODAS las columnas de semana a float. Esto es vital para la App.
            cols_semanas_todas = [c for c in df.columns if re.search(r'Sem.*?(\d+)', c, re.IGNORECASE)]
            
            if tipo == 'tiempo':
                for col in cols_semanas_todas:
                    df[col] = df[col].apply(convertir_a_numero_excel).astype(float)
            else:
                for col in cols_semanas_todas:
                    df[col] = df[col].apply(limpiar_numero).astype(float)

            # D. RECÁLCULO DE TOTALES Y PROMEDIOS
            for i, row in df.iterrows():
                vals = [row[c] for c in cols_semanas_todas if row
