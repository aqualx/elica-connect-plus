# Elica Connect Plus

Integrazione Home Assistant potenziata per cappe **Elica Connect**
(ESP32-C6, app `com.replyconnect.elica`). Fork di
[benedettosiddi/elica-connect-ha](https://github.com/benedettosiddi/elica-connect-ha)
con connettività cloud irrobustita, funzionalità opzionali e suite di test
completa.

🇬🇧 [English](README.md) · 🇩🇪 [Deutsch](README.de.md) · 🇪🇸 [Español](README.es.md) · 🇫🇷 [Français](README.fr.md)

> Verificata su: **Elica Illusion** (dataModelIdx 8, PRF0199706) — compatibile con tutte le cappe **Elica Connect**, vedi Compatibilità — HA 2024.11+, verificata su 2026.7

## Entità

| Entità | Tipo | Descrizione |
|--------|------|-------------|
| Fan | `fan` | Preset velocità nominati + percentuale; preset auto opzionale (nomi localizzati in italiano) |
| Light | `light` | On/off + dimmer; tunable white opzionale con preset nominati |
| Ambient light | `light` | Luce secondaria opzionale: dimmer + tunable white |
| Filter | `sensor` | Efficienza filtro antigrasso % |
| Air quality | `sensor` | Opzionale (vedi sotto) |
| Timer | `number` | Timer di spegnimento nativo opzionale (minuti) |

Stato in tempo reale via **push MQTT cloud**, con poll REST di verifica ogni
5 minuti. I comandi sono ottimistici: la UI reagisce all'istante e torna
indietro da sola se il cloud rifiuta il comando.

## Compatibilità

| Cappa | Stato |
|-------|-------|
| **Elica Illusion** (dataModelIdx 8) | ✅ Completamente verificata: tutti i codici capability confermati su dispositivo reale (tabella sotto) |
| Qualsiasi altra cappa **Elica Connect** (app `com.replyconnect.elica`) | ✅ Compatibile: le entità base (ventola, luce principale, filtro) funzionano subito; le funzioni specifiche del modello si attivano con il **trova codice** integrato — vedi [DISCOVERY.it.md](custom_components/elica_connect_plus/DISCOVERY.it.md) |

L'API cloud è la stessa per tutta la gamma Elica Connect; variano solo i
codici capability di alcune funzioni. Il flusso Opzioni + trova codice serve
esattamente a questo: identifichi i codici della tua cappa una volta sola,
li inserisci, fatto. Condividi quello che trovi con un issue
"Capability report".

## Miglioramenti rispetto all'integrazione originale

- **Push MQTT resiliente**: riconnessione automatica con backoff; alla
  scadenza del token OAuth le nuove credenziali MQTT vengono passate al
  client, così il push non muore mai silenziosamente
- **Rinnovo proattivo del token** basato sul claim `exp` del JWT
- **Reauth flow**: password Elica cambiata → banner standard di HA invece
  di errore permanente
- **Anti-duplicati**: una config entry per cappa (`unique_id`)
- **Stato ottimistico robusto**: niente rimbalzi della UI, rollback su errore
- **Diagnostica scaricabile** con oscuramento dei dati sensibili
- **Broker MQTT configurabile** (host/porta) nelle Opzioni, così un futuro
  cambio del broker Elica non richiede una nuova release
- **Options flow** per i codici capability delle funzioni non ancora mappate
- **Suite di test**: 20 test con `pytest-homeassistant-custom-component`

## Installazione

### HACS (consigliato)

1. HACS → ⋮ → *Repository personalizzati* → aggiungi questo repo come
   **Integration**
2. Installa **Elica Connect Plus** e riavvia Home Assistant
3. *Impostazioni → Dispositivi e servizi → Aggiungi integrazione* →
   **Elica Connect Plus**
4. Inserisci le credenziali dell'app Elica Connect

### Manuale

Copia `custom_components/elica_connect_plus/` nella cartella
`custom_components/` di HA e riavvia.

> **Arrivi dall'integrazione originale?** Rimuovila prima: il dominio è
> diverso (`elica_connect_plus`), quindi gli entity_id cambieranno —
> controlla le automazioni.

## Funzionalità opzionali

Qualità dell'aria, modalità AUTO e colore luce usano codici capability del
dataModel **non ancora documentati pubblicamente**, che possono variare per
modello. L'integrazione li supporta già, dietro le Opzioni:

1. Scopri i codici sulla *tua* cappa seguendo
   [DISCOVERY.it.md](custom_components/elica_connect_plus/DISCOVERY.it.md)
   (bastano due download della diagnostica, nessuno strumento esterno)
2. Inseriscili in *Impostazioni → Dispositivi e servizi → Elica Connect
   Plus → Configura*
3. L'integrazione si ricarica da sola e compaiono le nuove entità/funzioni

Hai trovato i codici per il tuo modello? [Apri un issue](../../issues) così
li documentiamo per tutti.

## Codici capability confermati — Elica Illusion (dataModelIdx 8)

| Codice | Funzione | Valori |
|--------|----------|--------|
| 64 | Modalità ventola | 1=normale, 4=boost |
| 96 | Luminosità luce | 0–100 (%; 0=off) |
| 110 | Velocità ventola | 0=off, 1–3 |
| 97 | Colore luce (tunable white) | 0=calda – 100=fredda |
| 64 | Modalità ventola (esteso) | 16=auto (bitmask: 1=normale, 4=boost, 16=auto) |
| 112 | Qualità aria | 1=Ottima, 2=Buona, 3=Media, 4=Scarsa, 5=Pessima; pubblicato solo a sensore attivo (auto) |
| 432 | Timer di spegnimento | minuti (conto alla rovescia firmware fino a 0) |
| 100 | Luminosità luce ambiente | 0–100 (%; 0=off); solo dimmer, senza colore |

## Lingue

Inglese (default), italiano, tedesco, spagnolo e francese, seguendo la
lingua dell'interfaccia di Home Assistant. Le automazioni usano gli slug
neutri (`medium`, `very_warm`, `fair`, ...).

## Automazioni di esempio

Vedi [docs/automations.md](docs/automations.md): accensione automatica in
cottura, spegnimento ritardato, avviso manutenzione filtro, luce di
cortesia notturna.

Preferisci tasti rotondi ai menu a tendina dei preset? Vedi la
[guida dashboard](docs/dashboard.md) opzionale (YAML nativo o
`custom:button-card`).

Usi Amazon Alexa? Vedi la [guida Alexa](docs/alexa.md) opzionale per comandi
vocali e annunci parlati (alcuni esempi richiedono l'integrazione custom
Alexa Media Player).

## Sviluppo e test

```bash
pip install -r requirements_test.txt
pytest tests/
```

## Licenza

Distribuito con [Licenza MIT](LICENSE), © 2026 Roberto Marturano.

Questo progetto è un fork di
[elica-connect-ha](https://github.com/benedettosiddi/elica-connect-ha) di
[@benedettosiddi](https://github.com/benedettosiddi) e ne amplia il lavoro —
pieno riconoscimento al reverse engineering originale.

## Crediti

API cloud reverse-engineered via mitmproxy da
[@benedettosiddi](https://github.com/benedettosiddi), sul cui lavoro questo
fork si basa.

## Disclaimer

**Elica Connect Plus è un progetto indipendente e non ufficiale. Non è
affiliato, autorizzato né approvato da Elica S.p.A.**, fornitrice del sistema
Elica Connect e del relativo ecosistema. "Elica", "Elica Connect" e tutti i
nomi, marchi e loghi correlati sono marchi di Elica S.p.A. o dei rispettivi
proprietari, qui utilizzati a soli fini identificativi. Questa integrazione
si basa su un'interfaccia ricavata per reverse engineering e non documentata,
che può cambiare o smettere di funzionare in qualsiasi momento.

Il software è fornito "così com'è", senza garanzie di alcun tipo. Gli autori
e i contributori non si assumono **alcuna responsabilità** per danni ad
apparecchiature o cose, malfunzionamenti, perdita di dati, interruzioni del
servizio o problemi con l'account derivanti dal suo utilizzo. **L'uso è
interamente a proprio rischio.**

Vedi [DISCLAIMER.md](DISCLAIMER.md) per il testo completo (disponibile in
English, Italiano, Deutsch, Español e Français).
