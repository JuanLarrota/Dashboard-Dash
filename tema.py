import plotly.graph_objects as go
import plotly.io as pio

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_TENUE = "#898781"
CUADRICULA = "#e1e0d9"
EJE = "#c3c2b7"

AZUL = "#2a78d6"
NARANJA = "#eb6834"
AGUAMARINA = "#1baf7a"
AMARILLO = "#eda100"
ROJO = "#e34948"

FUENTE = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'

pio.templates["dashboard"] = go.layout.Template(
    layout=go.Layout(
        font={"family": FUENTE, "size": 12, "color": TINTA_SECUNDARIA},
        title={"font": {"size": 15, "color": TINTA}, "x": 0, "xanchor": "left", "pad": {"l": 4}},
        paper_bgcolor=SUPERFICIE,
        plot_bgcolor=SUPERFICIE,
        colorway=[AZUL, NARANJA, AGUAMARINA, AMARILLO, ROJO],
        margin={"l": 56, "r": 20, "t": 56, "b": 40},
        hovermode="x unified",
        hoverlabel={"bgcolor": "#ffffff", "bordercolor": CUADRICULA, "font": {"family": FUENTE, "color": TINTA}},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "traceorder": "normal",
            "font": {"color": TINTA_SECUNDARIA},
        },
        xaxis={
            "showgrid": False,
            "linecolor": EJE,
            "ticks": "outside",
            "tickcolor": EJE,
            "tickfont": {"color": TINTA_TENUE},
            "zeroline": False,
            "tickformat": "%H:%M",
            "hoverformat": "%d/%m %H:%M",
        },
        yaxis={
            "gridcolor": CUADRICULA,
            "gridwidth": 1,
            "zeroline": False,
            "rangemode": "tozero",
            "tickfont": {"color": TINTA_TENUE},
            "title": {"font": {"color": TINTA_TENUE, "size": 12}},
            "separatethousands": True,
        },
        separators=",.",
        bargap=0.35,
        barcornerradius=4,
    ),
    data={
        "scatter": [go.Scatter(line={"width": 2}, mode="lines")],
        "bar": [go.Bar(marker={"line": {"color": SUPERFICIE, "width": 1}})],
    },
)

pio.templates.default = "dashboard"

CONFIG_GRAFICA = {
    "displaylogo": False,
    "displayModeBar": "hover",
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
}
