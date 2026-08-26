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
            padding-left: 1.2rem !important;
            padding-right: 1.2rem !important;
            padding-top: 1.5rem !important; 
            max-width: 100% !important;
        }
        .fin-kpi-container { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
        .fin-kpi-card { flex: 1; min-width: 200px; background: linear-gradient(145deg, #111c30 0%, #0f172a 100%); border-left: 5px solid #3b82f6; border-radius: 8px; padding: 18px 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); display: flex; flex-direction: column; justify-content: center; }
        .fin-kpi-title { font-size: 0.80rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px; }
        .fin-kpi-val { font-size: 2.0rem; font-weight: 900; color: #ffffff; line-height: 1; }
        .fin-kpi-card.green-theme { border-left-color: #10b981; }
        .fin-kpi-card.purple-theme { border-left-color: #8b5cf6; }
        
        .login-card {
            background-color: #111c30;
            padding: 30px;
            border-radius: 10px;
            border: 1px solid #1e3a8a;
            max-width: 450px;
            margin: 60px auto;
            box-shadow: 0 8px 16px rgba(0,0,0,0.5);
        }
    </style>
""", unsafe_allow_html=True)

# --- CAPA DE SEGURIDAD (SESIÓN 60 MINUTOS) ---
TIEMPO_EXPIRACION_SEGUNDOS = 60 * 60

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "ultimo_acceso" not in st.session_state:
    st.session_state.ultimo_acceso = 0

if st.session_state.autenticado:
    if time.time() - st.session_state.ultimo_acceso > TIEMPO_EXPIRACION_SEGUNDOS:
        st.session_state.autenticado = False
        st.session_state.ultimo_acceso = 0
        st.warning("⏳ Tu sesión ha expirado por tiempo límite (60 min). Ingresa nuevamente.")

def login_form():
    st.markdown("<div class='login-card'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #fff; margin-top: 0;'>🔒 Acceso Planograma 2.0</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.85rem;'>Ingresa tus credenciales corporativas (Sesión: 60 min)</p>", unsafe_allow_html=True)
    
    usuario = st.text_input("Usuario:", key="user_input")
    password = st.text_input("Contraseña:", type="password", key="pass_input")
    
    if st.button("Iniciar Sesión", type="primary", use_container_width=True):
        if usuario == "S003" and password == "S0032026":
            st.session_state.autenticado = True
            st.session_state.ultimo_acceso = time.time()
            st.rerun()
        else:
            st.error("❌ Credenciales incorrectas. Verifica usuario o contraseña.")
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

# --- GENERADOR HTML INTERACTIVO ---
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
        * {{ box-sizing: border-box; }}
        body, html {{ 
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
          background-color: #070d19; 
          color: #fff; 
          margin: 0; 
          padding: 0; 
          min-height: 100vh; 
          overflow-x: hidden; 
        }}
        
        .main-container {{ 
          padding: 10px 8px; 
          min-height: 100vh; 
          display: flex; 
          flex-direction: column; 
          box-sizing: border-box;
        }}

        ::-webkit-scrollbar {{ height: 8px; width: 8px; }}
        ::-webkit-scrollbar-track {{ background: #0f172a; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb {{ background: #3b82f6; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #2563eb; }}

        /* KPI CONTAINER */
        .kpi-container {{ display: flex; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; justify-content: center; flex-shrink: 0; }}
        .kpi-card {{ flex: 1; min-width: 120px; background: #111c30; border: 1px solid #1e3a8a; border-radius: 8px; padding: 10px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.4); }}
        .kpi-title {{ font-size: 0.65rem; font-weight: 800; color: #93c5fd; text-transform: uppercase; margin-bottom: 4px; display: block; letter-spacing: 0.5px; }}
        .kpi-val {{ font-size: 1.5rem; font-weight: 900; line-height: 1; display: block; }}
        
        /* FILTROS */
        .filter-panel {{ background: #111c30; border: 1px solid #1e3a8a; border-radius: 8px; padding: 10px 14px; margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-end; flex-shrink: 0; }}
        .filter-group {{ display: flex; flex-direction: column; gap: 4px; flex-grow: 1; }}
        .filter-label {{ font-size: 0.7rem; font-weight: 700; color: #93c5fd; text-transform: uppercase; }}
        .filter-select, .filter-input {{ background: #ffffff; border: 2px solid #3b82f6; color: #0f172a; padding: 5px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 600; outline: none; width: 100%; min-width: 120px; }}
        .btn-group {{ display: flex; gap: 8px; margin-left: auto; flex-wrap: wrap; align-items: center; }}
        
        .filter-btn-reset {{ background: #ef4444; border: none; color: white; font-weight: 700; font-size: 0.75rem; padding: 8px 14px; border-radius: 4px; cursor: pointer; transition: background 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
        .filter-btn-print {{ background: #10b981; border: none; color: white; font-weight: 700; font-size: 0.75rem; padding: 8px 14px; border-radius: 4px; cursor: pointer; transition: background 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
        
        /* CHECKBOX VISTA CELULAR */
        .mobile-checkbox-label {{
          display: flex;
          align-items: center;
          gap: 6px;
          background: #1e3a8a;
          border: 1.5px solid #3b82f6;
          padding: 6px 12px;
          border-radius: 4px;
          color: #ffffff;
          font-weight: 700;
          font-size: 0.75rem;
          cursor: pointer;
          user-select: none;
        }}
        .mobile-checkbox-label input[type="checkbox"] {{
          accent-color: #f59e0b;
          width: 16px;
          height: 16px;
          cursor: pointer;
        }}
        
        .legend-panel {{ background: #111c30; border: 1px solid #1e3a8a; border-radius: 8px; padding: 8px 16px; margin-bottom: 10px; display: flex; align-items: center; flex-wrap: wrap; gap: 10px; flex-shrink: 0; }}
        .legend-title {{ font-size: 0.75rem; font-weight: 700; color: #93c5fd; text-transform: uppercase; margin-right: 8px; }}
        .legend-chips {{ display: flex; flex-wrap: wrap; gap: 8px; }}
        .legend-chip {{ background: var(--bg); color: var(--tc); border: var(--bd, 1px solid transparent); font-weight: 700; font-size: 0.70rem; padding: 5px 10px; border-radius: 20px; cursor: pointer; transition: all 0.2s; opacity: 0.85; outline: none; }}
        .legend-chip.active {{ opacity: 1; transform: scale(1.05); box-shadow: 0 0 12px rgba(59, 130, 246, 0.9); border: 2px solid #3b82f6 !important; }}
        
        /* CONTENEDOR TÁCTIL PRINCIPAL */
        .aisle-wrapper {{ 
          display: block; 
          width: 100%; 
          position: relative; 
          flex-grow: 1; 
          height: auto;
          min-height: 480px;
          overflow: visible;
          background: #0b1324;
          border-radius: 8px;
          border: 1.5px solid #1e293b;
          touch-action: pan-y;
          padding: 0;
        }}
        
        /* FLECHAS FIJAS A LOS EXTREMOS EN ESCRITORIO */
        .nav-btn {{ 
          position: absolute;
          top: 50%;
          transform: translateY(-50%);
          background: rgba(30, 58, 138, 0.85); 
          color: white; 
          border: 2px solid #3b82f6; 
          border-radius: 8px; 
          width: 44px; 
          height: 60px;
          font-size: 1.8rem; 
          font-weight: bold; 
          cursor: pointer; 
          z-index: 100; 
          display: flex; 
          align-items: center; 
          justify-content: center; 
          box-shadow: 0 4px 15px rgba(0,0,0,0.6); 
          backdrop-filter: blur(4px);
          transition: all 0.2s;
        }}
        .nav-btn-prev {{ left: 8px; }}
        .nav-btn-next {{ right: 8px; }}
        .nav-btn:disabled {{ opacity: 0; pointer-events: none; }}
        
        .zoom-layer {{
          display: block;
          width: 100%;
          height: auto;
          transform-origin: 0 0;
          will-change: transform;
        }}

        .aisle-container {{ 
          display: flex; 
          flex-direction: row; 
          gap: 16px; 
          background: #0f172a; 
          border-radius: 8px; 
          padding: 14px 45px; 
          overflow-x: auto; 
          overflow-y: visible; 
          scroll-behavior: smooth; 
          scroll-snap-type: x mandatory; 
          width: 100%; 
          box-sizing: border-box;
        }}
        
        .bay-column {{ 
          flex: 0 0 100%; 
          width: 100%; 
          background: #111c30; 
          border: 1.5px solid #1e293b; 
          border-radius: 6px; 
          display: flex; 
          flex-direction: column; 
          height: auto; 
          scroll-snap-align: center; 
          padding-bottom: 12px; 
          box-sizing: border-box;
        }}
        .bay-column.hidden {{ display: none !important; }}
        
        .bay-title {{ background: #1e3a8a; padding: 8px; font-size: 0.90rem; font-weight: 700; text-align: center; border-bottom: 2px solid #3b82f6; border-radius: 4px 4px 0 0; display: flex; flex-direction: column; gap: 2px; flex-shrink: 0; }}
        .bay-subcat {{ font-size: 0.70rem; font-weight: 600; color: #93c5fd; text-transform: uppercase; letter-spacing: 0.3px; }}
        
        .bay-shelves {{ padding: 12px; display: flex; flex-direction: column; gap: 16px; flex-grow: 1; height: auto; }}
        .shelf-row {{ display: flex; flex-direction: column; position: relative; padding-top: 8px; transition: all 0.3s; }}
        .shelf-row.hidden {{ display: none !important; }}
        
        .shelf-products {{ display: flex; flex-direction: row; gap: 4px; padding: 6px 8px; min-height: 105px; overflow-x: auto; padding-bottom: 6px; align-items: flex-end; justify-content: flex-start; }}
        .sku-item.dimmed {{ opacity: 0.15; filter: grayscale(1); z-index: 1; }}
        .sku-item.highlighted {{ transform: scale(1.02); z-index: 20; }}
        
        .shelf-base {{ height: 12px; background: linear-gradient(180deg, #fde047 0%, #ca8a04 100%); border-radius: 2px; box-shadow: 0 4px 6px rgba(0,0,0,0.6); display: flex; justify-content: center; position: relative; z-index: 5; margin-top: -2px; border-top: 1px solid #fef08a; border-bottom: 2px solid #854d0e; }}
        .shelf-name-tag {{ position: absolute; top: 10px; background: rgba(0,0,0,0.7); color: #fef08a; font-size: 0.55rem; padding: 1px 6px; border-radius: 0 0 4px 4px; font-weight: 800; letter-spacing: 0.5px; }}
        
        .sku-group {{ display: flex; flex-direction: column; align-items: center; position: relative; cursor: pointer; transition: all 0.2s; z-index: 10; padding: 0 2px; flex-shrink: 0; }}
        .sku-images-wrapper {{ display: flex; flex-direction: row; align-items: flex-end; gap: 1px; }}
        .sku-images-wrapper img {{ height: 90px; width: auto; max-width: 60px; object-fit: contain; filter: drop-shadow(2px 4px 4px rgba(0,0,0,0.5)); transition: transform 0.2s; }}
        .sku-group:hover .sku-images-wrapper img {{ transform: translateY(-4px); filter: drop-shadow(4px 8px 8px rgba(0,0,0,0.7)); }}
        
        .sku-fleje {{ background: #ffffff; color: #000; border: 1px solid #64748b; font-size: 0.50rem; display: flex; flex-direction: column; align-items: center; line-height: 1; margin-top: 2px; z-index: 15; box-shadow: 0 2px 4px rgba(0,0,0,0.5); width: max-content; padding: 1px 2px; }}
        .fleje-ean {{ font-weight: 600; font-family: monospace; letter-spacing: -0.5px; }}
        .fleje-caras {{ font-weight: 900; background: #e2e8f0; width: 100%; text-align: center; border-top: 1px solid #cbd5e1; padding-top: 1px; color: #1e293b; }}
        
        .alerta-bloqueado .sku-images-wrapper img {{ filter: grayscale(100%) opacity(0.4) drop-shadow(0 0 2px #fff); }}
        .alerta-sinstock .sku-images-wrapper img {{ filter: drop-shadow(0 0 10px #ef4444) drop-shadow(0 0 5px #ef4444); }}
        .alerta-stockbajo .sku-images-wrapper img {{ filter: drop-shadow(0 0 8px #f59e0b); }}
        .sku-group.is-top .top-badge::after {{ content: '⭐'; position: absolute; top: -15px; right: -5px; font-size: 1.1rem; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.8)); z-index: 30; animation: float 2s ease-in-out infinite; }}
        @keyframes float {{ 0% {{transform: translateY(0px);}} 50% {{transform: translateY(-4px);}} 100% {{transform: translateY(0px);}} }}
        
        .sku-card {{ border-radius: 4px; padding: 6px; display: flex; flex-direction: column; justify-content: space-between; min-width: 95px; position: relative; transition: all 0.2s; cursor: pointer; align-items: stretch; flex-shrink: 0; outline: none; }}
        .sku-card.is-top {{ outline: 2px solid #FFC000 !important; outline-offset: -1px; }}
        .sku-pos {{ position: absolute; top: 4px; left: 4px; background: #0f172a; color: #fff; font-size: 0.6rem; font-weight: 800; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; border-radius: 2px; }}
        .sku-caras-tag {{ position: absolute; top: 4px; right: 4px; background: rgba(255,255,255,0.9); color: #000; font-size: 0.55rem; font-weight: 800; padding: 1px 4px; border-radius: 2px; }}
        .sku-details {{ margin-top: 18px; display: flex; flex-direction: column; gap: 3px; text-align: center; overflow: hidden; }}
        .sku-brand-text {{ font-size: 0.65rem; font-weight: 800; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .sku-name-text {{ font-size: 0.70rem; font-weight: 700; line-height: 1.15; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }}
        .sku-bottom-bar {{ margin-top: 4px; border-top: 1px dashed; padding-top: 2px; display: flex; justify-content: space-between; align-items: center; gap: 4px; }}
        .sku-ean-code {{ font-size: 0.60rem; font-family: monospace; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-shrink: 1; }}
        .sku-cap-val {{ font-size: 0.65rem; font-weight: 800; padding: 1px 3px; border-radius: 2px; flex-shrink: 0; }}
        .shelf-bottom-rail {{ height: 8px; background: linear-gradient(180deg, #94a3b8 0%, #475569 100%); border-radius: 0 0 3px 3px; margin-top: 2px; }}
        .shelf-info {{ background: rgba(30, 58, 138, 0.8); padding: 4px 8px; font-size: 0.7rem; font-weight: 700; display: flex; justify-content: space-between; border-left: 3px solid #60a5fa; }}
        
        .modal-overlay {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 99999; opacity: 0; pointer-events: none; transition: opacity 0.2s; }}
        .modal-overlay.active {{ opacity: 1; pointer-events: auto; }}
        .modal-content {{ background: #1e293b; color: #fff; padding: 22px; border-radius: 8px; width: 90%; max-width: 420px; max-height: 85vh; overflow-y: auto; border: 2px solid #3b82f6; }}
        .modal-close {{ position: absolute; top: 10px; right: 15px; font-size: 1.8rem; cursor: pointer; color: #94a3b8; font-weight: bold; line-height: 1; }}
        .m-row {{ border-bottom: 1px solid #334155; padding: 7px 0; display: flex; justify-content: space-between; font-size: 0.85rem; }}
        .m-label {{ font-weight: 700; color: #93c5fd; }}
        .m-val {{ font-weight: 600; text-align: right; max-width: 65%; word-wrap: break-word; }}

        /* --- MODO MÓVIL: SIN FLECHAS, SWIPE CON DEDOS Y AJUSTE 100% --- */
        .mobile-mode-active .nav-btn,
        @media (max-width: 768px) {{
            .nav-btn {{ display: none !important; }}
            .aisle-container {{ padding: 10px 4px !important; }}
            .kpi-container {{
              display: grid !important;
              grid-template-columns: repeat(2, 1fr) !important;
              gap: 8px !important;
              overflow-x: visible !important;
            }}
            .kpi-card {{ min-width: unset !important; }}
            .kpi-card:last-child {{ grid-column: 1 / -1 !important; }}
            .bay-column {{
              flex: 0 0 100% !important;
              width: 100% !important;
              max-width: 100% !important;
              height: auto !important;
            }}
            .bay-shelves {{
              gap: 12px !important;
              padding: 6px !important;
            }}
            .shelf-products {{
              min-height: 80px !important;
              padding: 2px !important;
            }}
            .sku-card {{ min-width: 75px !important; padding: 3px !important; }}
            .sku-images-wrapper img {{ height: 75px !important; max-width: 42px !important; }}
        }}

        @media print {{
          @page {{ size: A4 portrait; margin: 5mm; }}
          body, html, .main-container {{ background-color: #fff !important; color: #000 !important; margin: 0 !important; padding: 0 !important; height: 100% !important; overflow: hidden !important; }}
          .filter-panel, .legend-panel, .modal-overlay, .nav-btn, .kpi-container, .top-panel {{ display: none !important; }}
          .aisle-wrapper {{ display: block !important; width: 100% !important; height: 100% !important; border: none !important; }}
          .aisle-container {{ display: block !important; width: 100% !important; height: 100% !important; background: transparent !important; border: none !important; padding: 0 !important; overflow: visible !important; }}
          .bay-column {{ background: #fff !important; border: 3px solid #000 !important; width: 195mm !important; height: 280mm !important; max-width: 100% !important; page-break-inside: avoid; margin: 0 auto !important; display: flex !important; flex-direction: column !important; }}
          .bay-column.hidden {{ display: none !important; }}
          .bay-title {{ background: #e2e8f0 !important; color: #000 !important; border-bottom: 3px solid #000 !important; padding: 10px !important; font-size: 20pt !important; display: block; text-align: center; }}
          .bay-subcat {{ color: #334155 !important; font-size: 14pt !important; display: block; }}
          .bay-shelves {{ padding: 5px !important; gap: 15px !important; display: flex !important; flex-direction: column !important; flex-grow: 1 !important; justify-content: space-evenly !important; overflow: visible !important; height: 100% !important; }}
          .shelf-row {{ background: transparent !important; display: flex !important; flex-direction: column !important; justify-content: flex-end !important; flex-grow: 1 !important; margin-bottom: 0 !important; padding-top: 5px !important; }}
          .shelf-products {{ flex-grow: 0 !important; padding: 2px !important; gap: 2px !important; display: flex !important; align-items: flex-end !important; justify-content: center !important; overflow: visible !important; }}
          .sku-images-wrapper img {{ height: 110px !important; max-width: 45px !important; filter: none !important; }}
          .sku-fleje {{ font-size: 7pt !important; padding: 2px !important; margin-top: 1px !important; border: 1px solid #000 !important; }}
          .fleje-ean {{ font-size: 7pt !important; font-weight: bold !important; }}
          .fleje-caras {{ font-size: 8pt !important; font-weight: 900 !important; color: #000 !important; background: transparent !important; border-top: 1px solid #000 !important; }}
          .shelf-base {{ height: 10px !important; background: #eab308 !important; border-bottom: 3px solid #000 !important; border-top: 1px solid #000 !important; box-shadow: none !important; margin-top: 0 !important; }}
          .shelf-name-tag {{ background: #fff !important; color: #000 !important; border: 1px solid #000 !important; border-top: none !important; font-size: 8pt !important; top: 8px !important; padding: 1px 4px !important; font-weight: bold !important; }}
          .top-badge::after {{ font-size: 14pt !important; top: -15px !important; filter: none !important; }}
          .sku-card {{ background: #fff !important; border: 2px solid #000 !important; color: #000 !important; padding: 4px !important; display: flex !important; flex-direction: column !important; justify-content: space-between !important; flex-basis: 0 !important; flex-grow: 1 !important; min-width: unset !important; }}
          .sku-pos, .sku-caras-tag {{ background: #fff !important; color: #000 !important; border: 1px solid #000 !important; font-size: 9pt !important; width: auto !important; height: auto !important; padding: 2px 4px !important; font-weight: bold !important; }}
          .sku-details {{ margin-top: 15px !important; }}
          .sku-brand-text {{ font-size: 10pt !important; color: #000 !important; display: block; font-weight: bold !important; }}
          .sku-name-text {{ font-size: 11pt !important; color: #000 !important; -webkit-line-clamp: 4 !important; line-height: 1.2 !important; font-weight: bold !important; }}
          .sku-bottom-bar {{ border-top: 2px dashed #000 !important; margin-top: auto !important; padding-top: 4px !important; }}
          .sku-ean-code, .sku-cap-val, span {{ color: #000 !important; font-size: 9pt !important; }}
          .shelf-info {{ background: #f1f5f9 !important; color: #000 !important; border-left: 5px solid #000 !important; font-size: 14pt !important; padding: 4px 8px !important; font-weight: 900 !important; }}
          .shelf-caras-count {{ background: #e2e8f0 !important; color: #000 !important; font-size: 12pt !important; }}
        }}
      </style>
    </head>
    <body>
      <div class="main-container" id="mainContainer">

        <div id="productModal" class="modal-overlay">
          <div class="modal-content">
            <span class="modal-close">&times;</span>
            <h3 id="m-name" style="margin-top: 0; font-size: 1.1rem; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; line-height: 1.3;">Producto</h3>
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

        <div class="top-panel" style="background: #111c30; border: 1px solid #1e3a8a; border-radius: 8px; padding: 12px; margin-bottom: 12px; display: flex; align-items: center; gap: 15px; flex-wrap: wrap; flex-shrink: 0;">
          <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 1.2rem;">🏆</span>
              <label style="color: #93c5fd; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; margin: 0;">Resaltar TOP Ventas:</label>
              <input type="number" id="topNInput" value="5" min="1" max="500" style="background: #ffffff; border: 2px solid #3b82f6; border-radius: 4px; padding: 4px 8px; width: 70px; font-weight: bold; color: #0f172a; outline: none;">
              <span style="color: #94a3b8; font-size: 0.8rem; font-weight: bold;">SKUs</span>
          </div>
          <div id="topNInfo" style="color: #cbd5e1; font-size: 0.85rem; background: rgba(59,130,246,0.1); padding: 8px 12px; border-radius: 4px; border-left: 4px solid #3b82f6; flex-grow: 1;">
              💡 Calculando...
          </div>
        </div>

        <!-- TARJETAS KPIS -->
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
          <div class="filter-group"><span class="filter-label">📂 Categoría</span><select id="catSelect" class="filter-select"><option value="ALL">Todas</option>{options_categorias}</select></div>
          <div class="filter-group"><span class="filter-label">📦 Cuerpo</span><select id="baySelect" class="filter-select"><option value="ALL">Todos</option>{options_cuerpos}</select></div>
          <div class="filter-group"><span class="filter-label">📶 Nivel</span><select id="levelSelect" class="filter-select"><option value="ALL">Todos</option>{options_niveles}</select></div>
          <div class="btn-group">
            <label class="mobile-checkbox-label">
              <input type="checkbox" id="mobileCheckbox"> 📱 Vista Móvil (Ajuste Auto)
            </label>
            <button id="resetBtn" class="filter-btn-reset">Restablecer</button>
            <button type="button" id="printBayBtn" class="filter-btn-print" title="Imprime el cuerpo visible optimizado en A4">🖨️ Imprimir</button>
          </div>
        </div>

        <div class="legend-panel">
          <span class="legend-title">📍 Leyenda Interactiva</span>
          <div class="legend-chips">
            <button class="legend-chip" data-filter="Bloqueado" style="--bg: #FFC7CE; --tc: #9C0006;">Bloqueado</button>
            <button class="legend-chip" data-filter="Sin Stock" style="--bg: #F4B084; --tc: #833C0C;">Sin Stock</button>
            <button class="legend-chip" data-filter="Stock Bajo" style="--bg: #FFFF99; --tc: #8A5A00;">Stock 1 a 5</button>
            <button class="legend-chip" data-filter="Stock OK" style="--bg: #C6EFCE; --tc: #006100;">Stock > 5</button>
            <button class="legend-chip" data-filter="cob-alta" style="--bg: #ffffff; --tc: #ef4444; --bd: 2px solid #ef4444;">Cobertura Alta</button>
            <button class="legend-chip" data-filter="top-ventas" style="--bg: #ffffff; --tc: #b45309; --bd: 2px solid #FFC000;">★ TOP VENTAS</button>
          </div>
        </div>

        <!-- CONTENEDOR MULTITOUCH CON FLECHAS FIJAS -->
        <div class="aisle-wrapper" id="aisleWrapper">
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
        // --- MOTOR MULTITÁCTIL Y NAVEGACIÓN ---
        const aisleWrapper = document.getElementById('aisleWrapper');
        const zoomLayer = document.getElementById('zoomLayer');
        const container = document.getElementById('aisleContainer');
        const btnPrev = document.getElementById('btnPrev');
        const btnNext = document.getElementById('btnNext');
        
        let scale = 1, minScale = 0.8, maxScale = 3.5;
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

        aisleWrapper.addEventListener('touchstart', (e) => {{
          if (e.touches.length === 1) {{
            if (scale > 1) {{
              isTouching = true;
              startX = e.touches[0].clientX - posX;
              startY = e.touches[0].clientY - posY;
            }}
            const now = new Date().getTime();
            if (now - lastTap < 300 && now - lastTap > 0) {{
              if (scale > 1.2) {{ scale = 1; posX = 0; posY = 0; }}
              else {{ scale = 1.8; }}
              updateZoom();
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
            btnPrev.disabled = container.scrollLeft <= 5;
            btnNext.disabled = container.scrollLeft >= maxScroll - 5;
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

        // --- CHECKBOX MODO MÓVIL ---
        const mobileCheckbox = document.getElementById('mobileCheckbox');
        mobileCheckbox.addEventListener('change', () => {{
          document.body.classList.toggle('mobile-mode-active', mobileCheckbox.checked);
          scale = 1; posX = 0; posY = 0; updateZoom();
          applyFilters();
        }});

        // --- FILTROS Y LÓGICA DE SKUS ---
        const searchInput = document.getElementById('searchInput');
        const brandSelect = document.getElementById('brandSelect');
        const catSelect = document.getElementById('catSelect');
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
          document.getElementById('topNInfo').innerHTML = "💡 Has resaltado el <b>TOP " + topNSkusSet.size + "</b> de esta vista. Concentran el <b style='color:#10b981; font-size:1rem;'>" + pct.toFixed(2) + "%</b> de la venta mostrada (S/ " + totalVentasFiltered.toLocaleString('en-US', {{minimumFractionDigits:2, maximumFractionDigits:2}}) + ").";

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
             if(isTop) {{
                 card.classList.add('is-top');
             }} else {{
                 card.classList.remove('is-top');
             }}

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
          allCats.forEach(opt => {{ if(opt.val === 'ALL' || availableCats.has(opt.val)) catSelect.add(new Option(opt.text, opt.val, false, opt.val === selectedCat)); }});

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
        catSelect.addEventListener('change', applyFilters);
        baySelect.addEventListener('change', applyFilters);
        levelSelect.addEventListener('change', applyFilters);
        topNInput.addEventListener('input', applyFilters);
        
        resetBtn.addEventListener('click', () => {{
          searchInput.value = ''; currentLegendFilter = null;
          document.querySelectorAll('.legend-chip').forEach(c => c.classList.remove('active'));
          brandSelect.innerHTML = ''; allBrands.forEach(o => brandSelect.add(new Option(o.text, o.val)));
          catSelect.innerHTML = ''; allCats.forEach(o => catSelect.add(new Option(o.text, o.val)));
          baySelect.innerHTML = ''; allBays.forEach(o => baySelect.add(new Option(o.text, o.val)));
          levelSelect.innerHTML = ''; allLevels.forEach(o => levelSelect.add(new Option(o.text, o.val)));
          brandSelect.value = 'ALL'; catSelect.value = 'ALL'; baySelect.value = 'ALL'; levelSelect.value = 'ALL';
          topNInput.value = 5;
          scale = 1; posX = 0; posY = 0; updateZoom();
          applyFilters();
        }});

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
            mobileCheckbox.checked = true;
            document.body.classList.add('mobile-mode-active');
            applyFilters();
          }}
        }}, 100);
      </script>
    </body>
    </html>
    """

# --- LÓGICA DE CARGA HÍBRIDA (NUBE + MANUAL) ---
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

# --- HEADER PRINCIPAL ---
col_head1, col_head2, col_head3, col_head4 = st.columns([4, 1.5, 3.5, 1])

with col_head1:
    st.markdown("<h1 style='margin: 0; padding: 0; font-size: 2.1rem; color: #fff;'>📦 Planograma 2.0</h1>", unsafe_allow_html=True)
    
with col_head2:
    st.markdown("<div style='margin-top: 5px;'>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar", use_container_width=True):
        st.cache_data.clear()
        st.session_state.ultimo_acceso = time.time()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with col_head3:
    header_time_placeholder = st.empty()

with col_head4:
    st.markdown("<div style='margin-top: 5px;'>", unsafe_allow_html=True)
    if st.button("🚪 Salir", use_container_width=True, help="Cerrar sesión segura"):
        st.session_state.autenticado = False
        st.session_state.ultimo_acceso = 0
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='border-bottom: 2px solid #1e3a8a; padding-bottom: 5px; margin-bottom: 15px;'><span style='color: #93c5fd; font-size: 0.9rem;'>Análisis interactivo de pasillos y rentabilidad de tienda</span></div>", unsafe_allow_html=True)

with st.spinner("Sincronizando base de datos central, jerarquías e imágenes..."):
    df_nube, df_aux_nube, df_jer_nube, df_fotos_nube, info_hora, error_nube = cargar_datos_nube(URL_NUBE, URL_JERARQUIA, URL_FOTOS)

header_time_placeholder.markdown(f"""
    <div style="text-align: right; margin-top: 5px;">
        <div style="font-size: 0.92rem; color: #cbd5e1;">Desarrollado por <b>Alfredo HM</b></div>
        <div style="font-size: 0.75rem; color: #64748b; margin-top: 2px;">Última actualización: {info_hora if info_hora else 'No disponible'}</div>
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
        st.markdown("### ⚙️ Control de Visualización")
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
            st.markdown("<div style='text-align: right; font-size: 0.82rem; color: #94a3b8; margin-top: 5px;'>👆 <i>Pellizca con 2 dedos para Zoom y arrastra para recorrer la góndola.</i></div>", unsafe_allow_html=True)
            
        st.markdown("---")
        
        html_pasillo = generar_html_pasillo_interactivo(df_base, es_realograma=es_realograma)
        components.html(html_pasillo, height=2200, scrolling=False)
            
    with tab2:
        top_n_fijo = 5
        df_top_calc_dash = df_unicos.sort_values(by='Venta_Num', ascending=False)
        skus_top_dash = df_top_calc_dash.head(top_n_fijo)['COD REAL'].astype(str).str.strip().tolist()
        df_unicos['TOPVENTAS'] = df_unicos['COD REAL'].astype(str).str.strip().apply(lambda x: "TOP" if x in skus_top_dash else "NO")

        st.markdown("### 💼 Resumen Ejecutivo")
        
        ventas_globales = df_unicos['Venta_Num'].sum()
        margen_global = df_unicos['Margen_Num'].sum()
        margen_pct_global = (margen_global / ventas_globales) if ventas_globales > 0 else 0
        total_skus_activos = len(df_unicos)
        
        st.markdown(f"""
            <div class="fin-kpi-container">
                <div class="fin-kpi-card">
                    <span class="fin-kpi-title">Ventas Totales (Acumuladas)</span>
                    <span class="fin-kpi-val">S/ {ventas_globales:,.2f}</span>
                </div>
                <div class="fin-kpi-card green-theme">
                    <span class="fin-kpi-title">Margen Total (Acumulado)</span>
                    <span class="fin-kpi-val">S/ {margen_global:,.2f}</span>
                </div>
                <div class="fin-kpi-card purple-theme">
                    <span class="fin-kpi-title">Margen Global (%)</span>
                    <span class="fin-kpi-val">{margen_pct_global*100:.1f}%</span>
                </div>
                <div class="fin-kpi-card">
                    <span class="fin-kpi-title">SKUs Únicos en Mueble</span>
                    <span class="fin-kpi-val">{total_skus_activos}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        cats_disponibles = sorted([c for c in df_unicos['Categoría'].dropna().unique() if c not in ['S/C', 'nan', '']])
        col_seg_cat, _ = st.columns([2, 2])
        with col_seg_cat:
            cat_seleccionada = st.selectbox("🎯 Filtrar Dashboard por Categoría:", ["Todas las Categorías"] + cats_disponibles)
        
        df_dash_base = df_base.copy()
        if cat_seleccionada != "Todas las Categorías":
            df_dash_base = df_dash_base[df_dash_base['Categoría'] == cat_seleccionada]
            
        df_dash_unicos = df_dash_base.drop_duplicates(subset=['COD REAL']).copy()

        col_graf_izq, col_graf_der = st.columns([6.5, 3.5])
        
        with col_graf_izq:
            st.markdown("##### 📈 Ventas y Rentabilidad por Cuerpo")
            
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
                if cat_nombre and len(cat_nombre) > 18:
                    cat_nombre = cat_nombre[:16] + ".."
                return f"Cuerpo {int(c_num)}<br><sub>{cat_nombre}</sub>" if cat_nombre else f"Cuerpo {int(c_num)}"

            ventas_cuerpo['Cuerpo_Label'] = ventas_cuerpo['Cuerpo_Ord'].apply(crear_etiqueta_eje)
            ventas_cuerpo['Margen_Pct'] = ventas_cuerpo.apply(
                lambda row: row['Margen_Total'] / row['Venta_Total'] if row['Venta_Total'] > 0 else 0, 
                axis=1
            )
            
            col_ord, _ = st.columns([1.5, 2.5])
            with col_ord:
                orden_grafico = st.selectbox("Ordenar por:", 
                    ["Cuerpo (Secuencial)", "Mayor a Menor Venta", "Mayor Margen (%)"],
                    label_visibility="collapsed"
                )
            
            if orden_grafico == "Mayor a Menor Venta": ventas_cuerpo = ventas_cuerpo.sort_values('Venta_Total', ascending=False)
            elif orden_grafico == "Mayor Margen (%)": ventas_cuerpo = ventas_cuerpo.sort_values('Margen_Pct', ascending=False)
            else: ventas_cuerpo = ventas_cuerpo.sort_values('Cuerpo_Ord')

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Bar(
                    x=ventas_cuerpo['Cuerpo_Label'], 
                    y=ventas_cuerpo['Venta_Total'],
                    name="Ventas Totales (S/)",
                    text=ventas_cuerpo['Venta_Total'].apply(lambda x: f"S/ {x:,.0f}"),
                    textposition='auto',
                    textfont=dict(color='#ffffff', size=11, weight='bold'),
                    marker=dict(color='rgba(59, 130, 246, 0.75)', line=dict(color='#3b82f6', width=2)),
                    hovertemplate="<b>%{x}</b><br>Ventas: S/ %{y:,.2f}<br>SKUs Únicos: %{customdata}<extra></extra>",
                    customdata=ventas_cuerpo['SKUs_Total']
                ), secondary_y=False
            )

            fig.add_trace(
                go.Scatter(
                    x=ventas_cuerpo['Cuerpo_Label'], 
                    y=ventas_cuerpo['Margen_Pct'],
                    name="Margen %",
                    mode="lines+markers+text",
                    text=ventas_cuerpo['Margen_Pct'].apply(lambda x: f"{x*100:,.1f}%"),
                    textposition='top center',
                    textfont=dict(color='#10b981', size=12, weight='bold'),
                    marker=dict(color="#10b981", size=9, symbol='circle', line=dict(color='#ffffff', width=2)),
                    line=dict(color="#10b981", width=3.5, shape='spline'),
                    hovertemplate="<b>%{x}</b><br>Margen: %{text}<extra></extra>"
                ), secondary_y=True
            )

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(color='#cbd5e1')),
                margin=dict(t=10, b=30, l=10, r=10),
                xaxis=dict(showgrid=False, color='#cbd5e1', tickfont=dict(size=11, weight='bold')),
                yaxis=dict(title="Ventas (S/)", showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='#cbd5e1', zeroline=False),
                yaxis2=dict(title="Margen (%)", showgrid=False, color='#10b981', zeroline=False)
            )
            
            fig.update_xaxes(fixedrange=True)
            fig.update_yaxes(fixedrange=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        with col_graf_der:
            st.markdown("##### 🍩 Distribución de Ventas")
            
            vista_anillo = st.selectbox("Analizar por:", 
                ["Categoría", "Departamento", "Sección", "Grupo de artículo", "Marca"], 
                label_visibility="collapsed"
            )
            
            df_pie = df_dash_unicos.groupby(vista_anillo)['Venta_Num'].sum().reset_index()
            df_pie = df_pie[df_pie['Venta_Num'] > 0].sort_values(by='Venta_Num', ascending=False)
            
            ventas_dash_total = df_dash_unicos['Venta_Num'].sum()
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=df_pie[vista_anillo], 
                values=df_pie['Venta_Num'], 
                hole=0.48,
                textinfo='label+percent',
                textposition='inside',
                insidetextorientation='horizontal',
                textfont=dict(size=13, color='#ffffff', family='Arial Black'),
                marker=dict(colors=['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#14b8a6'], 
                            line=dict(color='#0f172a', width=2))
            )])
            
            fig_pie.update_layout(
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=10, b=10, l=10, r=10),
                annotations=[dict(text=f'<b>S/ {ventas_dash_total/1000:,.1f}K</b>', x=0.5, y=0.5, font_size=18, showarrow=False, font_color='#ffffff')]
            )
            fig_pie.update_traces(hovertemplate="<b>%{label}</b><br>Ventas: S/ %{value:,.2f}<br>Participación: %{percent}<extra></extra>")
            
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        st.markdown("### ⚖️ Análisis Fair Share: Participación de Espacio vs Rendimiento Financiero")
        
        col_fs_dim, col_fs_met = st.columns([2, 2])
        with col_fs_dim:
            dim_fs = st.selectbox(
                "Segmentar Fair Share por:", 
                ["Categoría", "Sección", "Departamento", "Grupo de artículo", "Marca"],
                key="fs_dim_select"
            )
        with col_fs_met:
            metrica_espacio = st.radio(
                "Métrica de Espacio Físico a Comparar:",
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
            
            fig_fs.add_trace(go.Bar(
                x=df_fs[dim_fs],
                y=df_fs['Pct_Espacio'],
                name=f"% Espacio ({'Caras' if metrica_espacio == 'Caras (Facings)' else 'Unid. Bandeja'})",
                text=df_fs['Pct_Espacio'].apply(lambda x: f"{x*100:.1f}%"),
                textposition='auto',
                textfont=dict(color='#ffffff', size=11, weight='bold'),
                marker=dict(color='rgba(59, 130, 246, 0.85)', line=dict(color='#3b82f6', width=2)),
                hovertemplate="<b>%{x}</b><br>% Espacio: %{y:.1%}<br>Total Físico: %{customdata:,.0f}<extra></extra>",
                customdata=df_fs['Espacio_Total']
            ))
            
            fig_fs.add_trace(go.Bar(
                x=df_fs[dim_fs],
                y=df_fs['Pct_Ventas'],
                name="% Ventas (Monto S/)",
                text=df_fs['Pct_Ventas'].apply(lambda x: f"{x*100:.1f}%"),
                textposition='auto',
                textfont=dict(color='#ffffff', size=11, weight='bold'),
                marker=dict(color='rgba(16, 185, 129, 0.85)', line=dict(color='#10b981', width=2)),
                hovertemplate="<b>%{x}</b><br>% Ventas: %{y:.1%}<br>Ventas S/: %{customdata:,.2f}<extra></extra>",
                customdata=df_fs['Ventas_Total']
            ))

            fig_fs.add_trace(go.Bar(
                x=df_fs[dim_fs],
                y=df_fs['Pct_Margen'],
                name="% Margen (Ganancia S/)",
                text=df_fs['Pct_Margen'].apply(lambda x: f"{x*100:.1f}%"),
                textposition='auto',
                textfont=dict(color='#ffffff', size=11, weight='bold'),
                marker=dict(color='rgba(245, 158, 11, 0.85)', line=dict(color='#f59e0b', width=2)),
                hovertemplate="<b>%{x}</b><br>% Margen: %{y:.1%}<br>Margen S/: %{customdata:,.2f}<extra></extra>",
                customdata=df_fs['Margen_Total']
            ))
            
            fig_fs.update_layout(
                barmode='group',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(color='#cbd5e1')),
                margin=dict(t=20, b=40, l=10, r=10),
                xaxis=dict(showgrid=False, color='#cbd5e1', tickfont=dict(size=11, weight='bold')),
                yaxis=dict(title="Participación Relativa (%)", showgrid=True, gridcolor='rgba(255,255,255,0.08)', color='#cbd5e1', tickformat=".0%")
            )
            
            fig_fs.update_xaxes(fixedrange=True)
            fig_fs.update_yaxes(fixedrange=True)
            st.plotly_chart(fig_fs, use_container_width=True, config={'displayModeBar': False})
            
            col_diag1, col_diag2 = st.columns(2)
            subdimensionados = df_fs[df_fs['Brecha_Share'] > 0.03]
            sobredimensionados = df_fs[df_fs['Brecha_Share'] < -0.03]
            
            with col_diag1:
                if not subdimensionados.empty:
                    top_sub = subdimensionados.iloc[0]
                    st.success(f"🚀 **Oportunidad de Crecimiento:** `{top_sub[dim_fs]}` genera el **{top_sub['Pct_Ventas']*100:.1f}%** de las ventas pero solo ocupa el **{top_sub['Pct_Espacio']*100:.1f}%** del espacio físico.")
                else:
                    st.info("✅ La asignación de espacio físico está equilibrada frente a las ventas.")
                    
            with col_diag2:
                if not sobredimensionados.empty:
                    top_sobre = sobredimensionados.sort_values(by='Brecha_Share', ascending=True).iloc[0]
                    st.warning(f"⚠️ **Alerta de Sobreasignación:** `{top_sobre[dim_fs]}` consume el **{top_sobre['Pct_Espacio']*100:.1f}%** del espacio pero solo aporta el **{top_sobre['Pct_Ventas']*100:.1f}%** de las ventas.")
                else:
                    st.info("✅ No se detectan sobreasignaciones críticas de espacio físico.")
            
        st.markdown("---")
        
        st.markdown("### 📋 Reporte Detallado (SKUs Únicos)")
        
        col_filt, col_dl = st.columns([4, 1.5])
        with col_filt:
            filtro_reporte = st.selectbox("Filtrar Tabla Resumen:", [
                "Todos los SKUs",
                "Bloqueados (Estado B)",
                "Sin Stock (Stock = 0)",
                "Stock Bajo (Stock 1 a 5)",
                "Cobertura Alta (≥ 30)"
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
            elif filtro_reporte == "Sin Stock (Stock = 0)":
                df_rep = df_rep[(df_rep['Estado'].astype(str).str.strip().str.upper() == 'A') & (df_rep['Stock_Num'] <= 0)]
            elif filtro_reporte == "Stock Bajo (Stock 1 a 5)":
                df_rep = df_rep[(df_rep['Estado'].astype(str).str.strip().str.upper() == 'A') & (df_rep['Stock_Num'] > 0) & (df_rep['Stock_Num'] <= 5)]
            elif filtro_reporte == "Cobertura Alta (≥ 30)":
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
                
            st.markdown("<div style='margin-top: 15px;'>", unsafe_allow_html=True)
            st.download_button(
                label="📥 Descargar a Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name="reporte_planograma_skus_unicos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("<p style='font-size: 0.85rem; color: #94a3b8; margin-top: -10px;'>💡 También puedes usar el ícono nativo de descarga que aparece al pasar el cursor sobre la esquina derecha de la tabla.</p>", unsafe_allow_html=True)
        st.dataframe(df_rep[cols_to_show], use_container_width=True, hide_index=True)
