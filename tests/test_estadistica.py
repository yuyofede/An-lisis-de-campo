"""Pruebas de las fórmulas de diseño muestral."""

import math

import pytest

from muestreo import estadistica as E


def test_z_para_confianzas_estandar():
    assert E.z_para_confianza(0.90) == pytest.approx(1.6448536, rel=1e-6)
    assert E.z_para_confianza(0.95) == pytest.approx(1.9599640, rel=1e-6)
    assert E.z_para_confianza(0.99) == pytest.approx(2.5758293, rel=1e-6)


def test_confianza_para_z_es_inversa():
    for confianza in (0.80, 0.90, 0.95, 0.99):
        z = E.z_para_confianza(confianza)
        assert E.confianza_para_z(z) == pytest.approx(confianza, abs=1e-9)


def test_tamano_poblacion_infinita():
    res = E.calcular_tamano_muestra(poblacion=None, error=0.05, confianza=0.95)
    esperado = E.z_para_confianza(0.95) ** 2 * 0.25 / 0.05 ** 2
    assert res.n_infinita == pytest.approx(esperado)
    assert res.muestra == 385  # siempre hacia arriba
    assert res.muestra == math.ceil(res.n_exacta - 1e-9)
    assert res.poblacion_infinita is True
    assert res.fraccion_muestral == 0.0


def test_tamano_poblacion_finita_aplica_correccion():
    res = E.calcular_tamano_muestra(poblacion=1000, error=0.05, confianza=0.95)
    assert res.n_infinita == pytest.approx(384.1459, abs=1e-3)
    assert res.n_exacta < res.n_infinita
    assert res.muestra == 278
    assert res.n_exacta == pytest.approx(
        res.n_infinita / (1 + (res.n_infinita - 1) / 1000), abs=1e-9
    )
    assert 0 < res.factor_correccion < 1
    assert res.fraccion_muestral == pytest.approx(0.278)


def test_tamano_nunca_supera_la_poblacion():
    res = E.calcular_tamano_muestra(poblacion=50, error=0.01, confianza=0.99)
    assert res.muestra == 50
    assert res.fraccion_muestral == 1.0


def test_tamano_con_z_manual():
    res = E.calcular_tamano_muestra(poblacion=None, error=0.05, z=1.96)
    assert res.z == pytest.approx(1.96)
    assert res.confianza == pytest.approx(E.confianza_para_z(1.96))


def test_proporciones_personalizadas():
    res = E.calcular_tamano_muestra(poblacion=None, error=0.03, p=0.30)
    assert res.q == pytest.approx(0.70)
    # p=0.3 produce una muestra menor que el escenario conservador p=0.5
    conservador = E.calcular_tamano_muestra(poblacion=None, error=0.03, p=0.5)
    assert res.muestra < conservador.muestra


def test_errores_de_validacion():
    with pytest.raises(ValueError):
        E.calcular_tamano_muestra(error=0)
    with pytest.raises(ValueError):
        E.calcular_tamano_muestra(error=0.05, p=1.0)
    with pytest.raises(ValueError):
        E.calcular_tamano_muestra(error=0.05, p=0.4, q=0.4)
    with pytest.raises(ValueError):
        E.calcular_tamano_muestra(poblacion=0, error=0.05)
    with pytest.raises(ValueError):
        E.confianza_para_z(-1)


def test_margen_error_infinito_y_finito():
    e_inf = E.margen_error(385, None, confianza=0.95)
    assert e_inf == pytest.approx(0.05, abs=1e-4)
    e_fin = E.margen_error(278, 1000, confianza=0.95)
    assert e_fin == pytest.approx(0.05, abs=1e-4)
    # Con corrección por población finita el error es menor
    assert e_fin < E.margen_error(278, None, confianza=0.95)


def test_margen_error_censo_es_cero():
    assert E.margen_error(500, 500, confianza=0.95) == 0.0
    assert E.margen_error(600, 500, confianza=0.95) == 0.0


def test_confianza_alcanzada_coincide_con_el_diseno():
    conf = E.confianza_alcanzada(385, 0.05, None)
    assert conf == pytest.approx(0.95, abs=1e-3)


def test_comparacion_planeado_vs_real():
    comp = E.comparar_muestras(400, 250, poblacion=5000, confianza=0.95)
    assert comp.muestra_planeada == 400
    assert comp.muestra_real == 250
    assert comp.error_real > comp.error_planeado
    assert comp.diferencia_error > 0
    assert comp.confianza_real < comp.confianza_original
    assert comp.muestra_faltante == 150
    assert comp.logro_muestra == pytest.approx(0.625)


def test_comparacion_muestra_completa():
    comp = E.comparar_muestras(300, 300, poblacion=None, confianza=0.90)
    assert comp.diferencia_error == pytest.approx(0.0, abs=1e-12)
    assert comp.muestra_faltante == 0
    assert comp.logro_muestra == 1.0


def test_tabla_sensibilidad_es_monotona():
    tabla = E.tabla_sensibilidad(poblacion=10_000, confianza=0.95)
    muestras = [f["muestra"] for f in tabla]
    assert len(tabla) == 7
    # A mayor margen de error permitido, menor muestra requerida.
    assert muestras == sorted(muestras, reverse=True)
    assert all(m >= 1 for m in muestras)
