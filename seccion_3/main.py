from datetime import date
from pathlib import Path
import sys

from generacion_datos import (
    generar_datos_base,
    introducir_variaciones_estandarizables,
    introducir_errores_calidad,
    introducir_duplicados_unicidad
)

from validacion_calidad import (
    preparar_datos,
    validar_completitud,
    validar_validez,
    validar_unicidad,
    validar_consistencia,
    validar_oportunidad,
    consolidar_incidencias,
    clasificar_registros,
    generar_reporte_calidad
)

from exportacion_resultados import (
    exportar_resultados
)


def main():

    # Directorio donde se encuentra este archivo
    directorio_base = Path(__file__).resolve().parent

    # Directorio de salida independiente del punto de ejecución
    directorio_salida = directorio_base / "salidas"

    # Fecha de referencia única para toda la ejecución
    fecha_ejecucion = date.today()

    # 1. Generar población base
    df_base = generar_datos_base(
        fecha_ejecucion=fecha_ejecucion
    )

    # 2. Introducir variaciones estandarizables
    (
        df_prueba,
        log_variaciones
    ) = introducir_variaciones_estandarizables(
        df_base
    )

    # 3. Introducir errores controlados
    (
        df_prueba,
        log_errores,
        limite_plausibilidad
    ) = introducir_errores_calidad(
        df=df_prueba,
        df_base=df_base,
        log_variaciones=log_variaciones,
        fecha_ejecucion=fecha_ejecucion
    )

    # 4. Introducir problemas de Unicidad
    (
        df_prueba,
        log_unicidad
    ) = introducir_duplicados_unicidad(
        df=df_prueba,
        log_variaciones=log_variaciones,
        log_errores=log_errores
    )

    # 5. Preparar datos
    df_preparado = preparar_datos(
        df_prueba
    )

    # 6. Ejecutar validaciones
    incidencias_completitud = (
        validar_completitud(
            df_preparado
        )
    )

    incidencias_validez = (
        validar_validez(
            df=df_preparado,
            limite_plausibilidad=limite_plausibilidad
        )
    )

    incidencias_unicidad = (
        validar_unicidad(
            df_preparado
        )
    )

    incidencias_consistencia = (
        validar_consistencia(
            df_preparado
        )
    )

    incidencias_oportunidad = (
        validar_oportunidad(
            df_preparado,
            fecha_ejecucion=fecha_ejecucion
        )
    )

    # 7. Consolidar incidencias
    detalle_incidencias = consolidar_incidencias(
        incidencias_completitud=
            incidencias_completitud,

        incidencias_validez=
            incidencias_validez,

        incidencias_unicidad=
            incidencias_unicidad,

        incidencias_consistencia=
            incidencias_consistencia,

        incidencias_oportunidad=
            incidencias_oportunidad
    )

    # 8. Clasificar registros
    (
        df_validos,
        df_rechazados
    ) = clasificar_registros(
        df=df_preparado,
        detalle_incidencias=detalle_incidencias
    )

    # 9. Generar reporte
    reporte_calidad = generar_reporte_calidad(
        df=df_preparado,
        df_validos=df_validos,
        df_rechazados=df_rechazados,
        detalle_incidencias=detalle_incidencias,
        fecha_ejecucion=fecha_ejecucion
    )

    # 10. Exportar resultados
    exportar_resultados(
        reporte_calidad=reporte_calidad,
        df_validos=df_validos,
        df_rechazados=df_rechazados,
        detalle_incidencias=detalle_incidencias,
        directorio_salida=str(directorio_salida)
    )

    # 11. Resumen final
    print(
        "\n=== PROCESO FINALIZADO ==="
    )

    print(
        f"Registros procesados: "
        f"{len(df_preparado)}"
    )

    print(
        f"Registros válidos: "
        f"{len(df_validos)}"
    )

    print(
        f"Registros rechazados: "
        f"{len(df_rechazados)}"
    )

    print(
        f"Incidencias detectadas: "
        f"{len(detalle_incidencias)}"
    )

if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print(
            "\n=== ERROR EN LA EJECUCIÓN ==="
        )

        print(
            f"{type(error).__name__}: {error}"
        )

        sys.exit(1)