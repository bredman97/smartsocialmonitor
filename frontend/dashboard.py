import dash
from dash import dcc, html, Input, Output
import plotly.express as px
from backend.data_metrics import Controller

# Initialize Controller and data
controller = Controller()
df = controller.sites
site_options =  controller.list_of_domains()

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Website Privacy Dashboard"

# Dark theme colors
colors = {
    "background": "#121212",
    "card": "#1E1E1E",
    "text": "#E0E0E0",
    "accent": "#00BFFF",
}

# App Layout
app.layout = html.Div(
    style={
        "padding": "20px",
        "backgroundColor": colors["background"],
        "color": colors["text"],
        "fontFamily": "Segoe UI, sans-serif",
    },
    children=[
        html.H1(
            "Website Privacy Metrics Dashboard",
            style={"textAlign": "center", "color": colors["accent"]},
        ),

        html.Div(
            [
                html.Label("Select Site:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="site-dropdown",
                    options=site_options,
                    value='google.com',
                    clearable=False,
                    style={"width": "50%", "margin": "auto", "color": "#000"},
                ),
            ],
            style={"textAlign": "center","margin": "auto", "marginBottom": "30px"},
        ),

        html.Div(
            [
                html.Label("Filter by Total Trackers:", style={"fontWeight": "bold"}),
                dcc.Slider(
                    id="tracker-slider",
                    min=int(df["total_trackers"].min()),
                    max=int(df["total_trackers"].max()),
                    value=int(df["total_trackers"].max()),
                    step=1,
                    marks={
                        int(df["total_trackers"].min()): "Min",
                        int(df["total_trackers"].max()): "Max",
                    },
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ],
            style={"marginBottom": "40px"},
        ),

        html.Div(
            id="metrics-grid",
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(200px, 1fr))",
                "gap": "20px",
                "justifyItems": "center",
            },
        ),

        html.Div(
            dcc.Graph(id="scatter-graph"),
            style={"marginTop": "40px"},
        ),
        html.Div(
            dcc.Graph(id="pie-chart"),
            style={"marginTop": "40px"},
        ),
        html.Div(
            dcc.Graph(id="bar-chart"),
            style={"marginTop": "40px"},
        ),
    ],
)


# --- CALLBACKS ---

@app.callback(
    Output("metrics-grid", "children"),
    Input("site-dropdown", "value"),
)
def update_metrics(selected_site):
    """Update metric grid cards when a site is selected."""
    metrics = {
        "Privacy Score": controller.get_privacy_score(selected_site),
        "Total Trackers": controller.get_tracker_total(selected_site),
        "AVG Companies On Site": controller.get_avg_companies(selected_site),
        "AVG Trackers On Site": controller.get_avg_trackers_on_site(selected_site),
        "Requests Tracking": controller.get_percent_request_tracking(selected_site),
        "Referer Leaked": controller.get_referer_leaked(selected_site),
    }

    cards = []
    for metric, value in metrics.items():
        cards.append(
            html.Div(
                style={
                    "backgroundColor": colors["card"],
                    "borderRadius": "12px",
                    "padding": "15px",
                    "textAlign": "center",
                    "width": "180px",
                    "boxShadow": "2px 2px 8px rgba(0,0,0,0.4)",
                },
                children=[
                    html.H4(metric, style={"marginBottom": "8px", "color": colors["accent"]}),
                    html.H2(
                        f"{value:.2f}" if isinstance(value, float) else str(value),
                        style={"color": colors["text"], "margin": 0},
                    ),
                ],
            )
        )

    return cards


@app.callback(
    Output("scatter-graph", "figure"),
    Output("pie-chart", "figure"),
    Output("bar-chart", "figure"),
    Input("tracker-slider", "value"),
    Input("site-dropdown", "value"),
)
def update_scatter(max_trackers, selected_site):
    """Update scatter plot based on tracker slider."""
    filtered_df = df[df["total_trackers"] <= max_trackers]

    fig = px.scatter(
        filtered_df,
        x="total_trackers",
        y="privacy_score",
        hover_data=["site"],
        title=f"Total Trackers vs Privacy Score (≤ {max_trackers} trackers)",
        template="plotly_dark",
        color="privacy_score",
        color_continuous_scale=px.colors.sequential.Bluered,
    )

    fig.update_layout(
        plot_bgcolor=colors["background"],
        paper_bgcolor=colors["background"],
        font_color=colors["text"],
    )
    fig2 = px.pie(
        controller.get_category_numbers(selected_site),
        names="category",
        values="num_trackers",
        hover_data=["percent"],
        title=f"Tracker Categories for {selected_site}",
        template="plotly_dark",
        color_discrete_sequence=px.colors.sequential.Bluered_r
    )
    fig2.update_layout(
        plot_bgcolor=colors["background"],
        paper_bgcolor=colors["background"],
        font_color=colors["text"],
    )
    fig3 = px.bar(
        controller.get_site_df(selected_site),
        x = 'tracker',
        y = 'site_reach_top10k',
        text_auto='.2s',
        template="plotly_dark",
        barmode='group'
    )
    fig3.update_layout(
        plot_bgcolor=colors["background"],
        paper_bgcolor=colors["background"],
        font_color=colors["text"],
    )

    return fig, fig2, fig3


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
