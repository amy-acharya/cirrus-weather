#Create list of states and months
states = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois",
    "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
    "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana",
    "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
    "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah",
    "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
]

months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
]

full_months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]

mapped_months = {}
for i in range(len(months)):
    mapped_months[full_months[i]] = months[i]

select_params = [
    'Maximum Temperature',
    'Minimum Temperature',
    'Average Temperature',
    'Wind Chill',
    'Heat Index',
    'Precipitation',
    'Snow Depth',
    'Wind Speed',
    'Wind Gust',
    'Visibility',
    'Cloud Cover',
    'Relative Humidity'
]

units = ['°F', '°F', '°F', '°F', '°F', 'in', 'in', 'mph', 'mph', 'mi', '%', '%']

mapped_params = {
    'Maximum Temperature': 'max_temp',
    'Minimum Temperature': 'min_temp',
    'Average Temperature': 'avg_temp',
    'Wind Chill': 'wind_chill',
    'Heat Index': 'heat_index',
    'Precipitation': 'precipitation',
    'Snow Depth': 'snow_depth',
    'Wind Speed': 'wind_speed',
    'Wind Gust': 'wind_gust',
    'Visibility': 'visibility',
    'Cloud Cover': 'cloud_cover',
    'Relative Humidity': 'relative_humidity'
}

param_units = {}
for i in range(len(select_params)):
    param_units[select_params[i]] = units[i]

url_headers = {
    'User-Agent': 'Mozilla/5.0 \
    (Macintosh; Intel Mac OS X 10_10_1) \
    AppleWebKit/537.36 (KHTML, like Gecko) \
    Chrome/39.0.2171.95 Safari/537.36'
}


#True if database is already populated
weather_data_collected = True
zipdata_collected = True
