from flask import Flask, request, jsonify
from pytrends.request import TrendReq
import pandas as pd
import matplotlib.pyplot as plt
from prophet import Prophet
from io import BytesIO
from scipy import stats
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
pytrends = TrendReq()

# Helper Functions
def fetch_interest_data(keyword, timeframe, location=''):
    """Fetch interest over time data from Google Trends."""
    if isinstance(keyword, str):
        keyword = [keyword]
    keyword = list(set(keyword))
    print(keyword)
    pytrends.build_payload(keyword, timeframe=timeframe, geo=location)
    data = pytrends.interest_over_time().reset_index()
    if 'isPartial' in data.columns:
        data.drop(columns=['isPartial'], inplace=True)

    return data if not data.empty else None

def prepare_data(data):
    """Prepare data for Prophet by handling outliers and creating lag features."""
    original_data = data.copy()
    data.rename(columns={'date': 'ds', data.columns[1]: 'y'}, inplace=True)
    data = data[(abs(stats.zscore(data['y'])) < 3)].dropna()  # Remove outliers
    for lag in range(1, 8):
        data[f'lag_{lag}'] = data['y'].shift(lag)
    return original_data, data.dropna()

def fit_prophet_model(data):
    """Fit the Prophet model using the prepared data."""
    model = Prophet()
    for lag in range(1, 8):
        model.add_regressor(f'lag_{lag}')
    model.fit(data)
    return model

# Create future DataFrame and make predictions
def make_predictions(model, data, periods):
    future = model.make_future_dataframe(periods=periods)

    # Prepare future DataFrame with lagged values
    for i in range(len(future)):
        if i < len(data):
            for lag in range(1, 8):
                future.loc[i, f'lag_{lag}'] = data['y'].iloc[i - lag] if i - lag >= 0 else None

    # Fill remaining lag values with the last known value
    for lag in range(1, 8):
        last_known_value = data['y'].iloc[-1] if len(data) > 0 else 0
        future[f'lag_{lag}'].fillna(last_known_value, inplace=True)

    forecast = model.predict(future)
    return forecast


def calculate_growth_rate(data, keyword):
    """Calculate the compound growth rate and indicate trend direction."""
    beginning_value = data[keyword].iloc[0]
    ending_value = data[keyword].iloc[-1]
    n = len(data) - 1

    if beginning_value > 0:
        cgr = (ending_value / beginning_value) ** (1 / n) - 1
        indication = "increasing trend" if cgr > 0 else "decreasing trend"
        return {"compound_growth_rate": f"{cgr:.2%}", "indication": f"The interest for '{keyword}' shows an {indication}."}
    return {"compound_growth_rate": None, "indication": "Beginning value is zero; cannot calculate growth rate."}


def determine_forecast_period(timeframe):
    """Determine the forecast period in days based on the timeframe input."""
    match = re.match(r'.*?(\d+)-([y|m|w|d])', timeframe)
    if match:
        duration, unit = int(match.group(1)), match.group(2)
        return {'y': 365, 'm': 30, 'w': 7, 'd': duration}.get(unit, 30)
    return 30  # Default to a month if the format is unclear

@app.route('/api/forecast_data', methods=['POST'])
def forecast_data():
    data = request.get_json()
    keyword = data.get('keyword')
    timeframe = data.get('timeframe', 'today 5-y')
    location = data.get('location', '')

    if not keyword:
        return jsonify({"error": "Please provide a keyword."}), 400

    interest_data = fetch_interest_data(keyword, timeframe, location)
    if interest_data is None:
        return jsonify({"error": "No data found for the specified keyword, timeframe, and location."}), 404

    original_data, processed_data = prepare_data(interest_data)
    model = fit_prophet_model(processed_data)

    forecast_period = determine_forecast_period(timeframe)
    forecast = make_predictions(model, processed_data, periods=forecast_period)

    # Prepare data to send to the frontend
    forecast_data = forecast[['ds', 'yhat']].to_json(date_format='iso', orient='records')
    original_data = original_data[['date', original_data.columns[1]]].to_json(date_format='iso' , orient='records')

    # Send both original data and forecast data to the frontend
    return jsonify({
        'original_data': original_data,
        'forecast': forecast_data
    })
@app.route('/api/growth_rate', methods=['POST'])
def growth_rate():
    data = request.get_json()
    keyword = data.get('keyword')
    timeframe = data.get('timeframe', 'today 3-m')

    if not keyword:
        return jsonify({"error": "Please provide a keyword."}), 400

    interest_data = fetch_interest_data(keyword, timeframe)
    if interest_data is None:
        return jsonify({"error": "No data found for the specified keyword and timeframe."}), 404

    interest_data.reset_index(inplace=True)
    result = calculate_growth_rate(interest_data, keyword)
    return jsonify(result)

@app.route('/api/interest_data', methods=['POST'])
def interest_data():
    data = request.get_json()
    keywords = data.get('keyword')
    timeframe = data.get('timeframe', 'today 5-y')
    location = data.get('location', '')

    if not keywords:
        return jsonify({"error": "Please provide a keyword."}), 400
    keywords = list(set(keywords))
    print(keywords)
    interest_data = fetch_interest_data(keywords, timeframe, location)
    if interest_data is None:
        return jsonify({"error": "No data found for the specified keywords."}), 404

    return interest_data.to_json(date_format='iso', orient='records')

@app.route('/api/keyword_suggestions', methods=['GET'])
def get_keyword_suggestions():
    keyword = request.args.get('keyword',  type=str)
    
    # Get suggestions for the given keyword
    suggestions = pytrends.suggestions(keyword=keyword)
    
    # Extract titles only
    titles = [suggestion['title'] for suggestion in suggestions if suggestion['title'].lower() != keyword]
    
    # Return the titles in JSON format
    return jsonify({"titles": titles})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
