# Contributing

This repository accepts hackathon submissions via **Pull Request (PR)**.

A submission is eligible only if it:

1. follows the required repository layout and submission format, and
2. passes the repository’s **automatic GitHub checks** (CI).

If anything here is unclear, open an Issue before investing time in a full submission.

## High-level workflow

1. **Fork** this repository.
2. Create a new branch in your fork.
3. Add your submission file in the required location and format.
4. Test locally (recommended, see the README).
5. Open a **Pull Request** from your branch into this repository.
6. CI runs automated checks.
7. Maintainers review only PRs that pass CI and meet requirements.

## What gets accepted

We accept **one submission per participant per season**, unless a season explicitly says otherwise.

We merge PRs that:

- add a valid submission file in the correct season folder
- do not modify runner code, the server, CI, or other participants’ submissions
- pass all required checks

## Submission location and naming

For the hackathon, participants submit **a single JSON file** (not Python code).

Place your file in the current season folder (Season 1 shown here):

```text
season_1/agent_<your_github_handle>.json
````

Example:

```text
season_1/agent_remytuyeras.json
```

Rules:

* The filename must start with `agent_`.
* `<your_github_handle>` must match your GitHub username.
* The file must be **valid JSON** (`.json`, no comments).

  * For documentation, see `season_1/full_template.jsonc` (JSONC with comments).

## What not to change

Your PR must **not**:

* modify runner code under `agent_templates/`
* modify `agent_InputAgent/`
* modify the server, SDK, CI configuration, or repository tooling
* modify other participants’ files
* add secrets (API keys, tokens, credentials)
* add large binaries or datasets

If your PR changes anything outside your single `season_<n>/agent_<handle>.json` file, it will be closed unless a maintainer explicitly requested those changes.

## Submission format (JSON)

Your submission is a JSON config consumed by the season’s runner template.

At minimum, it should define:

* `steps`: an array of step objects (each step is one model call)
* optionally: `system_prompt`, `output_agents`

For the full set of fields and examples, use:

* `season_1/full_template.jsonc` (documentation template)
* the project README (how to run and test)

### Output expectations

Your configured output step(s) should return a JSON object mapping QIDs to answers:

```json
{
  "Q4127": "…",
  "Q0951": "…"
}
```

The runner wraps your mapping into:

```json
{
  "answers": { "Q4127": "…", "Q0951": "…" }
}
```

If your output step returns plain text instead of a JSON object, it will not produce QID → answer mappings.

## Runner-enforced limits (Season 1: `template_1_1`)

These are enforced at runtime by the runner:

* Max **5** model calls per incoming payload (only the first 5 steps execute)
* Max **2000 input tokens per step** (step is cancelled if exceeded)
* Max **600 output tokens per step**
* Allowed models: `gpt-4o-mini`, `gpt-4o` (others are overridden to `gpt-4o-mini`)
* Must respond within **1 minute per scenario** (otherwise ignored)

## External services and secrets

Your submission is JSON-only, and the runner performs the allowed OpenAI call(s).

Do not attempt to introduce additional external calls by modifying repo code.
Do not include API keys in your PR. Runtime keys are provided via environment configuration.

## Security and safety constraints

Do not submit changes that attempt to:

* escalate privileges or escape the sandbox
* scan networks, probe ports, or exfiltrate data
* fetch or execute arbitrary code from the internet
* add malware-like behavior (persistence, stealth, obfuscation)
* access files outside the repo structure or runtime working directory

(Participants should not be adding code at all. This section clarifies what is disallowed in PRs.)

## Reproducibility expectations

We run agents multiple times across scenarios. You should:

* keep prompts stable and deterministic where possible
* avoid relying on undefined or optional fields
* assume payload shapes and sizes vary across scenarios

## Local testing (recommended)

Before opening a PR:

* run the season runner locally with your JSON file
* use the InputAgent `/test` workflow described in the README

Startup order matters:

1. server
2. your agent (runner template)
3. InputAgent
4. then `/test`

## PR checklist

Your PR must:

* [ ] add exactly one file: `season_1/agent_<your_github_handle>.json`
* [ ] keep it valid JSON (no comments)
* [ ] not modify runner/server/SDK/CI or other submissions
* [ ] pass all CI checks

## Review process

Maintainers review PRs that pass CI. If changes are requested:

* push commits to the same branch
* do not open a new PR unless asked

## Licensing

By submitting a PR, you agree that your contribution can be used and redistributed under this repository’s license.

If your submission includes third-party content, you are responsible for ensuring you have the right to submit it and that any required attribution is included.

## Questions

Open an Issue with:

* what you are trying to build
* what season you are targeting
* what constraint you are hitting (token limits, output format, etc.)

Resolving constraints early is preferred over debugging CI later.
