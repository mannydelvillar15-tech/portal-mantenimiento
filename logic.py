import calendar
import unicodedata
from datetime import datetime

MESES_NUM = {
    'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Ago': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12
}
NOMBRES_MESES = list(MESES_NUM.keys())


def normalizar_texto(texto):
    if not texto:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    )


def is_produccion(origen):
    return normalizar_texto(origen) == 'produccion'


def convert_12h_to_24h(time_12h):
    if not time_12h:
        return "00:00"
    try:
        dt = datetime.strptime(time_12h.strip().upper(), "%I:%M %p")
        return dt.strftime("%H:%M")
    except ValueError:
        return time_12h


def calcular_tiempo(inicio_str, fin_str):
    """Acepta formato 'HH:MM' o 'HH:MM AM/PM' y retorna ('Xh Ym', horas_decimales)."""
    if not inicio_str or not fin_str:
        return "", 0.0
    try:
        ini_24 = convert_12h_to_24h(inicio_str) if ("AM" in inicio_str.upper() or "PM" in inicio_str.upper()) else inicio_str
        fin_24 = convert_12h_to_24h(fin_str) if ("AM" in fin_str.upper() or "PM" in fin_str.upper()) else fin_str

        h1, m1 = map(int, ini_24.split(":")[:2])
        h2, m2 = map(int, fin_24.split(":")[:2])
        total_min = (h2 * 60 + m2) - (h1 * 60 + m1)
        if total_min < 0:
            total_min += 24 * 60
        horas = total_min // 60
        mins = total_min % 60
        dec = round(total_min / 60.0, 1)
        return f"{horas}h {mins}m", dec
    except Exception:
        return "", 0.0


def calcular_horas_totales(mes_str, anio_str):
    year = int(anio_str)
    if mes_str == 'Todos':
        return 8784 if calendar.isleap(year) else 8760
    mes_num = MESES_NUM.get(mes_str, 1)
    dias_mes = calendar.monthrange(year, mes_num)[1]
    return dias_mes * 24


def calcular_kpis_visor(matriz, historial_fallas, anio_plan, mes_plan, meta_mttr=3.0):
    plan_sel = matriz.get(anio_plan, {}).get(mes_plan, [])
    pp = sum(item.get("prevProgramados", 0) for item in plan_sel)
    pr = sum(item.get("prevRealizados", 0) for item in plan_sel)
    cr = sum(item.get("corrRealizados", 0) for item in plan_sel)

    fallas_visor = [f for f in historial_fallas if f.get("mes") == mes_plan and f.get("anio") == anio_plan]
    hp = sum(f.get("tiempo", 0.0) for f in fallas_visor)
    na = sum(f.get("averias", 0) for f in fallas_visor)
    ht = calcular_horas_totales(mes_plan, anio_plan)

    disp = round(((ht - hp) / ht) * 100, 1) if ht > 0 else 0.0
    mtbf = round(ht / na, 1) if na > 0 else None
    mttr = round(hp / na, 1) if na > 0 else 0.0
    mttf = round((ht - hp) / na, 1) if na > 0 else None

    pmp = round((pr / pp) * 100, 1) if pp > 0 else 0.0
    backlog = max(0, pp - pr)

    carga_total = pr + cr
    prev_pct = round((pr / carga_total) * 100) if carga_total > 0 else 0
    corr_pct = round((cr / carga_total) * 100) if carga_total > 0 else 0

    meta_mttr_num = float(meta_mttr) if meta_mttr and meta_mttr > 0 else 1.0
    score_prev = min(100, round((pr / pp) * 100)) if pp > 0 else 0
    score_mttr = min(100, round((meta_mttr_num / mttr) * 100)) if mttr > 0 else 100
    desempeno_general = round((score_prev + score_mttr) / 2)

    return {
        "pp": pp, "pr": pr, "cr": cr,
        "ht": ht, "hp": hp, "na": na,
        "disponibilidad": disp,
        "mtbf": mtbf,
        "mttr": mttr,
        "mttf": mttf,
        "pmp": pmp,
        "backlog": backlog,
        "prev_pct": prev_pct,
        "corr_pct": corr_pct,
        "score_prev": score_prev,
        "score_mttr": score_mttr,
        "desempeno_general": desempeno_general
    }