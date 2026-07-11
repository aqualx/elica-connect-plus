# Elica Connect Plus

Intégration Home Assistant améliorée pour les hottes **Elica Connect**
(ESP32-C6, application `com.replyconnect.elica`). Fork de
[benedettosiddi/elica-connect-ha](https://github.com/benedettosiddi/elica-connect-ha)
avec une connectivité cloud renforcée, des fonctions optionnelles et une
suite de tests complète.

🇬🇧 [English](README.md) · 🇮🇹 [Italiano](README.it.md) · 🇩🇪 [Deutsch](README.de.md) · 🇪🇸 [Español](README.es.md)

> Vérifiée sur : **Elica Illusion** (dataModelIdx 8, PRF0199706) —
> compatible avec toutes les hottes **Elica Connect**, voir Compatibilité — HA 2024.11+, vérifiée sur 2026.7

## Entités

| Entité | Type | Description |
|--------|------|-------------|
| Ventilateur | `fan` | Préréglages nommés + pourcentage ; préréglage auto optionnel |
| Éclairage | `light` | On/off + luminosité ; température de couleur avec préréglages (optionnel) |
| Éclairage d'ambiance | `light` | Éclairage secondaire optionnel : variable |
| Filtre | `sensor` | Efficacité du filtre à graisse % |
| Qualité de l'air | `sensor` | Optionnel |

État en temps réel via **push MQTT cloud**, avec interrogation keep-alive
configurable.

## Compatibilité

| Hotte | État |
|-------|------|
| **Elica Illusion** (dataModelIdx 8) | ✅ Entièrement vérifiée : tous les codes de capability confirmés sur un appareil réel |
| Toute autre hotte **Elica Connect** (application `com.replyconnect.elica`) | ✅ Compatible : les entités de base (ventilateur, éclairage principal, filtre) fonctionnent immédiatement ; les fonctions propres au modèle s'activent via le **chercheur de codes** intégré — voir [DISCOVERY.fr.md](custom_components/elica_connect_plus/DISCOVERY.fr.md) |

L'API cloud est la même pour toute la gamme Elica Connect ; seuls les codes
de capability de certaines fonctions varient selon le modèle. C'est
précisément le rôle du flux Options + chercheur de codes.

## Améliorations par rapport à l'intégration d'origine

- **Push MQTT résilient** : reconnexion automatique avec backoff ; à
  l'expiration du jeton OAuth, de nouvelles informations d'identification
  MQTT sont transmises au client afin que les mises à jour en temps réel ne
  s'arrêtent jamais silencieusement
- **Renouvellement proactif du jeton** basé sur le claim `exp` du JWT
- **Flux de ré-authentification** : un mot de passe modifié déclenche la
  bannière standard au lieu d'une erreur permanente
- **Protection contre les doublons** : une entrée par hotte (`unique_id`)
- **État optimiste robuste** avec restauration en cas d'erreur
- **Diagnostic téléchargeable** avec masquage des données sensibles
- **Options** pour les codes de capability non encore mappés
- **Suite de tests** (29 tests)

## Installation

### HACS (recommandé)

1. HACS → ⋮ → *Dépôts personnalisés* → ajoutez ce dépôt comme
   **Integration**
2. Installez **Elica Connect Plus** et redémarrez Home Assistant
3. *Paramètres → Appareils et services → Ajouter une intégration* →
   **Elica Connect Plus**
4. Saisissez les identifiants de l'application Elica Connect

### Manuel

Copiez `custom_components/elica_connect_plus/` dans votre dossier
`custom_components/` de HA et redémarrez.

## Fonctions optionnelles

La qualité de l'air, le mode AUTO, la couleur de l'éclairage et l'éclairage
d'ambiance utilisent des codes de capability qui varient selon le modèle.
Identifiez-les avec
[DISCOVERY.fr.md](custom_components/elica_connect_plus/DISCOVERY.fr.md) et
saisissez-les dans *Paramètres → Appareils et services → Elica Connect Plus →
Configurer*.

## Codes de capability confirmés — Elica Illusion (dataModelIdx 8)

| Code | Fonction | Valeurs |
|------|----------|---------|
| 64 | Mode ventilateur | 1=normal, 4=boost, 16=auto (masque de bits) |
| 96 | Luminosité éclairage principal | 0–100 |
| 97 | Couleur éclairage principal | 0=chaude – 100=froide |
| 100 | Luminosité éclairage d'ambiance | 0–100 (variateur uniquement) |
| 110 | Vitesse ventilateur | 0=arrêt, 1–3 |
| 112 | Qualité de l'air | 1=excellente … 5=très mauvaise |

## Langues

Anglais (par défaut), italien, allemand, espagnol et français, selon la
langue de l'interface HA.

## Exemples d'automatisations

Voir [docs/automations.md](docs/automations.md) pour du YAML prêt à
l'emploi : démarrage automatique pendant la cuisson, arrêt différé, alertes
d'entretien du filtre, éclairage de courtoisie nocturne.

Vous préférez des boutons ronds aux menus déroulants ? Voir le
[guide dashboard](docs/dashboard.md) optionnel (YAML natif ou
`custom:button-card`).

Vous utilisez Amazon Alexa ? Voir le [guide Alexa](docs/alexa.md) optionnel
pour le contrôle vocal et les annonces vocales (certains exemples nécessitent
l'intégration Alexa Media Player).

## Développement

```bash
pip install -r requirements_test.txt
pytest tests/
```

La CI exécute la suite de tests ainsi que les validations hassfest et HACS à
chaque push.

## Licence

Publié sous [licence MIT](LICENSE), © 2026 Roberto Marturano.

Ce projet est un fork de
[elica-connect-ha](https://github.com/benedettosiddi/elica-connect-ha) de
[@benedettosiddi](https://github.com/benedettosiddi) et étend son travail —
plein crédit au reverse engineering d'origine.

## Remerciements

API cloud analysée via mitmproxy par
[@benedettosiddi](https://github.com/benedettosiddi), sur le travail duquel
ce fork est basé.

## Avertissement

**Elica Connect Plus est un projet indépendant et non officiel. Il n'est ni
affilié, ni autorisé, ni approuvé par Elica S.p.A.**, fournisseur du système
Elica Connect et de son écosystème. « Elica », « Elica Connect » et tous les
noms, marques et logos associés sont des marques d'Elica S.p.A. ou de leurs
propriétaires respectifs, utilisés ici uniquement à des fins d'identification.
Cette intégration repose sur une interface obtenue par rétro-ingénierie et non
documentée, susceptible de changer ou de cesser de fonctionner à tout moment.

Le logiciel est fourni « tel quel », sans garantie d'aucune sorte. Les auteurs
et contributeurs déclinent **toute responsabilité** en cas de dommage aux
appareils ou aux biens, de dysfonctionnement, de perte de données,
d'interruption de service ou de problème de compte résultant de son
utilisation. **Vous l'utilisez entièrement à vos propres risques.**

Voir [DISCLAIMER.md](DISCLAIMER.md) pour le texte complet (disponible en
English, Italiano, Deutsch, Español et Français).
