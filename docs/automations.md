# Example automations / Automazioni di esempio

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


Replace entity IDs with yours (find them under the hood's device page).
Sostituisci gli entity_id con i tuoi (li trovi nella pagina dispositivo della cappa).

## Auto-start while cooking (induction hob power sensor)

```yaml
automation:
  - alias: "Hood - auto start on cooking"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.induction_hob_power
        above: 300
        for: "00:00:30"
    conditions:
      - condition: state
        entity_id: fan.hood_fan
        state: "off"
    actions:
      - action: fan.set_percentage
        target:
          entity_id: fan.hood_fan
        data:
          percentage: 50
```

## Boost on heavy cooking

```yaml
  - alias: "Hood - boost on heavy cooking"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.induction_hob_power
        above: 2000
        for: "00:01:00"
    actions:
      - action: fan.set_percentage
        target:
          entity_id: fan.hood_fan
        data:
          percentage: 100
```

## Delayed switch-off after cooking (kitchen humidity)

```yaml
  - alias: "Hood - delayed off"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.kitchen_humidity
        below: 55
        for: "00:05:00"
    conditions:
      - condition: state
        entity_id: fan.hood_fan
        state: "on"
    actions:
      - action: fan.turn_off
        target:
          entity_id: fan.hood_fan
```

## Filter maintenance notification

```yaml
  - alias: "Hood - clean the grease filter"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.hood_filter
        below: 20
    actions:
      - action: notify.mobile_app_your_phone
        data:
          title: "Hood filter"
          message: >
            Grease filter efficiency at
            {{ states('sensor.hood_filter') }}% — time to wash it.
```

## Courtesy night light (motion in the kitchen)

```yaml
  - alias: "Hood - courtesy light at night"
    triggers:
      - trigger: state
        entity_id: binary_sensor.kitchen_motion
        to: "on"
    conditions:
      - condition: time
        after: "23:00:00"
        before: "06:30:00"
      - condition: state
        entity_id: light.hood_light
        state: "off"
    actions:
      - action: light.turn_on
        target:
          entity_id: light.hood_light
        data:
          brightness_pct: 30
      - wait_for_trigger:
          - trigger: state
            entity_id: binary_sensor.kitchen_motion
            to: "off"
            for: "00:03:00"
      - action: light.turn_off
        target:
          entity_id: light.hood_light
```

## AUTO mode when air quality degrades (requires optional features configured)

```yaml
  - alias: "Hood - auto mode on poor air quality"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.hood_air_quality
        above: 2
    conditions:
      - condition: state
        entity_id: fan.hood_fan
        state: "off"
    actions:
      - action: fan.set_preset_mode
        target:
          entity_id: fan.hood_fan
        data:
          preset_mode: auto
```

## Watchdog: cloud integration went unavailable

```yaml
  - alias: "Hood - integration watchdog"
    triggers:
      - trigger: state
        entity_id: fan.hood_fan
        to: "unavailable"
        for: "00:15:00"
    actions:
      - action: notify.mobile_app_your_phone
        data:
          title: "Elica Connect Plus"
          message: >
            The hood has been unavailable for 15 minutes — the Elica cloud
            may be down or the API may have changed.
```
