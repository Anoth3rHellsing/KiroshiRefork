import pytest
import os
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
from case_documentation_app import _collect_recent_logs, LOG_FILE

def test_collect_recent_logs_synthetic_payload():
    with patch.dict(os.environ, {"KIROSHI_SYNTHETIC_LOGS": "Mocked synthetic log"}):
        result = _collect_recent_logs()
        assert result == "Mocked synthetic log"

def test_collect_recent_logs_file_not_found():
    with patch.dict(os.environ, clear=True):
        with patch.object(Path, "exists", return_value=False):
            result = _collect_recent_logs()
            assert result == "Log file not found."

def test_collect_recent_logs_read_success_small_file():
    mock_log_content = "Log line 1\nLog line 2"
    with patch.dict(os.environ, clear=True):
        with patch.object(Path, "exists", return_value=True):
            # When size is smaller than max_bytes, start is 0
            with patch("pathlib.Path.open") as m:
                    mock_file = MagicMock()
                    m.return_value.__enter__.return_value = mock_file
                    mock_file.tell.return_value = len(mock_log_content)
                    mock_file.read.return_value = mock_log_content
                    result = _collect_recent_logs(max_bytes=65536)
                    assert result == mock_log_content

def test_collect_recent_logs_read_success_large_file():
    mock_log_content = "Log line 1\nLog line 2\nLog line 3"
    with patch.dict(os.environ, clear=True):
        with patch.object(Path, "exists", return_value=True):
            with patch("pathlib.Path.open") as m:
                mock_file = MagicMock()
                m.return_value.__enter__.return_value = mock_file
                mock_file.tell.return_value = 100
                mock_file.read.return_value = "Log line 3"
                result = _collect_recent_logs(max_bytes=20)
                mock_file.seek.assert_any_call(80)
                mock_file.readline.assert_called_once()
                assert result == "Log line 3"

def test_collect_recent_logs_oserror():
    with patch.dict(os.environ, clear=True):
        with patch.object(Path, "exists", return_value=True):
            with patch("pathlib.Path.open", side_effect=OSError("Permission denied")):
                result = _collect_recent_logs()
                assert "Unable to read logs: Permission denied" in result
