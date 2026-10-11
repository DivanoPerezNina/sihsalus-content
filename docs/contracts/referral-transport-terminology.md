# Contrato de terminología para transporte de referencia institucional

## Fuente de verdad

Los modos de transporte usados por la Hoja de Referencia Institucional viven exclusivamente en el
source OCL `SIHSALUS/referencia-institucional`. La primera release aprobada es `2026-08-25-01` y
contiene exactamente tres conceptos activos `Misc/N/A`, sin mappings:

| Código OCL | UUID OpenMRS | Nombre preferido en español | Nombre corto |
| --- | --- | --- | --- |
| `REF-TR-01` | `844be877-6d20-45e2-876f-dc5de42edd67` | Transporte terrestre para referencia | Terrestre |
| `REF-TR-02` | `2a228c88-7daf-4f60-9e55-c884c9302bd8` | Transporte aéreo para referencia | Aéreo |
| `REF-TR-03` | `d5e04df9-d1dc-431e-bd71-c934ec3e18e2` | Transporte fluvial para referencia | Fluvial |

Los UUIDs proceden del contenido introducido en el commit
`6d888833a4d445ea408c45c133f12c7dbf5ddbb6` y deben permanecer estables. La migración conserva
también los nombres completos y cortos en inglés y las descripciones en español del CSV original.

## Export estático

El export oficial combinado de OCL tiene SHA-256
`7aace7703f32045901838a1b1e44fcc6648f9f1f872dd4948437d1c686f17ada`. El paquete distribuye su
partición reproducible de conceptos como
`16_SIHSALUS_referencia-institucional_concepts_2026-08-25-01.zip`, con SHA-256
`f96a5afbda6084af5b4a26425e4d5cbef45809c708414d90d2a40bbd81cd51cf`. El JSON canónico del
export tiene SHA-256 `9a85ebac1f3710be861ddb092fb9806eee0e5d60557e494bcdb742be510aedff`.

El validador fija source, versión, release, inventario, UUIDs, códigos, nombres, descripciones, clase,
datatype, URLs y unicidad dentro del bundle. También exige que
`configuration/concepts/referral_transport_concepts.csv` permanezca ausente.

Este catálogo conserva su release independiente del source principal. Su migración no modifica los
mappings `Q-AND-A` de `sihsalus`; el frontend coordinado utiliza explícitamente los tres UUIDs
como respuestas permitidas. Desde `1.25.19`, el paquete incorpora el export principal `2026-09-09-1`
con las exclusiones de barrios documentadas en [la auditoría OCL](../audits/2026-09-12-ocl-refresh.md);
`openconceptlab.subscriptionUrl` conserva la release `2026-07-16-02` de OCL Cloud
y el namespace validado de los imports existentes. La transición al servidor
institucional sigue pendiente de validación nativa de upgrade; los mappings
`Q-AND-A` de este catálogo conservan sus identidades.

## Actualización

Para cambiar este catálogo:

1. Preservar los códigos y UUIDs existentes; una corrección de nombre no crea otro concepto.
2. Publicar una nueva release de `referencia-institucional` y descargar su export oficial.
3. Sustituir el ZIP del slot `16_` y retirar la versión anterior en el mismo cambio.
4. Mantener el CSV de Initializer ausente y ejecutar todos los validadores del paquete.
5. Validar una importación en base limpia y el guardado/lectura de una referencia con datos sintéticos
   antes del despliegue.
