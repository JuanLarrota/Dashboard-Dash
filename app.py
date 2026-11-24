from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

import tema
from conexion import consultar

ZONA_HORARIA = "America/Bogota"

VENTANAS = {
    "1h": {"horas": 1, "bucket": "1min", "texto": "última hora"},
    "3h": {"horas": 3, "bucket": "5min", "texto": "últimas 3 horas"},
    "24h": {"horas": 24, "bucket": "30min", "texto": "últimas 24 horas"},
}

REFRESCOS = {"10s": 10_000, "60s": 60_000}

servicios = consultar("SELECT DISTINCT svc FROM logs ORDER BY svc")["svc"].tolist()
opciones_servicio = [{"label": "Todos los servicios", "value": "todos"}] + [
    {"label": s, "value": s} for s in servicios
]


def tarjeta(titulo, id_kpi, color):
    return html.Div([
        html.Div([
            html.Span(className="kpi-muestra", style={"background": color}),
            titulo,
        ], className="kpi-titulo"),
        html.Div("—", id=f"{id_kpi}-valor", className="kpi-valor"),
        html.Div("", id=f"{id_kpi}-detalle", className="kpi-detalle"),
    ], id=id_kpi, className="kpi")


def filtro(titulo, componente):
    return html.Div([html.Span(titulo, className="filtro-titulo"), componente], className="filtro")


def grafica(id_grafica, ancha=False):
    return html.Div(
        dcc.Graph(id=id_grafica, config=tema.CONFIG_GRAFICA, style={"height": "340px"}),
        className="tarjeta-grafica ancha" if ancha else "tarjeta-grafica",
    )


app = Dash(__name__, title="Dashboard de logs", update_title=None)

app.layout = html.Div([
    html.Header([
        html.Div([
            html.H1("Dashboard de logs"),
            html.P("Response time, throughput y errores por servicio"),
        ]),
        html.Div(id="ultima-actualizacion", className="estado-vivo"),
    ], className="cabecera"),

    html.Div([
        filtro("Servicio", dcc.Dropdown(
            id="filtro-servicio",
            options=opciones_servicio,
            value="todos",
            clearable=False,
            searchable=False,
            className="selector-servicio",
        )),
        filtro("Ventana", dcc.RadioItems(
            id="filtro-ventana",
            options=list(VENTANAS),
            value="1h",
            inline=True,
            className="segmentado",
        )),
        filtro("Actualizar cada", dcc.RadioItems(
            id="filtro-refresco",
            options=list(REFRESCOS),
            value="10s",
            inline=True,
            className="segmentado",
        )),
    ], className="barra-filtros"),

    dcc.Interval(id="intervalo", interval=REFRESCOS["10s"]),

    dcc.Loading(
        html.Div([
            html.Div([
                tarjeta("Response time promedio", "kpi-promedio", tema.AZUL),
                tarjeta("Throughput", "kpi-rpm", tema.AZUL),
                tarjeta("Errores 4xx", "kpi-4xx", tema.AMARILLO),
                tarjeta("Errores 5xx", "kpi-5xx", tema.ROJO),
                tarjeta("p95 response time", "kpi-p95", tema.NARANJA),
                tarjeta("p99 response time", "kpi-p99", tema.AGUAMARINA),
            ], className="kpis"),

            html.Div([
                grafica("grafica-response-time", ancha=True),
                grafica("grafica-throughput"),
                grafica("grafica-errores"),
            ], className="graficas"),
        ]),
        type="dot",
        color=tema.AZUL,
        delay_show=600,
        overlay_style={"visibility": "visible", "opacity": 0.55},
    ),
], className="contenedor")


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
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    figura.add_annotation(
        text="Sin datos en esta ventana",
        showarrow=False,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        font={"size": 14, "color": tema.TINTA_TENUE},
    )
    return figura


def formato_ms(valor):
    return f"{valor:,.0f} ms".replace(",", ".")


def formato_entero(valor):
    return f"{valor:,}".replace(",", ".")


def porcentaje(parte, total):
    return f"{parte / total * 100:.1f}".replace(".", ",") + " % de las peticiones"


@app.callback(
    Output("intervalo", "interval"),
    Input("filtro-refresco", "value"),
)
def cambiar_refresco(refresco):
    return REFRESCOS[refresco]


@app.callback(
    Output("kpi-promedio-valor", "children"),
    Output("kpi-promedio-detalle", "children"),
    Output("kpi-rpm-valor", "children"),
    Output("kpi-rpm-detalle", "children"),
    Output("kpi-4xx-valor", "children"),
    Output("kpi-4xx-detalle", "children"),
    Output("kpi-5xx-valor", "children"),
    Output("kpi-5xx-detalle", "children"),
    Output("kpi-5xx", "className"),
    Output("kpi-p95-valor", "children"),
    Output("kpi-p95-detalle", "children"),
    Output("kpi-p99-valor", "children"),
    Output("kpi-p99-detalle", "children"),
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
    hora = f"En vivo · actualizado {pd.Timestamp.now(tz=ZONA_HORARIA).strftime('%H:%M:%S')}"
    contexto = f"{config['texto']} · {'todos' if servicio == 'todos' else servicio}"

    titulos = ("Response time", "Throughput (RPM)", "Errores 4xx y 5xx")

    if datos.empty:
        return (
            "—", contexto,
            "0", "peticiones por minuto",
            "0", "sin peticiones",
            "0", "sin peticiones", "kpi",
            "—", contexto,
            "—", contexto,
            *[figura_vacia(t) for t in titulos],
            hora,
        )

    total = len(datos)
    es_4xx = datos["status_code"].between(400, 499)
    es_5xx = datos["status_code"].between(500, 599)
    total_4xx = int(es_4xx.sum())
    total_5xx = int(es_5xx.sum())
    rpm_ventana = total / (config["horas"] * 60)

    bucket = config["bucket"]
    minutos_bucket = pd.Timedelta(bucket).total_seconds() / 60
    ahora = pd.Timestamp.now(tz=ZONA_HORARIA)
    inicio = (ahora - pd.Timedelta(hours=config["horas"])).ceil(bucket)
    rango = pd.date_range(inicio, ahora.floor(bucket), freq=bucket)

    datos = datos.assign(es_4xx=es_4xx, es_5xx=es_5xx).set_index("ts")
    agrupado = datos[datos.index >= inicio].resample(bucket)

    tiempos = pd.DataFrame({
        "promedio": agrupado["duration"].mean(),
        "p95": agrupado["duration"].quantile(0.95),
        "p99": agrupado["duration"].quantile(0.99),
    }).reindex(rango)
    figura_tiempos = go.Figure([
        go.Scatter(x=tiempos.index, y=tiempos["promedio"], name="Promedio",
                   line={"color": tema.AZUL}, hovertemplate="%{y:,.0f} ms"),
        go.Scatter(x=tiempos.index, y=tiempos["p95"], name="p95",
                   line={"color": tema.NARANJA}, hovertemplate="%{y:,.0f} ms"),
        go.Scatter(x=tiempos.index, y=tiempos["p99"], name="p99",
                   line={"color": tema.AGUAMARINA}, hovertemplate="%{y:,.0f} ms"),
    ])
    figura_tiempos.update_layout(title="Response time", yaxis_title="ms")

    rpm = agrupado.size().reindex(rango, fill_value=0) / minutos_bucket
    figura_rpm = go.Figure(go.Scatter(
        x=rpm.index,
        y=rpm,
        name="RPM",
        line={"color": tema.AZUL},
        fill="tozeroy",
        fillcolor="rgba(42, 120, 214, 0.10)",
        hovertemplate="%{y:,.1f} peticiones/min",
    ))
    figura_rpm.update_layout(title="Throughput (RPM)", yaxis_title="peticiones / min", showlegend=False)

    errores = pd.DataFrame({
        "4xx": agrupado["es_4xx"].sum(),
        "5xx": agrupado["es_5xx"].sum(),
    }).reindex(rango, fill_value=0)
    figura_errores = go.Figure([
        go.Bar(x=errores.index, y=errores["4xx"], name="4xx",
               marker_color=tema.AMARILLO, hovertemplate="%{y}"),
        go.Bar(x=errores.index, y=errores["5xx"], name="5xx",
               marker_color=tema.ROJO, hovertemplate="%{y}"),
    ])
    figura_errores.update_layout(title="Errores 4xx y 5xx", barmode="stack", yaxis_title="errores")

    return (
        formato_ms(datos["duration"].mean()), contexto,
        f"{rpm_ventana:,.1f}".replace(".", ","), "peticiones por minuto",
        formato_entero(total_4xx), porcentaje(total_4xx, total),
        formato_entero(total_5xx), porcentaje(total_5xx, total),
        "kpi critico" if total_5xx > 0 else "kpi",
        formato_ms(datos["duration"].quantile(0.95)), contexto,
        formato_ms(datos["duration"].quantile(0.99)), contexto,
        figura_tiempos,
        figura_rpm,
        figura_errores,
        hora,
    )


if __name__ == "__main__":
    app.run(debug=True)
