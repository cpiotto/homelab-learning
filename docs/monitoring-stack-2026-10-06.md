# Central homelab monitoring stack - 6 October 2026

## Goal

Build a dedicated monitoring environment for all four Proxmox hosts using open-source tools commonly found in infrastructure and operations environments.

The monitoring workload was deployed on `pve3080` instead of duplicating the Ubuntu VM workloads already running on `pve3090`.

## Monitoring container

A new unprivileged Debian 13 LXC was created on `pve3080`:

- VMID: 200
- Hostname: `monitor01`
- 2 vCPU
- 4 GB RAM
- 512 MB swap
- 32 GB root filesystem on `local-lvm`
- `nesting=1`
- `keyctl=1`
- start at boot enabled
- DHCP with a router reservation
- reserved address: `192.168.1.238`

The container was updated before application deployment.

## Docker platform

Docker was installed from the official Docker repository for Debian Trixie.

Installed components include:

- Docker Engine
- Docker CLI
- containerd
- Docker Buildx
- Docker Compose plugin

The installation was validated with the `hello-world` container.

## Uptime Kuma

Uptime Kuma 2 was deployed with Docker Compose and persistent storage.

Service:

`http://192.168.1.238:3001`

Four ICMP monitors were created:

- `pve` - `192.168.1.164`
- `pve3090` - `192.168.1.165`
- `pve3080` - `192.168.1.166`
- `pve3080b` - `192.168.1.167`

All four hosts were online at the end of the session.

Uptime Kuma is used for simple availability monitoring: whether a host is reachable.

## Node Exporter

The Debian `prometheus-node-exporter` package was installed on all four Proxmox hosts.

Node Exporter exposes host-level Linux metrics such as:

- CPU
- memory
- filesystem
- load
- network counters

The exporter listens on TCP port `9100`.

Each endpoint was tested locally and from the monitoring container before adding it to Prometheus.

## Prometheus

Prometheus was deployed in Docker on `monitor01`.

Service:

`http://192.168.1.238:9090`

Scrape interval:

`15s`

Configured Node Exporter targets:

- `192.168.1.164:9100` -> instance label `pve`
- `192.168.1.165:9100` -> instance label `pve3090`
- `192.168.1.166:9100` -> instance label `pve3080`
- `192.168.1.167:9100` -> instance label `pve3080b`

The Prometheus configuration was validated with `promtool check config` before reload.

All targets reported `UP` after configuration.

## Grafana

Grafana was deployed alongside Prometheus in Docker.

Service:

`http://192.168.1.238:3000`

Prometheus was configured as the Grafana data source using the Docker service name:

`http://prometheus:9090`

The data-source test completed successfully.

## Dashboard

A dashboard named `Homelab Piotto - Monitoring` was created.

Current panels:

1. CPU Usage (%)
2. RAM Usage (%)
3. Disk Usage (%)
4. System Load (%)
5. Network Download (Mbps)
6. Network Upload (Mbps)
7. Host Status

The Host Status panel uses:

```promql
up{job="node_exporter"}
```

Value mappings:

- `1` -> `UP`
- `0` -> `DOWN`

The panel uses an Instant query because the requirement is to show the current state of each host.

## Example PromQL

### CPU usage

```promql
100 - (avg by (instance) (rate(node_cpu_seconds_total{job="node_exporter",mode="idle"}[5m])) * 100)
```

### RAM usage

```promql
100 * (1 - (node_memory_MemAvailable_bytes{job="node_exporter"} / node_memory_MemTotal_bytes{job="node_exporter"}))
```

### Root filesystem usage

```promql
100 * (1 - (node_filesystem_avail_bytes{job="node_exporter",mountpoint="/"} / node_filesystem_size_bytes{job="node_exporter",mountpoint="/"}))
```

### System load normalised by logical CPU count

```promql
100 * node_load1{job="node_exporter"} / on(instance) count by (instance) (node_cpu_seconds_total{job="node_exporter",mode="idle"})
```

### Physical NIC download

```promql
rate(node_network_receive_bytes_total{job="node_exporter",device="nic0"}[1m]) * 8 / 1000000
```

### Physical NIC upload

```promql
rate(node_network_transmit_bytes_total{job="node_exporter",device="nic0"}[1m]) * 8 / 1000000
```

Only the physical interface `nic0` is used for throughput panels to avoid double-counting traffic through Linux bridges, TAP devices and LXC veth interfaces.

## Network-drop investigation

While validating network metrics, a repeatable RX-drop pattern was observed.

The investigation included:

- Prometheus `rate()` and `increase()`
- `ethtool -S nic0`
- `ip -s link show nic0`
- `/proc/net/dev`
- sysfs network statistics
- a short `tcpdump` broadcast/multicast capture
- comparison between `nic0` and `vmbr0`

Findings:

- RX errors: 0
- TX errors: 0
- alignment errors: 0
- historical `rx_missed` counter was stable during observation
- current `nic0` RX drops increased slowly at approximately one event per minute
- `vmbr0` maintained a separate and much faster software-layer drop counter
- normal LAN, Internet, monitoring and host availability remained healthy

No evidence of an active physical cable or NIC failure was found, so no configuration or hardware change was made. The issue is documented for future troubleshooting only if user-visible symptoms appear.

This exercise was useful for learning the difference between:

- physical NIC errors
- driver counters
- Linux network counters
- bridge statistics
- Prometheus-exported metrics

## Monitoring architecture

```text
pve        ─┐
pve3090    ─┤
pve3080    ─┼── Node Exporter ──> Prometheus ──> Grafana
pve3080b   ─┘

All Proxmox hosts ─────────────────────────────> Uptime Kuma

monitor01
└── Docker
    ├── Uptime Kuma
    ├── Prometheus
    └── Grafana
```

## Skills practised

- LXC provisioning
- Debian administration
- Docker and Docker Compose
- Prometheus configuration
- PromQL
- Grafana dashboard design
- Node Exporter deployment
- service validation
- network troubleshooting
- infrastructure documentation

## Next steps

- configure Uptime Kuma notifications
- add useful monitoring alerts
- review backup strategy for `monitor01`
- consider version-pinning Docker images
- continue with DNS and infrastructure services
