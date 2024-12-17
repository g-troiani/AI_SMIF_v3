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
import sqlite3



# Ensure the directory structure exist for plots
import os

if not os.path.exists('static'):
    os.makedirs('static')
if not os.path.exists('static/plots'):
    os.makedirs('static/plots')

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
        

     

from flask import Flask, jsonify
from flask_cors import CORS
import os
import logging
import requests
from datetime import datetime
import pytz
from typing import Dict, List, Optional, Union

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# app = Flask(__name__)
# CORS(app)

# Market symbols configuration
MARKET_SYMBOLS = {
    'SPY': "S&P 500",
    'QQQ': "NASDAQ",
    'IWV': "Russell 3000",
    'GLD': "Gold",
    'VXX': "VIX",
    'EWJ': "Japan (XJPX Proxy)",
    'EWU': "UK (XLON Proxy)",
    'BTC/USD': "Bitcoin"
}

class MarketData:
    def __init__(self):
        self.base_url = "https://data.alpaca.markets"
        self.headers = {
            "APCA-API-KEY-ID": os.getenv('APCA_API_KEY_ID', ''),
            "APCA-API-SECRET-KEY": os.getenv('APCA_API_SECRET_KEY', ''),
            "accept": "application/json"
        }

    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Get current price and previous close for a stock."""
        try:
            # Get latest price from snapshot
            snapshot_resp = requests.get(
                f"{self.base_url}/v2/stocks/{symbol}/snapshot",
                headers=self.headers,
                params={"feed": "sip"}
            )
            snapshot_resp.raise_for_status()
            snapshot_data = snapshot_resp.json()
            current_price = snapshot_data.get('latestTrade', {}).get('p')
            prev_close = snapshot_data.get('prevDailyBar', {}).get('c')

            return {
                'current_price': current_price,
                'prev_close': prev_close
            }
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None

    def get_crypto_data(self, symbol: str) -> Optional[Dict]:
        """Get current price and previous close for crypto."""
        try:
            # Get latest trade
            trade_resp = requests.get(
                f"{self.base_url}/v1beta3/crypto/us/latest/trades",
                headers=self.headers,
                params={"symbols": symbol}
            )
            trade_resp.raise_for_status()
            current_price = trade_resp.json().get('trades', {}).get(symbol, {}).get('p')

            # Get previous day's close
            bars_resp = requests.get(
                f"{self.base_url}/v1beta3/crypto/us/bars",
                headers=self.headers,
                params={
                    "symbols": symbol,
                    "timeframe": "1Day",
                    "limit": 2
                }
            )
            bars_resp.raise_for_status()
            bars = bars_resp.json().get('bars', {}).get(symbol, [])
            prev_close = bars[0].get('c') if bars else None

            return {
                'current_price': current_price,
                'prev_close': prev_close
            }
        except Exception as e:
            logger.error(f"Error fetching crypto data for {symbol}: {e}")
            return None

    @staticmethod
    def calculate_change(current: float, previous: float) -> float:
        """Calculate percentage change between two values."""
        if not (current and previous and previous != 0):
            return 0.0
        return ((current - previous) / previous) * 100

@app.route('/api/market-overview', methods=['GET'])
def market_overview():
    """Get market overview data for all tracked symbols."""
    try:
        market_data = []
        market_service = MarketData()

        for symbol, name in MARKET_SYMBOLS.items():
            try:
                # Get price data based on symbol type
                if symbol == 'BTC/USD':
                    data = market_service.get_crypto_data(symbol)
                else:
                    data = market_service.get_stock_data(symbol)

                if data and data['current_price']:
                    # Calculate change and format price
                    change = market_service.calculate_change(
                        data['current_price'], 
                        data['prev_close']
                    )
                    
                    market_data.append({
                        'symbol': symbol,
                        'name': name,
                        'price': f"{data['current_price']:,.2f}",
                        'change': round(change, 2)
                    })
                else:
                    # Add placeholder data if fetch failed
                    market_data.append({
                        'symbol': symbol,
                        'name': name,
                        'price': 'N/A',
                        'change': 0.0
                    })

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                # Maintain symbol visibility even on error
                market_data.append({
                    'symbol': symbol,
                    'name': name,
                    'price': 'N/A',
                    'change': 0.0
                })

        # Sort market data by symbol
        market_data.sort(key=lambda x: x['symbol'])
        
        return jsonify({
            'success': True,
            'data': market_data
        })

    except Exception as e:
        logger.error(f"General error in market overview: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500



        

@app.route('/api/backtest/strategies', methods=['GET'])
def get_available_strategies():
    from components.backtesting_module.backtrader.strategy_adapters import StrategyAdapter
    # StrategyAdapter.STRATEGIES is a dict { 'Name': StrategyClass, ... }
    strategies = list(StrategyAdapter.STRATEGIES.keys())
    return jsonify({
        'success': True,
        'strategies': strategies
    })



@app.route('/api/backtest/run', methods=['POST'])
def run_backtest():
    from components.backtesting_module.backtester import Backtester
    data = request.get_json()
    strategy_name = data.get('strategy')
    symbol = data.get('symbol')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    # Optional parameters
    stop_loss = data.get('stop_loss')
    take_profit = data.get('take_profit')

    try:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        # If strategy parameters are passed, extract them:
        # strategy_params = data.get('strategy_params', {})
        strategy_params = {}  # For now, empty or fill as needed.

        backtester = Backtester(
            strategy_name=strategy_name,
            strategy_params=strategy_params,
            ticker=symbol,
            start_date=start_dt,
            end_date=end_dt,
            db_path=os.path.join(project_root, 'data', 'market_data.db'),
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        backtester.run_backtest()

        # Retrieve the metrics we just saved from the database
        conn = sqlite3.connect('data/backtesting_results.db')
        cursor = conn.cursor()

        # Get the most recent backtest record for this strategy/ticker/date combination
        cursor.execute('''
            SELECT strategy_name, ticker, start_date, end_date, cagr, total_pct_change, std_dev, annual_vol, sharpe_ratio,
                   sortino_ratio, max_drawdown, win_rate, num_trades, information_ratio, strategy_unique_id
            FROM backtest_summary
            WHERE strategy_name = ? AND ticker = ? AND start_date = ? AND end_date = ?
            ORDER BY id DESC LIMIT 1
        ''', (strategy_name, symbol, start_dt.strftime('%Y-%m-%d %H:%M:%S'), end_dt.strftime('%Y-%m-%d %H:%M:%S')))
        row = cursor.fetchone()
        conn.close()

        if row:
            # Extract metrics
            metrics = {
                'strategy_name': row[0],
                'ticker': row[1],
                'start_date': row[2],
                'end_date': row[3],
                'cagr': row[4],
                'total_return_pct': row[5],
                'std_dev': row[6],
                'annual_vol': row[7],
                'sharpe_ratio': row[8],
                'sortino_ratio': row[9],
                'max_drawdown': row[10],
                'win_rate': row[11],
                'num_trades': row[12],
                'information_ratio': row[13],
                'strategy_unique_id': row[14]
            }
        else:
            metrics = None

        # Return the plot_url if we have it
        plot_filename = getattr(backtester, 'plot_filename', None)
        plot_url = None
        if plot_filename:
            plot_url = '/' + plot_filename.replace('\\', '/').lstrip('/')

        return jsonify({
            'success': True,
            'message': 'Backtest completed successfully',
            'plot_url': plot_url,
            'metrics': metrics  # Return the metrics we just fetched
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500








@app.route('/api/backtests', methods=['GET'])
def get_all_backtests():
    import sqlite3, json
    conn = sqlite3.connect('data/backtesting_results.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id,
            strategy_name,
            strategy_params,
            ticker,
            start_date,
            end_date,
            final_value,
            total_pl,
            total_pct_change,
            cagr,
            total_return,
            std_dev,
            annual_vol,
            sharpe_ratio,
            sortino_ratio,
            max_drawdown,
            win_rate,
            alpha,
            num_trades,
            information_ratio,
            strategy_unique_id,
            timestamp
        FROM backtest_summary
        ORDER BY timestamp DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        strategy_params = json.loads(row[2]) if row[2] else {}
        result = {
            'id': row[0],
            'strategy_name': row[1],
            'strategy_params': strategy_params,
            'ticker': row[3],
            'start_date': row[4],
            'end_date': row[5],
            'final_value': row[6],
            'total_pl': row[7],
            'total_return_pct': row[8],  # Changed from 'total_pct_change' to 'total_return_pct'
            'cagr': row[9],
            'total_return': row[10],
            'std_dev': row[11],
            'annual_vol': row[12],
            'sharpe_ratio': row[13],
            'sortino_ratio': row[14],
            'max_drawdown': row[15],
            'win_rate': row[16],
            'alpha': row[17],
            'num_trades': row[18],
            'information_ratio': row[19],
            'strategy_unique_id': row[20],
            'timestamp': row[21]
        }
        results.append(result)
    return jsonify({'success': True, 'results': results})







if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    # Initialize the app when imported as a module
    initialize_app()

logger.debug(f"Flask backend starting with PID: {os.getpid()}")