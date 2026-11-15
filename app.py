import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ================== KONFIGURASI ==================
# Ganti pake API key & Device ID lu yang asli dari .env VPS
API_KEY_NPSN = os.environ.get("API_KEY_NPSN", "XQPC-EDY7-D1NL-THMA-DMVT")
DEVICE_ID    = os.environ.get("DEVICE_ID",    "thoz-pc-01")
API_URL_NPSN = "https://api-baberkyu-vps-team-official.my.id/"

# ================== SESSION ==================
session = requests.Session()

# ================== HELPER ==================
def verify_api_key(expected_key: str):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return False, "API Key tidak ditemukan."
    if api_key != expected_key:
        return False, "API Key tidak valid."
    return True, ""

# ================== FUNGSI NPSN ==================
def api_npsn(npsn: str):
    """Request ke API siswa lu, bawa header API Key & Device ID."""
    try:
        headers = {
            "X-API-Key": API_KEY_NPSN,
            "X-Device-ID": DEVICE_ID,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        params = {"npsn": npsn}
        
        # Timeout (6, 12) = 6 detik connect, 12 detik read
        response = requests.get(API_URL_NPSN, params=params, headers=headers, timeout=(6, 12))

        try:
            data = response.json()
        except ValueError:
            data = {"error": "Response bukan JSON", "raw": response.text}

        app.logger.info(f"Fetch NPSN {npsn} -> HTTP {response.status_code}")
        return True, data, response.status_code

    except requests.exceptions.Timeout as e:
        app.logger.error(f"NPSN timeout: {e}")
        return False, {"error": f"Timeout: {e}"}, 504
    except requests.exceptions.RequestException as e:
        app.logger.error(f"NPSN request error: {e}")
        return False, {"error": f"Request error: {e}"}, 502
    except Exception as e:
        app.logger.error(f"NPSN error: {e}")
        return False, {"error": str(e)}, 500

# ================== ENDPOINT NPSN ==================
@app.route('/npsn', methods=['GET'])
def npsn():
    # Cek API Key lu yang dipake sama client (Thoz)
    valid, msg = verify_api_key(API_KEY_NPSN)
    if not valid:
        return jsonify({"error": msg}), 401

    # Ambil NPSN dari query param
    npsn_param = request.args.get('npsn')
    if not npsn_param or not npsn_param.strip():
        return jsonify({"error": "Parameter 'npsn' wajib diisi."}), 400

    # Tembak API asli lu di VPS
    ok, data, status = api_npsn(npsn_param.strip())

    # Balikin data JSON apa adanya
    return jsonify(data), status

# ================== GLOBAL ERROR HANDLER ==================
@app.errorhandler(Exception)
def handle_unhandled(e):
    import traceback
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return jsonify({"error": e.name, "code": e.code}), e.code
    tb = traceback.format_exc()
    app.logger.error(f"UNHANDLED: {e}\n{tb}")
    return jsonify({
        "error": "internal",
        "message": str(e),
        "type": type(e).__name__
    }), 500

# ================== ROOT ==================
@app.route('/')
def index():
    return jsonify({
        "message": "Silahkan masukkan APIKEY API !",
        "endpoints": {
            "Toolsv6": "Api dump siswa !"
        },
        "authentication": "Header X-API-Key"
    })

if __name__ == '__main__':
    # debug=False buat production
    app.run(host='0.0.0.0', port=5000, debug=False)