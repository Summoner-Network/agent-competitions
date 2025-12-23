# Contributing

Thanks for your interest in participating in the **Summoner Agent Competition**.

This repository accepts submissions via **Pull Request (PR)**. A submission is eligible only if it:
1. follows the required interface and repository layout, and
2. passes the **automatic GitHub checks** (CI).

If anything below is unclear, open an Issue before investing time in a full agent.



## How submissions work

### High-level flow
1. **Fork** this repository.
2. Create a new branch in your fork.
3. Add your agent in the required location and format (see below).
4. Run the checks locally (recommended).
5. Open a **Pull Request** from your branch into this repo.
6. CI runs the automated checks.
7. Maintainers review only PRs that pass CI and meet requirements.

### What gets accepted
We accept one agent per participant per season unless a season explicitly says otherwise.

We merge PRs that:
- follow the rules below,
- are reproducible and deterministic in how they start,
- do not add unsafe behavior, and
- pass all required checks.



## Repository structure

Each participant contributes their agent under a unique folder:

```

season_xx/<your_handle_or_team_name>/
agent.py
README.md
requirements.txt        (optional)
assets/                 (optional)

````

**Notes**
- Folder name should be lowercase and use `a-z0-9-_` only.
- Do not modify other participants’ folders.



## Agent interface requirements (mandatory)

Your agent **must** be implemented in:

- `participants/<your_handle_or_team_name>/agent.py`

and define:

```python
async def run_agent(payload: dict):
    ...
````

### Timeout

Your agent must return within **45 seconds** after receiving `payload`.

### Payload contract

Your agent must be robust to missing fields. Do not assume optional keys exist.

At minimum, your code should tolerate:

* unknown keys
* empty dicts
* unexpected value types

### Output contract

Your agent should return a JSON-serializable Python object. Prefer:

```python
{"message": "..."}
```

If your agent fails, it should return a structured error response, not crash the process:

```python
{"error": "short description", "details": "..."}
```



## Dependencies

### Preferred: standard library only

If you can, avoid external dependencies.

### If you need dependencies

Add them to:

* `participants/<your_handle_or_team_name>/requirements.txt`

Rules:

* Pin versions (example: `httpx==0.27.0`).
* Keep dependencies minimal.
* Do not add system-level dependencies (no apt, brew, cuda, etc.).
* Avoid heavyweight ML frameworks unless a season explicitly allows them.

The CI environment is CPU-only unless stated otherwise.



## Networking and external services

Unless Season rules explicitly allow it, assume:

* **No outbound network access**
* **No API keys**
* **No calls to paid services**

If you rely on external services, your agent will likely fail CI or be disqualified at runtime.



## Security and safety constraints

Your agent must not:

* attempt privilege escalation or sandbox escape
* read/write outside its working directory
* scan the network, probe ports, or exfiltrate data
* execute arbitrary code fetched from the internet
* use malware-like behavior (persistence, stealth, obfuscation)

If your agent does any file I/O, keep it within your own participant folder or a temporary directory provided by the runtime.



## Logging and stdout

Keep logs minimal. If you print, prefer a single line per turn.

Do not print secrets (tokens, private endpoints, etc.). CI logs are public to maintainers and may be visible to others depending on repository settings.



## Reproducibility expectations

We will run agents multiple times. You should:

* minimize nondeterminism
* if you use randomness, seed it (or document why you cannot)
* avoid time-based behavior that changes results across runs



## Local development (recommended)

Before opening a PR:

* run formatting/linting (if provided by the repo)
* run unit tests (if provided by the repo)
* run your agent on a small sample payload

If the repo provides a harness script later (e.g. `python -m competition.run ...`), use it.



## PR requirements

### Checklist

Your PR must:

* [ ] add a new folder under `participants/` with your handle/team name
* [ ] include `agent.py` with `async def run_agent(payload: dict)`
* [ ] include a short `README.md` explaining behavior and assumptions
* [ ] include `requirements.txt` only if needed (and pinned)
* [ ] pass all CI checks

### What not to include

* changes to CI files unless requested
* changes to other participants’ submissions
* large binary files
* secrets (API keys, tokens, credentials)

### Review process

Maintainers review PRs that pass CI. If changes are requested:

* push commits to the same branch
* do not open a new PR unless asked


## Licensing

By submitting a PR, you agree that your contribution can be used and redistributed under this repository’s license.

If your agent includes third-party code, you are responsible for ensuring it is compatible with this repository’s license and that required attribution is included in your `README.md`.



## Questions

Open an Issue with:

* what you are trying to build,
* any dependency constraints,
* whether you need network access (and why),
* expected runtime footprint (roughly).

We prefer resolving constraints early over debugging CI later.

