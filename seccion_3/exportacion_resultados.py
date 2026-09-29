import json
from pathlib import Path

import pandas as pd


def exportar_resultados(
    reporte_calidad: dict,
    df_validos: pd.DataFrame,
    df_rechazados: pd.DataFrame,
    detalle_incidencias: pd.DataFrame,
    directorio_salida: str = "salidas"
) -> None:
    """
    Exporta los resultados finales del proceso de calidad:

    - reporte_calidad.json
    - registros_validos.parquet
    - registros_rechazados.xlsx

    El archivo Excel contiene:
        1. registros_rechazados
        2. detalle_rechazos
    """

    ruta_salida = Path(directorio_salida)

    ruta_salida.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # 1. Reporte JSON
    # ========================================================

    ruta_json = (
        ruta_salida
        / "reporte_calidad.json"
    )

    with open(
        ruta_json,
        "w",
        encoding="utf-8"
    ) as archivo_json:

        json.dump(
            reporte_calidad,
            archivo_json,
            ensure_ascii=False,
            indent=4
        )

    # ========================================================
    # 2. Registros válidos - Parquet
    # ========================================================

    ruta_parquet = (
        ruta_salida
        / "registros_validos.parquet"
    )

    df_validos.to_parquet(
        ruta_parquet,
        index=False
    )

    # ========================================================
    # 3. Registros rechazados - Excel
    # ========================================================

    ruta_excel = (
        ruta_salida
        / "registros_rechazados.xlsx"
    )

    with pd.ExcelWriter(
        ruta_excel,
        engine="openpyxl"
    ) as writer:

        df_rechazados.to_excel(
            writer,
            sheet_name="registros_rechazados",
            index=False
        )

        detalle_incidencias.to_excel(
            writer,
            sheet_name="detalle_rechazos",
            index=False
        )

    print(
        "\n=== ARCHIVOS GENERADOS ==="
    )

    print(
        f"JSON: {ruta_json}"
    )

    print(
        f"Parquet: {ruta_parquet}"
    )

    print(
        f"Excel: {ruta_excel}"
    )