import os
from flask import Flask, request, jsonify, send_from_directory
from scanner import scan_payload, model, vectorizer

# Initialize Flask app
# Serve static files directly from GUI_Version directory
app = Flask(__name__, static_folder='GUI_Version')

@app.route('/')
def serve_index():
    return send_from_directory('GUI_Version', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('GUI_Version', path)

@app.route('/api/scan', methods=['POST'])
def api_scan():
    try:
        text_payload = request.form.get('text', '')
        
        file_bytes = None
        filename = ''
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                file_bytes = file.read()
                filename = file.filename

        # Send to scanner engine
        result = scan_payload(text_payload=text_payload, file_bytes=file_bytes, filename=filename)
        return jsonify(result)
        
    except Exception as e:
        print(f"Error during scan: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """Returns system health for the Telemetry Node view."""
    vt_key = os.environ.get("VT_API_KEY", "")
    return jsonify({
        "node": "AetherGuard v1.0",
        "ml_loaded": model is not None and vectorizer is not None,
        "vt_api_active": len(vt_key) > 0,
        "gateway_status": "ONLINE"
    })

if __name__ == '__main__':
    print("Starting AetherGuard Web3 Security Gateway...")
    print("Server running on http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)

