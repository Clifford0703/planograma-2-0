import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import io
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Planograma 2.0 - Realograma",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        .block-container {
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-top: 1.2rem !important; 
            max-width: 100% !important;
        }
        .fin-kpi-container { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); 
            gap: 10px; 
            margin-bottom: 15px; 
        }
        @media (max-width: 768px) {
            .fin-kpi-container {
                grid-template-columns: repeat(2, 1fr) !important;
            }
        }
        .fin-kpi-card { 
            background: linear-gradient(145deg, #111c30 0%, #0f172a 100%); 
            border-left: 4px solid #3b82f6; 
            border-radius: 8px; 
            padding: 12px 14px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
            display: flex; 
            flex-direction: column; 
            justify-content: center; 
        }
        .fin-kpi-title { font-size: 0.70rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.3px; }
        .fin-kpi-val { font-size: 1.4rem; font-weight: 900; color: #ffffff; line-height: 1.1; }
        .fin-kpi-card.green-theme { border-left-color: #10b981; }
        .fin-kpi-card.purple-theme { border-left-color: #8b5cf6; }
        
        .login-card {
            background-color: #111c30;
            padding: 26px;
            border-radius: 10px;
            border: 1px solid #1e3a8a;
            max-width: 400px;
            margin: 30px auto;
            box-shadow: 0 8px 16px rgba(0,0,0,0.5);
        }
    </style>
""", unsafe_allow_html=True)

# --- CAPA DE SEGURIDAD (EXPIRACIÓN 60 MINUTOS) ---
TIEMPO_EXPIRACION_SEGUNDOS = 60 * 60  # 60 minutos

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "ultimo_acceso" not in st.session_state:
    st.session_state.ultimo_acceso = 0

if st.session_state.autenticado:
    if time.time() - st.session_state.ultimo_acceso > TIEMPO_EXPIRACION_SEGUNDOS:
        st.session_state.autenticado = False
        st.session_state.ultimo_acceso = 0
        st.warning("⏳ Sesión expirada (60 min). Por favor ingresa nuevamente.")

def login_form():
    st.markdown("<div class='login-card'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #fff; margin-top: 0;'>🔒 Acceso Planograma 2.0</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.85rem;'>Ingresa tus credenciales corporativas</p>", unsafe_allow_html=True)
    
    usuario = st.text_input("Usuario:", key="user_input")
    password = st.text_input("Contraseña:", type="password", key="pass_input")
    
    if st.button("Iniciar Sesión", type="primary", use_container_width=True):
        if usuario == "S003" and password == "S0032026":
            st.session_state.autenticado = True
            st.session_state.ultimo_acceso = time.time()
            st.rerun()
        else:
            st.error("❌ Credenciales incorrectas.")
    st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.autenticado:
    login_form()
    st.stop()

st.session_state.ultimo_acceso = time.time()

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

def clean_sku(val):
    if pd.isna(val): return ""
    s = str(val).strip()
    if s.endswith('.0'):
        s = s[:-2]
    return s

def obtener_estado_y_color(estado, stock_val):
    estado = str(estado).strip().upper()
    if estado == "B": 
        return "#FFC7CE", "#9C0006", "Bloqueado"
    elif estado == "A":
        if stock_val <= 0: return "#F4B084", "#833C0C", "Sin Stock"
        elif stock_val <= 5: return "#FFFF99", "#8A5A00", "Stock Bajo"
        else: return "#C6EFCE", "#006100", "Stock OK"
    else: 
        return "#D9D9D9", "#000000", "Desconocido"

def obtener_alerta_css(estado, stock_val):
    estado = str(estado).strip().upper()
    if estado == "B": return "alerta-bloqueado", "Bloqueado"
    elif estado == "A":
        if stock_val <= 0: return "alerta-sinstock", "Sin Stock"
        elif stock_val <= 5: return "alerta-stockbajo", "Stock Bajo"
        else: return "alerta-ok", "Stock OK"
    else: return "alerta-desconocido", "Desconocido"

# --- GENERADOR HTML CON TOUCH PINCH-TO-ZOOM Y 2 COLS EN MÓVIL ---
def generar_html_pasillo_interactivo(df, es_realograma=False):
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
                estilo_cobertura = "color: red; font-weight: bold;" if cob_val >= 30 else ""
                
                if es_realograma:
                    link_foto = str(it.get("Links de fotos", ""))
                    if link_foto in ['nan', '', 'None']:
                        link_foto = "https://via.placeholder.com/60x150.png/0f172a/94a3b8?text=Sin+Foto"
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
                    bg_color, text_color, cat_leyenda = obtener_estado_y_color(estado, stock_val)
                    html_interno = f"""
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
                    """
                    clase_wrapper = "sku-item sku-card"
                    estilo_wrapper = f"flex: {caras}; background-color: {bg_color}; border: 1px solid #7f7f7f;"

                cards_html += f"""
                <div class="{clase_wrapper}" style="{estilo_wrapper}" 
                     data-brand="{marca}" data-name="{nombre}" data-ean="{ean}"
                     data-stock="{stock_fmt}" data-cob="{cob_fmt}" data-venta="{venta_val}" data-part="{part_fmt}" 
                     data-cod="{cod_real}" data-cat="{cat_leyenda}" 
                     data-dept="{dept_val}" data-sec="{sec_val}" data-catjer="{catjer_val}" data-ga="{ga_val}"
                     title="Clic para ver detalles de {nombre}">
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

        subtitulo_cat = f'<div class="bay-subcat">{cat_predominante}</div>' if cat_predominante else ''

        html_cuerpos += f"""
        <div class="bay-column" data-module="{cuerpo_num}">
          <div class="bay-title">
            <span>{cuerpo_nombre.upper()}</span>
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

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
      <style>
        * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
        body, html {{ 
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
          background-color: #070d19; 
          color: #fff; 
          margin: 0; 
          padding: 0; 
          width: 100%;
          overflow-x: hidden;
        }}
        
        .main-container {{ 
          padding: 6px; 
          width: 100%; 
          display: flex; 
          flex-direction: column; 
        }}

        /* --- KPIS: 2 POR FILA EN MÓVIL Y GRID COMPACTO --- */
        .kpi-grid {{ 
          display: grid; 
          grid-template-columns: repeat(2, 1fr); 
          gap: 6px; 
          margin-bottom: 8px; 
        }}
        @media (min-width: 769px) {{
          .kpi-grid {{ grid-template-columns: repeat(7, 1fr); }}
        }}
        .kpi-card {{ 
          background: #111c30; 
          border: 1px solid #1e3a8a; 
          border-radius: 6px; 
          padding: 6px 8px; 
          text-align: center; 
          display: flex;
          flex-direction: column;
          justify-content: center;
        }}
        .kpi-title {{ font-size: 0.60rem; font-weight: 800; color: #93c5fd; text-transform: uppercase; margin-bottom: 2px; display: block; }}
        .kpi-val {{ font-size: 1.35rem; font-weight: 900; line-height: 1; display: block; }}
        
        /* FILTROS */
        .filter-panel {{ 
          background: #111c30; 
          border: 1px solid #1e3a8a; 
          border-radius: 6px; 
          padding: 8px; 
          margin-bottom: 8px; 
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 6px; 
        }}
        @media (min-width: 769px) {{
          .filter-panel {{ grid-template-columns: repeat(5, 1fr) auto; }}
        }}
        .filter-group {{ display: flex; flex-direction: column; gap: 2px; }}
        .filter-group.full-width {{ grid-column: 1 / -1; }}
        .filter-label {{ font-size: 0.62rem; font-weight: 700; color: #93c5fd; text-transform: uppercase; }}
        .filter-select, .filter-input {{ 
          background: #ffffff; 
          border: 1.5px solid #3b82f6; 
          color: #0f172a; 
          padding: 5px 6px; 
          border-radius: 4px; 
          font-size: 0.80rem; 
          font-weight: 600; 
          outline: none; 
          width: 100%; 
        }}
        .btn-group {{ display: flex; gap: 6px; grid-column: 1 / -1; margin-top: 4px; }}
        .filter-btn-reset, .filter-btn-print {{ 
          flex: 1; border: none; color: white; font-weight: 700; font-size: 0.72rem; padding: 7px; border-radius: 4px; cursor: pointer; text-align: center;
        }}
        .filter-btn-reset {{ background: #ef4444; }}
        .filter-btn-print {{ background: #10b981; }}
        
        /* LEYENDA */
        .legend-panel {{ 
          background: #111c30; 
          border: 1px solid #1e3a8a; 
          border-radius: 6px; 
          padding: 6px; 
          margin-bottom: 8px; 
          display: flex; 
          align-items: center; 
          gap: 6px; 
          overflow-x: auto;
        }}
        .legend-title {{ font-size: 0.65rem; font-weight: 700; color: #93c5fd; white-space: nowrap; }}
        .legend-chips {{ display: flex; gap: 5px; flex-shrink: 0; }}
        .legend-chip {{ 
          background: var(--bg); 
          color: var(--tc); 
          border: var(--bd, 1px solid transparent); 
          font-weight: 700; 
          font-size: 0.62rem; 
          padding: 4px 7px; 
          border-radius: 12px; 
          cursor: pointer; 
          white-space: nowrap;
        }}
        .legend-chip.active {{ transform: scale(1.05); border: 2px solid #3b82f6 !important; }}
        
        /* --- VIEWPORT TÁCTIL PINCH-TO-ZOOM --- */
        .touch-viewport {{
          position: relative;
          width: 100%;
          min-height: 520px;
          height: 72vh;
          background: #0b1324;
          border: 1.5px solid #1e3a8a;
          border-radius: 8px;
          overflow: hidden;
          touch-action: none; /* Control total por JS */
          user-select: none;
        }}
        
        .zoom-canvas {{
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          transform-origin: 0 0;
          will-change: transform;
          display: flex;
          align-items: flex-start;
          padding: 8px;
        }}
        
        .aisle-container {{ 
          display: flex; 
          flex-direction: row; 
          gap: 12px; 
          width: 100%;
          height: 100%;
        }}
        
        .bay-column {{ 
          flex: 0 0 96%; 
          width: 96%;
          max-width: 520px; 
          background: #111c30; 
          border: 1.5px solid #1e293b; 
          border-radius: 6px; 
          display: flex; 
          flex-direction: column; 
          padding-bottom: 10px; 
          margin: 0 auto;
        }}
        @media (min-width: 769px) {{
          .bay-column {{ flex: 0 0 100%; max-width: 100%; }}
        }}
        .bay-column.hidden {{ display: none !important; }}
        
        .bay-title {{ 
          background: #1e3a8a; 
          padding: 6px 8px; 
          font-size: 0.80rem; 
          font-weight: 700; 
          text-align: center; 
          border-bottom: 2px solid #3b82f6; 
          border-radius: 4px 4px 0 0; 
        }}
        .bay-subcat {{ font-size: 0.65rem; font-weight: 600; color: #93c5fd; text-transform: uppercase; }}
        
        .bay-shelves {{ 
          padding: 6px; 
          display: flex; 
          flex-direction: column; 
          gap: 14px; 
          flex-grow: 1; 
          overflow-y: auto;
        }}
        .shelf-row {{ display: flex; flex-direction: column; position: relative; padding-top: 6px; }}
        .shelf-row.hidden {{ display: none !important; }}
        
        .shelf-products {{ 
          display: flex; 
          flex-direction: row; 
          gap: 3px; 
          padding: 4px; 
          min-height: 80px; 
          overflow-x: auto; 
          align-items: flex-end; 
          justify-content: flex-start; 
        }}
        .sku-item.dimmed {{ opacity: 0.15; filter: grayscale(1); }}
        .sku-item.highlighted {{ transform: scale(1.02); z-index: 20; }}
        
        .shelf-base {{ height: 10px; background: linear-gradient(180deg, #fde047 0%, #ca8a04 100%); border-radius: 2px; position: relative; border-bottom: 2px solid #854d0e; }}
        .shelf-name-tag {{ position: absolute; top: 7px; background: rgba(0,0,0,0.8); color: #fef08a; font-size: 0.50rem; padding: 1px 4px; border-radius: 0 0 3px 3px; font-weight: 800; }}
        
        .sku-group {{ display: flex; flex-direction: column; align-items: center; position: relative; cursor: pointer; flex-shrink: 0; }}
        .sku-images-wrapper {{ display: flex; flex-direction: row; align-items: flex-end; gap: 1px; }}
        .sku-images-wrapper img {{ height: 75px; width: auto; max-width: 45px; object-fit: contain; }}
        
        .sku-fleje {{ background: #ffffff; color: #000; border: 1px solid #64748b; font-size: 0.45rem; display: flex; flex-direction: column; align-items: center; line-height: 1; margin-top: 2px; width: max-content; padding: 1px 2px; }}
        .fleje-ean {{ font-weight: 600; font-family: monospace; }}
        .fleje-caras {{ font-weight: 900; background: #e2e8f0; width: 100%; text-align: center; color: #1e293b; }}
        
        .alerta-bloqueado .sku-images-wrapper img {{ filter: grayscale(100%) opacity(0.4); }}
        .alerta-sinstock .sku-images-wrapper img {{ filter: drop-shadow(0 0 8px #ef4444); }}
        .alerta-stockbajo .sku-images-wrapper img {{ filter: drop-shadow(0 0 6px #f59e0b); }}
        .sku-group.is-top .top-badge::after {{ content: '⭐'; position: absolute; top: -12px; right: -4px; font-size: 1rem; }}
        
        .sku-card {{ border-radius: 4px; padding: 4px; display: flex; flex-direction: column; justify-content: space-between; min-width: 75px; position: relative; cursor: pointer; flex-shrink: 0; }}
        .sku-pos {{ position: absolute; top: 2px; left: 2px; background: #0f172a; color: #fff; font-size: 0.52rem; font-weight: 800; padding: 1px 3px; border-radius: 2px; }}
        .sku-caras-tag {{ position: absolute; top: 2px; right: 2px; background: rgba(255,255,255,0.9); color: #000; font-size: 0.48rem; font-weight: 800; padding: 1px 3px; border-radius: 2px; }}
        .sku-details {{ margin-top: 14px; display: flex; flex-direction: column; gap: 1px; text-align: center; }}
        .sku-brand-text {{ font-size: 0.55rem; font-weight: 800; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .sku-name-text {{ font-size: 0.60rem; font-weight: 700; line-height: 1.1; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
        .sku-bottom-bar {{ margin-top: 2px; border-top: 1px dashed; padding-top: 2px; display: flex; justify-content: space-between; align-items: center; }}
        .sku-ean-code {{ font-size: 0.52rem; font-family: monospace; font-weight: 800; }}
        .sku-cap-val {{ font-size: 0.55rem; font-weight: 800; }}
        .shelf-bottom-rail {{ height: 5px; background: linear-gradient(180deg, #94a3b8 0%, #475569 100%); border-radius: 0 0 2px 2px; margin-top: 2px; }}
        .shelf-info {{ background: rgba(30, 58, 138, 0.85); padding: 3px 6px; font-size: 0.60rem; font-weight: 700; display: flex; justify-content: space-between; border-left: 3px solid #60a5fa; }}
        
        /* BOTONES FLOTANTES DE ZOOM PARA ACCESIBILIDAD */
        .zoom-controls {{
          position: absolute;
          bottom: 12px;
          right: 12px;
          display: flex;
          flex-direction: column;
          gap: 6px;
          z-index: 1000;
        }}
        .zoom-btn {{
          background: #1e3a8a;
          color: #ffffff;
          border: 1.5px solid #3b82f6;
          border-radius: 50%;
          width: 38px;
          height: 38px;
          font-size: 1.2rem;
          font-weight: 900;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 8px rgba(0,0,0,0.6);
          cursor: pointer;
        }}
        
        /* NAVEGADOR DE CUERPOS EN MÓVIL */
        .mobile-nav-bar {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: #111c30;
          border: 1px solid #1e3a8a;
          border-radius: 6px;
          padding: 6px 10px;
          margin-top: 6px;
        }}
        .mob-btn {{
          background: #3b82f6;
          border: none;
          color: white;
          padding: 6px 14px;
          border-radius: 4px;
          font-weight: bold;
          font-size: 0.8rem;
          cursor: pointer;
        }}

        /* MODAL */
        .modal-overlay {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 99999; opacity: 0; pointer-events: none; transition: opacity 0.2s; }}
        .modal-overlay.active {{ opacity: 1; pointer-events: auto; }}
        .modal-content {{ background: #1e293b; color: #fff; padding: 16px; border-radius: 8px; width: 90%; max-width: 380px; max-height: 80vh; overflow-y: auto; border: 2px solid #3b82f6; }}
        .modal-close {{ position: absolute; top: 8px; right: 12px; font-size: 1.6rem; cursor: pointer; color: #94a3b8; font-weight: bold; }}
        .m-row {{ border-bottom: 1px solid #334155; padding: 4px 0; display: flex; justify-content: space-between; font-size: 0.78rem; }}
        .m-label {{ font-weight: 700; color: #93c5fd; }}
        .m-val {{ font-weight: 600; text-align: right; max-width: 65%; word-wrap: break-word; }}
      </style>
    </head>
    <body>
      <div class="main-container">

        <div id="productModal" class="modal-overlay">
          <div class="modal-content">
            <span class="modal-close">&times;</span>
            <h3 id="m-name" style="margin-top: 0; font-size: 0.95rem; border-bottom: 2px solid #3b82f6; padding-bottom: 4px; line-height: 1.2;">Producto</h3>
            <div class="m-row"><span class="m-label">Cód. Real:</span><span class="m-val" id="m-cod"></span></div>
            <div class="m-row"><span class="m-label">EAN:</span><span class="m-val" id="m-ean"></span></div>
            <div class="m-row"><span class="m-label">Marca:</span><span class="m-val" id="m-brand"></span></div>
            <div class="m-row"><span class="m-label">Departamento:</span><span class="m-val" id="m-dept" style="color: #cbd5e1;"></span></div>
            <div class="m-row"><span class="m-label">Sección:</span><span class="m-val" id="m-sec" style="color: #cbd5e1;"></span></div>
            <div class="m-row"><span class="m-label">Categoría:</span><span class="m-val" id="m-catjer" style="color: #cbd5e1;"></span></div>
            <div class="m-row"><span class="m-label">Grupo Artículo:</span><span class="m-val" id="m-ga" style="color: #cbd5e1;"></span></div>
            <div class="m-row"><span class="m-label">Stock Actual:</span><span class="m-val" id="m-stock"></span></div>
            <div class="m-row"><span class="m-label">Cobertura:</span><span class="m-val" id="m-cob"></span></div>
            <div class="m-row"><span class="m-label">Ventas:</span><span class="m-val" id="m-venta"></span></div>
            <div class="m-row" style="border-bottom: none;"><span class="m-label" style="color: #fbbf24; font-weight: 800;">¿Es TOP Ventas?:</span><span class="m-val" id="m-top" style="color: #fbbf24; font-weight: 800;"></span></div>
          </div>
        </div>

        <!-- KPIS EN 2 COLUMNAS POR FILA EN MÓVIL -->
        <div class="kpi-grid">
          <div class="kpi-card" style="border-bottom: 3px solid #3b82f6;"><span class="kpi-title">Total SKUs</span><span class="kpi-val" id="t-total" style="color: #fff;">0</span></div>
          <div class="kpi-card" style="border-bottom: 3px solid #FFC7CE;"><span class="kpi-title">Bloqueados</span><span class="kpi-val" id="t-bloq" style="color: #FFC7CE;">0</span></div>
          <div class="kpi-card" style="border-bottom: 3px solid #F4B084;"><span class="kpi-title">Sin Stock (0)</span><span class="kpi-val" id="t-sin" style="color: #F4B084;">0</span></div>
          <div class="kpi-card" style="border-bottom: 3px solid #FFFF99;"><span class="kpi-title">Stock Bajo (1-5)</span><span class="kpi-val" id="t-bajo" style="color: #FFFF99;">0</span></div>
          <div class="kpi-card" style="border-bottom: 3px solid #C6EFCE;"><span class="kpi-title">Stock OK (>5)</span><span class="kpi-val" id="t-ok" style="color: #C6EFCE;">0</span></div>
          <div class="kpi-card" style="border-bottom: 3px solid #ef4444;"><span class="kpi-title">Cob. Alta (≥30)</span><span class="kpi-val" id="t-cob" style="color: #ef4444;">0</span></div>
          <div class="kpi-card" style="border-bottom: 3px solid #fbbf24; grid-column: 1 / -1;"><span class="kpi-title">★ TOP Ventas</span><span class="kpi-val" id="t-top" style="color: #fbbf24;">0</span></div>
        </div>

        <div class="filter-panel">
          <div class="filter-group full-width"><span class="filter-label">🔍 Buscar Producto</span><input type="text" id="searchInput" class="filter-input" placeholder="Nombre o EAN..."></div>
          <div class="filter-group"><span class="filter-label">🏷️ Marca</span><select id="brandSelect" class="filter-select"><option value="ALL">Todas</option>{options_marcas}</select></div>
          <div class="filter-group"><span class="filter-label">📂 Categoría</span><select id="catSelect" class="filter-select"><option value="ALL">Todas</option>{options_categorias}</select></div>
          <div class="filter-group"><span class="filter-label">📦 Cuerpo</span><select id="baySelect" class="filter-select"><option value="ALL">Todos</option>{options_cuerpos}</select></div>
          <div class="filter-group"><span class="filter-label">📶 Nivel</span><select id="levelSelect" class="filter-select"><option value="ALL">Todos</option>{options_niveles}</select></div>
          <div class="btn-group">
            <button id="resetBtn" class="filter-btn-reset">Restablecer</button>
            <button type="button" id="printBayBtn" class="filter-btn-print">🖨️ Imprimir</button>
          </div>
        </div>

        <div class="legend-panel">
          <span class="legend-title">📍 Leyenda:</span>
          <div class="legend-chips">
            <button class="legend-chip" data-filter="Bloqueado" style="--bg: #FFC7CE; --tc: #9C0006;">Bloqueado</button>
            <button class="legend-chip" data-filter="Sin Stock" style="--bg: #F4B084; --tc: #833C0C;">Sin Stock</button>
            <button class="legend-chip" data-filter="Stock Bajo" style="--bg: #FFFF99; --tc: #8A5A00;">Stock 1-5</button>
            <button class="legend-chip" data-filter="Stock OK" style="--bg: #C6EFCE; --tc: #006100;">Stock >5</button>
            <button class="legend-chip" data-filter="cob-alta" style="--bg: #ffffff; --tc: #ef4444; --bd: 2px solid #ef4444;">Cob ≥30</button>
            <button class="legend-chip" data-filter="top-ventas" style="--bg: #ffffff; --tc: #b45309; --bd: 2px solid #FFC000;">★ TOP</button>
          </div>
        </div>

        <!-- LIENZO TÁCTIL INTERACTIVO (TOUCH & PINCH-TO-ZOOM) -->
        <div class="touch-viewport" id="viewport">
          <div class="zoom-canvas" id="canvas">
            <div class="aisle-container" id="aisleContainer">
              {html_cuerpos}
            </div>
          </div>
          <div class="zoom-controls">
            <button class="zoom-btn" id="btnZoomIn" title="Acercar">+</button>
            <button class="zoom-btn" id="btnZoomOut" title="Alejar">−</button>
            <button class="zoom-btn" id="btnZoomReset" style="font-size: 0.9rem;" title="Reiniciar">↺</button>
          </div>
        </div>

        <div class="mobile-nav-bar">
          <button class="mob-btn" id="btnPrevBay">❮ Anterior</button>
          <span id="currentBayLabel" style="font-size: 0.8rem; font-weight: bold; color: #93c5fd;">Cuerpo 1</span>
          <button class="mob-btn" id="btnNextBay">Siguiente ❯</button>
        </div>

      </div>

      <script>
        // --- MOTOR DE GESTOS MULTITÁCTIL (PINCH-TO-ZOOM Y PAN) ---
        const viewport = document.getElementById('viewport');
        const canvas = document.getElementById('canvas');
        let scale = 1, minScale = 0.5, maxScale = 4.0;
        let posX = 0, posY = 0;
        let startX = 0, startY = 0;
        let initialDistance = 0;
        let isTouching = false;
        let lastTap = 0;

        function updateTransform() {{
          canvas.style.transform = `translate3d(${{posX}}px, ${{posY}}px, 0) scale(${{scale}})`;
        }}

        function getDistance(touches) {{
          const dx = touches[0].clientX - touches[1].clientX;
          const dy = touches[0].clientY - touches[1].clientY;
          return Math.sqrt(dx * dx + dy * dy);
        }}

        viewport.addEventListener('touchstart', (e) => {{
          if (e.touches.length === 1) {{
            isTouching = true;
            startX = e.touches[0].clientX - posX;
            startY = e.touches[0].clientY - posY;
            
            // Detección de doble toque (Double-tap to zoom)
            const currentTime = new Date().getTime();
            const tapLength = currentTime - lastTap;
            if (tapLength < 300 && tapLength > 0) {{
              if (scale > 1.2) {{ scale = 1; posX = 0; posY = 0; }}
              else {{ scale = 2.0; }}
              updateTransform();
            }}
            lastTap = currentTime;
          }} else if (e.touches.length === 2) {{
            isTouching = true;
            initialDistance = getDistance(e.touches);
          }}
        }}, {{ passive: false }});

        viewport.addEventListener('touchmove', (e) => {{
          e.preventDefault();
          if (!isTouching) return;
          
          if (e.touches.length === 1 && scale > 1) {{
            // Desplazar góndola cuando hay zoom
            posX = e.touches[0].clientX - startX;
            posY = e.touches[0].clientY - startY;
            updateTransform();
          }} else if (e.touches.length === 2) {{
            // Pellizcar para zoom
            const newDist = getDistance(e.touches);
            const diff = newDist / initialDistance;
            scale = Math.min(Math.max(scale * (diff > 1 ? 1.03 : 0.97), minScale), maxScale);
            initialDistance = newDist;
            updateTransform();
          }}
        }}, {{ passive: false }});

        viewport.addEventListener('touchend', () => {{ isTouching = false; }});

        // Botones flotantes de accesibilidad
        document.getElementById('btnZoomIn').addEventListener('click', () => {{ scale = Math.min(scale + 0.3, maxScale); updateTransform(); }});
        document.getElementById('btnZoomOut').addEventListener('click', () => {{ scale = Math.max(scale - 0.3, minScale); updateTransform(); }});
        document.getElementById('btnZoomReset').addEventListener('click', () => {{ scale = 1; posX = 0; posY = 0; updateTransform(); }});

        // NAVEGACIÓN RÁPIDA ENTRE CUERPOS
        const baySelect = document.getElementById('baySelect');
        const currentBayLabel = document.getElementById('currentBayLabel');
        
        function changeBay(direction) {{
          const options = Array.from(baySelect.options).filter(o => o.value !== 'ALL');
          let currentIndex = options.findIndex(o => o.value === baySelect.value);
          if (currentIndex === -1) currentIndex = 0;
          
          let newIndex = currentIndex + direction;
          if (newIndex >= 0 && newIndex < options.length) {{
            baySelect.value = options[newIndex].value;
            currentBayLabel.textContent = options[newIndex].text;
            scale = 1; posX = 0; posY = 0; updateTransform();
            applyFilters();
          }}
        }}

        document.getElementById('btnPrevBay').addEventListener('click', () => changeBay(-1));
        document.getElementById('btnNextBay').addEventListener('click', () => changeBay(1));

        // --- FILTROS Y LÓGICA DE SKUS ---
        const searchInput = document.getElementById('searchInput');
        const brandSelect = document.getElementById('brandSelect');
        const catSelect = document.getElementById('catSelect');
        const levelSelect = document.getElementById('levelSelect');
        const resetBtn = document.getElementById('resetBtn');
        const printBayBtn = document.getElementById('printBayBtn');

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

          let visibleSkus = new Map();
          document.querySelectorAll('.sku-item').forEach(card => {{
             const brand = card.getAttribute('data-brand') || '';
             const catjer = card.getAttribute('data-catjer') || '';
             const bay = card.closest('.bay-column').getAttribute('data-module');
             const level = card.closest('.shelf-row').getAttribute('data-level');
             const name = (card.getAttribute('data-name') || '').toLowerCase();
             const ean = card.getAttribute('data-ean') || '';
             const cod = card.getAttribute('data-cod');
             const venta = parseFloat((card.getAttribute('data-venta') || "0").replace(/,/g, '')) || 0;

             if ((query === '' || name.includes(query) || ean.includes(query) || brand.toLowerCase().includes(query)) &&
                 (selectedBrand === 'ALL' || brand === selectedBrand) &&
                 (selectedCat === 'ALL' || catjer === selectedCat) &&
                 (selectedBay === 'ALL' || bay === selectedBay) &&
                 (selectedLevel === 'ALL' || level === selectedLevel)) {{
                 if (!visibleSkus.has(cod)) visibleSkus.set(cod, venta);
             }}
          }});

          let sortedSkus = Array.from(visibleSkus.entries()).sort((a, b) => b[1] - a[1]);
          let topNSkusSet = new Set(sortedSkus.slice(0, 5).map(x => x[0]));

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
             if(isTop) {{ card.classList.add('is-top'); if(card.classList.contains('sku-card')) card.style.border = "2px solid #FFC000"; }}
             else {{ card.classList.remove('is-top'); if(card.classList.contains('sku-card')) card.style.border = "1px solid #7f7f7f"; }}

             const match = (query === '' || name.includes(query) || ean.includes(query) || brand.toLowerCase().includes(query)) &&
                           (selectedBrand === 'ALL' || brand === selectedBrand) &&
                           (selectedCat === 'ALL' || catjer === selectedCat) &&
                           (selectedBay === 'ALL' || bay === selectedBay) &&
                           (selectedLevel === 'ALL' || level === selectedLevel);

             if(match) {{
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

             if (match && passesLegend) {{ card.classList.remove('dimmed'); card.classList.add('highlighted'); }}
             else {{ card.classList.add('dimmed'); card.classList.remove('highlighted'); }}
          }});

          document.getElementById('t-total').textContent = setTot.size;
          document.getElementById('t-bloq').textContent = setBloq.size;
          document.getElementById('t-sin').textContent = setSin.size;
          document.getElementById('t-bajo').textContent = setBajo.size;
          document.getElementById('t-ok').textContent = setOk.size;
          document.getElementById('t-cob').textContent = setCob.size;
          document.getElementById('t-top').textContent = setTop.size;

          document.querySelectorAll('.bay-column').forEach(bay => {{
            const bayNum = bay.getAttribute('data-module');
            bay.classList.toggle('hidden', !(selectedBay === 'ALL' || selectedBay === bayNum));
          }});

          document.querySelectorAll('.shelf-row').forEach(shelf => {{
            const shelfLevel = shelf.getAttribute('data-level');
            shelf.classList.toggle('hidden', !(selectedLevel === 'ALL' || selectedLevel === shelfLevel));
          }});
        }}

        printBayBtn.addEventListener('click', () => window.print());

        document.querySelectorAll('.legend-chip').forEach(chip => {{
            chip.addEventListener('click', () => {{
                const filter = chip.getAttribute('data-filter');
                if (currentLegendFilter === filter) {{ currentLegendFilter = null; chip.classList.remove('active'); }}
                else {{
                    document.querySelectorAll('.legend-chip').forEach(c => c.classList.remove('active'));
                    currentLegendFilter = filter;
                    chip.classList.add('active');
                }}
                applyFilters();
            }});
        }});

        searchInput.addEventListener('input', applyFilters);
        brandSelect.addEventListener('change', applyFilters);
        catSelect.addEventListener('change', applyFilters);
        baySelect.addEventListener('change', () => {{
          currentBayLabel.textContent = baySelect.options[baySelect.selectedIndex].text;
          applyFilters();
        }});
        levelSelect.addEventListener('change', applyFilters);
        
        resetBtn.addEventListener('click', () => {{
          searchInput.value = ''; currentLegendFilter = null;
          document.querySelectorAll('.legend-chip').forEach(c => c.classList.remove('active'));
          brandSelect.value = 'ALL'; catSelect.value = 'ALL'; baySelect.value = 'ALL'; levelSelect.value = 'ALL';
          currentBayLabel.textContent = "Todos los Cuerpos";
          scale = 1; posX = 0; posY = 0; updateTransform();
          applyFilters();
        }});

        const modal = document.getElementById('productModal');
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
                
                const ventaVal = parseFloat((card.getAttribute('data-venta') || "0").replace(/,/g, '')) || 0;
                document.getElementById('m-venta').textContent = "S/ " + ventaVal.toLocaleString('en-US', {{minimumFractionDigits:2, maximumFractionDigits:2}});
                document.getElementById('m-top').textContent = card.classList.contains('is-top') ? '⭐ SÍ' : 'NO';
                
                modal.classList.add('active');
            }});
        }});
        document.querySelector('.modal-close').addEventListener('click', () => modal.classList.remove('active'));
        window.addEventListener('click', (e) => {{ if(e.target === modal) modal.classList.remove('active'); }});

        setTimeout(applyFilters, 100);
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

df_raw, df_aux_raw, df_jer_raw, df_fotos_raw, info_hora, error_nube = cargar_datos_nube(URL_NUBE, URL_JERARQUIA, URL_FOTOS)

# --- HEADER CON BOTONES COMPACTOS ---
col_head1, col_head2, col_head3 = st.columns([5, 2, 2])
with col_head1:
    st.markdown("<h2 style='margin: 0; padding: 0; font-size: 1.5rem; color: #fff;'>🏪 Planograma 2.0</h2>", unsafe_allow_html=True)
with col_head2:
    if st.button("🔄 Actualizar", use_container_width=True):
        st.cache_data.clear()
        st.session_state.ultimo_acceso = time.time()
        st.rerun()
with col_head3:
    if st.button("🚪 Salir", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.ultimo_acceso = 0
        st.rerun()

st.caption(f"Desarrollado por Alfredo HM | {info_hora if info_hora else ''}")

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
                df_margen = df_margen[df_margen['Mat_Ventas_Str'] != ""].drop_duplicates(subset=['Mat_Ventas_Str'])
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
            rename_dict = {'DEPARTAMENTO (2)': 'Departamento', 'SECCIÓN (3)': 'Sección', 'CATEGORIA (4)': 'Categoría', 'GRUPO ARTICULO (6)': 'Grupo de artículo'}
            cols_to_keep = ['CodGA_Str']
            for old_name, new_name in rename_dict.items():
                if old_name in df_jer_raw.columns:
                    df_jer_raw.rename(columns={old_name: new_name}, inplace=True)
                    cols_to_keep.append(new_name)
                    
            df_jer_unique = df_jer_raw[cols_to_keep].drop_duplicates(subset=['CodGA_Str'])
            df_base = df_base.merge(df_jer_unique, left_on='Grupo_A_Str', right_on='CodGA_Str', how='left')
            for col in columnas_jerarquia: df_base[col] = df_base[col].fillna('S/D') if col in df_base.columns else 'S/D'
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
        else: df_base['Links de fotos'] = ""
    else: df_base['Links de fotos'] = ""
        
    df_base.drop(columns=['COD_REAL_Str', 'Grupo_A_Str', 'CodGA_Str', '_SKUReferenceCode'], inplace=True, errors='ignore')

    df_base['Venta_Num'] = df_base['Venta'].apply(safe_float)
    df_base['Margen_Num'] = df_base['Monto Margen'].apply(safe_float)
    df_base['Part_Num'] = df_base['% Part'].apply(safe_float)
    df_base['Stock_Num'] = df_base['Stock'].apply(safe_float)
    df_base['Cob_Num'] = df_base['Cobertura'].apply(safe_float)
    df_base['Caras_Num'] = df_base['Caras'].apply(lambda x: safe_float(x, default=1.0))
    col_unid = 'Total Unid en Bandeja' if 'Total Unid en Bandeja' in df_base.columns else ('Total_Unidades' if 'Total_Unidades' in df_base.columns else 'Stock')
    df_base['Unid_Bandeja_Num'] = df_base[col_unid].apply(safe_float)
    
    df_unicos = df_base.drop_duplicates(subset=['COD REAL']).copy()
    df_unicos = df_unicos[df_unicos['COD REAL'].notna()]
    
    tab1, tab2 = st.tabs(["🛒 Vista del Pasillo", "📊 Dashboard Financiero"])
    
    with tab1:
        col_v1, col_v2 = st.columns([2, 1])
        with col_v1:
            modo_vista = st.radio(
                "Modo:", 
                ["🖼️ Realograma", "📦 Bloques (Colores)"], 
                index=1, 
                horizontal=True, 
                label_visibility="collapsed"
            )
        with col_v2:
            st.markdown("<div style='text-align: right; font-size: 0.75rem; color: #94a3b8;'>👆 Usa 2 dedos para Zoom / Arrastrar</div>", unsafe_allow_html=True)
            
        html_pasillo = generar_html_pasillo_interactivo(df_base, es_realograma=("Realograma" in modo_vista))
        components.html(html_pasillo, height=900, scrolling=False)
            
    with tab2:
        st.markdown("### 💼 Resumen Ejecutivo")
        ventas_globales = df_unicos['Venta_Num'].sum()
        margen_global = df_unicos['Margen_Num'].sum()
        margen_pct_global = (margen_global / ventas_globales) if ventas_globales > 0 else 0
        total_skus_activos = len(df_unicos)
        
        st.markdown(f"""
            <div class="fin-kpi-container">
                <div class="fin-kpi-card">
                    <span class="fin-kpi-title">Ventas Totales</span>
                    <span class="fin-kpi-val">S/ {ventas_globales:,.0f}</span>
                </div>
                <div class="fin-kpi-card green-theme">
                    <span class="fin-kpi-title">Margen Total</span>
                    <span class="fin-kpi-val">S/ {margen_global:,.0f}</span>
                </div>
                <div class="fin-kpi-card purple-theme">
                    <span class="fin-kpi-title">Margen %</span>
                    <span class="fin-kpi-val">{margen_pct_global*100:.1f}%</span>
                </div>
                <div class="fin-kpi-card">
                    <span class="fin-kpi-title">SKUs Únicos</span>
                    <span class="fin-kpi-val">{total_skus_activos}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        cats_disponibles = sorted([c for c in df_unicos['Categoría'].dropna().unique() if c not in ['S/C', 'nan', '']])
        cat_seleccionada = st.selectbox("Filtrar por Categoría:", ["Todas"] + cats_disponibles)
        
        df_dash_base = df_base.copy()
        if cat_seleccionada != "Todas":
            df_dash_base = df_dash_base[df_dash_base['Categoría'] == cat_seleccionada]
        df_dash_unicos = df_dash_base.drop_duplicates(subset=['COD REAL']).copy()

        # --- GRÁFICO DE BARRAS OPTIMIZADO PARA MÓVIL ---
        st.markdown("##### 📈 Ventas y Rentabilidad por Cuerpo")
        
        bandeja_str = df_dash_base.get('Bandeja', pd.Series(["1.1"]*len(df_dash_base))).astype(str)
        df_dash_base['Cuerpo_Ord'] = bandeja_str.str.extract(r'(\d+)\.(\d+)')[0]
        df_dash_base['Cuerpo_Ord'] = pd.to_numeric(df_dash_base['Cuerpo_Ord'], errors='coerce').fillna(1)
        
        df_sku_cuerpo = df_dash_base.drop_duplicates(subset=['COD REAL', 'Cuerpo_Ord']).copy()
        
        ventas_cuerpo = df_sku_cuerpo.groupby('Cuerpo_Ord').agg(
            Venta_Total=('Venta_Num', 'sum'),
            Margen_Total=('Margen_Num', 'sum'),
            SKUs_Total=('COD REAL', 'count')
        ).reset_index()
        
        ventas_cuerpo['Cuerpo_Label'] = ventas_cuerpo['Cuerpo_Ord'].apply(lambda c: f"Cuerpo {int(c)}")
        ventas_cuerpo['Margen_Pct'] = ventas_cuerpo.apply(
            lambda r: r['Margen_Total'] / r['Venta_Total'] if r['Venta_Total'] > 0 else 0, axis=1
        )
        ventas_cuerpo = ventas_cuerpo.sort_values('Cuerpo_Ord')

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(
                x=ventas_cuerpo['Cuerpo_Label'], 
                y=ventas_cuerpo['Venta_Total'],
                name="Ventas (S/)",
                text=ventas_cuerpo['Venta_Total'].apply(lambda x: f"S/ {x/1000:,.1f}K" if x >= 1000 else f"S/ {x:,.0f}"),
                textposition='auto',
                textfont=dict(color='#ffffff', size=9, weight='bold'),
                marker=dict(color='rgba(59, 130, 246, 0.8)'),
                hovertemplate="<b>%{x}</b><br>Venta: S/ %{y:,.2f}<extra></extra>"
            ), secondary_y=False
        )

        fig.add_trace(
            go.Scatter(
                x=ventas_cuerpo['Cuerpo_Label'], 
                y=ventas_cuerpo['Margen_Pct'],
                name="Margen %",
                mode="lines+markers+text",
                text=ventas_cuerpo['Margen_Pct'].apply(lambda x: f"{x*100:.0f}%"),
                textposition='top center',
                textfont=dict(color='#10b981', size=10, weight='bold'),
                marker=dict(color="#10b981", size=6),
                line=dict(color="#10b981", width=2),
                hovertemplate="<b>%{x}</b><br>Margen: %{text}<extra></extra>"
            ), secondary_y=True
        )

        # CONFIGURACIÓN RESPONSIVE DE EJES PARA EVITAR AMONTONAMIENTO
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color='#cbd5e1', size=9)),
            margin=dict(t=10, b=40, l=5, r=5),
            xaxis=dict(
                showgrid=False, 
                color='#cbd5e1', 
                tickangle=-30, # Inclinación para no chocar en pantallas angostas
                tickfont=dict(size=9, weight='bold')
            ),
            yaxis=dict(title=None, showgrid=True, gridcolor='rgba(255,255,255,0.08)', color='#cbd5e1', showticklabels=False),
            yaxis2=dict(title=None, showgrid=False, color='#10b981', showticklabels=False)
        )
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # --- DONUT & FAIR SHARE ---
        col_d1, col_d2 = st.columns([1, 1])
        with col_d1:
            st.markdown("##### 🍩 Distribución de Ventas")
            vista_anillo = st.selectbox("Agrupar por:", ["Categoría", "Marca", "Sección", "Departamento"], label_visibility="collapsed")
            df_pie = df_dash_unicos.groupby(vista_anillo)['Venta_Num'].sum().reset_index()
            df_pie = df_pie[df_pie['Venta_Num'] > 0].sort_values(by='Venta_Num', ascending=False).head(6)
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=df_pie[vista_anillo], 
                values=df_pie['Venta_Num'], 
                hole=0.5,
                textinfo='percent',
                textposition='inside',
                insidetextorientation='horizontal',
                textfont=dict(size=10, color='#ffffff', family='Arial Black'),
                marker=dict(colors=['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'])
            )])
            fig_pie.update_layout(
                showlegend=True,
                legend=dict(font=dict(color='#cbd5e1', size=8), orientation='h', yanchor='top', y=-0.1),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=5, b=30, l=5, r=5)
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

        with col_d2:
            st.markdown("##### ⚖️ Fair Share (Espacio vs Venta)")
            df_fs = df_dash_base.groupby('Categoría').agg(
                Espacio=('Caras_Num', 'sum'),
                Venta=('Venta_Num', 'sum')
            ).reset_index()
            df_fs = df_fs[~df_fs['Categoría'].isin(['S/D', 'S/C', 'nan', ''])].copy()
            tot_esp = df_fs['Espacio'].sum()
            tot_vta = df_fs['Venta'].sum()
            
            if tot_esp > 0 and tot_vta > 0:
                df_fs['% Espacio'] = df_fs['Espacio'] / tot_esp
                df_fs['% Venta'] = df_fs['Venta'] / tot_vta
                df_fs = df_fs.sort_values(by='% Venta', ascending=False).head(5)
                
                fig_fs = go.Figure()
                fig_fs.add_trace(go.Bar(x=df_fs['Categoría'], y=df_fs['% Espacio'], name="% Espacio", marker=dict(color='#3b82f6')))
                fig_fs.add_trace(go.Bar(x=df_fs['Categoría'], y=df_fs['% Venta'], name="% Venta", marker=dict(color='#10b981')))
                fig_fs.update_layout(
                    barmode='group',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(color='#cbd5e1', size=8)),
                    margin=dict(t=5, b=40, l=5, r=5),
                    xaxis=dict(color='#cbd5e1', tickangle=-25, tickfont=dict(size=8, weight='bold')),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.08)', showticklabels=False)
                )
                fig_fs.update_xaxes(fixedrange=True)
                fig_fs.update_yaxes(fixedrange=True)
                st.plotly_chart(fig_fs, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        st.markdown("### 📋 Descarga de Datos")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_unicos.to_excel(writer, index=False, sheet_name='Reporte')
        st.download_button(
            label="📥 Descargar Reporte Completo (.xlsx)",
            data=buffer.getvalue(),
            file_name="reporte_planograma.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
