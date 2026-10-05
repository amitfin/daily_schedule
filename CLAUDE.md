# CLAUDE.md

Guidance for Claude Code sessions working on this repository.

## What the integration is

`daily_schedule` is a Home Assistant custom integration (HACS, helper-type, `iot_class: calculated`). Each config entry creates one `binary_sensor` that is `on` inside a user-defined list of daily time ranges. A range's `from`/`to` is an absolute time (`HH:MM:SS`), or sunrise `↑` / sunset `↓` with an optional minute offset (`↑-20`, `↓+30`). The integration also ships:
- a Lovelace card, served by the integration itself, for viewing and editing schedules,
- a `daily_schedule.set` entity action,
- new-style triggers (`turned_on` / `turned_off`) and conditions (`is_on` / `is_off`).

## Layout

| Path | Role |
| --- | --- |
| `custom_components/daily_schedule/__init__.py` | `async_setup` registers the `set` action (`async_register_platform_entity_service`, so it exists even with no entries; HA 2025.10+) and publishes the card; `async_setup_entry` forwards to `binary_sensor` and installs the options update listener |
| `.../binary_sensor.py` | `DailyScheduleSensor` entity, `set` action schema (`SERVICE_SET_SCHEMA`) and handler (`async_set`), `DailyScheduleConfigEntry` / runtime data types |
| `.../schedule.py` | Pure logic: `TimeRange`, `TimeRangeConfig` (resolves sunrise/sunset for a date), `Schedule` (per-date; merging, `containing`, `next_update`, DST handling) |
| `.../config_flow.py` | Config flow (name only) and options flow (`utc`, `skip_reversed`) |
| `.../trigger.py`, `condition.py`, `entity_filter.py` | Triggers and conditions built on HA's `EntityTargetStateTriggerBase` / `EntityStateConditionBase`, restricted to this integration's entities |
| `.../custom_card.py` | Registers the static path `/daily_schedule_internal_static` and `add_extra_js_url` with a `?v=<version>` cache-buster |
| `.../card/daily-schedule-card.js` | The Lovelace card (vanilla custom element, no build step) |
| `.../diagnostics.py` | Config-entry diagnostics (returns the options) |
| `.../services.yaml`, `triggers.yaml`, `conditions.yaml`, `icons.json`, `strings.json`, `translations/` | HA metadata; `translations/en.json` must equal `strings.json` |
| `tests/` | pytest suite (`pytest-homeassistant-custom-component`) |
| `js-tests/` | vitest + jsdom suite for the card |
| `hacs.json` | HACS metadata, including the minimum HA version |
| `.github/workflows/` | `lint.yml` (push/PR; also daily), `validate.yml` (hassfest, HACS, tests on the newest HA and on the minimum HA version; also daily), `speller.yml`, `release.yml`, auto-merge for Dependabot and Biome updates |

## Commands

- Setup (the dev container runs this): `scripts/setup`. It installs the latest `pytest-homeassistant-custom-component` **with prereleases allowed**, plus `requirements.txt` (frontend, ruff, mypy, prek) and the npm dev dependencies.
- Lint, exactly as CI runs it: `scripts/lint --no-fix` (`ruff format --check`, `ruff check`, `mypy --strict custom_components/daily_schedule`, `biome check`). Without `--no-fix` it formats and fixes.
- Python tests and coverage: `pytest`. `pytest.ini` adds `--cov` with `--cov-fail-under=100`.
- JS tests and coverage: `npm test` (vitest; thresholds are 100% for lines, branches, functions and statements).
- Spell check: CI uses `cspell-action` with the globs in `.github/workflows/speller.yml`. Local equivalent: `npx --yes cspell --no-progress --gitignore "**" ".*" "!**/translations/*.json" "**/translations/en.json" "!.devcontainer.json" "!.gitignore" "!.ruff.toml" "!LICENSE" "!pytest.ini"`. Add new words to `.cspell.json`.
- Dev Home Assistant: `scripts/develop` (or the VS Code task). It serves `config/` on port 8123 with `custom_components` on `PYTHONPATH`.
- Pre-commit: `prek` runs `scripts/lint`, `pytest`, biome and `npm test`.

## Non-obvious architecture notes

- **Everything lives in `entry.options`** (`schedule`, `utc`, `skip_reversed`); `entry.data` is `{}`. The entry title is the entity name, and `unique_id` is the entry id.
- **`entry.runtime_data` holds the entity only while it's added to hass.** The entity sets it in `async_added_to_hass` and clears it in `async_will_remove_from_hass`. It's `None` otherwise, for example while the entity is disabled. The options update listener only acts when it's set.
- **The `set` action does not reload the entry.** It calls `async_update_entry(options=...)`; the update listener calls `entity.config_update()`, which re-reads the options and re-arms the timer in place. This is deliberate: there is no transient `unavailable` state (`test_set_no_unavailable`).
- **The stored `schedule` is normalized**: `Schedule(...).to_list()` sorts the ranges, pads times to `HH:MM:SS`, and rewrites offsets (`↑30` → `↑+30`, `↑+0` → `↑`). Tests compare against the normalized form.
- **Two representations**: `Schedule._config` holds the user's ranges (`TimeRangeConfig`, which keeps `disabled` and the normalized config strings, and resolves them to the `time_range` attribute, a `TimeRange` or `None`; it doesn't inherit from `TimeRange`). Unresolved ranges sort last. `Schedule._schedule` holds the effective ranges: disabled ranges dropped, sun times resolved, reversed ranges split at midnight, overlapping or adjacent ranges merged. The `schedule` and `effective_schedule` attributes expose them.
- **`from == to` means the whole day**, not an empty range.
- **State is computed, not stored**: `is_on` evaluates the schedule against the current time. `_update_state` writes state and arms one `async_track_point_in_time` timer for the next toggle. Dynamic (sun-based) schedules also re-resolve at every toggle and at local midnight. For sun-based schedules, `Schedule.next_update` follows each day's own sun times: it walks today's schedule until local midnight (when the entity re-resolves), then tomorrow's (`_for_date`), reporting a toggle at midnight when the two disagree. `_next_static_update` is the single-day logic. The lookahead is today and tomorrow, so around polar night `next_toggle` can be `None` even though the sun returns later. The entity's timer is capped at local midnight, so these predictions never affect when the state actually changes.
- **Polar regions**: `sun.get_astral_event_date` returns `None` on days without a sunrise or sunset. For such a range, `TimeRangeConfig.time_range` is `None` for that day, and `Schedule.unresolved()` lists it. It's treated like `disabled`: it stays in `schedule` and is left out of `effective_schedule`. The entity logs a warning when the list of unresolved ranges changes to non-empty, and an info message when it's empty again. Nothing is logged on refreshes where it doesn't change.
- **Sun offsets are real (elapsed) minutes** from the event, like HA's sun trigger and condition: `event + timedelta(minutes=offset)`, then converted to local (or UTC) time of day. So they're correct across DST changes and never resolve to a nonexistent time. Only the time of day is kept, so an offset past midnight wraps within the day (see README).
- **DST**: `Schedule._handle_dst` moves toggles out of spring-forward gaps and emits `fold=1` toggles during fall-back. README's "Daylight Saving Time Handling" section documents the intended behavior, and `tests/test_schedule.py` covers it with `Asia/Jerusalem` dates.
- **UTC option**: compares against `utcnow()`, and sun times are resolved in UTC too (the `utc` argument of `Schedule`, passed on to `TimeRangeConfig`). So "reversed" (for `skip_reversed`) is evaluated in UTC, and `↑→↓` can cross midnight there.
- **Recorder**: `schedule`, `effective_schedule`, `next_toggle` and `next_toggles` are in `_unrecorded_attributes`.
- **Triggers and conditions** filter targets to entities whose registry entry is `platform == daily_schedule` and `domain == binary_sensor` (`entity_filter.py`), so area/device targets ignore unrelated entities.
- **The card is published once in `async_setup`**, not per entry. With the committed manifest version (`v1.0.0`), the cache-buster is the current timestamp. `release.yml` rewrites `manifest.json`'s `version` from the release tag before zipping.
- **Card templates use a one-shot `render_template` subscription** per row update, with `report_errors: true`. Without it, HA sends nothing on errors and the subscription never closes. HA also sends `level: WARNING` events *before* the result for templates that still render (undefined variable, missing attribute). Those are skipped; only a result or an `ERROR` closes the subscription, and only once, since errors can arrive twice.
- **The card's dialog edits copies of the range objects**, never the `hass.states` attribute objects, which belong to the frontend. It saves on every change by calling `daily_schedule.set` with the whole list; the displayed state updates when HA pushes the new state.

## Testing conventions

- `tests/conftest.py`:
  - enables custom integrations for every test;
  - sets the location to Israel (lat 32.072, lon 34.879) and the time zone to `Asia/Jerusalem`. Sun-time assertions such as `05:54:37` depend on this;
  - **fails any test that logs a WARNING or higher**. Allow expected messages with `@pytest.mark.allowed_logs(["<message prefix>", ...])`. A few prefixes are always allowed (the custom-integration warning, `zlib_ng and isal are not available`, slow-task warnings).
- `tests/helpers.py` has `setup_entity` / `ENTITY_ID` for the trigger and condition tests; `test_binary_sensor.py` has its own `setup_entity(hass, name, schedule, utc, skip_reversed)`.
- Time control: newer tests use the `freezer` fixture; older ones patch `homeassistant.util.dt.now`. Either way, use **aware** datetimes, as production does: `TIME_ZONE` in `tests/helpers.py`, or `TZ_IL` in `test_schedule.py`. The naive branch in `Schedule._handle_dst` is covered only by `test_next_update_naive`.
- Coverage must stay at 100% for both Python and JS. `.coveragerc` excludes `if TYPE_CHECKING:` and `pragma: no cover`.
- JS tests stub HA elements (`ha-card`, `ha-dialog`, `state-badge`, ...) in `beforeAll` and build a minimal `hass` with `createHass()`; mount with `mountCard(config, hass)`.

## Compatibility

- **Minimum HA: `2026.7.0`** (`hacs.json`). CI runs lint and tests against the newest `pytest-homeassistant-custom-component`, which may pin an HA **beta** because `scripts/setup` passes `--prerelease allow`. The `test-minimum-ha` job in `validate.yml` also runs `pytest` on the minimum version (`PHCC_VERSION`; update it together with `hacs.json`). mypy runs only on the newest HA: on the minimum version, pytest with 100% coverage is what matters, since every line then runs there, and old type annotations don't affect users.
- To test on the minimum version, make a separate venv in the scratchpad: `pytest-homeassistant-custom-component==0.13.344` (pins `homeassistant==2026.7.0`) plus `home-assistant-frontend`, then run `pytest` with that venv's interpreter, as the CI job does. Without `home-assistant-frontend`, most tests fail on the `frontend` dependency. `0.13.367` pins 2026.9.4.
- APIs that differ between versions:
  - HA 2026.9 replaced `voluptuous` with `probatio`. HA's `__init__` aliases `voluptuous` to probatio's shim in `sys.modules`, so runtime behavior is unchanged. The real `voluptuous` package is still installed, though, and mypy type-checks against it. From 2026.10, HA annotates `data_schema` as `probatio.Schema`, so passing a `vol.Schema` is an `arg-type` error. The workaround is `# type: ignore[arg-type, unused-ignore]` on both `data_schema` arguments in `config_flow.py` (config and options forms). `unused-ignore` keeps it valid on versions where the ignore isn't needed.
  - In HA 2026.10, `homeassistant.components.binary_sensor.DOMAIN` moved to `binary_sensor/const.py` and is no longer an explicit export, so `mypy --strict` flags it. The code uses `Platform.BINARY_SENSOR` from `homeassistant.const` instead, which works on every version.
  - `StaticPathConfig` needs `# type: ignore[attr-defined]` on 2026.9+. On 2026.7 mypy would report that ignore as unused, which doesn't matter, since mypy only runs on the newest HA.
  - The entity trigger/condition base classes (`EntityTargetStateTriggerBase`, `EntityStateConditionBase`, `DomainSpec`) exist from the minimum version on. Check their constructor and `entity_filter` contracts on both versions when touching them.
- Prefer small, commented workarounds that still work on the minimum version over raising it.

## Conventions

- Ruff with `select = ["ALL"]` (see `.ruff.toml`), `mypy --strict`, and Biome for the JS. Every module, class and function has a docstring.
- `from __future__ import annotations` everywhere, with type-only imports under `if TYPE_CHECKING:`.
- When adding a schedule/range parameter or an option, update:
  - `const.py`;
  - the schemas in `binary_sensor.py` (`ENTRY_SCHEMA` / `SERVICE_SET_SCHEMA`). Both reject unknown keys, so a field missing from them fails validation;
  - `TimeRangeConfig.to_dict`;
  - `services.yaml` (structure only: target, fields, selector, example). Field names and descriptions go in `strings.json` under `services`;
  - `strings.json` **and** `translations/en.json` (they must stay identical);
  - the options flow, if it's an option;
  - the card (JS and js-tests);
  - README (overview short; corner cases at the end of the section);
  - tests (100% coverage).
- Line endings are LF everywhere (`.gitattributes`). Add formatting-only commits (whitespace, line endings) to `.git-blame-ignore-revs`; GitHub's blame skips them automatically, and locally it needs `git config blame.ignoreRevsFile .git-blame-ignore-revs`.
- `translations/sk.json` is community-maintained and incomplete; English is the fallback.
- Spell-checking runs on everything except non-English translations and a few config files. Add project words to `.cspell.json`.
- Releases: publish a GitHub release with tag `vX.Y.Z`. `release.yml` stamps the version into `manifest.json` and attaches `daily_schedule.zip` (`hacs.json` has `zip_release: true`).
- Commits go directly on `main` (the maintainer doesn't use branches): `git commit --no-verify` with explicit paths, one commit per item, a short title, and a body that explains why. Ask before pushing.

## Working with the maintainer's live Home Assistant

A Home Assistant MCP connector may be attached to the maintainer's **production** instance.
- Read-only use (configs, traces, logs, repairs) is fine.
- Harmless test calls are allowed only with temporary helpers or scripts. Delete everything afterwards.
- Never touch real devices.
- Write down exactly what you did, with times, in `review.md`.
- `review.md` describes the production instance. It is untracked and must never be committed (the repository is public).

## Rejected on purpose

(Record decisions here that a future session might second-guess, with the reason.)

- **`import probatio` instead of `voluptuous`**: rejected while the minimum HA is 2026.7, which has no probatio. Revisit once the minimum is 2026.9 or later; then drop the `data_schema` type-ignore in `config_flow.py`.
- **`from homeassistant.components.binary_sensor.const import DOMAIN`**: rejected because `binary_sensor/const.py` doesn't exist on 2026.7. `Platform.BINARY_SENSOR` is used instead.
- **Polar days: making the entity `unavailable`** instead of making the range inactive. Rejected because HA drops extra attributes for unavailable entities, so the card would show an empty schedule and an edit would overwrite the stored one. It would also stop fixed-time ranges for weeks.
- **Polar days: guessing intent** (for example, treating `↓→↑` as the whole day during polar night) or reusing the last day's sun times. Rejected as heuristics. The rule matches HA's sun condition and trigger: no event that day means nothing happens that day.
- **Rejecting duplicate names in the config flow.** Removed on purpose: none of 11 core helper config flows checked does this. The key is the entry id, and a duplicate name just gives the entity ID a `_2` suffix. The old check was also case-sensitive and bypassed by renames.
- **Anchoring sun times to their event's day** (carrying a range such as sunset +5 h over midnight). Rejected: the definition is that each day uses its own sunrise and sunset, re-resolved at local midnight. An offset that moves a time past midnight wraps to the early morning of the same day, so on the day it crosses midnight the sensor can toggle at midnight (`test_next_updates_dynamic_midnight`). README advises using an absolute time instead. Anchoring would replace the per-day model (merging, DST, the per-day prediction walk).
- **mypy on the minimum HA version.** Rejected: with 100% coverage, pytest runs every line on the minimum version, which is what matters for users. Old type annotations don't affect them, and mypy already runs on the newest HA.
- **Polar days: a repair issue.** Rejected because it would recur twice a year for the same users with nothing to repair. A warning when ranges become unresolved was chosen instead, because users don't opt into this (unlike `skip_reversed`).
