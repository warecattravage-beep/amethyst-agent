#!/usr/bin/env python3
"""
✦ Onyx Web Dashboard — Serves a local web UI for managing Onyx Agent.
Used automatically on Termux (Android). Access at http://localhost:9091
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core.config import Config

PORT = 9091
log = logging.getLogger("onyx.webdash")

# ── HTML template (single-page app, no external deps) ──

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>✦ Onyx Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0e0e12;color:#e8e8f0;font-family:-apple-system,system-ui,sans-serif;padding:20px}
h1{color:#4aa8f0;font-size:22px;margin-bottom:20px}
h2{color:#4aa8f0;font-size:15px;margin:16px 0 8px}
.card{background:#18181e;border-radius:8px;padding:16px;margin-bottom:12px}
.row{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #222}
.row:last-child{border:0}
label{color:#aaa}
.val{color:#e8e8f0}
.switch{position:relative;width:44px;height:24px;cursor:pointer}
.switch input{opacity:0;width:0;height:0}
.slider{position:absolute;top:0;left:0;right:0;bottom:0;background:#333;border-radius:12px;transition:.3s}
.slider:before{content:"";position:absolute;height:18px;width:18px;left:3px;bottom:3px;background:#888;border-radius:50%;transition:.3s}
.switch input:checked+.slider{background:#33cc66}
.switch input:checked+.slider:before{background:#fff;transform:translateX(20px)}
.btn{background:#4aa8f0;color:#fff;border:0;padding:8px 20px;border-radius:6px;cursor:pointer;font-size:13px}
.btn:hover{opacity:.85}
.btn.green{background:#33cc66}
.btn.red{background:#e64444}
.row .btn{padding:4px 12px;font-size:12px}
textarea{width:100%;min-height:300px;background:#0e0e12;color:#e8e8f0;border:1px solid #333;border-radius:6px;padding:12px;font-family:monospace;font-size:12px}
pre{font-size:11px;color:#aaa;max-height:300px;overflow:auto;white-space:pre-wrap}
.tabs{display:flex;gap:4px;margin-bottom:16px;flex-wrap:wrap}
.tab{padding:8px 16px;border-radius:6px;cursor:pointer;background:#222;color:#aaa;font-size:13px;border:0}
.tab.active{background:#4aa8f0;color:#fff}
.panel{display:none}
.panel.active{display:block}
.status-ok{color:#33cc66}
.status-off{color:#888}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px}
.badge.on{background:#33cc6622;color:#33cc66}
.badge.off{background:#444;color:#888}
input[type=text]{background:#0e0e12;border:1px solid #333;color:#e8e8f0;padding:6px 10px;border-radius:4px;width:200px}
</style>
</head>
<body>
<h1>✦ Onyx Agent</h1>
<div class="tabs" id="tabs"></div>
<div id="panels"></div>

<script>
const API = '';
let config = {};

async function load(){const r=await fetch(API+'/api/config');config=await r.json();render();}
async function toggle(path,val){set(path,val);await fetch(API+'/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(config)});render();}
function set(path,val){const parts=path.split('.');let o=config;for(let i=0;i<parts.length-1;i++)o=o[parts[i]];o[parts[parts.length-1]]=val;}

function tab(name){return `<button class="tab${name==='status'?' active':''}" onclick="show('${name}')">${name.charAt(0).toUpperCase()+name.slice(1)}</button>`}
function panel(id,html){return `<div class="panel${id==='status'?' active':''}" id="p-${id}">${html}</div>`}

function show(id){document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));document.querySelector(`.tab[onclick*="show('${id}')"]`).classList.add('active');document.getElementById('p-'+id).classList.add('active');}

function render(){
const tabs=['status','messengers','models','skills','config','logs'];
document.getElementById('tabs').innerHTML=tabs.map(tab).join('');
const cm=(k,en)=>`<label class="switch"><input type="checkbox" ${en?'checked':''} onchange="toggle('${k}',this.checked)"><span class="slider"></span></label>`;

const mlist=Object.entries(config.messengers||{}).map(([n,c])=>`<div class="row"><label>${n}</label>${cm('messengers.'+n+'.enabled',c.enabled)} <span class="badge ${c.enabled?'on':'off'}">${c.enabled?'on':'off'}</span></div>`).join('');

let statusHtml=`<div class="card"><div class="row"><label>Active Model</label><span class="val">${config.active_model||'none'}</span></div>`;
const actMs=Object.entries(config.messengers||{}).filter(([,c])=>c.enabled).map(([n])=>n).join(', ')||'none';
statusHtml+=`<div class="row"><label>Messengers</label><span class="val">${actMs}</span></div>`;
const actSk=Object.entries(config.skills||{}).filter(([,c])=>c.enabled).map(([n])=>n).join(', ')||'none';
statusHtml+=`<div class="row"><label>Skills</label><span class="val">${actSk}</span></div>`;
statusHtml+=`<div class="row"><label>Config</label><span class="val">${config.agent_name||'Onyx'}</span></div></div>`;

const msgrHtml=`<div class="card">${mlist}</div>`;

const modHtml=`<div class="card">`+Object.entries(config.models||{}).map(([n,c])=>{
const isActive=n===config.active_model;
return `<div class="row"><label><b>${n}</b>${isActive?' ⭐':''}</label><span class="val">${c.model||'?'}</span>${cm('models.'+n+'.enabled',c.enabled)}${!isActive?`<button class="btn" onclick="setActive('${n}')">Use</button>`:'<span class="badge on">active</span>'}</div>`;
}).join('')+`</div>`;

const skillHtml=`<div class="card">`+Object.entries(config.skills||{}).map(([n,c])=>{
return `<div class="row"><label>${n}</label>${cm('skills.'+n+'.enabled',c.enabled)}<span class="badge ${c.enabled?'on':'off'}">${c.enabled?'on':'off'}</span></div>`;
}).join('')+`</div>`;

const cfgHtml=`<div class="card"><textarea id="cfgtext">${safe(JSON.stringify(config,null,2))}</textarea><br><button class="btn green" onclick="saveConfig()">Save & Reload</button></div>`;

const logHtml=`<div class="card"><pre id="logpre">(loading...)</pre><button class="btn" onclick="loadLogs()">Refresh</button></div>`;

document.getElementById('panels').innerHTML=
panel('status',statusHtml)+
panel('messengers',msgrHtml)+
panel('models',modHtml)+
panel('skills',skillHtml)+
panel('config',cfgHtml)+
panel('logs',logHtml);
loadLogs();
}

function safe(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

async function setActive(name){
Object.keys(config.models||{}).forEach(k=>set('models.'+k+'.enabled',k===name));
config.active_model=name;
await fetch(API+'/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(config)});
render();
}

async function saveConfig(){
try{const data=JSON.parse(document.getElementById('cfgtext').value);config=data;await fetch(API+'/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(config)});render();alert('Saved!');}
catch(e){alert('JSON error: '+e.message);}
}

async function loadLogs(){
try{const r=await fetch(API+'/api/logs');const t=await r.text();document.getElementById('logpre').textContent=t||'(no logs)';}
catch(e){document.getElementById('logpre').textContent='Error: '+e.message;}
}

load();
</script>
</body>
</html>"""


# ── HTTP Server ──

class DashboardHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for the web dashboard."""

    def log_message(self, fmt, *args):
        log.debug(fmt, *args)

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text):
        body = text.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if path == '' or path == '/':
            self._send_html(HTML)

        elif path == '/api/config':
            self._send_json(self.server.config.data)

        elif path == '/api/logs':
            log_file = self.server.config.resolve('log_file')
            if log_file.exists():
                lines = log_file.read_text().split('\n')
                self._send_text('\n'.join(lines[-40:]))
            else:
                self._send_text('(no log file yet)')

        elif path == '/api/status':
            cfg = self.server.config
            uptime = cfg.data.get('_uptime', '?')
            self._send_json({
                'model': cfg.get('active_model', 'none'),
                'messengers': cfg.active_messengers,
                'skills': cfg.enabled_skills,
                'uptime': uptime,
            })

        else:
            self._send_json({'error': 'not found'}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if path == '/api/config':
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length).decode()
            try:
                data = json.loads(raw)
                self.server.config.data = data
                self.server.config.save()
                log.info("Config updated via web dashboard")
                self._send_json({'status': 'ok'})
            except json.JSONDecodeError as e:
                self._send_json({'error': str(e)}, 400)
        else:
            self._send_json({'error': 'not found'}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def run(config_path: str = "config.json"):
    """Start the web dashboard server."""
    config = Config(config_path)
    server = HTTPServer(('127.0.0.1', PORT), DashboardHandler)
    server.config = config

    url = f"http://localhost:{PORT}"
    print(f"\n  ✦ Onyx Dashboard — Web Mode")
    print(f"  ───────────────────────────")
    print(f"  Open in browser: {url}")
    print(f"  Press Ctrl+C to stop\n")

    config.data.setdefault('_uptime', datetime.now().isoformat())
    config.save()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Dashboard stopped.")
        server.server_close()


if __name__ == "__main__":
    run()
