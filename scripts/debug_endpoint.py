import requests
import json
import sys

# Set unicode encoding for console output
sys.stdout.reconfigure(encoding='utf-8')

url = "http://localhost:8082/api/stream_chat"
payload = {
    "text": "मुझे किस तरह मदद करसकते है",
    "language": "hi"
}
headers = {'Content-Type': 'application/json'}

print(f"Testing {url} with payload {payload}...")

try:
    with requests.post(url, json=payload, headers=headers, stream=True) as r:
        print(f"Status Code: {r.status_code}")
        if r.status_code != 200:
            print("Error Content:", r.text)
        else:
            print("Streaming response started...")
            for line in r.iter_lines():
                if line:
                    print(f"Received: {line.decode('utf-8')}")
            print("Stream finished.")
except Exception as e:
    print(f"Request failed: {e}")
