# Elica Connect Plus

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/marturano/elica-connect-plus/actions/workflows/validate.yml/badge.svg)](https://github.com/marturano/elica-connect-plus/actions/workflows/validate.yml)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![HA min](https://img.shields.io/badge/Home%20Assistant-2024.11%2B-41BDF5.svg)

Enhanced Home Assistant integration for **Elica Connect** range hoods
(ESP32-C6 based, app `com.replyconnect.elica`). Fork of
[benedettosiddi/elica-connect-ha](https://github.com/benedettosiddi/elica-connect-ha)
with hardened cloud connectivity, optional features and a full test suite.

🇮🇹 [Italiano](README.it.md) · 🇩🇪 [Deutsch](README.de.md) · 🇪🇸 [Español](README.es.md) · 🇫🇷 [Français](README.fr.md)

> Verified on: **Elica Illusion** (dataModelIdx 8, PRF0199706) — compatible with all **Elica Connect** hoods, see [Compatibility](#compatibility) — HA 2024.11+, verified on 2026.7

## Features

| Entity | Type | Description |
|--------|------|-------------|
| Fan | `fan` | Named presets low/medium/high/boost + percentage; optional auto preset |
| Light | `light` | On/off + brightness; optional tunable white with named presets |
| Ambient light | `light` | Optional secondary light: dimmer + tunable white |
| Filter | `sensor` | Grease filter efficiency % |
| Air quality | `sensor` | Optional (see [Optional features](#optional-features)) |
| Timer | `number` | Optional native auto-off timer (minutes) |

Real-time state via **cloud MQTT push** (`cloudprodmqtt.elica.com`), with a
5-minute REST sanity poll. Commands are optimistic: the UI reacts instantly
and reverts automatically if the cloud rejects the command.

## Compatibility

| Hood | Status |
|------|--------|
| **Elica Illusion** (dataModelIdx 8) | ✅ Fully verified: all capability codes confirmed on a real device (see table below) |
| Any other **Elica Connect** hood (app `com.replyconnect.elica`) | ✅ Compatible: core entities (fan, main light, filter) work out of the box; model-specific features are enabled via the built-in **code finder** — see [DISCOVERY.md](custom_components/elica_connect_plus/DISCOVERY.md) |

The cloud API is the same for the whole Elica Connect range; only the
capability codes of some features vary by model. That is exactly what the
Options + code finder workflow is for: identify the codes on your hood once,
enter them, done. Please share what you find via a
[Capability report](../../issues) issue.

## Improvements over the original integration

- **Resilient MQTT push** — automatic reconnect with backoff; when the OAuth
  token expires, fresh MQTT credentials are pushed to the client so push
  updates never silently die
- **Proactive token refresh** based on the JWT `exp` claim (no 401 round-trips)
- **Reauthentication flow** — a changed Elica password triggers the standard
  HA reauth banner instead of a permanent setup error
- **Duplicate protection** — one config entry per hood (`unique_id`)
- **Robust optimistic state** — no UI bounce-back after commands; rollback
  on cloud errors
- **Downloadable diagnostics** with sensitive-data redaction
- **Options flow** for capability codes of not-yet-mapped features
- **Configurable MQTT broker** (host/port) in the Options, so a future
  Elica broker change needs no new release
- **Test suite** — 20 tests via `pytest-homeassistant-custom-component`

## Installation

### HACS (recommended)

1. HACS → ⋮ → *Custom repositories* → add this repository as **Integration**
2. Install **Elica Connect Plus** and restart Home Assistant
3. *Settings → Devices & services → Add integration* → **Elica Connect Plus**
4. Enter your Elica Connect app credentials

### Manual

Copy `custom_components/elica_connect_plus/` into your HA
`custom_components/` folder and restart.

> **Migrating from the original integration?** Remove it first: the domain
> is different (`elica_connect_plus`), so entity IDs will change — review
> your automations.

## Optional features

Air quality, AUTO mode and light color use dataModel capability codes that
are **not yet publicly documented** and may vary by model. The integration
supports them out of the box, gated behind the integration Options:

1. Discover the codes on *your* hood following
   [DISCOVERY.md](custom_components/elica_connect_plus/DISCOVERY.md)
   (two diagnostics downloads, no extra tools needed)
2. Enter them in *Settings → Devices & services → Elica Connect Plus →
   Configure*
3. The integration reloads itself and the new entities/features appear

Found the codes for your model? Please
[open an issue](../../issues) so they can be documented for everyone.

## Confirmed capability codes — Elica Illusion (dataModelIdx 8)

| Code | Function | Values |
|------|----------|--------|
| 64 | Fan mode | 1=normal, 4=boost |
| 96 | Light brightness | 0–100 (%; 0=off) |
| 110 | Fan speed | 0=off, 1–3 |
| 97 | Light color (tunable white) | 0=warm – 100=cold |
| 64 | Fan mode (extended) | 16=auto (bitmask: 1=normal, 4=boost, 16=auto) |
| 112 | Air quality | 1=ottima … 5=pessima; published only while the sensor is active (auto mode) |
| 432 | Auto-off timer | minutes (firmware countdown to 0) |
| 100 | Ambient light brightness | 0–100 (%; 0=off); dimmer only, no color |

## Languages

English (default), Italian, German, Spanish and French, following the
Home Assistant UI language: entity names, options dialog, fan preset names,
light effect names and air quality states are all localized via
`translations/`. Automations use the language-neutral slugs (`medium`,
`very_warm`, `fair`, ...). PRs adding languages are welcome — copy
`translations/en.json` and translate.

## Example automations

See [docs/automations.md](docs/automations.md) for ready-to-use YAML:
cooking auto-start, delayed switch-off, filter maintenance alerts,
courtesy night light.

Prefer round preset buttons over the default dropdowns? See the optional
[dashboard guide](docs/dashboard.md) (native YAML or `custom:button-card`).

Using Amazon Alexa? See the optional [Alexa guide](docs/alexa.md) for voice
control and spoken announcements (some examples need the Alexa Media Player
custom integration).

## Development

```bash
pip install -r requirements_test.txt
pytest tests/
```

CI runs the test suite plus [hassfest](https://developers.home-assistant.io/docs/creating_integration_manifest/#validation)
and [HACS validation](https://github.com/hacs/action) on every push.

## License

Released under the [MIT License](LICENSE), © 2026 Roberto Marturano.

This project is a fork of and builds upon
[elica-connect-ha](https://github.com/benedettosiddi/elica-connect-ha) by
[@benedettosiddi](https://github.com/benedettosiddi) — full credit to their
original reverse-engineering work.

## Credits

Cloud API reverse-engineered via mitmproxy by
[@benedettosiddi](https://github.com/benedettosiddi), whose work this fork
builds upon.

## Disclaimer

**Elica Connect Plus is an independent, unofficial project. It is not
affiliated with, authorized by, or endorsed by Elica S.p.A.**, provider of
the Elica Connect system and its ecosystem. "Elica", "Elica Connect" and all
related names, marks and logos are trademarks of Elica S.p.A. or their
respective owners, used here for identification purposes only. This
integration relies on a reverse-engineered, undocumented interface that may
change or stop working at any time.

The software is provided "as is", without warranty of any kind. The authors
and contributors accept **no liability** for any damage to appliances or
property, malfunction, data loss, service disruption or account issues
arising from its use. **You use it entirely at your own risk.**

See [DISCLAIMER.md](DISCLAIMER.md) for the full text (available in English,
Italiano, Deutsch, Español and Français).
