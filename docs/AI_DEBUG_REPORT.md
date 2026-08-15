# AI Debug Report

- Date/time: 2026-08-15 16:58:37 +05:00
- Status: Verified

## Behavior investigated

Whether local Python virtual-environment folders are protected from accidental
Git commits.

## Problem and root cause

The repository contained an untracked `.venvv/` local virtual environment.
Git ignored `.venv/`, but `.gitignore` did not contain a rule for `.venvv/`.
This made `.venvv/` a possible accidental commit candidate.

## Files changed

- `.gitignore` - adds `.venvv/` to the ignored virtual-environment folders.
- `tests/test_repository_hygiene.py` - adds automated Git-ignore checks.
- `docs/AI_DEBUG_REPORT.md` - this debugging record.
- `PROJECT_STATUS.md` - records the completed milestone.

No model, dataset, notebook, image, credential, or remote service changed.

## Automated checks created

`tests/test_repository_hygiene.py` verifies that:

1. `.venv` is ignored (existing normal behavior).
2. `.venvv` is ignored (the repaired behavior).
3. `.venv_backup` is not ignored, so the rule is not unnecessarily broad.

## Commands executed

```text
.\.venv\Scripts\python.exe -m unittest tests.test_repository_hygiene -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "load saved configuration and model"
git diff --check
```

## Real before/after results

Before the fix, the targeted test failed because Git did not ignore `.venvv`.
The normal `.venv` check and the non-broad-rule check passed.

After adding the one `.gitignore` rule, the targeted check passed: 2 tests
passed. The full suite passed: 5 tests passed. The local saved-model load check
also passed and confirmed the expected 224 x 224 input shape.

## Remaining limitations and unverified areas

- The check covers `.venv` and the observed `.venvv` typo only; a differently
  named future environment would need its own explicit ignore rule.
- The live public app was not changed or exercised in this debugging task.
- No model was retrained or re-evaluated, and no protected test data was used.

## Plain-language explanation

Git uses `.gitignore` as a "do not upload" list. We added the missing name of
the extra local environment folder. The new test checks that both environment
folder names stay outside Git, while ordinary folders with similar names remain
visible to Git.
