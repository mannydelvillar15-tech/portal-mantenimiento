import io
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, LineChart, Reference


def plot_solicitudes_mensuales(df_mensual, anio):
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Creadas', x=df_mensual['Mes'], y=df_mensual['Creadas'], marker_color='#60a5fa', text=df_mensual['Creadas'], textposition='outside'))
    fig.add_trace(go.Bar(name='Resueltas', x=df_mensual['Mes'], y=df_mensual['Resueltas'], marker_color='#34d399', text=df_mensual['Resueltas'], textposition='outside'))
    fig.add_trace(go.Bar(name='Pendientes', x=df_mensual['Mes'], y=df_mensual['Pendientes'], marker_color='#f87171', text=df_mensual['Pendientes'], textposition='outside'))
    fig.update_layout(
        title=f"Tendencia Mensual ({anio})",
        barmode='group',
        height=380,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def plot_solicitudes_area(df_area, titulo_periodo):
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Creadas', x=df_area['Área'], y=df_area['Creadas'], marker_color='#60a5fa', text=df_area['Creadas'], textposition='outside'))
    fig.add_trace(go.Bar(name='Resueltas', x=df_area['Área'], y=df_area['Resueltas'], marker_color='#34d399', text=df_area['Resueltas'], textposition='outside'))
    fig.add_trace(go.Bar(name='Pendientes', x=df_area['Área'], y=df_area['Pendientes'], marker_color='#f87171', text=df_area['Pendientes'], textposition='outside'))
    fig.update_layout(
        title=f"Distribución por Áreas ({titulo_periodo})",
        barmode='group',
        height=380,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def plot_donut_mantenimiento(prev_pct, corr_pct):
    fig = go.Figure(data=[go.Pie(
        labels=['Preventivos Realizados', 'Correctivos Realizados'],
        values=[prev_pct, corr_pct] if (prev_pct + corr_pct) > 0 else [1, 0],
        hole=0.65,
        marker=dict(colors=['#3b82f6', '#f97316'] if (prev_pct + corr_pct) > 0 else ['#e2e8f0', '#e2e8f0']),
        textinfo='none'
    )])
    fig.update_layout(
        showlegend=True,
        height=280,
        margin=dict(l=10, r=10, t=10, b=10),
        annotations=[dict(text=f"<b>{prev_pct}%</b> Prev<br><b>{corr_pct}%</b> Corr", x=0.5, y=0.5, font_size=14, showarrow=False)]
    )
    return fig


def plot_pmp_global(df_pmp, anio):
    colors = [
        '#e2e8f0' if prog == 0 else ('#10b981' if pct >= 90 else ('#fbbf24' if pct >= 70 else '#f87171'))
        for prog, pct in zip(df_pmp['Prev. Prog.'], df_pmp['Cumplimiento (%)'])
    ]
    text_labels = [
        'N/A' if prog == 0 else f"{pct}%"
        for prog, pct in zip(df_pmp['Prev. Prog.'], df_pmp['Cumplimiento (%)'])
    ]
    fig = go.Figure(data=[go.Bar(
        x=df_pmp['Mes'],
        y=df_pmp['Cumplimiento (%)'],
        marker_color=colors,
        text=text_labels,
        textposition='outside',
        hovertext=[f"Realizado: {r} / {p}" for r, p in zip(df_pmp['Prev. Real.'], df_pmp['Prev. Prog.'])]
    )])
    fig.update_layout(
        title=f"Tendencia Global de Cumplimiento PMP ({anio})",
        yaxis=dict(range=[0, 115], title="% Cumplimiento"),
        height=380,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def plot_pmp_lineas_areas(df_lineas, anio):
    fig = px.line(
        df_lineas,
        x='Mes',
        y=[c for c in df_lineas.columns if c != 'Mes'],
        markers=True,
        title=f"Evolución de Cumplimiento por Área ({anio})"
    )
    fig.update_layout(
        yaxis=dict(range=[0, 105], title="% Cumplimiento"),
        height=420,
        legend_title_text="Áreas (clic para ocultar/mostrar)"
    )
    return fig


def build_excel_buffer(headers, rows, sheet_name="Reporte", chart_type=None, chart_title=""):
    """Genera un archivo .xlsx estilizado en memoria, con gráfico nativo opcional."""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]

    header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    ws.append(headers)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    for r_idx, row_data in enumerate(rows, start=2):
        ws.append(row_data)
        for cell in ws[r_idx]:
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="left", vertical="center")

    # Autoajuste de columnas
    for col in ws.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 3, 12), 55)

    # Insertar gráfico nativo de Excel si se solicita
    if chart_type and len(rows) > 0:
        chart = BarChart() if chart_type == "bar" else LineChart()
        chart.title = chart_title
        chart.style = 10
        chart.width = 18
        chart.height = 10

        data_ref = Reference(ws, min_col=2, min_row=1, max_col=len(headers), max_row=len(rows) + 1)
        cats_ref = Reference(ws, min_col=1, min_row=2, max_row=len(rows) + 1)
        chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(cats_ref)
        ws.add_chart(chart, f"{chr(65 + len(headers) + 1)}2")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf