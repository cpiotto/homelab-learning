# ESP32 Xiaozhi MCP Integration: Voice-Controlled BIND9 DNS Health Check — 22 November 2026

## Objective and outcome

Integrate an existing ESP32-S3 Xiaozhi voice assistant with the homelab's BIND9 DNS server using a custom, read-only Model Context Protocol (MCP) tool. Preserve the working ESP32 firmware and voice settings; reuse the existing Debian container; avoid exposing administrative services or opening inbound router ports.

**Status: Version 1 functionally complete (22 November 2026).** A spoken command reached a custom Python tool running in the existing `ansible01` LXC container, queried BIND9, and produced a prompt spoken response on the ESP32. The MCP connection was subsequently moved from an interactive terminal into a `systemd` service and worked again after a service restart. The service was confirmed `enabled` for container startup. A full container reboot and long-term reliability testing were **not** performed.

This is a **cloud-assisted voice/MCP integration**, not an offline voice assistant. It is separate from the [fully offline workstation voice project](local-ai-voice-assistant-2026-11-04.md).

## Scope and environment

| Component | Implementation / observation |
| --- | --- |
| Voice client | ESP32-S3 device running existing Xiaozhi firmware; voice and firmware unchanged |
| Xiaozhi console | Agent configured for Brazilian Portuguese; Extensions > Custom Services > MCP Endpoint |
| Cloud connection | Outbound authenticated WebSocket (WSS) to Xiaozhi MCP endpoint |
| Proxmox host | `pve3080b`, LXC CT 202 |
| MCP client container | `ansible01`, Debian 13; also hosts existing Ansible installation |
| Python | 3.13.5; isolated virtual environment with pip 25.1.1 initially |
| DNS server | `dns01` / BIND9, `192.168.1.195`, UDP/53 |
| Test domain | `example.com`, IPv4 A records |
| Bridge source | `https://github.com/78/mcp-calculator` at commit `c537f71d61fd73b47d6c8955b5df6d3721acf4e4` |
| Bridge installation | `/opt/xiaozhi-mcp` |
| Tool | `check_dns`, implemented in `check_dns.py` with `FastMCP` and `dnspython` |
| Service | `xiaozhi-mcp.service` managed by `systemd` |
| Credentials | `/etc/xiaozhi-mcp/bridge.env`, mode `600`, owner `root:root` |

The example uses private RFC1918 addresses from this lab. They are not public Internet endpoints. No inbound port forwarding or new VM was required.

## Architecture and request path

```text
Person asks: "Nexo, use check_dns to check my DNS server."
   |
   v
ESP32-S3 Xiaozhi (microphone / speaker)
   |
   v
Xiaozhi cloud agent
   |
   | WSS: authenticated MCP endpoint (outbound from homelab)
   v
Existing Debian 13 LXC CT 202: ansible01 (on pve3080b)
   |
   +-- systemd: xiaozhi-mcp.service
   |     |
   |     +-- Python: mcp_pipe.py check_dns.py
   |           |
   |           +-- MCP stdio tool: check_dns()
   |                 |
   |                 +-- dnspython query, UDP/53
   |                       |
   |                       v
   |                 BIND9 / dns01 (192.168.1.195)
   |                       |
   |                       +-- resolves example.com A
   |
   +-- MCP result -> Xiaozhi cloud -> ESP32 spoken answer
```

**Trust boundary:** The device sends the voice interaction through Xiaozhi's cloud service. The bridge authenticates using a secret-bearing WSS URL. The tool does not expose a generic remote shell or perform DNS administration. It calls the BIND9 resolver directly, **not** through AdGuard Home; therefore this experiment does not validate AdGuard filtering or the AdGuard-to-BIND9 forwarding chain.

## Implementation record

The commands below reflect the successful session. They are a record of a working lab, **not a one-click deployment script**. Review commands and package versions before reproducing them. Do not overwrite existing files or launch duplicate bridge processes on a live environment. Run `pct` commands on the Proxmox host; commands without `pct` below run as root *inside* the LXC container.

### 1. Verify existing container, Python and network prerequisites

On `pve3080b`:

```bash
pct status 202
pct exec 202 -- bash -lc 'python3 --version; git --version; command -v dig || echo "dig not installed"'
pct exec 202 -- dig @192.168.1.195 example.com A +time=2 +tries=1
```

Observed:

- CT 202 reported `status: running`.
- Python was `3.13.5`; `dig` was already installed; Git was initially missing.
- BIND9 returned `status: NOERROR`, two A records for `example.com` (`172.66.147.243` and `104.20.23.154` at that time), via `192.168.1.195#53` (UDP), with an observed `Query time: 373 msec`.
- Those IP addresses and query times are point-in-time observations, not expected permanent values.

An HTTPS connectivity test from the container returned `GitHub HTTPS: 200`.

### 2. Troubleshoot and validate Python virtual environments

The first attempt to create `/tmp/xiaozhi-venv-test` failed because Debian did not have `ensurepip` for Python 3.13.

Solution, run from the Proxmox host:

```bash
pct exec 202 -- apt update
pct exec 202 -- apt install python3.13-venv
pct exec 202 -- python3 -m venv --clear /tmp/xiaozhi-venv-test
pct exec 202 -- /tmp/xiaozhi-venv-test/bin/python -m pip --version
```

Observed: `pip 25.1.1` running under Python 3.13. The isolated environment prevented changing system-wide Python packages used by Ansible.

### 3. Obtain bridge source and install its Python dependencies

Git was installed in CT 202. The bridge was cloned and checked out at a specific revision:

```bash
pct exec 202 -- apt install git
pct exec 202 -- bash -lc 'git clone https://github.com/78/mcp-calculator.git /opt/xiaozhi-mcp && cd /opt/xiaozhi-mcp && git checkout c537f71d61fd73b47d6c8955b5df6d3721acf4e4 && cat requirements.txt'
```

The detached-HEAD notice is expected when checking out a commit rather than a branch. The source declares minimum versions rather than fully pinned dependencies.

The following creates a dedicated environment and installs the source's requirements:

```bash
pct exec 202 -- bash -lc 'python3 -m venv /opt/xiaozhi-mcp/.venv && /opt/xiaozhi-mcp/.venv/bin/python -m pip install -r /opt/xiaozhi-mcp/requirements.txt'
```

The installation completed successfully on 22 November 2026, including `mcp 1.30.0`, `mcp-proxy 0.15.0`, `fastmcp 3.4.11`, `websockets 17.4` and `dnspython 2.9.2`. This demonstrates a successful installation on Python 3.13 but is **not** a guarantee of compatibility with future releases.

### 4. Create the read-only DNS MCP tool

Source: [`check_dns.py`](../examples/xiaozhi-mcp/check_dns.py).

The tool has **no user-supplied domain or server arguments**. It always queries `example.com` A through the known BIND9 IP using a three-second overall timeout. It returns either `status: working` with the DNS answers or `status: failed` with an error. The complete working example is kept in the linked source file.

The file was created in `/opt/xiaozhi-mcp/check_dns.py` and tested directly:

```bash
cd /opt/xiaozhi-mcp
.venv/bin/python -c "from check_dns import check_dns; print(check_dns())"
```

Actual observed output:

```python
{'server': '192.168.1.195', 'status': 'working', 'domain': 'example.com', 'addresses': ['104.20.23.154', '172.66.147.243']}
```

This direct Python call validates name resolution and function output, but does not by itself validate MCP tool discovery or voice invocation.

### 5. Connect the tool to the Xiaozhi MCP endpoint

In the Xiaozhi console, the agent's **Extensions > Custom Services > MCP Endpoint** section displayed the WSS endpoint. The secret-bearing full URL was entered privately in the container:

```bash
cd /opt/xiaozhi-mcp
read -r -s -p "Paste the complete MCP endpoint: " MCP_ENDPOINT
echo
export MCP_ENDPOINT
.venv/bin/python mcp_pipe.py check_dns.py
```

**Never commit or paste the full MCP endpoint URL, screenshots with a visible token, or the shell environment file.** The WebSocket URL contains an authentication token. The example commands above deliberately do not include a real URL.

Observed initial logs included:

```text
Connecting to WebSocket server...
Successfully connected to WebSocket server
Started server process: /opt/xiaozhi-mcp/.venv/bin/python check_dns.py
Processing request of type ListToolsRequest
```

The Xiaozhi console showed **Endpoint Status: Online** and **Enabled Services: check_dns**. A voice request from the ESP32 returned an appropriate answer, and the container logs showed `CallToolRequest`. This confirms tool execution in addition to connection/discovery. The process was then stopped intentionally with Ctrl+C; the log showed orderly server process termination.

### 6. Protect credentials and run via systemd

The running shell's `MCP_ENDPOINT` variable was used to save the token into a local root-owned environment file:

```bash
test -n "$MCP_ENDPOINT" && \
install -d -m 700 /etc/xiaozhi-mcp && \
(umask 077; printf 'MCP_ENDPOINT=%s\n' "$MCP_ENDPOINT" > /etc/xiaozhi-mcp/bridge.env) && \
echo "Credential saved"
stat -c '%a %U:%G' /etc/xiaozhi-mcp/bridge.env
```

Observed permissions: `600 root:root`. The directory was created with mode `700`.

The [`xiaozhi-mcp.service` example](../examples/xiaozhi-mcp/xiaozhi-mcp.service) reproduces the unit installed at `/etc/systemd/system/xiaozhi-mcp.service`. Key decisions:

- `EnvironmentFile` loads the local credential without embedding it in the service definition.
- `DynamicUser=yes`, `NoNewPrivileges=yes`, `ProtectSystem=strict`, `ProtectHome=yes` and `PrivateTmp=yes` reduce exposure of the running service.
- `Restart=on-failure` with `RestartSec=5` attempts recovery from process failures.
- `Wants=network-online.target` and `After=network-online.target` express a dependency on network readiness.
- `WorkingDirectory` and `ExecStart` invoke the already-tested venv and Python bridge.

The system manager reads the `EnvironmentFile` to start the service; the protected credential must remain **on the container**, not in this repository. Environment variables are not a general-purpose secret vault: privileged local users and diagnostic tools may still inspect them. Do not expose detailed process environments or WSS URLs in public logs.

Deployment and verification:

```bash
systemctl daemon-reload
systemctl start xiaozhi-mcp
systemctl is-active xiaozhi-mcp
journalctl -u xiaozhi-mcp -n 25 --no-pager
systemctl enable xiaozhi-mcp
systemctl is-enabled xiaozhi-mcp
systemctl restart xiaozhi-mcp
systemctl status xiaozhi-mcp --no-pager
```

Observed: `active` and `enabled`. Logs showed successful WebSocket connection, Python subprocess startup, `ListToolsRequest` and later `PingRequest`. After `systemctl restart`, the ESP32 again answered the DNS-check request successfully.

**Boot semantics:** `systemctl enable` prepares startup when CT 202 boots. It does not by itself configure Proxmox to power on CT 202 when the Proxmox host starts. The container's Proxmox `onboot` configuration was not checked in this session.

## Test evidence summary

| Test | Evidence | Result |
| --- | --- | --- |
| CT health | `pct status 202` → `running` | Pass |
| Direct BIND9 query | `dig` → `NOERROR`; two `example.com` A records | Pass |
| Python venv | `pip 25.1.1` under Python 3.13 | Pass after installing `python3.13-venv` |
| Python tool | `check_dns()` → `status: working` | Pass |
| Bridge connection | `Successfully connected to WebSocket server` | Pass |
| Tool discovery | Console showed `check_dns`; `ListToolsRequest` logged | Pass |
| Voice invocation | ESP32 responded and `CallToolRequest` logged | Pass |
| Managed service | `systemctl is-active` → `active`; `PingRequest` logged | Pass |
| Service restart | Voice request succeeded again after restarting service | Pass |
| Startup configuration | `systemctl is-enabled` → `enabled` | Pass |
| Full CT reboot recovery | No full container reboot performed | **Not tested** |
| Long-duration / disconnect recovery | No extended observation recorded | **Not tested** |

## Troubleshooting and lessons learned

1. **Python `venv` failure:** Debian installed the Python interpreter without the matching `ensurepip` support; installing `python3.13-venv` fixed virtual environment creation.
2. **Git missing:** `git` was not initially installed on CT 202; add only what is required.
3. **Very early active status is not proof of readiness:** The first `systemctl status` was captured 14 ms after startup. Checking `journalctl` provided stronger evidence of authenticated WebSocket connection and tool discovery.
4. **A configured tool is not a called tool:** Seeing `check_dns` in the console validated discovery, while a real voice request plus `CallToolRequest` validated execution.
5. **Foreground testing before service installation:** Validating interactively first made it easier to isolate DNS, Python, MCP and service-management issues.
6. **Keep Python dependencies isolated:** The pre-existing Ansible installation was left intact; no new Proxmox host or container was created.

## Security, limitations and next work

- **Do not commit credentials:** `/etc/xiaozhi-mcp/bridge.env` and any endpoint token are intentionally absent. If an entire token-bearing URL is ever exposed publicly, rotate or invalidate it using the provider's available controls.
- **Cloud dependency:** WSS connectivity and Xiaozhi cloud availability are required for this voice-to-tool path. This is not an offline voice system.
- **Limited health coverage:** A successful `example.com` A lookup tests one recursive IPv4 DNS resolution path, not internal `home.arpa` records, TCP fallback, DNSSEC enforcement, IPv6, all clients, upstream reachability under every condition, or AdGuard filtering.
- **Availability:** The bridge runs while CT 202 is online; the Proxmox container `onboot` state and full host/container restart recovery remain untested.
- **Dependency drift:** Bridge source was checked out at a specific commit but Python package requirements use minimum version ranges. Freeze/lock dependencies before future redeployment if reproducibility becomes necessary.
- **External tool boundary:** The currently deployed tool has a fixed DNS query and returns data only. Additional tools should use least privilege and avoid unrestricted shell execution.
- **Data exposure:** Public documentation uses private IP addresses already documented in this homelab; do not post device identifiers, real secrets, screenshots exposing the WSS token or private configuration files.

## Post-change smoke check — 23 November 2026

Following the separate Windows Open WebUI LAN-access change, the operator reported that the ESP32 Xiaozhi assistant **continued responding to a voice question about the DNS server**. This provides useful continuity evidence for the ESP32 voice interface. The session did not capture a fresh MCP `CallToolRequest`, DNS query, or service journal entry, so the observation alone must not be treated as a newly verified end-to-end DNS tool invocation. The original 22 November end-to-end evidence remains valid for the earlier validation.

The ESP32 Xiaozhi/MCP DNS path is architecturally independent of the Windows-hosted Open WebUI/Piper text-to-speech path. Successful ESP32 speech does **not** validate that Piper TTS is still reachable from the recreated `open-webui` container.

## Closure

**Version 1 closure decision: complete for the intended read-only voice DNS check.** Verified: an ESP32 voice command triggered `check_dns` via Xiaozhi/MCP; the Debian container queried BIND9; the tool returned a response; the bridge worked again after a `systemd` service restart; automatic startup at the Linux service level was enabled.

**Documented non-blocking follow-up:** Test a full CT 202 restart and verify Proxmox `onboot` separately during planned maintenance. Expansion to AdGuard status, additional DNS checks, monitoring or local Ollama is optional future work and **not required** to consider this first integration finished.

## Skills demonstrated

- Linux package management and Python virtual environments
- Proxmox/LXC service reuse and network testing
- DNS resolution testing with `dig` and `dnspython`
- Python development with a read-only MCP tool
- WebSocket-based system integration and credential handling
- `systemd` unit management, service logs and troubleshooting
- Evidence-based validation, security boundaries and technical documentation
