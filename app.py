import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import io
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

# --- GESTIÓN DE TEMA GLOBAL (LIGHT / DARK) ---
if "tema_actual" not in st.session_state:
    st.session_state.tema_actual = "dark"

es_oscuro = st.session_state.tema_actual == "dark"

# --- DESIGN SYSTEM VARIABLES ---
theme_vars = {
    "dark": {
        "bg_app": "#070d19",
        "bg_surface": "#0f172a",
        "bg_card": "#111c30",
        "border": "#1e3a8a",
        "border_subtle": "#1e293b",
        "text_primary": "#ffffff",
        "text_secondary": "#93c5fd",
        "text_muted": "#64748b",
        "accent": "#3b82f6",
        "accent_green": "#10b981",
        "accent_purple": "#8b5cf6",
        "accent_amber": "#fbbf24",
        "grid_color": "rgba(255, 255, 255, 0.08)",
        "card_shadow": "0 4px 10px rgba(0,0,0,0.4)",
        "plotly_text": "#cbd5e1",
    },
    "light": {
        "bg_app": "#f8fafc",
        "bg_surface": "#ffffff",
        "bg_card": "#ffffff",
        "border": "#3b82f6",
        "border_subtle": "#e2e8f0",
        "text_primary": "#0f172a",
        "text_secondary": "#2563eb",
        "text_muted": "#64748b",
        "accent": "#2563eb",
        "accent_green": "#059669",
        "accent_purple": "#7c3aed",
        "accent_amber": "#d97706",
        "grid_color": "rgba(0, 0, 0, 0.06)",
        "card_shadow": "0 2px 6px rgba(0,0,0,0.05)",
        "plotly_text": "#334155",
    }
}
t = theme_vars[st.session_state.tema_actual]

# INYECCIÓN CSS FORZADA (CONTROL TOTAL DEL TEMA EN STREAMLIT)
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
        
        .stApp, [data-testid="stAppViewContainer"], .main, section.main, [data-testid="stHeader"] {{
            background-color: {t["bg_app"]} !important;
            background: {t["bg_app"]} !important;
            color: {t["text_primary"]} !important;
            font-family: 'Inter', sans-serif !important;
        }}
        
        header[data-testid="stHeader"] {{
            background-color: transparent !important;
        }}
        
        .block-container {{
            padding-left: 1.2rem !important;
            padding-right: 1.2rem !important;
            padding-top: 1rem !important;
            padding-bottom: 1.5rem !important;
            max-width: 100% !important;
        }}
        
        /* HEADER SAAS */
        .saas-header-box {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: {t["bg_card"]};
            border: 1px solid {t["border_subtle"]};
            border-radius: 8px;
            padding: 12px 18px;
            margin-bottom: 12px;
            box-shadow: {t["card_shadow"]};
        }}
        
        /* TARJETAS KPIS DEL DASHBOARD */
        .fin-kpi-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
            margin-bottom: 14px;
        }}
        
        .fin-kpi-card {{
            background: {t["bg_card"]};
            border: 1px solid {t["border_subtle"]};
            border-radius: 8px;
            padding: 14px 18px;
            box-shadow: {t["card_shadow"]};
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        .fin-kpi-card:hover {{
            border-color: {t["accent"]};
            transform: translateY(-2px);
        }}
        
        .fin-kpi-title {{
            font-size: 0.68rem;
            font-weight: 800;
            color: {t["text_secondary"]};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .fin-kpi-val {{
            font-size: 1.85rem;
            font-weight: 900;
            color: {t["text_primary"]};
            line-height: 1.1;
            font-feature-settings: "tnum";
            margin-bottom: 4px;
        }}

        .fin-kpi-subtitle {{
            font-size: 0.72rem;
            font-weight: 600;
            color: {t["text_muted"]};
        }}
        
        /* CONTENEDORES DE GRÁFICOS Y FAIR SHARE */
        .dash-card {{
            background: {t["bg_card"]};
            border: 1px solid {t["border_subtle"]};
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 12px;
            box-shadow: {t["card_shadow"]};
        }}
        
        .dash-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            padding-bottom: 6px;
            border-bottom: 1px solid {t["border_subtle"]};
        }}
        
        .dash-card-title {{
            font-size: 0.85rem;
            font-weight: 800;
            color: {t["text_primary"]};
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        /* SELECTBOXES Y WIDGETS EN MODO CLARO/OSCURO */
        .stSelectbox label, .stRadio label {{
            color: {t["text_primary"]} !important;
            font-weight: 700 !important;
            font-size: 0.80rem !important;
        }}
        
        /* PESTAÑAS (TABS) */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: {t["bg_card"]};
            padding: 6px;
            border-radius: 8px;
            border: 1px solid {t["border_subtle"]};
            margin-bottom: 12px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            height: 36px;
            padding: 0 18px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.84rem;
            color: {t["text_muted"]};
            background-color: transparent;
            border: none !important;
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: {t["accent"]} !important;
            color: #ffffff !important;
        }}
    </style>
""", unsafe_allow_html=True)

# --- FUNCIONES AUXILIARES ---
def safe_float(val, default=0.0):
    if pd.isna(val): return default
    try:
        if isinstance(val, str):
            val = val.replace('%', '').replace(',', '').strip()
        return float(val)
    except (ValueError, TypeError):
        return default

def format_pct(val):
    return f"{val*100:.2f}%" if val < 1 else f"{val:.2f}%"

def clean_sku(val):
    if pd.isna(val): return ""
    s = str(val).strip()
    if s.endswith('.0'): s = s[:-2]
    return s

def obtener_estado_y_color(estado, stock_val, dark=True):
    estado = str(estado).strip().upper()
    if estado == "B": 
        bg = "#451a1a" if dark else "#fee2e2"
        border = "#7f1d1d" if dark else "#fca5a5"
        tc = "#fca5a5" if dark else "#991b1b"
        name_c = "#fecaca" if dark else "#7f1d1d"
        return bg, border, tc, name_c, "Bloqueado"
    elif estado == "A":
        if stock_val <= 0: 
            bg = "#431407" if dark else "#ffedd5"
            border = "#7c2d12" if dark else "#fdba74"
            tc = "#fdba74" if dark else "#9a3412"
            name_c = "#ffedd5" if dark else "#7c2d12"
            return bg, border, tc, name_c, "Sin Stock"
        elif stock_val <= 5: 
            bg = "#422006" if dark else "#fef9c3"
            border = "#713f12" if dark else "#fde047"
            tc = "#fde047" if dark else "#854d0e"
            name_c = "#fef08a" if dark else "#713f12"
            return bg, border, tc, name_c, "Stock Bajo"
        else: 
            bg = "#064e3b" if dark else "#dcfce7"
            border = "#065f46" if dark else "#86efac"
            tc = "#6ee7b7" if dark else "#166534"
            name_c = "#ecfdf5" if dark else "#14532d"
            return bg, border, tc, name_c, "Stock OK"
    else: 
        bg = "#1e293b" if dark else "#f1f5f9"
        border = "#334155" if dark else "#cbd5e1"
        tc = "#94a3b8" if dark else "#475569"
        name_c = "#f8fafc" if dark else "#0f172a"
        return bg, border, tc, name_c, "Desconocido"

def obtener_alerta_css(estado, stock_val):
    estado = str(estado).strip().upper()
    if estado == "B": return "alerta-bloqueado", "Bloqueado"
    elif estado == "A":
        if stock_val <= 0: return "alerta-sinstock", "Sin Stock"
        elif stock_val <= 5: return "alerta-stockbajo", "Stock Bajo"
        else: return "alerta-ok", "Stock OK"
    else: return "alerta-desconocido", "Desconocido"

# --- GENERADOR DEL PLANOGRAMA ---
def generar_html_pasillo_interactivo(df, es_realograma=False, es_oscuro=True):
    df = df.copy()
    df['FilaOriginal'] = range(len(df))
    df['TieneOrden'] = pd.to_numeric(df.get('N° ORDEN', pd.Series([None]*len(df))), errors='coerce').notna()
    df['NumOrden'] = pd.to_numeric(df.get('N° ORDEN', pd.Series([None]*len(df))), errors='coerce').fillna(999999)
    
    bandeja_str = df.get('Bandeja', pd.Series(["1.1"]*len(df))).astype(str)
    df[['Cuerpo_Ord', 'Nivel_Ord']] = bandeja_str.str.extract(r'(\d+)\.(\d+)')
    df['Cuerpo_Ord'] = pd.to_numeric(df['Cuerpo_Ord'], errors='coerce').fillna(1)
    df['Nivel_Ord'] = pd.to_numeric(df['Nivel_Ord'], errors='coerce').fillna(1)

    df = df.sort_values(
        by=['Cuerpo_Ord', 'Nivel_Ord', 'TieneOrden', 'NumOrden', 'FilaOriginal'], 
        ascending=[True, False, False, True, True]
    )

    cuerpos = {}
    todas_marcas = sorted(list(df["Marca"].dropna().unique())) if "Marca" in df.columns else []
    todas_categorias = sorted(list(df["Categoría"].dropna().unique())) if "Categoría" in df.columns else []
    todos_niveles = sorted(list(df["Nivel_Ord"].dropna().unique()), reverse=True)

    for _, r in df.iterrows():
        b_str = str(r.get("Bandeja", "1.1")).strip()
        cuerpo_id = f"Cuerpo {b_str.split('.')[0]}" if "." in b_str else "Cuerpo 1"
        if cuerpo_id not in cuerpos: cuerpos[cuerpo_id] = {}
        if b_str not in cuerpos[cuerpo_id]: cuerpos[cuerpo_id][b_str] = []
        cuerpos[cuerpo_id][b_str].append(r)

    html_cuerpos = ""
    for cuerpo_nombre, niveles_dict in sorted(cuerpos.items()):
        cuerpo_num = cuerpo_nombre.replace("Cuerpo ", "").strip()
        niveles_ordenados = sorted(niveles_dict.keys(), reverse=True)
        html_niveles = ""
        
        todos_items_cuerpo = [it for sublist in niveles_dict.values() for it in sublist]
        cats_cuerpo = [str(it.get('Categoría', '')) for it in todos_items_cuerpo if str(it.get('Categoría', '')) not in ['', 'S/C', 'nan']]
        cat_predominante = max(set(cats_cuerpo), key=cats_cuerpo.count) if cats_cuerpo else ""

        for b_nombre in niveles_ordenados:
            items = niveles_dict[b_nombre]
            total_caras = sum([int(it.get("Caras", 1)) if str(it.get("Caras", 1)).isdigit() else 1 for it in items])
            nivel_num = b_nombre.split(".")[-1] if "." in b_nombre else "1"

            cards_html = ""
            for it in items:
                cod_real = str(it.get("COD REAL", ""))
                ean = str(it.get("EAN", ""))
                nombre = str(it.get("Descripción", it.get("Nombre", "")))
                marca = str(it.get("Marca", "S/M"))
                estado = str(it.get("Estado", ""))
                
                caras_val = str(it.get("Caras", "1"))
                caras = int(caras_val) if caras_val.isdigit() and int(caras_val) > 0 else 1
                pos = str(it.get("N°", "-")) if not pd.isna(it.get("N°", "-")) else "-"

                stock_val = safe_float(it.get("Stock", 0))
                cob_val = safe_float(it.get("Cobertura", 0))
                venta_val = safe_float(it.get("Venta", 0))
                part_val = safe_float(it.get("% Part", 0))
                
                dept_val = str(it.get("Departamento", "S/D")).replace('"', '&quot;')
                sec_val = str(it.get("Sección", "S/S")).replace('"', '&quot;')
                catjer_val = str(it.get("Categoría", "S/C")).replace('"', '&quot;')
                ga_val = str(it.get("Grupo de artículo", "S/G")).replace('"', '&quot;')
                
                part_fmt = format_pct(part_val)
                stock_fmt = f"{stock_val:.2f}"
                cob_fmt = f"{cob_val:.2f}"
                estilo_cobertura = "color: #ef4444; font-weight: 800;" if cob_val >= 30 else ""
                
                if es_realograma:
                    link_foto = str(it.get("Links de fotos", ""))
                    if link_foto in ['nan', '', 'None']:
                        link_foto = "https://via.placeholder.com/60x150.png/1e293b/94a3b8?text=Sin+Foto"
                    else:
                        link_foto = link_foto.replace("http://", "https://")
                    
                    clase_alerta, cat_leyenda = obtener_alerta_css(estado, stock_val)
                    img_tags = "".join([f'<img src="{link_foto}" alt="{marca}">' for _ in range(caras)])
                    
                    html_interno = f"""
                      <div class="top-badge"></div>
                      <div class="sku-images-wrapper">{img_tags}</div>
                      <div class="sku-fleje">
                        <span class="fleje-ean">{ean}</span>
                        <span class="fleje-caras">{caras}C</span>
                      </div>
                    """
                    clase_wrapper = f"sku-item sku-group {clase_alerta}"
                    estilo_wrapper = ""
                else:
                    bg_color, border_color, text_color, name_color, cat_leyenda = obtener_estado_y_color(estado, stock_val, dark=es_oscuro)
                    
                    html_interno = f"""
                      <div class="sku-header-row">
                        <span class="sku-pos" style="color: {text_color}; font-weight: 800;">{pos}</span>
                        <span class="sku-caras-tag" style="color: {text_color}; background: rgba(0,0,0,0.25); border: 1px solid {text_color}44;">{caras}C</span>
                      </div>
                      <div class="sku-details">
                        <span class="sku-brand-text" style="color: {text_color};">{marca}</span>
                        <span class="sku-name-text" style="color: {name_color};">{nombre}</span>
                      </div>
                      <div class="sku-bottom-bar" style="border-top: 1px dashed {border_color};">
                        <span class="sku-stock-pill" style="color: {text_color}; font-weight: 800;">Stk: {stock_fmt}</span>
                        <span class="sku-cap-val" style="{estilo_cobertura}">Cob: {cob_fmt}</span>
                      </div>
                    """
                    clase_wrapper = "sku-item sku-card"
                    estilo_wrapper = f"flex: {caras}; background-color: {bg_color}; border: 1.5px solid {border_color};"

                cards_html += f"""
                <div class="{clase_wrapper}" style="{estilo_wrapper}" 
                     data-brand="{marca}" data-name="{nombre}" data-ean="{ean}"
                     data-stock="{stock_fmt}" data-cob="{cob_fmt}" data-venta="{venta_val}" data-part="{part_fmt}" 
                     data-cod="{cod_real}" data-cat="{cat_leyenda}" 
                     data-dept="{dept_val}" data-sec="{sec_val}" data-catjer="{catjer_val}" data-ga="{ga_val}"
                     title="Detalles: {nombre}">
                  {html_interno}
                </div>
                """

            if es_realograma:
                shelf_render = f"""
                  <div class="shelf-products">{cards_html}</div>
                  <div class="shelf-base"><span class="shelf-name-tag">NIVEL {nivel_num} • {total_caras} CARAS</span></div>
                """
            else:
                shelf_render = f"""
                  <div class="shelf-info"><span>NIVEL {nivel_num}</span><span class="shelf-caras-count">{total_caras} CARAS</span></div>
                  <div class="shelf-products">{cards_html}</div>
                  <div class="shelf-bottom-rail"></div>
                """

            html_niveles += f"""
            <div class="shelf-row" data-level="{nivel_num}">
              {shelf_render}
            </div>
            """

        subtitulo_cat = f'<span class="bay-subcat">{cat_predominante}</span>' if cat_predominante else ''

        html_cuerpos += f"""
        <div class="bay-column" data-module="{cuerpo_num}">
          <div class="bay-title">
            <span class="bay-main-title">{cuerpo_nombre.upper()}</span>
            {subtitulo_cat}
          </div>
          <div class="bay-shelves">
            {html_niveles}
          </div>
        </div>
        """

    options_marcas = "".join([f'<option value="{m}">{m}</option>' for m in todas_marcas])
    options_categorias = "".join([f'<option value="{c}">{c}</option>' for c in todas_categorias if c not in ['S/C', 'nan', '']])
    options_cuerpos = "".join([f'<option value="{k.replace("Cuerpo ", "")}">{k}</option>' for k in cuerpos.keys()])
    options_niveles = "".join([f'<option value="{int(lvl)}">Nivel {int(lvl)}</option>' for lvl in todos_niveles])

    app_bg = t["bg_app"]
    surface_bg = t["bg_surface"]
    card_bg = t["bg_card"]
    border_col = t["border_subtle"]
    text_primary = t["text_primary"]
    text_secondary = t["text_secondary"]
    input_bg = t["bg_card"]

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
        * {{ box-sizing: border-box; }}
        
        body, html {{ 
          font-family: 'Inter', sans-serif; 
          background-color: {app_bg}; 
          color: {text_primary}; 
          margin: 0; 
          padding: 0; 
          height: 100vh; 
          overflow: hidden; 
        }}
        
        .main-container {{ 
          padding: 4px 6px; 
          height: 100vh; 
          display: flex; 
          flex-direction: column; 
          box-sizing: border-box;
          overflow: hidden;
        }}

        ::-webkit-scrollbar {{ height: 6px; width: 6px; }}
        ::-webkit-scrollbar-track {{ background: {card_bg}; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb {{ background: #3b82f6; border-radius: 4px; }}

        .saas-top-bar {{
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: {card_bg};
          border: 1px solid {border_col};
          border-radius: 8px;
          padding: 8px 14px;
          margin-bottom: 8px;
          flex-shrink: 0;
        }}
        
        .top-highlight-badge {{
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.78rem;
          font-weight: 700;
          color: {text_primary};
        }}

        .kpi-container {{ 
          display: flex; 
          gap: 8px; 
          margin-bottom: 8px; 
          flex-wrap: wrap; 
          justify-content: space-between; 
          flex-shrink: 0; 
        }}
        .kpi-card {{ 
          flex: 1; 
          min-width: 100px; 
          background: {card_bg}; 
          border: 1px solid {border_col}; 
          border-radius: 8px; 
          padding: 8px 12px; 
          text-align: left; 
          box-shadow: {t["card_shadow"]}; 
        }}
        .kpi-title {{ font-size: 0.62rem; font-weight: 700; color: {text_secondary}; text-transform: uppercase; margin-bottom: 2px; letter-spacing: 0.5px; }}
        .kpi-val {{ font-size: 1.35rem; font-weight: 900; line-height: 1.1; color: {text_primary}; font-feature-settings: "tnum"; }}
        
        .filter-panel {{ 
          background: {card_bg}; 
          border: 1px solid {border_col}; 
          border-radius: 8px; 
          padding: 8px 12px; 
          margin-bottom: 8px; 
          display: flex; 
          flex-wrap: wrap; 
          gap: 8px; 
          align-items: flex-end; 
          flex-shrink: 0; 
        }}
        .filter-group {{ display: flex; flex-direction: column; gap: 3px; flex-grow: 1; }}
        .filter-label {{ font-size: 0.65rem; font-weight: 700; color: {text_secondary}; text-transform: uppercase; }}
        .filter-select, .filter-input {{ 
          background: {input_bg}; 
          border: 1px solid {border_col}; 
          color: {text_primary}; 
          padding: 6px 10px; 
          border-radius: 6px; 
          font-size: 0.80rem; 
          font-weight: 500; 
          outline: none; 
          width: 100%; 
          min-width: 120px; 
          transition: border-color 0.2s;
        }}
        .filter-select:focus, .filter-input:focus {{ border-color: #3b82f6; }}
        .btn-group {{ display: flex; gap: 6px; margin-left: auto; flex-wrap: wrap; align-items: center; }}
        
        .btn-saas {{ 
          border: none; 
          font-weight: 700; 
          font-size: 0.75rem; 
          padding: 7px 14px; 
          border-radius: 6px; 
          cursor: pointer; 
          transition: all 0.2s ease; 
          display: flex;
          align-items: center;
          gap: 4px;
        }}
        .btn-reset {{ background: #ef44441a; color: #ef4444; border: 1px solid #ef444433; }}
        .btn-reset:hover {{ background: #ef4444; color: #fff; }}
        .btn-print {{ background: #10b9811a; color: #10b981; border: 1px solid #10b98133; }}
        .btn-print:hover {{ background: #10b981; color: #fff; }}
        .btn-fullscreen {{ background: #3b82f61a; color: #3b82f6; border: 1px solid #3b82f633; }}
        .btn-fullscreen:hover {{ background: #3b82f6; color: #fff; }}
        
        .legend-panel {{ 
          background: {card_bg}; 
          border: 1px solid {border_col}; 
          border-radius: 8px; 
          padding: 6px 12px; 
          margin-bottom: 8px; 
          display: flex; 
          align-items: center; 
          flex-wrap: wrap; 
          gap: 8px; 
          flex-shrink: 0; 
        }}
        .legend-title {{ font-size: 0.68rem; font-weight: 700; color: {text_secondary}; text-transform: uppercase; margin-right: 4px; }}
        .legend-chips {{ display: flex; flex-wrap: wrap; gap: 6px; }}
        .legend-chip {{ 
          background: var(--bg); 
          color: var(--tc); 
          border: var(--bd, 1px solid transparent); 
          font-weight: 700; 
          font-size: 0.65rem; 
          padding: 4px 10px; 
          border-radius: 20px; 
          cursor: pointer; 
          transition: all 0.15s ease; 
          opacity: 0.90; 
          outline: none; 
        }}
        .legend-chip.active {{ opacity: 1; transform: scale(1.04); box-shadow: 0 0 0 2px #3b82f6 !important; }}
        
        .aisle-wrapper {{ 
          display: flex;
          flex-direction: column;
          width: 100%; 
          position: relative; 
          flex: 1;
          min-height: 0;
          background: {card_bg};
          border-radius: 10px;
          border: 1px solid {border_col};
          padding: 0;
          overflow: hidden;
        }}

        .fullscreen-legend-bar {{
          display: none;
          position: sticky;
          top: 0;
          left: 0;
          right: 0;
          background: {card_bg};
          border-bottom: 1px solid {border_col};
          padding: 12px 20px;
          z-index: 10000;
          backdrop-filter: blur(8px);
          align-items: center;
          gap: 12px;
          overflow-x: auto;
          white-space: nowrap;
        }}
        
        .fs-cat-wrapper {{
          display: flex;
          align-items: center;
          gap: 8px;
          margin-left: auto;
        }}
        .fs-cat-select {{
          background: {input_bg};
          border: 1px solid {border_col};
          color: {text_primary};
          padding: 5px 10px;
          border-radius: 6px;
          font-size: 0.80rem;
          font-weight: 600;
          outline: none;
        }}
        
        .aisle-wrapper:fullscreen, .aisle-wrapper:-webkit-full-screen {{
          background: {app_bg} !important;
          width: 100vw !important;
          height: 100vh !important;
          padding: 0 !important;
          border: none !important;
        }}
        .aisle-wrapper:fullscreen .fullscreen-legend-bar, 
        .aisle-wrapper:-webkit-full-screen .fullscreen-legend-bar {{
          display: flex !important;
        }}

        .nav-btn {{ 
          position: absolute;
          top: 50%;
          transform: translateY(-50%);
          background: {card_bg}; 
          color: {text_primary}; 
          border: 1px solid {border_col}; 
          border-radius: 50%; 
          width: 40px; 
          height: 40px;
          font-size: 1.2rem; 
          font-weight: 700; 
          cursor: pointer; 
          z-index: 100; 
          display: flex; 
          align-items: center; 
          justify-content: center; 
          box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
          transition: all 0.2s;
        }}
        .nav-btn:hover {{ background: {t["accent"]}; color: #ffffff; border-color: {t["accent"]}; transform: translateY(-50%) scale(1.08); }}
        .nav-btn-prev {{ left: 10px; }}
        .nav-btn-next {{ right: 10px; }}
        .nav-btn:disabled {{ opacity: 0; pointer-events: none; }}
        
        .zoom-layer {{
          display: flex;
          width: 100%;
          height: 100%;
          transform-origin: 50% 0;
          will-change: transform;
          justify-content: center;
          align-items: stretch;
          transition: transform 0.2s ease-out;
        }}

        .aisle-container {{ 
          display: flex; 
          flex-direction: row; 
          gap: 16px; 
          background: {app_bg}; 
          padding: 14px 45px; 
          overflow-x: auto; 
          overflow-y: auto; 
          scroll-behavior: smooth; 
          scroll-snap-type: x mandatory; 
          width: 100%; 
          height: 100%;
          box-sizing: border-box;
        }}
        
        .bay-column {{ 
          flex: 0 0 100%; 
          width: 100%; 
          background: {card_bg}; 
          border: 1px solid {border_col}; 
          border-radius: 8px; 
          display: flex; 
          flex-direction: column; 
          height: fit-content; 
          scroll-snap-align: center; 
          padding-bottom: 12px; 
          box-sizing: border-box;
          box-shadow: {t["card_shadow"]};
        }}
        .bay-column.hidden {{ display: none !important; }}
        
        .bay-title {{ 
          background: {card_bg}; 
          padding: 10px 14px; 
          border-bottom: 1px solid {border_col}; 
          border-radius: 8px 8px 0 0; 
          display: flex; 
          justify-content: space-between; 
          align-items: center; 
          flex-shrink: 0; 
        }}
        .bay-main-title {{ font-size: 0.82rem; font-weight: 800; color: {text_primary}; letter-spacing: 0.5px; }}
        .bay-subcat {{ font-size: 0.70rem; font-weight: 600; color: #3b82f6; text-transform: uppercase; }}
        
        .bay-shelves {{ padding: 12px; display: flex; flex-direction: column; gap: 14px; flex-grow: 1; }}
        .shelf-row {{ display: flex; flex-direction: column; position: relative; padding-top: 4px; }}
        .shelf-row.hidden {{ display: none !important; }}
        
        .shelf-products {{ display: flex; flex-direction: row; gap: 6px; padding: 4px 6px; min-height: 95px; overflow-x: auto; padding-bottom: 4px; align-items: flex-end; justify-content: flex-start; }}
        .sku-item.dimmed {{ opacity: 0.15; filter: grayscale(1); }}
        .sku-item.highlighted {{ transform: scale(1.02); z-index: 20; }}
        
        .shelf-base {{ height: 8px; background: linear-gradient(180deg, #f59e0b 0%, #d97706 100%); border-radius: 2px; position: relative; z-index: 5; margin-top: -2px; }}
        .shelf-name-tag {{ position: absolute; top: 6px; background: {card_bg}; border: 1px solid {border_col}; color: {text_primary}; font-size: 0.52rem; padding: 1px 6px; border-radius: 4px; font-weight: 800; }}
        
        .sku-group {{ display: flex; flex-direction: column; align-items: center; position: relative; cursor: pointer; transition: all 0.2s; z-index: 10; padding: 0 2px; flex-shrink: 0; }}
        .sku-images-wrapper {{ display: flex; flex-direction: row; align-items: flex-end; gap: 1px; }}
        .sku-images-wrapper img {{ height: 85px; width: auto; max-width: 55px; object-fit: contain; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.15)); transition: transform 0.2s; }}
        .sku-group:hover .sku-images-wrapper img {{ transform: translateY(-3px); }}
        
        .sku-fleje {{ background: {card_bg}; color: {text_primary}; border: 1px solid {border_col}; font-size: 0.48rem; display: flex; flex-direction: column; align-items: center; line-height: 1; margin-top: 2px; z-index: 15; box-shadow: 0 1px 3px rgba(0,0,0,0.1); width: max-content; padding: 1px 4px; border-radius: 2px; }}
        .fleje-ean {{ font-weight: 600; font-family: monospace; }}
        .fleje-caras {{ font-weight: 800; color: #3b82f6; }}
        
        .alerta-bloqueado .sku-images-wrapper img {{ filter: grayscale(100%) opacity(0.4); }}
        .alerta-sinstock .sku-images-wrapper img {{ filter: drop-shadow(0 0 8px #ef4444); }}
        .alerta-stockbajo .sku-images-wrapper img {{ filter: drop-shadow(0 0 6px #f59e0b); }}
        .sku-group.is-top .top-badge::after {{ content: '⭐'; position: absolute; top: -14px; right: -4px; font-size: 1rem; }}
        
        /* BLOQUES DE PRODUCTOS */
        .sku-card {{ 
          border-radius: 6px; 
          padding: 6px; 
          display: flex; 
          flex-direction: column; 
          justify-content: space-between; 
          min-width: 95px; 
          position: relative; 
          transition: transform 0.15s ease, box-shadow 0.15s ease; 
          cursor: pointer; 
          align-items: stretch; 
          flex-shrink: 0; 
          box-shadow: 0 1px 3px rgba(0,0,0,0.15);
        }}
        .sku-card:hover {{
          transform: translateY(-2px);
          box-shadow: 0 4px 10px rgba(0,0,0,0.25);
        }}
        .sku-card.is-top {{ outline: 2.5px solid #f59e0b !important; outline-offset: -1px; }}
        .sku-header-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }}
        .sku-pos {{ font-size: 0.60rem; font-weight: 900; }}
        .sku-caras-tag {{ font-size: 0.55rem; font-weight: 800; padding: 1px 4px; border-radius: 4px; }}
        
        .sku-details {{ display: flex; flex-direction: column; gap: 2px; text-align: left; overflow: hidden; margin-bottom: 6px; }}
        .sku-brand-text {{ font-size: 0.62rem; font-weight: 900; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; letter-spacing: 0.3px; }}
        .sku-name-text {{ font-size: 0.66rem; font-weight: 700; line-height: 1.15; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
        
        .sku-bottom-bar {{ display: flex; justify-content: space-between; align-items: center; gap: 4px; padding-top: 3px; }}
        .sku-stock-pill {{ font-size: 0.58rem; }}
        .sku-cap-val {{ font-size: 0.60rem; font-weight: 800; }}
        
        .shelf-bottom-rail {{ height: 4px; background: {border_col}; border-radius: 0 0 2px 2px; }}
        .shelf-info {{ background: {card_bg}; border-left: 3px solid #3b82f6; padding: 3px 8px; font-size: 0.65rem; font-weight: 700; display: flex; justify-content: space-between; color: {text_primary}; }}
        
        /* MODAL OVERLAY */
        .modal-overlay {{ 
          position: fixed !important; 
          inset: 0 !important;
          width: 100vw !important;
          height: 100vh !important;
          background: rgba(0,0,0,0.65) !important; 
          z-index: 9999999 !important; 
          opacity: 0; 
          pointer-events: none; 
          transition: opacity 0.2s ease; 
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
          padding: 16px !important;
          backdrop-filter: blur(6px);
        }}
        .modal-overlay.active {{ opacity: 1 !important; pointer-events: auto !important; }}
        .modal-content {{ 
          background: {card_bg} !important; 
          color: {text_primary} !important; 
          padding: 24px !important; 
          border-radius: 12px !important; 
          width: 90% !important; 
          max-width: 440px !important; 
          max-height: 85vh !important; 
          overflow-y: auto !important; 
          border: 1px solid {border_col} !important; 
          box-shadow: 0 20px 40px rgba(0,0,0,0.3) !important; 
          position: relative !important;
        }}
        .modal-close {{ position: absolute; top: 12px; right: 16px; font-size: 1.5rem; cursor: pointer; color: {text_secondary}; font-weight: 700; }}
        .modal-close:hover {{ color: {text_primary}; }}
        .m-row {{ border-bottom: 1px solid {border_col}; padding: 8px 0; display: flex; justify-content: space-between; font-size: 0.82rem; }}
        .m-label {{ font-weight: 600; color: {text_secondary}; }}
        .m-val {{ font-weight: 700; text-align: right; max-width: 65%; font-feature-settings: "tnum"; }}

        @media (max-width: 768px) {{
            .nav-btn {{ display: none !important; }}
            .aisle-container {{ padding: 8px 4px !important; touch-action: pan-x pan-y !important; }}
            .kpi-container {{ display: grid !important; grid-template-columns: repeat(2, 1fr) !important; gap: 6px !important; }}
            .kpi-card {{ min-width: unset !important; }}
            .kpi-card:last-child {{ grid-column: 1 / -1 !important; }}
            .bay-column {{ flex: 0 0 100% !important; width: 100% !important; max-width: 100% !important; scroll-snap-align: center !important; }}
            .shelf-products {{ min-height: 70px !important; }}
            .sku-card {{ min-width: 75px !important; }}
            .sku-images-wrapper img {{ height: 70px !important; max-width: 40px !important; }}
        }}
      </style>
    </head>
    <body>
      <div class="main-container" id="mainContainer">

        <!-- MODAL GLOBAL -->
        <div id="productModal" class="modal-overlay">
          <div class="modal-content" id="modalContent">
            <span class="modal-close">&times;</span>
            <h3 id="m-name" style="margin-top: 0; font-size: 1.05rem; font-weight: 800; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; line-height: 1.3;">Producto</h3>
            <div class="m-row"><span class="m-label">Cód. Real:</span><span class="m-val" id="m-cod" style="font-family: monospace;"></span></div>
            <div class="m-row"><span class="m-label">EAN:</span><span class="m-val" id="m-ean" style="font-family: monospace;"></span></div>
            <div class="m-row"><span class="m-label">Marca:</span><span class="m-val" id="m-brand"></span></div>
            <div class="m-row"><span class="m-label">Departamento:</span><span class="m-val" id="m-dept"></span></div>
            <div class="m-row"><span class="m-label">Sección:</span><span class="m-val" id="m-sec"></span></div>
            <div class="m-row"><span class="m-label">Categoría:</span><span class="m-val" id="m-catjer"></span></div>
            <div class="m-row"><span class="m-label">Grupo Artículo:</span><span class="m-val" id="m-ga"></span></div>
            <div class="m-row"><span class="m-label">Stock Actual:</span><span class="m-val" id="m-stock"></span></div>
            <div class="m-row"><span class="m-label">Cobertura:</span><span class="m-val" id="m-cob"></span></div>
            <div class="m-row"><span class="m-label">Ventas:</span><span class="m-val" id="m-venta"></span></div>
            <div class="m-row" style="border-bottom: none;"><span class="m-label" style="color: #f59e0b; font-weight: 700;">★ TOP Ventas:</span><span class="m-val" id="m-top" style="color: #f59e0b; font-weight: 800;"></span></div>
          </div>
        </div>

        <div class="saas-top-bar">
          <div class="top-highlight-badge">
              <span>🏆</span>
              <span style="font-size: 0.75rem; text-transform: uppercase;">Resaltar TOP Ventas:</span>
              <input type="number" id="topNInput" value="5" min="1" max="500" class="filter-input" style="width: 55px; padding: 3px 6px; font-weight: bold; font-size: 0.8rem; text-align: center;">
              <span style="color: {text_secondary}; font-size: 0.75rem;">SKUs</span>
          </div>
          <div id="topNInfo" style="color: {text_secondary}; font-size: 0.78rem; font-weight: 500;">
              Calculando concentración...
          </div>
        </div>

        <!-- TARJETAS KPIS -->
        <div class="kpi-container">
          <div class="kpi-card" style="border-left: 3px solid #3b82f6;"><span class="kpi-title">Total SKUs</span><span class="kpi-val" id="t-total">0</span></div>
          <div class="kpi-card" style="border-left: 3px solid #ef4444;"><span class="kpi-title">Bloqueados</span><span class="kpi-val" id="t-bloq" style="color: #ef4444;">0</span></div>
          <div class="kpi-card" style="border-left: 3px solid #f97316;"><span class="kpi-title">Sin Stock (0)</span><span class="kpi-val" id="t-sin" style="color: #f97316;">0</span></div>
          <div class="kpi-card" style="border-left: 3px solid #eab308;"><span class="kpi-title">Stock Bajo (1-5)</span><span class="kpi-val" id="t-bajo" style="color: #eab308;">0</span></div>
          <div class="kpi-card" style="border-left: 3px solid #10b981;"><span class="kpi-title">Stock OK (>5)</span><span class="kpi-val" id="t-ok" style="color: #10b981;">0</span></div>
          <div class="kpi-card" style="border-left: 3px solid #ec4899;"><span class="kpi-title">Cob. Alta (≥30)</span><span class="kpi-val" id="t-cob" style="color: #ec4899;">0</span></div>
          <div class="kpi-card" style="border-left: 3px solid #f59e0b;"><span class="kpi-title">★ Top Ventas</span><span class="kpi-val" id="t-top" style="color: #f59e0b;">0</span></div>
        </div>

        <div class="filter-panel">
          <div class="filter-group"><span class="filter-label">🔍 Buscar Producto</span><input type="text" id="searchInput" class="filter-input" placeholder="Nombre o EAN..."></div>
          <div class="filter-group"><span class="filter-label">🏷️ Marca</span><select id="brandSelect" class="filter-select"><option value="ALL">Todas</option>{options_marcas}</select></div>
          <div class="filter-group"><span class="filter-label">📂 Categoría</span><select id="catSelect" class="filter-select"><option value="ALL">Todas</option>{options_categorias}</select></div>
          <div class="filter-group"><span class="filter-label">📦 Cuerpo</span><select id="baySelect" class="filter-select"><option value="ALL">Todos</option>{options_cuerpos}</select></div>
          <div class="filter-group"><span class="filter-label">📶 Nivel</span><select id="levelSelect" class="filter-select"><option value="ALL">Todos</option>{options_niveles}</select></div>
          <div class="btn-group">
            <button id="fullscreenBtn" class="btn-saas btn-fullscreen" title="Pantalla Completa">⛶ Pantalla Completa</button>
            <button id="resetBtn" class="btn-saas btn-reset">Restablecer</button>
            <button type="button" id="printBayBtn" class="btn-saas btn-print">🖨️ Imprimir</button>
          </div>
        </div>

        <div class="legend-panel">
          <span class="legend-title">📍 Leyenda:</span>
          <div class="legend-chips">
            <button class="legend-chip" data-filter="Bloqueado" style="--bg: {'#451a1a' if es_oscuro else '#fee2e2'}; --tc: {'#fca5a5' if es_oscuro else '#991b1b'}; --bd: 1px solid {'#7f1d1d' if es_oscuro else '#fca5a5'};">Bloqueado</button>
            <button class="legend-chip" data-filter="Sin Stock" style="--bg: {'#431407' if es_oscuro else '#ffedd5'}; --tc: {'#fdba74' if es_oscuro else '#9a3412'}; --bd: 1px solid {'#7c2d12' if es_oscuro else '#fdba74'};">Sin Stock</button>
            <button class="legend-chip" data-filter="Stock Bajo" style="--bg: {'#422006' if es_oscuro else '#fef9c3'}; --tc: {'#fde047' if es_oscuro else '#854d0e'}; --bd: 1px solid {'#713f12' if es_oscuro else '#fde047'};">Stock 1 a 5</button>
            <button class="legend-chip" data-filter="Stock OK" style="--bg: {'#064e3b' if es_oscuro else '#dcfce7'}; --tc: {'#6ee7b7' if es_oscuro else '#166534'}; --bd: 1px solid {'#065f46' if es_oscuro else '#86efac'};">Stock > 5</button>
            <button class="legend-chip" data-filter="cob-alta" style="--bg: {'#1e293b' if es_oscuro else '#ffffff'}; --tc: #ef4444; --bd: 1px solid #ef4444;">Cob ≥ 30</button>
            <button class="legend-chip" data-filter="top-ventas" style="--bg: {'#422006' if es_oscuro else '#fef3c7'}; --tc: #d97706; --bd: 1px solid #f59e0b;">★ TOP VENTAS</button>
          </div>
        </div>

        <!-- CONTENEDOR CON SCROLL Y MODAL INTEGRADO -->
        <div class="aisle-wrapper" id="aisleWrapper">
          <div class="fullscreen-legend-bar">
            <span style="font-size: 0.80rem; font-weight: 800; color: #3b82f6;">📍 LEYENDA:</span>
            <div class="legend-chips">
              <button class="legend-chip" data-filter="Bloqueado" style="--bg: {'#451a1a' if es_oscuro else '#fee2e2'}; --tc: {'#fca5a5' if es_oscuro else '#991b1b'};">Bloqueado</button>
              <button class="legend-chip" data-filter="Sin Stock" style="--bg: {'#431407' if es_oscuro else '#ffedd5'}; --tc: {'#fdba74' if es_oscuro else '#9a3412'};">Sin Stock</button>
              <button class="legend-chip" data-filter="Stock Bajo" style="--bg: {'#422006' if es_oscuro else '#fef9c3'}; --tc: {'#fde047' if es_oscuro else '#854d0e'};">Stock 1-5</button>
              <button class="legend-chip" data-filter="Stock OK" style="--bg: {'#064e3b' if es_oscuro else '#dcfce7'}; --tc: {'#6ee7b7' if es_oscuro else '#166534'};">Stock >5</button>
              <button class="legend-chip" data-filter="cob-alta" style="--bg: {'#1e293b' if es_oscuro else '#ffffff'}; --tc: #ef4444; --bd: 1px solid #ef4444;">Cob ≥30</button>
              <button class="legend-chip" data-filter="top-ventas" style="--bg: {'#422006' if es_oscuro else '#fef3c7'}; --tc: #d97706; --bd: 1px solid #f59e0b;">★ TOP</button>
            </div>
            
            <div class="fs-cat-wrapper">
              <span style="font-size: 0.75rem; font-weight: 700; color: {text_secondary};">Categoría:</span>
              <select id="fsCatSelect" class="fs-cat-select">
                <option value="ALL">Todas las Categorías</option>
                {options_categorias}
              </select>
            </div>
            
            <button id="exitFsBtn" class="btn-saas btn-reset" style="padding: 4px 10px;">✕ Salir</button>
          </div>

          <button class="nav-btn nav-btn-prev" id="btnPrev" title="Cuerpo Anterior">❮</button>
          <div class="zoom-layer" id="zoomLayer">
            <div class="aisle-container" id="aisleContainer">
              {html_cuerpos}
            </div>
          </div>
          <button class="nav-btn nav-btn-next" id="btnNext" title="Cuerpo Siguiente">❯</button>
        </div>

      </div>

      <script>
        const aisleWrapper = document.getElementById('aisleWrapper');
        const zoomLayer = document.getElementById('zoomLayer');
        const container = document.getElementById('aisleContainer');
        const btnPrev = document.getElementById('btnPrev');
        const btnNext = document.getElementById('btnNext');
        const fullscreenBtn = document.getElementById('fullscreenBtn');
        const exitFsBtn = document.getElementById('exitFsBtn');
        
        let scale = 1, minScale = 0.5, maxScale = 3.5;
        let posX = 0, posY = 0;
        let startX = 0, startY = 0;
        let initialDist = 0;
        let isTouching = false;
        let lastTap = 0;

        function updateZoom() {{
          zoomLayer.style.transform = `translate3d(${{posX}}px, ${{posY}}px, 0) scale(${{scale}})`;
        }}

        function getDistance(t) {{
          return Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
        }}

        function autoFitCuerpo(targetBay) {{
          const bay = targetBay || document.querySelector('.bay-column:not(.hidden)');
          if (bay) {{
            const viewportW = container.clientWidth;
            const viewportH = container.clientHeight;
            const bayW = bay.offsetWidth || bay.scrollWidth;
            const bayH = bay.offsetHeight || bay.scrollHeight;

            if (bayW > 0 && bayH > 0) {{
              const scaleW = (viewportW - 16) / bayW;
              const scaleH = (viewportH - 20) / bayH;
              scale = Math.min(scaleW, scaleH, 1.0);
              posX = 0;
              posY = 0;
              updateZoom();
            }}
          }}
        }}

        aisleWrapper.addEventListener('touchstart', (e) => {{
          if (e.touches.length === 1) {{
            if (scale > 1) {{
              isTouching = true;
              startX = e.touches[0].clientX - posX;
              startY = e.touches[0].clientY - posY;
            }}
            const now = new Date().getTime();
            if (now - lastTap < 300 && now - lastTap > 0) {{
              if (scale < 0.95 || scale > 1.05) {{
                scale = 1; posX = 0; posY = 0; updateZoom();
              }} else {{
                const clickedBay = e.target.closest('.bay-column');
                autoFitCuerpo(clickedBay);
              }}
            }}
            lastTap = now;
          }} else if (e.touches.length === 2) {{
            isTouching = true;
            initialDist = getDistance(e.touches);
          }}
        }}, {{ passive: false }});

        aisleWrapper.addEventListener('touchmove', (e) => {{
          if (!isTouching) return;
          if (e.touches.length === 1 && scale > 1) {{
            e.preventDefault();
            posX = e.touches[0].clientX - startX;
            posY = e.touches[0].clientY - startY;
            updateZoom();
          }} else if (e.touches.length === 2) {{
            e.preventDefault();
            const currentDist = getDistance(e.touches);
            const factor = currentDist / initialDist;
            scale = Math.min(Math.max(scale * (factor > 1 ? 1.03 : 0.97), minScale), maxScale);
            initialDist = currentDist;
            updateZoom();
          }}
        }}, {{ passive: false }});

        aisleWrapper.addEventListener('touchend', () => {{ isTouching = false; }});

        function updateScrollButtons() {{
          requestAnimationFrame(() => {{
            const maxScroll = container.scrollWidth - container.clientWidth;
            btnPrev.disabled = container.scrollLeft <= 10;
            btnNext.disabled = container.scrollLeft >= maxScroll - 10;
          }});
        }}

        btnPrev.addEventListener('click', () => {{
          const visibleModule = container.querySelector('.bay-column:not(.hidden)');
          if(visibleModule) {{
            container.scrollBy({{ left: -(visibleModule.offsetWidth + 16), behavior: 'smooth' }});
            setTimeout(updateScrollButtons, 350);
          }}
        }});
        
        btnNext.addEventListener('click', () => {{
          const visibleModule = container.querySelector('.bay-column:not(.hidden)');
          if(visibleModule) {{
            container.scrollBy({{ left: (visibleModule.offsetWidth + 16), behavior: 'smooth' }});
            setTimeout(updateScrollButtons, 350);
          }}
        }});
        
        container.addEventListener('scroll', updateScrollButtons);
        window.addEventListener('resize', updateScrollButtons);

        fullscreenBtn.addEventListener('click', () => {{
          if (!document.fullscreenElement) {{
            if (aisleWrapper.requestFullscreen) aisleWrapper.requestFullscreen();
            else if (aisleWrapper.webkitRequestFullscreen) aisleWrapper.webkitRequestFullscreen();
            fullscreenBtn.textContent = "✕ Salir Pantalla Completa";
          }} else {{
            if (document.exitFullscreen) document.exitFullscreen();
            fullscreenBtn.textContent = "⛶ Pantalla Completa";
          }}
        }});

        exitFsBtn.addEventListener('click', () => {{
          if (document.exitFullscreen) document.exitFullscreen();
          fullscreenBtn.textContent = "⛶ Pantalla Completa";
        }});

        document.addEventListener('fullscreenchange', () => {{
          if (!document.fullscreenElement) fullscreenBtn.textContent = "⛶ Pantalla Completa";
          scale = 1; posX = 0; posY = 0; updateZoom();
        }});

        const searchInput = document.getElementById('searchInput');
        const brandSelect = document.getElementById('brandSelect');
        const catSelect = document.getElementById('catSelect');
        const fsCatSelect = document.getElementById('fsCatSelect');
        const baySelect = document.getElementById('baySelect');
        const levelSelect = document.getElementById('levelSelect');
        const resetBtn = document.getElementById('resetBtn');
        const printBayBtn = document.getElementById('printBayBtn');
        const topNInput = document.getElementById('topNInput');

        let currentLegendFilter = null;
        const allBrands = Array.from(brandSelect.options).map(o => ({{val: o.value, text: o.text}}));
        const allCats = Array.from(catSelect.options).map(o => ({{val: o.value, text: o.text}}));
        const allBays = Array.from(baySelect.options).map(o => ({{val: o.value, text: o.text}}));
        const allLevels = Array.from(levelSelect.options).map(o => ({{val: o.value, text: o.text}}));

        function applyFilters() {{
          const query = searchInput.value.toLowerCase().trim();
          let selectedBrand = brandSelect.value;
          let selectedCat = catSelect.value;
          let selectedBay = baySelect.value;
          let selectedLevel = levelSelect.value;
          const topN = parseInt(topNInput.value) || 5;

          let visibleSkus = new Map();
          let totalVentasFiltered = 0;

          document.querySelectorAll('.sku-item').forEach(card => {{
             const brand = card.getAttribute('data-brand') || '';
             const catjer = card.getAttribute('data-catjer') || '';
             const bay = card.closest('.bay-column').getAttribute('data-module');
             const level = card.closest('.shelf-row').getAttribute('data-level');
             const name = (card.getAttribute('data-name') || '').toLowerCase();
             const ean = card.getAttribute('data-ean') || '';
             const cod = card.getAttribute('data-cod');
             const ventaStr = card.getAttribute('data-venta') || "0";
             const venta = parseFloat(ventaStr.replace(/,/g, '')) || 0;

             const matchSearch = (query === '' || name.includes(query) || ean.includes(query) || brand.toLowerCase().includes(query));
             const matchBrand = (selectedBrand === 'ALL' || brand === selectedBrand);
             const matchCat = (selectedCat === 'ALL' || catjer === selectedCat);
             const matchBay = (selectedBay === 'ALL' || bay === selectedBay);
             const matchLevel = (selectedLevel === 'ALL' || level === selectedLevel);

             if (matchSearch && matchBrand && matchCat && matchBay && matchLevel) {{
                 if (!visibleSkus.has(cod)) {{
                     visibleSkus.set(cod, venta);
                     totalVentasFiltered += venta;
                 }}
             }}
          }});

          let sortedSkus = Array.from(visibleSkus.entries()).sort((a, b) => b[1] - a[1]);
          let topNSkusSet = new Set();
          let topVentasSum = 0;

          for (let i = 0; i < Math.min(topN, sortedSkus.length); i++) {{
              topNSkusSet.add(sortedSkus[i][0]);
              topVentasSum += sortedSkus[i][1];
          }}

          let pct = totalVentasFiltered > 0 ? (topVentasSum / totalVentasFiltered) * 100 : 0;
          document.getElementById('topNInfo').innerHTML = "TOP <b>" + topNSkusSet.size + "</b> concentra el <b style='color:#10b981;'>" + pct.toFixed(1) + "%</b> de la venta (S/ " + totalVentasFiltered.toLocaleString('en-US', {{minimumFractionDigits:2, maximumFractionDigits:2}}) + ").";

          let availableBrands = new Set();
          let availableCats = new Set();
          let availableBays = new Set();
          let availableLevels = new Set();
          
          let setTot = new Set(), setBloq = new Set(), setSin = new Set(), setBajo = new Set(), setOk = new Set(), setCob = new Set(), setTop = new Set();

          document.querySelectorAll('.sku-item').forEach(card => {{
             const brand = card.getAttribute('data-brand') || '';
             const catjer = card.getAttribute('data-catjer') || '';
             const bay = card.closest('.bay-column').getAttribute('data-module');
             const level = card.closest('.shelf-row').getAttribute('data-level');
             const name = (card.getAttribute('data-name') || '').toLowerCase();
             const ean = card.getAttribute('data-ean') || '';
             const cat = card.getAttribute('data-cat') || '';
             const cobVal = parseFloat(card.getAttribute('data-cob')) || 0;
             const cod = card.getAttribute('data-cod');
             
             const isTop = topNSkusSet.has(cod);
             if(isTop) card.classList.add('is-top');
             else card.classList.remove('is-top');

             const matchSearch = (query === '' || name.includes(query) || ean.includes(query) || brand.toLowerCase().includes(query));
             const matchBrand = (selectedBrand === 'ALL' || brand === selectedBrand);
             const matchCat = (selectedCat === 'ALL' || catjer === selectedCat);
             const matchBay = (selectedBay === 'ALL' || bay === selectedBay);
             const matchLevel = (selectedLevel === 'ALL' || level === selectedLevel);

             const passesStandard = matchSearch && matchBrand && matchCat && matchBay && matchLevel;

             if(matchSearch && matchCat && matchBay && matchLevel) availableBrands.add(brand);
             if(matchSearch && matchBrand && matchBay && matchLevel && catjer) availableCats.add(catjer);
             if(matchSearch && matchBrand && matchCat && matchLevel) availableBays.add(bay);
             if(matchSearch && matchBrand && matchCat && matchBay) availableLevels.add(level);

             if(passesStandard) {{
                 setTot.add(cod);
                 if(cat === 'Bloqueado') setBloq.add(cod);
                 if(cat === 'Sin Stock') setSin.add(cod);
                 if(cat === 'Stock Bajo') setBajo.add(cod);
                 if(cat === 'Stock OK') setOk.add(cod);
                 if(cobVal >= 30) setCob.add(cod);
                 if(isTop) setTop.add(cod);
             }}

             let passesLegend = true;
             if (currentLegendFilter) {{
                 if (currentLegendFilter === 'cob-alta') passesLegend = (cobVal >= 30);
                 else if (currentLegendFilter === 'top-ventas') passesLegend = isTop;
                 else passesLegend = (cat === currentLegendFilter);
             }}

             if (matchBrand && matchCat && matchSearch) {{
                 if (currentLegendFilter) {{
                     if (passesLegend) {{
                         card.classList.remove('dimmed');
                         card.classList.add('highlighted');
                     }} else {{
                         card.classList.add('dimmed');
                         card.classList.remove('highlighted');
                     }}
                 }} else {{
                     card.classList.remove('dimmed');
                     card.classList.toggle('highlighted', (query !== '' || selectedBrand !== 'ALL' || selectedCat !== 'ALL'));
                 }}
             }} else {{
                 card.classList.add('dimmed');
                 card.classList.remove('highlighted');
             }}
          }});

          document.getElementById('t-total').textContent = setTot.size;
          document.getElementById('t-bloq').textContent = setBloq.size;
          document.getElementById('t-sin').textContent = setSin.size;
          document.getElementById('t-bajo').textContent = setBajo.size;
          document.getElementById('t-ok').textContent = setOk.size;
          document.getElementById('t-cob').textContent = setCob.size;
          document.getElementById('t-top').textContent = setTop.size;

          if (selectedBrand !== 'ALL' && !availableBrands.has(selectedBrand)) selectedBrand = 'ALL';
          if (selectedCat !== 'ALL' && !availableCats.has(selectedCat)) selectedCat = 'ALL';
          if (selectedBay !== 'ALL' && !availableBays.has(selectedBay)) selectedBay = 'ALL';
          if (selectedLevel !== 'ALL' && !availableLevels.has(selectedLevel)) selectedLevel = 'ALL';

          brandSelect.innerHTML = '';
          allBrands.forEach(opt => {{ if(opt.val === 'ALL' || availableBrands.has(opt.val)) brandSelect.add(new Option(opt.text, opt.val, false, opt.val === selectedBrand)); }});

          catSelect.innerHTML = '';
          fsCatSelect.innerHTML = '';
          allCats.forEach(opt => {{ 
            if(opt.val === 'ALL' || availableCats.has(opt.val)) {{
              catSelect.add(new Option(opt.text, opt.val, false, opt.val === selectedCat));
              fsCatSelect.add(new Option(opt.text, opt.val, false, opt.val === selectedCat));
            }}
          }});

          baySelect.innerHTML = '';
          allBays.forEach(opt => {{ if(opt.val === 'ALL' || availableBays.has(opt.val)) baySelect.add(new Option(opt.text, opt.val, false, opt.val === selectedBay)); }});

          levelSelect.innerHTML = '';
          allLevels.forEach(opt => {{ if(opt.val === 'ALL' || availableLevels.has(opt.val)) levelSelect.add(new Option(opt.text, opt.val, false, opt.val === selectedLevel)); }});

          document.querySelectorAll('.bay-column').forEach(bay => {{
            const bayNum = bay.getAttribute('data-module');
            const passesBayFilter = (selectedBay === 'ALL' || selectedBay === bayNum);
            const hasMatch = Array.from(bay.querySelectorAll('.sku-item')).some(card => {{
                if (currentLegendFilter) return card.classList.contains('highlighted');
                return !card.classList.contains('dimmed');
            }});

            bay.classList.toggle('hidden', !(passesBayFilter && hasMatch));
          }});

          document.querySelectorAll('.shelf-row').forEach(shelf => {{
            const shelfLevel = shelf.getAttribute('data-level');
            const passesLevelFilter = (selectedLevel === 'ALL' || selectedLevel === shelfLevel);
            shelf.classList.toggle('hidden', !passesLevelFilter);
          }});
          
          updateScrollButtons();
        }}

        printBayBtn.addEventListener('click', () => {{
            let currentBay = baySelect.value;
            if (currentBay === 'ALL') {{
                const firstVisible = document.querySelector('.bay-column:not(.hidden)');
                if (firstVisible) {{
                    const bayId = firstVisible.getAttribute('data-module');
                    baySelect.value = bayId;
                    applyFilters();
                }}
            }}
            window.print();
        }});

        // LEYENDA
        document.querySelectorAll('.legend-chip').forEach(chip => {{
            chip.addEventListener('click', () => {{
                const filter = chip.getAttribute('data-filter');
                if (currentLegendFilter === filter) {{
                    currentLegendFilter = null;
                    document.querySelectorAll('.legend-chip').forEach(c => c.classList.remove('active'));
                }} else {{
                    document.querySelectorAll('.legend-chip').forEach(c => c.classList.remove('active'));
                    document.querySelectorAll(`.legend-chip[data-filter="${{filter}}"]`).forEach(c => c.classList.add('active'));
                    currentLegendFilter = filter;
                }}
                applyFilters();
            }});
        }});

        searchInput.addEventListener('input', applyFilters);
        brandSelect.addEventListener('change', applyFilters);
        
        catSelect.addEventListener('change', () => {{
          fsCatSelect.value = catSelect.value;
          applyFilters();
        }});
        
        fsCatSelect.addEventListener('change', () => {{
          catSelect.value = fsCatSelect.value;
          applyFilters();
        }});

        baySelect.addEventListener('change', applyFilters);
        levelSelect.addEventListener('change', applyFilters);
        topNInput.addEventListener('input', applyFilters);
        
        resetBtn.addEventListener('click', () => {{
          searchInput.value = ''; currentLegendFilter = null;
          document.querySelectorAll('.legend-chip').forEach(c => c.classList.remove('active'));
          brandSelect.innerHTML = ''; allBrands.forEach(o => brandSelect.add(new Option(o.text, o.val)));
          catSelect.innerHTML = ''; fsCatSelect.innerHTML = ''; allCats.forEach(o => {{ catSelect.add(new Option(o.text, o.val)); fsCatSelect.add(new Option(o.text, o.val)); }});
          baySelect.innerHTML = ''; allBays.forEach(o => baySelect.add(new Option(o.text, o.val)));
          levelSelect.innerHTML = ''; allLevels.forEach(o => levelSelect.add(new Option(o.text, o.val)));
          brandSelect.value = 'ALL'; catSelect.value = 'ALL'; fsCatSelect.value = 'ALL'; baySelect.value = 'ALL'; levelSelect.value = 'ALL';
          topNInput.value = 5;
          scale = 1; posX = 0; posY = 0; updateZoom();
          applyFilters();
        }});

        // MODAL PRODUCTO (CENTRADO NATIVO)
        const modal = document.getElementById('productModal');
        const closeBtn = document.querySelector('.modal-close');
        
        document.querySelectorAll('.sku-item').forEach(card => {{
            card.addEventListener('click', () => {{
                document.getElementById('m-name').textContent = card.getAttribute('data-name');
                document.getElementById('m-cod').textContent = card.getAttribute('data-cod');
                document.getElementById('m-ean').textContent = card.getAttribute('data-ean');
                document.getElementById('m-brand').textContent = card.getAttribute('data-brand');
                document.getElementById('m-dept').textContent = card.getAttribute('data-dept');
                document.getElementById('m-sec').textContent = card.getAttribute('data-sec');
                document.getElementById('m-catjer').textContent = card.getAttribute('data-catjer');
                document.getElementById('m-ga').textContent = card.getAttribute('data-ga');
                document.getElementById('m-stock').textContent = card.getAttribute('data-stock');
                document.getElementById('m-cob').textContent = card.getAttribute('data-cob');
                
                const ventaStr = card.getAttribute('data-venta') || "0";
                const ventaVal = parseFloat(ventaStr.replace(/,/g, '')) || 0;
                document.getElementById('m-venta').textContent = "S/ " + ventaVal.toLocaleString('en-US', {{minimumFractionDigits:2, maximumFractionDigits:2}});
                
                const isTop = card.classList.contains('is-top');
                document.getElementById('m-top').textContent = isTop ? '⭐ SÍ (Top Ventas)' : 'NO';
                
                modal.classList.add('active');
            }});
        }});
        closeBtn.addEventListener('click', () => modal.classList.remove('active'));
        window.addEventListener('click', (e) => {{ if(e.target === modal) modal.classList.remove('active'); }});

        setTimeout(() => {{
          applyFilters();
          if (window.innerWidth <= 768) {{
            if (baySelect.value === 'ALL') {{
              const firstVisible = document.querySelector('.bay-column:not(.hidden)');
              if (firstVisible) baySelect.value = firstVisible.getAttribute('data-module');
            }}
            applyFilters();
          }}
        }}, 100);
      </script>
    </body>
    </html>
    """

# --- LÓGICA DE CARGA HÍBRIDA ---
@st.cache_data(ttl=14400)
def cargar_datos_nube(url_matriz, url_jerarquia, url_fotos):
    try:
        try:
            df_matriz = pd.read_excel(url_matriz, sheet_name="MATRIZ", skiprows=5, usecols="C:AB")
        except Exception:
            df_matriz = pd.read_excel(url_matriz, skiprows=5, usecols="C:AB")
            
        try:
            df_aux = pd.read_excel(url_matriz, sheet_name="DATA_AUX", skiprows=5)
        except Exception:
            df_aux = pd.DataFrame()

        df_matriz.columns = [str(c).strip() for c in df_matriz.columns]
        if "Bandeja" in df_matriz.columns and "EAN" in df_matriz.columns:
            df_matriz = df_matriz.dropna(subset=["Bandeja", "EAN"], how="all")
            
        try:
            df_jer = pd.read_excel(url_jerarquia, skiprows=2)
            if 'CodGA' not in df_jer.columns:
                 df_jer = pd.read_excel(url_jerarquia)
        except Exception:
            df_jer = pd.DataFrame()
            
        try:
            df_fotos = pd.read_excel(url_fotos)
        except Exception:
            df_fotos = pd.DataFrame()
            
        hora_lectura = pd.Timestamp.now('America/Lima').strftime("%d/%m/%Y - %I:%M %p")
        return df_matriz, df_aux, df_jer, df_fotos, hora_lectura, None
    except Exception as e:
        return None, None, None, None, None, str(e)

URL_NUBE = "https://drive.google.com/uc?export=download&id=1QFqktucaF983WXcjupQI-jpeEZzWxtX_"
URL_JERARQUIA = "https://drive.google.com/uc?export=download&id=1JI4Ef0138lwI-fJsQmX5lz-fqXvemZQD"
URL_FOTOS = "https://drive.google.com/uc?export=download&id=1y8P_GVLySBrbGkm-1nc0BiTwGCorhVtF"

df_raw = None
df_aux_raw = None
df_jer_raw = None
df_fotos_raw = None
info_hora = None
error_nube = None

# --- HEADER SAAS UNIFICADO ---
col_head1, col_head2, col_head3 = st.columns([5.5, 2, 2.5])

with col_head1:
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="font-size: 1.5rem; font-weight: 900; letter-spacing: -0.5px; color: {t['text_primary']};">
                🏪 Planograma <span style="color: {t['accent']}; font-weight: 800;">2.0</span>
            </div>
            <span style="background: {t['accent']}1a; color: {t['accent']}; font-size: 0.65rem; font-weight: 800; padding: 2px 8px; border-radius: 12px; border: 1px solid {t['accent']}33;">ENTERPRISE</span>
        </div>
    """, unsafe_allow_html=True)
    
with col_head2:
    modo_btn_label = "☀️ Modo Claro" if es_oscuro else "🌙 Modo Oscuro"
    if st.button(modo_btn_label, use_container_width=True):
        st.session_state.tema_actual = "light" if es_oscuro else "dark"
        st.rerun()

with col_head3:
    col_act, col_time = st.columns([1, 2])
    with col_act:
        if st.button("🔄 Sync", use_container_width=True, help="Sincronizar base central"):
            st.cache_data.clear()
            st.rerun()
    with col_time:
        header_time_placeholder = st.empty()

with st.spinner("Sincronizando base de datos central..."):
    df_nube, df_aux_nube, df_jer_nube, df_fotos_nube, info_hora, error_nube = cargar_datos_nube(URL_NUBE, URL_JERARQUIA, URL_FOTOS)

header_time_placeholder.markdown(f"""
    <div style="text-align: right; line-height: 1.2;">
        <div style="font-size: 0.75rem; font-weight: 700; color: {t['text_primary']};">Tienda Central</div>
        <div style="font-size: 0.65rem; color: {t['text_muted']};">{info_hora if info_hora else 'En línea'}</div>
    </div>
""", unsafe_allow_html=True)

if df_nube is not None:
    df_raw = df_nube
    df_aux_raw = df_aux_nube
    df_jer_raw = df_jer_nube
    df_fotos_raw = df_fotos_nube
else:
    st.warning("⚠️ No se pudo conectar a la Nube. Puedes subir el archivo MATRIZ manualmente.")
    archivo_manual = st.file_uploader("📥 Subir archivo Excel del Planograma (.xlsx, .xlsb)", type=["xlsx", "xls", "xlsb"])
    if archivo_manual:
        motor = "pyxlsb" if archivo_manual.name.endswith(".xlsb") else None
        try:
            try:
                df_raw = pd.read_excel(archivo_manual, sheet_name="MATRIZ", skiprows=5, usecols="C:AB", engine=motor)
            except Exception:
                df_raw = pd.read_excel(archivo_manual, skiprows=5, usecols="C:AB", engine=motor)
                
            try:
                df_aux_raw = pd.read_excel(archivo_manual, sheet_name="DATA_AUX", skiprows=5, engine=motor)
            except Exception:
                df_aux_raw = pd.DataFrame()
                
            df_jer_raw = pd.DataFrame()
            df_fotos_raw = pd.DataFrame()
            
            df_raw.columns = [str(c).strip() for c in df_raw.columns]
            if "Bandeja" in df_raw.columns and "EAN" in df_raw.columns:
                df_raw = df_raw.dropna(subset=["Bandeja", "EAN"], how="all")
        except Exception as e:
            st.error(f"Error al leer el archivo manual: {e}")

if df_raw is not None:
    df_base = df_raw.copy()
    df_base['COD_REAL_Str'] = df_base['COD REAL'].apply(clean_sku)
    
    if df_aux_raw is not None and not df_aux_raw.empty:
        df_aux_raw.columns = [str(c).strip() for c in df_aux_raw.columns]
        
        if 'Monto Margen' in df_aux_raw.columns:
            cols_material = [c for c in df_aux_raw.columns if 'Material' in c]
            if cols_material:
                col_mat_ventas = cols_material[0]
                df_margen = df_aux_raw[[col_mat_ventas, 'Monto Margen']].copy()
                df_margen['Mat_Ventas_Str'] = df_margen[col_mat_ventas].apply(clean_sku)
                df_margen = df_margen[df_margen['Mat_Ventas_Str'] != ""]
                df_margen = df_margen.drop_duplicates(subset=['Mat_Ventas_Str'])
                df_base = df_base.merge(df_margen[['Mat_Ventas_Str', 'Monto Margen']], left_on='COD_REAL_Str', right_on='Mat_Ventas_Str', how='left')
                df_base.drop(columns=['Mat_Ventas_Str'], inplace=True, errors='ignore')
        
        if 'Grupo de A' in df_aux_raw.columns:
            cols_material = [c for c in df_aux_raw.columns if 'Material' in c]
            if cols_material:
                col_mat_barras = cols_material[-1] 
                df_barras = df_aux_raw[[col_mat_barras, 'Grupo de A']].copy()
                df_barras['Mat_Barras_Str'] = df_barras[col_mat_barras].apply(clean_sku)
                df_barras['Grupo_A_Str'] = df_barras['Grupo de A'].apply(clean_sku)
                df_barras = df_barras.drop_duplicates(subset=['Mat_Barras_Str'])
                df_base = df_base.merge(df_barras[['Mat_Barras_Str', 'Grupo_A_Str']], left_on='COD_REAL_Str', right_on='Mat_Barras_Str', how='left')
                df_base.drop(columns=['Mat_Barras_Str'], inplace=True, errors='ignore')
        else:
            df_base['Grupo_A_Str'] = ""
    else:
        df_base['Grupo_A_Str'] = ""
        
    df_base['Monto Margen'] = df_base.get('Monto Margen', 0.0).fillna(0.0)

    columnas_jerarquia = ['Departamento', 'Sección', 'Categoría', 'Grupo de artículo']
    if df_jer_raw is not None and not df_jer_raw.empty:
        df_jer_raw.columns = [str(c).strip() for c in df_jer_raw.columns]
        if 'CodGA' in df_jer_raw.columns:
            df_jer_raw['CodGA_Str'] = df_jer_raw['CodGA'].apply(clean_sku)
            rename_dict = {
                'DEPARTAMENTO (2)': 'Departamento',
                'SECCIÓN (3)': 'Sección',
                'CATEGORIA (4)': 'Categoría',
                'GRUPO ARTICULO (6)': 'Grupo de artículo'
            }
            cols_to_keep = ['CodGA_Str']
            for old_name, new_name in rename_dict.items():
                if old_name in df_jer_raw.columns:
                    df_jer_raw.rename(columns={old_name: new_name}, inplace=True)
                    cols_to_keep.append(new_name)
                    
            df_jer_unique = df_jer_raw[cols_to_keep].drop_duplicates(subset=['CodGA_Str'])
            df_base = df_base.merge(df_jer_unique, left_on='Grupo_A_Str', right_on='CodGA_Str', how='left')
            
            for col in columnas_jerarquia:
                if col not in df_base.columns: df_base[col] = 'S/D'
                else: df_base[col] = df_base[col].fillna('S/D')
        else:
            for col in columnas_jerarquia: df_base[col] = 'S/D'
    else:
        for col in columnas_jerarquia: df_base[col] = 'S/D'
        
    if df_fotos_raw is not None and not df_fotos_raw.empty:
        df_fotos_raw.columns = [str(c).strip() for c in df_fotos_raw.columns]
        if '_SKUReferenceCode' in df_fotos_raw.columns and 'Links de fotos' in df_fotos_raw.columns:
            df_fotos_raw['_SKUReferenceCode'] = df_fotos_raw['_SKUReferenceCode'].apply(clean_sku)
            df_fotos_unique = df_fotos_raw[['_SKUReferenceCode', 'Links de fotos']].drop_duplicates(subset=['_SKUReferenceCode'])
            df_base = df_base.merge(df_fotos_unique, left_on='COD_REAL_Str', right_on='_SKUReferenceCode', how='left')
        else:
            df_base['Links de fotos'] = ""
    else:
        df_base['Links de fotos'] = ""
        
    df_base.drop(columns=['COD_REAL_Str', 'Grupo_A_Str', 'CodGA_Str', '_SKUReferenceCode'], inplace=True, errors='ignore')

    df_base['Venta_Num'] = df_base['Venta'].apply(safe_float)
    df_base['Margen_Num'] = df_base['Monto Margen'].apply(safe_float)
    df_base['Part_Num'] = df_base['% Part'].apply(safe_float)
    df_base['Stock_Num'] = df_base['Stock'].apply(safe_float)
    df_base['Cob_Num'] = df_base['Cobertura'].apply(safe_float)
    df_base['Caras_Num'] = df_base['Caras'].apply(lambda x: safe_float(x, default=1.0))
    
    col_unid_bandeja = 'Total Unid en Bandeja' if 'Total Unid en Bandeja' in df_base.columns else ('Total_Unidades' if 'Total_Unidades' in df_base.columns else 'Stock')
    df_base['Unid_Bandeja_Num'] = df_base[col_unid_bandeja].apply(safe_float)
    
    df_unicos = df_base.drop_duplicates(subset=['COD REAL']).copy()
    df_unicos = df_unicos[df_unicos['COD REAL'].notna()]
    
    tab1, tab2 = st.tabs(["🛒 Vista Interactiva del Pasillo", "📊 Dashboard Analítico Financiero"])
    
    with tab1:
        col_view1, col_view2 = st.columns([1.5, 2])
        with col_view1:
            modo_vista = st.radio(
                "Modo de Vista:", 
                ["🖼️ Realograma (Imágenes)", "📦 Bloques (Colores)"], 
                index=1, 
                horizontal=True, 
                label_visibility="collapsed"
            )
            es_realograma = ("Realograma" in modo_vista)
        with col_view2:
            st.markdown(f"<div style='text-align: right; font-size: 0.80rem; color: {t['text_muted']}; margin-top: 5px;'>👆 <i>Pellizca para Zoom o haz <b>doble toque</b> para auto-encajar el cuerpo.</i></div>", unsafe_allow_html=True)
            
        html_pasillo = generar_html_pasillo_interactivo(df_base, es_realograma=es_realograma, es_oscuro=es_oscuro)
        components.html(html_pasillo, height=840, scrolling=False)
            
    # =========================================================================
    # --- PESTAÑA 2: DASHBOARD ANALÍTICO REDISEÑADO AL 100% ---
    # =========================================================================
    with tab2:
        ventas_globales = df_unicos['Venta_Num'].sum()
        margen_global = df_unicos['Margen_Num'].sum()
        margen_pct_global = (margen_global / ventas_globales) if ventas_globales > 0 else 0
        total_skus_activos = len(df_unicos)
        promedio_venta_sku = (ventas_globales / total_skus_activos) if total_skus_activos > 0 else 0
        
        # --- TARJETAS KPIS CON FORMATO Y PALETA EXACTA A PESTAÑA 1 ---
        st.markdown(f"""
            <div class="fin-kpi-container">
                <div class="fin-kpi-card" style="border-bottom: 4px solid #3b82f6;">
                    <div class="fin-kpi-title">
                        <span>Ventas Brutas</span>
                        <span>💳</span>
                    </div>
                    <div class="fin-kpi-val">S/ {ventas_globales:,.2f}</div>
                    <div class="fin-kpi-subtitle">Ticket Promedio/SKU: S/ {promedio_venta_sku:,.2f}</div>
                </div>
                <div class="fin-kpi-card" style="border-bottom: 4px solid #10b981;">
                    <div class="fin-kpi-title">
                        <span>Margen Total Bruto</span>
                        <span>📈</span>
                    </div>
                    <div class="fin-kpi-val" style="color: {t['accent_green']};">S/ {margen_global:,.2f}</div>
                    <div class="fin-kpi-subtitle">Ganancia Monetaria Acumulada</div>
                </div>
                <div class="fin-kpi-card" style="border-bottom: 4px solid #8b5cf6;">
                    <div class="fin-kpi-title">
                        <span>Margen Global</span>
                        <span>📊</span>
                    </div>
                    <div class="fin-kpi-val" style="color: {t['accent_purple']};">{margen_pct_global*100:.1f}%</div>
                    <div class="fin-kpi-subtitle">Rentabilidad sobre Venta</div>
                </div>
                <div class="fin-kpi-card" style="border-bottom: 4px solid #fbbf24;">
                    <div class="fin-kpi-title">
                        <span>Surtido Activo</span>
                        <span>📦</span>
                    </div>
                    <div class="fin-kpi-val" style="color: {t['accent_amber']};">{total_skus_activos}</div>
                    <div class="fin-kpi-subtitle">SKUs Únicos en Mueble</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # --- FILTRO POR CATEGORÍA ---
        cats_disponibles = sorted([c for c in df_unicos['Categoría'].dropna().unique() if c not in ['S/C', 'nan', '']])
        col_seg_cat, col_sp_info = st.columns([3, 7])
        with col_seg_cat:
            cat_seleccionada = st.selectbox("🎯 Filtrar Dashboard por Categoría:", ["Todas las Categorías"] + cats_disponibles)
        with col_sp_info:
            st.markdown(f"<div style='margin-top: 30px; font-size: 0.78rem; color: {t['text_muted']}; text-align: right;'>Métricas sincronizadas en tiempo real</div>", unsafe_allow_html=True)
        
        df_dash_base = df_base.copy()
        if cat_seleccionada != "Todas las Categorías":
            df_dash_base = df_dash_base[df_dash_base['Categoría'] == cat_seleccionada]
            
        df_dash_unicos = df_dash_base.drop_duplicates(subset=['COD REAL']).copy()

        # --- NIVEL 2: GRÁFICOS OPERATIVOS CON ETIQUETAS DE ALTO CONTRASTE ---
        col_graf_izq, col_graf_der = st.columns([6.2, 3.8])
        
        with col_graf_izq:
            st.markdown(f"""
                <div class="dash-card">
                    <div class="dash-card-header">
                        <span class="dash-card-title">📈 Rendimiento Comercial por Cuerpo</span>
                        <span style="font-size: 0.70rem; font-weight: 700; color: {t['text_muted']};">VENTAS (S/) vs MARGEN (%)</span>
                    </div>
            """, unsafe_allow_html=True)
            
            bandeja_str = df_dash_base.get('Bandeja', pd.Series(["1.1"]*len(df_dash_base))).astype(str)
            df_dash_base['Cuerpo_Ord'] = bandeja_str.str.extract(r'(\d+)\.(\d+)')[0]
            df_dash_base['Cuerpo_Ord'] = pd.to_numeric(df_dash_base['Cuerpo_Ord'], errors='coerce').fillna(1)
            
            df_sku_cuerpo = df_dash_base.drop_duplicates(subset=['COD REAL', 'Cuerpo_Ord']).copy()
            
            cat_por_cuerpo = df_sku_cuerpo.groupby('Cuerpo_Ord')['Categoría'].agg(
                lambda x: max(set([str(i) for i in x if str(i) not in ['S/C', 'nan', '']]), key=[str(i) for i in x].count) if len([i for i in x if str(i) not in ['S/C', 'nan', '']]) > 0 else ""
            ).to_dict()
            
            ventas_cuerpo = df_sku_cuerpo.groupby('Cuerpo_Ord').agg(
                Venta_Total=('Venta_Num', 'sum'),
                Margen_Total=('Margen_Num', 'sum'),
                SKUs_Total=('COD REAL', 'count')
            ).reset_index()
            
            def crear_etiqueta_eje(c_num):
                cat_nombre = cat_por_cuerpo.get(c_num, "")
                if cat_nombre and len(cat_nombre) > 14:
                    cat_nombre = cat_nombre[:12] + ".."
                return f"Cuerpo {int(c_num)}<br><sub>{cat_nombre}</sub>" if cat_nombre else f"Cuerpo {int(c_num)}"

            ventas_cuerpo['Cuerpo_Label'] = ventas_cuerpo['Cuerpo_Ord'].apply(crear_etiqueta_eje)
            ventas_cuerpo['Margen_Pct'] = ventas_cuerpo.apply(
                lambda row: row['Margen_Total'] / row['Venta_Total'] if row['Venta_Total'] > 0 else 0, 
                axis=1
            )
            
            col_ord, _ = st.columns([2.5, 1.5])
            with col_ord:
                orden_grafico = st.selectbox("Ordenar:", 
                    ["Secuencial (Cuerpo 1..N)", "Mayor a Menor Venta", "Mayor Margen (%)"],
                    label_visibility="collapsed"
                )
            
            if orden_grafico == "Mayor a Menor Venta": ventas_cuerpo = ventas_cuerpo.sort_values('Venta_Total', ascending=False)
            elif orden_grafico == "Mayor Margen (%)": ventas_cuerpo = ventas_cuerpo.sort_values('Margen_Pct', ascending=False)
            else: ventas_cuerpo = ventas_cuerpo.sort_values('Cuerpo_Ord')

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Barras de Venta con color sólido de contraste y etiquetas nítidas
            fig.add_trace(
                go.Bar(
                    x=ventas_cuerpo['Cuerpo_Label'], 
                    y=ventas_cuerpo['Venta_Total'],
                    name="Ventas Totales (S/)",
                    text=ventas_cuerpo['Venta_Total'].apply(lambda x: f"S/ {x/1000:,.1f}K" if x >= 1000 else f"S/ {x:,.0f}"),
                    textposition='inside',
                    insidetextanchor='middle',
                    textfont=dict(color='#ffffff', size=11, family='Inter', weight='bold'),
                    marker=dict(color='#2563eb', line=dict(color='#1d4ed8', width=1.5)),
                    hovertemplate="<b>%{x}</b><br>Ventas: S/ %{y:,.2f}<br>SKUs Únicos: %{customdata}<extra></extra>",
                    customdata=ventas_cuerpo['SKUs_Total']
                ), secondary_y=False
            )

            # Línea de Margen (%) con etiqueta flotante resaltada
            fig.add_trace(
                go.Scatter(
                    x=ventas_cuerpo['Cuerpo_Label'], 
                    y=ventas_cuerpo['Margen_Pct'],
                    name="Margen %",
                    mode="lines+markers+text",
                    text=ventas_cuerpo['Margen_Pct'].apply(lambda x: f"{x*100:,.1f}%"),
                    textposition='top center',
                    textfont=dict(color=t["accent_green"], size=11, family='Inter', weight='bold'),
                    marker=dict(color=t["accent_green"], size=9, symbol='circle', line=dict(color=t["bg_card"], width=2)),
                    line=dict(color=t["accent_green"], width=3, shape='spline'),
                    hovertemplate="<b>%{x}</b><br>Margen: %{text}<extra></extra>"
                ), secondary_y=True
            )

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(color=t["plotly_text"], size=10)),
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=False, color=t["plotly_text"], tickfont=dict(size=10, weight='bold')),
                yaxis=dict(title="Ventas (S/)", showgrid=True, gridcolor=t["grid_color"], color=t["plotly_text"], zeroline=False),
                yaxis2=dict(title="Margen (%)", showgrid=False, color=t["accent_green"], zeroline=False)
            )
            
            fig.update_xaxes(fixedrange=True)
            fig.update_yaxes(fixedrange=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_graf_der:
            st.markdown(f"""
                <div class="dash-card">
                    <div class="dash-card-header">
                        <span class="dash-card-title">🍩 Mix de Venta</span>
                        <span style="font-size: 0.70rem; font-weight: 700; color: {t['text_muted']};">PARTICIPACIÓN</span>
                    </div>
            """, unsafe_allow_html=True)
            
            vista_anillo = st.selectbox("Agrupar mix por:", 
                ["Categoría", "Departamento", "Sección", "Grupo de artículo", "Marca"], 
                label_visibility="collapsed"
            )
            
            df_pie = df_dash_unicos.groupby(vista_anillo)['Venta_Num'].sum().reset_index()
            df_pie = df_pie[df_pie['Venta_Num'] > 0].sort_values(by='Venta_Num', ascending=False)
            ventas_dash_total = df_dash_unicos['Venta_Num'].sum()
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=df_pie[vista_anillo], 
                values=df_pie['Venta_Num'], 
                hole=0.60,
                textinfo='percent',
                textposition='inside',
                insidetextorientation='horizontal',
                textfont=dict(size=11, color='#ffffff', family='Inter', weight='bold'),
                marker=dict(colors=['#2563eb', '#7c3aed', '#059669', '#d97706', '#dc2626', '#0891b2', '#db2777', '#0d9488'], 
                            line=dict(color=t["bg_card"], width=2))
            )])
            
            fig_pie.update_layout(
                showlegend=True,
                legend=dict(font=dict(color=t["plotly_text"], size=9), orientation='h', yanchor='top', y=-0.1),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=10, b=25, l=10, r=10),
                annotations=[dict(text=f'<b>S/ {ventas_dash_total/1000:,.1f}K</b><br><span style="font-size:8px; color:{t["text_muted"]}">TOTAL</span>', x=0.5, y=0.5, font_size=15, showarrow=False, font_color=t["text_primary"])]
            )
            fig_pie.update_traces(hovertemplate="<b>%{label}</b><br>Ventas: S/ %{value:,.2f}<br>Participación: %{percent}<extra></extra>")
            
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
            st.markdown("</div>", unsafe_allow_html=True)

        # --- NIVEL 3: FAIR SHARE ANALYSIS ---
        st.markdown(f"""
            <div class="dash-card">
                <div class="dash-card-header">
                    <span class="dash-card-title">⚖️ Fair Share: Espacio Físico vs Rendimiento</span>
                    <span style="font-size: 0.70rem; font-weight: 700; color: {t['text_muted']};">ANÁLISIS DE EFICIENCIA</span>
                </div>
        """, unsafe_allow_html=True)
        
        col_fs_dim, col_fs_met = st.columns([2, 2])
        with col_fs_dim:
            dim_fs = st.selectbox(
                "Segmentar por:", 
                ["Categoría", "Sección", "Departamento", "Grupo de artículo", "Marca"],
                key="fs_dim_select"
            )
        with col_fs_met:
            metrica_espacio = st.radio(
                "Métrica de Espacio:",
                ["Caras (Facings)", "Total Unidades en Bandeja"],
                horizontal=True,
                key="fs_met_radio"
            )

        col_espacio_elegida = 'Caras_Num' if metrica_espacio == "Caras (Facings)" else 'Unid_Bandeja_Num'
        
        df_fs = df_dash_base.groupby(dim_fs).agg(
            Espacio_Total=(col_espacio_elegida, 'sum'),
            Ventas_Total=('Venta_Num', 'sum'),
            Margen_Total=('Margen_Num', 'sum')
        ).reset_index()
        
        df_fs = df_fs[~df_fs[dim_fs].isin(['S/D', 'S/C', 'S/S', 'S/G', 'nan', ''])].copy()
        
        total_espacio_sum = df_fs['Espacio_Total'].sum()
        total_ventas_sum = df_fs['Ventas_Total'].sum()
        total_margen_sum = df_fs['Margen_Total'].sum()
        
        if total_espacio_sum > 0 and total_ventas_sum > 0:
            df_fs['Pct_Espacio'] = df_fs['Espacio_Total'] / total_espacio_sum
            df_fs['Pct_Ventas'] = df_fs['Ventas_Total'] / total_ventas_sum
            df_fs['Pct_Margen'] = df_fs['Margen_Total'] / total_margen_sum if total_margen_sum > 0 else 0.0
            df_fs['Brecha_Share'] = df_fs['Pct_Ventas'] - df_fs['Pct_Espacio']
            
            df_fs = df_fs.sort_values(by='Pct_Ventas', ascending=False)
            
            fig_fs = go.Figure()
            
            # Barra % Espacio
            fig_fs.add_trace(go.Bar(
                x=df_fs[dim_fs],
                y=df_fs['Pct_Espacio'],
                name=f"% Espacio ({'Caras' if metrica_espacio == 'Caras (Facings)' else 'Unid. Bandeja'})",
                text=df_fs['Pct_Espacio'].apply(lambda x: f"{x*100:.1f}%"),
                textposition='inside',
                insidetextanchor='middle',
                textfont=dict(color='#ffffff', size=10, family='Inter', weight='bold'),
                marker=dict(color='#2563eb', line=dict(color='#1d4ed8', width=1)),
                hovertemplate="<b>%{x}</b><br>% Espacio: %{y:.1%}<br>Total Físico: %{customdata:,.0f}<extra></extra>",
                customdata=df_fs['Espacio_Total']
            ))
            
            # Barra % Ventas
            fig_fs.add_trace(go.Bar(
                x=df_fs[dim_fs],
                y=df_fs['Pct_Ventas'],
                name="% Ventas (Monto S/)",
                text=df_fs['Pct_Ventas'].apply(lambda x: f"{x*100:.1f}%"),
                textposition='inside',
                insidetextanchor='middle',
                textfont=dict(color='#ffffff', size=10, family='Inter', weight='bold'),
                marker=dict(color='#059669', line=dict(color='#047857', width=1)),
                hovertemplate="<b>%{x}</b><br>% Ventas: %{y:.1%}<br>Ventas S/: %{customdata:,.2f}<extra></extra>",
                customdata=df_fs['Ventas_Total']
            ))

            # Barra % Margen
            fig_fs.add_trace(go.Bar(
                x=df_fs[dim_fs],
                y=df_fs['Pct_Margen'],
                name="% Margen (Ganancia S/)",
                text=df_fs['Pct_Margen'].apply(lambda x: f"{x*100:.1f}%"),
                textposition='inside',
                insidetextanchor='middle',
                textfont=dict(color='#ffffff', size=10, family='Inter', weight='bold'),
                marker=dict(color='#d97706', line=dict(color='#b45309', width=1)),
                hovertemplate="<b>%{x}</b><br>% Margen: %{y:.1%}<br>Margen S/: %{customdata:,.2f}<extra></extra>",
                customdata=df_fs['Margen_Total']
            ))
            
            fig_fs.update_layout(
                barmode='group',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(color=t["plotly_text"], size=10)),
                margin=dict(t=20, b=20, l=10, r=10),
                xaxis=dict(showgrid=False, color=t["plotly_text"], tickfont=dict(size=10, weight='bold')),
                yaxis=dict(title="Participación (%)", showgrid=True, gridcolor=t["grid_color"], color=t["plotly_text"], tickformat=".0%")
            )
            
            fig_fs.update_xaxes(fixedrange=True)
            fig_fs.update_yaxes(fixedrange=True)
            st.plotly_chart(fig_fs, use_container_width=True, config={'displayModeBar': False})
            
            # DIAGNÓSTICOS SEMÁNTICOS
            subdimensionados = df_fs[df_fs['Brecha_Share'] > 0.03]
            sobredimensionados = df_fs[df_fs['Brecha_Share'] < -0.03]
            
            col_diag1, col_diag2 = st.columns(2)
            with col_diag1:
                if not subdimensionados.empty:
                    top_sub = subdimensionados.iloc[0]
                    brecha_val = top_sub['Brecha_Share'] * 100
                    st.success(f"🚀 **Oportunidad de Crecimiento:** `{top_sub[dim_fs]}` genera el **{top_sub['Pct_Ventas']*100:.1f}%** de la venta pero ocupa el **{top_sub['Pct_Espacio']*100:.1f}%** del espacio (+{brecha_val:.1f}% de rendimiento positivo).")
                else:
                    st.info("✅ Asignación de espacio balanceada frente a las ventas.")
                    
            with col_diag2:
                if not sobredimensionados.empty:
                    top_sobre = sobredimensionados.sort_values(by='Brecha_Share', ascending=True).iloc[0]
                    brecha_sobre = abs(top_sobre['Brecha_Share'] * 100)
                    st.warning(f"⚠️ **Alerta de Sobreasignación:** `{top_sobre[dim_fs]}` ocupa el **{top_sobre['Pct_Espacio']*100:.1f}%** de la repisa pero solo aporta el **{top_sobre['Pct_Ventas']*100:.1f}%** de las ventas ({brecha_sobre:.1f}% de espacio no rentable).")
                else:
                    st.info("✅ No se detectan sobreasignaciones críticas de espacio.")
            
            st.markdown("</div>", unsafe_allow_html=True)

        # --- NIVEL 4: REPORTE OPERATIVO DETALLADO ---
        st.markdown(f"""
            <div class="dash-card">
                <div class="dash-card-header">
                    <span class="dash-card-title">📋 Detalle Operativo por SKU Único</span>
                    <span style="font-size: 0.70rem; font-weight: 700; color: {t['text_muted']};">AUDITORÍA COMPLETA</span>
                </div>
        """, unsafe_allow_html=True)
        
        col_filt, col_dl = st.columns([4, 1.5])
        with col_filt:
            filtro_reporte = st.selectbox("Filtrar Tabla por Estado:", [
                "Todos los SKUs Activos",
                "Bloqueados (Estado B)",
                "Sin Stock (Quiebre: Stock = 0)",
                "Stock Bajo (Alerta: Stock 1 a 5)",
                "Cobertura Alta (Sobreabastecido: ≥ 30 días)"
            ], label_visibility="collapsed")
        
        with col_dl:
            buffer = io.BytesIO()
            df_agrupado = df_base.copy()
            def formatear_ubicacion(val):
                val_str = str(val).strip()
                if '.' in val_str:
                    partes = val_str.split('.')
                    return f"C{partes[0]} (N{partes[1]})"
                return f"Cuerpo {val_str}"
            df_agrupado['Ubic_Txt'] = df_agrupado['Bandeja'].apply(formatear_ubicacion)
            ubicaciones_map = df_agrupado.groupby('COD REAL')['Ubic_Txt'].apply(
                lambda x: ", ".join(sorted(list(set(x.dropna()))))
            ).to_dict()

            df_rep = df_unicos.copy()
            df_rep['Ubicación(es)'] = df_rep['COD REAL'].map(ubicaciones_map)
            
            if filtro_reporte == "Bloqueados (Estado B)":
                df_rep = df_rep[df_rep['Estado'].astype(str).str.strip().str.upper() == 'B']
            elif filtro_reporte == "Sin Stock (Quiebre: Stock = 0)":
                df_rep = df_rep[(df_rep['Estado'].astype(str).str.strip().str.upper() == 'A') & (df_rep['Stock_Num'] <= 0)]
            elif filtro_reporte == "Stock Bajo (Alerta: Stock 1 a 5)":
                df_rep = df_rep[(df_rep['Estado'].astype(str).str.strip().str.upper() == 'A') & (df_rep['Stock_Num'] > 0) & (df_rep['Stock_Num'] <= 5)]
            elif filtro_reporte == "Cobertura Alta (Sobreabastecido: ≥ 30 días)":
                df_rep = df_rep[df_rep['Cob_Num'] >= 30]
                
            col_desc = 'Descripción' if 'Descripción' in df_rep.columns else 'Nombre'
            cols_to_show = [
                'COD REAL', 'EAN', col_desc, 'Ubicación(es)', 
                'Departamento', 'Sección', 'Categoría', 'Grupo de artículo', 
                'Marca', 'Stock', 'Cobertura', 'Venta', 'Monto Margen'
            ]
            cols_to_show = [c for c in cols_to_show if c in df_rep.columns]

            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_rep[cols_to_show].to_excel(writer, index=False, sheet_name='Reporte_SKUs')
                
            st.download_button(
                label="📥 Exportar Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name="reporte_planograma_skus.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        st.dataframe(df_rep[cols_to_show], use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
