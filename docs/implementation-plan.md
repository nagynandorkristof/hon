# hOn Integration — Phased Implementation Plan (for AI coding agents)

**Source of truth for *why*:** [audit-2026-08-17.md](audit-2026-08-17.md). This document is the *what/when/how to execute* — every task below cites the audit section it implements. Don't re-derive rationale here; read the cited section if you need the reasoning behind a task.

**Audience:** an AI coding agent picking up one phase at a time, likely without memory of prior phases. Each phase is written to be self-contained: goal, preconditions, exact files, step-by-step tasks, and acceptance criteria. Do not start a phase whose preconditions aren't met.

## How to use this plan

- Phases are ordered by dependency, not just priority — Phase 2 (restructuring) must land before Phase 3+ touch entity-behavior files, and Phase 1 (library exception types) must land before Phase 3's integration-layer error handling has anything typed to catch.
- Do one phase per PR/commit series. Run the **Verification** block at the end of a phase before moving on; do not start the next phase if verification fails.
- Stay inside the **Scope** listed for each phase. If you notice an unrelated issue while working, note it for a later phase instead of fixing it inline — this keeps each phase's diff reviewable and matched to one audit section.
- Every code snippet in the audit is illustrative, not a literal patch — read the current file before editing; line numbers will have shifted after Phase 2.
- If a task's precondition isn't met (e.g. the constant it depends on doesn't exist yet), stop and say so rather than improvising a substitute.

---

## Phase 0 — Baseline capture

**Goal:** establish a known-good baseline before any change, so later phases have something to diff against and revert to if needed.

**Preconditions:** none.

**Tasks:**
1. Confirm the working tree is clean (`git status`). If not, stop and ask — do not start this plan on top of uncommitted, unrelated work.
2. Run and record the output of the full verification suite (see below) as-is, before any changes. Some things (e.g. `mypy -p custom_components.hon.pyhon`) should already pass cleanly per the vendoring work in this session; others (integration-wide `mypy`, `flake8`) may not have been run end-to-end — capture whatever the current state is so later phases can tell what they changed vs. what was already broken.
3. Confirm `custom_components/hon/pyhon/` (the vendored library) and `docs/audit-2026-08-17.md` both exist. If either is missing, stop — this plan assumes both are already in place.

**Verification (repeat after every phase from here on):**
```bash
python3 -m black --check custom_components/hon
python3 -m mypy --config-file mypy.ini -p custom_components.hon.pyhon
python3 -m py_compile $(find custom_components/hon -name '*.py')
```
(`mypy -p custom_components.hon` in full requires `homeassistant` installed — run it if available; otherwise the `pyhon`-scoped run plus `py_compile` across everything is the minimum bar.) Where a phase touches HA entity behavior, also do a manual reload against a real account or the `TestAPI`/`hon-test-data` fixture path and confirm no entities disappear from the entity registry and no new exceptions appear in the log.

---

## Phase 1 — `pyhon` library reliability fixes

**Goal:** make the vendored library itself safe to build integration-layer error handling on top of. Every later phase that wraps a `pyhon` call in a `try/except` depends on this phase existing first — there's currently no exception type that means "the network failed," so nothing downstream can catch one.

**Preconditions:** Phase 0 done.

**Scope:** `custom_components/hon/pyhon/` only. Do not touch `custom_components/hon/*.py` (the integration layer) in this phase — that's Phase 3+.

**Tasks:**

1. **New connectivity exception** (audit §7.3). In `custom_components/hon/pyhon/exceptions.py`, add:
   ```python
   class HonConnectionError(Exception):
       pass
   ```
2. **Request timeout** (audit §7.1). In `custom_components/hon/pyhon/connection/handler/base.py`, `ConnectionHandler.create()`: construct the session with a bounded timeout, e.g. `aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))` instead of `aiohttp.ClientSession()`. Define the `30` as a module-level constant (e.g. `_REQUEST_TIMEOUT_SECONDS = 30` near the top of the file) rather than an inline literal — this file is a plausible place for future tuning.
3. **Wrap network errors at the transport layer** (audit §7.3). In `ConnectionHandler._intercept` (`connection/handler/base.py`) and `HonConnectionHandler._intercept` (`connection/handler/hon.py`), catch `aiohttp.ClientError` and `TimeoutError` around the `async with method(...)` call and re-raise as `HonConnectionError` (chain with `from`). Do this at the lowest layer that actually makes the request, so every caller — `HonAPI`, `HonAuth`, `HonCommand` — gets the typed exception for free without needing its own handling.
4. **Fix the confirmed root cause of the production crash** (audit §7.2, ties to audit §4.1). In `custom_components/hon/pyhon/commands.py`, `HonCommand.send_parameters`: broaden the `except NoAuthenticationException:` clause to also catch `HonConnectionError` and `ApiError` (the latter is currently raised two lines above in the same function and not caught by anything). Decide and document the return contract for each: today the function returns `False` on `NoAuthenticationException` — do the same for `HonConnectionError` (a caller-recoverable condition), but let `ApiError` re-raise instead of being silently swallowed to `False`, since a rejected command is a stronger signal than "no auth" and callers (Phase 3) need to distinguish "command sent but device is offline" from "command outright failed."
5. **MQTT watchdog self-protection** (audit §8.1). In `custom_components/hon/pyhon/connection/mqtt.py`, `MQTTClient._watchdog`: wrap the reconnect attempt (`await self._start()` + `self._subscribe_appliances()`) in `try/except Exception: _LOGGER.exception(...)` so a failed reconnect is logged and retried on the next 5-second tick instead of silently ending the watchdog task forever.
6. **Guard the MQTT message callback** (audit §9.1). In `MQTTClient._on_publish_received` (`connection/mqtt.py`): wrap the body in `try/except Exception: _LOGGER.exception(...)`, and replace the bare `next(a for a in self._appliances if topic in a.info["topics"]["subscribe"])` with `next((a for a in self._appliances if topic in a.info.get("topics", {}).get("subscribe", [])), None)` followed by an explicit `if appliance is None: return`.
7. **Fix appliance-list aliasing** (audit §9.2). In `MQTTClient`, replace the cached `self._appliances = hon.appliances` with a property or direct `self._hon.appliances` lookup wherever `self._appliances` is currently read, so it always reflects the live list rather than a reference captured at construction time.
8. **Don't keep half-loaded appliances** (audit §10.1). In `custom_components/hon/pyhon/hon.py`, `Hon._create_appliance`: move `self._appliances.append(appliance)` inside the `try` block (after the three `load_*` calls succeed), and widen the caught exception tuple to also include `(HonConnectionError, ApiError)` alongside the existing `(KeyError, ValueError, IndexError)`, so a network failure during one appliance's load doesn't add a half-initialized appliance to the list, and doesn't abort loading the rest of the account's appliances either.

**Explicitly out of scope for this phase:** the `OS_VERSION`/`USER_AGENT`/`DEVICE_MODEL`/`MOBILE_ID` constants (audit §12) — that's Phase 8, gated separately.

**Verification:** the Phase 0 suite, plus:
```bash
python3 -m mypy --config-file mypy.ini -p custom_components.hon.pyhon
```
must still pass clean (0 errors) after these changes — this phase touches files that already pass strict mypy, so don't regress that.

---

## Phase 2 — Repository restructuring

**Goal:** split declarative per-appliance-type data out of the ten platform files before any behavior changes land in them, so Phases 3–6 operate on small, focused files instead of 300–900-line ones. Pure refactor — no behavior change, verified by diffing that nothing except `import`s and the moved dataclass/dict definitions changed.

**Preconditions:** Phase 1 done (not strictly required by dependency, but keeps the diff history clean — library fixes and integration restructuring shouldn't be interleaved in the same commits).

**Scope:** `custom_components/hon/*.py` (not `pyhon/`). Full target layout and rationale: audit §13–17.

**Hard constraint — read before starting:** `sensor.py`, `switch.py`, `binary_sensor.py`, `button.py`, `climate.py`, `fan.py`, `light.py`, `lock.py`, `number.py`, `select.py` **must remain directly under `custom_components/hon/`**. Home Assistant imports `custom_components.hon.<platform>` by convention (`const.py`'s `PLATFORMS` list); moving these files into a subpackage will break the integration. Only their *data* moves — the files themselves stay where they are, just shrink.

**Tasks, in this order (smallest file first, to prove the pattern before the big ones):**

1. Create `custom_components/hon/descriptions/__init__.py` (empty).
2. For each platform below, move its entity-description dataclass(es) and its top-level dict constant into `custom_components/hon/descriptions/<platform>.py`, and replace them in the original file with an `from .descriptions.<platform> import <DICT_NAME>` (plus importing the dataclass types needed for `entity_description:` type annotations on the entity classes that remain). Order: `lock.py`, `fan.py`, `button.py`, `light.py`, `number.py`, `select.py`, `switch.py`, `binary_sensor.py`, `sensor.py`, `climate.py` (climate.py's `CLIMATES` dict is small — do it last, low priority, mainly for consistency).
3. While moving `select.py` and `sensor.py`: also relocate the option-lookup tables from `const.py` that only those two files use — `WASHING_PR_PHASE`, `MACH_MODE`, `DIRTY_LEVEL`, `STEAM_LEVEL`, `DISHWASHER_PR_PHASE`, `TUMBLE_DRYER_PR_PHASE`, `TUMBLE_DRYER_DRY_LEVEL`, `AC_MACH_MODE`, `AC_FAN_MODE`, `AC_HUMAN_SENSE`, `AP_MACH_MODE`, `AP_DIFFUSER_LEVEL`, `REF_HUMIDITY_LEVELS`, `AC_POSITION_HORIZONTAL`, `AC_POSITION_VERTICAL`, `STAIN_TYPES` — into `descriptions/select.py` / `descriptions/sensor.py` respectively (verify each table's actual consumer with `grep` before moving; the audit's mapping was correct as of the audit date but re-verify since files will have changed).
4. While moving `climate.py`: relocate `HON_HVAC_MODE`, `HON_HVAC_PROGRAM`, `HON_FAN` from `const.py` directly into `climate.py` itself (not `descriptions/climate.py` — these are used in entity *logic*, not the description dict).
5. Trim `const.py` down to `DOMAIN`, `MOBILE_ID`, `CONF_REFRESH_TOKEN`, `PLATFORMS`, `APPLIANCES`, `LANGUAGES`. Confirm with `grep -rn` that nothing else in the repo still imports a symbol you removed from `const.py` before finishing this step.
6. Extract the coordinator setup currently inline in `custom_components/hon/__init__.py` (`DataUpdateCoordinator(...)` construction + `hon.subscribe_updates(...)`) into a new `custom_components/hon/coordinator.py` defining `HonCoordinator`. Leave its behavior identical for this phase — Phase 4 is where the fallback-poll logic gets added to it.

**Acceptance criteria specific to this phase:**
- `git diff --stat` after each platform's move should show the platform file shrinking and a new `descriptions/<platform>.py` appearing with a comparable line count added — if a platform file's line count doesn't drop substantially, something wasn't actually moved.
- No `unique_id`, `translation_key`, or dict key changes anywhere — this must be a pure move. Diff each moved dict's contents against its pre-move version (e.g. `git show HEAD:custom_components/hon/switch.py | grep -A2 'key='` vs. the new `descriptions/switch.py`) to confirm nothing was dropped or altered in transcription.
- A manual HA reload (or entity-registry diff) shows the exact same set of entities before and after.

**Verification:** Phase 0 suite, plus `flake8 . --count --select=E9,F63,F7,F82` (catches leftover undefined-name references from an incomplete move).

---

## Phase 3 — Integration setup/lifecycle reliability

**Goal:** stop `async_setup_entry`/`async_unload_entry` from crashing ungracefully, using the exception types Phase 1 introduced.

**Preconditions:** Phase 1 (needs `HonConnectionError`) and Phase 2 (operating on the post-restructure `__init__.py`/`coordinator.py`) both done.

**Scope:** `custom_components/hon/__init__.py`, `custom_components/hon/coordinator.py`.

**Tasks:**
1. **(audit §1.2)** In `async_setup_entry`, wrap the `Hon(...).create()` call: catch `HonAuthenticationError` (from `pyhon.exceptions`) and re-raise as `homeassistant.exceptions.ConfigEntryAuthFailed`; catch `HonConnectionError` (from Phase 1) and re-raise as `homeassistant.exceptions.ConfigEntryNotReady`.
2. **(audit §1.3)** Replace the per-platform `hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, platform))` loop with a single `await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)`.
3. **(audit §1.4)** In `async_unload_entry`, guard the `hass.data[DOMAIN][entry.unique_id]` lookup with `.get()` and return early (or skip the refresh-token save) if the entry was never fully set up, instead of letting a bare `KeyError` propagate.

**Verification:** Phase 0 suite. Manually verify (or reason through, if HA isn't runnable in this environment) the three new failure paths: wrong password → should surface as a reauth prompt, not a crash; cloud unreachable at startup → should retry per HA's `ConfigEntryNotReady` backoff, not fail permanently; unload during partial setup → should not raise.

---

## Phase 4 — Availability & fallback polling

**Goal:** make entity `available` state actually reflect device connectivity across all platforms, and add the periodic REST fallback poll as a safety net against a dead MQTT connection (audit §8.1's failure mode, even after Phase 1's fix reduces its likelihood — defense in depth).

**Preconditions:** Phase 2 (needs `coordinator.py` to exist) and Phase 3 done.

**Scope:** `custom_components/hon/entity.py`, `custom_components/hon/coordinator.py`, `custom_components/hon/const.py`.

**Tasks:**
1. **(audit §2.2)** In `entity.py`, add a shared `available` property to the `HonEntity` base class that checks `self._device.connection` (matching the pattern already used independently by `switch.py`/`number.py`/`select.py`/`lock.py`). Then remove the now-redundant per-subclass `available` overrides in those files if they're identical to the new base implementation, or leave subclass overrides in place only where they add something the base doesn't (e.g. the `remoteCtrValid` check). `sensor.py`, `binary_sensor.py`, and `climate.py` currently have no `available` override at all — confirm after this change that they now inherit the base implementation and are no longer always-available.
2. **(audit §2.1/§8.2, and the follow-up constraint on poll frequency)** In `const.py`, add:
   ```python
   FALLBACK_POLL_INTERVAL = timedelta(minutes=1)  # must not be looser than this
   ```
   Do not hardcode this duration anywhere else — every reference must go through this constant.
3. In `coordinator.py`, set `HonCoordinator`'s `update_interval = FALLBACK_POLL_INTERVAL` and implement `_async_update_data` to iterate `hon.appliances` calling `await appliance.update()` on each (catching `HonConnectionError` per-appliance so one unreachable device doesn't fail the whole refresh cycle — log and continue).
4. Confirm `HonAppliance.update()`'s own internal debounce (`_MINIMAL_UPDATE_INTERVAL = 5` seconds, in `pyhon/appliance.py`) is unrelated to and doesn't conflict with the new coordinator-level interval — it's a per-appliance safeguard against being called too often, not a substitute for scheduling.

**Verification:** Phase 0 suite. Confirm `FALLBACK_POLL_INTERVAL` is referenced (not duplicated as a literal) everywhere it's used: `grep -rn "FALLBACK_POLL_INTERVAL\|update_interval" custom_components/hon --include=*.py` should show exactly one definition and one assignment site.

---

## Phase 5 — Defensive data access

**Goal:** stop unguarded dict/lookup access from crashing entity state getters on malformed, partial, or unexpected cloud payloads.

**Preconditions:** Phase 2 done (targets the post-restructure file layout).

**Scope:** `custom_components/hon/climate.py`, `custom_components/hon/sensor.py`, and (opportunistically, same pattern) any other platform file where `self._device.settings[key]` / `LOOKUP[value]` appears without a `.get()`.

**Tasks:**
1. **(audit §3.1)** In `climate.py`, replace `HON_HVAC_MODE[self._device.get("machMode")]` and `HON_FAN[self._device.get("windSpeed")]` with `.get(..., <sensible default>)` — e.g. `HON_HVAC_MODE.get(mode, HVACMode.OFF)`, `HON_FAN.get(speed, FAN_AUTO)` — and log a warning when the fallback is hit, so an unmapped value is discoverable rather than silently masked.
2. **(audit §3.2)** In `sensor.py`, `HonSensorEntity._handle_coordinator_update`: replace `if not (options := self._device.settings.get("startProgram.program")): raise ValueError` with a graceful skip — keep the previous `_attr_options`/value rather than raising, and log at debug level.
3. **Sweep for the same class of bug** (audit §5, general pattern): `grep -rn "\.settings\[" custom_components/hon/*.py` and `grep -rn "self\._device\[" custom_components/hon/*.py` to find remaining direct-indexing hot-path property getters (things HA calls on every state read, not one-time `__init__` setup code); convert to `.get()` with a documented default where the value can plausibly be absent for a given firmware/model variant. Use judgment — `__init__`-time indexing that intentionally should fail fast if a description is misconfigured (a programmer error) is fine to leave as direct indexing; it's the properties read on every coordinator update that need to be defensive against a modified/partial payload.

**Verification:** Phase 0 suite. If a `TestAPI`/`hon-test-data` fixture set is available, run through it and confirm no new exceptions in the log versus the Phase 0 baseline.

---

## Phase 6 — Config flow credential validation & reauth

**Goal:** move credential-failure detection from "several steps later, as an unhandled crash" (fixed to *some* degree by Phase 3) to "immediately, in the config form, with a clear error."

**Preconditions:** Phase 1 (needs `HonAuthenticationError`/`HonConnectionError`) and Phase 3 done.

**Scope:** `custom_components/hon/config_flow.py`.

**Tasks:**
1. **(audit §5)** In `async_step_user`, after collecting email/password and before `async_create_entry`, attempt `await Hon(email, password, ...).create()` (or a login-only call if one exists in `pyhon`'s public surface). On `HonAuthenticationError`, re-show the form with `errors["base"] = "invalid_auth"` instead of creating the entry. On `HonConnectionError`, show a distinct `errors["base"] = "cannot_connect"` so the user can tell "wrong password" from "hOn is down right now" apart.
2. Add `async_step_reauth` (standard HA pattern: triggered when `ConfigEntryAuthFailed` is raised from Phase 3's `async_setup_entry` fix) that re-prompts for password only (email/unique_id already established) and updates the existing config entry on success instead of requiring delete-and-recreate.
3. Add the corresponding `errors` strings to `custom_components/hon/translations/en.json` (and other locale files if the project maintains translations for form errors — check `translations/` for the existing pattern other config flows in this repo use, if any exist yet).

**Verification:** Phase 0 suite. Manually walk both new paths: wrong password at setup → inline form error, not a crash; simulate an auth failure post-setup (e.g. by invalidating the stored refresh token) → reauth flow triggers.

---

## Phase 7 — Test coverage

**Goal:** every behavior fixed in Phases 1–6 gets a regression test, since none of this was previously covered and the audit's findings would otherwise be free to silently regress.

**Preconditions:** Phases 1–6 done. (Can start earlier per-phase if preferred — e.g. write Phase 1's tests right after Phase 1 lands rather than batching all testing at the end. This plan lists it last only because it's lowest-risk to defer, not because it's optional.)

**Scope:** new `tests/` directory (none exists yet — this phase creates it) plus the `pytest`/`pytest-homeassistant-custom-component` dev dependencies needed to run HA-flavored tests; add to `requirements_dev.txt`.

**Tasks (one test module per phase, minimum viable coverage — not exhaustive):**
1. `tests/pyhon/test_commands.py` — mock `HonAPI.send_command` to raise `aiohttp.ClientError`/`TimeoutError` and assert `send_parameters` returns `False` (or the agreed contract from Phase 1 task 4) rather than propagating; assert `ApiError` still propagates.
2. `tests/pyhon/test_mqtt.py` — mock `_start()` to raise and assert the watchdog loop survives and retries rather than the task dying (Phase 1 task 5); mock a malformed publish payload and assert `_on_publish_received` doesn't raise (Phase 1 task 6).
3. `tests/test_init.py` — assert `async_setup_entry` raises `ConfigEntryAuthFailed`/`ConfigEntryNotReady` (not a raw exception) for the corresponding `pyhon` exceptions (Phase 3).
4. `tests/test_entity.py` — assert `HonEntity.available` reflects `_device.connection` for at least one representative subclass per platform, including `sensor`/`binary_sensor`/`climate` which had no coverage of this before (Phase 4).
5. `tests/test_climate.py` — assert an out-of-range `machMode`/`windSpeed` value falls back to the documented default instead of raising `KeyError` (Phase 5).
6. `tests/test_config_flow.py` — assert wrong credentials produce a form error, not an exception, and that the reauth flow updates rather than duplicates the config entry (Phase 6).

**Verification:** `pytest tests/` passes; re-run the Phase 0 suite once more as a full-repo sanity check now that everything above has landed.

---

## Phase 8 — Device identification constants (requires explicit human sign-off before starting)

**Goal:** implements audit §12.

**Preconditions:** none technical — but **do not start this phase without an explicit go-ahead from a human maintainer**, separate from whatever approval gated the rest of this plan. Unlike every other phase, this one touches values that interact with a documented prior legal dispute between this project's upstream and Haier (`takedown_faq.md`, `takedown_timeline.md`). The audit deliberately separated the two constants into different risk tiers — respect that split rather than doing both in one step:

**Tasks:**
1. **Lower-risk, purely technical (§12):** in `custom_components/hon/pyhon/const.py`, update `OS_VERSION` and `USER_AGENT` to values matching a real, current Android/Chrome release consistent with `APP_VERSION`. This is a reliability hardening (implausible values risk future server-side rejection) with no policy dimension — safe for an agent to do once this phase is greenlit.
2. **Do not change `DEVICE_MODEL` or `MOBILE_ID` as part of this plan.** The audit is explicit that this is "a project/policy decision... rather than an incidental fix." Flag it for a human decision; do not make the call unilaterally even if asked to "finish the phase."

**Verification:** Phase 0 suite. Confirm (manually, by reading the diff) that only `OS_VERSION`/`USER_AGENT` changed and `DEVICE_MODEL`/`MOBILE_ID` were left untouched.

---

## Phase summary table

| Phase | Depends on | Touches | Audit sections | Risk |
|---|---|---|---|---|
| 0 | — | (none, capture only) | — | none |
| 1 | 0 | `pyhon/` | 7.1–7.3, 8.1, 9.1, 9.2, 10.1 | low (isolated library) |
| 2 | 1 | integration `*.py` (structure only) | 13–17 | low (pure refactor) |
| 3 | 1, 2 | `__init__.py`, `coordinator.py` | 1.2–1.4 | medium (setup/unload path) |
| 4 | 2, 3 | `entity.py`, `coordinator.py`, `const.py` | 2.1, 2.2, 8.2 | medium (affects every entity's availability) |
| 5 | 2 | `climate.py`, `sensor.py`, sweep | 3.1, 3.2, §5 pattern | low–medium |
| 6 | 1, 3 | `config_flow.py` | §5 (Part 1) | low |
| 7 | 1–6 | new `tests/` | all | none (additive) |
| 8 | human sign-off | `pyhon/const.py` | 12 | policy-sensitive, technically low |
