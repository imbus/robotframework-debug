# Compatibility matrix

Acceptance suite (`tests/atest/suites`) run against each Robot Framework release in an isolated `uv` venv, each paired with a Python version inside that release's support window. Cells show passed/total tests.

| Feature area | RF 5.0.1<br/>(Py 3.10.19) | RF 6.0.2<br/>(Py 3.11.15) | RF 6.1.1<br/>(Py 3.11.15) | RF 7.0.1<br/>(Py 3.11.15) | RF 7.2.2<br/>(Py 3.12.8) | RF 7.3.2<br/>(Py 3.12.8) | RF 7.4.2<br/>(Py 3.12.8) |
|---|---|---|---|---|---|---|---|
| REPL basics | ✅ 9/9 | ✅ 9/9 | ✅ 9/9 | ✅ 9/9 | ✅ 9/9 | ✅ 9/9 | ✅ 9/9 |
| REPL commands | ✅ 16/16 | ✅ 16/16 | ✅ 16/16 | ✅ 16/16 | ✅ 16/16 | ✅ 16/16 | ✅ 16/16 |
| Debug keyword | ✅ 6/6 | ✅ 6/6 | ✅ 6/6 | ✅ 6/6 | ✅ 6/6 | ✅ 6/6 | ✅ 6/6 |
| Listener on error | ✅ 6/6 | ✅ 6/6 | ✅ 6/6 | ✅ 6/6 | ✅ 6/6 | ✅ 6/6 | ✅ 6/6 |
| Step debugging | ✅ 5/5 | ✅ 5/5 | ✅ 5/5 | ✅ 5/5 | ✅ 5/5 | ✅ 5/5 | ✅ 5/5 |
| **Total** | **✅ 42/42** | **✅ 42/42** | **✅ 42/42** | **✅ 42/42** | **✅ 42/42** | **✅ 42/42** | **✅ 42/42** |

## Notes
All tested Robot Framework versions pass the full suite.
