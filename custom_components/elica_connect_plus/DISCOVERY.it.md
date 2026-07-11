# Scoprire i codici capability della tua cappa

🇬🇧 [English](DISCOVERY.md) · 🇩🇪 [Deutsch](DISCOVERY.de.md) · 🇪🇸 [Español](DISCOVERY.es.md) · 🇫🇷 [Français](DISCOVERY.fr.md)


L'API cloud Elica rappresenta ogni funzione della cappa come una coppia
`codice: valore` nel campo `dataModel`. L'integrazione funziona con **tutte
le cappe Elica Connect**; questa pagina è il *trova codice* integrato per
attivare le funzioni specifiche del modello. Codici confermati per la
**Elica Illusion** (dataModelIdx 8):

| Codice | Funzione | Valori |
|--------|----------|--------|
| 64 | Modalità ventola | 1=normale, 4=boost |
| 96 | Luminosità luce | 0–100 (%) |
| 110 | Velocità ventola | 0=off, 1–3 |
| 97 | Colore luce (tunable white) | 0=calda – 100=fredda |
| 64 | Modalità AUTO | valore 16 (i valori 1/4/16 suggeriscono una bitmask) |
| 112 | Qualità aria | 1=Ottima, 2=Buona, 3=Media, 4=Scarsa, 5=Pessima |
| 432 | Timer di spegnimento | minuti; scrivendo N parte un conto alla rovescia gestito dal firmware, il valore scala fino a 0 |
| 100 | Luminosità luce ambiente | 0–100; la luce ambiente non ha controllo colore |

Note dal campo (dataModelIdx 8):
- Il codice **112** non appare nel dump completo del dataModel a riposo:
  viene pubblicato via MQTT solo quando il sensore è attivo (tipicamente in
  modalità Auto). Dopo un riavvio di HA il sensore resta `unavailable`
  finché non arriva il primo valore.
- In modalità Auto la velocità reale continua a essere riportata nel
  codice 110: HA mostra sia il preset `auto` sia la percentuale corrente.
- I comandi REST usano il `device_id` (es. `Utya8g`), il topic MQTT usa il
  `cuid` (es. `J2BDYM2XTVYC`): sono identificatori diversi, è normale.
- Il codice **5** compare spesso negli update a valore 0 insieme ad altri
  cambi: sembra un flag di transizione del firmware, ignorabile.

Qualità dell'aria, modalità AUTO e colore luce usano **altri codici, ancora
da identificare**. Questa integrazione li supporta già: vanno solo inseriti
in *Impostazioni → Dispositivi e servizi → Elica Connect → Configura* una
volta scoperti.

## Metodo 1 — Diff della diagnostica (consigliato, senza strumenti)

L'integrazione riceve via MQTT *tutti* i codici del dataModel, anche quelli
che non conosce. Quindi:

1. Cappa accesa, tutto spento/normale. Scarica la diagnostica:
   *Impostazioni → Dispositivi e servizi → Elica Connect → ⋮ → Scarica
   diagnostica*. Apri il JSON e copia la sezione `state_cache` (baseline).
2. Dall'app Elica Connect attiva **una sola** funzione (es. modalità AUTO).
3. Attendi ~10 secondi, scarica di nuovo la diagnostica e confronta
   `state_cache` con la baseline.
4. Il codice che è cambiato è quello della funzione:
   - **AUTO**: quasi certamente cambia il codice `64` verso un valore
     diverso da 1 e 4 (es. 2 o 3). Quel valore va nel campo
     *Fan mode value for AUTO*.
   - **Colore luce**: muovi lo slider caldo/freddo nell'app e osserva quale
     codice si muove (atteso 0–100). Quel codice va in
     *Light color capability code*.
   - **Qualità aria**: il sensore cambia da solo — soffia vicino alla cappa
     (o cucina qualcosa) e osserva quale codice si muove senza che tu tocchi
     nulla. Quel codice va in *Air quality sensor capability code*.
5. Ripeti per ogni funzione, una alla volta.

Suggerimento: `diff <(jq .state_cache prima.json) <(jq .state_cache dopo.json)`

## Metodo 2 — mitmproxy (per verificare i payload dei comandi)

Se vuoi vedere anche *come* l'app invia i comandi (utile se AUTO usasse un
codice dedicato invece di un valore di 64):

1. `mitmproxy` sul PC, proxy configurato sul telefono, certificato mitm
   installato (l'app non usa certificate pinning).
2. Attiva la funzione dall'app e osserva la `POST
   /eiot-api/v1/devices/{id}/commands`: il campo `capabilities` contiene
   esattamente i codici e i valori da usare.

## Dopo la scoperta

Inserisci i codici nelle Opzioni dell'integrazione: HA la ricarica da solo e
compaiono le nuove entità/funzioni:

- **Qualità aria** → nuovo `sensor` (valore grezzo com'è riportato dal cloud).
- **AUTO** → preset mode `auto` sull'entità `fan` (usabile anche nelle
  automazioni: `fan.set_preset_mode`).
- **Colore luce** → l'entità `light` guadagna il controllo di temperatura
  colore (assunto tunable white 0–100 mappato su 2700–6500 K; se la scala
  risultasse invertita o diversa, i limiti sono in `const.py`:
  `LIGHT_COLOR_MIN_KELVIN` / `LIGHT_COLOR_MAX_KELVIN`).

Se scopri i codici, condividili in un issue sul repo originale: aiuterai chi
ha la stessa cappa.
