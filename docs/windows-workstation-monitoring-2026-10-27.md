# Windows Workstation Monitoring with Prometheus and Grafana — 27 October 2026

## Objective

Integrate a Windows gaming and development workstation into an existing Linux-based homelab monitoring stack, without deploying a second monitoring server or interfering with normal desktop use.

**Status:** Core monitoring implemented and validated on 27 October 2026. Security hardening and long-term availability remain subject to periodic review.

## Environment

| Component | Configuration |
| --- | --- |
| Windows workstation | `PiottoDesktop` (MSI MAG Infinite S3) |
| Workstation hardware | Intel Core i5-14400F (16 logical processors), 16 GB DDR5, NVIDIA RTX 4070 Ti |
| LAN address (DHCP at test time) | `192.168.1.248` |
| Connection | Intel Wi-Fi 6 AX201 |
| Windows metrics | `windows_exporter` v0.32.0, TCP 9182 |
| Monitoring LXC | `monitor01` (CT 200), `192.168.1.238` |
| Metrics store | Prometheus in Docker, TCP 9090 |
| Visualisation | Grafana in Docker, TCP 3000 |
| Grafana dashboard | Grafana Labs dashboard 24390, Windows Exporter Dashboard 2025 |

All addresses above are lab-specific and must be adapted before reuse.

## Architecture

```text
PiottoDesktop (Windows, 192.168.1.248)
  └── windows_exporter (:9182)
        ↑ HTTP /metrics, scraped every 15 seconds
monitor01 (Debian LXC, 192.168.1.238)
  └── Docker
      ├── Prometheus (:9090) ── metrics storage
      └── Grafana (:3000) ──── dashboards
```

Prometheus **pulls** metrics from the Windows Exporter. The desktop is not a 24/7 server, so collection stops when it is switched off, asleep or unavailable on Wi-Fi.

## Implementation

### 1. Troubleshoot LAN routing

Initially, a TCP connection to `192.168.1.238:9090` succeeded, but Windows selected the `Tailscale` interface and source address `100.80.22.91` instead of the local Wi-Fi interface.

`Find-NetRoute -RemoteIPAddress 192.168.1.238` and `Get-NetRoute -DestinationPrefix 192.168.1.0/24` showed two competing /24 routes:

| Route | Route metric | Interface metric | Combined |
| --- | ---: | ---: | ---: |
| Tailscale | 0 | 5 | 5 |
| Wi-Fi | 256 | 35 | 291 |

Tailscale's accepted subnet route was preferred. On this local Windows workstation, the following setting disabled acceptance of advertised subnet routes:

```powershell
tailscale set --accept-routes=false
```

A subsequent `Find-NetRoute` selected `Wi-Fi 2` with source `192.168.1.248`; `Test-NetConnection 192.168.1.238 -Port 9090` returned `TcpTestSucceeded : True`.

**Trade-off:** this setting can stop the workstation accessing *remote subnets* through Tailscale subnet routers. Tailscale peer access via tailnet addresses remains a separate capability. It does not remove subnet advertisements from other devices.

### 2. Install and test Windows Exporter

Installed the official Windows x64 MSI for `windows_exporter` v0.32.0 with the HTTP metrics endpoint on port 9182.

Validated the Windows service:

```powershell
Get-Service windows_exporter
```

Observed state: `Running`.

Validated local HTTP access:

```powershell
(Invoke-WebRequest -Uri "http://localhost:9182/metrics" -UseBasicParsing).StatusCode
```

Observed response: `200`. The `-UseBasicParsing` flag avoids the legacy Windows PowerShell 5.1 parsing prompt.

### 3. Limit the inbound firewall rule

Created an explicit Windows Defender Firewall inbound allow rule:

```powershell
New-NetFirewallRule `
  -DisplayName "Homelab - Prometheus Windows Exporter" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 9182 `
  -RemoteAddress 192.168.1.238 `
  -Action Allow `
  -Profile Any
```

Verified that the rule was enabled, set to inbound/allow, matched TCP/9182 and specified remote address `192.168.1.238`.

**Security limitation:** validating this allow rule does **not** prove that no other broader firewall rule permits port 9182. A separate firewall policy review is optional future hardening. Do not expose the exporter to the public Internet.

From the Proxmox host running CT 200, tested the network path *inside the monitoring LXC*:

```bash
pct exec 200 -- curl -s -o /dev/null -w "%{http_code}\n" http://192.168.1.248:9182/metrics
```

Observed response: `200`.

### 4. Add the Windows target to Prometheus

Existing Prometheus configuration on `monitor01`:

```text
/opt/monitoring/prometheus/prometheus.yml
```

The Docker container sees the file as `/etc/prometheus/prometheus.yml`, mounted read-only. A backup was created before editing.

Added a separate scrape job alongside existing Linux `node_exporter` targets:

```yaml
  - job_name: "windows_exporter"
    static_configs:
      - targets: ["192.168.1.248:9182"]
        labels:
          instance: "PiottoDesktop"
```

The configuration's global scrape interval is `15s`. Preserve the existing `global:`, `scrape_configs:`, `prometheus` and `node_exporter` jobs when adapting this snippet.

### 5. Troubleshoot YAML and file bind mounts

An initial `promtool check config` failed due to incorrectly indented YAML; `- job_name: "windows_exporter"` had been nested under the previous job's `static_configs`.

Tools used:

```bash
pct exec 200 -- nl -ba /opt/monitoring/prometheus/prometheus.yml
pct exec 200 -- sed -n '25,40l' /opt/monitoring/prometheus/prometheus.yml
```

After fixing indentation with `sed -i`, the LXC file showed the correct contents, but `docker exec prometheus ...` still displayed the earlier version. Docker had a **read-only single-file bind mount**, and `sed -i` can replace a file with a new inode, leaving the running bind mount referring to the old inode.

Checked the updated source independently in a temporary container:

```bash
pct exec 200 -- docker run --rm \
  -v /opt/monitoring/prometheus/prometheus.yml:/tmp/prometheus.yml:ro \
  --entrypoint promtool prom/prometheus:latest \
  check config /tmp/prometheus.yml
```

Observed: `SUCCESS: /tmp/prometheus.yml is valid prometheus config file syntax`.

The service definition in `/opt/monitoring/compose.yaml` used a named `prometheus-data` volume. Recreated **only** the Prometheus service, without pulling another image or removing volumes:

```bash
pct exec 200 -- sh -c 'cd /opt/monitoring && docker compose up -d --no-deps --force-recreate --pull never prometheus'
```

Prometheus restarted; Grafana and Uptime Kuma remained running. The Prometheus target-health page showed **7/7 UP** (five Linux targets, Prometheus itself and `PiottoDesktop`).

### 6. Configure Grafana dashboards

Grafana's Prometheus data source URL was already `http://prometheus:9090`; the **Save & test** result was `Successfully queried the Prometheus API`.

Imported Grafana Labs dashboard **24390** (Windows Exporter Dashboard 2025) and selected the existing `prometheus` data source.

Several resource panels worked straight away, including memory, disks, network and processes. CPU panels initially showed `No data`, because the dashboard's earlier query expected `windows_cpu_time_total`, which was not available in the collected series.

Exploration found 16 series each for `windows_cpu_processor_utility_total` and `windows_cpu_processor_rtc_total`. The following query produced a working CPU utilisation chart for `PiottoDesktop`:

```promql
avg by (instance) (
  clamp_max(
    rate(windows_cpu_processor_utility_total{instance="PiottoDesktop"}[2m])
    /
    rate(windows_cpu_processor_rtc_total{instance="PiottoDesktop"}[2m]),
    100
  )
)
```

Used this expression to repair the CPU Usage by Host, compact CPU Usage and CPU Utilization panels. During observation, the resulting CPU graph showed roughly 11–18% utilisation. This is a **sample from the validation session**, not a benchmark or long-term measurement.

The exporter also exposed volumes `C:`, `D:`, `E:` and `HarddiskVolume5`. The additional volumes were identified as recovery-related partitions from a previous storage change. To avoid misleading low-space indicators, the dashboard was filtered to the main `C:` volume.

Example C: occupancy:

```promql
100 * (
  1 - windows_logical_disk_free_bytes{instance="PiottoDesktop",volume="C:"}
    / windows_logical_disk_size_bytes{instance="PiottoDesktop",volume="C:"}
)
```

For the Remaining Disk Space panel, preserved the existing dashboard variables and both free/total series:

```promql
windows_logical_disk_free_bytes{job=~"$job",instance=~"$instance",volume="C:"}
```

```promql
windows_logical_disk_size_bytes{job=~"$job",instance=~"$instance",volume="C:"}
```

The C: usage panel showed approximately 26.3% occupied and the available-space panel roughly 716 GB free during validation.

## Evidence and validation

| Test | Result |
| --- | --- |
| Windows route to monitor01 | Wi-Fi 2 chosen, source 192.168.1.248 |
| TCP to Prometheus from MSI | `TcpTestSucceeded : True` |
| Windows Exporter service | `Running` |
| Local Windows Exporter endpoint | HTTP `200` |
| Exporter endpoint from monitor01 | HTTP `200` |
| Updated Prometheus source config | `promtool` SUCCESS |
| Prometheus target health | 7/7 UP, including PiottoDesktop |
| Grafana Prometheus data source | API query successful |
| CPU utilisation | Corrected panels displayed readings |
| Disk occupancy | Dashboard adjusted to display C: only |

These results are based on interactive tests and dashboard screenshots taken during the session; screenshots are not yet stored in this repository.

## Lessons learned

- A successful connection does not prove the optimal interface or route was selected.
- Windows Firewall rule scope should be verified separately from exporter availability.
- Prometheus pull-based collection makes endpoint reachability and lab IP stability important.
- YAML indentation can stop a service loading its updated configuration.
- Replacing a file that is mounted as an individual Docker bind mount can leave the running container referencing the former inode.
- `promtool` validation before deployment reduces configuration risk.
- Community Grafana dashboards may need PromQL changes when exporter metrics evolve.
- Recovery partitions should be distinguished from primary storage before treating low free space as an incident.

## Known limitations and next actions

- The MSI's `192.168.1.248` address was assigned by DHCP. Reserve an address or update the target if it changes.
- Windows monitoring is only available while the workstation is powered on and reachable.
- Review all effective Windows Firewall rules before claiming strict network isolation of port 9182.
- Pin Prometheus and Grafana image versions during a future maintenance cycle instead of relying indefinitely on `:latest`.
- Add selected redacted screenshots when available; do not include user credentials, tokens or sensitive host data.
- GPU-specific metrics are intentionally **out of scope** for this completed monitoring task.

## Skills demonstrated

Windows administration · TCP/IP routing · Tailscale route selection · firewall scoping · Linux CLI · Proxmox LXC · Docker Compose and bind mounts · YAML debugging · Prometheus · PromQL · Grafana · troubleshooting and verification.
