"""Read-only BIND9 recursive DNS health check exposed as an MCP tool.

Public portfolio example. Does not require or contain the Xiaozhi MCP token.
Run with the isolated Python environment used by the MCP bridge.
"""
from mcp.server.fastmcp import FastMCP
import dns.resolver

mcp = FastMCP("HomelabDNS")


@mcp.tool()
def check_dns() -> dict:
    """Check if the homelab BIND9 DNS server is resolving domains correctly."""
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = ["192.168.1.195"]
    resolver.timeout = 2
    resolver.lifetime = 3

    try:
        answers = resolver.resolve("example.com", "A")
        return {
            "server": "192.168.1.195",
            "status": "working",
            "domain": "example.com",
            "addresses": [a.to_text() for a in answers],
        }
    except Exception as error:
        return {
            "server": "192.168.1.195",
            "status": "failed",
            "error": str(error),
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
