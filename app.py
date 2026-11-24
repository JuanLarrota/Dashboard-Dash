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

    dcc.Graph(id="grafica-response-time"),
], style={"fontFamily": "sans-serif", "padding": "0 20px"})


def cargar_logs(servicio, horas):
    datos = consultar(
        """
        SELECT ts, duration
        FROM logs
        WHERE ts >= now() - make_interval(hours => :horas)
          AND (:svc = 'todos' OR svc = :svc)
        """,
        {"horas": horas, "svc": servicio},
    )
    datos["ts"] = pd.to_datetime(datos["ts"], utc=True).dt.tz_convert(ZONA_HORARIA)
    return datos


@app.callback(
    Output("intervalo", "interval"),
    Input("filtro-refresco", "value"),
)
def cambiar_refresco(refresco):
    return REFRESCOS[refresco]


@app.callback(
    Output("grafica-response-time", "figure"),
    Output("ultima-actualizacion", "children"),
    Input("filtro-servicio", "value"),
    Input("filtro-ventana", "value"),
    Input("intervalo", "n_intervals"),
)
def actualizar(servicio, ventana, _):
    config = VENTANAS[ventana]
    datos = cargar_logs(servicio, config["horas"])
    hora = f"Última actualización: {datetime.now().strftime('%H:%M:%S')}"

    figura = go.Figure()
    figura.update_layout(title="Response time promedio", yaxis_title="ms")

    if datos.empty:
        figura.add_annotation(
            text="Sin datos en esta ventana",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )
        return figura, hora

    promedio = datos.set_index("ts").resample(config["bucket"])["duration"].mean()
    figura.add_trace(go.Scatter(x=promedio.index, y=promedio, name="Promedio", mode="lines"))

    return figura, hora


if __name__ == "__main__":
    app.run(debug=True)
