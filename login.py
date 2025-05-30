from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import uuid

MAX_PLAYERS = 2
players = {}  # Maps screen_name (lowercase) -> player_id

class LoginHandler(BaseHTTPRequestHandler):

    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path == '/login':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data)
            except json.JSONDecodeError:
                self._send_json(400, {'error': 'Invalid JSON'})
                return

            screen_name = data.get('screen_name', '').strip()
            if not screen_name:
                self._send_json(400, {'error': 'Missing screen_name'})
                return

            key = screen_name.lower()
            if key in players:
                self._send_json(409, {'error': 'Screen name already taken'})
                return

            if len(players) >= MAX_PLAYERS:
                self._send_json(403, {'error': 'Maximum number of players reached'})
                return

            player_id = str(uuid.uuid4())[:8]
            players[key] = player_id

            self._send_json(200, {
                'player_id': player_id,
                'screen_name': screen_name
            })

        else:
            self.send_response(404)
            self._set_cors_headers()
            self.end_headers()

    def _send_json(self, status_code, obj):
        response_bytes = json.dumps(obj).encode('utf-8')
        self.send_response(status_code)
        self._set_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

def run(server_class=HTTPServer, handler_class=LoginHandler, port=8766):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Login server running')
    httpd.serve_forever()

if __name__ == '__main__':
    run()