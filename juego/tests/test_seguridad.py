# juego/tests/test_seguridad.py
"""Autenticación de profesor/admin y protección de endpoints."""

from django.test import override_settings
from django.urls import reverse

from juego.auth import verificar_clave_profesor
from juego.models import Grupo, Reto, Retogrupo, Usuario

from .base import BaseJuegoTestCase, crear_profesor, crear_sesion, crear_grupos


class LoginAccesoTests(BaseJuegoTestCase):
    def test_login_profesor_correcto(self):
        respuesta = self.client.post(reverse("login_acceso"), {
            "rol": "profesor",
            "email": "profe@udd.cl",
            "clave": "clave-segura-123",
        })

        self.assertRedirects(respuesta, reverse("dashboardprofesor"), fetch_redirect_response=False)
        self.assertEqual(
            self.client.session.get("profesor_id"), self.profesor.idprofesor
        )

    def test_login_profesor_clave_incorrecta(self):
        respuesta = self.client.post(reverse("login_acceso"), {
            "rol": "profesor",
            "email": "profe@udd.cl",
            "clave": "incorrecta",
        })

        self.assertEqual(respuesta.status_code, 200)
        self.assertIsNone(self.client.session.get("profesor_id"))

    def test_login_profesor_email_case_insensitive(self):
        self.client.post(reverse("login_acceso"), {
            "rol": "profesor",
            "email": "PROFE@UDD.CL",
            "clave": "clave-segura-123",
        })
        self.assertEqual(
            self.client.session.get("profesor_id"), self.profesor.idprofesor
        )

    @override_settings(CLAVE_ADMIN="clave-admin-test")
    def test_login_admin_correcto(self):
        respuesta = self.client.post(reverse("login_acceso"), {
            "rol": "admin",
            "clave": "clave-admin-test",
        })
        self.assertRedirects(respuesta, reverse("dashboardadmin"), fetch_redirect_response=False)
        self.assertTrue(self.client.session.get("es_admin"))

    @override_settings(CLAVE_ADMIN="clave-admin-test")
    def test_login_admin_incorrecto(self):
        self.client.post(reverse("login_acceso"), {
            "rol": "admin",
            "clave": "otra",
        })
        self.assertFalse(self.client.session.get("es_admin"))

    def test_clave_legacy_en_texto_plano_nunca_valida(self):
        """Las cuentas antiguas guardaban 'temp' sin hashear: no deben poder entrar."""
        usuario = Usuario.objects.create(password="temp")
        from juego.models import Profesor
        legado = Profesor.objects.create(
            usuario_idusuario=usuario, emailprofesor="legado@udd.cl"
        )
        self.assertFalse(verificar_clave_profesor(legado, "temp"))

    def test_logout_limpia_roles(self):
        self.login_profesor()
        self.login_admin()
        self.client.get(reverse("logout_acceso"))
        self.assertIsNone(self.client.session.get("profesor_id"))
        self.assertIsNone(self.client.session.get("es_admin"))

    def test_next_no_permite_redireccion_externa(self):
        respuesta = self.client.post(
            reverse("login_acceso"),
            {
                "rol": "profesor",
                "email": "profe@udd.cl",
                "clave": "clave-segura-123",
                "next": "https://malicioso.example.com/",
            },
        )
        self.assertRedirects(respuesta, reverse("dashboardprofesor"), fetch_redirect_response=False)


class ProteccionEndpointsProfesorTests(BaseJuegoTestCase):
    def test_dashboard_profesor_requiere_login(self):
        respuesta = self.client.get(reverse("dashboardprofesor"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("login_acceso"), respuesta.url)

    def test_dashboard_profesor_muestra_sesion_del_profesor_logueado(self):
        otro_profesor = crear_profesor("otro@udd.cl")
        sesion_ajena = crear_sesion(otro_profesor, nombre="Sesión ajena")

        self.login_profesor(self.profesor)
        respuesta = self.client.get(reverse("dashboardprofesor"))

        self.assertEqual(respuesta.status_code, 200)
        sesion_ctx = respuesta.context["sesion"]
        self.assertIsNotNone(sesion_ctx)
        self.assertEqual(sesion_ctx.idsesion, self.sesion.idsesion)
        self.assertNotEqual(sesion_ctx.idsesion, sesion_ajena.idsesion)

    def test_siguiente_fase_bloqueada_sin_login(self):
        url = reverse("profesor_siguiente_fase", args=[self.sesion.idsesion])
        respuesta = self.post_json(url)
        self.assertEqual(respuesta.status_code, 403)

        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f1_bienvenida")

    def test_siguiente_fase_permitida_a_profesor(self):
        self.login_profesor()
        url = reverse("profesor_siguiente_fase", args=[self.sesion.idsesion])
        respuesta = self.post_json(url)
        self.assertEqual(respuesta.status_code, 200)

        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f1_conocidos")

    def test_alumno_logueado_no_puede_avanzar_fase(self):
        """Un alumno con sesión de grupo activa sigue sin poder tocar el control."""
        self.login_alumno(self.grupo)
        url = reverse("profesor_siguiente_fase", args=[self.sesion.idsesion])
        respuesta = self.post_json(url)
        self.assertEqual(respuesta.status_code, 403)

    def test_dev_timer_bloqueado_sin_login(self):
        url = reverse("dev_timer_10_segundos", args=[self.sesion.idsesion])
        respuesta = self.post_json(url)
        self.assertEqual(respuesta.status_code, 403)

    def test_ver_como_grupo_bloqueado_sin_login(self):
        url = reverse("ver_como_grupo", args=[self.grupo.idgrupo])
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("login_acceso"), respuesta.url)

    def test_control_sesion_permitido_a_admin(self):
        self.login_admin()
        respuesta = self.client.get(
            reverse("control_sesion", args=[self.sesion.idsesion])
        )
        self.assertEqual(respuesta.status_code, 200)

    def test_estado_sesion_sigue_publico_para_alumnos(self):
        """El polling de estado lo usan los alumnos: no debe requerir login."""
        respuesta = self.client.get(
            reverse("estado_sesion", args=[self.sesion.idsesion])
        )
        self.assertEqual(respuesta.status_code, 200)


class ProteccionEndpointsAdminTests(BaseJuegoTestCase):
    def test_dashboard_admin_requiere_admin(self):
        respuesta = self.client.get(reverse("dashboardadmin"))
        self.assertEqual(respuesta.status_code, 302)

    def test_profesor_no_entra_al_panel_admin(self):
        self.login_profesor()
        respuesta = self.client.get(reverse("dashboardadmin"))
        self.assertEqual(respuesta.status_code, 302)

    def test_admin_entra_al_panel_admin(self):
        self.login_admin()
        respuesta = self.client.get(reverse("dashboardadmin"))
        self.assertEqual(respuesta.status_code, 200)

    def test_eliminar_profesor_bloqueado_sin_admin(self):
        url = reverse("eliminar_profesor", args=[self.profesor.idprofesor])
        respuesta = self.post_json(url)
        self.assertEqual(respuesta.status_code, 403)


class MarcarListoSeguroTests(BaseJuegoTestCase):
    def test_grupo_no_puede_marcar_listo_a_otro(self):
        self.set_fase("f1_bienvenida")
        atacante, victima = self.grupos[0], self.grupos[1]
        self.login_alumno(atacante)

        url = reverse("marcar_grupo_listo", args=[victima.idgrupo])
        respuesta = self.post_json(url, {"fase": None})

        self.assertEqual(respuesta.status_code, 403)
        victima.refresh_from_db()
        self.assertFalse(victima.listo_lobby)

    def test_grupo_puede_marcarse_a_si_mismo(self):
        self.set_fase("f1_bienvenida")
        self.login_alumno(self.grupo)

        url = reverse("marcar_grupo_listo", args=[self.grupo.idgrupo])
        respuesta = self.post_json(url, {"fase": None})

        self.assertEqual(respuesta.status_code, 200)
        self.grupo.refresh_from_db()
        self.assertTrue(self.grupo.listo_lobby)

    def test_sin_sesion_no_puede_marcar_listo(self):
        url = reverse("marcar_grupo_listo", args=[self.grupo.idgrupo])
        respuesta = self.post_json(url, {"fase": None})
        self.assertEqual(respuesta.status_code, 403)

    def test_listo_ranking_solo_para_el_propio_grupo(self):
        atacante, victima = self.grupos[0], self.grupos[1]
        self.login_alumno(atacante)

        url = reverse("marcar_listo_ranking", args=[victima.idgrupo])
        respuesta = self.post_json(url)

        self.assertEqual(respuesta.status_code, 403)
        victima.refresh_from_db()
        self.assertFalse(victima.listo_ranking)


class MarketSeguroTests(BaseJuegoTestCase):
    def test_no_se_puede_retar_a_grupo_de_otra_sesion(self):
        reto = Reto.objects.create(nombrereto="Reto", costoreto=0)

        otra_sesion = crear_sesion(crear_profesor("x@udd.cl"))
        (grupo_externo,) = crear_grupos(otra_sesion, 1)

        self.login_alumno(self.grupo)
        respuesta = self.client.post(
            reverse("issue_challenge", args=[reto.idreto]),
            {"target_team_id": grupo_externo.idgrupo},
        )

        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(Retogrupo.objects.count(), 0)

    def test_no_se_puede_retar_a_si_mismo(self):
        reto = Reto.objects.create(nombrereto="Reto", costoreto=0)
        self.login_alumno(self.grupo)

        respuesta = self.client.post(
            reverse("issue_challenge", args=[reto.idreto]),
            {"target_team_id": self.grupo.idgrupo},
        )

        self.assertRedirects(respuesta, reverse("market"), fetch_redirect_response=False)
        self.assertEqual(Retogrupo.objects.count(), 0)

    def test_reto_valido_descuenta_costo(self):
        reto = Reto.objects.create(nombrereto="Reto", costoreto=4)
        receptor = self.grupos[1]
        self.login_alumno(self.grupo)

        self.client.post(
            reverse("issue_challenge", args=[reto.idreto]),
            {"target_team_id": receptor.idgrupo},
        )

        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.tokensgrupo, 6)
        self.assertEqual(Retogrupo.objects.count(), 1)


class SesionesPorProfesorTests(BaseJuegoTestCase):
    """Cada profesor ve y crea solo sus sesiones; el admin las ve todas."""

    def _csv_alumnos(self, cantidad=4):
        import io as _io

        lineas = ["Nombre,Apellido Paterno,Apellido Materno,RUT,Correo,Carrera"]
        for i in range(cantidad):
            lineas.append(f"Alumno{i},Pérez,Soto,1{i}.111.111-{i},a{i}@udd.cl,Ingeniería")

        archivo = _io.BytesIO("\n".join(lineas).encode("utf-8"))
        archivo.name = "alumnos.csv"
        return archivo

    def test_listar_sesiones_solo_muestra_las_propias(self):
        otro = crear_profesor("otro@udd.cl")
        ajena = crear_sesion(otro, nombre="Sesión ajena")

        self.login_profesor(self.profesor)
        respuesta = self.client.get(reverse("listar_sesiones"))

        ids = [i["sesion"].idsesion for i in respuesta.context["sesiones_info"]]
        self.assertIn(self.sesion.idsesion, ids)
        self.assertNotIn(ajena.idsesion, ids)

    def test_admin_ve_todas_las_sesiones(self):
        otro = crear_profesor("otro@udd.cl")
        ajena = crear_sesion(otro, nombre="Sesión ajena")

        self.login_admin()
        respuesta = self.client.get(reverse("listar_sesiones"))

        ids = [i["sesion"].idsesion for i in respuesta.context["sesiones_info"]]
        self.assertIn(self.sesion.idsesion, ids)
        self.assertIn(ajena.idsesion, ids)

    def test_crear_sesion_la_asigna_al_profesor_logueado(self):
        from juego.models import Sesion

        nuevo = crear_profesor("nuevo@udd.cl")
        self.login_profesor(nuevo)

        respuesta = self.client.post(reverse("crear_sesion"), {
            "nombre": "Mi sesión",
            "modo_creacion": "recomendado",
            "archivo_excel": self._csv_alumnos(),
        })

        self.assertEqual(respuesta.status_code, 200)
        creada = Sesion.objects.filter(nombre="Mi sesión").first()
        self.assertIsNotNone(creada)
        self.assertEqual(creada.profesor_id, nuevo.idprofesor)

    def test_crear_sesion_no_corrompe_a_otro_profesor(self):
        """Regresión: el flujo antiguo sobrescribía email/facultad del primer profesor."""
        nuevo = crear_profesor("nuevo@udd.cl")
        self.login_profesor(nuevo)

        self.client.post(reverse("crear_sesion"), {
            "nombre": "Mi sesión",
            "email_profesor": "cualquiercosa@udd.cl",
            "facultad": "Otra",
            "modo_creacion": "recomendado",
            "archivo_excel": self._csv_alumnos(),
        })

        self.profesor.refresh_from_db()
        self.assertEqual(self.profesor.emailprofesor, "profe@udd.cl")
        self.assertEqual(self.profesor.facultad, "Ingeniería")

    def test_admin_crea_sesion_para_profesor_por_email(self):
        from juego.models import Sesion

        self.login_admin()
        respuesta = self.client.post(reverse("crear_sesion"), {
            "nombre": "Sesión admin",
            "email_profesor": "PROFE@UDD.CL",
            "modo_creacion": "recomendado",
            "archivo_excel": self._csv_alumnos(),
        })

        self.assertEqual(respuesta.status_code, 200)
        creada = Sesion.objects.filter(nombre="Sesión admin").first()
        self.assertIsNotNone(creada)
        self.assertEqual(creada.profesor_id, self.profesor.idprofesor)

    def test_admin_sin_email_recibe_error(self):
        from juego.models import Sesion

        self.login_admin()
        self.client.post(reverse("crear_sesion"), {
            "nombre": "Sin dueño",
            "modo_creacion": "recomendado",
            "archivo_excel": self._csv_alumnos(),
        })
        self.assertFalse(Sesion.objects.filter(nombre="Sin dueño").exists())


    def test_formulario_profesor_no_pide_email(self):
        """El profesor logueado no debe ver el campo email_profesor obligatorio."""
        self.login_profesor(self.profesor)
        respuesta = self.client.get(reverse("crear_sesion"))
        self.assertNotContains(respuesta, 'name="email_profesor"')
        self.assertContains(respuesta, "profe@udd.cl")

    def test_formulario_admin_si_pide_email(self):
        self.login_admin()
        respuesta = self.client.get(reverse("crear_sesion"))
        self.assertContains(respuesta, 'name="email_profesor"')
