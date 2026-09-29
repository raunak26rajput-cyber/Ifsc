# zvxay open-source release — re-share only with proper credit.

from flask import Flask, request, jsonify
import requests
import re
import os

app = Flask(__name__)

RAZORPAY_IFSC_URL = "https://ifsc.razorpay.com/"
REQUEST_TIMEOUT = (5, 15)
CREDIT = "@zvxay"


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "message": "IFSC API is running",
        "endpoints": {
            "health": "/health",
            "ifsc": "/ifsc?code=IFSC_CODE"
        },
        "credit": CREDIT
    })


@app.route("/ifsc", methods=["GET"])
def get_ifsc_info():
    ifsc_code = request.args.get("code", "").strip().upper()

    if not ifsc_code:
        return jsonify({
            "error": "IFSC code is required",
            "message": "Please provide IFSC code using 'code' parameter",
            "credit": CREDIT
        }), 400

    if not re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", ifsc_code):
        return jsonify({
            "error": "Invalid IFSC code format",
            "message": "IFSC code must be 11 characters in the format ABCD0XXXXXX",
            "credit": CREDIT
        }), 400

    try:
        response = requests.get(
            f"{RAZORPAY_IFSC_URL}{ifsc_code}",
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "zvxay-IFSC-API/2.0",
                "Accept": "application/json"
            }
        )

        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError:
                return jsonify({
                    "error": "Invalid response from upstream API",
                    "message": "The upstream service returned a non-JSON response",
                    "credit": CREDIT
                }), 502

            if isinstance(data, dict):
                data["credit"] = CREDIT
            return jsonify(data), 200

        if response.status_code == 404:
            return jsonify({
                "error": "IFSC code not found",
                "message": f"No bank found with IFSC code: {ifsc_code}",
                "credit": CREDIT
            }), 404

        return jsonify({
            "error": "Upstream service error",
            "status_code": response.status_code,
            "message": "Unable to retrieve IFSC information",
            "credit": CREDIT
        }), 502

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Request timeout",
            "message": "The upstream IFSC service took too long to respond",
            "credit": CREDIT
        }), 504

    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Connection error",
            "message": "Unable to connect to the upstream IFSC service",
            "credit": CREDIT
        }), 503

    except requests.exceptions.RequestException as exc:
        return jsonify({
            "error": "API request failed",
            "message": str(exc),
            "credit": CREDIT
        }), 502


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "IFSC API is running",
        "credit": CREDIT
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "message": "Available endpoints: GET /, GET /ifsc?code=IFSC_CODE, GET /health",
        "credit": CREDIT
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method not allowed",
        "message": "Use GET for this endpoint",
        "credit": CREDIT
    }), 405


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "Something went wrong on the server",
        "credit": CREDIT
    }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
