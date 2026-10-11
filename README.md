# SIHSALUS Content Package

Metadata backend para OpenMRS: formularios AMPATH, terminología OCL, catálogos,
configuración institucional y roles del Hospital Santa Clotilde.

La metadata que carga Initializer está en [configuration/](configuration).
[pom.xml](pom.xml) define la versión del paquete y filtra
[content.properties](content.properties), que declara sus dependencias.
[assembly.xml](assembly.xml) genera el ZIP distribuible.

## Estructura

| Ruta | Responsabilidad |
| --- | --- |
| [configuration/](configuration) | Metadata declarativa, separada por dominio de Initializer. |
| [docs/](docs/README.md) | Guías, contratos y auditorías históricas. |
| [.github/scripts/](.github/scripts) | Validadores y sus pruebas de regresión. |
| [.github/integration/](.github/integration) | Ensayos de MariaDB/Liquibase, Initializer y autorización nativa. |
| [.github/workflows/](.github/workflows) | Validación, construcción y publicación. |
| [CHANGELOG.md](CHANGELOG.md) | Cambios por versión y estado de publicación. |

Los dominios se mantienen directamente bajo `configuration/`. Dentro del ZIP
conservan el prefijo `configuration/backend_configuration/` que consume el
distro; este detalle del artefacto no requiere otra carpeta en el árbol de fuentes.

## Desarrollo y validación

Antes de editar, leer [AGENTS.md](AGENTS.md) y el
[contrato del dominio](docs/README.md#contratos-por-dominio).

Para construir el paquete y comprobar sus propiedades:

```sh
./mvnw clean verify --batch-mode --file pom.xml
```

El ZIP se genera en `target/sihsalus-content-<version>.zip`. Este comando no ejecuta
los validadores de dominio ni los ensayos de integración; estos se ejecutan
por separado en [CI](.github/workflows/main.yml). La
[guía de desarrollo](docs/development.md) explica cómo ejecutarlos, los requisitos
y las condiciones de publicación.

## Documentación del contenido

- [Índice de contratos y guías](docs/README.md).
- [Guía por dominio y alcance clínico documentado](docs/content-guide.md).
- [Identidad y versiones de formularios AMPATH](configuration/ampathforms/Readme).
- [Catálogo clínico de medicamentos](docs/clinical-drug-catalog.md).
- [Roles y acceso clínico](docs/clinical-rbac.md).

La configuración visual se mantiene en `sihsalus-frontend`; la lógica clínica y
la autorización efectiva corresponden a los módulos backend. Las comprobaciones
del paquete no sustituyen la aceptación clínica ni la validación de un despliegue.
