from app.desktop.perception.ocr_fallback import build_ocr_fallback_request


def test_build_ocr_fallback_request_tracks_missing_fields_and_regions():
    request = build_ocr_fallback_request(
        missing_fields=["latest_customer_message", "product_title"],
        screenshot_path="tmp/jd_workspace.png",
        region_names=["chat_region", "product_region"],
    )

    assert request["ok"] is True
    assert request["missing_fields"] == ["latest_customer_message", "product_title"]
    assert request["region_names"] == ["chat_region", "product_region"]
    assert request["screenshot_path"] == "tmp/jd_workspace.png"
