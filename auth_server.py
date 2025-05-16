from flask import Flask, request
import logging
from config import FYERS_CLIENT_ID, FYERS_SECRET_KEY
import json

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/callback')
def callback():
    """Handle the callback from Fyers authentication"""
    try:
        # Get the auth code from URL parameters
        auth_code = request.args.get('auth_code')
        if auth_code:
            # Save the auth code to a file
            with open('auth_code.txt', 'w') as f:
                f.write(auth_code)
            return "Authentication successful! You can close this window now."
        else:
            return "No auth code received", 400
    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        return "Error processing callback", 500

if __name__ == '__main__':
    # Run the Flask server on port 8000
    app.run(port=8000)
