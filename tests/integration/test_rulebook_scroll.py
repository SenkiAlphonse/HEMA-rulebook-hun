"""Integration tests for rulebook jump-to-rule scrolling behavior."""

from __future__ import annotations

import socket
import threading

import pytest
from werkzeug.serving import make_server

from app import create_app


@pytest.fixture(scope="module")
def live_rulebook_server() -> str:
    """Run a temporary local server for browser-based integration testing."""
    app = create_app()
    app.config["TESTING"] = True

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    host, port = sock.getsockname()
    sock.close()

    server = make_server(host, port, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)


@pytest.fixture
def page():
    """Provide a Playwright page object, skipping if browser runtime is missing."""
    playwright_sync = pytest.importorskip(
        "playwright.sync_api",
        reason="Playwright is not installed; skipping browser scroll regression tests.",
    )
    sync_playwright = playwright_sync.sync_playwright
    PlaywrightError = playwright_sync.Error

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except PlaywrightError as exc:
            pytest.skip(f"Playwright browser runtime not available: {exc}")

        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()


@pytest.mark.integration
@pytest.mark.slow
def test_jump_to_rule_respects_sticky_header_offset(page, live_rulebook_server):
    """Jump-to-rule should align rule headers just below the sticky search bar."""
    page.goto(f"{live_rulebook_server}/rulebook?lang=hun")

    page.fill("#searchInput", "GEN-1")
    page.get_by_role("button", name="Jump to Rule").click()

    page.wait_for_function(
        """
        () => {
            const target = document.getElementById('GEN-1');
            const searchBox = document.querySelector('.search-box');
            if (!target || !searchBox) {
                return false;
            }
            const expectedOffset = Math.ceil(searchBox.getBoundingClientRect().height + 12);
            const actualTop = target.getBoundingClientRect().top;
            return Math.abs(actualTop - expectedOffset) <= 36;
        }
        """,
        timeout=5000,
    )

    measurement = page.evaluate(
        """
        () => {
            const target = document.getElementById('GEN-1');
            const searchBox = document.querySelector('.search-box');
            const expectedOffset = Math.ceil(searchBox.getBoundingClientRect().height + 12);
            const actualTop = target.getBoundingClientRect().top;
            return { expectedOffset, actualTop, diff: Math.abs(actualTop - expectedOffset) };
        }
        """
    )

    assert measurement["diff"] <= 36
