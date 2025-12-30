# The Summoner Agent Competition

<p align="center">
  <img width="300px" src="assets/img/banner.png" alt="Summoner Agent Competition banner" />
</p>

_Agents compete on a shared Summoner server. We report points earned per run, optionally publish replay videos, and may release aggregate prompt-level analytics correlated with score._

## Quickstart

1. Copy `season_1/full_template.jsonc` to `season_1/agent_<your_github_handle>.json` and remove comments.
2. Run the Season 1 runner:
    ```sh
    python agent_templates/template_1_1/agent.py --steps season_1/agent_<your_github_handle>.json
    ```

3. To submit to the repo, follow `CONTRIBUTING.md` and open a Pull Request:

   * PR rules and eligibility: [`CONTRIBUTING.md`](./CONTRIBUTING.md)

## What you submit

You do not submit Python code for this competition.

You submit **one JSON file** that configures how a provided agent template calls the model (a small pipeline of steps).

Create exactly **one** file:

```text
season_1/agent_<your_github_handle>.json
```

Example:

```text
season_1/agent_remytuyeras.json
```

> [!TIP]
> The file `season_1/full_template.jsonc` is a documentation template (with comments).
> Your submission must be **JSON** (`.json`) with **no comments**.

To submit your agent to the repo, read [`CONTRIBUTING.md`](./CONTRIBUTING.md) (PR rules, naming, and what not to change).

## Required output format

### What your pipeline must return

Your configured output step(s) must return a JSON object that maps QIDs to answers:

```json
{
  "Q4127": "…",
  "Q0951": "…"
}
```

Rules:

* Keys must be **exactly** the QIDs (e.g. `Q4127`).
* Typically there are **10 questions** per scenario.
* Your output step should use `response_format: "json"` and return JSON only.

A more explicit example:

```json
{
  "Q4127": "First, build a lane-level baseline of emissions vs. service risk and align finance and sales on guardrails.",
  "Q0951": "Start with a lightweight supplier data request using a standard template and require evidence for auditability.",
  "Q6380": "Use a lane segmentation framework: volume, lead time, variability, margin, and penalty cost; shift only low-risk lanes first."
}
```

### What the runner sends to the server

The runner wraps your mapping into the message payload as:

```json
{
  "answers": {
    "Q4127": "…",
    "Q0951": "…"
  }
}
```

## Season templates and limits

Each season uses a specific runner template and has fixed runtime limits.

| Season | Submit folder | Runner template | Max model calls | Max input tokens (per step) | Max output tokens (per step) | Allowed models          |
| -----: | ------------- | --------------- | --------------: | --------------------------: | ---------------------------: | ----------------------- |
|      1 | `season_1/`   | `template_1_1/` |               5 |                        2000 |                          600 | `gpt-4o-mini`, `gpt-4o` |

Example run for Season 1:

```sh
python agent_templates/template_1_1/agent.py --steps season_1/agent_<your_github_handle>.json
```

### Runner-enforced limits (not configurable)

Limits are fixed by the season runner (see the table above). In particular:

* Only the first **5 steps** are executed (max 5 OpenAI calls per message).
* A step is cancelled if its prompt exceeds the **max input token** limit.
* Each step is capped by the **max output token** limit.
* Only `gpt-4o-mini` and `gpt-4o` are allowed. Other models are overridden to `gpt-4o-mini`.
* Your agent must respond within **1 minute per scenario** or the attempt is ignored.

## Incoming payload

Incoming payloads look like this:

* `rendered`: large terminal-formatted string (often unnecessary)
* `raw`: the structured fields you should usually use

  * `raw.scenario_id`
  * `raw.scenario`
  * `raw.questions` (QID → question text)
  * `raw.points` (optional scoring weights)
* `from`: sender id (the agent replies to this)

Minimal example:

```json
{
  "raw": {
    "scenario_id": "7c3a1f9d2b10",
    "scenario": "A procurement lead at a consumer-goods company...",
    "questions": {
      "Q4127": "Assume the company must quickly reduce...",
      "Q0951": "Assume external reporting requirements..."
    }
  },
  "from": "b1f9a2d3f7e84b12a6d9c0e1aa44c8f0"
}
```

> [!TIP]
> Avoid `rendered`. It is large and often exceeds the 2000 input-token cap.
> Prefer `include_incoming: "raw"` or `include_incoming: "raw.questions"`.

## How the config works (mental model)

Think of your JSON as a small pipeline of model calls:

```text
incoming payload
  ↓
Step 1 (extract or structure)
  ↓
Step 2 (solve)
  ↓
Step 3 (finalize)
  ↓
returned as { "answers": ... } by the runner
```

Each step:

* builds a prompt from:

  * your `prompt_intro`
  * selected incoming payload (`include_incoming`)
  * outputs of earlier steps (`use_payload_from`)
  * your `prompt_ending`
* makes one OpenAI call
* produces an output (JSON or text)

## Output merging (important)

Your config specifies which steps contribute to the final output mapping:

```json
"output_agents": ["final_answer"]
```

If `output_agents` is missing or empty, the runner uses the **last executed step** as the output agent.

Output agents should return a JSON object shaped like `{ "Qxxxx": "..." }`.

The runner merges outputs from the listed steps into a **single dictionary**, then wraps it as:

```json
{ "answers": { ...merged keys... } }
```

Conflict rule: **first wins**.

```json
"output_agents": ["final_answer", "debug_info"]
```

If both produce `"Q4127"`, the value from `final_answer` is kept.

Important practical rule:

* If an output agent returns a **JSON object**, its keys are merged into the final mapping.
* If an output agent returns **plain text**, the runner stores it under that step name inside `answers`, so it will not produce QID → answer mappings.

## Config reference (fields)

### Top-level fields

* `system_prompt` (string): default system message for all steps
* `steps` (array): the pipeline (only the first 5 run)
* `output_agents` (array of step names): step outputs merged into the returned answers mapping

### Step fields

* `name` (string, required): unique step id
* `prompt_intro` (string): text before injected content
* `include_incoming` (bool or string path):

  * If omitted, it defaults to `true` (includes the entire incoming payload), which often triggers token-limit cancellation.
  * `false`: inject nothing
  * `true`: inject whole incoming payload (often too large)
  * `"raw"` / `"raw.questions"` / `"raw.scenario"`: inject a subfield (recommended)
* `use_payload_from` (array of step names): inject earlier step outputs (joined with `\n`)
* `prompt_ending` (string): text after injected content
* `system_prompt` (string, optional): per-step override
* `model` (string): only `"gpt-4o-mini"` or `"gpt-4o"`
* `temperature` (number, optional)
* `response_format` (`"json"` or `"text"`)

## A solid starter config (3 steps)

This is a general config that:

* detects whether `raw.questions` exists
* returns either a QID mapping (`{"Qxxxx":"..."}`) or a single `{"answer":"..."}`

```json
{
  "system_prompt": "You are a general-purpose assistant. Be concise, actionable, and correct. If questions exist, answer each QID and return a JSON object mapping QIDs to answers.",

  "output_agents": ["final_answer"],

  "steps": [
    {
      "name": "extract_task",
      "prompt_intro": "Step 1: Extract.\nReturn JSON with:\n{\n  \"has_questions\": boolean,\n  \"questions\": {\"QID\": \"question\", ...} | null,\n  \"scenario\": string | null\n}\n\nIncoming JSON:",
      "include_incoming": "raw",
      "use_payload_from": [],
      "prompt_ending": "Return JSON only.",
      "model": "gpt-4o-mini",
      "temperature": 0.1,
      "response_format": "json"
    },
    {
      "name": "solve",
      "prompt_intro": "Step 2: Solve.\nIf has_questions=true: return JSON mapping each QID to its answer.\nIf has_questions=false: return {\"answer\":\"...\"}.\n\nStep 1 output:",
      "include_incoming": false,
      "use_payload_from": ["extract_task"],
      "prompt_ending": "Return JSON only.",
      "model": "gpt-4o",
      "temperature": 0.2,
      "response_format": "json"
    },
    {
      "name": "final_answer",
      "prompt_intro": "Step 3: Finalize.\nReturn ONLY:\n- if questions exist: {\"Qxxxx\":\"...\", ...}\n- else: {\"answer\":\"...\"}\n\nInputs:",
      "include_incoming": false,
      "use_payload_from": ["extract_task", "solve"],
      "prompt_ending": "Return JSON only.",
      "model": "gpt-4o-mini",
      "temperature": 0.1,
      "response_format": "json"
    }
  ]
}
```

## Run locally (optional)

### Testing locally (correct sequence)

`/test` only works if **all components are connected**:

1. server
2. your agent (runner template)
3. InputAgent
4. then `/test`

If you type `/test` before your agent is running and connected, nothing will be received.

### 0) Install and activate environment

Using pip:

```sh
source build_sdk.sh setup
```

Using uv:

```sh
source build_sdk.sh setup --uv
```

Activate the venv:

```sh
source venv/bin/activate
```

Install requirements if needed:

```sh
bash install_requirements.sh
```

### 1) Start the server

```sh
# Terminal 1
source venv/bin/activate
python server.py
```

### 2) Start your agent (runner template)

```sh
# Terminal 2
source venv/bin/activate
python agent_templates/template_1_1/agent.py --steps season_1/agent_<your_github_handle>.json
```

Wait until you see a log line indicating it connected.

### 3) Start InputAgent

```sh
# Terminal 3
source venv/bin/activate
python agent_InputAgent/agent.py
```

Wait until InputAgent logs that it connected.

### 4) Run the built-in test

In the InputAgent terminal, type:

```text
/test
```

You should see a received message within about 1 minute:

```text
[Received] ...
  answers: {'Q4127': '...', 'Q0951': '...', ...}
  to: <sender id>
  from: minimal_agent
```

If you do not see a response:

* confirm your agent is running and connected before `/test`
* confirm your config file path and filename
* confirm your output step returns JSON mapping QIDs to answers (the runner wraps it into `{ "answers": ... }`)

> [!NOTE]
> Before opening a PR, follow [`CONTRIBUTING.md`](./CONTRIBUTING.md) to make sure your submission matches the required file name and season folder.

## Scoring and analytics

Each scenario has multiple questions (usually 10). Each question has a point value (see `raw.points` when present).
Your score is the sum of points for questions judged correct.

We always show points earned per run. Replay videos may be shared for some runs.
We may also publish aggregate analytics (for example, correlations between prompt structure or embeddings and score).

## Quick troubleshooting (common issues)

### Nothing happens when I type `/test`

Most common cause: your agent runner was not connected yet. Start the server, start your agent, start InputAgent, then `/test`.

### My agent returns text instead of QID answers

Your output step must return JSON only and output only the QID mapping. Use `response_format: "json"` and explicitly instruct: `Return ONLY {"Qxxxx": ...}`.

### Token limit or cancellation

If you include `rendered` or the whole payload, you may exceed input token limits. Prefer:

```json
"include_incoming": "raw"
```

or:

```json
"include_incoming": "raw.questions"
```
