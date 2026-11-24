from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

from conexion import consultar

ZONA_HORARIA = "America/Bogota"

VENTANAS = {
    "1h": {"horas": 1, "bucket": "1min"},
    "3h": {"horas": 3, "bucket": "5min"},
    "24h": {"horas": 24, "bucket": "30min"},
}

REFRESCOS = {"10s": 10_000, "60s": 60_000}

servicios = consultar("SELECT DISTINCT svc FROM logs ORDER BY svc")["svc"].tolist()
opciones_servicio = [{"label": "Todos", "value": "todos"}] + [
    {"label": s, "value": s} for s in servicios
]

ESTILO_TARJETA = {
    "flex": "1",
    "minWidth": "140px",
    "padding": "12px 16px",
    "border": "1px solid #ddd",
    "borderRadius": "8px",
    "background": "#fafafa",
}


def tarjeta(titulo, id_valor):
    return html.Div([
        html.Div(titulo, style={"fontSize": "13px", "color": "#666"}),
        html.Div("—", id=id_valor, style={"fontSize": "26px", "fontWeight": "bold"}),
    ], style=ESTILO_TARJETA)


app = Dash(__name__)

app.layout = html.Div([
    html.H1("Dashboard de logs"),

    html.Div([
        html.Div([
            html.Label("Servicio"),
            dcc.Dropdown(
                id="filtro-servicio",
                options=opciones_servicio,
                value="todos",
                clearable=False,
                style={"width": "220px"},
            ),
        ]),
        html.Div([
            html.Label("Ventana"),
            dcc.RadioItems(
                id="filtro-ventana",
                options=list(VENTANAS),
                value="1h",
                inline=True,
            ),
        ]),
        html.Div([
            html.Label("Actualizar cada"),
            dcc.RadioItems(
                id="filtro-refresco",
                options=list(REFRESCOS),
                value="10s",
                inline=True,
            ),
        ]),
        html.Div(id="ultima-actualizacion", style={"marginLeft": "auto", "color": "#666"}),
    ], style={"display": "flex", "gap": "30px", "alignItems": "flex-end", "flexWrap": "wrap"}),

    dcc.Interval(id="intervalo", interval=REFRESCOS["10s"]),

    html.Div([
        tarjeta("Response time promedio", "kpi-promedio"),
        tarjeta("Throughput (RPM)", "kpi-rpm"),
        tarjeta("Errores 4xx", "kpi-4xx"),
        tarjeta("Errores 5xx", "kpi-5xx"),
        tarjeta("p95 response time", "kpi-p95"),
        tarjeta("p99 response time", "kpi-p99"),
    ], style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "margin": "20px 0"}),

    dcc.Graph(id="grafica-response-time"),
    dcc.Graph(id="grafica-throughput"),
    dcc.Graph(id="grafica-errores"),
], style={"fontFamily": "sans-serif", "padding": "0 20px"})


def cargar_logs(servicio, horas):
    datos = consultar(
        """
        SELECT ts, status_code, duration
        FROM logs
        WHERE ts >= now() - make_interval(hours => :horas)
          AND (:svc = 'todos' OR svc = :svc)
        """,
        {"horas": horas, "svc": servicio},
    )
    datos["ts"] = pd.to_datetime(datos["ts"], utc=True).dt.tz_convert(ZONA_HORARIA)
    return datos


def figura_vacia(titulo):
    figura = go.Figure()
    figura.update_layout(
        title=titulo,
        annotations=[{
            "text": "Sin datos en esta ventana",
            "showarrow": False,
            "xref": "paper",
            "yref": "paper",
            "x": 0.5,
            "y": 0.5,
        }],
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    return figura


def formato_ms(valor):
    return f"{valor:,.0f} ms"


@app.callback(
    Output("intervalo", "interval"),
    Input("filtro-refresco", "value"),
)
def cambiar_refresco(refresco):
    return REFRESCOS[refresco]


@app.callback(
    Output("kpi-promedio", "children"),
    Output("kpi-rpm", "children"),
    Output("kpi-4xx", "children"),
    Output("kpi-5xx", "children"),
    Output("kpi-p95", "children"),
    Output("kpi-p99", "children"),
    Output("grafica-response-time", "figure"),
    Output("grafica-throughput", "figure"),
    Output("grafica-errores", "figure"),
    Output("ultima-actualizacion", "children"),
    Input("filtro-servicio", "value"),
    Input("filtro-ventana", "value"),
    Input("intervalo", "n_intervals"),
)
def actualizar(servicio, ventana, _):
    config = VENTANAS[ventana]
    datos = cargar_logs(servicio, config["horas"])
    hora = f"Última actualización: {datetime.now().strftime('%H:%M:%S')}"

    titulos = ("Response time", "Throughput (RPM)", "Errores 4xx y 5xx")

    if datos.empty:
        return ("—", "0", "0", "0", "—", "—",
                *[figura_vacia(t) for t in titulos], hora)

    es_4xx = datos["status_code"].between(400, 499)
    es_5xx = datos["status_code"].between(500, 599)
    minutos_ventana = config["horas"] * 60

    kpis = (
        formato_ms(datos["duration"].mean()),
        f"{len(datos) / minutos_ventana:,.1f}",
        f"{es_4xx.sum():,}",
        f"{es_5xx.sum():,}",
        formato_ms(datos["duration"].quantile(0.95)),
        formato_ms(datos["duration"].quantile(0.99)),
    )

    datos = datos.assign(es_4xx=es_4xx, es_5xx=es_5xx).set_index("ts")
    bucket = config["bucket"]
    minutos_bucket = pd.Timedelta(bucket).total_seconds() / 60
    agrupado = datos.resample(bucket)

    tiempos = pd.DataFrame({
        "promedio": agrupado["duration"].mean(),
        "p95": agrupado["duration"].quantile(0.95),
        "p99": agrupado["duration"].quantile(0.99),
    })
    figura_tiempos = go.Figure([
        go.Scatter(x=tiempos.index, y=tiempos["promedio"], name="Promedio", mode="lines"),
        go.Scatter(x=tiempos.index, y=tiempos["p95"], name="p95", mode="lines"),
        go.Scatter(x=tiempos.index, y=tiempos["p99"], name="p99", mode="lines"),
    ])
    figura_tiempos.update_layout(title="Response time", yaxis_title="ms")

    rpm = agrupado.size() / minutos_bucket
    figura_rpm = go.Figure(go.Scatter(x=rpm.index, y=rpm, name="RPM", mode="lines"))
    figura_rpm.update_layout(title="Throughput (RPM)", yaxis_title="peticiones / min")

    errores = pd.DataFrame({
        "4xx": agrupado["es_4xx"].sum(),
        "5xx": agrupado["es_5xx"].sum(),
    })
    figura_errores = go.Figure([
        go.Bar(x=errores.index, y=errores["4xx"], name="4xx", marker_color="#f0a030"),
        go.Bar(x=errores.index, y=errores["5xx"], name="5xx", marker_color="#d04040"),
    ])
    figura_errores.update_layout(title="Errores 4xx y 5xx", barmode="stack", yaxis_title="errores")

    return (*kpis, figura_tiempos, figura_rpm, figura_errores, hora)


if __name__ == "__main__":
    app.run(debug=True)
