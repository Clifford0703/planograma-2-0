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
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1.2rem !important; 
            max-width: 100% !important;
        }
        .fin-kpi-container { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
        .fin-kpi-card { flex: 1; min-width: 180px; background: linear-gradient(145deg, #111c30 0%, #0f172a 100%); border-left: 5px solid #3b82f6; border-radius: 8px; padding: 14px 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); display: flex; flex-direction: column; justify-content: center; }
        .fin-kpi-title { font-size: 0.75rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px; }
        .fin-kpi-val { font-size: 1.7rem; font-weight: 900; color: #ffffff; line-height: 1; }
        .fin-kpi-card.green-theme { border-left-color: #10b981; }
        .fin-kpi-card.purple-theme { border-left-color: #8b5cf6; }
        
        .login-card {
            background-color: #111c30;
            padding: 30px;
            border-radius: 10px;
            border: 1px solid #1e3a8a;
            max-width: 420px;
            margin: 40px auto;
            box-shadow: 0 8px 16px rgba(0,0,0,0.5);
        }
    </style>
""", unsafe_allow_html=True)

# --- CAPA DE SEGURIDAD CON TIMEOUT DE 60 MINUTOS ---
TIEMPO_EXPIRACION_SEGUNDOS = 60 * 60  # 60 minutos = 3600 seg

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "ultimo_acceso" not in st.session_state:
    st.session_state.ultimo_acceso = 0

# Validación de expiración de sesión
if st.session_state.autenticado:
    tiempo_transcurrido = time.time() - st.session_state.ultimo_acceso
    if tiempo_transcurrido > TIEMPO_EXPIRACION_SEGUNDOS:
        st.session_state.autenticado = False
        st.session_state.ultimo_acceso = 0
        st.warning("⏳ Tu sesión ha expirado por inactividad (60 min). Ingresa nuevamente.")

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

# Actualiza el timer en cada interacción
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

# --- GENERADOR HTML INTERACTIVO (OPTIMIZADO PARA MÓVIL Y PINCH-TO-ZOOM) ---
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
      <!-- VIEWPORT OPTIMIZADO PARA CELULAR: Permite Zoom Natural y Pinch-to-Zoom -->
      <meta name="viewport" content="width=device-width, initial-scale=0.85, minimum-scale=0.25, maximum-scale=5.0, user-scalable=yes">
      <style>
        * {{ box-sizing: border-box; }}
        body, html {{ 
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
          background-color: #070d19; 
          color: #fff; 
          margin: 0; 
          padding: 0; 
          width: 100%;
          min-height: 100vh;
          touch-action: manipulation;
        }}
        
        .main-container {{ 
          padding: 8px; 
          width: 100%; 
          display: flex; 
          flex-direction: column; 
        }}

        ::-webkit-scrollbar {{ height: 6px; width: 6px; }}
        ::-webkit-scrollbar-track {{ background: #0f172a; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb {{ background: #3b82f6; border-radius: 4px; }}

        .kpi-container {{ 
          display: flex; 
          gap: 8px; 
          margin-bottom: 8px; 
          overflow-x: auto; 
          padding-bottom: 4px; 
          flex-shrink: 0; 
          scroll-snap-type: x mandatory;
        }}
        .kpi-card {{ 
          flex: 0 0 115px; 
          background: #111c30; 
          border: 1px solid #1e3a8a; 
          border-radius: 6px; 
          padding: 6px 8px; 
          text-align: center; 
          scroll-snap-align: start;
        }}
        .kpi-title {{ font-size: 0.60rem; font-weight: 800; color: #93c5fd; text-transform: uppercase; margin-bottom: 2px; display: block; }}
        .kpi-val {{ font-size: 1.3rem; font-weight: 900; line-height: 1; display: block; }}
        
        .filter-panel {{ 
          background: #111c30; 
          border: 1px solid #1e3a8a; 
          border-radius: 6px; 
          padding: 8px 10px; 
          margin-bottom: 8px; 
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
          gap: 6px; 
          align-items: flex-end; 
        }}
        .filter-group {{ display: flex; flex-direction: column; gap: 2px; }}
        .filter-label {{ font-size: 0.65rem; font-weight: 700; color: #93c5fd; text-transform: uppercase; }}
        .filter-select, .filter-input {{ 
          background: #ffffff; 
          border: 1.5px solid #3b82f6; 
          color: #0f172a; 
          padding: 4px 6px; 
          border-radius: 4px; 
          font-size: 0.80rem; 
          font-weight: 600; 
          outline: none; 
          width: 100%; 
        }}
        .btn-group {{ display: flex; gap: 6px; grid-column: 1 / -1; margin-top: 4px; }}
        
        .filter-btn-reset, .filter-btn-print {{ 
          flex: 1;
          border: none; 
          color: white; 
          font-weight: 700; 
          font-size: 0.72rem; 
          padding: 6px 10px; 
          border-radius: 4px; 
          cursor: pointer; 
          text-align: center;
        }}
        .filter-btn-reset {{ background: #ef4444; }}
        .filter-btn-print {{ background: #10b981; }}
        
        .legend-panel {{ 
          background: #111c30; 
          border: 1px solid #1e3a8a; 
          border-radius: 6px; 
          padding: 6px 10px; 
          margin-bottom: 8px; 
          display: flex; 
          align-items: center; 
          gap: 6px; 
          overflow-x: auto;
        }}
        .legend-title {{ font-size: 0.68rem; font-weight: 700; color: #93c5fd; white-space: nowrap; }}
        .legend-chips {{ display: flex; gap: 6px; flex-shrink: 0; }}
        .legend-chip {{ 
          background: var(--bg); 
          color: var(--tc); 
          border: var(--bd, 1px solid transparent); 
          font-weight: 700; 
          font-size: 0.65rem; 
          padding: 4px 8px; 
          border-radius: 15px; 
          cursor: pointer; 
          white-space: nowrap;
        }}
        .legend-chip.active {{ transform: scale(1.05); border: 2px solid #3b82f6 !important; }}
        
        /* CONTENEDOR DEL PLANOGRAMA / ZOOM Y SCROLL MULTITOUCH */
        .aisle-wrapper {{ 
          display: flex; 
          align-items: stretch; 
          gap: 6px; 
          width: 100%; 
          position: relative; 
          touch-action: pan-x pan-y pinch-zoom;
        }}
        .nav-btn {{ 
          background: #1e3a8a; 
          color: white; 
          border: 1px solid #3b82f6; 
          border-radius: 6px; 
          width: 28px; 
          font-size: 1.1rem; 
          font-weight: bold; 
          cursor: pointer; 
          display: flex; 
          align-items: center; 
          justify-content: center; 
          flex-shrink: 0; 
        }}
        .nav-btn:disabled {{ background: #0f172a; border-color: #334155; color: #475569; }}
        
        .aisle-container {{ 
          display: flex; 
          flex-direction: row; 
          gap: 12px; 
          background: #0f172a; 
          border: 1px solid #1e293b; 
          border-radius: 8px; 
          padding: 10px; 
          overflow-x: auto; 
          overflow-y: hidden; 
          scroll-behavior: smooth; 
          scroll-snap-type: x mandatory; 
          flex-grow: 1; 
          touch-action: pan-x pan-y pinch-zoom;
        }}
        
        .bay-column {{ 
          flex: 0 0 88vw; 
          max-width: 480px; 
          background: #111c30; 
          border: 1.5px solid #1e293b; 
          border-radius: 6px; 
          display: flex; 
          flex-direction: column; 
          scroll-snap-align: center; 
          padding-bottom: 12px; 
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
          gap: 16px; 
          flex-grow: 1; 
        }}
        .shelf-row {{ display: flex; flex-direction: column; position: relative; padding-top: 8px; }}
        .shelf-row.hidden {{ display: none !important; }}
        
        .shelf-products {{ 
          display: flex; 
          flex-direction: row; 
          gap: 3px; 
          padding: 4px 6px; 
          min-height: 90px; 
          overflow-x: auto; 
          align-items: flex-end; 
          justify-content: flex-start; 
        }}
        .sku-item.dimmed {{ opacity: 0.15; filter: grayscale(1); }}
        .sku-item.highlighted {{ transform: scale(1.02); z-index: 20; }}
        
        .shelf-base {{ height: 10px; background: linear-gradient(180deg, #fde047 0%, #ca8a04 100%); border-radius: 2px; position: relative; border-bottom: 2px solid #854d0e; }}
        .shelf-name-tag {{ position: absolute; top: 8px; background: rgba(0,0,0,0.7); color: #fef08a; font-size: 0.50rem; padding: 1px 4px; border-radius: 0 0 3px 3px; font-weight: 800; }}
        
        .sku-group {{ display: flex; flex-direction: column; align-items: center; position: relative; cursor: pointer; flex-shrink: 0; }}
        .sku-images-wrapper {{ display: flex; flex-direction: row; align-items: flex-end; gap: 1px; }}
        .sku-images-wrapper img {{ height: 80px; width: auto; max-width: 50px; object-fit: contain; }}
        
        .sku-fleje {{ background: #ffffff; color: #000; border: 1px solid #64748b; font-size: 0.45rem; display: flex; flex-direction: column; align-items: center; line-height: 1; margin-top: 2px; width: max-content; padding: 1px 2px; }}
        .fleje-ean {{ font-weight: 600; font-family: monospace; }}
        .fleje-caras {{ font-weight: 900; background: #e2e8f0; width: 100%; text-align: center; color: #1e293b; }}
        
        .alerta-bloqueado .sku-images-wrapper img {{ filter: grayscale(100%) opacity(0.4); }}
        .alerta-sinstock .sku-images-wrapper img {{ filter: drop-shadow(0 0 8px #ef4444); }}
        .alerta-stockbajo .sku-images-wrapper img {{ filter: drop-shadow(0 0 6px #f59e0b); }}
        .sku-group.is-top .top-badge::after {{ content: '⭐'; position: absolute; top: -12px; right: -4px; font-size: 1rem; }}
        
        .sku-card {{ border-radius: 4px; padding: 4px; display: flex; flex-direction: column; justify-content: space-between; min-width: 80px; position: relative; cursor: pointer; flex-shrink: 0; }}
        .sku-pos {{ position: absolute; top: 2px; left: 2px; background: #0f172a; color: #fff; font-size: 0.55rem; font-weight: 800; padding: 1px 3px; border-radius: 2px; }}
        .sku-caras-tag {{ position: absolute; top: 2px; right: 2px; background: rgba(255,255,255,0.9); color: #000; font-size: 0.50rem; font-weight: 800; padding: 1px 3px; border-radius: 2px; }}
        .sku-details {{ margin-top: 14px; display: flex; flex-direction: column; gap: 2px; text-align: center; }}
        .sku-brand-text {{ font-size: 0.58rem; font-weight: 800; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .sku-name-text {{ font-size: 0.62rem; font-weight: 700; line-height: 1.1; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
        .sku-bottom-bar {{ margin-top: 3px; border-top: 1px dashed; padding-top: 2px; display: flex; justify-content: space-between; align-items: center; }}
        .sku-ean-code {{ font-size: 0.55rem; font-family: monospace; font-weight: 800; }}
        .sku-cap-val {{ font-size: 0.58rem; font-weight: 800; }}
        .shelf-bottom-rail {{ height: 6px; background: linear-gradient(180deg, #94a3b8 0%, #475569 100%); border-radius: 0 0 2px 2px; margin-top: 2px; }}
        .shelf-info {{ background: rgba(30, 58, 138, 0.8); padding: 3px 6px; font-size: 0.62rem; font-weight: 700; display: flex; justify-content: space-between; border-left: 3px solid #60a5fa; }}
        
        /* MODAL RESPONSIVE */
        .modal-overlay {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.75); display: flex; align-items: center; justify-content: center; z-index: 99999; opacity: 0; pointer-events: none; transition: opacity 0.2s; }}
        .modal-overlay.active {{ opacity: 1; pointer-events: auto; }}
        .modal-content {{ background: #1e293b; color: #fff; padding: 18px; border-radius: 8px; width: 92%; max-width: 400px; max-height: 85vh; overflow-y: auto; position: relative; border: 2px solid #3b82f6; }}
        .modal-close {{ position: absolute; top: 8px; right: 12px; font-size: 1.6rem; cursor: pointer; color: #94a3b8; font-weight: bold; }}
        .m-row {{ border-bottom: 1px solid #334155; padding: 5px 0; display: flex; justify-content: space-between; font-size: 0.80rem; }}
        .m-label {{ font-weight: 700; color: #93c5fd; }}
        .m-val {{ font-weight: 600; text-align: right; max-width: 65%; word-wrap: break-word; }}

        /* AJUSTES PARA PANTALLAS GRANDES */
        @media (min-width: 769px) {{
          .bay-column {{ flex: 0 0 100%; max-width: 100%; }}
          .filter-panel {{ grid-template-columns: repeat(5, 1fr) auto; }}
          .btn-group {{ grid-column: auto; }}
        }}
      </style>
    </head>
    <body>
      <div class="main-container">

        <div id="productModal" class="modal-overlay">
          <div class="modal-content">
            <span class="modal-close">&times;</span>
            <h3 id="m-name" style="margin-top: 0; font-size: 1.0rem; border-bottom: 2px solid #3b82f6; padding-bottom: 6px; line-height: 1.2;">Producto</h3>
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

        <div class="top-panel" style="background: #111c30; border: 1px solid #1e3a8a; border-radius: 6px; padding: 8px 10px; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          <div style="display: flex; align-items: center; gap: 6px;">
              <span style="font-size: 1.1rem;">🏆</span>
              <label style="color: #93c5fd; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; margin: 0;">TOP Ventas:</label>
              <input type="number" id="topNInput" value="5" min="1" max="500" style="background: #ffffff; border: 1.5px solid #3b82f6; border-radius: 4px; padding: 2px 6px; width: 55px; font-weight: bold; color: #0f172a; outline: none; font-size: 0.8rem;">
              <span style="color: #94a3b8; font-size: 0.75rem; font-weight: bold;">SKUs</span>
          </div>
          <div id="topNInfo" style="color: #cbd5e1; font-size: 0.75rem; background: rgba(59,130,246,0.1); padding: 4px 8px; border-radius: 4px; border-left: 3px solid #3b82f6; flex-grow: 1;">
              💡 Calculando...
          </div>
        </div>

        <div class="kpi-container">
          <div class="kpi-card" style="border-bottom: 3px solid #3b82f6;"><span class="kpi-title">Total SKUs</span><span class="kpi-val" id="t-total" style="color: #fff;">0</span></div>
          <div class="kpi-card" style="border-bottom: 3px solid #FFC7CE;"><span class="kpi-title">Bloqueados</span><span class="kpi-val" id="t-bloq" style="color: #FFC7CE;">0</span></div>
          <div class="kpi-card" style="border-bottom: 3px solid #F4B084;"><span class="kpi-title">Sin Stock</span><span class="kpi-val" id="t-sin" style="color: #F4B084;">0</span></div>
          <div class="kpi-card" style="border-bottom: 3px solid #FFFF99;"><span class="kpi-title">Stock Bajo</span><span class="kpi-val" id="t-bajo" style="color: #FFFF99;">0</span></div>
          <div class="kpi-card" style="border-bottom: 3px solid #C6EFCE;"><span class="kpi-title">Stock OK</span><span class="kpi-val" id="t-ok" style="color: #C6EFCE;">0</span></div>
          <div class="kpi-card" style="border-bottom: 3px solid #ef4444;"><span class="kpi-title">Cob. Alta</span><span class="kpi-val" id="t-cob" style="color: #ef4444;">0</span></div>
          <div class="kpi-card" style="border-bottom: 3px solid #fbbf24;"><span class="kpi-title">★ Top</span><span class="kpi-val" id="t-top" style="color: #fbbf24;">0</span></div>
        </div>

        <div class="filter-panel">
          <div class="filter-group"><span class="filter-label">🔍 Buscar</span><input type="text" id="searchInput" class="filter-input" placeholder="Nombre o EAN..."></div>
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

        <div class="aisle-wrapper">
          <button class="nav-btn" id="btnPrev">❮</button>
          <div class="aisle-container" id="aisleContainer">
            {html_cuerpos}
          </div>
          <button class="nav-btn" id="btnNext">❯</button>
        </div>

      </div>

      <script>
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
          document.getElementById('topNInfo').innerHTML = "💡 <b>TOP " + topNSkusSet.size + "</b> concentra el <b style='color:#10b981; font-size:0.9rem;'>" + pct.toFixed(1) + "%</b> de la venta (S/ " + totalVentasFiltered.toLocaleString('en-US', {{minimumFractionDigits:2, maximumFractionDigits:2}}) + ").";

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
                 if(card.classList.contains('sku-card')) card.style.border = "2px solid #FFC000";
             }} else {{
                 card.classList.remove('is-top');
                 if(card.classList.contains('sku-card')) card.style.border = "1px solid #7f7f7f";
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
          applyFilters();
        }});

        const modal = document.getElementById('productModal');
        const closeBtn = document.querySelector('.modal-close');
        document.querySelectorAll('.sku-item').forEach(card => {{
            card.addEventListener('click', (e) => {{
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

        const container = document.getElementById('aisleContainer');
        const btnPrev = document.getElementById('btnPrev');
        const btnNext = document.getElementById('btnNext');
        function updateScrollButtons() {{
            btnPrev.disabled = container.scrollLeft <= 10;
            btnNext.disabled = container.scrollLeft + container.clientWidth >= container.scrollWidth - 10;
        }}
        btnPrev.addEventListener('click', () => {{
            const visibleModule = container.querySelector('.bay-column:not(.hidden)');
            if(visibleModule) container.scrollBy({{ left: -(visibleModule.offsetWidth + 12), behavior: 'smooth' }});
        }});
        btnNext.addEventListener('click', () => {{
            const visibleModule = container.querySelector('.bay-column:not(.hidden)');
            if(visibleModule) container.scrollBy({{ left: (visibleModule.offsetWidth + 12), behavior: 'smooth' }});
        }});
        container.addEventListener('scroll', updateScrollButtons);
        window.addEventListener('resize', updateScrollButtons);
        setTimeout(applyFilters, 100);
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

# --- HEADER RESPONSIVE CON ACCIONES ---
col_head1, col_head2, col_head3, col_head4 = st.columns([3.5, 1.5, 3.5, 1.5])

with col_head1:
    st.markdown("<h2 style='margin: 0; padding: 0; font-size: 1.8rem; color: #fff;'>🏪 Planograma 2.0</h2>", unsafe_allow_html=True)
    
with col_head2:
    if st.button("🔄 Actualizar", use_container_width=True):
        st.cache_data.clear()
        st.session_state.ultimo_acceso = time.time()
        st.rerun()

with col_head3:
    header_time_placeholder = st.empty()

with col_head4:
    if st.button("🚪 Salir", use_container_width=True, help="Cerrar sesión segura"):
        st.session_state.autenticado = False
        st.session_state.ultimo_acceso = 0
        st.rerun()

st.markdown("<div style='border-bottom: 2px solid #1e3a8a; padding-bottom: 3px; margin-bottom: 10px;'><span style='color: #93c5fd; font-size: 0.82rem;'>Análisis interactivo de pasillos y rentabilidad de tienda</span></div>", unsafe_allow_html=True)

with st.spinner("Sincronizando bases de datos..."):
    df_nube, df_aux_nube, df_jer_nube, df_fotos_nube, info_hora, error_nube = cargar_datos_nube(URL_NUBE, URL_JERARQUIA, URL_FOTOS)

header_time_placeholder.markdown(f"""
    <div style="text-align: right; margin-top: 2px;">
        <div style="font-size: 0.85rem; color: #cbd5e1;">Desarrollado por <b>Alfredo HM</b></div>
        <div style="font-size: 0.70rem; color: #64748b;">Actualizado: {info_hora if info_hora else 'No disponible'}</div>
    </div>
""", unsafe_allow_html=True)

if df_nube is not None:
    df_raw = df_nube
    df_aux_raw = df_aux_nube
    df_jer_raw = df_jer_nube
    df_fotos_raw = df_fotos_nube
else:
    st.warning("⚠️ No se pudo conectar a la Nube. Sube el archivo MATRIZ manualmente.")
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
            st.error(f"Error al leer el archivo: {e}")

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
        # VISTA PREDETERMINADA: 📦 Bloques (Colores) -> index=1
        modo_vista = st.radio(
            "Modo de Vista:", 
            ["🖼️ Realograma (Imágenes)", "📦 Bloques (Colores)"], 
            index=1, 
            horizontal=True, 
            label_visibility="collapsed"
        )
        es_realograma = ("Realograma" in modo_vista)
            
        html_pasillo = generar_html_pasillo_interactivo(df_base, es_realograma=es_realograma)
        # Altura adaptable con scroll encapsulado dentro del iframe
        components.html(html_pasillo, height=1300, scrolling=True)
            
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
                    <span class="fin-kpi-title">Ventas Totales</span>
                    <span class="fin-kpi-val">S/ {ventas_globales:,.2f}</span>
                </div>
                <div class="fin-kpi-card green-theme">
                    <span class="fin-kpi-title">Margen Total</span>
                    <span class="fin-kpi-val">S/ {margen_global:,.2f}</span>
                </div>
                <div class="fin-kpi-card purple-theme">
                    <span class="fin-kpi-title">Margen Global (%)</span>
                    <span class="fin-kpi-val">{margen_pct_global*100:.1f}%</span>
                </div>
                <div class="fin-kpi-card">
                    <span class="fin-kpi-title">SKUs Únicos</span>
                    <span class="fin-kpi-val">{total_skus_activos}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        cats_disponibles = sorted([c for c in df_unicos['Categoría'].dropna().unique() if c not in ['S/C', 'nan', '']])
        cat_seleccionada = st.selectbox("🎯 Filtrar Dashboard por Categoría:", ["Todas las Categorías"] + cats_disponibles)
        
        df_dash_base = df_base.copy()
        if cat_seleccionada != "Todas las Categorías":
            df_dash_base = df_dash_base[df_dash_base['Categoría'] == cat_seleccionada]
            
        df_dash_unicos = df_dash_base.drop_duplicates(subset=['COD REAL']).copy()

        col_graf_izq, col_graf_der = st.columns([6, 4])
        
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
                if cat_nombre and len(cat_nombre) > 16:
                    cat_nombre = cat_nombre[:14] + ".."
                return f"C{int(c_num)}<br><sub>{cat_nombre}</sub>" if cat_nombre else f"C{int(c_num)}"

            ventas_cuerpo['Cuerpo_Label'] = ventas_cuerpo['Cuerpo_Ord'].apply(crear_etiqueta_eje)
            ventas_cuerpo['Margen_Pct'] = ventas_cuerpo.apply(
                lambda row: row['Margen_Total'] / row['Venta_Total'] if row['Venta_Total'] > 0 else 0, 
                axis=1
            )
            
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
                    name="Ventas (S/)",
                    text=ventas_cuerpo['Venta_Total'].apply(lambda x: f"S/ {x:,.0f}"),
                    textposition='auto',
                    textfont=dict(color='#ffffff', size=10, weight='bold'),
                    marker=dict(color='rgba(59, 130, 246, 0.75)', line=dict(color='#3b82f6', width=1.5)),
                    hovertemplate="<b>%{x}</b><br>Ventas: S/ %{y:,.2f}<br>SKUs: %{customdata}<extra></extra>",
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
                    textfont=dict(color='#10b981', size=11, weight='bold'),
                    marker=dict(color="#10b981", size=7, symbol='circle'),
                    line=dict(color="#10b981", width=2.5),
                    hovertemplate="<b>%{x}</b><br>Margen: %{text}<extra></extra>"
                ), secondary_y=True
            )

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color='#cbd5e1', size=10)),
                margin=dict(t=10, b=20, l=10, r=10),
                xaxis=dict(showgrid=False, color='#cbd5e1', tickfont=dict(size=10, weight='bold')),
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
                textinfo='percent',
                textposition='inside',
                insidetextorientation='horizontal',
                textfont=dict(size=11, color='#ffffff', family='Arial Black'),
                marker=dict(colors=['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#14b8a6'], 
                            line=dict(color='#0f172a', width=1.5))
            )])
            
            fig_pie.update_layout(
                showlegend=True,
                legend=dict(font=dict(color='#cbd5e1', size=9), orientation='v'),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=5, b=5, l=5, r=5),
                annotations=[dict(text=f'<b>S/ {ventas_dash_total/1000:,.1f}K</b>', x=0.5, y=0.5, font_size=15, showarrow=False, font_color='#ffffff')]
            )
            fig_pie.update_traces(hovertemplate="<b>%{label}</b><br>Ventas: S/ %{value:,.2f}<br>Participación: %{percent}<extra></extra>")
            
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        st.markdown("### ⚖️ Fair Share: Espacio vs Rendimiento")
        
        col_fs_dim, col_fs_met = st.columns([1, 1])
        with col_fs_dim:
            dim_fs = st.selectbox(
                "Segmentar por:", 
                ["Categoría", "Sección", "Departamento", "Grupo de artículo", "Marca"],
                key="fs_dim_select"
            )
        with col_fs_met:
            metrica_espacio = st.radio(
                "Métrica Espacio:",
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
                x=df_fs[dim_fs], y=df_fs['Pct_Espacio'],
                name=f"% Espacio",
                text=df_fs['Pct_Espacio'].apply(lambda x: f"{x*100:.1f}%"),
                textposition='auto',
                marker=dict(color='rgba(59, 130, 246, 0.85)')
            ))
            fig_fs.add_trace(go.Bar(
                x=df_fs[dim_fs], y=df_fs['Pct_Ventas'],
                name="% Ventas",
                text=df_fs['Pct_Ventas'].apply(lambda x: f"{x*100:.1f}%"),
                textposition='auto',
                marker=dict(color='rgba(16, 185, 129, 0.85)')
            ))
            fig_fs.add_trace(go.Bar(
                x=df_fs[dim_fs], y=df_fs['Pct_Margen'],
                name="% Margen",
                text=df_fs['Pct_Margen'].apply(lambda x: f"{x*100:.1f}%"),
                textposition='auto',
                marker=dict(color='rgba(245, 158, 11, 0.85)')
            ))
            
            fig_fs.update_layout(
                barmode='group',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color='#cbd5e1', size=10)),
                margin=dict(t=10, b=30, l=10, r=10),
                xaxis=dict(showgrid=False, color='#cbd5e1', tickfont=dict(size=10, weight='bold')),
                yaxis=dict(title="Participación (%)", showgrid=True, gridcolor='rgba(255,255,255,0.08)', color='#cbd5e1', tickformat=".0%")
            )
            fig_fs.update_xaxes(fixedrange=True)
            fig_fs.update_yaxes(fixedrange=True)
            st.plotly_chart(fig_fs, use_container_width=True, config={'displayModeBar': False})
            
            subdimensionados = df_fs[df_fs['Brecha_Share'] > 0.03]
            sobredimensionados = df_fs[df_fs['Brecha_Share'] < -0.03]
            
            if not subdimensionados.empty:
                top_sub = subdimensionados.iloc[0]
                st.success(f"🚀 **Oportunidad:** `{top_sub[dim_fs]}` genera el **{top_sub['Pct_Ventas']*100:.1f}%** de venta y solo ocupa **{top_sub['Pct_Espacio']*100:.1f}%** de espacio.")
            if not sobredimensionados.empty:
                top_sobre = sobredimensionados.sort_values(by='Brecha_Share', ascending=True).iloc[0]
                st.warning(f"⚠️ **Sobreasignación:** `{top_sobre[dim_fs]}` ocupa el **{top_sobre['Pct_Espacio']*100:.1f}%** de espacio pero solo aporta **{top_sobre['Pct_Ventas']*100:.1f}%** de venta.")
            
        st.markdown("---")
        st.markdown("### 📋 Reporte Detallado")
        
        filtro_reporte = st.selectbox("Filtrar Tabla:", [
            "Todos los SKUs",
            "Bloqueados (Estado B)",
            "Sin Stock (Stock = 0)",
            "Stock Bajo (Stock 1 a 5)",
            "Cobertura Alta (≥ 30)"
        ], label_visibility="collapsed")
        
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
            
        st.download_button(
            label="📥 Descargar a Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name="reporte_planograma_skus_unicos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.dataframe(df_rep[cols_to_show], use_container_width=True, hide_index=True)
