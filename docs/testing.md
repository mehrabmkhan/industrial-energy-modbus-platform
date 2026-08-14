# Testing

The test suite covers:

- register encoding and decoding
- coherent measurement block generation
- alarm threshold behavior
- device configuration validation
- SQLite storage and CSV export
- FastAPI OpenAPI loading

Run locally:

```powershell
pytest -q
```

Compile package and web modules:

```powershell
python -m compileall src web
```

GitHub Actions runs the same checks on push and pull request.
