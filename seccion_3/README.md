# Sección 3 — Python: automatización y validación de calidad del dato

## Ejercicio 3.1 — Validación de calidad del dato

### 1. Objetivo

Desarrollar un proceso automatizado en Python para validar la calidad de un archivo de facturación antes de su ingreso al pipeline de datos.

La solución simula el procesamiento de una nueva carga de información y evalúa cada registro mediante cinco dimensiones de calidad:

- **Completitud:** verificación de campos obligatorios sin valores nulos.
- **Validez:** validación de formatos y rangos esperados.
- **Unicidad:** detección de duplicados por cliente y período.
- **Consistencia:** validación de reglas lógicas entre variables.
- **Oportunidad:** validación de la vigencia temporal de los registros.

Como resultado del proceso, los registros se clasifican en válidos o rechazados. Para los registros rechazados se conserva la razón del rechazo, permitiendo identificar las reglas de calidad incumplidas.

Adicionalmente, el proceso genera un reporte consolidado de calidad y exporta los registros válidos y rechazados en los formatos definidos para la entrega.

### 2. Alcance

La solución desarrollada para este ejercicio contempla:

- Generación de un archivo de prueba con más de 1.000 registros de facturación, incluyendo problemas de calidad introducidos de forma intencional.
- Lectura y preparación de la información para su validación.
- Evaluación de los registros mediante las dimensiones de completitud, validez, unicidad, consistencia y oportunidad.
- Identificación de las reglas de calidad incumplidas por cada registro.
- Clasificación de los registros en válidos y rechazados.
- Generación de un reporte consolidado de calidad en formato JSON.
- Exportación de los registros válidos en formato Parquet.
- Exportación de los registros rechazados en formato Excel, incluyendo la razón del rechazo.
- Manejo de errores durante la ejecución para evitar fallos no controlados del proceso.

La solución representa la etapa de control de calidad previa al ingreso de una nueva carga al pipeline de datos. No contempla la integración con un orquestador, base de datos o plataforma de procesamiento productiva.

### 3. Criterio de estandarización y rechazo

Antes de ejecutar las reglas de calidad, el proceso aplica estandarizaciones controladas sobre aquellos valores cuya transformación sea determinística y no altere el significado del dato.

Por ejemplo, formatos de fecha reconocidos o espacios adicionales en identificadores pueden llevarse a una representación estándar cuando su interpretación sea inequívoca.

Cuando la transformación requiera inferir, adivinar o corregir el contenido del dato, el registro no es modificado y se rechaza mediante la regla de calidad correspondiente.

En términos generales:

- **Estandarizar:** cuando la transformación es determinística y conserva el significado original.
- **Rechazar:** cuando sería necesario inferir o corregir el contenido del dato.

Los valores originales se conservan para mantener trazabilidad sobre la información recibida.

### 4. Contrato de datos

El archivo de entrada simula una carga de información de facturación y contiene las variables necesarias para ejecutar las reglas de calidad definidas en el ejercicio.

| Campo | Descripción | Tipo esperado |
|---|---|---|
| `id_cliente` | Identificador del cliente asociado al registro | Texto |
| `periodo` | Fecha correspondiente al período informado | Fecha |
| `valor_contrato` | Valor económico asociado al contrato | Numérico |
| `trabajadores_activos` | Número de trabajadores activos asociados al contrato | Entero |

Adicionalmente, durante el procesamiento se genera un `id_registro` como identificador técnico de cada fila. Este campo no forma parte de las reglas de calidad del negocio y se utiliza únicamente para mantener trazabilidad durante la validación y el reporte de rechazos.

#### `id_cliente`

Identificador del cliente asociado al registro.

- **Tipo esperado:** texto.
- **Formato estándar:** `CLI-<n>`, donde `<n>` corresponde a un entero positivo.
- **Ejemplos válidos:** `CLI-1`, `CLI-25`, `CLI-1250`, `CLI-9845231`.
- **Campo obligatorio:** sí.

El prefijo `CLI-` identifica la entidad como cliente. La parte numérica no tiene una longitud fija y debe corresponder a un entero positivo.

Antes de validar el formato se permiten únicamente estandarizaciones que no modifican el significado del identificador:

- eliminación de espacios al inicio y al final;
- conversión de caracteres alfabéticos a mayúsculas;
- eliminación de ceros a la izquierda en la parte numérica.

Ejemplo:

`" cli-00125 "` → `CLI-125`

No se agregan prefijos ni caracteres faltantes. Cuando el identificador no puede llevarse al formato estándar sin inferir información, el registro se rechaza por **Validez**.

Los valores nulos se rechazan por **Completitud**.

#### `periodo`

Fecha correspondiente al período informado en el registro.

- **Tipo esperado:** fecha.
- **Formato esperado de entrada:** `DD/MM/YYYY`.
- **Formato estándar interno:** `YYYY-MM-DD`.
- **Ejemplo de entrada válida:** `29/09/2026`.
- **Campo obligatorio:** sí.

Cuando el valor recibido corresponde de manera inequívoca al formato `DD/MM/YYYY`, el proceso lo convierte al formato estándar `YYYY-MM-DD` para su procesamiento interno.

No se interpretan formatos ambiguos ni se corrigen fechas inexistentes. Por ejemplo, valores como `31/02/2026` se rechazan por **Validez**.

Los valores nulos se rechazan por **Completitud**.

Una vez validada y estandarizada la fecha, se evalúa la dimensión de **Oportunidad**. Para ello, la `fecha_ejecucion` corresponde a la fecha del sistema en el momento en que se ejecuta el proceso.

El período debe cumplir la siguiente condición:

`fecha_ejecucion - 60 días <= periodo <= fecha_ejecucion`

Por lo tanto:

- un período posterior a la fecha de ejecución se rechaza por **Oportunidad: período futuro**;
- un período con más de 60 días de antigüedad se rechaza por **Oportunidad: antigüedad superior a 60 días**.


#### `valor_contrato`

Valor económico asociado al contrato.

- **Tipo esperado:** numérico.
- **Valores permitidos:** enteros o decimales.
- **Campo obligatorio:** sí.
- **Regla mínima:** el valor debe ser mayor o igual a cero.

El proceso admite representaciones numéricas que puedan interpretarse de forma inequívoca y las estandariza a una representación numérica común antes de ejecutar las validaciones.

Por ejemplo, pueden presentarse valores con separadores de miles y decimales en diferentes convenciones, siempre que su interpretación sea determinística.

Ejemplos de representaciones equivalentes:

- `1500000`
- `1500000.50`
- `1.500.000,50`
- `1,500,000.50`

Todos pueden representar el mismo valor económico y deben estandarizarse antes de la validación.

Cuando una representación sea ambigua y no pueda interpretarse de forma segura sin inferir información, el registro se rechaza por **Validez**.

Los valores nulos se rechazan por **Completitud**.

Los valores negativos se rechazan por **Validez**.

Adicionalmente, se implementa un control de plausibilidad para detectar valores cuya magnitud sea inconsistente con el número de trabajadores asociados al contrato.

Cuando `trabajadores_activos > 0`, se calcula el valor del contrato por trabajador:

`valor_por_trabajador = valor_contrato / trabajadores_activos`

El límite superior de referencia se obtiene a partir de los 1.000 registros válidos generados antes de introducir los errores intencionales:

`limite_superior = media(valor_por_trabajador) + 3 * desviacion_estandar(valor_por_trabajador)`

Posteriormente, algunos registros son modificados intencionalmente para generar valores por trabajador superiores a este límite y comprobar el funcionamiento de la regla de validación.

Este enfoque evita considerar automáticamente como incorrecto un contrato de alto valor únicamente por su magnitud absoluta, ya que un contrato mayor puede ser coherente cuando se encuentra asociado a un mayor número de trabajadores.

El control busca representar situaciones como errores de digitación en los que el valor mantiene un formato numérico correcto, pero contiene un cero o un dígito adicional y genera un monto desproporcionado frente al número de trabajadores asociados.

El umbral se calcula utilizando la población válida de referencia antes de introducir los errores intencionales, evitando que los propios valores extremos modifiquen la media y la desviación estándar utilizadas para definir el límite.

Esta regla de plausibilidad se evalúa únicamente cuando `trabajadores_activos > 0`. Cuando `trabajadores_activos = 0`, la relación entre ambas variables se analiza mediante la regla de **Consistencia**.

Este criterio corresponde a un supuesto estadístico de la simulación y no representa una regla real de negocio de SURA. En un entorno productivo, los rangos de plausibilidad deberían definirse utilizando información histórica, reglas de negocio y características del cliente.

#### `trabajadores_activos`

Número de trabajadores activos asociados al contrato.

- **Tipo esperado:** entero.
- **Valor mínimo permitido:** `0`.
- **Campo obligatorio:** sí.

El campo representa un conteo, por lo que únicamente se permiten números enteros mayores o iguales a cero.

Las representaciones textuales de enteros pueden estandarizarse cuando su interpretación sea inequívoca.

Ejemplos:

- `"25"` → `25`
- `" 25 "` → `25`
- `"005"` → `5`

No se admiten valores decimales, negativos ni representaciones cuya interpretación requiera inferir información. Estos casos se rechazan por **Validez**.

Los valores nulos se rechazan por **Completitud**.

Adicionalmente, el campo participa en la regla de **Consistencia** definida para el ejercicio:

`si valor_contrato > 0, entonces trabajadores_activos > 0`

Por lo tanto, un valor de `0` puede ser válido individualmente, pero el registro será rechazado por **Consistencia** cuando exista un `valor_contrato` mayor que cero.


### 5. Reglas de calidad

#### 5.1 Completitud

La dimensión de completitud verifica que los campos obligatorios del registro contengan información.

Para este ejercicio, los campos obligatorios son:

- `id_cliente`
- `periodo`
- `valor_contrato`
- `trabajadores_activos`

Un registro incumple la regla de **Completitud** cuando al menos uno de estos campos contiene un valor nulo o ausente.

La validación de completitud se realiza antes de las reglas que dependen del contenido del campo, con el fin de evitar interpretar o procesar valores inexistentes.

Ejemplo:

| id_cliente | periodo | valor_contrato | trabajadores_activos | Resultado |
|---|---|---:|---:|---|
| `CLI-125` | `29/09/2026` | `2500000` | `10` | Cumple |
| `NULL` | `29/09/2026` | `2500000` | `10` | Rechazo por Completitud |
| `CLI-125` | `NULL` | `2500000` | `10` | Rechazo por Completitud |

Cuando un registro presenta más de un campo obligatorio ausente, se conservan todos los incumplimientos detectados para mantener trazabilidad sobre las causas del rechazo.

#### 5.2 Validez

La dimensión de validez verifica que los valores informados cumplan los tipos, formatos y rangos definidos en el contrato de datos.

Antes de evaluar esta dimensión, el proceso puede aplicar estandarizaciones controladas cuando la transformación sea determinística y no modifique el significado del dato. Cuando sea necesario inferir o corregir el contenido, el valor se considera inválido.

Las reglas de validez son las siguientes:

##### `id_cliente`

Debe cumplir el formato:

`CLI-<n>`

donde `<n>` corresponde a un entero positivo.

Ejemplos válidos:

- `CLI-1`
- `CLI-125`
- `CLI-9845231`

Se permiten estandarizaciones como eliminación de espacios externos, conversión a mayúsculas y eliminación de ceros a la izquierda en la parte numérica.

Ejemplo:

`" cli-00125 "` → `CLI-125`

Valores como `CLI-0`, `CLI--5`, `CLI-12A5` o `EMP-125` se rechazan por **Validez**.

##### `periodo`

El formato esperado de entrada es:

`DD/MM/YYYY`

El valor debe corresponder a una fecha calendario existente y debe poder interpretarse de forma inequívoca.

Ejemplos:

- `29/09/2026` → válido.
- `31/02/2026` → inválido.
- `2026/09/29` → inválido por no cumplir el formato definido.
- `texto` → inválido.

Las fechas válidas se estandarizan internamente al formato `YYYY-MM-DD`.

La vigencia temporal del período no se evalúa en esta dimensión, sino posteriormente mediante la regla de **Oportunidad**.

##### `valor_contrato`

Debe corresponder a un valor numérico mayor o igual a cero.

Se permiten valores enteros o decimales y representaciones monetarias cuya interpretación pueda determinarse de forma inequívoca.

Por ejemplo:

- `1500000`
- `1500000.50`
- `1.500.000,50`
- `1,500,000.50`

pueden estandarizarse a una representación numérica común.

Las representaciones ambiguas o no numéricas se rechazan por **Validez**.

Además, se aplica un control de plausibilidad para identificar valores excepcionalmente altos dentro de la simulación.

El límite superior se calcula a partir de los valores de `valor_contrato` de los 1.000 registros válidos utilizados como población de referencia, antes de introducir los errores intencionales:

`limite_superior = media(valor_contrato) + 3 * desviacion_estandar(valor_contrato)`

Posteriormente, algunos registros son modificados intencionalmente con valores superiores a este límite para comprobar el funcionamiento de la regla de validación.

El umbral se calcula antes de contaminar los datos, evitando que los valores extremos introducidos artificialmente incrementen la media y la desviación estándar y desplacen el límite de detección.

Este criterio se utiliza como supuesto estadístico para la simulación y no implica que, en un entorno productivo, todo valor superior a tres desviaciones estándar deba considerarse incorrecto. En un escenario real, el rango esperado debería definirse utilizando información histórica, reglas de negocio y, cuando corresponda, métodos estadísticos robustos o límites diferenciados según las características del cliente.

##### `trabajadores_activos`

Debe corresponder a un número entero mayor o igual a cero.

Ejemplos válidos:

- `0`
- `15`
- `"25"` → `25`
- `"005"` → `5`

Se rechazan por **Validez**:

- valores negativos;
- valores decimales;
- valores no numéricos;
- representaciones que requieran inferir información para ser interpretadas.

Un valor de `0` es válido individualmente. Su relación con `valor_contrato` se evalúa posteriormente mediante la regla de **Consistencia**.

##### Registro de incumplimientos

Un mismo registro puede incumplir más de una regla de validez. El proceso conserva todos los incumplimientos detectados con el fin de mantener trazabilidad sobre las causas del rechazo.


#### 5.3 Unicidad

La dimensión de unicidad verifica que no existan múltiples registros para una misma combinación de cliente y período.

La llave definida para esta validación es:

`id_cliente + periodo`

La evaluación se realiza sobre los valores previamente estandarizados, con el fin de evitar que diferencias únicamente de representación oculten registros duplicados.

Por ejemplo:

- `" cli-00125 "` + `29/09/2026`
- `CLI-125` + `29/09/2026`

después de la estandarización corresponden a la misma llave:

`CLI-125` + `2026-09-29`

y, por lo tanto, incumplen la regla de **Unicidad**.

Cuando una misma combinación de `id_cliente` y `periodo` aparece más de una vez, todos los registros asociados a esa llave se marcan como rechazados por **Unicidad**. No se conserva automáticamente uno de los registros, ya que no existe una regla de negocio que permita determinar cuál de ellos debe prevalecer.

Adicionalmente, para mejorar la trazabilidad del rechazo, los duplicados se clasifican en:

- **Duplicado exacto:** la combinación `id_cliente + periodo` está repetida y los demás valores del registro también son iguales.
- **Duplicado por llave con valores diferentes:** la combinación `id_cliente + periodo` está repetida, pero existen diferencias en uno o más de los demás campos.

Ambos casos representan un incumplimiento de la regla de **Unicidad**.

La validación de unicidad se aplica únicamente cuando `id_cliente` y `periodo` pueden ser interpretados y estandarizados correctamente. Los registros con valores nulos o inválidos en estos campos son tratados por las dimensiones de **Completitud** o **Validez**, según corresponda.

#### 5.4 Consistencia

La dimensión de consistencia verifica que exista coherencia lógica entre `valor_contrato` y `trabajadores_activos`.

La regla definida para el ejercicio es:

`si valor_contrato > 0, entonces trabajadores_activos > 0`

Por lo tanto, cuando existe un valor de contrato positivo, debe existir al menos un trabajador activo asociado al registro.

Ejemplos:

| valor_contrato | trabajadores_activos | Resultado |
|---:|---:|---|
| `5000000` | `10` | Cumple |
| `5000000` | `0` | Rechazo por Consistencia |
| `0` | `0` | Cumple la regla definida |
| `0` | `10` | No incumple la regla definida |

La regla proporcionada para el ejercicio es una implicación en una sola dirección:

`valor_contrato > 0 → trabajadores_activos > 0`

Por tanto, no se asume automáticamente la regla inversa.

Un registro con `valor_contrato = 0` y `trabajadores_activos > 0` no se rechaza con las reglas actualmente definidas. Sin embargo, se considera un caso que debería ser revisado con el área de negocio para determinar si corresponde a una situación válida o si es necesario incorporar una regla adicional de consistencia.

Esta distinción busca evitar la creación de reglas de rechazo no sustentadas, manteniendo al mismo tiempo una postura crítica frente a patrones de información que pueden requerir validación funcional.

La validación de consistencia se ejecuta únicamente cuando ambos campos contienen valores válidos que permiten evaluar la relación.

Los valores nulos son tratados previamente por **Completitud**, mientras que los valores que incumplen el contrato de datos son tratados por **Validez**.

#### 5.5 Oportunidad

La dimensión de oportunidad verifica que el `periodo` informado se encuentre dentro de la ventana temporal permitida para la carga.

La referencia para esta validación es la `fecha_ejecucion`, correspondiente a la fecha del sistema en el momento en que se ejecuta el proceso.

El período debe cumplir la siguiente condición:

`fecha_ejecucion - 60 días <= periodo <= fecha_ejecucion`

Por lo tanto, se consideran oportunos los registros cuyo período se encuentre entre la fecha de ejecución y los 60 días anteriores, incluyendo ambos límites.

Ejemplo: si el proceso se ejecuta el `29/09/2026`, el rango permitido es:

`31/07/2026 <= periodo <= 29/09/2026`

Ejemplos:

| periodo | Resultado |
|---|---|
| `29/09/2026` | Cumple |
| `15/09/2026` | Cumple |
| `31/07/2026` | Cumple |
| `30/07/2026` | Rechazo por Oportunidad: antigüedad superior a 60 días |
| `30/09/2026` | Rechazo por Oportunidad: período futuro |

Para mejorar la trazabilidad, los incumplimientos de oportunidad se diferencian en:

- **Período futuro:** `periodo > fecha_ejecucion`.
- **Período fuera de vigencia:** `periodo < fecha_ejecucion - 60 días`.

La validación de oportunidad se realiza únicamente cuando `periodo` contiene una fecha válida que pudo ser interpretada y estandarizada correctamente.

Los valores nulos son tratados previamente por **Completitud**, mientras que las fechas inexistentes o con formatos no permitidos son tratadas por **Validez**.

### 6. Registro de rechazos y trazabilidad

El proceso evalúa todas las reglas de calidad que puedan aplicarse a cada registro y conserva todos los incumplimientos detectados.

Un único incumplimiento es suficiente para clasificar un registro como rechazado. Sin embargo, el proceso continúa evaluando las reglas independientes que puedan aplicarse con el fin de obtener un diagnóstico completo de la calidad de la información.

Las reglas que dependen de otras variables se ejecutan únicamente cuando dichas variables están presentes y han superado las validaciones necesarias para poder ser interpretadas correctamente.

Por ejemplo, si `periodo` es nulo:

- se registra un incumplimiento de **Completitud**;
- no se evalúa **Oportunidad**, porque no existe una fecha válida;
- no se evalúa **Unicidad** para esa fila, porque no puede construirse completamente la llave `id_cliente + periodo`;
- las validaciones independientes de `valor_contrato` y `trabajadores_activos` continúan ejecutándose.

#### Estructura de los registros rechazados

El archivo `registros_rechazados.xlsx` contiene dos hojas con diferentes niveles de granularidad.

##### Hoja `registros_rechazados`

Contiene una fila por registro rechazado y conserva los valores recibidos en la carga junto con su identificador técnico `id_registro`.

Esta hoja permite conocer qué registros no superaron el control de calidad y conservar la información original para su posterior revisión.

##### Hoja `detalle_rechazos`

Contiene una fila por cada incumplimiento detectado.

Su estructura incluye:

| Campo | Descripción |
|---|---|
| `id_registro` | Identificador técnico del registro afectado |
| `criterio` | Dimensión de calidad incumplida |
| `variable` | Variable o combinación de variables involucradas |
| `codigo_regla` | Código único de la regla incumplida |
| `descripcion` | Explicación específica del motivo del rechazo |
| `valor_original` | Valor recibido que originó el incumplimiento, cuando aplique |

Ejemplo:

| id_registro | criterio | variable | codigo_regla | descripcion | valor_original |
|---:|---|---|---|---|---|
| `250` | Completitud | `id_cliente` | `COM_001` | Campo obligatorio ausente | `NULL` |
| `250` | Validez | `periodo` | `VAL_002` | Fecha inexistente | `31/02/2026` |
| `250` | Validez | `valor_contrato` | `VAL_003` | Valor negativo | `-500000` |

Este diseño evita almacenar múltiples criterios o motivos concatenados en una misma celda y permite analizar posteriormente la calidad de los datos mediante herramientas de BI.

A partir de `detalle_rechazos` pueden responderse preguntas como:

- ¿Qué variables presentan más incumplimientos?
- ¿Qué dimensiones de calidad generan más rechazos?
- ¿Cuáles son las reglas que fallan con mayor frecuencia?
- ¿Cuántos registros presentan problemas en más de una dimensión?
- ¿Qué tipo de error se presenta con mayor frecuencia en cada variable?

Cuando una regla involucra más de una variable, el campo `variable` conserva la combinación evaluada. Por ejemplo:

- Unicidad: `id_cliente + periodo`.
- Consistencia: `valor_contrato + trabajadores_activos`.

Los valores originales se conservan durante el procesamiento para mantener trazabilidad sobre la información recibida y sobre las estandarizaciones aplicadas.

### 7. Generación de datos sintéticos

Para la construcción de los datos de prueba se parte internamente de una base de **1.000 registros válidos**. Esta base se utiliza únicamente como punto de partida para controlar la generación de los casos de prueba y no constituye un archivo adicional de entrega.

Posteriormente, sobre estos registros se introducen de forma controlada diferentes problemas de calidad requeridos por el ejercicio, entre ellos:

- identificadores con formatos inconsistentes;
- períodos con problemas de formato o validez;
- valores negativos;
- valores nulos en campos obligatorios;
- inconsistencias entre variables;
- períodos fuera de la ventana de oportunidad;
- duplicados por la combinación `id_cliente + periodo`.

Los registros afectados se seleccionan de forma pseudoaleatoria utilizando una semilla fija, lo que permite distribuir los errores a lo largo de la carga y, al mismo tiempo, reproducir la simulación en ejecuciones posteriores.

La introducción de errores **no modifica el orden de los registros existentes**. El `id_registro` técnico conserva la secuencia de ingreso y permite mantener la trazabilidad durante todo el proceso.

Algunos problemas de calidad pueden generarse modificando los registros existentes. Por ejemplo, un valor nulo, un valor negativo o un período futuro puede introducirse sobre cualquiera de los 1.000 registros iniciales.

En otros casos, como la validación de **Unicidad**, pueden agregarse nuevas observaciones que repitan una combinación existente de `id_cliente + periodo`. Estas nuevas filas reciben un nuevo `id_registro` consecutivo y representan registros que ingresaron posteriormente a la carga.

Por esta razón, el conjunto de datos final puede contener más de 1.000 registros. El número de filas adicionales no representa la cantidad total de registros con problemas de calidad, ya que una parte de los errores se encuentra distribuida dentro de los 1.000 registros iniciales.

Adicionalmente, se incorporan algunas variaciones de formato que son estandarizables y que no deben producir rechazo. Esto permite comprobar que el proceso diferencia entre una representación diferente del dato y un incumplimiento real de calidad.

#### 7.1 Generación de la población base válida

La simulación parte de 1.000 registros que cumplen inicialmente todas las reglas de calidad definidas.

Se utiliza una semilla fija (`RANDOM_SEED = 42`) para garantizar la reproducibilidad de la generación de datos y de la posterior selección de registros que serán modificados.

##### Clientes

Se generan 250 clientes identificados mediante el formato:

`CLI-<n>`

donde `<n>` corresponde a un entero positivo.

Un mismo cliente puede aparecer en diferentes períodos. Sin embargo, en la población base se garantiza que la combinación:

`id_cliente + periodo`

sea única.

##### Períodos

Los períodos se generan dentro de la ventana de oportunidad definida:

`fecha_ejecucion - 60 días <= periodo <= fecha_ejecucion`

Las combinaciones de cliente y período se seleccionan sin reemplazo, evitando duplicados accidentales antes de introducir los errores intencionales.

##### Trabajadores activos

Para representar una población en la que existan principalmente clientes pequeños y medianos y un menor número de clientes de mayor tamaño, se utiliza una distribución Gamma para generar el número base de trabajadores por cliente.

Conceptualmente:

`trabajadores_base_cliente ~ Gamma(forma = 2, escala = 20)`

Los valores se convierten a enteros positivos.

Cuando un mismo cliente aparece en diferentes períodos, su número de trabajadores puede presentar pequeñas variaciones respecto a su tamaño base, evitando generar cambios excesivos entre registros consecutivos del mismo cliente.

##### Valor del contrato

El valor del contrato se genera en función del número de trabajadores activos, de manera que exista una relación razonable entre ambas variables.

Para cada registro se genera un valor unitario por trabajador alrededor de $40.000. Este valor corresponde únicamente a un parámetro de simulación y no representa una tarifa real de negocio.

Para introducir variabilidad, el valor unitario se genera dentro de un intervalo definido alrededor de dicho valor de referencia.

Posteriormente:

`valor_contrato = trabajadores_activos * valor_unitario`

De esta manera, los contratos de mayor valor pueden estar asociados naturalmente a clientes con un mayor número de trabajadores, evitando generar montos completamente independientes del tamaño del cliente.

#### 7.2 Introducción controlada de variaciones y errores

Una vez generados los 1.000 registros válidos de referencia, se introducen de forma controlada diferentes variaciones y problemas de calidad.

La selección de los registros que serán modificados se realiza de forma pseudoaleatoria utilizando la semilla definida para la simulación. Las modificaciones no alteran el orden original de los registros ni su `id_registro`.

Se distinguen dos tipos de modificaciones:

1. Variaciones de representación que pueden estandarizarse sin modificar el significado del dato.
2. Incumplimientos reales de las reglas de calidad que deben generar rechazo.

##### Variaciones estandarizables

Estas modificaciones permiten comprobar que el proceso diferencia entre un formato distinto y un dato realmente inválido.

| Variable | Variación introducida | Cantidad | Resultado esperado |
|---|---|---:|---|
| `id_cliente` | Espacios externos, minúsculas y ceros a la izquierda, por ejemplo `" cli-00125 "` | 15 | Estandarización, sin rechazo |
| `periodo` | Formato `YYYY-MM-DD` | 10 | Estandarización, sin rechazo |
| `periodo` | Formato `DD-MM-YYYY` | 10 | Estandarización, sin rechazo |
| `valor_contrato` | Formato monetario latino, por ejemplo `1.500.000,50` | 10 | Estandarización, sin rechazo |
| `valor_contrato` | Formato monetario internacional, por ejemplo `1,500,000.50` | 10 | Estandarización, sin rechazo |

Estas variaciones no se consideran incumplimientos de calidad siempre que puedan interpretarse de forma determinística.

##### Problemas de Completitud

| Problema introducido | Cantidad |
|---|---:|
| `id_cliente = NULL` | 10 |
| `periodo = NULL` | 10 |
| `valor_contrato = NULL` | 10 |
| `trabajadores_activos = NULL` | 10 |

##### Problemas de Validez

| Problema introducido | Cantidad |
|---|---:|
| `id_cliente` con formato no interpretable | 10 |
| Fecha inexistente | 10 |
| Fecha no interpretable | 10 |
| `valor_contrato < 0` | 10 |
| Valor por trabajador superior al límite de plausibilidad | 10 |
| `trabajadores_activos < 0` | 10 |
| `trabajadores_activos` decimal | 10 |

##### Problemas de Consistencia

Se generan 10 registros en los que:

`valor_contrato > 0`

y simultáneamente:

`trabajadores_activos = 0`

Estos registros deben ser rechazados por **Consistencia**.

##### Problemas de Oportunidad

| Problema introducido | Cantidad |
|---|---:|
| `periodo > fecha_ejecucion` | 10 |
| `periodo < fecha_ejecucion - 60 días` | 10 |

##### Problemas de Unicidad

Para probar la dimensión de Unicidad se agregan nuevas observaciones después de los 1.000 registros iniciales.

| Caso | Registros adicionales |
|---|---:|
| Duplicado exacto | 10 |
| Misma combinación `id_cliente + periodo` con diferencias en otros campos | 10 |

Por lo tanto, la carga final contiene:

`1.000 registros iniciales + 20 registros adicionales = 1.020 registros`

Las 20 filas adicionales no representan la totalidad de los registros con problemas de calidad. Los demás incumplimientos se encuentran distribuidos dentro de los 1.000 registros iniciales.

##### Registros con múltiples incumplimientos

Para comprobar que el proceso puede identificar más de una causa de rechazo en un mismo registro, algunos errores se introducen deliberadamente sobre las mismas observaciones.

Se definen los siguientes casos:

- 5 registros presentan simultáneamente `id_cliente = NULL` y `valor_contrato < 0`.
- 5 registros presentan simultáneamente un `periodo` futuro y `trabajadores_activos = 0`, manteniendo `valor_contrato > 0`.

De esta forma, un mismo registro puede generar incumplimientos correspondientes a diferentes dimensiones de calidad.

La existencia de estos solapamientos implica que la cantidad total de incidencias detectadas no necesariamente coincide con la cantidad de registros rechazados.