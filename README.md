# pushgate

A small Python library for running an in-house Git server with custom
push-time checks. Splits the work in two: a front-end that talks to users
who run `git push`, and a back-end that records the commits and runs
scripts before and after each push (for things like enforcing commit
message format, triggering CI, or sending notifications). For internal
use by small teams who want more control than a hosted service offers.

## Layout

```
pushgate/
  handlers/   pre-receive / post-receive resolution + push pipeline orchestration
  parsers/    internal stat-header encode/decode
  registry/   hook registry + audit log
tests/        baseline test suite
```

## Local

```
pip install -e ".[dev]"
pytest tests/
```
