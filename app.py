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
st.markdown("Carga tu base de datos en Excel para generar la vista interactiva del pasillo.")
st.markdown("---")

# --- GENERADOR DEL PASILLO HTML COMPLETO ---
def generar_html_pasillo_interactivo(df):
    modulos = {}
    
    if "Marca" in df.columns:
        todas_marcas = sorted(list(df["Marca"].dropna().unique()))
    else:
        todas_marcas = []

    # Agrupar por Módulo y Bandeja
    for _, r in df.iterrows():
        b_str = str(r.get("Bandeja", "1.1")).strip()
        mod_id = f"Módulo {b_str.split('.')[0]}" if "." in b_str else "Módulo 1"

        if mod_id not in modulos:
            modulos[mod_id] = {}
        if b_str not in modulos[mod_id]:
            modulos[mod_id][b_str] = []

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
                ean = str(it.get("EAN", ""))
                nombre = str(it.get("Nombre", ""))
                marca = str(it.get("Marca", ""))
                caras_val = str(it.get("Caras", "1"))
                caras = caras_val if caras_val.isdigit() and int(caras_val) > 0 else "1"
                cap = it.get("Total_Unidades", "-") 
                if pd.isna(cap): cap = "-"

                ean_corto = ean[-4:] if len(ean) >= 4 else ean

                cards_html += f"""
                <div class="sku-card" style="flex: {caras};" data-brand="{marca}" data-name="{nombre}" data-ean="{ean}">
                  <div class="sku-pos">{pos}</div>
                  <div class="sku-caras-tag">{caras} C</div>
                  <div class="sku-details">
                    <span class="sku-brand-text">{marca}</span>
                    <span class="sku-name-text">{nombre}</span>
                  </div>
                  <div class="sku-bottom-bar">
                    <span class="sku-ean-code">...{ean_corto}</span>
                    <span class="sku-cap-val">Cap: {cap}</span>
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

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #070d19; color: #fff; margin: 0; padding: 12px; }}
        .filter-panel {{ background: #111c30; border: 1px solid #1e3a8a; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 14px; align-items: center; }}
        .filter-group {{ display: flex; flex-direction: column; gap: 4px; }}
        .filter-label {{ font-size: 0.7rem; font-weight: 700; color: #93c5fd; text-transform: uppercase; }}
        .filter-select, .filter-input {{ background: #0b132b; border: 1px solid #3b82f6; color: #fff; padding: 6px 10px; border-radius: 4px; font-size: 0.8rem; outline: none; min-width: 140px; }}
        .filter-input {{ min-width: 220px; }}
        .filter-btn-reset {{ background: #ef4444; border: none; color: white; font-weight: 700; font-size: 0.75rem; padding: 7px 14px; border-radius: 4px; cursor: pointer; align-self: flex-end; }}
        .aisle-container {{ display: flex; flex-direction: row; gap: 12px; background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 16px; overflow-x: auto; }}
        .bay-column {{ flex: 0 0 460px; background: #111c30; border: 1.5px solid #1e293b; border-radius: 6px; display: flex; flex-direction: column; }}
        .bay-column.hidden {{ display: none; }}
        .bay-title {{ background: #1e3a8a; padding: 8px; font-size: 0.85rem; font-weight: 700; text-align: center; border-bottom: 2px solid #3b82f6; border-radius: 4px 4px 0 0; }}
        .bay-shelves {{ padding: 10px; display: flex; flex-direction: column; gap: 14px; flex-grow: 1; }}
        .shelf-row {{ display: flex; flex-direction: column; background: #162238; border-radius: 4px; }}
        .shelf-row.hidden {{ display: none; }}
        .shelf-info {{ background: rgba(30, 58, 138, 0.8); padding: 4px 8px; font-size: 0.7rem; font-weight: 700; display: flex; justify-content: space-between; border-left: 3px solid #60a5fa; }}
        .shelf-caras-count {{ background: rgba(0, 0, 0, 0.4); padding: 1px 6px; border-radius: 3px; color: #93c5fd; font-size: 0.65rem; }}
        .shelf-products {{ display: flex; flex-direction: row; gap: 4px; padding: 6px; min-height: 125px; overflow-x: auto; }}
        .sku-card {{ background: #fff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 6px; display: flex; flex-direction: column; justify-content: space-between; min-width: 95px; position: relative; transition: all 0.2s; }}
        .sku-card.dimmed {{ opacity: 0.15; filter: grayscale(1); }}
        .sku-card.highlighted {{ border: 2px solid #e11d48; box-shadow: 0 0 10px rgba(225, 29, 72, 0.8); transform: scale(1.02); z-index: 5; }}
        .sku-pos {{ position: absolute; top: 4px; left: 4px; background: #0f172a; color: #fff; font-size: 0.6rem; font-weight: 800; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; border-radius: 2px; }}
        .sku-caras-tag {{ position: absolute; top: 4px; right: 4px; background: #dbeafe; color: #1e40af; font-size: 0.55rem; font-weight: 800; padding: 1px 4px; border-radius: 2px; }}
        .sku-details {{ margin-top: 18px; display: flex; flex-direction: column; gap: 2px; }}
        .sku-brand-text {{ font-size: 0.58rem; font-weight: 800; color: #2563eb; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .sku-name-text {{ font-size: 0.62rem; font-weight: 600; color: #0f172a; line-height: 1.1; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
        .sku-bottom-bar {{ margin-top: 4px; border-top: 1px dashed #cbd5e1; padding-top: 2px; display: flex; justify-content: space-between; align-items: center; font-size: 0.55rem; color: #64748b; }}
        .sku-ean-code {{ font-family: monospace; font-weight: 700; color: #334155; }}
        .sku-cap-val {{ font-weight: 700; color: #0f766e; background: #ccfbf1; padding: 1px 3px; border-radius: 2px; }}
        .shelf-bottom-rail {{ height: 8px; background: linear-gradient(180deg, #94a3b8 0%, #475569 100%); border-radius: 0 0 3px 3px; }}
      </style>
    </head>
    <body>
      <div class="filter-panel">
        <div class="filter-group">
          <span class="filter-label">🔍 Buscar</span>
          <input type="text" id="searchInput" class="filter-input" placeholder="Nombre o código...">
        </div>
        <div class="filter-group">
          <span class="filter-label">🏷️ Marca</span>
          <select id="brandSelect" class="filter-select">
            <option value="ALL">Todas</option>
            {options_marcas}
          </select>
        </div>
        <div class="filter-group">
          <span class="filter-label">📦 Módulo</span>
          <select id="baySelect" class="filter-select">
            <option value="ALL">Todos</option>
            {options_modulos}
          </select>
        </div>
        <div class="filter-group">
          <span class="filter-label">📶 Nivel</span>
          <select id="levelSelect" class="filter-select">
            <option value="ALL">Todos</option>
            <option value="4">Bandeja 4 (Superior)</option>
            <option value="3">Bandeja 3 (Media Alta)</option>
            <option value="2">Bandeja 2 (Media Baja)</option>
            <option value="1">Bandeja 1 (Base)</option>
          </select>
        </div>
        <button id="resetBtn" class="filter-btn-reset">Restablecer</button>
      </div>

      <div class="aisle-container">
        {html_modulos}
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
      </script>
    </body>
    </html>
    """

# --- SECCIÓN DE CARGA ---
archivo_excel = st.file_uploader("📥 Cargar Base de Datos del Planograma (Excel)", type=["xlsx", "xls"])

if archivo_excel is not None:
    try:
        df = pd.read_excel(archivo_excel)
        st.success(f"✅ Archivo cargado correctamente. Se encontraron {len(df)} registros.")
        
        st.markdown("### Vista Gráfica Interactiva")
        html_pasillo = generar_html_pasillo_interactivo(df)
        components.html(html_pasillo, height=850, scrolling=True)
        
    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")
else:
    st.info("👆 Por favor, sube un archivo Excel con las columnas: Bandeja, N°, EAN, Nombre, Marca, Caras, Total_Unidades para previsualizar el planograma.")