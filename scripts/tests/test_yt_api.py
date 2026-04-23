import io
import json
import os
import unittest
from unittest.mock import MagicMock, patch

import yt_api


def _urlopen_mock(data: dict) -> MagicMock:
    """Return a mock context manager that yields a BytesIO of data."""
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=io.BytesIO(json.dumps(data).encode()))
    cm.__exit__ = MagicMock(return_value=False)
    return cm


class TestLoadApiKey(unittest.TestCase):
    @patch("yt_api.Path")
    def test_reads_from_env_file(self, mock_path_cls):
        mock_env = MagicMock()
        mock_path_cls.return_value = mock_env
        mock_env.exists.return_value = True
        mock_env.read_text.return_value = "YOUTUBE_API_KEY=key_from_file\n"

        key = yt_api.load_api_key()
        self.assertEqual(key, "key_from_file")

    @patch("yt_api.Path")
    @patch.dict(os.environ, {"YOUTUBE_API_KEY": "key_from_env"})
    def test_reads_from_environment(self, mock_path_cls):
        mock_path_cls.return_value.exists.return_value = False

        key = yt_api.load_api_key()
        self.assertEqual(key, "key_from_env")

    @patch("yt_api.Path")
    def test_exits_when_key_missing(self, mock_path_cls):
        mock_path_cls.return_value.exists.return_value = False
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("YOUTUBE_API_KEY", None)
            with self.assertRaises(SystemExit):
                yt_api.load_api_key()

    @patch("yt_api.Path")
    def test_env_file_key_without_newline(self, mock_path_cls):
        mock_env = MagicMock()
        mock_path_cls.return_value = mock_env
        mock_env.exists.return_value = True
        mock_env.read_text.return_value = "OTHER=val\nYOUTUBE_API_KEY=abc123"

        key = yt_api.load_api_key()
        self.assertEqual(key, "abc123")


class TestFetchChannel(unittest.TestCase):
    @patch("yt_api.urllib.request.urlopen")
    def test_returns_first_item(self, mock_urlopen):
        item = {"id": "UC123", "snippet": {"title": "Test Channel"}}
        mock_urlopen.return_value = _urlopen_mock({"items": [item]})

        result = yt_api.fetch_channel("fake_key", id="UC123")
        self.assertEqual(result, item)

    @patch("yt_api.urllib.request.urlopen")
    def test_returns_empty_dict_when_no_items(self, mock_urlopen):
        mock_urlopen.return_value = _urlopen_mock({"items": []})

        result = yt_api.fetch_channel("fake_key", id="UC_missing")
        self.assertEqual(result, {})

    @patch("yt_api.urllib.request.urlopen")
    def test_passes_params_correctly(self, mock_urlopen):
        mock_urlopen.return_value = _urlopen_mock({"items": []})

        yt_api.fetch_channel("my_key", forHandle="TestHandle")

        called_url = mock_urlopen.call_args[0][0]
        self.assertIn("forHandle=TestHandle", called_url)
        self.assertIn("key=my_key", called_url)
        self.assertIn("part=snippet", called_url)


class TestResolveChannel(unittest.TestCase):
    @patch("yt_api.fetch_channel")
    def test_channel_url_format(self, mock_fetch):
        channel_id = "UCX6OQ3DkcsbYNE6H8uQQuVA"
        mock_fetch.return_value = {"id": channel_id, "snippet": {"title": "MrBeast"}}

        cid, title = yt_api.resolve_channel(
            f"https://www.youtube.com/channel/{channel_id}", "fake_key"
        )
        self.assertEqual(cid, channel_id)
        self.assertEqual(title, "MrBeast")

    @patch("yt_api.fetch_channel")
    def test_handle_url_format(self, mock_fetch):
        mock_fetch.return_value = {
            "id": "UCabc",
            "snippet": {"title": "Handle Channel"},
        }

        cid, title = yt_api.resolve_channel(
            "https://www.youtube.com/@SomeHandle", "fake_key"
        )
        self.assertEqual(cid, "UCabc")
        self.assertEqual(title, "Handle Channel")
        mock_fetch.assert_called_once_with("fake_key", forHandle="SomeHandle")

    @patch("yt_api.fetch_channel")
    def test_custom_c_url_format(self, mock_fetch):
        mock_fetch.return_value = {
            "id": "UCdef",
            "snippet": {"title": "Custom Channel"},
        }

        cid, title = yt_api.resolve_channel(
            "https://www.youtube.com/c/CustomName", "fake_key"
        )
        self.assertEqual(cid, "UCdef")
        mock_fetch.assert_called_once_with("fake_key", forUsername="CustomName")

    @patch("yt_api.fetch_channel")
    def test_user_url_format(self, mock_fetch):
        mock_fetch.return_value = {
            "id": "UCghi",
            "snippet": {"title": "User Channel"},
        }

        cid, _ = yt_api.resolve_channel(
            "https://www.youtube.com/user/OldUsername", "fake_key"
        )
        self.assertEqual(cid, "UCghi")
        mock_fetch.assert_called_once_with("fake_key", forUsername="OldUsername")

    @patch("yt_api.fetch_channel")
    def test_handle_not_found_exits(self, mock_fetch):
        mock_fetch.return_value = {}

        with self.assertRaises(SystemExit):
            yt_api.resolve_channel("https://www.youtube.com/@Ghost", "fake_key")

    def test_unrecognized_url_exits(self):
        with self.assertRaises(SystemExit):
            yt_api.resolve_channel("https://www.youtube.com/watch?v=abc123", "fake_key")

    @patch("yt_api.fetch_channel")
    def test_trailing_slash_is_ignored(self, mock_fetch):
        channel_id = "UCX6OQ3DkcsbYNE6H8uQQuVA"
        mock_fetch.return_value = {"id": channel_id, "snippet": {"title": "Chan"}}

        cid, _ = yt_api.resolve_channel(
            f"https://www.youtube.com/channel/{channel_id}/", "fake_key"
        )
        self.assertEqual(cid, channel_id)


if __name__ == "__main__":
    unittest.main()
