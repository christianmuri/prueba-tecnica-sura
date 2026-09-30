from datetime import date, timedelta

import numpy as np
import pandas as pd


# ============================================================
# PARÁMETROS DE LA SIMULACIÓN
# ============================================================

RANDOM_SEED = 42

N_REGISTROS_BASE = 1000
N_CLIENTES = 250

# Distribución Gamma para trabajadores activos
GAMMA_FORMA = 2
GAMMA_ESCALA = 20

# Valor simulado por trabajador
VALOR_UNITARIO_MIN = 30_000
VALOR_UNITARIO_MAX = 50_000


# ============================================================
# GENERACIÓN DE LA POBLACIÓN BASE VÁLIDA
# ============================================================

def generar_datos_base(
    fecha_ejecucion: date | None = None,
    seed: int = RANDOM_SEED
) -> pd.DataFrame:
    """
    Genera los 1.000 registros válidos utilizados como base
    de la simulación.

    Características:
    - 250 clientes representados al menos una vez.
    - La combinación id_cliente + periodo es única.
    - Los periodos se encuentran dentro de los últimos 60 días.
    - trabajadores_activos es un entero positivo.
    - valor_contrato se relaciona con el número de trabajadores.
    - La generación es reproducible mediante una semilla fija.
    """

    if fecha_ejecucion is None:
        fecha_ejecucion = date.today()

    rng = np.random.default_rng(seed)

    # --------------------------------------------------------
    # 1. Generar clientes
    # --------------------------------------------------------

    clientes = [
        f"CLI-{i}"
        for i in range(1, N_CLIENTES + 1)
    ]

    # Tamaño base de cada cliente.
    # La distribución Gamma permite representar una mayor
    # concentración de clientes pequeños y medianos, con
    # una cola hacia clientes de mayor tamaño.
    trabajadores_base = rng.gamma(
        shape=GAMMA_FORMA,
        scale=GAMMA_ESCALA,
        size=N_CLIENTES
    )

    trabajadores_base = np.maximum(
        1,
        np.rint(trabajadores_base).astype(int)
    )

    df_clientes = pd.DataFrame({
        "id_cliente": clientes,
        "trabajadores_base": trabajadores_base
    })

    # --------------------------------------------------------
    # 2. Generar periodos válidos
    # --------------------------------------------------------

    # Fecha de ejecución + los 60 días anteriores.
    fechas_validas = [
        fecha_ejecucion - timedelta(days=i)
        for i in range(61)
    ]

    # Todas las combinaciones posibles cliente + periodo.
    combinaciones = pd.MultiIndex.from_product(
        [clientes, fechas_validas],
        names=["id_cliente", "periodo"]
    ).to_frame(index=False)

    # --------------------------------------------------------
    # 3. Garantizar que los 250 clientes estén representados
    # --------------------------------------------------------

    indices_obligatorios = []

    for cliente in clientes:

        indices_cliente = combinaciones.index[
            combinaciones["id_cliente"] == cliente
        ].to_numpy()

        indice_seleccionado = rng.choice(
            indices_cliente
        )

        indices_obligatorios.append(
            indice_seleccionado
        )

    indices_obligatorios = np.array(
        indices_obligatorios
    )

    # Excluir las combinaciones ya seleccionadas.
    indices_disponibles = np.setdiff1d(
        combinaciones.index.to_numpy(),
        indices_obligatorios
    )

    # Completar los 1.000 registros.
    n_restantes = (
        N_REGISTROS_BASE
        - N_CLIENTES
    )

    indices_adicionales = rng.choice(
        indices_disponibles,
        size=n_restantes,
        replace=False
    )

    indices_seleccionados = np.concatenate([
        indices_obligatorios,
        indices_adicionales
    ])

    # Definir el orden inicial de la carga antes de crear
    # el identificador técnico.
    rng.shuffle(indices_seleccionados)

    df = (
        combinaciones
        .loc[indices_seleccionados]
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # 4. Asociar tamaño base del cliente
    # --------------------------------------------------------

    df = df.merge(
        df_clientes,
        on="id_cliente",
        how="left",
        validate="many_to_one"
    )

    # Pequeña variación del número de trabajadores entre
    # diferentes periodos del mismo cliente.
    variacion_trabajadores = rng.normal(
        loc=1.0,
        scale=0.10,
        size=len(df)
    )

    df["trabajadores_activos"] = np.maximum(
        1,
        np.rint(
            df["trabajadores_base"]
            * variacion_trabajadores
        ).astype(int)
    )

    # --------------------------------------------------------
    # 5. Generar valor del contrato
    # --------------------------------------------------------

    valor_unitario = rng.uniform(
        low=VALOR_UNITARIO_MIN,
        high=VALOR_UNITARIO_MAX,
        size=len(df)
    )

    df["valor_contrato"] = np.round(
        df["trabajadores_activos"]
        * valor_unitario,
        2
    )

    # --------------------------------------------------------
    # 6. Crear identificador técnico
    # --------------------------------------------------------

    df.insert(
        0,
        "id_registro",
        np.arange(
            1,
            len(df) + 1
        )
    )

    # trabajadores_base es una variable auxiliar utilizada
    # únicamente durante la generación.
    df = df.drop(
        columns=["trabajadores_base"]
    )

    # Formato preferido de entrada para periodo.
    df["periodo"] = pd.to_datetime(
        df["periodo"]
    ).dt.strftime("%d/%m/%Y")

    return df


def introducir_variaciones_estandarizables(
    df: pd.DataFrame,
    seed: int = RANDOM_SEED
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Introduce variaciones de representación que pueden ser
    estandarizadas sin modificar el significado del dato.

    Retorna:
    - DataFrame con las variaciones introducidas.
    - DataFrame de trazabilidad de las modificaciones realizadas.
    """

    rng = np.random.default_rng(seed)

    df_prueba = df.copy(deep=True)

    # valor_contrato debe permitir temporalmente valores de tipo texto,
    # ya que se simularán diferentes representaciones monetarias.
    df_prueba["valor_contrato"] = (
        df_prueba["valor_contrato"].astype(object)
    )

    # --------------------------------------------------------
    # Seleccionar 55 registros diferentes
    # --------------------------------------------------------

    indices = rng.choice(
        df_prueba.index.to_numpy(),
        size=55,
        replace=False
    )

    idx_id = indices[:15]
    idx_fecha_iso = indices[15:25]
    idx_fecha_guion = indices[25:35]
    idx_valor_latino = indices[35:45]
    idx_valor_internacional = indices[45:55]

    log_variaciones = []

    # --------------------------------------------------------
    # 1. id_cliente
    # --------------------------------------------------------

    for idx in idx_id:

        valor_original = df_prueba.at[
            idx,
            "id_cliente"
        ]

        numero_cliente = valor_original.split("-")[1]

        valor_modificado = (
            f" cli-{int(numero_cliente):05d} "
        )

        df_prueba.at[
            idx,
            "id_cliente"
        ] = valor_modificado

        log_variaciones.append({
            "id_registro":
                df_prueba.at[idx, "id_registro"],
            "variable":
                "id_cliente",
            "valor_original":
                valor_original,
            "valor_modificado":
                valor_modificado,
            "tipo_modificacion":
                "formato_estandarizable"
        })

    # --------------------------------------------------------
    # 2. periodo en formato YYYY-MM-DD
    # --------------------------------------------------------

    for idx in idx_fecha_iso:

        valor_original = df_prueba.at[
            idx,
            "periodo"
        ]

        fecha = pd.to_datetime(
            valor_original,
            format="%d/%m/%Y"
        )

        valor_modificado = fecha.strftime(
            "%Y-%m-%d"
        )

        df_prueba.at[
            idx,
            "periodo"
        ] = valor_modificado

        log_variaciones.append({
            "id_registro":
                df_prueba.at[idx, "id_registro"],
            "variable":
                "periodo",
            "valor_original":
                valor_original,
            "valor_modificado":
                valor_modificado,
            "tipo_modificacion":
                "formato_estandarizable"
        })

    # --------------------------------------------------------
    # 3. periodo en formato DD-MM-YYYY
    # --------------------------------------------------------

    for idx in idx_fecha_guion:

        valor_original = df_prueba.at[
            idx,
            "periodo"
        ]

        fecha = pd.to_datetime(
            valor_original,
            format="%d/%m/%Y"
        )

        valor_modificado = fecha.strftime(
            "%d-%m-%Y"
        )

        df_prueba.at[
            idx,
            "periodo"
        ] = valor_modificado

        log_variaciones.append({
            "id_registro":
                df_prueba.at[idx, "id_registro"],
            "variable":
                "periodo",
            "valor_original":
                valor_original,
            "valor_modificado":
                valor_modificado,
            "tipo_modificacion":
                "formato_estandarizable"
        })

    # --------------------------------------------------------
    # 4. valor_contrato en formato latino
    #    Ejemplo: 1.500.000,50
    # --------------------------------------------------------

    for idx in idx_valor_latino:

        valor_original = df_prueba.at[
            idx,
            "valor_contrato"
        ]

        valor_modificado = (
            f"{float(valor_original):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        df_prueba.at[
            idx,
            "valor_contrato"
        ] = valor_modificado

        log_variaciones.append({
            "id_registro":
                df_prueba.at[idx, "id_registro"],
            "variable":
                "valor_contrato",
            "valor_original":
                valor_original,
            "valor_modificado":
                valor_modificado,
            "tipo_modificacion":
                "formato_estandarizable"
        })

    # --------------------------------------------------------
    # 5. valor_contrato en formato internacional
    #    Ejemplo: 1,500,000.50
    # --------------------------------------------------------

    for idx in idx_valor_internacional:

        valor_original = df_prueba.at[
            idx,
            "valor_contrato"
        ]

        valor_modificado = (
            f"{float(valor_original):,.2f}"
        )

        df_prueba.at[
            idx,
            "valor_contrato"
        ] = valor_modificado

        log_variaciones.append({
            "id_registro":
                df_prueba.at[idx, "id_registro"],
            "variable":
                "valor_contrato",
            "valor_original":
                valor_original,
            "valor_modificado":
                valor_modificado,
            "tipo_modificacion":
                "formato_estandarizable"
        })

    df_log_variaciones = pd.DataFrame(
        log_variaciones
    )

    return df_prueba, df_log_variaciones



def introducir_errores_calidad(
    df: pd.DataFrame,
    df_base: pd.DataFrame,
    log_variaciones: pd.DataFrame,
    fecha_ejecucion: date | None = None,
    seed: int = 43
) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    """
    Introduce de forma controlada los errores de calidad definidos
    para Completitud, Validez, Consistencia y Oportunidad.

    Los registros utilizados para variaciones estandarizables se
    excluyen de esta etapa para mantenerlos como casos de control.

    Se generan:
    - 40 incidencias de Completitud.
    - 70 incidencias de Validez.
    - 10 incidencias de Consistencia.
    - 20 incidencias de Oportunidad.

    Se incluyen 10 solapamientos intencionales:
    - 5 registros: id_cliente nulo + valor_contrato negativo.
    - 5 registros: periodo futuro + inconsistencia.

    Por tanto:
    - 140 incidencias.
    - 130 registros distintos afectados.

    La función no modifica el número ni el orden de las filas.
    """

    if fecha_ejecucion is None:
        fecha_ejecucion = date.today()

    rng = np.random.default_rng(seed)

    df_error = df.copy(deep=True)

    # Permitir nulos y decimales en trabajadores_activos.
    df_error["trabajadores_activos"] = (
        df_error["trabajadores_activos"].astype(object)
    )

    # --------------------------------------------------------
    # 1. Calcular límite de plausibilidad usando la base limpia
    # --------------------------------------------------------

    valor_por_trabajador_base = (
        df_base["valor_contrato"]
        / df_base["trabajadores_activos"]
    )

    limite_plausibilidad = (
        valor_por_trabajador_base.mean()
        + 3 * valor_por_trabajador_base.std()
    )

    # --------------------------------------------------------
    # 2. Excluir registros con variaciones estandarizables
    # --------------------------------------------------------

    ids_variaciones = set(
        log_variaciones["id_registro"].tolist()
    )

    indices_disponibles = df_error.index[
        ~df_error["id_registro"].isin(ids_variaciones)
    ].to_numpy()

    # Necesitamos 130 registros distintos.
    indices_seleccionados = rng.choice(
        indices_disponibles,
        size=130,
        replace=False
    )

    # Función auxiliar para ir tomando posiciones
    # sin repetirlas accidentalmente.
    posicion = 0

    def tomar_indices(n: int) -> np.ndarray:
        nonlocal posicion

        resultado = indices_seleccionados[
            posicion: posicion + n
        ]

        posicion += n

        return resultado

    # --------------------------------------------------------
    # 3. Distribuir los índices
    # --------------------------------------------------------

    # Solapamiento 1:
    # id_cliente nulo + valor_contrato negativo.
    idx_id_null_y_contrato_negativo = tomar_indices(5)

    # Otros 5 para completar los 10 id_cliente nulos.
    idx_id_null = tomar_indices(5)

    # Otros 5 para completar los 10 contratos negativos.
    idx_contrato_negativo = tomar_indices(5)

    # Solapamiento 2:
    # periodo futuro + inconsistencia.
    idx_futuro_y_consistencia = tomar_indices(5)

    # Otros 5 para completar los 10 periodos futuros.
    idx_periodo_futuro = tomar_indices(5)

    # Otros 5 para completar las 10 inconsistencias.
    idx_consistencia = tomar_indices(5)

    # Completitud
    idx_periodo_null = tomar_indices(10)
    idx_contrato_null = tomar_indices(10)
    idx_trabajadores_null = tomar_indices(10)

    # Validez
    idx_id_invalido = tomar_indices(10)
    idx_fecha_inexistente = tomar_indices(10)
    idx_fecha_no_interpretable = tomar_indices(10)
    idx_plausibilidad = tomar_indices(10)
    idx_trabajadores_negativos = tomar_indices(10)
    idx_trabajadores_decimales = tomar_indices(10)

    # Oportunidad
    idx_periodo_antiguo = tomar_indices(10)

    # --------------------------------------------------------
    # 4. Log de errores inyectados
    # --------------------------------------------------------

    errores_inyectados = []

    def registrar_error(
        idx,
        criterio,
        variable,
        codigo_regla,
        descripcion,
        valor_original,
        valor_inyectado
    ):
        errores_inyectados.append({
            "id_registro":
                df_error.at[idx, "id_registro"],
            "criterio":
                criterio,
            "variable":
                variable,
            "codigo_regla":
                codigo_regla,
            "descripcion":
                descripcion,
            "valor_original":
                valor_original,
            "valor_inyectado":
                valor_inyectado
        })

    # ========================================================
    # COMPLETITUD
    # ========================================================

    # --------------------------------------------------------
    # COM_001 - id_cliente nulo
    # --------------------------------------------------------

    indices = np.concatenate([
        idx_id_null_y_contrato_negativo,
        idx_id_null
    ])

    for idx in indices:

        original = df_error.at[idx, "id_cliente"]

        df_error.at[idx, "id_cliente"] = pd.NA

        registrar_error(
            idx=idx,
            criterio="Completitud",
            variable="id_cliente",
            codigo_regla="COM_001",
            descripcion="Campo obligatorio ausente",
            valor_original=original,
            valor_inyectado=None
        )

    # --------------------------------------------------------
    # COM_002 - periodo nulo
    # --------------------------------------------------------

    for idx in idx_periodo_null:

        original = df_error.at[idx, "periodo"]

        df_error.at[idx, "periodo"] = pd.NA

        registrar_error(
            idx=idx,
            criterio="Completitud",
            variable="periodo",
            codigo_regla="COM_002",
            descripcion="Campo obligatorio ausente",
            valor_original=original,
            valor_inyectado=None
        )

    # --------------------------------------------------------
    # COM_003 - valor_contrato nulo
    # --------------------------------------------------------

    for idx in idx_contrato_null:

        original = df_error.at[idx, "valor_contrato"]

        df_error.at[idx, "valor_contrato"] = pd.NA

        registrar_error(
            idx=idx,
            criterio="Completitud",
            variable="valor_contrato",
            codigo_regla="COM_003",
            descripcion="Campo obligatorio ausente",
            valor_original=original,
            valor_inyectado=None
        )

    # --------------------------------------------------------
    # COM_004 - trabajadores_activos nulo
    # --------------------------------------------------------

    for idx in idx_trabajadores_null:

        original = df_error.at[
            idx,
            "trabajadores_activos"
        ]

        df_error.at[
            idx,
            "trabajadores_activos"
        ] = pd.NA

        registrar_error(
            idx=idx,
            criterio="Completitud",
            variable="trabajadores_activos",
            codigo_regla="COM_004",
            descripcion="Campo obligatorio ausente",
            valor_original=original,
            valor_inyectado=None
        )

    # ========================================================
    # VALIDEZ
    # ========================================================

    # --------------------------------------------------------
    # VAL_001 - id_cliente inválido
    # --------------------------------------------------------

    for idx in idx_id_invalido:

        original = df_error.at[idx, "id_cliente"]

        nuevo = "CLI-12A5"

        df_error.at[idx, "id_cliente"] = nuevo

        registrar_error(
            idx=idx,
            criterio="Validez",
            variable="id_cliente",
            codigo_regla="VAL_001",
            descripcion=(
                "El identificador no cumple el formato "
                "CLI-<entero positivo>"
            ),
            valor_original=original,
            valor_inyectado=nuevo
        )

    # --------------------------------------------------------
    # VAL_002 - fecha inexistente
    # --------------------------------------------------------

    for idx in idx_fecha_inexistente:

        original = df_error.at[idx, "periodo"]

        nuevo = "31/02/2026"

        df_error.at[idx, "periodo"] = nuevo

        registrar_error(
            idx=idx,
            criterio="Validez",
            variable="periodo",
            codigo_regla="VAL_002",
            descripcion=(
                "La fecha no existe en el calendario"
            ),
            valor_original=original,
            valor_inyectado=nuevo
        )

    # --------------------------------------------------------
    # VAL_003 - fecha no interpretable
    # --------------------------------------------------------

    for idx in idx_fecha_no_interpretable:

        original = df_error.at[idx, "periodo"]

        nuevo = "fecha_desconocida"

        df_error.at[idx, "periodo"] = nuevo

        registrar_error(
            idx=idx,
            criterio="Validez",
            variable="periodo",
            codigo_regla="VAL_003",
            descripcion=(
                "El valor no puede interpretarse como fecha"
            ),
            valor_original=original,
            valor_inyectado=nuevo
        )

    # --------------------------------------------------------
    # VAL_004 - valor_contrato negativo
    # --------------------------------------------------------

    indices = np.concatenate([
        idx_id_null_y_contrato_negativo,
        idx_contrato_negativo
    ])

    for idx in indices:

        original = float(
            df_base.at[idx, "valor_contrato"]
        )

        nuevo = -abs(original)

        df_error.at[idx, "valor_contrato"] = nuevo

        registrar_error(
            idx=idx,
            criterio="Validez",
            variable="valor_contrato",
            codigo_regla="VAL_004",
            descripcion=(
                "El valor del contrato no puede ser negativo"
            ),
            valor_original=original,
            valor_inyectado=nuevo
        )

    # --------------------------------------------------------
    # VAL_005 - valor por trabajador fuera de plausibilidad
    # --------------------------------------------------------

    for idx in idx_plausibilidad:

        original = float(
            df_base.at[idx, "valor_contrato"]
        )

        # Simula un cero adicional de digitación.
        nuevo = round(
            original * 10,
            2
        )

        df_error.at[idx, "valor_contrato"] = nuevo

        registrar_error(
            idx=idx,
            criterio="Validez",
            variable="valor_contrato",
            codigo_regla="VAL_005",
            descripcion=(
                "El valor por trabajador supera "
                "el límite de plausibilidad"
            ),
            valor_original=original,
            valor_inyectado=nuevo
        )

    # --------------------------------------------------------
    # VAL_006 - trabajadores negativos
    # --------------------------------------------------------

    for idx in idx_trabajadores_negativos:

        original = int(
            df_base.at[idx, "trabajadores_activos"]
        )

        nuevo = -abs(original)

        df_error.at[
            idx,
            "trabajadores_activos"
        ] = nuevo

        registrar_error(
            idx=idx,
            criterio="Validez",
            variable="trabajadores_activos",
            codigo_regla="VAL_006",
            descripcion=(
                "El número de trabajadores no puede ser negativo"
            ),
            valor_original=original,
            valor_inyectado=nuevo
        )

    # --------------------------------------------------------
    # VAL_007 - trabajadores decimales
    # --------------------------------------------------------

    for idx in idx_trabajadores_decimales:

        original = int(
            df_base.at[idx, "trabajadores_activos"]
        )

        nuevo = original + 0.5

        df_error.at[
            idx,
            "trabajadores_activos"
        ] = nuevo

        registrar_error(
            idx=idx,
            criterio="Validez",
            variable="trabajadores_activos",
            codigo_regla="VAL_007",
            descripcion=(
                "El número de trabajadores debe ser entero"
            ),
            valor_original=original,
            valor_inyectado=nuevo
        )

    # ========================================================
    # CONSISTENCIA
    # ========================================================

    indices = np.concatenate([
        idx_futuro_y_consistencia,
        idx_consistencia
    ])

    for idx in indices:

        contrato = float(
            df_base.at[idx, "valor_contrato"]
        )

        trabajadores_originales = int(
            df_base.at[idx, "trabajadores_activos"]
        )

        df_error.at[
            idx,
            "trabajadores_activos"
        ] = 0

        registrar_error(
            idx=idx,
            criterio="Consistencia",
            variable=(
                "valor_contrato + "
                "trabajadores_activos"
            ),
            codigo_regla="CON_001",
            descripcion=(
                "valor_contrato > 0 requiere "
                "trabajadores_activos > 0"
            ),
            valor_original=(
                f"valor_contrato={contrato}; "
                f"trabajadores_activos="
                f"{trabajadores_originales}"
            ),
            valor_inyectado=(
                f"valor_contrato={contrato}; "
                f"trabajadores_activos=0"
            )
        )

    # ========================================================
    # OPORTUNIDAD
    # ========================================================

    # --------------------------------------------------------
    # OPO_001 - periodo futuro
    # --------------------------------------------------------

    indices = np.concatenate([
        idx_futuro_y_consistencia,
        idx_periodo_futuro
    ])

    for idx in indices:

        original = df_error.at[idx, "periodo"]

        dias_futuro = int(
            rng.integers(1, 31)
        )

        nueva_fecha = (
            fecha_ejecucion
            + timedelta(days=dias_futuro)
        )

        nuevo = nueva_fecha.strftime(
            "%d/%m/%Y"
        )

        df_error.at[idx, "periodo"] = nuevo

        registrar_error(
            idx=idx,
            criterio="Oportunidad",
            variable="periodo",
            codigo_regla="OPO_001",
            descripcion="Periodo posterior a la fecha de ejecución",
            valor_original=original,
            valor_inyectado=nuevo
        )

    # --------------------------------------------------------
    # OPO_002 - periodo con antigüedad > 60 días
    # --------------------------------------------------------

    for idx in idx_periodo_antiguo:

        original = df_error.at[idx, "periodo"]

        dias_antiguedad = int(
            rng.integers(61, 121)
        )

        nueva_fecha = (
            fecha_ejecucion
            - timedelta(days=dias_antiguedad)
        )

        nuevo = nueva_fecha.strftime(
            "%d/%m/%Y"
        )

        df_error.at[idx, "periodo"] = nuevo

        registrar_error(
            idx=idx,
            criterio="Oportunidad",
            variable="periodo",
            codigo_regla="OPO_002",
            descripcion=(
                "Periodo con antigüedad superior a 60 días"
            ),
            valor_original=original,
            valor_inyectado=nuevo
        )

    # --------------------------------------------------------
    # Construir log final
    # --------------------------------------------------------

    df_errores_inyectados = pd.DataFrame(
        errores_inyectados
    )

    return (
        df_error,
        df_errores_inyectados,
        limite_plausibilidad
    )

def introducir_duplicados_unicidad(
    df: pd.DataFrame,
    log_variaciones: pd.DataFrame,
    log_errores: pd.DataFrame,
    seed: int = 44
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Introduce problemas de Unicidad agregando 20 registros nuevos:

    - 10 duplicados exactos.
    - 10 registros con la misma llave id_cliente + periodo,
      pero con valores diferentes en otros campos.

    Los registros originales utilizados se seleccionan únicamente
    entre filas que no presentan otras variaciones ni errores.

    Tanto el registro original como el registro agregado se
    consideran afectados por Unicidad.
    """

    rng = np.random.default_rng(seed)

    df_resultado = df.copy(deep=True)

    # --------------------------------------------------------
    # 1. Excluir registros previamente modificados
    # --------------------------------------------------------

    ids_variaciones = set(
        log_variaciones["id_registro"].tolist()
    )

    ids_errores = set(
        log_errores["id_registro"].tolist()
    )

    ids_excluidos = (
        ids_variaciones
        | ids_errores
    )

    candidatos = df_resultado[
        ~df_resultado["id_registro"].isin(
            ids_excluidos
        )
    ].copy()

    # Seleccionar 20 registros originales diferentes.
    indices_seleccionados = rng.choice(
        candidatos.index.to_numpy(),
        size=20,
        replace=False
    )

    idx_duplicados_exactos = (
        indices_seleccionados[:10]
    )

    idx_duplicados_diferentes = (
        indices_seleccionados[10:]
    )

    nuevos_registros = []
    errores_unicidad = []

    siguiente_id = (
        int(df_resultado["id_registro"].max())
        + 1
    )

    # --------------------------------------------------------
    # Función auxiliar para registrar la incidencia
    # --------------------------------------------------------

    def registrar_unicidad(
        id_registro,
        codigo_regla,
        descripcion,
        valor_llave
    ):
        errores_unicidad.append({
            "id_registro": id_registro,
            "criterio": "Unicidad",
            "variable": "id_cliente + periodo",
            "codigo_regla": codigo_regla,
            "descripcion": descripcion,
            "valor_original": valor_llave,
            "valor_inyectado": valor_llave
        })

    # ========================================================
    # 2. DUPLICADOS EXACTOS
    # ========================================================

    for idx in idx_duplicados_exactos:

        registro_original = (
            df_resultado.loc[idx].copy()
        )

        id_original = int(
            registro_original["id_registro"]
        )

        id_nuevo = siguiente_id
        siguiente_id += 1

        registro_nuevo = (
            registro_original.copy()
        )

        registro_nuevo["id_registro"] = (
            id_nuevo
        )

        nuevos_registros.append(
            registro_nuevo
        )

        llave = (
            f"{registro_original['id_cliente']} | "
            f"{registro_original['periodo']}"
        )

        # El original también queda afectado.
        registrar_unicidad(
            id_registro=id_original,
            codigo_regla="UNI_001",
            descripcion=(
                "Duplicado exacto para la combinación "
                "id_cliente + periodo"
            ),
            valor_llave=llave
        )

        # Y también el nuevo registro.
        registrar_unicidad(
            id_registro=id_nuevo,
            codigo_regla="UNI_001",
            descripcion=(
                "Duplicado exacto para la combinación "
                "id_cliente + periodo"
            ),
            valor_llave=llave
        )

    # ========================================================
    # 3. MISMA LLAVE CON VALORES DIFERENTES
    # ========================================================

    for idx in idx_duplicados_diferentes:

        registro_original = (
            df_resultado.loc[idx].copy()
        )

        id_original = int(
            registro_original["id_registro"]
        )

        id_nuevo = siguiente_id
        siguiente_id += 1

        registro_nuevo = (
            registro_original.copy()
        )

        registro_nuevo["id_registro"] = (
            id_nuevo
        )

        # Se modifica valor_contrato manteniendo el mismo
        # id_cliente y periodo.
        #
        # Un incremento del 5 % conserva el valor dentro de
        # un rango plausible para los registros base.
        valor_original = float(
            registro_original["valor_contrato"]
        )

        registro_nuevo["valor_contrato"] = round(
            valor_original * 1.05,
            2
        )

        nuevos_registros.append(
            registro_nuevo
        )

        llave = (
            f"{registro_original['id_cliente']} | "
            f"{registro_original['periodo']}"
        )

        # Original afectado.
        registrar_unicidad(
            id_registro=id_original,
            codigo_regla="UNI_002",
            descripcion=(
                "Llave id_cliente + periodo duplicada "
                "con diferencias en otros campos"
            ),
            valor_llave=llave
        )

        # Nuevo registro afectado.
        registrar_unicidad(
            id_registro=id_nuevo,
            codigo_regla="UNI_002",
            descripcion=(
                "Llave id_cliente + periodo duplicada "
                "con diferencias en otros campos"
            ),
            valor_llave=llave
        )

    # --------------------------------------------------------
    # 4. Agregar nuevas filas al final de la carga
    # --------------------------------------------------------

    df_nuevos = pd.DataFrame(
        nuevos_registros
    )

    df_resultado = pd.concat(
        [
            df_resultado,
            df_nuevos
        ],
        ignore_index=True
    )

    df_errores_unicidad = pd.DataFrame(
        errores_unicidad
    )

    return (
        df_resultado,
        df_errores_unicidad
    )
