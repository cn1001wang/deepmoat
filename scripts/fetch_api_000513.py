import requests
import json
from pathlib import Path
from datetime import datetime

# API endpoint
url = "http://localhost:5100/stock/000513.SZ"
output_dir = Path(__file__).parent.parent / 'outputs'
output_dir.mkdir(exist_ok=True)

try:
    print(f"Fetching data from {url}...")
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()

    # Save to file
    output_file = output_dir / 'stock-000592-SZ.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Data saved to {output_file}")
    print(f"Response status: {response.status_code}")

except requests.exceptions.ConnectionError:
    print("[ERROR] Cannot connect to API server at localhost:5100")
    print("Please ensure the backend server is running:")
    print("  uvicorn app.main:app --host 0.0.0.0 --port 5100 --reload")
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
