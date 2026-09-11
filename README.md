# Homelab Learning

This repository documents my practical learning journey with Linux, networking, virtualization, containers, monitoring, troubleshooting and server administration.

## Lab Hardware

### PVE-01 - Lenovo ThinkCentre V520s

- Intel Core i5-7400
- 16 GB RAM
- 256 GB SSD
- Proxmox VE
- Primary homelab virtualization node
- Management address: `192.168.1.164:8006`

### PVE-02 - Dell OptiPlex 3090 Micro

- Proxmox VE
- Secondary virtualization and infrastructure lab node
- Hostname: `pve3090`
- Static management address: `192.168.1.165:8006`
- NVMe system storage connected through a Realtek RTL9210 bridge

## Technologies

- Proxmox VE
- Debian Linux
- LXC Containers
- Docker
- Docker Compose
- Portainer
- Uptime Kuma
- SSH / OpenSSH
- Linux administration
- Networking
- DHCP and static addressing
- Linux bridges
- EXT4 / LVM
- SMART / NVMe diagnostics
- Monitoring
- Infrastructure troubleshooting

## Current Architecture

```text
Home Network
├── PVE-01 - Lenovo ThinkCentre V520s
│   └── Proxmox VE - 192.168.1.164
│       └── LXC 100 - docker01
│           └── Debian 13 - 192.168.1.101
│               ├── SSH Server
│               └── Docker
│                   ├── Portainer
│                   │   └── portainer_data volume
│                   └── Uptime Kuma
│                       └── uptime-kuma-data volume
│
└── PVE-02 - Dell OptiPlex 3090 Micro
    └── Proxmox VE - 192.168.1.165
        └── Secondary virtualization / infrastructure node
```

## Network

> The addresses below are private RFC1918 LAN addresses. They are not publicly routable Internet addresses.

| Service / Node | Address / Port | Purpose |
| --- | --- | --- |
| PVE-01 - Lenovo V520s | `192.168.1.164:8006` | Primary Proxmox management |
| PVE-02 - OptiPlex 3090 | `192.168.1.165:8006` | Secondary Proxmox management |
| docker01 | `192.168.1.101` | Debian LXC Docker host |
| SSH - docker01 | `192.168.1.101:22` | Remote Linux administration |
| Portainer | `192.168.1.101:9443` | Docker web management |
| Uptime Kuma | `192.168.1.101:3001` | Service monitoring |

The `docker01` server uses DHCP with a router reservation so it keeps the address `192.168.1.101`.

The OptiPlex Proxmox node uses a static address configured directly on the Proxmox bridge `vmbr0`:

```text
address 192.168.1.165/24
gateway 192.168.1.254
bridge-ports eno2
```

## Proxmox Nodes

### PVE-01 - Lenovo V520s

This is the primary node and currently hosts `docker01`, the Debian LXC container used for Docker services and Linux administration practice.

### PVE-02 - Dell OptiPlex 3090

The second Proxmox node was added to expand the lab and provide another system for virtualization, networking and infrastructure troubleshooting.

During setup, the node experienced a storage/filesystem incident where EXT4 remounted the root filesystem read-only. The troubleshooting process included:

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

Full incident notes are available here:

- [PVE-02 / OptiPlex 3090 troubleshooting](docs/pve3090-troubleshooting.md)

## Docker Services

### Portainer

Portainer provides a graphical interface for managing Docker.

It is deployed using:

- Docker container
- HTTPS port `9443`
- Persistent Docker volume `portainer_data`
- Docker socket access for local Docker management

### Uptime Kuma

Uptime Kuma is deployed using Docker Compose through a Portainer Stack.

It uses:

- Docker image `louislam/uptime-kuma:2`
- Port `3001`
- Persistent volume `uptime-kuma-data`
- Automatic restart policy
- SQLite database

Current monitors include:

- Proxmox VE
- Portainer

## Remote Administration

The Debian LXC `docker01` can be administered remotely from Windows using SSH.

Basic connection:

```powershell
ssh cesar@192.168.1.101
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
apt full-upgrade -y
apt install
hostname -I
whoami
hostname
groups
usermod
sudo
systemctl status
lsblk -f
findmnt
smartctl
dmesg
cat /etc/network/interfaces
poweroff
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
```

### SSH and Windows network diagnostics

```text
ssh
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
- [x] Verified static Proxmox management IP on PVE-02
- [x] Diagnosed network reachability versus application availability
- [x] Investigated EXT4 read-only recovery on PVE-02
- [x] Checked NVMe SMART health and Linux kernel storage logs
- [x] Recovered PVE-02 web management access
- [x] Documented the PVE-02 troubleshooting process
- [ ] Configure Uptime Kuma notifications
- [ ] Create a homelab status page
- [ ] Deploy workloads on PVE-02
- [ ] Learn Docker networking in more depth
- [ ] Configure backups
- [ ] Improve homelab security
- [ ] Monitor PVE-02 for recurring storage / bridge errors
