# Tailscale remote-access VPN — 17 October 2026

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

- Tailscale policy at the time of review: default allow-all (`src: ["*"]`, `dst: ["*"]`, `ip: ["*"]`).
- One tailnet user (owner), and two registered machines. Admission of invited users required approval.
- The allow-all policy is **broader than least privilege**: a compromised authorized device could potentially reach more services than necessary. Review tailnet access grants/ACLs and restrict administrative service access as the deployment matures. Avoid applying untested policies while relying exclusively on the VPN.
- Review device key expiry and recovery access, maintain guest backups, and consider monitoring Tailscale availability.
- IPv6 forwarding was not configured or tested; only IPv4 subnet routing was validated.
- Keep Proxmox authentication, updates and firewall protections enabled. Tailscale authentication does not replace application-layer security.

## Skills demonstrated

Linux network forwarding; subnet routing; VPN provisioning; authenticated remote access; troubleshooting minimal Debian systems; service startup persistence; TCP connectivity testing; security policy assessment; operational documentation.
