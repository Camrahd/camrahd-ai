from camrahd_ai.tools import terminal_tools
from camrahd_ai.tools.approval import DENIED


def test_blocked_command_is_rejected():
    result = terminal_tools.run_command.invoke({"command": "dd if=/dev/zero of=/dev/sda"})
    assert "not allowed" in result


def test_empty_command_is_rejected():
    result = terminal_tools.run_command.invoke({"command": "   "})
    assert result.startswith("Error")


def test_denied_approval_returns_denied(monkeypatch):
    monkeypatch.setattr(terminal_tools, "request_approval", lambda description: False)
    result = terminal_tools.run_command.invoke({"command": "echo hi"})
    assert result == DENIED


def test_approved_command_runs(monkeypatch):
    monkeypatch.setattr(terminal_tools, "request_approval", lambda description: True)
    result = terminal_tools.run_command.invoke({"command": "echo hi"})
    assert "hi" in result
