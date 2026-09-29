import re

import numpy as np
import pandas as pd


# ============================================================
# ESTANDARIZACIÓN DE CAMPOS
# ============================================================

def estandarizar_id_cliente(valor):
    """
    Estandariza id_cliente cuando la transformación es
    determinística.

    Ejemplos:
        " cli-00125 " -> "CLI-125"
        "CLI-25"      -> "CLI-25"

    Si el valor está ausente o no puede interpretarse de forma
    segura, devuelve pd.NA.
    """

    if pd.isna(valor):
        return pd.NA

    valor = str(valor).strip().upper()

    coincidencia = re.fullmatch(
        r"CLI-(\d+)",
        valor
    )

    if coincidencia is None:
        return pd.NA

    numero_cliente = int(
        coincidencia.group(1)
    )
    if numero_cliente <= 0:
        return pd.NA

    return f"CLI-{numero_cliente}"

def estandarizar_periodo(valor):
    """
    Interpreta únicamente formatos de fecha conocidos y
    determinísticos.

    Formatos aceptados:
        DD/MM/YYYY
        YYYY-MM-DD
        DD-MM-YYYY

    Devuelve pd.Timestamp si puede interpretarse.
    Devuelve pd.NaT si el valor está ausente o no es válido.
    """

    if pd.isna(valor):
        return pd.NaT

    valor = str(valor).strip()

    formatos_aceptados = [
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d-%m-%Y"
    ]

    for formato in formatos_aceptados:

        fecha = pd.to_datetime(
            valor,
            format=formato,
            errors="coerce"
        )

        if not pd.isna(fecha):
            return fecha

    return pd.NaT

def estandarizar_valor_contrato(valor):
    """
    Convierte representaciones monetarias conocidas a float.

    Ejemplos aceptados:
        1500000
        1500000.50
        "1.500.000,50"
        "1,500,000.50"

    Si el valor no puede interpretarse de forma determinística,
    devuelve np.nan.
    """

    if pd.isna(valor):
        return np.nan

    # Si ya es numérico, no requiere transformación textual.
    if isinstance(
        valor,
        (int, float, np.integer, np.floating)
    ):
        return float(valor)

    valor = str(valor).strip()

    # --------------------------------------------------------
    # Número simple:
    # 1500000
    # 1500000.50
    # -1500000.50
    # --------------------------------------------------------

    if re.fullmatch(
        r"[+-]?\d+(?:\.\d+)?",
        valor
    ):
        return float(valor)

    # --------------------------------------------------------
    # Formato latino:
    # 1.500.000,50
    # --------------------------------------------------------

    if re.fullmatch(
        r"[+-]?\d{1,3}(?:\.\d{3})+,\d{2}",
        valor
    ):
        valor_convertido = (
            valor
            .replace(".", "")
            .replace(",", ".")
        )

        return float(valor_convertido)

    # --------------------------------------------------------
    # Formato internacional:
    # 1,500,000.50
    # --------------------------------------------------------

    if re.fullmatch(
        r"[+-]?\d{1,3}(?:,\d{3})+\.\d{2}",
        valor
    ):
        valor_convertido = (
            valor.replace(",", "")
        )

        return float(valor_convertido)

    return np.nan

def estandarizar_trabajadores_activos(valor):
    """
    Convierte representaciones determinísticas de trabajadores
    a valor numérico.

    Ejemplos:
        25       -> 25
        25.0     -> 25
        "25"     -> 25
        " 25 "   -> 25
        "005"    -> 5

    Los valores decimales reales, como 25.5, se conservan como
    número para que posteriormente Validez determine que no son
    enteros.

    Los valores no interpretables devuelven np.nan.
    """

    if pd.isna(valor):
        return np.nan

    if isinstance(
        valor,
        (int, float, np.integer, np.floating)
    ):
        return float(valor)

    valor = str(valor).strip()

    if re.fullmatch(
        r"[+-]?\d+(?:\.\d+)?",
        valor
    ):
        return float(valor)

    return np.nan

def preparar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera una copia de la carga original y añade columnas
    estandarizadas para las validaciones posteriores.

    Las columnas originales no se modifican para conservar
    trazabilidad.
    """

    df_preparado = df.copy(deep=True)

    df_preparado["id_cliente_std"] = (
        df_preparado["id_cliente"]
        .apply(estandarizar_id_cliente)
    )

    df_preparado["periodo_std"] = (
        df_preparado["periodo"]
        .apply(estandarizar_periodo)
    )

    df_preparado["valor_contrato_std"] = (
        df_preparado["valor_contrato"]
        .apply(estandarizar_valor_contrato)
    )

    df_preparado["trabajadores_activos_std"] = (
        df_preparado["trabajadores_activos"]
        .apply(
            estandarizar_trabajadores_activos
        )
    )

    return df_preparado

# ============================================================
# VALIDACIÓN DE COMPLETITUD
# ============================================================

REGLAS_COMPLETITUD = {
    "id_cliente": {
        "codigo": "COM_001",
        "descripcion": "Campo obligatorio ausente"
    },
    "periodo": {
        "codigo": "COM_002",
        "descripcion": "Campo obligatorio ausente"
    },
    "valor_contrato": {
        "codigo": "COM_003",
        "descripcion": "Campo obligatorio ausente"
    },
    "trabajadores_activos": {
        "codigo": "COM_004",
        "descripcion": "Campo obligatorio ausente"
    }
}


def validar_completitud(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Valida que los cuatro campos obligatorios estén presentes.

    Se revisan los valores originales, no las columnas
    estandarizadas, para no confundir ausencia con un valor
    presente pero inválido.

    Retorna una fila por cada incumplimiento encontrado.
    """

    incidencias = []

    for variable, regla in REGLAS_COMPLETITUD.items():

        mascara_nulos = df[variable].isna()

        registros_nulos = df.loc[
            mascara_nulos,
            ["id_registro", variable]
        ]

        for _, fila in registros_nulos.iterrows():

            incidencias.append({
                "id_registro":
                    int(fila["id_registro"]),

                "criterio":
                    "Completitud",

                "variable":
                    variable,

                "codigo_regla":
                    regla["codigo"],

                "descripcion":
                    regla["descripcion"],

                "valor_original":
                    None
            })

    return pd.DataFrame(
        incidencias,
        columns=[
            "id_registro",
            "criterio",
            "variable",
            "codigo_regla",
            "descripcion",
            "valor_original"
        ]
    )

# ============================================================
# VALIDACIÓN DE VALIDEZ
# ============================================================

def validar_validez(
    df: pd.DataFrame,
    limite_plausibilidad: float
) -> pd.DataFrame:
    """
    Valida formato, tipo y rango de los campos.

    Las reglas dependientes solo se evalúan cuando los valores
    necesarios están presentes y son interpretables.

    Retorna una fila por cada incumplimiento encontrado.
    """

    incidencias = []

    def registrar_incidencia(
        fila,
        variable,
        codigo_regla,
        descripcion
    ):
        incidencias.append({
            "id_registro":
                int(fila["id_registro"]),

            "criterio":
                "Validez",

            "variable":
                variable,

            "codigo_regla":
                codigo_regla,

            "descripcion":
                descripcion,

            "valor_original":
                fila[variable]
        })

    # ========================================================
    # VAL_001 - id_cliente inválido
    # ========================================================

    mascara = (
        df["id_cliente"].notna()
        &
        df["id_cliente_std"].isna()
    )

    for _, fila in df.loc[mascara].iterrows():

        registrar_incidencia(
            fila=fila,
            variable="id_cliente",
            codigo_regla="VAL_001",
            descripcion=(
                "El identificador no cumple el formato "
                "CLI-<entero positivo>"
            )
        )

    # ========================================================
    # VAL_002 / VAL_003 - periodo inválido
    # ========================================================

    mascara_periodo_invalido = (
        df["periodo"].notna()
        &
        df["periodo_std"].isna()
    )

    for _, fila in df.loc[
        mascara_periodo_invalido
    ].iterrows():

        valor = str(
            fila["periodo"]
        ).strip()

        # Si tiene estructura de uno de los formatos conocidos,
        # pero no pudo convertirse, se interpreta como una
        # fecha inexistente.
        patron_fecha = (
            r"(?:"
            r"\d{2}/\d{2}/\d{4}"
            r"|"
            r"\d{4}-\d{2}-\d{2}"
            r"|"
            r"\d{2}-\d{2}-\d{4}"
            r")"
        )

        if re.fullmatch(
            patron_fecha,
            valor
        ):
            codigo = "VAL_002"

            descripcion = (
                "La fecha no existe en el calendario"
            )

        else:
            codigo = "VAL_003"

            descripcion = (
                "El valor no puede interpretarse como fecha"
            )

        registrar_incidencia(
            fila=fila,
            variable="periodo",
            codigo_regla=codigo,
            descripcion=descripcion
        )

    # ========================================================
    # VAL_004 - valor_contrato negativo
    # ========================================================

    mascara = (
        df["valor_contrato"].notna()
        &
        df["valor_contrato_std"].notna()
        &
        (
            df["valor_contrato_std"] < 0
        )
    )

    for _, fila in df.loc[mascara].iterrows():

        registrar_incidencia(
            fila=fila,
            variable="valor_contrato",
            codigo_regla="VAL_004",
            descripcion=(
                "El valor del contrato no puede ser negativo"
            )
        )

    # ========================================================
    # VAL_005 - valor por trabajador no plausible
    # ========================================================

    mascara_evaluable = (
        df["valor_contrato_std"].notna()
        &
        df["trabajadores_activos_std"].notna()
        &
        (
            df["valor_contrato_std"] >= 0
        )
        &
        (
            df["trabajadores_activos_std"] > 0
        )
        &
        (
            df["trabajadores_activos_std"] % 1 == 0
        )
    )

    valor_por_trabajador = pd.Series(
        np.nan,
        index=df.index
    )

    valor_por_trabajador.loc[
        mascara_evaluable
    ] = (
        df.loc[
            mascara_evaluable,
            "valor_contrato_std"
        ]
        /
        df.loc[
            mascara_evaluable,
            "trabajadores_activos_std"
        ]
    )

    mascara = (
        mascara_evaluable
        &
        (
            valor_por_trabajador
            > limite_plausibilidad
        )
    )

    for _, fila in df.loc[mascara].iterrows():

        registrar_incidencia(
            fila=fila,
            variable="valor_contrato",
            codigo_regla="VAL_005",
            descripcion=(
                "El valor por trabajador supera "
                "el límite de plausibilidad"
            )
        )

    # ========================================================
    # VAL_006 - trabajadores_activos negativos
    # ========================================================

    mascara = (
        df["trabajadores_activos"].notna()
        &
        df["trabajadores_activos_std"].notna()
        &
        (
            df["trabajadores_activos_std"] < 0
        )
    )

    for _, fila in df.loc[mascara].iterrows():

        registrar_incidencia(
            fila=fila,
            variable="trabajadores_activos",
            codigo_regla="VAL_006",
            descripcion=(
                "El número de trabajadores no puede ser negativo"
            )
        )

    # ========================================================
    # VAL_007 - trabajadores_activos decimal
    # ========================================================

    mascara = (
        df["trabajadores_activos"].notna()
        &
        df["trabajadores_activos_std"].notna()
        &
        (
            df["trabajadores_activos_std"] >= 0
        )
        &
        (
            df["trabajadores_activos_std"] % 1 != 0
        )
    )

    for _, fila in df.loc[mascara].iterrows():

        registrar_incidencia(
            fila=fila,
            variable="trabajadores_activos",
            codigo_regla="VAL_007",
            descripcion=(
                "El número de trabajadores debe ser entero"
            )
        )

    return pd.DataFrame(
        incidencias,
        columns=[
            "id_registro",
            "criterio",
            "variable",
            "codigo_regla",
            "descripcion",
            "valor_original"
        ]
    )

# ============================================================
# VALIDACIÓN DE UNICIDAD
# ============================================================

def validar_unicidad(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Valida que la combinación id_cliente + periodo sea única.

    La regla se evalúa únicamente cuando ambos componentes
    de la llave están presentes y son válidos.

    Se distinguen dos situaciones:

    UNI_001:
        Duplicado exacto en los campos de negocio.

    UNI_002:
        Misma llave id_cliente + periodo, pero con diferencias
        en otros campos.

    Todos los registros involucrados en una llave duplicada
    son rechazados.
    """

    incidencias = []

    # --------------------------------------------------------
    # 1. Determinar registros evaluables
    # --------------------------------------------------------

    mascara_evaluable = (
        df["id_cliente"].notna()
        &
        df["periodo"].notna()
        &
        df["id_cliente_std"].notna()
        &
        df["periodo_std"].notna()
    )

    df_evaluable = df.loc[
        mascara_evaluable
    ].copy()

    # --------------------------------------------------------
    # 2. Detectar llaves duplicadas
    # --------------------------------------------------------

    mascara_duplicados = (
        df_evaluable.duplicated(
            subset=[
                "id_cliente_std",
                "periodo_std"
            ],
            keep=False
        )
    )

    df_duplicados = df_evaluable.loc[
        mascara_duplicados
    ].copy()

    # --------------------------------------------------------
    # 3. Analizar cada llave duplicada
    # --------------------------------------------------------

    grupos = df_duplicados.groupby(
        [
            "id_cliente_std",
            "periodo_std"
        ],
        dropna=False
    )

    for (
        id_cliente,
        periodo
    ), grupo in grupos:

        # Campos de negocio distintos de la llave.
        columnas_comparacion = [
            "valor_contrato_std",
            "trabajadores_activos_std"
        ]

        # Si existe una única combinación de valores entre
        # todos los registros del grupo, es duplicado exacto.
        combinaciones_distintas = (
            grupo[columnas_comparacion]
            .drop_duplicates()
        )

        if len(combinaciones_distintas) == 1:

            codigo_regla = "UNI_001"

            descripcion = (
                "Duplicado exacto para la combinación "
                "id_cliente + periodo"
            )

        else:

            codigo_regla = "UNI_002"

            descripcion = (
                "Llave id_cliente + periodo duplicada "
                "con diferencias en otros campos"
            )

        valor_llave = (
            f"{id_cliente} | "
            f"{periodo.strftime('%Y-%m-%d')}"
        )

        # Todos los registros de la llave quedan afectados.
        for _, fila in grupo.iterrows():

            incidencias.append({
                "id_registro":
                    int(fila["id_registro"]),

                "criterio":
                    "Unicidad",

                "variable":
                    "id_cliente + periodo",

                "codigo_regla":
                    codigo_regla,

                "descripcion":
                    descripcion,

                "valor_original":
                    valor_llave
            })

    return pd.DataFrame(
        incidencias,
        columns=[
            "id_registro",
            "criterio",
            "variable",
            "codigo_regla",
            "descripcion",
            "valor_original"
        ]
    )

# ============================================================
# VALIDACIÓN DE CONSISTENCIA
# ============================================================

def validar_consistencia(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Valida la relación lógica entre valor_contrato y
    trabajadores_activos.

    Regla:
        Si valor_contrato > 0,
        entonces trabajadores_activos > 0.

    La regla solo se evalúa cuando ambos campos están presentes,
    son interpretables y cumplen sus condiciones individuales
    básicas de validez.
    """

    incidencias = []

    # --------------------------------------------------------
    # 1. Determinar registros evaluables
    # --------------------------------------------------------

    mascara_evaluable = (
        df["valor_contrato"].notna()
        &
        df["trabajadores_activos"].notna()
        &
        df["valor_contrato_std"].notna()
        &
        df["trabajadores_activos_std"].notna()
        &
        (
            df["valor_contrato_std"] >= 0
        )
        &
        (
            df["trabajadores_activos_std"] >= 0
        )
        &
        (
            df["trabajadores_activos_std"] % 1 == 0
        )
    )

    # --------------------------------------------------------
    # 2. Aplicar regla de Consistencia
    # --------------------------------------------------------

    mascara_inconsistencia = (
        mascara_evaluable
        &
        (
            df["valor_contrato_std"] > 0
        )
        &
        (
            df["trabajadores_activos_std"] == 0
        )
    )

    for _, fila in df.loc[
        mascara_inconsistencia
    ].iterrows():

        valor_original = (
            f"valor_contrato="
            f"{fila['valor_contrato']}; "
            f"trabajadores_activos="
            f"{fila['trabajadores_activos']}"
        )

        incidencias.append({
            "id_registro":
                int(fila["id_registro"]),

            "criterio":
                "Consistencia",

            "variable":
                "valor_contrato + trabajadores_activos",

            "codigo_regla":
                "CON_001",

            "descripcion":
                (
                    "valor_contrato > 0 requiere "
                    "trabajadores_activos > 0"
                ),

            "valor_original":
                valor_original
        })

    return pd.DataFrame(
        incidencias,
        columns=[
            "id_registro",
            "criterio",
            "variable",
            "codigo_regla",
            "descripcion",
            "valor_original"
        ]
    )

# ============================================================
# VALIDACIÓN DE OPORTUNIDAD
# ============================================================

def validar_oportunidad(
    df: pd.DataFrame,
    fecha_ejecucion=None
) -> pd.DataFrame:
    """
    Valida que periodo esté dentro de la ventana temporal
    permitida.

    Regla:
        fecha_ejecucion - 60 días
        <= periodo
        <= fecha_ejecucion

    Solo se evalúan periodos presentes y válidos.
    """

    if fecha_ejecucion is None:
        fecha_ejecucion = pd.Timestamp.today().normalize()
    else:
        fecha_ejecucion = pd.Timestamp(
            fecha_ejecucion
        ).normalize()

    fecha_minima = (
        fecha_ejecucion
        - pd.Timedelta(days=60)
    )

    incidencias = []

    # --------------------------------------------------------
    # 1. Registros evaluables
    # --------------------------------------------------------

    mascara_evaluable = (
        df["periodo"].notna()
        &
        df["periodo_std"].notna()
    )

    # ========================================================
    # OPO_001 - periodo futuro
    # ========================================================

    mascara_futuro = (
        mascara_evaluable
        &
        (
            df["periodo_std"]
            > fecha_ejecucion
        )
    )

    for _, fila in df.loc[
        mascara_futuro
    ].iterrows():

        incidencias.append({
            "id_registro":
                int(fila["id_registro"]),

            "criterio":
                "Oportunidad",

            "variable":
                "periodo",

            "codigo_regla":
                "OPO_001",

            "descripcion":
                (
                    "Periodo posterior a la fecha "
                    "de ejecución"
                ),

            "valor_original":
                fila["periodo"]
        })

    # ========================================================
    # OPO_002 - periodo con antigüedad > 60 días
    # ========================================================

    mascara_antiguo = (
        mascara_evaluable
        &
        (
            df["periodo_std"]
            < fecha_minima
        )
    )

    for _, fila in df.loc[
        mascara_antiguo
    ].iterrows():

        incidencias.append({
            "id_registro":
                int(fila["id_registro"]),

            "criterio":
                "Oportunidad",

            "variable":
                "periodo",

            "codigo_regla":
                "OPO_002",

            "descripcion":
                (
                    "Periodo con antigüedad "
                    "superior a 60 días"
                ),

            "valor_original":
                fila["periodo"]
        })

    return pd.DataFrame(
        incidencias,
        columns=[
            "id_registro",
            "criterio",
            "variable",
            "codigo_regla",
            "descripcion",
            "valor_original"
        ]
    )

# ============================================================
# CONSOLIDACIÓN DE RESULTADOS
# ============================================================

def consolidar_incidencias(
    incidencias_completitud: pd.DataFrame,
    incidencias_validez: pd.DataFrame,
    incidencias_unicidad: pd.DataFrame,
    incidencias_consistencia: pd.DataFrame,
    incidencias_oportunidad: pd.DataFrame
) -> pd.DataFrame:
    """
    Consolida todas las incidencias detectadas por las cinco
    dimensiones de calidad en una única tabla de detalle.

    Cada fila representa un incumplimiento específico.
    """

    detalle_incidencias = pd.concat(
        [
            incidencias_completitud,
            incidencias_validez,
            incidencias_unicidad,
            incidencias_consistencia,
            incidencias_oportunidad
        ],
        ignore_index=True
    )

    detalle_incidencias = (
        detalle_incidencias
        .sort_values(
            by=[
                "id_registro",
                "criterio",
                "codigo_regla"
            ]
        )
        .reset_index(drop=True)
    )

    return detalle_incidencias

def clasificar_registros(
    df: pd.DataFrame,
    detalle_incidencias: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separa la carga en registros válidos y rechazados.

    Un registro se considera rechazado cuando presenta al menos
    una incidencia de calidad.

    Los registros válidos se entregan con los valores
    estandarizados.

    Los rechazados conservan los valores originales para
    trazabilidad.
    """

    ids_rechazados = set(
        detalle_incidencias["id_registro"]
        .unique()
    )

    mascara_rechazados = (
        df["id_registro"].isin(
            ids_rechazados
        )
    )

    # ========================================================
    # REGISTROS VÁLIDOS
    # ========================================================

    df_validos_base = df.loc[
        ~mascara_rechazados
    ].copy()

    df_validos = pd.DataFrame({
        "id_registro":
            df_validos_base["id_registro"],

        "id_cliente":
            df_validos_base["id_cliente_std"],

        "periodo":
            df_validos_base["periodo_std"],

        "valor_contrato":
            df_validos_base["valor_contrato_std"],

        "trabajadores_activos":
            df_validos_base[
                "trabajadores_activos_std"
            ]
    })

    # Todos los trabajadores de registros válidos deben ser
    # enteros en este punto.
    df_validos["trabajadores_activos"] = (
        df_validos["trabajadores_activos"]
        .astype("int64")
    )

    df_validos = (
        df_validos
        .reset_index(drop=True)
    )

    # ========================================================
    # REGISTROS RECHAZADOS
    # ========================================================

    df_rechazados = df.loc[
        mascara_rechazados,
        [
            "id_registro",
            "id_cliente",
            "periodo",
            "valor_contrato",
            "trabajadores_activos"
        ]
    ].copy()

    # Número total de incumplimientos por registro.
    n_incumplimientos = (
        detalle_incidencias
        .groupby("id_registro")
        .size()
        .rename("n_incumplimientos")
    )

    # Número de dimensiones diferentes afectadas.
    n_dimensiones = (
        detalle_incidencias
        .groupby("id_registro")["criterio"]
        .nunique()
        .rename("n_dimensiones_fallidas")
    )

    df_rechazados = (
        df_rechazados
        .merge(
            n_incumplimientos,
            on="id_registro",
            how="left"
        )
        .merge(
            n_dimensiones,
            on="id_registro",
            how="left"
        )
    )

    df_rechazados = (
        df_rechazados
        .sort_values("id_registro")
        .reset_index(drop=True)
    )

    return (
        df_validos,
        df_rechazados
    )

# ============================================================
# REPORTE DE CALIDAD
# ============================================================

def generar_reporte_calidad(
    df: pd.DataFrame,
    df_validos: pd.DataFrame,
    df_rechazados: pd.DataFrame,
    detalle_incidencias: pd.DataFrame,
    fecha_ejecucion=None
) -> dict:
    """
    Construye el reporte general de calidad de la carga.

    El score de cada dimensión se calcula como:

        (total_registros - registros_con_falla)
        / total_registros * 100

    Cada registro se cuenta una sola vez por dimensión,
    independientemente del número de reglas incumplidas
    dentro de ella.
    """

    if fecha_ejecucion is None:
        fecha_ejecucion = pd.Timestamp.today().normalize()
    else:
        fecha_ejecucion = pd.Timestamp(
            fecha_ejecucion
        ).normalize()

    total_registros = len(df)

    # --------------------------------------------------------
    # 1. Resumen general
    # --------------------------------------------------------

    resumen = {
        "fecha_ejecucion":
            fecha_ejecucion.strftime("%Y-%m-%d"),

        "total_registros":
            int(total_registros),

        "registros_validos":
            int(len(df_validos)),

        "registros_rechazados":
            int(len(df_rechazados)),

        "total_incidencias":
            int(len(detalle_incidencias))
    }

    # --------------------------------------------------------
    # 2. Score por dimensión
    # --------------------------------------------------------

    dimensiones = [
        "Completitud",
        "Validez",
        "Unicidad",
        "Consistencia",
        "Oportunidad"
    ]

    scores = {}

    for dimension in dimensiones:

        registros_con_falla = (
            detalle_incidencias.loc[
                detalle_incidencias["criterio"]
                == dimension,
                "id_registro"
            ]
            .nunique()
        )

        registros_sin_falla = (
            total_registros
            - registros_con_falla
        )

        score = (
            registros_sin_falla
            / total_registros
            * 100
        )

        scores[dimension] = {
            "score_pct":
                round(float(score), 2),

            "registros_sin_falla":
                int(registros_sin_falla),

            "registros_con_falla":
                int(registros_con_falla)
        }

    # --------------------------------------------------------
    # 3. Registros rechazados por regla
    # --------------------------------------------------------

    rechazados_por_regla = []

    agrupacion_reglas = (
        detalle_incidencias
        .groupby(
            [
                "codigo_regla",
                "criterio",
                "variable",
                "descripcion"
            ],
            dropna=False
        )["id_registro"]
        .nunique()
        .reset_index(
            name="registros_rechazados"
        )
        .sort_values(
            "codigo_regla"
        )
    )

    for _, fila in agrupacion_reglas.iterrows():

        rechazados_por_regla.append({
            "codigo_regla":
                fila["codigo_regla"],

            "dimension":
                fila["criterio"],

            "variable":
                fila["variable"],

            "descripcion":
                fila["descripcion"],

            "registros_rechazados":
                int(
                    fila["registros_rechazados"]
                )
        })

    # --------------------------------------------------------
    # 4. Construir reporte final
    # --------------------------------------------------------

    reporte = {
        "resumen": resumen,
        "score_por_dimension": scores,
        "rechazados_por_regla":
            rechazados_por_regla
    }

    return reporte