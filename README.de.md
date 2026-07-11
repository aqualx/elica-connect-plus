# Elica Connect Plus

Erweiterte Home-Assistant-Integration für **Elica Connect** Dunstabzugshauben
(ESP32-C6, App `com.replyconnect.elica`). Fork von
[benedettosiddi/elica-connect-ha](https://github.com/benedettosiddi/elica-connect-ha)
mit robuster Cloud-Anbindung, optionalen Funktionen und vollständiger
Testsuite.

🇬🇧 [English](README.md) · 🇮🇹 [Italiano](README.it.md) · 🇪🇸 [Español](README.es.md) · 🇫🇷 [Français](README.fr.md)

> Verifiziert mit: **Elica Illusion** (dataModelIdx 8, PRF0199706) —
> kompatibel mit allen **Elica Connect** Hauben, siehe Kompatibilität — HA 2024.11+, verifiziert mit 2026.7

## Entitäten

| Entität | Typ | Beschreibung |
|---------|-----|--------------|
| Lüfter | `fan` | Benannte Presets + Prozent; optionales Auto-Preset |
| Licht | `light` | Ein/Aus + Helligkeit; optional Farbtemperatur mit Presets |
| Ambientelicht | `light` | Optionales Zweitlicht: dimmbar |
| Filter | `sensor` | Fettfilter-Effizienz % |
| Luftqualität | `sensor` | Optional |

Echtzeitstatus über **Cloud-MQTT-Push**, mit konfigurierbarem Keep-Alive-Poll.

## Kompatibilität

| Haube | Status |
|-------|--------|
| **Elica Illusion** (dataModelIdx 8) | ✅ Vollständig verifiziert: alle Capability-Codes an einem echten Gerät bestätigt |
| Jede andere **Elica Connect** Haube (App `com.replyconnect.elica`) | ✅ Kompatibel: Basis-Entitäten (Lüfter, Hauptlicht, Filter) funktionieren sofort; modellspezifische Funktionen werden über den integrierten **Code-Finder** aktiviert — siehe [DISCOVERY.de.md](custom_components/elica_connect_plus/DISCOVERY.de.md) |

Die Cloud-API ist für die gesamte Elica-Connect-Reihe gleich; nur die
Capability-Codes einiger Funktionen variieren je nach Modell. Genau dafür ist
der Ablauf Optionen + Code-Finder gedacht.

## Verbesserungen gegenüber der Originalintegration

- **Robuster MQTT-Push**: automatische Wiederverbindung mit Backoff; bei
  Ablauf des OAuth-Tokens werden neue MQTT-Zugangsdaten an den Client
  übergeben, sodass Echtzeit-Updates nie stillschweigend ausfallen
- **Proaktive Token-Erneuerung** anhand des JWT-`exp`-Claims
- **Erneute Authentifizierung**: ein geändertes Passwort löst den Standard-
  Reauth-Dialog aus statt eines dauerhaften Fehlers
- **Duplikatschutz**: ein Konfigurationseintrag pro Haube (`unique_id`)
- **Robuster optimistischer Zustand** mit Rollback bei Fehlern
- **Herunterladbare Diagnose** mit Schwärzung sensibler Daten
- **Optionen** für Capability-Codes noch nicht zugeordneter Funktionen
- **Testsuite** (29 Tests)

## Installation

### HACS (empfohlen)

1. HACS → ⋮ → *Benutzerdefinierte Repositories* → dieses Repository als
   **Integration** hinzufügen
2. **Elica Connect Plus** installieren und Home Assistant neu starten
3. *Einstellungen → Geräte & Dienste → Integration hinzufügen* →
   **Elica Connect Plus**
4. Zugangsdaten der Elica-Connect-App eingeben

### Manuell

Kopiere `custom_components/elica_connect_plus/` in deinen HA-Ordner
`custom_components/` und starte neu.

## Optionale Funktionen

Luftqualität, AUTO-Modus, Lichtfarbe und Ambientelicht verwenden
Capability-Codes, die je nach Modell variieren. Ermittle die Codes deiner
Haube mit [DISCOVERY.de.md](custom_components/elica_connect_plus/DISCOVERY.de.md)
und trage sie unter *Einstellungen → Geräte & Dienste → Elica Connect Plus →
Konfigurieren* ein.

## Bestätigte Capability-Codes — Elica Illusion (dataModelIdx 8)

| Code | Funktion | Werte |
|------|----------|-------|
| 64 | Lüftermodus | 1=normal, 4=Boost, 16=Auto (Bitmaske) |
| 96 | Helligkeit Hauptlicht | 0–100 |
| 97 | Farbe Hauptlicht | 0=warm – 100=kalt |
| 100 | Helligkeit Ambientelicht | 0–100 (nur dimmbar) |
| 110 | Lüftergeschwindigkeit | 0=aus, 1–3 |
| 112 | Luftqualität | 1=ausgezeichnet … 5=sehr schlecht |

## Sprachen

Englisch (Standard), Italienisch, Deutsch, Spanisch und Französisch,
entsprechend der HA-Oberflächensprache.

## Beispiel-Automatisierungen

Siehe [docs/automations.md](docs/automations.md) für gebrauchsfertiges YAML:
automatischer Start beim Kochen, verzögertes Abschalten, Hinweise zur
Filterwartung, Orientierungslicht bei Nacht.

Runde Preset-Tasten statt der Standard-Dropdowns? Siehe die optionale
[Dashboard-Anleitung](docs/dashboard.md) (natives YAML oder
`custom:button-card`).

Nutzt du Amazon Alexa? Siehe die optionale [Alexa-Anleitung](docs/alexa.md)
für Sprachsteuerung und gesprochene Ansagen (einige Beispiele benötigen die
Alexa-Media-Player-Integration).

## Entwicklung

```bash
pip install -r requirements_test.txt
pytest tests/
```

Die CI führt bei jedem Push die Testsuite sowie hassfest- und
HACS-Validierung aus.

## Lizenz

Veröffentlicht unter der [MIT-Lizenz](LICENSE), © 2026 Roberto Marturano.

Dieses Projekt ist ein Fork von
[elica-connect-ha](https://github.com/benedettosiddi/elica-connect-ha) von
[@benedettosiddi](https://github.com/benedettosiddi) und erweitert dessen
Arbeit — voller Dank für das ursprüngliche Reverse Engineering.

## Danksagung

Cloud-API per mitmproxy von
[@benedettosiddi](https://github.com/benedettosiddi) analysiert, auf dessen
Arbeit dieser Fork aufbaut.

## Haftungsausschluss

**Elica Connect Plus ist ein unabhängiges, inoffizielles Projekt. Es ist
nicht mit Elica S.p.A. verbunden, von dieser autorisiert oder unterstützt**,
dem Anbieter des Elica-Connect-Systems und seines Ökosystems. „Elica",
„Elica Connect" und alle zugehörigen Namen, Marken und Logos sind Marken von
Elica S.p.A. bzw. ihrer jeweiligen Eigentümer und werden hier nur zu
Identifikationszwecken verwendet. Diese Integration beruht auf einer per
Reverse Engineering ermittelten, nicht dokumentierten Schnittstelle, die sich
jederzeit ändern oder den Betrieb einstellen kann.

Die Software wird „wie besehen" ohne jegliche Gewährleistung bereitgestellt.
Die Autoren und Mitwirkenden übernehmen **keine Haftung** für Schäden an
Geräten oder Eigentum, Fehlfunktionen, Datenverlust, Dienstunterbrechungen
oder Kontoprobleme, die aus der Nutzung entstehen. **Die Nutzung erfolgt
vollständig auf eigenes Risiko.**

Siehe [DISCLAIMER.md](DISCLAIMER.md) für den vollständigen Text (verfügbar in
English, Italiano, Deutsch, Español und Français).
