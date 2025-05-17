import requests
import webbrowser
import json
import urllib.parse
from config import UPSTOX_API_KEY, UPSTOX_API_SECRET, UPSTOX_REDIRECT_URI

def get_login_url():
    """
    Generate and open the Upstox authorization URL.
    This is the first step in the OAuth 2.0 flow.
    """
    try:
        print("Starting OAuth authorization flow...")
        
        # Construct the login URL as per Upstox docs
        base_url = "https://api-v2.upstox.com/login/authorization/dialog"
        params = {
            "response_type": "code",
            "client_id": UPSTOX_API_KEY,
            "redirect_uri": UPSTOX_REDIRECT_URI,
        }
        
        # Build the URL with parameters
        login_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        print(f"Authorization URL: {login_url}")
        
        # Open the URL in browser
        print("Opening authorization URL in browser...")
        webbrowser.open(login_url)
        return login_url
        
    except Exception as e:
        print(f"Error in get_login_url: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def get_access_token(auth_code):
    """
    Exchange authorization code for access token.
    This is the second step in the OAuth 2.0 flow.
    """
    try:
        print("\nExchanging authorization code for access token...")
        
        # Token endpoint as per Upstox docs
        token_url = "https://api-v2.upstox.com/login/authorization/token"
        
        # Headers
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        # Form data as required by Upstox
        payload = {
            "code": auth_code,
            "client_id": UPSTOX_API_KEY,
            "client_secret": UPSTOX_API_SECRET,
            "redirect_uri": UPSTOX_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        print("Sending token request with payload:")
        print(json.dumps(payload, indent=2))
        
        # Make the token request
        response = requests.post(
            token_url, 
            data=payload,
            headers=headers
        )
        
        print(f"Response status code: {response.status_code}")
        
        # Process the response
        if response.status_code == 200:
            token_data = response.json()
            print("Token response received:")
            # Create a safe version for printing (hide actual token)
            safe_data = token_data.copy()
            if 'access_token' in safe_data:
                safe_data['access_token'] = safe_data['access_token'][:10] + '...'
            print(json.dumps(safe_data, indent=2))
            
            if 'access_token' in token_data:
                access_token = token_data['access_token']
                save_token_to_file(access_token)
                return access_token
            else:
                print("Error: Access token not found in response")
                print("Full response:", response.text)
                return None
        else:
            print(f"Error: Token request failed with status {response.status_code}")
            print("Response:", response.text)
            return None
            
    except Exception as e:
        print(f"Error in get_access_token: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def save_token_to_file(token, filename="access_token.txt"):
    """Save the access token to a file"""
    try:
        with open(filename, 'w') as f:
            f.write(token)
        print(f"Access token saved to {filename}")
    except Exception as e:
        print(f"Error saving token to file: {str(e)}")

def load_token_from_file(filename="access_token.txt"):
    """Load the access token from a file"""
    try:
        with open(filename, 'r') as f:
            token = f.read().strip()
            if token:
                print("Access token loaded successfully")
                return token
            else:
                print("Access token file is empty")
                return None
    except FileNotFoundError:
        print(f"Token file {filename} not found")
        return None
    except Exception as e:
        print(f"Error loading token from file: {str(e)}")
        return None

if __name__ == "__main__":
    print("===== Upstox API Authentication =====")
    
    # Check if we already have a token
    existing_token = load_token_from_file()
    if existing_token:
        print("\nAn existing access token was found.")
        choice = input("Do you want to use this token or generate a new one? (use/new): ").lower()
        if choice == "use":
            print("Using existing token. You can now run your bot.")
            exit(0)
    
    # Step 1: Get authorization URL and open browser
    login_url = get_login_url()
    if not login_url:
        print("Failed to generate login URL. Check your configuration.")
        exit(1)
    
    print("\n===== BROWSER AUTHENTICATION =====")
    print("1. A browser window should have opened.")
    print("2. Log in to your Upstox account.")
    print("3. Authorize the application when prompted.")
    print("4. You will be redirected to your redirect URI with a 'code' parameter.")
    print("   The URL will look like: your_redirect_uri?code=XXXX")
    
    # Step 2: Get authorization code from user
    auth_code = input("\nEnter the authorization code from the redirect URL: ").strip()
    if not auth_code:
        print("No authorization code provided. Exiting.")
        exit(1)
    
    # Step 3: Exchange authorization code for access token
    access_token = get_access_token(auth_code)
    
    if access_token:
        print("\n===== AUTHENTICATION SUCCESSFUL =====")
        print("The access token has been saved to 'access_token.txt'")
        print("You can now run your bot.py script to start monitoring market data.")
    else:
        print("\n===== AUTHENTICATION FAILED =====")
        print("Failed to obtain access token. Please check the error messages above.")