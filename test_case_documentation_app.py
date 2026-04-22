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
         patch("case_documentation_app.db_manager.save_settings") as mock_save_settings, \
         patch("case_documentation_app.logging.warning") as mock_warning:

        # mock_st.session_state is a dict-like object in Streamlit
        # We can just use a real dict or a mocked object with get
        mock_st.session_state = MagicMock()
        mock_st.session_state.get.return_value = "default_value"

        yield {
            "mock_st": mock_st,
            "mock_save_settings": mock_save_settings,
            "mock_warning": mock_warning,
            "cache": case_documentation_app._persistent_settings_cache
        }

def test_persist_setting_invalid_key(mock_dependencies):
    case_documentation_app._persist_setting("invalid_key")
    # DB save should not be called
    mock_dependencies["mock_save_settings"].assert_not_called()
    # Cache should be empty
    assert mock_dependencies["cache"] == {}

def test_persist_setting_happy_path(mock_dependencies):
    # Set a value in session state
    mock_dependencies["mock_st"].session_state.get.return_value = "new_value"

    case_documentation_app._persist_setting("valid_key")

    # Value should be cached
    assert mock_dependencies["cache"] == {"valid_key": "new_value"}

    # Should be saved to DB
    mock_dependencies["mock_save_settings"].assert_called_once_with(
        case_documentation_app.DATABASE_DIR,
        {"valid_key": "new_value"}
    )

def test_persist_setting_oserror(mock_dependencies):
    mock_dependencies["mock_st"].session_state.get.return_value = "new_value"

    mock_error = Exception("Mocked Error")
    mock_dependencies["mock_save_settings"].side_effect = mock_error

    case_documentation_app._persist_setting("valid_key")

    # Warning should be logged
    mock_dependencies["mock_warning"].assert_called_once_with(
        "Failed to persist setting %s: %s", "valid_key", mock_error
    )
