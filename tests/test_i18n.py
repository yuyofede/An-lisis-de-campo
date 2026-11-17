"""Pruebas del módulo de internacionalización."""

import pytest

from muestreo import i18n


def test_idiomas_disponibles():
    assert list(i18n.ETIQUETAS_IDIOMA.keys()) == ["es", "en", "no"]


def test_tr_devuelve_traduccion_existente_en_todos_los_idiomas():
    claves = set(i18n.TR["es"].keys())
    for idioma in i18n.IDIOMAS:
        faltantes = claves - set(i18n.TR[idioma].keys())
        assert not faltantes, f"Faltan claves para el idioma {idioma}: {faltantes}"


def test_set_idioma_y_tr():
    i18n.set_idioma("en")
    assert i18n.idioma_actual() == "en"
    assert i18n.t("tamano_muestra") == "Sample size"
    i18n.set_idioma("no")
    assert i18n.t("tamano_muestra") == "Størrelse"
    i18n.set_idioma("es")
    assert i18n.t("tamano_muestra") == "Tamaño de muestra"
