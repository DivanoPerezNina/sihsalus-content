# Documentación

El [README principal](../README.md) describe el paquete y su estructura.
Consultar [AGENTS.md](../AGENTS.md) antes de contribuir.

## Guías

| Documento | Contenido |
| --- | --- |
| [Desarrollo y validación](development.md) | Requisitos, comandos locales, empaquetado y publicación. |
| [Contenido por dominio](content-guide.md) | Decisiones de contenido, coordinación con frontend y alcance clínico documentado. |
| [Formularios AMPATH](../configuration/ampathforms/Readme) | Nombres, versiones e identidad persistida. |
| [Medicamentos](clinical-drug-catalog.md) | Conceptos y presentaciones adicionales mediante CSV nativos. |
| [Acceso clínico](clinical-rbac.md) | Roles, privilegios y restricciones por ámbito. |

## Contratos por dominio

| Dominio | Contrato |
| --- | --- |
| Identidad institucional | [Hospital Santa Clotilde](contracts/hospital-santa-clotilde-institutional-metadata.md) |
| Catálogo territorial | [Barrios de Santa Clotilde](contracts/santa-clotilde-neighborhoods.md) |
| Referencias institucionales | [Terminología de transporte](contracts/referral-transport-terminology.md) |
| Procedimientos | [Sitios anatómicos en español](contracts/procedure-anatomy.md) |
| Admisión | [Reconciliación de roles](contracts/admission-role-reconciliation.md), [confirmación de pago](contracts/arrival-payment.md) |
| Perfiles del hospital | [Criterios y aceptación](contracts/hospital-access-profiles.md), [contrato verificable](contracts/hospital-access-profiles.json) |
| Visit Notes | [Identidades y datatypes](contracts/visit-note-content-contract.json) |
| Consulta externa | [Diagnóstico CE-001](content-guide.md#contrato-de-diagnóstico-de-ce-001), [examen físico](content-guide.md#contrato-de-examen-físico-de-consulta-externa) |
| Historia social | [Alcohol y tabaco](contracts/social-history.md) |
| CRED | [Curvas, instrumentos, controles neonatales y hemoglobina](contracts/cred-clinical-completion.md) |
| Laboratorio | [Captura y rangos](contracts/laboratory-reporting.md) |
| Signos vitales | [Contrato de encuentros y evidencia fechada](audits/2026-07-16-chart-vitals-encounter-contract.md) |
| Enrutamiento de atención | [Catálogo canónico](contracts/hsc-care-routing.csv), [auditoría](audits/2026-07-18-canonical-care-routing.md) |
| Export OCL principal | [Exclusiones reproducibles](contracts/ocl-sihsalus-2026-09-09-1-exclusions.json), [auditoría de actualización](audits/2026-09-12-ocl-refresh.md) |

## Evidencia e historia

El [índice de auditorías](audits/README.md) organiza las revisiones por fecha y
tema. Sus observaciones, versiones, rutas antiguas y resultados corresponden al
momento de cada revisión; no describen automáticamente el estado de un entorno hoy.
El [CHANGELOG](../CHANGELOG.md) distingue cambios publicados y propuestas sin release.

Las fuentes actuales están en `configuration/`. El prefijo histórico
`configuration/backend_configuration/` se conserva dentro del ZIP distribuible;
la [guía de desarrollo](development.md#contrato-de-empaquetado) explica la diferencia.

Los resultados de CI corresponden al commit ensayado. La aceptación clínica,
la autorización efectiva en el hospital y el despliegue necesitan su propia
evidencia, según el contrato de cada dominio.

La [revisión de Liquibase e Initializer](audits/2026-09-22-liquibase-initializer.md)
identifica qué capacidades faltan para sustituir el SQL por metadata declarativa
y verifica los doce changesets ya publicados en `1.25.24`.
