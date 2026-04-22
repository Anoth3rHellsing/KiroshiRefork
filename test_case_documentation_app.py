import pytest
from unittest.mock import patch, MagicMock, mock_open
import json
import logging
import case_documentation_app

@pytest.fixture
def mock_dependencies():
    with patch("case_documentation_app.PERSISTENT_SETTINGS_DEFAULTS", {"valid_key": "default_value"}), \
         patch("case_documentation_app.st") as mock_st, \
         patch("case_documentation_app._persistent_settings_cache", {}), \
         patch("case_documentation_app.SETTINGS_FILE") as mock_settings_file, \
         patch("case_documentation_app.logging.warning") as mock_warning:

        # mock_st.session_state is a dict-like object in Streamlit
        # We can just use a real dict or a mocked object with get
        mock_st.session_state = MagicMock()
        mock_st.session_state.get.return_value = "default_value"

        yield {
            "mock_st": mock_st,
            "mock_settings_file": mock_settings_file,
            "mock_warning": mock_warning,
            "cache": case_documentation_app._persistent_settings_cache
        }

def test_persist_setting_invalid_key(mock_dependencies):
    case_documentation_app._persist_setting("invalid_key")
    # File should not be opened
    mock_dependencies["mock_settings_file"].open.assert_not_called()
    # Cache should be empty
    assert mock_dependencies["cache"] == {}

def test_persist_setting_happy_path(mock_dependencies):
    # Set a value in session state
    mock_dependencies["mock_st"].session_state.get.return_value = "new_value"

    mock_file = mock_open()
    mock_dependencies["mock_settings_file"].open = mock_file

    case_documentation_app._persist_setting("valid_key")

    # Value should be cached
    assert mock_dependencies["cache"] == {"valid_key": "new_value"}

    # File should be opened for writing
    mock_dependencies["mock_settings_file"].open.assert_called_once_with("w", encoding="utf-8")

    # Check that content was written
    handle = mock_file()
    written_content = "".join(call.args[0] for call in handle.write.call_args_list)
    assert json.loads(written_content) == {"valid_key": "new_value"}

def test_persist_setting_oserror(mock_dependencies):
    mock_dependencies["mock_st"].session_state.get.return_value = "new_value"

    mock_dependencies["mock_settings_file"].open.side_effect = OSError("Mocked Error")

    case_documentation_app._persist_setting("valid_key")

    # Warning should be logged
    mock_dependencies["mock_warning"].assert_called_once_with(
        "Failed to persist setting %s: %s", "valid_key", mock_dependencies["mock_settings_file"].open.side_effect
    )
