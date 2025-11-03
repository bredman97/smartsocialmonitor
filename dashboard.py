from dash import Dash, dcc, ctx, exceptions, html, Input, Output, State, MATCH
from flask import Flask
from flask_caching import Cache
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from collections import OrderedDict
from backend import data_metrics

# initialize flask server, cache, stylesheets
server = Flask(__name__)
cache = Cache(server, config={'CACHE_TYPE':'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

app = Dash(__name__, server=server, external_stylesheets=[dbc.themes.CYBORG, dbc.icons.BOOTSTRAP])
load_figure_template('CYBORG')
app.title = "Privacy Dashboard"

# initialize controller
controller = data_metrics.Controller()

# helper function for accordion header colors
def grade_color(score):
    if score >= 75:
        return "success"
    elif score >= 40:
        return "warning"
    else:
        return "danger"

# makes sure data is aligned and correct
def helper(privacyspy_data, tosdr_data):
    if isinstance(privacyspy_data, list) and isinstance(tosdr_data, dict):
        privacyspy_hostnames = set(h.lower() for h in privacyspy_data[2]['hostnames'])
        tosdr_hostnames = set(h.lower() for h in tosdr_data['urls'])

        same_company = privacyspy_hostnames.intersection(tosdr_hostnames)

        if not same_company:
            points_component = html.Div('Please refine search...')
            rubric_component = html.Div('Please refine search...')
            privacy_score = None
            name = None
        else:
            points_component = make_points_accordion(tosdr_data)
            rubric_component = make_rubric_accordion(privacyspy_data)
            privacy_score = controller.overall_privacy_score(privacyspy_data, tosdr_data)
            name = tosdr_data['name']

    elif isinstance(privacyspy_data, list) ^ isinstance(tosdr_data, dict):
            points_component = make_points_accordion(tosdr_data)
            rubric_component = make_rubric_accordion(privacyspy_data)
            privacy_score = controller.overall_privacy_score(privacyspy_data, tosdr_data)
            name = tosdr_data['name'] if isinstance(tosdr_data,dict) else privacyspy_data[0]['company']
    else:
        points_component = html.Div('Search is not in Database...')
        rubric_component = html.Div('Search is not in Database...')
        privacy_score = None
        name = None
    
    return points_component, rubric_component, privacy_score, name

# creates accordion for tosdr data
def make_points_accordion(points_list):
    
    if not points_list:
        return html.P('Try a different search')
    
    if isinstance(points_list,str):
        return html.P(points_list)
    
    classifications = OrderedDict()

    for point in points_list['points']:
        classification = point['case']['classification'].capitalize()
        classifications.setdefault(classification, []).append(point)

    if 'Neutral' in classifications:
        classifications.move_to_end('Good')
        classifications.move_to_end('Neutral')

    if 'Bad' in classifications:
        classifications.move_to_end('Good')
        classifications.move_to_end('Neutral')
        classifications.move_to_end('Bad')

    if 'Blocker' in classifications:
        classifications['Critical'] = classifications.pop('Blocker')
        classifications.move_to_end('Critical')

    classification_columns = []

    for classification, points in classifications.items():
        first_points = points[:4]
        extra_points = points[4:]

        def make_point_item(point):
            statement = point['case']['title']
            description = point['case']['description']

            title_row = html.Div([
                html.Span(statement, className="points-statement"),
            ], className='points-title')

            body_content = html.Div([
                html.P(description, className="points-description"),
            ])

            return dbc.AccordionItem(body_content, title=title_row, id=f'{classification}')
        
        first_items = [make_point_item(p) for p in first_points]
        extra_items = [make_point_item(p) for p in extra_points]

        collapse_id = {'type': 'collapse', 'index': classification}
        button_id = {'type': 'toggle', 'index': classification}

        column_content = [
            html.H5(classification, className="text-center mb-2"),
            dbc.Accordion(first_items, start_collapsed=True, flush=True)
        ]

        if extra_items:
            column_content += [
                dbc.Collapse(
                    dbc.Accordion(extra_items, start_collapsed=True, flush=True),
                    id=collapse_id,
                    is_open=False,   # start collapsed
                ),
                dbc.Button(
                    "View more",
                    id=button_id,
                    color="link",
                    size="sm",
                    className="mt-1"
                )
            ]

        classification_columns.append(
            dbc.Col(column_content, width=12 // len(classifications) if len(classifications) <= 4 else 3)
        )

    return classification_columns

# make accordion for privacyspy data
def make_rubric_accordion(rubric_list):

    # check if rubric is available
    if isinstance(rubric_list,str) or not rubric_list:
        return html.P("No rubric data available.", className="text-muted")

    
    rubric_items = rubric_list[3:]
    categories = {}

    # Group questions by category
    for item in rubric_items:
        category = item.get("category")
        categories.setdefault(category, []).append(item)

    rubric_sections = []

    for category, items in categories.items():
        accordion_items = []

        for item in items:
            question = item.get("question", "")
            option = item.get("option", "")

            score = item['score'] / item['total_points'] * 100

            header_color = grade_color(score)

            citations = item.get("citations")[0] if item.get("citations") else ''

            title_row = html.Div([
                html.Span(question, className="rubric-question"),
            ], className='rubric-title')

            body_content = html.Div([
                html.P(f"Answer: {option}", className="rubric-answer"),
                html.Small(f"Citations: {citations}",
                           className="rubric-citation")
            ])

            accordion_items.append(
                dbc.AccordionItem(body_content, title=title_row, id=f'{header_color}')
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
            dbc.Col(html.Img(src="assets/SSM_Logo.png", id="logo"), md=2, sm=12),
            dbc.Col(
                html.Div(
                    [
                        html.Label("Search a Company...", id="search-label", className="bar-label"),
                        dbc.Input(placeholder='Type here...', id='search', type='search', className="bar-input"),
                        dbc.Button("Search", id='search-btn', color='primary', className="bar-button"),
                    ],
                    className="search-bar"
                ),
                md=4, sm=12
            ),
            dbc.Col(
                [
                    html.Div(
                        [
                            html.Label("Compare Companies...", id="compare-label", className="bar-label"),
                            dbc.Input(placeholder='Type here...', id='compare', type='search', className="bar-input"),
                            dbc.Button("Compare", id='compare-btn', color='info', className="bar-button"),
                        ],
                        className="compare-bar"
                    )
                ],
            id='compare-column',
            className='hidden',
            md=4, sm=12
        ),

             # Toggle Switch
            dbc.Col([
                html.Div(
                    dbc.Checklist(
                        options=[{"label": "compare", "value": 1}],
                        value=[],
                        id="switch-input",
                        switch=True,
                    ),
                id='header-switch',
                )
            ], md=2, sm=12),
        ], id="header"),

           
            html.Div(
            id="dashboard-content",

            # Placeholder layout for where components will appear
            children=[
                dbc.Row([
                    dbc.Col(
                        dcc.Loading(
                            type="circle",
                            color="#0d6efd",
                            children=dbc.Card(dbc.CardBody(
                                html.Div(id="gauge-chart-placeholder")
                            ))
                        ),
                        id='search-gauge-column'
                    ),
                    dbc.Col(
                        dcc.Loading(
                            type="circle",
                            color="#0d6efd",
                            delay_hide = 500 ,
                            children=dbc.Card(dbc.CardBody(
                                html.Div(id="comparison-gauge-placeholder")
                            ))
                        ),
                        id='comparison-gauge-column',
                    )
                ], className='hidden mb-3'),

                # Placeholder for points accordion
                dcc.Loading(
                    type="circle",
                    color="#0d6efd",
                    delay_hide = 500 ,
                    children=html.Div(id="points-placeholder"),
                ),

                # Placeholder for rubric accordion
                dcc.Loading(
                    type="circle",
                    color="#0d6efd",
                    delay_hide = 500 ,
                    children=html.Div(id="rubric-placeholder"),
                ),
            ]
        ),
       

        html.Footer([
                html.P("© 2025 Smart Social Monitor. All rights reserved."),
                html.P("Data Used From PrivacySpy and TOSDR")
            ], id="footer")

        ], fluid=True, id="main-container")

# ------- Callbacks -----------
@app.callback(
    Output("dashboard-content", "children"),
    Input('search-btn', 'n_clicks'),
    State("search", "value"),
)

# fills dashboard with content
def update_dashboard(search_click, site):

    if not search_click:
        site=site

    if site:
        site = site.replace(" ","")

    privacyspy_data = controller.get_privacyspy_info(site)
    tosdr_data = controller.get_tosdr_data(site)

    points_component, rubric_component, privacy_score, company_name = helper(privacyspy_data, tosdr_data)
    

    # search gauge chart
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=privacy_score,
        title={'text': f"{company_name.capitalize() if company_name else ''} Policy Score"},
        gauge={
            'axis': {'range': [0, 10], 'tickvals':[0,2,5,8,10], 'ticktext':['Critical','Bad', 'Average', 'Good','Excellent']}, 
            'bar': {'color': "black"},   # needle/bar color
            'steps': [
                {'range': [0, 2], 'color': 'red'},
                {'range': [2, 5], 'color': 'orange'},
                {'range': [5, 8], 'color': 'yellow'},
                {'range': [8, 10], 'color': 'green'}
            ],

        }
    )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    # ---------- Return dynamic dashboard content ----------
    dash_content = html.Div([
        
        # Stats and gauge chart row

        dbc.Row([
            dbc.Col([
                dcc.Loading(
                    type="circle",
                    color="#0d6efd",
                    delay_hide = 500 ,
                    children=dbc.Card(
                        dbc.CardBody(dcc.Graph(figure=fig, id="gauge-chart"))
                    )
                )
            ],id='search-gauge-column', className='mb-2'),

            dbc.Col([
                dcc.Loading(
                    type="circle",
                    color="#0d6efd",
                    delay_hide = 500 ,
                    children=dbc.Card(
                        dbc.CardBody(dcc.Graph(figure=fig, id="comparison-gauge-chart"))
                    )
                )
            ], id='comparison-gauge-column', width=6, className='hidden mb-2')
        ], className='mb-3'),

        # Points component section
        dcc.Loading(
            type="circle",
            color="#0d6efd",
            delay_hide = 500 ,
            children=dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        dbc.Row(points_component)
                    ])
                )
            ], className='mb-4')
        ),

        # Rubric component section
        dcc.Loading(
            type="circle",
            color="#0d6efd",
            delay_hide = 500 ,
            children=dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.Div(rubric_component, id="rubric-container")
                        ])
                    )
                ])
            ])
        )
    ])
    return dash_content

# handles view more/less logic in points accordion
@app.callback(
    Output({'type': 'collapse', 'index': MATCH}, 'is_open'),
    Output({'type': 'toggle', 'index': MATCH}, 'children'),
    Input({'type': 'toggle', 'index': MATCH}, 'n_clicks'),
    State({'type': 'collapse', 'index': MATCH}, 'is_open'),
    prevent_initial_call=True
)
def toggle_collapse(n_clicks, is_open):
    if not n_clicks:
        return is_open, "View more"
    new_state = not is_open
    new_label = "View less" if new_state else "View more"
    return new_state, new_label

# handles header switch for when compare data appears
@app.callback(
    Output('switch-input', 'value'),
    Output('compare-column', 'className'),
    Input('switch-input', 'value'),
    Input('search-btn', 'n_clicks'),
    prevent_initial_call=True
)

def toggle_or_reset_compare(switch, n_clicks):
    trigger = ctx.triggered_id

    if trigger == 'search-btn':
        return [0], 'hidden'

    if 1 in switch:
        return switch, ''
    else:
        return switch, 'hidden'

# handles logic for showing comparison gauge chart
@app.callback(
    Output("comparison-gauge-column", "children"),
    Output("comparison-gauge-column", "className"),
    Output("search-gauge-column", "width"),
    Input("compare-btn", "n_clicks"),
    State("compare", "value"),
    prevent_initial_call=True
)
def update_comparison_gauge(n_clicks, compare_site):
    if not n_clicks:
        raise exceptions.PreventUpdate
    
    if compare_site:
        compare_site = compare_site.replace(" ","")

    privacyspy_data = controller.get_privacyspy_info(compare_site)
    tosdr_data = controller.get_tosdr_data(compare_site)
    compare_score = helper(privacyspy_data, tosdr_data)[2]
    compare_name = helper(privacyspy_data, tosdr_data)[3]
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=compare_score,
        title={'text': f"{compare_name.capitalize() if compare_name else ''} Policy Score"},
        gauge={
            'axis': {'range': [0, 10], 'tickvals':[0,2,5,8,10], 'ticktext':['Critical','Bad', 'Average', 'Good','Excellent']},
            'bar': {'color': "black"},
            'steps': [
                {'range': [0, 2], 'color': 'red'},
                {'range': [2, 5], 'color': 'orange'},
                {'range': [5, 8], 'color': 'yellow'},
                {'range': [8, 10], 'color': 'green'}
            ],
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    return dbc.Card(dbc.CardBody(dcc.Graph(figure=fig, id="comparison-gauge-chart"))), '', 6


if __name__ == "__main__":
    app.run(debug=True)