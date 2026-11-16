import sqlite3
import json
import os
from datetime import datetime
import streamlit as st

DB_FILE = "mantenimiento.db"

DEFAULT_DEPARTAMENTOS = [
    'Mantenimiento', 'Producción', 'Control de Calidad', 'Desarrollo Galénico', 'Almacén'
]

DEFAULT_EQUIPOS_POR_AREA = {
    'Sólido': [
        {'nombre': 'Mezclador V', 'codigo': 'MEZ-V-01', 'sala': 'Mezclado'},
        {'nombre': 'Tableteadora 1', 'codigo': 'TAB-01', 'sala': 'Compresión 1'},
        {'nombre': 'Tableteadora 2', 'codigo': 'TAB-02', 'sala': 'Compresión 2'},
        {'nombre': 'Recubridora', 'codigo': 'REC-01', 'sala': 'Recubrimiento'},
        {'nombre': 'Granulador', 'codigo': 'GRA-01', 'sala': 'Granulado'}
    ],
    'Líquido': [
        {'nombre': 'Tanque Mezclador L1', 'codigo': 'TML-01', 'sala': 'Preparación 1'},
        {'nombre': 'Tanque Mezclador L2', 'codigo': 'TML-02', 'sala': 'Preparación 2'},
        {'nombre': 'Tanque de Almacenamiento', 'codigo': 'TAL-01', 'sala': 'Almacenamiento'},
        {'nombre': 'Llenadora de Frascos', 'codigo': 'LLF-01', 'sala': 'Llenado Sintético'},
        {'nombre': 'Marmita 1', 'codigo': 'MAR-01', 'sala': 'Preparación 1'}
    ],
    'Semisólido': [
        {'nombre': 'Mezclador Planetario', 'codigo': 'MEZ-P-01', 'sala': 'Preparación'},
        {'nombre': 'Llenadora de Tubos', 'codigo': 'LLT-01', 'sala': 'Llenado de Crema'},
        {'nombre': 'Marmita 2', 'codigo': 'MAR-02', 'sala': 'Preparación'},
        {'nombre': 'Emulsionador', 'codigo': 'EMU-01', 'sala': 'Preparación'}
    ],
    'Empaque': [
        {'nombre': 'Estuchadora A', 'codigo': 'EST-A-01', 'sala': 'Área de Estuchado'},
        {'nombre': 'Estuchadora B', 'codigo': 'EST-B-01', 'sala': 'Área de Estuchado'},
        {'nombre': 'Blistera 1', 'codigo': 'BLI-01', 'sala': 'Línea de Blíster 1'},
        {'nombre': 'Blistera 2', 'codigo': 'BLI-02', 'sala': 'Línea de Blíster 1'},
        {'nombre': 'Etiquetadora', 'codigo': 'ETI-01', 'sala': 'Área de Estuchado'}
    ],
    'Pesadas': [
        {'nombre': 'Balanza Analítica 1', 'codigo': 'BAL-A-01', 'sala': 'Cuarto de Pesadas A'},
        {'nombre': 'Balanza Analítica 2', 'codigo': 'BAL-A-02', 'sala': 'Cuarto de Pesadas B'},
        {'nombre': 'Cabina de Flujo Laminar', 'codigo': 'CFL-01', 'sala': 'Cuarto de Pesadas A'},
        {'nombre': 'Báscula de Piso', 'codigo': 'BAS-P-01', 'sala': 'Cuarto de Pesadas B'}
    ],
    'D. Galénico': [
        {'nombre': 'Mini Mezclador V', 'codigo': 'MMV-01', 'sala': 'Laboratorio Piloto 1'},
        {'nombre': 'Prensa Piloto', 'codigo': 'PRE-P-01', 'sala': 'Laboratorio Piloto 1'},
        {'nombre': 'Agitador Magnético', 'codigo': 'AGI-M-01', 'sala': 'Laboratorio Piloto 1'},
        {'nombre': 'Campana de Extracción', 'codigo': 'CAM-E-01', 'sala': 'Laboratorio Piloto 1'}
    ],
    'Lab. Fisicoquímico': [
        {'nombre': 'HPLC 1', 'codigo': 'HPLC-01', 'sala': 'Sala de Instrumentos'},
        {'nombre': 'HPLC 2', 'codigo': 'HPLC-02', 'sala': 'Sala de Instrumentos'},
        {'nombre': 'Espectrofotómetro', 'codigo': 'ESP-01', 'sala': 'Sala de Instrumentos'},
        {'nombre': 'Cámara de Estabilidad', 'codigo': 'CAM-EST-01', 'sala': 'Área de Muestras'},
        {'nombre': 'Disolutor', 'codigo': 'DIS-01', 'sala': 'Área de Muestras'}
    ],
    'Microbiología': [
        {'nombre': 'Autoclave', 'codigo': 'AUT-01', 'sala': 'Área Estéril'},
        {'nombre': 'Incubadora 1', 'codigo': 'INC-01', 'sala': 'Sala de Incubadoras'},
        {'nombre': 'Cabina de Bioseguridad', 'codigo': 'CAB-B-01', 'sala': 'Área Estéril'},
        {'nombre': 'Microscopio', 'codigo': 'MIC-01', 'sala': 'Sala de Incubadoras'},
        {'nombre': 'Horno de Despirogenización', 'codigo': 'HOR-D-01', 'sala': 'Área Estéril'}
    ],
    'Almacén': [
        {'nombre': 'Montacargas 1', 'codigo': 'MON-01', 'sala': 'Recepción'},
        {'nombre': 'Montacargas 2', 'codigo': 'MON-02', 'sala': 'Producto Terminado'},
        {'nombre': 'Apilador Eléctrico', 'codigo': 'API-E-01', 'sala': 'Cuarentena'},
        {'nombre': 'Transpaleta Eléctrica', 'codigo': 'TRA-E-01', 'sala': 'Recepción'},
        {'nombre': 'Banda Transportadora', 'codigo': 'BAN-T-01', 'sala': 'Producto Terminado'}
    ]
}

DEFAULT_SALAS_POR_AREA = {
    'Sólido': ['Compresión 1', 'Compresión 2', 'Ensobradora', 'Blíster', 'Recubrimiento', 'Granulado', 'Mezclado', 'Control de Proceso'],
    'Líquido': ['Preparación 1', 'Preparación 2', 'Almacenamiento', 'Llenado Sintético', 'Llenado Naturales', 'Llenado Manual', 'Control de Proceso'],
    'Semisólido': ['Preparación', 'Llenado de Crema', 'Óvulo', 'Control de Proceso'],
    'Empaque': ['Línea de Blíster 1', 'Área de Estuchado'],
    'Pesadas': ['Cuarto de Pesadas A', 'Cuarto de Pesadas B'],
    'D. Galénico': ['Laboratorio Piloto 1'],
    'Lab. Fisicoquímico': ['Sala de Instrumentos', 'Área de Muestras'],
    'Microbiología': ['Área Estéril', 'Sala de Incubadoras'],
    'Almacén': ['Recepción', 'Cuarentena', 'Producto Terminado']
}

NOMBRES_MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']


def get_connection():
    """Retorna conexión SQLite local o PostgreSQL en la nube si existe en secrets."""
    cloud_url = None
    try:
        cloud_url = st.secrets.get("CLOUD_DB_URL", None)
    except Exception:
        cloud_url = None

    if cloud_url:
        import psycopg2
        return psycopg2.connect(cloud_url), "postgres"
    return sqlite3.connect(DB_FILE, check_same_thread=False), "sqlite"


def init_db():
    conn, db_type = get_connection()
    c = conn.cursor()

    # Tabla de usuarios
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            departamento TEXT NOT NULL
        )
    """)

    # Historial de accesos
    c.execute("""
        CREATE TABLE IF NOT EXISTS login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            name TEXT,
            departamento TEXT,
            date TEXT,
            time TEXT
        )
    """)

    # Configuración maestra (JSON)
    c.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Matriz de solicitudes y preventivos por año/mes/área
    c.execute("""
        CREATE TABLE IF NOT EXISTS matriz_solicitudes (
            anio TEXT,
            mes TEXT,
            area TEXT,
            creadas INTEGER DEFAULT 0,
            resueltas INTEGER DEFAULT 0,
            prev_programados INTEGER DEFAULT 0,
            prev_realizados INTEGER DEFAULT 0,
            corr_realizados INTEGER DEFAULT 0,
            PRIMARY KEY (anio, mes, area)
        )
    """)

    # Tickets (Activos y Resueltos)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            codigo TEXT PRIMARY KEY,
            estado TEXT DEFAULT 'Abierto',
            anio TEXT,
            mes TEXT,
            fecha_visual TEXT,
            hora_visual TEXT,
            area TEXT,
            sala TEXT,
            equipo TEXT,
            codigo_equipo TEXT,
            solicitante TEXT,
            codigo_empleado TEXT,
            origen TEXT,
            tipo_tarea TEXT,
            descripcion TEXT,
            tipo_falla TEXT,
            tecnico TEXT,
            accion_tomada TEXT,
            hora_inicio TEXT,
            hora_fin TEXT,
            tiempo_total TEXT
        )
    """)

    # Historial de fallas correctivas
    c.execute("""
        CREATE TABLE IF NOT EXISTS historial_fallas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anio TEXT,
            mes TEXT,
            area TEXT,
            sala TEXT,
            equipo TEXT,
            codigo_equipo TEXT,
            detalle TEXT,
            averias INTEGER DEFAULT 1,
            tiempo REAL DEFAULT 0.0,
            impacto TEXT
        )
    """)

    # Parámetros operativos (Meta MTTR global y por área)
    c.execute("""
        CREATE TABLE IF NOT EXISTS parametros (
            scope TEXT PRIMARY KEY,
            meta_mttr REAL DEFAULT 3.0
        )
    """)

    # Insertar usuario admin inicial si no existe
    c.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO users (username, password, name, departamento) VALUES (?, ?, ?, ?)",
            ('admin', '123', 'Administrador Principal', 'Mantenimiento')
        )

    # Insertar configuración inicial si no existe
    c.execute("SELECT COUNT(*) FROM config WHERE key = 'maestros'")
    if c.fetchone()[0] == 0:
        default_cfg = {
            "equiposPorArea": DEFAULT_EQUIPOS_POR_AREA,
            "salasPorArea": DEFAULT_SALAS_POR_AREA,
            "departamentos": DEFAULT_DEPARTAMENTOS
        }
        c.execute("INSERT INTO config (key, value) VALUES ('maestros', ?)", (json.dumps(default_cfg),))
        conn.commit()  # <-- Asegura que se guarde antes de leerlo abajo

    # Inicializar matriz 2025 y 2026 si está vacía
    c.execute("SELECT COUNT(*) FROM matriz_solicitudes")
    if c.fetchone()[0] == 0:
        areas = list(DEFAULT_EQUIPOS_POR_AREA.keys())
        for anio in ['2025', '2026']:
            for mes in NOMBRES_MESES:
                for area in areas:
                    c.execute("""
                        INSERT INTO matriz_solicitudes (anio, mes, area, creadas, resueltas, prev_programados, prev_realizados, corr_realizados)
                        VALUES (?, ?, ?, 0, 0, 0, 0, 0)
                    """, (anio, mes, area))

    conn.commit()
    conn.close()


# --- FUNCIONES CRUD ---

def get_config():
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key = 'maestros'")
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        return json.loads(row[0])
    return {
        "equiposPorArea": DEFAULT_EQUIPOS_POR_AREA,
        "salasPorArea": DEFAULT_SALAS_POR_AREA,
        "departamentos": DEFAULT_DEPARTAMENTOS
    }


def save_config(cfg_dict):
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("UPDATE config SET value = ? WHERE key = 'maestros'", (json.dumps(cfg_dict),))
    conn.commit()
    conn.close()


def authenticate_user(username, password):
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, password, name, departamento FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
    row = c.fetchone()
    conn.close()
    if row and row[1] == password:
        return {"username": row[0], "name": row[2], "departamento": row[3]}
    return None


def register_user(username, password, name, departamento):
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
    if c.fetchone()[0] > 0:
        conn.close()
        return False, "El nombre de usuario ya existe. Elige otro."
    c.execute(
        "INSERT INTO users (username, password, name, departamento) VALUES (?, ?, ?, ?)",
        (username.strip(), password, name.strip(), departamento)
    )
    conn.commit()
    conn.close()
    return True, "¡Usuario registrado exitosamente! Ahora puedes iniciar sesión."


def log_login(user):
    conn, _ = get_connection()
    c = conn.cursor()
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    time_str = now.strftime("%I:%M %p").lstrip("0")
    c.execute(
        "INSERT INTO login_history (username, name, departamento, date, time) VALUES (?, ?, ?, ?, ?)",
        (user["username"], user["name"], user.get("departamento", "No especificado"), date_str, time_str)
    )
    conn.commit()
    conn.close()


def get_login_history():
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, name, departamento, date, time FROM login_history ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [
        {"id": r[0], "username": r[1], "name": r[2], "departamento": r[3], "date": r[4], "time": r[5]}
        for r in rows
    ]


def get_next_ticket_code():
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tickets")
    count = c.fetchone()[0] + 1
    while True:
        code = f"TKT-{count:03d}"
        c.execute("SELECT COUNT(*) FROM tickets WHERE codigo = ?", (code,))
        if c.fetchone()[0] == 0:
            conn.close()
            return code
        count += 1


def create_ticket(ticket_data):
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tickets WHERE LOWER(codigo) = LOWER(?)", (ticket_data["codigo"],))
    if c.fetchone()[0] > 0:
        conn.close()
        return False, "Este código de ticket ya está en uso."

    c.execute("""
        INSERT INTO tickets (
            codigo, estado, anio, mes, fecha_visual, hora_visual,
            area, sala, equipo, codigo_equipo, solicitante, codigo_empleado,
            origen, tipo_tarea, descripcion
        ) VALUES (?, 'Abierto', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_data["codigo"], ticket_data["anio"], ticket_data["mes"],
        ticket_data["fechaVisual"], ticket_data["horaVisual"],
        ticket_data["area"], ticket_data["sala"], ticket_data["equipo"],
        ticket_data["codigoEquipo"], ticket_data["solicitante"],
        ticket_data["codigoEmpleado"], ticket_data["origen"],
        ticket_data["tipoTarea"], ticket_data["descripcion"]
    ))

    # Incrementar 'creadas' en matriz_solicitudes
    c.execute("""
        UPDATE matriz_solicitudes
        SET creadas = creadas + 1
        WHERE anio = ? AND mes = ? AND area = ?
    """, (ticket_data["anio"], ticket_data["mes"], ticket_data["area"]))

    conn.commit()
    conn.close()
    return True, "Solicitud registrada exitosamente."


def get_tickets(estado="Abierto"):
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tickets WHERE estado = ? ORDER BY rowid DESC", (estado,))
    cols = [desc[0] for desc in c.description]
    rows = [dict(zip(cols, r)) for r in c.fetchall()]
    conn.close()
    return rows


def get_ticket_by_code(codigo):
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tickets WHERE LOWER(codigo) = LOWER(?) AND estado = 'Abierto'", (codigo.strip(),))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    cols = [desc[0] for desc in c.description]
    conn.close()
    return dict(zip(cols, row))


def close_ticket(cierre_data, tiempo_horas_dec):
    conn, _ = get_connection()
    c = conn.cursor()

    # Verificar si el ticket existe
    c.execute("SELECT COUNT(*) FROM tickets WHERE LOWER(codigo) = LOWER(?) AND estado = 'Abierto'", (cierre_data["codigo"],))
    exists = c.fetchone()[0] > 0

    if exists:
        c.execute("""
            UPDATE tickets
            SET estado = 'Cerrado', tipo_tarea = ?, tipo_falla = ?, tecnico = ?,
                accion_tomada = ?, hora_inicio = ?, hora_fin = ?, tiempo_total = ?
            WHERE LOWER(codigo) = LOWER(?)
        """, (
            cierre_data["tipo"], cierre_data["tipoFalla"], cierre_data["tecnico"],
            cierre_data["accionTomada"], cierre_data["horaInicio"], cierre_data["horaFin"],
            cierre_data["tiempoTotal"], cierre_data["codigo"]
        ))
    else:
        # Cierre directo sin ticket previo abierto
        c.execute("""
            INSERT INTO tickets (
                codigo, estado, anio, mes, area, sala, equipo, codigo_equipo,
                tipo_tarea, tipo_falla, tecnico, accion_tomada, hora_inicio, hora_fin, tiempo_total
            ) VALUES (?, 'Cerrado', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cierre_data["codigo"], cierre_data["anio"], cierre_data["mes"],
            cierre_data["area"], cierre_data["sala"], cierre_data["equipo"],
            cierre_data["codigoEquipo"], cierre_data["tipo"], cierre_data["tipoFalla"],
            cierre_data["tecnico"], cierre_data["accionTomada"], cierre_data["horaInicio"],
            cierre_data["horaFin"], cierre_data["tiempoTotal"]
        ))

    # Actualizar matriz_solicitudes
    c.execute("""
        SELECT creadas, resueltas FROM matriz_solicitudes
        WHERE anio = ? AND mes = ? AND area = ?
    """, (cierre_data["anio"], cierre_data["mes"], cierre_data["area"]))
    row = c.fetchone()
    if row:
        creadas, resueltas = row
        if resueltas >= creadas:
            creadas = resueltas + 1
        resueltas += 1
        prev_inc = 1 if cierre_data["tipo"] == "Preventivo" else 0
        corr_inc = 1 if cierre_data["tipo"] == "Correctivo" else 0
        c.execute("""
            UPDATE matriz_solicitudes
            SET creadas = ?, resueltas = ?,
                prev_realizados = prev_realizados + ?,
                corr_realizados = corr_realizados + ?
            WHERE anio = ? AND mes = ? AND area = ?
        """, (creadas, resueltas, prev_inc, corr_inc, cierre_data["anio"], cierre_data["mes"], cierre_data["area"]))

    # Registrar en historial_fallas si es Correctivo con tiempo > 0
    if cierre_data["tipo"] == "Correctivo" and tiempo_horas_dec > 0:
        impacto = "Alto" if tiempo_horas_dec > 4 else ("Medio" if tiempo_horas_dec > 2 else "Bajo")
        detalle = cierre_data["tipoFalla"] if cierre_data["tipoFalla"] not in ("N/A", "") else "Falla General"
        c.execute("""
            INSERT INTO historial_fallas (anio, mes, area, sala, equipo, codigo_equipo, detalle, averias, tiempo, impacto)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (
            cierre_data["anio"], cierre_data["mes"], cierre_data["area"],
            cierre_data["sala"], cierre_data["equipo"], cierre_data["codigoEquipo"],
            detalle, tiempo_horas_dec, impacto
        ))

    conn.commit()
    conn.close()


def get_matriz_solicitudes():
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("SELECT anio, mes, area, creadas, resueltas, prev_programados, prev_realizados, corr_realizados FROM matriz_solicitudes")
    rows = c.fetchall()
    conn.close()

    matriz = {}
    for anio, mes, area, creadas, resueltas, pp, pr, cr in rows:
        matriz.setdefault(anio, {}).setdefault(mes, []).append({
            "area": area,
            "creadas": creadas,
            "resueltas": resueltas,
            "prevProgramados": pp,
            "prevRealizados": pr,
            "corrRealizados": cr
        })
    return matriz


def update_prev_programados(anio, mes, area, valor):
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE matriz_solicitudes
        SET prev_programados = ?
        WHERE anio = ? AND mes = ? AND area = ?
    """, (valor, anio, mes, area))
    conn.commit()
    conn.close()


def add_area_to_matriz(nombre_area):
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT anio FROM matriz_solicitudes")
    anios = [r[0] for r in c.fetchall()] or ['2025', '2026']
    for anio in anios:
        for mes in NOMBRES_MESES:
            c.execute("""
                INSERT OR IGNORE INTO matriz_solicitudes (anio, mes, area, creadas, resueltas, prev_programados, prev_realizados, corr_realizados)
                VALUES (?, ?, ?, 0, 0, 0, 0, 0)
            """, (anio, mes, nombre_area))
    conn.commit()
    conn.close()


def get_historial_fallas():
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM historial_fallas ORDER BY id DESC")
    cols = [desc[0] for desc in c.description]
    rows = [dict(zip(cols, r)) for r in c.fetchall()]
    conn.close()
    return rows


def get_meta_mttr(scope="GLOBAL"):
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("SELECT meta_mttr FROM parametros WHERE scope = ?", (scope,))
    row = c.fetchone()
    conn.close()
    return float(row[0]) if row else 3.0


def set_meta_mttr(scope, valor):
    conn, _ = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO parametros (scope, meta_mttr) VALUES (?, ?)
        ON CONFLICT(scope) DO UPDATE SET meta_mttr = excluded.meta_mttr
    """, (scope, valor))
    conn.commit()
    conn.close()