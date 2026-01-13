import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session

from support_bot import handle_user_query

load_dotenv()

DEFAULT_MAX_MESSAGES = 30
DEFAULT_MAX_MESSAGE_CHARS = 2000


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default

# maximum character limit
def _truncate(text: str, limit: int) -> str:
    if text is None:
        return ""
    text = str(text)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"


def _get_chat() -> list[dict]:
    chat = session.get("chat")
    if not isinstance(chat, list):
        chat = []
        session["chat"] = chat
    return chat

# appends message to session chat history , max of messages 
def _append_message(msg: dict) -> None:
    chat = _get_chat()
    chat.append(msg)

    max_messages = _get_int_env("CHAT_MAX_MESSAGES", DEFAULT_MAX_MESSAGES)
    if max_messages > 0 and len(chat) > max_messages:
        session["chat"] = chat[-max_messages:]


def create_app() -> Flask:
    # Get the directory where this file is located
    web_dir = Path(__file__).parent
    
    app = Flask(
        __name__,
        template_folder=str(web_dir / "templates"),
        static_folder=str(web_dir / "static"),
    )

    # Session cookie signing key.
    # For local dev only: fallback to a constant if not set.
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")

    @app.get("/")
    def index():
        chat = _get_chat()
        return render_template("index.html", chat=chat)
    
# receives user input, cleans it, stores it in session, calls handler, returns bot reply
    @app.post("/api/chat") 
    def api_chat():
        payload = request.get_json(silent=True) or {}
        message = payload.get("message", "")
        debug = bool(payload.get("debug", False))

        max_chars = _get_int_env("CHAT_MAX_MESSAGE_CHARS", DEFAULT_MAX_MESSAGE_CHARS)
        message = _truncate(message, max_chars).strip()

        if not message:
            return jsonify({"ok": False, "error": "Message is empty."}), 400

        try:
            # Multi-turn UX enhancement (legacy):
            # Previously we asked users if they wanted to see other matches.
            # We now show all matches immediately, so disable this flow.
            pending = []
            pending_language = None
            if False and isinstance(pending, list) and pending:
                normalized = (message or "").strip().lower()
                yes_set = {"yes", "y", "yeah", "yep", "ok", "okay", "sure", "да", "добре", "ок", "давай"}
                no_set = {"no", "n", "nope", "не", "не благодаря"}

                if normalized in yes_set:
                    session.pop("pending_product_matches", None)
                    session.pop("pending_product_matches_language", None)

                    lines: list[str] = []
                    for p in pending:
                        if not isinstance(p, dict):
                            continue
                        if pending_language == "bg":
                            name = p.get("name_bg") or p.get("name") or ""
                        else:
                            name = p.get("name") or p.get("name_bg") or ""
                        price = p.get("price")
                        lines.append(f"{name} — ${price}")

                    if pending_language == "bg":
                        reply = (
                            "Ето и другите съвпадения: " + " | ".join(lines)
                            if lines
                            else "Ето и другите съвпадения."
                        )
                    else:
                        reply = "Here are the other matches: " + " | ".join(lines) if lines else "Here are the other matches."

                    _append_message({"role": "user", "text": message, "ts": _utc_iso()})
                    _append_message({"role": "bot", "text": reply, "ts": _utc_iso()})
                    return jsonify({"ok": True, "reply": reply})

                if normalized in no_set:
                    session.pop("pending_product_matches", None)
                    session.pop("pending_product_matches_language", None)

                    reply = (
                        "Ок — мога ли да помогна с нещо друго?"
                        if pending_language == "bg"
                        else "Ok — can I help you with something else?"
                    )
                    _append_message({"role": "user", "text": message, "ts": _utc_iso()})
                    _append_message({"role": "bot", "text": reply, "ts": _utc_iso()})
                    return jsonify({"ok": True, "reply": reply})

                # If it's not an obvious yes/no, fall through and treat it as a new query.

            _append_message({"role": "user", "text": message, "ts": _utc_iso()})

            if debug:
                reply, dbg = handle_user_query(message, debug=True)
                _append_message({"role": "bot", "text": reply, "ts": _utc_iso(), "debug": dbg})

                # Store follow-up matches for next turn (web only).
                matches = dbg.get("pending_product_matches") if isinstance(dbg, dict) else None
                if isinstance(matches, list) and matches:
                    session["pending_product_matches"] = matches
                    # Best-effort: infer language from the last tool call args.
                    lang = None
                    tools = dbg.get("tools_called") if isinstance(dbg, dict) else None
                    if isinstance(tools, list):
                        for t in tools:
                            if isinstance(t, dict) and t.get("name") == "file_search_products":
                                args = t.get("args")
                                if isinstance(args, dict):
                                    lang = args.get("language")
                    if lang in ("en", "bg"):
                        session["pending_product_matches_language"] = lang

                return jsonify({"ok": True, "reply": reply, "debug": dbg})

            reply = handle_user_query(message)
            _append_message({"role": "bot", "text": reply, "ts": _utc_iso()})

            # Store follow-up matches for next turn (web only) even when debug is off.
            # We infer intent from the reply text, and re-run the agent with debug only when needed.
            if isinstance(reply, str) and (
                "Do you want to see the other matches?" in reply
                or "Искате ли да ги видите?" in reply
            ):
                try:
                    _reply_dbg, dbg = handle_user_query(message, debug=True)
                    matches = dbg.get("pending_product_matches") if isinstance(dbg, dict) else None
                    if isinstance(matches, list) and matches:
                        session["pending_product_matches"] = matches

                        # Best-effort: infer language from tool args.
                        lang = None
                        tools = dbg.get("tools_called") if isinstance(dbg, dict) else None
                        if isinstance(tools, list):
                            for t in tools:
                                if isinstance(t, dict) and t.get("name") == "file_search_products":
                                    args = t.get("args")
                                    if isinstance(args, dict):
                                        lang = args.get("language")
                        if lang in ("en", "bg"):
                            session["pending_product_matches_language"] = lang

                    # Mark session as changed so Flask reliably persists these keys.
                    session.modified = True
                except Exception as e:
                    # Non-fatal: follow-up UX is best-effort.
                    print("[api_chat] follow-up capture failed:", e)

            return jsonify({"ok": True, "reply": reply})

        except Exception as e:
            return jsonify({"ok": False, "error": f"Server error: {e}"}), 500


# clears chat history stored in session

    @app.post("/api/clear")
    def api_clear():
        session["chat"] = []
        session.pop("pending_product_matches", None)
        session.pop("pending_product_matches_language", None)
        return jsonify({"ok": True})

    return app


if __name__ == "__main__":
    app = create_app()

    host = os.getenv("HOST", "127.0.0.1")
    port = _get_int_env("PORT", 5000)
    debug = os.getenv("FLASK_DEBUG", "").strip() == "1"

    app.run(host=host, port=port, debug=debug)
