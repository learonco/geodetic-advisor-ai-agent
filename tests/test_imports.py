"""Module import smoke tests — all key packages must import cleanly."""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestImports:
    def test_import_src_tools_geodesy(self):
        import src.tools.geodesy  # noqa: F401

    def test_import_src_agents_geodetic(self):
        """Agent module should import cleanly (LLM is instantiated at module level,
        so we patch ChatGoogleGenerativeAI and create_agent)."""
        with patch("langchain_google_genai.ChatGoogleGenerativeAI"), \
             patch("langchain.agents.create_agent"):
            import src.agents.geodetic
            importlib.reload(src.agents.geodetic)

    def test_import_webui_chat_utils(self):
        """chat_utils imports geodetic_agent at module level; patch it."""
        with patch("src.agents.geodetic.geodetic_agent", new=MagicMock()):
            import src.webui.chat_utils  # noqa: F401

    def test_import_webui_map_utils(self):
        import src.webui.map_utils  # noqa: F401
