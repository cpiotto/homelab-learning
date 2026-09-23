# Homelab Learning

This repository documents my practical learning journey with Linux, networking, virtualization, containers, monitoring, troubleshooting and server administration.

## Lab Hardware

### PVE-01 - Lenovo ThinkCentre V520s

- Intel Core i5-7400
- 16 GB RAM
- Proxmox VE 9.2.20
- Running kernel: `7.0.14-17-pve`
- Samsung SSD 830 256 GB SATA system disk
- Samsung PM991a 256 GB NVMe as `nvme-storage` for VMs/LXC
- Samsung MZ7LN256HCHP 256 GB SATA as `backup-storage`
- Virtualization and storage lab node
- Management address: `192.168.1.164:8006`

### PVE-02 - Dell OptiPlex 3090 Micro

- Intel Core i5-10500T
- 6 cores / 12 threads
- 16 GB RAM
- Proxmox VE 9.2.20
- Running kernel: `7.0.14-17-pve`
- Secondary virtualization and infrastructure lab node
- Hostname: `pve3090`
- Static management address: `192.168.1.165:8006`
- Samsung SSD 840 Series 120 GB SATA system disk
- NVMe/Kioxia storage detection retained as a future troubleshooting task

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
- SSH / OpenSSH
- QEMU Guest Agent
- Linux administration
- Networking
- DHCP and DHCP reservations
- Static addressing
- Linux bridges
- Routing and default gateways
- DNS troubleshooting
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
│   └── Proxmox VE 9.2.20 - 192.168.1.164
│       ├── Samsung SSD 830 256 GB SATA - Proxmox system disk
│       ├── nvme-storage - Samsung PM991a 256 GB NVMe
│       │   └── LVM-thin storage for new VMs/LXC
│       ├── backup-storage - Samsung MZ7LN256HCHP 256 GB SATA
│       │   └── EXT4 mounted at /mnt/pve-backup
│       └── docker01 - old LXC removed; clean rebuild planned
│
└── PVE-02 - Dell OptiPlex 3090 Micro
    └── Proxmox VE 9.2.20 - 192.168.1.165
        ├── Samsung SSD 840 Series SATA system disk
        └── VM 100 - ubuntu-server
            └── Ubuntu Server 24.04.5 LTS - 192.168.1.106
                ├── 2 vCPU / 2 GB RAM / 20 GiB disk
                ├── SSH Server
                ├── QEMU Guest Agent
                └── DHCP reservation + Start at boot
```

## Network

> The addresses below are private RFC1918 LAN addresses. They are not publicly routable Internet addresses.

| Service / Node | Address / Port | Purpose |
| --- | --- | --- |
| PVE-01 - Lenovo V520s | `192.168.1.164:8006` | Primary Proxmox management |
| PVE-02 - OptiPlex 3090 | `192.168.1.165:8006` | Secondary Proxmox management |
| docker01 | `192.168.1.101` | Debian LXC Docker host |
| SSH - docker01 | `192.168.1.101:22` | Remote Linux administration |
| ubuntu-server | `192.168.1.106` | Ubuntu Server VM on PVE-02 |
| SSH - ubuntu-server | `192.168.1.106:22` | Remote Ubuntu administration |
| Portainer | `192.168.1.101:9443` | Docker web management |
| Uptime Kuma | `192.168.1.101:3001` | Service monitoring |

The previous `docker01` LXC used a router DHCP reservation at `192.168.1.101`. Its old storage was removed on 23 September 2026 and a clean rebuild is planned.

The `ubuntu-server` VM also uses DHCP with a router reservation. The router maps MAC address `BC:24:11:47:01:A7` to `192.168.1.106`, so the guest keeps a predictable address while Netplan remains DHCP-based.

Both Proxmox hosts use the LAN gateway and DNS resolver at `192.168.1.254`.

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

The Enterprise PVE and unused Ceph Enterprise repositories were disabled on PVE-02, the `pve-no-subscription` repository was configured, and a simulated full upgrade was reviewed before applying updates. The node finished the session on Proxmox VE 9.2.20 with kernel `7.0.14-17-pve`, matching PVE-01.

Later the same day, PVE-02 received its first full virtual machine: `VM 100 - ubuntu-server`. Ubuntu Server 24.04.5 LTS was installed with 2 vCPU, 2 GB RAM and a 20 GiB virtual disk on `local-lvm`. Its VirtIO network adapter is attached to `vmbr0`, giving the guest direct access to the home LAN at reserved address `192.168.1.106`. OpenSSH and the QEMU Guest Agent were enabled and tested, the VM was configured to start automatically with the host, and a reboot test confirmed that networking, SSH and guest-agent integration return correctly.

Full troubleshooting and maintenance notes are available here:

- [PVE-02 / OptiPlex 3090 troubleshooting](docs/pve3090-troubleshooting.md)
- [PVE-02 storage troubleshooting - 14 September 2026](docs/pve3090-storage-troubleshooting-2026-09-14.md)
- [Network and Proxmox maintenance - 15 September 2026](docs/network-maintenance-2026-09-15.md)
- [First Ubuntu Server VM on PVE-02 - 15 September 2026](docs/first-vm-ubuntu-server-2026-09-15.md)
- [Lenovo V520s storage upgrade and cleanup - 23 September 2026](docs/lenovo-storage-upgrade-2026-09-23.md)

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
- [x] Deployed the first workload on PVE-02
- [x] Created VM 100 `ubuntu-server` on PVE-02 and connected it through `vmbr0`
- [x] Installed Ubuntu Server 24.04.5 LTS on VM 100
- [x] Configured and tested SSH on the Ubuntu VM
- [x] Installed and tested QEMU Guest Agent
- [x] Reserved `192.168.1.106` for the Ubuntu VM using DHCP reservation
- [x] Configured VM 100 to start automatically with PVE-02
- [x] Reboot-tested VM 100 and verified IP, SSH and QEMU Guest Agent recovery
- [ ] Configure Uptime Kuma notifications
- [ ] Create a homelab status page
- [ ] Learn Docker networking in more depth
- [ ] Configure backups
- [ ] Improve homelab security
- [ ] Revisit NVMe support on PVE-02 using a safe test path
- [ ] Monitor PVE-02 storage health
