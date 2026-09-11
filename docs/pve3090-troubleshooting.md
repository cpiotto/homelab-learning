# PVE-02 / Dell OptiPlex 3090 Troubleshooting

Date: 11 September 2026

This document records the troubleshooting process used when the second Proxmox node (`pve3090`) was reachable on the network but the Proxmox web interface and SSH were not working correctly.

## Node details

| Item | Value |
| --- | --- |
| Hardware | Dell OptiPlex 3090 Micro |
| Hostname | `pve3090` |
| Role | Secondary Proxmox VE node |
| Management IP | `192.168.1.165/24` |
| Gateway | `192.168.1.254` |
| Proxmox web UI | `https://192.168.1.165:8006` |
| Physical network interface | `eno2` |
| Proxmox bridge | `vmbr0` |
| Root filesystem | `/dev/mapper/pve-root` |
| Filesystem | EXT4 |
| Storage path | NVMe SSD through a Realtek RTL9210 bridge |

The Proxmox management address is configured statically in `/etc/network/interfaces`.

```text
auto lo
iface lo inet loopback

iface eno2 inet manual

auto vmbr0
iface vmbr0 inet static
    address 192.168.1.165/24
    gateway 192.168.1.254
    bridge-ports eno2
    bridge-stp off
    bridge-fd 0

iface wlp3s0 inet manual

source /etc/network/interfaces.d/*
```

## Initial symptoms

The server appeared to be online, but the Proxmox web interface would not load.

Basic ICMP connectivity worked:

```powershell
ping 192.168.1.165
```

TCP checks also showed that ports 22 and 8006 were reachable:

```powershell
Test-NetConnection 192.168.1.165 -Port 22
Test-NetConnection 192.168.1.165 -Port 8006
```

Both reported:

```text
TcpTestSucceeded : True
```

However, browser access to the Proxmox interface timed out.

A direct HTTPS test also timed out:

```powershell
curl.exe -k --max-time 10 https://192.168.1.165:8006/
```

SSH behaved differently: the TCP connection opened, but the remote host immediately closed the session.

```powershell
ssh -v root@192.168.1.165
```

The client reported:

```text
kex_exchange_identification: Connection closed by remote host
```

This was an important lesson: an open TCP port does not prove that the application behind the port is healthy.

## Console investigation

A monitor and keyboard were connected directly to the OptiPlex.

The console showed EXT4 errors including:

```text
EXT4-fs (dm-1): failed to convert unwritten extents
EXT4-fs error (device dm-1)
Detected aborted journal
Remounting filesystem read-only
```

Linux had remounted the root filesystem read-only after detecting a filesystem/storage error. This explained why the machine could still answer basic network traffic while services such as SSH and the Proxmox web interface behaved incorrectly.

## Filesystem identification

The storage layout was inspected with:

```bash
lsblk -f
```

The Proxmox root filesystem was identified as:

```text
/dev/mapper/pve-root
```

with EXT4 as the filesystem.

After reboot, the mount state was checked with:

```bash
findmnt -no SOURCE,FSTYPE,OPTIONS /
```

The result showed:

```text
/dev/mapper/pve-root ext4 rw,...
```

The `rw` flag confirmed that the root filesystem had returned to normal read/write operation.

## NVMe health check

SMART/NVMe health information was inspected with:

```bash
smartctl -a /dev/sda
```

Important results:

```text
SMART overall-health self-assessment test result: PASSED
Critical Warning: 0x00
Available Spare: 100%
Percentage Used: 0%
Media and Data Integrity Errors: 0
Error Information Log Entries: 0
```

The reported temperature was approximately 42 C.

At the time of testing, SMART did not show evidence of physical SSD failure.

The drive had also recorded multiple unsafe shutdowns, which is relevant when investigating filesystem journal recovery or corruption.

## Kernel log investigation

Kernel messages were filtered with:

```bash
dmesg | grep -Ei 'EXT4|NVMe|I/O error'
```

The system identified the storage bridge as:

```text
Realtek RTL9210 NVME
```

After reboot, EXT4 showed normal journal/orphan recovery and then remounted the filesystem read/write. No new critical I/O errors were observed during the follow-up check.

## Physical connection check

Because the SSD SMART data looked healthy, the NVMe bridge/cable became a possible source of the transient I/O problem.

The node was shut down cleanly before touching the storage connection:

```bash
poweroff
```

The cable connected to the NVMe adapter was replaced. The OptiPlex was then booted again with a monitor attached so the startup messages could be observed.

After the cable replacement:

- Proxmox booted normally.
- No new critical EXT4 or I/O errors appeared during the check.
- The root filesystem was mounted read/write.
- The Proxmox node showed online in the web interface.
- `https://192.168.1.165:8006` became accessible again.
- Proxmox showed the NVMe S.M.A.R.T. status as `PASSED`.

The cable/bridge is a suspected cause, not a proven root cause. The node should be monitored for recurrence.

## Network configuration verification

The network configuration was checked with:

```bash
cat /etc/network/interfaces
```

The Proxmox bridge was already configured with a static management address:

```text
iface vmbr0 inet static
    address 192.168.1.165/24
    gateway 192.168.1.254
    bridge-ports eno2
```

No additional static-IP change was required on the host.

## Commands used

### Windows / PowerShell

```powershell
ping 192.168.1.165
Test-NetConnection 192.168.1.165 -Port 22
Test-NetConnection 192.168.1.165 -Port 8006
curl.exe -k --max-time 10 https://192.168.1.165:8006/
ssh -v root@192.168.1.165
arp -a
```

### Linux / Proxmox

```bash
lsblk -f
findmnt -no SOURCE,FSTYPE,OPTIONS /
smartctl -a /dev/sda
dmesg | grep -Ei 'EXT4|NVMe|I/O error'
cat /etc/network/interfaces
poweroff
```

## Lessons learned

This incident provided practical experience across several layers of a real infrastructure problem:

1. Verify the target IP before troubleshooting an application.
2. Separate ICMP reachability from TCP reachability and application health.
3. An open port does not guarantee that the service is functioning correctly.
4. Linux may remount EXT4 read-only to protect data after filesystem or I/O errors.
5. Use `lsblk`, `findmnt`, SMART data and `dmesg` together to narrow down storage problems.
6. A healthy SSD does not rule out problems with a USB/NVMe bridge, cable or power path.
7. Always shut a server down cleanly before disconnecting its system storage.
8. Proxmox nodes should use predictable management addresses.
9. Documenting the troubleshooting path is as valuable as documenting the final fix.

## Follow-up

- Monitor the node for new EXT4 or I/O errors.
- Avoid forced power-offs where possible.
- If the error returns, test a different NVMe enclosure/bridge or connect the SSD through another supported path.
- Configure backups before placing important workloads on the second node.
