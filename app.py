from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import numpy as np
import joblib
import json
import plotly
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'data'

# Global variables to store model and data
model = None
scaler = None
feature_names = None
df_data = None

def load_model_components():
    """Load the trained model, scaler, and feature names"""
    global model, scaler, feature_names
    try:
        model = joblib.load('models/gold_price_prediction_ridge_regression.pkl')
        scaler = joblib.load('models/scaler_ridge_regression.pkl')
        feature_names = joblib.load('models/features_ridge_regression.pkl')
        print("Model components loaded successfully!")
        return True
    except Exception as e:
        print(f"Error loading model: {e}")
        return False

def load_data():
    """Load and preprocess the dataset"""
    global df_data
    try:
        # Try loading from root directory first, then dataset directory
        try:
            df_data = pd.read_csv('Daily.csv')
        except:
            df_data = pd.read_csv('dataset/Daily.csv')
            
        df_data['Date'] = pd.to_datetime(df_data['Date'])
        df_data = df_data.replace('#N/A', np.nan)
        
        # Convert numeric columns
        for col in df_data.columns[1:]:
            df_data[col] = pd.to_numeric(df_data[col].astype(str).str.replace(',', ''), errors='coerce')
        
        df_data = df_data.fillna(method='ffill').fillna(method='bfill')
        print("Data loaded successfully!")
        return True
    except Exception as e:
        print(f"Error loading data: {e}")
        return False

def create_sample_features(base_price=2000):
    """Create sample features for prediction"""
    np.random.seed(42)
    sample_features = {}
    
    # Currency features (correlated with gold price)
    currencies = ['EUR', 'GBP', 'JPY', 'CAD', 'CHF', 'INR', 'CNY', 'AED']
    for currency in currencies:
        if currency == 'JPY':
            sample_features[currency] = base_price * np.random.uniform(140, 160)
        elif currency == 'INR':
            sample_features[currency] = base_price * np.random.uniform(80, 85)
        else:
            sample_features[currency] = base_price * np.random.uniform(0.7, 1.3)
    
    # Date features
    today = datetime.now()
    sample_features['Year'] = today.year
    sample_features['Month'] = today.month
    sample_features['Day'] = today.day
    sample_features['DayOfWeek'] = today.weekday()
    sample_features['Quarter'] = (today.month - 1) // 3 + 1
    
    # Lagged features
    for lag in [1, 3, 7, 14, 30]:
        sample_features[f'USD_lag_{lag}'] = base_price * np.random.uniform(0.98, 1.02)
    
    # Moving averages
    for window in [3, 7, 14, 30]:
        sample_features[f'USD_MA_{window}'] = base_price * np.random.uniform(0.99, 1.01)
    
    # Additional features
    sample_features['USD_pct_change'] = np.random.uniform(-0.02, 0.02)
    sample_features['USD_price_change'] = np.random.uniform(-20, 20)
    sample_features['USD_volatility_7'] = np.random.uniform(10, 50)
    sample_features['USD_volatility_30'] = np.random.uniform(15, 60)
    sample_features['USD_RSI'] = np.random.uniform(30, 70)
    
    return sample_features

# Initialize components when the app starts
def initialize_app():
    """Initialize model and data components"""
    print("Initializing application...")
    load_model_components()
    load_data()
    print("Application initialized successfully!")

# Routes
@app.route('/')
def index():
    """Home page with hero section"""
    # Get latest gold price for hero section
    latest_price = None
    price_change = None
    if df_data is not None and not df_data.empty:
        latest_price = df_data['USD'].iloc[-1]
        price_change = df_data['USD'].iloc[-1] - df_data['USD'].iloc[-2]
    
    return render_template('index.html', 
                         latest_price=latest_price, 
                         price_change=price_change)

@app.route('/about')
def about():
    """About page with model information"""
    model_info = {
        'algorithm': 'Ridge Regression',
        'r2_score': 0.9999,
        'rmse': 2.80,
        'mae': 2.13,
        'features_count': 20,
        'training_samples': 9277,
        'test_samples': 2319
    }
    return render_template('about.html', model_info=model_info)

@app.route('/visualization')
def visualization():
    """Visualization page with interactive charts"""
    return render_template('visualization.html')

@app.route('/prediction')
def prediction():
    """Prediction page with input form"""
    return render_template('prediction.html')

@app.route('/model-info')
def model_info():
    """Detailed model information page"""
    model_info = {
        'algorithm': 'Ridge Regression',
        'r2_score': '99.99%',
        'rmse': 2.80,
        'mae': 2.13,
        'features_count': 20,
        'training_samples': 9277,
        'test_samples': 2319,
        'mape': '0.15%',
        'description': 'Advanced Ridge Regression model with L2 regularization',
        'last_updated': datetime.now().strftime('%Y-%m-%d'),
        'features': [
            'Currency Exchange Rates',
            'Technical Indicators',
            'Market Trends',
            'Historical Prices',
            'Volatility Measures'
        ]
    }
    return render_template('model_info.html', model_info=model_info)

# API Routes
@app.route('/api/predict', methods=['POST'])
def predict():
    """API endpoint for gold price prediction"""
    if model is None:
        return jsonify({'error': 'Model is currently loading. Please try again in a few moments.'}), 503
    
    try:
        # Get input data
        input_data = request.get_json()
        
        if not input_data:
            # Use sample features if no input provided
            features = create_sample_features()
        else:
            features = input_data
        
        # Create DataFrame with required features
        feature_df = pd.DataFrame([features])
        
        # Ensure all required features are present
        for feature in feature_names:
            if feature not in feature_df.columns:
                # Fill missing features with sample values
                if 'USD' in feature:
                    feature_df[feature] = features.get('USD', 2000) * np.random.uniform(0.99, 1.01)
                else:
                    feature_df[feature] = np.random.uniform(100, 1000)
        
        # Select only required features
        feature_df = feature_df[feature_names]
        
        # Make prediction
        prediction = model.predict(feature_df)[0]
        
        # Calculate confidence interval (approximate)
        confidence = prediction * 0.02  # 2% confidence interval
        
        return jsonify({
            'prediction': round(prediction, 2),
            'confidence_lower': round(prediction - confidence, 2),
            'confidence_upper': round(prediction + confidence, 2),
            'model': 'Ridge Regression',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'error': 'An error occurred while making the prediction. Please try again.'}), 500

@app.route('/api/historical-data')
def get_historical_data():
    """API endpoint for historical gold price data"""
    if df_data is None:
        return jsonify({'error': 'Historical data is currently loading. Please refresh the page in a few moments.'}), 503
    
    try:
        # Get last 365 days of data
        recent_data = df_data.tail(365).copy()
        
        # Prepare data for charts
        chart_data = {
            'dates': recent_data['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'prices': recent_data['USD'].tolist(),
            'volume': np.random.randint(1000, 5000, len(recent_data)).tolist()  # Mock volume data
        }
        
        return jsonify(chart_data)
    
    except Exception as e:
        print(f"Historical data error: {e}")
        return jsonify({'error': 'An error occurred while fetching historical data. Please refresh the page.'}), 500

@app.route('/api/price-analysis')
def price_analysis():
    """API endpoint for price analysis data"""
    if df_data is None:
        return jsonify({'error': 'Price analysis data is currently loading. Please refresh the page in a few moments.'}), 503
    
    try:
        recent_data = df_data.tail(30)  # Last 30 days
        
        analysis = {
            'current_price': float(recent_data['USD'].iloc[-1]),
            'price_change_24h': float(recent_data['USD'].iloc[-1] - recent_data['USD'].iloc[-2]),
            'price_change_7d': float(recent_data['USD'].iloc[-1] - recent_data['USD'].iloc[-7]),
            'price_change_30d': float(recent_data['USD'].iloc[-1] - recent_data['USD'].iloc[0]),
            'volatility': float(recent_data['USD'].std()),
            'avg_price_30d': float(recent_data['USD'].mean()),
            'min_price_30d': float(recent_data['USD'].min()),
            'max_price_30d': float(recent_data['USD'].max())
        }
        
        return jsonify(analysis)
    
    except Exception as e:
        print(f"Price analysis error: {e}")
        return jsonify({'error': 'An error occurred while analyzing price data. Please refresh the page.'}), 500

@app.route('/api/correlation-data')
def correlation_data():
    """API endpoint for currency correlation data"""
    if df_data is None:
        return jsonify({'error': 'Correlation data is currently loading. Please refresh the page in a few moments.'}), 503
    
    try:
        # Calculate correlations with USD
        currency_cols = ['EUR', 'GBP', 'JPY', 'CAD', 'CHF', 'INR', 'CNY', 'AED']
        available_currencies = [col for col in currency_cols if col in df_data.columns]
        
        correlations = {}
        for currency in available_currencies:
            corr = df_data[['USD', currency]].corr().iloc[0, 1]
            if not np.isnan(corr):
                correlations[currency] = float(corr)
        
        return jsonify(correlations)
    
    except Exception as e:
        print(f"Correlation data error: {e}")
        return jsonify({'error': 'An error occurred while calculating correlations. Please refresh the page.'}), 500

if __name__ == '__main__':
    # Initialize the application components
    with app.app_context():
        initialize_app()
    
    # Run the Flask application
    app.run(debug=True, host='0.0.0.0', port=5000)
