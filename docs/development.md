# Desarrollo, validación y publicación

Ejecutar los comandos desde la raíz del repositorio. Antes de cambiar metadata,
leer [AGENTS.md](../AGENTS.md) y el [contrato correspondiente](README.md#contratos-por-dominio).

## Requisitos

- Python 3.9 o superior para los validadores y pruebas de biblioteca estándar.
- Bash para las comprobaciones de rangos, terminología y publicación.
- Node 24 y npm para ejecutar las expresiones JavaScript de formularios con la
  misma biblioteca de fechas del motor. Esta prueba usa el runner nativo de Node;
  los validadores Python no ejecutan JavaScript.
- Maven Wrapper fija Maven 3.10.0 para el paquete y su publicación; descarga la
  distribución oficial y comprueba su SHA-256.
- Java: CI usa Java 21 LTS para el paquete, publicación y MariaDB/Liquibase,
  alineado con el backend. El ensayo independiente de autorización de rangos
  mantiene Java 17.
- MariaDB y el backend de OpenMRS solo se necesitan en sus ensayos de integración;
  cada ensayo documenta su infraestructura y aislamiento.

## Validación local

El [workflow principal](../.github/workflows/main.yml) es la fuente de los comandos
de CI. Para ejecutar todos sus validadores de metadata y las regresiones locales:

```sh
set -e
for validator in .github/scripts/validate_*.py; do
  python3 "$validator"
done
python3 -m unittest discover -s .github/scripts -p 'test_*.py'
bash .github/scripts/validate_reference_ranges.sh
for regression in .github/scripts/test_*.sh; do
  bash "$regression"
done
python3 -B .github/integration/admission-initializer/test_harness.py
npm ci --prefix .github/integration/form-expressions --ignore-scripts
npm test --prefix .github/integration/form-expressions
TZ=America/New_York npm test --prefix .github/integration/form-expressions
```

Las pruebas de regresión usan fixtures sintéticas y copias temporales cuando
necesitan mutar metadata. No requieren servidores del hospital.

Para comprobar las propiedades del paquete y generar el ZIP:

```sh
./mvnw clean verify --batch-mode --file pom.xml
```

Maven no ejecuta las pruebas Python, Bash ni las integraciones de esta guía.
Tampoco formatea ni reescribe fuentes. Los proyectos Java de integración tienen
sus propios POM y no forman parte del artefacto distribuido.

Para cambios solo de documentación, revisar el diff, los enlaces y la coherencia
con los archivos referenciados. No se necesitan pruebas nuevas ni subir la
versión del paquete; véase [AGENTS.md](../AGENTS.md#validación-y-revisión).

## Contrato de empaquetado

[assembly.xml](../assembly.xml) toma los archivos directamente de `configuration/`
y los ubica bajo `configuration/backend_configuration/` dentro del ZIP.
`content.properties` queda en la raíz con nombre y versión filtrados desde el POM.

Se excluyen `.DS_Store`, `.gitkeep`, la guía `ampathforms/Readme` y los formularios
de `ampathforms/_deprecated/`. Las guías, pruebas y workflows quedan fuera del ZIP.
No renombrar dominios, formularios ni archivos de migración por criterios de estilo.

Los dos commits históricos fijados por el ensayo de Initializer conservan su
estructura antigua. El arnés reconoce explícitamente esas fuentes y la estructura
actual; ambos producen las mismas rutas de ejecución. Una reorganización debe
conservar los bytes de la metadata distribuida y las identidades/checksums de
Liquibase.

## Ensayos de integración

| Ensayo | Ejecución y alcance |
| --- | --- |
| [Autorización de rangos](../.github/integration/reference-range-access/README.md) | Core real con datos sintéticos, sin base de datos ni servidor; Java 17. |
| [MariaDB/Liquibase](../.github/integration/admission-role-reconciliation/README.md) | Migración completa contra MariaDB efímero; Java 21. |
| [Initializer](../.github/integration/admission-initializer/README.md) | Backend fijado, instalación nueva y dos escenarios de actualización; runner desechable de GitHub. |

Dos comprobaciones Java se pueden ejecutar sin base de datos ni Docker, con la
versión de Java indicada por cada proyecto:

```sh
mvn --batch-mode --no-transfer-progress \
  --file .github/integration/reference-range-access/pom.xml test
mvn --batch-mode --no-transfer-progress \
  --file .github/integration/admission-role-reconciliation/pom.xml \
  -Dtest=HarnessGuardTest test
```

El ensayo completo de MariaDB requiere una base sintética exclusivamente suya;
el de Initializer exige el runner efímero descrito en su README. Ejecutarlos
mediante sus workflows existentes. Las pruebas locales del arnés no demuestran
que el backend arrancó ni que la migración pasó contra MariaDB.

## Validación y publicación

El CI ejecuta en paralelo la validación del paquete, la integración
MariaDB/Liquibase, la autorización nativa de rangos y los tres escenarios de
Initializer: actualización, instalación nueva y alias operativo. Un fallo de
integración no oculta los resultados del build ni cancela los otros escenarios.
La publicación en Maven Central exige que todas estas comprobaciones pasen en
el mismo commit de `main` o `pre-release`; los PR solo validan.

Después de publicar, `Validate with SIHSALUS` construye el backend con el paquete
publicado y arranca `db` y `backend` mediante el `docker-compose.yml` normal del
distro. Sus dependencias incluyen el generador nativo de `oauth2.properties`,
incluso con autenticación local, y la política `initializer.startup.load=fail_on_error`.
No usar el fixture histórico `docker-compose-no-volumes.yml`: omite esa
configuración y puede producir fallos de módulos y permisos ajenos al paquete.
La sonda de arranque se ejecuta dentro del backend, sin publicar un puerto del
host. El proyecto exclusivo del runner se elimina con sus volúmenes al terminar;
no usa datos ni servidores del hospital. El clasificador conserva el rechazo de
errores de carga aun cuando el endpoint HTTP responda correctamente.

### Compatibilidad de la herramienta de publicación

Usar Java 21 LTS y `./mvnw` para construir y publicar con Maven 3.10.0. El Wrapper
comprueba el SHA-256 de la distribución oficial; CI utiliza el mismo ejecutable
que el desarrollo local. El perfil `release` requiere Maven 3.10 y mantiene la
firma de Maven GPG.

La publicación utiliza los mecanismos nativos de Maven y JReleaser 1.26.0:

1. `maven-deploy-plugin` coloca el POM, ZIP y sus firmas en un repositorio remoto
   de tipo `file:` bajo `target/staging-deploy`.
2. El goal `jreleaser:deploy`, enlazado a la fase `deploy`, valida el POM, calcula
   los checksums y crea el bundle de Maven Central. Reutiliza las firmas existentes.
3. JReleaser publica mediante el Portal y comprueba su resultado. CI además espera
   que el POM y ZIP sean descargables mediante `wait_for_maven_central.sh`.

El repositorio de staging está separado del repositorio local de dependencias.
Se sustituye Central Publishing 0.10.0 porque su instalador heredado incorpora
metadata local con Maven 3.10; la versión 0.11.0 conserva ese comportamiento.
No se limpian ni reempaquetan bundles con scripts. JReleaser administra el bundle
partiendo de artefactos desplegados mediante la API de Maven.
PomChecker conserva los errores como fallos. `strict=false` y `failOnWarning=false`
permiten los repositorios OpenMRS existentes, que el checker señala como avisos;
son necesarios para el plugin de empaquetado que no está publicado en Central.
`verifyPom=true` y `failOnError=true` conservan las comprobaciones obligatorias del POM.

Las credenciales existentes `CENTRAL_USERNAME` y `CENTRAL_PASSWORD` se proporcionan
al publicador mediante las variables `JRELEASER_MAVENCENTRAL_CENTRAL_USERNAME` y
`JRELEASER_MAVENCENTRAL_CENTRAL_PASSWORD`. `authorization=BASIC` indica al cliente
que construya el token Bearer del Portal a partir de ese par. La firma sigue usando
`GPG_PRIVATE_KEY` y `GPG_PASSPHRASE` en CI. El goal empleado es exclusivamente
`deploy`; no se ejecuta `full-release` ni se crean releases o tags de GitHub.

```sh
bash .github/scripts/test_maven_central_publication.sh --bundle
```

Esta regresión ejecuta el perfil real con el modo `dryRun` nativo de JReleaser y
una clave GPG efímera, sin claves de producción ni subidas. Comprueba que el bundle
contenga exactamente POM, ZIP, sus firmas válidas y los cuatro checksums; rechaza
archivos de metadata del repositorio. También retira el nombre de una copia del
POM en staging y exige que PomChecker rechace su publicación, comprobando que los
errores siguen bloqueando el flujo. Un ensayo local correcto no acredita una
publicación real: el job `publish` y la comprobación de descarga son obligatorios.

Para publicar fuera de CI, usar `./mvnw -P release clean deploy` con las mismas
variables de credenciales y el llavero de firma configurado; comprobar después
`.github/scripts/wait_for_maven_central.sh <version>`.

Referencias: [publicación con Maven y JReleaser](https://jreleaser.org/guide/latest/examples/maven/maven-central.html),
[configuración del Portal](https://jreleaser.org/guide/latest/reference/deploy/maven/maven-central.html)
y [cambios de Maven 3.10.0](https://maven.apache.org/docs/3.10.0/release-notes.html).

Después de que `publish` confirme el POM y ZIP en Maven Central, el mismo
workflow llama a `Validate with SIHSALUS` usando el mismo commit del paquete.
También valida si la versión ya estaba publicada; se omite si `publish` falla
o se omite. Conserva la ejecución manual y la entrada `sihsalus_ref`, con `main`
como referencia predeterminada del distro. Esta comprobación es posterior a la
publicación: un fallo no revierte el artefacto publicado.
