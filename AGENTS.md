# ok-ww — AGENTS.md

Image-recognition automation for **Wuthering Waves** (鸣潮).  
Built on [ok-script](https://github.com/ok-oldking/ok-script) (~3000 LOC Python framework vendored at `ok/`).

## Python & Environment

- **Python 3.12 only.** No other version works.
- **Windows only.** Game window: `UnrealWindow` class, `Client-Win64-Shipping.exe`.
- **Must run from an ASCII-only path** (no Chinese, no spaces-in-some-builds). The framework checks this at startup.
- **Virtual environment (uv):** Managed with [uv](https://docs.astral.sh/uv/).
  ```bash
  uv venv                      # Create .venv
  .venv\Scripts\activate       # Activate (PowerShell)
  uv pip sync requirements.txt # Install all deps (faster than pip)
  uv pip install -r requirements.txt --upgrade  # Update deps
  ```
  The `.venv` directory is at the project root. Always activate it before running any commands.
- `requirements.txt` is auto-generated from `requirements.in` via `pip-compile`. Edit `.in` and re-compile, do not edit `.txt` directly.

## Entrypoints

| Command | Mode |
|---|---|
| `python main.py` | Release GUI |
| `python main_debug.py` | Debug GUI (sets `config['debug'] = True`) |
| `python -m ok run_task TaskName` | Headless task run (CLI) |
| `python main.py -t 1 -e` | Auto-start first task, exit on finish |

The `ok` CLI (`ok/__main__.py` / `ok/cli.py`) auto-discovers config via `src.config:config` or `config:config`.

## Architecture

```
ok/               ← ok-script framework (BaseTask, OK, device, capture, OCR, GUI)
src/              ← Game-specific logic
  task/           ← Tasks (one-time + trigger)
  char/           ← Character rotation logic (50+ chars)
    BaseChar.py   ← Contract: subclass overrides do_perform()
    CharFactory.py← Registry mapping labels → character classes
    CustomCharLoader.py ← Hot-reload character code from configs/custom_chars/
  char_combo/     ← Alternative combo-rotation implementations
  scene/          ← WWScene (combat/in_team detection)
  combat/         ← CombatCheck (combat state machine)
  gui/            ← Custom tabs (CharacterCodeTab, ComboTab)
  combo/          ← Combo rotation toggle system
  Labels.py       ← Enum of all template-matching feature names
  globals.py      ← Globals singleton (YOLO model, login state)
  OnnxYolo8Detect.py / OpenVinoYolo8Detect.py ← Echo detection
assets/           ← coco_annotations.json (feature templates), echo_model/ (YOLO ONNX)
configs/          ← Per-task JSON configs, custom_chars/ for user code
i18n/             ← UI translations (zh_CN, en_US, ja_JP, ko_KR, zh_TW)
```

## Key Source Files

- **`config.py`** — central config dict. Version `v3.4.7`. Defines tasks, capture, OCR, GUI, hotkeys.
- **`src/task/AutoCombatTask.py`** — the main trigger task for open-world auto-combat (loops fighting).
- **`src/task/BaseCombatTask.py`** — team management, switch logic, concerto detection, combat flow.
- **`src/char/CharFactory.py`** — character registry. **Add new characters here** by mapping a label to a class with `char_type` and `ring_index`.
- **`src/char/BaseChar.do_perform()`** — the method every character subclass overrides for rotation logic.

## Character System

### Adding a new character

1. Create `src/char/<Name>.py` with a class extending `BaseChar`.
2. Override `do_perform()` — this is the on-field rotation.
3. Register in `src/char/CharFactory.py` `_char_dict_raw` with label, class, `char_type` and `ring_index` (element).
4. Add the label to `src/Labels.py` if new.

### Rotation conventions

- Use helpers from `BaseChar` (not raw keys): `click_resonance()`, `click_liberation()`, `click_echo()`, `heavy_attack()`, `continues_normal_attack()`, `switch_next_char()`.
- Keep loops bounded by timeouts. Call `self.task.next_frame()` while waiting.
- `do_perform()` should end with `self.switch_next_char()` to pass control.
- Override `get_switch_priority()` for special team-ordering logic (MUST/NO/NORMAL).
- Override `on_combat_end()` for combat cleanup (e.g., switch to healer).
- See `src/char/Sanhua.py` (simple, 35 lines) or `src/char/Camellya.py` (complex forte tracking) as examples.

### CustomCharLoader (hot-reload)

Characters can have custom code in `configs/custom_chars/<ClassName>.py` that replaces their class at runtime without restart. Managed via the CharacterCodeTab GUI. The combo rotation system (`src/combo/`) uses this to install alternative rotation logic from `src/char_combo/`.

## Task System

Two kinds, configured in `config.py` under `onetime_tasks` and `trigger_tasks`:

- **One-time tasks** (e.g., DailyTask, FarmEchoTask) — run a finite workflow then stop.
- **Trigger tasks** (e.g., AutoCombatTask, AutoPickTask) — run continuously on a `Trigger Interval` (default 1 s).

All tasks extend `BaseTask` (from `ok/`). The game scene hierarchy:  
`BaseWWTask → CombatCheck → BaseCombatTask → concrete tasks`.

## Config

- Main config → `config.py` dict, version `v3.4.7`.
- Per-task configs → `configs/<TaskName>.json` (auto-saved by framework).
- Global options → `configs/Basic Options.json` (hotkeys, start/stop, DirectML, mute, etc.).
- Hotkeys → `configs/Game Hotkey.json` (q/r/e/t/space/lshift/tab defaults).
- `use_gui: True` for GUI mode, `False` for headless.

## Input & Capture

- **Interaction**: `PostMessage` (background key/mouse simulation to game window).
- **Capture**: `WGC` preferred, `BitBlt_RenderFull` fallback.
- **OCR**: `onnxocr` with OpenVINO acceleration (`use_openvino: True`).
- **Template matching**: COCO-format annotations at `assets/coco_annotations.json`.
- **YOLO echo detection**: `assets/echo_model/echo.onnx`, loaded lazily via `src/globals.py`.
- Supported resolutions: 16:9, 2560×1440 / 1920×1080 / 1600×900 / 1280×720 (min 1280×720).

## Testing

- Based on `unittest`, runner at `ok/test/RunTests.py`.
- Base class: `ok/test/TaskTestCase.py`.
- Tests need a game window / capture device (integration tests, not unit-only).
- Run: `cd <project_root> && python -m unittest discover tests/`
- The `ok/test/OKTestRunner.py` provides additional test infrastructure.

## Build / Packaging

- Build config: `pyappify.yml` — profiles `China` (with UAC, Python 3.12, signed) and `Global`.
- `pyappify` packager produces `ok-ww-win32-China-setup.exe`.
- EXE signed via [SignPath.io](https://signpath.io/).

## CLI Headless Usage

```bash
# Run task by index (1-based)
python main.py -t 1 -e

# Run task by name (installed ok-script package)
python -m ok run_task DailyTask -e

# CLI arguments
-t, --task    Task index or name
-e, --exit    Exit after task completes
-d, --debug   Enable debug mode
-c, --config  Config import target (default: src.config:config)
```

## Important Dev Commands

```bash
pip install -r requirements.txt --upgrade   # Install/update deps
python main.py                               # Release GUI
python main_debug.py                         # Debug GUI
python -m ok run_task TaskName               # Headless task
python -m unittest discover tests/           # Run tests
```

Available `ok.yml` profiles: `default` (main.py), `direct-ml` (main_direct_ml.py), `debug` (main_debug.py).

## Quirks & Gotchas

- **PATH workaround**: `os.environ['PATH']` is set to `""` early in both `ok/__init__.py` and `config.py` to avoid a PySide6 `KeyError: 'PATH'` issue.
- **Start/Stop toggle**: Bound to F9 by default. Also toggled via GUI.
- **Auto-resize**: Enabled by default. Resizes game to a supported resolution.
- **Kill launcher after start**: Enabled by default.
- **Monthly card popup**: All tasks check for it via `check_for_monthly_card()`.
- **DirectML**: Auto-enabled if free NVIDIA GPU memory > 3000 MiB and Windows build ≥ 18362. Configurable in Basic Options.
- **Blur area**: Configurable for sensitive regions of the screen.
- **Concurrent instance**: Mutex check enabled by default.
- **English-only path** (ASCII): The framework checks and refuses to start otherwise.
- **HDR**: Detection disabled by default (`check_hdr: False`). Night light detection enabled.
- The `_ok.json` config file stores window position/size/maximized state.
- Logs go to `logs/ok-ww.log` and `logs/ok-ww_error.log` (auto-rotating daily).

## Conventions

- Type annotations are used (see `BaseChar`, `CharFactory`).
- All labels/template names go in `src/Labels.py` as `str` enum members.
- Character registry in `CharFactory._char_dict_raw` uses `Labels` enum values as keys.
- Character file naming: `<ClassName>.py` in `src/char/`, PascalCase class name matching the game character name.
- Combo rotation implementations: `src/char_combo/<ClassName>.py`.
- Documentation is in Chinese (README) and English (README_en.md). Code comments are bilingual.
- Git commits often contain multiple contributors' work in single squashed merges.

## Available Agent Skill

`ok-ww-hezhou` — Provides in-depth knowledge about 合轴 (concerto rotation / switch) mechanics, underlying game systems, rotation methodology, and how to apply these to character auto-combat scripts. Load via `skill(name="ok-ww-hezhou")` when implementing or reviewing character rotations.
