# Homelab rack migration: Ethernet and DNS incident recovery

**Date:** 28 October 2026  
**Status:** Recovery validated on the MSI Windows workstation; follow-up limitations documented  
**Scope:** Proxmox LXC, Windows networking, IPv4/IPv6 DNS, AdGuard Home, BIND9 and basic incident response

## 1. Objective and context

After powering down the Lenovo and Dell OptiPlex systems to relocate them into a rack, the Proxmox nodes were brought back online and were reachable over the LAN. However, the MSI Windows workstation could not reliably resolve website names.

The goal was to restore working connectivity **without reinstalling services, disabling IPv6, or changing the whole network**, then validate the DNS filtering path.

### Relevant components

| Component | Host / container | LAN address | Function |
| --- | --- | --- | --- |
| EE router | Home router | `192.168.1.254` | LAN gateway and automatic network configuration |
| MSI PiottoDesktop | Windows, `Ethernet 3` | `192.168.1.126` during testing | DNS client and troubleshooting workstation |
| AdGuard Home | `pve3080b` / LXC **204**, `adguard01` | `192.168.1.129` | DNS filtering and upstream forwarding |
| BIND9 | `pve3080` / LXC **201**, `dns01` | `192.168.1.195` | Internal `home.arpa` DNS |
| TP-Link Gigabit switch | Rack | — | Wired connectivity |

**Intended logical design:**

```text
MSI Windows workstation
       |
       | DNS over IPv4 or IPv6
       v
AdGuard Home (CT 204, 192.168.1.129) -- filtering / query log
       |
       +--> Internal DNS (BIND9, CT 201, 192.168.1.195)
       +--> Configured external upstream(s), including Quad9 DoH
```

The exact conditional-forwarding rule from AdGuard Home to BIND9 was **not separately inspected** in this incident. Successful `home.arpa` resolution through AdGuard is evidence of functioning internal resolution, not by itself proof of the selected upstream.

## 2. Symptoms and initial isolation

The MSI could reach Proxmox nodes on the LAN but browser name resolution failed. We used independent tests to distinguish IP connectivity from DNS resolution.

| Diagnostic | Observed result | Interpretation |
| --- | --- | --- |
| `ping 192.168.1.254` | 4/4 replies; 0% loss | LAN gateway reachable |
| `ping 1.1.1.1` | Replies; 0% loss | IPv4 Internet connectivity available |
| `nslookup google.com` | Timeout against an automatically selected IPv6 DNS server | DNS failure, not a general IPv4 outage |
| `nslookup google.com 192.168.1.195` | IPv4 and IPv6 answers | BIND9 DNS service reachable and resolving |
| `nslookup google.com 192.168.1.129` **before CT 204 recovery** | Timeout | AdGuard Home endpoint not responding |

The failing DNS addresses observed during different phases included:

- `2a00:23c7:2e06:2d01:be24:11ff:fea1:f4b7` — later confirmed as the **AdGuard Home LXC** global IPv6 address.
- `2a00:23c7:2e06:2d01::1` — an automatically received IPv6 DNS address that also timed out; its device/service ownership was not conclusively established.

**Important:** These are separate addresses and should not be treated as the same failure. A router/IPv6 advertisement hypothesis was explored, but the complete origin of the second address remains unverified.

## 3. Wired link speed: a separate fault

After reconnecting the MSI by Ethernet, the Internet worked but the switch showed a different link indicator colour for the MSI. Windows reported:

```powershell
Get-NetAdapter -Name "Ethernet 3" | Select-Object Name, LinkSpeed

# Before replacing the cable
# Ethernet 3  100 Mbps

# After replacing the cable
# Ethernet 3  1 Gbps
```

**Action:** Replaced the Ethernet patch cable. The negotiated link speed increased to **1 Gbps**.

**Inference:** The previous cable or its termination limited link negotiation; the exact cable defect or category was not independently established. This was distinct from the DNS outage.

## 4. Identifying the unavailable DNS service

The `dns01` container on `pve3080` was healthy, but its web port 80 did not answer. This was a false lead: `dns01` runs **BIND9**, not AdGuard Home.

From the Proxmox shell:

```bash
pct list
pct exec 201 -- ss -lntup
```

The `named` process was listening on TCP/UDP port 53 for IPv4 and IPv6, with no AdGuard administration web listener in that container.

The AdGuard Home service was located on **`pve3080b`, CT 204 (`adguard01`)**, rather than on CT 201. CT 204 had not started automatically following the physical migration. Once it was started, the service status showed:

```bash
pct exec 204 -- systemctl status AdGuardHome --no-pager
# Active: active (running)
# Loaded: ... enabled
```

The startup status included some truncated `dnsproxy` error messages. No persistent upstream fault was demonstrated after service recovery; logs would be needed to classify those lines.

### Prevent recurrence

On the `pve3080b` Proxmox host:

```bash
pct config 204 | grep -E '^(onboot|startup):'
# Initially: no output

pct set 204 -onboot 1

pct config 204 | grep onboot
# onboot: 1
```

This configures Proxmox to **attempt to start CT 204 at host boot**. The setting was verified; a complete host-reboot test was **not performed**.

## 5. Recovery and validation

### DNS service and query logging

After CT 204 was running:

```powershell
nslookup google.com 192.168.1.129
```

returned normal A and AAAA answers and identified the server as `adguard01.lan`.

The AdGuard Home dashboard became reachable. Its Query Log recorded `example.org` requests from `PiottoDesktop` / `192.168.1.126` as processed, confirming that explicit test queries reached AdGuard Home.

### Blocking test

```powershell
nslookup logs.ads.vungle.com 192.168.1.129
```

returned:

```text
Name: logs.ads.vungle.com
Addresses: ::
           0.0.0.0
```

The AdGuard Query Log confirmed the A and AAAA lookups were **blocked by the AdGuard DNS filter**. One earlier explicit query showed a transient timeout before its blocked answer; later tests succeeded cleanly.

### AdGuard IPv6 reachability

The IPv6 address of CT 204 was obtained without using the container console:

```bash
pct exec 204 -- ip -6 -brief address show
# eth0 ... 2a00:23c7:2e06:2d01:be24:11ff:fea1:f4b7/64 ...
```

A direct Windows lookup using that IPv6 address returned normal DNS answers.

### Workstation DNS settings

After recovery, the MSI's **Ethernet 3** DNS settings were configured to point to AdGuard Home on both address families:

| Address family | Configured DNS server |
| --- | --- |
| IPv4 | `192.168.1.129` |
| IPv6 | `2a00:23c7:2e06:2d01:be24:11ff:fea1:f4b7` |

Validation without explicitly specifying a server:

```powershell
nslookup google.com
# Server address: 2a00:23c7:2e06:2d01:be24:11ff:fea1:f4b7
# Returned A and AAAA records with no timeout

nslookup logs.ads.vungle.com
# Addresses: :: and 0.0.0.0 (blocked)

nslookup dns01.home.arpa
# Address: 192.168.1.195
```

These results demonstrate that the default DNS path on the tested Ethernet interface reached AdGuard Home, applied filtering, and resolved the internal `dns01.home.arpa` record.

`Server: UnKnown` in `nslookup` was not itself a DNS failure; it means the server's reverse name was not obtained.

## 6. Changes made and controls

- Replaced the MSI Ethernet patch cable; link negotiation increased from 100 Mbps to 1 Gbps.
- Started the previously stopped AdGuard Home CT 204.
- Enabled Proxmox `onboot: 1` for CT 204.
- Configured MSI `Ethernet 3` DNS to use AdGuard Home over IPv4 and IPv6.
- During isolation, tested manual IPv6 DNS servers (including Cloudflare and BIND9) and inspected DHCP/Router Advertisement settings. The temporary `RA Based DNS Config` change was reverted to `enabled`.
- Did **not** reinstall AdGuard Home/BIND9, turn off IPv6 globally, or change the EE router.

## 7. Limitations and follow-up work

1. **Public IPv6 prefix:** The CT 204 IPv6 address is globally scoped and tied to the ISP-delegated prefix, which may change. The MSI's statically configured IPv6 DNS address may then become stale. A stable addressing/discovery approach can be assessed later; current functionality is validated, but resilience to renumbering is not.
2. **Automatic DNS distribution:** The address `2a00:23c7:2e06:2d01::1` was received automatically and timed out. The precise source/mechanism (e.g. DHCPv6 versus RA/RDNSS) was not proven. No router-wide change was made.
3. **BIND9 forwarding path:** A lookup of `dns01.home.arpa` through AdGuard resolved correctly, but a dedicated conditional-forwarding or upstream-log inspection was not performed.
4. **Boot reliability:** `onboot: 1` is confirmed, but an actual cold-boot recovery test has not been carried out.
5. **Other client paths:** Windows Wi-Fi, encrypted DNS in browsers, VPN routing, and other devices were not exhaustively audited for bypassing AdGuard filtering.
6. **Startup warnings:** Some abbreviated `dnsproxy` errors were seen immediately after AdGuard startup. They should only be revisited if resolution problems recur.

These are **documented, non-blocking follow-ups** for the present recovery, not prerequisites for declaring the rack-migration incident resolved.

## 8. Lessons learned and professional relevance

- Separate **Layer 1/2 link negotiation**, **Layer 3 IP connectivity**, and **Layer 7 DNS name resolution** rather than treating all failures as an Internet outage.
- Test a public IP address independently of domain names to isolate DNS problems.
- A running DNS server (`named`/BIND9) does not imply that a distinct filtering service (AdGuard Home) is running.
- Check the **correct Proxmox node and LXC ID** before troubleshooting a service.
- A successful direct `nslookup <name> <server>` does not prove the client uses that server by default; repeat the test without the server argument.
- Validate filtering through **both DNS responses and AdGuard Query Log**.
- Use Proxmox start-on-boot configuration for critical lab services, and distinguish a configured boot policy from a successfully tested restart.
- Keep unresolved ISP IPv6 behaviour documented without allowing it to block completion of the main objective.

**Relevant entry-level skills:** Windows PowerShell, Linux commands, Proxmox/LXC operations, TCP/IP, IPv4/IPv6, DHCP/DNS, systematic troubleshooting, root-cause analysis and evidence-based incident documentation.
