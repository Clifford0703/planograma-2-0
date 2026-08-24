import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import io
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Planograma 2.0",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        .block-container {
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            padding-top: 1.5rem !important;
            max-width: 100% !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE APOYO Y LIMPIEZA ---
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

def obtener_estado_y_color(estado, stock_val):
    estado = str(estado).strip().upper()
    if estado == "B": 
        return "#FFC7CE", "#9C0006", "bloqueado"
    elif estado == "A":
        if stock_val <= 0: return "#F4B084", "#833C0C", "sin-stock"
        elif stock_val <= 5: return "#FFFF99", "#8A5A00", "stock-bajo"
        else: return "#C6EFCE", "#006100", "stock-ok"
    else: 
        return "#D9D9D9", "#000000", "desconocido"

# --- GENERADOR HTML INTERACTIVO ---
def generar_html_pasillo_interactivo(df):
    df = df.copy()
    df['FilaOriginal'] = range(len(df))
    df['TieneOrden'] = pd.to_numeric(df.get('N° ORDEN', pd.Series([None]*len(df))), errors='coerce').notna()
    df['NumOrden'] = pd.to_numeric(df.get('N° ORDEN', pd.Series([None]*len(df))), errors='coerce').fillna(999999)
    
    bandeja_str = df.get('Bandeja', pd.Series(["1.1"]*len(df))).astype(str)
    df[['Modulo_Ord', 'Nivel_Ord']] = bandeja_str.str.extract(r'(\d+)\.(\d+)')
    df['Modulo_Ord'] = pd.to_numeric(df['Modulo_Ord'], errors='coerce').fillna(1)
    df['Nivel_Ord'] = pd.to_numeric(df['Nivel_Ord'], errors='coerce').fillna(1)

    df = df.sort_values(
        by=['Modulo_Ord', 'Nivel_Ord', 'TieneOrden', 'NumOrden', 'FilaOriginal'], 
        ascending=[True, False, False, True, True]
    )

    modulos = {}
    todas_marcas = sorted(list(df["Marca"].dropna().unique())) if "Marca" in df.columns else []
    todos_niveles = sorted(list(df["Nivel_Ord"].dropna().unique()), reverse=True)

    for _, r in df.iterrows():
        b_str = str(r.get("Bandeja", "1.1")).strip()
        mod_id = f"Módulo {b_str.split('.')[0]}" if "." in b_str else "Módulo 1"
        if mod_id not in modulos: modulos[mod_id] = {}
        if b_str not in modulos[mod_id]: modulos[mod_id][b_str] = []
        modulos[mod_id][b_str].append(r)

    html_modulos = ""
    for mod_nombre, bandejas_dict in sorted(modulos.items()):
        mod_num = mod_nombre.replace("Módulo ", "").strip()
        bandejas_ordenadas = sorted(bandejas_dict.keys(), reverse=True)
        html_bandejas = ""

        for b_nombre in bandejas_ordenadas:
            items = bandejas_dict[b_nombre]
            total_caras = sum([int(it.get("Caras", 1)) if str(it.get("Caras", 1)).isdigit() else 1 for it in items])
            nivel_num = b_nombre.split(".")[-1] if "." in b_nombre else "1"

            cards_html = ""
            for it in items:
                pos = it.get("N°", "-")
                if pd.isna(pos): pos = "-"
                
                cod_real = str(it.get("COD REAL", ""))
                ean = str(it.get("EAN", ""))
                nombre = str(it.get("Descripción", it.get("Nombre", "")))
                marca = str(it.get("Marca", "S/M"))
                estado = str(it.get("Estado", ""))
                top_ventas = str(it.get("TOPVENTAS", "")).strip().upper()
                caras_val = str(it.get("Caras", "1"))
                caras = caras_val if caras_val.isdigit() and int(caras_val) > 0 else "1"

                stock_val = safe_float(it.get("Stock", 0))
                cob_val = safe_float(it.get("Cobertura", 0))
                venta_val = safe_float(it.get("Venta", 0))
                part_val = safe_float(it.get("% Part", 0))
                
                part_fmt = format_pct(part_val)
                bg_color, text_color, cat_leyenda = obtener_estado_y_color(estado, stock_val)
                es_top = top_ventas == "TOP"
                border_style = "border: 3px solid #FFC000;" if es_top else "border: 1px solid #7f7f7f;"
                estilo_cobertura = "color: red; font-weight: bold;" if cob_val >= 30 else ""
                
                stock_fmt = f"{stock_val:.2f}"
                cob_fmt = f"{cob_val:.2f}"
                venta_fmt = f"{venta_val:.2f}"

                cards_html += f"""
                <div class="sku-card" style="flex: {caras}; background-color: {bg_color}; {border_style}" 
                     data-brand="{marca}" data-name="{nombre}" data-ean="{ean}" data-top="{top_ventas}"
                     data-stock="{stock_fmt}" data-cob="{cob_fmt}" data-venta="{venta_fmt}" data-part="{part_fmt}" data-cod="{cod_real}" data-cat="{cat_leyenda}">
                  <div class="sku-pos">{pos}</div>
                  <div class="sku-caras-tag">{caras} C</div>
                  <div class="sku-details">
                    <span class="sku-brand-text" style="color: {text_color};">{marca}</span>
                    <span class="sku-name-text" style="color: #000000;">{nombre}</span>
                    <span style="font-size: 0.65rem; color: {text_color}; font-weight: 800; margin-top: 2px;">Stock: {stock_fmt}</span>
                  </div>
                  <div class="sku-bottom-bar" style="border-top-color: {text_color};">
                    <span class="sku-ean-code" style="color: {text_color};">EAN: {ean}</span>
                    <span class="sku-cap-val" style="{estilo_cobertura}">Cob: {cob_fmt}</span>
                  </div>
                </div>
                """

            html_bandejas += f"""
            <div class="shelf-row" data-level="{nivel_num}">
              <div class="shelf-info"><span>BANDEJA {b_nombre}</span><span class="shelf-caras-count">{total_caras} CARAS</span></div>
              <div class="shelf-products">
                {cards_html}
              </div>
              <div class="shelf-bottom-rail"></div>
            </div>
            """

        html_modulos += f"""
        <div class="bay-column" data-module="{mod_num}">
          <div class="bay-title">{mod_nombre.upper()}</div>
          <div class="bay-shelves">
            {html_bandejas}
          </div>
        </div>
        """

    options_marcas = "".join([f'<option value="{m}">{m}</option>' for m in todas_marcas])
    options_modulos = "".join([f'<option value="{k.replace("Módulo ", "")}">{k}</option>' for k in modulos.keys()])
    options_niveles = "".join([f'<option value="{int(lvl)}">Bandeja {int(lvl)}</option>' for lvl in todos_niveles])

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
      <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #070d19; color: #fff; margin: 0; padding: 12px; touch-action: pan-x pan-y pinch-zoom; }}
        
        ::-webkit-scrollbar {{ height: 8px; width: 8px; }}
        ::-webkit-scrollbar-track {{ background: #0f172a; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb {{ background: #3b82f6; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #2563eb; }}

        .kpi-container {{ display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; justify-content: center; }}
        .kpi-card {{ flex: 1; min-width: 120px; background: #111c30; border: 1px solid #1e3a8a; border-radius: 8px; padding: 14px 10px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.4); }}
        .kpi-title {{ font-size: 0.65rem; font-weight: 800; color: #93c5fd; text-transform: uppercase; margin-bottom: 6px; display: block; letter-spacing: 0.5px; }}
        .kpi-val {{ font-size: 1.8rem; font-weight: 900; line-height: 1; display: block; }}
        
        .filter-panel {{ background: #111c30; border: 1px solid #1e3a8a; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 14px; align-items: flex-end; }}
        .filter-group {{ display: flex; flex-direction: column; gap: 4px; flex-grow: 1; }}
        .filter-label {{ font-size: 0.7rem; font-weight: 700; color: #93c5fd; text-transform: uppercase; }}
        .filter-select, .filter-input {{ background: #ffffff; border: 2px solid #3b82f6; color: #0f172a; padding: 6px 10px; border-radius: 4px; font-size: 0.85rem; font-weight: 600; outline: none; width: 100%; min-width: 140px; }}
        .btn-group {{ display: flex; gap: 8px; margin-left: auto; flex-wrap: wrap; }}
        
        .filter-btn-reset {{ background: #ef4444; border: none; color: white; font-weight: 700; font-size: 0.75rem; padding: 8px 14px; border-radius: 4px; cursor: pointer; transition: background 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
        .filter-btn-print {{ background: #10b981; border: none; color: white; font-weight: 700; font-size: 0.75rem; padding: 8px 14px; border-radius: 4px; cursor: pointer; transition: background 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
        .filter-btn-fs {{ background: #8b5cf6; border: none; color: white; font-weight: 700; font-size: 0.75rem; padding: 8px 14px; border-radius: 4px; cursor: pointer; transition: background 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
        
        .legend-panel {{ background: #111c30; border: 1px solid #1e3a8a; border-radius: 8px; padding: 10px 16px; margin-bottom: 16px; display: flex; align-items: center; flex-wrap: wrap; gap: 10px; }}
        .legend-title {{ font-size: 0.75rem; font-weight: 700; color: #93c5fd; text-transform: uppercase; margin-right: 8px; }}
        .legend-chips {{ display: flex; flex-wrap: wrap; gap: 8px; }}
        .legend-chip {{ background: var(--bg); color: var(--tc); border: var(--bd, 1px solid transparent); font-weight: 700; font-size: 0.70rem; padding: 5px 10px; border-radius: 20px; cursor: pointer; transition: all 0.2s; opacity: 0.85; box-shadow: 0 2px 4px rgba(0,0,0,0.2); outline: none; }}
        .legend-chip.active {{ opacity: 1; transform: scale(1.05); box-shadow: 0 0 12px rgba(59, 130, 246, 0.9); border: 2px solid #3b82f6 !important; }}
        
        .aisle-wrapper {{ display: flex; align-items: stretch; gap: 8px; width: 100%; position: relative; }}
        .nav-btn {{ background: #1e3a8a; color: white; border: 2px solid #3b82f6; border-radius: 8px; width: 40px; font-size: 1.5rem; font-weight: bold; cursor: pointer; z-index: 10; display: flex; align-items: center; justify-content: center; transition: all 0.2s; flex-shrink: 0; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }}
        .nav-btn:disabled {{ background: #0f172a; border-color: #334155; color: #475569; cursor: not-allowed; box-shadow: none; }}
        
        .aisle-container {{ display: flex; flex-direction: row; gap: 16px; background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 16px; overflow-x: auto; scroll-behavior: smooth; scroll-snap-type: x mandatory; flex-grow: 1; touch-action: pan-x pan-y pinch-zoom; }}
        
        .bay-column {{ flex: 1 0 480px; max-width: 100%; background: #111c30; border: 1.5px solid #1e293b; border-radius: 6px; display: flex; flex-direction: column; scroll-snap-align: center; transition: all 0.3s; }}
        .bay-column.hidden {{ display: none !important; }}
        
        .bay-title {{ background: #1e3a8a; padding: 8px; font-size: 0.85rem; font-weight: 700; text-align: center; border-bottom: 2px solid #3b82f6; border-radius: 4px 4px 0 0; }}
        .bay-shelves {{ padding: 10px; display: flex; flex-direction: column; gap: 14px; flex-grow: 1; }}
        .shelf-row {{ display: flex; flex-direction: column; background: #162238; border-radius: 4px; transition: all 0.3s; }}
        .shelf-row.hidden {{ display: none !important; }}
        .shelf-info {{ background: rgba(30, 58, 138, 0.8); padding: 4px 8px; font-size: 0.7rem; font-weight: 700; display: flex; justify-content: space-between; border-left: 3px solid #60a5fa; }}
        .shelf-caras-count {{ background: rgba(0, 0, 0, 0.4); padding: 1px 6px; border-radius: 3px; color: #93c5fd; font-size: 0.65rem; }}
        
        .shelf-products {{ display: flex; flex-direction: row; gap: 4px; padding: 6px; min-height: 125px; overflow-x: auto; padding-bottom: 8px; }}
        
        .sku-card {{ border-radius: 4px; padding: 6px; display: flex; flex-direction: column; justify-content: space-between; min-width: 95px; position: relative; transition: all 0.2s; cursor: pointer; }}
        .sku-card.dimmed {{ opacity: 0.2; filter: grayscale(1); }}
        .sku-card.highlighted {{ box-shadow: 0 0 12px rgba(59, 130, 246, 0.9); transform: scale(1.02); z-index: 5; border-color: #3b82f6 !important; }}
        .sku-pos {{ position: absolute; top: 4px; left: 4px; background: #0f172a; color: #fff; font-size: 0.6rem; font-weight: 800; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; border-radius: 2px; }}
        .sku-caras-tag {{ position: absolute; top: 4px; right: 4px; background: rgba(255,255,255,0.9); color: #000; font-size: 0.55rem; font-weight: 800; padding: 1px 4px; border-radius: 2px; }}
        .sku-details {{ margin-top: 18px; display: flex; flex-direction: column; gap: 3px; text-align: center; overflow: hidden; }}
        .sku-brand-text {{ font-size: 0.65rem; font-weight: 800; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .sku-name-text {{ font-size: 0.70rem; font-weight: 700; line-height: 1.15; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }}
        .sku-bottom-bar {{ margin-top: 4px; border-top: 1px dashed; padding-top: 2px; display: flex; justify-content: space-between; align-items: center; gap: 4px; }}
        .sku-ean-code {{ font-size: 0.60rem; font-family: monospace; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-shrink: 1; }}
        .sku-cap-val {{ font-size: 0.65rem; font-weight: 800; padding: 1px 3px; border-radius: 2px; flex-shrink: 0; }}
        .shelf-bottom-rail {{ height: 8px; background: linear-gradient(180deg, #94a3b8 0%, #475569 100%); border-radius: 0 0 3px 3px; }}
        
        .aisle-container.single-module {{ justify-content: center; }}
        .aisle-container.single-module .bay-column {{ flex: 1 1 100%; max-width: 100%; min-width: unset; }}
        .aisle-container.single-module .shelf-products {{ overflow-x: hidden; justify-content: center; gap: 2px; }}
        .aisle-container.single-module .sku-card {{ min-width: 40px !important; padding: 4px; }}
        .aisle-container.single-module .sku-name-text {{ font-size: 0.60rem; -webkit-line-clamp: 4; }}
        .aisle-container.single-module .sku-pos,
        .aisle-container.single-module .sku-caras-tag {{ font-size: 0.5rem; padding: 1px 2px; }}
        .aisle-container.single-module .sku-bottom-bar {{ flex-direction: column; align-items: center; gap: 1px; font-size: 0.55rem; }}
        .aisle-container.single-module .sku-ean-code {{ max-width: 100%; }}
        
        .modal-overlay {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 9999; opacity: 0; pointer-events: none; transition: opacity 0.2s; }}
        .modal-overlay.active {{ opacity: 1; pointer-events: auto; }}
        .modal-content {{ background: #1e293b; color: #fff; padding: 24px; border-radius: 8px; width: 90%; max-width: 450px; position: relative; box-shadow: 0 10px 30px rgba(0,0,0,0.8); transform: translateY(20px); transition: transform 0.2s; border: 2px solid #3b82f6; }}
        .modal-overlay.active .modal-content {{ transform: translateY(0); }}
        .modal-close {{ position: absolute; top: 10px; right: 15px; font-size: 1.8rem; cursor: pointer; color: #94a3b8; font-weight: bold; line-height: 1; }}
        .m-row {{ border-bottom: 1px solid #334155; padding: 10px 0; display: flex; justify-content: space-between; font-size: 0.9rem; }}
        .m-label {{ font-weight: 700; color: #93c5fd; }}
        .m-val {{ font-weight: 600; text-align: right; max-width: 65%; word-wrap: break-word; }}

        @media (max-width: 768px) {{
            .kpi-card {{ flex: 1 1 30%; min-width: 30%; padding: 8px 4px; }}
            .kpi-val {{ font-size: 1.2rem; }}
            .kpi-title {{ font-size: 0.55rem; }}
            .filter-panel {{ flex-direction: column; align-items: stretch; gap: 8px; }}
            .btn-group {{ justify-content: center; width: 100%; margin-top: 4px; }}
            .legend-chips {{ justify-content: center; }}
            .nav-btn {{ width: 22px; font-size: 1.2rem; border-width: 1px; padding: 0; }}
            .aisle-wrapper {{ gap: 4px; }}
            .bay-column {{ flex: 0 0 100%; max-width: 100%; margin-right: 0; }}
            .sku-card {{ min-width: 80px; }}
            .aisle-container.single-module .bay-column {{ flex: 1 0 100%; }}
        }}
      </style>
    </head>
    <body>

      <div id="productModal" class="modal-overlay">
        <div class="modal-content">
          <span class="modal-close">&times;</span>
          <h3 id="m-name" style="margin-top: 0; font-size: 1.1rem; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; line-height: 1.3;">Producto</h3>
          <div class="m-row"><span class="m-label">Cód. Real:</span><span class="m-val" id="m-cod"></span></div>
          <div class="m-row"><span class="m-label">EAN:</span><span class="m-val" id="m-ean"></span></div>
          <div class="m-row"><span class="m-label">Marca:</span><span class="m-val" id="m-brand"></span></div>
          <div class="m-row"><span class="m-label">Stock Actual:</span><span class="m-val" id="m-stock"></span></div>
          <div class="m-row"><span class="m-label">Cobertura:</span><span class="m-val" id="m-cob"></span></div>
          <div class="m-row"><span class="m-label">Ventas:</span><span class="m-val" id="m-venta"></span></div>
          <div class="m-row"><span class="m-label">% Participación:</span><span class="m-val" id="m-part"></span></div>
          <div class="m-row" style="border-bottom: none;"><span class="m-label">Top Ventas:</span><span class="m-val" id="m-top" style="color: #fbbf24; font-weight: 800;"></span></div>
        </div>
      </div>

      <div class="kpi-container">
        <div class="kpi-card" style="border-bottom: 4px solid #3b82f6;"><span class="kpi-title">Total SKUs</span><span class="kpi-val" id="t-total" style="color: #fff;">0</span></div>
        <div class="kpi-card" style="border-bottom: 4px solid #FFC7CE;"><span class="kpi-title">Bloqueados</span><span class="kpi-val" id="t-bloq" style="color: #FFC7CE;">0</span></div>
        <div class="kpi-card" style="border-bottom: 4px solid #F4B084;"><span class="kpi-title">Sin Stock (0)</span><span class="kpi-val" id="t-sin" style="color: #F4B084;">0</span></div>
        <div class="kpi-card" style="border-bottom: 4px solid #FFFF99;"><span class="kpi-title">Stock Bajo (1-5)</span><span class="kpi-val" id="t-bajo" style="color: #FFFF99;">0</span></div>
        <div class="kpi-card" style="border-bottom: 4px solid #C6EFCE;"><span class="kpi-title">Stock OK (>5)</span><span class="kpi-val" id="t-ok" style="color: #C6EFCE;">0</span></div>
        <div class="kpi-card" style="border-bottom: 4px solid #ef4444;"><span class="kpi-title">Cob. Alta (≥30)</span><span class="kpi-val" id="t-cob" style="color: #ef4444;">0</span></div>
        <div class="kpi-card" style="border-bottom: 4px solid #fbbf24;"><span class="kpi-title">★ Top Ventas</span><span class="kpi-val" id="t-top" style="color: #fbbf24;">0</span></div>
      </div>

      <div class="filter-panel">
        <div class="filter-group"><span class="filter-label">🔍 Buscar Producto</span><input type="text" id="searchInput" class="filter-input" placeholder="Nombre o EAN..."></div>
        <div class="filter-group"><span class="filter-label">🏷️ Marca</span><select id="brandSelect" class="filter-select"><option value="ALL">Todas</option>{options_marcas}</select></div>
        <div class="filter-group"><span class="filter-label">📦 Cuerpo / Módulo</span><select id="baySelect" class="filter-select"><option value="ALL">Todos</option>{options_modulos}</select></div>
        <div class="filter-group"><span class="filter-label">📶 Nivel / Bandeja</span><select id="levelSelect" class="filter-select"><option value="ALL">Todos</option>{options_niveles}</select></div>
        <div class="btn-group">
          <button id="resetBtn" class="filter-btn-reset">Restablecer</button>
          <button type="button" id="fullscreenBtn" class="filter-btn-fs" title="Ver Mueble Completo">🔲 Pantalla Completa</button>
        </div>
      </div>

      <div class="legend-panel">
        <span class="legend-title">📍 Leyenda Interactiva (Filtra módulos y resalta productos)</span>
        <div class="legend-chips">
          <button class="legend-chip" data-filter="bloqueado" style="--bg: #FFC7CE; --tc: #9C0006;">Bloqueado</button>
          <button class="legend-chip" data-filter="sin-stock" style="--bg: #F4B084; --tc: #833C0C;">Sin Stock</button>
          <button class="legend-chip" data-filter="stock-bajo" style="--bg: #FFFF99; --tc: #8A5A00;">Stock 1 a 5</button>
          <button class="legend-chip" data-filter="stock-ok" style="--bg: #C6EFCE; --tc: #006100;">Stock > 5</button>
          <button class="legend-chip" data-filter="cob-alta" style="--bg: #ffffff; --tc: #ef4444; --bd: 2px solid #ef4444;">Cobertura Alta</button>
          <button class="legend-chip" data-filter="top-ventas" style="--bg: #ffffff; --tc: #b45309; --bd: 2px solid #FFC000;">★ TOP VENTAS</button>
        </div>
      </div>

      <div class="aisle-wrapper">
        <button class="nav-btn" id="btnPrev" title="Módulo Anterior">❮</button>
        <div class="aisle-container" id="aisleContainer">
          {html_modulos}
        </div>
        <button class="nav-btn" id="btnNext" title="Módulo Siguiente">❯</button>
      </div>

      <script>
        const searchInput = document.getElementById('searchInput');
        const brandSelect = document.getElementById('brandSelect');
        const baySelect = document.getElementById('baySelect');
        const levelSelect = document.getElementById('levelSelect');
        const resetBtn = document.getElementById('resetBtn');

        let currentLegendFilter = null;
        const allBrands = Array.from(brandSelect.options).map(o => ({{val: o.value, text: o.text}}));
        const allBays = Array.from(baySelect.options).map(o => ({{val: o.value, text: o.text}}));
        const allLevels = Array.from(levelSelect.options).map(o => ({{val: o.value, text: o.text}}));

        function applyFilters() {{
          const query = searchInput.value.toLowerCase().trim();
          let selectedBrand = brandSelect.value;
          let selectedBay = baySelect.value;
          let selectedLevel = levelSelect.value;

          let availableBrands = new Set();
          let availableBays = new Set();
          let availableLevels = new Set();
          let cTot=0, cBloq=0, cSin=0, cBajo=0, cOk=0, cCob=0, cTop=0;
          let visibleBaysCount = 0;

          document.querySelectorAll('.sku-card').forEach(card => {{
             const brand = card.getAttribute('data-brand') || '';
             const bay = card.closest('.bay-column').getAttribute('data-module');
             const level = card.closest('.shelf-row').getAttribute('data-level');
             const name = (card.getAttribute('data-name') || '').toLowerCase();
             const ean = card.getAttribute('data-ean') || '';
             const cat = card.getAttribute('data-cat') || '';
             const isTop = card.getAttribute('data-top') === 'TOP';
             const cobVal = parseFloat(card.getAttribute('data-cob')) || 0;

             const matchSearch = (query === '' || name.includes(query) || ean.includes(query) || brand.toLowerCase().includes(query));
             const matchBrand = (selectedBrand === 'ALL' || brand === selectedBrand);
             const matchBay = (selectedBay === 'ALL' || bay === selectedBay);
             const matchLevel = (selectedLevel === 'ALL' || level === selectedLevel);

             const passesStandard = matchSearch && matchBrand && matchBay && matchLevel;

             if(matchSearch && matchBay && matchLevel) availableBrands.add(brand);
             if(matchSearch && matchBrand && matchLevel) availableBays.add(bay);
             if(matchSearch && matchBrand && matchBay) availableLevels.add(level);

             if(passesStandard) {{
                 cTot++;
                 if(cat === 'bloqueado') cBloq++;
                 if(cat === 'sin-stock') cSin++;
                 if(cat === 'stock-bajo') cBajo++;
                 if(cat === 'stock-ok') cOk++;
                 if(cobVal >= 30) cCob++;
                 if(isTop) cTop++;
             }}

             let passesLegend = true;
             if (currentLegendFilter) {{
                 if (currentLegendFilter === 'cob-alta') passesLegend = (cobVal >= 30);
                 else if (currentLegendFilter === 'top-ventas') passesLegend = isTop;
                 else passesLegend = (cat === currentLegendFilter);
             }}

             if (matchBrand && matchSearch) {{
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
                     card.classList.toggle('highlighted', (query !== '' || selectedBrand !== 'ALL'));
                 }}
             }} else {{
                 card.classList.add('dimmed');
                 card.classList.remove('highlighted');
             }}
          }});

          document.getElementById('t-total').textContent = cTot;
          document.getElementById('t-bloq').textContent = cBloq;
          document.getElementById('t-sin').textContent = cSin;
          document.getElementById('t-bajo').textContent = cBajo;
          document.getElementById('t-ok').textContent = cOk;
          document.getElementById('t-cob').textContent = cCob;
          document.getElementById('t-top').textContent = cTop;

          if (selectedBrand !== 'ALL' && !availableBrands.has(selectedBrand)) selectedBrand = 'ALL';
          if (selectedBay !== 'ALL' && !availableBays.has(selectedBay)) selectedBay = 'ALL';
          if (selectedLevel !== 'ALL' && !availableLevels.has(selectedLevel)) selectedLevel = 'ALL';

          brandSelect.innerHTML = '';
          allBrands.forEach(opt => {{ if(opt.val === 'ALL' || availableBrands.has(opt.val)) brandSelect.add(new Option(opt.text, opt.val, false, opt.val === selectedBrand)); }});

          baySelect.innerHTML = '';
          allBays.forEach(opt => {{ if(opt.val === 'ALL' || availableBays.has(opt.val)) baySelect.add(new Option(opt.text, opt.val, false, opt.val === selectedBay)); }});

          levelSelect.innerHTML = '';
          allLevels.forEach(opt => {{ if(opt.val === 'ALL' || availableLevels.has(opt.val)) levelSelect.add(new Option(opt.text, opt.val, false, opt.val === selectedLevel)); }});

          document.querySelectorAll('.bay-column').forEach(bay => {{
            const bayNum = bay.getAttribute('data-module');
            const passesBayFilter = (selectedBay === 'ALL' || selectedBay === bayNum);
            const hasMatch = Array.from(bay.querySelectorAll('.sku-card')).some(card => {{
                if (currentLegendFilter) return card.classList.contains('highlighted');
                return !card.classList.contains('dimmed');
            }});

            const isVisible = passesBayFilter && hasMatch;
            bay.classList.toggle('hidden', !isVisible);
            if (isVisible) visibleBaysCount++;
          }});

          const aisleContainer = document.getElementById('aisleContainer');
          if (visibleBaysCount === 1) {{ aisleContainer.classList.add('single-module'); }} 
          else {{ aisleContainer.classList.remove('single-module'); }}

          document.querySelectorAll('.shelf-row').forEach(shelf => {{
            const shelfLevel = shelf.getAttribute('data-level');
            const passesLevelFilter = (selectedLevel === 'ALL' || selectedLevel === shelfLevel);
            shelf.classList.toggle('hidden', !passesLevelFilter);
          }});
          
          updateScrollButtons();
        }}

        document.querySelectorAll('.legend-chip').forEach(chip => {{
            chip.addEventListener('click', () => {{
                const filter = chip.getAttribute('data-filter');
                if (currentLegendFilter === filter) {{
                    currentLegendFilter = null;
                    chip.classList.remove('active');
                }} else {{
                    document.querySelectorAll('.legend-chip').forEach(c => c.classList.remove('active'));
                    currentLegendFilter = filter;
                    chip.classList.add('active');
                }}
                applyFilters();
            }});
        }});

        searchInput.addEventListener('input', applyFilters);
        brandSelect.addEventListener('change', applyFilters);
        baySelect.addEventListener('change', applyFilters);
        levelSelect.addEventListener('change', applyFilters);
        
        resetBtn.addEventListener('click', () => {{
          searchInput.value = ''; currentLegendFilter = null;
          document.querySelectorAll('.legend-chip').forEach(c => c.classList.remove('active'));
          brandSelect.innerHTML = ''; allBrands.forEach(o => brandSelect.add(new Option(o.text, o.val)));
          baySelect.innerHTML = ''; allBays.forEach(o => baySelect.add(new Option(o.text, o.val)));
          levelSelect.innerHTML = ''; allLevels.forEach(o => levelSelect.add(new Option(o.text, o.val)));
          brandSelect.value = 'ALL'; baySelect.value = 'ALL'; levelSelect.value = 'ALL';
          applyFilters();
        }});

        const fsBtn = document.getElementById('fullscreenBtn');
        fsBtn.addEventListener('click', () => {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen().catch(err => console.log(err.message));
            }} else {{
                if (document.exitFullscreen) document.exitFullscreen();
            }}
        }});
        
        document.addEventListener('fullscreenchange', () => {{
            fsBtn.innerHTML = !document.fullscreenElement ? '🔲 Pantalla Completa' : '✖ Salir Pantalla Completa';
        }});

        const modal = document.getElementById('productModal');
        const closeBtn = document.querySelector('.modal-close');
        document.querySelectorAll('.sku-card').forEach(card => {{
            card.addEventListener('click', () => {{
                document.getElementById('m-name').textContent = card.getAttribute('data-name');
                document.getElementById('m-cod').textContent = card.getAttribute('data-cod');
                document.getElementById('m-ean').textContent = card.getAttribute('data-ean');
                document.getElementById('m-brand').textContent = card.getAttribute('data-brand');
                document.getElementById('m-stock').textContent = card.getAttribute('data-stock');
                document.getElementById('m-cob').textContent = card.getAttribute('data-cob');
                document.getElementById('m-venta').textContent = card.getAttribute('data-venta');
                document.getElementById('m-part').textContent = card.getAttribute('data-part');
                document.getElementById('m-top').textContent = card.getAttribute('data-top');
                modal.classList.add('active');
            }});
        }});
        closeBtn.addEventListener('click', () => modal.classList.remove('active'));
        window.addEventListener('click', (e) => {{ if(e.target === modal) modal.classList.remove('active'); }});

        const container = document.getElementById('aisleContainer');
        const btnPrev = document.getElementById('btnPrev');
        const btnNext = document.getElementById('btnNext');
        function updateScrollButtons() {{
            btnPrev.disabled = container.scrollLeft <= 10;
            btnNext.disabled = container.scrollLeft + container.clientWidth >= container.scrollWidth - 10;
        }}
        btnPrev.addEventListener('click', () => {{
            const visibleModule = container.querySelector('.bay-column:not(.hidden)');
            if(visibleModule) container.scrollBy({{ left: -(visibleModule.offsetWidth + 16), behavior: 'smooth' }});
        }});
        btnNext.addEventListener('click', () => {{
            const visibleModule = container.querySelector('.bay-column:not(.hidden)');
            if(visibleModule) container.scrollBy({{ left: (visibleModule.offsetWidth + 16), behavior: 'smooth' }});
        }});
        container.addEventListener('scroll', updateScrollButtons);
        window.addEventListener('resize', updateScrollButtons);
        setTimeout(applyFilters, 100);
      </script>
    </body>
    </html>
    """

# --- LÓGICA DE CARGA HÍBRIDA (NUBE + MANUAL) ---

@st.cache_data(ttl=14400) # Memoria caché de 4 horas
def cargar_datos_nube(url):
    try:
        # Ahora Pandas lee ambas hojas: MATRIZ y DATA_AUX
        try:
            df_matriz = pd.read_excel(url, sheet_name="MATRIZ", skiprows=5, usecols="C:AB")
        except Exception:
            df_matriz = pd.read_excel(url, skiprows=5, usecols="C:AB")
            
        try:
            df_aux = pd.read_excel(url, sheet_name="DATA_AUX", skiprows=5)
        except Exception:
            df_aux = pd.DataFrame()

        df_matriz.columns = [str(c).strip() for c in df_matriz.columns]
        
        if "Bandeja" in df_matriz.columns and "EAN" in df_matriz.columns:
            df_matriz = df_matriz.dropna(subset=["Bandeja", "EAN"], how="all")
            
        hora_lectura = pd.Timestamp.now('America/Lima').strftime("%d/%m/%Y - %I:%M %p")
        return df_matriz, df_aux, hora_lectura, None
    except Exception as e:
        return None, None, None, str(e)

# --- ENLACE DIRECTO DE GOOGLE DRIVE ---
URL_NUBE = "https://drive.google.com/uc?export=download&id=1QFqktucaF983WXcjupQI-jpeEZzWxtX_"

df_raw = None
df_aux_raw = None
info_hora = None
error_nube = None

# Botón de Sincronización Manual
col_sync1, col_sync2 = st.columns([1, 6])
with col_sync1:
    if st.button("🔄 Sincronizar Datos", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Intentar cargar desde Drive
with st.spinner("Sincronizando base de datos central..."):
    df_nube, df_aux_nube, info_hora, error_nube = cargar_datos_nube(URL_NUBE)

if df_nube is not None:
    df_raw = df_nube
    df_aux_raw = df_aux_nube
else:
    # Respaldo Manual si Drive falla
    st.warning("⚠️ No se pudo conectar a Google Drive. Puedes subir el archivo manualmente para continuar.")
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
            
            df_raw.columns = [str(c).strip() for c in df_raw.columns]
            if "Bandeja" in df_raw.columns and "EAN" in df_raw.columns:
                df_raw = df_raw.dropna(subset=["Bandeja", "EAN"], how="all")
                
            info_hora = pd.Timestamp.now('America/Lima').strftime("%d/%m/%Y - %I:%M %p (Carga Local)")
        except Exception as e:
            st.error(f"Error al leer el archivo manual: {e}")

# SI TENEMOS DATOS RENDERIZAMOS LA APP
if df_raw is not None:
    
    # ---------------------------------------------------------
    # 🔗 CRUCE DE TABLAS (BUSCARV): MATRIZ + DATA_AUX (Monto Margen)
    # ---------------------------------------------------------
    df_base = df_raw.copy()
    
    if df_aux_raw is not None and not df_aux_raw.empty:
        df_aux_raw.columns = [str(c).strip() for c in df_aux_raw.columns]
        
        if 'Material' in df_aux_raw.columns and 'Monto Margen' in df_aux_raw.columns:
            # Limpiamos los códigos para hacer el cruce perfecto (evitar que 1022988.0 no cruce con 1022988)
            df_aux_raw['Material_Str'] = df_aux_raw['Material'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            df_base['COD_REAL_Str'] = df_base['COD REAL'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            
            # Eliminamos duplicados de DATA_AUX por si acaso
            df_aux_unique = df_aux_raw.drop_duplicates(subset=['Material_Str'])
            
            # Cruce (Left Join)
            df_base = df_base.merge(df_aux_unique[['Material_Str', 'Monto Margen']], left_on='COD_REAL_Str', right_on='Material_Str', how='left')
            df_base.drop(columns=['Material_Str', 'COD_REAL_Str'], inplace=True, errors='ignore')
            
            # Llenar vacíos con 0
            df_base['Monto Margen'] = df_base['Monto Margen'].fillna(0)
        else:
            df_base['Monto Margen'] = 0.0
    else:
        df_base['Monto Margen'] = 0.0
    # ---------------------------------------------------------

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; margin-bottom: 20px;">
        <div>
            <h1 style="margin: 0; font-size: 2.2rem; color: #fff;">📦 Planograma 2.0</h1>
            <span style="color: #93c5fd; font-size: 0.9rem;">Análisis interactivo de pasillos en tiempo real</span>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.95rem; color: #cbd5e1;">Desarrollado por <b>Alfredo HM</b></div>
            <div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">Última actualización: {info_hora}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🛒 Vista Interactiva del Pasillo", "📊 Dashboard y Reporte Excel"])
    
    with tab1:
        
        # ==========================================
        # ⚙️ MÓDULO DE SEGMENTACIÓN DINÁMICA
        # ==========================================
        st.markdown("### ⚙️ Segmentación Dinámica de Ventas")
        col_cfg1, col_cfg2 = st.columns([1, 3])
        
        with col_cfg1:
            top_n = st.number_input("🏆 Resaltar TOP Ventas (Cantidad de SKUs):", min_value=1, max_value=200, value=30, step=1)
        
        df_base['Venta_Num'] = df_base['Venta'].apply(safe_float)
        df_base['Part_Num'] = df_base['% Part'].apply(safe_float)
        
        df_unicos = df_base.drop_duplicates(subset=['COD REAL']).copy()
        df_unicos = df_unicos[df_unicos['COD REAL'].notna()]
        
        df_unicos = df_unicos.sort_values(by='Venta_Num', ascending=False)
        
        skus_top = df_unicos.head(top_n)['COD REAL'].astype(str).str.strip().tolist()
        part_acumulada = df_unicos.head(top_n)['Part_Num'].sum()
        
        with col_cfg2:
            st.write("") 
            st.info(f"💡 Has seleccionado el **TOP {top_n}**. Estos {top_n} productos concentran el **{part_acumulada*100:.2f}%** de la venta total de la categoría.")

        df_base['TOPVENTAS'] = df_base['COD REAL'].astype(str).str.strip().apply(lambda x: "TOP" if x in skus_top else "NO")
        # ==========================================

        st.markdown("---")
        st.markdown("##### Control de Vista")
        mobile_preview = st.toggle("📱 Simular Vista Móvil (Celular)")
        
        html_pasillo = generar_html_pasillo_interactivo(df_base)
        
        if mobile_preview:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.markdown("""
                <div style='
                    border: 12px solid #1e293b; 
                    border-radius: 36px; 
                    padding: 0; 
                    background: #000; 
                    box-shadow: 0 20px 40px rgba(0,0,0,0.5); 
                    max-width: 400px; 
                    margin: 0 auto;
                    overflow: hidden;'>
                """, unsafe_allow_html=True)
                components.html(html_pasillo, height=850, scrolling=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            components.html(html_pasillo, height=1300, scrolling=True)
            
    with tab2:
        st.markdown("### 📈 Análisis Financiero: Ventas vs Margen por Módulo")
        
        df_chart = df_base.copy()
        df_chart['Margen_Num'] = df_chart['Monto Margen'].apply(safe_float)
        
        bandeja_str = df_chart.get('Bandeja', pd.Series(["1.1"]*len(df_chart))).astype(str)
        df_chart['Modulo_Ord'] = bandeja_str.str.extract(r'(\d+)\.(\d+)')[0]
        df_chart['Modulo_Ord'] = pd.to_numeric(df_chart['Modulo_Ord'], errors='coerce').fillna(1)
        
        # AGRUPACIÓN DE TOTALES POR MÓDULO
        ventas_mod = df_chart.groupby('Modulo_Ord').agg(
            Venta_Total=('Venta_Num', 'sum'),
            Margen_Total=('Margen_Num', 'sum'),
            SKUs_Total=('COD REAL', 'count')
        ).reset_index()
        
        ventas_mod['Módulo'] = "Módulo " + ventas_mod['Modulo_Ord'].astype(int).astype(str)
        
        # CÁLCULO DEL MARGEN REAL % DEL MÓDULO COMPLETO
        ventas_mod['Margen_Pct'] = ventas_mod.apply(
            lambda row: row['Margen_Total'] / row['Venta_Total'] if row['Venta_Total'] > 0 else 0, 
            axis=1
        )
        
        col_ord, _ = st.columns([1, 3])
        with col_ord:
            orden_grafico = st.selectbox("Ordenar Gráfico por:", 
                ["Módulo (Secuencial)", "Mayor a Menor Venta", "Menor a Mayor Venta", "Mayor Margen (%)"]
            )
            
        if orden_grafico == "Mayor a Menor Venta":
            ventas_mod = ventas_mod.sort_values('Venta_Total', ascending=False)
        elif orden_grafico == "Menor a Mayor Venta":
            ventas_mod = ventas_mod.sort_values('Venta_Total', ascending=True)
        elif orden_grafico == "Mayor Margen (%)":
            ventas_mod = ventas_mod.sort_values('Margen_Pct', ascending=False)
        else:
            ventas_mod = ventas_mod.sort_values('Modulo_Ord')

        # ---------------------------------------------------------
        # 🎨 REDISEÑO DEL GRÁFICO (DARK MODE BI)
        # ---------------------------------------------------------
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Barras de Venta (Azul Translúcido)
        fig.add_trace(
            go.Bar(
                x=ventas_mod['Módulo'], 
                y=ventas_mod['Venta_Total'],
                name="Ventas Totales (S/)",
                text=ventas_mod['Venta_Total'].apply(lambda x: f"S/ {x:,.0f}"),
                textposition='auto',
                marker=dict(
                    color='rgba(59, 130, 246, 0.7)',
                    line=dict(color='#3b82f6', width=2)
                ),
                hovertemplate="<b>%{x}</b><br>Ventas: S/ %{y:,.2f}<br>Cant. SKUs: %{customdata}<extra></extra>",
                customdata=ventas_mod['SKUs_Total']
            ),
            secondary_y=False
        )

        # Línea de Margen % (Verde Neón)
        fig.add_trace(
            go.Scatter(
                x=ventas_mod['Módulo'], 
                y=ventas_mod['Margen_Pct'],
                name="Margen %",
                mode="lines+markers+text",
                text=ventas_mod['Margen_Pct'].apply(lambda x: f"{x*100:,.1f}%"),
                textposition='top center',
                textfont=dict(color='#10b981', size=13, weight='bold'),
                marker=dict(
                    color="#10b981", 
                    size=10, 
                    symbol='circle', 
                    line=dict(color='#ffffff', width=2)
                ),
                line=dict(color="#10b981", width=4, shape='spline'),
                hovertemplate="<b>%{x}</b><br>Margen: %{text}<extra></extra>"
            ),
            secondary_y=True
        )

        # Diseño de Fondo y Ejes
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(color='#cbd5e1')),
            margin=dict(t=50, b=20, l=20, r=20),
            xaxis=dict(showgrid=False, color='#cbd5e1', tickfont=dict(size=12, weight='bold')),
            yaxis=dict(
                title="Ventas (S/)", 
                showgrid=True, 
                gridcolor='rgba(255,255,255,0.1)', 
                color='#cbd5e1', 
                zeroline=False
            ),
            yaxis2=dict(
                title="Margen (%)", 
                showgrid=False, 
                color='#10b981', 
                zeroline=False
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        # ---------------------------------------------------------
        
        st.markdown("---")
        st.markdown("### 📋 Reporte Detallado y Exportación")
        
        col_filt, col_btn = st.columns([2, 1])
        with col_filt:
            filtro_reporte = st.selectbox("Filtrar Tabla Resumen:", [
                "Todos los SKUs",
                "Bloqueados (Estado B)",
                "Sin Stock (Stock = 0)",
                "Stock Bajo (Stock 1 a 5)",
                "Top Ventas (TOP)",
                "Cobertura Alta (≥ 30)"
            ])
        
        df_rep = df_base.copy()
        
        if filtro_reporte == "Bloqueados (Estado B)":
            df_rep = df_rep[df_rep['Estado'].astype(str).str.strip().str.upper() == 'B']
        elif filtro_reporte == "Sin Stock (Stock = 0)":
            df_rep = df_rep[(df_rep['Estado'].astype(str).str.strip().str.upper() == 'A') & (df_rep['Stock_Num'] <= 0)]
        elif filtro_reporte == "Stock Bajo (Stock 1 a 5)":
            df_rep = df_rep[(df_rep['Estado'].astype(str).str.strip().str.upper() == 'A') & (df_rep['Stock_Num'] > 0) & (df_rep['Stock_Num'] <= 5)]
        elif filtro_reporte == "Top Ventas (TOP)":
            df_rep = df_rep[df_rep['TOPVENTAS'].astype(str).str.strip().str.upper() == 'TOP']
        elif filtro_reporte == "Cobertura Alta (≥ 30)":
            df_rep = df_rep[df_rep['Cob_Num'] >= 30]
            
        col_desc = 'Descripción' if 'Descripción' in df_rep.columns else 'Nombre'
        cols_to_show = ['Bandeja', 'N°', 'COD REAL', 'EAN', col_desc, 'Marca', 'Stock', 'Cobertura', 'Venta', 'Monto Margen', 'TOPVENTAS']
        cols_to_show = [c for c in cols_to_show if c in df_rep.columns]
        
        with col_btn:
            st.write("") 
            st.write("")
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_rep[cols_to_show].to_excel(writer, index=False, sheet_name='Reporte')
            
            st.download_button(
                label="📥 Descargar a Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name="reporte_planograma_financiero.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        st.dataframe(df_rep[cols_to_show], use_container_width=True, hide_index=True, height=800)
