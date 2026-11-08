from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware


class SessionMiddlewareSinBorrarCookieAjena(SessionMiddleware):
    """
    SessionMiddleware de Django, salvo un caso: no borra la cookie cuando la
    sesión llegó vacía y nadie la modificó.

    Al registrarse un grupo, la sesión anterior se elimina y el navegador
    recibe una cookie nueva. Si en ese instante otra pestaña del mismo
    navegador (por ejemplo, el panel del profesor) tenía una consulta en
    curso con la cookie anterior, esa respuesta llegaba después con la orden
    de borrar la cookie, y se llevaba la nueva: el grupo terminaba en el
    registro al salir del video de bienvenida.

    Dejar una cookie que no corresponde a ninguna sesión es inofensivo: Django
    la ignora. Cuando la vista sí vacía la sesión (salir, flush), se mantiene
    el comportamiento original.
    """

    def process_response(self, request, response):
        try:
            vacia_sin_cambios = (
                request.session.is_empty() and not request.session.modified
            )
        except AttributeError:
            return response

        if vacia_sin_cambios and settings.SESSION_COOKIE_NAME in request.COOKIES:
            return response

        return super().process_response(request, response)
