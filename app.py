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
            html.P("The points are sorted using the following steps:"),
            html.Ol([
                html.Li("First, all points are sorted by their Y-axis values in descending order (from top to bottom)."),
                html.Li("Next, points are grouped together if their Y-axis values are within a specified tolerance. This means that points that are close to each other on the Y-axis will be considered part of the same group."),
                html.Li("Within each group, the points are then sorted by their X-axis values in ascending order (from left to right)."),
                html.Li("Finally, the sorted points are displayed in the list on the right side of the app, with visual separators (horizontal lines) between different groups."),
            ]),
            html.P("This sorting method ensures that points are grouped together when they are close on the Y-axis, and within each group, they are ordered by their X-axis values. This helps in visually organizing the points on the right side panel, making it easier to understand their relative positions."),
        ], width=12)
    ])
], fluid=True)

# Initialize points
points = {'x': [], 'y': [], 'names': []}
used_names = set()
removed_names = []

# Generate point names
def generate_point_name():
    if removed_names:
        return removed_names.pop(0)
    
    for char in 'abcdefghijklmnopqrstuvwxyz':
        name = char
        if name not in used_names:
            used_names.add(name)
            return name

    i = 1
    while True:
        for char in 'abcdefghijklmnopqrstuvwxyz':
            name = f'{char}{i}'
            if name not in used_names:
                used_names.add(name)
                return name
        i += 1

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

# Helper function to calculate the max y distance in a group
def max_y_distance(group):
    if not group:
        return 0
    y_values = [p[1] for p in group]
    return max(y_values) - min(y_values)

# Helper function to find the optimal grouping
def find_optimal_grouping(points, tolerance):
    points = sorted(points, key=lambda p: -p[1])  # Sort points by y descending
    groups = []
    current_group = []

    for point in points:
        if not current_group:
            current_group.append(point)
        else:
            max_y = max(current_group, key=lambda p: p[1])[1]
            min_y = min(current_group, key=lambda p: p[1])[1]
            current_max_distance = max_y - min_y
            new_max_distance = max_y_distance(current_group + [point])

            if new_max_distance < tolerance:
                current_group.append(point)
            else:
                # Try to split the group optimally
                new_group = [point]
                remaining_group = current_group[:]
                
                for p in current_group:
                    temp_group = new_group + [p]
                    temp_remaining_group = remaining_group[:]
                    temp_remaining_group.remove(p)
                    if max_y_distance(temp_group) < max_y_distance(temp_remaining_group + [p]):
                        new_group.append(p)
                        remaining_group.remove(p)
                
                groups.append(remaining_group)
                current_group = new_group

    if current_group:
        groups.append(current_group)
    
    return groups

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

        name = generate_point_name()
        points['x'].append(x_coord)
        points['y'].append(y_coord)
        points['names'].append(f'{name} ({x_coord:.2f}, {y_coord:.2f})')
    
    elif triggered_id == 'remove-point-button' and points['x']:
        removed_x = points['x'].pop()
        removed_y = points['y'].pop()
        removed_name = points['names'].pop()
        name = removed_name.split()[0]  # Get the name without coordinates
        used_names.remove(name)
        removed_names.append(name)

    # Prepare points data
    point_data = list(zip(points['x'], points['y'], points['names']))

    # Find optimal grouping
    tolerance = 1  # Tolerance for y-values to consider points close
    grouped_points = find_optimal_grouping(point_data, tolerance)

    # Sort each group by x-axis
    grouped_points = [sorted(group, key=lambda p: p[0]) for group in grouped_points]

    # Flatten the list
    sorted_within_tolerance = [point for group in grouped_points for point in group]

    # Create a list of HTML elements with visual separation for groups
    points_list = []
    for i, group in enumerate(grouped_points):
        if i > 0:
            points_list.append(html.Hr())  # Add a divider between groups
        for j, (x, y, name) in enumerate(group):
            points_list.append(html.Div(f'{name}: ({x:.2f}, {y:.2f})', style={'backgroundColor': '#f0f0f0' if j % 2 == 0 else '#ffffff'}))

    return create_plot(), points_list

if __name__ == '__main__':
    app.run_server(debug=True)

# Add this line at the end to make the `server` available for Gunicorn
server = app.server
