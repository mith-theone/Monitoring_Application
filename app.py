"""Local demo entrypoint — run with: python app.py"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Local demo: listen on all interfaces; debug off by default.
    app.run(host="0.0.0.0", port=5000, debug=False)
