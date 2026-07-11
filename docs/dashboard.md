# Optional dashboard: round preset buttons

> 🌍 **EN** · The YAML below is language-independent — just replace the
> `*_ENTITY_ID` placeholders with your own entity IDs. Button/notification
> labels are free text you can translate.
> **IT** · Lo YAML è indipendente dalla lingua: sostituisci i segnaposto
> `*_ENTITY_ID` con i tuoi entity_id. Le etichette dei pulsanti/notifiche
> sono testo libero traducibile.
> **DE** · Das YAML ist sprachunabhängig — ersetze die `*_ENTITY_ID`
> -Platzhalter durch deine Entitäts-IDs. Beschriftungen sind frei übersetzbar.
> **ES** · El YAML es independiente del idioma: sustituye los marcadores
> `*_ENTITY_ID` por tus entity_id. Las etiquetas son texto libre traducible.
> **FR** · Le YAML est indépendant de la langue : remplacez les espaces
> réservés `*_ENTITY_ID` par vos entity_id. Les libellés sont librement
> traduisibles.


The light effect presets and fan speed presets normally appear as dropdown
menus in the entity's more-info dialog (that layout is controlled by Home
Assistant, not by this integration). If you prefer **round buttons with an
icon and a label**, add one of the Lovelace cards below to a dashboard.

This is entirely optional and changes nothing in the integration.

## Before you start: replace the entity IDs

Every card below uses placeholders you MUST replace with your own entity IDs
(find them under *Settings → Devices & services → Elica Connect Plus →*
your hood):

| Placeholder | Replace with your… |
|-------------|--------------------|
| `LIGHT_ENTITY_ID` | main light, e.g. `light.cappa_cucina_light` |
| `FAN_ENTITY_ID` | fan, e.g. `fan.cappa_cucina_fan` |

Preset/effect values are language-neutral slugs and must NOT be translated:
light effects `very_warm / warm / neutral / cool / very_cool`, fan presets
`low / medium / high / boost / auto`.

How to add: dashboard → Edit → **Add card** → **Manual** → paste the YAML.

---

## Option A — Native YAML (no installation)

Uses standard `button` cards in a `horizontal-stack`. Buttons are rounded
(not perfect circles) but everything is built in.

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: "### Light color"
  - type: horizontal-stack
    cards:
      - type: button
        name: Very warm
        icon: mdi:weather-sunset
        icon_height: 32px
        tap_action:
          action: perform-action
          perform_action: light.turn_on
          target: {entity_id: LIGHT_ENTITY_ID}
          data: {effect: very_warm}
      - type: button
        name: Warm
        icon: mdi:white-balance-incandescent
        icon_height: 32px
        tap_action:
          action: perform-action
          perform_action: light.turn_on
          target: {entity_id: LIGHT_ENTITY_ID}
          data: {effect: warm}
      - type: button
        name: Neutral
        icon: mdi:circle-half-full
        icon_height: 32px
        tap_action:
          action: perform-action
          perform_action: light.turn_on
          target: {entity_id: LIGHT_ENTITY_ID}
          data: {effect: neutral}
      - type: button
        name: Cool
        icon: mdi:snowflake-melt
        icon_height: 32px
        tap_action:
          action: perform-action
          perform_action: light.turn_on
          target: {entity_id: LIGHT_ENTITY_ID}
          data: {effect: cool}
      - type: button
        name: Very cool
        icon: mdi:snowflake
        icon_height: 32px
        tap_action:
          action: perform-action
          perform_action: light.turn_on
          target: {entity_id: LIGHT_ENTITY_ID}
          data: {effect: very_cool}
  - type: markdown
    content: "### Fan speed"
  - type: horizontal-stack
    cards:
      - type: button
        name: Low
        icon: mdi:fan-speed-1
        icon_height: 32px
        tap_action:
          action: perform-action
          perform_action: fan.set_preset_mode
          target: {entity_id: FAN_ENTITY_ID}
          data: {preset_mode: low}
      - type: button
        name: Medium
        icon: mdi:fan-speed-2
        icon_height: 32px
        tap_action:
          action: perform-action
          perform_action: fan.set_preset_mode
          target: {entity_id: FAN_ENTITY_ID}
          data: {preset_mode: medium}
      - type: button
        name: High
        icon: mdi:fan-speed-3
        icon_height: 32px
        tap_action:
          action: perform-action
          perform_action: fan.set_preset_mode
          target: {entity_id: FAN_ENTITY_ID}
          data: {preset_mode: high}
      - type: button
        name: Boost
        icon: mdi:fan-plus
        icon_height: 32px
        tap_action:
          action: perform-action
          perform_action: fan.set_preset_mode
          target: {entity_id: FAN_ENTITY_ID}
          data: {preset_mode: boost}
      - type: button
        name: Auto
        icon: mdi:fan-auto
        icon_height: 32px
        tap_action:
          action: perform-action
          perform_action: fan.set_preset_mode
          target: {entity_id: FAN_ENTITY_ID}
          data: {preset_mode: auto}
```

---

## Option B — custom:button-card (true round buttons, highlights active)

Requires the **button-card** frontend plugin (HACS → Frontend → search
"button-card" → install). This version renders real circles and highlights
the button matching the current state.

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: "### Light color"
  - type: horizontal-stack
    cards:
      - type: custom:button-card
        entity: LIGHT_ENTITY_ID
        name: Very warm
        icon: mdi:weather-sunset
        tap_action:
          action: perform-action
          perform_action: light.turn_on
          target: {entity_id: LIGHT_ENTITY_ID}
          data: {effect: very_warm}
        state:
          - operator: template
            value: "[[[ return entity.attributes.effect === 'very_warm' ]]]"
            styles:
              card: [{background-color: "#ff9800"}]
              icon: [{color: white}]
        styles:
          card: [{border-radius: 50%}, {height: 90px}, {width: 90px}]
          icon: [{width: 36px}]
          name: [{font-size: 11px}]
      - type: custom:button-card
        entity: LIGHT_ENTITY_ID
        name: Warm
        icon: mdi:white-balance-incandescent
        tap_action:
          action: perform-action
          perform_action: light.turn_on
          target: {entity_id: LIGHT_ENTITY_ID}
          data: {effect: warm}
        state:
          - operator: template
            value: "[[[ return entity.attributes.effect === 'warm' ]]]"
            styles:
              card: [{background-color: "#ffb74d"}]
              icon: [{color: white}]
        styles:
          card: [{border-radius: 50%}, {height: 90px}, {width: 90px}]
          icon: [{width: 36px}]
          name: [{font-size: 11px}]
      - type: custom:button-card
        entity: LIGHT_ENTITY_ID
        name: Neutral
        icon: mdi:circle-half-full
        tap_action:
          action: perform-action
          perform_action: light.turn_on
          target: {entity_id: LIGHT_ENTITY_ID}
          data: {effect: neutral}
        state:
          - operator: template
            value: "[[[ return entity.attributes.effect === 'neutral' ]]]"
            styles:
              card: [{background-color: "#fff176"}]
              icon: [{color: "#333"}]
        styles:
          card: [{border-radius: 50%}, {height: 90px}, {width: 90px}]
          icon: [{width: 36px}]
          name: [{font-size: 11px}]
      - type: custom:button-card
        entity: LIGHT_ENTITY_ID
        name: Cool
        icon: mdi:snowflake-melt
        tap_action:
          action: perform-action
          perform_action: light.turn_on
          target: {entity_id: LIGHT_ENTITY_ID}
          data: {effect: cool}
        state:
          - operator: template
            value: "[[[ return entity.attributes.effect === 'cool' ]]]"
            styles:
              card: [{background-color: "#90caf9"}]
              icon: [{color: white}]
        styles:
          card: [{border-radius: 50%}, {height: 90px}, {width: 90px}]
          icon: [{width: 36px}]
          name: [{font-size: 11px}]
      - type: custom:button-card
        entity: LIGHT_ENTITY_ID
        name: Very cool
        icon: mdi:snowflake
        tap_action:
          action: perform-action
          perform_action: light.turn_on
          target: {entity_id: LIGHT_ENTITY_ID}
          data: {effect: very_cool}
        state:
          - operator: template
            value: "[[[ return entity.attributes.effect === 'very_cool' ]]]"
            styles:
              card: [{background-color: "#42a5f5"}]
              icon: [{color: white}]
        styles:
          card: [{border-radius: 50%}, {height: 90px}, {width: 90px}]
          icon: [{width: 36px}]
          name: [{font-size: 11px}]
  - type: markdown
    content: "### Fan speed"
  - type: horizontal-stack
    cards:
      - type: custom:button-card
        entity: FAN_ENTITY_ID
        name: Low
        icon: mdi:fan-speed-1
        tap_action:
          action: perform-action
          perform_action: fan.set_preset_mode
          target: {entity_id: FAN_ENTITY_ID}
          data: {preset_mode: low}
        state:
          - operator: template
            value: "[[[ return entity.attributes.preset_mode === 'low' ]]]"
            styles:
              card: [{background-color: "#4caf50"}]
              icon: [{color: white}]
        styles:
          card: [{border-radius: 50%}, {height: 90px}, {width: 90px}]
          icon: [{width: 36px}]
          name: [{font-size: 11px}]
      - type: custom:button-card
        entity: FAN_ENTITY_ID
        name: Medium
        icon: mdi:fan-speed-2
        tap_action:
          action: perform-action
          perform_action: fan.set_preset_mode
          target: {entity_id: FAN_ENTITY_ID}
          data: {preset_mode: medium}
        state:
          - operator: template
            value: "[[[ return entity.attributes.preset_mode === 'medium' ]]]"
            styles:
              card: [{background-color: "#4caf50"}]
              icon: [{color: white}]
        styles:
          card: [{border-radius: 50%}, {height: 90px}, {width: 90px}]
          icon: [{width: 36px}]
          name: [{font-size: 11px}]
      - type: custom:button-card
        entity: FAN_ENTITY_ID
        name: High
        icon: mdi:fan-speed-3
        tap_action:
          action: perform-action
          perform_action: fan.set_preset_mode
          target: {entity_id: FAN_ENTITY_ID}
          data: {preset_mode: high}
        state:
          - operator: template
            value: "[[[ return entity.attributes.preset_mode === 'high' ]]]"
            styles:
              card: [{background-color: "#4caf50"}]
              icon: [{color: white}]
        styles:
          card: [{border-radius: 50%}, {height: 90px}, {width: 90px}]
          icon: [{width: 36px}]
          name: [{font-size: 11px}]
      - type: custom:button-card
        entity: FAN_ENTITY_ID
        name: Boost
        icon: mdi:fan-plus
        tap_action:
          action: perform-action
          perform_action: fan.set_preset_mode
          target: {entity_id: FAN_ENTITY_ID}
          data: {preset_mode: boost}
        state:
          - operator: template
            value: "[[[ return entity.attributes.preset_mode === 'boost' ]]]"
            styles:
              card: [{background-color: "#ff5722"}]
              icon: [{color: white}]
        styles:
          card: [{border-radius: 50%}, {height: 90px}, {width: 90px}]
          icon: [{width: 36px}]
          name: [{font-size: 11px}]
      - type: custom:button-card
        entity: FAN_ENTITY_ID
        name: Auto
        icon: mdi:fan-auto
        tap_action:
          action: perform-action
          perform_action: fan.set_preset_mode
          target: {entity_id: FAN_ENTITY_ID}
          data: {preset_mode: auto}
        state:
          - operator: template
            value: "[[[ return entity.attributes.preset_mode === 'auto' ]]]"
            styles:
              card: [{background-color: "#2196f3"}]
              icon: [{color: white}]
        styles:
          card: [{border-radius: 50%}, {height: 90px}, {width: 90px}]
          icon: [{width: 36px}]
          name: [{font-size: 11px}]
```

> Tip: labels are free text — translate "Very warm", "Low", etc. to your
> language if you like. Only the `effect:` / `preset_mode:` slug values must
> stay in English.

---

## Fan control with timer buttons in one card

This combines the fan controls and the auto-off timer into a single card, so
5 / 10 / 20 / 30-minute buttons sit right under the fan — the "timer in the
fan control" experience. The fan and timer stay separate entities under the
hood; this just groups them visually.

Replace `FAN_ENTITY_ID` and `TIMER_ENTITY_ID` with yours.

```yaml
type: vertical-stack
cards:
  - type: tile
    entity: FAN_ENTITY_ID
    features_position: bottom
    features:
      - type: fan-speed
      - type: fan-preset-modes
        style: dropdown
  - type: horizontal-stack
    cards:
      - type: button
        name: 5 min
        icon: mdi:timer-outline
        tap_action:
          action: perform-action
          perform_action: number.set_value
          target: {entity_id: TIMER_ENTITY_ID}
          data: {value: 5}
      - type: button
        name: 10 min
        icon: mdi:timer-outline
        tap_action:
          action: perform-action
          perform_action: number.set_value
          target: {entity_id: TIMER_ENTITY_ID}
          data: {value: 10}
      - type: button
        name: 20 min
        icon: mdi:timer-outline
        tap_action:
          action: perform-action
          perform_action: number.set_value
          target: {entity_id: TIMER_ENTITY_ID}
          data: {value: 20}
      - type: button
        name: 30 min
        icon: mdi:timer-outline
        tap_action:
          action: perform-action
          perform_action: number.set_value
          target: {entity_id: TIMER_ENTITY_ID}
          data: {value: 30}
      - type: button
        name: "Off"
        icon: mdi:timer-off-outline
        tap_action:
          action: perform-action
          perform_action: number.set_value
          target: {entity_id: TIMER_ENTITY_ID}
          data: {value: 0}
```

The tile shows the fan speed slider and preset dropdown; the row below is the
timer. While a timer is running, add the `TIMER_ENTITY_ID` entity anywhere on
the dashboard to see the remaining minutes count down.

## Optional: auto-off timer buttons

If you enabled the timer (Options → *Auto-off timer capability code* = 432 on
Elica Illusion), the timer is a `number` entity. Replace `TIMER_ENTITY_ID`
with yours (e.g. `number.cappa_cucina_timer`).

Quick-set buttons for 5 / 10 / 20 / 30 minutes and off:

```yaml
type: horizontal-stack
cards:
  - type: button
    name: 5 min
    icon: mdi:timer-outline
    tap_action:
      action: perform-action
      perform_action: number.set_value
      target: {entity_id: TIMER_ENTITY_ID}
      data: {value: 5}
  - type: button
    name: 10 min
    icon: mdi:timer-outline
    tap_action:
      action: perform-action
      perform_action: number.set_value
      target: {entity_id: TIMER_ENTITY_ID}
      data: {value: 10}
  - type: button
    name: 20 min
    icon: mdi:timer-outline
    tap_action:
      action: perform-action
      perform_action: number.set_value
      target: {entity_id: TIMER_ENTITY_ID}
      data: {value: 20}
  - type: button
    name: 30 min
    icon: mdi:timer-outline
    tap_action:
      action: perform-action
      perform_action: number.set_value
      target: {entity_id: TIMER_ENTITY_ID}
      data: {value: 30}
  - type: button
    name: "Off"
    icon: mdi:timer-off-outline
    tap_action:
      action: perform-action
      perform_action: number.set_value
      target: {entity_id: TIMER_ENTITY_ID}
      data: {value: 0}
```

For a custom duration ("personalizzato" in the app), add the timer `number`
entity itself to a dashboard — it shows a spin box where you can type any
value — or call `number.set_value` with the minutes you want.

For a custom duration, add the number entity itself to a dashboard (it shows
a spin box) or use the `number.set_value` action with any value. While a
timer is running, the same entity shows the remaining minutes counting down.
