# Sección 4 — Tablero de monitoreo

Dashboard interactivo desarrollado para el monitoreo de casos, costos e incidencia sobre trabajadores activos.

Los datos utilizados son sintéticos y se generan directamente dentro de `app.py`, sin depender de archivos externos.

---

## Ejecución rápida

Desde la raíz del proyecto:

```bash
python -m pip install -r requirements.txt
```

Ejecutar el tablero:

```bash
python -m streamlit run seccion_4/app.py
```

Abrir en el navegador la dirección indicada por Streamlit, normalmente:

```text
http://localhost:8501
```

---

## Objetivo

Construir un tablero ligero que permita a un coordinador consultar de forma sencilla el comportamiento de los casos registrados, su impacto económico y su incidencia sobre la población de trabajadores activos.

El tablero fue diseñado para responder tanto a una consulta general como a diferentes contextos de análisis mediante filtros interactivos.

---

## Herramientas seleccionadas

Se utilizó **Streamlit** para construir la aplicación y **Plotly** para las visualizaciones.

### Streamlit

Se seleccionó porque permite desarrollar aplicaciones analíticas interactivas directamente en Python, sin requerir licencias adicionales y manteniendo en un mismo entorno la generación de datos, la lógica de negocio, los filtros y la presentación.

### Plotly

Se utilizó para construir visualizaciones interactivas, principalmente la tendencia temporal y la distribución de casos.

Esta combinación permite ejecutar el tablero localmente con una configuración mínima.

---

## Datos sintéticos

Toda la información es generada dentro de `app.py`.

Se simulan tres años completos:

```text
01/01/2024 → 31/12/2026
```

La simulación contiene:

- 30 clientes.
- Clases de riesgo entre 1 y 5.
- Trabajadores asociados a cada cliente.
- Evolución mensual de trabajadores activos.
- Casos leves y graves.
- Días de ausencia.
- Costos asociados a los casos.
- Facturación mensual.
- Actividades de prevención.

Se utiliza una semilla fija:

```python
SEED = 42
```

Esto permite obtener los mismos resultados en cada ejecución.

---

## Criterios de generación

Los datos no se generan de forma completamente independiente. Se definieron relaciones entre las variables para mantener coherencia dentro de la simulación.

### Clientes y trabajadores

Los clientes se distribuyen entre diferentes sectores y clases de riesgo.

Cada cliente tiene una plantilla inicial de trabajadores que evoluciona durante los 36 meses mediante variaciones controladas.

Las altas y retiros se gestionan de forma que sea posible validar qué trabajadores estaban activos en cada momento.

### Casos

La cantidad esperada de casos depende de:

```text
Trabajadores activos
        +
Clase de riesgo
        ↓
Número esperado de casos
```

El número mensual de casos se genera mediante una distribución de Poisson.

Las clases de riesgo superiores presentan una mayor tasa esperada de ocurrencia.

### Gravedad

La probabilidad de que un caso sea grave aumenta con la clase de riesgo.

Los casos se clasifican como:

```text
Leve
Grave
```

### Días de ausencia y costo

Los días de ausencia dependen del tipo de caso.

Los casos graves presentan, en promedio, una mayor cantidad de días de ausencia.

El costo se genera utilizando:

```text
Tipo de caso
      +
Días de ausencia
      ↓
Costo estimado
```

Por tanto, los casos graves tienden a producir un mayor impacto económico.

### Facturación

La tabla de facturación contiene una fila por cliente y mes.

El valor del contrato depende principalmente de:

```text
Trabajadores activos
        +
Clase de riesgo
        +
Factor anual
```

### Prevención

Las actividades preventivas dependen del tamaño del cliente y, moderadamente, de su clase de riesgo.

La cantidad de participantes nunca puede superar la cantidad de trabajadores activos del cliente en el periodo correspondiente.

La prevención no se utiliza para reducir automáticamente la ocurrencia de casos, evitando introducir una relación causal artificial en los datos sintéticos.

---

## Indicadores principales

El tablero presenta los tres indicadores solicitados.

### Total de casos

Número de casos registrados dentro del periodo seleccionado.

### Costo total

Suma del costo asociado a los casos registrados dentro del periodo seleccionado.

### Tasa de incidencia

Número de casos registrados por cada 100 trabajadores activos.

Se calcula como:

```text
Tasa de incidencia =
(Número de casos / Trabajadores activos) × 100
```

Para periodos que abarcan varios meses no se suman directamente los trabajadores activos mensuales, ya que esto contabilizaría repetidamente la misma población.

Se utiliza una plantilla promedio expuesta durante el periodo analizado.

---

## Comparación con periodo anterior

Cada indicador se compara automáticamente con el periodo inmediatamente anterior equivalente.

| Periodo seleccionado | Comparación |
|---|---|
| Día | Día anterior |
| Semana | Semana anterior |
| Mes | Mes anterior |
| Año | Año anterior |

Para total de casos y costo se calcula la variación porcentual.

Para la tasa de incidencia se muestra la diferencia en puntos de tasa.

Cuando el periodo anterior no se encuentra dentro del histórico disponible, la comparación no se muestra.

De igual forma, cuando el valor anterior es cero y no es posible calcular una variación porcentual válida, la variación se deja en blanco.

---

## Filtros

Los filtros actualizan los indicadores y visualizaciones del tablero.

### Pregunta de análisis

Se incorporó un selector orientado a preguntas de negocio:

```text
Panorama general
Impacto de los casos graves
Clientes de mayor riesgo
Clientes de menor riesgo
```

Cada opción corresponde a una regla aplicada sobre los datos.

Por ejemplo:

```text
Impacto de los casos graves
→ tipo = Grave
```

```text
Clientes de mayor riesgo
→ clase de riesgo = 4 o 5
```

```text
Clientes de menor riesgo
→ clase de riesgo = 1 o 2
```

### Periodo

El usuario puede seleccionar:

```text
Día
Semana
Mes
Año
```

La aplicación calcula automáticamente el rango correspondiente y su periodo anterior.

Las semanas se consideran de lunes a domingo.

### Cliente

Es posible analizar:

```text
Todos los clientes
```

o seleccionar un cliente específico.

Todos los componentes del tablero responden a este filtro.

---

## Visualizaciones

### Tendencia mensual de casos

Se muestran los últimos 12 meses hasta el periodo seleccionado.

La visualización incluye:

- Número de casos de cada mes.
- Línea de referencia del promedio histórico mensual.

El promedio histórico utiliza la información disponible desde enero de 2024.

Cuando el periodo seleccionado corresponde a un mes parcial, la aplicación evita utilizar información posterior a la fecha seleccionada.

---

### Top 10 clientes

Se muestra una tabla con los clientes que presentan el mayor número de casos dentro del periodo y contexto seleccionado.

La tabla incluye:

```text
Cliente
Número de casos
Clase de riesgo
```

Cuando se selecciona un cliente específico, la tabla responde al mismo filtro aplicado al resto del tablero.

---

### Distribución de casos

Se presenta la cantidad de casos:

```text
Leves
Graves
```

para cada clase de riesgo:

```text
1
2
3
4
5
```

Esto permite observar simultáneamente la frecuencia y gravedad de los casos según el nivel de riesgo.

---

## Validaciones implementadas

Durante la generación se realizan controles automáticos para garantizar consistencia entre las tablas.

Entre las principales validaciones se encuentran:

- 30 clientes generados.
- 36 periodos mensuales por cliente.
- Unicidad de identificadores.
- Relaciones válidas entre clientes, trabajadores y casos.
- Un trabajador no puede tener un caso antes de su fecha de ingreso.
- Un trabajador retirado no puede recibir casos posteriores a su retiro.
- Los trabajadores activos mensuales siempre son mayores que cero.
- La facturación conserva exactamente la cantidad de trabajadores activos definida para cada cliente y periodo.
- Los participantes de una actividad preventiva no pueden superar la plantilla activa.
- Los casos graves presentan rangos de ausencia diferentes a los casos leves.
- Las fechas se mantienen dentro del periodo de simulación.

---

## Modelo de información generado

La aplicación construye cinco tablas principales:

```text
clientes
trabajadores
casos
facturacion
prevencion
```

Relaciones principales:

```text
clientes
   │
   ├── 1:N ── trabajadores
   │             │
   │             └── 1:N ── casos
   │
   ├── 1:N ── casos
   │
   ├── 1:N ── facturacion
   │
   └── 1:N ── prevencion
```

---

## Organización del código

El código se encuentra organizado en funciones separadas para:

```text
Generación de datos
Validación
Cálculo de periodos
Aplicación de filtros
Cálculo de KPI
Preparación de visualizaciones
Formato
Construcción del dashboard
```

Esto permite separar la generación de datos de la lógica analítica y de la presentación.

---

## Conexión con un Lakehouse en producción

En un ambiente productivo, la generación sintética de información sería reemplazada por una capa de acceso a datos conectada al Lakehouse.

Las tablas de:

```text
clientes
trabajadores
casos
facturacion
prevencion
```

podrían obtenerse mediante consultas SQL o mediante el conector disponible en la plataforma donde se encuentre implementado el Lakehouse.

La estructura podría seguir el siguiente flujo:

```text
Lakehouse
   ↓
Consultas / capa de acceso
   ↓
DataFrames
   ↓
Funciones de transformación y cálculo
   ↓
Indicadores y visualizaciones
   ↓
Streamlit
```

La lógica de negocio desarrollada para filtros, periodos, indicadores y visualizaciones podría mantenerse prácticamente sin cambios siempre que las tablas obtenidas del Lakehouse respeten el esquema esperado.

De esta manera se mantiene separada la capa de almacenamiento de la lógica analítica y de la presentación del tablero.

---

## Estructura de la sección

```text
seccion_4/
├── app.py
└── README.md
```

Las dependencias se encuentran centralizadas en el archivo:

```text
requirements.txt
```

ubicado en la raíz del proyecto.