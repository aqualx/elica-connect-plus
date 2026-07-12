# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-07-11

First stable release of **Elica Connect Plus**, a fork of
[elica-connect-ha](https://github.com/benedettosiddi/elica-connect-ha) with
hardened cloud connectivity, optional features, full test suite and
multilingual documentation. Verified end-to-end on the **Elica Illusion**
(dataModelIdx 8); compatible with the whole **Elica Connect** range via the
built-in code finder.

### Entities

- **Fan** — 4 speeds + boost, named speed presets (low/medium/high/boost),
  optional `auto` preset
- **Light** (main) — on/off + brightness; optional tunable white with five
  named presets (very_warm → very_cool)
- **Ambient light** — optional secondary light (dimmer)
- **Filter** — grease filter efficiency sensor
- **Air quality** — optional enum sensor (excellent → very_poor, matching
  the Elica app scale)
- **Timer** — optional `number` for the hood's native auto-off countdown

### Reliability

- **Resilient MQTT push**: automatic reconnect with backoff; on OAuth token
  expiry, fresh MQTT credentials are fed to the client so real-time updates
  never silently die (the original silently degraded to slow polling)
- **Proactive token refresh** based on the JWT `exp` claim; single request
  helper with a 401 retry
- **Reauthentication flow**: a changed Elica password triggers the standard
  HA reauth banner instead of a permanent setup error
- **Duplicate protection**: one config entry per hood (`unique_id`)
- **Robust optimistic state**: instant UI feedback, no bounce-back, and
  automatic rollback when the cloud rejects a command
- **Configurable keep-alive**: cloud poll interval (1–60 min) plus an
  optional aggressive mode that sends a harmless no-op command, forcing the
  hood itself to wake up — for models with aggressive Wi-Fi power management
- **Configurable MQTT broker** host and port (default
  cloudprodmqtt.elica.com:8883), so a future broker change needs no new
  release

### Configuration

- **Options flow** for capability codes that vary by model (air quality,
  auto mode, light color, ambient light, timer) — everything optional is
  off by default and safely absent on hoods without it. Each field is
  documented with the known code for dataModelIdx 8
- **Downloadable diagnostics** with redaction of account and device
  identifiers

### Compatibility

- Home Assistant 2024.11+ (verified on 2026.7). Uses `OptionsFlowWithReload`
  on HA 2025.8+, with a fallback update listener on older versions;
  coordinator receives its `config_entry` explicitly (HA 2025.11+)

### Documentation & internationalization

- **Five languages** for the interface, README and DISCOVERY guide:
  English (default), Italian, German, Spanish, French
- Guides: capability code discovery (DISCOVERY.md), example automations,
  optional round-button dashboard, combined fan+timer card, and Amazon
  Alexa optimization (voice control and spoken announcements)
- Local **brand icon** (`brand/icon.png`, `brand/icon@2x.png`)
- Clear **disclaimer** of non-affiliation with Elica S.p.A. in five
  languages (DISCLAIMER.md)

### Quality

- 33 tests (pytest-homeassistant-custom-component)
- GitHub Actions CI: test suite + hassfest + HACS validation
- quality_scale.yaml self-assessment (Bronze complete)

### Credits

Based on the reverse-engineering work of
[@benedettosiddi](https://github.com/benedettosiddi). Released under the MIT
License.

[1.0.0]: https://github.com/marturano/elica-connect-plus/releases/tag/v1.0.0
