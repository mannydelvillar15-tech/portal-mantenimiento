import re
from datetime import datetime
import pandas as pd
import streamlit as st

import database as db
import logic
import charts
import unicodedata

st.set_page_config(
    page_title="Dashboard de Mantenimiento",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inicializar base de datos al arrancar
db.init_db()

# Estilos CSS ligeros para tarjetas KPI y estética limpia
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .kpi-box {
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Estado de sesión
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None


# ==========================================
# PANTALLA DE AUTENTICACIÓN (LOGIN / REGISTRO)
# ==========================================
def render_auth_screen():
    col_izq, col_der = st.columns([1.1, 1], gap="large")

    with col_izq:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    padding: 48px 36px; border-radius: 18px; color: white; height: 100%;">
            <div style="background:#4f46e5; width:60px; height:60px; border-radius:14px;
                        display:flex; align-items:center; justify-content:center; font-size:30px; margin-bottom:24px;">
                ⚙️
            </div>
            <h1 style="font-size: 2.4rem; font-weight: 900; margin-bottom: 12px; line-height: 1.1;">
                Portal de <span style="color: #818cf8;">Mantenimiento</span>
            </h1>
            <p style="color: #cbd5e1; font-size: 1.05rem; line-height: 1.6;">
                Gestión inteligente de activos, control de averías y planificación preventiva centralizada en una sola plataforma sincronizada.
            </p>
            <hr style="border-color: #334155; margin: 28px 0;">
            <p style="color: #94a3b8; font-size: 0.85rem;">
                💡 Pista inicial — Usuario: <b>admin</b> | Contraseña: <b>123</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_der:
        def generar_usuario_auto(nombre_str):
            limpio = " ".join(nombre_str.strip().split())
            partes = limpio.split(" ")
            if len(partes) < 2:
                return ""
            sin_tildes = "".join(
                c for c in unicodedata.normalize("NFD", f"{partes[0][0].upper()}.{partes[1].capitalize()}")
                if unicodedata.category(c) != "Mn"
            )
            return sin_tildes

        tab_login, tab_reg = st.tabs(["🔐 Iniciar Sesión", "📝 Crear Cuenta"])
        cfg = db.get_config()
        departamentos = cfg.get("departamentos", db.DEFAULT_DEPARTAMENTOS)

        with tab_login:
            st.subheader("Bienvenido de nuevo")
            st.caption("Ingresa tus credenciales para continuar.")
            with st.form("form_login"):
                u_login = st.text_input("Usuario", placeholder="Ej. J.Perez")
                p_login = st.text_input("Contraseña", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Iniciar Sesión", type="primary", use_container_width=True)
                if submitted:
                    if not u_login or not p_login:
                        st.error("Ingresa usuario y contraseña.")
                    else:
                        user_match = db.authenticate_user(u_login.strip(), p_login.strip())
                        if user_match:
                            db.log_login(user_match)
                            st.session_state.current_user = user_match
                            st.session_state.authenticated = True
                            st.rerun()
                        else:
                            st.error("Usuario o contraseña incorrectos.")

        with tab_reg:
            st.subheader("Crear una cuenta")
            st.caption("Regístrate para acceder al panel operativo.")

            if st.session_state.pop("limpiar_registro_user", False):
                st.session_state["reg_u_nombre"] = ""
                st.session_state["reg_u_depto"] = ""
                st.session_state["reg_u_user"] = ""
                st.session_state["reg_u_pin"] = ""

            if st.session_state.get("reg_user_msg"):
                st.success(st.session_state.pop("reg_user_msg"))

            r_nombre = st.text_input(
                "Nombre Completo *",
                placeholder="Ej. Juan Pérez",
                key="reg_u_nombre"
            )
            r_depto = st.selectbox(
                "Departamento *",
                [""] + departamentos,
                format_func=lambda x: "Seleccione departamento..." if x == "" else x,
                key="reg_u_depto"
            )

            usuario_generado = generar_usuario_auto(r_nombre)
            st.session_state["reg_u_user"] = usuario_generado

            st.text_input(
                "Usuario (Generado automáticamente)",
                disabled=True,
                placeholder="Se generará como N.Apellido (ej. J.Perez)",
                key="reg_u_user"
            )
            r_pin = st.text_input(
                "Contraseña (PIN de 4 dígitos) *",
                type="password",
                max_chars=4,
                placeholder="••••",
                key="reg_u_pin"
            )
            st.caption("• Mínimo y máximo de 4 dígitos numéricos (PIN).")

            if st.button("Registrar Usuario", type="primary", use_container_width=True):
                if len(r_nombre.strip().split()) < 2 or not usuario_generado:
                    st.error("Ingresa al menos un Nombre y un Apellido (ej. Juan Pérez) para generar el usuario.")
                elif not r_depto:
                    st.error("Selecciona un departamento.")
                elif len(r_pin) != 4 or not r_pin.isdigit():
                    st.error("El PIN debe contener exactamente 4 dígitos numéricos.")
                else:
                    ok, msg = db.register_user(r_nombre.strip(), r_depto, usuario_generado, r_pin)
                    if ok:
                        st.session_state["limpiar_registro_user"] = True
                        st.session_state["reg_user_msg"] = f"¡Usuario '{usuario_generado}' registrado exitosamente! Ahora puedes iniciar sesión."
                        st.rerun()
                    else:
                        st.error(msg)

def _cerrar_modal_activos():
    st.session_state["modal_activos_abierto"] = False
    st.session_state["confirm_delete"] = None

@st.dialog("➕ Gestión de Registros Maestros", width="large", on_dismiss=_cerrar_modal_activos)
def modal_gestion_activos():
    cfg = db.get_config()
    base_areas = list(cfg["equiposPorArea"].keys())

    # Selector de sección persistente en session_state (no se resetea al recargar)
    seccion = st.radio(
        "Sección",
        ["🔧 Equipo", "🚪 Sala", "📍 Área", "🏢 Departamento"],
        horizontal=True,
        label_visibility="collapsed",
        key="tab_modal_activos"
    )
    st.divider()

    def render_confirmacion_borrado(tipo_key, etiqueta, on_confirm_fn):
        if st.session_state.get("confirm_delete") == tipo_key:
            st.warning(f"⚠️ ¿Estás seguro de que deseas eliminar **{etiqueta}**? Esta acción no se puede deshacer.")
            c_si, c_no = st.columns(2)
            if c_si.button("✅ Sí, eliminar", type="primary", key=f"yes_{tipo_key}", use_container_width=True):
                on_confirm_fn()
                st.session_state["confirm_delete"] = None
                st.rerun()
            if c_no.button("❌ Cancelar", key=f"no_{tipo_key}", use_container_width=True):
                st.session_state["confirm_delete"] = None
                st.rerun()

    if seccion == "🔧 Equipo":
        c_sel1, c_sel2 = st.columns(2)
        area_sel = c_sel1.selectbox("Área a la que pertenece", base_areas, key="add_eq_area")
        salas_area_sel = cfg["salasPorArea"].get(area_sel, [])
        sala_eq_sel = c_sel2.selectbox(
            "Sala / Ubicación",
            [""] + salas_area_sel,
            format_func=lambda x: "Todas / Sin sala específica" if x == "" else x,
            key="add_eq_sala"
        )

        c1, c2 = st.columns(2)
        eq_name = c1.text_input("Nombre del Equipo / Activo", placeholder="Ej. Empacadora 3000")
        eq_code = c2.text_input("Código del Equipo", placeholder="Ej. EMP-001 (Opcional)")
        if st.button("Agregar Equipo", type="primary", use_container_width=True):
            if not eq_name.strip():
                st.error("Completa el nombre del equipo.")
            elif any(e["nombre"].lower() == eq_name.strip().lower() and e.get("sala", "") == sala_eq_sel for e in cfg["equiposPorArea"].get(area_sel, [])):
                st.error("El equipo ya existe en esta sala.")
            else:
                cfg["equiposPorArea"][area_sel].append({
                    "nombre": eq_name.strip(),
                    "codigo": eq_code.strip(),
                    "sala": sala_eq_sel
                })
                db.save_config(cfg)
                st.success("Equipo agregado correctamente.")
                st.rerun()

        st.markdown(f"**Equipos Registrados en {area_sel}:**")
        for eq in cfg["equiposPorArea"].get(area_sel, []):
            del_id = f"eq_{area_sel}_{eq['nombre']}_{eq.get('sala', '')}"
            ca, cb = st.columns([5, 1])
            sala_tag = f" — 📍 *{eq['sala']}*" if eq.get("sala") else ""
            ca.write(f"• **{eq['nombre']}** `{eq.get('codigo', '')}`{sala_tag}")
            if cb.button("🗑️", key=f"btn_{del_id}"):
                st.session_state["confirm_delete"] = del_id
                st.rerun()

            def _borrar_eq(a=area_sel, target=eq):
                cfg["equiposPorArea"][a] = [e for e in cfg["equiposPorArea"][a] if e != target]
                db.save_config(cfg)

            render_confirmacion_borrado(del_id, f"el equipo '{eq['nombre']}'", _borrar_eq)

    elif seccion == "🚪 Sala":
        area_sala = st.selectbox("Área a la que pertenece", base_areas, key="add_sala_area")
        sala_name = st.text_input("Nombre de la Sala / Ubicación", placeholder="Ej. Sala de Mezclado 1")
        if st.button("Agregar Sala", type="primary", use_container_width=True):
            if not sala_name.strip():
                st.error("Completa el nombre de la sala.")
            elif sala_name.strip() in cfg["salasPorArea"].get(area_sala, []):
                st.error("La sala ya existe en esta área.")
            else:
                cfg["salasPorArea"].setdefault(area_sala, []).append(sala_name.strip())
                db.save_config(cfg)
                st.success("Sala agregada correctamente.")
                st.rerun()

        st.markdown(f"**Salas Registradas en {area_sala}:**")
        for s in cfg["salasPorArea"].get(area_sala, []):
            del_id = f"sala_{area_sala}_{s}"
            ca, cb = st.columns([5, 1])
            ca.write(f"• {s}")
            if cb.button("🗑️", key=f"btn_{del_id}"):
                st.session_state["confirm_delete"] = del_id
                st.rerun()

            def _borrar_sala(a=area_sala, target=s):
                cfg["salasPorArea"][a] = [x for x in cfg["salasPorArea"][a] if x != target]
                db.save_config(cfg)

            render_confirmacion_borrado(del_id, f"la sala '{s}'", _borrar_sala)

    elif seccion == "📍 Área":
        area_new = st.text_input("Nombre de la Nueva Área", placeholder="Ej. Inyectables")
        if st.button("Agregar Área", type="primary", use_container_width=True):
            if not area_new.strip():
                st.error("Ingresa el nombre del área.")
            elif area_new.strip() in cfg["equiposPorArea"]:
                st.error("El área ya existe.")
            else:
                cfg["equiposPorArea"][area_new.strip()] = []
                cfg["salasPorArea"][area_new.strip()] = []
                db.save_config(cfg)
                db.add_area_to_matriz(area_new.strip())
                st.success("Área agregada correctamente.")
                st.rerun()

        st.markdown("**Áreas Registradas:**")
        for a in base_areas:
            del_id = f"area_{a}"
            ca, cb = st.columns([5, 1])
            ca.write(f"• {a}")
            if cb.button("🗑️", key=f"btn_{del_id}"):
                st.session_state["confirm_delete"] = del_id
                st.rerun()

            def _borrar_area(target=a):
                cfg["equiposPorArea"].pop(target, None)
                cfg["salasPorArea"].pop(target, None)
                db.save_config(cfg)

            render_confirmacion_borrado(del_id, f"el área '{a}' y todos sus equipos/salas", _borrar_area)

    elif seccion == "🏢 Departamento":
        dept_new = st.text_input("Nombre del Departamento", placeholder="Ej. Logística Inversa")
        if st.button("Agregar Departamento", type="primary", use_container_width=True):
            if not dept_new.strip():
                st.error("Ingresa el nombre del departamento.")
            elif dept_new.strip() in cfg["departamentos"]:
                st.error("El departamento ya existe.")
            else:
                cfg["departamentos"].append(dept_new.strip())
                db.save_config(cfg)
                st.success("Departamento agregado correctamente.")
                st.rerun()

        st.markdown("**Departamentos Registrados:**")
        for d in cfg["departamentos"]:
            del_id = f"dept_{d}"
            ca, cb = st.columns([5, 1])
            ca.write(f"• {d}")
            if cb.button("🗑️", key=f"btn_{del_id}"):
                st.session_state["confirm_delete"] = del_id
                st.rerun()

            def _borrar_dept(target=d):
                cfg["departamentos"] = [x for x in cfg["departamentos"] if x != target]
                db.save_config(cfg)

            render_confirmacion_borrado(del_id, f"el departamento '{d}'", _borrar_dept)

@st.dialog("📜 Historial de Accesos (Auditoría)", width="large")
def modal_historial_accesos():
    conn, db_type = db.get_connection()
    logs = pd.DataFrame()
    try:
        if db_type == "postgres":
            tablas_df = pd.read_sql_query(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'", conn
            )
            tablas = tablas_df["table_name"].tolist()
        else:
            tablas_df = pd.read_sql_query(
                "SELECT name FROM sqlite_master WHERE type='table'", conn
            )
            tablas = tablas_df["name"].tolist()

        tabla_logs = next(
            (t for t in tablas if any(k in t.lower() for k in ["acceso", "access", "login", "log"])),
            None
        )
        if tabla_logs:
            logs = pd.read_sql_query(f"SELECT * FROM {tabla_logs} ORDER BY id DESC LIMIT 100", conn)
    except Exception as e:
        st.error(f"Error al consultar historial: {e}")
    finally:
        conn.close()

    if logs.empty:
        st.info("No hay registros de acceso todavía.")
    else:
        st.dataframe(logs, use_container_width=True, hide_index=True)

@st.dialog("ℹ️ Detalle y Fórmula del Indicador (KPI)", width="large")
def modal_info_kpi(kpi_id):
    details = {
        "disponibilidad": (
            "Disponibilidad de Equipos",
            "Porcentaje de tiempo que los equipos estuvieron en condiciones de operar respecto al tiempo total programado.",
            "((Horas Totales Prog. - Horas de Parada) / Horas Totales Prog.) × 100",
            None
        ),
        "mtbf": (
            "MTBF (Mean Time Between Failures)",
            "Tiempo Medio Entre Fallas. Mide la confiabilidad de los equipos. Incluye tanto el tiempo de operación como el tiempo de reparación anterior.",
            "Horas Totales Programadas / Número Total de Averías",
            "[ Falla 1 ] ──► [ Reparación (MTTR) ] ──────► [ Tiempo Operación (MTTF) ] ──► [ Falla 2 ]\n|<────────────────────────── MTBF (Ciclo Completo) ──────────────────────────>|"
        ),
        "mttr": (
            "MTTR (Mean Time To Repair)",
            "Tiempo Medio de Reparación. Mide la mantenibilidad y eficiencia del equipo técnico desde que ocurre la avería hasta que se restaura.",
            "Tiempo Total de Paradas (Horas) / Número Total de Averías",
            "[ Operación ] ──► [ 🚨 Avería ] ══► [ 🔧 Intervención Técnica (MTTR) ] ══► [ ✅ Restaurado ]"
        ),
        "pmp": (
            "Cumplimiento Preventivo (PMP)",
            "Porcentaje de intervenciones de mantenimiento preventivo ejecutadas con éxito respecto a las planificadas en el periodo.",
            "(Preventivos Realizados / Preventivos Programados) × 100",
            None
        ),
        "mttf": (
            "MTTF (Mean Time To Failure)",
            "Tiempo Medio Hasta la Falla. Excluye el tiempo detenido y mide estrictamente el tiempo continuo de funcionamiento hasta la avería.",
            "(Horas Totales Prog. - Horas de Parada) / Número Total de Averías",
            "[ Arranque ] ══════════════════► [ MTTF (Tiempo Neto Operativo) ] ══════════════════► [ ❌ Falla ]"
        ),
        "backlog": (
            "Backlog (Preventivos Pendientes)",
            "Órdenes de Trabajo preventivas programadas que aún no se han completado. Representa el trabajo atrasado acumulado.",
            "Preventivos Programados - Preventivos Realizados",
            None
        )
    }
    title, desc, formula, graphic = details[kpi_id]
    st.subheader(title)
    st.write(desc)
    st.info(f"**Fórmula de Cálculo:**\n\n`{formula}`")
    if graphic:
        st.caption("Esquema Gráfico Explicativo:")
        st.code(graphic, language="text")


@st.dialog("📊 Centro de Exportación Nativo (XLSX + Gráficos)", width="large")
def modal_exportar_excel():
    matriz = db.get_matriz_solicitudes()
    cfg = db.get_config()
    base_areas = list(cfg["equiposPorArea"].keys())
    anios = sorted(list(matriz.keys()))
    sel_year = st.selectbox("Año de Exportación Base", anios, index=len(anios)-1)

    t_activos = db.get_tickets("Abierto")
    t_resueltos = db.get_tickets("Cerrado")
    fallas = db.get_historial_fallas()

    st.markdown("### 1. Reportes de Datos Principales")
    c1, c2 = st.columns(2)

    with c1:
        # 1. Activas
        h1 = ['Código Ticket', 'Fecha Ingreso', 'Hora Ingreso', 'Área', 'Sala', 'Equipo', 'Cód. Equipo', 'Departamento', 'Solicitante', 'Descripción']
        r1 = [[t['codigo'], t['fecha_visual'], t['hora_visual'], t['area'], t['sala'], t['equipo'], t['codigo_equipo'], t['origen'], t['solicitante'], t['descripcion']] for t in t_activos]
        st.download_button("📥 1. Solicitudes Activas (.xlsx)", charts.build_excel_buffer(h1, r1, "Activas"), "Solicitudes_Activas.xlsx", use_container_width=True)

        # 3. Matriz General
        h3 = ['Año', 'Mes', 'Área', 'Creadas', 'Resueltas', 'Pendientes']
        r3 = []
        for a in anios:
            for m in logic.NOMBRES_MESES:
                for item in matriz.get(a, {}).get(m, []):
                    cre = item.get('creadas', 0)
                    res = item.get('resueltas', 0)
                    r3.append([a, m, item['area'], cre, res, max(0, cre - res)])
        st.download_button("📥 3. Matriz General Solicitudes (.xlsx)", charts.build_excel_buffer(h3, r3, "Matriz_General"), "Matriz_Solicitudes_General.xlsx", use_container_width=True)

        # 5. Matriz PMP
        h5 = [f"Área \\ Mes ({sel_year})"] + logic.NOMBRES_MESES
        r5 = []
        for area in base_areas:
            row = [area]
            for m in logic.NOMBRES_MESES:
                d = next((x for x in matriz.get(sel_year, {}).get(m, []) if x['area'] == area), {})
                prog, real = d.get('prevProgramados', 0), d.get('prevRealizados', 0)
                row.append(f"{round((real/prog)*100)}% ({real}/{prog})" if prog > 0 else "N/A")
            r5.append(row)
        st.download_button(f"📥 5. Matriz Cumplimiento PMP {sel_year} (.xlsx)", charts.build_excel_buffer(h5, r5, "Matriz_PMP"), f"Matriz_Cumplimiento_PMP_{sel_year}.xlsx", use_container_width=True)

    with c2:
        # 2. Resueltas
        h2 = ['Código Ticket', 'Mes', 'Año', 'Área', 'Sala', 'Equipo', 'Cód. Equipo', 'Tipo Tarea', 'Tipo Falla', 'Tiempo Total', 'Técnico']
        r2 = [[t['codigo'], t['mes'], t['anio'], t['area'], t['sala'], t['equipo'], t['codigo_equipo'], t['tipo_tarea'], t['tipo_falla'], t['tiempo_total'], t['tecnico']] for t in t_resueltos]
        st.download_button("📥 2. Solicitudes Resueltas (.xlsx)", charts.build_excel_buffer(h2, r2, "Resueltas"), "Solicitudes_Resueltas.xlsx", use_container_width=True)

        # 4. Averías
        h4 = ['Mes', 'Año', 'Área', 'Sala', 'Equipo', 'Cód. Equipo', 'Detalle / Falla', 'Cant. Averías', 'Tiempo Perdido (hrs)', 'Impacto']
        r4 = [[f['mes'], f['anio'], f['area'], f['sala'], f['equipo'], f['codigo_equipo'], f['detalle'], f['averias'], f['tiempo'], f['impacto']] for f in fallas]
        st.download_button("📥 4. Registro Detallado de Averías (.xlsx)", charts.build_excel_buffer(h4, r4, "Averias"), "Registro_Detallado_Averias.xlsx", use_container_width=True)

    st.markdown("### 2. Reportes Visuales (Tabla + Gráfico Nativo de Excel)")
    g1, g2 = st.columns(2)
    with g1:
        # 6. Tendencia Mensual
        hg1 = ['Mes', 'Creadas', 'Resueltas', 'Pendientes']
        rg1 = []
        for m in logic.NOMBRES_MESES:
            items = matriz.get(sel_year, {}).get(m, [])
            cre = sum(x.get('creadas', 0) for x in items)
            res = sum(x.get('resueltas', 0) for x in items)
            rg1.append([m, cre, res, max(0, cre - res)])
        st.download_button(f"📊 6. Gráfico Tendencia Mensual {sel_year}", charts.build_excel_buffer(hg1, rg1, "Tendencia", "bar", f"Tendencia Mensual {sel_year}"), f"Grafico_Tendencia_Mensual_{sel_year}.xlsx", use_container_width=True)

        # 8. Tendencia Global PMP
        hg3 = ['Mes', 'Prev. Prog.', 'Prev. Real.', 'Cumplimiento (%)']
        rg3 = []
        for m in logic.NOMBRES_MESES:
            items = matriz.get(sel_year, {}).get(m, [])
            prog = sum(x.get('prevProgramados', 0) for x in items)
            real = sum(x.get('prevRealizados', 0) for x in items)
            rg3.append([m, prog, real, round((real/prog)*100) if prog > 0 else 0])
        st.download_button(f"📊 8. Gráfico Tendencia Global PMP {sel_year}", charts.build_excel_buffer(hg3, rg3, "PMP_Global", "bar", f"Cumplimiento PMP {sel_year}"), f"Grafico_Tendencia_Global_PMP_{sel_year}.xlsx", use_container_width=True)

    with g2:
        # 7. Distribución por Área
        hg2 = ['Área', 'Creadas', 'Resueltas', 'Pendientes']
        rg2 = []
        for area in base_areas:
            cre = sum(next((x.get('creadas', 0) for x in matriz.get(sel_year, {}).get(m, []) if x['area'] == area), 0) for m in logic.NOMBRES_MESES)
            res = sum(next((x.get('resueltas', 0) for x in matriz.get(sel_year, {}).get(m, []) if x['area'] == area), 0) for m in logic.NOMBRES_MESES)
            rg2.append([area, cre, res, max(0, cre - res)])
        st.download_button(f"📊 7. Gráfico Distribución por Área {sel_year}", charts.build_excel_buffer(hg2, rg2, "Por_Area", "bar", f"Distribución por Área {sel_year}"), f"Grafico_Distribucion_Area_{sel_year}.xlsx", use_container_width=True)

        # 9. Líneas PMP por Área
        hg4 = ['Mes'] + base_areas
        rg4 = []
        for m in logic.NOMBRES_MESES:
            row = [m]
            for area in base_areas:
                d = next((x for x in matriz.get(sel_year, {}).get(m, []) if x['area'] == area), {})
                prog, real = d.get('prevProgramados', 0), d.get('prevRealizados', 0)
                row.append(round((real/prog)*100) if prog > 0 else 0)
            rg4.append(row)
        st.download_button(f"📈 9. Gráfica Líneas Evolución PMP {sel_year}", charts.build_excel_buffer(hg4, rg4, "Lineas_PMP", "line", f"Evolución PMP por Área {sel_year}"), f"Grafica_Lineas_PMP_{sel_year}.xlsx", use_container_width=True)


# ==========================================
# DASHBOARD PRINCIPAL
# ==========================================
def render_dashboard():
    user = st.session_state.current_user
    is_admin = user["username"] == "admin"
    can_close_tickets = is_admin or user.get("departamento") == "Mantenimiento"

    cfg = db.get_config()
    base_areas = list(cfg["equiposPorArea"].keys())
    departamentos = cfg["departamentos"]

    # --- HEADER PRINCIPAL ---
    h_left, h_right = st.columns([2, 2.2])
    with h_left:
        st.title("🔧 Dashboard de Mantenimiento")
        st.caption(f"📈 Resumen de KPIs y Rendimiento de Equipos  |  👤 **{user['name']}** (`@{user['username']}` • {user['departamento']})")

    with h_right:
        b1, b2, b3, b4 = st.columns(4)
        if b1.button("➕ Activo/Área", disabled=not is_admin, use_container_width=True, help="Solo administradores"):
            st.session_state["modal_activos_abierto"] = True

        if st.session_state.get("modal_activos_abierto", False):
            modal_gestion_activos()
        if b2.button("📜 Accesos", use_container_width=True):
            modal_historial_accesos()
        if b3.button("📊 Excel", disabled=not is_admin, use_container_width=True, help="Solo administradores"):
            modal_exportar_excel()
        if b4.button("🚪 Salir", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()

    st.divider()

    # --- PESTAÑAS ---
    tabs = st.tabs([
        "📝 Registro de Solicitudes",
        "📋 Visor de Solicitudes",
        "🔍 Análisis de Fallas",
        "🗓️ Plan de Mantenimiento",
        "📊 Visor de Resultados",
        "✅ Visor Cumplimiento Prev."
    ])

    # ==========================================================
    # PESTAÑA 1: REGISTRO DE SOLICITUDES (CREAR + CERRAR + ACTIVAS)
    # ==========================================================
    with tabs[0]:
        st.subheader("🟠 Crear Nueva Solicitud (Ticket)")
        now = datetime.now()
        anio_actual = str(now.year)
        mes_actual = logic.NOMBRES_MESES[now.month - 1]
        fecha_visual = now.strftime("%d/%m/%Y")
        hora_visual = now.strftime("%I:%M %p").lstrip("0")
        next_code = db.get_next_ticket_code()

        # Limpiar campos del registro de ticket antes de dibujar los widgets
        if st.session_state.pop("limpiar_registro_pendiente", False):
            st.session_state["reg_area"] = ""
            st.session_state["reg_sala"] = ""
            st.session_state["reg_equipo"] = ""
            st.session_state["reg_cod_eq"] = ""
            st.session_state["reg_cod_emp"] = ""
            st.session_state["reg_solicitante"] = ""
            st.session_state["reg_origen"] = ""
            st.session_state["reg_tipo_tarea"] = ""
            st.session_state["reg_desc"] = ""

        if st.session_state.get("registro_ticket_msg"):
            st.success(st.session_state.pop("registro_ticket_msg"))

        # Selectores dinámicos fuera del form para reactividad inmediata Área -> Sala/Equipo -> Código
        c_top1, c_top2, c_top3 = st.columns(3)
        c_top1.text_input("Código Ticket (Auto)", value=next_code, disabled=True)
        c_top2.text_input("Fecha de Ingreso", value=fecha_visual, disabled=True)
        c_top3.text_input("Hora de Ingreso", value=hora_visual, disabled=True)

        c_loc1, c_loc2, c_loc3, c_loc4 = st.columns(4)
        sel_area = c_loc1.selectbox("Área *", [""] + base_areas, format_func=lambda x: "Seleccione..." if x == "" else x, key="reg_area")
        salas_disp = cfg["salasPorArea"].get(sel_area, []) if sel_area else []
        sel_sala = c_loc2.selectbox("Sala / Ubicación *", [""] + salas_disp, disabled=not bool(sel_area), format_func=lambda x: "Seleccione..." if x == "" else x, key="reg_sala")

        # Filtrar equipos únicamente de la sala seleccionada (o sin sala asignada)
        equipos_area = cfg["equiposPorArea"].get(sel_area, []) if sel_area else []
        equipos_disp = [
            e for e in equipos_area
            if sel_sala and (e.get("sala") == sel_sala or not e.get("sala"))
        ]
        nombres_eq = [e["nombre"] for e in equipos_disp]
        sel_equipo = c_loc3.selectbox(
            "Equipo / Máquina",
            [""] + nombres_eq,
            disabled=not bool(sel_sala),
            format_func=lambda x: "Seleccione..." if x == "" else x,
            key="reg_equipo"
        )

        cod_auto = next((e["codigo"] for e in equipos_disp if e["nombre"] == sel_equipo), "")
        st.session_state["reg_cod_eq"] = cod_auto
        cod_equipo = c_loc4.text_input(
            "Código del Equipo",
            disabled=True,
            placeholder="Autocompletado",
            key="reg_cod_eq"
        )

        c_emp1, c_emp2, c_emp3, c_emp4 = st.columns(4)
        cod_empleado = c_emp1.text_input("Cód. Empleado *", placeholder="Ej. EMP-123", key="reg_cod_emp")
        solicitante = c_emp2.text_input("Solicitante *", placeholder="Ej. Juan Pérez", key="reg_solicitante")
        origen = c_emp3.selectbox("Departamento *", [""] + departamentos, format_func=lambda x: "Seleccione..." if x == "" else x, key="reg_origen")

        tarea_disabled = (origen != "" and origen != "Mantenimiento")
        tipo_tarea = c_emp4.selectbox(
            "Tipo de Tarea",
            ["", "Preventivo", "Correctivo", "Mejora"],
            disabled=tarea_disabled,
            format_func=lambda x: "Seleccione..." if x == "" else ("Mejora de Proceso" if x == "Mejora" else x),
            key="reg_tipo_tarea"
        )

        c_desc, c_btn = st.columns([4, 1], vertical_alignment="bottom")
        descripcion = c_desc.text_input("Descripción Breve *", placeholder="Ej. El motor principal se detuvo repentinamente...", key="reg_desc")

        if c_btn.button("➕ Registrar Ticket", type="primary", use_container_width=True):
            if not sel_area or not sel_sala or not cod_empleado.strip() or not solicitante.strip() or not origen or not descripcion.strip():
                st.error("Completa todos los campos obligatorios marcados con *.")
            elif origen == "Mantenimiento" and not tipo_tarea:
                st.error("Si el departamento es Mantenimiento, debes seleccionar el Tipo de Tarea.")
            else:
                ok, msg = db.create_ticket({
                    "codigo": next_code,
                    "anio": anio_actual,
                    "mes": mes_actual,
                    "fechaVisual": fecha_visual,
                    "horaVisual": hora_visual,
                    "area": sel_area,
                    "sala": sel_sala,
                    "equipo": sel_equipo,
                    "codigoEquipo": cod_equipo,
                    "solicitante": solicitante.strip(),
                    "codigoEmpleado": cod_empleado.strip(),
                    "origen": origen,
                    "tipoTarea": "" if tarea_disabled else tipo_tarea,
                    "descripcion": descripcion.strip()
                })
                if ok:
                    st.session_state.limpiar_registro_pendiente = True
                    st.session_state.registro_ticket_msg = f"✅ {msg} ({next_code})"
                    st.rerun()
                else:
                    st.error(msg)

        st.divider()

        # --- FORMULARIO DE CIERRE DE TICKETS ---
        st.subheader("🟢 Cierre de Solicitud (Completar Ticket)")
        if not can_close_tickets:
            st.warning("🔒 **Acceso Restringido:** Solo los usuarios pertenecientes al departamento de **Mantenimiento** (o el administrador) pueden cerrar tickets técnicos.")
        else:
            # 1. Ejecutar limpieza PENDIENTE antes de dibujar cualquier widget
                def set_cierre_fields(tkt):
                    st.session_state["c_f_ing"] = tkt["fecha_visual"] if tkt else ""
                    st.session_state["c_h_ing"] = tkt["hora_visual"] if tkt else ""
                    st.session_state["c_area"] = tkt["area"] if tkt else ""
                    st.session_state["c_sala"] = tkt["sala"] if tkt else ""
                    st.session_state["c_eq"] = tkt["equipo"] if tkt else ""
                    st.session_state["c_codeq"] = tkt["codigo_equipo"] if tkt else ""
                    tipo_pref = tkt["tipo_tarea"] if (tkt and tkt.get("tipo_tarea")) else ""
                    st.session_state["c_tipo"] = tipo_pref if tipo_pref in ["", "Preventivo", "Correctivo", "Mejora"] else ""

                def reset_horas_cierre():
                    for k in ["c_hi_h", "c_hi_m", "c_hi_ampm", "c_hf_h", "c_hf_m", "c_hf_ampm"]:
                        st.session_state[k] = None
                    st.session_state["c_t_tot"] = ""

                if st.session_state.pop("limpiar_cierre_pendiente", False):
                    st.session_state.ticket_encontrado = None
                    st.session_state.cierre_busq_msg = None
                    st.session_state["cierre_busq"] = ""
                    st.session_state["c_tecnico"] = ""
                    st.session_state["c_accion"] = ""
                    set_cierre_fields(None)
                    reset_horas_cierre()

                b_col1, b_col2, b_col3 = st.columns([3, 1, 1], vertical_alignment="bottom")
                cod_busqueda = b_col1.text_input(
                    "Buscar Ticket Abierto (Autocompletar)",
                    placeholder="Ingrese código (ej. TKT-001)",
                    key="cierre_busq"
                ).strip().upper()

                if b_col2.button("🔍 Buscar", use_container_width=True):
                    tkt = db.get_ticket_by_code(cod_busqueda)
                    if tkt:
                        st.session_state.ticket_encontrado = tkt
                        st.session_state.cierre_busq_msg = ("success", "Ticket encontrado. Ubicación de equipo bloqueada por seguridad.")
                        set_cierre_fields(tkt)
                        st.rerun()
                    else:
                        st.session_state.ticket_encontrado = None
                        st.session_state.cierre_busq_msg = ("error", "Ticket no encontrado o ya fue cerrado.")
                        set_cierre_fields(None)
                        st.rerun()

                if b_col3.button("🧹 Limpiar", use_container_width=True):
                    st.session_state.ticket_encontrado = None
                    st.session_state.cierre_busq_msg = None
                    st.session_state["cierre_busq"] = ""
                    set_cierre_fields(None)
                    reset_horas_cierre()
                    st.rerun()

                if st.session_state.get("cierre_busq_msg"):
                    tipo_msg, txt_msg = st.session_state.cierre_busq_msg
                    if tipo_msg == "success":
                        st.success(txt_msg)
                    else:
                        st.error(txt_msg)

                tkt_enc = st.session_state.get("ticket_encontrado", None)

                r1_1, r1_2, r1_3 = st.columns(3)
                r1_1.text_input("Fecha de Ingreso", disabled=True, placeholder="Autocompletado", key="c_f_ing")
                r1_2.text_input("Hora de Ingreso", disabled=True, placeholder="Autocompletado", key="c_h_ing")
                r1_3.text_input("Área", disabled=True, placeholder="Autocompletado", key="c_area")

                r2_1, r2_2, r2_3 = st.columns(3)
                r2_1.text_input("Sala / Ubicación", disabled=True, placeholder="Autocompletado", key="c_sala")
                r2_2.text_input("Equipo / Máquina", disabled=True, placeholder="Autocompletado", key="c_eq")
                r2_3.text_input("Código del Equipo", disabled=True, placeholder="Autocompletado", key="c_codeq")

                r3_1, r3_2, r3_3 = st.columns(3)
                origen_tkt = tkt_enc["origen"] if tkt_enc else ""
                opciones_tipo = ["", "Preventivo", "Correctivo", "Mejora"]

                c_tipo = r3_1.selectbox(
                    "Tipo de Tarea Atendida *",
                    opciones_tipo,
                    disabled=bool(tkt_enc and origen_tkt == "Mantenimiento"),
                    format_func=lambda x: "Seleccione..." if x == "" else ("Mejora de Proceso" if x == "Mejora" else x),
                    key="c_tipo"
                )

                falla_disabled = (c_tipo != "Correctivo")
                c_falla = r3_2.selectbox(
                    "Tipo de Falla Real",
                    ["N/A", "Mecánica", "Eléctrica", "Neumática", "Operacional", "Otra"] if not falla_disabled else ["N/A"],
                    disabled=falla_disabled,
                    key="c_falla"
                )
                c_tecnico = r3_3.text_input("Técnico Responsable *", placeholder="Nombre del técnico...", key="c_tecnico")

                horas_12 = [f"{h:02d}" for h in range(1, 13)]
                minutos_60 = [f"{m:02d}" for m in range(0, 60)]
                periodos_ampm = ["AM", "PM"]

                r4_1, r4_2, r4_3 = st.columns([1.3, 1.3, 1])

                with r4_1:
                    st.markdown('<span style="font-size:12px; font-weight:700; color:#475569;">🕒 HORA DE INICIO *</span>', unsafe_allow_html=True)
                    hi_c1, hi_c2, hi_c3 = st.columns(3)
                    hi_h = hi_c1.selectbox("Hora Ini", horas_12, index=None, placeholder="HH", label_visibility="collapsed", key="c_hi_h")
                    hi_m = hi_c2.selectbox("Min Ini", minutos_60, index=None, placeholder="MM", label_visibility="collapsed", key="c_hi_m")
                    hi_p = hi_c3.selectbox("AM/PM Ini", periodos_ampm, index=None, placeholder="AM/PM", label_visibility="collapsed", key="c_hi_ampm")

                with r4_2:
                    st.markdown('<span style="font-size:12px; font-weight:700; color:#475569;">⏱️ HORA DE FINALIZACIÓN *</span>', unsafe_allow_html=True)
                    hf_c1, hf_c2, hf_c3 = st.columns(3)
                    hf_h = hf_c1.selectbox("Hora Fin", horas_12, index=None, placeholder="HH", label_visibility="collapsed", key="c_hf_h")
                    hf_m = hf_c2.selectbox("Min Fin", minutos_60, index=None, placeholder="MM", label_visibility="collapsed", key="c_hf_m")
                    hf_p = hf_c3.selectbox("AM/PM Fin", periodos_ampm, index=None, placeholder="AM/PM", label_visibility="collapsed", key="c_hf_ampm")

                h_ini_str = f"{hi_h}:{hi_m} {hi_p}" if (hi_h and hi_m and hi_p) else ""
                h_fin_str = f"{hf_h}:{hf_m} {hf_p}" if (hf_h and hf_m and hf_p) else ""

                tiempo_str, tiempo_dec = logic.calcular_tiempo(h_ini_str, h_fin_str)
                st.session_state["c_t_tot"] = tiempo_str

                with r4_3:
                    st.markdown('<span style="font-size:12px; font-weight:700; color:#475569;">TIEMPO TOTAL TOMADO</span>', unsafe_allow_html=True)
                    st.text_input(
                        "Tiempo Total Tomado",
                        disabled=True,
                        placeholder="Calculado auto.",
                        label_visibility="collapsed",
                        key="c_t_tot"
                    )

                r5_1, r5_2 = st.columns([3, 1], vertical_alignment="bottom")
                c_accion = r5_1.text_input("Acción Tomada / Solución Realizada *", placeholder="Ej. Se reemplazó el sensor defectuoso y se calibró...", key="c_accion")

                if r5_2.button("✅ Ejecutar Cierre", type="primary", use_container_width=True):
                    if not tkt_enc:
                        st.error("Primero busca y selecciona un ticket abierto válido.")
                    elif not c_tipo or not c_tecnico.strip() or not h_ini_str or not h_fin_str or not c_accion.strip():
                        st.error("Completa todos los campos obligatorios para cerrar el ticket.")
                    else:
                        db.close_ticket({
                            "codigo": tkt_enc["codigo"],
                            "anio": tkt_enc["anio"],
                            "mes": tkt_enc["mes"],
                            "area": tkt_enc["area"],
                            "sala": tkt_enc["sala"],
                            "equipo": tkt_enc["equipo"],
                            "codigoEquipo": tkt_enc["codigo_equipo"],
                            "tipo": c_tipo,
                            "tipoFalla": c_falla if c_tipo == "Correctivo" else "N/A",
                            "tecnico": c_tecnico.strip(),
                            "accionTomada": c_accion.strip(),
                            "horaInicio": h_ini_str,
                            "horaFin": h_fin_str,
                            "tiempoTotal": tiempo_str or "0h 0m"
                        }, tiempo_dec)
                        st.session_state.limpiar_cierre_pendiente = True
                        if c_tipo == "Correctivo":
                            st.session_state.cierre_busq_msg = ("success", f"Ticket cerrado. +{tiempo_dec} hrs sumadas al tiempo detenido global.")
                        else:
                            st.session_state.cierre_busq_msg = ("success", "Ticket cerrado exitosamente.")
                        st.rerun()    

        st.divider()

        # --- TABLA DE TICKETS ACTIVOS ---
        activos = db.get_tickets("Abierto")
        st.subheader(f"🔵 Solicitudes Activas (Pendientes de Cierre) — Total Abiertas: {len(activos)}")
        if activos:
            df_act = pd.DataFrame(activos)[[
                "codigo", "fecha_visual", "hora_visual", "area", "sala", "equipo", "codigo_equipo", "origen", "solicitante", "descripcion"
            ]]
            df_act.columns = ["Código", "Fecha", "Hora", "Área", "Sala", "Equipo", "Cód. Equipo", "Departamento", "Solicitante", "Descripción"]
            st.dataframe(df_act, use_container_width=True, hide_index=True)
        else:
            st.info("No hay solicitudes activas en este momento. Todas las solicitudes creadas han sido cerradas.")

    # ==========================================================
    # PESTAÑA 2: VISOR DE SOLICITUDES
    # ==========================================================
    with tabs[1]:
        matriz = db.get_matriz_solicitudes()
        anios_disp = sorted(list(matriz.keys()))
        f_col1, f_col2 = st.columns(2)
        anio_visor = f_col1.selectbox("Filtrar Año", anios_disp, index=len(anios_disp)-1, key="visor_sol_anio")
        mes_visor = f_col2.selectbox("Filtrar Distribución por Áreas", ["Todos"] + logic.NOMBRES_MESES, key="visor_sol_mes")

        mensual_rows = []
        for m in logic.NOMBRES_MESES:
            items = matriz.get(anio_visor, {}).get(m, [])
            cre = sum(x.get("creadas", 0) for x in items)
            res = sum(x.get("resueltas", 0) for x in items)
            mensual_rows.append({"Mes": m, "Creadas": cre, "Resueltas": res, "Pendientes": max(0, cre - res)})
        df_mensual = pd.DataFrame(mensual_rows)

        tot_creadas = int(df_mensual["Creadas"].sum())
        tot_resueltas = int(df_mensual["Resueltas"].sum())
        tot_pendientes = tot_creadas - tot_resueltas
        tasa_res = round((tot_resueltas / tot_creadas) * 100) if tot_creadas > 0 else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Solicitudes Creadas", tot_creadas, f"Año {anio_visor}")
        k2.metric("Solicitudes Resueltas", tot_resueltas, f"Año {anio_visor}")
        k3.metric("No Resueltas (Pendientes)", tot_pendientes, "En atraso", delta_color="inverse")
        k4.metric("Tasa de Resolución", f"{tasa_res}%", "Eficiencia")

        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.plotly_chart(charts.plot_solicitudes_mensuales(df_mensual, anio_visor), use_container_width=True)

        with g_col2:
            area_rows = []
            for area in base_areas:
                if mes_visor != "Todos":
                    d = next((x for x in matriz.get(anio_visor, {}).get(mes_visor, []) if x["area"] == area), {})
                    cre, res = d.get("creadas", 0), d.get("resueltas", 0)
                else:
                    cre = sum(next((x.get("creadas", 0) for x in matriz.get(anio_visor, {}).get(m, []) if x["area"] == area), 0) for m in logic.NOMBRES_MESES)
                    res = sum(next((x.get("resueltas", 0) for x in matriz.get(anio_visor, {}).get(m, []) if x["area"] == area), 0) for m in logic.NOMBRES_MESES)
                area_rows.append({"Área": area, "Creadas": cre, "Resueltas": res, "Pendientes": max(0, cre - res)})
            df_area = pd.DataFrame(area_rows)
            titulo_p = f"Todo el {anio_visor}" if mes_visor == "Todos" else f"{mes_visor} {anio_visor}"
            st.plotly_chart(charts.plot_solicitudes_area(df_area, titulo_p), use_container_width=True)

        st.subheader("🟢 Historial de Solicitudes Resueltas (Últimos Cierres)")
        resueltos = db.get_tickets("Cerrado")
        if resueltos:
            df_res = pd.DataFrame(resueltos)[[
                "codigo", "mes", "anio", "area", "sala", "equipo", "codigo_equipo", "tipo_tarea", "tipo_falla", "tiempo_total", "tecnico"
            ]]
            df_res.columns = ["Código", "Mes", "Año", "Área", "Sala", "Equipo", "Cód. Equipo", "Tipo", "Falla", "Tiempo Total", "Técnico"]
            st.dataframe(df_res, use_container_width=True, hide_index=True)
        else:
            st.info("Aún no se han cerrado tickets. Los tickets cerrados aparecerán aquí con su detalle de tiempo y técnico responsable.")

    # ==========================================================
    # PESTAÑA 3: ANÁLISIS DE FALLAS
    # ==========================================================
    with tabs[2]:
        matriz = db.get_matriz_solicitudes()
        fallas_all = db.get_historial_fallas()

        st.subheader("🧮 Variables Operativas Globales")
        vf1, vf2 = st.columns(2)
        filtro_var_mes = vf1.selectbox("Mes", ["Todos"] + logic.NOMBRES_MESES, key="var_mes")
        filtro_var_anio = vf2.selectbox("Año", sorted(list(matriz.keys())), index=len(matriz.keys())-1, key="var_anio")

        fallas_filt = [
            f for f in fallas_all
            if (filtro_var_mes == "Todos" or f["mes"] == filtro_var_mes) and f["anio"] == filtro_var_anio
        ]
        ht_global = logic.calcular_horas_totales(filtro_var_mes, filtro_var_anio)
        hp_global = sum(f["tiempo"] for f in fallas_filt)
        na_global = sum(f["averias"] for f in fallas_filt)
        meta_global = db.get_meta_mttr("GLOBAL")

        vg1, vg2, vg3, vg4 = st.columns(4)
        vg1.metric("Horas Totales Prog. (Auto)", f"{ht_global} hrs")
        vg2.metric("Horas Parada (Auto filtrado)", f"{hp_global:.1f} hrs")
        vg3.metric("Número Averías (Auto filtrado)", na_global)
        nueva_meta_g = vg4.number_input("Meta MTTR (hrs)", min_value=0.1, step=0.1, value=meta_global, disabled=not is_admin, key="meta_g")
        if is_admin and nueva_meta_g != meta_global:
            db.set_meta_mttr("GLOBAL", nueva_meta_g)

        st.subheader("🏭 Variables Operativas Específicas (Por Área)")
        area_espec = st.selectbox("Seleccionar Área", base_areas, key="var_area_espec")
        fallas_area = [f for f in fallas_filt if f["area"] == area_espec]
        hp_area = sum(f["tiempo"] for f in fallas_area)
        na_area = sum(f["averias"] for f in fallas_area)
        meta_area = db.get_meta_mttr(area_espec)

        va1, va2, va3, va4 = st.columns(4)
        va1.metric("Horas Totales Prog. (Auto)", f"{ht_global} hrs")
        va2.metric("Horas Parada (Área)", f"{hp_area:.1f} hrs")
        va3.metric("Número Averías (Área)", na_area)
        nueva_meta_a = va4.number_input("Meta MTTR Área (hrs)", min_value=0.1, step=0.1, value=meta_area, disabled=not is_admin, key="meta_a")
        if is_admin and nueva_meta_a != meta_area:
            db.set_meta_mttr(area_espec, nueva_meta_a)

        st.divider()
        col_top, col_par = st.columns(2)
        with col_top:
            with st.container(border=True):
                st.markdown("#### 🚨 Top Equipos Críticos")
                if fallas_filt:
                    eq_map = {}
                    for f in fallas_filt:
                        eq = f["equipo"] or "Sin especificar"
                        eq_map.setdefault(eq, {"Área": f["area"], "Equipo": eq, "Averías": 0, "T. Detenido": 0.0})
                        eq_map[eq]["Averías"] += f["averias"]
                        eq_map[eq]["T. Detenido"] += f["tiempo"]
                    top_list = sorted(eq_map.values(), key=lambda x: x["T. Detenido"], reverse=True)[:4]
                    for item in top_list:
                        t = item["T. Detenido"]
                        item["Impacto"] = "🔴 Alto" if t > 6 else ("🟡 Medio" if t > 3 else "🟢 Bajo")
                        item["T. Detenido (hrs)"] = f"{t:.1f} hrs"
                    df_top = pd.DataFrame(top_list)[["Área", "Equipo", "Averías", "T. Detenido (hrs)", "Impacto"]]
                    st.dataframe(df_top, use_container_width=True, hide_index=True)
                else:
                    st.markdown(
                        '<p style="text-align:center; color:#64748b; padding:32px 0; font-size:0.88rem;">'
                        'No hay equipos con averías registradas. Crea un ticket correctivo para iniciar el análisis.'
                        '</p>',
                        unsafe_allow_html=True
                    )

                # Leyenda idéntica al diseño original debajo de Top Equipos Críticos
                st.markdown("""
                <div style="margin-top: 14px; padding-top: 12px; border-top: 1px solid #f1f5f9;
                            display: flex; flex-wrap: wrap; justify-content: center; align-items: center;
                            gap: 14px; font-size: 12px; color: #64748b; font-weight: 500;">
                    <span style="color: #334155; font-weight: 700;">Impacto por tiempo acumulado:</span>
                    <span style="display: inline-flex; align-items: center; gap: 5px;">
                        <span style="width: 9px; height: 9px; border-radius: 50%; background-color: #ef4444; display: inline-block;"></span>
                        Alto (&gt; 6 hrs)
                    </span>
                    <span style="display: inline-flex; align-items: center; gap: 5px;">
                        <span style="width: 9px; height: 9px; border-radius: 50%; background-color: #f59e0b; display: inline-block;"></span>
                        Medio (3 a 6 hrs)
                    </span>
                    <span style="display: inline-flex; align-items: center; gap: 5px;">
                        <span style="width: 9px; height: 9px; border-radius: 50%; background-color: #10b981; display: inline-block;"></span>
                        Bajo (&le; 3 hrs)
                    </span>
                </div>
                """, unsafe_allow_html=True)

        with col_par:
            with st.container(border=True):
                st.markdown("#### 📊 Distribución por Tipo de Falla")
                if fallas_filt:
                    f_map = {}
                    for f in fallas_filt:
                        det = f["detalle"] or "Otra"
                        if det != "N/A":
                            f_map[det] = f_map.get(det, 0) + f["averias"]

                    if f_map:
                        color_fallas = {
                            "Mecánica": "#ef4444",     # Rojo
                            "Eléctrica": "#f59e0b",    # Ámbar
                            "Neumática": "#3b82f6",    # Azul
                            "Operacional": "#64748b",  # Gris pizarra
                            "Otra": "#a855f7"          # Morado
                        }
                        ordenado = sorted(f_map.items(), key=lambda x: x[1], reverse=True)
                        max_f = max(v for _, v in ordenado) or 1

                        items_html = []
                        for tipo_f, cant in ordenado:
                            pct_w = round((cant / max_f) * 100, 1)
                            bar_color = color_fallas.get(tipo_f, "#64748b")
                            etiqueta_falla = "falla" if cant == 1 else "fallas"
                            items_html.append(
                                f'<div style="margin-bottom:14px;">'
                                f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">'
                                f'<span style="font-size:14px; font-weight:700; color:#334155;">{tipo_f}</span>'
                                f'<span style="font-size:13px; font-weight:700; color:#64748b;">{cant} {etiqueta_falla}</span>'
                                f'</div>'
                                f'<div style="width:100%; height:14px; background-color:#f1f5f9; border-radius:999px; overflow:hidden;">'
                                f'<div style="width:{pct_w}%; height:100%; background-color:{bar_color}; border-radius:999px;"></div>'
                                f'</div>'
                                f'</div>'
                            )

                        barras_html = f'<div style="padding: 10px 4px 8px 4px;">{"".join(items_html)}</div>'
                        st.markdown(barras_html, unsafe_allow_html=True)
                    else:
                        st.markdown('<p style="text-align:center; color:#64748b; padding:32px 0; font-size:0.88rem;">No hay fallas para este periodo.</p>', unsafe_allow_html=True)
                else:
                    st.markdown('<p style="text-align:center; color:#64748b; padding:32px 0; font-size:0.88rem;">No hay fallas para este periodo.</p>', unsafe_allow_html=True)

        st.subheader("📋 Registro Detallado de Averías por Equipo")
        if fallas_filt:
            df_fallas = pd.DataFrame(fallas_filt)[["mes", "area", "sala", "equipo", "codigo_equipo", "detalle", "averias", "tiempo", "impacto"]]
            df_fallas.columns = ["Mes", "Área", "Sala", "Equipo", "Cód. Equipo", "Detalle / Falla", "Cant. Averías", "Tiempo Perdido (hrs)", "Impacto"]
            st.dataframe(df_fallas, use_container_width=True, hide_index=True)
        else:
            st.info("No hay averías críticas registradas para este periodo.")

    # ==========================================================
    # PESTAÑA 4: PLAN DE MANTENIMIENTO
    # ==========================================================
    with tabs[3]:
        matriz = db.get_matriz_solicitudes()
        p1, p2 = st.columns(2)
        anio_plan = p1.selectbox("Año del Plan", sorted(list(matriz.keys())), index=len(matriz.keys())-1, key="plan_anio")
        mes_plan = p2.selectbox(
            "Mes",
            logic.NOMBRES_MESES,
            index=datetime.now().month - 1,
            label_visibility="collapsed",
            key="plan_mes"
        )

        st.subheader(f"🗓️ Planificación y Ejecución por Áreas ({mes_plan} - {anio_plan})")
        if not is_admin:
            st.caption("🔒 Solo el administrador puede modificar los Preventivos Programados. Los realizados se actualizan solos al cerrar un ticket.")

        items_mes = matriz.get(anio_plan, {}).get(mes_plan, [])
        for item in items_mes:
            area_n = item["area"]
            max_eq = len(cfg["equiposPorArea"].get(area_n, []))
            col_a, col_pp, col_pr, col_cr = st.columns([2, 1, 1, 1], vertical_alignment="center")
            col_a.markdown(f"**{area_n}**  \n<span style='font-size:12px;color:#64748b;'>{max_eq} equipos registrados</span>", unsafe_allow_html=True)

            nuevo_pp = col_pp.number_input(
                "Prev. Prog.",
                min_value=0,
                max_value=max_eq,
                value=min(item.get("prevProgramados", 0), max_eq),
                disabled=not is_admin,
                key=f"pp_{anio_plan}_{mes_plan}_{area_n}"
            )
            if is_admin and nuevo_pp != item.get("prevProgramados", 0):
                db.update_prev_programados(anio_plan, mes_plan, area_n, nuevo_pp)
                st.rerun()

            col_pr.metric("Prev. Realizados", item.get("prevRealizados", 0))
            col_cr.metric("Corr. Realizados", item.get("corrRealizados", 0))

        st.divider()
        tot_pp = sum(x.get("prevProgramados", 0) for x in items_mes)
        tot_pr = sum(x.get("prevRealizados", 0) for x in items_mes)
        tot_cr = sum(x.get("corrRealizados", 0) for x in items_mes)
        r1, r2, r3 = st.columns(3)
        r1.metric("Total Prev. Programados", tot_pp, f"Mes {mes_plan}")
        r2.metric("Total Preventivos Realizados", tot_pr, f"Mes {mes_plan}")
        r3.metric("Total Correctivos Realizados", tot_cr, f"Mes {mes_plan}")

    # ==========================================================
    # PESTAÑA 5: VISOR DE RESULTADOS (KPIs + DESEMPEÑO)
    # ==========================================================
    with tabs[4]:
        matriz = db.get_matriz_solicitudes()
        fallas_all = db.get_historial_fallas()
        v1, v2 = st.columns(2)
        anio_res = v1.selectbox("Año a Evaluar", sorted(list(matriz.keys())), index=len(matriz.keys())-1, key="res_anio")
        mes_res = v2.selectbox(
            "Mes",
            logic.NOMBRES_MESES,
            index=datetime.now().month - 1,
            label_visibility="collapsed",
            key="res_mes"
        )

        kpis = logic.calcular_kpis_visor(matriz, fallas_all, anio_res, mes_res, db.get_meta_mttr("GLOBAL"))

        row1_1, row1_2, row1_3 = st.columns(3)
        with row1_1:
            st.metric("MTTF (Tiempo Hasta Falla)", f"{kpis['mttf']} hrs" if kpis['mttf'] is not None else "N/A")
            if st.button("ℹ️ Fórmula MTTF", key="btn_mttf", use_container_width=True):
                modal_info_kpi("mttf")
        with row1_2:
            st.metric("MTTR (Tiempo de Reparación)", f"{kpis['mttr']} hrs")
            if st.button("ℹ️ Fórmula MTTR", key="btn_mttr", use_container_width=True):
                modal_info_kpi("mttr")
        with row1_3:
            st.metric("MTBF (Tiempo Entre Fallas)", f"{kpis['mtbf']} hrs" if kpis['mtbf'] is not None else "N/A")
            if st.button("ℹ️ Fórmula MTBF", key="btn_mtbf", use_container_width=True):
                modal_info_kpi("mtbf")

        row2_1, row2_2, row2_3 = st.columns(3)
        with row2_1:
            st.metric("Disponibilidad de Equipos", f"{kpis['disponibilidad']}%")
            if st.button("ℹ️ Fórmula Disponibilidad", key="btn_disp", use_container_width=True):
                modal_info_kpi("disponibilidad")
        with row2_2:
            st.metric("Cumplimiento Prev. (PMP)", f"{kpis['pmp']}%")
            if st.button("ℹ️ Fórmula PMP", key="btn_pmp", use_container_width=True):
                modal_info_kpi("pmp")
        with row2_3:
            st.metric("Backlog (Prev. Pendientes)", f"{kpis['backlog']} OT")
            if st.button("ℹ️ Fórmula Backlog", key="btn_backlog", use_container_width=True):
                modal_info_kpi("backlog")

        st.divider()
        d_col1, d_col2 = st.columns([1, 1.4])
        with d_col1:
            st.subheader("Relación Mantenimiento")
            st.caption(f"Distribución de carga de trabajo ({mes_res} - {anio_res})")
            st.plotly_chart(charts.plot_donut_mantenimiento(kpis["prev_pct"], kpis["corr_pct"]), use_container_width=True)

        with d_col2:
            st.subheader(f"🏆 Evaluación de Desempeño Técnico ({mes_res} - {anio_res})")
            st.metric("Índice Global de Desempeño", f"{kpis['desempeno_general']}%")
            st.write(f"**Cumplimiento Preventivo (PMP):** {kpis['score_prev']}%")
            st.progress(kpis["score_prev"] / 100.0)
            st.write(f"**Eficiencia de Reparación (MTTR real vs Meta):** {kpis['score_mttr']}%")
            st.progress(kpis["score_mttr"] / 100.0)
            st.info(f"📋 **Notas para el Comité:** Desempeño técnico en **{kpis['desempeno_general']}%** | Disponibilidad global en **{kpis['disponibilidad']}%**.")

    # ==========================================================
    # PESTAÑA 6: VISOR CUMPLIMIENTO PREVENTIVO (PMP)
    # ==========================================================
    with tabs[5]:
        matriz = db.get_matriz_solicitudes()
        anio_pmp = st.selectbox("Año de Evaluación PMP", sorted(list(matriz.keys())), index=len(matriz.keys())-1, key="pmp_anio")

        pmp_rows = []
        for m in logic.NOMBRES_MESES:
            items = matriz.get(anio_pmp, {}).get(m, [])
            prog = sum(x.get("prevProgramados", 0) for x in items)
            real = sum(x.get("prevRealizados", 0) for x in items)
            pct = round((real / prog) * 100) if prog > 0 else 0
            pmp_rows.append({"Mes": m, "Prev. Prog.": prog, "Prev. Real.": real, "Cumplimiento (%)": pct})
        df_pmp = pd.DataFrame(pmp_rows)
        st.plotly_chart(charts.plot_pmp_global(df_pmp, anio_pmp), use_container_width=True)

        st.subheader("🗺️ Matriz de Cumplimiento por Área (Mapa de Calor)")
        matrix_rows = []
        line_rows = {m: {"Mes": m} for m in logic.NOMBRES_MESES}

        for area in base_areas:
            row_dict = {"Área \\ Mes": area}
            for m in logic.NOMBRES_MESES:
                d = next((x for x in matriz.get(anio_pmp, {}).get(m, []) if x["area"] == area), {})
                prog, real = d.get("prevProgramados", 0), d.get("prevRealizados", 0)
                if prog > 0:
                    pct = round((real / prog) * 100)
                    row_dict[m] = f"{pct}% ({real}/{prog})"
                    line_rows[m][area] = pct
                else:
                    row_dict[m] = "N/A"
                    line_rows[m][area] = None
            matrix_rows.append(row_dict)

        df_heatmap = pd.DataFrame(matrix_rows)

        def color_cells(val):
            if not isinstance(val, str) or val == "N/A":
                return "background-color: #f1f5f9; color: #94a3b8;"
            pct = int(val.split("%")[0])
            if pct >= 90:
                return "background-color: #d1fae5; color: #065f46; font-weight: bold;"
            elif pct >= 70:
                return "background-color: #fef3c7; color: #92400e; font-weight: bold;"
            return "background-color: #fee2e2; color: #991b1b; font-weight: bold;"

        st.dataframe(
            df_heatmap.style.map(color_cells, subset=logic.NOMBRES_MESES),
            use_container_width=True,
            hide_index=True
        )

        with st.expander("📈 Ver Gráfica de Líneas: Evolución por Área", expanded=False):
            df_lineas = pd.DataFrame(list(line_rows.values()))
            st.plotly_chart(charts.plot_pmp_lineas_areas(df_lineas, anio_pmp), use_container_width=True)


# Punto de entrada
if not st.session_state.authenticated:
    render_auth_screen()
else:
    render_dashboard()