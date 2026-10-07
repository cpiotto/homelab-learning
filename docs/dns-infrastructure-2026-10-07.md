# Internal DNS infrastructure - 7 October 2026

## Goal

Deploy a dedicated internal DNS service for the homelab so hosts and services can be reached by predictable names instead of relying only on IP addresses.

The service was deliberately tested on individual clients before considering any router-wide DNS change.

## DNS container

A new unprivileged Debian 13 LXC was created on `pve3080`:

- VMID: 201
- Hostname: `dns01`
- 1 vCPU
- 1 GB RAM
- 512 MB swap
- 8 GB root filesystem on `local-lvm`
- start at boot enabled
- DHCP with a router reservation
- reserved IPv4 address: `192.168.1.195`

The container was upgraded from the original Debian 13.6 template packages to the current Debian 13.7 repository state before DNS configuration.

## BIND9

Installed packages:

- `bind9`
- `bind9-utils`
- `dnsutils`

The BIND service runs as `named.service`.

Before changing the configuration, `/etc/bind` was backed up.

## Forward zone

The internal zone is:

`home.arpa`

This namespace is reserved for home networks and avoids conflicts with public DNS names and mDNS conventions.

The server is authoritative for the zone.

Current A records include:

| Name | IPv4 |
| --- | --- |
| `pve.home.arpa` | `192.168.1.164` |
| `pve3090.home.arpa` | `192.168.1.165` |
| `pve3080.home.arpa` | `192.168.1.166` |
| `pve3080b.home.arpa` | `192.168.1.167` |
| `dns01.home.arpa` | `192.168.1.195` |
| `monitor01.home.arpa` | `192.168.1.238` |
| `grafana.home.arpa` | `192.168.1.238` |
| `kuma.home.arpa` | `192.168.1.238` |
| `prometheus.home.arpa` | `192.168.1.238` |

The zone uses a short 300-second TTL while the environment is still being developed.

## Reverse DNS

A reverse zone was also created:

`1.168.192.in-addr.arpa`

PTR records were created for the main homelab hosts and infrastructure containers, allowing tests such as:

`192.168.1.165 -> pve3090.home.arpa`

## Validation

Configuration was validated before reload using:

```bash
named-checkzone home.arpa /etc/bind/db.home.arpa
named-checkzone 1.168.192.in-addr.arpa /etc/bind/db.192.168.1
named-checkconf
```

The BIND service was then reloaded without a full restart.

### Internal resolution

A direct query from another Proxmox host confirmed:

```text
pve3090.home.arpa -> 192.168.1.165
```

The response carried the authoritative-answer flag because `dns01` is authoritative for `home.arpa`.

### External resolution

Queries such as `google.com` also succeeded through `dns01`, confirming that the server can resolve Internet names as well as its local authoritative zone.

### Reverse lookup

A reverse query confirmed:

```text
192.168.1.165 -> pve3090.home.arpa
```

## Windows client test

A Windows desktop was used as a real client.

First, `nslookup` was pointed directly at `192.168.1.195` and successfully resolved `pve.home.arpa`.

The Wi-Fi adapter was then configured to use `dns01` as its DNS server. During testing, Windows initially preferred the router-provided IPv6 DNS server, so dual-stack DNS behaviour was investigated.

BIND was confirmed to answer correctly over both IPv4 and IPv6. The desktop was then configured to use `dns01` for both address families.

Final tests succeeded without manually specifying the DNS server:

- `pve.home.arpa` resolved to `192.168.1.164`
- `google.com` returned public IPv4 and IPv6 records
- `http://grafana.home.arpa:3000` reached the Grafana login page

This confirmed that internal service names now work in normal client use.

The DNS change has not yet been distributed to the entire home network through the router. The desktop is being used as the controlled test client first.

## Monitoring integration

`prometheus-node-exporter` was installed in `dns01`.

Prometheus was updated with a new Node Exporter target:

`192.168.1.195:9100`

with instance label:

`dns01`

The configuration was backed up and validated with `promtool check config` before Prometheus was reloaded with SIGHUP.

The Prometheus `up` metric returned `1` for `dns01`.

Grafana automatically began displaying `dns01` in host-level panels such as:

- CPU
- RAM
- disk
- load
- host status

Network panels currently filter on physical host interface `nic0`, so the LXC `eth0` interface is intentionally not included in those existing panels.

## Uptime Kuma

Two monitors were created:

### Host reachability

- name: `dns01`
- type: Ping
- target: `192.168.1.195`
- interval: 60 seconds
- retries: 2

### DNS service validation

- name: `DNS home.arpa`
- type: DNS
- resolver: `192.168.1.195`
- port: 53
- query: `pve.home.arpa`
- record type: A
- expected record: `192.168.1.164`
- interval: 60 seconds
- retries: 2

This second monitor checks the actual DNS service and expected answer rather than only verifying that the host responds to ICMP.

## Architecture after this session

```text
Home LAN
   |
   +-- pve
   +-- pve3090
   +-- pve3080
   |    |
   |    +-- LXC 200 monitor01
   |    |    +-- Prometheus
   |    |    +-- Grafana
   |    |    +-- Uptime Kuma
   |    |
   |    +-- LXC 201 dns01
   |         +-- BIND9
   |         +-- Node Exporter
   |
   +-- pve3080b
```

## Skills practised

- DNS architecture
- authoritative DNS
- recursive resolution
- BIND9 administration
- forward zones
- reverse zones
- A records
- PTR records
- SOA and NS records
- TTLs
- `dig`
- `nslookup`
- configuration validation
- IPv4 and IPv6 DNS behaviour
- client DNS configuration
- monitoring a DNS service
- safe staged infrastructure rollout

## Next steps

- observe the desktop using `dns01` before changing router-wide DNS
- decide on the long-term IPv6 DNS strategy
- add or refine service records as the homelab grows
- later combine DNS with a reverse proxy and HTTPS
- continue toward Ansible and infrastructure automation
