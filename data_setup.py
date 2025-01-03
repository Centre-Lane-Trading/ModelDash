import Class
from datetime import date, time, datetime, timedelta


start_date = "2024-12-15"
end_date = "2024-12-31"
features_list = [
    "PJM nyis DA",
    "NYIS pjm DA",
    "PJMnyis shock X forecast",
    "NYISpjm shock X forecast",
    "PJM nyis DA regular prediction",
    "NYIS pjm DA regular prediction",
]

actual = Class.Ops()
actual.update_data_features(features_list)
actual.update_date_range(start_date, end_date)
actual.update_df()
actual.create_feature(
    [
        {"Feature": "NYISpjm shock X forecast"},
        {"Feature": "PJMnyis shock X forecast", "Operation": "-"},
    ],
    False,
    "PJM to NYIS shock predicted spread",
)

actual.create_feature(
    [
        {"Feature": "NYIS pjm DA regular prediction"},
        {"Feature": "PJM nyis DA regular prediction", "Operation": "-"},
    ],
    False,
    "PJM to NYIS regular predicted spread",
)

print(actual.df)


# Predict toggle: 
#   When this toggle is off it should show the layout described below with all the data in the dataframe
#   but the tables should be hidden.
#   When the toggle is on it should only show the last day of data in the dataframe with the exact layout described below.

# App layout:
#   Graph one should show the regular forcast(NYIS pjm DA regular prediction), the shock forcast(NYISpjm shock X forecast), and the actuals(NYIS pjm DA) for NYIS pjm.
#       When the shock forcast is greater than the regualr forcast highlight the area bettweent the two forcasts in green,
#       when the regualr forcast is greater than the shock forcast highlight the area in red.
#       Then the table assosiated with this graph should be right underneath this graph.
#       Row one of the table should be the hours (0-23), row two is the shock forcast, and row three is the regular forcast

#   Graph two should be the same as Graph one but for PJM nyis (including the assosiated table)

#   Graph three should be the shock model predicted spread and graph four should be the regular model predicted spread
#       When the spread is greater than 0 highlight the area between the x-axis and the line in green, when less than 0 highlight in red
