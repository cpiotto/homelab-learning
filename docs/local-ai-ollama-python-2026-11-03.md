# Local AI Inference and Ollama API Integration — 3 November 2026

## Objective

Validate local large language model (LLM) inference on an existing Windows workstation, compare two models under practical workloads, and build a minimal Python client for Ollama's HTTP API. The experiment is intended to develop transferable skills in Python, HTTP/JSON APIs, GPU monitoring and evidence-based troubleshooting, without adding another homelab server or purchasing hardware.

**Status:** Phase 1 complete — local inference, GPU placement, performance sampling, API access and session-only chat history were tested. Speech input/output, ESP32 hardware and persistent memory are **not implemented**.

## Environment

| Component | Observed configuration |
| --- | --- |
| Workstation | MSI Windows desktop, Intel Core i5-14400F, 16 GB DDR5 |
| GPU | NVIDIA GeForce RTX 4070 Ti, reported 12,282 MiB VRAM |
| Runtime | Ollama on Windows, using the `llamacpp` runner |
| Models | `qwen3.5:9b` (6.6 GB download), `gemma4:12b` |
| Gemma metadata | `gemma4`, 11.9B parameters, `Q4_K_M` quantisation |
| Context | 4,096 tokens as reported by `ollama ps` during the tests |
| Python | Python 3.15.2, pip 26.2.2 |
| Local API | `http://localhost:11434` |
| Python dependencies | Standard library only: `json` and `urllib.request` |

The Gemma model advertises a larger maximum context, but **that is not the configured 4,096-token runtime context** used here. The installed Ollama application version was not separately recorded.

## Architecture

```text
Windows PowerShell
   |
   | launches Python client / sends question
   v
Python standard-library HTTP client
   |  POST /api/generate  (single prompt)
   |  POST /api/chat      (conversation history)
   |  JSON over localhost:11434
   v
Ollama on the MSI workstation
   |
   |  qwen3.5:9b or gemma4:12b
   v
RTX 4070 Ti (local model inference)
   |
   v
JSON response -> Python -> Windows terminal
```

No Proxmox VM, cloud inference API, broker or additional monitoring stack was introduced. API requests were sent to the local loopback address; access from other network devices was **not** configured or validated.

## Implementation

### 1. Confirm installed models

```powershell
ollama list
```

Observed:

```text
NAME              ID              SIZE
qwen3.5:9b        56671c2ab938    6.6 GB
qwen2.5:latest    845dbda0ea48    4.7 GB
```

The `qwen2.5:latest` model was present but not part of this comparison. Gemma 4 12B was downloaded subsequently.

For the model information:

```powershell
ollama show gemma4:12b
```

Observed `11.9B` parameters, `Q4_K_M` quantisation and reported capabilities including completion, vision, audio, tools and thinking. Those capabilities were not all exercised in this experiment.

### 2. Validate GPU placement and utilisation

```powershell
ollama ps
nvidia-smi --query-gpu=memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu --format=csv
```

Ollama reported `100% GPU` for **both models**, with a 4,096-token context and the `llamacpp` runner. This indicates model placement, **not** 100% GPU utilisation.

| Metric (separate snapshots) | Qwen 3.5 9B | Gemma 4 12B |
| --- | ---: | ---: |
| Total GPU memory | 12,282 MiB | 12,282 MiB |
| Used GPU memory | 7,814 MiB | 10,155 MiB |
| Free GPU memory | 4,181 MiB | 1,840 MiB |
| Instantaneous GPU utilisation | 2% | 2% |
| GPU temperature | 32.88 °C | 32.11 °C |
| Ollama reported processor | 100% GPU | 100% GPU |

These are **system-wide GPU memory** measurements, including Windows graphics and other applications, not isolated per-model allocation. They were taken at different times. The reported used and free figures do not sum to the total exactly; reserve/unaccounted memory or driver reporting must not be attributed to the model.

**Anomaly:** `ollama ps` displayed `SIZE 1.1 GB` for `gemma4:12b` even though the downloaded model weights were much larger and the system-level GPU reading was 10,155 MiB in use. That column was not treated as authoritative for actual VRAM usage; the discrepancy was not resolved.

### 3. Compare inference quality and performance

Enabled verbose timing in Ollama's interactive prompt:

```text
/set verbose
/set nothink
```

The `/set nothink` setting disabled the model's explicit thinking mode for the comparison. The tests used different conversation histories, response lengths, model-loading states and cache states; they are **practical observations, not controlled scientific benchmarks**.

| Workload | Model | Total duration | Generation rate | Output tokens | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| Linux network troubleshooting, thinking enabled | Qwen 9B | 46.08 s | 72.91 tok/s | 3,060 | 3.36 s loading; generated many tokens |
| Linux network troubleshooting, thinking off | Qwen 9B | 5.40 s | 72.30 tok/s | 357 | Model already loaded |
| Linux network troubleshooting, thinking off | Gemma 12B | 26.41 s | 104.04 tok/s | 1,007 | 6.69 s loading; 10.02 s prompt processing |
| Proxmox explanation, thinking off | Gemma 12B | 1.86 s | 98.80 tok/s | 81 | Warm model |
| Proxmox explanation, thinking off | Qwen 9B | 1.42 s | 71.86 tok/s | 71 | Warm model |
| Proxmox explanation repeated, thinking off | Qwen 9B | 1.36 s | 71.74 tok/s | 69 | Warm model |

**Interpretation:** Gemma generated output tokens faster in these observations, but Qwen used less total GPU memory and completed the short Proxmox question faster when warm. For the 46-second Qwen result, turning off explicit thinking greatly reduced generated tokens and elapsed time; no general guarantee follows from this single test.

**Quality checks:** Both models gave usable networking explanations but made overconfident simplifications. For example, a failed ICMP ping to a gateway does not prove a physical-layer fault; ICMP can be blocked. Gemma gave a more comprehensive Linux troubleshooting sequence in this sample. The models' correctness should be assessed with testable commands and real host evidence rather than assumed from fluent wording.

### 4. Verify Ollama's HTTP API

First, a PowerShell HTTP POST to `/api/generate` returned a correct plain-language description of DNS. This demonstrated that an external local client can receive a response without using the Ollama interactive prompt.

Then confirmed Python and pip:

```powershell
python --version
python -m pip --version
```

Observed `Python 3.15.2` and `pip 26.2.2`.

The first script, [`local_ai.py`](../scripts/local-ai/local_ai.py), sends a single request:

```json
{
  "model": "qwen3.5:9b",
  "prompt": "What is the difference between a VM and an LXC container?",
  "stream": false,
  "think": false
}
```

Endpoint: `POST http://localhost:11434/api/generate`.

Observed: Python displayed a detailed answer describing separate guest kernels in VMs versus the host kernel shared by LXC containers. The explanation was broadly sound but overstated some boot-time and isolation comparisons; model text should not be treated as authoritative without verification.

### 5. Verify temporary conversation memory

The second script, [`local_ai_chat.py`](../scripts/local-ai/local_ai_chat.py), calls `POST /api/chat`, maintaining an in-process list of messages with `system`, `user` and `assistant` roles. It sends that list with each new user message and stores the model's answer after success.

Evidence from the interactive Python test:

```text
User: My DNS server is named dns01 and uses BIND9.
Qwen: Understood. You have a server named dns01 running BIND9.
User: What is the name of the DNS server I mentioned?
Qwen: The DNS server you mentioned is dns01.
```

Actual prompts and answers were in Brazilian Portuguese; the excerpt is translated here. The model correctly recalled `dns01` because the Python client supplied previous messages within the same process.

This is **not a persistent memory feature**: the list is lost when the Python process exits and can eventually exceed the configured context window.

## Reproduce the experiment

Requirements: a working Ollama installation, the `qwen3.5:9b` model already downloaded, Python on the PATH and sufficient resources for the model.

From the repository root in PowerShell:

```powershell
python .\scripts\local-ai\local_ai.py
python .\scripts\local-ai\local_ai_chat.py
```

Run either script independently. Enter a question when prompted; in the chat client enter `sair` to exit. The examples deliberately use only Python standard-library modules, without additional packages. They were recreated from the tested code used in the learning session; no automated test suite or clean-machine installation was performed.

## Troubleshooting and observations

- `py --version` initially failed because the Windows `py` launcher was unavailable. `python --version` also reported no Python installation at that stage. Python was then installed and confirmed as 3.15.2.
- Entering `ollama ps` at the Ollama `>>>` conversation prompt caused the model to interpret it as text and answer incorrectly that no such command exists. Running `ollama ps` in **a separate PowerShell window** worked correctly. This is a useful illustration of the difference between an operating-system shell and a model's interactive prompt.
- The first request after switching models included several seconds of model loading. Warm-model timings are more useful for a voice-assistant latency baseline.
- The initial response contained a technical hallucination about Ollama CLI functionality. Verify critical commands independently.

## Validation checklist

| Check | Observed result |
| --- | --- |
| Ollama model download and listing | Passed for Qwen; Gemma subsequently downloaded |
| Qwen responds interactively | Passed |
| Gemma responds interactively | Passed |
| Model placement via `ollama ps` | Both reported 100% GPU |
| GPU system metrics via `nvidia-smi` | Collected for both |
| Thinking on/off comparison | Collected for Qwen |
| Short-answer warm inference | Collected for both |
| PowerShell POST to local API | Passed |
| Python single-prompt HTTP client | Passed |
| Python multi-turn session history | Passed: `dns01` correctly recalled |
| Audio input, text-to-speech, ESP32 | Not tested |
| Long-running reliability and concurrency | Not tested |

## Lessons learned

- Model parameter count alone does not determine practical answer quality or latency.
- Loading time, prompt processing, output token count and tokens per second measure different things.
- `100% GPU` in Ollama identifies placement, while `nvidia-smi` reports device-wide usage.
- CPU/GPU memory figures should be interpreted with awareness of other Windows processes.
- LLMs can confidently invent CLI facts; a working command or service response is stronger evidence.
- A simple localhost API and Python's standard library are enough to build a useful first integration.
- Chat context is supplied by the client; the model does not automatically store long-term memories.

## Scope closure and future work

**Completed:** local inference benchmark and a Python API prototype with temporary multi-turn context.

**Known limitations:** inconsistent Gemma SIZE reporting, uncontrolled benchmark variables, 4,096-token runtime context, no persistence or context trimming, rudimentary error handling and no formal security review of any remote API access.

**Optional next experiment:** add locally hosted speech-to-text and text-to-speech on the Windows workstation, validating voice latency before purchasing or connecting an ESP32.

**Future, not implemented:** ESP32-S3 circular display as a voice interface; read-only, authenticated homelab status retrieval. Do not expose the Ollama API directly to the Internet or grant a model unrestricted infrastructure administration access.

## Skills demonstrated

Python · PowerShell · REST-style HTTP APIs · JSON · local LLM inference · NVIDIA GPU diagnostics · quantisation awareness · benchmarking · context handling · technical validation · troubleshooting · evidence-based documentation.
