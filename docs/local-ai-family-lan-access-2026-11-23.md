# Local AI: Shared LAN Access and Custom Business Assistant — 23 November 2026

## Objective and outcome

Extend the existing Windows-hosted Ollama and Open WebUI installation so that a family member can use a local language model from a MacBook browser on the same home network. Keep accounts and chat histories separate, reuse the NVIDIA GPU on the Windows PC, and create a tailored Business Management assistant without downloading another model.

**Status: Core LAN chat workflow validated (23 November 2026).** A MacBook reached the Open WebUI sign-in page using the Windows host's LAN IP and port 3000. A separate user account was created, given access to a custom `Business & Personal Assistant` profile, and successfully received an answer after the model context setting was corrected.

**Closure boundary:** Browser access, authentication and a functional customised chat are confirmed. Windows Firewall scope, boot persistence, simultaneous use, long-term performance and the pre-existing Piper TTS network connection were **not** revalidated as part of this change.

This is an extension of the [offline voice assistant project](local-ai-voice-assistant-2026-11-04.md) and the [local LLM inference project](local-ai-ollama-python-2026-11-03.md), not a separate AI server.

## Environment and scope

| Component | Implementation / observation |
| --- | --- |
| AI server | Existing MSI Windows workstation |
| GPU | NVIDIA RTX 4070 Ti, 12 GB VRAM |
| LLM runtime | Ollama installed on the Windows host |
| Web interface | Open WebUI container managed by Docker Desktop / WSL 2 |
| Local model used for troubleshooting | `qwen3.5:9b`; an `ollama ps` check showed `100% GPU` and `CONTEXT 4096` before the later context issue was resolved |
| Other model tried | `gemma4:12b` |
| Remote client | MacBook, Safari browser, on the home LAN |
| Application container | `open-webui` |
| Persistent data | Docker named volume `open-webui` at `/app/backend/data` |
| Windows-host bridge | `host.docker.internal:host-gateway` |
| Web UI port (before) | `127.0.0.1:3000->8080/tcp` |
| Web UI port (after) | `0.0.0.0:3000->8080/tcp` |
| Voice sidecar | `piper-tts`, still published at `127.0.0.1:5000->5000/tcp` |
| Router | No inbound Internet port-forwarding change was made during this work |

The workstation LAN IP has deliberately been omitted; use `<WINDOWS_LAN_IP>` in the examples. No real email address, passwords, session secrets or other credentials are recorded in this public repository.

## Architecture

```text
MacBook (Safari)                           Windows workstation (LAN)
Separate Open WebUI user                    NVIDIA RTX 4070 Ti 12 GB
        |                                               |
        | HTTP http://<WINDOWS_LAN_IP>:3000              |
        +-----------------------------------------------+
                                                        |
                                           Docker published TCP 3000
                                           0.0.0.0:3000 -> 8080
                                                        |
                                                Open WebUI
                                           Docker container / volume
                                                        |
                                         host.docker.internal:11434
                                                        |
                                                Ollama on Windows
                                                        |
                                             Qwen3.5 9B (GPU)
                                                        |
                                     Custom Business & Personal Assistant
                                     (system prompt + per-model settings)
```

Open WebUI handles the browser interface, user accounts, chat history, model profiles and permissions. Ollama performs inference on the Windows host; the MacBook is a **client**, not an inference server. A custom model profile changes the assistant's instructions and presentation, not the underlying weights or parameter count.

**Security boundary:** `0.0.0.0` binds the container's published port on **all applicable host interfaces**, not just the private LAN. Restrict access with an appropriately scoped Windows Firewall rule and router configuration. Browser access here is over plain HTTP and should be treated as suitable only for a trusted local network until HTTPS is configured. Do not expose port 3000 directly to the public Internet.

## Implementation record

These steps document what was observed and changed in this session. They are **not an unattended deployment script**. Inspect the live container before replacing it, especially its environment, volumes, network attachments, restart policy and security settings.

### 1. Identify why the MacBook could not reach the app

On the Windows PowerShell host:

```powershell
docker ps
```

The initial Open WebUI mapping was:

```text
127.0.0.1:3000->8080/tcp
```

This loopback binding only accepts published-port connections via the Windows host's own loopback interface; it does not provide normal LAN access to the MacBook.

### 2. Confirm data persistence and host routing before making changes

Read-only inspection:

```powershell
docker inspect open-webui --format '{{range .Mounts}}{{.Type}}: {{.Name}} -> {{.Destination}}{{println}}{{end}}'
docker inspect open-webui --format '{{json .HostConfig.ExtraHosts}}'
docker inspect open-webui --format '{{json .Config.Labels}}'
```

Observed:

```text
volume: open-webui -> /app/backend/data
["host.docker.internal:host-gateway"]
```

The labels listed image metadata and no Docker Compose project label, suggesting a direct `docker run` installation. The named volume means the application's database is stored independently of the replaceable container filesystem. **It is not itself a backup**; a separate volume backup is still advisable.

A previous inspection attempt using a nested quoted template failed with `template parsing error: function "com" not defined` because of PowerShell quoting. A subsequent PowerShell pipeline also failed because `docker inspect` returns an array. The simpler JSON format inspection worked.

### 3. Recreate only Open WebUI with a LAN-visible published port

The live session stopped and renamed the old container to `open-webui-backup`, disabled the old container's restart policy, and launched a replacement using the **same image ID**, existing named data volume, saved environment variables, restart policy and `host.docker.internal` mapping.

The material networking change was:

```text
Before: -p 127.0.0.1:3000:8080
After:  -p 0.0.0.0:3000:8080
```

The complete inspected runtime state was **not** reproduced in a portable Compose file. In particular, the recreation command did not explicitly restore membership in the previously documented `ai-voice` user-defined Docker network. This is an important verification item for the existing Piper voice integration.

No Ollama models were reinstalled, and the `piper-tts` container was not intentionally changed.

### 4. Verify published port and browser reachability

Post-change `docker ps` showed:

```text
open-webui   0.0.0.0:3000->8080/tcp
piper-tts    127.0.0.1:5000->5000/tcp
```

The replacement Open WebUI container was initially reported as `health: starting`; there was no later recorded `healthy` inspection. However, the MacBook successfully reached the sign-in screen and completed an interactive chat, which verifies application-level reachability.

Client browser URL, using the real Windows LAN address:

```text
http://<WINDOWS_LAN_IP>:3000
```

No router port-forwarding or cloud-hosted LLM service was required for the tested local-LAN path.

### 5. Add a separate user account

The remote user initially saw only `Sign In`. An administrator temporarily enabled `Enable New Sign Ups`, the family member completed `Sign Up`, and the administrator **disabled new sign-ups again** after account creation.

The account was intended to be a standard `User` account rather than an administrator. Its private chat history is distinct from the main administrator account.

The new user initially did not see a model to select; model visibility and access permissions were reviewed in Open WebUI. This is an **application permission** issue, not a sign that the MacBook lacks a GPU.

### 6. Resolve an insufficient context-window error

A short message, even a simple arithmetic question, failed with an error similar to:

```text
the prompt is longer than the context length currently available to the model
```

The remote account's effective context length was set to a little over 2,000 tokens. This limit covers more than the user's typed question: it also includes system instructions, recent history and any enabled tool descriptions.

The context setting was increased in Open WebUI, after which responses worked. An earlier local `ollama ps` showed a `4096` context for Qwen, but that earlier check does **not** establish the effective value of each later Open WebUI conversation. An `8192` context was proposed as a starting point; the final saved value for the new customised profile was not independently captured.

**Concept:** model size (`9B` / `12B`) is not context size (tokens). Raising context size can increase VRAM use and slow inference, especially for models near the GPU's 12 GB limit.

### 7. Create and share the customised academic assistant

In **Workspace / Models**, a new custom profile was created:

| Setting | Choice / evidence |
| --- | --- |
| Display name | `Business & Personal Assistant` |
| Intended base model | `qwen3.5:9b` (reuse existing Ollama model) |
| Description | `Academic and personal assistant for Business Management studies in the UK and everyday tasks.` |
| System prompt | Support Business Management topics, learning, coursework planning, British English writing, references and everyday activities |
| Model permissions | Family member explicitly added with `Read` access |
| Public editing | `Allow public write access` disabled |

The system prompt encourages teaching and critical thinking instead of doing assessed coursework without explanation; asks for British English when appropriate; and instructs the model **not to invent academic references**. These are behavioural guidelines rather than a guarantee of factual accuracy.

The access-control screenshot still showed the global visibility setting as `Public` while the family member had explicit `Read` permission. A switch to `Private` / restricted visibility was recommended, but the final visibility setting was **not confirmed**. Do not report the custom profile as private until this has been verified.

A separate existing `Homelab Technical Assistant` profile remained present; the new Business profile does not need another Ollama model download.

## Validation and evidence

| Test | Observed result | Status |
| --- | --- | --- |
| Persistent Open WebUI data location | Named volume `open-webui` mounted at `/app/backend/data` | Pass |
| Host mapping used by Ollama connection | `host.docker.internal:host-gateway` present before change and included in replacement command | Pass for configuration; inference revalidated through chat |
| LAN port mapping | `docker ps` showed `0.0.0.0:3000->8080/tcp` | Pass |
| MacBook access | Safari reached Open WebUI sign-in page | Pass |
| New user registration | Separate account created; sign-ups disabled afterwards | Pass |
| Custom assistant access | Separate user could select/use the Business assistant | Pass |
| Context issue | Very short prompts failed at ~2K context; worked after context was increased | Pass |
| Academic test | User confirmed customised assistant responded well | Pass, qualitative |
| Windows Firewall limited to trusted LAN | Rule not independently inspected | Not verified |
| Profile visibility is restricted to selected users | `Public` observed in screenshot, final selection unknown | Not verified |
| Piper voice after container recreation | Prior `ai-voice` network attachment may not have been restored | Not tested |
| Automatic restart after PC reboot | No reboot validation recorded | Not tested |
| Two simultaneous users / 24/7 load | No timing or concurrency benchmark | Not tested |
| Offline MacBook operation without Internet | Not retested for this LAN workflow | Not tested |

## Safe read-only follow-up checks

Run these in **PowerShell on the Windows host** when validating maintenance changes:

```powershell
docker ps --filter "name=open-webui"
docker inspect open-webui --format '{{json .NetworkSettings.Networks}}'
docker network inspect ai-voice
```

The second and third commands help determine whether the recreated Open WebUI can still reach `piper-tts` by container name. Do **not** run a second container or recreate the `ai-voice` network blindly. If Open WebUI is absent from that existing network, assess reconnecting the current container to it, then retest speech output.

For application performance, while a chat is active:

```powershell
ollama ps
```

The `PROCESSOR` and `CONTEXT` columns show the active model's current inference placement and context. They do not, by themselves, prove how much total VRAM is free.

## Security, limitations and operational notes

- Keep **new user registrations disabled** except when adding an authorised account.
- Use individual accounts and strong passwords; retain administrative rights only on the administrator account.
- Keep custom assistants read-only for ordinary users. Confirm whether `Public` visibility is actually desired, as explicit user access entries do not automatically make a public profile private.
- Scope inbound TCP/3000 in **Windows Firewall** to the trusted private network and appropriate source subnet; the Docker `0.0.0.0` binding is not a security boundary.
- Do not configure router port forwarding for this service. If access is needed outside the home later, evaluate an authenticated VPN and HTTPS rather than public HTTP exposure.
- Avoid committing `docker inspect` environment output, secrets, account details, or private prompts containing personal information to this public repository.
- Keep `piper-tts` on its existing localhost-only published port; do not expose it just to solve a Docker-internal network problem.
- Record the `open-webui-backup` container as a temporary rollback resource. Do not delete it before verifying the replacement's settings, volume, audio integration and a usable volume backup.
- A running container is not proof of healthy end-to-end inference; test with a real browser, a real model prompt and an authorised non-admin account.

## Troubleshooting summary

| Symptom | Cause / reasoning | Resolution or diagnostic |
| --- | --- | --- |
| Works at `localhost:3000` but not from MacBook | Docker port published only at `127.0.0.1` | Preserve application data and rebuild container with LAN-accessible port; verify Windows Firewall |
| New account only sees `Sign In` | Self-registration disabled | Enable sign-up temporarily; disable again after approved registration |
| New account has no model choices | Model visibility / permissions not set for user | Check Open WebUI account status, base-model access and custom-profile permissions |
| Even `2+2` exceeds context | Small effective context plus system/tools/history | Increase effective context in Open WebUI; retest a new chat; monitor VRAM |
| Model slower than expected | Potential GPU memory pressure, model switching or CPU offload | Check `ollama ps` during inference; compare controlled tests |
| Voice output stops after LAN migration | Possible lost Docker `ai-voice` network membership | Inspect network attachment and retest existing Piper route before changing settings |

## Learning outcomes and career relevance

This task exercises common entry-level infrastructure/support skills:

1. **Networking:** local vs all-interface bindings, IPv4 LAN addressing, TCP ports and firewall boundaries.
2. **Container operations:** inspect existing containers before editing; preserve volume data, image identity, environment and network attachment.
3. **Identity and access management:** separate accounts, registration policy, least-privilege model access.
4. **Troubleshooting:** distinguish network reachability, authorisation, model execution and context-window failures.
5. **Technical documentation:** preserve reproducible evidence, record unknowns and avoid publishing credentials.

The practical result is a functioning **self-hosted multi-user AI web interface**, not merely an installed package.

## Completion criteria

**Completed for version 1:** another household user can sign in from a MacBook on the LAN, select the customised Business assistant and obtain a working response; the core Open WebUI data volume was retained and registration was closed again.

**Focused follow-ups, not blockers for basic text chat:** verify `ai-voice` network and Piper, confirm the final custom-profile visibility, review Windows Firewall restrictions, validate a clean restart and make a recoverable volume backup. Concurrent-user performance tests can remain optional until they are needed.

No new hardware, separate server, Proxmox VM or model download is necessary for these follow-ups.
