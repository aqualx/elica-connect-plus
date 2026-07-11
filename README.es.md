# Elica Connect Plus

Integración mejorada de Home Assistant para campanas extractoras
**Elica Connect** (ESP32-C6, app `com.replyconnect.elica`). Fork de
[benedettosiddi/elica-connect-ha](https://github.com/benedettosiddi/elica-connect-ha)
con conectividad cloud reforzada, funciones opcionales y una suite de
pruebas completa.

🇬🇧 [English](README.md) · 🇮🇹 [Italiano](README.it.md) · 🇩🇪 [Deutsch](README.de.md) · 🇫🇷 [Français](README.fr.md)

> Verificada en: **Elica Illusion** (dataModelIdx 8, PRF0199706) —
> compatible con todas las campanas **Elica Connect**, ver Compatibilidad — HA 2024.11+, verificada en 2026.7

## Entidades

| Entidad | Tipo | Descripción |
|---------|------|-------------|
| Ventilador | `fan` | Presets con nombre + porcentaje; preset auto opcional |
| Luz | `light` | On/off + brillo; temperatura de color con presets (opcional) |
| Luz ambiental | `light` | Luz secundaria opcional: regulable |
| Filtro | `sensor` | Eficiencia del filtro antigrasa % |
| Calidad del aire | `sensor` | Opcional |

Estado en tiempo real vía **push MQTT en la nube**, con sondeo keep-alive
configurable.

## Compatibilidad

| Campana | Estado |
|---------|--------|
| **Elica Illusion** (dataModelIdx 8) | ✅ Totalmente verificada: todos los códigos de capability confirmados en un dispositivo real |
| Cualquier otra campana **Elica Connect** (app `com.replyconnect.elica`) | ✅ Compatible: las entidades base (ventilador, luz principal, filtro) funcionan de inmediato; las funciones específicas del modelo se activan con el **buscador de códigos** integrado — ver [DISCOVERY.es.md](custom_components/elica_connect_plus/DISCOVERY.es.md) |

La API cloud es la misma para toda la gama Elica Connect; solo varían los
códigos de capability de algunas funciones. Para eso sirve el flujo
Opciones + buscador de códigos.

## Mejoras respecto a la integración original

- **Push MQTT resiliente**: reconexión automática con backoff; cuando el
  token OAuth caduca, se pasan nuevas credenciales MQTT al cliente para que
  las actualizaciones en tiempo real nunca fallen en silencio
- **Renovación proactiva del token** según el claim `exp` del JWT
- **Flujo de reautenticación**: una contraseña cambiada activa el diálogo
  estándar en lugar de un error permanente
- **Protección de duplicados**: una entrada por campana (`unique_id`)
- **Estado optimista robusto** con reversión ante errores
- **Diagnóstico descargable** con ocultación de datos sensibles
- **Opciones** para códigos de capability aún no mapeados
- **Suite de pruebas** (29 pruebas)

## Instalación

### HACS (recomendado)

1. HACS → ⋮ → *Repositorios personalizados* → añade este repositorio como
   **Integration**
2. Instala **Elica Connect Plus** y reinicia Home Assistant
3. *Ajustes → Dispositivos y servicios → Añadir integración* →
   **Elica Connect Plus**
4. Introduce las credenciales de la app Elica Connect

### Manual

Copia `custom_components/elica_connect_plus/` en tu carpeta
`custom_components/` de HA y reinicia.

## Funciones opcionales

Calidad del aire, modo AUTO, color de la luz y luz ambiental usan códigos de
capability que varían según el modelo. Descúbrelos con
[DISCOVERY.es.md](custom_components/elica_connect_plus/DISCOVERY.es.md) e
introdúcelos en *Ajustes → Dispositivos y servicios → Elica Connect Plus →
Configurar*.

## Códigos de capability confirmados — Elica Illusion (dataModelIdx 8)

| Código | Función | Valores |
|--------|---------|---------|
| 64 | Modo ventilador | 1=normal, 4=boost, 16=auto (máscara de bits) |
| 96 | Brillo luz principal | 0–100 |
| 97 | Color luz principal | 0=cálida – 100=fría |
| 100 | Brillo luz ambiental | 0–100 (solo regulable) |
| 110 | Velocidad ventilador | 0=apagado, 1–3 |
| 112 | Calidad del aire | 1=excelente … 5=muy mala |

## Idiomas

Inglés (predeterminado), italiano, alemán, español y francés, según el
idioma de la interfaz de HA.

## Automatizaciones de ejemplo

Consulta [docs/automations.md](docs/automations.md) para YAML listo para
usar: arranque automático al cocinar, apagado retardado, avisos de
mantenimiento del filtro, luz de cortesía nocturna.

¿Prefieres botones redondos en lugar de los menús desplegables? Consulta la
[guía de dashboard](docs/dashboard.md) opcional (YAML nativo o
`custom:button-card`).

¿Usas Amazon Alexa? Consulta la [guía de Alexa](docs/alexa.md) opcional para
control por voz y anuncios hablados (algunos ejemplos requieren la
integración Alexa Media Player).

## Desarrollo

```bash
pip install -r requirements_test.txt
pytest tests/
```

La CI ejecuta la suite de pruebas y las validaciones hassfest y HACS en cada
push.

## Licencia

Publicado bajo la [Licencia MIT](LICENSE), © 2026 Roberto Marturano.

Este proyecto es un fork de
[elica-connect-ha](https://github.com/benedettosiddi/elica-connect-ha) de
[@benedettosiddi](https://github.com/benedettosiddi) y amplía su trabajo —
pleno reconocimiento al reverse engineering original.

## Créditos

API cloud analizada mediante mitmproxy por
[@benedettosiddi](https://github.com/benedettosiddi), sobre cuyo trabajo se
basa este fork.

## Aviso legal

**Elica Connect Plus es un proyecto independiente y no oficial. No está
afiliado, autorizado ni respaldado por Elica S.p.A.**, proveedora del sistema
Elica Connect y su ecosistema. «Elica», «Elica Connect» y todos los nombres,
marcas y logotipos relacionados son marcas de Elica S.p.A. o de sus
respectivos propietarios, utilizados aquí solo con fines identificativos.
Esta integración se basa en una interfaz obtenida por ingeniería inversa y no
documentada, que puede cambiar o dejar de funcionar en cualquier momento.

El software se proporciona «tal cual», sin garantía de ningún tipo. Los
autores y colaboradores no asumen **ninguna responsabilidad** por daños a
electrodomésticos o bienes, fallos de funcionamiento, pérdida de datos,
interrupciones del servicio o problemas con la cuenta derivados de su uso.
**El uso es enteramente bajo tu propia responsabilidad.**

Consulta [DISCLAIMER.md](DISCLAIMER.md) para el texto completo (disponible en
English, Italiano, Deutsch, Español y Français).
