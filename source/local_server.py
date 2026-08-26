from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, urllib.parse, subprocess, sys, webbrowser, threading

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'source'/'site-data.json'
sys.path.insert(0,str(ROOT/'source'))
from build_site import build

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        path=urllib.parse.urlparse(path).path
        path=urllib.parse.unquote(path)
        rel=Path(path.lstrip('/'))
        return str(ROOT/rel)
    def do_GET(self):
        if self.path=='/':
            self.send_response(302); self.send_header('Location','/docs/'); self.end_headers(); return
        if self.path.startswith('/api/data'):
            raw=DATA.read_text(encoding='utf-8').encode('utf-8')
            self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw); return
        return super().do_GET()
    def do_POST(self):
        if not self.path.startswith('/api/'):
            self.send_error(404); return
        try:
            n=int(self.headers.get('Content-Length','0')); payload=json.loads(self.rfile.read(n).decode('utf-8'))
            if self.path=='/api/save':
                DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                result={'ok':True,'message':'Source data saved.'}
            elif self.path=='/api/build':
                DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                info=build(payload); result={'ok':True,'message':'Website built.','build':info}
            elif self.path=='/api/backup':
                from datetime import datetime
                p=ROOT/'backups'/f'might-help-site-data-{datetime.now().strftime("%Y-%m-%d-%H%M%S")}.json'
                p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                result={'ok':True,'message':f'Backup saved: {p.name}'}
            else:
                self.send_error(404); return
            raw=json.dumps(result).encode('utf-8'); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
        except Exception as exc:
            raw=json.dumps({'ok':False,'message':str(exc)}).encode('utf-8'); self.send_response(500); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)

if __name__=='__main__':
    port=8000
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print('Might Help local editor/server')
    print(f'Public site:  http://127.0.0.1:{port}/docs/')
    print(f'Offline editor: http://127.0.0.1:{port}/editor/')
    print('Press Ctrl+C to stop.')
    threading.Timer(0.8,lambda:(webbrowser.open(f'http://127.0.0.1:{port}/docs/'),webbrowser.open(f'http://127.0.0.1:{port}/editor/'))).start()
    try: server.serve_forever()
    except KeyboardInterrupt: pass
