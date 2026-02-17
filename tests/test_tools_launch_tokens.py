"""
Unit tests for claw_swarm.tools.launch_tokens.
"""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import httpx
import pytest

from claw_swarm.tools import launch_tokens


class TestGetPrivateKey:
    """Test _get_private_key."""

    def test_raises_when_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="WALLET_PRIVATE_KEY"
            ):
                launch_tokens._get_private_key()

    def test_raises_when_empty_string(self):
        with patch.dict(
            os.environ, {"WALLET_PRIVATE_KEY": "   "}, clear=False
        ):
            with pytest.raises(
                ValueError, match="WALLET_PRIVATE_KEY"
            ):
                launch_tokens._get_private_key()

    def test_returns_stripped_value(self):
        with patch.dict(
            os.environ,
            {"WALLET_PRIVATE_KEY": "  mykey  "},
            clear=False,
        ):
            assert launch_tokens._get_private_key() == "mykey"


class TestGetApiKey:
    """Test _get_api_key."""

    def test_raises_when_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="SWARMS_API_KEY"):
                launch_tokens._get_api_key()

    def test_returns_stripped_value(self):
        with patch.dict(
            os.environ, {"SWARMS_API_KEY": "  apikey  "}, clear=False
        ):
            assert launch_tokens._get_api_key() == "apikey"


class TestLaunchToken:
    """Test launch_token (with mocked httpx)."""

    def test_posts_to_launch_endpoint(self):
        resp = httpx.Response(
            200, json={"success": True, "id": "123"}
        )
        with patch.object(httpx.Client, "post", return_value=resp):
            with patch.object(
                launch_tokens, "_get_private_key", return_value="pk"
            ):
                with patch.object(
                    launch_tokens, "_get_api_key", return_value="ak"
                ):
                    result = launch_tokens.launch_token(
                        name="Agent",
                        description="Desc",
                        ticker="TKR",
                    )
        data = json.loads(result)
        assert data["success"] is True
        assert data["id"] == "123"

    def test_includes_image_when_provided(self):
        resp = httpx.Response(200, json={"success": True})
        with patch.object(
            httpx.Client, "post", return_value=resp
        ) as mock_post:
            with patch.object(
                launch_tokens, "_get_private_key", return_value="pk"
            ):
                with patch.object(
                    launch_tokens, "_get_api_key", return_value="ak"
                ):
                    launch_tokens.launch_token(
                        name="A",
                        description="D",
                        ticker="T",
                        image="https://example.com/img.png",
                    )
        call_json = mock_post.call_args[1]["json"]
        assert "image" in call_json
        assert call_json["image"] == "https://example.com/img.png"

    def test_raises_on_http_error(self):
        with patch.object(
            httpx.Client,
            "post",
            side_effect=httpx.HTTPStatusError(
                "err",
                request=MagicMock(),
                response=MagicMock(status_code=500),
            ),
        ):
            with patch.object(
                launch_tokens, "_get_private_key", return_value="pk"
            ):
                with patch.object(
                    launch_tokens, "_get_api_key", return_value="ak"
                ):
                    with pytest.raises(httpx.HTTPStatusError):
                        launch_tokens.launch_token("A", "D", "T")


class TestClaimFees:
    """Test claim_fees (with mocked httpx)."""

    def test_posts_ca_and_private_key(self):
        resp = httpx.Response(
            200, json={"success": True, "signature": "sig"}
        )
        with patch.object(
            httpx.Client, "post", return_value=resp
        ) as mock_post:
            with patch.object(
                launch_tokens, "_get_private_key", return_value="pk"
            ):
                result = launch_tokens.claim_fees(
                    "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
                )
        data = json.loads(result)
        assert data["success"] is True
        call_json = mock_post.call_args[1]["json"]
        assert (
            call_json["ca"]
            == "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
        )
        assert call_json["privateKey"] == "pk"

    def test_raises_on_http_error(self):
        with patch.object(
            httpx.Client,
            "post",
            side_effect=httpx.HTTPStatusError(
                "err",
                request=MagicMock(),
                response=MagicMock(status_code=400),
            ),
        ):
            with patch.object(
                launch_tokens, "_get_private_key", return_value="pk"
            ):
                with pytest.raises(httpx.HTTPStatusError):
                    launch_tokens.claim_fees("ca_address")
