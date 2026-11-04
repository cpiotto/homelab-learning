# Fully Offline Brazilian Portuguese Voice Assistant — 4 November 2026

## Objective and outcome

Build a practical voice interface for an existing local LLM without purchasing hardware or expanding the Proxmox homelab. The assistant must accept spoken Brazilian Portuguese, generate an answer locally and speak it back in Brazilian Portuguese.

**Status: Version 1 complete.** On 4 November 2026, a full voice interaction succeeded with the Windows workstation disconnected from the Internet. The speech-to-text (STT), language model and text-to-speech (TTS) components were all operating locally. This validates the **tested workstation workflow**, not remote access, unattended reliability or every possible offline feature of the web application.

This project extends the [3 November Ollama/Python experiment](local-ai-ollama-python-2026-11-03.md) rather than replacing its historical test results.

## Environment and scope

| Component | Implementation / observation |
| --- | --- |
| Host | MSI Windows workstation (Windows build 26300.9711) |
| CPU and RAM | Intel Core i5-14400F; 16 GB DDR5 (as recorded in the previous experiment) |
| GPU | NVIDIA RTX 4070 Ti 12 GB, used for Ollama inference |
| WSL | WSL 3.0.3.0, Linux kernel 6.18.54.1-1 |
| Containers | Docker Desktop 4.98.0 using WSL 2 |
| LLM host | Existing Ollama installation on Windows |
| Model used | `gemma4:12b` |
| Additional installed models | `qwen3.5:9b` and `qwen2.5:latest` |
| Browser interface | Open WebUI container, `http://localhost:3000` |
| Speech input | Open WebUI local Whisper, `base` multilingual model |
| Speech output | Piper TTS, `pt_BR-faber-medium` voice |
| Piper interface | OpenAI-compatible speech API exposed by a community container |
| Container communication | User-defined Docker bridge network `ai-voice` |

**Boundary:** No Proxmox host, new NAS hardware, ESP32 board, cloud LLM or remote access configuration was required.

## Architecture

```text
Brazilian Portuguese voice (microphone / headset)
    |
    v
Chrome on the MSI -- http://localhost:3000
    |
    v
Open WebUI container
    |  Local Whisper "base": audio -> text
    |
    +-- HTTP via host.docker.internal:11434 --> Ollama on Windows
    |                                           |
    |                                           +--> gemma4:12b / RTX 4070 Ti
    |                                           |
    |<-------------------------- generated text -+
    |
    +-- Docker network "ai-voice" --> piper-tts:5000/v1
                                        |
                                        +--> pt_BR-faber-medium: text -> speech
    |
    v
Browser audio playback / headset
```

The Open WebUI container publishes `127.0.0.1:3000` to container port `8080`; the Piper container publishes `127.0.0.1:5000` to its API on port `5000`. The loopback bindings limit those published ports to the workstation; the two containers additionally communicate by name over `ai-voice`.

The URL `host.docker.internal` is the Docker-to-Windows-host route used for the existing Ollama installation. The `piper-tts` hostname resolves between containers on the user-defined Docker network.

## Implementation record

The commands below document the working installation sequence. They are **reference commands**, not an automated deployment script. Check for existing containers, network names and ports before attempting to reproduce them on another machine. Never run the create commands again against existing resources without inspecting their state and backing up any important data.

### 1. Confirm existing Ollama and install Docker prerequisites

PowerShell:

```powershell
ollama list
wsl --version
docker info --format '{{.ServerVersion}}'
```

The Ollama listing showed `gemma4:12b`, `qwen3.5:9b` and `qwen2.5:latest`. Initially neither Docker nor WSL was available. WSL was installed using:

```powershell
wsl --install --no-distribution
```

A Windows restart was required before verifying WSL 3.0.3.0. Docker Desktop was then installed with the WSL 2 backend. This allowed Open WebUI to run in a Linux container while reusing Ollama running natively on Windows.

### 2. Create Open WebUI with persistent storage

Generate a random secret in PowerShell instead of committing or sharing its value:

```powershell
$key = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($key)
$secret = [BitConverter]::ToString($key).Replace('-', '').ToLowerInvariant()
```

Then the installation used:

```powershell
docker run -d -p 127.0.0.1:3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data -e WEBUI_SECRET_KEY=$secret -e OLLAMA_BASE_URL=http://host.docker.internal:11434 -e WHISPER_MULTILINGUAL=true --name open-webui --restart unless-stopped ghcr.io/open-webui/open-webui:main
```

- `open-webui` is the named volume for application data and conversation persistence.
- `WEBUI_SECRET_KEY` supports application session security; its value is deliberately **not** stored here.
- `OLLAMA_BASE_URL` directs the web application to the existing host-side Ollama API.
- `--restart unless-stopped` configures Docker restart behaviour; restart persistence was not separately tested.

The operator verified the container with `docker ps --filter "name=open-webui"`, confirmed the secret was populated without printing it, opened `http://localhost:3000` and successfully received a Portuguese answer from `gemma4:12b`.

### 3. Set up local speech recognition

In **Open WebUI > Admin Panel > Settings > Audio**:

| Setting | Working value |
| --- | --- |
| Speech-to-Text engine | Whisper (Local) |
| STT model | `base` |

In **Personal Settings > Audio**, the speech-recognition engine was left on **Default**, and the speech language was set to `pt`. A spoken test phrase was transcribed accurately, confirming that Portuguese microphone input reached the chat.

### 4. Run Piper with a Brazilian Portuguese voice

The successful container command was:

```powershell
docker run -d --name piper-tts -p 127.0.0.1:5000:5000 -e PORT=5000 -v piper-voices:/data --restart unless-stopped kamilkrawiec/piper-openai-tts
```

This image is a **third-party community API wrapper**, not the base Piper project. The named volume `piper-voices` is intended to retain downloaded voice data. A one-time voice test produced a WAV file:

```powershell
$body = @{
    model = "piper"
    voice = "pt_BR-faber-medium"
    input = "Olá! Agora sou uma inteligência artificial com voz brasileira funcionando localmente."
    response_format = "wav"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:5000/v1/audio/speech" -Method Post -ContentType "application/json; charset=utf-8" -Body $body -OutFile "$env:TEMP\piper-teste.wav"
Invoke-Item "$env:TEMP\piper-teste.wav"
```

The WAV file played successfully, and the voice quality was assessed as good. This independently verified Piper output before changing the working browser audio configuration.

### 5. Connect the two Docker containers

```powershell
docker network create ai-voice
docker network connect ai-voice open-webui
docker network connect ai-voice piper-tts
```

This allows Open WebUI to access the Piper API using the container DNS name `piper-tts`. The network was used for application-to-application traffic; it does not publish an API to the Internet.

### 6. Configure Open WebUI to use Piper for speech output

In **Admin Panel > Settings > Audio**, leave **Speech-to-Text** on **Whisper (Local)**. Configure **Text-to-Speech** separately:

| Text-to-Speech setting | Working value |
| --- | --- |
| Engine | OpenAI-compatible / OpenAI |
| API base URL | `http://piper-tts:5000/v1` |
| API key | `local-piper` (local placeholder; not a cloud credential) |
| Model | `tts-1` |
| Voice | `pt_BR-faber-medium` |

Selecting an OpenAI-compatible API engine **does not mean using a cloud API**: this URL points to the local Piper container.

In **Personal Settings > Audio**, the TTS engine was set to **Default** so that the administrator's Piper configuration was applied. The user also enabled automatic response playback and automatic submission of transcribed speech.

## Validation evidence

| Test | Observed outcome | Result |
| --- | --- | --- |
| Ollama lists downloaded models | Gemma and Qwen models displayed | Pass |
| Docker Desktop / Open WebUI starts | Container `open-webui` running and reachable on localhost port 3000 | Pass |
| Open WebUI connects to Ollama | `gemma4:12b` returned a valid Portuguese text answer | Pass |
| Local Whisper microphone test | Spoken Brazilian Portuguese transcribed accurately | Pass |
| Piper API stand-alone test | `piper-teste.wav` generated and played clearly in Brazilian Portuguese | Pass |
| Piper integration with Open WebUI | Spoken answer reproduced with the Piper voice | Pass |
| **Disconnected-Internet end-to-end test** | User confirmed a full voice conversation worked with workstation Internet access disabled | **Pass** |
| Fresh boot, 24/7 stability, concurrent users | Not performed | Not tested |
| Access from mobile device / ESP32-S3 | Not configured | Not tested |

The offline result is a practical end-to-end functional test. No packets were captured, no external endpoint audit was completed and no offline cold-start/recovery test was recorded. Do not infer results for those additional checks.

## Troubleshooting and fixes

1. **Docker command initially unrecognised:** Docker Desktop and WSL were missing. Install WSL 2, reboot, install Docker Desktop and confirm the engine is running.
2. **English accent in browser TTS:** Initially only Windows voices David, Mark and Zira were listed. The Google Brazilian Portuguese option appeared when non-local browser voices were allowed; it was not an acceptable fully offline solution.
3. **Windows Portuguese speech pack was missing:** `Get-WindowsCapability -Online -Name 'Language.TextToSpeech~~~pt-BR~0.0.1.0'` initially reported `NotPresent`. The capability was installed, but this did not by itself expose a Brazilian voice in the Chrome/Edge local voice list. Piper subsequently solved this independently of Windows browser voices.
4. **STT/TTS settings were confused:** The Piper API URL was accidentally entered under **Speech-to-Text** when the engine was changed to OpenAI. Restore **Whisper (Local)** for input, and configure Piper only under **Text-to-Speech**.
5. **Piper first validated independently:** Testing its `/v1/audio/speech` endpoint with an actual WAV file isolated voice synthesis from Open WebUI integration problems.

## Security, operations and limitations

- No cloud LLM inference or online voice synthesis was needed for the tested voice conversation.
- The public Docker port bindings use `127.0.0.1`. The services were **not** opened to the LAN or to the Internet.
- The first Open WebUI admin account uses local authentication. No multi-user permissions review or external-access hardening was performed.
- The Open WebUI secret is generated locally. Never commit the actual secret, credentials, conversation exports or personal recordings to this public repository.
- The currently used image tags (including `main`) are mutable. Before a future rebuild, inspect and pin audited image versions/digests for reproducibility.
- The Piper wrapper is a third-party container. Its update, provenance and maintenance policy should be reviewed before production use.
- Model files and Piper voice assets must be cached locally for offline operation. Do not assume a new installation can fetch them without Internet access.
- No reliable latency statistics, 24-hour stability tests, volume backup/restore test, or reboot persistence test were recorded.
- Browser, microphone and headset access were tested on the local MSI workstation only.

## Completion criteria and closure

**Version 1 acceptance criteria achieved:**

- [x] Speak Brazilian Portuguese into the workstation microphone.
- [x] Transcribe speech locally with Whisper.
- [x] Generate a useful Portuguese answer with a locally hosted Ollama model.
- [x] Synthesize and hear a Brazilian Portuguese answer with Piper.
- [x] Complete a voice interaction while disconnected from the Internet.
- [x] Document configuration, evidence and known limitations.

**Status: CLOSED — 4 November 2026.**

Future enhancements are explicitly **out of scope** for Version 1: authenticated LAN/mobile access, ESP32-S3 microphone/display client, quality/latency benchmarking, offline restart testing, container image pinning, voice options and backup/restore verification. None is required to consider the current project complete.

## Skills demonstrated

Windows and WSL 2 administration · Docker container lifecycle · persistent volumes · bridge networking and container DNS · loopback exposure · HTTP/JSON APIs · Ollama inference · STT vs TTS architecture · offline model/voice deployment · layered troubleshooting · functional verification · technical documentation.
