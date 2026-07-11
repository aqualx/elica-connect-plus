# Descubrir los códigos de capability de tu campana

🇬🇧 [English](DISCOVERY.md) · 🇮🇹 [Italiano](DISCOVERY.it.md) · 🇩🇪 [Deutsch](DISCOVERY.de.md) · 🇫🇷 [Français](DISCOVERY.fr.md)

La API cloud de Elica representa cada función de la campana como un par
`código: valor` en el campo `dataModel`. La integración funciona con **todas
las campanas Elica Connect**; esta página es el *buscador de códigos*
integrado para activar las funciones específicas del modelo. Códigos
confirmados para la **Elica Illusion** (dataModelIdx 8):

| Código | Función | Valores |
|--------|---------|---------|
| 64 | Modo ventilador | 1=normal, 4=boost, 16=auto (los valores sugieren una máscara de bits) |
| 96 | Brillo luz principal | 0–100 (%; 0=apagado) |
| 97 | Color luz principal (blanco regulable) | 0=cálida – 100=fría |
| 100 | Brillo luz ambiental | 0–100; la luz ambiental no tiene control de color |
| 110 | Velocidad ventilador | 0=apagado, 1–3 (también se informa en modo auto) |
| 112 | Calidad del aire | 1=excelente … 5=muy mala |
| 432 | Temporizador de apagado | minutos; escribir N inicia una cuenta atrás de N minutos gestionada por el firmware, el valor desciende hasta 0 |

Otros modelos de campana pueden usar códigos distintos: la integración los
admite mediante las Opciones — solo hay que identificarlos una vez.

## Método 1 — Lectura del log MQTT en directo (recomendado)

La integración recibe **todos** los códigos del dataModel vía push MQTT,
incluso los desconocidos. Con el registro de depuración activado, cada cambio
aparece en el log de HA en tiempo real:

1. Añade a `configuration.yaml` y reinicia:
   ```yaml
   logger:
     default: warning
     logs:
       custom_components.elica_connect_plus: debug
   ```
2. Observa el log (`tail -f /config/home-assistant.log | grep "Elica MQTT"`).
3. En la app Elica, cambia **una sola** cosa cada vez (activar auto, mover un
   deslizador) y espera la línea correspondiente:
   `Elica MQTT: state update {'97': 100}`
4. El código que ha cambiado es el que buscas. Introdúcelo en *Ajustes →
   Dispositivos y servicios → Elica Connect Plus → Configurar*.
5. Para el sensor de calidad del aire, no toques nada: sopla hacia la rejilla
   o pulveriza algo cerca y observa qué código cambia por sí solo.

## Método 2 — Comparación de diagnósticos

Sin necesidad de acceder al log: descarga el diagnóstico (página del
dispositivo → ⋮ → Descargar diagnóstico), cambia una cosa en la app, descarga
de nuevo tras ~10 segundos y compara las secciones `state_cache`:
`diff <(jq .state_cache antes.json) <(jq .state_cache despues.json)`

## Método 3 — mitmproxy

Para ver también cómo la app *escribe* los comandos: ejecuta mitmproxy, dirige
el teléfono a través de él (la app no tiene certificate pinning) y observa
`POST /eiot-api/v1/devices/{id}/commands` — el campo `capabilities` contiene
los códigos y valores exactos.

## Notas de campo — Elica Illusion (dataModelIdx 8)

- El código **112** no aparece en el volcado completo del dataModel en
  reposo: solo se publica por MQTT mientras el sensor está activo
  (normalmente en modo auto). Tras reiniciar HA, el sensor permanece
  `unavailable` hasta que llega el primer valor.
- En modo auto, la velocidad real se sigue informando en el código 110: HA
  muestra tanto el preset `auto` como el porcentaje actual.
- Los comandos REST usan el `device_id` (p. ej. `Utya8g`), el topic MQTT usa
  el `cuid` (p. ej. `J2BDYM2XTVYC`): identificadores distintos, ambos correctos.
- El código **5** aparece a menudo en las actualizaciones como 0 junto a
  otros cambios: parece un indicador de transición del firmware y puede
  ignorarse.

¿Has encontrado códigos de otro modelo? Abre un issue **Capability report**
para documentarlos para todos.
