"""Whole-API access: every function FL exposes to MIDI scripts, discovered live."""

from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..bridge_client import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def fl_api_introspect() -> dict:
        """List every function FL exposes to scripts in the running build, per module
        (documented and undocumented). Pair with fl_api_call."""
        return get_client().call("api.introspect")

    @mcp.tool()
    def fl_api_call(module: str, fn: str, args: Optional[list] = None) -> dict:
        """Call any FL scripting function directly, e.g. module='mixer', fn='getTrackName',
        args=[1]. Modules: arrangement, channels, device, general, mixer, patterns,
        playlist, plugins, transport, ui. Use fl_api_introspect to discover names."""
        return get_client().call("api.call", module=module, fn=fn, args=list(args or []))
