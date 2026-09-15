# Homelab Network and Proxmox Maintenance - 15 September 2026

This session focused on understanding how the two Proxmox hosts communicate, diagnosing the OptiPlex 3090 network configuration, validating storage and Proxmox networking concepts, and bringing both nodes to the same software level.

## Hosts used

| Host | Role | Management IP |
| --- | --- | --- |
| Lenovo ThinkCentre V520s | PVE-01 / primary node | `192.168.1.164` |
| Dell OptiPlex 3090 Micro | PVE-02 / secondary node | `192.168.1.165` |

Both hosts are on the `192.168.1.0/24` LAN.

## Basic connectivity testing

Connectivity was first verified in both directions using `ping`.

```bash
ping 192.168.1.165
ping 192.168.1.164
```

Both hosts responded correctly with no packet loss.

SSH was then tested from the Lenovo to the OptiPlex 3090:

```bash
ssh root@192.168.1.165
```

The remote session was verified with:

```bash
hostname
whoami
```

This confirmed that the Lenovo could remotely administer the 3090 over the LAN.

## OptiPlex 3090 system inspection

### Uptime

```bash
uptime
```

The command was used to learn how Linux reports uptime, active users and load averages.

### Memory

```bash
free -h
```

Observed configuration:

- 16 GB physical RAM installed
- approximately 15 GiB visible to Linux
- 8 GiB swap
- swap unused during the session

### CPU

```bash
lscpu
```

Confirmed hardware:

- Intel Core i5-10500T
- 6 physical cores
- 12 logical CPUs / threads
- Intel VT-x virtualization support
- maximum reported CPU frequency: 3.8 GHz

## Storage inspection

The storage layout was inspected with:

```bash
lsblk
lsblk -o NAME,SIZE,TRAN,MODEL
```

The active system disk was confirmed as:

- Samsung SSD 840 Series
- SATA
- approximately 120 GB marketed capacity / 111.8 GiB reported by Linux

The Proxmox layout includes:

- EFI boot partition
- `pve-root`
- `pve-swap`
- `pve-data` thin pool

Proxmox storage was checked using:

```bash
pvesm status
```

Observed storages:

- `local` - directory storage for ISO images, backups, templates and imports
- `local-lvm` - LVM-thin storage for VM and LXC disks

The storage configuration was inspected with:

```bash
cat /etc/pve/storage.cfg
```

This session reinforced the difference between the physical disk, Linux partitions, LVM volumes and Proxmox logical storages.

## Proxmox bridge networking

The 3090 network configuration was inspected with:

```bash
cat /etc/network/interfaces
ip -br addr
bridge link
ip route
ip neigh
```

The working structure is:

```text
Physical Ethernet
      |
    nic0
      |
    vmbr0
      |
Proxmox host + future VMs/LXC
```

Confirmed management configuration:

```text
address 192.168.1.165/24
gateway 192.168.1.254
bridge-ports nic0
```

`bridge link` confirmed that `nic0` is a member of `vmbr0` and is forwarding traffic.

## Gateway troubleshooting

The initial 3090 configuration used the wrong gateway:

```text
192.168.1.1
```

The 3090 could communicate with the Lenovo because both were on the same local subnet, but it could not reach the configured gateway.

The Lenovo routing table was used as the known-good reference:

```bash
ip route
```

The correct gateway was identified as:

```text
192.168.1.254
```

The persistent 3090 network configuration was backed up:

```bash
cp /etc/network/interfaces /etc/network/interfaces.backup
```

The gateway in `/etc/network/interfaces` was corrected and the active route was updated without rebooting:

```bash
ip route replace default via 192.168.1.254 dev vmbr0
```

The new route was verified with:

```bash
ip route
```

Testing then succeeded:

```bash
ping -c 4 192.168.1.254
ping -c 4 8.8.8.8
```

This proved that LAN routing and Internet access by IP were working.

## DNS troubleshooting

Although Internet access by IP worked, name resolution failed:

```bash
ping -c 4 google.com
```

The 3090 resolver configuration showed:

```text
nameserver 192.168.1.1
```

The Lenovo was checked as the known-good host and used:

```text
nameserver 192.168.1.254
```

The 3090 resolver file was backed up:

```bash
cp /etc/resolv.conf /etc/resolv.conf.backup
```

The DNS server was then corrected to:

```text
nameserver 192.168.1.254
```

After the correction:

```bash
ping -c 4 google.com
```

resolved the hostname and completed successfully.

This clearly demonstrated the difference between:

- local connectivity
- default gateway routing
- Internet connectivity by IP
- DNS name resolution

## Proxmox repository troubleshooting

`apt update` initially reached the Internet successfully but returned `401 Unauthorized` for the Proxmox Enterprise repositories.

The repository files were inspected under:

```bash
/etc/apt/sources.list.d/
```

The Enterprise PVE repository was disabled by renaming the file rather than deleting it:

```bash
mv /etc/apt/sources.list.d/pve-enterprise.sources \
   /etc/apt/sources.list.d/pve-enterprise.sources.disabled
```

A no-subscription repository was configured in:

```text
/etc/apt/sources.list.d/proxmox.sources
```

with:

```text
Types: deb
URIs: http://download.proxmox.com/debian/pve
Suites: trixie
Components: pve-no-subscription
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
```

The unused Ceph Enterprise repository was also disabled:

```bash
mv /etc/apt/sources.list.d/ceph.sources \
   /etc/apt/sources.list.d/ceph.sources.disabled
```

After this change:

```bash
apt update
```

completed normally using the Debian and Proxmox no-subscription repositories.

## Safe upgrade workflow

Before performing upgrades, the planned changes were simulated:

```bash
apt -s full-upgrade
```

This allowed confirmation that no packages would be removed.

The 3090 simulation reported:

- 167 packages to upgrade
- 2 packages to install
- 0 packages to remove

The upgrade was then performed with:

```bash
apt full-upgrade
```

After the upgrade the host was rebooted so the new kernel could be loaded.

The same workflow was then performed on the Lenovo node. Its simulation reported:

- 63 packages to upgrade
- 2 packages to install
- 0 packages to remove

## Final software state

Both primary Proxmox nodes finished the session on the same versions:

| Host | Proxmox VE | Running kernel |
| --- | --- | --- |
| Lenovo V520s | 9.2.20 | `7.0.14-17-pve` |
| OptiPlex 3090 | 9.2.20 | `7.0.14-17-pve` |

## Commands practised

```bash
hostname -I
ping
ssh
hostname
whoami
uptime
free -h
lscpu
lsblk
lsblk -o NAME,SIZE,TRAN,MODEL
pvesm status
cat /etc/pve/storage.cfg
cat /etc/network/interfaces
ip -br addr
bridge link
ip route
ip neigh
cat /etc/resolv.conf
ls -l /etc/resolv.conf
apt update
apt -s full-upgrade
apt full-upgrade
pveversion
uname -r
reboot
```

## Key lessons

1. Hosts on the same subnet can communicate even when the default gateway is wrong.
2. Successful access to an Internet IP does not prove DNS is working.
3. `vmbr0` acts as the software bridge between the physical NIC, the Proxmox host and future guests.
4. Proxmox storage names such as `local` and `local-lvm` are logical storage definitions, not separate physical disks.
5. Repository/authentication errors are different from network connectivity errors.
6. `apt -s full-upgrade` is useful for reviewing a major update before applying it.
7. A new kernel is not active until the host is rebooted.

## Next step

Create the first VM on PVE-02 and attach its virtual network adapter to `vmbr0`, then verify:

- DHCP / IP addressing
- gateway
- DNS
- Internet access
- SSH access between hosts and the VM
