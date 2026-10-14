"""AppleScript quoting for channel_add_plugin: an agent-supplied name must not break out of the string."""
from fl_studio_mcp.tools.channels import _q


def test_applescript_quote_escapes():
    assert _q('Evil" to do shell script "rm \\x') == '"Evil\\" to do shell script \\"rm \\\\x"'
