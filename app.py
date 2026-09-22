import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import io
import os
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
    "text_muted": "#475569",
    "accent": "#2563eb",
    "grid_color": "rgba(0, 0, 0, 0.06)",
    "card_shadow": "0 2px 6px rgba(0,0,0,0.05)",
}

# INYECCIÓN CSS
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
        
        html, body, .stApp, [data-testid="stAppViewContainer"], .main, section.main, [data-testid="stHeader"] {{
            background-color: {t["bg_app"]} !important;
            background: {t["bg_app"]} !important;
            color: {t["text_primary"]} !important;
            font-family: 'Inter', sans-serif !important;
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
            background-color: #f1f5f9 !important;
            padding: 6px !important;
            border-radius: 8px !important;
            border: 1.5px solid {t["border_subtle"]} !important;
            margin-bottom: 14px !important;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            height: 40px !important;
            padding: 0 20px !important;
            border-radius: 6px !important;
            font-weight: 800 !important;
            font-size: 0.88rem !important;
            background-color: #e2e8f0 !important;
            border: 1.5px solid {t["border_subtle"]} !important;
            opacity: 1 !important;
            transition: all 0.2s ease !important;
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
            box-shadow: 0 2px 6px rgba(0,0,0,0.15) !important;
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
        
        /* TARJETAS KPIS */
        .fin-kpi-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
        
        .dash-card {{
            background: {t["bg_card"]};
            border: 1px solid {t["border_subtle"]};
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 12px;
            box-shadow: {t["card_shadow"]};
        }}

        .insight-box {{
            border-radius: 8px;
            padding: 14px 16px;
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

# --- GENERADOR DEL PLANOGRAMA PANORÁMICO CON LEYENDA INTERACTIVA INTEGRADA ---
def generar_html_planograma_panoramico(df, titulo_categoria="PLANOGRAMA"):
    df = df.copy()
    df['FilaOriginal'] = range(len(df))
    
    col_pos = 'N° ORDEN' if 'N° ORDEN' in df.columns else ('N°' if 'N°' in df.columns else None)
    if col_pos:
        df['TieneOrden'] = pd.to_numeric(get_clean_series(df, col_pos), errors='coerce').notna()
        df['NumOrden'] = pd.to_numeric(get_clean_series(df, col_pos), errors='coerce').fillna(999999)
    else:
        df['TieneOrden'] = False
        df['NumOrden'] = 999999
    
    bandeja_series = get_clean_series(df, 'Bandeja')
    desglose = bandeja_series.apply(desglosar_cuerpo_y_nivel)
    df['Cuerpo_Ord'] = [x[0] for x in desglose]
    df['Nivel_Num'] = [x[1] for x in desglose]

    df = df.sort_values(
        by=['Cuerpo_Ord', 'Nivel_Num', 'TieneOrden', 'NumOrden', 'FilaOriginal'], 
        ascending=[True, False, False, True, True]
    )

    cuerpos_dict = {}
    for _, r in df.iterrows():
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

                for c_idx in range(caras):
                    rects_html += f"""
                    <div class="plano-rect" style="background-color: {bg_color}; border-color: {border_color}; color: {text_color};"
                         data-estado="{cat_leyenda}"
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
                <div class="plano-facings-container">
                    {rects_html}
                </div>
                <div class="plano-shelf-bar"></div>
            </div>
            """

        html_cuerpos += f"""
        <div class="plano-cuerpo-col" style="flex: 0 0 {pct_cuerpo}%; max-width: {pct_cuerpo}%;">
            <div class="plano-cuerpo-shelves">
                {html_niveles}
            </div>
            <div class="plano-cuerpo-footer">{cuerpo_id}</div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Inter', sans-serif; background: #ffffff; color: #0f172a; padding: 2px; width: 100%; }}
        
        /* LEYENDA INTERACTIVA */
        .interactive-legend-bar {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            padding: 8px 10px;
            background: #ffffff;
            border: 1.5px solid #cbd5e1;
            border-radius: 6px;
            margin-bottom: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
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
            padding: 4px 12px;
            border-radius: 14px;
            cursor: pointer;
            border: 2px solid transparent;
            transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
            user-select: none;
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
        
        .btn-bloq {{ background: #dc2626; color: #ffffff; border-color: #991b1b; }}
        .btn-sinstk {{ background: #ea580c; color: #ffffff; border-color: #c2410c; }}
        .btn-bajo {{ background: #facc15; color: #0f172a; border-color: #ca8a04; }}
        .btn-ok {{ background: #16a34a; color: #ffffff; border-color: #15803d; }}
        .btn-todos {{ background: #f1f5f9; color: #0f172a; border-color: #cbd5e1; }}

        .plano-outer-card {{
            border: 2px solid #0f172a;
            border-radius: 4px;
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
            background: #ffffff;
        }}
        
        .plano-cuerpo-col {{
            display: flex;
            flex-direction: column;
            border-right: 2px solid #0f172a;
            min-width: 0;
        }}
        .plano-cuerpo-col:last-child {{
            border-right: none;
        }}
        
        .plano-cuerpo-shelves {{
            display: flex;
            flex-direction: column;
            padding: 3px 2px;
            gap: 2.5px;
            flex-grow: 1;
        }}
        
        .plano-level-row {{
            display: flex;
            flex-direction: column;
            width: 100%;
        }}
        
        /* ALTURA REDUCIDA EN UN 30%: 45px */
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
            transition: transform 0.15s ease, opacity 0.2s ease, filter 0.2s ease, box-shadow 0.15s ease;
        }}
        
        /* ESTADOS DE INTERACTIVIDAD */
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
            font-family: monospace;
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
        
        /* MODAL */
        .modal-overlay {{ 
          position: fixed !important; 
          inset: 0 !important; 
          width: 100vw !important; 
          height: 100vh !important; 
          background: rgba(15, 23, 42, 0.65) !important; 
          z-index: 99999 !important; 
          opacity: 0; 
          pointer-events: none; 
          transition: opacity 0.2s ease; 
          display: flex !important; 
          align-items: center !important; 
          justify-content: center !important; 
          padding: 16px !important; 
          backdrop-filter: blur(4px); 
        }}
        .modal-overlay.active {{ opacity: 1 !important; pointer-events: auto !important; }}
        
        .modal-content {{ 
          background: #ffffff !important; 
          color: #0f172a !important; 
          padding: 22px !important; 
          border-radius: 10px !important; 
          width: 90% !important; 
          max-width: 440px !important; 
          border: 2.5px solid #2563eb !important; 
          box-shadow: 0 20px 40px rgba(0,0,0,0.2) !important; 
          position: relative !important; 
        }}
        .modal-close {{ position: absolute; top: 10px; right: 14px; font-size: 1.4rem; cursor: pointer; color: #64748b; font-weight: 800; }}
        .modal-close:hover {{ color: #0f172a; }}
        .m-row {{ border-bottom: 1px solid #e2e8f0; padding: 6px 0; display: flex; justify-content: space-between; font-size: 0.82rem; }}
        .m-label {{ font-weight: 600; color: #2563eb; }}
        .m-val {{ font-weight: 700; text-align: right; }}
      </style>
    </head>
    <body>
      <!-- BARRA DE LEYENDA INTERACTIVA -->
      <div class="interactive-legend-bar">
        <span class="legend-label-title">📍 Resaltar Estado:</span>
        <button type="button" class="legend-btn btn-bloq" data-target="Bloqueado">Bloqueado (B)</button>
        <button type="button" class="legend-btn btn-sinstk" data-target="Sin Stock">Sin Stock / Quiebre (0)</button>
        <button type="button" class="legend-btn btn-bajo" data-target="Stock Bajo">Stock Bajo (1 a 5)</button>
        <button type="button" class="legend-btn btn-ok" data-target="Stock OK">Stock OK (> 5)</button>
        <button type="button" class="legend-btn btn-todos" id="btnVerTodos" style="margin-left: auto;">Ver Todos</button>
      </div>

      <div class="plano-outer-card">
        <div class="plano-top-header">{titulo_categoria}</div>
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
        // LÓGICA DE LA LEYENDA INTERACTIVA
        let currentActiveState = null;
        const legendButtons = document.querySelectorAll('.legend-btn[data-target]');
        const btnVerTodos = document.getElementById('btnVerTodos');
        const rects = document.querySelectorAll('.plano-rect');

        function aplicarFiltroLeyenda(estado) {{
            if (currentActiveState === estado) {{
                // Desactivar si se hace clic de nuevo
                currentActiveState = null;
                legendButtons.forEach(b => b.classList.remove('active'));
                rects.forEach(r => {{
                    r.classList.remove('dimmed', 'highlighted');
                }});
                return;
            }}

            currentActiveState = estado;
            legendButtons.forEach(b => {{
                if (b.getAttribute('data-target') === estado) {{
                    b.classList.add('active');
                }} else {{
                    b.classList.remove('active');
                }}
            }});

            rects.forEach(r => {{
                const rEstado = r.getAttribute('data-estado');
                if (rEstado === estado) {{
                    r.classList.remove('dimmed');
                    r.classList.add('highlighted');
                }} else {{
                    r.classList.add('dimmed');
                    r.classList.remove('highlighted');
                }}
            }});
        }}

        legendButtons.forEach(btn => {{
            btn.addEventListener('click', () => {{
                const targetEstado = btn.getAttribute('data-target');
                aplicarFiltroLeyenda(targetEstado);
            }});
        }});

        btnVerTodos.addEventListener('click', () => {{
            currentActiveState = null;
            legendButtons.forEach(b => b.classList.remove('active'));
            rects.forEach(r => {{
                r.classList.remove('dimmed', 'highlighted');
            }});
        }});

        // LÓGICA DEL MODAL DE DETALLE
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

# --- MAPA DE PLANOGRAMAS INSTITUCIONALES (MUNDO DESAYUNO) ---
MAPA_PLANOGRAMAS_IMG = {
    "PANES Y TOSTADAS": "panes_y_tostadas.jpg",
    "MIELES / JALEAS / SIROPE": "mieles_jaleas_sirope.jpg",
    "TÉ E INFUSIONES": "te_e_infusiones.jpg",
    "MODIFICADORES DE LECHES / COMPLEMENTOS / SUPLEMENTOS": "modificadores_leches.jpg",
    "CAFÉ Y COMPLEMENTOS": "cafes_y_complementos.jpg",
}

# --- CARGA INTEGRADA DE FUENTES Y LIMPIEZA TOTAL ---
@st.cache_data(ttl=14400)
def cargar_todas_las_fuentes():
    try:
        url_planos = "https://docs.google.com/spreadsheets/d/1pbGYgDB8UBZnm0aJZLGOhZwWYq0IlDO8Uqv2n1-MgxI/export?format=xlsx"
        url_coberturas = "https://docs.google.com/spreadsheets/d/1deT1W2MA2kZzm-vJVSp6eL1IsLAKyaYLFCrZYxNU7-c/export?format=xlsx"
        url_ventas = "https://docs.google.com/spreadsheets/d/1NdEQXgbsb5bXbhIs2keFin9Wk5mC4dK7N_Y3dbv6fcg/export?format=xlsx"
        url_barras = "https://docs.google.com/spreadsheets/d/1veTjECI6wlFRqOVg1AKmV0yghxyGR5T0j0Im2AooukM/export?format=xlsx"
        url_jerarquia = "https://docs.google.com/spreadsheets/d/1JI4Ef0138lwI-fJsQmX5lz-fqXvemZQD/export?format=xlsx"
        url_fotos = "https://docs.google.com/spreadsheets/d/1y8P_GVLySBrbGkm-1nc0BiTwGCorhVtF/export?format=xlsx"

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

        # 1. Matriz de Planos
        df_matriz = leer_tabla_por_ancla(url_planos, "COD REAL", sheet_target=0, skiprows_fallback=3)
        if "COD REAL" not in df_matriz.columns:
            df_matriz = pd.read_excel(url_planos, sheet_name=0, skiprows=2)
            df_matriz.columns = [str(c).strip() for c in df_matriz.columns]
            df_matriz = df_matriz.loc[:, ~df_matriz.columns.duplicated()].copy()

        df_matriz['COD_REAL_Str'] = get_clean_series(df_matriz, 'COD REAL').apply(clean_sku)
        df_matriz['COD REAL'] = df_matriz['COD_REAL_Str']

        if 'PASILLO' not in df_matriz.columns:
            df_matriz['PASILLO'] = "1"
        if 'LATERAL' not in df_matriz.columns:
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
        if not df_sap_raw.empty and len(df_sap_raw.columns) >= 11:
            col_k_codga = df_sap_raw.columns[10]
            col_d_depto = df_sap_raw.columns[3]
            col_f_seccion = df_sap_raw.columns[5]
            col_h_cat = df_sap_raw.columns[7]
            col_n_ga = df_sap_raw.columns[13] if len(df_sap_raw.columns) > 13 else df_sap_raw.columns[10]

            df_sap['CodGA_Str'] = get_clean_series(df_sap_raw, col_k_codga).apply(clean_sku)
            df_sap['Departamento'] = get_clean_series(df_sap_raw, col_d_depto).fillna('SIN DATOS').str.strip()
            df_sap['Sección'] = get_clean_series(df_sap_raw, col_f_seccion).fillna('SIN DATOS').str.strip()
            df_sap['Categoría'] = get_clean_series(df_sap_raw, col_h_cat).fillna('SIN DATOS').str.strip()
            df_sap['Grupo de Artículo'] = get_clean_series(df_sap_raw, col_n_ga).fillna('SIN DATOS').str.strip()
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
                df_sap[['CodGA_Str', 'Departamento', 'Sección', 'Categoría', 'Grupo de Artículo']], 
                left_on='G.A._Str', 
                right_on='CodGA_Str', 
                how='left',
                suffixes=('', '_sap')
            )
            for col_target in ['Departamento', 'Sección', 'Categoría', 'Grupo de Artículo']:
                col_sap_name = f"{col_target}_sap"
                if col_sap_name in df_pasillo_base.columns:
                    target_s = get_clean_series(df_pasillo_base, col_target)
                    sap_s = get_clean_series(df_pasillo_base, col_sap_name)
                    df_pasillo_base[col_target] = sap_s.replace(['SIN DATOS', 'nan', 'None', '', 'NaN'], pd.NA).fillna(target_s)
                    df_pasillo_base.drop(columns=[col_sap_name], inplace=True, errors='ignore')

            df_pasillo_base.drop(columns=['CodGA_Str', 'G.A._Str'], inplace=True, errors='ignore')

        for col, val_def in [('Stock', -999.0), ('Cobertura', -999.0), ('Venta', -999.0), ('Monto Margen', -999.0), ('% Part', -999.0)]:
            sanitizar_columna_num(df_pasillo_base, col, val_def)

        for col, val_def in [('Estado', 'SIN DATOS'), ('Departamento', 'SIN DATOS'), ('Sección', 'SIN DATOS'), ('Categoría', 'SIN DATOS'), ('Grupo de Artículo', 'SIN DATOS'), ('G.A.', 'SIN DATOS'), ('Links de fotos', 'SIN DATOS'), ('Descripción', 'SIN DATOS'), ('EAN', 'SIN DATOS'), ('PASILLO', '1'), ('LATERAL', 'A')]:
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
                df_sap[['CodGA_Str', 'Departamento', 'Sección', 'Categoría', 'Grupo de Artículo']], 
                left_on='G.A._Str', 
                right_on='CodGA_Str', 
                how='left',
                suffixes=('', '_sap')
            )
            for col_target in ['Departamento', 'Sección', 'Categoría', 'Grupo de Artículo']:
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

        for col, val_def in [('Estado', 'SIN DATOS'), ('Descripción', 'SIN DATOS'), ('EAN', 'SIN DATOS'), ('Departamento', 'SIN DATOS'), ('Sección', 'SIN DATOS'), ('Categoría', 'SIN DATOS'), ('Grupo de Artículo', 'SIN DATOS'), ('Ubicación(es)', pd.NA)]:
            sanitizar_columna_str(df_sku_unico, col, val_def)

        hora_lectura = pd.Timestamp.now('America/Lima').strftime("%d/%m/%Y - %I:%M %p")
        return df_pasillo_base, df_sku_unico, hora_lectura, None
    except Exception as e:
        return None, None, None, str(e)

# --- HEADER Y CARGA ---
with st.spinner("Sincronizando fuentes externas en la nube..."):
    df_pasillo_global, df_sku_unico_global, info_hora, error_nube = cargar_todas_las_fuentes()

col_head1, col_head3 = st.columns([7.5, 2.5])
with col_head1:
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="font-size: 1.5rem; font-weight: 900; letter-spacing: -0.5px; color: {t['text_primary']};">
                🏪 Planograma <span style="color: {t['accent']}; font-weight: 800;">2.0</span>
            </div>
            <span style="background: {t['accent']}1a; color: {t['accent']}; font-size: 0.65rem; font-weight: 800; padding: 2px 8px; border-radius: 12px; border: 1px solid {t['accent']}33;">CENCOSUD PERÚ</span>
        </div>
    """, unsafe_allow_html=True)

with col_head3:
    st.markdown(f"""
        <div style="text-align: right; line-height: 1.3;">
            <div style="font-size: 0.78rem; font-weight: 800; color: {t['text_primary']};">Desarrollado por <b>Alfredo H.M.</b></div>
            <div style="font-size: 0.68rem; color: {t['text_muted']};">{info_hora if info_hora else 'En línea'}</div>
        </div>
    """, unsafe_allow_html=True)

if error_nube:
    st.warning(f"⚠️ Aviso de conexión a la nube: {error_nube}")

# --- COMPUERTA DE BÚSQUEDA (ESTILO SHAREPOINT) ---
if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False

st.markdown("""
    <div style="background: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
        <div style="font-size: 0.85rem; font-weight: 800; color: #1e3a8a; text-transform: uppercase; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            🏬 Filtros de Búsqueda de Planogramas
        </div>
""", unsafe_allow_html=True)

col_b1, col_b2, col_b3, col_b4 = st.columns([2.5, 2.5, 3.5, 1.5])

with col_b1:
    tienda_sel = st.selectbox("Tienda", ["S008 Metro Schell", "S001 Metro Miraflores", "S004 Wong Benavides", "Todas las Tiendas"], key="gate_tienda")

with col_b2:
    mundo_sel = st.selectbox("Mundo", ["DESAYUNO", "ABARROTES", "LÁCTEOS Y EMBUTIDOS", "LIMPIEZA"], key="gate_mundo")

with col_b3:
    if df_pasillo_global is not None and not df_pasillo_global.empty:
        cats_encontradas = sorted([c for c in df_pasillo_global['Categoría'].dropna().unique() if str(c) not in ['SIN DATOS', 'S/C', 'nan', '']])
    else:
        cats_encontradas = [
            "CAFÉ Y COMPLEMENTOS",
            "MODIFICADORES DE LECHES / COMPLEMENTOS / SUPLEMENTOS", 
            "TÉ E INFUSIONES", 
            "PANES Y TOSTADAS", 
            "MIELES / JALEAS / SIROPE"
        ]
    
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
    st.info("👆 **Seleccione la Tienda, Mundo y Categoría y haga clic en 'Buscar' (🔍) para consultar el planograma y sus indicadores.**")
else:
    df_base = df_pasillo_global.copy()
    
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

    tab_resumen, tab_plano, tab_dash, tab_errores = st.tabs([
        "📊 Resumen Ejecutivo",
        "📐 Planograma Físico Panorámico", 
        "📈 Dashboard Analítico Financiero", 
        "⚠️ Errores y Desajustes de Cruce"
    ])

    # =========================================================================
    # --- PESTAÑA 1: RESUMEN EJECUTIVO (GERENCIA DE OPERACIONES) ---
    # =========================================================================
    with tab_resumen:
        tot_skus_plano = len(df_unicos)
        quiebres_df = df_unicos[(df_unicos['Estado'].str.strip().str.upper() == 'A') & (df_unicos['Stock_Num'] <= 0)]
        tot_quiebres = len(quiebres_df)
        pct_quiebres = (tot_quiebres / tot_skus_plano * 100) if tot_skus_plano > 0 else 0
        osa_pct = 100.0 - pct_quiebres
        
        bloqueados_df = df_unicos[df_unicos['Estado'].str.strip().str.upper() == 'B']
        tot_bloqueados = len(bloqueados_df)
        
        ventas_tot_plano = df_unicos['Venta_Num'].sum()
        margen_tot_plano = df_unicos['Margen_Num'].sum()
        margen_pct_plano = (margen_tot_plano / ventas_tot_plano * 100) if ventas_tot_plano > 0 else 0
        venta_en_riesgo = quiebres_df['Venta_Num'].sum()
        
        df_no_plano = df_sku_unico_global[
            df_sku_unico_global['Ubicación(es)'].isna() | 
            (get_clean_series(df_sku_unico_global, 'Ubicación(es)').str.strip() == "") | 
            (get_clean_series(df_sku_unico_global, 'Ubicación(es)').str.strip() == "SIN DATOS")
        ].copy()
        tot_no_plano = len(df_no_plano)
        ventas_no_plano = df_no_plano['Venta'].apply(lambda x: 0.0 if safe_float(x, -999.0) == -999.0 else safe_float(x, 0.0)).sum()

        st.markdown(f"""
            <div class="fin-kpi-container">
                <div class="fin-kpi-card" style="border-bottom: 4px solid #10b981;">
                    <div class="fin-kpi-title"><span>Nivel de Servicio (OSA)</span><span>🎯</span></div>
                    <div class="fin-kpi-val" style="color: {'#10b981' if osa_pct >= 95 else ('#ea580c' if osa_pct >= 90 else '#dc2626')};">{osa_pct:.1f}%</div>
                    <div class="fin-kpi-subtitle">Disponibilidad en góndola (Meta &gt; 95%)</div>
                </div>
                <div class="fin-kpi-card" style="border-bottom: 4px solid #dc2626;">
                    <div class="fin-kpi-title"><span>Quiebres de Stock (0)</span><span>🚨</span></div>
                    <div class="fin-kpi-val" style="color: #dc2626;">{tot_quiebres}</div>
                    <div class="fin-kpi-subtitle"><b>{pct_quiebres:.1f}%</b> del surtido quebrado</div>
                </div>
                <div class="fin-kpi-card" style="border-bottom: 4px solid #64748b;">
                    <div class="fin-kpi-title"><span>SKUs Bloqueados (B)</span><span>🚫</span></div>
                    <div class="fin-kpi-val" style="color: #64748b;">{tot_bloqueados}</div>
                    <div class="fin-kpi-subtitle">Espacio a depurar en góndola</div>
                </div>
                <div class="fin-kpi-card" style="border-bottom: 4px solid #ea580c;">
                    <div class="fin-kpi-title"><span>Venta sin Planograma</span><span>📦</span></div>
                    <div class="fin-kpi-val" style="color: #ea580c;">{tot_no_plano}</div>
                    <div class="fin-kpi-subtitle">SKUs huérfanos con venta activa</div>
                </div>
                <div class="fin-kpi-card" style="border-bottom: 4px solid #2563eb;">
                    <div class="fin-kpi-title"><span>Venta en Góndola</span><span>💳</span></div>
                    <div class="fin-kpi-val" style="color: #2563eb;">S/ {ventas_tot_plano/1000:,.1f}K</div>
                    <div class="fin-kpi-subtitle">Margen: <b>{margen_pct_plano:.1f}%</b> (S/ {margen_tot_plano/1000:,.1f}K)</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        c_a1, c_a2 = st.columns(2)
        with c_a1:
            st.markdown(f"""
                <div class="insight-box" style="background-color: #fee2e2; border-left: 4px solid #dc2626; color: #991b1b;">
                    <b>🚨 Venta en Riesgo por Quiebres: S/ {venta_en_riesgo:,.2f}</b><br>
                    Hay <b>{tot_quiebres} SKUs con Stock 0</b> en repisa que detienen ventas directas en esta categoría.
                </div>
            """, unsafe_allow_html=True)
        with c_a2:
            st.markdown(f"""
                <div class="insight-box" style="background-color: #ffedd5; border-left: 4px solid #ea580c; color: #9a3412;">
                    <b>⚠️ Venta Fuera de Planograma: S/ {ventas_no_plano:,.2f}</b><br>
                    Existen <b>{tot_no_plano} SKUs vendidos</b> que no tienen una posición física registrada en el plano.
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        col_g1, col_g2 = st.columns([6.2, 3.8])
        with col_g1:
            st.markdown(f"<b>🔥 Quiebres por Categoría vs % Participación de Ventas</b>", unsafe_allow_html=True)
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
            st.markdown(f"<b>🎯 Salud del Stock en Góndola</b>", unsafe_allow_html=True)
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
    # --- PESTAÑA 2: NUEVO PLANOGRAMA PANORÁMICO (ALTURA REDUCIDA EN 30%) ---
    # =========================================================================
    with tab_plano:
        cat_actual_titulo = cat_sel if cat_sel != "Todas las Categorías" else "CAFÉS Y COMPLEMENTOS"
        st.markdown(f"<h4 style='color:#0f172a; margin-top: 0;'>{cat_actual_titulo}</h4>", unsafe_allow_html=True)
        
        # 1. IMAGEN DEL PLANOGRAMA INSTITUCIONAL ARRIBA
        nombre_archivo_img = MAPA_PLANOGRAMAS_IMG.get(cat_sel, "cafes_y_complementos.jpg")
        
        expander_img = st.expander("📸 Ver / Vincular Imagen Oficial del Planograma Institucional", expanded=True)
        with expander_img:
            if os.path.exists(nombre_archivo_img):
                st.image(nombre_archivo_img, use_container_width=True, caption=f"Planograma Oficial - {cat_actual_titulo}")
            elif os.path.exists(f"assets/{nombre_archivo_img}"):
                st.image(f"assets/{nombre_archivo_img}", use_container_width=True, caption=f"Planograma Oficial - {cat_actual_titulo}")
            else:
                st.markdown(f"<p style='color: #475569; font-size: 0.84rem;'>Sube la imagen del planograma para <b>{cat_actual_titulo}</b> (se recordará en la sesión):</p>", unsafe_allow_html=True)
                uploaded_img = st.file_uploader(f"Cargar imagen para {cat_actual_titulo}", type=["jpg", "png", "jpeg"], key=f"uploader_{cat_sel}")
                if uploaded_img:
                    st.image(uploaded_img, use_container_width=True, caption=f"Planograma Oficial - {cat_actual_titulo}")

        # 2. DIAGRAMA PANORÁMICO AJUSTADO CON LEYENDA INTERACTIVA INTEGRADA
        bandeja_series = get_clean_series(df_base, 'Bandeja')
        desglose = bandeja_series.apply(desglosar_cuerpo_y_nivel)
        niveles_reales = [x[1] for x in desglose]
        max_niveles_count = max(niveles_reales) if len(niveles_reales) > 0 else 8
        altura_plano = max(500, 160 + max_niveles_count * 53)

        html_plano_rect = generar_html_planograma_panoramico(df_base, titulo_categoria=cat_actual_titulo)
        components.html(html_plano_rect, height=altura_plano, scrolling=True)

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

        # FAIR SHARE CON SKU COUNT
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
                marker_color='#2563eb',
                hovertemplate="<b>%{x}</b><br>% Espacio: %{y:.1%}<br>SKUs Únicos: %{customdata}<extra></extra>",
                customdata=df_fs['SKUs_Activos']
            ))
            fig_fs.add_trace(go.Bar(
                x=df_fs['Categoría'], y=df_fs['Pct_Ventas'], name="% Ventas (Monto S/)",
                text=df_fs['Pct_Ventas'].apply(lambda x: f"{x*100:.1f}%"), textposition='inside',
                marker_color='#16a34a',
                hovertemplate="<b>%{x}</b><br>% Ventas: %{y:.1%}<br>SKUs Únicos: %{customdata}<extra></extra>",
                customdata=df_fs['SKUs_Activos']
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
        st.markdown("<div style='font-size: 0.85rem; font-weight: 800; color: #2563eb; margin-bottom: 8px;'>⚠️ CONTROL DE INTEGRIDAD DE DATOS (DATOST)</div>", unsafe_allow_html=True)
        df_err = df_base[(df_base['Stock'] == -999.0) | (df_base['Venta'] == -999.0) | (df_base['Estado'] == 'SIN DATOS')].copy()
        st.metric("Total de Filas / SKUs con Incongruencias", len(df_err))
        if len(df_err) > 0:
            cols_e = [c for c in ['COD REAL', 'EAN', 'Descripción', 'Bandeja', 'Stock', 'Venta', 'Estado'] if c in df_err.columns]
            cols_e = list(dict.fromkeys(cols_e))
            st.dataframe(df_err[cols_e], use_container_width=True, hide_index=True)
        else:
            st.success("🎉 ¡Excelente! No se detectaron desajustes de cruce en esta categoría.")
