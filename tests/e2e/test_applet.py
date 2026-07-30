from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page, expect


def _ready(page: Page, app_url: str) -> None:
    page.goto(app_url)
    expect(page.locator("#runtime-status")).to_have_attribute(
        "data-state",
        "ready",
        timeout=120_000,
    )


def test_worker_loads_and_calculates(page: Page, app_url: str) -> None:
    _ready(page, app_url)

    page.locator("#calculate").click()

    expect(page.locator("#runtime-status")).to_have_text("Calculation complete.")
    expect(page.locator("#result-summary")).to_contain_text("2 + 3 = 5")
    expect(page.locator("#result-table tbody tr")).to_have_count(3)
    expect(page.locator("#plot .plot-container")).to_be_visible()
    expect(page.locator("#runtime-versions")).to_contain_text("0.1.0")


def test_validation_error_and_worker_recovery(page: Page, app_url: str) -> None:
    _ready(page, app_url)
    page.locator("#first-value").fill("1e308")
    page.locator("#second-value").fill("1e308")
    page.locator("#calculate").click()

    expect(page.locator("#error-summary")).to_contain_text("total must be finite")
    expect(page.locator("#runtime-status")).to_have_attribute("data-state", "error")

    page.locator("#first-value").fill("4")
    page.locator("#second-value").fill("6")
    page.locator("#calculate").click()

    expect(page.locator("#runtime-status")).to_have_text("Calculation complete.")
    expect(page.locator("#result-summary")).to_contain_text("4 + 6 = 10")


def test_input_errors_link_to_controls(page: Page, app_url: str) -> None:
    _ready(page, app_url)
    page.locator("#first-value").fill("")
    page.locator("#calculate").click()

    expect(page.locator("#error-summary")).to_be_visible()
    expect(page.locator("#error-summary a")).to_have_attribute("href", "#first-value")
    expect(page.locator("#first-value")).to_have_attribute("aria-invalid", "true")


def test_csv_png_and_caption_exports(page: Page, app_url: str, tmp_path: Path) -> None:
    page.context.grant_permissions(
        ["clipboard-read", "clipboard-write"], origin=app_url.rstrip("/")
    )
    _ready(page, app_url)
    page.locator("#calculate").click()
    expect(page.locator("#runtime-status")).to_have_text("Calculation complete.")

    with page.expect_download() as csv_info:
        page.locator("#export-csv").click()
    csv_download = csv_info.value
    csv_path = tmp_path / csv_download.suggested_filename
    csv_download.save_as(csv_path)
    assert csv_path.read_bytes() == (
        b"Label,Value\r\nFirst value,2\r\nSecond value,3\r\nDemonstration total,5\r\n"
    )

    for selector, suffix in [
        ("#export-figure", "-figure.png"),
        ("#export-dashboard", "-dashboard.png"),
    ]:
        with page.expect_download(timeout=30_000) as png_info:
            page.locator(selector).click()
        download = png_info.value
        png_path = tmp_path / download.suggested_filename
        download.save_as(png_path)
        assert download.suggested_filename.endswith(suffix)
        assert png_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    page.locator("#copy-caption").click()
    expect(page.locator("#runtime-status")).to_have_text("Caption copied.")
    clipboard = page.evaluate("navigator.clipboard.readText()")
    assert "does not implement a scientific method" in clipboard


def test_mobile_keyboard_and_privacy_smoke(page: Page, app_url: str) -> None:
    requests: list[tuple[str, str | None]] = []
    page.context.on("request", lambda request: requests.append((request.url, request.post_data)))
    page.set_viewport_size({"width": 390, "height": 844})
    _ready(page, app_url)
    initial_url = page.url
    page.locator("#first-value").fill("12345.67891")
    page.locator("#second-value").fill("2")
    page.locator("#first-value").focus()
    page.keyboard.press("Tab")
    expect(page.locator("#second-value")).to_be_focused()
    page.locator("#calculate").click()
    expect(page.locator("#runtime-status")).to_have_text("Calculation complete.")

    assert page.url == initial_url
    assert page.evaluate("localStorage.length") == 0
    assert page.evaluate("sessionStorage.length") == 0
    assert page.evaluate("document.cookie") == ""
    serialized_requests = "\n".join(f"{url}\n{body or ''}" for url, body in requests)
    assert "12345.67891" not in serialized_requests
    expect(page.locator(".controls")).to_be_visible()
    expect(page.locator(".results")).to_be_visible()
