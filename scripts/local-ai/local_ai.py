"""Minimal local Ollama API client, using only the Python standard library."""

import json
import urllib.request

URL = "http://localhost:11434/api/generate"
MODEL = "qwen3.5:9b"

question = input("You: ")

payload = {
    "model": MODEL,
    "prompt": question,
    "stream": False,
    "think": False,
}

request = urllib.request.Request(
    URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(request, timeout=120) as response:
    result = json.load(response)

print("\nQwen:", result["response"])
