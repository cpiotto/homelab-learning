# Local AI Technical Assistant — Model Evaluation (5 November 2026)

## Status
**Initial configuration validated; multi-turn diagnostic reliability not yet validated.** Selected provisional model: `deepseek-r1:8b`. No production deployment or automated remediation is claimed.

## Objective
Build a local, Brazilian-Portuguese troubleshooting assistant that helps investigate Linux, Windows, DNS, networking, Proxmox and Docker incidents **one read-only command at a time**. The goal is to develop sound diagnostic habits: observe, form hypotheses, test, interpret evidence, then proceed. Avoid making configuration changes before the cause is understood.

## Existing environment
- MSI Windows workstation, NVIDIA RTX 4070 Ti 12 GB.
- Ollama provides local model inference.
- Open WebUI runs in the existing Docker Desktop / WSL 2 environment.
- An Open WebUI custom model/profile named **Homelab Technical Assistant** was reused, changing its base model for each comparison.
- Candidate base models: `qwen3.5:9b`, `gemma4:12b`, and `deepseek-r1:8b`.
- The local voice assistant (Whisper/Piper) is a separate previously validated workflow; voice integration was **not** evaluated here.
- No additional Proxmox infrastructure or hardware was needed.

## Method
1. Test a model with a fixed diagnostic prompt in a **new chat**.
2. Check adherence to response format, exactly one read-only command, sensible first test, no invented observations, no premature changes, and waiting for command output.
3. Change the base model in the **same** Open WebUI custom profile; keep System Prompt v2 unchanged for the final cross-model comparison.
4. Record actual outputs observed in the conversation, including technical caveats.
5. Select a provisional default; do not extrapolate three initial replies into proof of full troubleshooting capability.

### System Prompt v2
The following is the complete prompt used for the final comparison:

```text
You are Homelab Technical Assistant, an expert in Linux, Windows, Networking, DNS, Proxmox and Docker.

Always respond in Brazilian Portuguese.

Your job is to guide the user through ONE diagnostic step per response.

MANDATORY RESPONSE FORMAT:

1. PROBLEMA
Briefly explain what we know and what remains uncertain.

2. PRÓXIMO TESTE
Provide exactly ONE read-only diagnostic command.
Explain what it does and why it is necessary.

3. RESULTADO ESPERADO
Explain possible outcomes without inventing results.

4. AGUARDANDO
Ask the user to execute the command and share its output. STOP.

STRICT RULES:
- Never provide more than ONE executable command per response.
- Never provide a complete troubleshooting plan.
- Never assume command results.
- Never assume infrastructure details not provided.
- Never modify configurations without explicit authorization.
- Always analyze the previous result before choosing the next test.
- Prefer testing the affected client before investigating servers.
- If the user asks a conceptual question, answer normally without requiring commands.
- Prioritize accuracy, safety and clarity over completeness.
```

## Test cases and observed results

### Test 1 — Windows DNS resolution
**User scenario:** A Windows computer can access external IP addresses but cannot resolve DNS names; Proxmox hosts a Debian BIND9 server. Investigate progressively, without changing settings.

- **Qwen 3.5 9B:** Followed the four-section format and provided one command: `nslookup www.google.com <IP_DO_SEU_SERVIDOR_BIND>`. It waited for the result. **Limitation:** it tested BIND directly before identifying the DNS servers actually configured on the Windows client. Some possible-result explanations were overconfident.
- **Gemma 4 12B:** Returned a multi-stage troubleshooting plan with multiple commands, including `nslookup`, `dig @localhost`, `systemctl status bind9`, `ss`, and log/firewall checks. **Limitation:** violated the one-command-and-wait rule, although most commands were observational.
- **DeepSeek R1 8B:** Followed the format, suggested **`ipconfig /all`**, explained that it reveals configured DNS resolvers, and waited. **Caveat:** finding a public resolver does not alone prove misconfiguration; it depends on the intended DNS architecture.

### Test 2 — Docker service unreachable after reboot
**User scenario:** A Debian 12 server on Proxmox is accessible via SSH, but a previously reachable Docker-hosted service stopped responding after reboot. No restarts or changes permitted during diagnosis.

- **DeepSeek R1 8B:** Suggested **`systemctl status docker`** and waited. Appropriate read-only first check for daemon status.
- **Caveat:** an active Docker daemon does not establish that the relevant container or application is healthy; status output may not explain the failure.

### Test 3 — Connectivity between Debian hosts
**User scenario:** Debian server A has internet connectivity but cannot communicate with server B on the local network. Diagnose without configuration changes.

- **DeepSeek R1 8B:** Suggested **`ping -c 4 servidorB`**, explained basic ICMP connectivity, and waited.
- **Caveat:** prefer the known IP address when separating IP connectivity from name resolution. ICMP failure does not prove all application traffic is blocked; ICMP success does not prove the desired service is reachable.

## Summary

| Model | DNS test: one command | DNS: first-test choice | Docker test | Network test | Assessment |
|---|---|---|---|---|---|
| Qwen 3.5 9B | Yes | Valid but not ideal | Not tested | Not tested | Followed format after prompt simplification |
| Gemma 4 12B | No | Broad multi-step plan | Not tested | Not tested | Did not follow interaction constraints |
| DeepSeek R1 8B | Yes | Good: `ipconfig /all` | Good: `systemctl status docker` | Reasonable: `ping -c 4` | Provisional choice |

**Important comparison limitation:** Only the DNS scenario was repeated across all three models. The Docker and networking scenarios were run only with DeepSeek. This is **not** a statistically valid general model ranking. A displayed 'thought for N seconds' indicator is not a controlled throughput or latency benchmark.

## Reproduction (no additional installation)
1. Confirm Ollama already has the desired model; for DeepSeek, the downloaded model was `deepseek-r1:8b`.
2. Open Open WebUI → Workspace → Models → **Homelab Technical Assistant**.
3. Set the base model to `deepseek-r1:8b`; retain the prompt above and save.
4. Start a **new conversation** for each test case.
5. Record the first proposed command, its explanation, and whether the assistant waits.
6. In a real incident, inspect commands before execution. Do not treat model output as an authoritative diagnosis.

## Risks and known limitations
- **Prompt compliance is not guaranteed:** three successful first replies do not validate longer multi-turn troubleshooting.
- **Hallucinations and diagnostic overconfidence:** possible even when the format is correct.
- **Security and privacy:** command output can expose hostnames, private addresses, usernames, network configuration, and secrets. Redact before sharing or publishing.
- **Operational safety:** keep changes and restarts under human approval; do not enable autonomous shell execution.
- **Performance:** no controlled tokens/second, GPU utilization, cold-start timing, or power measurements were captured for this evaluation.
- **Scope:** no evidence here of multi-user concurrency, remote access, persistent assistant memory, or integration with voice/ESP32.

## Lessons learned
- A short, explicit system prompt with a mandatory response structure worked better in the observed tests than repeatedly adding more rules.
- A useful troubleshooting assistant should **identify the affected client and collect evidence first**, rather than jump to the most visible server.
- Evaluate **process quality** separately from technical correctness; an obedient response can still contain inaccurate conclusions.
- Choose a working baseline and document its limitations instead of endlessly tuning prompts.

## Completion criteria and next step
**Completed:** local profile configuration, fixed prompt, three DeepSeek first-step scenarios, comparison with Qwen and Gemma in the shared DNS scenario, and documented caveats.

**Pending, non-blocking:** one real **multi-turn** incident simulation with command outputs and follow-up decisions; optional latency/VRAM measurements using consistent conditions. Revisit the model choice only if practical evidence warrants it.

This project supports entry-level IT support, Linux administration, networking troubleshooting, documentation, and later AI infrastructure skills.
