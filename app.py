import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import Class
import io


start_date = "2024-12-2"
end_date = "2024-12-15" #date.today() + timedelta(days=2)
features_list = ["PJM nyis DA", "NYIS pjm DA", "PJMnyis shock X forecast", "NYISpjm shock X forecast", "Meteologica MISO Load forcast", "Meteologica NYISO Load forcast"]

actual = Class.Ops()
actual.update_data_features(features_list)
print(actual.data_features)
actual.update_date_range(start_date, end_date)
print(actual.start_date)
print(actual.end_date)
actual.update_df()
actual.create_feature([{"Feature": "PJM nyis DA"},{"Feature": "NYIS pjm DA", "Operation": "-"}], False, "NYIS to PJM spread")
actual.create_feature([{"Feature": "PJMnyis shock X forecast"},{"Feature": "NYISpjm shock X forecast", "Operation": "-"}], False, "NYIS to PJM shock spread")
actual.create_feature([{"Feature": "NYIS pjm DA"},{"Feature": "PJM nyis DA", "Operation": "-"}], False, "PJM to NYIS spread")
actual.create_feature([{"Feature": "NYISpjm shock X forecast"},{"Feature": "PJMnyis shock X forecast", "Operation": "-"}], False, "PJM to NYIS shock spread")
# Assuming you have your dataframe 'df' already loaded

app = Dash(__name__)
app.layout = html.Div([
    
    dcc.Graph(id='how-shocky'),
    dcc.Graph(id='model-spread'),
    html.Button("Download Data", id="btn-download"),
    dcc.Download(id="download-dataframe-csv"),
    html.Table([
        # Header row (Hours 1-24)
        html.Tr([html.Th('Hour')] + [html.Th(str(i)) for i in range(0, 24)]),
        
        # NYIS pjm DA row
        html.Tr(
            [html.Td('NYIS pjm DA')] + 
            [html.Td(id=f'nyis-da-{i}') for i in range(0, 24)]
        ),
        
        # NYISpjm shock X forecast row
        html.Tr(
            [html.Td('NYISpjm shock X forecast')] + 
            [html.Td(id=f'nyis-shock-{i}') for i in range(0, 24)]
        ),
        
        # User input row
        html.Tr(
            [html.Td('User Predictions')] + 
            [html.Td(dcc.Input(
                id=f'user-input-{i}',
                type='number',
                style={'width': '50px'}
            )) for i in range(0, 24)]
        )
    ], style={
        'border-collapse': 'collapse',
        'width': '100%',
        'textAlign': 'center'
    })
])

@app.callback(
    Output('how-shocky', 'figure'),
    Input('how-shocky', 'id'),
)
def update_how_shocky(id):
    fig = go.Figure()

    # Add traces for each column
    fig.add_trace(
        go.Scatter(
            x=actual.df.index, 
            y=actual.df["NYIS pjm DA"], 
            mode='lines', 
            name="regular forcast",
            line_shape='hv'  # This creates the step effect
        )
    )

    fig.add_trace(
        go.Scatter(
            x=actual.df.index, 
            y=actual.df["NYISpjm shock X forecast"], 
            mode='lines', 
            name="NYISpjm shock x forcast",
            line_shape='hv'  # This creates the step effect
        )
    )

    colors = []
    for i, row in actual.df.iterrows():
        if row["NYISpjm shock X forecast"] > row["NYIS pjm DA"]:
            colors.append('rgba(0, 255, 0, 0.7)')  # Bright green
        elif row["NYIS pjm DA"] > row["NYISpjm shock X forecast"]:
            colors.append('rgba(255, 0, 0, 0.7)')  # Bright red
        else:
            colors.append('rgba(0, 0, 0, 0)')  # Transparent

    for i in range(len(actual.df)-1):
        fig.add_trace(
            go.Scatter(
                x=[actual.df.index[i], actual.df.index[i], actual.df.index[i+1], actual.df.index[i+1]],
                y=[actual.df["NYIS pjm DA"].iloc[i], actual.df["NYISpjm shock X forecast"].iloc[i], 
                   actual.df["NYISpjm shock X forecast"].iloc[i], actual.df["NYIS pjm DA"].iloc[i]],
                fill='toself',
                fillcolor=colors[i],
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False,
                hoverinfo='none'
            )
        )
    fig.update_layout(
        title=f'How Shocky will NYIS be?',
        xaxis_title='Datetime',
        yaxis_title='Price',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis_range=[actual.df.index.min(), actual.df.index.max()]
    )
    return fig

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-download", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    # Get the last day of data
    last_day = actual.df.index.max().date()
    df_last_day = actual.df[actual.df.index.date == last_day]
    
    # Select and rename columns
    df_to_download = df_last_day[["NYIS pjm DA", "NYISpjm shock X forecast"]].reset_index()
    df_to_download = df_to_download.rename(columns={"datetime": "Datetime (HB)"})
    
    return dcc.send_data_frame(df_to_download.to_csv, f"nyis_pjm_data_{last_day}.csv", index=False)

@app.callback(
    Output('model-spread', 'figure'),
    Input('model-spread', 'id'),
)
def update_shock_models_predicted_spread(id):
    fig = go.Figure()


    # Add traces for each column
    fig.add_trace(
        go.Scatter(
            x=actual.df.index, 
            y=actual.df["PJM to NYIS shock spread"], 
            mode='lines', 
            name="PJM to NYIS Shock models predicted spread",
            line_shape='hv'  # This creates the step effect
        )
    )

    # Create color conditions
    colors = []
    for i, row in actual.df.iterrows():
        if row["PJM to NYIS shock spread"] > 0:
            colors.append('rgba(0, 255, 0, 0.7)')  # Bright green
        elif row["PJM to NYIS shock spread"] < 0:
            colors.append('rgba(255, 0, 0, 0.7)')  # Bright red
        else:
            colors.append('rgba(0, 0, 0, 0)')  # Transparent

    for i in range(len(actual.df) - 1):
        fig.add_trace(
            go.Scatter(
                x=[actual.df.index[i], actual.df.index[i], actual.df.index[i+1], actual.df.index[i+1]],
                y=[0, actual.df["PJM to NYIS shock spread"].iloc[i], actual.df["PJM to NYIS shock spread"].iloc[i], 0],
                fill='toself',
                fillcolor=colors[i],
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False,
                hoverinfo='none'
            )
        )

    # Update layout
    fig.update_layout(
        title=f'PJM to NYIS Shock models predicted spread',
        xaxis_title='Datetime',
        yaxis_title='Spread',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis_range=[actual.df.index.min(), actual.df.index.max()]
    )

    return fig


@app.callback(
    [Output(f'nyis-da-{i}', 'children') for i in range(0, 24)] +
    [Output(f'nyis-shock-{i}', 'children') for i in range(0, 24)],
    Input('how-shocky', 'id')
)
def update_table(id):
    last_day = actual.df.index.max().date()
    df_last_day = actual.df[actual.df.index.date == last_day]
    
    da_values = df_last_day['NYIS pjm DA'].round(2).tolist()
    shock_values = df_last_day['NYISpjm shock X forecast'].round(2).tolist()
    
    return da_values + shock_values




if __name__ == '__main__':
    app.run_server(debug=True)
