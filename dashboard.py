from dash import Dash, dcc, ctx, html, Input, Output, State, MATCH
from flask import Flask
from backend import cache_setup
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from collections import OrderedDict
from backend.data_metrics import Controller

# initialize flask server, cache, stylesheets
server = Flask(__name__)
cache = cache_setup.cache
cache.init_app(server, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT':86400})

app = Dash(__name__, server=server, external_stylesheets=[dbc.themes.CYBORG+ "?v=1", dbc.icons.BOOTSTRAP])
load_figure_template('CYBORG')
app.title = "Smart Social Monitor"

# initialize controller
controller = Controller()

sites = controller.get_site_list()

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
        points_component = html.Div('Please Choose A Site...')
        rubric_component = html.Div('Please Choose A Site...')
        privacy_score = None
        name = ""
    
    return points_component, rubric_component, privacy_score, name

# creates accordion for tosdr data
def make_points_accordion(points_list):
    
    if not points_list:
        return html.P('No Points Available...')
    
    if isinstance(points_list,str):
        return html.P(points_list)
    
    order = ["Good", "Tolerable", "Bad", "Abysmal"]

    classifications = {}

    for point in points_list['points']:

        classification = point['case']['classification'].capitalize()

        if classification == 'Blocker':
            classification = 'Abysmal'
        if classification == 'Neutral':
            classification = 'Tolerable'

        classifications.setdefault(classification, []).append(point)

    # Reorder into an OrderedDict according to `order`
    ordered_classifications = OrderedDict(
        sorted(
            classifications.items(),
            key=lambda kv: order.index(kv[0]) if kv[0] in order else len(order)
        )
    )

    classification_columns = []

    #map icons to respective classifications
    icon_map = {
        'Good': 'bi bi-emoji-smile',
        'Tolerable': 'bi bi-emoji-neutral',
        'Bad': 'bi bi-emoji-frown',
        'Abysmal': 'bi bi-emoji-dizzy'
    }

    for classification, points in ordered_classifications.items():

        emoji = icon_map[classification]

        first_points = points[:4]
        extra_points = points[4:]

        def make_point_item(point):
            statement = point['case']['title']
            description = point['case']['description'] if point['case']['description'] else 'No description available currently'

            title_row = html.Div([
                html.Span(statement, className="points-statement"),
            ], className='points-title')

            body_content = html.Div([
                html.P(description, className="points-description"),
            ])

            return dbc.AccordionItem(body_content, title=title_row, id=f'{classification}')
        
        #split points for increased UX 
        first_items = [make_point_item(p) for p in first_points]
        extra_items = [make_point_item(p) for p in extra_points]

        collapse_id = {'type': 'collapse', 'index': classification}
        button_id = {'type': 'toggle', 'index': classification}

        column_content = [
            html.Div([
                html.H5(classification, className="mb-2"),
                html.I(className=f'{emoji}'),
            ], id='classification-title'),
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
            dbc.Col(column_content, xs=12,sm=12, md= 12 // len(classifications) if classifications else 3)
        )

    return classification_columns

# make accordion for privacyspy data
def make_rubric_accordion(rubric_list):

    # check if rubric is available
    if isinstance(rubric_list,str) or not rubric_list:
        return html.P("No rubric data available.", className="text-muted")

    
    rubric_items = rubric_list[1:]
    categories = {}

    # Group questions by category
    for item in rubric_items:
        category = item.get("category")
        if category == 'Handling':
            category = 'How Is Your Information Handled?'
        
        if category == 'Transparency':
            category = 'How Transparent Are They?'

        if category == 'Collection':
            category = 'How Do They Collect Information?'

        categories.setdefault(category, []).append(item)

    rubric_sections = []

    for category, items in categories.items():
        accordion_items = []

        for item in items:
            question = item.get("question", "")
            option = item.get("option", "")

            score = item['score'] / item['total_points'] * 100

            header_color = grade_color(score)

            citations = item.get("citations")[0] if item.get("citations") else 'No citation available currently'

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
                html.Div([
                    html.H5(category, className="rubric-category"),
                    html.I(className='bi bi-search'),
                ], id='category-title'),
                dbc.Accordion(accordion_items, start_collapsed=True,
                                always_open=False, flush=True, className='mb-2')
            ])
        )

    return html.Div(rubric_sections, id = 'rubric-sections')

# helper function for displaying policy links
def policy_links(policies):

    if not policies:
        return None

    policy_links=[]
        
    for i, (name, link) in enumerate(policies.items()):
        spacer = " | " if i < (len(policies.items()) - 1) else ""
        policy_links.append(html.A(name+spacer, href=link, target="_blank"))
    
    first_links = policy_links[:3]
    extra_links = policy_links[3:]

    links_content = [
        html.Div("Policy Links:",className='fw-bold mb-2'),
        html.Div(first_links)
    ]
    
    if extra_links:
        links_content += [
            dbc.Collapse(
                html.Div(extra_links, className='mb-2'),
                id={'type':'collapse', 'index': 'policy-link'},
                is_open=False
            ),
            dbc.Button(
                "View more",
                id={'type':'toggle', 'index': 'policy-link'},
                color="link",
                size="sm",
            )
        ]
    
                                
    return html.Div(links_content, id='policy-links')


     
# -------------- Layout --------------

app.layout = dbc.Container([

 # ------------------ HEADER ------------------
        dbc.Row([
            dbc.Col(html.Img(src="assets/SSM_Logo.png", id="logo"), md=2, sm=12),
            dbc.Col(
                html.Div(
                    [
                        dbc.Label('Site Selection: ', html_for='site-dropdown', className='mt-2'),
                        dcc.Dropdown(
                            id='site-dropdown',
                            options = sites,
                            placeholder="Type a site..",
                            clearable=False,
                        )
                    ],
                    className="search-bar"
                ),
                md=4, sm=12, xs=12
            ),
            dbc.Col(
                html.Div(
                    [
                        dbc.Label('Comparison Selection: ', html_for='comparison-dropdown', className='mt-2'),
                        dcc.Dropdown(
                            id='comparison-dropdown',
                            options = [],
                            placeholder="Type a site..",
                            disabled = True,
                            clearable=False
                        )
                    ],
                    className = 'compare-bar'
                ),
                id='compare-column',
                className="hidden",
                md=4, sm=12, xs=12
            ),

             # Toggle Switch
            dbc.Col([
                html.Div(
                    dbc.Checklist(
                        options=[{"label": "Compare", "value": 1}],
                        value=[],
                        id="switch-input",
                        switch=True,
                    ),
                id='header-switch',
                )
            ], md=2, sm=12),
        ], id="header"),

    # ------------------ Main Content ------------------
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
                        id='search-gauge-column',
                        
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
                html.P("© Smart Social Monitor. All Rights Reserved."),
                html.P([
                    "Developed by: ",
                    html.A("Brandon", href="https://www.linkedin.com/in/brandon-redman-209732232/", target="_blank"),
                    " | ",
                    html.A("Munim", href="https://www.linkedin.com/in/munimmelaque/", target="_blank"),
                    " | ",
                    html.A("Ayman", href="https://www.linkedin.com/in/ayman-najmuddin-406519284/", target="_blank"),
                    " | ",
                    html.A("Ragib", href="https://www.linkedin.com/in/ragib-ehsan", target="_blank"),
                ]),
                html.P([
                    "Data Used From ",
                    html.A("PrivacySpy", href="https://privacyspy.org", target="_blank"),
                    " and ",
                    html.A("TOSDR", href="https://tosdr.org", target="_blank")
                ])
            ], id="footer")

        ], fluid=True, id="main-container")

# ------- Callbacks -----------
@app.callback(
    Output("dashboard-content", "children"),
    Input('site-dropdown', 'value'),
)

# fills dashboard with content
def update_dashboard(site):

    privacyspy_data = controller.get_privacyspy_info(site)
    tosdr_data = controller.get_tosdr_data(site)

    points_component, rubric_component, privacy_score, company_name = helper(privacyspy_data, tosdr_data)

    image = controller.get_site_image(privacyspy_data, tosdr_data)
    policies = controller.get_policy_urls(privacyspy_data, tosdr_data)

    # search gauge chart
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=privacy_score,
        title={'text': f"{company_name.title()} Policy Score"},
        gauge={
            'axis': {'range': [0, 10], 'tickvals':[0,2,5,8,10], 'ticktext':['Abysmal','Bad', 'Tolerable', 'Good','Excellent']}, 
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
        font=dict(color = 'white'),
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
                        dbc.CardBody([
                            html.Div(html.Div(html.Img(src=image, alt="") if image else None, id='site-logo'), id='site-logo-div'),
                            dcc.Graph(figure=fig, id="gauge-chart"),
                            policy_links(policies)
                        ])
                    )
                )
            ],id='search-gauge-column', className='mb-2'),

            dbc.Col([], id='comparison-gauge-column', width=6, className='hidden mb-2')
        ], className='mb-3'),

        # Points component section
        dcc.Loading(
            type="circle",
            color="#0d6efd",
            delay_hide = 500 ,
            children=dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.Div(
                            dbc.Row(points_component), 
                            id='points-container')
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
    ], className='mb-4')
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
    Input('site-dropdown', 'value'),
    prevent_initial_call=True
)

def toggle_or_reset_compare(switch, n_clicks):
    trigger = ctx.triggered_id

    if trigger == 'site-dropdown':
        return [0], 'hidden'

    if 1 in switch:
        return switch, ''
    else:
        return switch, 'hidden'

# handles logic for compare dropdown list
# enables the compare dropdown only when a site is selected
@app.callback(
    Output('comparison-dropdown', 'options'),
    Output('comparison-dropdown', 'disabled'),
    Input('site-dropdown', 'value'),
    prevent_initial_call=True
)
def update_comparison_dropdown(site):
    if site:
        comparison_sites = [s for s in sites if s != site]
        return comparison_sites, False
    else:
        return sites, True




# handles logic for showing comparison gauge chart
@app.callback(
    Output("comparison-gauge-column", "children"),
    Output("comparison-gauge-column", "className"),
    Output("search-gauge-column", "width"),
    Input("comparison-dropdown", "value"),
    prevent_initial_call=True
)
def update_comparison_gauge(compare_site):
    
    privacyspy_data = controller.get_privacyspy_info(compare_site)
    tosdr_data = controller.get_tosdr_data(compare_site)
    compare_score = helper(privacyspy_data, tosdr_data)[2]
    compare_name = helper(privacyspy_data, tosdr_data)[3]
    compare_image = controller.get_site_image(privacyspy_data, tosdr_data)
    compare_policies = controller.get_policy_urls(privacyspy_data, tosdr_data)
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=compare_score,
        title={'text': f"{compare_name.title()} Policy Score"},
        gauge={
            'axis': {'range': [0, 10], 'tickvals':[0,2,5,8,10], 'ticktext':['Abysmal','Bad', 'Tolerable', 'Good','Excellent']},
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
        font=dict(color = 'white'),
    )

    return dcc.Loading(
            type="circle",
            color="#0d6efd",
            delay_hide = 500 ,
            children=dbc.Card(
                dbc.CardBody([
                    html.Div(html.Div(html.Img(src=compare_image, alt='') if compare_image else None, id='site-logo'), id='site-logo-div'),
                    dcc.Graph(figure=fig, id="comparison-gauge-chart"),
                    policy_links(compare_policies)
                ]),
                color='secondary'
        )), '', 6


if __name__ == "__main__":
    app.run(debug=True)