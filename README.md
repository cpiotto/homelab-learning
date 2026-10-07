# Homelab Learning

This repository documents my practical learning journey with Linux, networking, virtualization, containers, monitoring, troubleshooting and server administration.

## Lab Hardware

### PVE-01 - Lenovo ThinkCentre V520s

- Intel Core i5-7400
- 16 GB RAM
- Proxmox VE 9.2.21
- Running kernel: `7.0.14-20-pve`
- Samsung SSD 830 256 GB SATA system disk
- Samsung PM991a 256 GB NVMe as `nvme-storage` for VMs/LXC
- Samsung MZ7LN256HCHP 256 GB SATA as `backup-storage`
- Virtualization and storage lab node
- Management address: `192.168.1.164:8006`

### PVE-02 - Dell OptiPlex 3090 Micro

- Intel Core i5-10500T
- 6 cores / 12 threads
- 16 GB RAM
- Proxmox VE 9.2.21
- Running kernel: `7.0.14-20-pve`
- Secondary virtualization and infrastructure lab node
- Hostname: `pve3090`
- Static management address: `192.168.1.165:8006`
- Samsung SSD 840 Series 120 GB SATA system disk
- NVMe/Kioxia storage detection retained as a future troubleshooting task

### PVE-03 - Dell OptiPlex 3080 Micro

- Intel Core i5-10500T
- 6 cores / 12 threads
- 16 GB DDR4-2666 RAM (2 x 8 GB)
- Proxmox VE 9.2.21
- Running kernel: `7.0.14-20-pve`
- Samsung MZ7LN256HCHP 256 GB SATA system disk
- Hostname: `pve3080`
- FQDN: `pve3080.home.arpa`
- Static management address: `192.168.1.166:8006`
- Realtek Gigabit Ethernet at 1 Gb/s full duplex
- Infrastructure / monitoring node
- Hosts LXC 200 `monitor01` for Prometheus, Grafana and Uptime Kuma
- Hosts LXC 201 `dns01` for BIND9 internal DNS

### Additional node - Dell OptiPlex 3080 Micro (`pve3080b`)

- Intel Core i5-10500T
- 8 GB DDR4-2666 RAM
- Proxmox VE 9.2.21
- Running kernel: `7.0.14-20-pve`
- SATA SSD system disk
- Hostname: `pve3080b`
- Static management address: `192.168.1.167:8006`
- Baseline audit completed on 6 October 2026
- Clean node reserved for testing, security and automation workloads

### Network switch

- TP-Link 8-port Ethernet switch
- Used as the central wired connection point for the homelab nodes
- Port 1: uplink to the wall/network connection
- Port 2: Dell OptiPlex 3090 (`pve3090`)
- Port 3: Lenovo ThinkCentre V520s (`pve`)
- Port 4: Dell OptiPlex 3080
- Remaining ports reserved for additional homelab devices

## Technologies

- Proxmox VE
- Debian Linux
- Ubuntu Server
- Virtual machines
- LXC Containers
- Docker
- Docker Compose
- Portainer
- Uptime Kuma
- Prometheus
- PromQL
- Grafana
- Node Exporter
- SSH / OpenSSH
- QEMU Guest Agent
- Linux administration
- Networking
- DHCP and DHCP reservations
- Static addressing
- Linux bridges
- Routing and default gateways
- DNS troubleshooting
- BIND9
- Authoritative and recursive DNS
- Forward and reverse DNS zones
- DNS A and PTR records
- `dig` / `nslookup`
- EXT4 / LVM
- SMART / NVMe diagnostics
- SATA / NVMe storage troubleshooting
- APT repository management
- Monitoring
- Infrastructure troubleshooting

## Current Architecture

```text
Home Network
├── PVE-01 - Lenovo ThinkCentre V520s
│   └── Proxmox VE 9.2.21 - 192.168.1.164
│       ├── Samsung SSD 830 256 GB SATA - Proxmox system disk
│       ├── nvme-storage - Samsung PM991a 256 GB NVMe
│       │   └── LVM-thin storage for new VMs/LXC
│       ├── backup-storage - Samsung MZ7LN256HCHP 256 GB SATA
│       │   └── EXT4 mounted at /mnt/pve-backup
│       └── docker01 - old LXC removed; monitoring rebuilt separately on pve3080
│
├── PVE-02 - Dell OptiPlex 3090 Micro
│   └── Proxmox VE 9.2.21 - 192.168.1.165
│       ├── Samsung SSD 840 Series 120 GB SATA system disk
│       ├── VM 100 - ubuntu-server
│       │   └── Ubuntu Server - 192.168.1.106
│       │       ├── 2 vCPU / 2 GB RAM / 20 GiB disk
│       │       ├── QEMU Guest Agent
│       │       └── Start at boot
│       ├── VM 101 - ubuntu-server-01
│       │   └── Ubuntu Server - 192.168.1.111
│       │       ├── 2 vCPU / 2 GB RAM / 32 GiB disk
│       │       ├── QEMU Guest Agent
│       │       └── Start at boot
│       └── lenovo-backup - NFS 4.2 remote backup storage
│           └── 192.168.1.164:/mnt/pve-backup
│
├── PVE-03 - Dell OptiPlex 3080 Micro
│   └── pve3080 - Proxmox VE 9.2.21 - 192.168.1.166
│       ├── Samsung MZ7LN256HCHP 256 GB SATA system disk
│       ├── local + local-lvm storage
│       ├── LXC 200 - monitor01 - 192.168.1.238
│       │   ├── Debian 13
│       │   ├── Docker + Docker Compose
│       │   ├── Uptime Kuma - port 3001
│       │   ├── Grafana - port 3000
│       │   └── Prometheus - port 9090
│       └── LXC 201 - dns01 - 192.168.1.195
│           ├── Debian 13
│           ├── BIND9 - port 53
│           └── Node Exporter - port 9100
│
└── Additional node - Dell OptiPlex 3080 Micro
    └── pve3080b - Proxmox VE 9.2.21 - 192.168.1.167
        └── Clean node reserved for testing, security and automation
```

## Network

> The addresses below are private RFC1918 LAN addresses. They are not publicly routable Internet addresses.

### Physical topology

A TP-Link 8-port Ethernet switch was added as the central wired connection point for the homelab. This makes the physical layout easier to expand and keeps the Proxmox nodes on the same LAN segment.

| Switch port | Connection |
| --- | --- |
| 1 | Uplink to wall / home network |
| 2 | Dell OptiPlex 3090 - `pve3090` |
| 3 | Lenovo ThinkCentre V520s - `pve` |
| 4 | Dell OptiPlex 3080 - `pve3080` |
| 5-8 | Available for future homelab devices |

The switch is currently unmanaged, so VLANs, port isolation and other Layer 2 features are not configured on the switch itself.

| Service / Node | Address / Port | Purpose |
| --- | --- | --- |
| PVE-01 - Lenovo V520s | `192.168.1.164:8006` | Primary Proxmox management |
| PVE-02 - OptiPlex 3090 | `192.168.1.165:8006` | Secondary Proxmox management |
| PVE-03 - OptiPlex 3080 | `192.168.1.166:8006` | Infrastructure / learning Proxmox node |
| pve3080b - OptiPlex 3080 | `192.168.1.167:8006` | Additional Proxmox management |
| ubuntu-server | `192.168.1.106` | Ubuntu Server VM 100 on PVE-02 |
| ubuntu-server-01 | `192.168.1.111` | Ubuntu Server VM 101 on PVE-02 |
| monitor01 | `192.168.1.238` | Debian 13 monitoring LXC on PVE-03 |
| Grafana | `192.168.1.238:3000` | Monitoring dashboard |
| Uptime Kuma | `192.168.1.238:3001` | Availability monitoring |
| Prometheus | `192.168.1.238:9090` | Metrics collection and time-series database |
| dns01 | `192.168.1.195:53` | BIND9 internal DNS |
| SSH - ubuntu-server | `192.168.1.106:22` | Remote Ubuntu administration |

The previous `docker01` LXC used a router DHCP reservation at `192.168.1.101`. Its old storage was removed on 23 September 2026 and a clean rebuild is planned.

The `ubuntu-server` VM also uses DHCP with a router reservation. The router maps MAC address `BC:24:11:47:01:A7` to `192.168.1.106`, so the guest keeps a predictable address while Netplan remains DHCP-based.

The Proxmox nodes currently use the LAN gateway at `192.168.1.254`. A dedicated internal DNS server, `dns01` at `192.168.1.195`, is now being tested on selected clients before any router-wide DNS change.

The OptiPlex Proxmox node uses a static address configured directly on the Proxmox bridge `vmbr0`:

```text
address 192.168.1.165/24
gateway 192.168.1.254
bridge-ports nic0
```

The physical interface `nic0` is attached to `vmbr0`. The bridge carries the Proxmox management address and also provides LAN access to VM 100 through its VirtIO network adapter.

## Proxmox Nodes

### PVE-01 - Lenovo V520s

On 23 September 2026 the Lenovo storage layout was reorganised. The existing Samsung SSD 830 SATA disk remains the Proxmox system disk. A Samsung PM991a 256 GB NVMe was repurposed as `nvme-storage` for new VMs and LXC containers, and a Samsung MZ7LN256HCHP 256 GB SATA SSD was configured as EXT4 `backup-storage` mounted at `/mnt/pve-backup`.

The backup SSD passed its extended SMART self-test, but its approximately 66,065 power-on hours were documented as a limitation, so it is treated as secondary lab storage rather than the sole copy of important data.

The old LXC 100 / `docker01` workload was stopped and its orphaned `local-lvm:vm-100-disk-0` volume was removed. A clean rebuild of `docker01` is planned.

The node uses the Proxmox `pve-no-subscription` repository and was updated to Proxmox VE 9.2.20 with kernel `7.0.14-17-pve` on 15 September 2026.

On 1 October 2026, `backup-storage` was also exported over NFS specifically to `pve3090` at `192.168.1.165`. The export is used as an off-host secondary backup target for the Ubuntu VMs on PVE-02.

### PVE-02 - Dell OptiPlex 3090

The second Proxmox node was added to expand the lab and provide another system for virtualization, networking and infrastructure troubleshooting.

During the initial setup, the node experienced a storage/filesystem incident where EXT4 remounted the root filesystem read-only. The troubleshooting process included:

- ICMP connectivity testing
- TCP port testing with `Test-NetConnection`
- SSH verbose diagnostics
- Direct HTTPS testing with `curl`
- Local console investigation
- LVM / EXT4 filesystem identification
- SMART/NVMe health checks
- Kernel log analysis with `dmesg`
- NVMe bridge/cable troubleshooting
- Static Proxmox network verification

A later storage session tested a Samsung SATA SSD and a Kioxia NVMe device. Linux successfully detected and booted Proxmox from the Samsung SSD 840 Series SATA drive, while the Kioxia NVMe device was not detected. BIOS and boot settings were investigated, including the observed `RAID On` storage mode. The working SATA configuration was kept as the known-good system disk rather than risking the stable installation with unnecessary controller-mode changes.

On 15 September 2026, the node was used for a practical networking and maintenance session. The LAN connection between PVE-01 and PVE-02 was verified with ICMP and SSH. A wrong default gateway (`192.168.1.1`) and DNS resolver (`192.168.1.1`) were identified on PVE-02 by comparing its configuration with the working Lenovo node. Both were corrected to `192.168.1.254`. Internet access, DNS resolution and APT were then validated independently.

The Enterprise PVE and unused Ceph Enterprise repositories were disabled on PVE-02, the `pve-no-subscription` repository was configured, and a simulated full upgrade was reviewed before applying updates. On 1 October 2026, the node was updated again to Proxmox VE 9.2.21 with kernel `7.0.14-20-pve`.

Later the same day, PVE-02 received its first full virtual machine: `VM 100 - ubuntu-server`. Ubuntu Server 24.04.5 LTS was installed with 2 vCPU, 2 GB RAM and a 20 GiB virtual disk on `local-lvm`. Its VirtIO network adapter is attached to `vmbr0`, giving the guest direct access to the home LAN at reserved address `192.168.1.106`. OpenSSH and the QEMU Guest Agent were enabled and tested, the VM was configured to start automatically with the host, and a reboot test confirmed that networking, SSH and guest-agent integration return correctly.

PVE-02 now also runs `VM 101 - ubuntu-server-01` with 2 vCPU, 2 GB RAM, a 32 GiB virtual disk, QEMU Guest Agent integration and address `192.168.1.111`. Both VMs are configured to start automatically.

On 1 October 2026, PVE-02 received a full maintenance audit. The Samsung SSD 840 Series 120 GB system disk passed SMART health and self-test checks, CPU temperatures were approximately 28-32°C, the host had about 11 GiB RAM available, and a high guest RX-drop counter was investigated across the physical NIC, TAP, VirtIO and Linux protocol layers. No meaningful packet loss was found.

The Lenovo `backup-storage` disk was then added to PVE-02 as NFS storage named `lenovo-backup`. Manual snapshot backups of VM 100 and VM 101 completed successfully and both archives passed `zstd -t` integrity tests. A daily 03:00 Proxmox backup job now protects both VMs using Zstandard compression, `keep-last=7` retention and repeat-missed scheduling.

Full troubleshooting and maintenance notes are available here:

- [PVE-02 / OptiPlex 3090 troubleshooting](docs/pve3090-troubleshooting.md)
- [PVE-02 storage troubleshooting - 14 September 2026](docs/pve3090-storage-troubleshooting-2026-09-14.md)
- [Network and Proxmox maintenance - 15 September 2026](docs/network-maintenance-2026-09-15.md)
- [First Ubuntu Server VM on PVE-02 - 15 September 2026](docs/first-vm-ubuntu-server-2026-09-15.md)
- [Lenovo V520s storage upgrade and cleanup - 23 September 2026](docs/lenovo-storage-upgrade-2026-09-23.md)
- [Homelab maintenance and automated backups - 1 October 2026](docs/homelab-maintenance-2026-10-01.md)
- [PVE-03 / OptiPlex 3080 baseline audit - 3 October 2026](docs/pve3080-audit-2026-10-03.md)
- [PVE-04 / OptiPlex 3080 baseline audit - 6 October 2026](docs/pve3080b-audit-2026-10-06.md)
- [Central homelab monitoring stack - 6 October 2026](docs/monitoring-stack-2026-10-06.md)
- [Internal DNS infrastructure - 7 October 2026](docs/dns-infrastructure-2026-10-07.md)

### PVE-03 - Dell OptiPlex 3080

On 3 October 2026, `pve3080` received a full baseline audit before deploying any workloads. The node was upgraded from Proxmox VE 9.2.20 / kernel `7.0.14-19-pve` to Proxmox VE 9.2.21 / kernel `7.0.14-20-pve`, then rebooted and verified.

The audit covered CPU topology and temperatures, memory and swap, LVM and Proxmox storage, SSD SMART health, filesystem capacity and inodes, networking, DNS, link negotiation, hostname/FQDN resolution, NTP, Proxmox services, current-boot logs, cluster state, firewall state, scheduled jobs, PCI devices and USB devices.

The Realtek Ethernet interface was confirmed at 1 Gb/s full duplex, with `vmbr0` providing the static management address `192.168.1.166/24` and gateway `192.168.1.254`. Internet connectivity and DNS resolution were validated independently.

A stale `iface nic1 inet manual` entry was also identified in `/etc/network/interfaces`. The nonexistent interface was checked for dependencies, the network configuration was backed up, the unused line was removed, and the change was verified with `diff -u`.

On 6 October 2026, `pve3080` received its first infrastructure workload: unprivileged LXC 200 `monitor01`. The Debian 13 container runs Docker and Docker Compose with Uptime Kuma, Prometheus and Grafana. Node Exporter was installed on all four Proxmox hosts, allowing Prometheus to collect host metrics and Grafana to display CPU, RAM, disk, load, physical NIC traffic and current host status.

The monitoring container uses a router-reserved address at `192.168.1.238` and starts automatically with the host.

On 7 October 2026, `pve3080` also received LXC 201 `dns01`, a dedicated Debian 13 BIND9 server at `192.168.1.195`. It is authoritative for the internal `home.arpa` zone, provides reverse DNS for the homelab IPv4 subnet, resolves external Internet names, and is monitored through Node Exporter, Prometheus, Grafana and Uptime Kuma.

The DNS service was validated from Proxmox and Windows clients before any router-wide DNS change. Internal service names such as `grafana.home.arpa` now resolve successfully.

Full notes:

- [PVE-03 / OptiPlex 3080 baseline audit - 3 October 2026](docs/pve3080-audit-2026-10-03.md)
- [Central homelab monitoring stack - 6 October 2026](docs/monitoring-stack-2026-10-06.md)
- [Internal DNS infrastructure - 7 October 2026](docs/dns-infrastructure-2026-10-07.md)

### PVE-04 - Dell OptiPlex 3080 (`pve3080b`)

On 6 October 2026, `pve3080b` received a full baseline audit. The node was verified on Proxmox VE 9.2.21 / kernel `7.0.14-20-pve`, with an Intel Core i5-10500T, 8 GB DDR4-2666 RAM and a 256 GB SATA SSD.

The audit covered CPU and temperatures, memory, storage, SMART, networking, DNS, NTP, Proxmox services, logs, firewall state, scheduled jobs and firmware information. The node was healthy enough for continued lab use and remains intentionally clean for future testing, security and automation work.

Full audit notes:

- [PVE-04 / OptiPlex 3080 baseline audit - 6 October 2026](docs/pve3080b-audit-2026-10-06.md)

## Monitoring Services

Monitoring services are now hosted in Debian 13 LXC 200 `monitor01` on `pve3080`.

### Uptime Kuma

Uptime Kuma 2 runs in Docker Compose with persistent storage and automatic restart.

It monitors the availability of all four Proxmox hosts plus `dns01`.

A dedicated DNS monitor also queries `pve.home.arpa` through `dns01` and verifies that the returned A record is `192.168.1.164`. This validates the DNS service itself rather than only host reachability.

### Prometheus

Prometheus runs in Docker and scrapes Node Exporter on all four Proxmox hosts plus `dns01` every 15 seconds.

It stores the time-series data used by Grafana.

### Grafana

Grafana runs in Docker and uses Prometheus as its data source.

The `Homelab Piotto - Monitoring` dashboard currently shows:

- CPU usage
- RAM usage
- root filesystem usage
- normalised system load
- physical NIC download
- physical NIC upload
- current host UP/DOWN state

### Portainer

Portainer was used in the earlier `docker01` environment. It has not yet been redeployed in `monitor01`.

## Internal DNS

Internal DNS is provided by BIND9 in LXC 201 `dns01` on `pve3080`.

- DNS server: `192.168.1.195`
- internal zone: `home.arpa`
- reverse zone: `1.168.192.in-addr.arpa`
- authoritative records for homelab hosts and services
- recursive resolution for Internet names
- A and PTR records
- monitored by Prometheus/Grafana and Uptime Kuma
- tested from a Windows client over IPv4 and IPv6

Examples:

```text
pve.home.arpa       -> 192.168.1.164
pve3090.home.arpa   -> 192.168.1.165
grafana.home.arpa   -> 192.168.1.238
dns01.home.arpa     -> 192.168.1.195
```

The service is currently being validated on selected clients before any network-wide DNS distribution through the router.

## Remote Administration

The previous Debian LXC `docker01` was administered remotely from Windows using SSH. It is currently offline after the 23 September 2026 cleanup and will be configured again when rebuilt.

The Ubuntu VM on PVE-02 can be administered from other LAN systems, including PVE-01:

```bash
ssh cesar@192.168.1.106
```

A normal Linux user was created instead of using `root` for daily administration.

Administrative commands can be executed using:

```bash
sudo
```

Example:

```bash
sudo whoami
```

Expected result:

```text
root
```

The Proxmox nodes can also be administered over SSH for infrastructure maintenance. During the 15 September networking session, PVE-01 was used to connect directly to PVE-02:

```bash
ssh root@192.168.1.165
```

## SSH Key Authentication

An Ed25519 SSH key pair was created on Windows.

```powershell
ssh-keygen -t ed25519 -C "cesar-homelab"
```

The private key remains on the Windows computer:

```text
C:\Users\cesar\.ssh\id_ed25519
```

The public key:

```text
C:\Users\cesar\.ssh\id_ed25519.pub
```

was added to the Debian server:

```text
/home/cesar/.ssh/authorized_keys
```

The Windows OpenSSH Authentication Agent (`ssh-agent`) was also enabled so the key can be unlocked once and reused for SSH sessions.

Useful commands:

```powershell
Get-Service ssh-agent
Start-Service ssh-agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519
ssh-add -l
ssh cesar@192.168.1.101
```

> The private SSH key, passwords and passphrases must never be stored in this repository.

## Commands Learned

### Linux / Proxmox

```bash
apt update
apt -s full-upgrade
apt full-upgrade
apt install
hostname -I
whoami
hostname
uptime
free -h
lscpu
groups
usermod
sudo
systemctl status
systemctl is-active
lsblk -f
lsblk -o NAME,SIZE,MODEL,TRAN
findmnt
smartctl
dmesg
pvesm status
pveversion
uname -r
qm status
qm config
qm reset
qm reboot
qm agent
qm guest cmd
cat /etc/pve/storage.cfg
cat /etc/network/interfaces
cat /etc/resolv.conf
ip -br addr
ip route
ip neigh
bridge link
ping -c 4
poweroff
reboot
sensors
dmidecode -t memory
dmidecode -t 16
ethtool nic0
timedatectl
systemctl --failed
journalctl -p 3 -b --no-pager
journalctl --disk-usage
df -h
df -i
pvecm status
pve-firewall status
systemctl list-timers --all
crontab -l
lspci
lsusb
diff -u
```

### Docker

```bash
docker ps
docker ps -a
docker images
docker version
docker logs
docker volume create
docker volume ls
docker restart
docker compose version
docker compose config
docker compose up -d
docker exec
docker kill --signal HUP
```

### Monitoring / networking

```bash
promtool check config
ethtool -S nic0
ip -s link show nic0
cat /proc/net/dev
tcpdump
```

### SSH and Windows network diagnostics

```text
ssh
ssh -vvv
ssh-keygen
ssh-add
ping
arp -a
Test-NetConnection
curl.exe
```

## Learning Goals

The goal of this homelab is to develop practical skills in:

- Linux administration
- Networking
- Virtualization
- Docker and containers
- Docker Compose
- Monitoring
- Troubleshooting
- Cybersecurity
- Remote server administration
- Storage diagnostics
- Infrastructure documentation

## Current Progress

- [x] Installed Proxmox VE on the Lenovo V520s
- [x] Configured Proxmox no-subscription repository
- [x] Updated Proxmox
- [x] Upgraded Lenovo homelab node to 16 GB RAM
- [x] Created Debian 13 LXC container
- [x] Configured networking with DHCP
- [x] Reserved a fixed DHCP address for docker01
- [x] Configured docker01 to start automatically
- [x] Installed Docker repository
- [x] Installed Docker Engine
- [x] Verified Docker service
- [x] Ran first Docker container (`hello-world`)
- [x] Learned Docker images, containers and logs
- [x] Created first persistent Docker volume
- [x] Installed and configured Portainer
- [x] Managed containers through Portainer
- [x] Learned Docker Compose basics
- [x] Learned YAML basics
- [x] Created first Portainer Stack
- [x] Deployed Uptime Kuma
- [x] Created persistent storage for Uptime Kuma
- [x] Monitored Proxmox VE with Uptime Kuma
- [x] Monitored Portainer with Uptime Kuma
- [x] Verified SSH server on docker01
- [x] Created a non-root Linux user
- [x] Configured sudo administrative access
- [x] Connected to docker01 using SSH from Windows
- [x] Created an Ed25519 SSH key pair
- [x] Configured SSH public-key authentication
- [x] Configured Windows ssh-agent
- [x] Added a second Proxmox node using a Dell OptiPlex 3090
- [x] Added a TP-Link 8-port Ethernet switch as the central wired homelab connection point
- [x] Verified static Proxmox management IP on PVE-02
- [x] Diagnosed network reachability versus application availability
- [x] Investigated EXT4 read-only recovery on PVE-02
- [x] Checked NVMe SMART health and Linux kernel storage logs
- [x] Recovered PVE-02 web management access
- [x] Documented the PVE-02 troubleshooting process
- [x] Tested Samsung SATA storage as the PVE-02 system disk
- [x] Used `lsblk` to verify the physical disk and Proxmox LVM layout
- [x] Investigated an undetected Kioxia NVMe device
- [x] Compared Linux storage detection with Dell BIOS/boot behaviour
- [x] Returned PVE-02 to stable headless operation on SATA storage
- [x] Verified ICMP connectivity in both directions between PVE-01 and PVE-02
- [x] Administered PVE-02 remotely from PVE-01 using SSH
- [x] Inspected `vmbr0`, `nic0`, routing and neighbour tables
- [x] Diagnosed and corrected the PVE-02 default gateway
- [x] Diagnosed and corrected PVE-02 DNS resolution
- [x] Configured the Proxmox no-subscription repository on PVE-02
- [x] Disabled unused Enterprise / Ceph Enterprise repositories on PVE-02
- [x] Practised safe upgrade simulation with `apt -s full-upgrade`
- [x] Updated PVE-01 and PVE-02 to Proxmox VE 9.2.20
- [x] Updated PVE-01 and PVE-02 to kernel `7.0.14-17-pve`
- [x] Updated PVE-02 to Proxmox VE 9.2.21 and kernel `7.0.14-20-pve`
- [x] Deployed the first workload on PVE-02
- [x] Created VM 100 `ubuntu-server` on PVE-02 and connected it through `vmbr0`
- [x] Installed Ubuntu Server 24.04.5 LTS on VM 100
- [x] Configured and tested SSH on the Ubuntu VM
- [x] Installed and tested QEMU Guest Agent
- [x] Reserved `192.168.1.106` for the Ubuntu VM using DHCP reservation
- [x] Configured VM 100 to start automatically with PVE-02
- [x] Reboot-tested VM 100 and verified IP, SSH and QEMU Guest Agent recovery
- [x] Added VM 101 `ubuntu-server-01` on PVE-02
- [x] Audited PVE-02 CPU, RAM, network and Samsung SSD 840 health
- [x] Installed Proxmox VE 9.2.21 on `pve3080b` at `192.168.1.167`
- [x] Exported Lenovo `backup-storage` to PVE-02 over NFS
- [x] Added `lenovo-backup` as Proxmox NFS storage on PVE-02
- [x] Validated VM 100 and VM 101 backups with `zstd -t`
- [x] Configured daily 03:00 automated backups for VM 100 and VM 101 with `keep-last=7`
- [x] Updated `pve3080` to Proxmox VE 9.2.21 and kernel `7.0.14-20-pve`
- [x] Completed a full baseline audit of `pve3080` before deploying workloads
- [x] Verified `pve3080` Ethernet at 1 Gb/s full duplex and validated gateway, Internet and DNS
- [x] Audited `pve3080` CPU, temperatures, RAM, swap, SSD SMART, LVM, filesystems and inodes
- [x] Verified `pve3080` hostname/FQDN, NTP and core Proxmox services
- [x] Removed the stale `nic1` network entry using backup, dependency search and diff verification
- [x] Completed a full baseline audit of `pve3080b`
- [x] Deployed the first infrastructure learning workload on `pve3080`
- [x] Created Debian 13 LXC 200 `monitor01`
- [x] Installed Docker and Docker Compose in `monitor01`
- [x] Deployed Uptime Kuma in `monitor01`
- [x] Installed Node Exporter on all four Proxmox hosts
- [x] Deployed Prometheus and configured all four Proxmox scrape targets
- [x] Deployed Grafana and connected the Prometheus data source
- [x] Built the `Homelab Piotto - Monitoring` dashboard
- [x] Added CPU, RAM, disk, load, download, upload and host-status panels
- [x] Investigated Linux NIC/bridge RX-drop counters without making unnecessary changes
- [x] Created Debian 13 LXC 201 `dns01`
- [x] Reserved `192.168.1.195` for `dns01`
- [x] Installed and configured BIND9
- [x] Created authoritative `home.arpa` forward zone
- [x] Created reverse DNS zone with PTR records
- [x] Validated BIND configuration with `named-checkzone` and `named-checkconf`
- [x] Verified internal and external DNS resolution with `dig`
- [x] Verified DNS resolution from Windows with `nslookup`
- [x] Accessed Grafana through `grafana.home.arpa`
- [x] Added `dns01` to Node Exporter, Prometheus and Grafana
- [x] Added Uptime Kuma Ping and DNS service monitors for `dns01`
- [ ] Decide on router-wide DNS rollout after client stability testing
- [ ] Configure Uptime Kuma notifications
- [ ] Create a homelab status page
- [ ] Learn Docker networking in more depth
- [ ] Improve homelab security
- [ ] Revisit NVMe support on PVE-02 using a safe test path
- [ ] Monitor PVE-02 storage health
