import warnings
warnings.filterwarnings("ignore", message=r".*supports OpenSSL.*LibreSSL.*")

import asyncio
import argparse
import json
import os
from typing import Any, Optional, Union
from aioconsole import aprint

from openai import AsyncOpenAI
from openai.types.chat.chat_completion import ChatCompletion
from dotenv import load_dotenv
load_dotenv()

from summoner.client import SummonerClient
from summoner.protocol import Direction, Event, Stay, Action

# Hackathon safeguard (local file, same folder)
from safeguards import count_chat_tokens

# -----------------------------------------------------------------------------
# Minimal config
# -----------------------------------------------------------------------------
AGENT_ID = "minimal_agent"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Hackathon knob: hard cap on how many OpenAI calls we do per incoming payload.
MAX_OPENAI_CALLS = int(os.getenv("MAX_OPENAI_CALLS", "5"))  # set to 5 for this example

# -----------------------------------------------------------------------------
# HACKATHON RESTRICTIONS (DO NOT MODIFY)
# -----------------------------------------------------------------------------
# These are intentionally not exposed in the JSON config.
# If a step would exceed MAX_INPUT_TOKENS, we cancel the chain and return an error.
MAX_INPUT_TOKENS = 2000
MAX_OUTPUT_TOKENS = 600

# Prompts come from a JSON file (see dummy format below).
PROMPT_STEPS: list[dict] = []
DEFAULT_SYSTEM_PROMPT = "You are an assistant helping other agents with their requests."

# Which step outputs are packaged into out["answers"].
# If empty, we default to [last step].
OUTPUT_AGENTS: list[str] = []

# One queue: receive handler buffers payloads, send handler consumes them.
message_buffer: Optional[asyncio.Queue] = None
buffer_lock: Optional[asyncio.Lock] = None

# OpenAI client (direct, no wrappers)
openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def sanitize_model(maybe_model: Any) -> str:
    """
    Hackathon restriction:
      - Only 'gpt-4o-mini' or 'gpt-4o' allowed.
      - Any other value becomes 'gpt-4o-mini'.
    """
    if maybe_model in ("gpt-4o-mini", "gpt-4o"):
        return maybe_model
    return "gpt-4o-mini"


def normalize_response_format(value: Any) -> str:
    """
    Hackathon-friendly:
      - Users choose 'json' or 'text'.
      - Anything else defaults to 'json'.
    """
    if value == "text":
        return "text"
    return "json"


def select_incoming_by_path(incoming: Any, path: str) -> Any:
    """
    Minimal dotted-path selector for hackathon configs.
    Examples:
      "raw" -> incoming["raw"]
      "raw.questions" -> incoming["raw"]["questions"]
    Missing path returns None.
    """
    cur = incoming
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def render_block(obj: Any) -> str:
    """Render injected blocks in a prompt-friendly way."""
    if obj is None:
        return ""
    if isinstance(obj, (dict, list)):
        return json.dumps(obj, ensure_ascii=False, indent=2)
    return str(obj)


async def setup(steps_path: str) -> None:
    global message_buffer, buffer_lock, PROMPT_STEPS, DEFAULT_SYSTEM_PROMPT, OUTPUT_AGENTS
    message_buffer = asyncio.Queue()
    buffer_lock = asyncio.Lock()

    # Hackathon participants: edit ONLY the JSON file, not the code.
    # JSON cannot contain comments, so we keep guidance here in Python.
    with open(steps_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    PROMPT_STEPS = cfg.get("steps", []) or []
    DEFAULT_SYSTEM_PROMPT = cfg.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
    OUTPUT_AGENTS = cfg.get("output_agents", []) or []

    if not isinstance(PROMPT_STEPS, list):
        raise ValueError("'steps' must be a list in the steps JSON config.")
    if not isinstance(OUTPUT_AGENTS, list):
        raise ValueError("'output_agents' must be a list in the steps JSON config.")


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
# Send handler: pop one buffered message and run up to N OpenAI steps from JSON
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
        if not PROMPT_STEPS:
            raise RuntimeError("No steps loaded. Provide a valid --steps JSON config.")

        incoming_json = json.dumps(incoming, ensure_ascii=False, indent=2)

        # We keep ALL step outputs internally so later steps can depend on them.
        all_step_outputs: dict[str, Any] = {}

        # Hard cap: no more than MAX_OPENAI_CALLS calls.
        steps_to_run = PROMPT_STEPS[:MAX_OPENAI_CALLS]

        cancelled = False
        cancel_reason: Optional[dict[str, Any]] = None

        for i, step in enumerate(steps_to_run):
            name = step.get("name") or f"agent_{i+1}"

            prompt_intro = step.get("prompt_intro", "") or ""
            prompt_ending = step.get("prompt_ending", "") or ""
            include_spec = step.get("include_incoming", True)

            incoming_block = ""
            if include_spec is True:
                incoming_block = render_block(incoming)  # full payload (may be large)
            elif include_spec is False:
                incoming_block = ""
            elif isinstance(include_spec, str):
                incoming_block = render_block(select_incoming_by_path(incoming, include_spec))

            # Dependency payload joining: only previous agents count.
            deps = step.get("use_payload_from", []) or []
            joined_deps: list[str] = []
            if isinstance(deps, list):
                for dep_name in deps:
                    if dep_name in all_step_outputs:
                        dep_payload = all_step_outputs[dep_name]
                        if isinstance(dep_payload, (dict, list)):
                            joined_deps.append(json.dumps(dep_payload, ensure_ascii=False, indent=2))
                        else:
                            joined_deps.append(str(dep_payload))

            dep_block = "\n".join(joined_deps).strip()

            # Prompt is built ONLY from JSON fields + injected blocks.
            pieces: list[str] = []
            if prompt_intro.strip():
                pieces.append(prompt_intro.strip())
            if incoming_block.strip():
                pieces.append(incoming_block)
            if dep_block:
                pieces.append(dep_block)
            if prompt_ending.strip():
                pieces.append(prompt_ending.strip())
            user_prompt = "\n\n".join(pieces).strip()

            # Per-step knobs (some optional, but restricted where requested)
            system_prompt = step.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
            model = sanitize_model(step.get("model", MODEL))
            temperature = step.get("temperature", None)
            fmt = normalize_response_format(step.get("response_format", "json"))

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # -------------------------------
            # Hackathon input token guardrail
            # -------------------------------
            input_tokens = count_chat_tokens(messages, model=model)
            if input_tokens > MAX_INPUT_TOKENS:
                cancelled = True
                cancel_reason = {
                    "error": "max_input_tokens_exceeded",
                    "step": name,
                    "max_input_tokens": MAX_INPUT_TOKENS,
                    "actual_input_tokens": input_tokens,
                }
                all_step_outputs[name] = cancel_reason
                break

            await aprint(f"\n\033[36m=== STEP {i+1}: {name} ===\033[0m")
            await aprint(user_prompt)

            kwargs: dict[str, Any] = {"max_tokens": MAX_OUTPUT_TOKENS}  # hackathon output cap
            if temperature is not None:
                kwargs["temperature"] = float(temperature)

            # "json" -> request json_object, and we'll parse.
            # "text" -> no response_format, keep text.
            if fmt == "json":
                kwargs["response_format"] = {"type": "json_object"}

            resp: ChatCompletion = await openai_client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs,
            )

            text = (resp.choices[0].message.content or "").strip()

            parsed: Any = text
            if fmt == "json":
                try:
                    parsed = json.loads(text)
                except Exception:
                    parsed = {
                        "error": "invalid_json_from_model",
                        "raw_text": text,
                    }

            all_step_outputs[name] = parsed
            await aprint(f"\033[34m{json.dumps({name: parsed}, indent=2, ensure_ascii=False)}\033[0m")

        # -------------------------------
        # Packaging for hackathon output (MERGED)
        # -------------------------------
        # We merge outputs of output_agents into ONE dict:
        # - If an output agent returns a dict, we merge keys into answers.
        # - Key conflicts resolved by output_agents priority: FIRST one wins.
        # - If an output agent returns non-dict, we store it under its agent name
        #   (also respecting "first wins" if that name key already exists).
        if OUTPUT_AGENTS:
            output_names = [n for n in OUTPUT_AGENTS if isinstance(n, str)]
        else:
            last_name = (steps_to_run[-1].get("name") if steps_to_run else None) or f"agent_{len(steps_to_run)}"
            output_names = [last_name]

        answers: dict[str, Any] = {}
        for n in output_names:
            if n not in all_step_outputs:
                continue
            payload = all_step_outputs[n]

            if isinstance(payload, dict):
                for k, v in payload.items():
                    if k not in answers:   # first wins
                        answers[k] = v
            else:
                if n not in answers:       # first wins
                    answers[n] = payload

        out: dict[str, Any] = {"answers": answers}

        # Optional: expose cancellation info in a stable place (hackathon-friendly).
        if cancelled and cancel_reason is not None:
            out["cancelled"] = cancel_reason

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
    parser.add_argument(
        "--steps",
        dest="steps_path",
        required=False,
        default="configs/agent_steps.json",
        help="Path to prompt steps JSON (hackathon participants edit this).",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8888, type=int)
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing in the environment.")

    agent.loop.run_until_complete(setup(args.steps_path))
    agent.run(host=args.host, port=args.port, config_path=args.config_path)
