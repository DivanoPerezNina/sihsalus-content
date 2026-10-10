# Guía de contenido por dominio

Esta guía conserva los contratos de formularios y las notas de alcance que no
tienen documento propio. El [índice de contratos](README.md#contratos-por-dominio)
enlaza las definiciones de catálogos, institución, Admisión e historia social.
Las presentaciones adicionales de medicamentos se describen en el
[catálogo clínico](clinical-drug-catalog.md).

## Contrato canónico de Visit Notes

Visit Notes usa el `Form` `c75f120a-04ec-11e3-8780-2b40bef9a44b` y el tipo de
encuentro `d7151f82-c1f3-4152-a605-2f9ea7414a79`. El pin comprobado de Initializer
`2.13.0-sihsalus.1` no ofrece un dominio CSV genérico para `Form`;
la [revisión de Liquibase](audits/2026-09-22-liquibase-initializer.md) documenta
la limitación y las alternativas. Liquibase crea de forma idempotente la metadata
que falta y solo completa una asociación de tipo de encuentro nula.
Un `Form` existente nunca se renombra, publica, retira ni reasocia silenciosamente.

El contrato también fija los datatypes de los conceptos consumidos por el frontend
y separa `app:hoja.clinica.resumenConsulta` de
`app:hoja.clinica.resumenConsulta.editar`. Los detalles verificables están en
[visit-note-content-contract.json](contracts/visit-note-content-contract.json).

## Contrato de diagnóstico de CE-001

`CE-001-CONSULTA EXTERNA` no captura diagnósticos. El diagnóstico CIE-10 se registra exclusivamente mediante Visit Notes como diagnóstico nativo del encuentro; no deben reintroducirse observaciones de texto, certeza u ocurrencia que simulen esa estructura.

La versión `1.0.3` elimina la página SOAP completa del formulario general y conserva los demás campos. La versión `1.0.2` corrigió anteriormente el diagnóstico. `AmpathFormsLoader` deriva la identidad persistida del nombre y la versión. En upgrades, una migración idempotente retira y despublica exclusivamente el `Form` `1.0.1` con UUID persistido `da631d8c-c695-3c4a-9d77-19bbbf0174e3`; no elimina ni modifica sus encuentros históricos. La migración publicada conserva su contrato original con `1.0.2` (`df1a34b4-0e8f-3564-84d9-55ce9e4284bd`) y no se modifica. Después, el loader nativo retira esa versión y crea `1.0.3` (`a43f4ba0-1d01-3533-aa96-927ad602851a`) sin sobrescribir los esquemas anteriores. En instalación limpia crea únicamente `1.0.3`. El `uuid` incluido en el JSON no es la identidad persistida y no debe usarse como contrato de integración.

Para rollback no se debe volver a publicar el JSON con una versión histórica, porque reutilizaría y sobrescribiría el recurso histórico que contiene la captura de diagnóstico obsoleta. Se revierte el frontend coordinadamente, sin reactivar el formulario retirado y conservando sus encuentros para lectura histórica.

## Contrato de examen físico de Consulta Externa

`CE-EXF-001-EXAMEN FISICO` versión `1.0.1` es el formulario propio de examen físico ambulatorio. Conserva los diez conceptos e identificadores de examen general y regional ya existentes; no incluye Subjetivo, Objetivo, Apreciación ni Plan. Estado general sigue siendo obligatorio y los sistemas específicos se registran según pertinencia clínica, sin completar hallazgos normales automáticamente. Anamnesis, diagnóstico y tratamiento mantienen sus formularios y servicios existentes.

El frontend debe resolver `formsList.physicalExamForm` por ese nombre, con la cabecera **Examen físico**. El contenido se incorpora antes o junto con el frontend; no se usa el antiguo formulario como alternativa cuando falta el nuevo.

`CE-SOAP-001-NOTA SOAP` `1.2.0` se despublica y retira declarativamente. Conserva nombre, versión, UUID, preguntas, conceptos y campos obligatorios; únicamente cambian `published` y `retired` en su esquema. No se elimina ni reasocia ningún encuentro u observación y no se usa una migración SQL. Los formularios propios de Hospitalización no cambian.

Validar la identidad nueva y el retiro con Initializer en instalación y actualización, y comprobar la lectura de encuentros anteriores con datos sintéticos. Las regresiones locales verifican los esquemas; no acreditan carga efectiva, retiro en el backend ni aceptación clínica. Las opciones de anamnesis heredadas de la integración anterior requieren revisión clínica; el catálogo prestacional por ubicación sigue pendiente.

## Anamnesis breve de Consulta Externa

`CE-ANAM-001-ANAMNESIS` `1.1.1` reduce de once a tres los campos clínicos de texto
libre: motivo de consulta, tiempo de enfermedad y detalle breve opcional.
Inicio, evolución y las seis funciones biológicas usan selectores; estas últimas
quedan en una sección inicialmente contraída. Ninguna opción se selecciona ni
se copia desde otra consulta automáticamente. Vacío no significa normal.

Los selectores reutilizan el soporte nativo `answers[].value` de O3 y conservan
las observaciones **Text** existentes. Las opciones son valores de texto, no
UUID de respuesta ni nuevos diagnósticos codificados; no cambia ningún datatype
ni se convierte contenido histórico. El motor debe incluir la corrección de
lectura/visualización de valores literales del frontend coordinado.

Las versiones `1.1.1` de anamnesis y `1.0.1` de examen físico limitan cada
área de texto a 4000 caracteres y muestran el contador en el motor de formularios.
El profesional responsable se muestra como dato de solo lectura: el motor toma
el proveedor clínico de la sesión al crear y conserva el proveedor del encuentro
al editar. La autorización del rol sigue siendo responsabilidad del backend.

**Coordinación:** content `1.25.29` y el frontend que configura explícitamente
anamnesis `1.1.1` y el formulario propio de examen físico `1.0.1` deben probarse juntos en QLTY. El frontend
no debe abrir la captura anterior si falta la versión esperada. Si una visita
abierta ya contiene un formulario anterior, conserva su lectura histórica y
bloquea una segunda captura; no reasigna ni duplica ese encuentro.

**Aceptación pendiente:** revisar opciones con el responsable clínico, crear,
guardar, recargar y editar con roles sintéticos, comprobar campos vacíos y
visitas que cruzan la actualización. Los validadores locales no acreditan esa
aceptación. En un rollback conservar los encuentros y esquemas nuevos, usar un
frontend compatible con ambas versiones y no republicar el esquema anterior
sobre la identidad nueva.

## Rangos de laboratorio

El [contrato de captura](contracts/laboratory-reporting.md) concentra datatypes,
unidades, puntos de corte de hemoglobina y pendientes de selección de población
y método. La [auditoría de rangos](audits/2026-09-10-laboratory-reference-ranges-pr-225.md)
y el [registro OCL](audits/2026-09-12-ocl-remote-corrections.md) conservan la evidencia
fechada. Las comprobaciones de coherencia del paquete no acreditan validación clínica.

## Contrato preparatorio para PDF de resultados de laboratorio

La [línea base de acceso clínico](clinical-rbac.md) define los marcadores de
adjuntos, la versión backend requerida y las pruebas de autorización pendientes.
El PDF es suplementario: su carga no completa la orden, cambia su estado ni
sustituye resultados estructurados o su validación clínica. Los permisos
declarados por este paquete no habilitan por sí solos el flujo.

## Base reproducible de Stock Management

El paquete provisiona los catálogos controlados de unidades de empaque y
dispensación, motivos de ajuste y toma física, tipos de fuente y categorías de
artículos. Los UUID se coordinan con
`sihsalus-frontend/config/frontend.json`; un validador bloquea divergencias entre
catálogos, propiedades globales y roles canónicos del módulo.

Esta base instala metadata y permisos, no inventario. Un despliegue limpio debe
comenzar con cero artículos y cero existencias hasta cargar un conteo físico
aprobado. Tampoco habilita el descuento automático desde dispensación: esa
integración requiere una transacción clínica/inventario recuperable antes de
considerarse segura.

## Relación madre-hijo y sala de hospitalización

`configuration/relationshiptypes/relationshiptypes.csv` define la relación
Madre→Hijo (`e6be4def-dbc8-462a-8714-53da66903cb8`). El mapeo
`emr.motherChildRelationshipType` de
`configuration/metadatatermmappings/metadatatermmappings-core-sihsalus.csv`
permite que EmrApi resuelva ese tipo para
`GET /emrapi/maternal/mothersAndChildren`; debe apuntar al mismo UUID. Los
registros guardados llevan a la madre en `personA` y al hijo en `personB`. La
configuración frontend `motherChildRelationshipTypeUuid` también debe coincidir
para que el flujo de parto y la sala materna compartan el mismo vínculo.

## Antecedentes obstétricos

`OBST-001-ANTECEDENTES` `1.0.1` permite declarar explícitamente **Ninguna** en
antecedentes familiares y personales. Reutiliza el concepto activo `sihsalus:521`
(`dbb7efe1-12d9-58b0-8de2-c218f626ff48`), ya asociado como respuesta a ambas
preguntas en el catálogo. El validador declarativo del motor impide combinarlo
con enfermedades. Ambos antecedentes siguen siendo obligatorios; no se
preselecciona una respuesta ni se interpreta un campo vacío como ausencia.

Vaginales, cesáreas, nacidos vivos, nacidos muertos y peso del RN pueden
registrarse aunque el contador de partos esté vacío o sea cero. Conservan sus
conceptos, límites y carácter opcional. Esto permite registrar un parto
pretérmino sin exigir un parto a término previo.

La corrección no resuelve la ambigüedad del concepto `sihsalus:915`
(`8795c05b-f286-4d70-a1e6-69172e676f05`): su nombre preferido en español indica
partos a término, mientras otras denominaciones y mapeos remiten a paridad.
Se conserva la etiqueta **Partos** y no se sustituye por `sihsalus:818`, cuya
definición tampoco acredita un contador equivalente. La
[revisión clínica documentada](audits/2026-09-23-forms-clinical-review.md)
requiere decisión del responsable clínico y de terminología antes de redefinir
estos conceptos, añadir un contador o reinterpretar observaciones históricas.

La nueva versión usa `AmpathFormsLoader` de Initializer; no sobrescribe el
esquema histórico `1.0.0` ni migra sus encuentros u observaciones. La integración
existente de [Initializer](../.github/integration/admission-initializer/README.md)
incluye el formulario y verifica la identidad y el esquema de las versiones
anteriores en actualización y reinicio. Su ejecución en CI sigue siendo
necesaria; las pruebas locales no acreditan carga efectiva ni aceptación clínica.

Para comprobar el esquema local, ejecutar `python3 .github/scripts/test_ampath_forms.py`,
`python3 .github/scripts/validate_ampath_forms.py` y
`npm test --prefix .github/integration/form-expressions` tras instalar las
dependencias propias según la [guía de desarrollo](development.md).
Para inspección visual, el Form Builder nativo del frontend ofrece
`/openmrs/spa/form-builder/new`: importar este JSON y usar **Render changes** y
**Preview**. La vista previa usa el motor real sin guardar respuestas clínicas;
comprobar Ninguna sola, Ninguna con enfermedad y los cinco campos con Partos
vacío o cero. Importar y previsualizar no publica el formulario en el backend.
La publicación del paquete candidato `1.25.31` sigue el workflow existente de
esa guía, después de sus comprobaciones y revisión; no requiere una migración
SQL ni un script de recarga del formulario.

## Responsable de puerperio inmediato

`OBST-006-PUERPERIO INMEDIATO` `1.0.2` concentra proveedor, ubicación y rol en
una página **Responsable**. Conserva el primer proveedor (`resposable`), que
gobierna el envío nativo, junto con `lugarAtencion` y `rolDelResponsable`.
Retira del nuevo esquema el segundo control `responsableAtencion`: ambos eran
metadata del mismo encuentro, sin concepto ni observación independiente, y se
rehidrataban del mismo proveedor guardado. No se renombra el ID histórico
`resposable` ni se modifica la captura clínica de puerperio.

La versión anterior `1.0.1` conserva su esquema y encuentros mediante el mismo
loader y las comprobaciones de historia de Initializer descritas arriba. No se
migran proveedores, roles, ubicaciones ni observaciones. La comprobación UI
pendiente debe verificar una página Responsable, un único proveedor y guardado
y lectura nativos con el mismo proveedor, rol y ubicación.

## Sujeto de la epicrisis obstétrica

`HOSP-010-EPICRISIS OBSTÉTRICO-POSTPARTO` `1.0.2` conserva la epicrisis de la
madre y retira de la captura nueva el grupo **Recién Nacido**: género, peso,
Apgar, observaciones, condición de alta y responsable de neonatología. Todos
eran observaciones del RN dentro del encuentro materno. El grupo no cambia el
sujeto del encuentro; su peso reutilizaba `5089AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA`,
el concepto general de peso, y podía atribuir una medida del niño a la madre.

Un control Markdown nativo, sin concepto ni observación, orienta a registrar la
evaluación y medidas en la historia propia del recién nacido desde **Hijos
vinculados**. El profesional elige al hijo correcto mediante el vínculo nativo;
el formulario no infiere un niño, duplica datos ni cambia el paciente activo.
El motor del frontend registra `markdown`, transforma su tipo a `control` y
renderiza `value`; el validador del paquete reconoce ahora ese renderer nativo
sin valor clínico. Conserva el rechazo de observaciones sin concepto y
renderers no soportados.
El esquema `1.0.1` y sus encuentros se conservan mediante el loader versionado
y la guarda de historia de Initializer. No se trasladan ni corrigen datos
históricos; cualquier revisión de atribución previa requiere un procedimiento
clínico separado.

La revisión acotada de `HOSP-007` y `OBST-005` encontró grupos Neonato que
registran el equipo/responsable de atención del parto, no peso ni Apgar del RN.
Esos campos de resumen requieren su propia revisión clínica y no se eliminan
por equivalencia con la biometría. El `pesoMadreKg` de `OBST-005` permanece como
medida materna. `HOSP-011` no contiene un grupo de biometría de recién nacido.
No se introducen filtros en lectores para ocultar observaciones mal atribuidas.

La aceptación pendiente debe comprobar que el nuevo formulario no ofrece
captura de RN en el encuentro materno, que muestra la orientación y que guarda
y lee la epicrisis materna. Registrar medidas del RN exige su propia historia,
visita y encuentro; probar únicamente con pacientes sintéticos propios.

## Sujeto del tamizaje de salud mental CRED

`CRED-011-SALUD MENTAL NIÑO Y CUIDADOR` `1.3.1` conserva el nombre y UUID
JSON para continuar su historia versionada; la captura nueva corresponde al
niño del encuentro. Retira las opciones PHQ-9 y AUDIT-C, que el propio esquema
anterior indicaba aplicar al cuidador, y la detección de violencia en la
madre/cuidadora con su campo `resultadoViolencia`. Estas observaciones se
guardaban bajo el paciente activo, sin un sujeto adulto independiente.

Un control Markdown nativo orienta a registrar los instrumentos y resultados
del cuidador en su propia historia clínica. La ayuda de instrumento y
observaciones deja de solicitar resultados del adulto. No selecciona ni abre
una historia automáticamente, no copia puntajes y no infiere quién es el
cuidador.

PPSC/PSC-17 conserva su opción, conceptos, rango de puntaje, resultados y edad
del niño. El plan sigue siendo obligatorio para resultados positivos o sospecha
diagnóstica. El cálculo y la visibilidad dejan de referenciar el campo de
violencia retirado; el puntaje sigue obligatorio para la opción infantil
restante. Esta corrección de sujeto no valida la selección clínica de PPSC o
PSC-17, no añade reglas de edad ni sustituye sus instrumentos oficiales.

El loader nativo conserva el esquema `1.3.0` y sus encuentros; el ensayo de
Initializer incluye ahora CRED-011 en la guarda de identidad, esquema y retiro
de versiones anteriores. No migra ni reatribuye resultados históricos del
cuidador. Su revisión requiere un procedimiento clínico separado. Las pruebas
de expresiones cubren resultado vacío, negativo, positivo y sospecha sin
referencias a campos retirados y sin dejar un plan obligatorio oculto.

La aceptación visual debe comprobar la única opción infantil y la orientación,
sin captura de violencia del cuidador. La publicación continúa por el mismo
paquete candidato y workflow descritos arriba; esta modificación de fuente no
acredita publicación, carga efectiva ni aceptación clínica.

## Alcance clínico documentado

El inventario siguiente orienta la revisión de formularios para categoría II-1 /
II-2. No certifica cobertura normativa ni que un flujo esté habilitado en el
hospital. Antes de implementar cambios, comprobar el contrato del dominio, los
módulos del distro y la norma vigente en fuentes oficiales.

### Formularios y metadata incluidos

| Área | Contenido y límites |
| --- | --- |
| Consulta externa y salud mental | `CE-*` y `PSIC-001` a `PSIC-004`. Los diagnósticos se registran mediante Visit Notes. |
| Signos vitales y emergencia | Metadata separada para el chart, triaje y atención posterior; el [contrato de encuentros](audits/2026-07-16-chart-vitals-encounter-contract.md) requiere captura embebida en el frontend. No hay un JSON AMPATH adicional. |
| Obstetricia y neonatal | `OBST-*`, partograma, recién nacido y puerperio. |
| Hospitalización | `HOSP-001`, `HOSP-004`, `HOSP-008`, `HOSP-009`, `HOSP-012` y `FormularioEpicrisisMédica`. |
| Referencia | `CE-REF-*` y [catálogo de transporte](contracts/referral-transport-terminology.md). |
| CRED | `CRED-*`, incluidos Huanca adaptado (`CRED-026`) y habilidades/conductas (`CRED-027`); el [contrato CRED actualizado](contracts/cred-clinical-completion.md) reúne integración, pruebas y pendientes. La [auditoría de julio](audits/2026-07-10-cred-nts238-forms.md) conserva su alcance histórico. |
| Odontología | `ODONT-*`; el odontograma es un componente separado. |
| Inmunizaciones | `INMU-001` e `INMU-002`; la [auditoría NTS 246](audits/2026-06-17-inmunizaciones-nts-246.md) registra brechas de vacunas y productos. |
| Laboratorio | Formularios de resultados y rangos con los límites del [contrato de laboratorio](contracts/laboratory-reporting.md). |

### Flujos que requieren comprobación o desarrollo coordinado

| Área | Revisión pendiente documentada |
| --- | --- |
| Emergencia | Atención inicial, observación, evolución y reanimación, además de la metadata de triaje. |
| Prescripción y farmacia | Verificar los módulos nativos de órdenes, dispensación y conciliación; completar seguimiento farmacéutico en hospitalización. |
| Laboratorio y transfusión | Solicitud, toma y trazabilidad de muestra; solicitud, compatibilidad y administración transfusional. |
| Imagen y patología | Comprobar módulos instalados y completar solicitud e informe. |
| Cirugía y anestesia | Evaluación preoperatoria, consentimiento, notas operatoria y anestésica, recuperación. |
| Hospitalización y cuidados críticos | Interconsulta, admisión no obstétrica, nutrición clínica y plan hospitalario; para II-2, ingreso y monitorización UCI según alcance aprobado. |
| Esterilización | Documentos de material y central de esterilización. |

### Referencias documentadas

- [NTS 021-MINSA/DGSP-V.03: categorías de establecimientos](https://spij.minjus.gob.pe/Graficos/Peru/2011/Julio/16/RM-546-2011-MINSA.pdf).
- [NTS 139-MINSA/2018/DGAIN: gestión de historia clínica](https://spij.minjus.gob.pe/Graficos/Peru/2018/Marzo/15/RM-214-2018-MINSA.pdf).
- [NTS 238-MINSA/DGIESP-2025: crecimiento y desarrollo del niño](https://www.gob.pe/institucion/minsa/informes-publicaciones/7857089-norma-tecnica-de-salud-para-el-control-de-crecimiento-y-desarrollo-del-nino-nts-n-238-minsa-dgiesp-2025).
- [NTS 246-MINSA/DGIESP-2026: esquema nacional de inmunizaciones](https://www.gob.pe/institucion/minsa/normas-legales/8265031-561-2026-minsa).
- [Guía de Vigilancia del Neurodesarrollo de Huanca Payehuanca](https://repositorio.essalud.gob.pe/handle/20.500.12959/5846).

Estas referencias conservan el contexto de las revisiones documentadas; no se
ha realizado una nueva auditoría normativa como parte de esta limpieza.
