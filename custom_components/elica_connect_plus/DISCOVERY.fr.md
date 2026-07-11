# Découvrir les codes de capability de votre hotte

🇬🇧 [English](DISCOVERY.md) · 🇮🇹 [Italiano](DISCOVERY.it.md) · 🇩🇪 [Deutsch](DISCOVERY.de.md) · 🇪🇸 [Español](DISCOVERY.es.md)

L'API cloud d'Elica représente chaque fonction de la hotte par une paire
`code : valeur` dans le champ `dataModel`. L'intégration fonctionne avec
**toutes les hottes Elica Connect** ; cette page est le *chercheur de codes*
intégré pour activer les fonctions propres au modèle. Codes confirmés pour la
**Elica Illusion** (dataModelIdx 8) :

| Code | Fonction | Valeurs |
|------|----------|---------|
| 64 | Mode ventilateur | 1=normal, 4=boost, 16=auto (les valeurs suggèrent un masque de bits) |
| 96 | Luminosité éclairage principal | 0–100 (%; 0=éteint) |
| 97 | Couleur éclairage principal (blanc réglable) | 0=chaude – 100=froide |
| 100 | Luminosité éclairage d'ambiance | 0–100 ; l'éclairage d'ambiance n'a pas de contrôle de couleur |
| 110 | Vitesse ventilateur | 0=arrêt, 1–3 (également signalée en mode auto) |
| 112 | Qualité de l'air | 1=excellente … 5=très mauvaise |
| 432 | Minuterie d'arrêt | minutes ; écrire N démarre un compte à rebours de N minutes géré par le firmware, la valeur descend jusqu'à 0 |

D'autres modèles de hotte peuvent utiliser des codes différents :
l'intégration les prend en charge via les Options — il suffit de les
identifier une seule fois.

## Méthode 1 — Lecture du log MQTT en direct (recommandée)

L'intégration reçoit **tous** les codes du dataModel via push MQTT, y compris
les inconnus. Avec la journalisation de débogage activée, chaque changement
apparaît dans le log de HA en temps réel :

1. Ajoutez à `configuration.yaml` et redémarrez :
   ```yaml
   logger:
     default: warning
     logs:
       custom_components.elica_connect_plus: debug
   ```
2. Observez le log (`tail -f /config/home-assistant.log | grep "Elica MQTT"`).
3. Dans l'application Elica, changez **une seule** chose à la fois (activer
   auto, déplacer un curseur) et attendez la ligne correspondante :
   `Elica MQTT: state update {'97': 100}`
4. Le code qui a changé est celui que vous cherchez. Saisissez-le dans
   *Paramètres → Appareils et services → Elica Connect Plus → Configurer*.
5. Pour le capteur de qualité de l'air, ne touchez à rien : soufflez vers la
   grille ou vaporisez quelque chose à proximité et observez quel code change
   de lui-même.

## Méthode 2 — Comparaison des diagnostics

Sans accès au log : téléchargez le diagnostic (page de l'appareil → ⋮ →
Télécharger le diagnostic), changez une chose dans l'application,
téléchargez à nouveau après ~10 secondes et comparez les sections
`state_cache` :
`diff <(jq .state_cache avant.json) <(jq .state_cache apres.json)`

## Méthode 3 — mitmproxy

Pour voir aussi comment l'application *écrit* les commandes : lancez
mitmproxy, faites passer le téléphone par lui (l'application n'a pas de
certificate pinning) et observez `POST /eiot-api/v1/devices/{id}/commands` —
le champ `capabilities` contient les codes et valeurs exacts.

## Notes de terrain — Elica Illusion (dataModelIdx 8)

- Le code **112** n'apparaît pas dans le vidage complet du dataModel au
  repos : il n'est publié via MQTT que lorsque le capteur est actif
  (généralement en mode auto). Après un redémarrage de HA, le capteur reste
  `unavailable` jusqu'à l'arrivée de la première valeur.
- En mode auto, la vitesse réelle continue d'être signalée dans le code 110 :
  HA affiche à la fois le préréglage `auto` et le pourcentage actuel.
- Les commandes REST utilisent le `device_id` (p. ex. `Utya8g`), le topic
  MQTT utilise le `cuid` (p. ex. `J2BDYM2XTVYC`) : identifiants différents,
  tous deux corrects.
- Le code **5** apparaît souvent dans les mises à jour à 0 avec d'autres
  changements : il ressemble à un indicateur de transition du firmware et
  peut être ignoré.

Vous avez trouvé des codes pour un autre modèle ? Ouvrez une issue
**Capability report** pour les documenter pour tout le monde.
