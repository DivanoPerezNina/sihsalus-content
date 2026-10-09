# Captura de laboratorio y compatibilidad con la normativa peruana

Revisión clínica y normativa inicial: **2026-09-12**. Cambios incorporados
desde el paquete publicado **1.25.19**. La corrección de selección del
**2026-09-23**, iniciada en `1.25.25` y ampliada en el candidato `1.25.26`, se
describe abajo; no acredita aceptación
clínica ni sustituye los procedimientos institucionales.
Este contrato distingue el contenido requerido del informe, los puntos de corte
diagnósticos y la representación informática. Una release OCL publicada no
demuestra por sí sola compatibilidad con los tres.

## Fuentes y alcance

- **NTS 072-MINSA/DGSP-V.01**, aprobada por
  [RM 627-2008/MINSA](https://www.gob.pe/institucion/minsa/normas-legales/354769-627-2008-):
  procedimientos validados, documentación técnica, control de calidad y formato
  institucional de resultados (§5.1, 5.7, 5.9 y 6.1).
  [Texto oficial, PDF pp. 12–16](https://mef.gob.pe/contenidos/inv_publica/docs/normas/normasv/snip/2015/Documentos_MINSA/26A_RM_N_627_2008_MINSA_Unidad_Productora_de_Servicios_de_Patologia_Clinica.pdf#page=12).
- **Manual INS de procedimientos de laboratorio para el diagnóstico de los
  parásitos intestinales del hombre**, segunda edición de septiembre de 2014,
  Serie de Normas Técnicas 37, `MPR-CNSP-015`, ISBN 978-612-310-040-7.
  [PDF INS](https://repositorio.ins.gob.pe/server/api/core/bitstreams/b47fe475-130d-496e-9f08-43f9f1f7e09f/content).
  Algunas fichas fechadas en 2014 enlazan la edición anterior de 2003; se verificó
  la edición dentro del documento.
- **NTS 213-MINSA/DGIESP-2024**, RM 251-2024 y modificatoria RM 429-2024.
  Se consultó la edición consolidada MINSA de abril de 2025,
  [tabla 13, p. 43](https://www.diresapuno.gob.pe/wp-content/uploads/2025/06/NTS-N%C2%B0-213-MINSA-DGIESP-2024.pdf#page=43).

La búsqueda en fuentes oficiales no localizó una norma sustitutoria posterior
para estas referencias hasta la fecha indicada. No es una certificación exhaustiva
de vigencia ni de cumplimiento clínico del paquete.

## Parasitología

El manual INS requiere identificar el parásito observado, su estadio y densidad
(§3.2.1.4, PDF p. 13). Su reporte incluye método, identificación a género o especie
según lo observado, forma evolutiva y cantidad; admite modalidades cualitativas
y semicuantitativas (§10, PDF pp. 60–61). Kato–Katz informa huevos por gramo
(§5.4, PDF pp. 29–31), una medida distinta de cruces por campo.

De ello se deriva el siguiente diseño de captura, no un datatype ordenado
literalmente por la norma:

- Conservar los conceptos históricos de hallazgo macroscópico `5282`
  (`6576cf12-ca50-4234-be46-ac74a4e7814d`) y microscópico `5286`
  (`a0d91c80-4e2f-4f12-8007-3a5c40931bf8`) como `Coded`.
- El informe completo debe permitir método y hallazgos repetibles con
  identificación, estadio y cantidad/modalidad/unidad, además de descripción
  complementaria. Los dos campos históricos por sí solos no cubren ese informe.
- Permitir identificación a género sin exigir una especie no demostrada.
  Separar negativo, pendiente, no realizado y muestra no evaluable. Nunca
  completar un negativo automáticamente por ausencia de hallazgos registrados.
- Una representación narrativa o un formulario nuevo necesita conceptos y
  versión propios, conservando los resultados históricos.

El validador implementado protege las identidades y datatypes históricos.
No acredita que el frontend ya capture todos los elementos del informe INS;
esa implementación coordinada permanece pendiente.

## Urobilinógeno y creatinina urinaria

La GT 091-DIRIS-LE/2024, aprobada en febrero de 2025, describe lectura
colorimétrica y uroanálisis cualitativo o semicuantitativo. Su alcance es el
primer nivel de DIRIS Lima Este: no establece un datatype nacional ni acredita
el método utilizado en Santa Clotilde.
[Guía oficial, p. interna 6/15](https://cdn.www.gob.pe/uploads/document/file/7633650/6472347-resolucion-directoral-000045-2025-dg.pdf).

Urobilinógeno `2470` (`267b3f53-10ff-498f-a37e-f33b945bd1ce`) conserva
`Numeric`, compatible con su formulario numérico actual. Una variante categórica
requiere otra identidad y las respuestas del método efectivamente utilizado.

Creatinina urinaria `5400` (`bc79bdb5-5bbe-4864-a2ed-81c7ad77ff88`) conserva
su magnitud histórica declarada `mg/24h`. Normalizar por peso produce
`mg/kg/24h`; requiere otra identidad y los datos necesarios para el cálculo.
Un cambio de etiqueta no convierte valores previos.
El [inserto del fabricante, p. 2](https://www.wiener-lab.com.ar/VademecumDocumentos/Vademecum%20espanol/creatinina_cinetica_aa_liquida_sp.pdf)
ilustra esa diferencia, sin acreditar su uso en el hospital.

La guarda de CI acepta la escritura histórica `Units` únicamente para detectar
un cambio de magnitud; esto no demuestra que OpenMRS importe la unidad.
La clave admitida por el importador es `units`. Esa metadata ya se corrigió en
HEAD remoto en la [revisión del 12 de septiembre](../audits/2026-09-12-ocl-remote-corrections.md),
junto con la recuperación de la magnitud histórica de `5400`.
En `1.25.25` las dos filas CSV que declaran `mg/kg/24h` bajo ese UUID conservan
su identidad, pero llevan `Criteria=false`: no pueden seleccionarse. Core usa
entonces los límites del `ConceptNumeric` existente en la magnitud absoluta.
No se convierten valores ni se recalculan interpretaciones históricas.

Initializer actualiza estos registros por UUID. `ConceptReferenceRange` no es
retirable y el parser de ese dominio no implementa borrado: quitar las filas del
CSV dejaría las reglas antiguas activas en instalaciones existentes. El criterio
falso usa el mecanismo nativo de selección para desactivarlas sin SQL ni purga.
Su sustitución por intervalos institucionalmente validados y cualquier revisión
de resultados previos siguen pendientes del procedimiento de laboratorio.

## Hemoglobina

La tabla 13 define puntos de corte de anemia, no límites analíticos universales.
Se corrigen cuatro límites inferiores que excluían la igualdad:

| Fila | Antes | Corregido, g/dL |
| --- | --- | --- |
| 24–59 meses | 11.1 | 11.0 |
| Gestación, primer trimestre | 11.1 | 11.0 |
| Gestación, segundo trimestre | 10.6 | 10.5 |
| Gestación, tercer trimestre | 11.1 | 11.0 |

Core considera bajo un valor `< normalLow` y normal la igualdad, siempre que
no supere el límite superior. El frontend utiliza el mismo comparador.
[Core 2.8.9](https://github.com/openmrs/openmrs-core/blob/4dda0f50a60991a5af9a4b36508e69bb3561c8a6/api/src/main/java/org/openmrs/validator/ObsValidator.java#L402),
[frontend](https://github.com/sihsalus/sihsalus-frontend/blob/1fc71e13d8f9fae2409ae60b6c194b336dcc9345/packages/libs/esm-patient-common-lib/src/results/helpers.ts#L59).

En esa revisión se retiró de HEAD remoto el máximo OCL de 20 g/dL: contradice los rangos
y no se encontró un mandato normativo que lo establezca. La release publicada
anterior conserva su contenido. Mantener provisionalmente crítico
22 y absoluto 30 tampoco los convierte en valores aprobados por MINSA.
Los límites analíticos requieren el método, equipo/reactivo y procedimiento local.
La guarda de CI exige coherencia entre límites absolutos OCL y CSV; no determina
la validez clínica de esos límites.

La NTS exige conservar Hb observada y ajustada cuando corresponde ajuste por
altitud (§5.3.2–5.3.3, p. 22). Este cambio no sobrescribe el valor observado
ni implementa una conversión automática.

## Captura prenatal OBST-013: revisión del 8 de octubre de 2026

Las etiquetas de clasificación de anemia en `OBST-013-TAMIZAJE PRENATAL`
no deben aplicar los puntos de corte del primer/tercer trimestre a toda gestación.
La [RM 429-2024/MINSA, tabla 13, PDF p. 9](https://cdn.www.gob.pe/uploads/document/file/6498138/5670414-rm-429-2024.pdf#page=9)
distingue el segundo trimestre: normal desde 10,5 g/dL, leve 9,5–10,4,
moderada 7,0–9,4 y severa por debajo de 7,0. La interpretación también necesita
el contexto aplicable de altitud y la hemoglobina ajustada cuando corresponde.

La corrección de captura elimina los intervalos universales de las opciones y
explicita que se registra una clasificación confirmada según trimestre y
altitud. Conserva nombre, versión `1.0.0`, UUIDs, respuestas codificadas,
hemoglobina medida, validaciones y observaciones históricas. Initializer
actualiza el esquema por su mecanismo AMPATH habitual; no hay SQL ni recarga
forzada. No se añade una clasificación calculada ni se deduce trimestre de los
campos independientes de tamizaje VIH o sífilis.

Esto corrige una indicación engañosa; no acredita cumplimiento de NTS 213.
La captura del contexto clínico y la interpretación derivada requieren el
contrato del componente backend responsable. La revisión funcional debe probar
la apertura de un encuentro histórico, su clasificación conservada y el
registro/recarga de una clasificación confirmada en QLTY antes de desplegar.

## Selección de poblaciones desde 1.25.25

Desde `1.25.26`, todas las bandas de edad de hemoglobina usan semanas, meses o
años completos a la fecha de la muestra mediante los helpers nativos de Core. Así, una muestra
neonatal histórica no coincide también con la banda de edad actual del paciente.
Las filas neonatales reutilizan el concepto `sihsalus:1030`
(`c2380004-0000-4000-8000-000000000004`), semanas de prematuridad, capturado por
CRED-009 y CRED-026: un valor positivo hasta 20 identifica prematuridad; cero
explícito permite los rangos de nacidos a término. Un dato ausente, inválido o
posterior a la muestra no establece esa condición. Las bandas de prematuros son
0–<1, 1–<4 y 4–<8 semanas completas, conforme a las semanas de vida de tabla 13.

Los rangos maternos reutilizan los estados del programa existente: «Control
Prenatal»/«Parto» para gestación y «Posparto» para puerperio. Se consulta el estado
activo en la fecha de la muestra; no se infiere parto a partir de 40 semanas.
El tercer trimestre continúa mientras persista el estado gestacional. Las
observaciones de edad gestacional posteriores a la muestra no se utilizan.

`getLatestObs` selecciona la última observación creada. La guarda de fecha evita
usar una observación futura, pero no busca una observación anterior alternativa.
Sin un rango coincidente, Core puede usar los límites generales del concepto:
ese fallback **no establece normalidad clínica específica por población**.
Se requiere mantener los datos de nacimiento y las transiciones del programa,
además de validar la captura y presentación en el entorno clínico.

## Pendientes de la actualización completa

Las correcciones de selección no validan los intervalos altos ni los métodos.
La [auditoría previa](../audits/2026-09-10-laboratory-reference-ranges-pr-225.md)
conserva el diagnóstico inicial; la
[revisión del 23 de septiembre](../audits/2026-09-23-forms-clinical-review.md)
distingue los defectos identificados y el alcance de las correcciones.

Para completar laboratorio se necesita el procedimiento/formato institucional,
los métodos y equipos/reactivos aplicados y sus intervalos verificados. Las
referencias de otros laboratorios o fabricantes no sustituyen esos datos.
Por eso se conserva la release anterior de laboratorio y no se escribe una
nueva release OCL con supuestos sobre métodos o pacientes.
Las [correcciones ya aplicadas en HEAD remoto](../audits/2026-09-12-ocl-remote-corrections.md)
resuelven tipos históricos, unidades y respuestas incompatibles, y documentan
los puntos de corte de Hb. Su verificación de metadata no reemplaza la validación
funcional y clínica de una futura release completa.
