import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Planograma 2.0",
    page_icon="📦",
    layout="wide",
)

st.title("📦 Planograma 2.0")
st.markdown("Carga tu base de datos en Excel (hoja MATRIZ) para generar la vista interactiva del pasillo.")
st.markdown("---")

# --- FUNCIONES DE APOYO Y LIMPIEZA ---
def safe_float(val, default=0.0):
    if pd.isna(val): return default
    try:
        if isinstance(val, str):
            val = val.replace('%', '').replace(',', '').strip()
        return float(val)
    except (ValueError, TypeError):
        return default

def obtener_color_estado_stock(estado, stock_val):
    estado = str(estado).strip().upper()
    if estado == "B": return "#FFC7CE", "#9C0006"
    elif estado == "A":
        if stock_val <= 0: return "#F4B084", "#833C0C"
        elif stock_val <= 5: return "#FFFF99", "#8A5A00"
        else: return "#C6EFCE", "#006100"
    else: return "#D9D9D9", "#000000"

# --- GENERADOR DEL PASILLO HTML COMPLETO ---
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
                
                part_fmt = f"{part_val*100:.2f}%" if part_val < 1 else f"{part_val:.2f}%"

                bg_color, text_color = obtener_color_estado_stock(estado, stock_val)
                es_top = top_ventas == "TOP"
                border_style = "border: 3px solid #FFC000;" if es_top else "border: 1px solid #7f7f7f;"
                estilo_cobertura = "color: red; font-weight: bold;" if cob_val >= 30 else ""
                
                stock_fmt = f"{stock_val:.2f}"
                cob_fmt = f"{cob_val:.2f}"
                venta_fmt = f"{venta_val:.2f}"

                cards_html += f"""
                <div class="sku-card" style="flex: {caras}; background-color: {bg_color}; {border_style}" 
                     data-brand="{marca}" data-name="{nombre}" data-ean="{ean}" data-top="{top_ventas}"
                     data-stock="{stock_fmt}" data-cob="{cob_fmt}" data-venta="{venta_fmt}" data-part="{part_fmt}" data-cod="{cod_real}">
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
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #070d19; color: #fff; margin: 0; padding: 12px; }}
        
        .filter-panel {{ background: #111c30; border: 1px solid #1e3a8a; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 14px; align-items: flex-end; }}
        .filter-group {{ display: flex; flex-direction: column; gap: 4px; }}
        .filter-label {{ font-size: 0.7rem; font-weight: 700; color: #93c5fd; text-transform: uppercase; }}
        .filter-select, .filter-input {{ background: #0b132b; border: 1px solid #3b82f6; color: #fff; padding: 6px 10px; border-radius: 4px; font-size: 0.8rem; outline: none; min-width: 140px; }}
        .filter-input {{ min-width: 200px; }}
        
        /* Selects Desactivados (Opciones Incompatibles) */
        .filter-select option:disabled {{ color: #475569; font-style: italic; }}
        
        .btn-group {{ display: flex; gap: 8px; margin-left: auto; }}
        .filter-btn-reset {{ background: #ef4444; border: none; color: white; font-weight: 700; font-size: 0.75rem; padding: 8px 14px; border-radius: 4px; cursor: pointer; transition: background 0.2s; }}
        .filter-btn-print {{ background: #10b981; border: none; color: white; font-weight: 700; font-size: 0.75rem; padding: 8px 14px; border-radius: 4px; cursor: pointer; transition: background 0.2s; }}
        
        .aisle-wrapper {{ display: flex; align-items: stretch; gap: 8px; width: 100%; position: relative; }}
        .nav-btn {{ background: #1e3a8a; color: white; border: 2px solid #3b82f6; border-radius: 8px; width: 45px; font-size: 1.5rem; font-weight: bold; cursor: pointer; z-index: 10; display: flex; align-items: center; justify-content: center; transition: all 0.2s; flex-shrink: 0; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }}
        .nav-btn:hover {{ background: #3b82f6; }}
        .nav-btn:active {{ transform: scale(0.95); }}
        .nav-btn:disabled {{ background: #0f172a; border-color: #334155; color: #475569; cursor: not-allowed; box-shadow: none; }}

        .aisle-container {{ display: flex; flex-direction: row; gap: 16px; background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 16px; overflow-x: auto; scroll-behavior: smooth; scroll-snap-type: x mandatory; flex-grow: 1; -ms-overflow-style: none; scrollbar-width: none; }}
        .aisle-container::-webkit-scrollbar {{ display: none; }}
        
        .bay-column {{ flex: 0 0 460px; background: #111c30; border: 1.5px solid #1e293b; border-radius: 6px; display: flex; flex-direction: column; scroll-snap-align: center; }}
        .bay-column.hidden {{ display: none !important; }}
        .bay-title {{ background: #1e3a8a; padding: 8px; font-size: 0.85rem; font-weight: 700; text-align: center; border-bottom: 2px solid #3b82f6; border-radius: 4px 4px 0 0; }}
        .bay-shelves {{ padding: 10px; display: flex; flex-direction: column; gap: 14px; flex-grow: 1; }}
        
        .shelf-row {{ display: flex; flex-direction: column; background: #162238; border-radius: 4px; }}
        .shelf-row.hidden {{ display: none !important; }}
        .shelf-info {{ background: rgba(30, 58, 138, 0.8); padding: 4px 8px; font-size: 0.7rem; font-weight: 700; display: flex; justify-content: space-between; border-left: 3px solid #60a5fa; }}
        .shelf-caras-count {{ background: rgba(0, 0, 0, 0.4); padding: 1px 6px; border-radius: 3px; color: #93c5fd; font-size: 0.65rem; }}
        .shelf-products {{ display: flex; flex-direction: row; gap: 4px; padding: 6px; min-height: 125px; overflow-x: auto; }}
        
        .sku-card {{ border-radius: 4px; padding: 6px; display: flex; flex-direction: column; justify-content: space-between; min-width: 110px; position: relative; transition: all 0.2s; cursor: pointer; }}
        .sku-card.dimmed {{ opacity: 0.15; filter: grayscale(1); }}
        .sku-card.highlighted {{ box-shadow: 0 0 12px rgba(59, 130, 246, 0.9); transform: scale(1.02); z-index: 5; border-color: #3b82f6 !important; }}
        
        .sku-pos {{ position: absolute; top: 4px; left: 4px; background: #0f172a; color: #fff; font-size: 0.6rem; font-weight: 800; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; border-radius: 2px; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }}
        .sku-caras-tag {{ position: absolute; top: 4px; right: 4px; background: rgba(255,255,255,0.9); color: #000; font-size: 0.55rem; font-weight: 800; padding: 1px 4px; border-radius: 2px; border: 1px solid #ccc; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }}
        .sku-details {{ margin-top: 18px; display: flex; flex-direction: column; gap: 3px; text-align: center; }}
        .sku-brand-text {{ font-size: 0.65rem; font-weight: 800; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .sku-name-text {{ font-size: 0.72rem; font-weight: 700; line-height: 1.15; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
        .sku-bottom-bar {{ margin-top: 4px; border-top: 1px dashed; padding-top: 2px; display: flex; justify-content: space-between; align-items: center; gap: 4px; }}
        .sku-ean-code {{ font-size: 0.60rem; font-family: monospace; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-shrink: 1; }}
        .sku-cap-val {{ font-size: 0.65rem; font-weight: 800; padding: 1px 3px; border-radius: 2px; flex-shrink: 0; }}
        .shelf-bottom-rail {{ height: 8px; background: linear-gradient(180deg, #94a3b8 0%, #475569 100%); border-radius: 0 0 3px 3px; }}

        .modal-overlay {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 9999; opacity: 0; pointer-events: none; transition: opacity 0.2s; }}
        .modal-overlay.active {{ opacity: 1; pointer-events: auto; }}
        .modal-content {{ background: #1e293b; color: #fff; padding: 24px; border-radius: 8px; width: 90%; max-width: 450px; position: relative; box-shadow: 0 10px 30px rgba(0,0,0,0.8); transform: translateY(20px); transition: transform 0.2s; border: 2px solid #3b82f6; }}
        .modal-overlay.active .modal-content {{ transform: translateY(0); }}
        .modal-close {{ position: absolute; top: 10px; right: 15px; font-size: 1.8rem; cursor: pointer; color: #94a3b8; font-weight: bold; line-height: 1; }}
        .modal-close:hover {{ color: #fff; }}
        .m-row {{ border-bottom: 1px solid #334155; padding: 10px 0; display: flex; justify-content: space-between; font-size: 0.9rem; }}
        .m-label {{ font-weight: 700; color: #93c5fd; }}
        .m-val {{ font-weight: 600; text-align: right; max-width: 65%; word-wrap: break-word; }}

        @media (max-width: 768px) {{
            .filter-panel {{ flex-direction: column; align-items: stretch; }}
            .btn-group {{ justify-content: space-between; width: 100%; margin-top: 8px; }}
            .bay-column {{ flex: 0 0 85vw; }}
            .nav-btn {{ width: 35px; font-size: 1.2rem; }}
            .sku-card {{ min-width: 100px; }}
        }}

        @media print {{
          @page {{ size: landscape; margin: 5mm; }}
          body {{ background-color: #fff !important; color: #000 !important; }}
          .filter-panel, .modal-overlay, .nav-btn {{ display: none !important; }}
          .aisle-wrapper {{ display: block; }}
          .aisle-container {{ display: block; border: none !important; background: #fff !important; padding: 0; }}
          .bay-column {{ background: #fff !important; border: 2px solid #000 !important; width: 100% !important; margin-bottom: 20px; page-break-inside: avoid; }}
          .bay-title {{ background: #e2e8f0 !important; color: #000 !important; border-bottom: 2px solid #000 !important; }}
          .shelf-row {{ background: #fff !important; border: 1px solid #000 !important; page-break-inside: avoid; }}
          .shelf-info {{ background: #f1f5f9 !important; color: #000 !important; border-left: 3px solid #000 !important; }}
          .sku-card {{ background: #fff !important; border: 1px solid #000 !important; color: #000 !important; }}
          .sku-card[data-top="TOP"] {{ border: 4px double #000 !important; }}
          .sku-pos, .sku-caras-tag {{ background: #fff !important; color: #000 !important; border: 1px solid #000 !important; }}
          .sku-brand-text, .sku-name-text, .sku-ean-code, span {{ color: #000 !important; }}
          .sku-bottom-bar {{ border-top: 1px dashed #000 !important; }}
          .shelf-bottom-rail {{ background: #000 !important; height: 3px !important; }}
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

      <div class="filter-panel">
        <div class="filter-group">
          <span class="filter-label">🔍 Buscar Producto</span>
          <input type="text" id="searchInput" class="filter-input" placeholder="Nombre o EAN...">
        </div>
        <div class="filter-group">
          <span class="filter-label">🏷️ Marca</span>
          <select id="brandSelect" class="filter-select"><option value="ALL">Todas</option>{options_marcas}</select>
        </div>
        <div class="filter-group">
          <span class="filter-label">📦 Cuerpo / Módulo</span>
          <select id="baySelect" class="filter-select"><option value="ALL">Todos</option>{options_modulos}</select>
        </div>
        <div class="filter-group">
          <span class="filter-label">📶 Nivel / Bandeja</span>
          <select id="levelSelect" class="filter-select"><option value="ALL">Todos</option>{options_niveles}</select>
        </div>
        
        <div class="btn-group">
          <button id="resetBtn" class="filter-btn-reset">Restablecer</button>
          <button type="button" class="filter-btn-print" onclick="window.print()">🖨️ Imprimir B/N</button>
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

        function applyFilters() {{
          const query = searchInput.value.toLowerCase().trim();
          const selectedBrand = brandSelect.value;
          const selectedBay = baySelect.value;
          const selectedLevel = levelSelect.value;

          // CONJUNTOS PARA FILTROS EN CASCADA
          let availableBrands = new Set();
          let availableBays = new Set();
          let availableLevels = new Set();

          // Analizar qué opciones son válidas basadas en las otras selecciones
          document.querySelectorAll('.sku-card').forEach(card => {{
             const brand = card.getAttribute('data-brand') || '';
             const bay = card.closest('.bay-column').getAttribute('data-module');
             const level = card.closest('.shelf-row').getAttribute('data-level');
             const name = (card.getAttribute('data-name') || '').toLowerCase();
             const ean = card.getAttribute('data-ean') || '';

             const matchSearch = (query === '' || name.includes(query) || ean.includes(query) || brand.toLowerCase().includes(query));
             const matchBrand = (selectedBrand === 'ALL' || brand === selectedBrand);
             const matchBay = (selectedBay === 'ALL' || bay === selectedBay);
             const matchLevel = (selectedLevel === 'ALL' || level === selectedLevel);

             if(matchSearch && matchBay && matchLevel) availableBrands.add(brand);
             if(matchSearch && matchBrand && matchLevel) availableBays.add(bay);
             if(matchSearch && matchBrand && matchBay) availableLevels.add(level);
          }});

          // Deshabilitar opciones no disponibles
          Array.from(brandSelect.options).forEach(opt => {{ if(opt.value !== 'ALL') opt.disabled = !availableBrands.has(opt.value); }});
          Array.from(baySelect.options).forEach(opt => {{ if(opt.value !== 'ALL') opt.disabled = !availableBays.has(opt.value); }});
          Array.from(levelSelect.options).forEach(opt => {{ if(opt.value !== 'ALL') opt.disabled = !availableLevels.has(opt.value); }});

          // Auto-Restablecer si la selección actual quedó deshabilitada por otro filtro
          let needReapply = false;
          if(brandSelect.options[brandSelect.selectedIndex].disabled) {{ brandSelect.value = 'ALL'; needReapply = true; }}
          if(baySelect.options[baySelect.selectedIndex].disabled) {{ baySelect.value = 'ALL'; needReapply = true; }}
          if(levelSelect.options[levelSelect.selectedIndex].disabled) {{ levelSelect.value = 'ALL'; needReapply = true; }}

          if(needReapply) {{
              applyFilters();
              return;
          }}

          // APLICAR VISIBILIDAD DOM
          document.querySelectorAll('.bay-column').forEach(bay => {{
            const bayNum = bay.getAttribute('data-module');
            bay.classList.toggle('hidden', !(selectedBay === 'ALL' || selectedBay === bayNum));
          }});

          document.querySelectorAll('.shelf-row').forEach(shelf => {{
            const shelfLevel = shelf.getAttribute('data-level');
            shelf.classList.toggle('hidden', !(selectedLevel === 'ALL' || selectedLevel === shelfLevel));
          }});

          document.querySelectorAll('.sku-card').forEach(card => {{
            const brand = card.getAttribute('data-brand') || '';
            const name = (card.getAttribute('data-name') || '').toLowerCase();
            const ean = card.getAttribute('data-ean') || '';

            const matchBrand = (selectedBrand === 'ALL' || brand === selectedBrand);
            const matchSearch = (query === '' || name.includes(query) || ean.includes(query) || brand.toLowerCase().includes(query));

            if (matchBrand && matchSearch) {{
              card.classList.remove('dimmed');
              card.classList.toggle('highlighted', (query !== '' || selectedBrand !== 'ALL'));
            }} else {{
              card.classList.add('dimmed');
              card.classList.remove('highlighted');
            }}
          }});
          updateScrollButtons();
        }}

        searchInput.addEventListener('input', applyFilters);
        brandSelect.addEventListener('change', applyFilters);
        baySelect.addEventListener('change', applyFilters);
        levelSelect.addEventListener('change', applyFilters);
        
        resetBtn.addEventListener('click', () => {{
          searchInput.value = '';
          brandSelect.value = 'ALL';
          baySelect.value = 'ALL';
          levelSelect.value = 'ALL';
          applyFilters();
        }});

        /* MODAL */
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

        /* CAROUSEL BOTONES */
        const container = document.getElementById('aisleContainer');
        const btnPrev = document.getElementById('btnPrev');
        const btnNext = document.getElementById('btnNext');

        function updateScrollButtons() {{
            btnPrev.disabled = container.scrollLeft <= 10;
            btnNext.disabled = container.scrollLeft + container.clientWidth >= container.scrollWidth - 10;
        }}

        btnPrev.addEventListener('click', () => {{
            const visibleModule = container.querySelector('.bay-column:not(.hidden)');
            if(visibleModule) {{
                const moduleWidth = visibleModule.offsetWidth + 16;
                container.scrollBy({{ left: -moduleWidth, behavior: 'smooth' }});
            }}
        }});

        btnNext.addEventListener('click', () => {{
            const visibleModule = container.querySelector('.bay-column:not(.hidden)');
            if(visibleModule) {{
                const moduleWidth = visibleModule.offsetWidth + 16;
                container.scrollBy({{ left: moduleWidth, behavior: 'smooth' }});
            }}
        }});

        container.addEventListener('scroll', updateScrollButtons);
        window.addEventListener('resize', updateScrollButtons);
        setTimeout(updateScrollButtons, 500);
      </script>
    </body>
    </html>
    """

# --- SECCIÓN DE CARGA ---
archivo_excel = st.file_uploader("📥 Cargar Base de Datos del Planograma (Excel o XLSB)", type=["xlsx", "xls", "xlsb"])

if archivo_excel is not None:
    try:
        motor = "pyxlsb" if archivo_excel.name.endswith(".xlsb") else None
        
        try:
            df = pd.read_excel(archivo_excel, sheet_name="MATRIZ", skiprows=5, usecols="C:AB", engine=motor)
        except Exception:
            df = pd.read_excel(archivo_excel, skiprows=5, usecols="C:AB", engine=motor)

        df.columns = [str(c).strip() for c in df.columns]
        
        if "Bandeja" in df.columns and "EAN" in df.columns:
            df = df.dropna(subset=["Bandeja", "EAN"], how="all")

        st.success(f"✅ Archivo cargado correctamente. Se procesaron {len(df)} SKUs.")
        
        st.markdown("### Vista Gráfica Interactiva")
        html_pasillo = generar_html_pasillo_interactivo(df)
        components.html(html_pasillo, height=1500, scrolling=True)
        
    except Exception as e:
        st.error(f"Error general en el proceso. Revisa el formato de la tabla: {e}")
else:
    st.info("👆 Por favor, sube tu Excel con la tabla maestra (hoja MATRIZ) para previsualizar el planograma.")
