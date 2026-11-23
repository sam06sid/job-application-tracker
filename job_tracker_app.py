"""
Job Application Tracker: a web-style front end for your C++ program.

Your C++ program is NOT changed. This script starts the compiled .exe in the
background, and the web page you see in your browser sends its menu choices to
it and shows what it prints. All the real work (linked list, hash table, BST,
min-heap, stack, queue, graph, merge sort, binary search) happens in C++.

How to run:
  1. Compile your C++ file in Dev C++ (this creates an .exe).
  2. Put this file in the same folder as the .exe.
  3. Run:  python job_tracker_app.py     (a browser tab opens by itself)
  Press Ctrl+C in the black window to stop.
"""

import json
import os
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MENU_PROMPT = "Enter choice: "


# ----------------------------------------------------------------------
# Talks to the C++ program like a person typing in the console
# ----------------------------------------------------------------------
class Engine:
    def __init__(self, exe_path):
        flags = 0x08000000 if os.name == "nt" else 0  # hide the console on Windows
        self.proc = subprocess.Popen(
            [exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=os.path.dirname(os.path.abspath(exe_path)),
            bufsize=0,
            creationflags=flags,
        )
        self.lock = threading.Lock()
        self._read_until_prompt()  # swallow the first menu

    def _read_until_prompt(self):
        data = b""
        while True:
            chunk = self.proc.stdout.read(4096)
            if not chunk:
                break
            data += chunk
            if data.endswith(b": "):
                break
        return data.decode("utf-8", "replace").replace("\r\n", "\n")

    def _send(self, text):
        self.proc.stdin.write((text + "\n").encode("utf-8"))
        self.proc.stdin.flush()

    @staticmethod
    def _cut_menu(text):
        marker = text.find("JOB APPLICATION TRACKING SYSTEM")
        if marker == -1:
            return text
        title_line = text.rfind("\n", 0, marker)
        bar_line = text.rfind("\n", 0, title_line)
        return text[: max(bar_line, 0)]

    def run(self, choice, answers):
        """Pick a menu option, answer its questions, return what the program printed."""
        with self.lock:
            answers = [str(a) for a in answers]
            transcript = ""
            self._send(str(choice))
            while True:
                text = self._read_until_prompt()
                if not text:
                    return {"transcript": transcript, "result": "The C++ program has closed."}
                last_line = text.split("\n")[-1]
                if last_line.endswith(MENU_PROMPT):
                    result = self._cut_menu(text)
                    return {"transcript": transcript + result, "result": result}
                transcript += text
                reply = answers.pop(0) if answers else "0"
                self._send(reply)
                transcript += reply + "\n"

    def close(self):
        try:
            self._send("0")
            self.proc.wait(timeout=2)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass


# ----------------------------------------------------------------------
# Tiny web server
# ----------------------------------------------------------------------
engine = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the console quiet

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
        else:
            self._send(404, b"Not found", "text/plain")

    def do_POST(self):
        if self.path != "/api/run":
            self._send(404, b"Not found", "text/plain")
            return
        try:
            size = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(size).decode("utf-8"))
            out = engine.run(int(req["choice"]), req.get("answers", []))
        except Exception as e:
            out = {"transcript": "", "result": "Error: %s" % e}
        self._send(200, json.dumps(out).encode("utf-8"), "application/json")


def find_exe():
    here = os.path.dirname(os.path.abspath(__file__))
    ext = ".exe" if os.name == "nt" else ""
    for name in sorted(os.listdir(here)):
        low = name.lower()
        if low.endswith((".py", ".cpp", ".html")) or "gui" in low or "app.py" in low:
            continue
        if ext and not low.endswith(ext):
            continue
        if "job" in low or "application" in low:
            path = os.path.join(here, name)
            if os.path.isfile(path) and (ext or os.access(path, os.X_OK)):
                return path
    return None


def main():
    global engine
    exe = sys.argv[1] if len(sys.argv) > 1 else find_exe()
    if not exe or not os.path.isfile(exe):
        print("Could not find your compiled C++ program (.exe) in this folder.")
        print("Compile the .cpp in Dev C++ first, or run:")
        print("   python job_tracker_app.py path\\to\\your_program.exe")
        input("Press Enter to close...")
        return
    engine = Engine(exe)

    server = None
    for port in range(8000, 8020):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    if server is None:
        print("No free port found between 8000 and 8019.")
        engine.close()
        return

    url = "http://127.0.0.1:%d" % server.server_address[1]
    print("Using C++ program:", os.path.basename(exe))
    print("Job Application Tracker is running at", url)
    print("Press Ctrl+C here to stop.")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        engine.close()
        server.server_close()


HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Job Application Tracker</title>
<style>
:root{
  --bg:#f4f5fb; --card:#ffffff; --ink:#1a1d3b; --muted:#6a6f92; --line:#e7e9f4;
  --accent:#5b5bf0; --accent-soft:#ececff; --side1:#1b1848; --side2:#2e2a7a;
  --green:#12a56b; --green-soft:#dcf5ea; --amber:#d98a0b; --amber-soft:#fff1d6;
  --red:#e04b5a; --red-soft:#fde3e6; --blue:#2f7be0; --blue-soft:#e0edff;
  --shadow:0 1px 2px rgba(26,29,59,.05),0 8px 24px rgba(26,29,59,.06);
}
:root[data-theme="dark"]{
  --bg:#0f1024; --card:#181a38; --ink:#eceefe; --muted:#9a9fc6; --line:#262a52;
  --accent:#7c7cff; --accent-soft:#25255a; --side1:#0b0a24; --side2:#161448;
  --green-soft:#10372c; --amber-soft:#3d2f0e; --red-soft:#40181e; --blue-soft:#14305a;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.25);
}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--ink);font-family:"Segoe UI",system-ui,-apple-system,Roboto,sans-serif;font-size:14px;line-height:1.45}
svg.i{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;flex:none}
button{font:inherit;cursor:pointer}

/* layout */
.shell{display:grid;grid-template-columns:240px 1fr;min-height:100vh}
.side{background:linear-gradient(180deg,var(--side1),var(--side2));color:#cfd0ff;padding:22px 14px;position:sticky;top:0;height:100vh;display:flex;flex-direction:column}
.brand{display:flex;align-items:center;gap:10px;padding:0 10px 22px;color:#fff;font-weight:700;font-size:16px;line-height:1.2;letter-spacing:.2px}
.logo{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#8b8bff,#c084fc);display:grid;place-items:center;color:#fff}
.nav a{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:10px;color:#cfd0ff;text-decoration:none;margin-bottom:4px;font-weight:500;cursor:pointer}
.nav a:hover{background:rgba(255,255,255,.08)}
.nav a.on{background:rgba(255,255,255,.16);color:#fff}
.side .foot{margin-top:auto;font-size:12px;color:#9fa0e0;padding:10px;border-top:1px solid rgba(255,255,255,.1)}
.side .foot b{color:#fff}
.main{padding:22px 28px 90px;min-width:0}
.top{display:flex;align-items:center;gap:12px;margin-bottom:20px;flex-wrap:wrap}
.top>div:first-child{flex:1;min-width:200px}
.top h1{font-size:24px;margin:0}
.top p{margin:2px 0 0;color:var(--muted);font-size:13px;font-weight:400}
.btn{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);background:var(--card);color:var(--ink);padding:9px 14px;border-radius:10px;font-weight:600}
.btn:hover{border-color:var(--accent)}
.btn.primary{background:linear-gradient(135deg,var(--accent),#8b5cf6);color:#fff;border:0;box-shadow:0 6px 16px rgba(91,91,240,.35)}
.btn.primary:hover{filter:brightness(1.08)}
.btn.sm{padding:6px 10px;font-size:12.5px;border-radius:8px}
.btn.icon{padding:9px}

/* cards */
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);padding:18px}
.card h3{margin:0 0 12px;font-size:15px;display:flex;align-items:center;gap:8px}
.card h3 .tag{margin-left:auto}
.grid{display:grid;gap:16px}
.g4{grid-template-columns:repeat(4,1fr)} .g2{grid-template-columns:1.2fr 1fr} .g3{grid-template-columns:repeat(3,1fr)}
@media(max-width:1100px){.g4{grid-template-columns:repeat(2,1fr)}.g2{grid-template-columns:1fr}.g3{grid-template-columns:repeat(2,1fr)}}
@media(max-width:820px){.shell{grid-template-columns:1fr}.side{position:static;height:auto;flex-direction:row;overflow:auto;padding:10px}.brand{padding:0 12px 0 4px}.side .foot{display:none}.nav{display:flex}.nav a{white-space:nowrap}.main{padding:16px 14px 90px}}

.hero{background:linear-gradient(120deg,#4f46e5,#8b5cf6 60%,#c084fc);color:#fff;border-radius:20px;padding:24px 26px;margin-bottom:16px;position:relative;overflow:hidden}
.hero h2{margin:0 0 4px;font-size:22px}.hero p{margin:0;opacity:.9}
.hero:after{content:"";position:absolute;right:-40px;top:-60px;width:220px;height:220px;border-radius:50%;background:rgba(255,255,255,.12)}
.stat{display:flex;gap:14px;align-items:center}
.stat .ico{width:44px;height:44px;border-radius:12px;display:grid;place-items:center;font-size:18px;font-weight:700}
.stat .num{font-size:28px;font-weight:700;line-height:1}
.stat .lbl{color:var(--muted);font-size:12.5px;margin-top:4px}

/* tags and badges */
.badge{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600}
.b-Applied{background:var(--blue-soft);color:var(--blue)} .b-Interview{background:var(--amber-soft);color:var(--amber)}
.b-Selected{background:var(--green-soft);color:var(--green)} .b-Rejected{background:var(--red-soft);color:var(--red)} .b-other{background:var(--accent-soft);color:var(--accent)}
.tag{display:inline-block;padding:2px 9px;border-radius:6px;background:var(--accent-soft);color:var(--accent);font-size:11.5px;font-weight:600}
.muted{color:var(--muted)}

/* applications */
.toolbar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:14px}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{border:1px solid var(--line);background:var(--card);color:var(--muted);padding:6px 14px;border-radius:999px;font-weight:600;font-size:13px}
.chip.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.search{display:flex;gap:8px;margin-left:auto;flex-wrap:wrap}
input,select,textarea{font:inherit;color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:10px;padding:9px 12px;outline:none;min-width:0}
input:focus,select:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.apps{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:16px}
.app{position:relative;transition:transform .15s,box-shadow .15s}
.app:hover{transform:translateY(-3px)}
.app .head{display:flex;gap:12px;align-items:center;margin-bottom:12px}
.avatar{width:42px;height:42px;border-radius:12px;display:grid;place-items:center;color:#fff;font-weight:700;font-size:17px;flex:none}
.app .co{font-weight:700;font-size:15.5px}.app .role{color:var(--muted);font-size:13px}
.app .id{margin-left:auto;color:var(--muted);font-size:12px;font-weight:600}
.meta{display:flex;flex-wrap:wrap;gap:8px 14px;margin:10px 0 14px;font-size:13px;color:var(--muted)}
.meta b{color:var(--ink);font-weight:600}
.due-late{color:var(--red)!important} .due-soon{color:var(--amber)!important}
.app .foot{display:flex;align-items:center;gap:8px;justify-content:space-between}
.pill-u{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;padding:3px 9px;border-radius:999px}
.u1,.u2{background:var(--red-soft);color:var(--red)} .u3{background:var(--amber-soft);color:var(--amber)} .u4,.u5{background:var(--green-soft);color:var(--green)}
select.status{padding:5px 8px;border-radius:8px;font-weight:600;font-size:12.5px}
.banner{padding:12px 16px;border-radius:12px;margin-bottom:14px;background:var(--accent-soft);color:var(--accent);font-weight:600;display:flex;gap:10px;align-items:center}
.banner.bad{background:var(--red-soft);color:var(--red)} .banner.ok{background:var(--green-soft);color:var(--green)}

/* lists */
.row{display:flex;align-items:center;gap:12px;padding:11px 0;border-bottom:1px solid var(--line)}
.row:last-child{border-bottom:0}
.rank{width:30px;height:30px;border-radius:9px;background:var(--accent-soft);color:var(--accent);display:grid;place-items:center;font-weight:700;flex:none}
.row .t{font-weight:600}.row .s{color:var(--muted);font-size:12.5px}.row .end{margin-left:auto;text-align:right}
.tabs{display:flex;gap:6px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:5px;width:max-content;max-width:100%;margin-bottom:16px;flex-wrap:wrap}
.tab{border:0;background:transparent;color:var(--muted);padding:8px 14px;border-radius:9px;font-weight:600}
.tab.on{background:var(--accent);color:#fff}
.alert{display:flex;gap:12px;align-items:center;padding:11px 12px;border-radius:12px;margin-bottom:8px}
.alert .dot{width:10px;height:10px;border-radius:50%;flex:none}
.a-OVERDUE{background:var(--red-soft)}.a-OVERDUE .dot{background:var(--red)}
.a-DUE{background:var(--red-soft)}.a-DUE .dot{background:var(--red)}
.a-URGENT{background:var(--amber-soft)}.a-URGENT .dot{background:var(--amber)}
.a-UPCOMING{background:var(--blue-soft)}.a-UPCOMING .dot{background:var(--blue)}
.alert .w{margin-left:auto;font-weight:700;font-size:12.5px;white-space:nowrap}
.timeline{border-left:3px solid var(--accent-soft);margin-left:8px;padding-left:20px}
.tl{position:relative;margin-bottom:18px}
.tl:before{content:"";position:absolute;left:-29px;top:4px;width:13px;height:13px;border-radius:50%;background:var(--accent);border:3px solid var(--card);box-shadow:0 0 0 2px var(--accent)}
.tl .d{font-weight:700}
.empty{text-align:center;padding:34px 10px;color:var(--muted)}
.empty .big{font-size:36px;margin-bottom:6px}

/* donut + bars */
.donutwrap{display:flex;gap:22px;align-items:center;flex-wrap:wrap}
.legend div{display:flex;align-items:center;gap:8px;margin:6px 0;font-weight:500}
.legend i{width:11px;height:11px;border-radius:3px;display:inline-block}
.bar{height:9px;border-radius:99px;background:var(--line);overflow:hidden;margin:6px 0 14px}
.bar span{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--accent),#c084fc);transition:width .6s}

/* career */
.fields{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px}
.field{border:1px solid var(--line);background:var(--card);border-radius:14px;padding:14px;text-align:left;color:var(--ink);font-weight:600;display:flex;gap:10px;align-items:center}
.field:hover,.field.on{border-color:var(--accent);background:var(--accent-soft)}
.field .e{font-size:20px}
.roles{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px;margin-top:14px}
.rolebox{background:var(--accent-soft);border-radius:12px;padding:14px;font-weight:600}
.path{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:10px}
.node{background:var(--accent);color:#fff;padding:7px 14px;border-radius:999px;font-weight:600}
.arrow{color:var(--muted)}
ul.check{list-style:none;padding:0;margin:0}
ul.check li{display:flex;gap:10px;align-items:flex-start;padding:9px 0;border-bottom:1px solid var(--line)}
ul.check li:last-child{border-bottom:0}
ul.check input{width:18px;height:18px;margin-top:2px;accent-color:var(--accent)}
ul.check input:checked+span{text-decoration:line-through;color:var(--muted)}

/* modal + toast + console */
.modal{position:fixed;inset:0;background:rgba(15,16,36,.55);display:none;place-items:center;z-index:50;padding:16px}
.modal.open{display:grid}
.sheet{background:var(--card);border-radius:18px;padding:24px;width:min(480px,100%);box-shadow:0 20px 60px rgba(0,0,0,.35);max-height:92vh;overflow:auto}
.sheet h2{margin:0 0 16px}
.f{margin-bottom:12px}.f label{display:block;font-size:12.5px;font-weight:600;color:var(--muted);margin-bottom:5px}
.f input,.f select{width:100%}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.acts{display:flex;gap:10px;justify-content:flex-end;margin-top:16px}
#toast{position:fixed;right:22px;top:22px;z-index:80;display:flex;flex-direction:column;gap:8px}
.toast{background:var(--ink);color:var(--bg);padding:12px 16px;border-radius:12px;box-shadow:var(--shadow);font-weight:600;max-width:340px;animation:in .25s}
.toast.ok{background:#0f8f5c;color:#fff}.toast.bad{background:#c93b4a;color:#fff}
@keyframes in{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:none}}
#console{position:fixed;left:240px;right:0;bottom:0;background:#0d0e22;color:#c8ccff;z-index:40;border-top:2px solid var(--accent);font-family:Consolas,"Courier New",monospace;font-size:12.5px}
@media(max-width:820px){#console{left:0}}
#console .bar2{display:flex;align-items:center;gap:10px;padding:9px 16px;cursor:pointer;user-select:none}
#console .bar2 .dotg{width:9px;height:9px;border-radius:50%;background:#33d17a}
#console .bar2 b{color:#fff}
#console .body{display:none;height:250px;overflow:auto;padding:0 16px 12px;border-top:1px solid #23264d}
#console.open .body{display:block}
#console .ent{margin-top:12px}
#console .ent .h{color:#8b8bff;font-weight:700}
#console .ent .ds{background:#2a2c66;color:#cfd0ff;padding:1px 8px;border-radius:6px;margin-left:8px}
#console pre{margin:6px 0 0;white-space:pre-wrap;color:#aab0e8}
</style>
</head>
<body>
<div class="shell">
  <aside class="side">
    <div class="brand"><div class="logo" id="logoIco"></div><span>Job Application<br>Tracker</span></div>
    <nav class="nav" id="nav"></nav>
    <div class="foot"><b>C++ engine</b> running<br>Linked list, hash table, BST, heap, stack, queue, graph, merge sort, binary search</div>
  </aside>
  <main class="main">
    <div class="top">
      <div><h1 id="title">Dashboard</h1><p id="sub"></p></div>
      <button class="btn icon" id="themeBtn" title="Dark mode"></button>
      <button class="btn" id="undoBtn"></button>
      <button class="btn primary" id="addBtn"></button>
    </div>
    <div id="page"></div>
  </main>
</div>

<div class="modal" id="addModal"><div class="sheet">
  <h2>Add application</h2>
  <div class="f"><label>Company</label><input id="f_company" placeholder="e.g. Shopify"></div>
  <div class="f"><label>Job role</label><input id="f_role" placeholder="e.g. Junior Developer"></div>
  <div class="f"><label>Job field</label><input id="f_field" list="fieldList" placeholder="e.g. Software Engineering">
    <datalist id="fieldList"><option>Software Engineering</option><option>Artificial Intelligence</option><option>Cybersecurity</option><option>Networking</option><option>Data Science</option><option>Web Development</option><option>Database</option></datalist></div>
  <div class="two">
    <div class="f"><label>Deadline</label><input type="date" id="f_deadline"></div>
    <div class="f"><label>Urgency (1 = most urgent)</label><select id="f_urg"><option>1</option><option>2</option><option selected>3</option><option>4</option><option>5</option></select></div>
  </div>
  <div class="f"><label>Status</label><select id="f_status"><option>Applied</option><option>Interview</option><option>Rejected</option><option>Selected</option></select></div>
  <div class="acts"><button class="btn" id="addCancel">Cancel</button><button class="btn primary" id="addSave">Save application</button></div>
</div></div>
<div id="toast"></div>
<div id="console">
  <div class="bar2" id="consoleBar"><span class="dotg"></span><b>C++ console</b><span id="consoleLast" class="muted">waiting for first command</span><span style="margin-left:auto">click to open</span></div>
  <div class="body" id="consoleBody"></div>
</div>

<script>
const $=s=>document.querySelector(s);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const ICON={
 home:'<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/>',
 list:'<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
 flag:'<path d="M4 22V4M4 4h13l-2 4 2 4H4"/>',
 users:'<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3 3-5 6-5s6 2 6 5"/><path d="M16 5a3 3 0 010 6M21 20c0-2-1.5-3.8-4-4.6"/>',
 compass:'<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
 undo:'<path d="M9 14L4 9l5-5"/><path d="M4 9h10a6 6 0 010 12h-3"/>',
 plus:'<path d="M12 5v14M5 12h14"/>',
 moon:'<path d="M21 13a9 9 0 11-10-10 7 7 0 0010 10z"/>',
 search:'<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.5-4.5"/>',
 bell:'<path d="M6 8a6 6 0 0112 0c0 7 3 8 3 8H3s3-1 3-8M10 21a2 2 0 004 0"/>',
 brief:'<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 012-2h2a2 2 0 012 2v2"/>',
 spark:'<path d="M12 3l2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2z"/>'
};
const ic=n=>'<svg class="i" viewBox="0 0 24 24">'+ICON[n]+'</svg>';

const DSA={1:'Linked List + rebuilds Hash, BST, Heap',2:'Linked List traversal',3:'Hash Table',4:'Merge Sort + Binary Search',5:'Binary Search Tree (in-order)',6:'Min-Heap',7:'Linked List + Stack + Queue',8:'Stack (undo)',9:'Queue',10:'Queue (dequeue)',11:'Graph (adjacency list)',12:'Graph BFS',13:'Recursive Merge Sort',14:'Recursion over Linked List',15:'Lookup table',16:'Lookup table',17:'Linked List traversal'};

let apps=[], stats=null, page='dashboard', filter='All', tabPri='heap', foundIds=null, banner=null, prep=null, recs=null, bfsPath=null, nowPrep=null;
const cache={};

/* ---------- talking to the C++ program ---------- */
async function run(choice,answers){
  answers=answers||[];
  const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({choice,answers})});
  const d=await r.json();
  logC(choice,d);
  return (d.result||'').replace(/\r/g,'');
}
function logC(choice,d){
  const b=$('#consoleBody');
  const e=document.createElement('div');e.className='ent';
  e.innerHTML='<div class="h">&gt; menu option '+choice+'<span class="ds">'+esc(DSA[choice]||'')+'</span></div><pre>'+esc((d.transcript||'').trim())+'</pre>';
  b.prepend(e);
  $('#consoleLast').textContent='last: option '+choice+' ('+(DSA[choice]||'')+')';
}

/* ---------- parsing what the C++ prints ---------- */
function parseApps(t){
  if(/No applications found/.test(t))return[];
  return t.split('-------------------------').map(b=>{
    const g=k=>{const m=b.match(new RegExp('^'+k+': (.*)$','m'));return m?m[1].trim():''};
    if(!g('ID'))return null;
    return{id:+g('ID'),company:g('Company'),role:g('Role'),field:g('Field'),deadline:g('Deadline'),status:g('Status'),urgency:+g('Urgency')};
  }).filter(Boolean);
}
function parseStats(t){
  const g=k=>{const m=t.match(new RegExp('^'+k+': (.*)$','m'));return m?m[1].trim():'0'};
  return{total:+g('Total Applications'),applied:+g('Applied'),interview:+g('Interviews'),rejected:+g('Rejected'),selected:+g('Selected'),
    success:parseFloat(g('Selection Success Rate'))||0,irate:parseFloat(g('Interview Rate'))||0};
}
const byId=id=>apps.find(a=>a.id===id);

/* ---------- helpers ---------- */
function toast(msg,kind){const d=document.createElement('div');d.className='toast '+(kind||'');d.textContent=msg;$('#toast').appendChild(d);setTimeout(()=>d.remove(),3800)}
function colorFor(s){let h=0;for(const c of s)h=(h*31+c.charCodeAt(0))%360;return 'hsl('+h+',60%,48%)'}
function daysLeft(d){const p=d.split('-').map(Number);if(p.length<3)return null;const t=new Date();const a=new Date(t.getFullYear(),t.getMonth(),t.getDate());const b=new Date(p[0],p[1]-1,p[2]);return Math.round((b-a)/864e5)}
function dueText(d){const n=daysLeft(d);if(n===null)return{t:d,c:''};if(n<0)return{t:Math.abs(n)+' day'+(n==-1?'':'s')+' overdue',c:'due-late'};if(n===0)return{t:'Due today',c:'due-late'};if(n<=3)return{t:'In '+n+' day'+(n==1?'':'s'),c:'due-soon'};return{t:'In '+n+' days',c:''}}
function badge(s){const k=['Applied','Interview','Rejected','Selected'].includes(s)?s:'other';return '<span class="badge b-'+k+'">'+esc(s)+'</span>'}
function ymd(offset){const d=new Date();d.setDate(d.getDate()+offset);return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')}
function empty(icon,msg,extra){return '<div class="empty"><div class="big">'+icon+'</div>'+msg+(extra?'<div style="margin-top:12px">'+extra+'</div>':'')+'</div>'}
const loadBtn='<button class="btn primary sm" onclick="loadSample()">Load sample data</button>';

async function refresh(){
  apps=parseApps(await run(2));
  stats=parseStats(await run(14));
}

/* ---------- pages ---------- */
const PAGES=[['dashboard','Dashboard','home'],['apps','Applications','list'],['priority','Priorities','flag'],['interviews','Interviews','users'],['career','Career and Network','compass']];
const SUBS={dashboard:'Your job hunt at a glance',apps:'Every application in one place',priority:'What needs your attention first',interviews:'Prepare for the conversations that matter',career:'Find roles and map related companies'};

function renderNav(){
  $('#nav').innerHTML=PAGES.map(p=>'<a class="'+(p[0]===page?'on':'')+'" data-p="'+p[0]+'">'+ic(p[2])+p[1]+'</a>').join('');
  $('#nav').querySelectorAll('a').forEach(a=>a.onclick=()=>go(a.dataset.p));
  $('#title').textContent=PAGES.find(p=>p[0]===page)[1];
  $('#sub').textContent=SUBS[page];
}
async function go(p){page=p;foundIds=null;banner=null;renderNav();$('#page').innerHTML='<div class="empty">Loading...</div>';await render();}
async function render(){
  const el=$('#page');
  if(page==='dashboard')el.innerHTML=await pDash();
  else if(page==='apps')el.innerHTML=pApps();
  else if(page==='priority')el.innerHTML=await pPri();
  else if(page==='interviews')el.innerHTML=await pInt();
  else el.innerHTML=pCareer();
  bind();
}

async function pDash(){
  await refresh();
  const s=stats;
  if(!apps.length)return '<div class="hero"><h2>Welcome to Job Application Tracker</h2><p>Add your first application, or load sample data to see everything in action.</p></div><div class="card">'+empty('&#128188;','No applications yet.',loadBtn)+'</div>';
  const heapT=await run(6);
  const heap=[...heapT.matchAll(/ID: (\d+) \| Urgency: (\d+) \| Deadline: (\S+)/g)].map(m=>({id:+m[1],u:+m[2],d:m[3]})).slice(0,5);
  const seg=[['Applied',s.applied,'#2f7be0'],['Interview',s.interview,'#d98a0b'],['Selected',s.selected,'#12a56b'],['Rejected',s.rejected,'#e04b5a']];
  const tot=seg.reduce((a,b)=>a+b[1],0)||1;let off=25,donut='';
  seg.forEach(x=>{const p=x[1]/tot*100;if(p>0){donut+='<circle cx="21" cy="21" r="15.9155" fill="none" stroke="'+x[2]+'" stroke-width="5.5" stroke-dasharray="'+p+' '+(100-p)+'" stroke-dashoffset="'+off+'"/>';off-=p}});
  const st=(n,l,bg,fg,sym)=>'<div class="card stat"><div class="ico" style="background:'+bg+';color:'+fg+'">'+sym+'</div><div><div class="num">'+n+'</div><div class="lbl">'+l+'</div></div></div>';
  return '<div class="hero"><h2>'+s.total+' application'+(s.total==1?'':'s')+' tracked</h2><p>Track, prioritize and prepare for every application.</p></div>'+
  '<div class="grid g4" style="margin-bottom:16px">'+st(s.total,'Total applications','var(--accent-soft)','var(--accent)','&#9776;')+st(s.interview,'Interviews','var(--amber-soft)','var(--amber)','&#9733;')+st(s.selected,'Selected','var(--green-soft)','var(--green)','&#10003;')+st(s.rejected,'Rejected','var(--red-soft)','var(--red)','&#10005;')+'</div>'+
  '<div class="grid g2" style="margin-bottom:16px;grid-template-columns:1fr 1fr">'+
  '<div class="card"><h3>Application status<span class="tag">Recursion</span></h3><div class="donutwrap"><svg viewBox="0 0 42 42" width="150" height="150"><circle cx="21" cy="21" r="15.9155" fill="none" stroke="var(--line)" stroke-width="5.5"/>'+donut+'<text x="21" y="22.5" text-anchor="middle" font-size="7.5" font-weight="700" fill="var(--ink)">'+s.total+'</text></svg><div class="legend">'+seg.map(x=>'<div><i style="background:'+x[2]+'"></i>'+x[0]+' <b>'+x[1]+'</b></div>').join('')+'</div></div>'+
   '<div style="margin-top:16px"><div class="muted">Interview rate <b style="float:right;color:var(--ink)">'+s.irate.toFixed(1)+'%</b></div><div class="bar"><span style="width:'+s.irate+'%"></span></div><div class="muted">Selection success rate <b style="float:right;color:var(--ink)">'+s.success.toFixed(1)+'%</b></div><div class="bar"><span style="width:'+s.success+'%"></span></div></div></div>'+
  '<div class="card"><h3>'+ic('flag')+'Top priorities<span class="tag">Min-Heap</span></h3>'+heap.map((h,i)=>{const a=byId(h.id)||{company:'ID '+h.id,role:''};const d=dueText(h.d);return '<div class="row"><div class="rank">'+(i+1)+'</div><div><div class="t">'+esc(a.company)+'</div><div class="s">'+esc(a.role)+'</div></div><div class="end"><span class="pill-u u'+h.u+'">Urgency '+h.u+'</span><div class="s '+d.c+'">'+d.t+'</div></div></div>'}).join('')+'</div></div>';
}

function appCard(a){
  const d=dueText(a.deadline);
  return '<div class="card app"><div class="head"><div class="avatar" style="background:'+colorFor(a.company)+'">'+esc(a.company.charAt(0).toUpperCase())+'</div><div><div class="co">'+esc(a.company)+'</div><div class="role">'+esc(a.role)+'</div></div><div class="id">#'+a.id+'</div></div>'+
  '<div class="meta"><span><span class="tag">'+esc(a.field)+'</span></span><span>Deadline <b>'+esc(a.deadline)+'</b></span><span class="'+d.c+'">'+d.t+'</span></div>'+
  '<div class="foot"><span class="pill-u u'+a.urgency+'">Urgency '+a.urgency+'</span><select class="status" data-id="'+a.id+'">'+['Applied','Interview','Selected','Rejected'].map(s=>'<option'+(s===a.status?' selected':'')+'>'+s+'</option>').join('')+'</select></div></div>';
}
function pApps(){
  let list=apps;
  if(foundIds)list=apps.filter(a=>foundIds.includes(a.id));
  else if(filter!=='All')list=apps.filter(a=>a.status===filter);
  const chips=['All','Applied','Interview','Selected','Rejected'].map(f=>'<button class="chip '+(filter===f&&!foundIds?'on':'')+'" data-f="'+f+'">'+f+'</button>').join('');
  return '<div class="toolbar"><div class="chips">'+chips+'</div><div class="search"><input id="q" placeholder="Search company (exact name)"><select id="qm"><option value="3">Hash Table</option><option value="4">Binary Search</option></select><button class="btn" id="qgo">'+ic('search')+'Search</button></div></div>'+
   (banner?'<div class="banner '+banner.k+'">'+esc(banner.t)+'</div>':'')+
   (list.length?'<div class="apps">'+list.map(appCard).join('')+'</div>':'<div class="card">'+empty('&#128196;',apps.length?'Nothing matches that.':'No applications yet.',apps.length?'':loadBtn)+'</div>');
}

async function pPri(){
  await refresh();
  const tabs='<div class="tabs"><button class="tab '+(tabPri==='heap'?'on':'')+'" data-t="heap">Urgency (Min-Heap)</button><button class="tab '+(tabPri==='bst'?'on':'')+'" data-t="bst">Deadlines (BST)</button><button class="tab '+(tabPri==='sort'?'on':'')+'" data-t="sort">Sorted (Merge Sort)</button></div>';
  if(!apps.length)return tabs+'<div class="card">'+empty('&#128196;','Add some applications first.',loadBtn)+'</div>';
  let body='';
  if(tabPri==='heap'){
    const t=await run(6);
    const h=[...t.matchAll(/ID: (\d+) \| Urgency: (\d+) \| Deadline: (\S+)/g)];
    body='<div class="card"><h3>Ranked by urgency, then earliest deadline<span class="tag">Min-Heap</span></h3>'+h.map((m,i)=>{const a=byId(+m[1])||{company:'ID '+m[1],role:''};const d=dueText(m[3]);return '<div class="row"><div class="rank">'+(i+1)+'</div><div class="avatar" style="width:36px;height:36px;font-size:15px;background:'+colorFor(a.company)+'">'+esc(a.company.charAt(0))+'</div><div><div class="t">'+esc(a.company)+'</div><div class="s">'+esc(a.role)+'</div></div><div class="end"><span class="pill-u u'+m[2]+'">Urgency '+m[2]+'</span><div class="s '+d.c+'">'+m[3]+' ('+d.t+')</div></div></div>'}).join('')+'</div>';
  }else if(tabPri==='bst'){
    const t=await run(5);
    const h=[...t.matchAll(/Deadline: (\S+) \| IDs: ([\d ]+)/g)];
    body='<div class="card"><h3>In-order walk of the tree = earliest deadline first<span class="tag">Binary Search Tree</span></h3><div class="timeline">'+h.map(m=>{const ids=m[2].trim().split(/\s+/).map(Number);const d=dueText(m[1]);return '<div class="tl"><div class="d">'+m[1]+' <span class="muted '+d.c+'" style="font-weight:500">('+d.t+')</span></div>'+ids.map(i=>{const a=byId(i)||{company:'ID '+i,role:''};return '<div class="s">'+esc(a.company)+' &middot; '+esc(a.role)+'</div>'}).join('')+'</div>'}).join('')+'</div></div>';
  }else if(tabPri==='sort'){
    const t=await run(13);
    const rows=t.split('\n').filter(l=>l.split(' | ').length===3).map(l=>l.split(' | '));
    body='<div class="card"><h3>Sorted by deadline<span class="tag">Recursive Merge Sort</span></h3>'+rows.map((r,i)=>'<div class="row"><div class="rank">'+(i+1)+'</div><div><div class="t">'+esc(r[0])+'</div><div class="s">'+esc(r[1])+'</div></div><div class="end t">'+esc(r[2])+'</div></div>').join('')+'</div>';
  }
  return tabs+body;
}

async function pInt(){
  await refresh();
  const q=await run(9);
  const queue=/queue is empty/.test(q)?[]:q.split('\n').filter(l=>/ - /.test(l)&&!/QUEUE/.test(l));
  const inInt=apps.filter(a=>a.status.toLowerCase()==='interview');
  let guide='';
  if(prep){
    guide='<div class="card" style="margin-top:16px"><h3>'+ic('spark')+'Preparation guide: '+esc(prep.title)+'<span class="tag">'+esc(prep.field)+'</span></h3><div class="grid g2" style="grid-template-columns:1fr 1fr"><div><div class="muted" style="font-weight:700;margin-bottom:4px">FIELD-SPECIFIC</div><ul class="check">'+prep.spec.map(x=>'<li><input type="checkbox"><span>'+esc(x)+'</span></li>').join('')+'</ul></div><div><div class="muted" style="font-weight:700;margin-bottom:4px">GENERAL TIPS</div><ul class="check">'+prep.gen.map(x=>'<li><input type="checkbox"><span>'+esc(x)+'</span></li>').join('')+'</ul></div></div></div>';
  }
  return '<div class="grid g2"><div class="card"><h3>Interview queue<span class="tag">Queue (FIFO)</span></h3>'+
   (queue.length?queue.map((l,i)=>{const p=l.split(' - ');return '<div class="row"><div class="rank">'+(i+1)+'</div><div><div class="t">'+esc(p[0])+'</div><div class="s">'+esc(p.slice(1).join(' - '))+'</div></div>'+(i===0?'<span class="tag end">Next up</span>':'')+'</div>'}).join(''):empty('&#128140;','The queue is empty. Change an application status to Interview to add it here.'))+
   '<div style="margin-top:14px"><button class="btn primary" id="procBtn"'+(queue.length?'':' disabled')+'>Process next interview</button></div>'+
   (nowPrep?'<div class="banner ok" style="margin-top:14px">Now preparing for '+esc(nowPrep)+'</div>':'')+'</div>'+
  '<div class="card"><h3>Prep guides<span class="tag">Applications at Interview stage</span></h3>'+
   (inInt.length?inInt.map(a=>'<div class="row"><div class="avatar" style="width:36px;height:36px;font-size:15px;background:'+colorFor(a.company)+'">'+esc(a.company.charAt(0))+'</div><div><div class="t">'+esc(a.company)+'</div><div class="s">'+esc(a.role)+'</div></div><button class="btn sm end" data-prep="'+a.id+'">Open guide</button></div>').join(''):empty('&#128221;','No applications are at Interview stage yet.'))+'</div></div>'+guide;
}

const FIELDS=[['Software Engineering','&#128187;'],['AI and Machine Learning','&#129302;'],['Cybersecurity','&#128274;'],['Networking','&#127760;'],['Data Science','&#128202;'],['Web Development','&#127912;'],['Database Management','&#128451;'],['Other field','&#10024;']];
function pCareer(){
  return '<div class="card"><h3>'+ic('compass')+'Job recommendations by field<span class="tag">Lookup table</span></h3><div class="fields">'+FIELDS.map((f,i)=>'<button class="field '+(recs&&recs.i===i?'on':'')+'" data-fi="'+i+'"><span class="e">'+f[1]+'</span>'+f[0]+'</button>').join('')+'</div>'+
   (recs?'<div style="margin-top:18px"><b>'+esc(recs.intro)+'</b><div class="roles">'+recs.roles.map(r=>'<div class="rolebox">'+esc(r)+'</div>').join('')+'</div>'+(recs.skills?'<p class="muted" style="margin-bottom:0"><b>Useful skills:</b> '+esc(recs.skills)+'</p>':'')+'<p class="muted" style="font-size:12.5px;margin-bottom:0">'+esc(recs.note)+'</p></div>':'')+'</div>'+
  '<div class="grid g2" style="grid-template-columns:1fr 1fr;margin-top:16px"><div class="card"><h3>Company connections<span class="tag">Graph</span></h3><div class="f"><label>Company</label><input id="c1" style="width:100%" placeholder="e.g. Google"></div><div class="f"><label>Related company</label><input id="c2" style="width:100%" placeholder="e.g. Shopify"></div><button class="btn" id="connBtn">Connect companies</button></div>'+
  '<div class="card"><h3>Explore the network<span class="tag">BFS traversal</span></h3><div class="f"><label>Start from</label><input id="bs" style="width:100%" placeholder="e.g. Google"></div><button class="btn primary" id="bfsBtn">Run BFS</button>'+
   (bfsPath?'<div class="path">'+bfsPath.map((n,i)=>(i?'<span class="arrow">&rarr;</span>':'')+'<span class="node">'+esc(n)+'</span>').join('')+'</div><p class="muted" style="font-size:12.5px">Nearest connections first.</p>':'')+'</div></div>';
}

/* ---------- actions ---------- */
function bind(){
  document.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>{filter=b.dataset.f;foundIds=null;banner=null;render()});
  document.querySelectorAll('select.status').forEach(s=>s.onchange=async()=>{
    const r=await run(7,[s.dataset.id,s.value]);toast(r.trim().split('\n').pop(),/success/.test(r)?'ok':'bad');await refresh();render()});
  const go2=$('#qgo');if(go2)go2.onclick=search; const q=$('#q');if(q)q.onkeydown=e=>{if(e.key==='Enter')search()};
  document.querySelectorAll('[data-t]').forEach(b=>b.onclick=async()=>{tabPri=b.dataset.t;$('#page').innerHTML=await pPri();bind()});
  const pb=$('#procBtn');if(pb)pb.onclick=async()=>{
    const r=await run(10);const m=r.match(/Preparing for: (.*)/);
    if(m){nowPrep=m[1];toast('Next interview: '+m[1],'ok');
      const a=apps.find(x=>(x.company+' - '+x.role)===m[1]);if(a)await openPrep(a.id,false);}
    else toast('No pending interviews.','bad');
    render()};
  document.querySelectorAll('[data-prep]').forEach(b=>b.onclick=()=>openPrep(+b.dataset.prep,true));
  document.querySelectorAll('[data-fi]').forEach(b=>b.onclick=()=>recommend(+b.dataset.fi));
  const cb=$('#connBtn');if(cb)cb.onclick=async()=>{const r=await run(11,[$('#c1').value.trim(),$('#c2').value.trim()]);toast(r.trim(),/added/.test(r)?'ok':'bad')};
  const bb=$('#bfsBtn');if(bb)bb.onclick=async()=>{
    const r=await run(12,[$('#bs').value.trim()]);const m=r.match(/BFS: (.*) -> END/);
    if(m){bfsPath=m[1].split(' -> ')}else{bfsPath=null;toast(r.trim()||'Not found','bad')}
    $('#page').innerHTML=pCareer();bind()};
}
async function search(){
  const name=$('#q').value.trim();if(!name)return;
  const m=$('#qm').value;const r=await run(+m,[name]);
  if(m==='3'){
    const ids=[...r.matchAll(/^ID: (\d+)/gm)].map(x=>+x[1]);
    if(ids.length){foundIds=ids;banner={k:'ok',t:'Found '+ids.length+' match'+(ids.length>1?'es':'')+' using the Hash Table'}}
    else{foundIds=[];banner={k:'bad',t:'Company not found (search is an exact match)'}}
  }else{
    foundIds=null;
    banner=/found using/.test(r)?{k:'ok',t:'Company found using Binary Search'}:{k:'bad',t:'Company not found (search is an exact match)'};
  }
  render();
}
async function openPrep(id,rerender){
  const r=await run(16,[String(id)]);
  const a=byId(id);
  const sec=(from,to)=>{const i=r.indexOf(from);if(i<0)return[];const j=to?r.indexOf(to,i):r.length;return r.slice(i,j<0?r.length:j).split('\n').filter(l=>/^\d+\. /.test(l)).map(l=>l.replace(/^\d+\. /,''))};
  if(!/PREPARATION GUIDE/.test(r)){toast(r.trim().split('\n').pop(),'bad');return}
  prep={title:a?a.company+' - '+a.role:'ID '+id,field:a?a.field:'',spec:sec('FIELD-SPECIFIC','GENERAL'),gen:sec('GENERAL INTERVIEW TIPS',null)};
  if(rerender!==false)render();
}
async function recommend(i){
  const r=await run(15,[String(i+1),i===7?(prompt('Enter your field of interest:')||''):'']);
  const roles=r.split('\n').filter(l=>/^\d+\. /.test(l)).map(l=>l.replace(/^\d+\. /,''));
  const sk=r.match(/^Useful skills: (.*)$/m);
  const intro=(r.match(/^(Explore entry-level roles.*|Recommended job roles:)$/m)||[0,'Recommended job roles'])[1].replace(/:$/,'');
  const note=(r.match(/^These are suggested.*$/m)||[''])[0];
  recs={i,intro,roles,skills:sk?sk[1]:'',note};
  $('#page').innerHTML=pCareer();bind();
}
async function loadSample(){
  const S=[['Google','Junior Software Developer','Software Engineering',2,'Applied',1],['Cisco','Network Support Technician','Networking',5,'Applied',2],['Shopify','Junior Web Developer','Web Development',12,'Applied',3],['RBC','Data Analyst Intern','Data Science',1,'Applied',1],['Microsoft','Application Support Analyst','Software Engineering',20,'Selected',4],['Amazon','Cloud Support Associate','Cloud and DevOps',9,'Applied',3],['Telus','Cybersecurity Analyst','Cybersecurity',30,'Rejected',5]];
  toast('Loading sample data...');
  for(const s of S)await run(1,[s[0],s[1],s[2],ymd(s[3]),s[4],String(s[5])]);
  await refresh();
  const g=n=>apps.find(a=>a.company===n);
  await run(7,[String(g('Cisco').id),'Interview']);await run(7,[String(g('RBC').id),'Interview']);
  const C=[['Google','Shopify'],['Shopify','RBC'],['Google','Microsoft'],['Microsoft','Amazon'],['RBC','Cisco']];
  for(const c of C)await run(11,[c[0],c[1]]);
  toast('Sample data loaded','ok');await go(page);
}

/* ---------- add modal, theme, console ---------- */
$('#logoIco').innerHTML=ic('brief');
$('#addBtn').innerHTML=ic('plus')+'Add application';
$('#undoBtn').innerHTML=ic('undo')+'Undo';
$('#themeBtn').innerHTML=ic('moon');
$('#addBtn').onclick=()=>{$('#f_deadline').value=ymd(7);$('#addModal').classList.add('open');$('#f_company').focus()};
$('#addCancel').onclick=()=>$('#addModal').classList.remove('open');
$('#addModal').onclick=e=>{if(e.target.id==='addModal')$('#addModal').classList.remove('open')};
$('#addSave').onclick=async()=>{
  const v=id=>$(id).value.trim();
  const r=await run(1,[v('#f_company'),v('#f_role'),v('#f_field'),v('#f_deadline'),v('#f_status'),v('#f_urg')]);
  const ok=/added/.test(r);toast(ok?r.trim().split('\n').pop():'Please fill every field correctly.',ok?'ok':'bad');
  if(ok){['#f_company','#f_role','#f_field'].forEach(i=>$(i).value='');$('#addModal').classList.remove('open');await go(page)}
};
$('#undoBtn').onclick=async()=>{const r=await run(8);toast(r.trim(),/undone|restored/.test(r)?'ok':'');await go(page)};
$('#themeBtn').onclick=()=>{const d=document.documentElement;const dark=d.dataset.theme==='dark';d.dataset.theme=dark?'light':'dark';try{localStorage.setItem('jt-theme',d.dataset.theme)}catch(e){}};
try{const t=localStorage.getItem('jt-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}
$('#consoleBar').onclick=()=>$('#console').classList.toggle('open');
renderNav();render();
</script>
</body>
</html>
'''

if __name__ == "__main__":
    main()
