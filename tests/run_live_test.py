import os
from components.integration_communication_module.live_data_integration import setup_live_data_cerebro
from components.backtesting_module.backtrader.immediate_action_strategy import ImmediateActionStrategy

if __name__ == "__main__":
    API_KEY = os.getenv("APCA_API_KEY_ID")
    API_SECRET = os.getenv("APCA_API_SECRET_KEY")
    SYMBOL = "NVDA"  # Symbol that trades frequently. Run during market hours.

    if not API_KEY or not API_SECRET:
        raise ValueError("Alpaca API credentials not found in environment variables.")

    cerebro, ws_client = setup_live_data_cerebro(API_KEY, API_SECRET, SYMBOL, ImmediateActionStrategy)

    # If you have implemented an AlpacaBroker, uncomment these lines:
    # from integration_communication_module.alpaca_broker import AlpacaBroker
    # broker = AlpacaBroker(API_KEY, API_SECRET, base_url="https://paper-api.alpaca.markets")
    # cerebro.setbroker(broker)

    try:
        print("Starting live test. Waiting for bars to arrive...")
        # Specify runonce=False here when running
        results = cerebro.run(runonce=False)
    finally:
        ws_client.stop()
        print("Live test concluded.")

    strat = results[0]
    if strat.bars_received:
        if strat.trades_made:
            print("Test successful: Bars were received and trades were executed.")
        else:
            print("Test successful: Bars were received, but no trades were executed.")
    else:
        print("Test not successful: No bars were received, so no trading took place.")
