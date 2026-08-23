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
    """Convierte de forma segura cualquier valor a float, ignorando texto o símbolos."""
    if pd.isna(val):
        return default
    try:
        if isinstance(val, str):
            val = val.replace('%', '').replace(',', '').strip()
        return float(val)
    except (ValueError, TypeError):
        return default

def obtener_color_estado_stock(estado, stock_val):
    """Aplica los colores según la lógica de la macro VBA."""
    estado = str(estado).strip().upper()
    
    if estado == "B":
        return "#FFC7CE", "#9C0006" # Bloqueado: Fondo rojo claro, texto rojo oscuro
    elif estado == "A":
        if stock_val <= 0:
            return "#F4B084", "#833C0C" # Activo sin stock: Naranja
        elif stock_val <= 5:
            return "#FFFF99", "#9C6500" # Activo stock bajo: Amarillo
        else:
            return "#C6EFCE", "#006100" # Activo stock ok: Verde claro
    else:
        return "#D9D9D9", "#000000" # Desconocido: Gris

# --- GENERADOR DEL PASILLO HTML COMPLETO ---
def generar_html_pasillo_interactivo(df):
    
    # 1. Preparar datos y replicar ordenamiento de la Macro
    df = df.copy()
    df['FilaOriginal'] = range(len(df))
    df['TieneOrden'] = pd.to_numeric(df.get('N° ORDEN', pd.Series([None]*len(df))), errors='coerce').notna()
    df['NumOrden'] = pd.to_numeric(df.get('N° ORDEN', pd.Series([None]*len(df))), errors='coerce').fillna(999999)
    
    # Extraer Módulo y Nivel para ordenar correctamente
    bandeja_str = df.get('Bandeja', pd.Series(["1.1"]*len(df))).astype(str)
    df[['Modulo_Ord', 'Nivel_Ord']] = bandeja_str.str.extract(r'(\d+)\.(\d+)')
    df['Modulo_Ord'] = pd.to_numeric(df['Modulo_Ord'], errors='coerce').fillna(1)
    df['Nivel_Ord'] = pd.to_numeric(df['Nivel_Ord'], errors='coerce').fillna(1)

    # Ordenar: Módulo -> Nivel (Desc) -> TieneOrden (Primero los True) -> NumOrden -> FilaOriginal
    df = df.sort_values(
        by=['Modulo_Ord', 'Nivel_Ord', 'TieneOrden', 'NumOrden', 'FilaOriginal'], 
        ascending=[True, False, False, True, True]
    )

    modulos = {}
    todas_marcas = sorted(list(df["Marca"].dropna().unique())) if "Marca" in df.columns else []

    # 2. Agrupar por Módulo y Bandeja
    for _, r in df.iterrows():
        b_str = str(r.get("Bandeja", "1.1")).strip()
        mod_id = f"Módulo {b_str.split('.')[0]}" if "." in b_str else "Módulo 1"

        if mod_id not in modulos:
            modulos[mod_id] = {}
        if b_str not in modulos[mod_id]:
            modulos[mod_id][b_str] = []

        modulos[mod_id][b_str].append(r)

    # 3. Construir HTML
    html_modulos = ""
    for mod_nombre, bandejas_dict in sorted(modulos.items()):
        mod_num = mod_nombre.replace("Módulo ", "").strip()
        # El ordenamiento de las bandejas se maneja de mayor a menor (de arriba hacia abajo)
        bandejas_ordenadas = sorted(bandejas_dict.keys(), reverse=True)
        html_bandejas = ""

        for b_nombre in bandejas_ordenadas:
            items = bandejas_dict[b_nombre]
            total_caras = sum([int(it.get("Caras", 1)) if str(it.get("Caras", 1)).isdigit() else 1 for it in items])
            nivel_num = b_nombre.split(".")[-1] if "." in b_nombre else "1"

            cards_html = ""
            for it in items:
                # Usamos N° para la posición gráfica (como se ve en la columna D de tu imagen)
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

                # Extracción segura de números
                stock_val = safe_float(it.get("Stock", 0))
                cob_val = safe_float(it.get("Cobertura", 0))
                venta_val = safe_float(it.get("Venta", 0))
                part_val = safe_float(it.get("% Part", 0))
                
                # Excel suele guardar los porcentajes como decimales (ej. 0.2124), si es mayor a 1 lo asumimos entero.
                if part_val < 1:
                    part_fmt = f"{part_val*100:.2f}%"
                else:
                    part_fmt = f"{part_val:.2f}%"

                # Formateos lógicos (Reglas VBA)
                bg_color, text_color = obtener_color_estado_stock(estado, stock_val)
                
                es_top = top_ventas == "TOP"
                border_style = "border: 3px solid #FFC000;" if es_top else "border: 1px solid #7f7f7f;"
                
                estilo_cobertura = "color: red; font-weight: bold;" if cob_val >= 30 else ""
                
                ean_corto = ean[-4:] if len(ean) >= 4 else ean
                stock_fmt = f"{stock_val:.2f}"
                cob_fmt = f"{cob_val:.2f}"
                venta_fmt = f"{venta_val:.2f}"

                # Tooltip nativo simulando "AgregarNotaProducto" de VBA
                tooltip_text = f"Descripción: {nombre}&#10;Código de barras: {ean}&#10;Venta: {venta_fmt}&#10;% Part: {part_fmt}&#10;TOPVENTAS: {top_ventas}"

                cards_html += f"""
                <div class="sku-card" style="flex: {caras}; background-color: {bg_color}; {border_style}" data-brand="{marca}" data-name="{nombre}" data-ean="{ean}" title="{tooltip_text}">
                  <div class="sku-pos">{pos}</div>
                  <div class="sku-caras-tag">{caras} C</div>
                  <div class="sku-details">
                    <span class="sku-brand-text" style="color: {text_color};">{cod_real}</span>
                    <span class="sku-name-text" style="color: {text_color};">Stock: {stock_fmt}</span>
                  </div>
                  <div class="sku-bottom-bar" style="border-top-color: {text_color};">
                    <span class="sku-ean-code" style="color: {text_color};">...{ean_corto}</span>
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
        .aisle-container {{ display: flex; flex-direction: row; gap: 12px; background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 16px; overflow-x: auto; align-items: stretch; }}
        .bay-column {{ flex: 0 0 460px; background: #111c30; border: 1.5px solid #1e293b; border-radius: 6px; display: flex; flex-direction: column; }}
        .bay-column.hidden {{ display: none; }}
        .bay-title {{ background: #1e3a8a; padding: 8px; font-size: 0.85rem; font-weight: 700; text-align: center; border-bottom: 2px solid #3b82f6; border-radius: 4px 4px 0 0; }}
        .bay-shelves {{ padding: 10px; display: flex; flex-direction: column; gap: 14px; flex-grow: 1; }}
        .shelf-row {{ display: flex; flex-direction: column; background: #162238; border-radius: 4px; }}
        .shelf-row.hidden {{ display: none; }}
        .shelf-info {{ background: rgba(30, 58, 138, 0.8); padding: 4px 8px; font-size: 0.7rem; font-weight: 700; display: flex; justify-content: space-between; border-left: 3px solid #60a5fa; }}
        .shelf-caras-count {{ background: rgba(0, 0, 0, 0.4); padding: 1px 6px; border-radius: 3px; color: #93c5fd; font-size: 0.65rem; }}
        .shelf-products {{ display: flex; flex-direction: row; gap: 4px; padding: 6px; min-height: 125px; overflow-x: auto; }}
        .sku-card {{ border-radius: 4px; padding: 6px; display: flex; flex-direction: column; justify-content: space-between; min-width: 95px; position: relative; transition: all 0.2s; cursor: help; }}
        .sku-card.dimmed {{ opacity: 0.15; filter: grayscale(1); }}
        .sku-card.highlighted {{ box-shadow: 0 0 12px rgba(59, 130, 246, 0.8); transform: scale(1.02); z-index: 5; }}
        .sku-pos {{ position: absolute; top: 4px; left: 4px; background: #0f172a; color: #fff; font-size: 0.6rem; font-weight: 800; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; border-radius: 2px; }}
        .sku-caras-tag {{ position: absolute; top: 4px; right: 4px; background: rgba(255,255,255,0.7); color: #000; font-size: 0.55rem; font-weight: 800; padding: 1px 4px; border-radius: 2px; }}
        .sku-details {{ margin-top: 18px; display: flex; flex-direction: column; gap: 2px; text-align: center; }}
        .sku-brand-text {{ font-size: 0.7rem; font-weight: 800; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .sku-name-text {{ font-size: 0.75rem; font-weight: 600; line-height: 1.1; }}
        .sku-bottom-bar {{ margin-top: 4px; border-top: 1px dashed; padding-top: 2px; display: flex; justify-content: space-between; align-items: center; font-size: 0.65rem; }}
        .sku-ean-code {{ font-family: monospace; font-weight: 700; }}
        .sku-cap-val {{ font-weight: 800; padding: 1px 3px; border-radius: 2px; }}
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
archivo_excel = st.file_uploader("📥 Cargar Base de Datos del Planograma (Excel o XLSB)", type=["xlsx", "xls", "xlsb"])

if archivo_excel is not None:
    try:
        motor = "pyxlsb" if archivo_excel.name.endswith(".xlsb") else None
        
        # Leemos el archivo exactamente desde C6 hasta AB
        try:
            df = pd.read_excel(archivo_excel, sheet_name="MATRIZ", skiprows=5, usecols="C:AB", engine=motor)
        except Exception:
            df = pd.read_excel(archivo_excel, skiprows=5, usecols="C:AB", engine=motor)

        # Limpieza de nombres de columnas (quita espacios invisibles)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Eliminar filas vacías debajo de la tabla
        if "Bandeja" in df.columns and "EAN" in df.columns:
            df = df.dropna(subset=["Bandeja", "EAN"], how="all")

        st.success(f"✅ Archivo cargado correctamente. Se procesaron {len(df)} SKUs.")
        
        st.markdown("### Vista Gráfica Interactiva")
        html_pasillo = generar_html_pasillo_interactivo(df)
        components.html(html_pasillo, height=850, scrolling=True)
        
    except Exception as e:
        st.error(f"Error general en el proceso. Revisa el formato de la tabla: {e}")
else:
    st.info("👆 Por favor, sube tu Excel con la tabla maestra (hoja MATRIZ) para previsualizar el planograma.")
