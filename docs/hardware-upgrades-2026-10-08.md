# Homelab hardware upgrades - 8 October 2026

## Goal

Validate recent memory upgrades and confirm that the Lenovo backup/storage role remained healthy after the hardware changes.

## PVE-01 - Lenovo ThinkCentre V520s

The Lenovo Proxmox node was upgraded to 32 GB of DDR4 memory.

Linux reported:

```text
31 GiB total
1.8 GiB used
29 GiB available
0 B swap used
```

The system detected four 8 GB DIMMs:

| Manufacturer | Part number | Nominal speed | Configured speed |
| --- | --- | ---: | ---: |
| Kingston | `9905678-026.A00G` | 2400 MT/s | 2400 MT/s |
| SK Hynix | `HMA81GU6CJR8N-VK` | 2667 MT/s | 2400 MT/s |
| Micron | `8ATF1G64AZ-2G6E1` | 2667 MT/s | 2400 MT/s |
| Crucial | `CT8G4DFS8266.M8FE` | 2667 MT/s | 2400 MT/s |

All modules are therefore operating at the common supported speed of 2400 MT/s.

A kernel log check did not show memory or machine-check errors. The only matching line was the normal EDAC subsystem initialisation message.

### Quadro P1000

The NVIDIA Quadro P1000 4 GB is physically installed and detected on PCIe:

```text
01:00.0 VGA compatible controller: NVIDIA Corporation GP107GL [Quadro P1000]
01:00.1 Audio device: NVIDIA Corporation GP107GL High Definition Audio Controller
```

The current plan is not to force the proprietary NVIDIA driver onto the Proxmox host. The GPU is reserved for a later PCIe passthrough project, where it can be assigned directly to a Linux VM for CUDA, container-GPU, transcoding or light inference experiments.

### Storage validation

After the memory upgrade, all Lenovo Proxmox storages remained active:

| Storage | Type | Status | Usage |
| --- | --- | --- | ---: |
| `backup-storage` | directory | active | 16.57% |
| `local` | directory | active | 15.12% |
| `local-lvm` | LVM-thin | active | 0% |
| `nvme-storage` | LVM-thin | active | 0% |

The NFS export also remained active:

```text
/mnt/pve-backup -> 192.168.1.165
```

The export is the off-host backup target for the Ubuntu VMs on `pve3090`.

## PVE-04 - Dell OptiPlex 3080 (`pve3080b`)

The clean automation/security test node was upgraded from 8 GB to 16 GB DDR4.

Linux reported:

```text
15 GiB total
1.7 GiB used
13 GiB available
0 B swap used
```

Installed modules:

| Manufacturer / module | Capacity | Configured speed |
| --- | ---: | ---: |
| Crucial `CT8G4SFRA266.C8FP` | 8 GB | 2666 MT/s |
| SK Hynix `HMA81GS6CJR8N-VK` | 8 GB | 2666 MT/s |

Both modules are operating at 2666 MT/s.

The extra memory gives this node more headroom for its planned role in:

- Ansible
- Python automation
- security labs
- disposable test VMs/LXC containers
- future read-only AI/operations experiments

## Backup path validation

The remote backup storage was checked from `pve3090` after the Lenovo upgrade.

`lenovo-backup` remained:

```text
Type: nfs
Status: active
Usage: 16.57%
```

This confirms that the path remains operational:

```text
VM 100 / VM 101
      |
      v
pve3090
      |
      | NFS
      v
Lenovo pve
      |
      v
/mnt/pve-backup
```

## Result

- Lenovo memory upgrade to 32 GB validated.
- Four Lenovo DIMMs detected and running at 2400 MT/s.
- No memory-related kernel errors observed.
- Quadro P1000 detected correctly on PCIe.
- Lenovo local, LVM-thin and NVMe storages remain active.
- Lenovo NFS export remains active.
- `pve3090` still sees `lenovo-backup` as active.
- `pve3080b` memory upgrade to 16 GB validated.
- Both `pve3080b` DIMMs run at 2666 MT/s.

## Next project

Begin an Ansible learning environment on `pve3080b`, initially using VM 100 `ubuntu-server` on `pve3090` as a safe managed target.
