# Changelog

Cambios del paquete y sus herramientas, agrupados por versión. Las entradas
históricas describen el contenido de esa revisión; sus rutas y pendientes no
deben interpretarse como instrucciones actuales. Consultar la
[guía de desarrollo](docs/development.md) y los [contratos](docs/README.md).

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Sitios anatómicos de procedimientos — candidata `1.25.32`

- Añade un conjunto de 133 sitios anatómicos humanos basado en los códigos
  HL7 v2-0550, versión 4.0.0 / THO 7.4.0, disponible bajo CC0. Los nombres en
  español son una adaptación SIHSALUS, sin atribuir homologación nacional.
- Reutiliza 13 conceptos históricos, agrega 120 sitios y conserva los demás
  registros y sus clases, tipos de dato, observaciones y UUIDs. El conjunto y
  sus equivalencias se distribuyen mediante exports OCL nativos versionados.
- Requiere el selector de procedimientos configurado por conjunto y la búsqueda
  nativa `q` + `memberOf`. La incorporación al servidor terminológico no activa
  el selector en QLTY. La aceptación clínica continúa pendiente.
- El ensayo existente de Initializer comprueba pertenencia, nombres españoles,
  equivalencias HL7, asociación FHIR, búsqueda y estabilidad al reiniciar en
  fresh y upgrade. La fuente se asocia al URI HL7 mediante el dominio nativo
  `fhirconceptsources`; no acredita intercambio integral de procedimientos.

### Captura CRED y materna — candidata `1.25.31`

- CRED-001 distingue la entrega de micronutrientes del tratamiento de anemia.
  CRED-002, CRED-003 y CRED-005 aclaran la procedencia normativa de sus descripciones.
  Estas aclaraciones conservan identidades, campos, conceptos y valores históricos;
  la auditoría documenta las limitaciones de captura pendientes.
- CRED-011 `1.3.1` retira PHQ-9, AUDIT-C y detección/resultados de violencia
  de la madre o cuidador del encuentro del niño. Conserva PPSC/PSC-17 y orienta
  a registrar los instrumentos del adulto en su propia historia clínica. No
  cambia edades, rangos, conceptos infantiles ni observaciones históricas.

- HOSP-010 `1.0.2` retira del encuentro materno los seis campos del grupo
  Recién Nacido y orienta a registrarlos en la historia propia del niño desde
  Hijos vinculados. Evita atribuir peso y otras observaciones del RN a la madre;
  conserva el esquema histórico sin trasladar ni reinterpretar datos previos.
- OBST-006 `1.0.2` reúne responsable, ubicación y rol en una página. Conserva el
  proveedor que gobierna el envío y retira solo el segundo control duplicado de
  proveedor del nuevo esquema; el esquema anterior y sus encuentros permanecen.
- OBST-001 `1.0.1` permite declarar «Ninguna» en antecedentes familiares y
  personales con la respuesta canónica existente; impide combinarla con enfermedades.
- La vía de parto, nacidos vivos/muertos y peso del RN se capturan de forma
  independiente del contador de partos a término. Conserva conceptos, límites y
  campos opcionales; no redefine paridad ni total de partos. La semántica histórica
  del concepto `8795c05b-f286-4d70-a1e6-69172e676f05` sigue pendiente de revisión
  clínica y terminológica.
- Evolución mediante el loader nativo de formularios; la guarda existente de
  Initializer incluye el nuevo esquema y la conservación de las versiones anteriores.

- OBST-013 retira los puntos de corte universales de las etiquetas de anemia.
  La clasificación confirmada requiere el trimestre y el contexto de altitud.
  Conserva identidad del formulario, conceptos, respuestas, mediciones y datos
  históricos; no calcula una clasificación ni modifica las reglas de laboratorio.

### Compatibilidad de la suscripción OCL — candidata `1.25.31`

- Restaura `openconceptlab.subscriptionUrl` a la release `2026-07-16-02` de
  OCL Cloud, el namespace de importación previamente validado. La preparación
  institucional de #254 cambió el host antes de disponer de una transición
  compatible: fresh pasa, pero los dos escenarios de upgrade abortan en OCL.
- Conserva los exports estáticos `2026-09-09-1`, exclusiones, UUIDs y checksums.
  La release institucional curada sigue documentada, con su activación pendiente
  de una transición nativa probada en instalación nueva y actualización. No
  añade SQL, reimportación forzada ni borrado del historial de imports.

### Relación madre-hijo — candidata `1.25.30`

- Añade el mapeo nativo EmrApi `emr.motherChildRelationshipType` al tipo Madre→Hijo
  existente. Permite consultar los vínculos desde el flujo de parto y la sala
  materna sin crear pacientes, modificar relaciones históricas ni ampliar roles.
  Requiere el frontend coordinado y aceptación con pacientes sintéticos en QLTY.

### Consulta externa — candidata `1.25.28`

- Consulta externa: `CE-001` `1.0.3` elimina la página SOAP del formulario general; el loader retira la versión anterior y conserva su esquema y encuentros.

- Formulario propio `CE-EXF-001-EXAMEN FISICO` `1.0.0`: examen general y por sistemas, sin Subjetivo,
  Objetivo, Apreciación ni Plan duplicados.
- Anamnesis `1.1.0`: ocho selectores explícitos, tres campos de texto y funciones
  biológicas contraídas. Conserva conceptos Text y no predetermina normalidad.
- Retira y despublica el formulario ambulatorio anterior `CE-SOAP-001-NOTA SOAP`
  `1.2.0`, conservando sus preguntas y el histórico de versiones previas.
- Evolución por el loader nativo de formularios, con conservación del histórico;
  amplía la integración de Initializer a ambos esquemas. Requiere el frontend
  coordinado y aceptación clínica QLTY antes de producción.

### Agregado

- Captura opcional de fecha/hora de alta neonatal en el formulario de nacimiento
  y contrato de dependencias clínicas de CRED, sin modificar observaciones históricas.

### Cambiado

- Organiza las fuentes directamente bajo `configuration/`, conservando las
  rutas y los bytes de los 207 archivos del ZIP publicado `1.25.24`.
- Simplifica el build y los validadores, retira configuración de formato sin
  uso y reúne las instrucciones de mantenimiento en `docs/`.
- Actualiza contratos, estados de publicación e índices de documentación;
  conserva la evidencia fechada de auditorías y los doce changesets publicados.

### Corregido

- CRED-001 `1.2.1` activa el aviso de ajuste de hemoglobina desde 500 m e incluye
  hasta 5.500 m. OBST-002 `1.0.2` calcula semanas completas a la fecha de atención,
  conserva el vacío sin FUM y admite fechas probables de parto pasadas.
- Los rangos de hemoglobina neonatal exigen prematuridad explícita y usan la edad
  a la fecha de la muestra. Los maternos distinguen los estados prenatales y de
  posparto; las 40 semanas dejan de funcionar como sustituto del parto.
- Extiende en `1.25.26` la edad a la fecha de la muestra a las siete bandas restantes
  de hemoglobina. Evita que muestras neonatales históricas coincidan también con
  rangos de la edad actual del paciente.
- Desactiva las dos reglas de creatinina normalizada por peso que se aplicaban
  a la medición absoluta de 24 horas. Conserva UUIDs y valores históricos; Core
  vuelve a los límites del concepto, pendientes de validación institucional.
- Añade regresiones de expresiones y selección nativa de rangos; amplía el ensayo
  de Initializer para comprobar esquemas históricos y criterios cargados.
- El validador AMPATH rechaza colisiones de la identidad persistida aunque los
  UUID JSON sean distintos, nombres o versiones vacíos y carpetas sin formularios.
  Comparte el cálculo de identidad con CE-001 e historia social e incorpora
  regresiones con datos sintéticos.

La limpieza de estructura y documentación conserva la metadata de `1.25.24`.
Las correcciones iniciales de formularios y rangos corresponden a `1.25.25`;
el alta neonatal y la ampliación a todas las edades están integradas en `main`
para **`1.25.26`**. El merge no acredita publicación ni despliegue; consultar la
[evidencia fechada de CRED](docs/contracts/cred-clinical-completion.md#evidencia-disponible)
y el resultado del workflow correspondiente.

## [1.25.24] - 2026-09-22

### Agregado

- Incorpora el formulario canónico de [historia social](docs/contracts/social-history.md)
  para alcohol y tabaco, preparado como `1.25.23` en el PR #235.
- Declara los roles operativos de Laboratorio y Soporte del
  [contrato de perfiles hospitalarios](docs/contracts/hospital-access-profiles.md).

### Corregido

- Reconcilia el alias operativo exacto de Admisión y retira su suplemento
  hospitalario, preservando las asignaciones canónicas y rechazando entradas
  fuera del contrato. Conserva las migraciones históricas publicadas.
- Concede `Get Patient Programs` a ambos perfiles de Laboratorio para la
  evaluación nativa de rangos maternos. Añade una integración de autorización
  con Core y amplía los ensayos de migración e Initializer.

La [auditoría de Liquibase](docs/audits/2026-09-22-liquibase-initializer.md)
verifica el XML publicado. La publicación no acredita despliegue ni aceptación
funcional. En la comprobación del 22 de septiembre del
[índice de Maven Central](https://repo.maven.apache.org/maven2/io/github/proyecto-santaclotilde/sihsalus-content/),
`1.25.23` no aparece como release pública independiente.

## [1.25.20] - 2026-09-14

### Agregado

- Provisiona el atributo de visita de [confirmación de pago en Admisión](docs/contracts/arrival-payment.md),
  opcional y de cardinalidad máxima uno, sin transformar visitas históricas.

## [1.25.19] - 2026-09-12

### Cambiado

- Actualiza el export principal OCL a `2026-09-09-1`, con exclusiones reproducibles
  de las identidades retiradas del catálogo de barrios. Conserva la suscripción
  remota anterior y la release de laboratorio; véase la
  [auditoría OCL](docs/audits/2026-09-12-ocl-refresh.md).

### Corregido

- Alinea cuatro límites inferiores de hemoglobina con los puntos de corte
  documentados en el [contrato de laboratorio](docs/contracts/laboratory-reporting.md).
  Los pendientes de población, método e intervalos analíticos siguen explícitos.
- El CI espera la disponibilidad pública del POM y ZIP después de la validación
  de Sonatype, mediante el mecanismo descrito en la
  [guía de publicación](docs/development.md#validación-y-publicación).

## [1.25.18] - 2026-09-12

### Agregado

- Incorpora ácido ursodesoxicólico como concepto local y presentación ordenable
  de 250 mg en tableta mediante CSV nativos, con pruebas de carga, reinicio y
  búsqueda. Véase el [catálogo clínico](docs/clinical-drug-catalog.md).

## [1.25.17] - 2026-09-12

### Corregido

- Revisa rangos de laboratorio y corrige criterios y diagnóstico del arranque
  de Initializer. La [auditoría del PR #225](docs/audits/2026-09-10-laboratory-reference-ranges-pr-225.md)
  conserva el alcance, los fallos detectados y los pendientes clínicos.
- Publica la reconciliación transaccional de Admisión preparada en `1.25.16`.
  La [revisión de artefactos](docs/audits/2026-09-21-admission-maintainability.md)
  confirma su presencia en el ZIP `1.25.17`.

## [1.25.16] - No publicada

### Corregido

- Sustituye la reconciliación candidata de Admisión por una operación
  transaccional con comprobaciones anteriores a la normalización histórica.
  Rechaza políticas de privilegios, herencias, identidades y referencias no
  admitidas; no modifica los changeSets históricos ya publicados.
- Añade controles estructurales y un harness de MariaDB/Liquibase con datos
  sintéticos. No sustituye la validación de Initializer ni de autorización.
  Los requisitos de actualización están en el
  [contrato de Admisión](docs/contracts/admission-role-reconciliation.md).

El número se conserva como antecedente: la comprobación de Maven Central no
encontró un artefacto `1.25.16`; la migración se distribuyó desde `1.25.17`.

## [1.25.15] - 2026-09-07

### Corregido

- Agrega `Delete Relationships` únicamente al rol canónico `Admision` para
  retirar o reemplazar relaciones de responsables y protege ese permiso en su
  lista explícita de privilegios.
- Añade regresiones que rechazan la pérdida del permiso, privilegios adicionales,
  herencia y cambios de identidad del rol. No incorpora la consolidación adicional
  de roles ni cambia las migraciones existentes.

## [1.25.14] - 2026-08-26

### Agregado

- Registra en el rol canónico `Laboratorio` los marcadores declarativos
  `Create Attachments` y `View Attachments`, conservando `Add Observations`
  como parte del contrato clínico existente. Estos marcadores no habilitan el
  flujo por sí solos; Attachments 4.0.0 no es compatible y permanece no
  operativo.
- Completa el contrato del adjuntador genérico: el rol lector conserva
  `View Attachments` y el rol editor recibe `Create Attachments` y
  `View Attachments`, sin ampliar otros roles.

### Seguridad

- Mantiene fuera del rol el marcador general
  `app:hoja.clinica.adjuntos.editar`. El rol legado
  `Tecnico de Laboratorio` permanece intacto.
- Rechaza explícitamente `Get Global Properties`. El flujo requiere una release
  backend compatible con Attachments `>=4.0.1-sihsalus.1 <5.0.0`, autorización
  server-side y acceso interno acotado a la configuración del módulo.
- Documenta que `Edit Observations` y `Delete Observations` ya formaban parte de
  `Laboratorio`. Esta versión no altera esas asignaciones ni promete impedir el
  borrado.
- Conserva sin cambios `Add Observations` y `Delete Observations` del rol editor
  genérico; los marcadores nuevos no prometen impedir borrado.
- Fija en CI el contrato declarativo de Laboratorio y establece que la futura
  carga PDF no deberá completar ni cambiar el estado de la orden.

## [1.25.13] - 2026-08-26

### Corregido

- Completa el rol `Farmacia` con `Edit Medication Dispense`, requerido por
  OpenMRS FHIR2 para crear y actualizar dispensaciones. Conserva
  `Get Medication Dispense` para su lectura y protege ambos privilegios mediante
  el validador del contrato de Stock Management.

## [1.25.12] - 2026-08-25

### Agregado

- Publica en un artefacto inmutable nuevo el tipo de identificador técnico y la fuente
  secuencial `RU-` usados por la Receta Única Estandarizada. La versión `1.25.11`
  ya había sido publicada antes de que esos metadatos ingresaran a `main` y no los contiene.

## [1.25.11] - 2026-08-25

### Corregido

- Retira y despublica de forma idempotente el `Form` persistido de
  `CE-001-CONSULTA EXTERNA` `1.0.1`, sin eliminar ni modificar sus encuentros históricos.
- Falla de forma cerrada si los UUID de `1.0.1` o `1.0.2` no corresponden a sus identidades
  esperadas, o si otra versión de `CE-001` permanece publicada junto a la canónica `1.0.2`.

## [1.25.10] - 2026-08-25

### Corregido

- Alinea la ubicación canónica del Hospital Santa Clotilde con la jerarquía territorial
  configurada: Loreto como región, Maynas como provincia, Napo como distrito y Santa Clotilde
  como centro poblado. Mantiene vacía la calle porque la fuente estatal no publica una
  dirección vial utilizable.

### Agregado

- Provisiona el teléfono institucional `965 336 199` y el Código Único IPRESS `00000066`
  como atributos estables de `Location`, con validación de su identidad y cardinalidad.
- Activa `drugOrder.requireOutpatientQuantity=true` para exigir los datos de dispensación en
  las prescripciones ambulatorias.

## [1.25.9] - 2026-08-25

### Cambiado

- Migra las respuestas `Terrestre`, `Aéreo` y `Fluvial` de la referencia institucional al source
  OCL aislado `SIHSALUS/referencia-institucional`, preservando sus UUID OpenMRS.
- Bundlea la release `2026-08-25-01` como export estático de conceptos y mantiene el source principal
  `sihsalus` en `2026-07-16-02`.

### Retirado

- Elimina `concepts/referral_transport_concepts.csv` para impedir que Initializer y OCL importen los
  mismos conceptos en paralelo.

## [1.25.8] - 2026-08-25

### Cambiado

- Publica `CE-REF-001-REFERENCIA-CONTRARREFERENCIA` `1.1.0` como compatibilidad de captura
  mínima de la Hoja de Referencia Institucional: destino, especialidad, prioridad, condición de
  salida y motivo. Retira el diagnóstico de texto duplicado porque la hoja reutiliza los
  diagnósticos nativos de la visita.

### Agregado

- Provisiona las respuestas operativas terrestre, aérea y fluvial para el concepto existente
  `Modo de transporte`. No agrega tablas ni changeSets Liquibase.

## [1.25.7] - 2026-08-25

### Corregido

- Completa el rol `Farmacia` con los privilegios mínimos de lectura de fuentes de conceptos y
  dispensaciones requeridos por la consulta FHIR de recetas, sin ampliar sus capacidades de
  escritura ni administración.
- Protege ambos privilegios mediante el validador del contrato de Stock Management.

## [1.25.6] - 2026-08-24

### Agregado

- Publica `CE-SOAP-001-NOTA SOAP` como versión `1.1.0` con examen físico segmentado en examen
  general y regional por sistemas, conforme al contenido mínimo de Consulta Externa de la NTS 139.
- Registra estado general y resumen regional como campos obligatorios, sin completar hallazgos
  normales automáticamente, y conserva la versión histórica `1.0.0`.

## [1.25.5] - 2026-08-24

### Corregido

- Retira de `CE-001-CONSULTA EXTERNA` la página de diagnóstico y las observaciones de texto,
  certeza y ocurrencia que no creaban un diagnóstico nativo del encuentro. El diagnóstico CIE-10
  se registra exclusivamente mediante Visit Notes.
- Publica el esquema corregido como versión `1.0.2`, con identidad persistida distinta de `1.0.1`,
  para preservar la definición y los encuentros históricos sin sobrescribir su recurso.

## [1.25.4] - 2026-08-24

### Agregado

- Provisiona los seis catálogos mínimos de Stock Management, reutilizando las
  unidades clínicas existentes y agregando motivos, fuentes y categorías
  administrativas controladas. Mantiene saldos negativos deshabilitados y no
  crea artículos, lotes ni existencias ficticias.
- Incorpora los roles canónicos del módulo de inventario y concede a Consulta
  Externa y Farmacia únicamente la lectura de disponibilidad en la ubicación de
  dispensación; las operaciones y la administración permanecen separadas.

## [1.25.3] - 2026-08-24

### Corregido

- Retira del rol granular de edición de Visit Notes el privilegio inexistente
  `Add Diagnoses` y la capacidad de purga `Delete Diagnoses`. OpenMRS 2.8.9 usa
  `Edit Diagnoses` tanto para guardar como para anular diagnósticos.
- Protege el contrato RBAC para impedir que esos privilegios se vuelvan a
  asignar al rol de edición. No modifica los changeSets Liquibase publicados en
  `1.25.1`, preservando sus checksums para instalaciones existentes.

## [1.25.1] - 2026-08-23

### Corregido

- Provisiona de forma idempotente la metadata canónica de `Visit Note` y valida el
  contrato de formulario, tipo de encuentro y datatypes clínicos consumidos por el
  frontend coordinado.
- Restaura `app:hoja.clinica.resumenConsulta.editar` con su UUID histórico,
  separado de lectura, y completa el rol funcional granular con las capacidades
  backend necesarias para registrar observaciones y diagnósticos nativos.

## [1.25.0] - 2026-08-22

### Cambiado

- Prepara la versión `1.25.0` como paquete exclusivamente backend: el ensamblado incluye solo
  `backend_configuration`, conserva los exports OCL y deja la configuración efectiva del SPA en
  `sihsalus-frontend/config/frontend.json`.

### Retirado

- Elimina `configuration/frontend_configuration/config.json` y las validaciones acopladas a ese
  archivo, porque la distribución SIHSALUS no lo sirve al navegador. Las validaciones de metadata
  backend, catálogos OCL y rutas de atención se conservan.

### Agregado

- Catálogo local de barrios de Santa Clotilde como atributo codificado de
  persona. Su activación en registro, búsqueda y datos adicionales corresponde
  a la configuración efectiva del frontend. El catálogo activo se aísla en la fuente OCL
  `SIHSALUS/barrios-santa-clotilde/2026-08-22-01`; el source clínico principal
  permanece en `SIHSALUS/sihsalus/2026-07-16-02`. Se retira `ADDRESS_3/Barrio`
  después de confirmar que no contiene datos reales que requieran migración.
- Habilita `ODONTOLOGIA GENERAL` (`5fe6c774-f888-40e5-b54f-e308e5fa26c8`) como
  destino del set `Tipo de Servicio` (`4bf3f465-…`), que alimenta el catálogo de
  interconsultas y colas. Reutiliza el concepto ya publicado en OCL en lugar de
  crear uno nuevo, según el [plan terminológico histórico](https://github.com/sihsalus/sihsalus-content/blob/c4abc8ff71c06f43e43f63132a9d3ee265388516/OCL-TERMINOLOGY-PLAN.md). Sin este miembro no existía
  ningún destino odontológico pese a que el sistema tiene módulo de atención
  odontológica con hoja clínica y privilegios propios.
- Rol `SIHSALUS Enfermero Triaje` (uuid canónico `c3c9b940-156f-4eaf-83b7-f11db420c51c`),
  hasta ahora creado a mano en cada base de datos con uuids divergentes y sin
  `Edit Visits` — sin ese privilegio, guardar signos vitales dentro de una
  visita activa falla, porque adjuntar un encuentro a la visita exige editarla.
  La lista de 45 privilegios se tomó del rol vigente en QLTY más la corrección.
  Incluye además la capacidad de leer la cita vinculada, necesaria para mostrar
  «Realizar triaje» y derivar al paciente a su cola clínica después de guardar
  los signos vitales.
  Una migración previa normaliza al UUID canónico las copias manuales del rol,
  sin reemplazar el nombre usado por las asignaciones de usuarios.
  `validate_appointment_queue_integrity.py` incorpora el rol al allowlist de
  asignaciones directas de `Manage Queue Entries` (triaje mueve pacientes en la
  cola) y fija sus invariantes: exige `Edit Visits` y los privilegios de signos
  vitales, y le prohíbe administrar o purgar colas.
- Pregunta `Código prestacional de la consulta SIH.SALUS`
  (`34630b86-5106-4aea-8382-f55c02e4ba2c`, clase Question, datatype Coded), que
  el resumen de consulta usa para persistir el código prestacional como
  respuesta codificada. Justificación de no reutilización: el único concepto
  existente era el ConvSet `Codigos Prestacionales` (`e82d45de…`, datatype N/A),
  que no admite valor — guardar contra él aborta el encounter completo con
  «Don't know how to handle ZZ» — y no existe ninguna otra pregunta Coded o Text
  para este dato en los 15 exports OCL.

### Corregido

- Autoriza `Edit People` en `SIHSALUS Consulta Externa` para que el profesional
  pueda registrar o corregir el estado de fallecimiento desde la historia
  clínica, y agrega el privilegio UI dedicado
  `app:hoja.clinica.estadoVitalPaciente` para no reutilizar el permiso amplio de
  edición de visitas. No concede `Add People`: el flujo actualiza una persona
  existente y el backend de OpenMRS exige una de esas dos capacidades, no ambas.
- Alinea la validación de integridad con los roles funcionales: deja de exigir
  el privilegio retirado `app:hoja.clinica.resumenConsulta.editar` y autoriza al
  rol `SIH SALUS Colas de atención editar` a registrar acompañantes y limpiar
  entradas activas de una cola según la matriz vigente.

## [1.24.2] - 2026-08-10

### Corregido

- Ajusta el límite absoluto superior de cuatro rangos de referencia de
  laboratorio, que estaba por encima del valor crítico y por tanto no marcaba
  como fuera de rango resultados que sí lo están:
  - `Proteinas Totales sericas g/dl` (recién nacido `811c9d4f…` y adulto/niño
    de 3 años `6012769e…`): máximo absoluto 15 → 12 g/dl.
  - `Creatinina en Suero` (hombre `26801d9a…` y mujer `74380209…`): máximo
    absoluto 15.0 → 13.0 mg/dl.

## [1.24.1] - 2026-08-05

### Corregido

- Corrige el formulario `Prescripción de medicamentos`, que quedó publicado como
  prueba: la observación «Observaciones» guardaba en el concepto «Evolución
  obstétrica» (`dfdc2f61…`) y ahora usa «Instrucciones de prescripción, no
  codificadas» (`480ab6d3…`); el lanzador de suplementos declaraba
  `workspaceContext`, que el motor ignora, y pasa a `workspaceProps`, de modo que
  el set «Suplementos para gestantes» (`1ecc7738…`) por fin se aplica. Conserva
  su tipo de encuentro Control Prenatal.
- Autoriza la lectura de adjuntos en `Application: Uses Patient Summary` y la
  creación y lectura en `SIHSALUS Consulta Externa`. Esto permite que Consulta
  Externa y Enfermería, por herencia, recuperen los archivos que registran con
  el módulo backend de adjuntos sin ampliar el acceso de otros roles clínicos.
- Provisiona y asigna de forma explícita los privilegios de fecha de citas:
  `app:appointments.startDate.edit` para Admisión, Consulta Externa y el rol de
  registro de citas; y `app:appointments.issueDate.edit` únicamente para
  Admisión, que registra citas emitidas previamente en papel.
- Separa la lectura de formularios y tareas clínicas de sus mutaciones mediante
  `app:hoja.clinica.formulariosClinicos.editar` y
  `app:hoja.clinica.listaTareas.editar`. Solo Consulta Externa y Enfermería por
  herencia reciben estas capacidades genéricas; Admisión, Emergencia,
  Laboratorio y Farmacia permanecen excluidos.
- Provisiona el tag backend `Care UPSS` y lo asigna exclusivamente a las once
  UPSS habilitadas para iniciar una atención. Las salas conservan
  `Visit Location`, `Admission Location` y `Transfer Location` para los flujos
  de hospitalización, pero dejan de ser candidatas del selector funcional de
  UPSS. CI mantiene sincronizado este tag con el contrato de tipos de atención.
- Separa las capacidades sensibles del frontend: `Admision` y `Personal de
  Emergencia` reciben `app:opciones.registrarAcompanante` para registrar una
  persona acompañante sólo junto con `Add People`; la limpieza masiva de
  entradas queda reservada a `Application: Gestionar Colas Servicio` mediante
  `app:home.colasAtencion.limpiar`. Esta última finaliza entradas activas y no
  concede `Purge Queue Entries` ni elimina historia.
- Agrega el privilegio API `Get Encounters` al rol `Admision` y lo protege en
  CI. Queue 3.0.0 lo exige indirectamente al guardar el número de turno como
  atributo de la consulta, porque OpenMRS Core ejecuta `VisitValidator`. No se
  agregan `View Encounters`, observaciones ni programas clínicos.
- Agrega `Get Concept Attribute Types` al rol `Admision` y lo protege en CI.
  OpenMRS Core lo exige al validar los atributos incluidos en el POST inicial
  de una visita; sin este privilegio, el registro atómico de llegada respondía
  `400` antes de crear la consulta.
- Restaura `Get Beds` y `Get Admission Locations` en el rol `Admision` y protege
  ambos privilegios en CI. `bedmanagement` los exige al validar cualquier visita,
  incluso una consulta ambulatoria sin cama; su ausencia bloqueaba el registro de
  llegada antes de crear la visita y la entrada de cola.
- Ordena las precondiciones antes del comentario en la migración del rol de Admisión,
  conforme al esquema Liquibase 1.9, y agrega una validación de este contrato al CI.
- El visit attribute **`Financiador`** (`3a988e33-…`) apuntaba al concepto inexistente
  `355ee63a-…`; ahora referencia el set canónico `Tipo de seguro` (`6b932638-…`), con lo
  que el atributo de visita vuelve a ser utilizable por admisión, facturación y FUA.
- Habilita al rol `Admision` el tablero y la operación de entradas de cola mediante
  `app:home.colasAtencion` y `app:home.colasAtencion.editar`. Mantiene fuera la configuración,
  habitaciones y purga de colas (`Manage Queues`, `Manage Queue Rooms`, `Purge Queue Entries`).
- Mapea las citas de cirujano dentista general en UPSS Consulta Externa a la cola compartida y usa el ámbito
  `Atención Ambulatoria`; la categoría `Odontología general` conserva el contexto sin duplicarlo en `VisitType`.
- Mantiene el nombre estable `Admision` para que Initializer pueda actualizar el rol existente por UUID, reemplazar
  su herencia y aplicar la allowlist de registro, citas y check-in. Esto restaura la lectura necesaria para encolar
  desde Citas y retira historia clínica, configuración/purgas de colas, administración de catálogos y
  acciones destructivas. CI exige la identidad y privilegios exactos del rol.
- Separa la visualización del resumen de consulta de su edición mediante
  `app:hoja.clinica.resumenConsulta.editar`, evitando que un permiso de lectura habilite el formulario clínico.
- Cura el set OCL `Signos Vitales` para que sus 13 miembros activos coincidan con el contrato longitudinal:
  reutiliza los conceptos numéricos existentes de perímetro abdominal y torácico, y retira del set Karnofsky
  y las cuatro observaciones Glasgow sin eliminar su historia ni crear conceptos duplicados.
- Documenta y valida el contrato de ubicación de los identificadores con
  `Location behavior = NOT_USED`: el consumidor debe omitir `identifiers[].location` en vez de
  enviar `null` o inventar una ubicación de sesión. La implementación del payload corresponde al
  frontend y queda como requisito de integración para evitar la excepción REST al guardar.
- Separa límites técnicos de captura y rangos clínicos: alinea los límites absolutos de signos
  vitales con cada `ConceptNumeric`, admite límites absolutos ausentes y deja vacío el crítico alto
  de saturación de oxígeno para que la metadata no clasifique `100%` como críticamente alto.
- Codifica sin sobreclasificar las fronteras estrictas de Prioridad I de la NT N.° 042 en campos
  críticos inclusivos para valores enteros (`<50` como `low=49`, `>150` como `high=151`, y sus
  equivalentes de presión y frecuencia respiratoria); documenta los contextos que el rango no cubre.
- Activa las 26 reglas obstétricas mediante la inscripción fechada `Madre Gestante` y el concepto de
  edad gestacional que sí escriben los formularios. Elimina el uso Boolean inválido de una respuesta
  `N/A`, resuelve una sola observación por criterio y fija PAS gestante `<90` como crítico (`89` para
  captura entera), dejando `90` como normal. Otorga a `Personal de Emergencia` únicamente
  `Get Patient Programs`, requerido por Core para evaluar la inscripción sin ampliar su gestión.
- Corrige la referencia normativa del tipo de encuentro y del tipo de visita de emergencia a la
  NT N.° 042-MINSA/DGSP-V.01; conserva intacto el tipo histórico mixto `Triaje` para no reetiquetar
  encuentros existentes.
- Endurece la clasificación de logs de validación para tratar logs con bytes NUL como texto y
  bloquear también errores de `BaseFileLoader`, incluidos JSON o archivos binarios duplicados y
  corruptos que no aparecían en el resumen CSV de Initializer; agrega fixtures de regresión en CI.
- Corrige el RBAC de cita-visita-cola para OpenMRS Core y los OMOD oficiales: retira el privilegio local sin
  consumidor `Manage Appointment Queue Lifecycle` y asigna `Manage Queue Entries` solo a admisión, registro de
  citas, gestión de colas, emergencia, consulta externa y administración técnica. Conserva fuera de esos roles la
  configuración de colas, el reinicio de estados y la purga de datos.
- Añade `Generate Fua from Visit` para que médicos y enfermería generen o reintenten la FUA de una consulta
  finalizada sin recibir `Manage Fua`; alinea además la navegación y lectura de visitas del digitador FUA, y el rol
  técnico de backend conserva la misma capacidad de recuperación.
- Define `Personal de Emergencia` como rol operativo directo para búsqueda y alta rápida, visitas, triaje,
  atención y movimientos de cola. Puede cerrar de forma coordinada registros legados vinculados a citas, sin
  heredar los permisos amplios de consulta externa ni recibir configuración, purga o borrado clínico.
- Conserva una duración base positiva en cada definición de servicio sin inventar horarios ni cupos, retira los
  tipos de servicio redundantes y publica reglas explícitas para todos los servicios programables.
- Protege `Get Providers` como privilegio requerido del rol `Admision` para que pueda listar doctores y
  proveedores mediante la API REST.
- Agrega `Get Concept Sources` al rol `Admision` para que FHIR pueda cargar los datos existentes al editar un
  paciente, evitando que la pantalla quede vacía por el error `HAPI-0389`.
- Agrega `Get Concepts` al rol `Admision` para cargar los conjuntos codificados de ocupación, idioma, religión,
  grado de instrucción y etnia durante el registro de pacientes, y valida que conserve `Add Patients`,
  `Edit Patients`, `Get Patient Identifiers` y `Edit Patient Identifiers`; ninguno de estos permisos otorga acceso
  de gestión de conceptos.

### Agregado

- Validador de integridad terminológica entre formularios y exports OCL
  (`validate_form_concept_integrity.py`). Bloquea de inmediato los conceptos
  referenciados que no existen y los renderings codificados sobre conceptos
  `Text` —que persistirían el UUID de la respuesta como cadena—. La deuda ya
  existente (23 colisiones de concepto dentro de un mismo formulario, 32
  answer sets divergentes, 66 labels con UUID distintos y 9 campos cuyo label
  promete un código pero guardan texto) queda inventariada en un baseline que
  solo puede encoger.
- Atributo de visita `Acompañante de consulta`
  (`710da0b9-e15f-47f0-827a-e97f1937c81d`), que el formulario de inicio de
  consulta del frontend usa para persistir el UUID de la persona acompañante.
  Sin este metadato el frontend degrada con "No se pudo guardar el
  acompañante" y la consulta se guarda sin acompañante.
- Contrato canónico versionado `docs/contracts/hsc-care-routing.csv` para los 16 servicios
  registrados. Define por UUID la categoría de agenda, ubicación, política de llegada, cola y
  ámbito de atención; 13 servicios quedan programables, 11 permiten cola y dos son de atención
  directa.
- Categoría local de agenda `Odontología general`, separada de la especialidad reconocida
  `Cirugía Bucal y Maxilofacial`, y atributo multivaluado de proveedor para habilitar categorías
  de agenda con validación frontend configurable (`off`, `warn` o `strict`).
- Conceptos dedicados para servicios de cola. `Queue.service` deja de reutilizar UUIDs de
  `AppointmentServiceDefinition`, que pertenecen a otro tipo de recurso.
- Person attribute **Método de Verificación de Seguro** (`bc1e5c92-e46a-4bc9-8cba-d9093a0eb659`, FreeText):
  traza cómo se verificó la afiliación (manual-web / setisis / siteds), requerido por la
  verificación SIS manual interina del frontend (sihsalus-frontend PR #623, plan PR #606).
- Catálogo canónico de financiadores (tipología IAFAS/RIAFAS): el set `Tipo de seguro`
  (`6b932638-…`) incorpora **EPS** (`9348006a-…`), **SOAT/AFOCAT** (`08a4d37a-…`),
  **Prepaga de salud** (`3fa0e9a8-…`), **Autoseguro de salud** (`1cf576eb-…`) y
  **Sanidad de las Fuerzas Armadas** (`e94d4d1a-…`). FOSPOLI se mantiene como IAFAS policial.
- Nueva pregunta **`Producto SIS`** (`72b9edbf-1ec8-4b1a-8957-b1597aab8757`) con respuestas
  SIS Gratuito, SIS Semicontributivo (legado), SIS Emprendedor, **SIS Para Todos**
  (`b23298e2-…`), **SIS Independiente** (`efd89ed6-…`) y **SIS Microempresas** (`dc8cbea7-…`),
  con la codificación FUA (2/3/E/9/R/8) documentada en las descripciones.
- Exports OCL de `SIHSALUS/seguros` actualizados a la versión liberada `2026-07-17-01`
  (25 conceptos, 33 mapeos).
- Aprovisiona las dos colas del flujo de emergencia del frontend en `sihsalus-queues.csv`: **Cola de Triaje de
  Emergencia** (`b1c5bb01-…`, prioridades = nuevo set *Clasificación Pre-Triaje*: Emergencia/Urgencia) y **Cola de
  Atención de Emergencia** (`ebd44a3d-…`, prioridades = *Sistema de Triaje de Cinco Niveles* con Prioridades I-IV),
  ambas en UPSS - EMERGENCIA con el set estándar de estados de cola. Sin esto, el flujo de emergencia del frontend
  solo funcionaba en servidores con colas creadas a mano.
- Nuevo concepto set `Clasificación Pre-Triaje` (`3f4db8e2-241c-45ef-8e52-cea8dc4118f0`, OCL id 4472) con miembros
  Emergencia (`e724bdb6-…`) y Urgencia (`89f8fab4-…`), según NT N.° 042-MINSA/DGSP-V.01.
- Actualiza los exports OCL de `SIHSALUS/sihsalus` a la versión liberada `2026-07-16-02` (4 472 conceptos,
  5 679 mapeos) y la suscripción de `openconceptlab.subscriptionUrl` a esa versión.
- Separa el registro longitudinal de signos vitales y antropometría del triaje de emergencia mediante
  tipos de encuentro y roles de proveedor distintos, sin formularios JSON ni migración automática de
  históricos. Agrega un contrato de ubicación/RBAC para el frontend y una validación CI de regresión.
- Agrega los atributos de visita `Número de turno de cola` y `UUID de cita vinculada`, la propiedad global del
  número de turno y una validación CI de RBAC con privilegios oficiales, metadata, duración y rutas exactas por
  UUID; declara `America/Lima` como zona operativa para los consumidores SIHSALUS y conserva UTC en servidor/JVM
  según la convención de OpenMRS.
- Agrega privilegios frontend específicos para la tabla de consultas activas, resumen de consulta, formularios
  clínicos, canasta de órdenes y lista de tareas. Los asigna a consulta externa y, de forma acotada, a los roles
  clínicos que ya tenían el acceso funcional equivalente; `Enfermera` los hereda de `Doctor Consulta Externa`.
- Agrega el privilegio estrecho `Generate Fua from Visit` y valida que solo se asigne directamente al rol clínico,
  digitadores FUA y rol técnico de backend.
- Agrega validaciones clínicas de regresión para CRED-001, 009, 010, 011, 015, 026 y 027: exige edad/altitud en
  anemia, trazabilidad de instrumentos resumidos, antropometría escolar y decisiones de desarrollo por edad.
- Extiende la validación CI de OCL para rechazar mappings sin extremos, fuentes destino incompletas, referencias
  internas no bundleadas y colisiones de nombres que puedan dejar un concepto sin nombre `FULLY_SPECIFIED`.
- Publica los concepts de formulario que faltaban para inmunizaciones, referencias, acompañamiento, PPL/PRU, personal de parto, estado de ecografía y plan de parto; agrega las opciones de seguro SIS y particular sin reutilizar conceptos de otras preguntas.
- Extiende la validación CI de formularios para resolver conceptos contra todos los ZIP OCL, comprobar `Q-AND-A` entre sources, detectar respuestas repetidas o autorreferenciales, datatypes incompatibles, renderers no soportados, expresiones con IDs inexistentes y discordancias de encounter type.
- Agrega `CIEL 170800 - Procedure status` con UUIDs OpenMRS canónicos, ocho respuestas `Q-AND-A` ordenadas, localización clínica en español y mapping a SNOMED CT `416342005`; excluye explícitamente el set de estados de dispensación de medicamentos.
- Agrega `CRED-028-TPED`, con 12 líneas y 89 hitos estructurados, y validación CI de la cardinalidad de los mappings y formularios de desarrollo.
- Conserva los tags de ubicación `Queue Location` y `Appointment Location` en Initializer, y define tipos de servicio de cita para que agenda no quede sin duración.
- Agrega especialidades y servicios de cita para Medicina de Rehabilitacion, Hemodialisis y Nutricion y Dietetica, alineados con las colas y servicios facturables ya existentes.
- Documenta en formato de release la actualización de la anamnesis (`CE-ANAM-001-ANAMNESIS`, versión `1.0.3`) y la actualización de la configuración de colas, citas y UPSS de soporte según revisión funcional.
- Agrega tipos de procedimiento EMR API mediante el dominio Initializer `proceduretypes`, junto con los privilegios requeridos para leer y gestionar procedimientos en el módulo O3.
- Agrega privilegios de frontend para admision (`app:adt`), citas, colas, modulos operativos del home, vacunacion independiente (`app:immunization`, `app:immunization.edit`) y FUA (`Fua Privilege`, `Read Fua`, `Manage Fua`, `Update Fua`), junto con roles de navegacion operativa y roles de vacunacion de lectura y edicion.

### Cambiado

- El rol de Admisión normaliza de forma transaccional su nombre histórico `SIHSALUS Admision`
  a `Admision`, conservando el UUID y todas las referencias de usuarios, privilegios y módulos.
  Esto permite que Initializer sincronice sus permisos de colas tanto en bases existentes como
  en instalaciones limpias.
- `VisitType` representa únicamente el ámbito: Atención Ambulatoria, Sesión Grupal Ambulatoria,
  Hospitalización, Emergencia o Atención Extramural. La especialidad y la prestación permanecen
  en el servicio de cita y el encuentro clínico.
- Obstetricia y nutrición ambulatorias se ubican en UPSS Consulta Externa; hospitalización de
  cirugía general se ubica en UPSS Hospitalización; Hemodiálisis usa UPSS Diálisis.
- Rehabilitación, hemodiálisis y nutrición tienen equivalencias explícitas con sus colas. El
  registro de llegada ya no depende de coincidencias por nombre ni de selección manual.
- Los tipos de servicio uno-a-uno se eliminan del paquete; la duración operativa vive en la definición
  del servicio hasta que el hospital configure variantes reales, como primera consulta o control.
- Los productos SIS (Gratuito/Semicontributivo/Emprendedor) **dejan el primer nivel** de
  `Tipo de seguro` (mapeos retirados) y pasan a ser respuestas de `Producto SIS`: el
  financiador es SIS y el producto se registra por separado.
- Presenta el identificador interoperable `DIE` como cédula de identidad emitida por el país de origen en la
  experiencia de registro, sin cambiar su UUID ni el concepto OCL. Conserva el código canónico de
  **Documento de Identidad Extranjero** definido por SUSALUD/RENHICE y deja explícito que su formato depende
  del país emisor.
- Consolida `Hospital Santa Clotilde` como única ubicación de inicio de sesión y conserva las UPSS y salas
  como ubicaciones asistenciales de citas, colas, visitas, admisión o transferencia según su función, sin
  modificar la configuración de Casita Azul. Fija además `UPSS - FARMACIA` como ubicación operativa de
  dispensación y configura `UPSS - CONSULTA EXTERNA` como ubicación prevista para citas CRED, separadas de la
  instalación usada para iniciar sesión. La generación de citas CRED sigue condicionada a configurar un
  `credScheduling.appointmentServiceUuid` canónico.
- Alinea los formularios CRED resumidos con NTS 238 y NTS 213/RM 429-2024: elimina umbrales fijos de anemia,
  identifica el instrumento de salud mental, retira clasificaciones nutricionales semánticamente ambiguas,
  corrige la pauta Huanca y hace auditables los resúmenes EDI y M-CHAT-R/F.
- Publica y bundlea `procedimientos`, `laboratorio`, `lenguas` y `geografia` `2026-07-10-02`, y `sihsalus`
  `2026-07-10-03`; restaura todos los extremos y fuentes destino requeridos por el importador OCL de OpenMRS y
  actualiza la suscripción principal a la nueva release.
- Publica y bundlea `sihsalus`, `seguros` y `laboratorio` `2026-07-10-01`; alinea 111 formularios con 3 641 referencias conceptuales, unifica el par activo Sí/No usado por O3 y limpia value sets mezclados sin eliminar observaciones históricas.
- Corrige la lógica de CRED: M-CHAT-R/F, Huanca y Lista de Habilidades calculan resultados de solo lectura; `CRED-004` admite hasta 143 meses y puntajes EEDP acumulados; el formulario EEDP rotulado como 21 meses se documenta correctamente como acumulado hasta 24 meses.
- Corrige campos semánticamente cruzados en Consulta Externa, inmunizaciones, obstetricia y hospitalización; reemplaza conceptos `N/A` usados para guardar fechas o números y separa estados, personas y hallazgos en preguntas propias.
- Migra los campos calculados de `editable: false` a `readonly: true`, soportado por el form engine O3, y corrige renderers, etiquetas, encounter types, BMI y condiciones de visibilidad detectadas en la auditoría final.
- Evita la colisión de Initializer con `Queue Location` y `Appointment Location`: las filas sin UUID se resuelven por nombre contra los tags creados por sus módulos, sin recrearlos ni migrar la base de datos.
- Publica y bundlea `SIHSALUS/sihsalus` `2026-07-09-02` con 4 459 conceptos y 5 635 mappings: conecta las 12 líneas y 89 hitos TPED, convierte TPED, Huanca, Lista, EDI y M-CHAT-R/F en sets navegables, conserva EEDP, TEPSI y TPED habilitados, e incorpora la terminología requerida por procedimientos O3.
- Completa `CIEL 1732 - Duration units` como `CONCEPT-SET` de ocho miembros, corrige los UUIDs OpenMRS de sus unidades, fija el orden oficial y localiza el conjunto como `Unidades de duración`.
- Alinea `CRED-004`, `CRED-009`, `CRED-010`, `CRED-026` y `CRED-027` con los nombres y resultados normativos: EDI Verde/Amarillo/Rojo, M-CHAT-R/F de 0 a 20 puntos y Huanca con pauta de 30 a 36 meses.
- Publica y bundlea `SIHSALUS/ocupaciones` `2026-07-09-01` con los 436 grupos unitarios CIUO-08, nombres oficiales preferidos en español, nombres ISCO-08 en inglés y 436 mappings `CONCEPT-SET` hacia el agrupador de ocupaciones.
- Refresca los exports OCL bundleados desde las versiones publicadas vigentes en `SIHSALUS`, actualiza `openconceptlab.subscriptionUrl` a `SIHSALUS/sihsalus/2026-07-09-02` y documenta la auditoría de cobertura de formularios contra conceptos.
- Alinea ubicaciones UPSS con colas, citas y ADT: Central de Esterilizacion queda como soporte interno, Admission/Transfer se conserva para salas de hospitalizacion, y las UPSS de soporte programables quedan como ubicaciones de cita sin ADT.
- Retira Emergencia del dominio de citas programadas; se conserva como cola operativa y servicio facturable.
- Actualiza los exports OCL del bundle a sus versiones publicadas más recientes en la org SIHSALUS: `laboratorio` a `24-06-2026-2` (completo y `concepts-only`) y `prestacionales` a `2026-06-18-01`; el resto de sources se mantiene en su versión publicada vigente.
- Agrega al bundle OCL el source `prestacionales` (`v2026-06-17-openmrs-current`) con 65 códigos prestacionales y un agrupador `CONCEPT-SET`, reclasificando los códigos como `Misc/N/A` y el set como `ConvSet/N/A`.
- Reemplaza los conceptCodes CIEL de dispositions por conceptos locales ya cargados en SIHSALUS, evitando dependencia runtime de CIEL para admisión, alta, transferencia, fallecido y observación.
- Restringe `Application: Registers Patients` a privilegios explícitos de registro de pacientes para evitar que `Admision` reciba permisos clínicos por herencia de `Privilege Level: High`.
- Asigna al rol `Admision` solo los accesos de admision, citas y colas necesarios para registro, agenda y derivacion operativa.
- Agrega `Get Beds` y `Get Admission Locations` al rol `Admision` porque el validador de `bedmanagement` los requiere al crear visitas, incluso cuando la consulta no asigna cama.
- Define los roles operativos `Laboratorista` y `Farmacia` con los privilegios de frontend y backend requeridos para ver y operar laboratorio y dispensacion sin heredar accesos de admision.
- Agrega el atributo de visita `Procedencia` para registrar desde dónde procede el paciente en una atención.
- Actualiza los exports OCL del content package a la org `SIHSALUS`; los sources de dominio quedan en `v2026-06-16-openmrs-current`.
- Actualiza el export principal `sihsalus` a `v2026-06-16-education-mappings-fix`, moviendo las respuestas de nivel educativo desde `No (respuesta)` hacia `Highest education level` y enlazando `Nivel I-2` a `Nivel de Atención`.
- Actualiza el export principal `sihsalus` a `v2026-06-16-glasgow-vitals`, agregando los conceptos de Escala de Glasgow usados por el ESM de signos vitales (`glasgowEyeOpeningUuid`, `glasgowVerbalResponseUuid`, `glasgowMotorResponseUuid`, `glasgowTotalUuid`) y sus respuestas.
- Actualiza el export principal `sihsalus` a `v2026-06-16-pns-contact-metadata`, agregando conceptos y mappings para metadata de contactos PNS usada por flujos de ficha familiar, relaciones y notificación de contactos.
- Actualiza el export principal `sihsalus` a `v2026-06-16-languages`, agregando sets de lenguas del mundo y lenguas indígenas u originarias del Perú (BDPI), separados de conceptos de etnia, más `Otra lengua no codificada`.
- Actualiza el export principal `sihsalus` a `v2026-06-16-qanda-cleanup`, completando mappings `Q-AND-A` determinísticos para preguntas CRED, atributos de persona, educación, grupo sanguíneo, acreditación y formularios sin reabrir la duplicidad controlada de `Sí`/`No`.
- Actualiza el export principal `sihsalus` a `v2026-06-17-openmrs-order-fix`, retirando un mapping activo desde un concepto retirado y reordenando los ZIPs OCL para que los conceptos destino existan antes de importar mappings cross-source.
- Actualiza el export `laboratorio` a `16-06-2026-2`.
- Corrige la validacion SIHSALUS con Initializer 2.12: evaluator SQL de Patient Flags, estado `Fallecido` en workflows de programa y referencia activa del medicamento MINSA `47343`.
- Apunta `openconceptlab.subscriptionUrl` al source principal versionado `SIHSALUS/sihsalus/v2026-06-17-openmrs-order-fix`.
- Consolida la curación OCL: conceptos administrativos movidos fuera de `laboratorio`, normalización de conceptos de laboratorio, insumos de `medicamentos` clasificados como `Medical supply`, y códigos CIE-10 `U*` clasificados como `Misc`.
- Re-exporta OCL tras los fixes de import OpenMRS: `inmunizaciones#584` queda como `Vacuna antiamarílica` y las respuestas clínicas de aborto se rewirean a `diagnosis`.
- Migra la configuracion de Patient Flags desde Liquibase a dominios Initializer (`flagpriorities`, `flagtags`, `flags`) y corrige el evaluator SQL al nombre soportado por `patientflags`.
- Alinea rangos críticos de signos vitales de triaje con la NT 042-MINSA/DGSP-V.01 y amplía límites absolutos para no bloquear valores de Prioridad I.
- Documenta la auditoría de inmunizaciones contra la NTS 246-MINSA/DGIESP-2026 y marca las brechas de hexavalente, VRS, meningococo, VPH y SR antes de modificar calendario o formularios.
- Fortalece CI con validacion de anchos CSV, UUIDs unicos en formularios AMPATH y verificacion real de rangos de referencia contra los exports OCL bundleados.
- Excluye artefactos no ejecutables del ZIP final (`.DS_Store`, `.gitkeep`, `ampathforms/Readme` y formularios `_deprecated`).
- Normaliza IDs de preguntas AMPATH a ASCII camelCase, corrige botones `workspace-launcher` para que no se guarden como `obs` sin concepto, y agrega validacion CI para estructura basica de formularios.
- Retira/reclasifica procedimientos duplicados y mappings huerfanos de `SIHSALUS/sihsalus` para que CPMS (`SIHSALUS/procedimientos`) sea la fuente canonica de procedimientos, y actualiza formularios obstetricos a UUIDs CPMS para parto instrumentado y cesarea.
- Retira/reclasifica conceptos `Drug` de `SIHSALUS/sihsalus` para que `SIHSALUS/medicamentos` sea la fuente canonica de medicamentos, manteniendo en `sihsalus` solo campos clinicos y respuestas de formulario no ordenables.
- Agrega `UBIGEO de Nacimiento` como atributo de persona buscable y retira el atributo textual legado `Lugar de Nacimiento`.
- Ordena los exports OCL con prefijos numericos para cargar primero `sihsalus` y `procedimientos`, evitando mappings hacia conceptos destino aun no importados.

### Retirado

- Servicios de cita para emergencia, atención inmediata del recién nacido y aplicación de
  inyectables. Son flujos no programables o requieren confirmar cartera y UPSS antes de activarse.
- Tipos de atención que codificaban especialidades, dispensación o diagnóstico dentro de
  `VisitType`, y el atributo ficticio `Parent Visit Type` que OpenMRS Core nunca interpretó, se
  eliminan del paquete canónico y no se recrean en instalaciones nuevas.

### Validación

- CI comprueba que la metadata backend reproduzca exactamente el contrato, que las colas usen
  Concepts dedicados, que no reaparezcan tipos especializados y que odontología general nunca
  quede asociada a Cirugía Bucal y Maxilofacial.

## [1.11.0] - 2026-06-09

### Agregado

- Privilegios granulares del modulo CRED (`app:cred.antecedentes`, `app:cred.cursoVida`, `app:cred.earlyStim`, `app:cred.immunization`, `app:cred.neonatal`, `app:cred.nutrition`, `app:cred.wellChild` y sus variantes `.edit`) en `privileges_core-demo.csv`.
- Roles `CRED lectura` y `CRED lectura y edicion` en `roles-core.csv`, agrupando los privilegios de lectura y de edicion del modulo CRED.

## [1.9.6] - 2026-06-04

### Corregido

- Migra referencias de formularios a conceptos SIHSALUS V4 cargados en QLTY, incluyendo respuestas Si/No, Otro, Normal, Ninguno, diagnostico, laboratorio y opciones no binarias que habian quedado apuntando a UUIDs CIEL antiguos.
- Agrega conceptos internos `SIH.SALUS - ...` para campos de formulario que no tienen equivalente directo en SIHSALUS V4, evitando colisiones de nombres durante Initializer.

## [1.9.4] - 2026-06-04

### Corregido

- Alinea las opciones de formularios `ODONT-003`, `PSIC-001`, `PSIC-002` y `PSIC-004` con UUIDs canonicos ya importados por la terminologia para evitar referencias a conceptos no cargados.
- Agrega la estructura de conceptos y mappings `CIEL` requeridos por FHIR2 `Immunization`, incluyendo el set `CIEL:984` con vacunas MINSA para `INMU-001`.
- Elimina filas de conceptos locales duplicados que fallaban en Initializer por nombres existentes en locale `es`.

## [1.8.32] - 2026-05-28

### Agregado

- Formulario `ODONT-003-ATENCIÓN ODONTOLÓGICA` para el registro clínico de la atención odontológica (motivo de consulta, índices CPO-D/ceo-d e IHOS, riesgo estomatológico, diagnóstico CIE-10, actividades preventivas y recuperativas, plan de tratamiento y disposición), usando el encounter type existente `Atención de Odontología`. Complementa el odontograma, que registra los hallazgos por pieza.
- Conceptos de odontología en `concepts-odontology.csv` para la atención clínica: tipo de atención, antecedentes estomatológicos, índices CPO-D/ceo-d, IHOS, riesgo estomatológico, actividades preventivas, procedimientos recuperativos, detalle de procedimientos, piezas tratadas y disposición.

## [1.8.31] - 2026-05-13

### Corregido

- Agrega membresias `conceptsets` para los conceptos de colas (`Tipo de Servicio`, `Estado de la Cola` y `Prioridad`) antes del dominio `queues`.
- Corrige el rechazo de las 16 colas por no tener sus servicios como miembros de `queue.serviceConceptSetName`.

## [1.8.30] - 2026-05-12

### Cambiado

- Actualiza el export OCL SIHSALUS-v4 a la version `12-05-2026-1`.
- Alinea el programa Tuberculosis para usar el concepto OCL `Programa de Tuberculosis` de clase `Program`.

## [1.8.29] - 2026-05-12

### Corregido

- Corrige filas mal escapadas en rangos de referencia de laboratorio que rompian el dominio `conceptreferencerange`.

## [1.8.28] - 2026-05-12

### Corregido

- Alinea el export OCL SIHSALUS-v4 con los servicios de Queue consumidos por el content package.
- Reemplaza codigos numericos OCL por UUIDs OpenMRS estables en queues y propiedades globales.
- Espera publicacion completa en Maven Central antes de considerar exitoso el deploy.

## [1.8.27] - 2026-05-12

### Corregido

- Nueva publicacion requerida porque `1.8.25` y `1.8.26` ya existen en Maven Central con configuracion de Queue no reproducible.
- Mantiene las colas y propiedades globales de Queue alineadas con UUIDs estables importados desde OCL.

## [1.8.25] - 2026-05-12

### Corregido

- Alineadas las colas de atencion con los conceptos importados desde OCL para evitar errores de Initializer en el dominio `queues`.

## [1.8.24] - 2026-05-11

### Cambiado

- Publicacion estable con carga controlada de conceptos SIH.SALUS en OCL y alineacion de configuracion frontend/CI.

## [1.8.20] - 2026-04-30

### Cambiado

- Publicacion del content package con las correcciones recientes de metadata y limpieza de configuracion frontend obsoleta.

### Agregado

- Workflow de GitHub Actions para validar el content package contra la distro SIHSALUS y exigir 0 errores de CSV/Initializer.

## [1.6.0] - 2026-02-11

### Corregido

- **UUIDs**: Regenerados 43 UUIDs inválidos (contenían caracteres no-hexadecimales) en encounter types, encounter roles, service definitions, visit types, programs, person attribute types, order frequencies y metadata term mappings
- **Formularios AMPATH**: Actualizados 33 formularios JSON con los nuevos UUIDs de encounter types
- **Cascading fixes**: Actualizadas colas de atención y metadata term mappings con los nuevos UUIDs referenciados
- **HOSP-010**: Corregido `encounterType` vacío en Epicrisis Obstétrico-Postparto (ahora apunta a Epicrisis Médica HSC)
- **Attribute Types**: Corregido UUID duplicado entre Profesión y Colegio Médico en provider attributes
- **Global Properties**: Reemplazado UUID placeholder (RFC 4122 example) en Fast Data Entry por UUID real de Consulta Ambulatoria

## [1.5.0] - 2026-02-11

### Agregado

- **Message Properties**: Traducciones i18n al español (`messages_es.properties`) con terminología MINSA
- **Cash Points**: 3 puntos de caja (Admisión, Farmacia, Emergencia) para módulo de billing
- **Billable Services**: 14 servicios facturables alineados con las UPSS del hospital (consultas, laboratorio, ecografía, cirugía, hemodiálisis, etc.)
- **Cohort Attribute Types**: 3 atributos para listas de pacientes (descripción, ubicación, programa asociado)

## [1.4.0] - 2026-02-11

### Agregado

- **FHIR Patient Identifier Systems**: URLs FHIR para todos los identificadores peruanos (DNI/RENIEC, CE, Pasaporte, CNV, Historia Clínica) - Requerido para interoperabilidad RENHICE (Ley 30024)
- **Dispositions**: Configuración de disposiciones clínicas (Admitir, Alta, Transferir, Fallecido, Observación) para flujo hospitalario O3

### Nota

Las dispositions requieren conceptos CIEL que deben agregarse a la colección OCL: 164180 (Disposition set), 1654 (Admit), 1655 (Transfer), 1656 (Died), 1657 (Discharge), 159791 (Admission Location), 160473 (Transfer Location)

## [1.3.0] - 2026-02-11

### Agregado

- **Encounter Type**: Sesión de Psicoprofilaxis (RM 361-2011)
- **Formularios AMPATH**: 5 nuevos formularios clínicos para CRED y Madre Gestante
- **Concept Sources**: Nuevos códigos y descripciones en `conceptsources.csv`

### Programas clínicos obligatorios (normativa MINSA)

- **Tuberculosis** (NTS 200-MINSA/DGIESP-2023, RM 339-2023)
- **VIH/SIDA** (NTS 169-MINSA/2020, RM 1024-2020)
- **Adulto Mayor** (NTS 207-MINSA/DGIESP-2023, RM 789-2023)
- **Planificación Familiar** (NTS 124-MINSA/2016, RM 652-2016)
- **Enfermedades No Transmisibles** (PP 0018, PP 0024)
- **Enfermedades Metaxénicas y Zoonosis** (PP 0017)

### Encounter types obligatorios (normativa MINSA)

- **Diagnóstico y Seguimiento de Tuberculosis** (NTS 200)
- **Tamizaje de VIH** (NTS 169)
- **Manejo de Terapia Antirretroviral - TARGA** (NTS 169)
- **Valoración Clínica del Adulto Mayor - VACAM** (NTS 207)
- **Consejería en Planificación Familiar** (NTS 124)
- **Tamizaje de Cáncer Cervical - PAP/IVAA** (PP 0024)
- **Atención de Enfermedades Metaxénicas** (PP 0017)
- **Atención Integral del Adolescente** (NTS 157)

### Corregido

- **GitHub Actions**: Workflow CI ahora apunta a las ramas `main` y `pre-release`

### Metadata alineada con referenceapplication

- **Cohort Types**: Agregado `cohorttypes/cohorttypes.csv` con System List y My List (faltaba completamente)
- **Global Properties**: Agregadas 4 propiedades core: `concept.true`, `concept.false`, `visits.assignmentHandler`, `visits.allowOverlappingVisits`
- **Privilegios**: Agregado privilegio `O3 Implementer Tools` (requerido para herramientas de implementador O3)

## [1.1.1] - 2026-01-13

### Corregido

**Problema:** Los archivos `programworkflows.csv` y `programworkflowstates.csv` agregados en v1.1.0 causaban errores de inicialización porque los conceptos referenciados no existen en la base de datos.

**Errores generados:**

```
java.lang.IllegalArgumentException: Unable to find concept: Estado de Control CRED
java.lang.IllegalArgumentException: Unable to find concept: Estado de Gestación
```

**Solución aplicada:**

- Vaciados los archivos `programworkflows/sihsalus-programworkflows.csv` (solo headers)
- Vaciados los archivos `programworkflowstates/sihsalus-programworkflowstates.csv` (solo headers)
- Los 8 programas clínicos funcionan sin workflows hasta que se creen los conceptos necesarios en OCL

### Archivos Modificados

- `configuration/backend_configuration/programworkflows/sihsalus-programworkflows.csv` (revertido a solo headers)
- `configuration/backend_configuration/programworkflowstates/sihsalus-programworkflowstates.csv` (revertido a solo headers)

### Pendiente registrado en esa versión

La reimplementación de workflows y estados de v1.1.0 quedó condicionada a crear
los conceptos apropiados en OpenConceptLab (OCL).

## [1.1.0] - 2026-01-12

Esta versión presentó errores de inicialización corregidos en `1.1.1`.

### Corregido

- **Colas de Atención (sihsalus-queues.csv)**: Corregidos 16 registros de colas que generaban errores de duplicados
  - Generados nuevos UUIDs únicos para cada cola
  - Vinculadas correctamente a servicios existentes en `appointmentservicedefinitions`
  - Eliminados errores "Queue with UUID already exists" en la inicialización

### Agregado

- **Program Workflows (sihsalus-programworkflows.csv)**: Agregados 3 workflows para programas clínicos activos
  - Workflow "Estado de Control CRED" para programa Control de Niño Sano
  - Workflow "Estado de Gestación" para programa Madre Gestante
  - Workflow "Estado de Vacunación Infantil" para programa de Vacunación Infantil

- **Program Workflow States (sihsalus-programworkflowstates.csv)**: Agregados 11 estados de workflow
  - **Control CRED**: Activo, Completado, Abandonado
  - **Gestación**: Primer Trimestre, Segundo Trimestre, Tercer Trimestre, Parto, Post-Parto
  - **Vacunación Infantil**: En Proceso, Completo, Incompleto

### Mapeo de Colas a Servicios

| Cola | Servicio Asignado |
|------|-------------------|
| Cola de Admisión Hospital | Consulta ambulatoria por médico general |
| Cola de Admisión Casita Azul | Consulta ambulatoria por médico general |
| Cola de Triaje | Atención ambulatoria por enfermera(o) |
| Cola de Consulta Externa | Consulta ambulatoria por médico general |
| Cola de Farmacia | Atención en farmacia clínica |
| Cola de Laboratorio | Procedimientos de Laboratorio Clínico Tipo II-1 |
| Cola de Hospitalización | Hospitalización de Cirugía General |
| Cola de Emergencia | Atención de urgencias y emergencias |
| Cola de Centro Obstétrico | Atención ambulatoria por obstetra |
| Cola de Centro Quirúrgico | Hospitalización de Cirugía General |
| Cola de Diagnóstico por Imágenes | Ecografía general y Doppler |
| Cola de Anatomía Patológica | Consulta ambulatoria por médico general |
| Cola de Central de Esterilización | Atención ambulatoria por enfermera(o) |
| Cola de Medicina de Rehabilitación | Atención ambulatoria por enfermera(o) |
| Cola de Hemodiálisis | Consulta ambulatoria por médico general |
| Cola de Nutrición y Dietética | Atención ambulatoria por enfermera(o) |

### Archivos Modificados

- `configuration/backend_configuration/queues/sihsalus-queues.csv`
- `configuration/backend_configuration/programworkflows/sihsalus-programworkflows.csv`
- `configuration/backend_configuration/programworkflowstates/sihsalus-programworkflowstates.csv`

## [1.0.0] - Fecha no registrada

### Agregado

- Configuración inicial del content package para SIHSALUS
- 38 módulos de configuración OpenMRS
- 56 formularios clínicos (Ampath Forms)
- Base de datos geográfica de Perú (94,924 registros)
- 495 medicamentos del petitorio nacional
- 6 paquetes OCL de terminología médica (~12.7 MB)
- Configuración FHIR con fuentes estándar (CIEL, LOINC, SNOMED CT)
- 17 ubicaciones hospitalarias
- 30 tipos de visita
- 8 programas clínicos
