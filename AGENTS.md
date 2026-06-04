# Agent Instructions

## Commands

```powershell
.\.venv\Scripts\python.exe main.py              # release
.\.venv\Scripts\python.exe main_debug.py        # debug mode
.\.venv\Scripts\python.exe -m unittest tests\TestXXX.py  # single test
.\run_tests.ps1                                 # all tests
```

## Testing

- **`unittest`** framework, **NOT pytest**. Base class: `ok.test.TaskTestCase.TaskTestCase`.
- Test images in `tests\images\`. Set with `self.set_image('tests/images/xxx.png')`.
- CI runs all `tests/*.py`: `python -m unittest discover -s tests -p "*.py"`.

## Registration (new tasks / characters / labels)

- **Tasks**: add `["src.task.ModuleName", "ClassName"]` to `config.py:138` `onetime_tasks` or `config.py:150` `trigger_tasks`.
- **Characters**: class under `src/char/`, register via `CharFactory`.
- **Labels**: add to `src/Labels.py` enum for new image template features.

## Key Quirks

- **Python 3.12 only**, Windows-only (pywin32, PostMessage, WGC/BitBlt capture).
- git submodule `ok_templates/` — run `git submodule update --init --recursive` if empty.
- `.agents/skills/` has repo-specific skills: deploy, ok-script-tasks, ok-ww-characters, ok-script-i18n, use-local-venv.
