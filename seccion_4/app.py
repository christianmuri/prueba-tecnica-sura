import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

SEED = 42

FECHA_INICIO_ANALISIS = pd.Timestamp("2024-01-01")
FECHA_FIN_ANALISIS = pd.Timestamp("2026-12-31")

N_CLIENTES = 30

DISTRIBUCION_TAMANOS = {
    "Pequeño": 10,
    "Mediano": 12,
    "Grande": 8,
}

RANGOS_TRABAJADORES = {
    "Pequeño": (50, 150),
    "Mediano": (151, 400),
    "Grande": (401, 900),
}

TASAS_CASOS_MENSUALES = {
    1: 0.30,
    2: 0.50,
    3: 0.80,
    4: 1.20,
    5: 1.70,
}

PROBABILIDAD_GRAVE = {
    1: 0.03,
    2: 0.05,
    3: 0.08,
    4: 0.12,
    5: 0.18,
}

TARIFA_BASE_RIESGO = {
    1: 45_000,
    2: 55_000,
    3: 70_000,
    4: 90_000,
    5: 120_000,
}

FACTOR_ANUAL_CONTRATO = {
    2024: 1.00,
    2025: 1.04,
    2026: 1.08,
}

FRECUENCIA_PREVENCION_TAMANO = {
    "Pequeño": 0.8,
    "Mediano": 1.8,
    "Grande": 3.0,
}

FACTOR_PREVENCION_RIESGO = {
    1: 0.90,
    2: 1.00,
    3: 1.05,
    4: 1.15,
    5: 1.25,
}

TIPOS_PREVENCION = [
    "Capacitación",
    "Inspección",
    "Asesoría",
    "Campaña preventiva",
]

RANGO_PARTICIPACION = {
    "Capacitación": (0.20, 0.45),
    "Inspección": (0.10, 0.25),
    "Asesoría": (0.10, 0.20),
    "Campaña preventiva": (0.30, 0.50),
}

# ============================================================
# GENERACIÓN DE CLIENTES
# ============================================================

def generar_clientes(seed=SEED):
    """
    Genera la dimensión de clientes para la simulación.

    Criterios:
    - 30 clientes.
    - Todos vinculados antes del 01/01/2024.
    - Todos activos durante el periodo de análisis.
    - Distribución controlada por sector.
    - Distribución controlada por clase de riesgo.
    - Se mantiene una relación razonable entre sector
      y clase de riesgo sin hacerla determinística.
    """

    rng = np.random.default_rng(seed)

    # Combinaciones definidas para garantizar exactamente
    # las distribuciones acordadas.
    perfiles = [
        # Servicios: 7
        ("Servicios", 1),
        ("Servicios", 1),
        ("Servicios", 1),
        ("Servicios", 2),
        ("Servicios", 2),
        ("Servicios", 2),
        ("Servicios", 3),

        # Comercio: 6
        ("Comercio", 1),
        ("Comercio", 2),
        ("Comercio", 2),
        ("Comercio", 3),
        ("Comercio", 3),
        ("Comercio", 3),

        # Manufactura: 5
        ("Manufactura", 2),
        ("Manufactura", 3),
        ("Manufactura", 3),
        ("Manufactura", 4),
        ("Manufactura", 5),

        # Construcción: 4
        ("Construcción", 3),
        ("Construcción", 4),
        ("Construcción", 5),
        ("Construcción", 5),

        # Transporte y logística: 4
        ("Transporte y logística", 2),
        ("Transporte y logística", 3),
        ("Transporte y logística", 4),
        ("Transporte y logística", 4),

        # Salud: 4
        ("Salud", 1),
        ("Salud", 4),
        ("Salud", 4),
        ("Salud", 5),
    ]

    # Mezclar los perfiles sin modificar sus distribuciones.
    orden = rng.permutation(len(perfiles))
    perfiles = [perfiles[i] for i in orden]

    # Todos los clientes se vinculan antes del periodo analizado.
    fecha_min = pd.Timestamp("2018-01-01")
    fecha_max = pd.Timestamp("2023-12-31")

    dias_disponibles = (fecha_max - fecha_min).days

    fechas_vinculacion = (
        fecha_min
        + pd.to_timedelta(
            rng.integers(
                0,
                dias_disponibles + 1,
                size=N_CLIENTES
            ),
            unit="D"
        )
    )

    registros = []

    for i in range(N_CLIENTES):
        sector, clase_riesgo = perfiles[i]

        registros.append(
            {
                "id_cliente": f"CLI-{i + 1:05d}",
                "nombre": f"Cliente {i + 1:02d}",
                "sector": sector,
                "clase_riesgo": clase_riesgo,
                "estado": "Activo",
                "fecha_vinculacion": fechas_vinculacion[i],
            }
        )

    return pd.DataFrame(registros)

def generar_parametros_clientes(df_clientes, seed=SEED + 1):
    """
    Genera parámetros auxiliares para cada cliente.

    Estos parámetros se utilizan únicamente durante la simulación
    y no modifican la estructura original de la tabla clientes.

    Criterios:
    - 10 clientes pequeños.
    - 12 clientes medianos.
    - 8 clientes grandes.
    - El tamaño se asigna independientemente de la clase de riesgo.
    - La plantilla inicial depende del tamaño del cliente.
    """

    rng = np.random.default_rng(seed)

    tamanos = (
        ["Pequeño"] * DISTRIBUCION_TAMANOS["Pequeño"]
        + ["Mediano"] * DISTRIBUCION_TAMANOS["Mediano"]
        + ["Grande"] * DISTRIBUCION_TAMANOS["Grande"]
    )

    rng.shuffle(tamanos)

    parametros = df_clientes[["id_cliente"]].copy()
    parametros["tamano_cliente"] = tamanos

    trabajadores_iniciales = []

    for tamano in parametros["tamano_cliente"]:
        minimo, maximo = RANGOS_TRABAJADORES[tamano]

        cantidad = rng.integers(
            minimo,
            maximo + 1
        )

        trabajadores_iniciales.append(int(cantidad))

    parametros["trabajadores_iniciales"] = trabajadores_iniciales

    return parametros

def generar_trabajadores_activos_mensuales(
    parametros_clientes,
    seed=SEED + 2
):
    """
    Genera la cantidad de trabajadores activos por cliente y mes.

    Criterios:
    - Periodo completo: enero 2024 a diciembre 2026.
    - 36 meses por cliente.
    - La plantilla parte de trabajadores_iniciales.
    - La variación mensual máxima es +/- 5 %.
    - Se introduce variabilidad moderada y reproducible.
    - Los cambios mensuales son acumulativos.
    """

    rng = np.random.default_rng(seed)

    meses = pd.date_range(
        start=FECHA_INICIO_ANALISIS,
        end=FECHA_FIN_ANALISIS,
        freq="MS"
    )

    registros = []

    for _, cliente in parametros_clientes.iterrows():

        trabajadores_iniciales = int(
            cliente["trabajadores_iniciales"]
        )

        trabajadores_actuales = trabajadores_iniciales

        # Tendencia propia del cliente.
        # Puede tener crecimiento o reducción moderada.
        tendencia_mensual = rng.uniform(-0.002, 0.004)

        for i, periodo in enumerate(meses):

            if i > 0:

                ruido = rng.normal(
                    loc=0,
                    scale=0.015
                )

                variacion = tendencia_mensual + ruido

                # Ningún cambio mensual puede superar +/- 5 %.
                variacion = np.clip(
                    variacion,
                    -0.05,
                    0.05
                )

                cambio = int(
                    round(
                        trabajadores_actuales
                        * variacion
                    )
                )

                # Límite entero para garantizar que,
                # incluso después del redondeo,
                # el cambio no supere el 5 %.
                max_cambio = int(
                    np.floor(
                        trabajadores_actuales * 0.05
                    )
                )

                cambio = int(
                    np.clip(
                        cambio,
                        -max_cambio,
                        max_cambio
                    )
                )

                trabajadores_actuales += cambio

                # Evitar valores inválidos.
                trabajadores_actuales = max(
                    trabajadores_actuales,
                    1
                )

            registros.append(
                {
                    "id_cliente": cliente["id_cliente"],
                    "periodo": periodo,
                    "trabajadores_activos": trabajadores_actuales,
                }
            )

    return pd.DataFrame(registros)
def generar_trabajadores(
    df_clientes,
    df_trabajadores_activos,
    seed=SEED + 3
):
    """
    Genera los trabajadores y su historial de actividad.

    Criterios:
    - La cantidad activa al cierre de cada mes coincide exactamente
      con trabajadores_activos.
    - Los trabajadores iniciales ingresaron antes del 01/01/2024.
    - Si la plantilla aumenta, se generan nuevas altas durante el mes.
    - Si disminuye, se generan retiros durante el mes.
    - fecha_retiro se conserva únicamente como variable auxiliar
      para garantizar coherencia temporal durante la simulación.
    """

    rng = np.random.default_rng(seed)

    registros = []
    contador_trabajadores = 1

    clientes_info = (
        df_clientes
        .set_index("id_cliente")
    )

    for id_cliente, df_cliente_mes in (
        df_trabajadores_activos
        .sort_values(["id_cliente", "periodo"])
        .groupby("id_cliente")
    ):

        df_cliente_mes = df_cliente_mes.reset_index(drop=True)

        fecha_vinculacion = clientes_info.loc[
            id_cliente,
            "fecha_vinculacion"
        ]

        activos = []

        # ====================================================
        # PLANTILLA INICIAL
        # ====================================================

        cantidad_inicial = int(
            df_cliente_mes.loc[
                0,
                "trabajadores_activos"
            ]
        )

        fecha_max_inicial = FECHA_INICIO_ANALISIS - pd.Timedelta(days=1)

        dias_disponibles = (
            fecha_max_inicial - fecha_vinculacion
        ).days

        for _ in range(cantidad_inicial):

            fecha_ingreso = (
                fecha_vinculacion
                + pd.to_timedelta(
                    rng.integers(
                        0,
                        dias_disponibles + 1
                    ),
                    unit="D"
                )
            )

            id_trabajador = (
                f"TRB-{contador_trabajadores:06d}"
            )

            registros.append(
                {
                    "id_trabajador": id_trabajador,
                    "id_cliente": id_cliente,
                    "nombre": (
                        f"Trabajador {contador_trabajadores:06d}"
                    ),
                    "fecha_ingreso": fecha_ingreso,
                    "fecha_retiro": pd.NaT,
                }
            )

            activos.append(
                len(registros) - 1
            )

            contador_trabajadores += 1

        # ====================================================
        # CAMBIOS DE PLANTILLA 2024-2026
        # ====================================================

        trabajadores_periodo_anterior = cantidad_inicial

        for i in range(1, len(df_cliente_mes)):

            periodo = df_cliente_mes.loc[i, "periodo"]

            trabajadores_objetivo = int(
                df_cliente_mes.loc[
                    i,
                    "trabajadores_activos"
                ]
            )

            diferencia = (
                trabajadores_objetivo
                - trabajadores_periodo_anterior
            )

            inicio_mes = periodo

            fin_mes = (
                periodo
                + pd.offsets.MonthEnd(0)
            )

            dias_mes = (
                fin_mes - inicio_mes
            ).days

            # -----------------------------------------------
            # ALTAS
            # -----------------------------------------------

            if diferencia > 0:

                for _ in range(diferencia):

                    fecha_ingreso = (
                        inicio_mes
                        + pd.to_timedelta(
                            rng.integers(
                                0,
                                dias_mes + 1
                            ),
                            unit="D"
                        )
                    )

                    id_trabajador = (
                        f"TRB-{contador_trabajadores:06d}"
                    )

                    registros.append(
                        {
                            "id_trabajador": id_trabajador,
                            "id_cliente": id_cliente,
                            "nombre": (
                                f"Trabajador "
                                f"{contador_trabajadores:06d}"
                            ),
                            "fecha_ingreso": fecha_ingreso,
                            "fecha_retiro": pd.NaT,
                        }
                    )

                    activos.append(
                        len(registros) - 1
                    )

                    contador_trabajadores += 1

            # -----------------------------------------------
            # RETIROS
            # -----------------------------------------------

            elif diferencia < 0:

                cantidad_retiros = abs(diferencia)

                seleccionados = rng.choice(
                    activos,
                    size=cantidad_retiros,
                    replace=False
                )

                for indice_registro in seleccionados:

                    fecha_retiro = (
                        inicio_mes
                        + pd.to_timedelta(
                            rng.integers(
                                0,
                                dias_mes + 1
                            ),
                            unit="D"
                        )
                    )

                    registros[
                        indice_registro
                    ]["fecha_retiro"] = fecha_retiro

                seleccionados = set(
                    seleccionados.tolist()
                )

                activos = [
                    indice
                    for indice in activos
                    if indice not in seleccionados
                ]

            trabajadores_periodo_anterior = (
                trabajadores_objetivo
            )

    historial = pd.DataFrame(registros)

    # Estado final al cierre del periodo analizado.
    historial["estado"] = np.where(
        historial["fecha_retiro"].isna(),
        "Activo",
        "Inactivo"
    )

    # Tabla final respetando el modelo original.
    trabajadores = historial[
        [
            "id_trabajador",
            "id_cliente",
            "nombre",
            "fecha_ingreso",
            "estado",
        ]
    ].copy()

    return trabajadores, historial

def generar_casos(
    df_clientes,
    df_trabajadores_activos,
    historial_trabajadores,
    seed=SEED + 4
):
    """
    Genera los casos ocurridos entre 2024 y 2026.

    Criterios:
    - El número mensual de casos depende de:
        * trabajadores activos
        * clase de riesgo
    - Se utiliza una distribución Poisson.
    - La probabilidad de caso grave aumenta con la clase de riesgo.
    - Los días de ausencia dependen del tipo de caso.
    - El costo depende del tipo y de los días de ausencia.
    - El trabajador asignado debe estar activo en la fecha del caso.
    """

    rng = np.random.default_rng(seed)

    clientes_info = (
        df_clientes[
            [
                "id_cliente",
                "clase_riesgo"
            ]
        ]
        .set_index("id_cliente")
    )

    registros = []
    contador_casos = 1

    for _, fila in (
        df_trabajadores_activos
        .sort_values(["id_cliente", "periodo"])
        .iterrows()
    ):

        id_cliente = fila["id_cliente"]
        periodo = fila["periodo"]

        trabajadores_activos = int(
            fila["trabajadores_activos"]
        )

        clase_riesgo = int(
            clientes_info.loc[
                id_cliente,
                "clase_riesgo"
            ]
        )

        tasa = TASAS_CASOS_MENSUALES[
            clase_riesgo
        ]

        # Número esperado de casos del cliente en el mes.
        lambda_casos = (
            trabajadores_activos
            * tasa
            / 100
        )

        numero_casos = rng.poisson(
            lambda_casos
        )

        if numero_casos == 0:
            continue

        fin_mes = (
            periodo
            + pd.offsets.MonthEnd(0)
        )

        dias_mes = (
            fin_mes - periodo
        ).days

        trabajadores_cliente = (
            historial_trabajadores[
                historial_trabajadores[
                    "id_cliente"
                ] == id_cliente
            ]
        )

        for _ in range(numero_casos):

            # ================================================
            # FECHA DEL CASO
            # ================================================

            fecha_ocurrencia = (
                periodo
                + pd.to_timedelta(
                    rng.integers(
                        0,
                        dias_mes + 1
                    ),
                    unit="D"
                )
            )

            # ================================================
            # TRABAJADOR ACTIVO EN ESA FECHA
            # ================================================

            disponibles = trabajadores_cliente[
                (
                    trabajadores_cliente[
                        "fecha_ingreso"
                    ] <= fecha_ocurrencia
                )
                &
                (
                    trabajadores_cliente[
                        "fecha_retiro"
                    ].isna()
                    |
                    (
                        trabajadores_cliente[
                            "fecha_retiro"
                        ] > fecha_ocurrencia
                    )
                )
            ]

            # Salvaguarda.
            if disponibles.empty:
                continue

            indice_trabajador = rng.choice(
                disponibles.index
            )

            id_trabajador = (
                historial_trabajadores.loc[
                    indice_trabajador,
                    "id_trabajador"
                ]
            )

            # ================================================
            # TIPO DEL CASO
            # ================================================

            es_grave = (
                rng.random()
                < PROBABILIDAD_GRAVE[
                    clase_riesgo
                ]
            )

            tipo = (
                "Grave"
                if es_grave
                else "Leve"
            )

            # ================================================
            # DÍAS DE AUSENCIA
            # ================================================

            if tipo == "Leve":

                dias_ausencia = int(
                    np.clip(
                        rng.poisson(2.5),
                        0,
                        10
                    )
                )

            else:

                dias_ausencia = int(
                    np.clip(
                        round(
                            rng.gamma(
                                shape=4,
                                scale=6
                            )
                        ),
                        10,
                        60
                    )
                )

            # ================================================
            # COSTO
            # ================================================

            if tipo == "Leve":

                costo_base = rng.uniform(
                    200_000,
                    600_000
                )

                costo_diario = rng.uniform(
                    80_000,
                    150_000
                )

            else:

                costo_base = rng.uniform(
                    1_500_000,
                    4_000_000
                )

                costo_diario = rng.uniform(
                    150_000,
                    300_000
                )

            costo_estimado = (
                costo_base
                + dias_ausencia
                * costo_diario
            )

            # Variabilidad adicional de +/- aproximadamente 5 %.
            ruido_costo = rng.normal(
                loc=1.0,
                scale=0.05
            )

            costo = int(
                round(
                    max(
                        costo_estimado
                        * ruido_costo,
                        0
                    )
                )
            )

            # ================================================
            # ESTADO DEL CASO
            # ================================================

            if fecha_ocurrencia.year == 2024:
                prob_cerrado = 0.98

            elif fecha_ocurrencia.year == 2025:
                prob_cerrado = 0.95

            else:
                # Los casos recientes tienen mayor
                # probabilidad de permanecer abiertos.
                if fecha_ocurrencia.month >= 10:
                    prob_cerrado = 0.75
                else:
                    prob_cerrado = 0.90

            estado = (
                "Cerrado"
                if rng.random() < prob_cerrado
                else "Abierto"
            )

            registros.append(
                {
                    "id_caso": (
                        f"CAS-{contador_casos:06d}"
                    ),
                    "id_cliente": id_cliente,
                    "id_trabajador": id_trabajador,
                    "fecha_ocurrencia": fecha_ocurrencia,
                    "tipo": tipo,
                    "dias_ausencia": dias_ausencia,
                    "costo": costo,
                    "estado": estado,
                }
            )

            contador_casos += 1

    return pd.DataFrame(registros)

def generar_facturacion(
    df_clientes,
    df_trabajadores_activos,
    seed=SEED + 5
):
    """
    Genera la facturación mensual por cliente.

    Criterios:
    - Una fila por cliente y mes.
    - trabajadores_activos proviene directamente de la
      evolución mensual ya generada.
    - valor_contrato depende de:
        * trabajadores activos
        * clase de riesgo
        * ajuste anual
        * variabilidad aleatoria moderada de +/- 3 %
    """

    rng = np.random.default_rng(seed)

    facturacion = (
        df_trabajadores_activos
        .merge(
            df_clientes[
                [
                    "id_cliente",
                    "clase_riesgo"
                ]
            ],
            on="id_cliente",
            how="left"
        )
        .copy()
    )

    valores_contrato = []

    for _, fila in facturacion.iterrows():

        clase_riesgo = int(
            fila["clase_riesgo"]
        )

        trabajadores_activos = int(
            fila["trabajadores_activos"]
        )

        anio = fila["periodo"].year

        tarifa_base = TARIFA_BASE_RIESGO[
            clase_riesgo
        ]

        factor_anual = FACTOR_ANUAL_CONTRATO[
            anio
        ]

        variacion = rng.uniform(
            0.97,
            1.03
        )

        valor_contrato = (
            trabajadores_activos
            * tarifa_base
            * factor_anual
            * variacion
        )

        valores_contrato.append(
            int(round(valor_contrato))
        )

    facturacion["valor_contrato"] = (
        valores_contrato
    )

    return facturacion[
        [
            "id_cliente",
            "periodo",
            "trabajadores_activos",
            "valor_contrato",
        ]
    ]

def generar_prevencion(
    df_clientes,
    parametros_clientes,
    df_trabajadores_activos,
    seed=SEED + 6
):
    """
    Genera actividades de prevención entre 2024 y 2026.

    Criterios:
    - La frecuencia depende del tamaño del cliente.
    - Clientes con mayor riesgo reciben ligeramente más
      actividades preventivas.
    - La cantidad de participantes depende del tipo
      de actividad.
    - participantes nunca puede superar la cantidad
      de trabajadores activos del cliente en ese mes.
    - La prevención no modifica directamente la
      probabilidad de ocurrencia de casos.
    """

    rng = np.random.default_rng(seed)

    informacion_clientes = (
        df_clientes[
            [
                "id_cliente",
                "clase_riesgo"
            ]
        ]
        .merge(
            parametros_clientes[
                [
                    "id_cliente",
                    "tamano_cliente"
                ]
            ],
            on="id_cliente",
            how="left"
        )
        .set_index("id_cliente")
    )

    registros = []
    contador_actividad = 1

    for _, fila in (
        df_trabajadores_activos
        .sort_values(
            [
                "id_cliente",
                "periodo"
            ]
        )
        .iterrows()
    ):

        id_cliente = fila["id_cliente"]
        periodo = fila["periodo"]

        trabajadores_activos = int(
            fila["trabajadores_activos"]
        )

        clase_riesgo = int(
            informacion_clientes.loc[
                id_cliente,
                "clase_riesgo"
            ]
        )

        tamano_cliente = (
            informacion_clientes.loc[
                id_cliente,
                "tamano_cliente"
            ]
        )

        frecuencia_base = (
            FRECUENCIA_PREVENCION_TAMANO[
                tamano_cliente
            ]
        )

        factor_riesgo = (
            FACTOR_PREVENCION_RIESGO[
                clase_riesgo
            ]
        )

        lambda_actividades = (
            frecuencia_base
            * factor_riesgo
        )

        numero_actividades = rng.poisson(
            lambda_actividades
        )

        if numero_actividades == 0:
            continue

        fin_mes = (
            periodo
            + pd.offsets.MonthEnd(0)
        )

        dias_mes = (
            fin_mes - periodo
        ).days

        for _ in range(numero_actividades):

            fecha = (
                periodo
                + pd.to_timedelta(
                    rng.integers(
                        0,
                        dias_mes + 1
                    ),
                    unit="D"
                )
            )

            tipo = rng.choice(
                TIPOS_PREVENCION
            )

            minimo_participacion, maximo_participacion = (
                RANGO_PARTICIPACION[tipo]
            )

            proporcion = rng.uniform(
                minimo_participacion,
                maximo_participacion
            )

            participantes = int(
                round(
                    trabajadores_activos
                    * proporcion
                )
            )

            participantes = max(
                participantes,
                1
            )

            participantes = min(
                participantes,
                trabajadores_activos
            )

            registros.append(
                {
                    "id_actividad": (
                        f"ACT-{contador_actividad:06d}"
                    ),
                    "id_cliente": id_cliente,
                    "fecha": fecha,
                    "tipo": tipo,
                    "participantes": participantes,
                }
            )

            contador_actividad += 1

    return pd.DataFrame(registros)
# ============================================================
# VALIDACIÓN
# ============================================================

def validar_clientes(df_clientes):
    """
    Comprueba que la tabla de clientes cumple los criterios
    definidos para la simulación.
    """

    distribucion_riesgo_esperada = {
        1: 5,
        2: 7,
        3: 8,
        4: 6,
        5: 4,
    }

    distribucion_sector_esperada = {
        "Servicios": 7,
        "Comercio": 6,
        "Manufactura": 5,
        "Construcción": 4,
        "Transporte y logística": 4,
        "Salud": 4,
    }

    assert len(df_clientes) == 30
    assert df_clientes["id_cliente"].is_unique
    assert df_clientes["estado"].eq("Activo").all()

    assert (
        df_clientes["fecha_vinculacion"]
        < FECHA_INICIO_ANALISIS
    ).all()

    assert (
        df_clientes["clase_riesgo"]
        .value_counts()
        .sort_index()
        .to_dict()
        == distribucion_riesgo_esperada
    )

    assert (
        df_clientes["sector"]
        .value_counts()
        .to_dict()
        == distribucion_sector_esperada
    )

def validar_parametros_clientes(parametros):
    """
    Valida la distribución de tamaños y los rangos
    de trabajadores iniciales.
    """

    distribucion_obtenida = (
        parametros["tamano_cliente"]
        .value_counts()
        .to_dict()
    )

    assert distribucion_obtenida == DISTRIBUCION_TAMANOS

    for tamano, (minimo, maximo) in RANGOS_TRABAJADORES.items():

        valores = parametros.loc[
            parametros["tamano_cliente"] == tamano,
            "trabajadores_iniciales"
        ]

        assert valores.between(minimo, maximo).all()

    assert parametros["id_cliente"].is_unique
    assert len(parametros) == N_CLIENTES

def validar_trabajadores_activos_mensuales(df_trabajadores_activos):
    """
    Valida la evolución mensual de trabajadores activos.
    """

    # 30 clientes x 36 meses.
    assert len(df_trabajadores_activos) == 1080

    # Una única fila por cliente y periodo.
    assert not df_trabajadores_activos.duplicated(
        subset=["id_cliente", "periodo"]
    ).any()

    # Todos los clientes deben tener exactamente 36 meses.
    meses_por_cliente = (
        df_trabajadores_activos
        .groupby("id_cliente")["periodo"]
        .nunique()
    )

    assert meses_por_cliente.eq(36).all()

    # No puede haber trabajadores activos <= 0.
    assert (
        df_trabajadores_activos["trabajadores_activos"] > 0
    ).all()

    # Verificación del cambio mensual máximo.
    df_validacion = (
        df_trabajadores_activos
        .sort_values(["id_cliente", "periodo"])
        .copy()
    )

    df_validacion["trabajadores_anterior"] = (
        df_validacion
        .groupby("id_cliente")["trabajadores_activos"]
        .shift(1)
    )

    df_validacion["variacion_mensual"] = (
        (
            df_validacion["trabajadores_activos"]
            - df_validacion["trabajadores_anterior"]
        )
        / df_validacion["trabajadores_anterior"]
    )

    variaciones = (
        df_validacion["variacion_mensual"]
        .dropna()
        .abs()
    )

    assert (variaciones <= 0.05).all()

def validar_trabajadores(
    trabajadores,
    historial_trabajadores,
    df_clientes,
    df_trabajadores_activos
):
    """
    Comprueba la integridad referencial y temporal
    de los trabajadores generados.
    """

    assert trabajadores["id_trabajador"].is_unique

    assert trabajadores["id_cliente"].isin(
        df_clientes["id_cliente"]
    ).all()

    # Ningún trabajador puede ingresar antes de que
    # el cliente se haya vinculado.
    validacion_fechas = historial_trabajadores.merge(
        df_clientes[
            [
                "id_cliente",
                "fecha_vinculacion"
            ]
        ],
        on="id_cliente",
        how="left"
    )

    assert (
        validacion_fechas["fecha_ingreso"]
        >= validacion_fechas["fecha_vinculacion"]
    ).all()

    # Un retiro nunca puede ocurrir antes del ingreso.
    retirados = historial_trabajadores[
        historial_trabajadores["fecha_retiro"].notna()
    ]

    assert (
        retirados["fecha_retiro"]
        >= retirados["fecha_ingreso"]
    ).all()


    # ====================================================
    # VALIDAR PLANTILLA ACTIVA AL CIERRE DE CADA MES
    # ====================================================

    for id_cliente, objetivos in (
        df_trabajadores_activos.groupby("id_cliente")
    ):

        trabajadores_cliente = (
            historial_trabajadores[
                historial_trabajadores["id_cliente"]
                == id_cliente
            ]
        )

        for _, fila in objetivos.iterrows():

            fin_mes = (
                fila["periodo"]
                + pd.offsets.MonthEnd(0)
            )

            activos_fin_mes = (
                (
                    trabajadores_cliente["fecha_ingreso"]
                    <= fin_mes
                )
                &
                (
                    trabajadores_cliente["fecha_retiro"].isna()
                    |
                    (
                        trabajadores_cliente["fecha_retiro"]
                        > fin_mes
                    )
                )
            ).sum()

            assert activos_fin_mes == int(
                fila["trabajadores_activos"]
            )


def validar_casos(
    casos,
    clientes,
    historial_trabajadores
):
    """
    Valida integridad referencial, temporal
    y reglas básicas de los casos.
    """

    assert casos["id_caso"].is_unique

    assert casos["id_cliente"].isin(
        clientes["id_cliente"]
    ).all()

    assert casos["id_trabajador"].isin(
        historial_trabajadores[
            "id_trabajador"
        ]
    ).all()

    assert casos["tipo"].isin(
        ["Leve", "Grave"]
    ).all()

    assert (
        casos["dias_ausencia"] >= 0
    ).all()

    assert (
        casos["costo"] >= 0
    ).all()

    assert casos["fecha_ocurrencia"].between(
        FECHA_INICIO_ANALISIS,
        FECHA_FIN_ANALISIS
    ).all()

    # ====================================================
    # VALIDACIÓN TEMPORAL DEL TRABAJADOR
    # ====================================================

    validacion = casos.merge(
        historial_trabajadores[
            [
                "id_trabajador",
                "id_cliente",
                "fecha_ingreso",
                "fecha_retiro",
            ]
        ],
        on=[
            "id_trabajador",
            "id_cliente"
        ],
        how="left"
    )

    # El trabajador ya debía haber ingresado.
    assert (
        validacion["fecha_ocurrencia"]
        >= validacion["fecha_ingreso"]
    ).all()

    # Si tiene fecha de retiro, el caso debe ser anterior.
    retirados = validacion[
        validacion["fecha_retiro"].notna()
    ]

    assert (
        retirados["fecha_ocurrencia"]
        < retirados["fecha_retiro"]
    ).all()

    # ====================================================
    # VALIDACIÓN DE DÍAS DE AUSENCIA
    # ====================================================

    leves = casos[
        casos["tipo"] == "Leve"
    ]

    graves = casos[
        casos["tipo"] == "Grave"
    ]

    assert leves["dias_ausencia"].between(
        0,
        10
    ).all()

    assert graves["dias_ausencia"].between(
        10,
        60
    ).all()

def validar_facturacion(
    facturacion,
    clientes,
    trabajadores_activos_mensuales
):
    """
    Valida estructura, granularidad y coherencia
    de la facturación.
    """

    assert len(facturacion) == 1080

    assert not facturacion.duplicated(
        subset=[
            "id_cliente",
            "periodo"
        ]
    ).any()

    assert facturacion["id_cliente"].isin(
        clientes["id_cliente"]
    ).all()

    assert (
        facturacion["trabajadores_activos"] > 0
    ).all()

    assert (
        facturacion["valor_contrato"] > 0
    ).all()

    assert facturacion["periodo"].between(
        FECHA_INICIO_ANALISIS,
        FECHA_FIN_ANALISIS
    ).all()

    # Verificar que trabajadores_activos coincide
    # exactamente con la tabla mensual ya validada.
    comparacion = facturacion.merge(
        trabajadores_activos_mensuales,
        on=[
            "id_cliente",
            "periodo"
        ],
        suffixes=(
            "_facturacion",
            "_original"
        )
    )

    assert (
        comparacion[
            "trabajadores_activos_facturacion"
        ]
        ==
        comparacion[
            "trabajadores_activos_original"
        ]
    ).all()


def validar_prevencion(
    prevencion,
    clientes,
    trabajadores_activos_mensuales
):
    """
    Valida integridad referencial y coherencia
    temporal de las actividades preventivas.
    """

    assert prevencion[
        "id_actividad"
    ].is_unique

    assert prevencion[
        "id_cliente"
    ].isin(
        clientes["id_cliente"]
    ).all()

    assert prevencion[
        "fecha"
    ].between(
        FECHA_INICIO_ANALISIS,
        FECHA_FIN_ANALISIS
    ).all()

    assert prevencion[
        "tipo"
    ].isin(
        TIPOS_PREVENCION
    ).all()

    assert (
        prevencion[
            "participantes"
        ] > 0
    ).all()

    # Crear el periodo mensual correspondiente
    # a cada actividad.
    validacion = prevencion.copy()

    validacion["periodo"] = (
        validacion["fecha"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    validacion = validacion.merge(
        trabajadores_activos_mensuales,
        on=[
            "id_cliente",
            "periodo"
        ],
        how="left"
    )

    assert validacion[
        "trabajadores_activos"
    ].notna().all()

    # Ninguna actividad puede tener más participantes
    # que trabajadores activos en ese mes.
    assert (
        validacion["participantes"]
        <= validacion["trabajadores_activos"]
    ).all()

@st.cache_data
def cargar_datos():
    """
    Genera y valida todas las tablas sintéticas utilizadas
    por el dashboard.

    Se utiliza cache para evitar regenerar los datos cada vez
    que el usuario modifica un filtro de Streamlit.
    """

    clientes = generar_clientes()
    validar_clientes(clientes)

    parametros_clientes = generar_parametros_clientes(
        clientes
    )
    validar_parametros_clientes(
        parametros_clientes
    )

    trabajadores_activos_mensuales = (
        generar_trabajadores_activos_mensuales(
            parametros_clientes
        )
    )

    validar_trabajadores_activos_mensuales(
        trabajadores_activos_mensuales
    )

    trabajadores, historial_trabajadores = (
        generar_trabajadores(
            clientes,
            trabajadores_activos_mensuales
        )
    )

    validar_trabajadores(
        trabajadores,
        historial_trabajadores,
        clientes,
        trabajadores_activos_mensuales
    )

    casos = generar_casos(
        clientes,
        trabajadores_activos_mensuales,
        historial_trabajadores
    )

    validar_casos(
        casos,
        clientes,
        historial_trabajadores
    )

    facturacion = generar_facturacion(
        clientes,
        trabajadores_activos_mensuales
    )

    validar_facturacion(
        facturacion,
        clientes,
        trabajadores_activos_mensuales
    )

    prevencion = generar_prevencion(
        clientes,
        parametros_clientes,
        trabajadores_activos_mensuales
    )

    validar_prevencion(
        prevencion,
        clientes,
        trabajadores_activos_mensuales
    )

    return (
        clientes,
        trabajadores,
        casos,
        facturacion,
        prevencion,
    )

def formatear_numero(valor, decimales=0):
    """
    Formato numérico con convención española/colombiana:
    punto para miles y coma para decimales.
    """

    formato = f"{valor:,.{decimales}f}"

    return (
        formato
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def formatear_moneda(valor):
    """
    Formatea valores monetarios de manera compacta.
    """

    if valor >= 1_000_000:
        return (
            f"${formatear_numero(valor / 1_000_000, 1)} M"
        )

    if valor >= 1_000:
        return (
            f"${formatear_numero(valor / 1_000, 1)} mil"
        )

    return f"${formatear_numero(valor, 0)}"


def formatear_delta_porcentual(valor):
    """
    Devuelve None cuando la variación no es calculable.
    """

    if pd.isna(valor):
        return None

    signo = "+" if valor > 0 else ""

    return (
        f"{signo}{formatear_numero(valor, 1)} % "
        f"vs. periodo anterior"
    )


def formatear_delta_tasa(valor):
    """
    Variación de la tasa expresada en puntos.
    """

    if pd.isna(valor):
        return None

    signo = "+" if valor > 0 else ""

    return (
        f"{signo}{formatear_numero(valor, 2)} pts "
        f"vs. periodo anterior"
    )

def construir_dashboard():

        # ========================================================
    # ESTILO VISUAL
    # ========================================================

    st.markdown(
        """
        <style>

        /* ----------------------------------------------------
           FONDO GENERAL
        ---------------------------------------------------- */

        .stApp {
            background-color: #F4F7FA;
        }

        .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }


        /* ----------------------------------------------------
           CABECERA
        ---------------------------------------------------- */

        .sura-header {
            background: linear-gradient(
                110deg,
                #003B7A 0%,
                #005CA9 65%,
                #0077B6 100%
            );

            padding: 28px 34px;
            border-radius: 18px;
            margin-bottom: 24px;

            box-shadow:
                0 8px 24px rgba(0, 59, 122, 0.16);
        }

        .sura-header-kicker {
            color: #70D6E3;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .sura-header-title {
            color: white;
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
            line-height: 1.15;
        }

        .sura-header-subtitle {
            color: rgba(255, 255, 255, 0.82);
            font-size: 0.95rem;
            margin-top: 9px;
            margin-bottom: 0;
        }


        /* ----------------------------------------------------
           TÍTULO DE FILTROS
        ---------------------------------------------------- */

        .filter-title {
            color: #003B7A;
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-top: 4px;
            margin-bottom: 8px;
        }


        /* ----------------------------------------------------
           SELECTORES
        ---------------------------------------------------- */

        div[data-baseweb="select"] > div {
            background-color: #FFFFFF;
            border-radius: 10px;
            border-color: #DCE5ED;
        }

        div[data-testid="stDateInput"] input {
            background-color: #FFFFFF;
            border-radius: 10px;
        }

        label[data-testid="stWidgetLabel"] p {
            color: #36546D;
            font-weight: 600;
        }


        /* ----------------------------------------------------
           TARJETAS KPI
        ---------------------------------------------------- */

        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E1E8EE;
            border-top: 4px solid #0077B6;
            border-radius: 14px;

            padding: 20px 22px 18px 22px;

            box-shadow:
                0 4px 14px rgba(32, 59, 78, 0.07);
        }

        div[data-testid="stMetricLabel"] {
            color: #49677D;
            font-weight: 600;
        }

        div[data-testid="stMetricValue"] {
            color: #003B7A;
            font-weight: 700;
        }


        /* ----------------------------------------------------
           DIVISORES
        ---------------------------------------------------- */

        hr {
            border-color: #DCE5ED !important;
        }


        /* ----------------------------------------------------
           DATAFRAMES Y GRÁFICOS
        ---------------------------------------------------- */

        div[data-testid="stDataFrame"] {
            background: white;
            border-radius: 14px;
            overflow: hidden;

            box-shadow:
                0 4px 14px rgba(32, 59, 78, 0.06);
        }


        /* ----------------------------------------------------
           SUBTÍTULOS
        ---------------------------------------------------- */

        h2, h3 {
            color: #003B7A !important;
        }


        /* ----------------------------------------------------
           OCULTAR ELEMENTOS STREAMLIT QUE NO APORTAN
        ---------------------------------------------------- */

        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    (
        clientes,
        trabajadores,
        casos,
        facturacion,
        prevencion,
    ) = cargar_datos()

    # ========================================================
    # CABECERA
    # ========================================================

    st.markdown(
        '<div class="sura-header">'
        '<div class="sura-header-kicker">PRUEBA TÉCNICA SURA</div>'
        '<div class="sura-header-title">Monitoreo operativo de casos</div>'
        '<div class="sura-header-subtitle">'
        'Tablero analítico · Información sintética · Enero 2024 – Diciembre 2026'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # ========================================================
    # FILTROS
    # ========================================================

    col_pregunta, col_tipo, col_periodo, col_cliente = (
        st.columns(
            [2.4, 1.2, 1.8, 1.8]
        )
    )

    pregunta = col_pregunta.selectbox(
        "Pregunta de análisis",
        [
            "Panorama general",
            "Impacto de los casos graves",
            "Clientes de mayor riesgo",
            "Clientes de menor riesgo",
        ]
    )

    tipo_periodo = col_tipo.selectbox(
        "Periodo",
        [
            "Día",
            "Semana",
            "Mes",
            "Año",
        ],
        index=2
    )

    # ========================================================
    # SELECTOR DINÁMICO DEL PERIODO
    # ========================================================

    meses_es = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }

    if tipo_periodo == "Día":

        fecha_referencia = col_periodo.date_input(
            "Fecha",
            value=FECHA_FIN_ANALISIS.date(),
            min_value=FECHA_INICIO_ANALISIS.date(),
            max_value=FECHA_FIN_ANALISIS.date(),
        )

        fecha_referencia = pd.Timestamp(
            fecha_referencia
        )

    elif tipo_periodo == "Semana":

        # Solo semanas completas dentro del rango.
        semanas = list(
            pd.date_range(
                start=FECHA_INICIO_ANALISIS,
                end=pd.Timestamp("2026-12-21"),
                freq="W-MON"
            )
        )

        fecha_referencia = col_periodo.selectbox(
            "Semana",
            semanas,
            index=len(semanas) - 1,
            format_func=lambda fecha: (
                f"{fecha.strftime('%d/%m/%Y')} - "
                f"{(fecha + pd.Timedelta(days=6)).strftime('%d/%m/%Y')}"
            )
        )

    elif tipo_periodo == "Mes":

        meses = list(
            pd.date_range(
                start=FECHA_INICIO_ANALISIS,
                end=FECHA_FIN_ANALISIS,
                freq="MS"
            )
        )

        fecha_referencia = col_periodo.selectbox(
            "Mes",
            meses,
            index=len(meses) - 1,
            format_func=lambda fecha: (
                f"{meses_es[fecha.month]} {fecha.year}"
            )
        )

    else:

        anio = col_periodo.selectbox(
            "Año",
            [2024, 2025, 2026],
            index=2
        )

        fecha_referencia = pd.Timestamp(
            year=anio,
            month=1,
            day=1
        )

    # ========================================================
    # CLIENTES DISPONIBLES SEGÚN PREGUNTA
    # ========================================================

    ids_disponibles = obtener_clientes_contexto(
        clientes,
        pregunta,
        None
    )

    clientes_disponibles = (
        clientes[
            clientes["id_cliente"].isin(
                ids_disponibles
            )
        ]
        .sort_values("nombre")
    )

    nombres_clientes = (
        clientes_disponibles[
            "nombre"
        ]
        .tolist()
    )

    cliente_seleccionado = (
        col_cliente.selectbox(
            "Cliente",
            ["Todos"] + nombres_clientes
        )
    )

    if cliente_seleccionado == "Todos":

        id_cliente = "Todos"

    else:

        id_cliente = (
            clientes_disponibles.loc[
                clientes_disponibles["nombre"]
                == cliente_seleccionado,
                "id_cliente"
            ]
            .iloc[0]
        )

    # ========================================================
    # KPI
    # ========================================================

    resultado = calcular_kpis_periodo(
        clientes=clientes,
        casos=casos,
        facturacion=facturacion,
        pregunta=pregunta,
        tipo_periodo=tipo_periodo,
        fecha_referencia=fecha_referencia,
        id_cliente=id_cliente
    )

    st.divider()

    kpi_1, kpi_2, kpi_3 = st.columns(3)

    kpi_1.metric(
        label="Total de casos",
        value=formatear_numero(
            resultado["total_casos"]
        ),
        delta=formatear_delta_porcentual(
            resultado["variacion_casos"]
        ),
        delta_color="normal"
    )

    kpi_2.metric(
        label="Costo total",
        value=formatear_moneda(
            resultado["costo_total"]
        ),
        delta=formatear_delta_porcentual(
            resultado["variacion_costo"]
        ),
        delta_color="normal"
    )

    tasa = resultado[
        "tasa_incidencia"
    ]

    valor_tasa = (
        f"{formatear_numero(tasa, 2)} / 100"
        if not pd.isna(tasa)
        else "—"
    )

    kpi_3.metric(
        label="Tasa de incidencia",
        value=valor_tasa,
        delta=formatear_delta_tasa(
            resultado["variacion_tasa"]
        ),
        delta_color="normal"
    )

    # ========================================================
    # TENDENCIA MENSUAL - ÚLTIMOS 12 MESES
    # ========================================================

    tendencia = preparar_tendencia_12_meses(
        clientes=clientes,
        casos=casos,
        pregunta=pregunta,
        tipo_periodo=tipo_periodo,
        fecha_referencia=fecha_referencia,
        id_cliente=id_cliente
    )

    st.markdown(
        '<div style="margin-top:28px; margin-bottom:8px;">'
        '<div style="color:#003B7A; font-size:1.15rem; font-weight:700;">'
        'Tendencia mensual de casos'
        '</div>'
        '<div style="color:#6B7F90; font-size:0.85rem; margin-top:3px;">'
        'Últimos 12 meses frente al promedio histórico'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    fig_tendencia = go.Figure()

    # Línea principal de casos
    fig_tendencia.add_trace(
        go.Scatter(
            x=tendencia["periodo"],
            y=tendencia["casos"],
            mode="lines+markers",
            name="Casos",
            line=dict(
                color="#0077B6",
                width=3
            ),
            marker=dict(
                size=7,
                color="#0077B6"
            ),
            hovertemplate=(
                "<b>%{x|%b %Y}</b><br>"
                "Casos: %{y}<extra></extra>"
            )
        )
    )

    # Promedio histórico
    fig_tendencia.add_trace(
        go.Scatter(
            x=tendencia["periodo"],
            y=tendencia["promedio_historico"],
            mode="lines",
            name="Promedio histórico",
            line=dict(
                color="#70D6E3",
                width=2,
                dash="dash"
            ),
            hovertemplate=(
                "Promedio histórico: "
                "%{y:.1f}<extra></extra>"
            )
        )
    )

    fig_tendencia.update_layout(
        height=380,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=25,
            b=20
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            title=None,
            showgrid=False,
            tickformat="%b\n%Y"
        ),
        yaxis=dict(
            title="Número de casos",
            gridcolor="#E9EFF4",
            zeroline=False
        )
    )

    st.plotly_chart(
        fig_tendencia,
        use_container_width=True
    )

    # ========================================================
    # DATOS PARA SEGUNDA FILA
    # ========================================================

    top_10 = preparar_top_10_clientes(
        clientes=clientes,
        casos=casos,
        pregunta=pregunta,
        tipo_periodo=tipo_periodo,
        fecha_referencia=fecha_referencia,
        id_cliente=id_cliente
    )

    distribucion = preparar_distribucion_casos(
        clientes=clientes,
        casos=casos,
        pregunta=pregunta,
        tipo_periodo=tipo_periodo,
        fecha_referencia=fecha_referencia,
        id_cliente=id_cliente
    )

    st.markdown(
        '<div style="margin-top:24px;"></div>',
        unsafe_allow_html=True
    )

    col_top, col_distribucion = st.columns(
        [1, 1],
        gap="large"
    )

    # ========================================================
    # TOP 10 CLIENTES
    # ========================================================

    with col_top:

        st.markdown(
            '<div style="color:#003B7A; font-size:1.15rem; font-weight:700;">'
            'Clientes con mayor número de casos'
            '</div>'
            '<div style="color:#6B7F90; font-size:0.85rem; margin-top:3px; margin-bottom:12px;">'
            'Top 10 del periodo y contexto seleccionados'
            '</div>',
            unsafe_allow_html=True
        )

        if top_10.empty:

            st.info(
                "No hay casos para la selección actual."
            )

        else:

            tabla_top = top_10.rename(
                columns={
                    "nombre": "Cliente",
                    "casos": "Casos",
                    "clase_riesgo": "Clase de riesgo"
                }
            )

            st.dataframe(
                tabla_top,
                hide_index=True,
                use_container_width=True,
                height=390
            )

    # ========================================================
    # DISTRIBUCIÓN POR TIPO Y RIESGO
    # ========================================================

    with col_distribucion:

        st.markdown(
            '<div style="color:#003B7A; font-size:1.15rem; font-weight:700;">'
            'Distribución de casos'
            '</div>'
            '<div style="color:#6B7F90; font-size:0.85rem; margin-top:3px; margin-bottom:12px;">'
            'Casos leves y graves por clase de riesgo'
            '</div>',
            unsafe_allow_html=True
        )

        fig_distribucion = go.Figure()

        datos_leves = distribucion[
            distribucion["tipo"] == "Leve"
        ]

        datos_graves = distribucion[
            distribucion["tipo"] == "Grave"
        ]

        fig_distribucion.add_trace(
            go.Bar(
                x=datos_leves["clase_riesgo"],
                y=datos_leves["casos"],
                name="Leve",
                marker_color="#0077B6",
                text=datos_leves["casos"],
                textposition="outside",
                cliponaxis= False,
                hovertemplate=(
                    "Clase de riesgo %{x}<br>"
                    "Casos leves: %{y}"
                    "<extra></extra>"
                )
            )
        )
        

        fig_distribucion.add_trace(
            go.Bar(
                x=datos_graves["clase_riesgo"],
                y=datos_graves["casos"],
                name="Grave",
                marker_color="#F5B335",
                text=datos_graves["casos"],
                textposition="outside",
                cliponaxis= False,
                hovertemplate=(
                    "Clase de riesgo %{x}<br>"
                    "Casos graves: %{y}"
                    "<extra></extra>"
                )
            )
        )

        fig_distribucion.update_layout(
            barmode="group",
            height=390,
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=20
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                title="Clase de riesgo",
                tickmode="array",
                tickvals=[1, 2, 3, 4, 5],
                showgrid=False,
                tickfont=dict(
                    color="#35566F",
                    size=12
                ),
                title_font=dict(
                    color="#35566F",
                    size=13
                )
            ),
            yaxis=dict(
                title="Número de casos",
                gridcolor="#E9EFF4",
                zeroline=False
            )
        )

        st.plotly_chart(
            fig_distribucion,
            use_container_width=True
        )

# ============================================================
# FILTROS Y KPIS
# ============================================================

def obtener_rango_periodo(tipo_periodo, fecha_referencia):
    """
    Obtiene el inicio y fin del periodo seleccionado.

    Tipos permitidos:
    - Día
    - Semana: lunes a domingo
    - Mes
    - Año
    """

    fecha = pd.Timestamp(fecha_referencia).normalize()

    if tipo_periodo == "Día":

        inicio = fecha
        fin = fecha

    elif tipo_periodo == "Semana":

        inicio = fecha - pd.Timedelta(
            days=fecha.weekday()
        )

        fin = inicio + pd.Timedelta(days=6)

    elif tipo_periodo == "Mes":

        inicio = fecha.replace(day=1)

        fin = (
            inicio
            + pd.offsets.MonthEnd(0)
        )

    elif tipo_periodo == "Año":

        inicio = pd.Timestamp(
            year=fecha.year,
            month=1,
            day=1
        )

        fin = pd.Timestamp(
            year=fecha.year,
            month=12,
            day=31
        )

    else:
        raise ValueError(
            "Tipo de periodo no válido."
        )

    return inicio, fin

def obtener_periodo_anterior(
    tipo_periodo,
    inicio_actual,
    fin_actual
):
    """
    Devuelve el periodo calendario inmediatamente anterior
    del mismo tipo que el periodo seleccionado.
    """

    if tipo_periodo == "Día":

        inicio_anterior = (
            inicio_actual
            - pd.Timedelta(days=1)
        )

        fin_anterior = inicio_anterior

    elif tipo_periodo == "Semana":

        inicio_anterior = (
            inicio_actual
            - pd.Timedelta(days=7)
        )

        fin_anterior = (
            fin_actual
            - pd.Timedelta(days=7)
        )

    elif tipo_periodo == "Mes":

        inicio_anterior = (
            inicio_actual
            - pd.offsets.MonthBegin(1)
        )

        fin_anterior = (
            inicio_actual
            - pd.Timedelta(days=1)
        )

    elif tipo_periodo == "Año":

        inicio_anterior = pd.Timestamp(
            year=inicio_actual.year - 1,
            month=1,
            day=1
        )

        fin_anterior = pd.Timestamp(
            year=inicio_actual.year - 1,
            month=12,
            day=31
        )

    else:
        raise ValueError(
            "Tipo de periodo no válido."
        )

    return inicio_anterior, fin_anterior

def obtener_clientes_contexto(
    clientes,
    pregunta,
    id_cliente=None
):
    """
    Determina qué clientes forman parte del contexto
    de análisis según la pregunta seleccionada y
    el filtro de cliente.
    """

    df = clientes.copy()

    if pregunta == "Clientes de mayor riesgo":

        df = df[
            df["clase_riesgo"].isin([4, 5])
        ]

    elif pregunta == "Clientes de menor riesgo":

        df = df[
            df["clase_riesgo"].isin([1, 2])
        ]

    elif pregunta not in [
        "Panorama general",
        "Impacto de los casos graves",
    ]:
        raise ValueError(
            "Pregunta de análisis no válida."
        )

    if (
        id_cliente is not None
        and id_cliente != "Todos"
    ):

        df = df[
            df["id_cliente"] == id_cliente
        ]

    return df["id_cliente"].tolist()

def filtrar_casos_contexto(
    casos,
    ids_clientes,
    pregunta,
    fecha_inicio,
    fecha_fin
):
    """
    Filtra los casos según clientes, pregunta
    y periodo seleccionado.
    """

    df = casos[
        casos["id_cliente"].isin(
            ids_clientes
        )
    ].copy()

    df = df[
        df["fecha_ocurrencia"].between(
            fecha_inicio,
            fecha_fin
        )
    ]

    if pregunta == "Impacto de los casos graves":

        df = df[
            df["tipo"] == "Grave"
        ]

    return df

def calcular_trabajadores_expuestos(
    facturacion,
    ids_clientes,
    fecha_inicio,
    fecha_fin
):
    """
    Calcula la plantilla promedio expuesta durante
    el periodo seleccionado.

    Los trabajadores activos mensuales se ponderan
    por el número de días del mes incluidos en
    el periodo analizado.
    """

    if len(ids_clientes) == 0:
        return 0.0

    df = facturacion[
        facturacion["id_cliente"].isin(
            ids_clientes
        )
    ].copy()

    dias_periodo = (
        fecha_fin - fecha_inicio
    ).days + 1

    exposicion_acumulada = 0.0

    for _, fila in df.iterrows():

        inicio_mes = fila["periodo"]

        fin_mes = (
            inicio_mes
            + pd.offsets.MonthEnd(0)
        )

        inicio_solapamiento = max(
            inicio_mes,
            fecha_inicio
        )

        fin_solapamiento = min(
            fin_mes,
            fecha_fin
        )

        if (
            inicio_solapamiento
            <= fin_solapamiento
        ):

            dias_solapamiento = (
                fin_solapamiento
                - inicio_solapamiento
            ).days + 1

            exposicion_acumulada += (
                fila["trabajadores_activos"]
                * dias_solapamiento
            )

    if dias_periodo <= 0:
        return 0.0

    trabajadores_promedio = (
        exposicion_acumulada
        / dias_periodo
    )

    return trabajadores_promedio

def calcular_kpis_periodo(
    clientes,
    casos,
    facturacion,
    pregunta,
    tipo_periodo,
    fecha_referencia,
    id_cliente=None
):
    """
    Calcula los tres KPI obligatorios y sus
    comparaciones frente al periodo anterior.

    KPI:
    - Total de casos
    - Costo total
    - Tasa de incidencia por cada 100 trabajadores
    """

    # ====================================================
    # PERIODO ACTUAL
    # ====================================================

    inicio_actual, fin_actual = (
        obtener_rango_periodo(
            tipo_periodo,
            fecha_referencia
        )
    )

    # ====================================================
    # PERIODO ANTERIOR
    # ====================================================

    inicio_anterior, fin_anterior = (
        obtener_periodo_anterior(
            tipo_periodo,
            inicio_actual,
            fin_actual
        )
    )

    # ====================================================
    # CLIENTES DEL CONTEXTO
    # ====================================================

    ids_clientes = (
        obtener_clientes_contexto(
            clientes,
            pregunta,
            id_cliente
        )
    )

    # ====================================================
    # CASOS ACTUALES
    # ====================================================

    casos_actuales = (
        filtrar_casos_contexto(
            casos,
            ids_clientes,
            pregunta,
            inicio_actual,
            fin_actual
        )
    )

    total_casos_actual = len(
        casos_actuales
    )

    costo_actual = (
        casos_actuales["costo"].sum()
    )

    trabajadores_actuales = (
        calcular_trabajadores_expuestos(
            facturacion,
            ids_clientes,
            inicio_actual,
            fin_actual
        )
    )

    tasa_actual = (
        total_casos_actual
        / trabajadores_actuales
        * 100
        if trabajadores_actuales > 0
        else np.nan
    )

    # ====================================================
    # ¿EXISTE PERIODO ANTERIOR?
    # ====================================================

    existe_periodo_anterior = (
        inicio_anterior
        >= FECHA_INICIO_ANALISIS
        and fin_anterior
        <= FECHA_FIN_ANALISIS
    )

    if not existe_periodo_anterior:

        return {
            "inicio_actual": inicio_actual,
            "fin_actual": fin_actual,
            "inicio_anterior": inicio_anterior,
            "fin_anterior": fin_anterior,
            "total_casos": total_casos_actual,
            "costo_total": costo_actual,
            "tasa_incidencia": tasa_actual,
            "variacion_casos": np.nan,
            "variacion_costo": np.nan,
            "variacion_tasa": np.nan,
        }

    # ====================================================
    # PERIODO ANTERIOR
    # ====================================================

    casos_anteriores = (
        filtrar_casos_contexto(
            casos,
            ids_clientes,
            pregunta,
            inicio_anterior,
            fin_anterior
        )
    )

    total_casos_anterior = len(
        casos_anteriores
    )

    costo_anterior = (
        casos_anteriores["costo"].sum()
    )

    trabajadores_anteriores = (
        calcular_trabajadores_expuestos(
            facturacion,
            ids_clientes,
            inicio_anterior,
            fin_anterior
        )
    )

    tasa_anterior = (
        total_casos_anterior
        / trabajadores_anteriores
        * 100
        if trabajadores_anteriores > 0
        else np.nan
    )

    # ====================================================
    # VARIACIONES
    # ====================================================

    variacion_casos = (
        (
            total_casos_actual
            - total_casos_anterior
        )
        / total_casos_anterior
        * 100
        if total_casos_anterior > 0
        else np.nan
    )

    variacion_costo = (
        (
            costo_actual
            - costo_anterior
        )
        / costo_anterior
        * 100
        if costo_anterior > 0
        else np.nan
    )

    # Para incidencia mostramos diferencia en puntos
    # de tasa, no variación porcentual.
    variacion_tasa = (
        tasa_actual - tasa_anterior
        if (
            not pd.isna(tasa_actual)
            and not pd.isna(tasa_anterior)
        )
        else np.nan
    )

    return {
        "inicio_actual": inicio_actual,
        "fin_actual": fin_actual,
        "inicio_anterior": inicio_anterior,
        "fin_anterior": fin_anterior,
        "total_casos": total_casos_actual,
        "costo_total": costo_actual,
        "tasa_incidencia": tasa_actual,
        "variacion_casos": variacion_casos,
        "variacion_costo": variacion_costo,
        "variacion_tasa": variacion_tasa,
    }

def preparar_tendencia_12_meses(
    clientes,
    casos,
    pregunta,
    tipo_periodo,
    fecha_referencia,
    id_cliente=None
):
    """
    Prepara la tendencia mensual de casos de los últimos
    12 meses hasta el periodo seleccionado.

    Reglas:
    - No utiliza información posterior al periodo seleccionado.
    - Los meses anteriores se muestran completos.
    - El mes actual puede ser parcial.
    - El promedio histórico utiliza únicamente meses completos,
      evitando comparar un mes parcial contra meses completos.
    """

    _, fin_actual = obtener_rango_periodo(
        tipo_periodo,
        fecha_referencia
    )

    # No permitir información posterior al rango disponible.
    fin_analisis = min(
        pd.Timestamp(fin_actual),
        FECHA_FIN_ANALISIS
    )

    mes_fin = (
        fin_analisis
        .to_period("M")
        .to_timestamp()
    )

    fin_mes_seleccionado = (
        mes_fin
        + pd.offsets.MonthEnd(0)
    )

    mes_inicio_12 = (
        mes_fin
        - pd.DateOffset(months=11)
    )

    mes_inicio_12 = max(
        mes_inicio_12,
        FECHA_INICIO_ANALISIS
    )

    ids_clientes = obtener_clientes_contexto(
        clientes,
        pregunta,
        id_cliente
    )

    # ====================================================
    # CASOS HASTA EL FINAL REAL DEL PERIODO SELECCIONADO
    # ====================================================

    casos_hasta_fecha = filtrar_casos_contexto(
        casos,
        ids_clientes,
        pregunta,
        FECHA_INICIO_ANALISIS,
        fin_analisis
    )

    casos_hasta_fecha = casos_hasta_fecha.assign(
        periodo=lambda x:
        x["fecha_ocurrencia"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    # ====================================================
    # TENDENCIA DE LOS ÚLTIMOS 12 MESES
    # ====================================================

    meses_12 = pd.date_range(
        start=mes_inicio_12,
        end=mes_fin,
        freq="MS"
    )

    casos_mensuales = (
        casos_hasta_fecha
        .groupby("periodo")
        .size()
        .reindex(
            meses_12,
            fill_value=0
        )
    )

    # ====================================================
    # PROMEDIO HISTÓRICO
    # ====================================================

    # Si el periodo seleccionado llega al último día del mes,
    # podemos considerar ese mes como completo.
    if fin_analisis.normalize() == fin_mes_seleccionado.normalize():

        ultimo_mes_historico = mes_fin

    else:

        ultimo_mes_historico = (
            mes_fin
            - pd.DateOffset(months=1)
        )

    if ultimo_mes_historico >= FECHA_INICIO_ANALISIS:

        meses_historicos = pd.date_range(
            start=FECHA_INICIO_ANALISIS,
            end=ultimo_mes_historico,
            freq="MS"
        )

        casos_historicos = (
            casos_hasta_fecha[
                casos_hasta_fecha["periodo"]
                <= ultimo_mes_historico
            ]
            .groupby("periodo")
            .size()
            .reindex(
                meses_historicos,
                fill_value=0
            )
        )

        promedio_historico = (
            casos_historicos.mean()
        )

    else:

        promedio_historico = np.nan

    tendencia = pd.DataFrame(
        {
            "periodo": meses_12,
            "casos": casos_mensuales.values,
        }
    )

    tendencia["promedio_historico"] = (
        promedio_historico
    )

    return tendencia

def preparar_top_10_clientes(
    clientes,
    casos,
    pregunta,
    tipo_periodo,
    fecha_referencia,
    id_cliente=None
):
    """
    Obtiene los 10 clientes con mayor número de casos
    dentro del contexto y periodo seleccionados.
    """

    inicio, fin = obtener_rango_periodo(
        tipo_periodo,
        fecha_referencia
    )

    ids_clientes = obtener_clientes_contexto(
        clientes,
        pregunta,
        id_cliente
    )

    casos_filtrados = filtrar_casos_contexto(
        casos,
        ids_clientes,
        pregunta,
        inicio,
        fin
    )

    if casos_filtrados.empty:

        return pd.DataFrame(
            columns=[
                "nombre",
                "casos",
                "clase_riesgo"
            ]
        )

    ranking = (
        casos_filtrados
        .groupby("id_cliente")
        .size()
        .reset_index(
            name="casos"
        )
        .merge(
            clientes[
                [
                    "id_cliente",
                    "nombre",
                    "clase_riesgo"
                ]
            ],
            on="id_cliente",
            how="left"
        )
        .sort_values(
            by=[
                "casos",
                "nombre"
            ],
            ascending=[
                False,
                True
            ]
        )
        .head(10)
        .reset_index(drop=True)
    )

    return ranking[
        [
            "nombre",
            "casos",
            "clase_riesgo"
        ]
    ]

def preparar_distribucion_casos(
    clientes,
    casos,
    pregunta,
    tipo_periodo,
    fecha_referencia,
    id_cliente=None
):
    """
    Calcula la distribución de casos por:
    - clase de riesgo 1 a 5
    - tipo Leve / Grave

    Siempre devuelve las cinco clases y ambos tipos,
    incluso cuando alguna combinación tenga cero casos.
    """

    inicio, fin = obtener_rango_periodo(
        tipo_periodo,
        fecha_referencia
    )

    ids_clientes = obtener_clientes_contexto(
        clientes,
        pregunta,
        id_cliente
    )

    casos_filtrados = filtrar_casos_contexto(
        casos,
        ids_clientes,
        pregunta,
        inicio,
        fin
    )

    casos_filtrados = casos_filtrados.merge(
        clientes[
            [
                "id_cliente",
                "clase_riesgo"
            ]
        ],
        on="id_cliente",
        how="left"
    )

    indice_completo = pd.MultiIndex.from_product(
        [
            [1, 2, 3, 4, 5],
            ["Leve", "Grave"]
        ],
        names=[
            "clase_riesgo",
            "tipo"
        ]
    )

    distribucion = (
        casos_filtrados
        .groupby(
            [
                "clase_riesgo",
                "tipo"
            ]
        )
        .size()
        .reindex(
            indice_completo,
            fill_value=0
        )
        .reset_index(
            name="casos"
        )
    )

    return distribucion

# ============================================================
# PRUEBA LOCAL
# ============================================================

if __name__ == "__main__":
    construir_dashboard()

    clientes = generar_clientes()
    validar_clientes(clientes)

    parametros_clientes = generar_parametros_clientes(clientes)
    validar_parametros_clientes(parametros_clientes)

    trabajadores_activos_mensuales = (
        generar_trabajadores_activos_mensuales(
            parametros_clientes
        )
    )

    validar_trabajadores_activos_mensuales(
        trabajadores_activos_mensuales
    )

    trabajadores, historial_trabajadores = generar_trabajadores(
        clientes,
        trabajadores_activos_mensuales
    )

    validar_trabajadores(
        trabajadores,
        historial_trabajadores,
        clientes,
        trabajadores_activos_mensuales
    )

    casos = generar_casos(
        clientes,
        trabajadores_activos_mensuales,
        historial_trabajadores
    )
    validar_casos(
        casos,
        clientes,
        historial_trabajadores
    )

    facturacion = generar_facturacion(
        clientes,
        trabajadores_activos_mensuales
    )

    validar_facturacion(
        facturacion,
        clientes,
        trabajadores_activos_mensuales
    )


    prevencion = generar_prevencion(
        clientes,
        parametros_clientes,
        trabajadores_activos_mensuales
    )

    validar_prevencion(
        prevencion,
        clientes,
        trabajadores_activos_mensuales
    )
    