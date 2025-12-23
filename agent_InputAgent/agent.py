from summoner.client import SummonerClient
from multi_ainput import multi_ainput
from aioconsole import ainput, aprint
from typing import Any
import argparse, json

# ---- CLI: prompt mode toggle -----------------------------------------------
prompt_parser = argparse.ArgumentParser()
prompt_parser.add_argument("--multiline", required=False, type=int, choices=[0, 1], default=0, help="Use multi-line input mode with backslash continuation (1 = enabled, 0 = disabled). Default: 0.")
prompt_args, _ = prompt_parser.parse_known_args()

client = SummonerClient(name="InputAgent")

@client.receive(route="")
async def receiver_handler(msg: Any) -> None:
    # Extract content from dict payloads, or use the raw message as-is.
    content = (msg["content"] if isinstance(msg, dict) and "content" in msg else msg)
    addr    = (msg.get("remote_addr") if isinstance(msg, dict) else "unknown")

    # Choose a display tag. This is visual only; it does not affect routing.
    tag = ("\r[From server]" if isinstance(content, str) and content[:len("Warning:")] == "Warning:" else "\r[Received]")

    max_len = 200
    if isinstance(content, dict):
        details = "\n".join(
            f"  \033[93m{k}\033[0m: \033[90m{str(v)[:max_len]}{'...' if len(str(v)) > max_len else ''}\033[0m"
            for k, v in content.items()
        )
    else:
        content_str = str(content)
        details = "\033[90m" + content_str[:max_len] + ("..." if len(content_str) > max_len else "") + "\033[0m"

    await aprint(f"\033[95m{tag}\033[0m Sent by \033[96m{addr}\033[0m:\n{details}")
    await aprint("> ", end="")

@client.send(route="")
async def send_handler() -> str:
    if bool(int(prompt_args.multiline)):
        # Multi-line compose with continuation and echo cleanup.
        content: str = await multi_ainput("> ", "~ ", "\\")
    else:
        # Single-line compose.
        content: str = await ainput("> ")

    strip = content.strip()

    if strip == "/test":
        return {
        "rendered": (
            "\x1b[1;34mScenario 7c3a1f9d2b10\x1b[0m\n\n"
            "\x1b[1;35mContext:\x1b[0m\n"
            "A procurement lead at a consumer-goods company must redesign part of the supply chain to improve sustainability while maintaining delivery reliability. The situation is defined by these facts: "
            "1) The company committed to cut Scope 3 supply-chain emissions by 20% within 24 months. "
            "2) A budget of $300,000 is available this year for supplier and logistics improvements. "
            "3) 55% of inbound shipments currently use air freight during seasonal peaks. "
            "4) Customer contracts now require quarterly sustainability reporting, and 2 key customers threaten to churn if reporting quality does not improve. "
            "5) Unit costs increased by 8% year-over-year due to fuel volatility and expedited shipping. "
            "6) The supplier base is fragmented: 40% of spend is with vendors lacking any verified environmental data. "
            "7) Internally, finance demands cost containment, while sales prioritizes on-time delivery above all else. "
            "8) The team must present measurable progress in 90 days and a scalable plan within 6 months. "
            "Two subtle constraints apply: reducing air freight too aggressively can break service levels, while improving reporting without operational changes risks accusations of greenwashing.\n\n"
            "\x1b[1;33mQuestions:\x1b[0m\n\n"
            "\x1b[1;36mQ4127\x1b[0m \x1b[32m[21 pts]\x1b[0m Assume the company must quickly reduce supply-chain emissions without harming delivery performance. What action should the procurement lead take first to align goals, budget, and operational constraints?\n"
            "\x1b[1;36mQ0951\x1b[0m \x1b[32m[21 pts]\x1b[0m Assume external reporting requirements tighten next quarter. What action should the team take to produce auditable supplier emissions data with minimal disruption?\n"
            "\x1b[1;36mQ6380\x1b[0m \x1b[32m[21 pts]\x1b[0m Assume air freight is the largest controllable emissions driver. What decision framework should be used to determine which lanes can shift to ocean/ground while preserving service levels?\n"
            "\x1b[1;36mQ2204\x1b[0m \x1b[32m[20 pts]\x1b[0m Assume some suppliers cannot provide verified sustainability metrics. What supplier management steps should the procurement lead implement to improve coverage and data quality?\n"
            "\x1b[1;36mQ7719\x1b[0m \x1b[32m[19 pts]\x1b[0m Assume finance blocks additional spend beyond the current budget. What resource-allocation priorities should be set to achieve measurable emissions reduction within 90 days?\n"
            "\x1b[1;36mQ5043\x1b[0m \x1b[32m[19 pts]\x1b[0m Assume customers demand transparency about logistics emissions. What actions should the company take to improve lane-level traceability and reporting credibility?\n"
            "\x1b[1;36mQ8872\x1b[0m \x1b[32m[19 pts]\x1b[0m Assume on-time delivery remains the top KPI for sales. What governance mechanism should be introduced so sustainability changes do not degrade service performance?\n"
            "\x1b[1;36mQ1608\x1b[0m \x1b[32m[19 pts]\x1b[0m Assume the supplier base is fragmented and risk is concentrated in peak season. What structural change should be made to improve resilience and sustainability simultaneously?\n"
            "\x1b[1;36mQ3095\x1b[0m \x1b[32m[18 pts]\x1b[0m Assume the organization wants to leverage technology to improve supply-chain sustainability. What specific technology-enabled capability should be deployed first and why?\n"
            "\x1b[1;36mQ9413\x1b[0m \x1b[32m[18 pts]\x1b[0m Assume regulators introduce a due-diligence requirement for environmental and labor risk in the supply chain. What actions should the procurement lead take to prepare and reduce exposure?\n"
        ),
        "raw": {
            "scenario_id": "7c3a1f9d2b10",
            "scenario": (
            "A procurement lead at a consumer-goods company must redesign part of the supply chain to improve sustainability while maintaining delivery reliability. "
            "The situation is defined by these facts: 1) The company committed to cut Scope 3 supply-chain emissions by 20% within 24 months. "
            "2) A budget of $300,000 is available this year for supplier and logistics improvements. "
            "3) 55% of inbound shipments currently use air freight during seasonal peaks. "
            "4) Customer contracts now require quarterly sustainability reporting, and 2 key customers threaten to churn if reporting quality does not improve. "
            "5) Unit costs increased by 8% year-over-year due to fuel volatility and expedited shipping. "
            "6) The supplier base is fragmented: 40% of spend is with vendors lacking any verified environmental data. "
            "7) Internally, finance demands cost containment, while sales prioritizes on-time delivery above all else. "
            "8) The team must present measurable progress in 90 days and a scalable plan within 6 months. "
            "Two subtle constraints apply: reducing air freight too aggressively can break service levels, while improving reporting without operational changes risks accusations of greenwashing."
            ),
            "questions": {
            "Q4127": "Assume the company must quickly reduce supply-chain emissions without harming delivery performance. What action should the procurement lead take first to align goals, budget, and operational constraints?",
            "Q0951": "Assume external reporting requirements tighten next quarter. What action should the team take to produce auditable supplier emissions data with minimal disruption?",
            "Q6380": "Assume air freight is the largest controllable emissions driver. What decision framework should be used to determine which lanes can shift to ocean/ground while preserving service levels?",
            "Q2204": "Assume some suppliers cannot provide verified sustainability metrics. What supplier management steps should the procurement lead implement to improve coverage and data quality?",
            "Q7719": "Assume finance blocks additional spend beyond the current budget. What resource-allocation priorities should be set to achieve measurable emissions reduction within 90 days?",
            "Q5043": "Assume customers demand transparency about logistics emissions. What actions should the company take to improve lane-level traceability and reporting credibility?",
            "Q8872": "Assume on-time delivery remains the top KPI for sales. What governance mechanism should be introduced so sustainability changes do not degrade service performance?",
            "Q1608": "Assume the supplier base is fragmented and risk is concentrated in peak season. What structural change should be made to improve resilience and sustainability simultaneously?",
            "Q3095": "Assume the organization wants to leverage technology to improve supply-chain sustainability. What specific technology-enabled capability should be deployed first and why?",
            "Q9413": "Assume regulators introduce a due-diligence requirement for environmental and labor risk in the supply chain. What actions should the procurement lead take to prepare and reduce exposure?"
            },
            "points": {
            "Q4127": 21,
            "Q0951": 21,
            "Q6380": 21,
            "Q2204": 20,
            "Q7719": 19,
            "Q5043": 19,
            "Q8872": 19,
            "Q1608": 19,
            "Q3095": 18,
            "Q9413": 18
            }
        },
        "from": "b1f9a2d3f7e84b12a6d9c0e1aa44c8f0"
        }

    # Parse as JSON if possible; otherwise, return the raw string
    output = None
    try:
        output = json.loads(content.replace("\n", ""))
    except:
        output = content
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a Summoner client with a specified config.")
    parser.add_argument('--config', dest='config_path', required=False, help='The relative path to the config file (JSON) for the client (e.g., --config configs/client_config.json)')
    args, _ = parser.parse_known_args()

    client.run(host="127.0.0.1", port=8888, config_path=args.config_path or "configs/client_config.json")
