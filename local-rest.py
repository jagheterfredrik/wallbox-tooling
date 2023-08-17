import subprocess
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

SQL_CMD = "mysql -u root -pfJmExsJgmKV7cq8H wallbox -B -e '%s'"

def query(q):
    result = subprocess.run(['mysql', '-u', 'root', '-pfJmExsJgmKV7cq8H', 'wallbox', '-B', '-e', q], stdout=subprocess.PIPE)
    try:
        k, v = result.stdout.decode("utf-8")[:-1].split('\n',2)
        return dict(zip(k.split('\t'), v.split('\t')))
    except:
        pass


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()

        if self.path == '/lock':
            query("UPDATE wallbox_config SET `lock`=1")
        elif self.path == '/unlock':
            query("UPDATE wallbox_config SET `lock`=0")
        elif self.path.startswith('/current/'):
            current = self.path[9:]
            query("UPDATE wallbox_config SET max_charging_current="+current)
        else:
            ret = query("SELECT * FROM wallbox_config")
            filtered = {k: v for k, v in ret.items() if k in ['lock', 
'max_charging_current', 'charging_enable']}
            self.wfile.write(bytes(json.dumps(filtered, 
ensure_ascii=False), 'utf-8'))


httpd = HTTPServer(('', 8000), SimpleHTTPRequestHandler)
httpd.serve_forever()
