# PVE-02 Emergency Runbook

This runbook is a practical step-by-step checklist for troubleshooting the Dell OptiPlex 3090 Proxmox node (`pve3090`) when the web interface, SSH, or storage appears unhealthy.

It is designed to be followed in order. The goal is to diagnose the problem safely before making changes.

## Node reference

| Item | Value |
| --- | --- |
| Hardware | Dell OptiPlex 3090 Micro |
| Hostname | `pve3090` |
| Role | Secondary Proxmox VE node |
| Management IP | `192.168.1.165` |
| Proxmox web UI | `https://192.168.1.165:8006` |
| SSH | `192.168.1.165:22` |
| Root filesystem | EXT4 on `/dev/mapper/pve-root` |
| Storage path | NVMe SSD through Realtek RTL9210 bridge |

Related incident documentation:

- [Initial PVE-02 troubleshooting](pve3090-troubleshooting.md)
- [Incident log - 12 September 2026](pve3090-incident-2026-09-12.md)

---

# 1. Check basic network reachability

From the Windows workstation, open PowerShell.

```powershell
ping 192.168.1.165
```

### Interpretation

- Replies received: the node is reachable at IP level.
- No replies: do not assume Proxmox itself is broken yet. Check power, Ethernet/powerline link, switch/router, and local console.

Then check the important TCP ports:

```powershell
Test-NetConnection 192.168.1.165 -Port 22
Test-NetConnection 192.168.1.165 -Port 8006
```

### Interpretation

- Port 22 open: SSH is accepting TCP connections.
- Port 8006 open: something is listening on the Proxmox web port.
- An open port does **not** prove the service behind it is healthy.

---

# 2. Test SSH

```powershell
ssh root@192.168.1.165
```

If it fails, retry with verbose output:

```powershell
ssh -v root@192.168.1.165
```

Useful failure patterns include:

```text
Connection reset by 192.168.1.165 port 22
```

or:

```text
kex_exchange_identification: Connection closed by remote host
```

If SSH opens normally, continue diagnostics remotely instead of moving monitor and keyboard.

If SSH immediately resets, continue to the HTTPS/API test.

---

# 3. Test the Proxmox API directly

```powershell
curl.exe -k https://192.168.1.165:8006/api2/json/version
```

A healthy Proxmox API should return JSON data.

If there is no useful response, use verbose mode:

```powershell
curl.exe -vk https://192.168.1.165:8006/api2/json/version
```

### Interpretation

- TCP connection cannot be established: network path or service is unavailable.
- TCP/TLS connects but no HTTP/API response arrives: `pveproxy` or the underlying system may be unhealthy.
- Repeated TLS renegotiation with no API response is abnormal.

---

# 4. Decide whether local console access is required

Use the physical console when one or more of these are true:

- Proxmox web interface does not load.
- SSH resets before login.
- Port 8006 accepts connections but the API does not respond normally.
- The node previously showed EXT4, NVMe, I/O, or read-only filesystem errors.

Connect a monitor and keyboard directly to the OptiPlex and log in as `root`.

Do **not** start by rebooting or restarting several services blindly. First determine whether the root filesystem is writable.

---

# 5. Check whether the root filesystem is read/write

Run:

```bash
findmnt -no TARGET,SOURCE,FSTYPE,OPTIONS /
```

Look for either `rw` or `ro` in the mount options.

### Healthy example

```text
/ /dev/mapper/pve-root ext4 rw,...
```

### Critical example

```text
/ /dev/mapper/pve-root ext4 ro,...
```

## If the filesystem is `ro`

Treat this as a storage/filesystem incident.

Do **not**:

- run `fsck` on the mounted root filesystem;
- perform package upgrades;
- create unnecessary files;
- repeatedly restart services;
- disconnect the NVMe storage while the machine is powered on.

Continue with the storage checks below and capture evidence before rebooting.

## If the filesystem is `rw`

Continue to the service checks in section 8.

---

# 6. Check kernel messages for storage/filesystem errors

```bash
dmesg -T | grep -Ei 'EXT4|I/O error|nvme|rtl9210|reset|read-only|journal' | tail -n 100
```

Look for messages such as:

```text
EXT4-fs error
Detected aborted journal
Remounting filesystem read-only
I/O error
```

Record or photograph the output before rebooting.

Then identify the disks/filesystems:

```bash
lsblk -f
```

---

# 7. Check SSD / NVMe health

On this node the NVMe SSD is exposed through the Realtek RTL9210 bridge and has previously appeared as `/dev/sda`.

First confirm the device name with:

```bash
lsblk
```

Then, if the system disk is still `/dev/sda`:

```bash
smartctl -a /dev/sda
```

Important fields to inspect include:

- SMART overall health
- Critical Warning
- Media and Data Integrity Errors
- Error Information Log Entries
- Temperature
- Unsafe Shutdowns

A SMART `PASSED` result does not completely rule out problems with the USB/NVMe bridge, cable, power path, or filesystem.

---

# 8. If the filesystem is `rw`, check Proxmox and SSH services

Start with failed services:

```bash
systemctl --failed
```

Then check the main services:

```bash
systemctl status pveproxy pvedaemon pvestatd ssh --no-pager -l
```

Check whether ports 22 and 8006 are listening:

```bash
ss -lntp | grep -E ':(22|8006)\b'
```

Check recent logs:

```bash
journalctl -b -p warning --no-pager | tail -n 100
```

For the Proxmox web proxy specifically:

```bash
journalctl -u pveproxy -b --no-pager | tail -n 100
```

---

# 9. Restart services only when storage is healthy and root is `rw`

If there are no current storage errors and the root filesystem is mounted read/write, restart the affected service one at a time.

For the Proxmox web interface:

```bash
systemctl restart pveproxy
```

Then verify:

```bash
systemctl status pveproxy --no-pager -l
```

For SSH, only if SSH itself is unhealthy:

```bash
systemctl restart ssh
```

Then verify:

```bash
systemctl status ssh --no-pager -l
```

Avoid restarting unrelated services at random. Change one thing at a time and test after each change.

---

# 10. Reboot decision

A clean reboot is reasonable when:

- console access works;
- diagnostic evidence has been captured;
- the node is unstable or the filesystem has remounted read-only;
- service restarts are not appropriate or do not solve the issue.

Use:

```bash
systemctl reboot
```

or:

```bash
reboot
```

Prefer a normal software reboot over holding the physical power button.

## Forced power-off

Holding the power button is a last resort only when:

- the local console is completely unresponsive;
- SSH and web access are unavailable;
- a normal ACPI button press does not trigger shutdown;
- there is no other practical way to regain control.

A forced power-off can increase the risk of filesystem corruption and should not be the first troubleshooting step.

---

# 11. Never run `fsck` on the mounted root filesystem

Do not run a command such as:

```text
fsck /dev/mapper/pve-root
```

while `/dev/mapper/pve-root` is mounted as `/`.

If the filesystem remains damaged or read-only after reboot, filesystem repair must be done **offline**, for example from recovery/rescue media or another environment where the root filesystem is not mounted.

At that point, stop and plan the repair carefully before proceeding.

---

# 12. Verify recovery

After the node comes back, check the filesystem first:

```bash
findmnt -no TARGET,SOURCE,FSTYPE,OPTIONS /
```

Confirm `rw`.

Then check for fresh storage errors:

```bash
dmesg -T | grep -Ei 'EXT4|I/O error|nvme|rtl9210|reset|read-only|journal' | tail -n 100
```

Check services:

```bash
systemctl --failed
systemctl status pveproxy pvedaemon pvestatd ssh --no-pager -l
```

From Windows, test again:

```powershell
ping 192.168.1.165
Test-NetConnection 192.168.1.165 -Port 22
Test-NetConnection 192.168.1.165 -Port 8006
curl.exe -k https://192.168.1.165:8006/api2/json/version
```

Finally open:

```text
https://192.168.1.165:8006
```

---

# Quick decision tree

```text
Proxmox web UI not opening
|
+-- Ping fails
|   +-- Check power / network / local console
|
+-- Ping works
    |
    +-- Test ports 22 and 8006
        |
        +-- Ports closed
        |   +-- Use local console and inspect networking/services
        |
        +-- Ports open
            |
            +-- Test SSH and curl API
                |
                +-- Both healthy
                |   +-- Browser/certificate/client-side issue likely
                |
                +-- SSH resets or API hangs
                    +-- Use local console
                        |
                        +-- Root filesystem = ro
                        |   +-- Treat as storage/filesystem incident
                        |       +-- Capture dmesg / lsblk / SMART
                        |       +-- Do not fsck mounted root
                        |       +-- Prefer clean reboot
                        |
                        +-- Root filesystem = rw
                            +-- Check pveproxy / pvedaemon / ssh
                            +-- Check journal logs
                            +-- Restart only the affected service
```

---

# What to record after every incident

Add the following to the GitHub incident log:

- date and time;
- symptoms;
- whether ping worked;
- whether ports 22 and 8006 were open;
- SSH error message;
- `curl` result;
- root filesystem state (`rw` or `ro`);
- relevant `dmesg` errors;
- SMART status;
- actions taken;
- whether a reboot was required;
- final result;
- suspected root cause.

This makes repeated failures easier to compare and turns troubleshooting into a repeatable operational process rather than relying on memory.