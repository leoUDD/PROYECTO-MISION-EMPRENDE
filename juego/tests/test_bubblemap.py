# juego/tests/test_bubblemap.py
"""Bubble map: reglas de puntaje e idempotencia."""

from django.urls import reverse

from juego.models import BubbleMapRespuesta, Grupo

from .base import BaseJuegoTestCase


def burbuja(texto, tipo="base"):
    return {"tipo": tipo, "titulo": "t", "texto": texto}


class BubbleMapTests(BaseJuegoTestCase):
    def setUp(self):
        super().setUp()
        self.set_fase("f2_bubblemap")
        self.login_alumno(self.grupo)

    def _enviar(self, burbujas, relato="", link=""):
        return self.post_json(reverse("otorgar_tokens_bubblemap"), {
            "burbujas": burbujas,
            "relato": relato,
            "link": link,
        })

    def test_puntaje_nivel_experto(self):
        # 5 burbujas base válidas (>=5 caracteres, <10 palabras para no sumar
        # el bonus de respuestas largas y mantener el cálculo predecible).
        burbujas = [burbuja(f"respuesta corta {i}") for i in range(5)]
        relato = " ".join(["palabra"] * 18)  # >= 18 palabras
        link = "https://ejemplo.cl/fuente"

        datos = self._enviar(burbujas, relato, link).json()

        # 5 válidas + 2 (>=4 válidas) + 3 (>=5 principales) + 2 relato + 2 link = 14
        self.assertTrue(datos["ok"])
        self.assertEqual(datos["tokens_otorgados"], 14)
        self.assertEqual(datos["nivel"], "Experto")
        self.assertEqual(datos["respuestas_largas"], 0)

        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.tokensgrupo, 24)
        self.assertTrue(self.grupo.bubble_tokens_otorgados)
        self.assertEqual(
            BubbleMapRespuesta.objects.filter(grupo=self.grupo).count(), 5
        )

    def test_respuesta_larga_suma_extra(self):
        burbujas = [burbuja(" ".join(["palabra"] * 12))]  # >=10 palabras
        datos = self._enviar(burbujas).json()

        # 1 válida + 1 larga = 2
        self.assertEqual(datos["tokens_otorgados"], 2)
        self.assertEqual(datos["respuestas_largas"], 1)

    def test_textos_cortos_no_cuentan(self):
        datos = self._enviar([burbuja("abc"), burbuja("    ")]).json()
        self.assertEqual(datos["tokens_otorgados"], 0)
        self.assertEqual(datos["nivel"], "Inicial")

    def test_doble_envio_no_duplica(self):
        burbujas = [burbuja(f"respuesta corta {i}") for i in range(3)]
        self._enviar(burbujas)
        datos = self._enviar(burbujas).json()

        self.assertTrue(datos["ya_otorgados"])
        self.assertEqual(datos["tokens_otorgados"], 0)

        self.grupo.refresh_from_db()
        # 3 válidas = 3 tokens, una sola vez.
        self.assertEqual(self.grupo.tokensgrupo, 13)

    def test_ultimo_grupo_dispara_ranking(self):
        otro = self.grupos[1]
        otro.bubble_tokens_otorgados = True
        otro.save(update_fields=["bubble_tokens_otorgados"])

        datos = self._enviar([burbuja("respuesta corta")]).json()

        self.assertTrue(datos["todos_terminaron"])
        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f2_ranking")

    def test_fuera_de_fase_rechaza(self):
        self.set_fase("f3_lego")
        respuesta = self._enviar([burbuja("respuesta corta")])
        self.assertEqual(respuesta.status_code, 400)
