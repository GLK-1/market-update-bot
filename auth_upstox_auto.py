import os
import webbrowser
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv  # python-dotenv package

from upstox_client import Configuration, ApiClient
from upstox_client.apis import AuthorizationApi
from upstox_client.models.access_token_request import AccessTokenRequest

# Load from environment variables
load_dotenv()
API_KEY = os.getenv("UPSTOX_API_KEY")
API_SECRET = os.getenv("UPSTOX_API_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"

class AuthHandler:
    def __init__(self):
        self.auth_code = None
        self.token = None

    class CallbackHandler(BaseHTTPRequestHandler):
        def __init__(self, request, client_address, server):
            self.server = server
            super().__init__(request, client_address, server)

        def do_GET(self):
            query = urlparse(self.path).query
            params = parse_qs(query)
            code = params.get("code", [None])[0]
            error = params.get("error", [None])[0]

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            if code:
                self.server.auth_handler.auth_code = code
                self.wfile.write(b"<h1>Authorization successful. You may close this window.</h1>")
            elif error:
                self.wfile.write(f"<h1>Error: {error}</h1>".encode())
            else:
                self.wfile.write(b"<h1>No authorization code received</h1>")

    def start_local_server(self):
        server = HTTPServer(("localhost", 8000), lambda *args: self.CallbackHandler(*args))
        server.auth_handler = self
        print("🌐 Waiting for Upstox auth redirect on http://localhost:8000/callback ...")
        server.handle_request()
        server.server_close()

    def get_login_url(self):
        config = Configuration()
        api_client = ApiClient(config)
        auth_api = AuthorizationApi(api_client)
        return auth_api.get_login_url(API_KEY, REDIRECT_URI)

    def get_access_token(self, code):
        config = Configuration()
        api_client = ApiClient(config)
        auth_api = AuthorizationApi(api_client)

        req = AccessTokenRequest(
            code=code,
            client_id=API_KEY,
            client_secret=API_SECRET,
            redirect_uri=REDIRECT_URI,
            grant_type="authorization_code"
        )

        return auth_api.get_access_token(req)

if __name__ == "__main__":
    print("🔐 Starting Upstox auth process...")
    auth = AuthHandler()

    # Start server in background
    server_thread = threading.Thread(target=auth.start_local_server)
    server_thread.start()

    # Open login URL
    login_url = auth.get_login_url()
    print("🔗 Opening login URL:", login_url)
    webbrowser.open(login_url)

    # Wait for auth to complete
    server_thread.join(timeout=120)  # 2 minute timeout

    if auth.auth_code:
        print(f"✅ Authorization code received")
        try:
            token = auth.get_access_token(auth.auth_code)
            print(f"\n✅ ACCESS TOKEN: {token.access_token}")
            print(f"🔁 REFRESH TOKEN: {token.refresh_token}")
            
            # Here you would typically store the tokens securely
        except Exception as e:
            print(f"❌ Failed to get access token: {str(e)}")
    else:
        print("❌ Authorization failed or timed out")