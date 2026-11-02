# AdGuard Home and BIND9 integration

## Objective and project context

Combine DNS filtering with predictable internal name resolution for the homelab. AdGuard Home provides the client-facing filtering layer, whilst BIND9 maintains the internal `home.arpa` namespace. This separation allows local service names to remain under local administration alongside external DNS resolution.

This document consolidates existing work; it is not a new deployment or a record of newly executed tests. Prepared on 27 October 2026, it builds on the [BIND9 implementation and validation notes](dns-infrastructure-2026-10-07.md) and the [13–14 October learning review](homelab-learning-review-2026-10-13-14.md). Those documents retain the detailed container specification, zone records, configuration checks and monitoring setup.

> **Validation update — 2 November 2026:** This project's selected-client DNS integration has now been functionally validated from the Windows MSI workstation. The new evidence, test outputs and remaining boundaries are recorded below. Statements labelled historical or unvalidated in the original 27 October assessment must be read in their original time context.


## Evidence status

Three evidence categories are used throughout:

- **Reported observed configuration:** AdGuard settings and dashboard observations supplied by the project owner for this document. They were not independently inspected during this documentation session.
- **Historical test:** results recorded in existing repository documents or reported by the owner from earlier testing. No DNS tests were repeated for this document.
- **Not yet validated:** behaviour that the available records do not demonstrate, including network-wide filtering coverage and a trace of the complete AdGuard-to-BIND query path.

The observation dates and dashboard reporting period were not supplied. No configuration export, dashboard capture or original command output for the AdGuard observations is included with this document.

## Architecture and responsibilities

| Component | Address | Responsibility |
| --- | --- | --- |
| AdGuard Home | `192.168.1.129` | Client-facing DNS filtering and upstream selection |
| BIND9 / `dns01` | `192.168.1.195` | Authoritative resolution for `home.arpa`; existing reverse zone for the homelab subnet |
| EE router | `192.168.1.254` | LAN gateway and reported default resolver for AdGuard private reverse DNS |
| Main Proxmox host / `pve` | `192.168.1.164` | Internal service target represented by `pve.home.arpa` |

BIND9 runs in Debian LXC 201 on `pve3080`, as documented in the earlier implementation notes. The AdGuard hosting platform, operating system and version have not been supplied and are not inferred here.

The following diagram describes the reported configuration, not a captured query trace:

```text
Clients using AdGuard Home
          |
          v
AdGuard Home — 192.168.1.129
          |
          +-- DNS filtering
          |
          +-- home.arpa queries --> BIND9 — 192.168.1.195
          |                         pve.home.arpa -> 192.168.1.164
          |
          +-- External upstream --> https://dns10.quad9.net/dns-query
          |
          +-- Private reverse DNS --> EE router — 192.168.1.254:53
```

The existing BIND documentation also records external name resolution through BIND. That historical capability does not mean AdGuard sends external queries to BIND: the supplied AdGuard configuration selects the Quad9 endpoint for external resolution.

## Reported observed configuration

### External and conditional upstreams

The supplied AdGuard upstream entries are:

```text
https://dns10.quad9.net/dns-query
[/home.arpa/]192.168.1.195
```

The HTTPS endpoint configures DNS-over-HTTPS for external upstream queries. This endpoint uses Quad9's service without threat blocking; DNS filtering is performed separately by AdGuard Home. The conditional entry selects BIND9 at `192.168.1.195` for the `home.arpa` namespace, keeping internal name resolution separate from the external upstream.

These entries document the configured destinations. They do not provide a new measurement of upstream availability or a query-log correlation proving which upstream answered an individual historical request. Bootstrap DNS, fallback resolvers, filtering lists and other settings are not specified in the supplied evidence.

### Private reverse DNS

Private reverse DNS functionality was reported as enabled, using the default resolver `192.168.1.254:53` on the EE router.

This is distinct from the conditional forward lookup rule for `home.arpa`. The earlier BIND implementation includes the reverse zone `1.168.192.in-addr.arpa`, but no supplied AdGuard setting directs private reverse queries to that zone on BIND. Successful historical reverse lookups against BIND therefore do not establish successful reverse lookups through AdGuard's router-based resolver. That path remains unvalidated in the available evidence.

## Reported dashboard observations

| Dashboard item | Reported observation |
| --- | --- |
| DNS queries | 108,530 |
| Blocked queries | 7,975 |
| Average processing time | 15 ms |
| Client addresses displayed | IPv4 and IPv6 |

These figures are a reported dashboard snapshot, not a benchmark or a current live reading. The reporting interval, capture time and workload are unknown. Average processing time must not be presented as a measured end-to-end application response time or an improvement over a previous baseline.

IPv4 and IPv6 client entries indicate that both address families appeared in the dashboard. They do not establish that every client used AdGuard exclusively or that all DNS traffic across the LAN was filtered.

## Historical validation and test boundaries

| Historical activity | Recorded or reported result | Evidence source and boundary |
| --- | --- | --- |
| BIND configuration and zone validation | Use of `named-checkconf` and `named-checkzone` before reload is recorded | 7 October BIND notes; not rerun for this document |
| Windows query directed at BIND | `pve.home.arpa` resolved to `192.168.1.164` | 7 October BIND notes; demonstrates direct BIND resolution, not the AdGuard path |
| Windows resolution after client DNS configuration | `pve.home.arpa` resolved without explicitly selecting the DNS server | 7 October BIND notes; the client was configured for BIND at that stage |
| Subsequent BIND checks | `pve.home.arpa` resolved to `192.168.1.164`; reverse resolution was also validated | 13–14 October review; historical revalidation of BIND |
| Internal resolution reported for this integration | `pve.home.arpa` returned `192.168.1.164` | Owner-reported earlier test; exact command, responding resolver and date were not supplied |
| Filtering of `doubleclick.net` | Blocking was observed with responses `0.0.0.0` and `::` | Owner-reported earlier test; original outputs, query-log entries, matched rule and date were not supplied |

The reported blocking responses support the historical observation for that domain. They do not establish universal blocking, identify the responsible filter list or demonstrate that all clients followed the same DNS path.

An IPv6-formatted answer is also distinct from IPv6 transport: receiving an AAAA record does not by itself prove that the DNS query travelled over IPv6. The test record must distinguish the requested record type from the resolver address and transport used.

Existing monitoring provides additional BIND context: Uptime Kuma was configured to query `pve.home.arpa` directly through `192.168.1.195` and expect `192.168.1.164`. This monitor does not test AdGuard filtering or the integrated forwarding path. The original monitoring details remain in the BIND document.

## EE router and IPv6 limitations

The 7 October notes record that Windows initially preferred the IPv6 DNS server supplied by the router. They also record a client-level configuration change to use BIND for both address families and successful subsequent resolution. These notes describe the earlier documented BIND client configuration; they do not establish the current AdGuard client configuration.

The project owner subsequently reported limitations associated with DNS IPv6 distribution by the EE router. The available evidence does not identify the exact router model, firmware, advertised resolver address, advertisement mechanism or which controls were unavailable. No specific router capability or attempted workaround is invented here.

The practical limitation is that configuring an IPv4 DNS path alone is insufficient evidence that clients will consistently use AdGuard when router-provided IPv6 DNS is also available. A client selecting another resolver may bypass the intended filtering path. The frequency and network-wide extent of that behaviour have not been established.

Consequently, this project does not claim enforced filtering across the entire home network. The earlier statement that BIND was being tested on selected clients is retained as historical context; the current DNS distribution configuration for all clients remains unconfirmed.

## Validation update — 2 November 2026

### Scope, systems and evidence

This is a **selected-client functional validation**, performed with the project owner on 2 November 2026 using PowerShell and the AdGuard Home web interface. Command results and configuration screenshots were provided during the troubleshooting session. No packet capture, BIND query-log correlation, router reconfiguration or whole-house client audit was performed.

| Component | Observed/recorded detail |
| --- | --- |
| Client | MSI Windows workstation; tested network interface: `Ethernet 3` |
| AdGuard | `adguard01`, LXC 204 on `pve3080b`; IPv4 `192.168.1.129` |
| AdGuard IPv6 DNS used by Windows | `2a00:23c7:2e06:2d01:be24:11ff:fea1:f4b7` (ISP prefix may change) |
| BIND9 | `dns01`, LXC 201 on `pve3080`; IPv4 `192.168.1.195` |
| Internal test record | `pve.home.arpa` -> `192.168.1.164` |
| Router | EE gateway `192.168.1.254` |

The owner confirmed that `pct status 204` indicated the container was running and that `pct exec 204 -- systemctl is-active AdGuardHome` indicated the service was active. The literal terminal output for these two service checks was not retained in this session.

### Configuration reviewed in the AdGuard interface

The primary upstream configuration was displayed as:

```text
https://dns10.quad9.net/dns-query
[/home.arpa/]192.168.1.195
```

The first entry configures Quad9 DNS-over-HTTPS for ordinary external lookups; the conditional rule selects BIND9 for `home.arpa`. The setting confirms **routing intent**, not a per-query trace of BIND9's participation.

Other settings observed: upstream strategy **Load balancing**; fallback DNS list empty; bootstrap DNS IPs `9.9.9.10`, `149.112.112.10`, `2620:fe::10`, and `2620:fe::fe:10`; upstream timeout **10 seconds**. Private reverse resolvers were enabled, with the displayed default `192.168.1.254:53` (EE router); client IP reverse-resolution was enabled. This reverse path is distinct from the `home.arpa` conditional forwarding rule.

### Windows client DNS selection

The PowerShell query below was used:

```powershell
Get-DnsClientServerAddress -InterfaceAlias "Ethernet 3" |
  Format-Table AddressFamily,ServerAddresses -AutoSize
```

Observed output:

```text
AddressFamily ServerAddresses
------------- ---------------
            2 {192.168.1.129}
           23 {2a00:23c7:2e06:2d01:be24:11ff:fea1:f4b7}
```

The selected interface showed one configured IPv4 DNS server and one IPv6 DNS server, both assigned to AdGuard. This does not inspect every Windows interface, every possible application-level resolver or every household client.

### Functional tests

| Test (2 November 2026) | Observed result | Assessment |
| --- | --- | --- |
| `nslookup pve.home.arpa 192.168.1.129` | Initial `DNS request timed out` / `Server: UnKnown`; nevertheless returned `pve.home.arpa -> 192.168.1.164` | Internal A-record resolution **passed** via explicit AdGuard IPv4. The initial timeout was not diagnosed; reverse server-name lookup is a plausible explanation, not a proven cause. |
| `nslookup logs.ads.vungle.com 192.168.1.129` | Resolver `adguard01.lan`; answers `::` and `0.0.0.0` | **Passed**: explicit AdGuard query was filtered for both address record families. |
| `nslookup logs.ads.vungle.com` | Automatically selected the AdGuard IPv6 resolver; answers `::` and `0.0.0.0` | **Passed**: the Windows client's default DNS selection used AdGuard for this query. |
| `nslookup pve.home.arpa` | Automatically selected the AdGuard IPv6 resolver; returned `192.168.1.164` | **Passed**: selected-client internal lookup works without specifying a DNS server. The returned A record is IPv4 data delivered by a query to an IPv6 resolver. |

Example of the automatic internal lookup:

```text
PS> nslookup pve.home.arpa
Server:  UnKnown
Address:  2a00:23c7:2e06:2d01:be24:11ff:fea1:f4b7

Non-authoritative answer:
Name:    pve.home.arpa
Address:  192.168.1.164
```

Here `Server: UnKnown` identifies an unresolved display name for the DNS server; it is **not** evidence that the requested internal A-record lookup failed.

### Query-log observations

In the AdGuard Home Query Log, `pve.home.arpa` queries of types **A** and **AAAA** were present on 2 November at 13:27:24, with the response state shown as **Processed** and an IPv6 client address. The log also displayed `pve.home.arpa.lan` search-suffix variants; their origin and significance were not investigated.

A separate real-world filtered query for `event.bblmw.com` showed **Blocked**, matching **AdGuard DNS filter**, with an AAAA response of `::`, `NOERROR`, TTL 10 and approximately 0.04 ms processing time. This corroborates actual filtering activity beyond the deliberate PowerShell test.

**Evidence boundary:** The displayed `pve.home.arpa` Query Log entries did not expose the upstream server that supplied the answer. A correct response could also be served from cache. Therefore the conditional forwarder is **configured and consistent with successful selected-client resolution**, but an individually traced AdGuard -> BIND9 query was **not captured**. Neither the short Query Log processing times nor the `Non-authoritative answer` label establish the upstream path.

### Scope-based completion decision

**Status: selected-client DNS integration validated and this learning stage closed as of 2 November 2026.**

Acceptance criteria met:

- AdGuard service/container operational per owner confirmation.
- Client DNS settings point to AdGuard for IPv4 and IPv6 on the tested Ethernet interface.
- Both explicit and automatic lookups demonstrate working internal resolution.
- Both deliberate and observed browsing-related queries demonstrate filtering.
- AdGuard UI shows the `home.arpa` -> BIND9 conditional forwarding rule.
- Outstanding limitations are recorded rather than treated as deployment failures.

**Not claimed:** enforced network-wide ad blocking, complete capture of every DNS path, a packet-level BIND forwarding trace, or validated private reverse-DNS behaviour via the EE router.

**Known limitations and deferred work:**

1. The EE router's IPv6 DNS advertisements may cause other clients to choose a non-AdGuard resolver; household-wide DNS enforcement remains unverified.
2. The ISP-assigned AdGuard IPv6 address may change when the WAN IPv6 prefix changes. Recheck client resolver selection after renumbering.
3. The reverse DNS default points to the EE router, not explicitly to BIND9. Only revisit if local host-name display or PTR lookups cause a concrete problem.
4. Optional stronger upstream evidence: run a unique uncached internal DNS test while observing AdGuard/BIND logs. Not necessary for closure of the current functional milestone.
5. The first explicit `pve.home.arpa` query had an initial timeout; repeat only if a user-visible failure or recurrent latency appears.

No new service, router purchase, forced IPv6 changes or additional homelab project is required for this milestone.

### Skills demonstrated

Selected-client IPv4/IPv6 resolver verification, Windows `nslookup` and PowerShell diagnostics, DNS filtering tests, understanding conditional forwarding versus reverse DNS, reading application logs, distinguishing observed outcomes from inferred architecture, and recording operational limitations. These map to entry-level IT Support and junior infrastructure troubleshooting work.

---

## Results (original 27 October assessment)

- The existing repository documents working historical internal DNS resolution through BIND, including `pve.home.arpa` and reverse lookups.
- The owner-reported AdGuard configuration separates external resolution through the supplied Quad9 endpoint from conditional resolution of `home.arpa` through BIND.
- Reported dashboard activity and the earlier `doubleclick.net` test provide evidence of filtering activity, within the stated limits of those observations.
- Private reverse DNS is documented separately because its reported resolver is the EE router, rather than BIND.
- Full end-to-end forwarding verification and consistent IPv4/IPv6 client coverage remain unvalidated. Documentation consolidation does not turn these gaps into completed tests.

## Lessons learnt

- Separate filtering, authoritative internal DNS and external resolution responsibilities so that each part can be explained and diagnosed independently.
- Record which resolver answered a test. A correct answer alone does not identify every component involved in obtaining it.
- Distinguish forward and reverse resolution: a working `home.arpa` rule does not prove that private PTR queries reach BIND.
- Treat IPv4 and IPv6 client resolver selection as part of the same operational design.
- Preserve test dates, sources and limitations. Historical success and dashboard totals are useful evidence, but neither replaces a current functional test.
- In professional infrastructure documentation, distinguish configured intent from observed behaviour and repeatable validation.

## Future improvements

These are documentation and validation follow-ups, not changes performed as part of this work.

| Priority | Follow-up | Purpose |
| --- | --- | --- |
| Essential for stronger integration evidence | Preserve an existing sanitised AdGuard settings capture and, if available, historical test output or query-log evidence | Support the reported configuration and identify the resolver/upstream used |
| Essential before claiming network-wide filtering | Document the actual IPv4/IPv6 client DNS settings and precise EE router limitation | Define the scope of filtering and any alternate resolver path |
| Optional | Validate private reverse resolution through the configured router resolver | Establish whether the existing reverse lookup behaviour meets the lab's needs |
| Future | Consider a functional monitor through AdGuard alongside the existing direct BIND monitor | Distinguish filtering/forwarding failures from BIND failures |

No additional service, router replacement or infrastructure project is required to review this document. Any later validation should target a specific evidence gap rather than repeat the original deployment.
