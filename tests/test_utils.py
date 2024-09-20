"""Tests for nrk_psapi utils."""

from __future__ import annotations

import pytest
from aiohttp import ClientSession
from aresponses import ResponsesMockServer
from yarl import URL

from nrk_psapi.utils import fetch_file_info


@pytest.mark.asyncio
async def test_fetch_file_info(aresponses: ResponsesMockServer):
    url = "http://example.com/file"
    expected_content_length = "1234"
    expected_content_type = "application/octet-stream"

    aresponses.add(
        "example.com",
        "/file",
        "HEAD",
        aresponses.Response(
            headers={
                "Content-Length": expected_content_length,
                "Content-Type": expected_content_type,
            }
        ),
    )

    async with ClientSession() as session:
        content_length, content_type = await fetch_file_info(URL(url), session)

    assert content_length == int(expected_content_length)
    assert content_type == expected_content_type


@pytest.mark.asyncio
async def test_fetch_file_info_no_session(aresponses: ResponsesMockServer):
    url = "http://example.com/file"
    expected_content_length = "5678"
    expected_content_type = "text/plain"

    aresponses.add(
        "example.com",
        "/file",
        "HEAD",
        aresponses.Response(
            headers={
                "Content-Length": expected_content_length,
                "Content-Type": expected_content_type,
            }
        ),
    )

    content_length, content_type = await fetch_file_info(URL(url))

    assert content_length == int(expected_content_length)
    assert content_type == expected_content_type
