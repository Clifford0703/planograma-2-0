import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import io
import re
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Planograma 2.0 | Retail Analytics",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- PALETA DESIGN SYSTEM ---
t = {
    "bg_app": "#f8fafc",
    "bg_surface": "#ffffff",
    "bg_card": "#ffffff",
    "border": "#2563eb",
    "border_subtle": "#cbd5e1",
    "text_primary": "#0f172a",
    "text_secondary": "#2563eb",
    "text_muted": "#64748b",
    "accent": "#2563eb",
    "grid_color": "rgba(0, 0, 0, 0.05)",
    "card_shadow": "0 2px 8px rgba(15, 23, 42, 0.05)",
    "card_hover_shadow": "0 8px 18px rgba(15, 23, 42, 0.09)",
}

# INYECCIÓN CSS PROFESIONAL UI/UX
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@700;800&display=swap');
        
        html, body, .stApp, [data-testid="stAppViewContainer"], .main, section.main, [data-testid="stHeader"] {{
            background-color: {t["bg_app"]} !important;
            background: {t["bg_app"]} !important;
            color: {t["text_primary"]} !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }}
        
        header[data-testid="stHeader"] {{
            background-color: transparent !important;
        }}
        
        .block-container {{
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-top: 0.8rem !important;
            padding-bottom: 1.5rem !important;
            max-width: 100% !important;
        }}
        
        /* PESTAÑAS (TABS) */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px !important;
            background-color: #e2e8f0 !important;
            padding: 5px !important;
            border-radius: 10px !important;
            border: 1px solid {t["border_subtle"]} !important;
            margin-bottom: 16px !important;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            height: 42px !important;
            padding: 0 20px !important;
            border-radius: 7px !important;
            font-weight: 800 !important;
            font-size: 0.86rem !important;
            background-color: #f1f5f9 !important;
            border: 1px solid transparent !important;
            opacity: 1 !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }}
        
        .stTabs [data-baseweb="tab"],
        .stTabs [data-baseweb="tab"] *,
        .stTabs [data-baseweb="tab"] p,
        .stTabs [data-baseweb="tab"] span,
        .stTabs [data-baseweb="tab"] div,
        .stTabs [data-baseweb="tab"] [data-testid="stMarkdownContainer"] p {{
            color: {t["text_primary"]} !important;
            -webkit-text-fill-color: {t["text_primary"]} !important;
            font-weight: 800 !important;
        }}
        
        .stTabs [aria-selected="true"],
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background-color: {t["accent"]} !important;
            background: {t["accent"]} !important;
            border-color: {t["accent"]} !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
        }}
        
        .stTabs [aria-selected="true"] *,
        .stTabs [aria-selected="true"] p,
        .stTabs [aria-selected="true"] span,
        .stTabs [aria-selected="true"] div,
        .stTabs [aria-selected="true"] [data-testid="stMarkdownContainer"] p {{
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            font-weight: 900 !important;
        }}

        /* TARJETAS KPIS CON VALORES CENTRADOS */
        .kpi-cards-grid {{
            display: grid;
            gap: 12px;
            margin-bottom: 16px;
        }}
        .grid-5-col {{ grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); }}
        .grid-4-col {{ grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }}

        @media (max-width: 768px) {{
            .grid-5-col, .grid-4-col {{
                grid-template-columns: repeat(3, 1fr) !important;
                gap: 8px !important;
            }}
        }}

        @media (max-width: 480px) {{
            .grid-5-col, .grid-4-col {{
                grid-template-columns: repeat(2, 1fr) !important;
            }}
        }}

        .kpi-card-lux {{
            background: {t["bg_card"]};
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 14px 16px;
            box-shadow: {t["card_shadow"]};
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            text-align: center;
            position: relative;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .kpi-card-lux:hover {{
            transform: translateY(-2px);
            box-shadow: {t["card_hover_shadow"]};
        }}
        .kpi-card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.70rem;
            font-weight: 800;
            color: {t["text_secondary"]};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}
        .kpi-card-value {{
            font-size: 1.95rem;
            font-weight: 900;
            line-height: 1.1;
            margin: 4px 0 6px 0;
            text-align: center;
            font-feature-settings: "tnum";
            letter-spacing: -0.5px;
        }}
        .kpi-card-footer {{
            font-size: 0.74rem;
            font-weight: 600;
            color: {t["text_muted"]};
            text-align: center;
            line-height: 1.3;
        }}

        .dash-card {{
            background: {t["bg_card"]};
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 14px;
            box-shadow: {t["card_shadow"]};
        }}

        .insight-box {{
            border-radius: 8px;
            padding: 14px 18px;
            line-height: 1.45;
            font-size: 0.84rem;
            box-shadow: {t["card_shadow"]};
        }}
    </style>
""", unsafe_allow_html=True)

# --- FUNCIONES AUXILIARES ---
def safe_float(val, default=-999.0):
    if pd.isna(val) or str(val).strip().upper() in ["SIN DATOS", "NAN", "NONE", ""]: return default
    try:
        if isinstance(val, str):
            val = val.replace('%', '').replace(',', '').strip()
        return float(val)
    except (ValueError, TypeError):
        return default

def format_pct(val):
    if val == -999.0: return "SIN DATOS"
    return f"{val*100:.2f}%" if val < 1 else f"{val:.2f}%"

def clean_sku(val):
    if pd.isna(val): return ""
    s = str(val).replace('\xa0', ' ').strip()
    if s.endswith('.0'): 
        s = s[:-2]
    if s.isdigit():
        s = str(int(s))
    return s.strip()

def get_clean_series(df, col_name):
    if col_name not in df.columns:
        return pd.Series([""] * len(df), index=df.index, dtype=str)
    item = df[col_name]
    if isinstance(item, pd.DataFrame):
        item = item.iloc[:, 0]
    return item.astype(str)

def sanitizar_columna_str(df, col, default="SIN DATOS"):
    if col in df.columns:
        s = get_clean_series(df, col).fillna(default).astype(str).str.strip()
        df.drop(columns=[col], inplace=True, errors='ignore')
        df[col] = s
    else:
        df[col] = default

def sanitizar_columna_num(df, col, default=-999.0):
    if col in df.columns:
        s = get_clean_series(df, col).apply(lambda x: safe_float(x, default))
        df.drop(columns=[col], inplace=True, errors='ignore')
        df[col] = s
    else:
        df[col] = default

def desglosar_cuerpo_y_nivel(val):
    s = clean_sku(val)
    if not s:
        return 1, 1
    if "." in s:
        parts = s.split(".")
        c = int(parts[0]) if parts[0].isdigit() else 1
        n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
        return c, n
    if len(s) >= 2 and s.isdigit():
        return int(s[0]), int(s[1])
    if s.isdigit():
        return 1, int(s)
    return 1, 1

def obtener_color_operativo(estado, stock_val):
    estado = str(estado).strip().upper()
    if estado == "B": 
        return "#dc2626", "#991b1b", "#ffffff", "Bloqueado"
    elif estado == "SIN DATOS":
        return "#64748b", "#334155", "#ffffff", "Sin Datos"
    elif estado == "A":
        if stock_val <= 0: 
            return "#ea580c", "#c2410c", "#ffffff", "Sin Stock"
        elif stock_val <= 5: 
            return "#facc15", "#ca8a04", "#0f172a", "Stock Bajo"
        else: 
            return "#16a34a", "#15803d", "#ffffff", "Stock OK"
    else: 
        return "#64748b", "#334155", "#ffffff", "Desconocido"

def convertir_link_directo_drive(url_str):
    if not url_str or pd.isna(url_str):
        return None
    url_str = str(url_str).strip()
    if "drive.google.com" in url_str:
        file_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', url_str)
        if not file_id_match:
            file_id_match = re.search(r'id=([a-zA-Z0-9_-]+)', url_str)
        if file_id_match:
            file_id = file_id_match.group(1)
            return f"https://lh3.googleusercontent.com/d/{file_id}"
    return url_str

# --- CARGA INTEGRADA DE TODAS LAS FUENTES CON CACHÉ ---
@st.cache_data(ttl=14400)
def cargar_todas_las_fuentes():
    try:
        url_planos = "https://docs.google.com/spreadsheets/d/1pbGYgDB8UBZnm0aJZLGOhZwWYq0IlDO8Uqv2n1-MgxI/export?format=xlsx"
        url_coberturas = "https://docs.google.com/spreadsheets/d/1deT1W2MA2kZzm-vJVSp6eL1IsLAKyaYLFCrZYxNU7-c/export?format=xlsx"
        url_ventas = "https://docs.google.com/spreadsheets/d/1NdEQXgbsb5bXbhIs2keFin9Wk5mC4dK7N_Y3dbv6fcg/export?format=xlsx"
        url_barras = "https://docs.google.com/spreadsheets/d/1veTjECI6wlFRqOVg1AKmV0yghxyGR5T0j0Im2AooukM/export?format=xlsx"
        url_jerarquia = "https://docs.google.com/spreadsheets/d/1JI4Ef0138lwI-fJsQmX5lz-fqXvemZQD/export?format=xlsx"
        url_fotos = "https://docs.google.com/spreadsheets/d/1y8P_GVLySBrbGkm-1nc0BiTwGCorhVtF/export?format=xlsx"
        url_cat_imagenes = "https://docs.google.com/spreadsheets/d/1E8B6FIK7XLAp9t-WqWnBU4jL1i3C3EhBmjP0W1_wI38/export?format=xlsx"

        def leer_tabla_por_ancla(url, palabra_ancla, sheet_target=0, skiprows_fallback=0):
            try:
                try:
                    df_raw = pd.read_excel(url, sheet_name=sheet_target, header=None)
                except Exception:
                    df_raw = pd.read_excel(url, sheet_name=0, header=None)
                
                header_idx = skiprows_fallback
                for idx, row in df_raw.head(15).iterrows():
                    row_str = " ".join([str(v).strip().upper() for v in row.values if pd.notna(v)])
                    if palabra_ancla.upper() in row_str:
                        header_idx = idx
                        break
                try:
                    df = pd.read_excel(url, sheet_name=sheet_target, skiprows=header_idx)
                except Exception:
                    df = pd.read_excel(url, sheet_name=0, skiprows=header_idx)
                
                df.columns = [str(c).strip() for c in df.columns]
                df = df.loc[:, ~df.columns.duplicated()].copy()
                return df
            except Exception:
                df = pd.read_excel(url, sheet_name=0, skiprows=skiprows_fallback)
                df.columns = [str(c).strip() for c in df.columns]
                df = df.loc[:, ~df.columns.duplicated()].copy()
                return df

        # 0. Cargar Libro de Imágenes
        mapa_imagenes_dict = {}
        try:
            df_img_sheet = pd.read_excel(url_cat_imagenes, sheet_name=0)
            df_img_sheet.columns = [str(c).strip() for c in df_img_sheet.columns]
            
            col_cat_img = None
            col_url_img = None
            for col in df_img_sheet.columns:
                col_lower = col.lower()
                if "categor" in col_lower:
                    col_cat_img = col
                if any(x in col_lower for x in ["link", "imagen", "url", "foto", "drive"]):
                    col_url_img = col
            
            if col_cat_img and col_url_img:
                for _, row in df_img_sheet.iterrows():
                    c_name = str(row[col_cat_img]).strip().upper()
                    u_link = convertir_link_directo_drive(str(row[col_url_img]).strip())
                    if c_name and u_link:
                        mapa_imagenes_dict[c_name] = u_link
        except Exception:
            pass

        # 1. Matriz de Planos (factPlano)
        df_matriz = leer_tabla_por_ancla(url_planos, "COD REAL", sheet_target=0, skiprows_fallback=3)
        if "COD REAL" not in df_matriz.columns:
            df_matriz = pd.read_excel(url_planos, sheet_name=0, skiprows=2)
            df_matriz.columns = [str(c).strip() for c in df_matriz.columns]
            df_matriz = df_matriz.loc[:, ~df_matriz.columns.duplicated()].copy()

        df_matriz['COD_REAL_Str'] = get_clean_series(df_matriz, 'COD REAL').apply(clean_sku)
        df_matriz['COD REAL'] = df_matriz['COD_REAL_Str']

        if 'PASILLO' not in df_matriz.columns:
            df_matriz['PASILLO'] = "6"
        else:
            df_matriz['PASILLO'] = get_clean_series(df_matriz, 'PASILLO').apply(clean_sku)

        if 'LATERAL' in df_matriz.columns:
            df_matriz['LATERAL'] = get_clean_series(df_matriz, 'LATERAL').str.extract(r'([ABab])')[0].str.upper().fillna('A')
        else:
            df_matriz['LATERAL'] = "A"

        # 2. Coberturas y Stock
        df_cob_raw = leer_tabla_por_ancla(url_coberturas, "Material", sheet_target=0, skiprows_fallback=3)
        df_cob = pd.DataFrame()
        if "Material" in df_cob_raw.columns:
            df_cob['Material_Str'] = get_clean_series(df_cob_raw, 'Material').apply(clean_sku)
            cols_map = {str(c).strip().lower(): c for c in df_cob_raw.columns}
            col_est = cols_map.get('estado material', cols_map.get('estado', None))
            col_stk = cols_map.get('stock actual', cols_map.get('stock', None))
            
            col_cob = None
            for k, original_name in cols_map.items():
                if 'cob' in k and ('días' in k or 'dia' in k or 'día' in k):
                    col_cob = original_name
                    break

            if col_est:
                est_series = get_clean_series(df_cob_raw, col_est)
                df_cob['Estado'] = est_series.str.extract(r'([ABab])')[0].str.upper().fillna('A')
            else:
                df_cob['Estado'] = 'A'

            df_cob['Stock'] = get_clean_series(df_cob_raw, col_stk).apply(safe_float) if col_stk else -999.0
            df_cob['Cobertura'] = get_clean_series(df_cob_raw, col_cob).apply(safe_float) if col_cob else -999.0
            df_cob = df_cob[df_cob['Material_Str'] != ""].drop_duplicates(subset=['Material_Str'])

        # 3. Ventas y Margen
        df_vta_raw = leer_tabla_por_ancla(url_ventas, "Material", sheet_target=0, skiprows_fallback=2)
        df_vta = pd.DataFrame()
        col_mat_vta = 'Material' if 'Material' in df_vta_raw.columns else ('COD REAL' if 'COD REAL' in df_vta_raw.columns else None)
        if col_mat_vta:
            mat_vta_series = get_clean_series(df_vta_raw, col_mat_vta).apply(clean_sku)
            df_vta['Material_Str'] = mat_vta_series
            df_vta = df_vta[~df_vta['Material_Str'].str.contains('-', na=False)].copy()

            col_v = 'Monto Venta Neta' if 'Monto Venta Neta' in df_vta_raw.columns else 'Venta'
            col_m = 'Monto Margen' if 'Monto Margen' in df_vta_raw.columns else 'Margen'
            col_p = '% PART' if '% PART' in df_vta_raw.columns else '% Part'
            
            df_vta['Venta'] = get_clean_series(df_vta_raw, col_v).apply(safe_float) if col_v in df_vta_raw.columns else -999.0
            df_vta['Monto Margen'] = get_clean_series(df_vta_raw, col_m).apply(safe_float) if col_m in df_vta_raw.columns else -999.0
            df_vta['% Part'] = get_clean_series(df_vta_raw, col_p).apply(safe_float) if col_p in df_vta_raw.columns else -999.0
            df_vta = df_vta[df_vta['Material_Str'] != ""].drop_duplicates(subset=['Material_Str'])

        # 4. Código de Barras
        df_bar_raw = leer_tabla_por_ancla(url_barras, "Material", sheet_target=0, skiprows_fallback=2)
        df_bar = pd.DataFrame()
        col_mat_bar = 'Material' if 'Material' in df_bar_raw.columns else ('COD REAL' if 'COD REAL' in df_bar_raw.columns else None)
        if col_mat_bar:
            df_bar['Material_Str'] = get_clean_series(df_bar_raw, col_mat_bar).apply(clean_sku)
            df_bar['EAN_Master'] = get_clean_series(df_bar_raw, 'Código EAN/UPC').apply(clean_sku) if 'Código EAN/UPC' in df_bar_raw.columns else ""
            df_bar['Descripción'] = get_clean_series(df_bar_raw, 'Texto breve de material').str.strip() if 'Texto breve de material' in df_bar_raw.columns else "SIN DATOS"
            
            bar_map = {str(c).strip().lower(): c for c in df_bar_raw.columns}
            col_ga_orig = bar_map.get('grupo de a', bar_map.get('grupo de artículo', None))
            df_bar['G.A.'] = get_clean_series(df_bar_raw, col_ga_orig).apply(clean_sku) if col_ga_orig else 'SIN DATOS'
            df_bar = df_bar[df_bar['Material_Str'] != ""].drop_duplicates(subset=['Material_Str'])

        # 5. Links de Fotos
        df_fotos_raw = leer_tabla_por_ancla(url_fotos, "SKUReferenceCode", sheet_target=0, skiprows_fallback=0)
        df_fotos = pd.DataFrame()
        if not df_fotos_raw.empty:
            fotos_map = {str(c).strip().lower(): c for c in df_fotos_raw.columns}
            col_sku_foto = fotos_map.get('_skureferencecode', fotos_map.get('skureferencecode', None))
            col_link_foto = fotos_map.get('links de fotos', fotos_map.get('link', None))
            if col_sku_foto and col_link_foto:
                df_fotos['Sku_Foto_Str'] = get_clean_series(df_fotos_raw, col_sku_foto).apply(clean_sku)
                df_fotos['Links de fotos'] = get_clean_series(df_fotos_raw, col_link_foto).str.strip()
                df_fotos = df_fotos[df_fotos['Sku_Foto_Str'] != ""].drop_duplicates(subset=['Sku_Foto_Str'])

        # 6. Jerarquía Comercial SAP
        try:
            df_sap_raw = pd.read_excel(url_jerarquia, sheet_name='NuevaJqGA', skiprows=2)
        except Exception:
            try:
                df_sap_raw = pd.read_excel(url_jerarquia, sheet_name=0, skiprows=2)
            except Exception:
                df_sap_raw = pd.DataFrame()
                
        df_sap_raw = df_sap_raw.loc[:, ~df_sap_raw.columns.duplicated()].copy()
        df_sap = pd.DataFrame()
        
        if not df_sap_raw.empty:
            cols_sap_map = {str(c).strip().upper(): c for c in df_sap_raw.columns}
            col_ga_sap = cols_sap_map.get('GRUPO ARTÍCULO', cols_sap_map.get('GRUPO ARTICULO', cols_sap_map.get('COD GA', None)))
            if not col_ga_sap and len(df_sap_raw.columns) >= 11:
                col_ga_sap = df_sap_raw.columns[10]

            col_sec_sap = None
            for col_cand in df_sap_raw.columns:
                c_clean = str(col_cand).strip().upper()
                if 'SECCIÓN' in c_clean or 'SECCION' in c_clean:
                    col_sec_sap = col_cand
                    break
            if not col_sec_sap and len(df_sap_raw.columns) >= 6:
                col_sec_sap = df_sap_raw.columns[5]

            col_cat_sap = cols_sap_map.get('CATEGORÍA', cols_sap_map.get('CATEGORIA', None))
            if not col_cat_sap and len(df_sap_raw.columns) >= 8:
                col_cat_sap = df_sap_raw.columns[7]

            col_dep_sap = cols_sap_map.get('DEPARTAMENTO', None)
            if not col_dep_sap and len(df_sap_raw.columns) >= 4:
                col_dep_sap = df_sap_raw.columns[3]

            col_nomga_sap = df_sap_raw.columns[13] if len(df_sap_raw.columns) > 13 else col_ga_sap

            if col_ga_sap:
                df_sap['CodGA_Str'] = get_clean_series(df_sap_raw, col_ga_sap).apply(clean_sku)
                df_sap['Mundo'] = get_clean_series(df_sap_raw, col_sec_sap).fillna('SIN DATOS').str.strip().str.upper() if col_sec_sap else 'SIN DATOS'
                df_sap['Sección'] = df_sap['Mundo']
                df_sap['Categoría'] = get_clean_series(df_sap_raw, col_cat_sap).fillna('SIN DATOS').str.strip() if col_cat_sap else 'SIN DATOS'
                df_sap['Departamento'] = get_clean_series(df_sap_raw, col_dep_sap).fillna('SIN DATOS').str.strip() if col_dep_sap else 'SIN DATOS'
                df_sap['Grupo de Artículo'] = get_clean_series(df_sap_raw, col_nomga_sap).fillna('SIN DATOS').str.strip() if col_nomga_sap else 'SIN DATOS'
                df_sap = df_sap[df_sap['CodGA_Str'] != ""].drop_duplicates(subset=['CodGA_Str'])

        # Cruce en df_pasillo_base
        df_pasillo_base = df_matriz.copy()
        
        if not df_cob.empty:
            df_pasillo_base.drop(columns=[c for c in ['Estado', 'Stock', 'Cobertura'] if c in df_pasillo_base.columns], inplace=True, errors='ignore')
            df_pasillo_base = df_pasillo_base.merge(df_cob[['Material_Str', 'Estado', 'Stock', 'Cobertura']], left_on='COD_REAL_Str', right_on='Material_Str', how='left')
            df_pasillo_base.drop(columns=['Material_Str'], inplace=True, errors='ignore')

        if not df_vta.empty:
            df_pasillo_base.drop(columns=[c for c in ['Venta', 'Monto Margen', '% Part'] if c in df_pasillo_base.columns], inplace=True, errors='ignore')
            df_pasillo_base = df_pasillo_base.merge(df_vta[['Material_Str', 'Venta', 'Monto Margen', '% Part']], left_on='COD_REAL_Str', right_on='Material_Str', how='left')
            df_pasillo_base.drop(columns=['Material_Str'], inplace=True, errors='ignore')

        if not df_bar.empty:
            df_pasillo_base.drop(columns=[c for c in ['EAN_Master', 'G.A.'] if c in df_pasillo_base.columns], inplace=True, errors='ignore')
            df_pasillo_base = df_pasillo_base.merge(df_bar[['Material_Str', 'EAN_Master', 'G.A.']], left_on='COD_REAL_Str', right_on='Material_Str', how='left')
            if 'EAN' not in df_pasillo_base.columns:
                df_pasillo_base.rename(columns={'EAN_Master': 'EAN'}, inplace=True)
            else:
                df_pasillo_base.drop(columns=['EAN_Master'], inplace=True, errors='ignore')
            df_pasillo_base.drop(columns=['Material_Str'], inplace=True, errors='ignore')

        if not df_fotos.empty:
            df_pasillo_base.drop(columns=[c for c in ['Links de fotos'] if c in df_pasillo_base.columns], inplace=True, errors='ignore')
            df_pasillo_base = df_pasillo_base.merge(df_fotos[['Sku_Foto_Str', 'Links de fotos']], left_on='COD_REAL_Str', right_on='Sku_Foto_Str', how='left')
            df_pasillo_base.drop(columns=['Sku_Foto_Str'], inplace=True, errors='ignore')

        if 'G.A.' in df_pasillo_base.columns:
            df_pasillo_base['G.A._Str'] = get_clean_series(df_pasillo_base, 'G.A.').apply(clean_sku)
        else:
            df_pasillo_base['G.A._Str'] = ""

        if not df_sap.empty:
            df_pasillo_base = df_pasillo_base.merge(
                df_sap[['CodGA_Str', 'Mundo', 'Departamento', 'Sección', 'Categoría', 'Grupo de Artículo']], 
                left_on='G.A._Str', 
                right_on='CodGA_Str', 
                how='left',
                suffixes=('', '_sap')
            )
            for col_target in ['Mundo', 'Departamento', 'Sección', 'Categoría', 'Grupo de Artículo']:
                col_sap_name = f"{col_target}_sap"
                if col_sap_name in df_pasillo_base.columns:
                    target_s = get_clean_series(df_pasillo_base, col_target)
                    sap_s = get_clean_series(df_pasillo_base, col_sap_name)
                    df_pasillo_base[col_target] = sap_s.replace(['SIN DATOS', 'nan', 'None', '', 'NaN'], pd.NA).fillna(target_s)
                    df_pasillo_base.drop(columns=[col_sap_name], inplace=True, errors='ignore')

            df_pasillo_base.drop(columns=['CodGA_Str', 'G.A._Str'], inplace=True, errors='ignore')

        for col, val_def in [('Stock', -999.0), ('Cobertura', -999.0), ('Venta', -999.0), ('Monto Margen', -999.0), ('% Part', -999.0)]:
            sanitizar_columna_num(df_pasillo_base, col, val_def)

        for col, val_def in [('Mundo', 'DESAYUNO'), ('Estado', 'SIN DATOS'), ('Departamento', 'SIN DATOS'), ('Sección', 'SIN DATOS'), ('Categoría', 'SIN DATOS'), ('Grupo de Artículo', 'SIN DATOS'), ('G.A.', 'SIN DATOS'), ('Links de fotos', 'SIN DATOS'), ('Descripción', 'SIN DATOS'), ('EAN', 'SIN DATOS'), ('PASILLO', '6'), ('LATERAL', 'A')]:
            sanitizar_columna_str(df_pasillo_base, col, val_def)

        if 'Bandeja' in df_pasillo_base.columns and 'EAN' in df_pasillo_base.columns:
            df_pasillo_base = df_pasillo_base.dropna(subset=["Bandeja", "EAN"], how="all")

        # Construcción de df_sku_unico
        if not df_vta.empty:
            mat_vta_base = df_vta[['Material_Str']].drop_duplicates().rename(columns={'Material_Str': 'Material_Unico'})
        else:
            mat_vta_base = pd.DataFrame(columns=['Material_Unico'])

        mat_plano_base = df_matriz[['COD_REAL_Str']].drop_duplicates().rename(columns={'COD_REAL_Str': 'Material_Unico'})
        df_catalogo_base = pd.concat([mat_vta_base, mat_plano_base]).drop_duplicates(subset=['Material_Unico'])
        df_catalogo_base = df_catalogo_base[df_catalogo_base['Material_Unico'] != ""].copy()

        def formatear_bandeja_limpia(val):
            c, n = desglosar_cuerpo_y_nivel(val)
            return f"C{c} (N{n})"

        df_matriz['Ubicacion_Fmt'] = get_clean_series(df_matriz, 'Bandeja').apply(formatear_bandeja_limpia)
        mapa_ubicaciones = df_matriz.groupby('COD_REAL_Str')['Ubicacion_Fmt'].apply(
            lambda x: ", ".join(sorted(list(set(x.dropna()))))
        ).to_dict()

        df_sku_unico = df_catalogo_base.copy()
        df_sku_unico['COD REAL'] = df_sku_unico['Material_Unico']

        if not df_bar.empty:
            df_sku_unico = df_sku_unico.merge(df_bar[['Material_Str', 'Descripción', 'EAN_Master', 'G.A.']], left_on='Material_Unico', right_on='Material_Str', how='left')
            df_sku_unico.rename(columns={'EAN_Master': 'EAN'}, inplace=True)
            df_sku_unico.drop(columns=['Material_Str'], inplace=True, errors='ignore')

        if not df_vta.empty:
            df_sku_unico = df_sku_unico.merge(df_vta[['Material_Str', 'Venta', 'Monto Margen']], left_on='Material_Unico', right_on='Material_Str', how='left')
            df_sku_unico.drop(columns=['Material_Str'], inplace=True, errors='ignore')

        if not df_cob.empty:
            df_sku_unico = df_sku_unico.merge(df_cob[['Material_Str', 'Estado', 'Stock', 'Cobertura']], left_on='Material_Unico', right_on='Material_Str', how='left')
            df_sku_unico.drop(columns=['Material_Str'], inplace=True, errors='ignore')

        if 'G.A.' in df_sku_unico.columns:
            df_sku_unico['G.A._Str'] = get_clean_series(df_sku_unico, 'G.A.').apply(clean_sku)
        else:
            df_sku_unico['G.A._Str'] = ""

        if not df_sap.empty:
            df_sku_unico = df_sku_unico.merge(
                df_sap[['CodGA_Str', 'Mundo', 'Departamento', 'Sección', 'Categoría', 'Grupo de Artículo']], 
                left_on='G.A._Str', 
                right_on='CodGA_Str', 
                how='left',
                suffixes=('', '_sap')
            )
            for col_target in ['Mundo', 'Departamento', 'Sección', 'Categoría', 'Grupo de Artículo']:
                col_sap_name = f"{col_target}_sap"
                if col_sap_name in df_sku_unico.columns:
                    target_s = get_clean_series(df_sku_unico, col_target)
                    sap_s = get_clean_series(df_sku_unico, col_sap_name)
                    df_sku_unico[col_target] = sap_s.replace(['SIN DATOS', 'nan', 'None', '', 'NaN'], pd.NA).fillna(target_s)
                    df_sku_unico.drop(columns=[col_sap_name], inplace=True, errors='ignore')
            df_sku_unico.drop(columns=['CodGA_Str', 'G.A._Str'], inplace=True, errors='ignore')

        df_sku_unico['Ubicación(es)'] = df_sku_unico['Material_Unico'].map(mapa_ubicaciones)

        for col, val_def in [('Stock', -999.0), ('Cobertura', -999.0), ('Venta', -999.0), ('Monto Margen', -999.0)]:
            sanitizar_columna_num(df_sku_unico, col, val_def)

        for col, val_def in [('Mundo', 'DESAYUNO'), ('Estado', 'SIN DATOS'), ('Descripción', 'SIN DATOS'), ('EAN', 'SIN DATOS'), ('Departamento', 'SIN DATOS'), ('Sección', 'SIN DATOS'), ('Categoría', 'SIN DATOS'), ('Grupo de Artículo', 'SIN DATOS'), ('Ubicación(es)', pd.NA)]:
            sanitizar_columna_str(df_sku_unico, col, val_def)

        hora_lectura = pd.Timestamp.now('America/Lima').strftime("%d/%m/%Y - %I:%M %p")
        return df_pasillo_base, df_sku_unico, mapa_imagenes_dict, hora_lectura, None
    except Exception as e:
        return None, None, {}, None, str(e)

# --- HEADER Y CONTROL DE ACTUALIZACIÓN ---
with st.spinner("Sincronizando fuentes externas en la nube..."):
    df_pasillo_global, df_sku_unico_global, mapa_imagenes_online, info_hora, error_nube = cargar_todas_las_fuentes()

col_head1, col_head2, col_head3 = st.columns([6.2, 1.8, 2.0])
with col_head1:
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="font-size: 1.5rem; font-weight: 900; letter-spacing: -0.5px; color: {t['text_primary']};">
                🏪 Planograma <span style="color: {t['accent']}; font-weight: 800;">2.0</span>
            </div>
            <span style="background: {t['accent']}1a; color: {t['accent']}; font-size: 0.65rem; font-weight: 800; padding: 2px 8px; border-radius: 12px; border: 1px solid {t['accent']}33;">CENCOSUD PERÚ</span>
        </div>
    """, unsafe_allow_html=True)

with col_head2:
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col_head3:
    st.markdown(f"""
        <div style="text-align: right; line-height: 1.3;">
            <div style="font-size: 0.78rem; font-weight: 800; color: {t['text_primary']};">Desarrollado por <b>Alfredo H.M.</b></div>
            <div style="font-size: 0.68rem; color: {t['text_muted']};">{info_hora if info_hora else 'En línea'}</div>
        </div>
    """, unsafe_allow_html=True)

if error_nube:
    st.warning(f"⚠️ Aviso de conexión a la nube: {error_nube}")

# --- COMPUERTA DE BÚSQUEDA INTELIGENTE CON LATERAL (A / B) ---
if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False

st.markdown("""
    <div style="background: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
        <div style="font-size: 0.85rem; font-weight: 800; color: #1e3a8a; text-transform: uppercase; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            🏬 Filtros de Búsqueda de Planogramas
        </div>
""", unsafe_allow_html=True)

col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns([2.2, 2.2, 3.0, 1.8, 1.3])

with col_b1:
    tiendas_lista = ["S003 Metro Aramburú", "S008 Metro Schell", "S001 Metro Miraflores", "S004 Wong Benavides", "Todas las Tiendas"]
    tienda_sel = st.selectbox("Tienda", tiendas_lista, index=0, key="gate_tienda")

if df_pasillo_global is not None and not df_pasillo_global.empty and 'Mundo' in df_pasillo_global.columns:
    mundos_disponibles = sorted([m for m in df_pasillo_global['Mundo'].dropna().unique() if str(m).strip() not in ['SIN DATOS', 'S/D', 'nan', '']])
    if not mundos_disponibles:
        mundos_disponibles = ["DESAYUNO"]
else:
    mundos_disponibles = ["DESAYUNO"]

with col_b2:
    mundo_sel = st.selectbox("Mundo (Sección SAP)", mundos_disponibles, key="gate_mundo")

if df_pasillo_global is not None and not df_pasillo_global.empty:
    df_filtrado_mundo = df_pasillo_global[df_pasillo_global['Mundo'] == mundo_sel]
    cats_encontradas = sorted([c for c in df_filtrado_mundo['Categoría'].dropna().unique() if str(c) not in ['SIN DATOS', 'S/C', 'nan', '']])
    if not cats_encontradas:
        cats_encontradas = sorted([c for c in df_pasillo_global['Categoría'].dropna().unique() if str(c) not in ['SIN DATOS', 'S/C', 'nan', '']])
else:
    cats_encontradas = [
        "CAFÉ Y COMPLEMENTOS",
        "MODIFICADORES DE LECHES / COMPLEMENTOS / SUPLEMENTOS", 
        "TÉ E INFUSIONES", 
        "PANES Y TOSTADAS", 
        "MIELES / JALEAS / SIROPE"
    ]

with col_b3:
    cat_sel = st.selectbox("Categoría", ["Todas las Categorías"] + cats_encontradas, key="gate_cat")

with col_b4:
    lateral_display_map = {"A": "Lateral A", "B": "Lateral B"}
    reverse_lateral_map = {"Lateral A": "A", "Lateral B": "B"}
    
    if cat_sel != "Todas las Categorías":
        df_cat_check = df_pasillo_global[(df_pasillo_global['Mundo'] == mundo_sel) & (df_pasillo_global['Categoría'] == cat_sel)]
        lats_detectados = [str(x).strip().upper() for x in df_cat_check['LATERAL'].dropna().unique() if str(x).strip().upper() in ['A', 'B']]
        letra_detectada = lats_detectados[0] if len(lats_detectados) > 0 else 'A'
        label_auto = lateral_display_map.get(letra_detectada, "Lateral A")
        lateral_sel_label = st.selectbox("Lateral (Auto)", [label_auto], disabled=True, key="gate_lat_auto")
        lat_letra_activa = reverse_lateral_map.get(lateral_sel_label, "A")
    else:
        lateral_sel_label = st.selectbox("Lateral (Obligatorio)", ["Lateral A", "Lateral B"], index=0, key="gate_lat_manual")
        lat_letra_activa = reverse_lateral_map.get(lateral_sel_label, "A")

with col_b5:
    st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
    if st.button("🔍 Buscar", use_container_width=True, type="primary"):
        st.session_state.busqueda_activa = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# --- EVALUACIÓN DE LA COMPUERTA ---
if not st.session_state.busqueda_activa:
    st.info("👆 **Seleccione la Tienda, Mundo, Categoría y Lateral, y haga clic en 'Buscar' (🔍) para consultar el planograma y sus indicadores.**")
else:
    df_base = df_pasillo_global.copy()
    
    if 'Mundo' in df_base.columns:
        df_base = df_base[df_base['Mundo'] == mundo_sel].copy()

    if cat_sel != "Todas las Categorías":
        df_base = df_base[df_base['Categoría'] == cat_sel].copy()
    
    if 'LATERAL' in df_base.columns:
        df_filtrado_lat = df_base[df_base['LATERAL'].astype(str).str.strip().str.upper() == lat_letra_activa].copy()
        if not df_filtrado_lat.empty:
            df_base = df_filtrado_lat
        else:
            st.warning(f"⚠️ Aviso: No se encontraron registros con Lateral '{lat_letra_activa}'. Mostrando registros disponibles.")

    df_base['Venta_Num'] = df_base['Venta'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0))
    df_base['Margen_Num'] = df_base['Monto Margen'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0))
    df_base['Part_Num'] = df_base['% Part'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0))
    df_base['Stock_Num'] = df_base['Stock'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0))
    df_base['Cob_Num'] = df_base['Cobertura'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0))
    df_base['Caras_Num'] = df_base['Caras'].apply(lambda x: safe_float(x, default=1.0))

    df_unicos = df_base.drop_duplicates(subset=['COD REAL']).copy()
    df_unicos = df_unicos[df_unicos['COD REAL'].astype(str).str.strip() != ""]

    tab_resumen, tab_plano, tab_dash, tab_errores = st.tabs([
        "📊 Resumen Ejecutivo",
        "📐 Planograma Físico Panorámico", 
        "📈 Dashboard Analítico Financiero", 
        "⚠️ Errores y Desajustes de Cruce"
    ])

    # =========================================================================
    # --- PESTAÑA 1: RESUMEN EJECUTIVO (GERENCIA DE OPERACIONES CON VELOCÍMETRO) ---
    # =========================================================================
    with tab_resumen:
        st.markdown(f"""
            <div style="margin-bottom: 14px;">
                <h3 style="font-size: 1.45rem; font-weight: 900; color: #0f172a; margin: 0 0 4px 0; letter-spacing: -0.3px;">
                    Control de Gestión Operativa en Góndola (Lateral {lat_letra_activa})
                </h3>
                <p style="font-size: 0.82rem; font-weight: 500; color: #64748b; margin: 0;">
                    Disponibilidad en góndola (OSA), impacto financiero de quiebres y cumplimiento de catálogo activo.
                </p>
            </div>
        """, unsafe_allow_html=True)

        tot_skus_plano = df_unicos['COD REAL'].nunique()
        quiebres_df = df_unicos[(df_unicos['Estado'].str.strip().str.upper() == 'A') & (df_unicos['Stock_Num'] <= 0)]
        tot_quiebres = quiebres_df['COD REAL'].nunique()
        pct_quiebres = (tot_quiebres / tot_skus_plano * 100) if tot_skus_plano > 0 else 0
        osa_pct = 100.0 - pct_quiebres
        bloqueados_df = df_unicos[df_unicos['Estado'].str.strip().str.upper() == 'B']
        tot_bloqueados = bloqueados_df['COD REAL'].nunique()
        
        ventas_tot_plano = df_unicos['Venta_Num'].sum()
        margen_tot_plano = df_unicos['Margen_Num'].sum()
        margen_pct_plano = (margen_tot_plano / ventas_tot_plano * 100) if ventas_tot_plano > 0 else 0
        venta_en_riesgo = quiebres_df['Venta_Num'].sum()
        
        df_no_plano = df_sku_unico_global[
            df_sku_unico_global['Ubicación(es)'].isna() | 
            (get_clean_series(df_sku_unico_global, 'Ubicación(es)').str.strip() == "") | 
            (get_clean_series(df_sku_unico_global, 'Ubicación(es)').str.strip() == "SIN DATOS")
        ].copy()
        tot_no_plano = df_no_plano['COD REAL'].nunique()
        ventas_no_plano = df_no_plano['Venta'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0)).sum()

        st.markdown(f"""
            <div class="kpi-cards-grid grid-5-col">
                <div class="kpi-card-lux" style="border-bottom: 4px solid #10b981;">
                    <div class="kpi-card-header"><span>NIVEL DE SERVICIO EN GÓNDOLA</span><span>🎯</span></div>
                    <div class="kpi-card-value" style="color: {'#10b981' if osa_pct >= 95 else ('#ea580c' if osa_pct >= 90 else '#dc2626')};">{osa_pct:.1f}%</div>
                    <div class="kpi-card-footer">OSA (On-Shelf Availability) meta &gt; 95%</div>
                </div>
                <div class="kpi-card-lux" style="border-bottom: 4px solid #dc2626;">
                    <div class="kpi-card-header"><span>QUIEBRES DE STOCK (0)</span><span>🚨</span></div>
                    <div class="kpi-card-value" style="color: #dc2626;">{tot_quiebres}</div>
                    <div class="kpi-card-footer"><b>{pct_quiebres:.1f}%</b> del surtido activo quebrado</div>
                </div>
                <div class="kpi-card-lux" style="border-bottom: 4px solid #64748b;">
                    <div class="kpi-card-header"><span>SKUS BLOQUEADOS (B)</span><span>🚫</span></div>
                    <div class="kpi-card-value" style="color: #64748b;">{tot_bloqueados}</div>
                    <div class="kpi-card-footer">Espacio ocioso a retirar del plano</div>
                </div>
                <div class="kpi-card-lux" style="border-bottom: 4px solid #ea580c;">
                    <div class="kpi-card-header"><span>VENTA SIN PLANOGRAMA</span><span>📦</span></div>
                    <div class="kpi-card-value" style="color: #ea580c;">{tot_no_plano}</div>
                    <div class="kpi-card-footer">SKUs huérfanos con venta activa</div>
                </div>
                <div class="kpi-card-lux" style="border-bottom: 4px solid #2563eb;">
                    <div class="kpi-card-header"><span>VENTA TOTAL EN PLANO</span><span>💳</span></div>
                    <div class="kpi-card-value" style="color: #2563eb;">S/ {ventas_tot_plano/1000:,.1f}K</div>
                    <div class="kpi-card-footer">Margen Bruto: <b>{margen_pct_plano:.1f}%</b> (S/ {margen_tot_plano/1000:,.1f}K)</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        c_a1, c_a2, c_a3 = st.columns([4.5, 4.5, 1.2])
        with c_a1:
            st.markdown(f"""
                <div class="insight-box" style="background-color: #fee2e2; border-left: 4px solid #dc2626; color: #991b1b;">
                    <b>🚨 Venta en Riesgo por Quiebres: S/ {venta_en_riesgo:,.2f}</b><br>
                    Los <b>{tot_quiebres} productos con Stock 0</b> en piso acumulan ventas activas y frenan la rotación.
                </div>
            """, unsafe_allow_html=True)
        with c_a2:
            st.markdown(f"""
                <div class="insight-box" style="background-color: #ffedd5; border-left: 4px solid #ea580c; color: #9a3412;">
                    <b>⚠️ Venta Huérfana (Sin Planograma): S/ {ventas_no_plano:,.2f}</b><br>
                    Existen <b>{tot_no_plano} SKUs con ventas</b> sin espacio físico estandarizado en el planograma.
                </div>
            """, unsafe_allow_html=True)
        with c_a3:
            buf_quiebres = io.BytesIO()
            cols_q_export = [c for c in ['COD REAL', 'EAN', 'Descripción', 'Marca', 'Categoría', 'Ubicación(es)', 'Estado', 'Stock', 'Cobertura', 'Venta'] if c in quiebres_df.columns]
            with pd.ExcelWriter(buf_quiebres, engine='openpyxl') as writer:
                quiebres_df[cols_q_export].to_excel(writer, index=False, sheet_name='Quiebres')
            st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
            st.download_button(
                "📥 Exportar", 
                buf_quiebres.getvalue(), 
                "quiebres_stock0.xlsx", 
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                use_container_width=True,
                help="Descargar listado de productos con Quiebre de Stock (0)"
            )
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # --- FILA SUPERIOR: VELOCÍMETRO GERENCIAL (ACTIVOS EN PLANO VS ACTIVOS EN COBERTURAS) ---
        col_gauge, col_pie = st.columns([5.5, 4.5])
        with col_gauge:
            col_g_title, col_g_btn = st.columns([5.8, 4.2])
            with col_g_title:
                st.markdown("<b>⏱️ Cumplimiento de Catálogo Activo en Góndola</b>", unsafe_allow_html=True)
            with col_g_btn:
                modo_gauge = st.segmented_control(
                    "Filtro Coberturas:",
                    ["Todos", "Con Stock"],
                    default="Todos",
                    label_visibility="collapsed",
                    key="switch_gauge_ops"
                )

            # 1. Universo de Coberturas de Referencia (Catálogo Comercial Activo 'A')
            df_universo_cob = df_sku_unico_global.copy()
            if 'Mundo' in df_universo_cob.columns:
                df_universo_cob = df_universo_cob[df_universo_cob['Mundo'] == mundo_sel].copy()

            if cat_sel != "Todas las Categorías":
                df_universo_cob = df_universo_cob[df_universo_cob['Categoría'] == cat_sel].copy()
            else:
                cats_en_este_lateral = [c for c in df_base['Categoría'].dropna().unique() if str(c) not in ['SIN DATOS', 'S/C', 'nan', '']]
                if cats_en_este_lateral:
                    df_universo_cob = df_universo_cob[df_universo_cob['Categoría'].isin(cats_en_este_lateral)].copy()

            df_cob_activos_base = df_universo_cob[df_universo_cob['Estado'].astype(str).str.strip().str.upper() == 'A'].copy()
            df_plano_activos_base = df_unicos[df_unicos['Estado'].astype(str).str.strip().str.upper() == 'A'].copy()
            skus_bloqueados_plano = df_unicos[df_unicos['Estado'].astype(str).str.strip().str.upper() == 'B']['COD REAL'].nunique()

            if modo_gauge == "Con Stock":
                numerador_gauge = df_plano_activos_base[df_plano_activos_base['Stock_Num'] > 0]['COD REAL'].nunique()
                denominador_gauge = df_cob_activos_base[df_cob_activos_base['Stock'] > 0]['COD REAL'].nunique()
                label_modo_gauge = "Activos con Stock (>0)"
                bar_color_gauge = "#16a34a"
            else:
                numerador_gauge = df_plano_activos_base['COD REAL'].nunique()
                denominador_gauge = df_cob_activos_base['COD REAL'].nunique()
                label_modo_gauge = "Todos los Activos (con o sin stock)"
                bar_color_gauge = "#2563eb"

            denominador_calc = denominador_gauge if denominador_gauge > 0 else max(numerador_gauge, 1)
            pct_gauge = min(100.0, (numerador_gauge / denominador_calc * 100)) if denominador_calc > 0 else 0.0

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pct_gauge,
                number={'suffix': "%", 'font': {'size': 38, 'weight': 900, 'color': '#0f172a'}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#64748b"},
                    'bar': {'color': bar_color_gauge, 'thickness': 0.3},
                    'bgcolor': "#ffffff",
                    'borderwidth': 1.5,
                    'bordercolor': "#cbd5e1",
                    'steps': [
                        {'range': [0, 75], 'color': 'rgba(239, 68, 68, 0.15)'},
                        {'range': [75, 90], 'color': 'rgba(234, 179, 8, 0.18)'},
                        {'range': [90, 100], 'color': 'rgba(34, 197, 94, 0.20)'}
                    ],
                    'threshold': {
                        'line': {'color': "#0f172a", 'width': 4},
                        'thickness': 0.75,
                        'value': pct_gauge
                    }
                }
            ))
            fig_gauge.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=15, b=10, l=20, r=20),
                height=250
            )

            st.markdown('<div class="dash-card">', unsafe_allow_html=True)
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
            st.markdown(f"""
                <div style="text-align: center; font-size: 0.82rem; font-weight: 700; color: #475569; margin-top: -12px;">
                    📌 <b>{numerador_gauge}</b> de <b>{denominador_gauge}</b> SKUs Activos ({label_modo_gauge}) en góndola
                    <span style="display: block; font-size: 0.74rem; font-weight: 600; color: #dc2626; margin-top: 4px;">
                        ⚠️ Ocupación Ociosa: <b>{skus_bloqueados_plano}</b> SKUs Bloqueados (B) en el plano
                    </span>
                </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_pie:
            st.markdown("<b>🎯 Salud del Stock y Ventas Asociadas <span style='font-size:0.75rem; color:#2563eb;'>(SURTIDO TOTAL)</span></b>", unsafe_allow_html=True)
            st.markdown('<div class="dash-card">', unsafe_allow_html=True)
            def get_h(r):
                if str(r['Estado']).strip().upper() == 'B': return 'Bloqueado (B)'
                elif r['Stock_Num'] <= 0: return 'Quiebre (0)'
                elif r['Stock_Num'] <= 5: return 'Alerta Baja (1-5)'
                else: return 'Stock OK (>5)'
            df_unicos['H_Estado'] = df_unicos.apply(get_h, axis=1)
            
            dh = df_unicos.groupby('H_Estado').agg(
                Cant=('COD REAL', 'nunique'),
                Venta_Asoc=('Venta_Num', 'sum')
            ).reset_index()
            
            fig_pie_h = px.pie(
                dh, values='Cant', names='H_Estado', hole=0.55, 
                color='H_Estado', 
                color_discrete_map={'Stock OK (>5)':'#16a34a', 'Alerta Baja (1-5)':'#facc15', 'Quiebre (0)':'#ea580c', 'Bloqueado (B)':'#dc2626'},
                custom_data=['Venta_Asoc']
            )
            fig_pie_h.update_traces(
                hovertemplate="<b>%{label}</b><br>SKUs: %{value} (%{percent})<br>Venta Asociada: S/ %{customdata[0]:,.2f}<extra></extra>"
            )
            fig_pie_h.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10), showlegend=True, height=270)
            st.plotly_chart(fig_pie_h, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        # --- FILA INFERIOR: QUIEBRES POR CATEGORÍA VS PARTICIPACIÓN DE VENTA ---
        st.markdown("<b>🔥 Quiebres por Categoría vs % Participación de Ventas <span style='font-size:0.75rem; color:#2563eb;'>(PRIORIZACIÓN OPERATIVA)</span></b>", unsafe_allow_html=True)
        st.markdown('<div class="dash-card">', unsafe_allow_html=True)
        ventas_por_cat = df_unicos.groupby('Categoría')['Venta_Num'].sum()
        total_vta_unicos = ventas_por_cat.sum()
        quiebres_por_cat = quiebres_df.groupby('Categoría')['COD REAL'].nunique()
        skus_tot_cat = df_unicos.groupby('Categoría')['COD REAL'].nunique()
        vta_riesgo_cat = quiebres_df.groupby('Categoría')['Venta_Num'].sum()
        
        df_cat_ops = pd.DataFrame({
            'Quiebres': quiebres_por_cat, 
            'Venta': ventas_por_cat,
            'SKUs_Total': skus_tot_cat,
            'Venta_Riesgo': vta_riesgo_cat
        }).fillna(0).reset_index()
        df_cat_ops = df_cat_ops[~df_cat_ops['Categoría'].isin(['SIN DATOS', 'S/C', 'nan', ''])].copy()
        df_cat_ops['Part_Venta'] = (df_cat_ops['Venta'] / total_vta_unicos) if total_vta_unicos > 0 else 0
        df_cat_ops['OSA_Cat'] = [((r['SKUs_Total'] - r['Quiebres']) / r['SKUs_Total'] * 100) if r['SKUs_Total'] > 0 else 100 for _, r in df_cat_ops.iterrows()]
        df_cat_ops = df_cat_ops.sort_values(by=['Quiebres', 'Part_Venta'], ascending=[False, False]).head(8)
        
        hover_q_matrix = df_cat_ops[['Venta_Riesgo', 'OSA_Cat', 'SKUs_Total']].values
        
        fig_ops = make_subplots(specs=[[{"secondary_y": True}]])
        fig_ops.add_trace(go.Bar(
            x=df_cat_ops['Categoría'], 
            y=df_cat_ops['Quiebres'], 
            name="Quiebres (Stock 0)",
            text=df_cat_ops['Quiebres'].apply(lambda x: f"{int(x)} Q"), 
            textposition='inside',
            marker=dict(color='#dc2626'),
            customdata=hover_q_matrix,
            hovertemplate="<b>%{x}</b><br>🚨 Quiebres: %{y} SKUs de %{customdata[2]}<br>💸 Venta en Riesgo: S/ %{customdata[0]:,.2f}<br>🎯 OSA Categoría: %{customdata[1]:.1f}%<extra></extra>"
        ), secondary_y=False)
        
        fig_ops.add_trace(go.Scatter(
            x=df_cat_ops['Categoría'], 
            y=df_cat_ops['Part_Venta'], 
            name="% Participación Venta",
            mode="lines+markers+text", 
            text=df_cat_ops['Part_Venta'].apply(lambda x: f"{x*100:.1f}%"),
            textposition='top center', 
            line=dict(color='#2563eb', width=3),
            hoverinfo='skip'
        ), secondary_y=True)
        fig_ops.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=20, l=10, r=10), hovermode='closest', height=330)
        st.plotly_chart(fig_ops, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    # =========================================================================
    # --- PESTAÑA 2: PLANOGRAMA FÍSICO PANORÁMICO ---
    # =========================================================================
    with tab_plano:
        cat_actual_titulo = f"{cat_sel} (Lateral {lat_letra_activa})" if cat_sel != "Todas las Categorías" else f"MUNDO {mundo_sel} - LATERAL {lat_letra_activa}"
        
        tot_skus_op = df_unicos['COD REAL'].nunique()
        bloq_op = df_unicos[df_unicos['Estado'].str.strip().str.upper() == 'B']['COD REAL'].nunique()
        quiebre_op = df_unicos[(df_unicos['Estado'].str.strip().str.upper() == 'A') & (df_unicos['Stock_Num'] <= 0)]['COD REAL'].nunique()
        stk_bajo_op = df_unicos[(df_unicos['Estado'].str.strip().str.upper() == 'A') & (df_unicos['Stock_Num'] > 0) & (df_unicos['Stock_Num'] <= 5)]['COD REAL'].nunique()
        stk_ok_op = df_unicos[(df_unicos['Estado'].str.strip().str.upper() == 'A') & (df_unicos['Stock_Num'] > 5)]['COD REAL'].nunique()
        cob_alta_op = df_unicos[df_unicos['Cob_Num'] >= 30]['COD REAL'].nunique()
        
        # Base ordenada de todos los SKUs para Top Ventas dinámico en JS
        df_top_ranking = df_unicos[['COD REAL', 'Venta_Num']].sort_values(by='Venta_Num', ascending=False)
        lista_skus_ventas_json = json.dumps([
            {"cod": str(row['COD REAL']), "vta": float(row['Venta_Num'])}
            for _, row in df_top_ranking.iterrows()
        ])
        
        total_venta_plano_float = float(ventas_tot_plano) if ventas_tot_plano > 0 else 1.0

        top_n_default = 5
        df_top_vta = df_unicos.sort_values(by='Venta_Num', ascending=False).head(top_n_default)
        monto_top_vta = df_top_vta['Venta_Num'].sum()
        pct_top_vta = (monto_top_vta / ventas_tot_plano * 100) if ventas_tot_plano > 0 else 0
        top_skus_set = set(df_top_vta['COD REAL'].astype(str).str.strip().unique())

        bandeja_series = get_clean_series(df_base, 'Bandeja')
        desglose = bandeja_series.apply(desglosar_cuerpo_y_nivel)
        df_base['Cuerpo_Ord'] = [x[0] for x in desglose]
        df_base['Nivel_Num'] = [x[1] for x in desglose]
        
        col_pos = 'N° ORDEN' if 'N° ORDEN' in df_base.columns else ('N°' if 'N°' in df_base.columns else None)
        if col_pos:
            df_base['TieneOrden'] = pd.to_numeric(get_clean_series(df_base, col_pos), errors='coerce').notna()
            df_base['NumOrden'] = pd.to_numeric(get_clean_series(df_base, col_pos), errors='coerce').fillna(999999)
        else:
            df_base['TieneOrden'] = False
            df_base['NumOrden'] = 999999
        df_base['FilaOriginal'] = range(len(df_base))

        df_base_sorted = df_base.sort_values(
            by=['Cuerpo_Ord', 'Nivel_Num', 'TieneOrden', 'NumOrden', 'FilaOriginal'], 
            ascending=[True, False, False, True, True]
        )

        cuerpos_dict = {}
        for _, r in df_base_sorted.iterrows():
            c_num = int(r['Cuerpo_Ord'])
            n_num = int(r['Nivel_Num'])
            cuerpo_id = f"CUERPO {c_num:02d}"
            if cuerpo_id not in cuerpos_dict:
                cuerpos_dict[cuerpo_id] = {}
            if n_num not in cuerpos_dict[cuerpo_id]:
                cuerpos_dict[cuerpo_id][n_num] = []
            cuerpos_dict[cuerpo_id][n_num].append(r)

        total_cuerpos = len(cuerpos_dict) if len(cuerpos_dict) > 0 else 1
        pct_cuerpo = 100.0 / total_cuerpos

        html_cuerpos = ""
        for cuerpo_id in sorted(cuerpos_dict.keys()):
            niveles_dict = cuerpos_dict[cuerpo_id]
            niveles_ordenados = sorted(niveles_dict.keys(), reverse=True)
            
            html_niveles = ""
            for n_num in niveles_ordenados:
                items = niveles_dict[n_num]
                rects_html = ""
                for it in items:
                    cod_real = str(it.get("COD REAL", ""))
                    ean = str(it.get("EAN", ""))
                    nombre = str(it.get("Descripción", it.get("Nombre", "")))
                    marca = str(it.get("Marca", "S/M"))
                    estado = str(it.get("Estado", ""))
                    caras = int(it.get("Caras", 1)) if str(it.get("Caras", 1)).isdigit() and int(it.get("Caras", 1)) > 0 else 1
                    pos_val = str(it.get(col_pos, "-")) if col_pos else "-"

                    stock_val = safe_float(it.get("Stock", -999.0))
                    cob_val = safe_float(it.get("Cobertura", -999.0))
                    venta_val = safe_float(it.get("Venta", -999.0))
                    part_val = safe_float(it.get("% Part", -999.0))

                    dept_val = str(it.get("Departamento", "SIN DATOS")).replace('"', '&quot;')
                    sec_val = str(it.get("Sección", "SIN DATOS")).replace('"', '&quot;')
                    catjer_val = str(it.get("Categoría", "SIN DATOS")).replace('"', '&quot;')
                    ga_val = str(it.get("Grupo de Artículo", "SIN DATOS")).replace('"', '&quot;')
                    
                    foto_sku = str(it.get("Links de fotos", "")).strip()
                    if foto_sku.upper() in ["SIN DATOS", "NAN", "NONE", ""]:
                        foto_sku = ""

                    bg_color, border_color, text_color, cat_leyenda = obtener_color_operativo(estado, stock_val)
                    es_cob_alta = "1" if cob_val >= 30 else "0"
                    es_top_vta = "1" if cod_real in top_skus_set else "0"

                    for c_idx in range(caras):
                        rects_html += f"""
                        <div class="plano-rect" style="background-color: {bg_color}; border-color: {border_color}; color: {text_color};"
                             data-estado="{cat_leyenda}" data-cobalta="{es_cob_alta}" data-topvta="{es_top_vta}"
                             data-brand="{marca}" data-name="{nombre}" data-ean="{ean}"
                             data-stock="{stock_val:.2f}" data-cob="{cob_val:.2f}" data-venta="{venta_val}" data-part="{format_pct(part_val)}"
                             data-cod="{cod_real}" data-cat="{cat_leyenda}" data-pos="{pos_val}" data-nivel="{n_num}"
                             data-dept="{dept_val}" data-sec="{sec_val}" data-catjer="{catjer_val}" data-ga="{ga_val}"
                             data-foto="{foto_sku}"
                             title="Nivel {n_num} • Pos {pos_val} | SAP: {cod_real} | {nombre}">
                            <span class="plano-sap-vertical">{cod_real}</span>
                        </div>
                        """

                html_niveles += f"""
                <div class="plano-level-row">
                    <div class="plano-facings-container">{rects_html}</div>
                    <div class="plano-shelf-bar"></div>
                </div>
                """

            html_cuerpos += f"""
            <div class="plano-cuerpo-col" style="flex: 0 0 {pct_cuerpo}%; max-width: {pct_cuerpo}%;">
                <div class="plano-cuerpo-shelves">{html_niveles}</div>
                <div class="plano-cuerpo-footer">{cuerpo_id}</div>
            </div>
            """

        marcas_unicas = sorted([m for m in df_base['Marca'].dropna().unique() if str(m).strip() not in ['SIN DATOS', 'nan', '']])
        options_marca = "".join([f"<option value='{m}'>{m}</option>" for m in marcas_unicas])

        niveles_reales = [x[1] for x in desglose]
        max_niveles_count = max(niveles_reales) if len(niveles_reales) > 0 else 8
        altura_cuerpo_px = max(260, max_niveles_count * 48)

        url_sheet_img = None
        cat_key_lookup = cat_actual_titulo.strip().upper()
        if cat_key_lookup in mapa_imagenes_online:
            url_sheet_img = mapa_imagenes_online[cat_key_lookup]
        else:
            for k, val in mapa_imagenes_online.items():
                if k in cat_key_lookup or cat_key_lookup in k:
                    url_sheet_img = val
                    break
        
        img_html_block = f"""
            <div class="planograma-img-frame" id="fullImgFrame">
                <img src="{url_sheet_img}" alt="Planograma Oficial {cat_actual_titulo}">
            </div>
        """ if url_sheet_img else ""

        offset_elementos = 740 if url_sheet_img else 460
        altura_iframe = altura_cuerpo_px + offset_elementos

        html_componente_completo = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
          <meta charset="UTF-8">
          <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            html, body {{
                font-family: 'Plus Jakarta Sans', sans-serif;
                background: #ffffff;
                color: #0f172a;
                padding: 4px;
                width: 100%;
                overflow-y: hidden !important;
                height: auto !important;
            }}
            .top-ventas-bar {{
                background: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px 14px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 12px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.03);
            }}
            .top-ventas-left {{
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 0.84rem;
                font-weight: 800;
                color: #0f172a;
            }}
            .top-ventas-input {{
                width: 70px;
                padding: 4px 8px;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                text-align: center;
                font-weight: 800;
                font-size: 0.88rem;
                color: #0f172a;
                outline: none;
            }}
            .top-ventas-right {{
                font-size: 0.84rem;
                font-weight: 800;
                color: #2563eb;
            }}
            .filter-cards-grid {{
                display: grid;
                grid-template-columns: repeat(6, 1fr);
                gap: 8px;
                margin-bottom: 12px;
            }}
            @media (max-width: 900px) {{
                .filter-cards-grid {{
                    grid-template-columns: repeat(3, 1fr) !important;
                    gap: 6px !important;
                }}
            }}
            .card-static {{
                background: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px 6px;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.04);
                user-select: none;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }}
            .card-static-title {{
                font-size: 0.65rem;
                font-weight: 800;
                text-transform: uppercase;
                margin-bottom: 4px;
                letter-spacing: 0.4px;
                text-align: center;
            }}
            .card-static-val {{
                font-size: 1.65rem;
                font-weight: 900;
                line-height: 1;
                text-align: center;
                font-feature-settings: "tnum";
            }}
            .cb-total {{ border-bottom: 4px solid #2563eb; }}
            .cb-total .card-static-title {{ color: #2563eb; }}
            .cb-total .card-static-val {{ color: #0f172a; }}
            .cb-bloq {{ border-bottom: 4px solid #dc2626; }}
            .cb-bloq .card-static-title {{ color: #dc2626; }}
            .cb-bloq .card-static-val {{ color: #dc2626; }}
            .cb-sinstk {{ border-bottom: 4px solid #ea580c; }}
            .cb-sinstk .card-static-title {{ color: #ea580c; }}
            .cb-sinstk .card-static-val {{ color: #ea580c; }}
            .cb-stkbajo {{ border-bottom: 4px solid #facc15; }}
            .cb-stkbajo .card-static-title {{ color: #ca8a04; }}
            .cb-stkbajo .card-static-val {{ color: #ca8a04; }}
            .cb-stkok {{ border-bottom: 4px solid #16a34a; }}
            .cb-stkok .card-static-title {{ color: #16a34a; }}
            .cb-stkok .card-static-val {{ color: #16a34a; }}
            .cb-cobalta {{ border-bottom: 4px solid #ec4899; }}
            .cb-cobalta .card-static-title {{ color: #db2777; }}
            .cb-cobalta .card-static-val {{ color: #db2777; }}

            .controls-panel {{
                background: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px 14px;
                margin-bottom: 12px;
                display: flex;
                align-items: flex-end;
                justify-content: space-between;
                gap: 10px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.03);
            }}
            .controls-left {{
                display: flex;
                gap: 10px;
                flex-grow: 1;
                align-items: flex-end;
            }}
            .ctrl-group {{
                display: flex;
                flex-direction: column;
                gap: 3px;
                flex: 1;
            }}
            .ctrl-label {{
                font-size: 0.68rem;
                font-weight: 800;
                color: #2563eb;
                text-transform: uppercase;
                display: flex;
                align-items: center;
                gap: 4px;
            }}
            .ctrl-input, .ctrl-select {{
                width: 100%;
                padding: 7px 10px;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                font-size: 0.82rem;
                font-weight: 600;
                color: #0f172a;
                background: #ffffff;
                outline: none;
            }}
            .buttons-actions-row {{
                display: flex;
                gap: 6px;
                align-items: center;
            }}
            .btn-icon-act {{
                width: 36px;
                height: 36px;
                border-radius: 6px;
                font-size: 1.15rem;
                font-weight: 900;
                cursor: pointer;
                border: 1.5px solid transparent;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.15s ease, background 0.15s ease;
            }}
            .btn-icon-act:hover {{ transform: translateY(-1px); }}
            .btn-fullscreen-icon {{ background: #eff6ff; color: #2563eb; border-color: #bfdbfe; }}
            .btn-reset-icon {{ background: #fee2e2; color: #dc2626; border-color: #fecaca; }}

            #fullscreenAuditor {{
                position: relative;
                background: #ffffff;
                width: 100%;
            }}
            #fullscreenAuditor:fullscreen {{
                padding: 16px;
                overflow-y: auto !important;
                background: #ffffff;
            }}
            .exit-fullscreen-btn {{
                display: none;
                position: fixed;
                top: 14px;
                right: 14px;
                z-index: 999999;
                background: #0f172a;
                color: #ffffff;
                border: 2px solid #ffffff;
                border-radius: 20px;
                padding: 6px 14px;
                font-size: 0.82rem;
                font-weight: 800;
                cursor: pointer;
                box-shadow: 0 4px 14px rgba(0,0,0,0.3);
                transition: transform 0.15s ease, background 0.15s ease;
            }}
            .exit-fullscreen-btn:hover {{
                background: #dc2626;
                transform: scale(1.05);
            }}
            #fullscreenAuditor:fullscreen .exit-fullscreen-btn {{
                display: flex;
                align-items: center;
                gap: 6px;
            }}

            .planograma-img-frame {{
                width: 100%;
                height: 260px;
                background: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
                margin-bottom: 12px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.04);
            }}
            .planograma-img-frame img {{
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
            }}

            .interactive-legend-bar {{
                display: flex;
                align-items: center;
                gap: 8px;
                flex-wrap: wrap;
                padding: 8px 12px;
                background: rgba(255, 255, 255, 0.98);
                backdrop-filter: blur(8px);
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                margin-bottom: 10px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                position: sticky;
                top: 0;
                z-index: 1000;
                width: 100%;
            }}
            .legend-label-title {{
                font-size: 0.72rem;
                font-weight: 800;
                color: #2563eb;
                text-transform: uppercase;
                letter-spacing: 0.4px;
                margin-right: 4px;
            }}
            .legend-btn {{
                font-size: 0.72rem;
                font-weight: 800;
                padding: 5px 13px;
                border-radius: 14px;
                cursor: pointer;
                border: 2px solid transparent;
                transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
                user-select: none;
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }}
            .legend-btn:hover {{
                transform: translateY(-1px);
                box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            }}
            .legend-btn.active {{
                outline: 2.5px solid #0f172a !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
                transform: scale(1.04);
            }}
            .btn-bloq {{ background: #dc2626 !important; color: #ffffff !important; border-color: #991b1b !important; }}
            .btn-sinstk {{ background: #ea580c !important; color: #ffffff !important; border-color: #c2410c !important; }}
            .btn-bajo {{ background: #facc15 !important; color: #0f172a !important; border-color: #ca8a04 !important; }}
            .btn-ok {{ background: #16a34a !important; color: #ffffff !important; border-color: #15803d !important; }}
            .btn-topvta {{ background: #8b5cf6 !important; color: #ffffff !important; border-color: #6d28d9 !important; }}
            .btn-todos {{ background: #f1f5f9 !important; color: #0f172a !important; border-color: #cbd5e1 !important; }}

            .plano-outer-card {{
                border: 2px solid #0f172a;
                border-radius: 6px;
                overflow: hidden;
                background: #ffffff;
                width: 100%;
            }}
            .plano-top-header {{
                background: #facc15;
                color: #b91c1c;
                font-size: 1.05rem;
                font-weight: 900;
                text-align: center;
                padding: 6px 10px;
                letter-spacing: 1px;
                text-transform: uppercase;
                border-bottom: 2px solid #0f172a;
            }}
            .plano-body-container {{
                display: flex;
                flex-direction: row;
                width: 100%;
                height: {altura_cuerpo_px}px;
                background: #ffffff;
            }}
            .plano-cuerpo-col {{
                display: flex;
                flex-direction: column;
                border-right: 2px solid #0f172a;
                min-width: 0;
                height: 100%;
            }}
            .plano-cuerpo-col:last-child {{ border-right: none; }}
            .plano-cuerpo-shelves {{
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                padding: 3px 2px;
                gap: 2.5px;
                flex-grow: 1;
                height: 100%;
            }}
            .plano-level-row {{
                display: flex;
                flex-direction: column;
                justify-content: flex-end;
                width: 100%;
                flex: 1 1 0;
                min-height: 0;
            }}
            .plano-facings-container {{
                display: flex;
                flex-direction: row;
                align-items: stretch;
                gap: 1px;
                height: 45px;
                padding: 0 1px;
                width: 100%;
            }}
            .plano-rect {{
                flex: 1 1 0;
                min-width: 0;
                height: 100%;
                border: 1px solid #000000;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                overflow: hidden;
                position: relative;
                transition: transform 0.15s ease, opacity 0.2s ease, filter 0.2s ease;
            }}
            .plano-rect.dimmed {{
                opacity: 0.12 !important;
                filter: grayscale(80%) !important;
            }}
            .plano-rect.highlighted {{
                transform: scale(1.08);
                z-index: 50;
                box-shadow: 0 0 0 2px #0f172a, 0 4px 10px rgba(0,0,0,0.4) !important;
            }}
            .plano-sap-vertical {{
                writing-mode: vertical-rl;
                transform: rotate(180deg);
                font-size: 0.50rem;
                font-weight: 900;
                letter-spacing: -0.3px;
                line-height: 1;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-height: 40px;
                font-family: 'JetBrains Mono', monospace;
                pointer-events: none;
                user-select: none;
            }}
            .plano-shelf-bar {{
                height: 4.5px;
                background: #facc15;
                border: 1px solid #ca8a04;
                margin-top: 1px;
                width: 100%;
            }}
            .plano-cuerpo-footer {{
                background: #ffffff;
                border-top: 2px solid #0f172a;
                color: #0f172a;
                font-size: 0.85rem;
                font-weight: 900;
                text-align: center;
                padding: 4px 0;
                letter-spacing: 0.5px;
            }}

            .modal-overlay {{ 
              position: fixed !important; 
              inset: 0 !important; 
              width: 100vw !important; 
              height: 100vh !important; 
              background: rgba(15, 23, 42, 0.72) !important; 
              z-index: 2147483647 !important; 
              opacity: 0; 
              pointer-events: none; 
              transition: opacity 0.2s ease; 
              display: flex !important; 
              align-items: center !important; 
              justify-content: center !important; 
              padding: 16px !important; 
              backdrop-filter: blur(5px); 
            }}
            .modal-overlay.active {{ opacity: 1 !important; pointer-events: auto !important; }}
            .modal-content {{ 
              background: #ffffff !important; 
              color: #0f172a !important; 
              padding: 20px 22px !important; 
              border-radius: 12px !important; 
              width: 92% !important; 
              max-width: 440px !important; 
              border: 2.5px solid #2563eb !important; 
              box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4) !important; 
              position: relative !important; 
            }}
            .modal-close {{ 
              position: absolute; 
              top: 10px; 
              right: 14px; 
              font-size: 1.4rem; 
              cursor: pointer; 
              color: #64748b; 
              font-weight: 800; 
              line-height: 1;
            }}
            .modal-close:hover {{ color: #dc2626; }}
            .m-header-box {{
                display: flex;
                gap: 12px;
                align-items: center;
                border-bottom: 2px solid #2563eb;
                padding-bottom: 12px;
                margin-bottom: 10px;
            }}
            .m-img-wrapper {{
                width: 76px;
                height: 76px;
                border-radius: 8px;
                background: #f8fafc;
                border: 1.5px solid #cbd5e1;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
                flex-shrink: 0;
            }}
            .m-img-wrapper img {{
                width: 100%;
                height: 100%;
                object-fit: contain;
            }}
            .m-no-img {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                color: #94a3b8;
                font-size: 0.62rem;
                font-weight: 800;
                text-align: center;
                line-height: 1.1;
                gap: 2px;
            }}
            .m-header-info {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                overflow: hidden;
            }}
            .m-header-title {{
                font-size: 0.88rem;
                font-weight: 800;
                color: #0f172a;
                line-height: 1.25;
                margin-bottom: 4px;
                word-wrap: break-word;
            }}
            .m-header-badge {{
                font-size: 0.65rem;
                font-weight: 800;
                color: #2563eb;
                text-transform: uppercase;
                letter-spacing: 0.4px;
            }}
            .m-row {{ 
              border-bottom: 1px solid #f1f5f9; 
              padding: 5px 0; 
              display: flex; 
              justify-content: space-between; 
              align-items: center;
              font-size: 0.80rem; 
            }}
            .m-label {{ font-weight: 600; color: #2563eb; }}
            .m-val {{ font-weight: 700; text-align: right; }}
          </style>
        </head>
        <body>

          <div class="top-ventas-bar">
            <div class="top-ventas-left">
                <span>🏆 RESALTAR TOP VENTAS:</span>
                <input type="number" id="inputTopVentas" class="top-ventas-input" value="{top_n_default}" min="1" max="{len(df_top_ranking)}">
                <span style="color: #2563eb;">SKUs</span>
            </div>
            <div class="top-ventas-right" id="labelTopInfo">
                TOP {top_n_default} concentra el <span style="color: #16a34a;">{pct_top_vta:.1f}%</span> de la venta (S/ {monto_top_vta:,.2f}).
            </div>
          </div>

          <div class="filter-cards-grid">
            <div class="card-static cb-total">
                <div class="card-static-title">TOTAL SKUS</div>
                <div class="card-static-val">{tot_skus_op}</div>
            </div>
            <div class="card-static cb-bloq">
                <div class="card-static-title">BLOQUEADOS</div>
                <div class="card-static-val">{bloq_op}</div>
            </div>
            <div class="card-static cb-sinstk">
                <div class="card-static-title">SIN STOCK (0)</div>
                <div class="card-static-val">{quiebre_op}</div>
            </div>
            <div class="card-static cb-stkbajo">
                <div class="card-static-title">STOCK BAJO (1-5)</div>
                <div class="card-static-val">{stk_bajo_op}</div>
            </div>
            <div class="card-static cb-stkok">
                <div class="card-static-title">STOCK OK (>5)</div>
                <div class="card-static-val">{stk_ok_op}</div>
            </div>
            <div class="card-static cb-cobalta">
                <div class="card-static-title">COB. ALTA (≥30)</div>
                <div class="card-static-val">{cob_alta_op}</div>
            </div>
          </div>

          <div class="controls-panel">
            <div class="controls-left">
                <div class="ctrl-group" style="flex: 2;">
                    <span class="ctrl-label">🔍 BUSCAR PRODUCTO</span>
                    <input type="text" id="busqNombre" class="ctrl-input" placeholder="Nombre, EAN o Código SAP...">
                </div>
                <div class="ctrl-group" style="flex: 1.2;">
                    <span class="ctrl-label">🏷️ MARCA</span>
                    <select id="selMarca" class="ctrl-select">
                        <option value="Todas">Todas las Marcas</option>
                        {options_marca}
                    </select>
                </div>
            </div>
            <div class="buttons-actions-row">
                <button type="button" class="btn-icon-act btn-fullscreen-icon" id="btnFullscreen" title="Pantalla Completa">⛶</button>
                <button type="button" class="btn-icon-act btn-reset-icon" id="btnResetAll" title="Restablecer Filtros">↺</button>
            </div>
          </div>

          <div id="fullscreenAuditor">
            <button type="button" class="exit-fullscreen-btn" id="btnExitFullscreen">
                ✕ Salir de Pantalla Completa
            </button>

            {img_html_block}

            <div class="interactive-legend-bar">
                <span class="legend-label-title">📍 LEYENDA OPERATIVA:</span>
                <button type="button" class="legend-btn btn-bloq" data-target="Bloqueado">Bloqueado (B)</button>
                <button type="button" class="legend-btn btn-sinstk" data-target="Sin Stock">Sin Stock / Quiebre (0)</button>
                <button type="button" class="legend-btn btn-bajo" data-target="Stock Bajo">Stock Bajo (1 a 5)</button>
                <button type="button" class="legend-btn btn-ok" data-target="Stock OK">Stock OK (> 5)</button>
                <button type="button" class="legend-btn btn-topvta" data-target="Top Ventas">🏆 Top Ventas</button>
                <button type="button" class="legend-btn btn-todos" id="btnVerTodos" style="margin-left: auto;">Ver Todos</button>
            </div>

            <div class="plano-outer-card" id="planoCard">
                <div class="plano-top-header">{cat_actual_titulo}</div>
                <div class="plano-body-container">
                    {html_cuerpos}
                </div>
            </div>

            <div id="pModal" class="modal-overlay">
              <div class="modal-content">
                <span class="modal-close">&times;</span>
                <div class="m-header-box">
                  <div class="m-img-wrapper" id="m-img-wrapper"></div>
                  <div class="m-header-info">
                    <span class="m-header-badge" id="m-brand"></span>
                    <h4 class="m-header-title" id="m-name">Producto</h4>
                  </div>
                </div>
                <div class="m-row"><span class="m-label">Código SAP / Cód. Real:</span><span class="m-val" id="m-cod" style="font-family: monospace; font-size: 0.95rem; font-weight: 900;"></span></div>
                <div class="m-row"><span class="m-label">Ubicación (Nivel / Pos):</span><span class="m-val" id="m-pos"></span></div>
                <div class="m-row"><span class="m-label">EAN:</span><span class="m-val" id="m-ean"></span></div>
                <div class="m-row"><span class="m-label">Categoría:</span><span class="m-val" id="m-catjer"></span></div>
                <div class="m-row"><span class="m-label">Stock Actual:</span><span class="m-val" id="m-stock"></span></div>
                <div class="m-row"><span class="m-label">Cobertura:</span><span class="m-val" id="m-cob"></span></div>
                <div class="m-row"><span class="m-label">Estado Stock:</span><span class="m-val" id="m-cat"></span></div>
                <div class="m-row"><span class="m-label">Ventas:</span><span class="m-val" id="m-venta"></span></div>
              </div>
            </div>
          </div>

          <script>
            let activeFilterType = 'TOTAL';
            const legendButtons = document.querySelectorAll('.legend-btn[data-target]');
            const rects = document.querySelectorAll('.plano-rect');
            const busqInput = document.getElementById('busqNombre');
            const selMarca = document.getElementById('selMarca');
            const topInput = document.getElementById('inputTopVentas');
            const topLabel = document.getElementById('labelTopInfo');

            // Data de ranking para Top Ventas en tiempo real
            const rankingVentas = {lista_skus_ventas_json};
            const totalVentaPlano = {total_venta_plano_float};

            function actualizarTopVentasDinamico() {{
                let n = parseInt(topInput.value) || 1;
                if (n < 1) n = 1;
                if (n > rankingVentas.length) n = rankingVentas.length;

                const topSlice = rankingVentas.slice(0, n);
                const codigosTop = new Set(topSlice.map(item => String(item.cod).trim().toLowerCase()));
                const sumaVentaTop = topSlice.reduce((acc, cur) => acc + (cur.vta > 0 ? cur.vta : 0), 0);
                const pctTop = totalVentaPlano > 0 ? (sumaVentaTop / totalVentaPlano * 100) : 0;

                // Actualizar texto en tiempo real
                topLabel.innerHTML = `TOP ${{n}} concentra el <span style="color: #16a34a;">${{pctTop.toFixed(1)}}%</span> de la venta (S/ ${{sumaVentaTop.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}).`;

                // Actualizar dataset en cada rect del planograma
                rects.forEach(r => {{
                    const cod = (r.getAttribute('data-cod') || '').trim().toLowerCase();
                    if (codigosTop.has(cod)) {{
                        r.setAttribute('data-topvta', '1');
                    }} else {{
                        r.setAttribute('data-topvta', '0');
                    }}
                }});

                // Si el filtro actual es TOP_VENTAS, re-aplicar resaltado visual
                if (activeFilterType === 'TOP_VENTAS') {{
                    aplicarFiltrosGlobales();
                }}
            }}

            function aplicarFiltrosGlobales() {{
                const q = busqInput.value.toLowerCase().trim();
                const m = selMarca.value;

                rects.forEach(r => {{
                    const estado = r.getAttribute('data-estado');
                    const cobAlta = r.getAttribute('data-cobalta') === '1';
                    const topVta = r.getAttribute('data-topvta') === '1';
                    const name = (r.getAttribute('data-name') || '').toLowerCase();
                    const ean = (r.getAttribute('data-ean') || '').toLowerCase();
                    const cod = (r.getAttribute('data-cod') || '').toLowerCase();
                    const brand = r.getAttribute('data-brand') || '';

                    let matchTipo = true;
                    if (activeFilterType === 'BLOQUEADOS') matchTipo = (estado === 'Bloqueado');
                    else if (activeFilterType === 'SIN_STOCK') matchTipo = (estado === 'Sin Stock');
                    else if (activeFilterType === 'STOCK_BAJO') matchTipo = (estado === 'Stock Bajo');
                    else if (activeFilterType === 'STOCK_OK') matchTipo = (estado === 'Stock OK');
                    else if (activeFilterType === 'COB_ALTA') matchTipo = cobAlta;
                    else if (activeFilterType === 'TOP_VENTAS') matchTipo = topVta;

                    let matchText = true;
                    if (q) {{
                        matchText = name.includes(q) || ean.includes(q) || cod.includes(q);
                    }}

                    let matchMarca = (m === 'Todas' || m === 'Todas las Marcas' || brand === m);

                    if (matchTipo && matchText && matchMarca) {{
                        r.classList.remove('dimmed');
                        if (activeFilterType !== 'TOTAL' || q) {{
                            r.classList.add('highlighted');
                        }} else {{
                            r.classList.remove('highlighted');
                        }}
                    }} else {{
                        r.classList.add('dimmed');
                        r.classList.remove('highlighted');
                    }}
                }});
            }}

            // Evento para actualizar Top Ventas en tiempo real al escribir o dar Enter
            topInput.addEventListener('input', () => {{
                actualizarTopVentasDinamico();
            }});
            topInput.addEventListener('change', () => {{
                actualizarTopVentasDinamico();
            }});
            topInput.addEventListener('keydown', (e) => {{
                if (e.key === 'Enter') {{
                    e.preventDefault();
                    actualizarTopVentasDinamico();
                    // Al pulsar enter, activa automáticamente el modo Top Ventas
                    const btnTop = document.querySelector('.legend-btn[data-target="Top Ventas"]');
                    if (btnTop) {{
                        legendButtons.forEach(b => b.classList.remove('active'));
                        btnTop.classList.add('active');
                        activeFilterType = 'TOP_VENTAS';
                        aplicarFiltrosGlobales();
                    }}
                }}
            }});

            legendButtons.forEach(btn => {{
                btn.addEventListener('click', () => {{
                    const target = btn.getAttribute('data-target');
                    if (btn.classList.contains('active')) {{
                        btn.classList.remove('active');
                        activeFilterType = 'TOTAL';
                    }} else {{
                        legendButtons.forEach(b => b.classList.remove('active'));
                        btn.classList.add('active');
                        if (target === 'Bloqueado') activeFilterType = 'BLOQUEADOS';
                        else if (target === 'Sin Stock') activeFilterType = 'SIN_STOCK';
                        else if (target === 'Stock Bajo') activeFilterType = 'STOCK_BAJO';
                        else if (target === 'Stock OK') activeFilterType = 'STOCK_OK';
                        else if (target === 'Top Ventas') {{
                            actualizarTopVentasDinamico();
                            activeFilterType = 'TOP_VENTAS';
                        }}
                    }}
                    aplicarFiltrosGlobales();
                }});
            }});

            document.getElementById('btnVerTodos').addEventListener('click', () => {{
                activeFilterType = 'TOTAL';
                legendButtons.forEach(b => b.classList.remove('active'));
                aplicarFiltrosGlobales();
            }});

            busqInput.addEventListener('input', aplicarFiltrosGlobales);
            selMarca.addEventListener('change', aplicarFiltrosGlobales);

            document.getElementById('btnResetAll').addEventListener('click', () => {{
                activeFilterType = 'TOTAL';
                legendButtons.forEach(b => b.classList.remove('active'));
                busqInput.value = '';
                selMarca.value = 'Todas';
                topInput.value = '{top_n_default}';
                actualizarTopVentasDinamico();
                aplicarFiltrosGlobales();
            }});

            const fullAuditor = document.getElementById('fullscreenAuditor');
            document.getElementById('btnFullscreen').addEventListener('click', () => {{
                if (!document.fullscreenElement) {{
                    fullAuditor.requestFullscreen().catch(err => {{
                        alert("No se pudo iniciar el modo pantalla completa.");
                    }});
                }} else {{
                    document.exitFullscreen();
                }}
            }});

            document.getElementById('btnExitFullscreen').addEventListener('click', () => {{
                if (document.fullscreenElement) {{
                    document.exitFullscreen();
                }}
            }});

            const modal = document.getElementById('pModal');
            const closeBtn = document.querySelector('.modal-close');
            const imgWrapper = document.getElementById('m-img-wrapper');

            rects.forEach(rect => {{
                rect.addEventListener('click', () => {{
                    document.getElementById('m-name').textContent = rect.getAttribute('data-name');
                    document.getElementById('m-cod').textContent = rect.getAttribute('data-cod');
                    document.getElementById('m-pos').textContent = "Nivel " + rect.getAttribute('data-nivel') + " • Posición " + rect.getAttribute('data-pos');
                    document.getElementById('m-ean').textContent = rect.getAttribute('data-ean');
                    document.getElementById('m-brand').textContent = rect.getAttribute('data-brand');
                    document.getElementById('m-catjer').textContent = rect.getAttribute('data-catjer');
                    document.getElementById('m-stock').textContent = rect.getAttribute('data-stock');
                    document.getElementById('m-cob').textContent = rect.getAttribute('data-cob');
                    document.getElementById('m-cat').textContent = rect.getAttribute('data-cat');
                    const v = parseFloat(rect.getAttribute('data-venta')) || 0;
                    document.getElementById('m-venta').textContent = v === -999 ? "SIN DATOS" : "S/ " + v.toLocaleString('en-US', {{minimumFractionDigits:2, maximumFractionDigits:2}});

                    const fotoUrl = rect.getAttribute('data-foto');
                    if (fotoUrl && fotoUrl.trim() !== '') {{
                        imgWrapper.innerHTML = `<img src="${{fotoUrl}}" alt="Producto" onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\\'m-no-img\\'><span style=\\'font-size:1.4rem;\\'>🖼️</span><span>Sin foto</span></div>';">`;
                    }} else {{
                        imgWrapper.innerHTML = `<div class="m-no-img"><span style="font-size:1.4rem;">🖼️</span><span>Sin foto</span></div>`;
                    }}

                    modal.classList.add('active');
                }});
            }});
            closeBtn.addEventListener('click', () => modal.classList.remove('active'));
            window.addEventListener('click', (e) => {{ if(e.target === modal) modal.classList.remove('active'); }});

            // Inicialización al cargar la vista
            actualizarTopVentasDinamico();
          </script>
        </body>
        </html>
        """
        components.html(html_componente_completo, height=altura_iframe, scrolling=False)

    # =========================================================================
    # --- PESTAÑA 3: DASHBOARD ANALÍTICO FINANCIERO (CONSOLIDADO EXACTO) ---
    # =========================================================================
    with tab_dash:
        df_universo_cat = df_sku_unico_global.copy()
        if 'Mundo' in df_universo_cat.columns:
            df_universo_cat = df_universo_cat[df_universo_cat['Mundo'] == mundo_sel].copy()

        if cat_sel != "Todas las Categorías":
            df_universo_cat = df_universo_cat[df_universo_cat['Categoría'] == cat_sel].copy()
            label_contexto = f"categoría {cat_sel}"
        else:
            cats_en_este_lateral = [c for c in df_base['Categoría'].dropna().unique() if str(c) not in ['SIN DATOS', 'S/C', 'nan', '']]
            if cats_en_este_lateral:
                df_universo_cat = df_universo_cat[df_universo_cat['Categoría'].isin(cats_en_este_lateral)].copy()
            label_contexto = f"Lateral {lat_letra_activa} ({len(cats_en_este_lateral)} categorías)"

        ventas_plano = df_unicos['Venta_Num'].sum()
        margen_bruto = df_unicos['Margen_Num'].sum()
        margen_global_pct = (margen_bruto / ventas_plano * 100) if ventas_plano > 0 else 0.0
        skus_en_plano = df_unicos['COD REAL'].nunique()

        tot_vta_universo = df_universo_cat['Venta'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0)).sum()
        pct_vta_tot = (ventas_plano / tot_vta_universo * 100) if tot_vta_universo > 0 else 100.0
        tot_skus_universo = df_universo_cat['COD REAL'].nunique()
        pct_skus_surtido = (skus_en_plano / tot_skus_universo * 100) if tot_skus_universo > 0 else 100.0

        st.markdown(f"""
            <div class="kpi-cards-grid grid-4-col">
                <div class="kpi-card-lux" style="border-bottom: 4px solid #2563eb;">
                    <div class="kpi-card-header"><span>VENTAS PLANOGRAMA</span><span>💳</span></div>
                    <div class="kpi-card-value" style="color: #0f172a;">S/ {ventas_plano:,.2f}</div>
                    <div class="kpi-card-footer">{pct_vta_tot:.1f}% de la venta en {label_contexto} (S/ {tot_vta_universo:,.2f})</div>
                </div>
                <div class="kpi-card-lux" style="border-bottom: 4px solid #10b981;">
                    <div class="kpi-card-header"><span>MARGEN TOTAL BRUTO</span><span>📈</span></div>
                    <div class="kpi-card-value" style="color: #10b981;">S/ {margen_bruto:,.2f}</div>
                    <div class="kpi-card-footer">Ganancia Monetaria en Planograma</div>
                </div>
                <div class="kpi-card-lux" style="border-bottom: 4px solid #8b5cf6;">
                    <div class="kpi-card-header"><span>MARGEN GLOBAL (%)</span><span>📊</span></div>
                    <div class="kpi-card-value" style="color: #8b5cf6;">{margen_global_pct:.1f}%</div>
                    <div class="kpi-card-footer">Rentabilidad sobre Venta Planograma</div>
                </div>
                <div class="kpi-card-lux" style="border-bottom: 4px solid #f59e0b;">
                    <div class="kpi-card-header"><span>SKUS EN PLANOGRAMA</span><span>📦</span></div>
                    <div class="kpi-card-value" style="color: #d97706;">{skus_en_plano}</div>
                    <div class="kpi-card-footer">{pct_skus_surtido:.1f}% del catálogo de {label_contexto} ({tot_skus_universo} SKUs)</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col_g_cuerpos, col_g_mix = st.columns([7, 3])
        with col_g_cuerpos:
            col_titulo_c, col_btn_orden = st.columns([5.5, 4.5])
            with col_titulo_c:
                st.markdown(f"<b>📈 Rendimiento por Cuerpo (Lateral {lat_letra_activa})</b>", unsafe_allow_html=True)
            with col_btn_orden:
                orden_sel = st.segmented_control(
                    "Ordenar por:",
                    ["Secuencial", "Por Venta", "Por Margen"],
                    default="Secuencial",
                    label_visibility="collapsed",
                    key="orden_cuerpo_ctrl"
                )

            bandeja_series = get_clean_series(df_base, 'Bandeja')
            df_base['Cuerpo_Num'] = [desglosar_cuerpo_y_nivel(v)[0] for v in bandeja_series]
            
            df_sku_cuerpo_caras = df_base.groupby(['COD REAL', 'Cuerpo_Num'])['Caras_Num'].sum().reset_index()
            df_sku_total_caras = df_base.groupby('COD REAL')['Caras_Num'].sum().reset_index().rename(columns={'Caras_Num': 'Caras_Total_SKU'})
            
            df_pesos = pd.merge(df_sku_cuerpo_caras, df_sku_total_caras, on='COD REAL', how='left')
            df_pesos['Factor_Ponderacion'] = df_pesos['Caras_Num'] / df_pesos['Caras_Total_SKU']
            
            df_pesos = pd.merge(df_pesos, df_unicos[['COD REAL', 'Venta_Num', 'Margen_Num']], on='COD REAL', how='left')
            df_pesos['Venta_Ponderada'] = df_pesos['Venta_Num'] * df_pesos['Factor_Ponderacion']
            df_pesos['Margen_Ponderado'] = df_pesos['Margen_Num'] * df_pesos['Factor_Ponderacion']
            
            mapa_cats_cuerpo = df_base.groupby('Cuerpo_Num')['Categoría'].apply(
                lambda s: ", ".join(sorted([c for c in set(s.dropna()) if str(c) not in ['SIN DATOS', 'S/C', 'nan', '']]))
            ).to_dict()

            vc = df_pesos.groupby('Cuerpo_Num').agg(
                Venta_Total=('Venta_Ponderada', 'sum'),
                Margen_Total=('Margen_Ponderado', 'sum'),
                SKUs=('COD REAL', 'nunique')
            ).reset_index()

            vc['Categorias_Txt'] = vc['Cuerpo_Num'].map(mapa_cats_cuerpo).fillna("Surtido Varios")
            vc['Margen_Pct'] = [r['Margen_Total']/r['Venta_Total'] if r['Venta_Total']>0 else 0 for _, r in vc.iterrows()]
            vc['Label'] = [f"Cuerpo {int(r['Cuerpo_Num']):02d}" for _, r in vc.iterrows()]
            vc['Part_Venta_Gondola'] = [(r['Venta_Total'] / ventas_plano * 100) if ventas_plano > 0 else 0 for _, r in vc.iterrows()]
            
            if orden_sel == "Por Venta":
                vc = vc.sort_values(by='Venta_Total', ascending=False)
            elif orden_sel == "Por Margen":
                vc = vc.sort_values(by='Margen_Pct', ascending=False)
            else:
                vc = vc.sort_values(by='Cuerpo_Num', ascending=True)

            c_meta = vc[['Venta_Total', 'Part_Venta_Gondola', 'Margen_Total', 'Margen_Pct', 'SKUs', 'Categorias_Txt']].copy()

            hover_template_cuerpo = (
                "<b>%{x}</b><br>" +
                "🏷️ <i>Categoría(s): %{customdata[5]}</i><br><br>" +
                "💳 <b>Venta Total:</b> S/ %{customdata[0]:,.2f}<br>" +
                "📊 <b>% Venta Góndola:</b> %{customdata[1]:.1f}%<br>" +
                "📈 <b>Margen Monetario:</b> S/ %{customdata[2]:,.2f}<br>" +
                "🎯 <b>Margen Comercial:</b> %{customdata[3]:.1%}<br>" +
                "📦 <b>SKUs Únicos:</b> %{customdata[4]} SKUs" +
                "<extra></extra>"
            )

            fig_c = make_subplots(specs=[[{"secondary_y": True}]])
            fig_c.add_trace(go.Bar(
                x=vc['Label'], 
                y=vc['Venta_Total'], 
                name="Ventas Totales (S/)", 
                marker_color='#2563eb',
                text=vc['Venta_Total'].apply(lambda x: f"S/ {x:,.0f}"),
                textposition='inside',
                customdata=c_meta.values,
                hovertemplate=hover_template_cuerpo
            ), secondary_y=False)
            
            fig_c.add_trace(go.Scatter(
                x=vc['Label'], 
                y=vc['Margen_Pct'], 
                name="Margen %", 
                mode="lines+markers+text", 
                text=vc['Margen_Pct'].apply(lambda x: f"{x*100:.1f}%"),
                textposition="top center",
                line=dict(color='#10b981', width=3),
                hoverinfo='skip'
            ), secondary_y=True)
            
            fig_c.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                margin=dict(t=25, b=20, l=10, r=10),
                hovermode='closest'
            )
            st.plotly_chart(fig_c, use_container_width=True, config={'displayModeBar': False})
            
        with col_g_mix:
            st.markdown("<b>🍩 Mix de Venta <span style='font-size:0.75rem; color:#2563eb;'>(MARCA)</span></b>", unsafe_allow_html=True)
            
            df_marca = df_unicos.groupby('Marca').agg(
                Venta_Num=('Venta_Num', 'sum'),
                Margen_Num=('Margen_Num', 'sum'),
                SKUs_Marca=('COD REAL', 'nunique')
            ).reset_index().sort_values('Venta_Num', ascending=False).head(7)
            
            tot_vta_marcas = df_marca['Venta_Num'].sum()
            df_marca['Part_Venta'] = (df_marca['Venta_Num'] / tot_vta_marcas * 100) if tot_vta_marcas > 0 else 0
            df_marca['Margen_Pct'] = [(r['Margen_Num'] / r['Venta_Num'] * 100) if r['Venta_Num'] > 0 else 0 for _, r in df_marca.iterrows()]
            
            fig_pm = px.pie(
                df_marca, 
                values='Venta_Num', 
                names='Marca', 
                hole=0.55,
                custom_data=['Part_Venta', 'Margen_Num', 'Margen_Pct', 'SKUs_Marca']
            )
            fig_pm.update_traces(
                hovertemplate="<b>Marca: %{label}</b><br>💳 Venta: S/ %{value:,.2f} (%{customdata[0]:.1f}%)<br>📈 Margen: S/ %{customdata[1]:,.2f} (%{customdata[2]:.1f}%)<br>📦 SKUs: %{customdata[3]} productos<extra></extra>"
            )
            fig_pm.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_pm, use_container_width=True, config={'displayModeBar': False})

        # FAIR SHARE CON 3 BARRAS (% ESPACIO, % VENTAS, % MARGEN), ACTIVACIÓN CENTRAL Y CUERPOS OCUPADOS
        st.markdown("<hr style='border-color: #cbd5e1; margin: 14px 0;'>", unsafe_allow_html=True)
        st.markdown("<b>⚖️ Fair Share: Espacio (% Caras) vs % Ventas y % Margen</b>", unsafe_allow_html=True)
        
        df_cuerpos_por_cat = df_base.groupby('Categoría')['Cuerpo_Num'].apply(
            lambda s: (len(set(s.dropna())), ", ".join([f"C{int(c):02d}" for c in sorted(set(s.dropna()))]))
        ).reset_index()
        df_cuerpos_por_cat['Cant_Cuerpos'] = [x[0] for x in df_cuerpos_por_cat['Cuerpo_Num']]
        df_cuerpos_por_cat['Lista_Cuerpos'] = [x[1] for x in df_cuerpos_por_cat['Cuerpo_Num']]
        df_cuerpos_por_cat.drop(columns=['Cuerpo_Num'], inplace=True)

        df_esp_cat = df_base.groupby('Categoría').agg(Caras_Total=('Caras_Num', 'sum')).reset_index()
        df_fin_cat = df_unicos.groupby('Categoría').agg(
            Ventas_Total=('Venta_Num', 'sum'),
            Margen_Total=('Margen_Num', 'sum'),
            SKUs_Activos=('COD REAL', 'nunique')
        ).reset_index()
        
        df_fs = pd.merge(df_esp_cat, df_fin_cat, on='Categoría', how='outer').fillna(0)
        df_fs = pd.merge(df_fs, df_cuerpos_por_cat, on='Categoría', how='left').fillna(0)
        df_fs = df_fs[~df_fs['Categoría'].isin(['SIN DATOS', 'S/C', 'nan', ''])].copy()
        
        tot_caras = df_fs['Caras_Total'].sum()
        tot_vta = df_fs['Ventas_Total'].sum()
        tot_mgn = df_fs['Margen_Total'].sum()
        
        if tot_caras > 0 and tot_vta > 0:
            df_fs['Pct_Espacio'] = df_fs['Caras_Total'] / tot_caras
            df_fs['Pct_Ventas'] = df_fs['Ventas_Total'] / tot_vta
            df_fs['Pct_Margen'] = (df_fs['Margen_Total'] / tot_mgn) if tot_mgn > 0 else 0.0
            
            hover_template_fs = (
                "<b>%{x}</b><br>" +
                "🏬 <b>Ocupación:</b> %{customdata[6]} cuerpos (%{customdata[7]})<br><br>" +
                "📐 <b>Espacio (% Caras):</b> %{customdata[0]:.1f}% (%{customdata[1]} Caras)<br>" +
                "💰 <b>Ventas:</b> %{customdata[2]:.1f}% (S/ %{customdata[3]:,.2f})<br>" +
                "📈 <b>Margen:</b> %{customdata[4]:.1f}% (S/ %{customdata[5]:,.2f})<br>" +
                "📦 <b>SKUs Únicos:</b> %{customdata[8]} SKUs" +
                "<extra></extra>"
            )

            custom_data_matrix = df_fs[[
                'Pct_Espacio', 'Caras_Total', 'Pct_Ventas', 'Ventas_Total', 'Pct_Margen', 'Margen_Total',
                'Cant_Cuerpos', 'Lista_Cuerpos', 'SKUs_Activos'
            ]].copy()
            custom_data_matrix['Pct_Espacio'] = custom_data_matrix['Pct_Espacio'] * 100
            custom_data_matrix['Pct_Ventas'] = custom_data_matrix['Pct_Ventas'] * 100
            custom_data_matrix['Pct_Margen'] = custom_data_matrix['Pct_Margen'] * 100

            fig_fs = go.Figure()
            fig_fs.add_trace(go.Bar(
                x=df_fs['Categoría'], 
                y=df_fs['Pct_Espacio'], 
                name="% Caras (Espacio)",
                text=df_fs['Pct_Espacio'].apply(lambda x: f"{x*100:.1f}%"), 
                textposition='inside',
                marker_color='#2563eb',
                customdata=custom_data_matrix.values,
                hovertemplate=hover_template_fs
            ))
            fig_fs.add_trace(go.Bar(
                x=df_fs['Categoría'], 
                y=df_fs['Pct_Ventas'], 
                name="% Ventas (Monto S/)",
                text=df_fs['Pct_Ventas'].apply(lambda x: f"{x*100:.1f}%"), 
                textposition='inside',
                marker_color='#10b981',
                hoverinfo='skip'
            ))
            fig_fs.add_trace(go.Bar(
                x=df_fs['Categoría'], 
                y=df_fs['Pct_Margen'], 
                name="% Margen (Ganancia S/)",
                text=df_fs['Pct_Margen'].apply(lambda x: f"{x*100:.1f}%"), 
                textposition='inside',
                marker_color='#8b5cf6',
                hoverinfo='skip'
            ))
            
            fig_fs.update_layout(
                barmode='group', 
                hovermode='x',
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                margin=dict(t=20, b=20, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_fs, use_container_width=True, config={'displayModeBar': False})

        # TABLA DETALLE Y EXPORTADOR
        st.markdown("<hr style='border-color: #cbd5e1; margin: 14px 0;'>", unsafe_allow_html=True)
        col_dt_f, col_dt_dl = st.columns([4, 1.5])
        with col_dt_f:
            f_rep = st.selectbox("Filtrar Tabla Detallada:", ["Todos los SKUs", "Quiebres (Stock 0)", "Bloqueados (B)", "No está en planograma"], key="dash_det_f")
        with col_dt_dl:
            buffer = io.BytesIO()
            df_rep = df_sku_unico_global.copy()
            if f_rep == "Quiebres (Stock 0)":
                df_rep = df_rep[(df_rep['Estado'] == 'A') & (df_rep['Stock'] <= 0)]
            elif f_rep == "Bloqueados (B)":
                df_rep = df_rep[df_rep['Estado'] == 'B']
            elif f_rep == "No está en planograma":
                df_rep = df_rep[df_rep['Ubicación(es)'].isna() | (get_clean_series(df_rep, 'Ubicación(es)').str.strip() == "") | (get_clean_series(df_rep, 'Ubicación(es)').str.strip() == "SIN DATOS")]
            
            cols_s = [c for c in ['COD REAL', 'EAN', 'Descripción', 'Estado', 'Ubicación(es)', 'Categoría', 'Stock', 'Cobertura', 'Venta'] if c in df_rep.columns]
            cols_s = list(dict.fromkeys(cols_s))
            df_rep = df_rep.loc[:, ~df_rep.columns.duplicated()].copy()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_rep[cols_s].to_excel(writer, index=False, sheet_name='SKUs')
            st.markdown("<div style='margin-top:28px;'>", unsafe_allow_html=True)
            st.download_button("📥 Exportar Excel", buffer.getvalue(), "reporte_skus.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.dataframe(df_rep[cols_s], use_container_width=True, hide_index=True)

    # =========================================================================
    # --- PESTAÑA 4: ERRORES Y DESAJUSTES DE CRUCE ---
    # =========================================================================
    with tab_errores:
        st.markdown("<div style='font-size: 0.85rem; font-weight: 800; color: #2563eb; margin-bottom: 8px;'>⚠️ CONTROL DE INTEGRIDAD DE DATOS (DATOST)</div>", unsafe_allow_html=True)
        df_err = df_base[(df_base['Stock'] == -999.0) | (df_base['Venta'] == -999.0) | (df_base['Estado'] == 'SIN DATOS')].copy()
        st.metric("Total de Filas / SKUs con Incongruencias", df_err['COD REAL'].nunique() if not df_err.empty else 0)
        if len(df_err) > 0:
            cols_e = [c for c in ['COD REAL', 'EAN', 'Descripción', 'Bandeja', 'Stock', 'Venta', 'Estado'] if c in df_err.columns]
            cols_e = list(dict.fromkeys(cols_e))
            st.dataframe(df_err[cols_e], use_container_width=True, hide_index=True)
        else:
            st.success("🎉 ¡Excelente! No se detectaron desajustes de cruce en esta categoría.")
