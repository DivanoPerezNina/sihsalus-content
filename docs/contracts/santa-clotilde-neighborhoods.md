# Contrato del catálogo de barrios de Santa Clotilde

## Alcance y fuente de verdad

El barrio de residencia es un atributo codificado de persona con UUID
`4a182c6e-9a19-4db8-8042-4bbf3b4308c2`. Sus valores activos pertenecen al set
`0fd3e744-6d2c-4cb3-9b7e-1f88899635d9`; el catálogo activo vive exclusivamente en la fuente OCL
`SIHSALUS/barrios-santa-clotilde`.

La primera release aceptada por este paquete es `2026-08-22-01`. Debe contener exactamente los diez
conceptos `SCL-01` a `SCL-10`, el concepto `SCL-BARRIOS` y diez mappings `CONCEPT-SET`. Los UUIDs de
OpenMRS son estables y el validador de CI comprueba IDs, UUIDs, nombres, clase, datatype, membresía,
orden y aislamiento respecto de `SIHSALUS/sihsalus`.

El export oficial combinado de esta release tiene SHA-256
`8430529c7325c11679eedb58e1e86340557523522284acc830c3f365c7d32fda`. El paquete lo divide con
`.github/scripts/split_ocl_export.py`; el JSON canónico recombinado debe conservar SHA-256
`fbcb4f0ed111ceb4c686ac343eee09c2435037f8dceb9b679cee0a226e1c9177`. Se verifica el contenido
canónico porque la metadata ZIP y el formato JSON no son evidencia terminológica.

Los campos OCL `extras.ui_color` y `extras.ui_tag_type` conservan metadata descriptiva de presentación.
No son clínicos, no forman parte del valor persistido y no garantizan su renderizado. El frontend actual
no los consume: obtiene las opciones desde `answerConceptSetUuid` y no duplica el catálogo en
`customConceptAnswers`.

Este paquete solo distribuye la metadata backend y los exports OCL. La configuración efectiva de
registro, búsqueda y banner pertenece a `sihsalus-frontend/config/frontend.json`; no se mantiene ni se
empaqueta una copia de configuración frontend en este repositorio.

## Historial retirado en `sihsalus`

La release errónea del source principal fue eliminada, pero OCL no permite a un administrador de la
organización purgar definitivamente los mappings. Por ello, los once conceptos y diez mappings quedaron
retirados en el HEAD de `SIHSALUS/sihsalus`. No forman parte de los exports principales bundleados por
este paquete y la nueva fuente es la única fuente activa del catálogo.

No se debe publicar ni incorporar una release futura de `sihsalus` que contenga esos UUIDs retirados
hasta que el personal de la plataforma OCL los purgue o el proceso de export los excluya explícitamente.
El validador bloquea cualquier duplicación bundleada, incluso retirada, para evitar que una importación
posterior reintroduzca o altere el catálogo.

Desde `1.25.19`, el paquete incluye el export principal `2026-09-09-1` con
exclusiones explícitas verificadas antes de dividir el ZIP. Solo se excluyen las once identidades
de conceptos y diez de mappings retirados que pertenecen a este catálogo. El manifiesto,
la reproducción y los hashes constan en [la auditoría OCL](../audits/2026-09-12-ocl-refresh.md).
El filtro rechaza registros activos o distintos de los revisados; no es una eliminación general
de registros retirados.

## Corte desde `ADDRESS_3`

`person_address.address3` se utilizó previamente para almacenar el barrio como texto libre. La primera
fase retiró `ADDRESS_3/Barrio` de `addressConfiguration.xml` y del formato visible de la dirección tras
comprobar la ausencia de datos que requirieran migración en el entorno revisado. Este corte no incluye scripts de
migración, aliases ni reconciliación. Si otro entorno contiene datos en ese campo, el
cambio debe bloquearse y rediseñarse; no se debe inferir ni transformar direcciones automáticamente.

## Actualización del catálogo

Para agregar o corregir un barrio:

1. Preservar los IDs y UUIDs existentes; una corrección de nombre no crea un concepto nuevo.
2. Publicar una nueva versión released de `barrios-santa-clotilde`.
3. Descargar los exports oficiales de conceptos y mappings, ubicarlos en los slots `15_` y `65_`, y
   retirar los dos exports de la versión anterior en el mismo cambio.
4. En el repositorio frontend, verificar que registro y búsqueda continúan apuntando al mismo
   `answerConceptSetUuid`; no duplicar respuestas ni metadata de presentación en su configuración.
5. Ejecutar todos los validadores del content package y una importación desde una base limpia antes de
   desplegar.

El global property `openconceptlab.subscriptionUrl` conserva la release
`2026-07-16-02` de OCL Cloud. Esa versión no contiene los UUID de barrios ni
elimina conceptos ausentes: es compatible con los dos conceptos activos
adicionales del export principal `2026-09-09-1`. Los barrios se cargan
exclusivamente desde sus ZIPs estáticos.

La preparación institucional de #254 cambió el host de esa propiedad; se
restaura el namespace anterior porque la instalación nueva pasó, pero los
escenarios nativos de upgrade y alias operativo abortaron en OCL (CI de main
`64fdf16`, run `37420274108`, y candidato `cc50fab`, run `38102454311`).
OCL 3.2.0 usa el host de la suscripción para resolver también las URLs relativas
de los ZIPs locales. Los imports previos conservan sus URLs y los ZIPs sin cambios
conservan sus checksums: cambiar sólo la propiedad no demuestra una transición
compatible. Se mantiene `fail_on_error`; no se borran checksums ni registros de
imports y no se fuerza una recarga. La excepción inferior no está preservada en
los artefactos sanitizados, por lo que el mecanismo identificado en la fuente
no se presenta como una excepción observada.

La activación de la release institucional curada `sihsalus/2026-09-09-1` queda
pendiente de una transición soportada por el componente OCL y probada con
instalación nueva, upgrade, referencias cruzadas y reinicio. El importador remoto
no aplica las exclusiones del paquete: también debe comprobarse el export
servido. Una futura release principal que modifique registros existentes debe
revisar la suscripción para evitar sobrescribirlos con metadata anterior.

La revisión del 2026-10-05 descargó el export autenticado de la release institucional:
contiene 4474 conceptos y 5679 mappings, sin las 21 identidades excluidas. Al comparar
por ID con los dos ZIPs del paquete, coinciden los UUIDs externos, nombres,
descripciones, clases, datatypes, estado de retiro, respuestas, miembros de sets y
códigos de mappings. La migración regeneró IDs internos de versiones y nombres;
413 mappings a fuentes externas ya no incluyen `to_concept_url`. Ninguno de esos
413 es `Q-AND-A` ni `CONCEPT-SET`; el importador de OpenMRS utiliza fuente y código
para sus términos de referencia. Esta comparación estática no acredita que una
sincronización completa termine correctamente en OpenMRS. La primera ejecución
debe ensayarse con una base sintética aislada y comprobar catálogo, errores y
reinicio antes de activar la suscripción en DEV o QLTY.
