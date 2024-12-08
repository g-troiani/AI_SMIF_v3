# add_ticker_command.py
import zmq
import sys
import time
import json

def send_add_ticker_command(ticker_symbol, max_retries=3):
    """Send command to add a new ticker to the running DataManager"""
    context = zmq.Context()
    command = {
        'type': 'add_ticker',
        'ticker': ticker_symbol.upper()
    }
    
    print(f"Attempting to connect to DataManager on port 5556...")
    for attempt in range(max_retries):
        try:
            # Create a new socket for each attempt
            socket = context.socket(zmq.REQ)
            socket.connect("tcp://localhost:5556")
            # Set socket options
            socket.setsockopt(zmq.LINGER, 1000)
            socket.setsockopt(zmq.RCVTIMEO, 5000)
            socket.setsockopt(zmq.SNDTIMEO, 5000)
            socket.setsockopt(zmq.IMMEDIATE, 1)
            
            print(f"Sending command: {command}")
            socket.send_json(command)
            print("Command sent, waiting for response...")
            response = socket.recv_json()
            
            if response.get('success'):
                print(f"Success: {response.get('message', 'Ticker added successfully')}")
                socket.close()
                context.term()
                return True
            else:
                print(f"Failed: {response.get('message', 'Unknown error occurred')}")
                socket.close()
                context.term()
                return False
                
        except zmq.error.Again:
            print(f"Timeout on attempt {attempt + 1}/{max_retries} - No response from DataManager")
            if attempt < max_retries - 1:
                print("Waiting before retry...")
                time.sleep(1)
            else:
                print("\nTroubleshooting tips:")
                print("1. Ensure your main program with DataManager is running")
                print("2. Check if port 5556 is available using: netstat -an | grep 5556")
                print("3. Check your main program's logs for any initialization errors")
            socket.close()
            continue  # Retry the loop
        except Exception as e:
            print(f"Error on attempt {attempt + 1}/{max_retries}: {str(e)}")
            print("This may indicate that DataManager is not running")
            if attempt < max_retries - 1:
                print("Waiting before retry...")
                time.sleep(1)
            else:
                print("\nTroubleshooting tips:")
                print("1. Ensure your main program with DataManager is running")
                print("2. Check if port 5556 is available using: netstat -an | grep 5556")
                print("3. Check your main program's logs for any initialization errors")
            socket.close()
            continue  # Retry the loop
        finally:
            # Ensure the socket is closed in case of any unexpected exceptions
            if not socket.closed:
                socket.close()
    # Clean up the context after all attempts
    context.term()
    return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_ticker_command.py TICKER")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    success = send_add_ticker_command(ticker)
    sys.exit(0 if success else 1)
