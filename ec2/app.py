import os
import json
import boto3
import requests
from flask import Flask, render_template_string, request, jsonify


app = Flask(__name__)


def get_secret():

    client = boto3.client(
        "secretsmanager",
        region_name="us-east-1"
    )

    response = client.get_secret_value(
        SecretId="ec2-lab"
    )

    return json.loads(response["SecretString"])


# Get values from AWS Secrets Manager
secret = get_secret()

API_URL = secret["API_URL"]
API_KEY = secret["API_KEY"]


HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Shon Drive</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"><style>
* {{ box-sizing: border-box; font-family: 'Inter', sans-serif; margin: 0; padding: 0; }}
body {{ background: #0f172a; color: #f8fafc; display: flex; height: 100vh; overflow: hidden; }}
.sidebar {{ width: 280px; padding: 25px 20px; background: #0f172a; border-right: 1px solid #334155; display: flex; flex-direction: column; }}
.main {{ flex: 1; background: #1e293b; display: flex; flex-direction: column; overflow: hidden; }}
.header {{ padding: 20px 30px; border-bottom: 1px solid #334155; font-size: 20px; font-weight: 600; color: #e2e8f0; }}
.content {{ flex: 1; padding: 30px; overflow-y: auto; }}
.btn {{ background: linear-gradient(135deg, #08d9d6, #3566F1); color: white; border: none; padding: 14px 24px; border-radius: 30px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 10px; width: 100%; justify-content: center; transition: opacity 0.2s; box-shadow: 0 4px 15px rgba(8, 217, 214, 0.2); margin-bottom: 20px; }}
.btn:hover {{ opacity: 0.9; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }}
.card {{ background: #334155; border: 1px solid #475569; border-radius: 12px; padding: 20px; display: flex; flex-direction: column; align-items: center; gap: 12px; cursor: pointer; transition: all 0.2s; position: relative; }}
.card:hover {{ border-color: #08d9d6; transform: translateY(-2px); }}
.card-icon {{ font-size: 48px; }}
.card-title {{ font-size: 13px; font-weight: 500; text-align: center; width: 100%; word-break: break-word; line-height: 1.4; color: #e2e8f0; min-height: 38px; }}
.card-actions {{ display: flex; gap: 6px; margin-top: 10px; width: 100%; flex-wrap: wrap; }}
.action-btn {{ background: rgba(8, 217, 214, 0.1); color: #08d9d6; border: 1px solid rgba(8, 217, 214, 0.3); padding: 6px 6px; border-radius: 6px; font-size: 11px; cursor: pointer; font-weight: 600; flex: 1; text-align: center; min-width: 60px; }}
.action-btn:hover {{ background: rgba(8, 217, 214, 0.2); }}
.action-btn.delete {{ color: #ef4444; background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.3); }}
.action-btn.delete:hover {{ background: rgba(239, 68, 68, 0.2); }}
.modal {{ display: none; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.9); z-index: 999; align-items: center; justify-content: center; }}
.modal-content {{ background: #1e293b; width: 85%; height: 85%; border-radius: 12px; padding: 20px; position: relative; border: 1px solid #475569; display: flex; flex-direction: column; }}
.close-btn {{ position: absolute; top: 15px; right: 25px; font-size: 28px; cursor: pointer; color: #94a3b8; border: none; background: none; }}
#viewerBody {{ flex: 1; display: flex; justify-content: center; align-items: center; overflow: hidden; margin-top: 10px; }}
#viewerBody img {{ max-width: 100%; max-height: 100%; border-radius: 8px; }}
#viewerBody iframe {{ width: 100%; height: 100%; border: none; border-radius: 8px; background: #f8fafc; }}
</style></head><body>
<div class="sidebar">
    <h2 style="font-size: 24px; margin-bottom: 30px; display: flex; align-items: center; gap: 10px;"><span style="color:#08d9d6">&#9729;</span> Shon Drive</h2>
    <input type="file" id="fileInput" style="display: none" onchange="uploadFile()">
    <button class="btn" onclick="document.getElementById('fileInput').click()"><span>&#10133;</span> Upload File</button>
</div>
<div class="main">
    <div class="header">My Drive</div>
    <div class="content"><div class="grid" id="fileList">Loading...</div></div>
</div>
<div id="fileModal" class="modal"><div class="modal-content"><span class="close-btn" onclick="closeViewer()">&times;</span><div id="viewerBody"></div></div></div>
<script>
const API_HEADERS = {{ 'x-api-key': '{API_KEY}' }};
const getIcon = f => {{ const e = f.split('.').pop().toLowerCase(); if (['jpg','jpeg','png','gif','svg'].includes(e)) return '&#128444;'; if (e==='pdf') return '&#128213;'; return '&#128196;'; }};

async function loadFiles() {{
    try {{
        const res = await fetch(`{API_URL}/files`, {{ headers: API_HEADERS }});
        const files = await res.json();
        document.getElementById('fileList').innerHTML = files.map(f => {{
            const displayName = decodeURIComponent(f.file_id).replace(/\\+/g, ' ');
            return `<div class="card">
                <div class="card-icon">${{getIcon(f.file_id)}}</div>
                <div class="card-title">${{displayName}}</div>
                <div style="font-size:11px; color:#94a3b8;">${{(f.size_bytes / 1048576).toFixed(2)}} MB</div>
                <div class="card-actions">
                    <button class="action-btn" onclick="viewFile('${{f.file_id}}')">View</button>
                    <button class="action-btn" onclick="downloadFile('${{f.file_id}}')">Download</button>
                    <button class="action-btn delete" onclick="deleteFile('${{f.file_id}}')">Delete</button>
                </div>
            </div>`;
        }}).join('') || "No files found.";
    }} catch (e) {{ document.getElementById('fileList').innerHTML = "Error loading files."; }}
}}

async function uploadFile() {{
    const fi = document.getElementById('fileInput'), file = fi.files[0]; if (!file) return;
    const btn = document.querySelector('.btn'); btn.innerHTML = "Uploading...";
    const fd = new FormData(); fd.append('file', file);
    try {{
        const res = await fetch('/proxy-upload', {{ method: 'POST', body: fd }});
        if (!res.ok) throw new Error();
        setTimeout(loadFiles, 1500);
    }} catch (e) {{ alert('Upload failed.'); }} finally {{ btn.innerHTML = "<span>&#10133;</span> Upload File"; fi.value = ""; }}
}}

async function downloadFile(filename) {{
    try {{
        const res = await fetch(`{API_URL}/download-url?filename=${{encodeURIComponent(filename)}}`, {{ headers: API_HEADERS }});
        const data = await res.json();
        window.open(data.download_url, '_blank');
    }} catch (e) {{ alert('Download failed.'); }}
}}

async function viewFile(filename) {{
    try {{
        const res = await fetch(`{API_URL}/download-url?filename=${{encodeURIComponent(filename)}}`, {{ headers: API_HEADERS }});
        const data = await res.json(), u = data.download_url, e = filename.split('.').pop().toLowerCase(), vb = document.getElementById('viewerBody');
        if (['jpg','jpeg','png','gif'].includes(e)) vb.innerHTML = `<img src="${{u}}">`;
        else if (e === 'pdf') vb.innerHTML = `<iframe src="${{u}}"></iframe>`;
        else return alert("No preview available.");
        document.getElementById('fileModal').style.display = 'flex';
    }} catch (e) {{ alert('Preview failed.'); }}
}}

async function deleteFile(filename) {{
    if (!confirm("Are you sure you want to delete this file?")) return;
    try {{
        const res = await fetch(`{API_URL}/delete-file?filename=${{encodeURIComponent(filename)}}`, {{
            method: 'DELETE',
            headers: API_HEADERS
        }});
        if (!res.ok) throw new Error();
        loadFiles();
    }} catch (e) {{ alert('Delete failed.'); }}
}}

function closeViewer() {{ document.getElementById('fileModal').style.display = 'none'; document.getElementById('viewerBody').innerHTML = ''; }}
loadFiles();
</script></body></html>"""


@app.route('/')
def home():
    return render_template_string(HTML)


@app.route('/proxy-upload', methods=['POST'])
def proxy_upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    try:
        res = requests.get(f"{API_URL}/upload-url", params={"filename": file.filename}, headers={'x-api-key': API_KEY})
        requests.put(res.json().get('upload_url'), data=file.read(), headers={'Content-Type': file.content_type or 'application/octet-stream'})
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
