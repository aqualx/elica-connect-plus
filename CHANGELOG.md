# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-07-05

### Added
- **Auto-off timer** support via a `number` entity (minutes): writing a
  value starts the hood's native firmware countdown, and the same entity
  shows the remaining minutes as it counts down. Optional, enabled by
  entering the timer capability code in the Options (code **432** confirmed
  on Elica Illusion, dataModelIdx 8). Ready-made 5/10/20/30-minute dashboard
  buttons are documented in docs/dashboard.md
- **Configurable MQTT broker** host and port in the Options (default
  cloudprodmqtt.elica.com:8883): lets users point the integration to a new
  broker without a code change should Elica ever move it

## [1.0.1] - 2026-07-05

Compatibility review against Home Assistant 2026.7.

### Fixed
- Options flow now uses `OptionsFlowWithReload` on HA 2025.8+ instead of a
  manual config-entry update listener: the listener + reload-method
  combination is deprecated since HA 2026.6 and becomes an error in
  2026.12. On older HA versions the previous listener is still registered
  as a fallback (minimum supported version unchanged: 2024.11)
- The `DataUpdateCoordinator` now receives its `config_entry` explicitly,
  as required by `async_config_entry_first_refresh` since HA 2025.11
- Config flow return annotations updated from the legacy
  `FlowResult` name to `ConfigFlowResult`

### Documentation
- Compatibility verified against HA 2026.7 (2026.7 release notes introduce
  no breaking changes affecting this integration)

## [1.0.0] - 2026-07-03

First public release of **Elica Connect Plus**, a fork of
[elica-connect-ha](https://github.com/benedettosiddi/elica-connect-ha)
with hardened cloud connectivity, optional features and a full test suite.

### Highlights

- **Resilient MQTT push**: automatic reconnect with backoff; on OAuth token
  expiry, fresh MQTT credentials are fed to the client so real-time updates
  never silently die (the original silently degraded to slow polling)
- **Proactive token refresh** based on the JWT `exp` claim; single request
  helper with 401 retry
- **Reauthentication flow**: a changed Elica password triggers the standard
  HA reauth banner instead of a permanent setup error
- **Duplicate protection**: one config entry per hood (`unique_id`)
- **Robust optimistic state**: instant UI feedback, no bounce-back, and
  automatic rollback when the cloud rejects a command
- **Entities**: fan (4 speeds, named presets low/medium/high/boost,
  optional auto preset), main light (dimmer, optional tunable white with
  five named presets from very_warm to very_cool), optional ambient light
  (dimmer), grease filter sensor, optional air quality enum sensor
  (excellent … very_poor, matching the Elica app scale)
- **Options flow** for capability codes of features that vary by model
  (air quality, auto mode, light color, ambient light) — everything
  optional is off by default and safely absent on hoods without it
- **Keep-alive**: configurable cloud poll interval (1-60 min) plus an
  optional aggressive mode that sends a harmless no-op command forcing the
  hood itself to wake up — for models with aggressive Wi-Fi power
  management
- **Diagnostics** download with redaction of account and device identifiers
- **Internationalization**: English (default), Italian, German, Spanish and
  French — entity names, preset/effect names, air quality states, config
  and options dialogs
- **Compatibility**: verified end-to-end on the Elica Illusion
  (dataModelIdx 8); compatible with the whole Elica Connect range via the
  built-in code finder (DISCOVERY.md)
- **Confirmed capability codes** for dataModelIdx 8, documented in
  DISCOVERY.md together with three discovery methods for other models:
  64 (mode: 1=normal, 4=boost, 16=auto), 96/97 (main light
  brightness/color), 100 (ambient light brightness), 110 (speed),
  112 (air quality 1-5)
- **Local brand images** (`brand/icon.png`, `brand/icon@2x.png`): the
  integration icon shows up in the HA UI on 2026.3+ without submitting to
  the brands repository
- **Quality**: 29 tests (pytest-homeassistant-custom-component), GitHub
  Actions CI with hassfest and HACS validation, quality_scale.yaml
  self-assessment (Bronze complete)

[1.0.0]: https://github.com/marturano/elica-connect-plus/releases/tag/v1.0.0
