import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import Class
import io

start_date = "2024-12-2"
end_date = "2024-12-15"
features_list = ["PJM nyis DA", "NYIS pjm DA", "PJMnyis shock X forecast", "NYISpjm shock X forecast", "Meteologica MISO Load forcast", "Meteologica NYISO Load forcast"]

actual = Class.Ops()
actual.update_data_features(features_list)
actual.update_date_range(start_date, end_date)
actual.update_df()
actual.create_feature([{"Feature": "PJM nyis DA"},{"Feature": "NYIS pjm DA", "Operation": "-"}], False, "NYIS to PJM spread")
actual.create_feature([{"Feature": "PJMnyis shock X forecast"},{"Feature": "NYISpjm shock X forecast", "Operation": "-"}], False, "NYIS to PJM shock spread")
actual.create_feature([{"Feature": "NYIS pjm DA"},{"Feature": "PJM nyis DA", "Operation": "-"}], False, "PJM to NYIS spread")
actual.create_feature([{"Feature": "NYISpjm shock X forecast"},{"Feature": "PJMnyis shock X forecast", "Operation": "-"}], False, "PJM to NYIS shock spread")

app = Dash(__name__)
app.layout = html.Div([
    dcc.Checklist(
        id='view-selector',
        options=[{'label': 'Show Last Day Only', 'value': 'last_day'}],
        value=[]
    ),
    dcc.Graph(id='how-shocky'),
    dcc.Graph(id='model-spread'),
    html.Div(id='download-and-table', children=[
        html.Button("Download Data", id="btn-download"),
        dcc.Download(id="download-dataframe-csv"),
        html.Table([
            html.Tr([html.Th('Hour')] + [html.Th(str(i)) for i in range(0, 24)]),
            html.Tr(
                [html.Td('NYIS pjm DA')] + 
                [html.Td(id=f'nyis-da-{i}') for i in range(0, 24)]
            ),
            html.Tr(
                [html.Td('NYISpjm shock X forecast')] + 
                [html.Td(id=f'nyis-shock-{i}') for i in range(0, 24)]
            ),
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
    ]),
])

@app.callback(
    [Output('how-shocky', 'figure'),
     Output('model-spread', 'figure')],
    [Input('view-selector', 'value')]
)
def update_graphs(view_selector):
    show_last_day = 'last_day' in view_selector
    
    if show_last_day:
        last_day = actual.df.index.max().date()
        df = actual.df[actual.df.index.date == last_day]
    else:
        df = actual.df

    fig1 = go.Figure()
    fig2 = go.Figure()

    fig1.add_trace(go.Scatter(x=df.index, y=df["NYIS pjm DA"], mode='lines', name="regular forecast", line_shape='hv'))
    fig1.add_trace(go.Scatter(x=df.index, y=df["NYISpjm shock X forecast"], mode='lines', name="NYISpjm shock x forecast", line_shape='hv'))

    colors = []
    for i, row in df.iterrows():
        if row["NYISpjm shock X forecast"] > row["NYIS pjm DA"]:
            colors.append('rgba(0, 255, 0, 0.7)')
        elif row["NYIS pjm DA"] > row["NYISpjm shock X forecast"]:
            colors.append('rgba(255, 0, 0, 0.7)')
        else:
            colors.append('rgba(0, 0, 0, 0)')

    for i in range(len(df)-1):
        fig1.add_trace(go.Scatter(
            x=[df.index[i], df.index[i], df.index[i+1], df.index[i+1]],
            y=[df["NYIS pjm DA"].iloc[i], df["NYISpjm shock X forecast"].iloc[i], 
               df["NYISpjm shock X forecast"].iloc[i], df["NYIS pjm DA"].iloc[i]],
            fill='toself', fillcolor=colors[i], line=dict(color='rgba(255,255,255,0)'),
            showlegend=False, hoverinfo='none'
        ))

    fig1.update_layout(
        title='How Shocky will NYIS be?',
        xaxis_title='Datetime',
        yaxis_title='Price',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis_range=[df.index.min(), df.index.max()]
    )

    fig2.add_trace(go.Scatter(x=df.index, y=df["PJM to NYIS shock spread"], mode='lines', 
                              name="PJM to NYIS Shock models predicted spread", line_shape='hv'))

    colors = []
    for i, row in df.iterrows():
        if row["PJM to NYIS shock spread"] > 0:
            colors.append('rgba(0, 255, 0, 0.7)')
        elif row["PJM to NYIS shock spread"] < 0:
            colors.append('rgba(255, 0, 0, 0.7)')
        else:
            colors.append('rgba(0, 0, 0, 0)')

    for i in range(len(df) - 1):
        fig2.add_trace(go.Scatter(
            x=[df.index[i], df.index[i], df.index[i+1], df.index[i+1]],
            y=[0, df["PJM to NYIS shock spread"].iloc[i], 
               df["PJM to NYIS shock spread"].iloc[i], 0],
            fill='toself', fillcolor=colors[i], line=dict(color='rgba(255,255,255,0)'),
            showlegend=False, hoverinfo='none'
        ))

    fig2.update_layout(
        title='PJM to NYIS Shock models predicted spread',
        xaxis_title='Datetime',
        yaxis_title='Spread',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis_range=[df.index.min(), df.index.max()]
    )

    return fig1, fig2

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-download", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    last_day = actual.df.index.max().date()
    df_last_day = actual.df[actual.df.index.date == last_day]
    df_to_download = df_last_day[["NYIS pjm DA", "NYISpjm shock X forecast"]].reset_index()
    df_to_download = df_to_download.rename(columns={"datetime": "Datetime (HB)"})
    return dcc.send_data_frame(df_to_download.to_csv, f"nyis_pjm_data_{last_day}.csv", index=False)

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

@app.callback(
    Output('download-and-table', 'style'),
    [Input('view-selector', 'value')]
)
def toggle_download_and_table(view_selector):
    if 'last_day' in view_selector:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

if __name__ == '__main__':
    app.run_server(debug=True)
