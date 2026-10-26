# Tailscale remote-access VPN — 17 and 26 October 2026

## Objective
Provide authenticated, encrypted access to Homelab Piotto from outside the home network without exposing the Proxmox web interface through router port-forwarding.

## Architecture

```text
Remote Windows 11 (PiottoDesktop)
    Tailscale 100.80.22.91
           |
    Encrypted Tailscale tunnel
           |
Debian 13 VM 210 (vpn01)
    Tailscale 100.72.195.67
    Subnet router advertising 192.168.1.0/24
           |
    Homelab LAN 192.168.1.0/24
           |
Proxmox pve (Lenovo V520s) 192.168.1.164:8006
```

- Host: Proxmox VE on Lenovo V520s (`pve`).
- VM: `210`, hostname `vpn01`, Debian 13, 1 vCPU, 1 GB RAM, 16 GB disk on `nvme-storage`.
- Tailscale version displayed in admin console: 1.104.1.
- No EE router inbound port-forwarding was required.
- Only the two above-mentioned Tailscale devices were listed as connected in the admin console at the time of the review.

## Implementation

1. Installed Tailscale in the Debian guest using the [official Linux installation procedure](https://tailscale.com/docs/install/linux), after installing the missing `curl` utility:
   ```bash
   sudo apt install curl -y
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
   The device was authorized via the browser login flow. Do not commit authentication URLs, credentials, node keys, or auth keys.
2. Enabled Linux IPv4 forwarding and made the setting persistent:
   ```bash
   echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-tailscale.conf
   sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
   cat /proc/sys/net/ipv4/ip_forward
   ```
   Output was `1` after activation and again after a guest reboot.
3. Advertised the LAN subnet:
   ```bash
   sudo tailscale set --advertise-routes=192.168.1.0/24
   ```
   Approved `192.168.1.0/24` under the machine's route settings in the Tailscale admin console. This is a subnet router, **not** an exit node.
4. Confirmed the VM has Proxmox `onboot: 1` and `systemctl is-enabled tailscaled` returned `enabled`.

## Validation evidence

- `tailscale status` showed `vpn01` at `100.72.195.67` and `piottodesktop` at `100.80.22.91`.
- From Windows, `tailscale ping vpn01` received a reply.
- Windows PowerShell:
  ```powershell
  Test-NetConnection 192.168.1.164 -Port 8006
  ```
  returned `TcpTestSucceeded : True`, `InterfaceAlias : Tailscale`, and source address `100.80.22.91`.
- The Windows machine was then connected **exclusively to an iPhone mobile hotspot**, rather than the home LAN. The same TCP test passed and the Proxmox web UI loaded in the browser. This confirms actual off-site access over a separate internet connection.
- Restarted **only VM 210**. After reboot, `tailscale status` showed the devices connected and `cat /proc/sys/net/ipv4/ip_forward` still returned `1`.

## Troubleshooting and lessons learned

- The QEMU Guest Agent had not been enabled initially; the Proxmox agent setting was enabled, but the package installation was deferred. Guest-agent functionality remains **unverified / unfinished**. A working guest console was sufficient to deploy Tailscale.
- On the minimal Debian install, `curl` was initially unavailable. Installing it resolved the immediate blocker.
- An incomplete shell quote produced a `>` continuation prompt. `Ctrl+C` safely cancels an unfinished shell command.
- Saving a `sysctl.d` file does **not** itself apply a kernel setting; loading it and checking `/proc/sys/net/ipv4/ip_forward` verified both runtime and reboot persistence.
- Test both the tunnel and the intended service, and distinguish a same-LAN test from a true mobile-network test.

## Security assessment and outstanding tasks

- Tailscale policy at the **17 October review**: default allow-all (`src: ["*"]`, `dst: ["*"]`, `ip: ["*"]`).
- One tailnet user (owner), and two registered machines. Admission of invited users required approval.
- The original allow-all policy was **broader than least privilege**. It was replaced with account-scoped grants on 26 October (see follow-up below). Further per-device and per-port restrictions remain outstanding.
- Review device key expiry and recovery access, maintain guest backups, and consider monitoring Tailscale availability.
- IPv6 forwarding was not configured or tested; only IPv4 subnet routing was validated.
- Keep Proxmox authentication, updates and firewall protections enabled. Tailscale authentication does not replace application-layer security.

## Skills demonstrated

Linux network forwarding; subnet routing; VPN provisioning; authenticated remote access; troubleshooting minimal Debian systems; service startup persistence; TCP connectivity testing; security policy assessment; operational documentation.

## Follow-up: tailnet policy hardening — 26 October 2026

### Goal and change control

Replace the default wildcard grant with a narrower owner-account policy without disrupting remote access to the homelab. Before changing the live policy, the original HuJSON file was saved locally as `tailscale-policy-backup-2026-10-26.hujson`. No credentials or backup policy contents were committed to this public repository.

The admin console showed two online machines: `vpn01` (Debian 13, `100.72.195.67`) and `piottodesktop` (Windows 11, `100.80.22.91`). The advertised subnet `192.168.1.0/24` was **Approved**; exit-node routing was **Not Allowed**.

### Access policy change

Replaced the original unrestricted grant:

```hujson
{"src": ["*"], "dst": ["*"], "ip": ["*"]}
```

with these two grants (the account address is deliberately represented by a placeholder in this public example):

```hujson
"grants": [
  {
    "src": ["<tailnet-owner-email>"],
    "dst": ["autogroup:self"],
    "ip": ["*"]
  },
  {
    "src": ["<tailnet-owner-email>"],
    "dst": ["192.168.1.0/24"],
    "ip": ["*"]
  }
],
```

The original `ssh` policy section was left unchanged. The first grant permits the account's own tailnet devices as destinations; the second explicitly permits reaching the routed homelab subnet. Both still permit all IP protocols and ports within those scopes. This is **account-scoped access**, not per-device or per-port least privilege.

During editing, an extra `],` delimiter was identified and removed before saving. **Preview changes** showed the wildcard grant removed and the two grants added. **Preview rules** for the owner showed `autogroup:self:*` and `192.168.1.0/24:*`. The updated policy was saved without a displayed error.

### Test evidence

| Test | Evidence | Outcome |
| --- | --- | --- |
| Tailnet node reachability | `tailscale ping 100.72.195.67` from Windows; reply from `vpn01` via `192.168.1.251:41641` in 5 ms | Passed; **local direct path**, not an off-site test |
| Proxmox TCP connection | `Test-NetConnection 192.168.1.164 -Port 8006` | `TcpTestSucceeded : True`, `InterfaceAlias : Tailscale`, `SourceAddress : 100.80.22.91` |
| Independent mobile-network test | Windows desktop connected to iPhone hotspot instead of home Wi-Fi; repeated same TCP command | Passed; interface and source remained Tailscale / `100.80.22.91` |
| Application-level check | Browsed to `https://192.168.1.164:8006` over the mobile hotspot | Proxmox login page loaded |

These results verify that **remote Proxmox administration remains reachable across the subnet router after the policy change**. They do not demonstrate that unwanted connections are denied, that every internal service works, or that adding a new device requires approval.

### Operational usage

A trusted remote computer can install Tailscale, authenticate to the authorized tailnet account, connect, and open `https://192.168.1.164:8006`. A random computer without tailnet authorization cannot access the private address just by browsing to it. Keep normal Proxmox authentication and host firewalls enabled. The home internet connection and `vpn01` must remain available.

### Further security work

- Enable and validate **device approval** for new tailnet devices; do not confuse user-invitation approval with device approval.
- Narrow grants to the required management ports and, where practical, designated administration devices; test allow and deny cases before and after rollout.
- Review the existing Tailscale SSH `check` rule separately; an authorization rule does not prove Tailscale SSH is enabled on a node.
- Test Grafana, Prometheus, Uptime Kuma, the other Proxmox hosts and SSH from a remote network individually.
- Review key expiry, recovery procedures, patching, and monitoring of the subnet router.

### Skills demonstrated

Change control and rollback preparation; HuJSON policy editing; identity-scoped authorization; VPN subnet routing; network interface and TCP diagnostics; independent-network validation; separating connectivity tests from security enforcement tests.
