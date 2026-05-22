#!/usr/bin/env python3
"""
✦ Amethyst Web Dashboard - Serves a local web UI for managing Amethyst Agent.
Used automatically on Termux (Android). Access at http://localhost:9091
"""
from __future__ import annotations

import json
import logging
import os
import platform as plat
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core.config import Config

PORT = 9091
log = logging.getLogger("amethyst.webdash")

# ── HTML template (single-page app, no external deps) ──

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>✦ Amethyst Dashboard</title>
<style>
:root{--bg:#0a0a0f;--bg-card:#13131c;--bg-card-alt:#191926;--text:#e2e2f0;--text-dim:#7a7a8e;--text-muted:#5a5a6e;--accent-v:#9b6dff;--accent-c:#4ac7f0;--accent-g:#33cc66;--accent-r:#e64444;--accent-y:#e6c644;--border:#1e1e2e;--border-focus:#2a2a40;--radius:10px;--radius-sm:6px;--shadow:0 2px 12px rgba(0,0,0,.4);--font:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;--font-mono:'JetBrains Mono','Fira Code','Cascadia Code','Consolas',monospace}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html{font-size:15px}
body{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh;line-height:1.5;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
/* Scrollbar */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:#2a2a3e;border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#3a3a4e}
/* Header */
.header{background:linear-gradient(135deg,#13131c 0%,#18182a 100%);border-bottom:1px solid var(--border);padding:16px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;position:sticky;top:0;z-index:10}
.header h1{font-size:18px;font-weight:700;background:linear-gradient(135deg,var(--accent-v),var(--accent-c));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-.3px}
.header-sub{font-size:12px;color:var(--text-dim);-webkit-text-fill-color:var(--text-dim);font-weight:400;margin-top:1px}
.header-right{display:flex;align-items:center;gap:12px}
.online-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--accent-g);box-shadow:0 0 6px rgba(51,204,102,.5);animation:pulse-dot 2s infinite}
@keyframes pulse-dot{0%,100%{opacity:1}50%{opacity:.5}}
/* Tabs */
.tab-bar{display:flex;gap:2px;padding:0 24px;background:var(--bg);border-bottom:1px solid var(--border);overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch;scrollbar-width:none}
.tab-bar::-webkit-scrollbar{display:none}
.tab-btn{flex-shrink:0;padding:10px 18px;cursor:pointer;background:transparent;color:var(--text-dim);font-size:13px;border:0;border-bottom:2px solid transparent;transition:color .2s,border-color .2s;white-space:nowrap;font-family:var(--font)}
.tab-btn:hover{color:var(--text);background:rgba(155,109,255,.06)}
.tab-btn.active{color:var(--accent-v);border-bottom-color:var(--accent-v);font-weight:600}
/* Content */
.content{padding:20px 24px 40px;max-width:900px;margin:0 auto}
/* Cards */
.card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:18px;margin-bottom:14px;transition:border-color .2s}
.card:hover{border-color:var(--border-focus)}
.card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid var(--border)}
.card-header h2{font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:.6px;color:var(--text-dim)}
.card-body{font-size:14px}
/* Status grid */
.status-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}
.stat-item{background:var(--bg-card-alt);border-radius:var(--radius-sm);padding:12px;text-align:center}
.stat-item .stat-icon{font-size:20px;margin-bottom:4px;display:block}
.stat-item .stat-val{font-size:15px;font-weight:600;color:var(--text)}
.stat-item .stat-label{font-size:11px;color:var(--text-muted);margin-top:2px}
/* Rows */
.row{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);gap:8px}
.row:last-child{border-bottom:0}
.row .label{color:var(--text-dim);font-size:13px;flex-shrink:0}
.row .val{color:var(--text);font-size:13px;text-align:right;word-break:break-all}
.row .val.mono{font-family:var(--font-mono);font-size:12px}
/* Status badges */
.badge{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;letter-spacing:.2px}
.badge.on{background:rgba(51,204,102,.12);color:var(--accent-g)}
.badge.off{background:rgba(90,90,110,.2);color:var(--text-muted)}
.badge.active{background:rgba(155,109,255,.15);color:var(--accent-v);border:1px solid rgba(155,109,255,.25)}
.badge .dot{display:inline-block;width:6px;height:6px;border-radius:50%}
.badge.on .dot{background:var(--accent-g);box-shadow:0 0 4px rgba(51,204,102,.6)}
.badge.off .dot{background:var(--text-muted)}
.badge.active .dot{background:var(--accent-v);box-shadow:0 0 4px rgba(155,109,255,.6)}
/* Toggle switch */
.switch{position:relative;width:40px;height:22px;flex-shrink:0}
.switch input{opacity:0;width:0;height:0}
.slider{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:#2a2a3e;border-radius:11px;transition:.25s}
.slider:before{content:"";position:absolute;height:16px;width:16px;left:3px;bottom:3px;background:#6a6a7e;border-radius:50%;transition:.25s}
.switch input:checked+.slider{background:rgba(51,204,102,.35)}
.switch input:checked+.slider:before{background:var(--accent-g);transform:translateX(18px);box-shadow:0 0 6px rgba(51,204,102,.4)}
/* Buttons */
.btn{display:inline-flex;align-items:center;gap:6px;background:var(--accent-v);color:#fff;border:0;padding:7px 16px;border-radius:var(--radius-sm);cursor:pointer;font-size:12px;font-weight:500;font-family:var(--font);transition:opacity .2s,transform .1s}
.btn:hover{opacity:.88}
.btn:active{transform:scale(.97)}
.btn.sm{padding:4px 10px;font-size:11px}
.btn.ghost{background:transparent;color:var(--text-dim);border:1px solid var(--border)}
.btn.ghost:hover{background:var(--bg-card-alt);color:var(--text)}
.btn.green{background:var(--accent-g)}
.btn.red{background:var(--accent-r)}
.btn.amber{background:var(--accent-y);color:#1a1a1a}
/* System info card */
.sysinfo-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px}
.sysinfo-item{background:var(--bg-card-alt);border-radius:var(--radius-sm);padding:10px 12px;display:flex;align-items:center;gap:10px}
.sysinfo-item .si-icon{font-size:16px;flex-shrink:0;width:28px;height:28px;display:flex;align-items:center;justify-content:center;background:rgba(155,109,255,.08);border-radius:6px}
.sysinfo-item .si-text{min-width:0}
.sysinfo-item .si-label{font-size:10px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px}
.sysinfo-item .si-val{font-size:13px;color:var(--text);font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
/* Chat terminal */
.chat-terminal{background:#0c0c12;border:1px solid #1a2a1a;border-radius:var(--radius-sm);padding:0;overflow:hidden;max-height:520px;display:flex;flex-direction:column}
.term-header{background:#0f0f18;border-bottom:1px solid #1a2a1a;padding:8px 14px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px}
.term-header .term-title{font-family:var(--font-mono);font-size:11px;color:#4a8a4a;letter-spacing:.3px}
.term-header .term-title::before{content:"⬤ ";color:#4aca4a}
.term-body{flex:1;overflow-y:auto;overflow-x:hidden;padding:10px 14px;font-family:var(--font-mono);font-size:12px;line-height:1.6;min-height:300px}
.term-line{padding:2px 0;white-space:pre-wrap;word-break:break-all;display:flex;gap:8px}
.term-time{color:#5a8a5a;flex-shrink:0;user-select:none}
.term-role{flex-shrink:0;min-width:48px;font-weight:600}
.term-role.user{color:#7acf7a}
.term-role.amethyst{color:#6abfda}
.term-role.system{color:#8a7ada}
.term-role.assistant{color:#6abfda}
.term-text{color:#d0d8d0;word-break:break-word}
.term-empty{color:#3a5a3a;padding:40px 0;text-align:center;font-size:13px}
.term-ctrl{display:flex;gap:6px}
.term-autorefresh{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--text-muted)}
.term-autorefresh input[type=checkbox]{accent-color:var(--accent-g);width:14px;height:14px}
/* JSON editor */
.json-editor{width:100%;min-height:300px;background:#0c0c12;color:var(--text);border:1px solid var(--border);border-radius:var(--radius-sm);padding:14px;font-family:var(--font-mono);font-size:12px;line-height:1.5;resize:vertical;tab-size:2}
.json-editor:focus{border-color:var(--accent-v);outline:none;box-shadow:0 0 0 2px rgba(155,109,255,.1)}
/* Log viewer */
.log-viewer{background:#0c0c12;border:1px solid var(--border);border-radius:var(--radius-sm);padding:14px;font-family:var(--font-mono);font-size:11px;line-height:1.5;max-height:450px;overflow:auto;white-space:pre-wrap;color:#9a9aaa}
/* Loading/error */
.loading{color:var(--text-dim);text-align:center;padding:40px 0;font-size:13px}
.error{color:var(--accent-r);text-align:center;padding:20px}
/* Responsive */
@media(max-width:640px){
html{font-size:14px}
.header{padding:12px 14px}
.header h1{font-size:16px}
.tab-bar{padding:0 14px}
.tab-btn{padding:8px 12px;font-size:12px}
.content{padding:14px 14px 30px}
.card{padding:14px}
.status-grid{grid-template-columns:repeat(2,1fr)}
.sysinfo-grid{grid-template-columns:1fr}
.chat-terminal{max-height:420px}
.term-body{min-height:220px}
}
@media(max-width:400px){
.status-grid{grid-template-columns:1fr}
}
/* Animations */
@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.panel{display:none;animation:fadeIn .25s ease-out}
.panel.active{display:block}
</style>
</head>
<body>

<div class="header">
<div>
<h1>✦ Amethyst Agent <span class="header-sub">dashboard</span></h1>
</div>
<div class="header-right">
<span class="online-dot" title="Online"></span>
<span style="font-size:12px;color:var(--text-dim)" id="status-summary">initializing...</span>
</div>
</div>

<div class="tab-bar" id="tabBar"></div>

<div class="content" id="content">
<div id="loadingMsg" class="loading">✦ Loading...</div>
</div>

<script>
const API = '';
let config = {};
let autoRefresh = true;
let refreshInterval = null;

// ── API ──

async function apiGet(path){const r=await fetch(API+path);return r.json();}
async function apiPost(path,body){const r=await fetch(API+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});return r.json();}
async function apiText(path){const r=await fetch(API+path);return r.text();}

// ── Load ──

async function load(){
try{
const [cfg,sys] = await Promise.all([apiGet('/api/config'),apiGet('/api/sysinfo')]);
config = cfg;
render(cfg,sys);
checkStatus();
}catch(e){
document.getElementById('loadingMsg').innerHTML='<span class="error">✗ Connection error: '+e.message+'</span>';
}
}

function checkStatus(){
const anyOn = Object.values(config.messengers||{}).some(m=>m.enabled);
document.getElementById('status-summary').textContent = anyOn ? 'active' : 'standby';
}

// ── Config Mutations ──

function toggle(path,val){
set(path,val);
apiPost('/api/config',config).then(()=>{checkStatus();renderAll();});
}
function set(path,val){
const parts=path.split('.');let o=config;
for(let i=0;i<parts.length-1;i++)o=o[parts[i]];
o[parts[parts.length-1]]=val;
}

async function setActive(name){
Object.keys(config.models||{}).forEach(k=>set('models.'+k+'.enabled',k===name));
config.active_model=name;
await apiPost('/api/config',config);
renderAll();
}

async function saveConfig(){
try{
const data=JSON.parse(document.getElementById('cfgtext').value);
config=data;
await apiPost('/api/config',config);
renderAll();
alert('✓ Config saved');
}catch(e){
alert('✗ JSON error: '+e.message);
}
}

// ── Tabs ──

const TABS = ['status','terminal','messengers','models','skills','config','logs'];
let currentTab = 'status';

function renderTabs(activeId){
const bar = document.getElementById('tabBar');
bar.innerHTML = TABS.map(t=>{
const label = t==='terminal' ? '💬 Terminal' : t.charAt(0).toUpperCase()+t.slice(1);
return `<button class="tab-btn${t===activeId?' active':''}" onclick="showTab('${t}')" data-tab="${t}">${label}</button>`;
}).join('');
}

function showTab(id){
currentTab = id;
renderTabs(id);
document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
const el = document.getElementById('panel-'+id);
if(el) el.classList.add('active');
if(id==='terminal') loadChatLog();
if(id==='logs') loadRawLogs();
}

// ── Render ──

function render(cfg,sys){
renderTabs('status');
renderStatusPanel(cfg,sys);
renderTerminalPanel();
renderMessengersPanel(cfg);
renderModelsPanel(cfg);
renderSkillsPanel(cfg);
renderConfigPanel(cfg);
renderLogsPanel();
showTab(currentTab);
}

function renderAll(){
apiGet('/api/config').then(c=>{config=c;checkStatus();});
apiGet('/api/sysinfo').then(s=>{renderStatusPanel(config,s);});
renderMessengersPanel(config);
renderModelsPanel(config);
renderSkillsPanel(config);
renderConfigPanel(config);
}

function safe(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

// ── Status Panel ──

function renderStatusPanel(cfg,sys){
const activeM = cfg.active_model||'none';
const msgrOn = Object.entries(cfg.messengers||{}).filter(([,c])=>c.enabled).map(([n])=>n);
const skillOn = Object.entries(cfg.skills||{}).filter(([,c])=>c.enabled).map(([n])=>n);

const si = sys||{hostname:'?',uptime:'?',python_version:'?',platform:'?',machine:'?'};

const html = `
<div class="card">
<div class="card-header"><h2>🖥 System</h2></div>
<div class="card-body">
<div class="sysinfo-grid">
<div class="sysinfo-item"><div class="si-icon">💻</div><div class="si-text"><div class="si-label">Hostname</div><div class="si-val">${safe(si.hostname)}</div></div></div>
<div class="sysinfo-item"><div class="si-icon">⏱</div><div class="si-text"><div class="si-label">Uptime</div><div class="si-val">${safe(si.uptime)}</div></div></div>
<div class="sysinfo-item"><div class="si-icon">🐍</div><div class="si-text"><div class="si-label">Python</div><div class="si-val">${safe(si.python_version)}</div></div></div>
<div class="sysinfo-item"><div class="si-icon">💿</div><div class="si-text"><div class="si-label">OS</div><div class="si-val">${safe(si.platform)}</div></div></div>
<div class="sysinfo-item"><div class="si-icon">🔧</div><div class="si-text"><div class="si-label">Arch</div><div class="si-val">${safe(si.machine)}</div></div></div>
</div>
</div>
</div>

<div class="card">
<div class="card-header"><h2>📊 Status</h2></div>
<div class="card-body">
<div class="status-grid">
<div class="stat-item"><span class="stat-icon">🧠</span><div class="stat-val">${safe(activeM)}</div><div class="stat-label">Active Model</div></div>
<div class="stat-item"><span class="stat-icon">💬</span><div class="stat-val">${msgrOn.length}</div><div class="stat-label">Messengers</div></div>
<div class="stat-item"><span class="stat-icon">🔧</span><div class="stat-val">${skillOn.length}</div><div class="stat-label">Skills</div></div>
<div class="stat-item"><span class="stat-icon">📝</span><div class="stat-val" id="chatCountStat">—</div><div class="stat-label">Messages</div></div>
</div>
<div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:6px">
${msgrOn.map(n=>`<span class="badge on"><span class="dot"></span>${safe(n)}</span>`).join('')}
${skillOn.map(n=>`<span class="badge active"><span class="dot"></span>${safe(n)}</span>`).join('')}
${msgrOn.length===0&&skillOn.length===0?'<span class="badge off"><span class="dot"></span>no active components</span>':''}
</div>
</div>
</div>
`;
setPanel('status',html);
}

// ── Terminal Panel ──

function renderTerminalPanel(){
const html = `
<div class="card" style="padding:0;border:0;background:transparent">
<div class="chat-terminal">
<div class="term-header">
<div class="term-title">amethyst-chat</div>
<div class="term-ctrl">
<label class="term-autorefresh"><input type="checkbox" checked onchange="toggleAutoRefresh(this.checked)"> auto</label>
<button class="btn sm ghost" onclick="loadChatLog()">↻ Refresh</button>
<button class="btn sm ghost" onclick="clearChatLog()">Clear cache</button>
</div>
</div>
<div class="term-body" id="termBody">
<div class="term-empty">⏳ Loading conversation log...</div>
</div>
</div>
</div>
`;
setPanel('terminal',html);
}

function toggleAutoRefresh(on){
autoRefresh = on;
if(refreshInterval){clearInterval(refreshInterval);refreshInterval=null;}
if(on) refreshInterval = setInterval(loadChatLog, 5000);
}

async function loadChatLog(){
try{
const text = await apiText('/api/logs');
const body = document.getElementById('termBody');
if(!body) return;

const lines = text.split('\n').filter(l=>l.trim()).slice(-80);
if(lines.length===0){
body.innerHTML='<div class="term-empty">⏳ No conversation logs yet.</div>';
return;
}

// Parse log lines into entries
const entries = lines.map(line=>{
// Try: "HH:MM LVL   name   message"
const m = line.match(/^(\d{2}:\d{2})\s+\S+\s+\S+\s+(.+)$/);
if(m) return {time:m[1], text:m[2]};
return {time:'--:--', text:line};
});

// Extract chat-like entries (messages from messenger, engine responses)
let chatLines = [];
entries.forEach(e=>{
const t = e.text;
// Match incoming messages: "Message from X (telegram): text"
let m = t.match(/^Message from\s+(.+?)\s*\(([^)]+)\):\s*(.+)$/);
if(m){
chatLines.push({time:e.time, role:'user', name:m[1], text:m[2]});
return;
}
// Match log entries that start with user/assistant (memory entries)
m = t.match(/^(user|assistant)\s*[|:]\s*(.+)$/i);
if(m){
chatLines.push({time:e.time, role:m[1].toLowerCase(), text:m[2]});
return;
}
// Generic important entries (errors, warnings, model responses)
m = t.match(/^(ERR|WRN|INF)\s+/);
if(t.includes('Error')||t.includes('error')||t.includes('timed out')||t.includes('Ready')||t.includes('Model initialized')){
chatLines.push({time:e.time, role:'system', text:t.replace(/^(ERR|WRN|INF)\s+/,'').trim()});
}
});

// Fallback: show raw lines if no structured entries
if(chatLines.length===0){
chatLines = entries.map(e=>({time:e.time, role:'system', text:e.text}));
}

const last = chatLines.slice(-60);
body.innerHTML = last.map(l=>{
const roleClass = l.role==='user'?'user': l.role==='assistant'||l.role==='amethyst'?'amethyst':'system';
const nameLabel = l.role==='user'? (l.name||'user') : l.role==='system'?'sys':'amethyst';
const cleanText = safe(l.text).replace(/\n/g,'↵ ');
return `<div class="term-line"><span class="term-time">[${safe(l.time||'--:--')}]</span><span class="term-role ${roleClass}">${safe(nameLabel)}</span><span class="term-text">${cleanText}</span></div>`;
}).join('');

body.scrollTop = body.scrollHeight;

// Update message count stat
const stat = document.getElementById('chatCountStat');
if(stat) stat.textContent = chatLines.length;

}catch(e){
const body = document.getElementById('termBody');
if(body) body.innerHTML=`<div class="term-empty">✗ Error loading logs: ${safe(e.message)}</div>`;
}
}

function clearChatLog(){
const body = document.getElementById('termBody');
if(body) body.innerHTML='<div class="term-empty">⏳ Cache cleared, waiting for new entries...</div>';
}

// ── Messengers Panel ──

function renderMessengersPanel(cfg){
const list = Object.entries(cfg.messengers||{});
const html = `<div class="card"><div class="card-header"><h2>📨 Messengers</h2></div><div class="card-body">${
list.length===0?'<div style="padding:12px;color:var(--text-muted);text-align:center;font-size:13px">No messengers configured</div>':
list.map(([n,c])=>`<div class="row"><span class="label"><b>${safe(n)}</b></span><span class="badge ${c.enabled?'on':'off'}"><span class="dot"></span>${c.enabled?'on':'off'}</span><label class="switch"><input type="checkbox" ${c.enabled?'checked':''} onchange="toggle('messengers.${n}.enabled',this.checked)"><span class="slider"></span></label></div>`
).join('')
}</div></div>`;
setPanel('messengers',html);
}

// ── Models Panel ──

function renderModelsPanel(cfg){
const list = Object.entries(cfg.models||{});
const active = cfg.active_model||'none';
const html = `<div class="card"><div class="card-header"><h2>🧠 Models</h2></div><div class="card-body">${
list.length===0?'<div style="padding:12px;color:var(--text-muted);text-align:center;font-size:13px">No models configured</div>':
list.map(([n,c])=>{
const isActive = n===active;
return `<div class="row"><span class="label"><b>${safe(n)}</b>${c.model?` <span style="color:var(--text-muted);font-weight:400">${safe(c.model)}</span>`:''}</span>${isActive?'<span class="badge active"><span class="dot"></span>active</span>':`<button class="btn sm ghost" onclick="setActive('${n}')">Use</button>`}<label class="switch"><input type="checkbox" ${c.enabled?'checked':''} onchange="toggle('models.${n}.enabled',this.checked)"><span class="slider"></span></label></div>`;
}).join('')
}</div></div>`;
setPanel('models',html);
}

// ── Skills Panel ──

function renderSkillsPanel(cfg){
const list = Object.entries(cfg.skills||{});
const html = `<div class="card"><div class="card-header"><h2>🔧 Skills</h2></div><div class="card-body">${
list.length===0?'<div style="padding:12px;color:var(--text-muted);text-align:center;font-size:13px">No skills configured</div>':
list.map(([n,c])=>`<div class="row"><span class="label"><b>${safe(n)}</b></span><span class="badge ${c.enabled?'on':'off'}"><span class="dot"></span>${c.enabled?'on':'off'}</span><label class="switch"><input type="checkbox" ${c.enabled?'checked':''} onchange="toggle('skills.${n}.enabled',this.checked)"><span class="slider"></span></label></div>`
).join('')
}</div></div>`;
setPanel('skills',html);
}

// ── Config Panel ──

function renderConfigPanel(cfg){
const html = `<div class="card"><div class="card-header"><h2>⚙ Config</h2></div><div class="card-body"><textarea class="json-editor" id="cfgtext">${safe(JSON.stringify(cfg,null,2))}</textarea><div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap"><button class="btn green" onclick="saveConfig()">✓ Save & Reload</button><button class="btn ghost" onclick="document.getElementById('cfgtext').value=JSON.stringify(config,null,2)">↻ Reset</button></div></div></div>`;
setPanel('config',html);
}

// ── Logs Panel ──

function renderLogsPanel(){
const html = `<div class="card"><div class="card-header"><h2>📋 Raw Logs</h2><button class="btn sm ghost" onclick="loadRawLogs()">↻ Refresh</button></div><div class="card-body"><pre class="log-viewer" id="logViewer">⏳ Loading...</pre></div></div>`;
setPanel('logs',html);
}

async function loadRawLogs(){
try{
const text = await apiText('/api/logs');
const el = document.getElementById('logViewer');
if(el) el.textContent = text||'(no logs)';
}catch(e){
const el = document.getElementById('logViewer');
if(el) el.textContent = 'Error: '+e.message;
}
}

// ── Helpers ──

function setPanel(id,html){
let el = document.getElementById('panel-'+id);
if(!el){
el = document.createElement('div');
el.id = 'panel-'+id;
el.className = 'panel';
document.getElementById('content').appendChild(el);
}
el.innerHTML = html;
}

// ── Init ──

document.addEventListener('DOMContentLoaded',()=>{
load();
refreshInterval = setInterval(loadChatLog, 5000);
});
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
                self._send_text('\n'.join(lines[-80:]))
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

        elif path == '/api/sysinfo':
            """Return system information for the dashboard."""
            import platform as plat
            import os
            # Uptime from /proc/uptime (Linux) or fallback
            uptime_str = '?'
            try:
                with open('/proc/uptime', 'r') as f:
                    secs = float(f.read().split()[0])
                    days = int(secs // 86400)
                    hours = int((secs % 86400) // 3600)
                    mins = int((secs % 3600) // 60)
                    if days > 0:
                        uptime_str = f"{days}d {hours}h {mins}m"
                    else:
                        uptime_str = f"{hours}h {mins}m"
            except Exception:
                pass

            py_ver = sys.version.split()[0]
            try:
                plat_str = plat.platform()
            except Exception:
                plat_str = sys.platform

            self._send_json({
                'hostname': plat.node(),
                'uptime': uptime_str,
                'python_version': py_ver,
                'platform': plat_str,
                'machine': plat.machine(),
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
    print(f"\n  ✦ Amethyst Dashboard - Web Mode")
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
