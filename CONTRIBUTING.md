# Contributing to Elica Connect Plus

Thanks for your interest! Contributions of any size are welcome.

## The most valuable contribution: capability codes

The Elica cloud API is undocumented. If you own a hood with a different
`dataModelIdx`, or you discover the codes for air quality / AUTO / light
color, please open an issue with:

- Hood model and `dataModelIdx` (visible in the diagnostics download)
- The capability codes you identified and their observed values
- How you verified them (diagnostics diff or mitmproxy capture)

Use the **Capability report** issue template.

## Development setup

```bash
git clone https://github.com/marturano/elica-connect-plus
cd elica-connect-plus
python -m venv .venv && source .venv/bin/activate
pip install -r requirements_test.txt
pytest tests/
```

## Pull requests

- One topic per PR (a fix, a feature, a refactor — not all three)
- New behaviour needs a test; the suite must stay green (`pytest tests/`)
- Follow the existing code style (async-first, type hints, `_LOGGER` for
  logging, constants in `const.py`)
- Never commit credentials, tokens, serial numbers or diagnostics dumps
  that haven't been redacted
- Update `CHANGELOG.md` under an *Unreleased* heading

## Reporting bugs

Attach the redacted diagnostics download (Settings → Devices & services →
Elica Connect Plus → ⋮ → Download diagnostics) and relevant log lines
(`custom_components.elica_connect_plus` logger, debug level can be enabled
via `logger:` in `configuration.yaml`).

## Code of conduct

Be kind. This is a hobby project maintained in spare time.
