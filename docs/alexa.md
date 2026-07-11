# Alexa optimization (optional)

> 🌍 **EN** · Examples are language-independent — replace the `*_ENTITY_ID`
> placeholders and the Echo device name with yours. Spoken labels/messages
> are free text you can translate.
> **IT** · Gli esempi sono indipendenti dalla lingua: sostituisci i
> segnaposto `*_ENTITY_ID` e il nome del dispositivo Echo. Le frasi
> pronunciate sono testo libero traducibile.
> **DE** · Die Beispiele sind sprachunabhängig — ersetze die `*_ENTITY_ID`
> -Platzhalter und den Echo-Gerätenamen. Gesprochene Texte sind frei
> übersetzbar.
> **ES** · Los ejemplos son independientes del idioma: sustituye los
> marcadores `*_ENTITY_ID` y el nombre del dispositivo Echo. Los mensajes
> hablados son texto libre traducible.
> **FR** · Les exemples sont indépendants de la langue : remplacez les
> espaces réservés `*_ENTITY_ID` et le nom de l'appareil Echo. Les messages
> vocaux sont librement traduisibles.

These are **optional** ideas for using the hood with Amazon Alexa. Nothing
here is part of the integration — it all lives in *your* Home Assistant
configuration (automations, scripts, exposure settings). Pick what you like.

## Two ways Alexa connects — and what each needs

| Feature | Requirement |
|---------|-------------|
| Voice control ("Alexa, turn on the hood") | **Official Alexa Smart Home skill** — Home Assistant Cloud (Nabu Casa) or a manually configured skill |
| Proactive spoken **announcements** ("The filter needs cleaning") | **Alexa Media Player** — a custom integration installed via HACS (`custom_components/alexa_media`), **not** an official add-on |

> ⚠️ **The announcement examples (section 3) require the Alexa Media Player
> custom integration** (HACS → search "Alexa Media Player"). Without it, the
> `notify.alexa_media_*` services do not exist. The voice-control examples
> (sections 1–2) work with the official skill and do **not** need it.

There is no way to visually restyle Alexa's own controls (the Alexa app and
Echo Show screens are closed): "optimizing Alexa" here means better exposure,
more natural voice commands, and spoken announcements — not custom UI.

---

## 1. Expose the right entities (official skill)

Alexa only sees what you expose. Exposing the filter sensor, the timer
`number` or the air-quality sensor just clutters the device list — they are
useless by voice. Expose the fan and lights only.

If you configure the skill via `configuration.yaml`:

```yaml
alexa:
  smart_home:
    filter:
      include_entities:
        - FAN_ENTITY_ID
        - LIGHT_ENTITY_ID
        - AMBIENT_LIGHT_ENTITY_ID
      exclude_entities:
        - FILTER_SENSOR_ENTITY_ID
        - AIR_QUALITY_SENSOR_ENTITY_ID
        - TIMER_ENTITY_ID
```

With Home Assistant Cloud (Nabu Casa) do the same from the UI:
*Settings → Home Assistant Cloud → Alexa → expose/hide entities*.

### Voice-friendly aliases

The entity name is what you say. Give each entity a few aliases (entity
settings → *Aliases*) so more phrasings work:

- fan → "Hood", "Extractor", "Kitchen fan"
- main light → "Hood light", "Kitchen light"
- ambient light → "Kitchen ambient light"

---

## 2. Natural voice commands

With good exposure, these work out of the box with the official skill:

- "Alexa, turn the hood on / off"
- "Alexa, set the hood to 50 percent"
- "Alexa, turn on the hood light"
- "Alexa, set the hood light to 30 percent"

### Commands Alexa can't do natively → expose scripts

Alexa handles a `fan`'s on/off and percentage, but **not** preset modes
(Boost, Auto) or light effects (Very warm). Wrap those in scripts and expose
each script to Alexa (as you would a scene); then say "Alexa, turn on
<script name>". These scripts need only the **official skill** (no Alexa
Media Player).

```yaml
script:
  hood_boost:
    alias: "Hood Boost"
    sequence:
      - action: fan.set_preset_mode
        target: {entity_id: FAN_ENTITY_ID}
        data: {preset_mode: boost}

  hood_auto:
    alias: "Hood Auto"
    sequence:
      - action: fan.set_preset_mode
        target: {entity_id: FAN_ENTITY_ID}
        data: {preset_mode: auto}

  hood_light_warm:
    alias: "Hood Warm Light"
    sequence:
      - action: light.turn_on
        target: {entity_id: LIGHT_ENTITY_ID}
        data: {effect: very_warm}

  hood_light_cool:
    alias: "Hood Cool Light"
    sequence:
      - action: light.turn_on
        target: {entity_id: LIGHT_ENTITY_ID}
        data: {effect: very_cool}

  hood_timer_10:
    alias: "Hood Timer 10"
    sequence:
      - action: number.set_value
        target: {entity_id: TIMER_ENTITY_ID}
        data: {value: 10}

  hood_timer_30:
    alias: "Hood Timer 30"
    sequence:
      - action: number.set_value
        target: {entity_id: TIMER_ENTITY_ID}
        data: {value: 30}
```

Now: "Alexa, turn on Hood Boost", "Alexa, turn on Hood Warm Light",
"Alexa, turn on Hood Timer 30", etc. Duplicate the timer script for 5 / 20
minutes as needed.

---

## 3. Proactive spoken announcements

> ⚠️ **Requires the Alexa Media Player custom integration** (HACS). Replace
> `notify.alexa_media_echo_kitchen` with your real Echo notify target.

### 3a. Filter needs cleaning

```yaml
automation:
  - alias: "Hood - filter announcement"
    triggers:
      - trigger: numeric_state
        entity_id: FILTER_SENSOR_ENTITY_ID
        below: 20
    actions:
      - action: notify.alexa_media_echo_kitchen
        data:
          message: "The hood filter is at {{ states('FILTER_SENSOR_ENTITY_ID') }} percent. It should be cleaned."
          data: {type: announce}
```

### 3b. Timer expired (code 432 reaches 0 from a positive value)

```yaml
  - alias: "Hood - timer expired announcement"
    triggers:
      - trigger: numeric_state
        entity_id: TIMER_ENTITY_ID
        below: 1
    conditions:
      - condition: template
        value_template: "{{ trigger.from_state.state | int(0) > 0 }}"
    actions:
      - action: notify.alexa_media_echo_kitchen
        data:
          message: "Hood timer finished."
          data: {type: announce}
```

### 3c. Poor air quality while the fan is off

```yaml
  - alias: "Hood - air quality announcement"
    triggers:
      - trigger: state
        entity_id: AIR_QUALITY_SENSOR_ENTITY_ID
        to:
          - poor
          - very_poor
    conditions:
      - condition: state
        entity_id: FAN_ENTITY_ID
        state: "off"
    actions:
      - action: notify.alexa_media_echo_kitchen
        data:
          message: "Kitchen air quality is {{ states('AIR_QUALITY_SENSOR_ENTITY_ID') }}. Shall I turn on the extraction?"
          data: {type: announce}
```

### 3d. Hood left running

```yaml
  - alias: "Hood - left on reminder"
    triggers:
      - trigger: state
        entity_id: FAN_ENTITY_ID
        state: "on"
        for: "01:00:00"
    actions:
      - action: notify.alexa_media_echo_kitchen
        data:
          message: "The hood has been on for an hour. Remember to switch it off."
          data: {type: announce}
```

---

## Placeholders used here

| Placeholder | Replace with your… |
|-------------|--------------------|
| `FAN_ENTITY_ID` | fan entity |
| `LIGHT_ENTITY_ID` | main light entity |
| `AMBIENT_LIGHT_ENTITY_ID` | ambient light entity (if configured) |
| `FILTER_SENSOR_ENTITY_ID` | filter sensor entity |
| `AIR_QUALITY_SENSOR_ENTITY_ID` | air quality sensor (if configured) |
| `TIMER_ENTITY_ID` | timer `number` entity (if configured) |
| `notify.alexa_media_echo_kitchen` | your Echo notify target (Alexa Media Player) |
