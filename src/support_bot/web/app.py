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

        _append_message({"role": "user", "text": message, "ts": _utc_iso()})

        try:
            if debug:
                reply, dbg = handle_user_query(message, debug=True)
                _append_message({"role": "bot", "text": reply, "ts": _utc_iso(), "debug": dbg})
                return jsonify({"ok": True, "reply": reply, "debug": dbg})

            reply = handle_user_query(message)
            _append_message({"role": "bot", "text": reply, "ts": _utc_iso()})
            return jsonify({"ok": True, "reply": reply})

        except Exception as e:
            return jsonify({"ok": False, "error": f"Server error: {e}"}), 500


# clears chat history stored in session

    @app.post("/api/clear")
    def api_clear():
        session["chat"] = []
        return jsonify({"ok": True})

    return app


if __name__ == "__main__":
    app = create_app()

    host = os.getenv("HOST", "127.0.0.1")
    port = _get_int_env("PORT", 5000)
    debug = os.getenv("FLASK_DEBUG", "").strip() == "1"

    app.run(host=host, port=port, debug=debug)
