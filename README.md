# Py_Chatbox — Developer Handoff

**Author:** Larvene Jafem (Commander KernelGhost)  
**License:** MIT  
**Stack:** Python 3 — zero external dependencies (stdlib only)

---

## Table of Contents

1. [What This Project Is](#what-this-project-is)
2. [Quick Start](#quick-start)
3. [Project Map](#project-map)
4. [Architecture & Data Flow](#architecture--data-flow)
5. [Module Breakdown](#module-breakdown)
6. [How to Extend](#how-to-extend)
7. [Known Issues & Technical Debt](#known-issues--technical-debt)
8. [Testing](#testing)

---

## What This Project Is

Three experiences in one terminal app:

| System | File | Description |
|--------|------|-------------|
| **PookieGPT** | `chatbox.py` | Gen-Z emotional-support chatbot with rank/XP progression. JSON-driven dialogue. |
| **KRNL System** | `krnl_system.py` | Keyword-response cadet simulator with persistent memory and stress tracking. |
| **ELIZA** | `eliza.py` | Full reimplementation of Weizenbaum's 1960s Rogerian therapist. Standalone library. |

A boot menu in `core.py` lets the user pick one. ELIZA unit tests run automatically on exit.

---

## Quick Start

```bash
python source/core.py
```

Standalone ELIZA:
```bash
python source/eliza.py
```

---

## Project Map

```
Chatbox-betaBranch/
│
├── users.json                  # Runtime data — user accounts (hashed pw, XP, rank)
│
├── source/
│   ├── core.py                 # ENTRY POINT — boot menu, launchers, test suite
│   ├── chatbox.py              # PookieGPT class + ASCII box UI helpers
│   ├── krnl_system.py          # KRNL simulator (keyword dispatch, memory, XP)
│   ├── eliza.py                # ELIZA engine (pattern matching, substitution, memory)
│   ├── ranking.py              # Auth (SHA-256), rank system, user CRUD
│   ├── slow_print.py           # Typing animation utility
│   │
│   ├── responses.json          # PookieGPT dialogue — all messages externalized here
│   ├── ranksystem_static.json  # Rank thresholds (9 ranks, Recruit → General)
│   └── doctor.txt              # ELIZA "doctor" script in custom tag format
│
└── README.md                   # ← you are here
```

---

## Architecture & Data Flow

### Design

Modular monolith. No framework, no database — the calling convention is direct imports between `.py` files. Every module has one responsibility.

### Flow

```
User runs core.py
       │
       ▼
  core.py (boot menu)
       │
       ├── Option 1 ──▶ run_pookie()
       │                   │
       │                   ├── ranking.userInitLogin()    # register/login
       │                   ├── chatbox.PookieGPT()
       │                   │       ├── introduction()
       │                   │       ├── general_quest()    # mood check
       │                   │       └── whatodo()          # action loop
       │                   │               ├── con_talk()
       │                   │               ├── askmeQuestion()
       │                   │               └── rage_quit()
       │                   └── (saves to users.json)
       │
       ├── Option 2 ──▶ run_krnl()
       │                   │
       │                   ├── loads user from users.json
       │                   ├── loads memory from memory.json
       │                   └── main loop:
       │                           ├── ai_response()      # keyword dispatch
       │                           ├── update XP / rank
       │                           └── save both JSON files
       │
       └── Exit ──▶ ElizaTest.run()    # 13 unit tests
```

### Data flow (applies to both bots)

```
JSON file ──> json.load() ──> Python dict ──> process input ──> mutate dict ──> json.dump() ──> JSON file
```

State is **written to disk after every interaction**. No in-memory state management, no cache layer, no reactive patterns.

---

## Module Breakdown

### `core.py` — Entry Point & Test Runner

**Responsibilities:**
- `ascii_box()` / `center_text()` — reusable ANSI box-drawing used by every module
- `run_pookie()` — orchestrates login → PookieGPT session
- `run_krnl()` — orchestrates user load → KRNL session
- `ElizaTest(TestCase)` — 13 unit tests for ELIZA pattern matching

**Key detail:** `ascii_box()` uses Unicode box-drawing characters (`┌─┐│└┘`). All UI rendering goes through it. If you change the UI, change this function.

---

### `chatbox.py` — PookieGPT

**Class:** `PookieGPT`

| Method | Purpose |
|--------|---------|
| `__init__()` | Loads `responses.json` into `self.responds` dict |
| `introduction()` | Welcome screen with ASCII art |
| `general_quest()` | Asks how the user is feeling — branches on mood |
| `con_talk()` | Free chat mode — picks random response from key |
| `askmeQuestion()` | Prompts user to ask a question |
| `whatodo()` | Main action router — user picks chat, ask, or quit |
| `rage_quit()` | Exit sequence |
| `legacy_shutdown()` | Original quit handler |

**Singleton:** `bot = PookieGPT()` is instantiated at module level — all functions reference this global.

**Dialogue:** Every response lives in `responses.json`. The bot does `random.choice()` from arrays keyed by scenario. There is **no NLP or intent parsing**. It's a fancy `if/else` + random picker.

---

### `krnl_system.py` — KRNL Simulator

**Pure functions** (no class):

| Function | Purpose |
|----------|---------|
| `create_user(name, age)` | Initializes user profile dict |
| `load_memory(name)` | Loads/sets up conversation memory from JSON |
| `remember(name, key, value, memory)` | Stores a fact in memory |
| `update_rank(user)` | Calculates rank from XP based on `ranksystem_static.json` |
| `ai_response(user_input, user, memory)` | **Main handler** — keyword dispatch + response generation |
| `status_panel(user)` | Renders XP bar + rank display |
| `main()` | Full interactive session loop |

**Keyword routing** (in `ai_response`): simple `if "keyword" in user_input.lower()` checks. Currently handles: `math`, `python`/`code`, `stress`/`tired`, `study`, `remember`, `memory`, `status`.

**Persistence:** Saves both `users.json` and `memory.json` every iteration.

---

### `eliza.py` — Reusable ELIZA Library

**Class:** `Eliza`

Fully implements the original 1960s algorithm:

- **Script format:** Custom tag-based (`initial:`, `final:`, `key:`, `decomp:`, `reasmb:`, `synon:`, etc.) — see `doctor.txt`
- **Pattern matching:** `*` wildcard, `@synonym` group expansion, `$` save flag, `goto` key redirect
- **Substitution:** Pre/post transforms swap pronouns ("you" → "I", "my" → "your", etc.)
- **Memory:** Can save a matched result and recall it later ("Earlier you said...")

**Usage (as library):**
```python
import eliza
e = eliza.Eliza()
e.load('doctor.txt')
print(e.initial())
while True:
    reply = e.respond(input('> '))
    if reply is None: break
    print(reply)
```

**Data classes:**
- `Key(keyword, rank, decomps)` — a keyword with ranked decomposition patterns
- `Decomp(pattern, memory_flag, reassembly_list)` — a pattern + possible responses

---

### `ranking.py` — Authentication & Progression

**Class:** `RankingSystem` (all `@staticmethod`)

| Method | Purpose |
|--------|---------|
| `hash_password(password)` | SHA-256 hex digest |
| `load_users()` / `save_users(data)` | CRUD on `users.json` |
| `load_ranks()` | Reads `ranksystem_static.json` into list of dicts |
| `register(username, password)` | Checks uniqueness, hashes, saves |
| `login(username, password)` | Hash comparison |
| `userInitLogin()` | Interactive R/L prompt → calls register or login |
| `registeringUserRank()` / `loggingInToUserRank()` | Collects name/age/goal interactively |

**File location:** `users.json` sits in the **project root** (one level up from `source/`). The path is hardcoded as `"../users.json"`.

---

### `slow_print.py` — Typing Animation

```python
slow_print(text, delay=(0.03, 0.1))   # prints char-by-char
slow_input(prompt, delay=(0.03, 0.1)) # prints prompt slowly, returns input()
```

Used by both bots for the "chatbot typing" feel. The delay is a `(min, max)` tuple — a random uniform delay per character.

---

## How to Extend

### Add new PookieGPT dialogue

Edit `source/responses.json`. Each key maps to an array of strings. The bot calls `random.choice()` on the array. Add a new key, then reference it in `chatbox.py` wherever you want it shown.

### Add a new KRNL keyword command

In `krnl_system.py` → `ai_response()`, add a new `elif "keyword" in user_input.lower():` branch. Build the response string, optionally grant XP, optionally save to memory.

### Add a new rank tier

Edit `source/ranksystem_static.json` — append a new object with `{"title": "...", "score": N}`. The rank order is array-index-based (index 0 = lowest).

### Modify the ELIZA script

Edit `source/doctor.txt`. The tag format is documented in the original comment block at the top of `eliza.py`. Key tags: `key:` (trigger keyword), `decomp:` (pattern with `*` wildcards), `reasmb:` (response template), `synon:` (synonym group).

---

## Known Issues & Technical Debt

| Issue | Location | Note |
|-------|----------|------|
| `users.json` path hardcoded as `../users.json` | `ranking.py:22` | Breaks if working directory isn't `source/` or if file is moved |
| Global singleton `bot = PookieGPT()` | `chatbox.py:278` | Module-level instantiation — prevents clean re-initialization |
| `core.py` does `from chatbox import *` | `core.py:4` | Wildcard import — pollutes namespace, unclear what's available |
| All UI helpers duplicated in `core.py` and `chatbox.py` | Both files | `ascii_box()` and `center_text()` are defined in both — should be shared |
| No `setup.py` / `pyproject.toml` | — | Can't `pip install` or publish to PyPI |
| No requirements file | — | Currently none needed (stdlib only), but a blank `requirements.txt` documents intent |
| ELIZA tests run on every exit | `core.py:115` | `ElizaTest().run()` is called unconditionally — user may not want tests every time |
| `memory.json` created in `source/` with no gitignore | `krnl_system.py` | Runtime artifact that could be accidentally committed |
| Exception handling is minimal | Throughout | User input is largely trusted; bad JSON or missing files will crash |
| No logging | — | `print()` everywhere — no log levels, no log files |

---

## Testing

```bash
# Run all ELIZA tests (also runs automatically on app exit)
python -c "from source.core import ElizaTest; ElizaTest().run()"

# With unittest runner
python -m unittest source.core.ElizaTest
```

Tests cover: keyword matching, wildcard capture, synonym expansion, pronoun substitution, memory save/recall, `goto` redirect, quit detection, and empty input handling.
