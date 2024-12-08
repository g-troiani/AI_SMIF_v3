from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import logging
import pandas as pd
import zmq
import json
from pathlib import Path
import traceback
from datetime import datetime, timedelta
from alpaca_trade_api.rest import REST
import os
import logging
import requests
from flask import jsonify
import pytz

# Configure logging with more detailed formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('flask_app.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ZeroMQ configuration for communication with data manager
class DataManagerClient:
    def __init__(self):
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5556")
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
        self.socket.setsockopt(zmq.LINGER, 0)
        logger.info("DataManagerClient initialized with socket connection to localhost:5556")

    def send_command(self, command):
        try:
            logger.info(f"Attempting to send command: {command}")
            logger.debug(f"ZMQ socket state - Connected: {self.socket}")
            
            self.socket.send_json(command)
            logger.info("Command sent successfully, waiting for response")
            
            response = self.socket.recv_json()
            logger.info(f"Received response: {response}")
            return response
            
        except zmq.error.Again:
            logger.error(f"""
            Timeout waiting for response from data manager
            Command: {command}
            Socket Details:
            - Type: {self.socket.type}
            - Endpoint: tcp://localhost:5556
            """)
            return {"success": False, "message": "Command timeout"}
        except Exception as e:
            logger.error(f"Error sending command to data manager: {str(e)}\nTraceback: {traceback.format_exc()}")
            return {"success": False, "message": str(e)}

    def close(self):
        self.socket.close()

app = Flask(__name__)
CORS(app)

# Initialize the data manager client
data_manager_client = DataManagerClient()

def get_tickers_file_path():
    """Get the absolute path to the tickers.csv file"""
    return os.path.join(project_root, 'tickers.csv')

def log_request_info(request):
    logger.debug(f"""
    Request Details:
    - Method: {request.method}
    - URL: {request.url}
    - Headers: {dict(request.headers)}
    - Body: {request.get_data()}
    """)

@app.route('/api/tickers', methods=['GET'])
def get_tickers():
    """Endpoint to get list of tickers"""
    try:
        tickers_file = get_tickers_file_path()
        if not os.path.exists(tickers_file):
            logger.error(f"Tickers file not found at: {tickers_file}")
            return jsonify({
                'success': False,
                'message': 'Tickers file not found'
            }), 404

        tickers_df = pd.read_csv(tickers_file, names=['ticker'])
        return jsonify({
            'success': True,
            'tickers': tickers_df['ticker'].tolist()
        })
    except Exception as e:
        logger.error(f"Error fetching tickers: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/tickers', methods=['POST'])
def add_ticker():
    """Endpoint to add a new ticker"""
    try:
        log_request_info(request)
        logger.info("Received request to add ticker")
        
        data = request.get_json()
        logger.debug(f"Received data: {data}")
        
        if not data or 'ticker' not in data:
            logger.warning("No ticker provided in request")
            return jsonify({
                'success': False,
                'message': 'No ticker provided'
            }), 400

        ticker = data['ticker'].upper()
        logger.info(f"Processing ticker: {ticker}")
        
        # Validate ticker format
        if not ticker.isalpha() or not (1 <= len(ticker) <= 5):
            return jsonify({
                'success': False,
                'message': 'Invalid ticker format'
            }), 400

        # Send command to data manager
        response = data_manager_client.send_command({
            'type': 'add_ticker',
            'ticker': ticker
        })

        if response.get('success'):
            return jsonify({
                'success': True,
                'message': f'Ticker {ticker} added successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': response.get('message', 'Failed to add ticker')
            }), 500

    except Exception as e:
        logger.error(f"Error adding ticker: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint to check if the service is running"""
    return jsonify({
        'status': 'healthy',
        'timestamp': pd.Timestamp.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    logger.info("Received request for strategies")
    try:
        config_path = os.path.join(project_root, 'config/strategies.json')
        logger.debug(f"Looking for strategies at: {config_path}")
        
        if not os.path.exists(config_path):
            logger.error(f"Strategies file not found at: {config_path}")
            return jsonify({
                'success': False,
                'message': 'Strategies configuration not found'
            }), 404
            
        with open(config_path, 'r') as f:
            strategies = json.load(f)
            logger.info(f"Successfully loaded {len(strategies)} strategies")
            return jsonify(strategies)
    except Exception as e:
        logger.error(f"Error loading strategies: {str(e)}\nTraceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

def initialize_app():
    """Initialize the application with required setup"""
    try:
        # Ensure tickers file exists
        tickers_file = get_tickers_file_path()
        if not os.path.exists(tickers_file):
            Path(tickers_file).parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(columns=['ticker']).to_csv(tickers_file, index=False)
            logger.info(f"Created new tickers file at {tickers_file}")

        logger.info("Flask application initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing application: {str(e)}")
        raise


@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Endpoint to get current positions from Alpaca"""
    try:
        logger.info("Attempting to fetch positions")
        
        # Alpaca API configuration
        url = "https://paper-api.alpaca.markets/v2/positions"
        headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": os.getenv('APCA_API_KEY_ID'),
            "APCA-API-SECRET-KEY": os.getenv('APCA_API_SECRET_KEY')
        }
        
        # Make the request
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # Parse the response
        positions = response.json()
        
        # Format positions data
        positions_data = [{
            'symbol': pos['symbol'],
            'qty': float(pos['qty']),
            'avgEntryPrice': float(pos['avg_entry_price']),
            'marketValue': float(pos['market_value']),
            'currentPrice': float(pos['current_price']),
            'unrealizedPL': float(pos['unrealized_pl']),
            'unrealizedPLPercent': float(pos['unrealized_plpc']),
            'change': float(pos['change_today'])
        } for pos in positions]
        
        logger.info(f"Successfully retrieved {len(positions_data)} positions")
        return jsonify({
            'success': True,
            'positions': positions_data
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching positions from Alpaca: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"API error: {str(e)}"
        }), 500
    except Exception as e:
        logger.error(f"Error processing positions data: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500    

@app.route('/api/recent-trades', methods=['GET'])
def get_recent_trades():
    """Endpoint to get recent trades from Alpaca"""
    try:
        logger.info("Attempting to fetch recent trades")
        
        base_url = "https://paper-api.alpaca.markets"
        endpoint = "/v2/account/activities/FILL"
        
        headers = {
            "APCA-API-KEY-ID": os.getenv('APCA_API_KEY_ID'),
            "APCA-API-SECRET-KEY": os.getenv('APCA_API_SECRET_KEY'),
            "accept": "application/json"
        }
        
        params = {
            "direction": "desc",  # Most recent first
            "page_size": 20      # Limit to 15 trades
        }
        
        logger.info("Making request to Alpaca API")
        response = requests.get(
            f"{base_url}{endpoint}", 
            headers=headers,
            params=params
        )
        
        response.raise_for_status()
        trades = response.json()
        
        logger.info(f"Retrieved {len(trades)} trades")
        
        # Format the trade data for frontend consumption
        formatted_trades = []
        for trade in trades:
            formatted_trade = {
                'symbol': trade['symbol'],
                'side': trade['side'],
                'qty': float(trade['qty']),
                'price': float(trade['price']),
                'time': trade['transaction_time'],
                'order_id': trade['order_id'],
                'total_value': float(trade['qty']) * float(trade['price'])
            }
            formatted_trades.append(formatted_trade)
        
        logger.info("Successfully formatted trade data")
        return jsonify({
            'success': True,
            'trades': formatted_trades
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching trades from Alpaca: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"API error: {str(e)}"
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error processing trades: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500



# Create console handler and set level to DEBUG
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(ch)


@app.route('/api/portfolio/history', methods=['GET'])
def get_portfolio_history():
    """Get historical portfolio value data based on time period"""
    try:
        # Get time period from query parameter (default to 1M)
        period = request.args.get('period', '1M')
        
        # Convert period to Alpaca's format (Y -> 12M)
        if period == '1Y':
            period = '12M'
        elif period == 'ALL':
            period = '60M'  # 5 years
        
        # Configure Alpaca API request
        base_url = "https://paper-api.alpaca.markets"
        headers = {
            "APCA-API-KEY-ID": os.getenv('APCA_API_KEY_ID'),
            "APCA-API-SECRET-KEY": os.getenv('APCA_API_SECRET_KEY'),
            "accept": "application/json"
        }
        
        # Set proper timeframe based on period according to Alpaca's rules
        params = {
            'extended_hours': 'true'
        }
        
        # Map timeframes based on period
        if period == '1D':
            params['timeframe'] = '5Min'
        elif period == '1W':
            params['timeframe'] = '15Min'
        else:
            params['timeframe'] = '1D'  # Use 1D for all longer periods
        
        # Add period parameter
        params['period'] = period
        
        logger.info(f"Requesting portfolio history with params: {params}")
        
        response = requests.get(
            f"{base_url}/v2/account/portfolio/history",
            headers=headers,
            params=params
        )
        
        if not response.ok:
            logger.error(f"Alpaca API error response: {response.text}")
            response.raise_for_status()
            
        history_data = response.json()
        
        # Process and format data for frontend
        timestamps = history_data.get('timestamp', [])
        equity = history_data.get('equity', [])
        base_value = history_data.get('base_value', 0)
        
        formatted_data = []
        est_tz = pytz.timezone('America/New_York')
        
        for timestamp, value in zip(timestamps, equity):
            if value is not None:  # Skip any null values
                dt = datetime.fromtimestamp(timestamp, pytz.UTC)
                dt_est = dt.astimezone(est_tz)
                formatted_data.append({
                    'date': dt_est.isoformat(),
                    'value': float(value)
                })
        
        # Calculate percentage change using base_value from Alpaca if available
        if len(formatted_data) >= 2:
            start_value = base_value if base_value else formatted_data[0]['value']
            end_value = formatted_data[-1]['value']
            percentage_change = ((end_value - start_value) / start_value) * 100 if start_value else 0
        else:
            percentage_change = 0
            
        response_data = {
            'success': True,
            'data': {
                'history': formatted_data,
                'currentBalance': formatted_data[-1]['value'] if formatted_data else 0,
                'percentageChange': round(percentage_change, 2)
            }
        }
        
        return jsonify(response_data)
        
    except requests.exceptions.RequestException as e:
        error_details = e.response.text if hasattr(e, 'response') else 'No response details'
        logger.error(f"Alpaca API error response: {error_details}")
        logger.error(f"Error fetching portfolio history from Alpaca: {str(e)}")
        logger.error(f"Full error details: {error_details}")
        return jsonify({
            'success': False,
            'message': f"API error: {str(e)}"
        }), 500
    except Exception as e:
        logger.error(f"Error processing portfolio history: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
        
        
@app.route('/api/dashboard-data', methods=['GET'])
def get_dashboard_data():
    """Endpoint to get dashboard metrics from Alpaca"""
    try:
        # Base URL for paper trading
        base_url = "https://paper-api.alpaca.markets"
        headers = {
            "APCA-API-KEY-ID": os.getenv('APCA_API_KEY_ID'),
            "APCA-API-SECRET-KEY": os.getenv('APCA_API_SECRET_KEY'),
            "accept": "application/json"
        }
        
        # Get account info
        account_response = requests.get(
            f"{base_url}/v2/account",
            headers=headers
        )
        account_response.raise_for_status()
        account = account_response.json()
        
        # Calculate metrics
        equity = float(account.get('equity', 0))
        cash = float(account.get('cash', 0))
        last_equity = float(account.get('last_equity', equity))
        today_pl = equity - last_equity
        today_return = (today_pl / last_equity) * 100 if last_equity != 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'account_balance': equity,
                'cash_available': cash,
                'today_pl': today_pl,
                'today_return': today_return
            }
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching account data from Alpaca: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"API error: {str(e)}"
        }), 500
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    # Initialize the app when imported as a module
    initialize_app()

logger.debug(f"Flask backend starting with PID: {os.getpid()}")