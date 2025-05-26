from http.server import BaseHTTPRequestHandler, HTTPServer
import json

scores = {}  # player_id -> score

class ScoreHandler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') #Allows access from anywhere
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/score/hit':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                pid = data.get('player_id')
                if pid is None:
                    raise ValueError("Missing 'player_id'")

                scores[pid] = scores.get(pid, 0) + 1
                self._set_headers()
                self.wfile.write(json.dumps({'player_id': pid, 'score': scores[pid]}).encode())

            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': str(e)}).encode())

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def do_GET(self):
        if self.path == '/score':
            self._set_headers()
            self.wfile.write(json.dumps(scores).encode())

        elif self.path.startswith('/score/'):
            try:
                pid = int(self.path.split('/')[-1])
                if pid not in scores:
                    raise KeyError
                self._set_headers()
                self.wfile.write(json.dumps({'player_id': pid, 'score': scores[pid]}).encode())
            except:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'Player not found'}).encode())

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

def run():
    server_address = ('localhost', 8767)
    httpd = HTTPServer(server_address, ScoreHandler)
    print("Scorekeeper running")
    httpd.serve_forever()

if __name__ == '__main__':
    run()