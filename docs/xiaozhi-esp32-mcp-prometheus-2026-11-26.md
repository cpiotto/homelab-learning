# Voice-driven infrastructure monitoring with ESP32, MCP and Prometheus

**Date:** 26 November 2026  
**Status:** Core integration validated; failure-path testing remains outstanding.

## Objective

Extend the existing [Xiaozhi DNS integration](xiaozhi-esp32-mcp-dns-2026-11-22.md) with a read-only tool that reports the availability of Prometheus scrape targets through spoken questions, without changing ESP32 firmware or deploying another service.

## Architecture

```text
ESP32 Xiaozhi → existing Xiaozhi service / MCP bridge
                         |
               ansible01 (LXC 202, pve3080b)
               FastMCP over stdio
                 |                  |
             check_dns          check_servers
                 |                  |
               BIND9          Prometheus HTTP API
```

The existing systemd service launches `mcp_pipe.py check_dns.py` using the Python virtual environment in `/opt/xiaozhi-mcp`. The new function is imported and registered on the same FastMCP instance. No systemd unit, MCP configuration file or firmware change was required.

## Implementation

From the Proxmox host, enter the container with `pct enter 202`. The initial HTTP test failed because curl was absent; after addressing that prerequisite, the following query succeeded:

```bash
curl -sS --max-time 10 'http://192.168.1.238:9090/api/v1/query?query=up'
```

Prometheus returns an instant vector. A value of 1 means the last scrape succeeded; 0 means it failed. This is not equivalent to proving that a host is powered on or that every service is healthy.

Back up the existing tool:

```bash
cd /opt/xiaozhi-mcp
cp check_dns.py check_dns.py.bak
```

Create `check_servers.py`:

```python
import json
import urllib.request

def check_servers() -> dict:
    """Check the availability of all monitored homelab servers using Prometheus."""
    url = "http://192.168.1.238:9090/api/v1/query?query=up"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.load(response)
        if data.get("status") != "success":
            raise ValueError("Prometheus query failed")
        servers = []
        for target in data["data"]["result"]:
            name = target["metric"]["instance"]
            status = "online" if target["value"][1] == "1" else "unreachable"
            servers.append({"name": name, "status": status})
        online = sum(s["status"] == "online" for s in servers)
        return {
            "status": "success" if servers else "no_data",
            "total": len(servers),
            "online": online,
            "unreachable": len(servers) - online,
            "servers": servers
        }
    except Exception as error:
        return {"status": "failed", "error": str(error)}
```

Add `from check_servers import check_servers` after the existing imports in `check_dns.py`, and `mcp.tool()(check_servers)` before its main guard. The original DNS function remains unchanged.

```bash
.venv/bin/python -c 'from check_servers import check_servers; import json; print(json.dumps(check_servers(), indent=2))'
.venv/bin/python -m py_compile check_dns.py check_servers.py
systemctl restart xiaozhi-mcp
systemctl status xiaozhi-mcp --no-pager
```

## Validation evidence

The direct API query and standalone Python test both returned seven successful scrape targets:

| Target | Result |
| --- | --- |
| prometheus:9090 | UP |
| pve3080 | UP |
| pve | UP |
| pve3090 | UP |
| pve3080b | UP |
| dns01 | UP |
| PiottoDesktop | UP |

Python returned `status: success`, `total: 7`, `online: 7`, `unreachable: 0`. The restarted systemd service reported active (running) and enabled. The operator confirmed all three spoken checks succeeded: target availability, target count and names, and the original DNS resolution check. Exact spoken transcripts and post-restart journal entries were not captured.

## Security and rollback

The new tool issues a fixed, read-only HTTP query to a private LAN endpoint; no arbitrary commands or write operations are exposed by this function. Keep Prometheus restricted to trusted networks. Its HTTP connection is not encrypted. The existing bridge authentication is unchanged; do not publish its token or credentials.

If the new registration fails, restore the backup and restart the service:

```bash
cd /opt/xiaozhi-mcp
cp check_dns.py.bak check_dns.py
systemctl restart xiaozhi-mcp
```

## Limitations and closure

- Only returned scrape targets are counted; AdGuard Home was not present in the observed query.
- A successful scrape is not a comprehensive host or application health check; missing series may be absent from the response.
- A failed scrape, empty response and API timeout have not been deliberately tested.
- Full container reboot recovery and long-term stability remain unverified.
- Core read-only voice integration and DNS regression checks are complete. GPU metrics are an optional next increment, not a requirement for closure.

## Skills demonstrated

Python functions, standard-library HTTP requests, JSON parsing, exception handling, PromQL, REST API troubleshooting, Linux systemd, incremental testing, MCP tool registration and safe rollback.
