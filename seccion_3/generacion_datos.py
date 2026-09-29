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

    Características principales:
    - 250 clientes representados al menos una vez.
    - La combinación id_cliente + periodo es única.
    - Los periodos se encuentran dentro de los últimos 60 días.
    - trabajadores_activos es un entero positivo.
    - valor_contrato es positivo y se relaciona con el número
      de trabajadores activos.
    - La generación es reproducible mediante una semilla fija.
    """

    if fecha_ejecucion is None:
        fecha_ejecucion = date.today()

    rng = np.random.default_rng(seed)

    # --------------------------------------------------------
    # 1. GENERAR CLIENTES
    # --------------------------------------------------------

    clientes = [
        f"CLI-{i}"
        for i in range(1, N_CLIENTES + 1)
    ]

    # Se genera un tamaño base por cliente mediante una
    # distribución Gamma, permitiendo mayor concentración
    # de clientes pequeños/medianos y una cola hacia clientes
    # de mayor tamaño.
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
    # 2. GENERAR PERIODOS VÁLIDOS
    # --------------------------------------------------------

    # Incluye la fecha de ejecución y los 60 días anteriores:
    # 61 fechas posibles en total.
    fechas_validas = [
        fecha_ejecucion - timedelta(days=i)
        for i in range(61)
    ]

    # Generar todas las combinaciones posibles cliente + periodo.
    combinaciones = pd.MultiIndex.from_product(
        [clientes, fechas_validas],
        names=["id_cliente", "periodo"]
    ).to_frame(index=False)

    # --------------------------------------------------------
    # 3. GARANTIZAR REPRESENTACIÓN DE LOS 250 CLIENTES
    # --------------------------------------------------------

    # Se selecciona inicialmente una combinación aleatoria
    # para cada cliente.
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

    # Excluir las combinaciones ya utilizadas.
    indices_disponibles = np.setdiff1d(
        combinaciones.index.to_numpy(),
        indices_obligatorios
    )

    # Número de registros adicionales necesarios para
    # completar los 1.000 registros base.
    n_restantes = (
        N_REGISTROS_BASE
        - N_CLIENTES
    )

    indices_adicionales = rng.choice(
        indices_disponibles,
        size=n_restantes,
        replace=False
    )

    # Unir las 250 observaciones obligatorias con las
    # 750 observaciones adicionales.
    indices_seleccionados = np.concatenate([
        indices_obligatorios,
        indices_adicionales
    ])

    # Se define aleatoriamente el orden inicial de la carga.
    # Esto ocurre antes de crear id_registro.
    rng.shuffle(indices_seleccionados)

    df = (
        combinaciones
        .loc[indices_seleccionados]
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # 4. ASOCIAR EL TAMAÑO BASE DEL CLIENTE
    # --------------------------------------------------------

    df = df.merge(
        df_clientes,
        on="id_cliente",
        how="left",
        validate="many_to_one"
    )

    # Se permite una pequeña variación del número de
    # trabajadores para un mismo cliente entre diferentes
    # periodos.
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
    # 5. GENERAR VALOR DEL CONTRATO
    # --------------------------------------------------------

    # Valor unitario simulado por trabajador.
    valor_unitario = rng.uniform(
        low=VALOR_UNITARIO_MIN,
        high=VALOR_UNITARIO_MAX,
        size=len(df)
    )

    # El valor del contrato se relaciona con el número
    # de trabajadores activos.
    df["valor_contrato"] = np.round(
        df["trabajadores_activos"]
        * valor_unitario,
        2
    )

    # --------------------------------------------------------
    # 6. CREAR IDENTIFICADOR TÉCNICO
    # --------------------------------------------------------

    df.insert(
        0,
        "id_registro",
        np.arange(
            1,
            len(df) + 1
        )
    )

    # La variable trabajadores_base es auxiliar y no forma
    # parte de la carga que será validada.
    df = df.drop(
        columns=["trabajadores_base"]
    )

    # Formato preferido de entrada.
    df["periodo"] = pd.to_datetime(
        df["periodo"]
    ).dt.strftime("%d/%m/%Y")

    return df


# ============================================================
# COMPROBACIÓN DE LA POBLACIÓN BASE
# ============================================================

if __name__ == "__main__":

    df = generar_datos_base()

    # --------------------------------------------------------
    # Exploración inicial
    # --------------------------------------------------------

    print("\n=== PRIMEROS REGISTROS ===")
    print(df.head())

    print("\n=== DIMENSIONES ===")
    print(df.shape)

    print("\n=== TIPOS DE DATOS ===")
    print(df.dtypes)

    print("\n=== NULOS ===")
    print(df.isna().sum())

    print("\n=== CLIENTES ÚNICOS ===")
    print(df["id_cliente"].nunique())

    print(
        "\n=== DUPLICADOS id_cliente + periodo ==="
    )
    print(
        df.duplicated(
            subset=["id_cliente", "periodo"]
        ).sum()
    )

    # --------------------------------------------------------
    # Distribución de trabajadores
    # --------------------------------------------------------

    print(
        "\n=== RESUMEN TRABAJADORES ACTIVOS ==="
    )
    print(
        df["trabajadores_activos"].describe()
    )

    # --------------------------------------------------------
    # Distribución del valor del contrato
    # --------------------------------------------------------

    print(
        "\n=== RESUMEN VALOR CONTRATO ==="
    )
    print(
        df["valor_contrato"].describe()
    )

    # --------------------------------------------------------
    # Valor por trabajador
    # --------------------------------------------------------

    df["valor_por_trabajador"] = (
        df["valor_contrato"]
        / df["trabajadores_activos"]
    )

    print(
        "\n=== RESUMEN VALOR POR TRABAJADOR ==="
    )
    print(
        df["valor_por_trabajador"].describe()
    )

    media_unitaria = (
        df["valor_por_trabajador"].mean()
    )

    std_unitaria = (
        df["valor_por_trabajador"].std()
    )

    limite_superior = (
        media_unitaria
        + 3 * std_unitaria
    )

    print(
        "\n=== CONTROL DE PLAUSIBILIDAD ==="
    )

    print(
        f"Media valor por trabajador: "
        f"{media_unitaria:,.2f}"
    )

    print(
        f"Desviación estándar: "
        f"{std_unitaria:,.2f}"
    )

    print(
        f"Límite superior (media + 3σ): "
        f"{limite_superior:,.2f}"
    )

    # --------------------------------------------------------
    # Relación trabajadores - valor contrato
    # --------------------------------------------------------

    correlacion = (
        df["trabajadores_activos"]
        .corr(df["valor_contrato"])
    )

    print(
        "\n=== CORRELACIÓN "
        "TRABAJADORES / VALOR CONTRATO ==="
    )

    print(correlacion)

    # ========================================================
    # VALIDACIONES DE LA POBLACIÓN BASE
    # ========================================================

    print("\n=== VALIDACIONES BASE ===")

    # 1. Exactamente 1.000 registros
    print(
        "1.000 registros:",
        len(df) == N_REGISTROS_BASE
    )

    # 2. Los 250 clientes están representados
    print(
        "250 clientes representados:",
        df["id_cliente"].nunique()
        == N_CLIENTES
    )

    # 3. id_registro es único
    print(
        "id_registro único:",
        df["id_registro"].is_unique
    )

    # 4. Formato válido de id_cliente
    ids_validos = (
        df["id_cliente"]
        .str.match(r"^CLI-[1-9]\d*$")
        .all()
    )

    print(
        "Formato id_cliente válido:",
        ids_validos
    )

    # 5. Llave id_cliente + periodo única
    llave_unica = ~df.duplicated(
        subset=["id_cliente", "periodo"]
    ).any()

    print(
        "id_cliente + periodo único:",
        llave_unica
    )

    # --------------------------------------------------------
    # 6. Validación de periodos
    # --------------------------------------------------------

    periodos = pd.to_datetime(
        df["periodo"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    print(
        "Todos los periodos interpretables:",
        periodos.notna().all()
    )

    fecha_ejecucion = pd.Timestamp(
        date.today()
    )

    fecha_minima = (
        fecha_ejecucion
        - pd.Timedelta(days=60)
    )

    oportunidad_valida = (
        (
            periodos >= fecha_minima
        )
        &
        (
            periodos <= fecha_ejecucion
        )
    ).all()

    print(
        "Todos los periodos dentro de 60 días:",
        oportunidad_valida
    )

    # --------------------------------------------------------
    # 7. Validación trabajadores activos
    # --------------------------------------------------------

    trabajadores_validos = (
        (
            df["trabajadores_activos"] >= 1
        )
        &
        (
            df["trabajadores_activos"] % 1
            == 0
        )
    ).all()

    print(
        "Trabajadores activos válidos:",
        trabajadores_validos
    )

    # --------------------------------------------------------
    # 8. Validación valor contrato
    # --------------------------------------------------------

    contratos_validos = (
        df["valor_contrato"] >= 0
    ).all()

    print(
        "Valores de contrato válidos:",
        contratos_validos
    )

    # --------------------------------------------------------
    # 9. Validación consistencia
    # --------------------------------------------------------

    consistencia_valida = (
        ~(
            (
                df["valor_contrato"] > 0
            )
            &
            (
                df["trabajadores_activos"] <= 0
            )
        )
    ).all()

    print(
        "Regla de consistencia cumplida:",
        consistencia_valida
    )

    # --------------------------------------------------------
    # 10. Valor por trabajador dentro del rango de generación
    # --------------------------------------------------------

    valor_unitario_valido = (
        (
            df["valor_por_trabajador"]
            >= VALOR_UNITARIO_MIN
        )
        &
        (
            df["valor_por_trabajador"]
            <= VALOR_UNITARIO_MAX
        )
    ).all()

    print(
        "Valor por trabajador dentro "
        "del rango esperado:",
        valor_unitario_valido
    )


if __name__ == "__main__":
    df = generar_datos_base()

    print("\n=== PRIMEROS REGISTROS ===")
    print(df.head())

    print("\n=== DIMENSIONES ===")
    print(df.shape)

    print("\n=== TIPOS DE DATOS ===")
    print(df.dtypes)

    print("\n=== NULOS ===")
    print(df.isna().sum())

    print("\n=== CLIENTES ÚNICOS ===")
    print(df["id_cliente"].nunique())

    print("\n=== DUPLICADOS id_cliente + periodo ===")
    print(df.duplicated(subset=["id_cliente", "periodo"]).sum())

    print("\n=== RESUMEN TRABAJADORES ACTIVOS ===")
    print(df["trabajadores_activos"].describe())

    print("\n=== RESUMEN VALOR CONTRATO ===")
    print(df["valor_contrato"].describe())

    # Valor del contrato por trabajador
    df["valor_por_trabajador"] = (
        df["valor_contrato"] / df["trabajadores_activos"]
    )

    print("\n=== RESUMEN VALOR POR TRABAJADOR ===")
    print(df["valor_por_trabajador"].describe())

    media_unitaria = df["valor_por_trabajador"].mean()
    std_unitaria = df["valor_por_trabajador"].std()
    limite_superior = media_unitaria + 3 * std_unitaria

    print("\n=== CONTROL DE PLAUSIBILIDAD ===")
    print(f"Media valor por trabajador: {media_unitaria:,.2f}")
    print(f"Desviación estándar: {std_unitaria:,.2f}")
    print(f"Límite superior (media + 3σ): {limite_superior:,.2f}")

    print("\n=== CORRELACIÓN TRABAJADORES / VALOR CONTRATO ===")
    print(
        df["trabajadores_activos"].corr(
            df["valor_contrato"]
        )
    )


    # ---------------------------------------------------------
    # Validaciones de la población base
    # ---------------------------------------------------------

    print("\n=== VALIDACIONES BASE ===")

    # 1. Exactamente 1.000 registros
    print(
        "1.000 registros:",
        len(df) == N_REGISTROS_BASE
    )

    # 2. id_registro único
    print(
        "id_registro único:",
        df["id_registro"].is_unique
    )

    # 3. id_cliente con formato correcto
    ids_validos = df["id_cliente"].str.match(r"^CLI-[1-9]\d*$").all()

    print(
        "Formato id_cliente válido:",
        ids_validos
    )

    # 4. Sin duplicados cliente + periodo
    llave_unica = ~df.duplicated(
        subset=["id_cliente", "periodo"]
    ).any()

    print(
        "id_cliente + periodo único:",
        llave_unica
    )

    # 5. Periodos válidos
    periodos = pd.to_datetime(
        df["periodo"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    print(
        "Todos los periodos interpretables:",
        periodos.notna().all()
    )

    fecha_ejecucion = pd.Timestamp(date.today())
    fecha_minima = fecha_ejecucion - pd.Timedelta(days=60)

    oportunidad_valida = (
        (periodos >= fecha_minima)
        & (periodos <= fecha_ejecucion)
    ).all()

    print(
        "Todos los periodos dentro de 60 días:",
        oportunidad_valida
    )

    # 6. Trabajadores enteros y positivos
    trabajadores_validos = (
        (df["trabajadores_activos"] >= 1)
        & (df["trabajadores_activos"] % 1 == 0)
    ).all()

    print(
        "Trabajadores activos válidos:",
        trabajadores_validos
    )

    # 7. Contratos no negativos
    contratos_validos = (
        df["valor_contrato"] >= 0
    ).all()

    print(
        "Valores de contrato válidos:",
        contratos_validos
    )

    # 8. Consistencia
    consistencia_valida = (
        ~(
            (df["valor_contrato"] > 0)
            & (df["trabajadores_activos"] <= 0)
        )
    ).all()

    print(
        "Regla de consistencia cumplida:",
        consistencia_valida
    )

    # 9. Valor unitario dentro del rango usado para generar la base
    valor_unitario_valido = (
        (df["valor_por_trabajador"] >= VALOR_UNITARIO_MIN)
        & (df["valor_por_trabajador"] <= VALOR_UNITARIO_MAX)
    ).all()

    print(
        "Valor por trabajador dentro del rango esperado:",
        valor_unitario_valido
    )