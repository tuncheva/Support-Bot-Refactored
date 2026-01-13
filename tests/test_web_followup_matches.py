import os


def test_web_product_query_shows_all_matches_immediately():
    """Regression: product queries should list all matches in the initial reply (no follow-up)."""

    os.environ["PYTHONPATH"] = os.path.join(os.getcwd(), "src")

    from support_bot.web.app import create_app

    app = create_app()
    app.testing = True

    with app.test_client() as c:
        r1 = c.post("/api/chat", json={"message": "pro"})
        assert r1.status_code == 200
        j1 = r1.get_json() or {}
        assert j1.get("ok") is True

        reply1 = j1.get("reply") or ""

        # No follow-up prompt should exist anymore.
        assert "Do you want to see the other matches?" not in reply1

        # Should contain multiple product lines.
        assert reply1.count("Price:") >= 2
