import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
import numpy as np

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout of the app
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='interactive-graph')
        ], width=8),
        dbc.Col([
            html.H4("Points List (sorted by y-axis):"),
            html.Div(id='points-list')
        ], width=4)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Input(id="x-coord", type="number", placeholder="X coordinate", style={"margin-right": "10px"}),
            dbc.Input(id="y-coord", type="number", placeholder="Y coordinate", style={"margin-right": "10px"}),
            dbc.Button("Add Point", id="add-point-button", color="primary", className="mr-1"),
            dbc.Button("Remove Point", id="remove-point-button", color="danger", className="mr-1")
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.H4("How to Use the App"),
            html.P("1. Enter the X and Y coordinates in the input fields and click 'Add Point' to add a point at the specified coordinates."),
            html.P("2. If the coordinates are left empty and 'Add Point' is clicked, a point will be added at a random location."),
            html.P("3. Click 'Remove Point' to remove the last added point."),
            html.P("4. The list on the right shows the points sorted by their Y-axis value from top to bottom. Points close to each other on the Y-axis are further sorted from left to right."),
            html.H4("Sorting Explanation"),
            html.P("The points are first sorted by their Y-axis values in descending order (from top to bottom). For points that are close to each other on the Y-axis (within a tolerance), they are further sorted by their X-axis values in ascending order (left to right)."),
        ], width=12)
    ])
], fluid=True)

# Initialize points
points = {'x': [], 'y': [], 'names': []}
point_names = iter("abcdefghijklmnopqrstuvwxyz")

# Create an empty plot
def create_plot():
    return go.Figure(
        data=[go.Scatter(
            x=points['x'], 
            y=points['y'], 
            mode='markers+text', 
            text=points['names'], 
            textposition='top center', 
            marker=dict(size=10, color='red')
        )],
        layout=go.Layout(
            xaxis=dict(range=[0, 10], title='X-axis'),
            yaxis=dict(range=[0, 10], title='Y-axis'),
            title="Interactive Graph with Movable Points"
        )
    )

# Callback to update the graph and points list when buttons are clicked
@app.callback(
    Output('interactive-graph', 'figure'),
    Output('points-list', 'children'),
    Input('add-point-button', 'n_clicks'),
    Input('remove-point-button', 'n_clicks'),
    State('x-coord', 'value'),
    State('y-coord', 'value')
)
def update_graph_and_list(add_clicks, remove_clicks, x_coord, y_coord):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'add-point-button':
        if x_coord is None or y_coord is None:
            x_coord = np.random.uniform(0, 10)
            y_coord = np.random.uniform(0, 10)

        try:
            name = next(point_names)
        except StopIteration:
            raise dash.exceptions.PreventUpdate
        
        points['x'].append(x_coord)
        points['y'].append(y_coord)
        points['names'].append(f'{name} ({x_coord:.2f}, {y_coord:.2f})')
    
    elif triggered_id == 'remove-point-button' and points['x']:
        points['x'].pop()
        points['y'].pop()
        points['names'].pop()

    # Sort points by y (descending), then by x for points that are close in y
    tolerance = 1  # tolerance for y-values to consider points close
    sorted_points = sorted(zip(points['x'], points['y'], points['names']), key=lambda p: (-p[1], p[0]))

    sorted_within_tolerance = []
    i = 0
    while i < len(sorted_points):
        group = [sorted_points[i]]
        while i + 1 < len(sorted_points) and abs(sorted_points[i + 1][1] - sorted_points[i][1]) < tolerance:
            i += 1
            group.append(sorted_points[i])
        sorted_within_tolerance.extend(sorted(group, key=lambda p: p[0]))
        i += 1

    points_list = [html.Div(f'{name}: ({x:.2f}, {y:.2f})') for x, y, name in sorted_within_tolerance]

    return create_plot(), points_list

if __name__ == '__main__':
    app.run_server(debug=True)

# Add this line at the end to make the `server` available for Gunicorn
server = app.server
