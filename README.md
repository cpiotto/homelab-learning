# Homelab Learning

This repository documents my practical learning journey with Linux, networking, virtualization, containers, monitoring and server administration.

## Lab Hardware

- Lenovo ThinkCentre V520s
- Intel Core i5-7400
- 16 GB RAM
- 256 GB SSD

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
- DHCP
- Monitoring

## Current Architecture

```text
Lenovo ThinkCentre V520s
└── Proxmox VE
    └── LXC 100 - docker01
        └── Debian 13
            ├── SSH Server
            └── Docker
                ├── Portainer
                │   └── portainer_data volume
                │
                └── Uptime Kuma
                    └── uptime-kuma-data volume
```

## Network

> IP addresses shown in this documentation are examples representing the internal homelab network.

| Service | Address / Port | Purpose |
| --- | --- | --- |
| Proxmox VE | `192.168.1.164:8006` | Hypervisor management |
| docker01 | `192.168.1.101` | Debian LXC Docker host |
| SSH | `192.168.1.101:22` | Remote Linux administration |
| Portainer | `192.168.1.101:9443` | Docker web management |
| Uptime Kuma | `192.168.1.101:3001` | Service monitoring |

The `docker01` server uses DHCP with a router reservation so it keeps the address `192.168.1.101`.

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

Current monitors:

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

### Linux

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

### SSH

```bash
ssh
ssh-keygen
ssh-add
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
- Infrastructure documentation

## Current Progress

- [x] Installed Proxmox VE
- [x] Configured Proxmox no-subscription repository
- [x] Updated Proxmox
- [x] Upgraded homelab to 16 GB RAM
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
- [ ] Configure Uptime Kuma notifications
- [ ] Create a homelab status page
- [ ] Deploy additional Docker services
- [ ] Learn Docker networking in more depth
- [ ] Configure backups
- [ ] Improve homelab security
