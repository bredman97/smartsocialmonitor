from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from backend import data_metrics
from backend import prepare_json
import time



app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG, dbc.icons.BOOTSTRAP])
load_figure_template('CYBORG')
app.title = "Privacy Dashboard"
controller = data_metrics.Controller()
df = controller.sites
site_options =  controller.list_of_domains()

# Rubric Accordion

def grade_color(score):
    if score >= 75:
        return "success"
    elif score >= 40:
        return "warning"
    else:
        return "danger"

def make_rubric_accordion(rubric_list):
    # Guard clause: if not enough data
    if len(rubric_list) < 3:
        return html.P("No rubric data available.", className="text-muted")

    # Group questions by category
    rubric_items = rubric_list[2:]
    categories = {}

    for item in rubric_items:
        category = item.get("category")
        categories.setdefault(category, []).append(item)

    rubric_sections = []

    for category, items in categories.items():
        accordion_items = []

        for item in items:
            question = item.get("question", "")
            option = item.get("option", "")
            total_points = item.get("total_points", 0)
            citations = item.get("citations")[0] if item.get("citations") else ''
            score = item.get("score", 0)
            percent = (score / total_points * 100) if total_points else 0

            # Badge color logic 
            badge_color = grade_color(percent)

            title_row = html.Div([
                html.Span(question, className="rubric-question"),
                html.Span(f"{score}/{total_points}",
                          className=f"badge bg-{badge_color}")
            ], className='rubric-title')

            body_content = html.Div([
                html.P(f"Answer: {option}", className="rubric-answer"),
                html.Small(f"Citations: {citations}",
                           className="rubric-citation")
            ])

            accordion_items.append(
                dbc.AccordionItem(body_content, title=title_row)
            )

        rubric_sections.append(
            html.Div([
                html.H5(category, className="rubric-category"),
                dbc.Accordion(accordion_items, start_collapsed=True,
                                always_open=False, flush=True)
            ])
        )

    return html.Div(rubric_sections, id = 'rubric-sections')

# -------------- Layout --------------

app.layout = dbc.Container([

 # ------------------ HEADER ------------------
    dbc.Row([
        dbc.Row([
            dbc.Col(html.Img(src="assets/SSM_Logo.png", id="logo"), md=2, sm=12),
            dbc.Col(html.H1("Privacy Dashboard", id="title"), md=6, sm=12),
            dbc.Col([
                html.Label("Select Website...", id="dropdown-label"),
                dcc.Dropdown(id="site-dropdown", options=site_options,
                             value='google.com', clearable=False)
            ], md=4, sm=12)
        ], id="header"),
    ]),

        dcc.Loading(
            id="loading-overlay",
            type="circle",          
            color="#0d6efd",        
            fullscreen=False,
            overlay_style={"visibility":"visible", "filter": "blur(3px)"},       
            children=[html.Div(id="dashboard-content")]  
        ),

        html.Footer([
                html.P("© 2025 Smart Social Monitor. All rights reserved."),
                html.P("Data Used From PrivacySpy and WhoTracksMe")
            ], id="footer")

        ], fluid=True, id="main-container")

# ================================
# Callbacks
# ================================
@app.callback(
    Output("dashboard-content", "children"),
    Input("site-dropdown", "value")
)
def update_dashboard(site):
    time.sleep(1)
    site_data = prepare_json.get_policy_info(site)
    
    # Stats cards
    stats = [
        ("Privacy Score", f'{controller.get_privacy_score(site)} / 10', 'Privacy score derived from multiple values normalized and weighted'),
        ("Total Trackers", controller.get_tracker_total(site), 'Total trackers seen on the website'),
        ("Avg # of Companies Found", controller.get_avg_companies(site), 'Average amount of distinct companies on the site'),
        ("Avg Trackers on Site", controller.get_avg_trackers_on_site(site), 'Average amount of trackers seen at any given time on the site'),
        ("Percent of Requests Tracking", f'{controller.get_percent_request_tracking(site)} %', 'Percentage of all requests that are third-party tracking on the site')
    ]
    stats_cards = [
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H6(label, className="stat-label"),
                    html.H4(value, className="stat-value"),

                    html.Div([
                        html.I(
                            className='bi bi-info-circle-fill',
                            id=f'{label}',
                        ), 
                        dbc.Popover(
                            info,
                            target=f'{label}',
                            placement='bottom',
                            body=True,
                            trigger='hover'
                        )
                    ], className='info-icon')
                ])
            ), md=2, sm=6, xs=10
        ) for label, value, info in stats
    ]

    if len(site_data) == 1:
        
        company_card = 'N/A'
        policy_card = 'N/A'
        rubric_component = make_rubric_accordion(site_data)
    else:
        badge_color = grade_color(float(site_data[1]['policy_score'])*10)
        
        company_card = f"{site_data[0]['company']}"
        policy_card = html.H1(f"{site_data[1]['policy_score']} / 10", className=f'policy-badge badge bg-{badge_color}')
        rubric_component = make_rubric_accordion(site_data)

    # Charts
    pie_fig = px.pie(controller.get_category_numbers(site), 
                    names="category", 
                    values="num_trackers",
                    hole=0.4, 
                    title=f"Tracker Categories for {site}",
                    labels= {'category': 'Tracker Category',"num_trackers": "Trackers in Category"})
    bar_fig = px.bar(controller.get_sites_trackers_df(site), 
                    x="tracker", 
                    y="site_reach_top10k", 
                    title=f"Tracker Bar Graph for {site}", 
                    labels= {'tracker': 'Tracker Names',"site_reach_top10k": "Presence on Top 10k Sites" })
    
    pie_fig.update_traces(hoverinfo='label+value', textfont_color= 'white')

    pie_fig.update_layout(
        hovermode="x",
        font_color = 'white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
        
    bar_fig.update_layout(
        font_color = 'white',  
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # ---------- Return dynamic dashboard content ----------
    dash_content = html.Div([
        # Stats Row
        dbc.Row(stats_cards, id="stats-row"),

        # Main Content
        dbc.Row([
            # LEFT COLUMN
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.Div([
                            html.H1(company_card, id="company-name"),
                            html.Div(policy_card, id="policy-score")
                        ], id="policy-header"),
                        html.Div(rubric_component, id="rubric-container")
                    ]))
            ], md=6, sm=12),

            # RIGHT COLUMN
            dbc.Col([
                dbc.Card(dbc.CardBody(dcc.Graph(figure=pie_fig, id="pie-chart"))),
                dbc.Card(dbc.CardBody(dcc.Graph(figure=bar_fig, id="bar-chart")))
            ], md=6, sm=12)
        ])
    ])
    return dash_content

if __name__ == "__main__":
    app.run(debug=True)