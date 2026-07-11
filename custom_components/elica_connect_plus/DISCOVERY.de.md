# Capability-Codes deiner Dunstabzugshaube ermitteln

🇬🇧 [English](DISCOVERY.md) · 🇮🇹 [Italiano](DISCOVERY.it.md) · 🇪🇸 [Español](DISCOVERY.es.md) · 🇫🇷 [Français](DISCOVERY.fr.md)

Die Elica-Cloud-API stellt jede Funktion der Haube als Paar `Code: Wert` im
Feld `dataModel` dar. Die Integration funktioniert mit **allen Elica-Connect-
Hauben**; diese Seite ist der integrierte *Code-Finder*, um modellspezifische
Funktionen zu aktivieren. Bestätigte Codes für die **Elica Illusion**
(dataModelIdx 8):

| Code | Funktion | Werte |
|------|----------|-------|
| 64 | Lüftermodus | 1=normal, 4=Boost, 16=Auto (Werte deuten auf eine Bitmaske) |
| 96 | Helligkeit Hauptlicht | 0–100 (%; 0=aus) |
| 97 | Farbe Hauptlicht (Tunable White) | 0=warm – 100=kalt |
| 100 | Helligkeit Ambientelicht | 0–100; das Ambientelicht hat keine Farbsteuerung |
| 110 | Lüftergeschwindigkeit | 0=aus, 1–3 (wird auch im Auto-Modus gemeldet) |
| 112 | Luftqualität | 1=ausgezeichnet … 5=sehr schlecht |
| 432 | Abschalt-Timer | Minuten; Schreiben von N startet einen N-minütigen Firmware-Countdown, der Wert zählt bis 0 herunter |

Andere Haubenmodelle können andere Codes verwenden: Die Integration
unterstützt sie über die Optionen — du musst sie nur einmal ermitteln.

## Methode 1 — Live-MQTT-Log mitlesen (empfohlen)

Die Integration empfängt **alle** dataModel-Codes per MQTT-Push, auch
unbekannte. Mit aktiviertem Debug-Logging erscheint jede Änderung in Echtzeit
im HA-Log:

1. In `configuration.yaml` eintragen und neu starten:
   ```yaml
   logger:
     default: warning
     logs:
       custom_components.elica_connect_plus: debug
   ```
2. Das Log beobachten (`tail -f /config/home-assistant.log | grep "Elica MQTT"`).
3. In der Elica-App **eine** Sache nach der anderen ändern (Auto umschalten,
   einen Regler bewegen) und auf die passende Zeile warten:
   `Elica MQTT: state update {'97': 100}`
4. Der Code, der sich geändert hat, ist der gesuchte. Trage ihn unter
   *Einstellungen → Geräte & Dienste → Elica Connect Plus → Konfigurieren* ein.
5. Für den Luftqualitätssensor nichts anfassen: Blase in Richtung Gitter oder
   sprühe etwas in der Nähe und beobachte, welcher Code sich von selbst ändert.

## Methode 2 — Diagnose-Vergleich

Kein Log-Zugriff nötig: Lade die Diagnose herunter (Geräteseite → ⋮ →
Diagnose herunterladen), ändere eine Sache in der App, lade nach ~10 Sekunden
erneut herunter und vergleiche die `state_cache`-Abschnitte:
`diff <(jq .state_cache vorher.json) <(jq .state_cache nachher.json)`

## Methode 3 — mitmproxy

Um auch zu sehen, wie die App Befehle *schreibt*: mitmproxy ausführen, das
Telefon darüber leiten (die App hat kein Certificate Pinning) und
`POST /eiot-api/v1/devices/{id}/commands` beobachten — das Feld
`capabilities` enthält die genauen Codes und Werte.

## Feldnotizen — Elica Illusion (dataModelIdx 8)

- Code **112** erscheint im vollständigen dataModel-Dump im Ruhezustand
  nicht: Er wird nur per MQTT veröffentlicht, während der Sensor aktiv ist
  (typischerweise im Auto-Modus). Nach einem HA-Neustart bleibt der Sensor
  `unavailable`, bis der erste Wert eintrifft.
- Im Auto-Modus wird die tatsächliche Geschwindigkeit weiter in Code 110
  gemeldet: HA zeigt sowohl das `auto`-Preset als auch den aktuellen Prozentwert.
- REST-Befehle nutzen die `device_id` (z. B. `Utya8g`), das MQTT-Topic nutzt
  die `cuid` (z. B. `J2BDYM2XTVYC`): unterschiedliche Kennungen, beide korrekt.
- Code **5** erscheint oft in Updates als 0 zusammen mit anderen Änderungen:
  Er sieht aus wie ein Firmware-Übergangsflag und kann ignoriert werden.

Codes für ein anderes Modell gefunden? Bitte einen **Capability report**
-Issue öffnen, damit sie für alle dokumentiert werden.
