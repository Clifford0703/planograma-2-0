import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import io
import re
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

# --- DESIGN SYSTEM / UI ---
t = {
    "bg_app": "#f4f7fb",
    "bg_surface": "#ffffff",
    "bg_card": "#ffffff",
    "border": "#d9e2ec",
    "border_subtle": "#e7edf4",
    "text_primary": "#172033",
    "text_secondary": "#344054",
    "text_muted": "#667085",
    "accent": "#155eef",
    "accent_soft": "#eef4ff",
    "success": "#16a34a",
    "warning": "#d97706",
    "danger": "#dc2626",
    "info": "#0284c7",
    "grid_color": "rgba(16, 24, 40, 0.06)",
    "card_shadow": "0 1px 2px rgba(16,24,40,.04), 0 4px 14px rgba(16,24,40,.04)",
}

# --- CSS GLOBAL / DESIGN TOKENS ---
st.markdown(f"""
<style>
    :root {{
        --bg-app: {t['bg_app']};
        --surface: {t['bg_surface']};
        --surface-muted: #f8fafc;
        --border: {t['border']};
        --border-subtle: {t['border_subtle']};
        --text-primary: {t['text_primary']};
        --text-secondary: {t['text_secondary']};
        --text-muted: {t['text_muted']};
        --primary: {t['accent']};
        --primary-soft: {t['accent_soft']};
        --success: {t['success']};
        --warning: {t['warning']};
        --danger: {t['danger']};
        --info: {t['info']};
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --shadow-card: {t['card_shadow']};
    }}

    html, body, .stApp, [data-testid="stAppViewContainer"], .main, section.main {{
        background: var(--bg-app) !important;
        color: var(--text-primary) !important;
        font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    }}

    header[data-testid="stHeader"] {{ background: transparent !important; }}
    .block-container {{
        padding: 1.15rem clamp(1rem, 2vw, 2.25rem) 2.5rem !important;
        max-width: 1600px !important;
    }}

    /* Controles nativos de Streamlit */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    textarea, input {{
        border-radius: 9px !important;
        border-color: var(--border) !important;
        background: var(--surface) !important;
    }}
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="input"] > div:focus-within,
    textarea:focus, input:focus {{
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(21,94,239,.10) !important;
    }}
    label[data-testid="stWidgetLabel"] p {{
        color: var(--text-secondary) !important;
        font-size: .76rem !important;
        font-weight: 700 !important;
        letter-spacing: .01em;
    }}

    /* Botones */
    .stButton > button {{
        border-radius: 9px !important;
        border: 1px solid var(--border) !important;
        font-weight: 700 !important;
        min-height: 38px !important;
        transition: all .16s ease !important;
    }}
    .stButton > button:hover {{
        border-color: #b8c7d9 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(16,24,40,.08) !important;
    }}
    .stButton > button[kind="primary"] {{
        background: var(--primary) !important;
        border-color: var(--primary) !important;
        color: #fff !important;
    }}

    /* Tabs: navegación sobria tipo producto SaaS */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 2px !important;
        background: #eef2f7 !important;
        padding: 4px !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 11px !important;
        margin: 8px 0 16px !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 38px !important;
        padding: 0 15px !important;
        border-radius: 8px !important;
        background: transparent !important;
        border: 0 !important;
        color: var(--text-muted) !important;
        font-size: .79rem !important;
        font-weight: 700 !important;
        transition: all .16s ease !important;
    }}
    .stTabs [data-baseweb="tab"] * {{ color: inherit !important; -webkit-text-fill-color: currentColor !important; }}
    .stTabs [data-baseweb="tab"]:hover {{ background: rgba(255,255,255,.72) !important; color: var(--text-primary) !important; }}
    .stTabs [aria-selected="true"], .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: #fff !important;
        color: var(--text-primary) !important;
        box-shadow: 0 1px 3px rgba(16,24,40,.10) !important;
    }}
    .stTabs [aria-selected="true"]::after {{ background: var(--primary) !important; height: 2px !important; }}

    /* Header */
    .app-header {{
        display:flex; align-items:center; justify-content:space-between; gap:20px;
        padding: 2px 0 18px; margin-bottom: 6px;
    }}
    .app-brand {{ display:flex; align-items:center; gap:12px; min-width:0; }}
    .app-logo {{
        width:42px; height:42px; border-radius:12px; display:grid; place-items:center;
        background: var(--primary-soft); color:var(--primary); font-size:20px;
        border:1px solid #d9e6ff;
    }}
    .app-title {{ font-size:1.22rem; line-height:1.15; font-weight:800; letter-spacing:-.02em; color:var(--text-primary); }}
    .app-subtitle {{ font-size:.76rem; color:var(--text-muted); margin-top:3px; font-weight:600; }}
    .app-context {{
        display:inline-flex; align-items:center; gap:6px; margin-left:8px;
        padding:4px 8px; border-radius:999px; background:#f2f6fb; border:1px solid var(--border-subtle);
        color:var(--text-secondary); font-size:.64rem; font-weight:800; letter-spacing:.04em;
    }}
    .app-meta {{ text-align:right; color:var(--text-muted); font-size:.68rem; line-height:1.45; }}
    .app-meta strong {{ color:var(--text-secondary); font-weight:700; }}

    /* Gate de filtros */
    .filter-shell {{
        background:var(--surface); border:1px solid var(--border-subtle); border-radius:var(--radius-md);
        padding:15px 16px 12px; margin:0 0 14px; box-shadow:var(--shadow-card);
    }}
    .section-eyebrow {{ color:var(--text-muted); font-size:.66rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; margin-bottom:4px; }}
    .section-title {{ color:var(--text-primary); font-size:.92rem; font-weight:800; margin-bottom:10px; }}
    .filter-context {{
        display:inline-flex; align-items:center; gap:6px; padding:5px 9px; margin-top:8px;
        background:var(--primary-soft); color:#174ea6; border:1px solid #dbe8ff; border-radius:999px;
        font-size:.69rem; font-weight:700;
    }}

    /* KPI cards */
    .fin-kpi-container {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:0 0 15px; }}
    .fin-kpi-card {{
        position:relative; background:var(--surface); border:1px solid var(--border-subtle); border-radius:var(--radius-md);
        padding:14px 16px; min-height:112px; box-shadow:var(--shadow-card); overflow:hidden;
        transition:transform .16s ease, box-shadow .16s ease, border-color .16s ease;
    }}
    .fin-kpi-card::before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:3px; background:var(--kpi-accent,var(--primary)); }}
    .fin-kpi-card:hover {{ transform:translateY(-2px); border-color:#d3ddea; box-shadow:0 8px 20px rgba(16,24,40,.07); }}
    .fin-kpi-title {{ display:flex; justify-content:space-between; gap:8px; color:var(--text-muted); font-size:.65rem; font-weight:800; letter-spacing:.07em; text-transform:uppercase; }}
    .fin-kpi-icon {{ width:24px; height:24px; border-radius:7px; display:grid; place-items:center; background:var(--primary-soft); color:var(--primary); font-size:.78rem; }}
    .fin-kpi-val {{ color:var(--text-primary); font-size:1.58rem; font-weight:800; line-height:1.15; letter-spacing:-.025em; margin:8px 0 4px; font-feature-settings:"tnum"; }}
    .fin-kpi-subtitle {{ color:var(--text-muted); font-size:.68rem; font-weight:600; line-height:1.35; }}

    .dash-card {{ background:var(--surface); border:1px solid var(--border-subtle); border-radius:var(--radius-md); padding:14px 16px; margin-bottom:12px; box-shadow:var(--shadow-card); }}
    .insight-box {{ border-radius:var(--radius-md); padding:13px 15px; line-height:1.5; font-size:.80rem; border:1px solid var(--border-subtle); box-shadow:var(--shadow-card); }}

    @media (max-width: 900px) {{
        .fin-kpi-container {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
        .app-header {{ align-items:flex-start; }}
        .app-meta {{ display:none; }}
    }}
    @media (max-width: 620px) {{
        .block-container {{ padding-left:.75rem !important; padding-right:.75rem !important; }}
        .fin-kpi-container {{ grid-template-columns:1fr; }}
        .app-context {{ display:none; }}
        .stTabs [data-baseweb="tab"] {{ padding:0 9px !important; font-size:.72rem !important; }}
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

        # 0. Cargar el Libro Maestro de Imágenes de Planogramas
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

        # 1. Matriz de Planos
        df_matriz = leer_tabla_por_ancla(url_planos, "COD REAL", sheet_target=0, skiprows_fallback=3)
        if "COD REAL" not in df_matriz.columns:
            df_matriz = pd.read_excel(url_planos, sheet_name=0, skiprows=2)
            df_matriz.columns = [str(c).strip() for c in df_matriz.columns]
            df_matriz = df_matriz.loc[:, ~df_matriz.columns.duplicated()].copy()

        df_matriz['COD_REAL_Str'] = get_clean_series(df_matriz, 'COD REAL').apply(clean_sku)
        df_matriz['COD REAL'] = df_matriz['COD_REAL_Str']

        if 'PASILLO' not in df_matriz.columns:
            df_matriz['PASILLO'] = "Pasillo 6"
        if 'LATERAL' not in df_matriz.columns:
            df_matriz['LATERAL'] = "Lateral A"

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

        # 6. Jerarquía Comercial SAP: MUNDO -> SECCIÓN (3)
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

        # Cruce seguro en df_pasillo_base
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

        for col, val_def in [('Mundo', 'DESAYUNO'), ('Estado', 'SIN DATOS'), ('Departamento', 'SIN DATOS'), ('Sección', 'SIN DATOS'), ('Categoría', 'SIN DATOS'), ('Grupo de Artículo', 'SIN DATOS'), ('G.A.', 'SIN DATOS'), ('Links de fotos', 'SIN DATOS'), ('Descripción', 'SIN DATOS'), ('EAN', 'SIN DATOS'), ('PASILLO', 'Pasillo 6'), ('LATERAL', 'Lateral A')]:
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

col_head1, col_head2, col_head3 = st.columns([6.4, 1.6, 2.0], vertical_alignment="center")
with col_head1:
    st.markdown("""
        <div class="app-header">
            <div class="app-brand">
                <div class="app-logo">⌘</div>
                <div>
                    <div class="app-title">Planograma <span style="color:var(--primary)">2.0</span>
                        <span class="app-context">CENCOSUD PERÚ</span>
                    </div>
                    <div class="app-subtitle">Retail Analytics · Planogram Management &amp; Store Execution</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
with col_head2:
    if st.button("↻  Actualizar", use_container_width=True, help="Volver a cargar las fuentes de datos"):
        st.cache_data.clear()
        st.rerun()
with col_head3:
    st.markdown(f"""
        <div class="app-meta">
            <div><strong>Desarrollado por Alfredo H.M.</strong></div>
            <div>Última sincronización · {info_hora if info_hora else 'En línea'}</div>
        </div>
    """, unsafe_allow_html=True)

if error_nube:
    st.warning(f"Aviso de conexión a la nube: {error_nube}")

# --- COMPUERTA DE BÚSQUEDA (ESTILO SHAREPOINT) ---
if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False

st.markdown("""
    <div class="filter-shell">
        <div class="section-eyebrow">Consulta de planograma</div>
        <div class="section-title">Selecciona el contexto que quieres analizar</div>
""", unsafe_allow_html=True)

col_b1, col_b2, col_b3, col_b4 = st.columns([2.5, 2.5, 3.5, 1.5])

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
    st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
    if st.button("🔍 Buscar", use_container_width=True, type="primary"):
        st.session_state.busqueda_activa = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# --- EVALUACIÓN DE LA COMPUERTA ---
if not st.session_state.busqueda_activa:
    st.info("Selecciona Tienda, Mundo y Categoría y pulsa **Buscar** para cargar el planograma y sus indicadores.")
else:
    df_base = df_pasillo_global.copy()
    
    if 'Mundo' in df_base.columns:
        df_base = df_base[df_base['Mundo'] == mundo_sel].copy()

    if cat_sel != "Todas las Categorías":
        df_base = df_base[df_base['Categoría'] == cat_sel].copy()

    df_base['Venta_Num'] = df_base['Venta'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0))
    df_base['Margen_Num'] = df_base['Monto Margen'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0))
    df_base['Part_Num'] = df_base['% Part'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0))
    df_base['Stock_Num'] = df_base['Stock'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0))
    df_base['Cob_Num'] = df_base['Cobertura'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0))
    df_base['Caras_Num'] = df_base['Caras'].apply(lambda x: safe_float(x, default=1.0))

    df_unicos = df_base.drop_duplicates(subset=['COD REAL']).copy()
    df_unicos = df_unicos[df_unicos['COD REAL'].astype(str).str.strip() != ""]

    # =========================================================================
    # --- TARJETAS KPIS FINANCIEROS (IMAGEN 2) ---
    # =========================================================================
    ventas_plano = df_unicos['Venta_Num'].sum()
    margen_bruto = df_unicos['Margen_Num'].sum()
    margen_global_pct = (margen_bruto / ventas_plano * 100) if ventas_plano > 0 else 0
    skus_en_plano = len(df_unicos)
    
    tot_vta_cat = df_sku_unico_global['Venta'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0)).sum()
    pct_vta_tot = (ventas_plano / tot_vta_cat * 100) if tot_vta_cat > 0 else 100.0
    tot_skus_cat = len(df_sku_unico_global)
    pct_skus_surtido = (skus_en_plano / tot_skus_cat * 100) if tot_skus_cat > 0 else 100.0

    st.markdown(f"""
        <div class="fin-kpi-container">
            <div class="fin-kpi-card" style="--kpi-accent:#155eef;">
                <div class="fin-kpi-title"><span>Ventas planograma</span><span class="fin-kpi-icon">↗</span></div>
                <div class="fin-kpi-val">S/ {ventas_plano:,.2f}</div>
                <div class="fin-kpi-subtitle">{pct_vta_tot:.1f}% de la venta total · S/ {tot_vta_cat:,.2f}</div>
            </div>
            <div class="fin-kpi-card" style="--kpi-accent:#16a34a;">
                <div class="fin-kpi-title"><span>Margen total bruto</span><span class="fin-kpi-icon" style="background:#ecfdf3;color:#16803b">%</span></div>
                <div class="fin-kpi-val">S/ {margen_bruto:,.2f}</div>
                <div class="fin-kpi-subtitle">Ganancia monetaria acumulada</div>
            </div>
            <div class="fin-kpi-card" style="--kpi-accent:#7c3aed;">
                <div class="fin-kpi-title"><span>Margen global</span><span class="fin-kpi-icon" style="background:#f3eefe;color:#6d28d9">◌</span></div>
                <div class="fin-kpi-val">{margen_global_pct:.1f}%</div>
                <div class="fin-kpi-subtitle">Rentabilidad sobre venta del planograma</div>
            </div>
            <div class="fin-kpi-card" style="--kpi-accent:#d97706;">
                <div class="fin-kpi-title"><span>SKUs en planograma</span><span class="fin-kpi-icon" style="background:#fff7ed;color:#c2410c">#</span></div>
                <div class="fin-kpi-val">{skus_en_plano}</div>
                <div class="fin-kpi-subtitle">{pct_skus_surtido:.1f}% del surtido · {tot_skus_cat} SKUs</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    tab_plano, tab_resumen, tab_dash, tab_errores = st.tabs([
        "Planograma",
        "Resumen ejecutivo",
        "Análisis financiero", 
        "Control de datos"
    ])

    # =========================================================================
    # --- PESTAÑA 1: PLANOGRAMA FÍSICO CON TARJETAS FILTRO OPERATIVAS (IMAGEN 1) ---
    # =========================================================================
    with tab_plano:
        cat_actual_titulo = cat_sel if cat_sel != "Todas las Categorías" else f"MUNDO {mundo_sel} - PLANOGRAMA INTEGRAL"
        
        # 1. IMAGEN DEL PLANOGRAMA ENMARCADA A ALTURA PANORÁMICA FIJA (260px)
        url_sheet_img = None
        cat_key_lookup = cat_actual_titulo.strip().upper()
        if cat_key_lookup in mapa_imagenes_online:
            url_sheet_img = mapa_imagenes_online[cat_key_lookup]
        else:
            for k, val in mapa_imagenes_online.items():
                if k in cat_key_lookup or cat_key_lookup in k:
                    url_sheet_img = val
                    break
        
        if url_sheet_img:
            st.markdown(f"""
                <div class="planograma-img-frame">
                    <img src="{url_sheet_img}" alt="Planograma Oficial {cat_actual_titulo}">
                </div>
            """, unsafe_allow_html=True)

        # 2. CÁLCULO DE MÉTRICAS PARA LAS TARJETAS OPERATIVAS (IMAGEN 1)
        tot_skus_op = len(df_unicos)
        bloq_op = len(df_unicos[df_unicos['Estado'].str.strip().str.upper() == 'B'])
        quiebre_op = len(df_unicos[(df_unicos['Estado'].str.strip().str.upper() == 'A') & (df_unicos['Stock_Num'] <= 0)])
        stk_bajo_op = len(df_unicos[(df_unicos['Estado'].str.strip().str.upper() == 'A') & (df_unicos['Stock_Num'] > 0) & (df_unicos['Stock_Num'] <= 5)])
        stk_ok_op = len(df_unicos[(df_unicos['Estado'].str.strip().str.upper() == 'A') & (df_unicos['Stock_Num'] > 5)])
        cob_alta_op = len(df_unicos[df_unicos['Cob_Num'] >= 30])
        
        # Cálculo de Top Ventas
        top_n_default = 5
        df_top_vta = df_unicos.sort_values(by='Venta_Num', ascending=False).head(top_n_default)
        monto_top_vta = df_top_vta['Venta_Num'].sum()
        pct_top_vta = (monto_top_vta / ventas_plano * 100) if ventas_plano > 0 else 0
        top_skus_set = set(df_top_vta['COD REAL'].astype(str).str.strip().unique())

        # 3. CONSTRUCCIÓN DE LA ESTRUCTURA DEL PLANOGRAMA PANORÁMICO
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
        categorias_unicas = sorted([c for c in df_base['Categoría'].dropna().unique() if str(c).strip() not in ['SIN DATOS', 'nan', '']])
        pasillos_unicos = sorted([p for p in df_base['PASILLO'].dropna().unique() if str(p).strip() not in ['SIN DATOS', 'nan', '']])
        laterales_unicos = sorted([l for l in df_base['LATERAL'].dropna().unique() if str(l).strip() not in ['SIN DATOS', 'nan', '']])

        options_marca = "".join([f"<option value='{m}'>{m}</option>" for m in marcas_unicas])
        options_cat = "".join([f"<option value='{c}'>{c}</option>" for c in categorias_unicas])
        options_pasillo = "".join([f"<option value='{p}'>{p}</option>" for p in pasillos_unicos])
        options_lateral = "".join([f"<option value='{l}'>{l}</option>" for l in laterales_unicos])

        niveles_reales = [x[1] for x in desglose]
        max_niveles_count = max(niveles_reales) if len(niveles_reales) > 0 else 8
        altura_cuerpo_px = max(260, max_niveles_count * 48)
        altura_iframe = altura_cuerpo_px + 290

        html_componente_completo = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
          <meta charset="UTF-8">
          <style>
            * {{ box-sizing:border-box; margin:0; padding:0; }}
            :root {{ --ink:#172033; --muted:#667085; --line:#d9e2ec; --line-soft:#e7edf4; --primary:#155eef; --surface:#fff; --canvas:#f8fafc; }}
            body {{ font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--canvas); color:var(--ink); padding:3px; width:100%; }}
            button,input,select {{ font:inherit; }}

            .top-ventas-bar {{ background:var(--surface); border:1px solid var(--line-soft); border-radius:12px; padding:10px 13px; display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:10px; box-shadow:0 1px 3px rgba(16,24,40,.04); }}
            .top-ventas-left {{ display:flex; align-items:center; gap:8px; font-size:.79rem; font-weight:750; color:var(--ink); }}
            .top-ventas-input {{ width:60px; padding:5px 7px; border:1px solid var(--line); border-radius:7px; text-align:center; font-weight:800; font-size:.82rem; color:var(--ink); background:#fff; outline:none; }}
            .top-ventas-input:focus {{ border-color:var(--primary); box-shadow:0 0 0 3px rgba(21,94,239,.10); }}
            .top-ventas-right {{ font-size:.77rem; font-weight:700; color:var(--muted); }}

            .filter-cards-grid {{ display:grid; grid-template-columns:repeat(7,minmax(0,1fr)); gap:7px; margin-bottom:10px; }}
            .card-btn {{ background:#fff; border:1px solid var(--line-soft); border-radius:10px; padding:9px 6px; text-align:center; cursor:pointer; transition:all .15s ease; box-shadow:0 1px 2px rgba(16,24,40,.03); user-select:none; }}
            .card-btn:hover {{ transform:translateY(-1px); border-color:#cbd6e2; box-shadow:0 5px 12px rgba(16,24,40,.07); }}
            .card-btn.active {{ border-color:#b8ccef !important; box-shadow:0 0 0 2px rgba(21,94,239,.12),0 5px 12px rgba(16,24,40,.07) !important; background:#f8fbff; }}
            .card-btn-title {{ font-size:.60rem; font-weight:800; color:var(--muted); text-transform:uppercase; margin-bottom:4px; letter-spacing:.04em; }}
            .card-btn-val {{ font-size:1.34rem; font-weight:800; line-height:1; }}
            .cb-total {{ border-left:3px solid #155eef; }} .cb-total .card-btn-val {{ color:#155eef; }}
            .cb-bloq {{ border-left:3px solid #dc2626; }} .cb-bloq .card-btn-val {{ color:#dc2626; }}
            .cb-sinstk {{ border-left:3px solid #ea580c; }} .cb-sinstk .card-btn-val {{ color:#ea580c; }}
            .cb-stkbajo {{ border-left:3px solid #d97706; }} .cb-stkbajo .card-btn-val {{ color:#b45309; }}
            .cb-stkok {{ border-left:3px solid #16a34a; }} .cb-stkok .card-btn-val {{ color:#15803d; }}
            .cb-cobalta {{ border-left:3px solid #c026d3; }} .cb-cobalta .card-btn-val {{ color:#a21caf; }}
            .cb-topvta {{ border-left:3px solid #7c3aed; }} .cb-topvta .card-btn-val {{ color:#6d28d9; }}

            .controls-panel {{ background:#fff; border:1px solid var(--line-soft); border-radius:12px; padding:10px 12px; margin-bottom:10px; box-shadow:0 1px 3px rgba(16,24,40,.04); }}
            .controls-row {{ display:grid; grid-template-columns:2.5fr 1.5fr 1.5fr 1.2fr 1.2fr; gap:8px; margin-bottom:9px; }}
            .ctrl-group {{ display:flex; flex-direction:column; gap:4px; }}
            .ctrl-label {{ font-size:.62rem; font-weight:800; color:var(--muted); text-transform:uppercase; display:flex; align-items:center; gap:4px; letter-spacing:.04em; }}
            .ctrl-input,.ctrl-select {{ width:100%; padding:7px 9px; border:1px solid var(--line); border-radius:8px; font-size:.76rem; font-weight:600; color:var(--ink); background:#fff; outline:none; }}
            .ctrl-input:focus,.ctrl-select:focus {{ border-color:var(--primary); box-shadow:0 0 0 3px rgba(21,94,239,.10); }}
            .buttons-actions-row {{ display:flex; justify-content:flex-end; gap:7px; align-items:center; }}
            .btn-act {{ padding:7px 11px; border-radius:8px; font-size:.72rem; font-weight:750; cursor:pointer; border:1px solid transparent; display:flex; align-items:center; gap:5px; transition:all .15s ease; }}
            .btn-act:hover {{ transform:translateY(-1px); }}
            .btn-fullscreen {{ background:#eef4ff; color:#174ea6; border-color:#d9e6ff; }}
            .btn-reset {{ background:#fff; color:#b42318; border-color:#f3d0cc; }}
            .btn-print {{ background:#f2faf5; color:#16703c; border-color:#d4eedf; }}

            .plano-outer-card {{ border:1px solid #cfd8e3; border-radius:12px; overflow:hidden; background:#fff; width:100%; box-shadow:0 2px 8px rgba(16,24,40,.05); }}
            .plano-top-header {{ background:#172033; color:#fff; font-size:.80rem; font-weight:800; text-align:left; padding:9px 13px; letter-spacing:.04em; text-transform:uppercase; border-bottom:1px solid #26334a; }}
            .plano-body-container {{ display:flex; flex-direction:row; width:100%; height:{altura_cuerpo_px}px; background:#f8fafc; }}
            .plano-cuerpo-col {{ display:flex; flex-direction:column; border-right:1px solid #cfd8e3; min-width:0; height:100%; }}
            .plano-cuerpo-col:last-child {{ border-right:none; }}
            .plano-cuerpo-shelves {{ display:flex; flex-direction:column; justify-content:space-between; padding:4px 3px; gap:3px; flex-grow:1; }}
            .plano-level-row {{ display:flex; flex-direction:column; justify-content:flex-end; flex:1; min-height:0; }}
            .plano-facings-container {{ display:flex; align-items:stretch; flex:1; min-height:0; overflow:hidden; gap:2px; padding:0 2px; }}
            .plano-shelf-bar {{ height:5px; background:linear-gradient(#8795a8,#5d6b7e); border-radius:2px; box-shadow:0 1px 0 rgba(0,0,0,.16); flex-shrink:0; }}
            .plano-rect {{ position:relative; flex:1 1 0; min-width:8px; height:100%; border:1px solid rgba(0,0,0,.16); border-radius:3px 3px 1px 1px; cursor:pointer; display:flex; align-items:center; justify-content:center; overflow:hidden; transition:opacity .15s ease,transform .15s ease,box-shadow .15s ease; }}
            .plano-rect:hover {{ transform:translateY(-2px); z-index:5; box-shadow:0 4px 10px rgba(16,24,40,.24); }}
            .plano-rect.dimmed {{ opacity:.12; filter:saturate(.4); }}
            .plano-rect.highlighted {{ box-shadow:0 0 0 2px #fff,0 0 0 4px var(--primary),0 5px 12px rgba(16,24,40,.18); z-index:6; }}
            .plano-sap-vertical {{ writing-mode:vertical-rl; transform:rotate(180deg); font-size:.52rem; font-weight:800; letter-spacing:.01em; white-space:nowrap; opacity:.88; user-select:none; }}
            .plano-cuerpo-footer {{ height:26px; display:flex; align-items:center; justify-content:center; background:#f1f5f9; color:#475467; font-size:.62rem; font-weight:800; border-top:1px solid #d9e2ec; letter-spacing:.04em; }}

            .modal-overlay {{ display:none; position:fixed; inset:0; background:rgba(15,23,42,.46); backdrop-filter:blur(3px); z-index:999; align-items:center; justify-content:center; padding:20px; }}
            .modal-overlay.active {{ display:flex; }}
            .modal-content {{ position:relative; width:min(520px,96vw); max-height:90vh; overflow:auto; background:#fff; border:1px solid #d9e2ec; border-radius:14px; padding:20px; box-shadow:0 24px 70px rgba(15,23,42,.24); }}
            .modal-content h4 {{ color:var(--ink); font-size:1rem; margin-bottom:12px; padding-bottom:10px; border-bottom:1px solid var(--line-soft); }}
            .modal-close {{ position:absolute; top:12px; right:14px; width:30px; height:30px; border-radius:8px; display:grid; place-items:center; cursor:pointer; color:#667085; font-size:1.25rem; font-weight:700; }}
            .modal-close:hover {{ background:#f2f4f7; color:#172033; }}
            .m-row {{ display:grid; grid-template-columns:150px 1fr; gap:12px; padding:8px 0; border-bottom:1px solid #f0f2f5; font-size:.74rem; }}
            .m-label {{ color:#667085; font-weight:650; }} .m-val {{ color:#172033; font-weight:750; overflow-wrap:anywhere; }}
            @media(max-width:850px){{ .filter-cards-grid{{grid-template-columns:repeat(4,minmax(0,1fr));}}.controls-row{{grid-template-columns:1fr 1fr;}} .top-ventas-bar{{align-items:flex-start;flex-direction:column;}} }}
            @media(max-width:560px){{ .filter-cards-grid{{grid-template-columns:repeat(2,minmax(0,1fr));}}.controls-row{{grid-template-columns:1fr;}}.buttons-actions-row{{flex-wrap:wrap;}}.m-row{{grid-template-columns:1fr;}} }}
          </style>
        </head>
        <body id="planoContainer">

          <!-- 1. FRANJA RESALTAR TOP VENTAS -->
          <div class="top-ventas-bar">
            <div class="top-ventas-left">
                <span>🏆 RESALTAR TOP VENTAS:</span>
                <input type="number" id="inputTopVentas" class="top-ventas-input" value="{top_n_default}" min="1" max="50">
                <span style="color: #2563eb;">SKUs</span>
            </div>
            <div class="top-ventas-right" id="labelTopInfo">
                TOP {top_n_default} concentra el <span style="color: #16a34a;">{pct_top_vta:.1f}%</span> de la venta (S/ {monto_top_vta:,.2f}).
            </div>
          </div>

          <!-- 2. TARJETAS FILTRO OPERATIVAS (IMAGEN 1) -->
          <div class="filter-cards-grid">
            <div class="card-btn cb-total active" data-filter="TOTAL">
                <div class="card-btn-title">TOTAL SKUS</div>
                <div class="card-btn-val">{tot_skus_op}</div>
            </div>
            <div class="card-btn cb-bloq" data-filter="BLOQUEADOS">
                <div class="card-btn-title">BLOQUEADOS</div>
                <div class="card-btn-val">{bloq_op}</div>
            </div>
            <div class="card-btn cb-sinstk" data-filter="SIN_STOCK">
                <div class="card-btn-title">SIN STOCK (0)</div>
                <div class="card-btn-val">{quiebre_op}</div>
            </div>
            <div class="card-btn cb-stkbajo" data-filter="STOCK_BAJO">
                <div class="card-btn-title">STOCK BAJO (1-5)</div>
                <div class="card-btn-val">{stk_bajo_op}</div>
            </div>
            <div class="card-btn cb-stkok" data-filter="STOCK_OK">
                <div class="card-btn-title">STOCK OK (>5)</div>
                <div class="card-btn-val">{stk_ok_op}</div>
            </div>
            <div class="card-btn cb-cobalta" data-filter="COB_ALTA">
                <div class="card-btn-title">COB. ALTA (≥30)</div>
                <div class="card-btn-val">{cob_alta_op}</div>
            </div>
            <div class="card-btn cb-topvta" data-filter="TOP_VENTAS">
                <div class="card-btn-title">★ TOP VENTAS</div>
                <div class="card-btn-val">{top_n_default}</div>
            </div>
          </div>

          <!-- 3. CONTROLES Y BUSCADOR (IMAGEN 1) -->
          <div class="controls-panel">
            <div class="controls-row">
                <div class="ctrl-group">
                    <span class="ctrl-label">🔍 BUSCAR PRODUCTO</span>
                    <input type="text" id="busqNombre" class="ctrl-input" placeholder="Nombre o EAN...">
                </div>
                <div class="ctrl-group">
                    <span class="ctrl-label">🏷️ MARCA</span>
                    <select id="selMarca" class="ctrl-select">
                        <option value="Todas">Todas</option>
                        {options_marca}
                    </select>
                </div>
                <div class="ctrl-group">
                    <span class="ctrl-label">📁 CATEGORÍA</span>
                    <select id="selCat" class="ctrl-select">
                        <option value="Todas">Todas</option>
                        {options_cat}
                    </select>
                </div>
                <div class="ctrl-group">
                    <span class="ctrl-label">📦 PASILLO</span>
                    <select id="selPasillo" class="ctrl-select">
                        <option value="Todos">Todos</option>
                        {options_pasillo}
                    </select>
                </div>
                <div class="ctrl-group">
                    <span class="ctrl-label">📊 LATERAL</span>
                    <select id="selLateral" class="ctrl-select">
                        <option value="Todos">Todos</option>
                        {options_lateral}
                    </select>
                </div>
            </div>
            <div class="buttons-actions-row">
                <button type="button" class="btn-act btn-fullscreen" id="btnFullscreen">⛶ Pantalla Completa</button>
                <button type="button" class="btn-act btn-reset" id="btnResetAll">Restablecer</button>
                <button type="button" class="btn-act btn-print" onclick="window.print()">🖨️ Imprimir</button>
            </div>
          </div>

          <!-- 4. PLANOGRAMA FÍSICO PANORÁMICO -->
          <div class="plano-outer-card" id="planoCard">
            <div class="plano-top-header">{cat_actual_titulo}</div>
            <div class="plano-body-container">
                {html_cuerpos}
            </div>
          </div>

          <!-- MODAL DE AUDITORÍA -->
          <div id="pModal" class="modal-overlay">
            <div class="modal-content">
              <span class="modal-close">&times;</span>
              <h4 id="m-name" style="margin-bottom: 8px; color: #0f172a; border-bottom: 2px solid #2563eb; padding-bottom: 6px;">Producto</h4>
              <div class="m-row"><span class="m-label">Código SAP / Cód. Real:</span><span class="m-val" id="m-cod" style="font-family: monospace; font-size: 0.95rem; font-weight: 900;"></span></div>
              <div class="m-row"><span class="m-label">Ubicación (Nivel / Pos):</span><span class="m-val" id="m-pos"></span></div>
              <div class="m-row"><span class="m-label">EAN:</span><span class="m-val" id="m-ean"></span></div>
              <div class="m-row"><span class="m-label">Marca:</span><span class="m-val" id="m-brand"></span></div>
              <div class="m-row"><span class="m-label">Categoría:</span><span class="m-val" id="m-catjer"></span></div>
              <div class="m-row"><span class="m-label">Stock Actual:</span><span class="m-val" id="m-stock"></span></div>
              <div class="m-row"><span class="m-label">Cobertura:</span><span class="m-val" id="m-cob"></span></div>
              <div class="m-row"><span class="m-label">Estado Stock:</span><span class="m-val" id="m-cat"></span></div>
              <div class="m-row"><span class="m-label">Ventas:</span><span class="m-val" id="m-venta"></span></div>
            </div>
          </div>

          <script>
            let activeFilterType = 'TOTAL';
            const cardButtons = document.querySelectorAll('.card-btn');
            const rects = document.querySelectorAll('.plano-rect');
            const busqInput = document.getElementById('busqNombre');
            const selMarca = document.getElementById('selMarca');
            const selCat = document.getElementById('selCat');

            function aplicarFiltrosGlobales() {{
                const q = busqInput.value.toLowerCase().trim();
                const m = selMarca.value;
                const c = selCat.value;

                rects.forEach(r => {{
                    const estado = r.getAttribute('data-estado');
                    const cobAlta = r.getAttribute('data-cobalta') === '1';
                    const topVta = r.getAttribute('data-topvta') === '1';
                    const name = (r.getAttribute('data-name') || '').toLowerCase();
                    const ean = (r.getAttribute('data-ean') || '').toLowerCase();
                    const cod = (r.getAttribute('data-cod') || '').toLowerCase();
                    const brand = r.getAttribute('data-brand') || '';
                    const cat = r.getAttribute('data-catjer') || '';

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

                    let matchMarca = (m === 'Todas' || brand === m);
                    let matchCat = (c === 'Todas' || cat === c);

                    if (matchTipo && matchText && matchMarca && matchCat) {{
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

            cardButtons.forEach(btn => {{
                btn.addEventListener('click', () => {{
                    cardButtons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    activeFilterType = btn.getAttribute('data-filter');
                    aplicarFiltrosGlobales();
                }});
            }});

            busqInput.addEventListener('input', aplicarFiltrosGlobales);
            selMarca.addEventListener('change', aplicarFiltrosGlobales);
            selCat.addEventListener('change', aplicarFiltrosGlobales);

            document.getElementById('btnResetAll').addEventListener('click', () => {{
                activeFilterType = 'TOTAL';
                cardButtons.forEach(b => b.classList.remove('active'));
                document.querySelector('.cb-total').classList.add('active');
                busqInput.value = '';
                selMarca.value = 'Todas';
                selCat.value = 'Todas';
                aplicarFiltrosGlobales();
            }});

            // PANTALLA COMPLETA
            document.getElementById('btnFullscreen').addEventListener('click', () => {{
                const elem = document.getElementById('planoCard');
                if (!document.fullscreenElement) {{
                    elem.requestFullscreen().catch(err => {{
                        alert("No se pudo iniciar el modo pantalla completa.");
                    }});
                }} else {{
                    document.exitFullscreen();
                }}
            }});

            // MODAL DE DETALLE
            const modal = document.getElementById('pModal');
            const closeBtn = document.querySelector('.modal-close');
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
                    modal.classList.add('active');
                }});
            }});
            closeBtn.addEventListener('click', () => modal.classList.remove('active'));
            window.addEventListener('click', (e) => {{ if(e.target === modal) modal.classList.remove('active'); }});
          </script>
        </body>
        </html>
        """
        components.html(html_componente_completo, height=altura_iframe, scrolling=True)

    # =========================================================================
    # --- PESTAÑA 2: RESUMEN EJECUTIVO (GERENCIA DE OPERACIONES) ---
    # =========================================================================
    with tab_resumen:
        quiebres_df = df_unicos[(df_unicos['Estado'].str.strip().str.upper() == 'A') & (df_unicos['Stock_Num'] <= 0)]
        tot_quiebres = len(quiebres_df)
        pct_quiebres = (tot_quiebres / skus_en_plano * 100) if skus_en_plano > 0 else 0
        osa_pct = 100.0 - pct_quiebres
        bloqueados_df = df_unicos[df_unicos['Estado'].str.strip().str.upper() == 'B']
        tot_bloqueados = len(bloqueados_df)
        venta_en_riesgo = quiebres_df['Venta_Num'].sum()
        
        df_no_plano = df_sku_unico_global[
            df_sku_unico_global['Ubicación(es)'].isna() | 
            (get_clean_series(df_sku_unico_global, 'Ubicación(es)').str.strip() == "") | 
            (get_clean_series(df_sku_unico_global, 'Ubicación(es)').str.strip() == "SIN DATOS")
        ].copy()
        tot_no_plano = len(df_no_plano)
        ventas_no_plano = df_no_plano['Venta'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0)).sum()

        c_a1, c_a2 = st.columns(2)
        with c_a1:
            st.markdown(f"""
                <div class="insight-box" style="background-color: #fee2e2; border-left: 4px solid #dc2626; color: #991b1b;">
                    <b>🚨 Venta en Riesgo por Quiebres: S/ {venta_en_riesgo:,.2f}</b><br>
                    Hay <b>{tot_quiebres} SKUs con Stock 0</b> en repisa ({pct_quiebres:.1f}% del surtido) que detienen ventas directas.
                </div>
            """, unsafe_allow_html=True)
        with c_a2:
            st.markdown(f"""
                <div class="insight-box" style="background-color: #ffedd5; border-left: 4px solid #ea580c; color: #9a3412;">
                    <b>⚠️ Venta Fuera de Planograma: S/ {ventas_no_plano:,.2f}</b><br>
                    Existen <b>{tot_no_plano} SKUs vendidos</b> sin ubicación asignada en el plano.
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        col_g1, col_g2 = st.columns([6.2, 3.8])
        with col_g1:
            st.markdown("<b>🔥 Quiebres por Categoría vs % Participación de Ventas</b>", unsafe_allow_html=True)
            st.markdown('<div class="dash-card">', unsafe_allow_html=True)
            ventas_por_cat = df_unicos.groupby('Categoría')['Venta_Num'].sum()
            total_vta_unicos = ventas_por_cat.sum()
            quiebres_por_cat = quiebres_df.groupby('Categoría')['COD REAL'].count()
            
            df_cat_ops = pd.DataFrame({'Quiebres': quiebres_por_cat, 'Venta': ventas_por_cat}).fillna(0).reset_index()
            df_cat_ops = df_cat_ops[~df_cat_ops['Categoría'].isin(['SIN DATOS', 'S/C', 'nan', ''])].copy()
            df_cat_ops['Part_Venta'] = (df_cat_ops['Venta'] / total_vta_unicos) if total_vta_unicos > 0 else 0
            df_cat_ops = df_cat_ops.sort_values(by=['Quiebres', 'Part_Venta'], ascending=[False, False]).head(8)
            
            fig_ops = make_subplots(specs=[[{"secondary_y": True}]])
            fig_ops.add_trace(go.Bar(
                x=df_cat_ops['Categoría'], y=df_cat_ops['Quiebres'], name="Quiebres (Stock 0)",
                text=df_cat_ops['Quiebres'].apply(lambda x: f"{int(x)} Q"), textposition='inside',
                marker=dict(color='#dc2626')
            ), secondary_y=False)
            fig_ops.add_trace(go.Scatter(
                x=df_cat_ops['Categoría'], y=df_cat_ops['Part_Venta'], name="% Participación Venta",
                mode="lines+markers+text", text=df_cat_ops['Part_Venta'].apply(lambda x: f"{x*100:.1f}%"),
                textposition='top center', line=dict(color='#2563eb', width=3)
            ), secondary_y=True)
            fig_ops.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=20, l=10, r=10))
            st.plotly_chart(fig_ops, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_g2:
            st.markdown("<b>🎯 Salud del Stock en Góndola</b>", unsafe_allow_html=True)
            st.markdown('<div class="dash-card">', unsafe_allow_html=True)
            def get_h(r):
                if str(r['Estado']).strip().upper() == 'B': return 'Bloqueado (B)'
                elif r['Stock_Num'] <= 0: return 'Quiebre (0)'
                elif r['Stock_Num'] <= 5: return 'Alerta Baja (1-5)'
                else: return 'Stock OK (>5)'
            df_unicos['H_Estado'] = df_unicos.apply(get_h, axis=1)
            dh = df_unicos['H_Estado'].value_counts().reset_index()
            dh.columns = ['Estado', 'Cant']
            fig_pie_h = px.pie(dh, values='Cant', names='Estado', hole=0.55, 
                               color='Estado', color_discrete_map={'Stock OK (>5)':'#16a34a', 'Alerta Baja (1-5)':'#facc15', 'Quiebre (0)':'#ea580c', 'Bloqueado (B)':'#dc2626'})
            fig_pie_h.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10), showlegend=True)
            st.plotly_chart(fig_pie_h, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

    # =========================================================================
    # --- PESTAÑA 3: DASHBOARD ANALÍTICO FINANCIERO ---
    # =========================================================================
    with tab_dash:
        st.markdown("<div style='font-size: 0.85rem; font-weight: 800; color: #2563eb; margin-bottom: 8px;'>🎯 ANÁLISIS DE RENTABILIDAD Y FAIR SHARE</div>", unsafe_allow_html=True)
        col_g_cuerpos, col_g_mix = st.columns([7, 3])
        with col_g_cuerpos:
            st.markdown("<b>Rendimiento por Cuerpo (Ventas vs Margen)</b>", unsafe_allow_html=True)
            bandeja_series = get_clean_series(df_base, 'Bandeja')
            df_base['Cuerpo_Num'] = [desglosar_cuerpo_y_nivel(v)[0] for v in bandeja_series]
            
            vc = df_base.drop_duplicates(subset=['COD REAL', 'Cuerpo_Num']).groupby('Cuerpo_Num').agg(
                Venta_Total=('Venta_Num', 'sum'),
                Margen_Total=('Margen_Num', 'sum'),
                SKUs=('COD REAL', 'count')
            ).reset_index()
            vc['Margen_Pct'] = [r['Margen_Total']/r['Venta_Total'] if r['Venta_Total']>0 else 0 for _, r in vc.iterrows()]
            vc['Label'] = [f"Cuerpo {int(r['Cuerpo_Num']):02d}" for _, r in vc.iterrows()]
            
            fig_c = make_subplots(specs=[[{"secondary_y": True}]])
            fig_c.add_trace(go.Bar(x=vc['Label'], y=vc['Venta_Total'], name="Venta (S/)", marker_color='#2563eb'), secondary_y=False)
            fig_c.add_trace(go.Scatter(x=vc['Label'], y=vc['Margen_Pct'], name="Margen %", mode="lines+markers", line=dict(color='#16a34a', width=3)), secondary_y=True)
            fig_c.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=20, l=10, r=10))
            st.plotly_chart(fig_c, use_container_width=True, config={'displayModeBar': False})
            
        with col_g_mix:
            st.markdown("<b>Mix de Venta por Marca</b>", unsafe_allow_html=True)
            df_marca = df_unicos.groupby('Marca')['Venta_Num'].sum().reset_index().sort_values('Venta_Num', ascending=False).head(6)
            fig_pm = px.pie(df_marca, values='Venta_Num', names='Marca', hole=0.55)
            fig_pm.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_pm, use_container_width=True, config={'displayModeBar': False})

        # FAIR SHARE
        st.markdown("<hr style='border-color: #cbd5e1; margin: 12px 0;'>", unsafe_allow_html=True)
        st.markdown("<b>⚖️ Fair Share: Espacio (% Caras) vs % Ventas y Margen</b>", unsafe_allow_html=True)
        df_esp_cat = df_base.groupby('Categoría').agg(Caras_Total=('Caras_Num', 'sum')).reset_index()
        df_fin_cat = df_unicos.groupby('Categoría').agg(
            Ventas_Total=('Venta_Num', 'sum'),
            Margen_Total=('Margen_Num', 'sum'),
            SKUs_Activos=('COD REAL', 'count')
        ).reset_index()
        
        df_fs = pd.merge(df_esp_cat, df_fin_cat, on='Categoría', how='outer').fillna(0)
        df_fs = df_fs[~df_fs['Categoría'].isin(['SIN DATOS', 'S/C', 'nan', ''])].copy()
        
        tot_caras = df_fs['Caras_Total'].sum()
        tot_vta = df_fs['Ventas_Total'].sum()
        
        if tot_caras > 0 and tot_vta > 0:
            df_fs['Pct_Espacio'] = df_fs['Caras_Total'] / tot_caras
            df_fs['Pct_Ventas'] = df_fs['Ventas_Total'] / tot_vta
            fig_fs = go.Figure()
            fig_fs.add_trace(go.Bar(
                x=df_fs['Categoría'], y=df_fs['Pct_Espacio'], name="% Caras (Espacio)",
                text=df_fs['Pct_Espacio'].apply(lambda x: f"{x*100:.1f}%"), textposition='inside',
                marker_color='#2563eb'
            ))
            fig_fs.add_trace(go.Bar(
                x=df_fs['Categoría'], y=df_fs['Pct_Ventas'], name="% Ventas (Monto S/)",
                text=df_fs['Pct_Ventas'].apply(lambda x: f"{x*100:.1f}%"), textposition='inside',
                marker_color='#16a34a'
            ))
            fig_fs.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=20, l=10, r=10))
            st.plotly_chart(fig_fs, use_container_width=True, config={'displayModeBar': False})

        # TABLA DETALLE Y EXPORTADOR
        st.markdown("<hr style='border-color: #cbd5e1; margin: 12px 0;'>", unsafe_allow_html=True)
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
        st.markdown("<div style='font-size: 0.85rem; font-weight: 800; color: #2563eb; margin-bottom: 8px;'>⚠️ CONTROL DE INTEGRIDAD DE DATOS</div>", unsafe_allow_html=True)
        df_err = df_base[(df_base['Stock'] == -999.0) | (df_base['Venta'] == -999.0) | (df_base['Estado'] == 'SIN DATOS')].copy()
        st.metric("Total de Filas / SKUs con Incongruencias", len(df_err))
        if len(df_err) > 0:
            cols_e = [c for c in ['COD REAL', 'EAN', 'Descripción', 'Bandeja', 'Stock', 'Venta', 'Estado'] if c in df_err.columns]
            cols_e = list(dict.fromkeys(cols_e))
            st.dataframe(df_err[cols_e], use_container_width=True, hide_index=True)
        else:
            st.success("🎉 ¡Excelente! No se detectaron desajustes de cruce en esta categoría.")
