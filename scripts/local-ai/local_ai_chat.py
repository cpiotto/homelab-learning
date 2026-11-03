"""Session-only chat memory with Ollama, using Python's standard library."""

import json
import urllib.request

URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:9b"

history = [
    {
        "role": "system",
        "content": (
            "You are a technical assistant. Reply in Brazilian Portuguese, "
            "clearly and concisely. Say when you do not know an answer."
        ),
    }
]

print("Local AI assistant started.")
print("Type 'sair' to exit.\n")

while True:
    question = input("You: ").strip()

    if question.lower() == "sair":
        break
    if not question:
        continue

    messages = history + [{"role": "user", "content": question}]
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
    }

    request = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.load(response)
        answer = result["message"]["content"]
        print(f"\nQwen: {answer}\n")
        history.extend([
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ])
    except Exception as error:
        print(f"API request failed: {error}")

print("Chat session ended.")
