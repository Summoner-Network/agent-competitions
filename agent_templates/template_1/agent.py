import warnings
warnings.filterwarnings("ignore", message=r".*supports OpenSSL.*LibreSSL.*")

import asyncio
import argparse
import json
import os
from typing import Any, Optional, Union
from aioconsole import aprint

from openai import AsyncOpenAI
from dotenv import load_dotenv
load_dotenv()

from summoner.client import SummonerClient
from summoner.protocol import Direction, Event, Stay, Action

# -----------------------------------------------------------------------------
# Minimal config
# -----------------------------------------------------------------------------
AGENT_ID = "minimal_agent"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# One queue: receive handler buffers payloads, send handler consumes them.
message_buffer: Optional[asyncio.Queue] = None
buffer_lock: Optional[asyncio.Lock] = None

# OpenAI client (direct, no wrappers)
open_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


async def setup() -> None:
    global message_buffer, buffer_lock
    message_buffer = asyncio.Queue()
    buffer_lock = asyncio.Lock()


# -----------------------------------------------------------------------------
# Summoner client + flow
# -----------------------------------------------------------------------------
agent = SummonerClient(name="MinimalAgent")
flow = agent.flow().activate()
Trigger = flow.triggers()


# -----------------------------------------------------------------------------
# State upload/download (minimal)
# -----------------------------------------------------------------------------
@agent.upload_states()
async def upload_states(_: Any) -> list[str]:
    return ["message"]


# -----------------------------------------------------------------------------
# Hooks (minimal)
# -----------------------------------------------------------------------------
@agent.hook(direction=Direction.RECEIVE)
async def validate_incoming(msg: Any) -> Optional[dict]:
    """
    Expect:
      msg = {"remote_addr": "...", "content": {...}}
    """
    if not (isinstance(msg, dict) and "remote_addr" in msg and "content" in msg):
        return None
    return msg


@agent.hook(direction=Direction.SEND)
async def add_sender_id(payload: Any) -> Optional[dict]:
    """
    Normalize outgoing payload to a dict and attach a stable sender id.
    """
    if isinstance(payload, str):
        payload = {"message": payload}
    if not isinstance(payload, dict):
        return None
    payload["from"] = AGENT_ID
    return payload


# -----------------------------------------------------------------------------
# Receive handler: buffer the message
# -----------------------------------------------------------------------------
@agent.receive(route="message")
async def recv_message(msg: Any) -> Event:
    assert message_buffer is not None
    content = msg["content"]

    # Buffer raw payload; the send handler will decide what to do with it.
    await message_buffer.put(content)
    return Stay(Trigger.ok)


# -----------------------------------------------------------------------------
# Send handler: pop one buffered message and call OpenAI directly
# -----------------------------------------------------------------------------
@agent.send(route="message", on_actions={Action.STAY}, on_triggers={Trigger.ok})
async def send_message() -> Optional[Union[dict, str]]:
    assert message_buffer is not None
    assert buffer_lock is not None

    if message_buffer.empty():
        await asyncio.sleep(0.05)
        return None

    async with buffer_lock:
        if message_buffer.empty():
            return None
        incoming = message_buffer.get_nowait()

    try:
        # -------------------------------
        # Put your "direct dummy project" here.
        # Users should edit ONLY this block.
        # -------------------------------
        user_prompt = (
            "You are a minimal agent.\n\n"
            "Incoming Summoner payload (JSON):\n"
            f"{json.dumps(incoming, ensure_ascii=False, indent=2)}\n\n"
            "Task: Find and address all implicit requests suggested by any 'questions', 'question', 'message' key in the payload. "
            "Keep your response JSON structure consistent with these requests. "
            "Any other Extra information in the request payload should ONLY be used for context to respond to the request, and should NOT repeated in your answer. "
        )
        await aprint(user_prompt)

        resp = await open_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an assistant helping other agents with their requests."},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        text = (resp.choices[0].message.content or "").strip()
        try:
            answers = json.loads(text)
        except:
            answers = text
        
        await aprint(f"\033[34m{json.dumps(answers, indent=2)}\033[34m")

        # Minimal reply envelope (keep routing fields if present).
        out: dict[str, Any] = {"answers": answers}

        # Common Summoner convention: reply to incoming["from"] when present.
        if isinstance(incoming, dict) and "from" in incoming:
            out["to"] = incoming["from"]

        return out

    finally:
        # Mark task done for queue hygiene.
        try:
            message_buffer.task_done()
        except Exception:
            pass


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minimal Summoner agent template.")
    parser.add_argument(
        "--config",
        dest="config_path",
        required=False,
        default="configs/client_config.json",
        help="Path to Summoner client config JSON.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8888, type=int)
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing in the environment.")

    agent.loop.run_until_complete(setup())
    agent.run(host=args.host, port=args.port, config_path=args.config_path)
