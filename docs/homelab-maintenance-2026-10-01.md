# Homelab Maintenance and Backup Configuration

Date: 1 October 2026

This document records the 1 October 2026 homelab session. The main goals were to bring a newly added Dell OptiPlex 3080 Proxmox node online, audit and update the existing `pve3090` node, validate its storage and networking health, and build an automated off-host backup path from `pve3090` to the Lenovo V520s.

## 1. New Proxmox node: `pve3080b`

A Dell OptiPlex 3080 Micro was prepared as an additional Proxmox VE node.

### Hardware observed

| Item | Value |
| --- | --- |
| Model | Dell OptiPlex 3080 Micro |
| CPU | Intel Core i5-10500T |
| RAM | 8 GB DDR4-2666 |
| Storage | SATA SSD |
| Hostname | `pve3080b` |
| Management IP | `192.168.1.167/24` |
| Gateway | `192.168.1.254` |
| DNS | `192.168.1.254` |

The machine has a locked Dell BIOS. The original NVMe device was removed and a clean SATA SSD was installed. Although the F12 boot menu requested the BIOS administrator password, the system successfully booted the Proxmox installer automatically from USB when no bootable OS was present on the SATA SSD.

### Proxmox installation and repository configuration

Proxmox VE was installed using the graphical installer with the management bridge configured at:

```text
192.168.1.167/24
```

The Enterprise PVE repository and unused Ceph Enterprise repository were disabled, and the no-subscription repository was enabled.

The installation was fully updated and rebooted.

Final verified versions:

```text
pve-manager/9.2.21/4f6e0ac86f9e8c7f
running kernel: 7.0.14-20-pve
```

The node is currently being left mostly clean so the existing `pve3090` and `pve3080` systems can be organised first.

## 2. PVE-02 / `pve3090` audit

The existing Dell OptiPlex 3090 Micro was reviewed before adding more workloads.

### Storage

`pvesm status` showed:

- `local` active
- `local-lvm` active
- Samsung SSD 840 Series 120 GB SATA system disk

The disk layout contains:

- 1 GB EFI partition
- 8 GB swap
- approximately 37.7 GB root filesystem
- approximately 49.3 GB LVM-thin data pool

Two VM disks are present:

- VM 100 disk: 20 GB
- VM 101 disk: 32 GB

Because `local-lvm` uses thin provisioning, the virtual disk allocation can exceed the currently consumed physical space.

### Running VMs

| VMID | Name | RAM | Disk | IPv4 | Start at boot |
| --- | --- | ---: | ---: | --- | --- |
| 100 | `ubuntu-server` | 2 GB | 20 GB | `192.168.1.106` | Yes |
| 101 | `ubuntu-server-01` | 2 GB | 32 GB | `192.168.1.111` | Yes |

Both VMs use:

- 2 vCPU
- VirtIO networking
- `vmbr0`
- QEMU Guest Agent
- Proxmox firewall on the VM NIC
- automatic startup

Both QEMU Guest Agents were verified after the host reboot.

## 3. Network investigation

The guest network counters initially showed a high `RX dropped` value inside both Ubuntu VMs.

The investigation checked several layers:

1. Physical Proxmox NIC
2. Proxmox TAP interface
3. VirtIO queue statistics
4. Linux IP/TCP/UDP counters inside the guest
5. Packet capture with `tcpdump`

Important findings:

- Physical NIC: no RX/TX errors
- VM TAP interface: zero drops
- VirtIO RX queue: zero drops
- `IpInDiscards`: zero
- TCP retransmissions: zero
- TCP receive queue drops: zero
- UDP receive-buffer errors: zero
- `tcpdump`: zero packets dropped by the kernel

The packet capture showed a large amount of normal LAN broadcast and multicast traffic, including:

- ARP
- mDNS / Google Cast
- IPv6 multicast
- IEEE 1905.1
- Rapid Spanning Tree Protocol
- Realtek broadcast frames

The conclusion was that the high guest `RX dropped` counter was not evidence of useful application traffic being lost. No network changes were made.

## 4. PVE-02 resource and temperature checks

The host had approximately:

```text
15 GiB RAM total
3.7 GiB used
11 GiB available
8 GiB swap
0 swap used
```

Load average was very low with both VMs running.

CPU temperature:

```text
Package: 32°C
Cores: approximately 28-31°C
```

Dell fan speed was approximately:

```text
1813 RPM
```

The thermal state was considered healthy.

## 5. Samsung SSD 840 health check

The 120 GB Samsung SSD 840 Series used by `pve3090` was checked with SMART.

Important values:

- SMART overall health: PASSED
- Power-on hours: 11,006
- Reallocated sectors: 0
- Uncorrectable errors: 0
- CRC errors: 0
- Runtime bad blocks: 0
- Temperature: approximately 29°C
- Wear-leveling normalised value: 78

A SMART self-test completed without error.

The SSD is old but currently healthy enough for continued lab use.

## 6. PVE-02 update

Before the update:

```text
pve-manager/9.2.20
kernel 7.0.14-17-pve
```

After `apt full-upgrade` and reboot:

```text
pve-manager/9.2.21/4f6e0ac86f9e8c7f
running kernel: 7.0.14-20-pve
```

Both VM 100 and VM 101 returned automatically after the reboot.

## 7. Lenovo NFS backup target

The Lenovo V520s already had a dedicated SATA backup disk configured as:

```text
backup-storage
/mnt/pve-backup
```

The storage showed approximately 234 GiB total and was almost empty.

The `nfs-kernel-server` package was installed on the Lenovo.

The NFS export was restricted to the `pve3090` host:

```text
/mnt/pve-backup 192.168.1.165(rw,sync,no_subtree_check,no_root_squash)
```

The export was applied with:

```bash
exportfs -rav
```

From `pve3090`, the export was verified with:

```bash
showmount -e 192.168.1.164
pvesm scan nfs 192.168.1.164
```

## 8. Proxmox NFS storage on PVE-02

The Lenovo export was added to `pve3090` as:

```text
lenovo-backup
```

The storage is mounted through NFS 4.2 and was verified as read/write.

A direct write/read test succeeded:

```bash
echo "NFS test from pve3090" > /mnt/pve/lenovo-backup/nfs-test.txt
cat /mnt/pve/lenovo-backup/nfs-test.txt
```

The storage appeared active in `pvesm status`.

> Note: the Lenovo backup SSD is an ageing lab drive with very high historical power-on hours. It is useful as an off-host secondary backup target, but it should not be treated as the only copy of irreplaceable data.

## 9. Manual VM backup validation

VM 100 and VM 101 were backed up manually to `lenovo-backup` using snapshot mode and Zstandard compression.

Example:

```bash
vzdump 100 --storage lenovo-backup --mode snapshot --compress zstd
```

VM 100:

- Backup completed successfully
- Archive size: approximately 2.94 GB
- Backup recognised by Proxmox storage
- `zstd -t` integrity test passed

VM 101:

- Backup completed successfully
- Archive size: approximately 2.38 GB
- Backup recognised by Proxmox storage
- `zstd -t` integrity test passed

The full path from VM to remote backup storage was therefore validated:

```text
VM
  -> vzdump snapshot
  -> zstd compression
  -> NFS 4.2
  -> Lenovo V520s
  -> /mnt/pve-backup
  -> integrity test
```

## 10. Automated backup job

A scheduled Proxmox backup job was created for both VMs.

Configuration:

| Setting | Value |
| --- | --- |
| Node | `pve3090` |
| VMs | `100,101` |
| Storage | `lenovo-backup` |
| Schedule | Daily at `03:00` |
| Mode | `snapshot` |
| Compression | `zstd` |
| Retention | `keep-last=7` |
| Repeat missed | Enabled |
| Job enabled | Yes |

The job ID generated by Proxmox is:

```text
cc902e41-8ba8-414d-87fb-22bbd4696af7
```

This provides an automatic off-host backup path for both Ubuntu VMs.

## Commands practised

```bash
pvesm status
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
qm list
qm config
qm guest cmd
qm guest exec
ip -br addr
ip -s link show
ethtool -S
nstat -az
tcpdump
free -h
uptime
sensors
smartctl -H
smartctl -A
smartctl -i
smartctl -t short
smartctl -l selftest
apt update
apt list --upgradable
apt full-upgrade
pveversion
uname -r
dpkg -l
exportfs
showmount
pvesm scan nfs
pvesm add nfs
findmnt
vzdump
pvesm list
pvesm path
zstd -t
pvesh get /cluster/backup
pvesh create /cluster/backup
pvesh usage /cluster/backup
```

## Skills practised

- Proxmox installation on locked-BIOS hardware
- Proxmox repository configuration
- Safe package updates and kernel verification
- VM inventory and resource auditing
- QEMU Guest Agent verification
- Linux network troubleshooting by layer
- VirtIO and TAP interface diagnostics
- Packet capture and broadcast/multicast analysis
- CPU and SSD temperature monitoring
- SMART health analysis
- NFS server configuration
- NFS access control
- Proxmox remote storage integration
- VM snapshot backups
- Backup integrity verification
- Automated backup scheduling
- Backup retention planning

## Outcome

At the end of the session:

- `pve3080b` was installed and updated to Proxmox VE 9.2.21 with kernel 7.0.14-20-pve.
- `pve3090` was audited, updated and verified healthy.
- VM 100 and VM 101 were confirmed operational after reboot.
- The Samsung SSD 840 system disk passed health checks.
- The apparent guest RX-drop issue was investigated and found not to represent meaningful packet loss.
- The Lenovo backup SSD was exported to `pve3090` over NFS.
- Both VMs were successfully backed up to the Lenovo and their archives passed integrity tests.
- A daily 03:00 automated backup job was configured with a seven-backup retention policy.

## Next steps

- Confirm the first scheduled 03:00 backup job completes successfully.
- After the scheduled backup is verified, consider removing older local VM backups from the `pve3090` system disk.
- Review and organise the existing `pve3080` node.
- Decide future workloads for `pve3080b`.
- Continue monitoring the health of the ageing Lenovo backup SSD.
