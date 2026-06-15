#NUEVO
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.conf import settings
from .image_utils import convertir_imagen_a_webp
from django.utils.text import slugify
from .models import TiempoFase
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from .models import BubbleMapRespuesta
from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Sum
import json
from datetime import timedelta
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Count, Q
from .models import Tematica, Desafio, Grupo, RuletaLegoOpcion
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

#NUEVO CIERRRE
from django.shortcuts import redirect, render
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import Tematica, Desafio
import openpyxl
import csv
import io
from .models import Alumno, Profesor, Usuario, Grupo, Desafio, Idadministrador, Sesion, Reto, Retogrupo, Evaluacion, PalabraSopaEncontrada
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import secrets
from django.shortcuts import get_object_or_404
import string
import random
from math import ceil
from django.utils import timezone
from django.db.models import F



FASES_ORDEN = [
    "intro_habilidades",
    "f1_bienvenida",
    "f1_conocidos",
    "f1_pre_sopa",
    "f1_sopa",
    "f1_ranking",

    "mapa_f2_empatia",
    "f2_transicion",
    "f2_tematicas",
    "f2_transicion_empatia",
    "f2_bubblemap",
    "f2_ranking",

    "mapa_f3_creatividad",
    "f3_transicion_creatividad",
    "f3_lego",
    "f3_ranking",

    "mapa_f4_final",
    "f4_transicion_comunicacion",
    "f4_construccion_pitch",
    "f4_orden_pitch",
    "f4_presentacion_pitch",
    "f5_evaluacion_pitch",

    "f6_ranking",
    "reflexion",
]

RUTA_POR_FASE = {
    "lobby": "pantalla_espera",
    "intro_habilidades": "habilidades_intro",
    "f1_bienvenida": "pantalla_inicio",
    "f1_conocidos": "promptconocidos",
    "f1_pre_sopa": "trabajoenequipo",
    "f1_sopa": "minijuego1",
    "f1_ranking": "ranking",

    "f2_transicion": "transiciondesafio",
    "f2_tematicas": "tematicas",
    "f2_transicion_empatia": "transicionempatia",
    "f2_bubblemap": "bubblemap",
    "f2_ranking": "ranking",
    "mapa_f2_empatia": "habilidades_intro",
    "mapa_f3_creatividad": "habilidades_intro",
    "mapa_f4_final": "habilidades_intro",

    "f3_transicion_creatividad": "transicioncreatividad",
    "f3_lego": "lego",
    "f3_ranking": "ranking",

    "f4_transicion_comunicacion": "transicioncomunicacion",
    "f4_construccion_pitch": "pitch",
    "f4_orden_pitch": "orden_presentacion_alumno",
    "f4_presentacion_pitch": "presentar_pitch",

    "f5_transicion_apoyo": "transicionapoyo",
    "f5_evaluacion_pitch": "peer_review",

    "f6_ranking": "ranking",
    "reflexion": "reflexion",
}

ETIQUETA_FASE = {

    "intro_habilidades": "Mapa · Trabajo en equipo",
    "mapa_f2_empatia": "Mapa · Empatía",
    "mapa_f3_creatividad": "Mapa · Creatividad",
    "mapa_f4_final": "Mapa · Misión final",
    "f1_bienvenida": "F1 · Bienvenida",
    "f1_conocidos": "F1 · Conocerse",
    "f1_pre_sopa": "F1 · Trabajo en equipo",
    "f1_sopa": "F1 · Sopa de letras",
    "f1_ranking": "F1 · Ranking",

    "f2_transicion": "F2 · Desafíos",
    "f2_tematicas": "F2 · Temáticas",
    "f2_transicion_empatia": "F2 · Transición Empatía",
    "f2_bubblemap": "F2 · Bubble Map",
    "f2_ranking": "F2 · Ranking",

    "f3_transicion_creatividad": "F3 · Transición Creatividad",
    "f3_lego": "F3 · Lego",
    "f3_ranking": "F3 · Ranking",

    "f4_transicion_comunicacion": "F4 · Transición Comunicación",
    "f4_construccion_pitch": "F4 · Construcción pitch",
    "f4_orden_pitch": "F4 · Sorteo orden pitch",
    "f4_presentacion_pitch": "F4 · Presentación pitch",

    "f5_transicion_apoyo": "F5 · Transición Apoyo",
    "f5_evaluacion_pitch": "F5 · Evaluación pitch",

    "f6_ranking": "Ranking final",
    "reflexion": "Cierre",
}

FASES_CON_INICIO_POR_ALUMNOS = {
    "f1_conocidos",
    "f1_sopa",
    "f2_tematicas",
    "f2_bubblemap",
    "f3_lego",
    "f4_construccion_pitch",
}


def reset_listos_inicio_fase(sesion, fase):
    grupos = Grupo.objects.filter(sesion=sesion)

    if fase == "f1_conocidos":
        grupos.update(listo_lobby=False)

    elif fase == "f1_sopa":
        grupos.update(
            listo_f1=False,
            sopa_ganada=False,
            sopa_tiempo_segundos=None,
            sopa_completada_en=None,
        )

    elif fase == "f2_bubblemap":
        grupos.update(listo_f2=False, bubble_tokens_otorgados=False)

    elif fase == "f3_lego":
        grupos.update(listo_inicio_f3=False)
        grupos.update(listo_f3=False)

    elif fase == "f2_tematicas":
        grupos.update(
            listo_f2_tematicas=False,
        listo_f2_desafio=False,
    )

    elif fase == "f4_construccion_pitch":
        grupos.update(listo_f4=False)

    sesion.inicio_fase_habilitado = False
    sesion.save(update_fields=["inicio_fase_habilitado"])


def contar_listos_inicio_fase(sesion, fase):
    grupos = Grupo.objects.filter(sesion=sesion)
    total = grupos.count()

    if fase == "f1_conocidos":
        listos = grupos.filter(listo_lobby=True).count()

    elif fase == "f1_sopa":
        listos = grupos.filter(listo_f1=True).count()

    elif fase == "f2_tematicas":
        listos = grupos.filter(listo_f2_tematicas=True).count()

    elif fase == "f2_bubblemap":
        listos = grupos.filter(listo_f2=True).count()

    elif fase == "f3_lego":
        listos = grupos.filter(listo_inicio_f3=True).count()

    elif fase == "f4_construccion_pitch":
        listos = grupos.filter(listo_f4=True).count()

    else:
        listos = total

    return total, listos, (total > 0 and listos == total)


def iniciar_timer_de_sesion(sesion):
    segundos = int(sesion.segundos_restantes or 0)

    if segundos <= 0:
        return

    ahora = timezone.now()

    sesion.timer_corriendo = True
    sesion.timer_inicio_at = ahora
    sesion.timer_fin_at = ahora + timedelta(seconds=segundos)
    sesion.save(update_fields=[
        "timer_corriendo",
        "timer_inicio_at",
        "timer_fin_at",
    ])


def obtener_grupo_desde_session(request):
    grupo_id = request.session.get("grupo_id")
    sesion_id = request.session.get("sesion_id")

    print("obtener_grupo_desde_session -> grupo_id:", grupo_id, "| sesion_id:", sesion_id)

    if not grupo_id or not sesion_id:
        return None

    try:
        grupo = Grupo.objects.select_related("sesion").get(
            pk=grupo_id,
            sesion_id=sesion_id,
        )
    except Grupo.DoesNotExist:
        print("obtener_grupo_desde_session -> grupo no existe, flush session")
        request.session.flush()
        return None

    print("obtener_grupo_desde_session -> grupo real:", grupo.idgrupo, "| nombre:", grupo.nombregrupo)
    return grupo

def salir_grupo(request):
    request.session.flush()
    messages.success(request, "Sesión del grupo cerrada correctamente.")
    return redirect("registro")

def siguiente_fase_automatica(fase_actual):
    try:
        idx = FASES_ORDEN.index(fase_actual)
        if idx + 1 < len(FASES_ORDEN):
            return FASES_ORDEN[idx + 1]
    except ValueError:
        pass

    return fase_actual

def fase_anterior_automatica(fase_actual):
    try:
        idx = FASES_ORDEN.index(fase_actual)
        if idx - 1 >= 0:
            return FASES_ORDEN[idx - 1]
    except ValueError:
        pass

    return fase_actual

@require_POST
def profesor_fase_anterior(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    fase_actual = sesion.fase_actual
    nueva_fase = fase_anterior_automatica(fase_actual)

    if nueva_fase == fase_actual:
        return JsonResponse({
            "ok": False,
            "error": f"La fase actual no está en el flujo: {fase_actual}"
        }, status=400)

    # Cambiar fase
    sesion.fase_actual = nueva_fase
    sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None
    sesion.inicio_fase_habilitado = False if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS else True

    grupos = Grupo.objects.filter(sesion=sesion)

    # Limpieza para evitar que al retroceder vuelva a autoavanzar inmediatamente
    if nueva_fase == "intro_habilidades":
        grupos.update(
            listo_lobby=False,
            listo_f1=False,
            listo_f2=False,
            listo_f3=False,
            listo_f4=False,
            listo_f5=False,
            listo_f6=False,
            listo_ranking=False,
        )

    elif nueva_fase == "f1_bienvenida":
        grupos.update(listo_lobby=False)

    elif nueva_fase == "f1_conocidos":
        grupos.update(listo_lobby=False)

    elif nueva_fase == "f1_pre_sopa":
        grupos.update(listo_f1=False)

    elif nueva_fase == "f1_sopa":
        grupos.update(
            listo_f1=False,
            sopa_ganada=False,
            sopa_tiempo_segundos=None,
            sopa_completada_en=None,
        )

    elif nueva_fase == "f1_ranking":
        grupos.update(listo_f6=False, listo_ranking=False)

    elif nueva_fase == "mapa_f2_empatia":
        grupos.update(listo_f6=False, listo_ranking=False)

    elif nueva_fase == "f2_transicion":
        grupos.update(listo_f2=False)

    elif nueva_fase == "f2_tematicas":
        grupos.update(
            listo_f2=False,
            listo_f2_tematica=False,
            listo_f2_desafio=False,
        )

    elif nueva_fase == "f2_transicion_empatia":
        grupos.update(listo_f2_empatia=False)

    elif nueva_fase == "f2_bubblemap":
        grupos.update(
            listo_f2=False,
            bubble_tokens_otorgados=False,
        )

    elif nueva_fase == "f2_ranking":
        grupos.update(listo_f6=False, listo_ranking=False)

    elif nueva_fase == "mapa_f3_creatividad":
        grupos.update(listo_f6=False, listo_ranking=False)

    elif nueva_fase == "f3_transicion_creatividad":
        grupos.update(listo_f3=False)

    elif nueva_fase == "f3_lego":
        grupos.update(
            listo_inicio_f3=False,
            listo_f3=False,
            listo_f3_lego=False,
            lego_sin_foto=False,
        )

    elif nueva_fase == "f3_ranking":
        grupos.update(listo_f6=False, listo_ranking=False)

    elif nueva_fase == "mapa_f4_final":
        grupos.update(listo_f6=False, listo_ranking=False)

    elif nueva_fase == "f4_transicion_comunicacion":
        grupos.update(listo_f4=False)

    elif nueva_fase == "f4_construccion_pitch":
        grupos.update(listo_f4=False)

    elif nueva_fase == "f4_orden_pitch":
        grupos.update(
            listo_f4_orden=False,
            orden_presentacion=None,
        )
        sesion.orden_sorteado = False
        sesion.grupo_presentando = None

    elif nueva_fase == "f4_presentacion_pitch":
        grupos.update(listo_f5=False)

    elif nueva_fase == "f5_evaluacion_pitch":
        grupos.update(listo_f5=False)

    elif nueva_fase == "f6_ranking":
        grupos.update(listo_f6=False, listo_ranking=False)

    sesion.save()

    grupos_data = [
        {
            "id": g.idgrupo,
            "nombre": g.nombregrupo,
            "tokens": g.tokensgrupo or 0,
            "temaElegido": g.tema_elegido or "",
            "desafioNombre": g.desafio_nombre or "",
            "legoConFoto": bool(g.foto_lego),
            "legoSinFoto": g.lego_sin_foto,
            "pitchTexto": bool(g.pitch_texto),
            "listoLobby": g.listo_lobby,
            "listoF1": g.listo_f1,
            "listoF2": g.listo_f2_desafio,
            "listoF2Generico": g.listo_f2,
            "listoF2Empatia": g.listo_f2_empatia,
            "listoF3": g.listo_f3,
            "listoF3Lego": g.listo_f3_lego,
            "listoF4": g.listo_f4,
            "listoF4Orden": g.listo_f4_orden,
            "listoF5": g.listo_f5,
            "listoF6": g.listo_f6,
        }
        for g in Grupo.objects.filter(sesion=sesion).order_by("idgrupo")
    ]

    total_grupos = len(grupos_data)

    return JsonResponse({
        "ok": True,
        "esProfesor": True,
        "faseActual": sesion.fase_actual,
        "faseEtiqueta": ETIQUETA_FASE.get(sesion.fase_actual, sesion.fase_actual),
        "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": sesion.segundos_restantes or 0,
        "totalGrupos": total_grupos,
        "grupos": grupos_data,
        "listosInicio": 0,
        "totalListosInicio": total_grupos,
        "inicioFaseHabilitado": sesion.inicio_fase_habilitado,
    })

# CAMBIAR TIMERS
def tiempo_por_fase(sesion, fase):
    tiempos = {
        "f1_conocidos": getattr(sesion, "t_rompehielo", 10),
        "f1_pre_sopa": 0,
        "f1_sopa": getattr(sesion, "t_diferencias", 60),
        "f1_ranking": 0,

        "f2_transicion": 0,
        "f2_tematicas": getattr(sesion, "t_tematicas", 120),
        "f2_transicion_empatia": 0,
        "f2_bubblemap": getattr(sesion, "t_empatia", 10),
        "f2_ranking": 0,

        "f3_transicion_creatividad": 0,
        "f3_lego": getattr(sesion, "t_creatividad", 10),
        "f3_ranking": 0,

        "f4_transicion_comunicacion": 0,
        "f4_construccion_pitch": getattr(sesion, "t_pitch_prep", 10),
        "f4_orden_pitch": 0,
        "f4_presentacion_pitch": 90,

        "f5_evaluacion_pitch": 90,
        "f6_ranking": 0,
        "reflexion": 0,
        "f1_bienvenida": 0,
        "lobby": 0,
    }

    return int(tiempos.get(fase, 0))


from django.utils import timezone

def calcular_segundos_restantes(sesion):
    if not sesion.timer_corriendo or not sesion.timer_fin_at:
        return max(int(sesion.segundos_restantes or 0), 0)

    restantes = int((sesion.timer_fin_at - timezone.now()).total_seconds())

    if restantes <= 0:
        fase_vencida = sesion.fase_actual

        sesion.timer_corriendo = False
        sesion.segundos_restantes = 0
        sesion.timer_inicio_at = None
        sesion.timer_fin_at = None

        # ===================== F4 PRESENTACION PITCH =====================
        if fase_vencida == "f4_presentacion_pitch":
            sesion.fase_actual = "f5_evaluacion_pitch"
            sesion.save(update_fields=[
                "fase_actual",
                "timer_corriendo",
                "segundos_restantes",
                "timer_inicio_at",
                "timer_fin_at",
            ])
            return 0

        # ===================== F2 TEMATICAS =====================
        fases_con_autoavance = {
            "f1_conocidos",
            "f1_sopa",
            "f4_construccion_pitch",
        }

        if fase_vencida == "f2_tematicas":
            asignar_tematica_y_desafio_aleatorio(sesion)
            sesion.fase_actual = "f2_transicion_empatia"
            sesion.segundos_restantes = tiempo_por_fase(sesion, "f2_transicion_empatia")
            sesion.save(update_fields=[
                "fase_actual",
                "timer_corriendo",
                "segundos_restantes",
                "timer_inicio_at",
                "timer_fin_at",
            ])
            return 0

        # ===================== F5 EVALUACION PITCH =====================
        if fase_vencida == "f5_evaluacion_pitch":
            # 1️⃣ Completar evaluaciones faltantes (penalización a los que no enviaron)
            completar_evaluaciones_faltantes(sesion)

            # 2️⃣ Recompensar al/los grupo(s) mejor evaluado(s) según los puntajes recibidos
            evaluaciones = Evaluacion.objects.filter(sesion=sesion)
            puntaje_recibido = {}  # {grupo_id: total_puntaje}

            for e in evaluaciones:
                total = (e.claridad or 0) + (e.creatividad or 0) + (e.viabilidad or 0) + (e.equipo or 0) + (e.presentacion or 0)
                gid = e.grupo_evaluado.id
                puntaje_recibido[gid] = puntaje_recibido.get(gid, 0) + total

            if puntaje_recibido:
                max_puntaje = max(puntaje_recibido.values())
                mejores = [gid for gid, puntaje in puntaje_recibido.items() if puntaje == max_puntaje]

                for gid in mejores:
                    grupo = Grupo.objects.get(pk=gid)
                    grupo.tokensgrupo = (grupo.tokensgrupo or 0) + 3
                    grupo.save(update_fields=["tokensgrupo"])

            # 3️⃣ Avanzar al siguiente pitch o ranking
            avanzar_al_siguiente_pitch_o_ranking(sesion)
            return 0

        # ===================== OTRAS FASES CON AUTOAVANCE =====================
        if fase_vencida in fases_con_autoavance:
            nueva_fase = siguiente_fase_automatica(fase_vencida)
            sesion.fase_actual = nueva_fase
            sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)

            if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS:
                sesion.inicio_fase_habilitado = False
                sesion.save(update_fields=[
                    "fase_actual",
                    "timer_corriendo",
                    "segundos_restantes",
                    "timer_inicio_at",
                    "timer_fin_at",
                    "inicio_fase_habilitado",
                ])
                reset_listos_inicio_fase(sesion, nueva_fase)
                return 0

        sesion.save(update_fields=[
            "fase_actual",
            "timer_corriendo",
            "segundos_restantes",
            "timer_inicio_at",
            "timer_fin_at",
        ])
        return 0

    return max(restantes, 0)

def autoavanzar_si_todos_listos(sesion):
    grupos = Grupo.objects.filter(sesion=sesion)
    total = grupos.count()

    if total == 0:
        return False

    fase_actual = sesion.fase_actual
    nueva_fase = None

    if fase_actual == "f1_bienvenida":
        if grupos.filter(listo_lobby=True).count() == total:
            nueva_fase = "f1_conocidos"

    elif fase_actual == "f1_pre_sopa":
        if grupos.filter(listo_f1=True).count() == total:
            nueva_fase = "f1_sopa"

    elif fase_actual == "f1_ranking":
        if grupos.filter(listo_f6=True).count() == total:
            nueva_fase = "mapa_f2_empatia"

    elif fase_actual == "f2_transicion":
        if grupos.filter(listo_f2=True).count() == total:
            nueva_fase = "f2_tematicas"

    elif fase_actual == "f2_tematicas":
        if grupos.filter(listo_f2_desafio=True).count() == total:
            nueva_fase = "f2_transicion_empatia"

    elif fase_actual == "f2_transicion_empatia":
        if grupos.filter(listo_f2_empatia=True).count() == total:
            nueva_fase = "f2_bubblemap"

    elif fase_actual == "f2_ranking":
        if grupos.filter(listo_f6=True).count() == total:
            nueva_fase = "mapa_f3_creatividad"

    elif fase_actual == "f3_transicion_creatividad":
        if grupos.filter(listo_f3=True).count() == total:
            nueva_fase = "f3_lego"

    elif fase_actual == "f3_lego":
        if grupos.filter(listo_f3_lego=True).count() == total:
            nueva_fase = "f3_ranking"

    elif fase_actual == "f3_ranking":
        if grupos.filter(listo_f6=True).count() == total:
            nueva_fase = "mapa_f4_final"

    elif fase_actual == "f4_transicion_comunicacion":
        if grupos.filter(listo_f4=True).count() == total:
            nueva_fase = "f4_construccion_pitch"

    elif fase_actual == "f4_orden_pitch":
        listos_orden = grupos.filter(listo_f4_orden=True).count()

        if not sesion.orden_sorteado:
            if listos_orden == total:
                grupos_lista = list(
                    Grupo.objects.filter(sesion=sesion).order_by("idgrupo")
                )
                random.shuffle(grupos_lista)

                for i, grupo in enumerate(grupos_lista, start=1):
                    grupo.orden_presentacion = i
                    grupo.save(update_fields=["orden_presentacion"])

                sesion.orden_sorteado = True
                sesion.grupo_presentando = sorted(
                    grupos_lista,
                    key=lambda g: g.orden_presentacion
                )[0]

                Grupo.objects.filter(sesion=sesion).update(listo_f4_orden=False)

                sesion.segundos_restantes = 0
                sesion.timer_corriendo = False
                sesion.timer_inicio_at = None
                sesion.timer_fin_at = None
                sesion.inicio_fase_habilitado = True
                sesion.save(update_fields=[
                    "orden_sorteado",
                    "grupo_presentando",
                    "segundos_restantes",
                    "timer_corriendo",
                    "timer_inicio_at",
                    "timer_fin_at",
                    "inicio_fase_habilitado",
                ])
                return True

        else:
            if listos_orden == total:
                nueva_fase = "f4_presentacion_pitch"

    elif fase_actual == "f6_ranking":
        if grupos.filter(listo_f6=True).count() == total:
            nueva_fase = "reflexion"
            borrar_fotos_lego_sesion(sesion)

    if not nueva_fase:
        return False

    sesion.fase_actual = nueva_fase
    sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None

    if nueva_fase in {"f5_evaluacion_pitch"}:
        ahora = timezone.now()
        sesion.timer_corriendo = sesion.segundos_restantes > 0
        sesion.timer_inicio_at = ahora if sesion.timer_corriendo else None
        sesion.timer_fin_at = ahora + timedelta(seconds=sesion.segundos_restantes) if sesion.timer_corriendo else None

    if nueva_fase in {"f1_ranking", "f2_ranking", "f3_ranking", "f6_ranking"}:
        Grupo.objects.filter(sesion=sesion).update(
            listo_f6=False,
            listo_ranking=False,
        )

    if nueva_fase == "f4_presentacion_pitch":
        sesion.grupo_presentando = Grupo.objects.filter(
            sesion=sesion,
            orden_presentacion__isnull=False
        ).order_by("orden_presentacion").first()

    if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS:
        sesion.inicio_fase_habilitado = False
        sesion.save(update_fields=[
            "fase_actual",
            "segundos_restantes",
            "timer_corriendo",
            "timer_inicio_at",
            "timer_fin_at",
            "inicio_fase_habilitado",
            "grupo_presentando",
        ])
        reset_listos_inicio_fase(sesion, nueva_fase)
        return True

    sesion.inicio_fase_habilitado = True
    sesion.save(update_fields=[
        "fase_actual",
        "segundos_restantes",
        "timer_corriendo",
        "timer_inicio_at",
        "timer_fin_at",
        "inicio_fase_habilitado",
        "grupo_presentando",
    ])
    return True


def peer_review_completado(grupo):
    sesion = grupo.sesion
    grupo_actual = sesion.grupo_presentando

    if not grupo_actual:
        return False

    if grupo.pk == grupo_actual.pk:
        return False

    return Evaluacion.objects.filter(
        sesion=sesion,
        grupo_evaluador=grupo,
        grupo_evaluado=grupo_actual,
    ).exists()


def ruta_alumno_por_estado(grupo):
    fase = grupo.sesion.fase_actual

    if fase == "f2_tematicas":
        if not (grupo.tema_elegido or "").strip():
            return "tematicas"
        return "desafios"

    if fase == "f5_evaluacion_pitch":
        return "peer_review"

    return RUTA_POR_FASE.get(fase, "pantalla_espera")

def acceso_permitido(grupo, nombre_vista):
    if not grupo or not grupo.sesion:
        return False

    fases_por_vista = {
        "pantalla_espera": ["lobby"],

        "pantalla_inicio": ["f1_bienvenida"],
        "conocidos": ["f1_conocidos"],
        "promptconocidos": ["f1_conocidos"],
        "conocidos_rapido": ["f1_conocidos"],
        "trabajoenequipo": ["f1_pre_sopa"],
        "minijuego1": ["f1_sopa"],

        "transiciondesafio": ["f2_transicion"],
        "tematicas": ["f2_tematicas"],
        "desafios": ["f2_tematicas"],
        "transicionempatia": ["f2_transicion_empatia"],
        "bubblemap": ["f2_bubblemap"],

        "transicioncreatividad": ["f3_transicion_creatividad"],
        "lego": ["f3_lego"],

        "transicioncomunicacion": ["f4_transicion_comunicacion"],
        "pitch": ["f4_construccion_pitch"],
        "orden_presentacion_alumno": ["f4_orden_pitch"],
        "presentar_pitch": ["f4_presentacion_pitch"],

        "transicionapoyo": ["f5_transicion_apoyo"],
        "peer_review": ["f5_evaluacion_pitch"],
        "mision_cumplida": ["f5_evaluacion_pitch"],

        "ranking": ["f1_ranking", "f2_ranking", "f3_ranking", "f6_ranking"],
        "reflexion": ["reflexion"],
    }

    return grupo.sesion.fase_actual in fases_por_vista.get(nombre_vista, [])

def espera_eleccion(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return redirect("registro")

    sesion = grupo.sesion
    grupos = Grupo.objects.filter(sesion=sesion)

    grupos_listos = grupos.filter(listo_f2_desafio=True).count()
    total_grupos = grupos.count()

    return render(request, "espera_eleccion.html", {
        "grupo": grupo,
        "tema": grupo.tema_elegido or "No seleccionada",
        "desafio_nombre": grupo.desafio_nombre or "No seleccionado",
        "grupos_listos": grupos_listos,
        "total_grupos": total_grupos,
    })

def serializar_estado_pitch(sesion, grupo_solicitante=None):
    grupo_actual = sesion.grupo_presentando

    orden_pitch = list(
        Grupo.objects.filter(sesion=sesion, orden_presentacion__isnull=False)
        .order_by("orden_presentacion")
        .values("idgrupo", "nombregrupo", "orden_presentacion")
    )

    foto_lego_url = None
    if grupo_actual and grupo_actual.foto_lego:
        try:
            foto_lego_url = grupo_actual.foto_lego.url
        except Exception:
            foto_lego_url = None

    segundos_restantes = max(int(sesion.segundos_restantes or 0), 0)
    if sesion.timer_corriendo and sesion.timer_fin_at:
        segundos_restantes = max(int((sesion.timer_fin_at - timezone.now()).total_seconds()), 0)

    return {
        "grupoActual": {
            "id": grupo_actual.idgrupo,
            "nombre": grupo_actual.nombregrupo,
            "fotoLego": foto_lego_url,
            "orden": grupo_actual.orden_presentacion,
        } if grupo_actual else None,
        "ordenPitch": [
            {
                "id": g["idgrupo"],
                "nombre": g["nombregrupo"],
                "orden": g["orden_presentacion"],
            }
            for g in orden_pitch
        ],
        "ordenSorteado": getattr(sesion, "orden_sorteado", False),
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": segundos_restantes,
        "miPitch": grupo_solicitante.pitch_texto if grupo_solicitante else "",
        "miEquipoPresenta": (
    grupo_solicitante and grupo_actual and
    grupo_solicitante.idgrupo == grupo_actual.idgrupo
),
    }


#PRESENTACION PITCH/LEGO
@require_GET
@never_cache
def estado_presentacion_pitch(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    grupo_solicitante = obtener_grupo_desde_session(request)
    if grupo_solicitante and grupo_solicitante.sesion_id != sesion.idsesion:
        grupo_solicitante = None

    calcular_segundos_restantes(sesion)
    autoavanzar_si_todos_listos(sesion)
    sesion.refresh_from_db()

    nombre_url = RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")

    grupos = Grupo.objects.filter(sesion=sesion).order_by("idgrupo")

    grupos_data = [
        {
            "id": g.idgrupo,
            "nombre": g.nombregrupo,
            "listoF4Orden": getattr(g, "listo_f4_orden", False),
        }
        for g in grupos
    ]

    total_grupos = len(grupos_data)
    grupos_listos_f4_orden = sum(1 for g in grupos_data if g["listoF4Orden"])
    todos_listos_f4_orden = total_grupos > 0 and grupos_listos_f4_orden == total_grupos

    data = {
        "ok": True,
        "faseActual": sesion.fase_actual,
        "rutaAlumno": reverse(nombre_url),
        "totalGrupos": total_grupos,
        "grupos": grupos_data,
        "gruposListosF4Orden": grupos_listos_f4_orden,
        "todosListosF4Orden": todos_listos_f4_orden,
        **serializar_estado_pitch(sesion, grupo_solicitante=grupo_solicitante),
    }
    return JsonResponse(data)

@require_POST
def iniciar_presentacion_pitch(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({
            "ok": False,
            "error": "No se pudo identificar tu grupo."
        }, status=403)

    if sesion.fase_actual != "f4_presentacion_pitch":
        return JsonResponse({
            "ok": False,
            "error": "La sesión no está en fase de presentación."
        }, status=400)

    grupo_actual = sesion.grupo_presentando
    if not grupo_actual:
        return JsonResponse({
            "ok": False,
            "error": "No hay un grupo asignado para presentar."
        }, status=400)

    if grupo.idgrupo != grupo_actual.idgrupo:
        return JsonResponse({
            "ok": False,
            "error": "Solo el grupo que está presentando puede iniciar el temporizador."
        }, status=403)

    segundos = int(sesion.segundos_restantes or sesion.t_pitch or 90)
    if segundos <= 0:
        segundos = int(sesion.t_pitch or 90)

    ahora = timezone.now()

    sesion.segundos_restantes = segundos
    sesion.timer_corriendo = True
    sesion.timer_inicio_at = ahora
    sesion.timer_fin_at = ahora + timedelta(seconds=segundos)
    sesion.save(update_fields=[
        "segundos_restantes",
        "timer_corriendo",
        "timer_inicio_at",
        "timer_fin_at",
    ])

    return JsonResponse({
        "ok": True,
        "faseActual": sesion.fase_actual,
        "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
        **serializar_estado_pitch(sesion, grupo_solicitante=grupo),
    })


@require_POST
def siguiente_grupo_pitch(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    actual = sesion.grupo_presentando

    if actual is None:
        siguiente = Grupo.objects.filter(
            sesion=sesion,
            orden_presentacion__isnull=False
        ).order_by("orden_presentacion").first()
    else:
        siguiente = Grupo.objects.filter(
            sesion=sesion,
            orden_presentacion__gt=actual.orden_presentacion
        ).order_by("orden_presentacion").first()

    if siguiente is None:
        return JsonResponse({
            "ok": False,
            "error": "Ya no quedan más grupos por presentar."
        }, status=400)

    sesion.grupo_presentando = siguiente
    sesion.segundos_restantes = 90
    sesion.timer_corriendo = False
    sesion.save(update_fields=["grupo_presentando", "segundos_restantes", "timer_corriendo"])

    return JsonResponse({
        "ok": True,
        **serializar_estado_pitch(sesion),
    })

@require_GET
def estado_sesion(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    if sesion.fase_actual == "f5_evaluacion_pitch" and evaluacion_actual_completa(sesion):
        avanzar_al_siguiente_pitch_o_ranking(sesion)

    autoavanzar_si_todos_listos(sesion)
    sesion.refresh_from_db()

    grupos = Grupo.objects.filter(sesion=sesion).order_by("idgrupo")

    fase_actual = sesion.fase_actual
    nombre_url = RUTA_POR_FASE.get(fase_actual, "pantalla_espera")
    if fase_actual == "f1_conocidos":
        modo = request.session.get("modo_conocidos")

        if modo == "rapido":
            nombre_url = "conocidos_rapido"
        elif modo == "normal":
            nombre_url = "conocidos"
        else:
            nombre_url = "promptconocidos"

    grupos_data = [
        {
            "esProfesor": True,
            "id": g.idgrupo,
            "nombre": g.nombregrupo,
           "tokens": g.tokensgrupo or 0,
           "temaElegido": g.tema_elegido or "",
            "desafioNombre": g.desafio_nombre or "",
            "desafioDescripcion": g.desafio_descripcion or "",
            "desafioIdExterno": g.desafio_id_externo or "",
            "bubbleTokensOtorgados": getattr(g, "bubble_tokens_otorgados", False),
            "listoLobby": g.listo_lobby,
            "listoF1": g.listo_f1,
            "listoF2": g.listo_f2_desafio,
            "listoF2Tematicas": g.listo_f2_tematicas,
           "listoF2Generico": g.listo_f2,
            "listoF2Empatia": getattr(g, "listo_f2_empatia", False),
            "listoF3": g.listo_f3,
            "listoInicioF3": getattr(g, "listo_inicio_f3", False),
           "listoF3Lego": getattr(g, "listo_f3_lego", False),
           "legoSinFoto": getattr(g, "lego_sin_foto", False),
           "legoConFoto": bool(getattr(g, "foto_lego", None)) and getattr(g, "listo_f3_lego", False),
           "listoF4": g.listo_f4,
           "listoF4Orden": getattr(g, "listo_f4_orden", False),
           "listoF5": getattr(g, "listo_f5", False),
          "listoF6": getattr(g, "listo_f6", False),
        }
        for g in grupos
]

    total_grupos = len(grupos_data)

    grupos_listos_lobby = sum(1 for g in grupos_data if g["listoLobby"])
    todos_listos_lobby = total_grupos > 0 and grupos_listos_lobby == total_grupos

    grupos_listos_f1 = sum(1 for g in grupos_data if g["listoF1"])
    todos_listos_f1 = total_grupos > 0 and grupos_listos_f1 == total_grupos

    grupos_listos_f2_generico = sum(1 for g in grupos_data if g["listoF2Generico"])
    todos_listos_f2_generico = total_grupos > 0 and grupos_listos_f2_generico == total_grupos

    grupos_listos_f2_tematicas = sum(1 for g in grupos_data if g["listoF2Tematicas"])
    todos_listos_f2_tematicas = total_grupos > 0 and grupos_listos_f2_tematicas == total_grupos

    grupos_listos_f2 = sum(1 for g in grupos_data if g["listoF2"])
    todos_listos_f2 = total_grupos > 0 and grupos_listos_f2 == total_grupos

    grupos_listos_f2_empatia = sum(1 for g in grupos_data if g["listoF2Empatia"])
    todos_listos_f2_empatia = total_grupos > 0 and grupos_listos_f2_empatia == total_grupos

    grupos_listos_f3 = sum(1 for g in grupos_data if g["listoF3"])
    todos_listos_f3 = total_grupos > 0 and grupos_listos_f3 == total_grupos
    grupos_listos_f3_lego = sum(1 for g in grupos_data if g["listoF3Lego"])
    todos_listos_f3_lego = total_grupos > 0 and grupos_listos_f3_lego == total_grupos

    grupos_con_foto_lego = sum(1 for g in grupos_data if g["legoConFoto"])
    grupos_sin_foto_lego = sum(1 for g in grupos_data if g["legoSinFoto"])
    grupos_listos_f4 = sum(1 for g in grupos_data if g["listoF4"])
    todos_listos_f4 = total_grupos > 0 and grupos_listos_f4 == total_grupos
    grupos_listos_f4_orden = sum(1 for g in grupos_data if g["listoF4Orden"])
    todos_listos_f4_orden = total_grupos > 0 and grupos_listos_f4_orden == total_grupos

    grupos_listos_f5 = sum(1 for g in grupos_data if g["listoF5"])
    todos_listos_f5 = total_grupos > 0 and grupos_listos_f5 == total_grupos

    grupos_listos_f6 = sum(1 for g in grupos_data if g["listoF6"])
    todos_listos_f6 = total_grupos > 0 and grupos_listos_f6 == total_grupos

    grupos_listos_ranking = Grupo.objects.filter(sesion=sesion, listo_ranking=True).count()
    todos_listos_ranking = total_grupos > 0 and grupos_listos_ranking == total_grupos
    total_inicio, listos_inicio, todos_inicio = contar_listos_inicio_fase(sesion, sesion.fase_actual)


    pitch_data = {}
    if fase_actual in {
        "f4_orden_pitch",
        "f4_presentacion_pitch",
        "f5_evaluacion_pitch",
        "f1_ranking",
        "f2_ranking",
        "f3_ranking",
        "f6_ranking",
    }:
        pitch_data = serializar_estado_pitch(sesion)


    data = {
        "sesionId": sesion.idsesion,
        "faseActual": fase_actual,
        "faseEtiqueta": ETIQUETA_FASE.get(fase_actual, fase_actual),
        "rutaAlumno": reverse(nombre_url),
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": calcular_segundos_restantes(sesion),

        "totalGrupos": total_grupos,
        "grupos": grupos_data,
        "esProfesor": request.user.is_staff,

        "gruposListosLobby": grupos_listos_lobby,
        "todosListosLobby": todos_listos_lobby,

        "gruposListosF1": grupos_listos_f1,
        "todosListosF1": todos_listos_f1,

        "gruposListosF2Tematicas": grupos_listos_f2_tematicas,
    "todosListosF2Tematicas": todos_listos_f2_tematicas,
        "gruposListosF2Generico": grupos_listos_f2_generico,
        "todosListosF2Generico": todos_listos_f2_generico,
        "gruposListosF2Empatia": grupos_listos_f2_empatia,
        "todosListosF2Empatia": todos_listos_f2_empatia,
        "gruposListosF2": grupos_listos_f2,
        "todosListosF2": todos_listos_f2,

        "gruposListosF3Lego": grupos_listos_f3_lego,
        "todosListosF3Lego": todos_listos_f3_lego,
        "gruposConFotoLego": grupos_con_foto_lego,
        "gruposSinFotoLego": grupos_sin_foto_lego,
        "gruposListosF3": grupos_listos_f3,
        "todosListosF3": todos_listos_f3,

        "gruposListosF4": grupos_listos_f4,
        "todosListosF4": todos_listos_f4,
        "gruposListosF4Orden": grupos_listos_f4_orden,
        "todosListosF4Orden": todos_listos_f4_orden,

        "gruposListosF5": grupos_listos_f5,
        "todosListosF5": todos_listos_f5,

        "gruposListosF6": grupos_listos_f6,
        "todosListosF6": todos_listos_f6,

        "gruposListosRanking": grupos_listos_ranking,
        "todosListosRanking": todos_listos_ranking,

        "inicioFaseHabilitado": sesion.inicio_fase_habilitado,
        "totalListosInicio": total_inicio,
        "listosInicio": listos_inicio,
        "todosListosInicio": todos_inicio,
        "faseRequiereInicio": sesion.fase_actual in FASES_CON_INICIO_POR_ALUMNOS,

        **pitch_data,
    }

    return JsonResponse(data)

def evaluacion_actual_completa(sesion):
    grupo_actual = sesion.grupo_presentando
    if not grupo_actual:
        return False

    total_evaluadores = Grupo.objects.filter(sesion=sesion).exclude(pk=grupo_actual.pk).count()

    realizadas = Evaluacion.objects.filter(
        sesion=sesion,
        grupo_evaluado=grupo_actual
    ).exclude(
        grupo_evaluador=grupo_actual
    ).count()

    return total_evaluadores > 0 and realizadas >= total_evaluadores


def asignar_tematica_y_desafio_aleatorio(sesion):
    tematicas_activas = list(Tematica.objects.filter(activa=True))

    for grupo in Grupo.objects.filter(sesion=sesion):
        if grupo.listo_f2_desafio:
            continue

        slug = (grupo.tema_elegido or "").strip().lower()
        tematica = Tematica.objects.filter(slug=slug, activa=True).first()

        if not tematica:
            if not tematicas_activas:
                continue
            tematica = random.choice(tematicas_activas)

        desafios = list(Desafio.objects.filter(tematica=tematica, activo=True))

        if not desafios:
            continue

        desafio = random.choice(desafios)

        grupo.tema_elegido = tematica.slug
        grupo.listo_f2_tematica = True
        grupo.desafio_elegido = desafio
        grupo.desafio_id_externo = str(desafio.iddesafio)
        grupo.desafio_nombre = desafio.nombredesafio or ""
        grupo.desafio_descripcion = desafio.descripciondesafio or ""
        grupo.listo_f2_desafio = True

        grupo.save(update_fields=[
            "tema_elegido",
            "listo_f2_tematica",
            "desafio_elegido",
            "desafio_id_externo",
            "desafio_nombre",
            "desafio_descripcion",
            "listo_f2_desafio",
        ])


def completar_evaluaciones_faltantes(sesion):
    grupo_actual = sesion.grupo_presentando

    if not grupo_actual:
        return

    evaluadores = Grupo.objects.filter(sesion=sesion).exclude(pk=grupo_actual.pk)

    for evaluador in evaluadores:
        ya_evaluo = Evaluacion.objects.filter(
            sesion=sesion,
            grupo_evaluador=evaluador,
            grupo_evaluado=grupo_actual,
        ).exists()

        if ya_evaluo:
            continue

        Evaluacion.objects.create(
            sesion=sesion,
            grupo_evaluador=evaluador,
            grupo_evaluado=grupo_actual,
            claridad=5,
            creatividad=5,
            viabilidad=5,
            equipo=5,
            presentacion=5,
            comentario="Evaluación completada automáticamente porque se agotó el tiempo.",
            reflexion="",
        )

        evaluador.tokensgrupo = max((evaluador.tokensgrupo or 0) - 2, 0)
        evaluador.save(update_fields=["tokensgrupo"])


def avanzar_al_siguiente_pitch_o_ranking(sesion):
    actual = sesion.grupo_presentando

    if actual is None:
        sesion.fase_actual = "f6_ranking"
        sesion.save(update_fields=["fase_actual"])
        return

    siguiente = Grupo.objects.filter(
        sesion=sesion,
        orden_presentacion__gt=actual.orden_presentacion
    ).order_by("orden_presentacion").first()

    if siguiente is None:
        sesion.fase_actual = "f6_ranking"
        sesion.grupo_presentando = None
        sesion.save(update_fields=["fase_actual", "grupo_presentando"])
        return

    sesion.grupo_presentando = siguiente
    sesion.fase_actual = "f4_presentacion_pitch"
    sesion.segundos_restantes = int(sesion.t_pitch or 90)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None
    sesion.inicio_fase_habilitado = True

    sesion.save(update_fields=[
        "grupo_presentando",
        "fase_actual",
        "segundos_restantes",
        "timer_corriendo",
        "timer_inicio_at",
        "timer_fin_at",
        "inicio_fase_habilitado",
    ])


@require_POST
def guardar_tematica(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    if grupo.sesion.fase_actual != "f2_tematicas":
        return JsonResponse({"ok": False, "error": "La sesión no está en la etapa de temáticas."}, status=400)

    try:
        payload = json.loads(request.body or "{}")
        slug = str(payload.get("tema") or "").strip().lower()
    except Exception:
        return JsonResponse({"ok": False, "error": "Solicitud inválida."}, status=400)

    if not slug:
        return JsonResponse({"ok": False, "error": "Debes seleccionar una temática."}, status=400)

    tematica = Tematica.objects.filter(slug=slug, activa=True).first()

    if not tematica:
        return JsonResponse({"ok": False, "error": "Temática no válida."}, status=404)

    grupo.tema_elegido = tematica.slug

    grupo.save(update_fields=["tema_elegido"])

    return JsonResponse({
        "ok": True,
        "tema": tematica.slug,
        "redirect_url": reverse("desafios"),
    })

@require_POST
def aplicar_resultado_ruleta_lego(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        return JsonResponse({"ok": False, "error": "Solicitud inválida."}, status=400)

    delta = int(payload.get("tokens") or 0)

    if delta not in [-2, -1, 0, 1, 2]:
        return JsonResponse({"ok": False, "error": "Resultado inválido."}, status=400)

    with transaction.atomic():
        grupo = Grupo.objects.select_for_update().get(pk=grupo.pk)
        grupo.tokensgrupo = max((grupo.tokensgrupo or 0) + delta, 0)
        grupo.save(update_fields=["tokensgrupo"])

    return JsonResponse({
        "ok": True,
        "tokens": grupo.tokensgrupo,
        "delta": delta,
    })
@require_POST
def guardar_desafio(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    if grupo.sesion.fase_actual != "f2_tematicas":
        return JsonResponse({"ok": False, "error": "La sesión no está en la etapa de desafíos."}, status=400)

    try:
        payload = json.loads(request.body or "{}")
        desafio_id = str(payload.get("desafio_id") or "").strip()
    except Exception:
        return JsonResponse({"ok": False, "error": "Solicitud inválida."}, status=400)

    if not desafio_id:
        return JsonResponse({"ok": False, "error": "Debes seleccionar un desafío."}, status=400)

    tema = (grupo.tema_elegido or "").strip().lower()

    desafio = Desafio.objects.filter(
        iddesafio=desafio_id,
        tematica__slug=tema,
        activo=True
    ).first()

    if not desafio:
        return JsonResponse({"ok": False, "error": "Desafío no válido."}, status=404)

    grupo.desafio_elegido = desafio
    grupo.desafio_id_externo = str(desafio.iddesafio)
    grupo.desafio_nombre = desafio.nombredesafio or ""
    grupo.desafio_descripcion = desafio.descripciondesafio or ""
    grupo.listo_f2_desafio = True

    grupo.save(update_fields=[
        "desafio_elegido",
        "desafio_id_externo",
        "desafio_nombre",
        "desafio_descripcion",
        "listo_f2_desafio",
    ])

    return JsonResponse({
        "ok": True,
        "desafio_id": grupo.desafio_id_externo,
        "desafio_nombre": grupo.desafio_nombre,
        "desafio_descripcion": grupo.desafio_descripcion,
        "bloqueado": True,
    })

@require_POST
def desbloquear_desafio(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    if grupo.sesion.fase_actual != "f2_tematicas":
        return JsonResponse({"ok": False, "error": "No puedes cambiar el desafío en esta etapa."}, status=400)

    grupo.listo_f2_desafio = False
    grupo.save(update_fields=["listo_f2_desafio"])

    return JsonResponse({"ok": True})

@require_POST
def profesor_actualizar_estado(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)
    payload = json.loads(request.body or "{}")

    fase_anterior = sesion.fase_actual
    nueva_fase = payload.get("faseActual")

    accion_timer = payload.get("accionTimer")

    if accion_timer == "reiniciar_fase":
        sesion.segundos_restantes = tiempo_por_fase(sesion, sesion.fase_actual)
        sesion.timer_corriendo = False
        sesion.timer_inicio_at = None
        sesion.timer_fin_at = None
        sesion.save()

    elif accion_timer == "iniciar":
        segundos = int(sesion.segundos_restantes or tiempo_por_fase(sesion, sesion.fase_actual))

        sesion.segundos_restantes = segundos
        sesion.timer_corriendo = segundos > 0
        sesion.timer_inicio_at = timezone.now() if segundos > 0 else None
        sesion.timer_fin_at = timezone.now() + timedelta(seconds=segundos) if segundos > 0 else None
        sesion.save()

    elif accion_timer == "detener":
        restantes = calcular_segundos_restantes(sesion)
        sesion.segundos_restantes = restantes
        sesion.timer_corriendo = False
        sesion.timer_inicio_at = None
        sesion.timer_fin_at = None
        sesion.save()

    if nueva_fase:
        if nueva_fase not in FASES_ORDEN:
            return JsonResponse({"ok": False, "error": "Pantalla inválida"}, status=400)
        sesion.fase_actual = nueva_fase

    if nueva_fase and nueva_fase != fase_anterior:
        sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
        sesion.timer_corriendo = False
        sesion.timer_inicio_at = None
        sesion.timer_fin_at = None

        if nueva_fase == "f4_orden_pitch":
            Grupo.objects.filter(sesion=sesion).update(listo_f4_orden=False)
            sesion.orden_sorteado = False
            sesion.grupo_presentando = None
            Grupo.objects.filter(sesion=sesion).update(orden_presentacion=None)

        if nueva_fase == "f4_orden_pitch":
            Grupo.objects.filter(sesion=sesion).update(listo_f4_orden=False)

        if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS:
            sesion.inicio_fase_habilitado = False
            sesion.save(update_fields=[
                "fase_actual",
                "segundos_restantes",
                "timer_corriendo",
                "timer_inicio_at",
                "timer_fin_at",
                "inicio_fase_habilitado",
            ])
            reset_listos_inicio_fase(sesion, nueva_fase)
        else:
            sesion.inicio_fase_habilitado = True

            if nueva_fase == "f5_evaluacion_pitch":
                Grupo.objects.filter(sesion=sesion).update(
                    listo_ranking=False,
                    recompensa_peer_otorgada=False,
                )

            if nueva_fase in {"f1_ranking", "f2_ranking", "f3_ranking", "f6_ranking"}:
                Grupo.objects.filter(sesion=sesion).update(
                    listo_f6=False,
                    listo_ranking=False,
                )

            sesion.save()

    if "timerCorriendo" in payload:
        timer_corriendo = bool(payload["timerCorriendo"])

        if timer_corriendo:
            segundos_base = int(payload.get("segundosRestantes", sesion.segundos_restantes or 0))
            sesion.segundos_restantes = max(segundos_base, 0)
            sesion.timer_corriendo = sesion.segundos_restantes > 0
            sesion.timer_inicio_at = timezone.now() if sesion.timer_corriendo else None
            sesion.timer_fin_at = (
                timezone.now() + timedelta(seconds=sesion.segundos_restantes)
                if sesion.timer_corriendo else None
            )
        else:
            restantes = calcular_segundos_restantes(sesion)
            sesion.segundos_restantes = restantes
            sesion.timer_corriendo = False
            sesion.timer_inicio_at = None
            sesion.timer_fin_at = None

    elif "segundosRestantes" in payload:
        sesion.segundos_restantes = max(int(payload["segundosRestantes"]), 0)
        sesion.timer_corriendo = False
        sesion.timer_inicio_at = None
        sesion.timer_fin_at = None

    sesion.save()

    return JsonResponse({
        "esProfesor": True,
        "ok": True,
        "faseActual": sesion.fase_actual,
        "faseEtiqueta": ETIQUETA_FASE.get(sesion.fase_actual, sesion.fase_actual),
        "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": calcular_segundos_restantes(sesion),
        **serializar_estado_pitch(sesion),
    })

@require_POST
def dev_timer_10_segundos(request, sesion_id):
    if not settings.DEBUG:
        return JsonResponse({
            "ok": False,
            "error": "Esta función solo está disponible en modo desarrollo."
        }, status=403)

    sesion = get_object_or_404(Sesion, pk=sesion_id)

    segundos = 10
    ahora = timezone.now()

    sesion.segundos_restantes = segundos
    sesion.timer_corriendo = True
    sesion.timer_inicio_at = ahora
    sesion.timer_fin_at = ahora + timedelta(seconds=segundos)
    sesion.save(update_fields=[
        "segundos_restantes",
        "timer_corriendo",
        "timer_inicio_at",
        "timer_fin_at",
    ])

    return JsonResponse({
        "ok": True,
        "segundosRestantes": segundos,
        "faseActual": sesion.fase_actual,
    })

@require_POST
def profesor_siguiente_fase(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    if sesion.fase_actual == "f2_tematicas":
        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f2_desafio=True).count()

        if total == 0 or listos < total:
            return JsonResponse({
                "ok": False,
                "error": f"Aún faltan grupos por elegir desafío ({listos}/{total})."
            }, status=400)

    try:
        idx = FASES_ORDEN.index(sesion.fase_actual)
    except ValueError:
        return JsonResponse({"ok": False, "error": "Fase actual inválida"}, status=400)

    if idx + 1 >= len(FASES_ORDEN):
        return JsonResponse({"ok": False, "error": "Ya está en la última fase"}, status=400)

    nueva_fase = FASES_ORDEN[idx + 1]


    sesion.fase_actual = nueva_fase
    sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None


    if nueva_fase in {"f2_tematicas", "f5_evaluacion_pitch"}:
        ahora = timezone.now()
        sesion.timer_corriendo = sesion.segundos_restantes > 0
        sesion.timer_inicio_at = ahora if sesion.timer_corriendo else None
        sesion.timer_fin_at = ahora + timedelta(seconds=sesion.segundos_restantes) if sesion.timer_corriendo else None

    if nueva_fase == "f4_orden_pitch":
        Grupo.objects.filter(sesion=sesion).update(listo_f4_orden=False, orden_presentacion=None)
        sesion.orden_sorteado = False
        sesion.grupo_presentando = None

    if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS:
        sesion.inicio_fase_habilitado = False
        sesion.save(update_fields=[
            "fase_actual",
            "segundos_restantes",
            "timer_corriendo",
            "timer_inicio_at",
            "timer_fin_at",
            "inicio_fase_habilitado",
        ])
        reset_listos_inicio_fase(sesion, nueva_fase)
    else:
        sesion.inicio_fase_habilitado = True
        sesion.save()

    return JsonResponse({
        "esProfesor": True,
        "ok": True,
        "faseActual": sesion.fase_actual,
        "faseEtiqueta": ETIQUETA_FASE.get(sesion.fase_actual, sesion.fase_actual),
        "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": calcular_segundos_restantes(sesion),
        **serializar_estado_pitch(sesion),
    })


@require_POST
def marcar_listo_ranking(request, grupo_id):
    grupo = get_object_or_404(Grupo, pk=grupo_id)

    grupo.listo_ranking = True
    grupo.save(update_fields=["listo_ranking"])

    sesion = grupo.sesion
    total_grupos = Grupo.objects.filter(sesion=sesion).count()
    grupos_listos_ranking = Grupo.objects.filter(sesion=sesion, listo_ranking=True).count()


    return JsonResponse({
        "ok": True,
        "grupoId": grupo.idgrupo,
        "listoRanking": True,
        "gruposListosRanking": grupos_listos_ranking,
        "totalGrupos": total_grupos,
        "todosListosRanking": total_grupos > 0 and grupos_listos_ranking == total_grupos,
    })

@require_POST
def marcar_grupo_listo(request, grupo_id):
    grupo = get_object_or_404(Grupo, pk=grupo_id)
    sesion = grupo.sesion
    fase_actual = sesion.fase_actual

    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        payload = {}

    fase_clave = payload.get("fase")

    # ============================================================
    # LOBBY / BIENVENIDA / CONOCIDOS
    # ============================================================
    if fase_actual in ["lobby", "f1_bienvenida", "f1_conocidos"]:
        if not grupo.listo_lobby:
            grupo.listo_lobby = True
            grupo.save(update_fields=["listo_lobby"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_lobby=True).count()
        todos = total > 0 and listos == total

        if fase_actual == "f1_conocidos" and todos and not sesion.inicio_fase_habilitado:
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=["inicio_fase_habilitado"])

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosLobby": listos,
            "todosListosLobby": todos,
            "inicio_fase_habilitado": sesion.inicio_fase_habilitado if fase_actual == "f1_conocidos" else True,
            "segundosRestantes": sesion.segundos_restantes,
        })

    # ============================================================
    # F1 — TRANSICIÓN TRABAJO EN EQUIPO
    # ============================================================
    if fase_actual == "f1_pre_sopa" and fase_clave == "f1":
        if not grupo.listo_f1:
            grupo.listo_f1 = True
            grupo.save(update_fields=["listo_f1"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f1=True).count()
        todos = total > 0 and listos == total

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF1": listos,
            "todosListosF1": todos,
        })

    # ============================================================
    # F1 — INICIO SOPA DE LETRAS
    # Botón "Listo para comenzar" dentro de la sopa.
    # ============================================================
    if fase_actual == "f1_sopa" and fase_clave in ["f1_sopa", "sopa", "f1", None, ""]:
        if not grupo.listo_f1:
            grupo.listo_f1 = True
            grupo.save(update_fields=["listo_f1"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f1=True).count()
        todos = total > 0 and listos == total

        if todos and not sesion.inicio_fase_habilitado:
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=["inicio_fase_habilitado"])

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF1": listos,
            "todosListosF1": todos,
            "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
            "segundosRestantes": sesion.segundos_restantes,
        })

    # ============================================================
    # F2 — TRANSICIÓN DESAFÍOS
    # ============================================================
    if fase_actual == "f2_transicion" and fase_clave == "f2":
        if not grupo.listo_f2:
            grupo.listo_f2 = True
            grupo.save(update_fields=["listo_f2"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f2=True).count()
        todos = total > 0 and listos == total

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF2Generico": listos,
            "todosListosF2Generico": todos,
        })

    # ============================================================
    # F2 — TEMÁTICAS
    # ============================================================
    if fase_actual == "f2_tematicas" and fase_clave == "f2_tematicas":
        if not grupo.listo_f2_tematicas:
            grupo.listo_f2_tematicas = True
            grupo.save(update_fields=["listo_f2_tematicas"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f2_tematicas=True).count()
        todos = total > 0 and listos == total

        if todos and not sesion.inicio_fase_habilitado:
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=["inicio_fase_habilitado"])

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF2Tematicas": listos,
            "todosListosF2Tematicas": todos,
            "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
            "segundosRestantes": sesion.segundos_restantes,
        })

    # ============================================================
    # F2 — TRANSICIÓN EMPATÍA
    # ============================================================
    if fase_actual == "f2_transicion_empatia" and fase_clave == "f2_empatia":
        if not getattr(grupo, "listo_f2_empatia", False):
            grupo.listo_f2_empatia = True
            grupo.save(update_fields=["listo_f2_empatia"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f2_empatia=True).count()
        todos = total > 0 and listos == total

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF2Empatia": listos,
            "todosListosF2Empatia": todos,
        })

    # ============================================================
    # F2 — BUBBLE MAP
    # ============================================================
    if fase_actual == "f2_bubblemap" and fase_clave == "f2_bubblemap":
        if not grupo.listo_f2:
            grupo.listo_f2 = True
            grupo.save(update_fields=["listo_f2"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f2=True).count()
        todos = total > 0 and listos == total

        if todos and not sesion.inicio_fase_habilitado:
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=["inicio_fase_habilitado"])

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF2": listos,
            "todosListosF2": todos,
            "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
            "segundosRestantes": sesion.segundos_restantes,
        })

    # ============================================================
    # F3 — TRANSICIÓN CREATIVIDAD
    # ============================================================
    if fase_actual == "f3_transicion_creatividad" and fase_clave == "f3":
        if not grupo.listo_f3:
            grupo.listo_f3 = True
            grupo.save(update_fields=["listo_f3"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f3=True).count()
        todos = total > 0 and listos == total

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF3": listos,
            "todosListosF3": todos,
        })

    # ============================================================
    # F3 — INICIO LEGO
    # ============================================================
    if fase_actual == "f3_lego" and fase_clave in ["inicio_f3", "f3_lego", "f3", None, ""]:
        if not grupo.listo_inicio_f3:
            grupo.listo_inicio_f3 = True
            grupo.save(update_fields=["listo_inicio_f3"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_inicio_f3=True).count()
        todos = total > 0 and listos == total

        if todos and not sesion.inicio_fase_habilitado:
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=["inicio_fase_habilitado"])

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosInicioF3": listos,
            "todosListosInicioF3": todos,
            "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
            "segundosRestantes": sesion.segundos_restantes,
        })

    # ============================================================
    # F4 — TRANSICIÓN COMUNICACIÓN
    # ============================================================
    if fase_actual == "f4_transicion_comunicacion" and fase_clave == "f4":
        if not grupo.listo_f4:
            grupo.listo_f4 = True
            grupo.save(update_fields=["listo_f4"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f4=True).count()
        todos = total > 0 and listos == total

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF4": listos,
            "todosListosF4": todos,
        })

    # ============================================================
    # F4 — INICIO CONSTRUCCIÓN PITCH
    # ============================================================
    if fase_actual == "f4_construccion_pitch" and fase_clave in ["f4_pitch", "f4_construccion_pitch", "f4", None, ""]:
        if not grupo.listo_f4:
            grupo.listo_f4 = True
            grupo.save(update_fields=["listo_f4"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f4=True).count()
        todos = total > 0 and listos == total

        if todos and not sesion.inicio_fase_habilitado:
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=["inicio_fase_habilitado"])

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF4": listos,
            "todosListosF4": todos,
            "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
            "segundosRestantes": sesion.segundos_restantes,
        })

    # ============================================================
    # F4 — ORDEN PRESENTACIÓN PITCH
    # ============================================================
    if fase_actual == "f4_orden_pitch" and fase_clave in ["f4_orden_pitch", "orden_pitch", "f4_orden", None, ""]:
        if not grupo.listo_f4_orden:
            grupo.listo_f4_orden = True
            grupo.save(update_fields=["listo_f4_orden"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f4_orden=True).count()
        todos = total > 0 and listos == total

        autoavanzar_si_todos_listos(sesion)
        sesion.refresh_from_db()

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF4Orden": listos,
            "todosListosF4Orden": todos,
            "ordenSorteado": getattr(sesion, "orden_sorteado", False),
        })

    # ============================================================
    # RANKING PARCIAL
    # ============================================================
    if fase_actual in {"f1_ranking", "f2_ranking", "f3_ranking"} and fase_clave == "ranking":
        if not grupo.listo_ranking:
            grupo.listo_ranking = True
            grupo.save(update_fields=["listo_ranking"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_ranking=True).count()
        todos = total > 0 and listos == total

        if todos:
            nueva_fase = siguiente_fase_automatica(fase_actual)

            sesion.fase_actual = nueva_fase
            sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
            sesion.timer_corriendo = False
            sesion.timer_inicio_at = None
            sesion.timer_fin_at = None
            sesion.inicio_fase_habilitado = False if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS else True
            sesion.save(update_fields=[
                "fase_actual",
                "segundos_restantes",
                "timer_corriendo",
                "timer_inicio_at",
                "timer_fin_at",
                "inicio_fase_habilitado",
            ])

            Grupo.objects.filter(sesion=sesion).update(
                listo_ranking=False,
                listo_f6=False,
            )

            if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS:
                reset_listos_inicio_fase(sesion, nueva_fase)

            return JsonResponse({
                "ok": True,
                "fase": fase_actual,
                "faseActual": sesion.fase_actual,
                "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
                "total": total,
                "listos": listos,
                "gruposListos": listos,
                "totalGrupos": total,
                "todos_listos": todos,
                "gruposListosRanking": listos,
                "todosListosRanking": todos,
            })

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosRanking": listos,
            "todosListosRanking": todos,
        })

    # ============================================================
    # RANKING FINAL
    # ============================================================
    if fase_actual == "f6_ranking" and fase_clave == "f6":
        if not grupo.listo_f6:
            grupo.listo_f6 = True
            grupo.save(update_fields=["listo_f6"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f6=True).count()
        todos = total > 0 and listos == total

        if todos:
            nueva_fase = siguiente_fase_automatica(fase_actual)
            if nueva_fase == "reflexion":
                borrar_fotos_lego_sesion(sesion)
            sesion.fase_actual = nueva_fase
            sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
            sesion.timer_corriendo = False
            sesion.timer_inicio_at = None
            sesion.timer_fin_at = None
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=[
                "fase_actual",
                "segundos_restantes",
                "timer_corriendo",
                "timer_inicio_at",
                "timer_fin_at",
                "inicio_fase_habilitado",
            ])

            Grupo.objects.filter(sesion=sesion).update(
                listo_f6=False,
                listo_ranking=False,
            )

            return JsonResponse({
                "ok": True,
                "fase": fase_actual,
                "faseActual": sesion.fase_actual,
                "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
                "total": total,
                "listos": listos,
                "gruposListos": listos,
                "totalGrupos": total,
                "todos_listos": todos,
                "gruposListosF6": listos,
                "todosListosF6": todos,
            })

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF6": listos,
            "todosListosF6": todos,
        })

    # ============================================================
    # SI NO COINCIDE NINGÚN CASO
    # ============================================================
    return JsonResponse({
        "ok": False,
        "error": f"No se pudo marcar listo. Fase actual: {fase_actual}, fase recibida: {fase_clave}"
    }, status=400)

@require_POST
def iniciar_timer_inicio_fase(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    if sesion.fase_actual not in FASES_CON_INICIO_POR_ALUMNOS:
        return JsonResponse({
            "ok": False,
            "error": "La fase actual no usa inicio grupal."
        }, status=400)

    if not sesion.inicio_fase_habilitado:
        return JsonResponse({
            "ok": False,
            "error": "La fase aún no está habilitada."
        }, status=400)

    if not sesion.timer_corriendo:
        iniciar_timer_de_sesion(sesion)
        sesion.refresh_from_db()

    return JsonResponse({
        "ok": True,
        "faseActual": sesion.fase_actual,
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": int(sesion.segundos_restantes or 0),
    })

@never_cache
def continuar_desde_mapa(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return redirect("registro")

    sesion = grupo.sesion
    fase_actual = sesion.fase_actual

    mapa_a_fase = {
        "intro_habilidades": "f1_conocidos",
        "mapa_f2_empatia": "f2_transicion",
        "mapa_f3_creatividad": "f3_transicion_creatividad",
        "mapa_f4_final": "f4_transicion_comunicacion",
    }

    nueva_fase = mapa_a_fase.get(fase_actual)

    if not nueva_fase:
        return redirect(ruta_alumno_por_estado(grupo))

    sesion.fase_actual = nueva_fase
    sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None
    sesion.inicio_fase_habilitado = False if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS else True
    sesion.save()

    if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS:
        reset_listos_inicio_fase(sesion, nueva_fase)

    return redirect(ruta_alumno_por_estado(grupo))

@never_cache
def habilidades_intro(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return redirect("registro")

    sesion = grupo.sesion
    fase_actual = sesion.fase_actual

    estado_mapa = {
        "habilidad_activa": "trabajo en equipo",
        "habilidades_completadas": [],
        "ruta_continuar": reverse("continuar_desde_mapa"),
        "texto_boton": "CONTINUAR A TRABAJO EN EQUIPO",
        "titulo_mapa": "HABILIDADES DE MISIÓN",
    }

    if fase_actual in ["mapa_f2_empatia", "f2_transicion", "f2_tematicas", "f2_transicion_empatia", "f2_bubblemap", "f2_ranking"]:
        estado_mapa = {
            "habilidad_activa": "empatia",
            "habilidades_completadas": ["trabajo en equipo"],
            "ruta_continuar": reverse("continuar_desde_mapa"),
            "texto_boton": "CONTINUAR A EMPATÍA",
            "titulo_mapa": "HABILIDADES DE MISIÓN",
        }

    elif fase_actual in ["mapa_f3_creatividad", "f3_transicion_creatividad", "f3_lego", "f3_ranking"]:
        estado_mapa = {
            "habilidad_activa": "creatividad",
            "habilidades_completadas": ["trabajo en equipo", "empatia"],
            "ruta_continuar": reverse("continuar_desde_mapa"),
            "texto_boton": "CONTINUAR A CREATIVIDAD",
            "titulo_mapa": "HABILIDADES DE MISIÓN",
        }

    elif fase_actual in [
        "mapa_f4_final",
        "f4_transicion_comunicacion",
        "f4_construccion_pitch",
        "f4_orden_pitch",
        "f4_presentacion_pitch",
        "f5_evaluacion_pitch",
        "f6_ranking",
    ]:
        estado_mapa = {
            "habilidad_activa": "mision final",
            "habilidades_completadas": ["trabajo en equipo", "empatia", "creatividad"],
            "ruta_continuar": reverse("continuar_desde_mapa"),
            "texto_boton": "CONTINUAR A MISIÓN FINAL",
            "titulo_mapa": "MISIÓN FINAL",
        }

    return render(request, "habilidades_intro.html", {
    "grupo": grupo,
    "sesion": sesion,
    "estado_mapa": estado_mapa,
    "habilidades_completadas_json": json.dumps(
        estado_mapa["habilidades_completadas"],
        ensure_ascii=False
    ),
})

@never_cache
def pantalla_espera(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        messages.error(request, "Debes ingresar con tu código.")
        return redirect("registro")

    ruta = ruta_alumno_por_estado(grupo)
    if ruta != "pantalla_espera":
        return redirect(ruta)

    return render(request, "pantalla_espera.html", {"grupo": grupo})


def pantalla_inicio(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "pantalla_inicio"):
        return redirect("pantalla_espera")
    return render(request, "pantalla_inicio.html", {"grupo": grupo})


def trabajoenequipo(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "trabajoenequipo"):
        return redirect("pantalla_espera")
    return render(request, "trabajoenequipo.html", {"grupo": grupo})

@never_cache
def tematicas(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "tematicas"):
        return redirect("pantalla_espera")

    if (grupo.tema_elegido or "").strip():
        return redirect("desafios")

    tematicas_bd = Tematica.objects.filter(activa=True).order_by("orden", "title")

    return render(request, "tematicas.html", {
        "grupo": grupo,
        "tema_actual": (grupo.tema_elegido or "").strip().lower(),
        "tematicas": tematicas_bd,
    })

@never_cache
def lego(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "lego"):
        return redirect("pantalla_espera")

    sesion = grupo.sesion

    if request.method == "POST":
        sin_foto = request.POST.get("sin_foto_lego") == "on"
        foto = request.FILES.get("foto_lego")

        if sin_foto:
            grupo.foto_lego = None
            grupo.listo_f3_lego = True
            grupo.lego_sin_foto = True
            grupo.save(update_fields=["foto_lego", "listo_f3_lego", "lego_sin_foto"])

        elif foto:
            grupo.foto_lego = foto
            grupo.listo_f3_lego = True
            grupo.lego_sin_foto = False
            grupo.save(update_fields=["foto_lego", "listo_f3_lego", "lego_sin_foto"])

            limpiar_fotos_lego_por_desafio(grupo.desafio_elegido)

        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({
                    "ok": False,
                    "error": "Debes subir una foto o marcar que no pudieron subirla."
                }, status=400)

            messages.error(request, "Debes subir una foto o marcar que no pudieron subirla.")
            return render(request, "lego.html", {
                "grupo": grupo,
                "desafio_nombre_actual": grupo.desafio_nombre or "Desafío no seleccionado",
                "desafio_descripcion_actual": grupo.desafio_descripcion or "Aún no hay descripción disponible para este desafío.",
                "tiempo_inicial_lego": grupo.sesion.segundos_restantes or 15,
                "opciones_ruleta": RuletaLegoOpcion.objects.filter(activa=True).order_by("orden")[:8],
            })

        autoavanzar_si_todos_listos(sesion)
        sesion.refresh_from_db()

        total_grupos = Grupo.objects.filter(sesion=sesion).count()
        grupos_listos = Grupo.objects.filter(sesion=sesion, listo_f3_lego=True).count()
        grupos_con_foto = Grupo.objects.filter(sesion=sesion, listo_f3_lego=True, foto_lego__isnull=False).count()
        grupos_sin_foto = Grupo.objects.filter(sesion=sesion, listo_f3_lego=True, lego_sin_foto=True).count()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "ok": True,
                "gruposListosF3Lego": grupos_listos,
                "gruposConFotoLego": grupos_con_foto,
                "gruposSinFotoLego": grupos_sin_foto,
                "totalGrupos": total_grupos,
                "todosListosF3Lego": total_grupos > 0 and grupos_listos == total_grupos,
                "faseActual": sesion.fase_actual,
                "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
            })

        return redirect("lego")

    return render(request, "lego.html", {
        "grupo": grupo,
        "desafio_nombre_actual": grupo.desafio_nombre or "Desafío no seleccionado",
        "desafio_descripcion_actual": grupo.desafio_descripcion or "Aún no hay descripción disponible para este desafío.",
        "tiempo_inicial_lego": grupo.sesion.segundos_restantes or 15,
        "opciones_ruleta": RuletaLegoOpcion.objects.filter(activa=True).order_by("orden")[:8],
    })


#NUEVO CIERRRE
def perfiles(request):
    return render(request, 'perfiles.html')


def bienvenida(request):
    return render(request, 'bienvenida.html')

def registro(request):
    error = None

    nombres_aleatorios = [
        "Equipo Cóndor",
        "Misión Alfa",
        "Agentes UDD",
        "Mentes Creativas",
        "Los Innovadores",
        "Escuadrón Delta",
        "Visionarios UDD",
        "Código Naranja",
        "Equipo Fénix",
        "StartUp Squad",
        "Los Estrategas",
        "Comando Emprende",
    ]

    if request.method == "POST":
        codigo = (request.POST.get("id_grupo") or "").strip()
        nombre_grupo = (request.POST.get("nombre_grupo") or "").strip()

        if not codigo:
            error = "Debes ingresar el código de escuadrón"
            return render(request, "registro.html", {"error": error})

        try:
            grupo = Grupo.objects.select_related("sesion").get(codigoacceso__iexact=codigo)
        except Grupo.DoesNotExist:
            error = "Código de grupo inválido"
            return render(request, "registro.html", {"error": error})

        if not grupo.sesion:
            error = "Este grupo no está asociado a ninguna sesión"
            return render(request, "registro.html", {"error": error})

        if not nombre_grupo:
            nombre_grupo = random.choice(nombres_aleatorios)

        grupo.nombregrupo = nombre_grupo[:100]
        grupo.save(update_fields=["nombregrupo"])

        request.session.flush()
        request.session.cycle_key()
        request.session["grupo_id"] = grupo.idgrupo
        request.session["sesion_id"] = grupo.sesion_id
        request.session["ranking_flags_reseteados"] = False
        request.session.modified = True

        print(
            f"registro -> codigo={codigo} | grupo={grupo.idgrupo} "
            f"| nombre={grupo.nombregrupo} | sesion={grupo.sesion.idsesion if grupo.sesion else 'SIN SESION'}"
        )

        return redirect("bienvenida")

    return render(request, "registro.html", {"error": error})


def introducciones(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "introducciones"):
        return redirect("pantalla_espera")
    return render(request, "introducciones.html", {"grupo": grupo})

def promptconocidos(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "promptconocidos"):
        return redirect("pantalla_espera")
    return render(request, "promptconocidos.html", {"grupo": grupo})

def conocidos(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "conocidos"):
        return redirect("pantalla_espera")
    return render(request, "conocidos.html", {"grupo": grupo})

def minijuego1(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "minijuego1"):
        return redirect("pantalla_espera")
    return render(request, "minijuego1.html", {
        "grupo": grupo,
        "sopa_ganada": bool(grupo.sopa_ganada),
    })

@require_POST
def sopa_completada(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return JsonResponse({
            "ok": False,
            "error": "No se pudo identificar tu grupo."
        }, status=403)

    with transaction.atomic():
        grupo = Grupo.objects.select_for_update().get(pk=grupo.pk)
        sesion = Sesion.objects.select_for_update().get(pk=grupo.sesion_id)

        if grupo.sopa_ganada:
            return JsonResponse({
                "ok": True,
                "ya_completada": True,
                "bonus_otorgado": 0,
                "primer_equipo": False,
                "todos_terminaron": False,
                "ranking_disparado": False,
                "faseActual": sesion.fase_actual,
                "rutaAlumno": reverse("minijuego1"),
                "sopa_tiempo_segundos": grupo.sopa_tiempo_segundos,
            })

        ya_habia_otro = Grupo.objects.select_for_update().filter(
            sesion=sesion,
            sopa_ganada=True
        ).exclude(pk=grupo.pk).exists()

        primer_equipo = not ya_habia_otro

        # Regla:
        # - Primer equipo: 5 tokens
        # - Equipos siguientes: 3 tokens
        bonus = 5 if primer_equipo else 3

        ahora = timezone.now()

        # Tiempo usado desde que comenzó realmente el timer de la fase.
        # Si por alguna razón no existe timer_inicio_at, se guarda None.
        tiempo_segundos = None

        if sesion.timer_inicio_at:
            tiempo_segundos = int((ahora - sesion.timer_inicio_at).total_seconds())
            tiempo_segundos = max(tiempo_segundos, 0)

        grupo.tokensgrupo = (grupo.tokensgrupo or 0) + bonus
        grupo.sopa_ganada = True
        grupo.sopa_tiempo_segundos = tiempo_segundos
        grupo.sopa_completada_en = ahora

        grupo.save(update_fields=[
            "tokensgrupo",
            "sopa_ganada",
            "sopa_tiempo_segundos",
            "sopa_completada_en",
        ])

        total_grupos = Grupo.objects.filter(sesion=sesion).count()
        grupos_terminados = Grupo.objects.filter(
            sesion=sesion,
            sopa_ganada=True
        ).count()

        todos_terminaron = total_grupos > 0 and grupos_terminados == total_grupos
        ranking_disparado = False

        if todos_terminaron:
            sesion.fase_actual = "f1_ranking"
            sesion.segundos_restantes = 0
            sesion.timer_corriendo = False
            sesion.timer_inicio_at = None
            sesion.timer_fin_at = None
            sesion.inicio_fase_habilitado = True

            sesion.save(update_fields=[
                "fase_actual",
                "segundos_restantes",
                "timer_corriendo",
                "timer_inicio_at",
                "timer_fin_at",
                "inicio_fase_habilitado",
            ])

            Grupo.objects.filter(sesion=sesion).update(
                listo_f6=False,
                listo_ranking=False,
            )

            ranking_disparado = True

    return JsonResponse({
        "ok": True,
        "bonus_otorgado": bonus,
        "primer_equipo": primer_equipo,
        "todos_terminaron": todos_terminaron,
        "ranking_disparado": ranking_disparado,
        "gruposTerminados": grupos_terminados,
        "totalGrupos": total_grupos,
        "faseActual": sesion.fase_actual,
        "rutaAlumno": reverse("ranking") if ranking_disparado else reverse("minijuego1"),
        "sopa_tiempo_segundos": tiempo_segundos,
    })

@require_POST
def registrar_palabra_sopa(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "No se pudo identificar tu grupo."}, status=403)

    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        payload = {}

    palabra = (payload.get("palabra") or "").strip().upper()
    if not palabra:
        return JsonResponse({"ok": False, "error": "Palabra inválida."}, status=400)

    with transaction.atomic():
        _, creada = PalabraSopaEncontrada.objects.get_or_create(
            sesion=grupo.sesion,
            grupo=grupo,
            palabra=palabra,
        )

        if creada:
            Grupo.objects.filter(pk=grupo.pk).update(tokensgrupo=F("tokensgrupo") + 1)

    return JsonResponse({
        "ok": True,
        "nueva": creada,
    })

def dashboardprofesor(request):
    profesor = Profesor.objects.first()
    sesion = None

    if profesor:
        sesion = Sesion.objects.filter(profesor=profesor).order_by("-fecha_creacion").first()

    return render(request, "dashboardprofesor.html", {"sesion": sesion})

def control_sesion(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)
    grupos = Grupo.objects.filter(sesion=sesion).order_by("idgrupo")

    return render(request, "control_sesion.html", {
        "sesion": sesion,
        "grupos": grupos,
        "es_profesor_panel": True,
    })



def porcentaje(parte, total):
    if not total:
        return 0
    return round((parte / total) * 100)


def dashboardadmin(request):
    total_grupos = Grupo.objects.count()

    grupos_sopa = Grupo.objects.filter(sopa_ganada=True).count()
    grupos_pitch = Grupo.objects.exclude(pitch_texto__isnull=True).exclude(pitch_texto__exact="").count()
    grupos_lego = Grupo.objects.exclude(foto_lego__isnull=True).exclude(foto_lego__exact="").count()

    tematicas_raw = (
        Grupo.objects
        .exclude(tema_elegido__isnull=True)
        .exclude(tema_elegido__exact="")
        .values("tema_elegido")
        .annotate(total=Count("idgrupo"))
        .order_by("-total")[:5]
    )

    max_tematica = max([x["total"] for x in tematicas_raw], default=0)

    tematicas_stats = []
    for item in tematicas_raw:
        nombre = item["tema_elegido"]
        tematica = Tematica.objects.filter(slug=nombre).first()
        tematicas_stats.append({
            "nombre": tematica.title if tematica else nombre,
            "total": item["total"],
            "porcentaje": porcentaje(item["total"], max_tematica),
        })

    desafios_raw = (
        Grupo.objects
        .exclude(desafio_nombre__isnull=True)
        .exclude(desafio_nombre__exact="")
        .values("desafio_nombre")
        .annotate(total=Count("idgrupo"))
        .order_by("-total")[:5]
    )

    max_desafio = max([x["total"] for x in desafios_raw], default=0)

    desafios_stats = [
        {
            "nombre": item["desafio_nombre"],
            "total": item["total"],
            "porcentaje": porcentaje(item["total"], max_desafio),
        }
        for item in desafios_raw
    ]

    sesiones_recientes = []
    for sesion in Sesion.objects.all().order_by("-idsesion")[:6]:
        grupos = Grupo.objects.filter(sesion=sesion)
        total = grupos.count()

        sesiones_recientes.append({
            "nombre": f"Sesión {sesion.idsesion}",
            "fase_actual": sesion.fase_actual,
            "total_grupos": total,
            "sopa": porcentaje(grupos.filter(sopa_ganada=True).count(), total),
            "pitch": porcentaje(
                grupos.exclude(pitch_texto__isnull=True).exclude(pitch_texto__exact="").count(),
                total
            ),
            "lego": porcentaje(
                grupos.exclude(foto_lego__isnull=True).exclude(foto_lego__exact="").count(),
                total
            ),
        })

    kpis = {
        "profesores": Profesor.objects.count(),
        "grupos": total_grupos,
        "sesiones": Sesion.objects.count(),
        "desafios_activos": Desafio.objects.filter(activo=True).count(),
        "pct_sopa": porcentaje(grupos_sopa, total_grupos),
        "pct_pitch": porcentaje(grupos_pitch, total_grupos),
        "pct_lego": porcentaje(grupos_lego, total_grupos),
    }

    return render(request, "dashboardadmin.html", {
        "kpis": kpis,
        "tematicas_stats": tematicas_stats,
        "desafios_stats": desafios_stats,
        "sesiones_recientes": sesiones_recientes,
    })


def agregardesafio(request):

    admin = Idadministrador.objects.first()

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        tokens = request.POST.get("tokens")

        if not nombre or not tokens:
            messages.error(request, "Debes ingresar nombre y tokens.")
            return redirect("agregardesafio")

        Desafio.objects.create(
            idadministrador_idadministrador=admin,
            nombredesafio=nombre,
            descripciondesafio=descripcion,
            tokensdesafio=int(tokens)
        )

        messages.success(request, "Desafío creado correctamente")
        return redirect("agregardesafio")
    
    return render(request, 'agregardesafio.html')

def lista_desafios(request):
    desafios = Desafio.objects.all().order_by('iddesafio')
    return render(request, 'listadesafios.html', {
        'desafios': desafios,
    })


def eliminar_desafio(request, iddesafio):
    desafio = get_object_or_404(Desafio, pk=iddesafio)

    if request.method == "POST":
        desafio.delete()
        messages.success(request, "Desafío eliminado correctamente 🗑️")
        return redirect('lista_desafios')

    return redirect('lista_desafios')

def transicionempatia(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "transicionempatia"):
        return redirect("pantalla_espera")
    return render(request, "transicionempatia.html", {"grupo": grupo})


def transicioncreatividad(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "transicioncreatividad"):
        return redirect("pantalla_espera")
    return render(request, "transicioncreatividad.html", {"grupo": grupo})

def transicioncomunicacion(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "transicioncomunicacion"):
        return redirect("pantalla_espera")
    return render(request, "transicioncomunicacion.html", {"grupo": grupo})


def transiciondesafio(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "transiciondesafio"):
        return redirect("pantalla_espera")
    return render(request, "transiciondesafio.html", {"grupo": grupo})


def transicionapoyo(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "transicionapoyo"):
        return redirect("pantalla_espera")
    return render(request, "transicionapoyo.html", {"grupo": grupo})

@transaction.atomic
def asignar_alumnos_a_grupos(sesion: Sesion):

    alumnos = list(
        Alumno.objects.filter(sesion=sesion, grupo__isnull=True)
        .order_by('idalumno')
    )

    if not alumnos:
        print("No hay alumnos sin grupo en esta sesión.")
        return 0

    grupos = list(Grupo.objects.filter(sesion=sesion).order_by('idgrupo'))

    if not grupos:
        n_alumnos = len(alumnos)
        num_grupos = ceil(n_alumnos / 8)

        for i in range(num_grupos):
            grupos.append(
                Grupo.objects.create(
                    sesion=sesion,
                    nombregrupo=f"Grupo {i+1}",
                    usuario_idusuario=None,
                    tokensgrupo=10,
                    etapa=1,
                    codigoacceso=generar_codigo_acceso(),
                )
            )
    else:
        for g in grupos:
            if not g.codigoacceso:
                g.codigoacceso = generar_codigo_acceso()
                g.save()

    n_alumnos = len(alumnos)
    n_grupos = len(grupos)

    capacidad_base = n_alumnos // n_grupos
    sobrantes = n_alumnos % n_grupos

    index_alumno = 0

    for i, grupo in enumerate(grupos):
        cantidad = capacidad_base + (1 if i < sobrantes else 0)

        for _ in range(cantidad):
            if index_alumno >= n_alumnos:
                break

            alumno = alumnos[index_alumno]
            alumno.grupo = grupo
            alumno.save()
            index_alumno += 1

    print(f"Asignados {index_alumno} alumnos en sesión {sesion.idsesion}")
    return index_alumno


def registrargrupos(request):
    profesor = Profesor.objects.first()

    if not profesor:
        messages.warning(
            request,
            "Primero debes registrar un profesor."
        )
        return redirect("registrarprofesor")

    sesion_activa = (
        Sesion.objects.filter(profesor=profesor)
        .order_by('-fecha_creacion')
        .first()
    )

    if not sesion_activa:
        messages.warning(
            request,
            "Aún no tienes sesiones creadas. Primero crea una sesión."
        )
        return redirect('crear_sesion')

    if request.method == "POST":
        cantidad = asignar_alumnos_a_grupos(sesion_activa)
        if cantidad == 0:
            messages.info(request, "No había alumnos sin grupo en esta sesión.")
        else:
            messages.success(
                request,
                f"Alumnos auto-asignados correctamente en la sesión '{sesion_activa.nombre}'."
            )
        return redirect("registrargrupos")

    grupos = (
        Grupo.objects
        .filter(sesion=sesion_activa)
        .prefetch_related("alumno_set")
        .order_by('idgrupo')
    )

    context = {
        "grupos": grupos,
        "sesion_activa": sesion_activa,
    }
    return render(request, "registrargrupos.html", context)


def generar_codigo_acceso(longitud=6):
    caracteres = string.ascii_uppercase + string.digits
    while True:
        codigo = ''.join(random.choices(caracteres, k=longitud))
        if not Grupo.objects.filter(codigoacceso=codigo).exists():
            return codigo

def cargar_alumnos(request):
    profesor = Profesor.objects.first()

    if not profesor:
        messages.warning(request, "Primero debes registrar un profesor.")
        return redirect("registrarprofesor")

    sesion_activa = (
        Sesion.objects.filter(profesor=profesor)
        .order_by('-fecha_creacion')
        .first()
    )

    if not sesion_activa:
        messages.warning(request, "Primero crea una sesión antes de cargar alumnos.")
        return redirect("crear_sesion")

    alumnos = (
        Alumno.objects.filter(profesor_idprofesor=profesor, sesion=sesion_activa)
        .order_by('idalumno')
    )

    if request.method == "POST" and request.FILES.get("archivo_excel"):
        archivo = request.FILES["archivo_excel"]

        try:
            nombre_archivo = archivo.name.lower()
            if not (nombre_archivo.endswith('.xlsx') or nombre_archivo.endswith('.csv')):
                messages.error(request, "Formato no soportado. Usa .xlsx o .csv.")
                return render(
                    request,
                    "registraralumnos.html",
                    {"alumnos": alumnos, "sesion_activa": sesion_activa},
                )

            filas = leer_filas_archivo(archivo)

            with transaction.atomic():
                for row in filas:
                    Alumno.objects.create(
                        profesor_idprofesor=profesor,
                        sesion=sesion_activa,
                        emailalumno=row.get('Correo'),
                        rutalumno=row.get('RUT'),
                        nombrealumno=row.get('Nombre'),
                        apellidopaternoalumno=row.get('Apellido Paterno'),
                        apellidomaternoalumno=row.get('Apellido Materno'),
                        carreraalumno=row.get('Carrera', ''),  # opcional
                    )

            messages.success(
                request,
                f"Alumnos cargados correctamente para la sesión '{sesion_activa.nombre}'."
            )

            alumnos = (
                Alumno.objects.filter(profesor_idprofesor=profesor, sesion=sesion_activa)
                .order_by('idalumno')
            )

        except Exception as e:
            messages.error(request, f"Error al leer el archivo: {e}")

    return render(
        request,
        "registraralumnos.html",
        {"alumnos": alumnos, "sesion_activa": sesion_activa},
    )

def cambiar_tematica(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    grupo.tema_elegido = ""
    grupo.desafio_id_externo = ""
    grupo.desafio_nombre = ""
    grupo.desafio_descripcion = ""
    grupo.listo_f2_tematica = False
    grupo.listo_f2_desafio = False

    grupo.save(update_fields=[
        "tema_elegido",
        "desafio_id_externo",
        "desafio_nombre",
        "desafio_descripcion",
        "listo_f2_tematica",
        "listo_f2_desafio",
    ])

    return redirect("tematicas")

def elegir_modo_conocidos(request, modo):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "promptconocidos"):
        return redirect("pantalla_espera")

    request.session["modo_conocidos"] = modo
    request.session.modified = True

    if modo == "rapido":
        return redirect("conocidos_rapido")

    return redirect("conocidos")


def conocidos_rapido(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "conocidos_rapido"):
        return redirect("pantalla_espera")

    return render(request, "conocidos.html", {
        "grupo": grupo,
        "modo_rapido": True,
    })

@require_http_methods(["POST"])
def agregar_alumno_manual(request):
    """
    Agrega un alumno manualmente a la SESIÓN ACTIVA del profesor.
    """
    correo = (request.POST.get("email") or "").strip()
    nombre = (request.POST.get("nombre") or "").strip()
    ap_paterno = (request.POST.get("apellido_paterno") or "").strip()
    ap_materno = (request.POST.get("apellido_materno") or "").strip()
    carrera = (request.POST.get("carrera") or "").strip()

    if not correo or not nombre:
        messages.warning(request, "Correo y Nombre son obligatorios.")
        return redirect("registraralumnos")

    try:
        validate_email(correo)
    except ValidationError:
        messages.error(request, "El correo no es válido.")
        return redirect("registraralumnos")

    profesor = Profesor.objects.first()
    if not profesor:
        messages.warning(request, "Primero debes registrar un profesor.")
        return redirect("registrarprofesor")

    sesion_activa = (
        Sesion.objects.filter(profesor=profesor)
        .order_by('-fecha_creacion')
        .first()
    )
    if not sesion_activa:
        messages.warning(request, "Primero crea una sesión antes de agregar alumnos.")
        return redirect("crear_sesion")

    if Alumno.objects.filter(emailalumno=correo, profesor_idprofesor=profesor, sesion=sesion_activa).exists():
        messages.warning(request, "⚠️ Ya existe un alumno con ese correo en esta sesión.")
        return redirect("registraralumnos")

    try:
        with transaction.atomic():
            Alumno.objects.create(
                profesor_idprofesor=profesor,
                sesion=sesion_activa,
                emailalumno=correo,
                nombrealumno=nombre,
                apellidopaternoalumno=ap_paterno,
                apellidomaternoalumno=ap_materno,
                carreraalumno=carrera or "No especificada",
            )
        messages.success(
            request,
            f"✅ Alumno agregado correctamente a la sesión '{sesion_activa.nombre}'."
        )
    except Exception as e:
        messages.error(request, f"Ocurrió un error al agregar: {e}")

    return redirect("registraralumnos")

@never_cache
def desafios(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "desafios"):
        return redirect("pantalla_espera")

    slug = (grupo.tema_elegido or "").strip().lower()
    if not slug:
        return redirect("tematicas")

    tematica = Tematica.objects.filter(slug=slug, activa=True).first()
    if not tematica:
        return redirect("tematicas")

    desafios_bd = Desafio.objects.filter(
        tematica=tematica,
        activo=True
    ).order_by("orden", "nombredesafio")

    return render(request, "desafios.html", {
        "grupo": grupo,
        "tematica": tematica,
        "desafios": desafios_bd,
        "slug": slug,
        "desafio_confirmado": bool(grupo.listo_f2_desafio),
        "desafio_id_actual": str(grupo.desafio_id_externo or ""),
        "desafio_nombre_actual": grupo.desafio_nombre or "",
        "desafio_descripcion_actual": grupo.desafio_descripcion or "",
    })

@never_cache
def bubblemap(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "bubblemap"):
        return redirect("pantalla_espera")

    grupo.refresh_from_db()
    sesion = grupo.sesion

    segundos = 180
    if sesion and sesion.segundos_restantes is not None:
        segundos = sesion.segundos_restantes

    return render(request, "bubblemap.html", {
        "grupo": grupo,
        "sesion": sesion,
        "desafio_nombre_actual": grupo.desafio_nombre or "Desafío no seleccionado",
        "desafio_descripcion_actual": grupo.desafio_descripcion or "Aún no hay descripción disponible para este desafío.",
        "desafio_foto_actual": (
            grupo.desafio_elegido.imagen_desafio.url
            if grupo.desafio_elegido and grupo.desafio_elegido.imagen_desafio
            else ""
        ),
        "segundos_restantes": segundos,
    })


@require_POST
def otorgar_tokens_bubblemap(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    if grupo.sesion.fase_actual != "f2_bubblemap":
        return JsonResponse({"ok": False, "error": "La sesión no está en Bubble Map."}, status=400)

    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        payload = {}

    burbujas = payload.get("burbujas", [])
    relato = (payload.get("relato") or "").strip()
    link = (payload.get("link") or "").strip()

    def texto_valido(texto):
        return len((texto or "").strip()) >= 5

    def cantidad_palabras(texto):
        return len((texto or "").strip().split())

    respuestas_validas = []
    principales_validas = []
    respuestas_largas = []

    for item in burbujas:
        if isinstance(item, dict):
            texto = (item.get("texto") or "").strip()
            tipo = item.get("tipo") or ""
        else:
            texto = str(item).strip()
            tipo = "base"

        if texto_valido(texto):
            respuestas_validas.append(texto)

            if tipo == "base":
                principales_validas.append(texto)

            if cantidad_palabras(texto) >= 10:
                respuestas_largas.append(texto)

    relato_valido = cantidad_palabras(relato) >= 18
    link_valido = ("http://" in link.lower()) or ("https://" in link.lower()) or ("www." in link.lower())

    tokens = 0

    tokens += len(respuestas_validas)

    if len(respuestas_validas) >= 4:
        tokens += 2

    if len(principales_validas) >= 5:
        tokens += 3

    tokens += len(respuestas_largas)

    if relato_valido:
        tokens += 2

    if link_valido:
        tokens += 2

    nivel = "Inicial"
    if len(respuestas_validas) >= 3:
        nivel = "Intermedio"
    if len(principales_validas) >= 5:
        nivel = "Completo"
    if len(principales_validas) >= 5 and (relato_valido or link_valido):
        nivel = "Experto"

    with transaction.atomic():
        grupo = Grupo.objects.select_for_update().get(pk=grupo.pk)
        sesion = Sesion.objects.select_for_update().get(pk=grupo.sesion_id)

        if getattr(grupo, "bubble_tokens_otorgados", False):
            return JsonResponse({
                "ok": True,
                "ya_otorgados": True,
                "tokens_otorgados": 0,
                "tokens_totales": grupo.tokensgrupo or 0,
                "nivel": nivel,
                "rutaAlumno": reverse("ranking") if sesion.fase_actual == "f2_ranking" else reverse("bubblemap"),
            })
        BubbleMapRespuesta.objects.filter(
            sesion=sesion,
            grupo=grupo
        ).delete()

        for item in burbujas:
            if isinstance(item, dict):
                BubbleMapRespuesta.objects.create(
                    sesion=sesion,
                    grupo=grupo,
                    desafio=grupo.desafio_elegido,
                    tipo=item.get("tipo") or "",
                    titulo=item.get("titulo") or "",
                    texto=(item.get("texto") or "").strip(),
                    relato=relato,
                    link=link
                )

        grupo.tokensgrupo = (grupo.tokensgrupo or 0) + tokens
        grupo.bubble_tokens_otorgados = True
        grupo.save(update_fields=["tokensgrupo", "bubble_tokens_otorgados"])

        total = Grupo.objects.filter(sesion=sesion).count()
        terminados = Grupo.objects.filter(
            sesion=sesion,
            bubble_tokens_otorgados=True
        ).count()

        todos_terminaron = total > 0 and terminados == total

        if todos_terminaron:
            sesion.fase_actual = "f2_ranking"
            sesion.segundos_restantes = 0
            sesion.timer_corriendo = False
            sesion.timer_inicio_at = None
            sesion.timer_fin_at = None
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=[
                "fase_actual",
                "segundos_restantes",
                "timer_corriendo",
                "timer_inicio_at",
                "timer_fin_at",
                "inicio_fase_habilitado",
            ])

            Grupo.objects.filter(sesion=sesion).update(
                listo_f6=False,
                listo_ranking=False,
            )

    return JsonResponse({
        "ok": True,
        "ya_otorgados": False,
        "tokens_otorgados": tokens,
        "tokens_totales": grupo.tokensgrupo,
        "nivel": nivel,
        "respuestas_validas": len(respuestas_validas),
        "principales_validas": len(principales_validas),
        "respuestas_largas": len(respuestas_largas),
        "relato_valido": relato_valido,
        "link_valido": link_valido,
        "todos_terminaron": todos_terminaron,
        "rutaAlumno": reverse("ranking") if todos_terminaron else reverse("bubblemap"),
    })

def orden_presentacion_alumno(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "orden_presentacion_alumno"):
        return redirect("pantalla_espera")

    grupos_ordenados = Grupo.objects.filter(
        sesion=grupo.sesion
    ).exclude(
        orden_presentacion__isnull=True
    ).order_by("orden_presentacion")

    return render(request, "orden_presentacion.html", {
        "grupo": grupo,
        "grupos_ordenados": grupos_ordenados,
    })

@never_cache
def pitch(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "pitch"):
        return redirect("pantalla_espera")

    grupo.refresh_from_db()

    return render(request, "pitch.html", {
        "grupo": grupo,
        "pitch_guardado": grupo.pitch_texto or "",
        "desafio_nombre_actual": grupo.desafio_nombre or "Desafío no seleccionado",
        "desafio_descripcion_actual": grupo.desafio_descripcion or "Aún no hay descripción disponible para este desafío.",
    })


@require_POST
def guardar_pitch(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        payload = {}

    pitch_texto = (payload.get("pitch") or "").strip()

    grupo.pitch_texto = pitch_texto
    grupo.save(update_fields=["pitch_texto"])

    return JsonResponse({
        "ok": True,
        "pitch": grupo.pitch_texto,
    })


@require_POST
def profesor_sortear_orden_pitch(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    grupos = list(Grupo.objects.filter(sesion=sesion).order_by("idgrupo"))
    if not grupos:
        return JsonResponse({"ok": False, "error": "No hay grupos en la sesión."}, status=400)

    random.shuffle(grupos)

    for i, grupo in enumerate(grupos, start=1):
        grupo.orden_presentacion = i
        grupo.save(update_fields=["orden_presentacion"])

    primer_grupo = sorted(grupos, key=lambda g: g.orden_presentacion)[0]

    sesion.grupo_presentando = primer_grupo
    sesion.segundos_restantes = int(sesion.t_pitch or 90)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None
    sesion.inicio_fase_habilitado = True
    sesion.save(update_fields=[
        "grupo_presentando",
        "segundos_restantes",
        "timer_corriendo",
        "timer_inicio_at",
        "timer_fin_at",
        "inicio_fase_habilitado",
    ])

    return JsonResponse({
        "ok": True,
        "orden": [
            {
                "id": g.idgrupo,
                "nombre": g.nombregrupo,
                "orden": g.orden_presentacion,
            }
            for g in sorted(grupos, key=lambda x: x.orden_presentacion)
        ],
        **serializar_estado_pitch(sesion),
    })

@never_cache
def presentar_pitch(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "presentar_pitch"):
        return redirect("pantalla_espera")

    return render(request, "presentar_pitch.html", {
        "grupo": grupo,
        "miPitch": grupo.pitch_texto or "",
    })


def registraralumnos(request):
    return cargar_alumnos(request)

def market_view(request):
    grupo_id = request.session.get("grupo_id")
    if not grupo_id:
        messages.error(request, "No se encontró el grupo asociado a esta sesión.")
        return redirect("registro")

    grupo_actual = get_object_or_404(Grupo, pk=grupo_id)

    user_tokens = grupo_actual.tokensgrupo or 0

    challenges = Reto.objects.all()

    other_teams = Grupo.objects.filter(
        sesion=grupo_actual.sesion
    ).exclude(pk=grupo_actual.pk)

    context = {
        "user_tokens": user_tokens,
        "challenges": challenges,
        "other_teams": other_teams,
    }
    return render(request, "market.html", context)

@require_http_methods(["POST"])
def issue_challenge_view(request, challenge_id):
    grupo_id = request.session.get("grupo_id")
    if not grupo_id:
        messages.error(request, "No se encontró el grupo asociado a esta sesión.")
        return redirect("market")

    grupo_emisor = get_object_or_404(Grupo, pk=grupo_id)

    reto = get_object_or_404(Reto, pk=challenge_id)

    target_team_id = request.POST.get("target_team_id")
    if not target_team_id:
        messages.error(request, "Selecciona un equipo objetivo.")
        return redirect("market")

    grupo_receptor = get_object_or_404(Grupo, pk=target_team_id)

    cost = int(reto.costoreto or 0)

    if cost < 0:
        messages.error(request, "El costo del reto no puede ser negativo.")
        return redirect("market")

    saldo_actual = grupo_emisor.tokensgrupo or 0
    if saldo_actual < cost:
        messages.error(request, "No tienes tokens suficientes para enviar este reto.")
        return redirect("market")

    if cost > 0:
        grupo_emisor.ajustar_tokens(-cost)

    desafio = reto.desafio_iddesafio
    recompensa = (desafio.tokensdesafio or 0) if desafio else 0

    if recompensa <= 0:
        recompensa = cost

    penalizacion = recompensa

    Retogrupo.objects.create(
        reto=reto,
        grupo_emisor=grupo_emisor,
        grupo_receptor=grupo_receptor,
        tokens_costo=cost,
        tokens_recompensa=recompensa,
        tokens_penalizacion=penalizacion,
        fecha_creacion=timezone.now()
    )

    nuevo_saldo = (grupo_emisor.tokensgrupo or 0)

    messages.success(
        request,
        f"Has retado al equipo {grupo_receptor.nombregrupo} con “{reto.nombrereto}” "
        f"por {cost} tokens. Te quedan ahora {nuevo_saldo} tokens."
    )
    return redirect("market")

@never_cache
def peer_review_view(request):
    grupo_evaluador = obtener_grupo_desde_session(request)
    if not grupo_evaluador:
        return redirect("registro")

    if not acceso_permitido(grupo_evaluador, "peer_review"):
        return redirect("pantalla_espera")

    sesion = grupo_evaluador.sesion
    grupo_objetivo = sesion.grupo_presentando

    if not grupo_objetivo:
        return redirect("pantalla_espera")

    criteria = [
        {"key": "claridad", "label": "Claridad"},
        {"key": "creatividad", "label": "Creatividad"},
        {"key": "viabilidad", "label": "Viabilidad"},
        {"key": "equipo", "label": "Trabajo en equipo"},
        {"key": "presentacion", "label": "Presentación"},
    ]

    if grupo_evaluador.pk == grupo_objetivo.pk:
        if evaluacion_actual_completa(sesion):
            avanzar_al_siguiente_pitch_o_ranking(sesion)
            return redirect("pantalla_espera")

        return render(request, "peer_review.html", {
            "session": sesion,
            "evaluator_team": grupo_evaluador,
            "grupo_objetivo": grupo_objetivo,
            "mi_equipo_presenta": True,
            "ya_evaluo": False,
            "criteria": criteria,
        })

    ya_evaluo = Evaluacion.objects.filter(
        sesion=sesion,
        grupo_evaluador=grupo_evaluador,
        grupo_evaluado=grupo_objetivo,
    ).exists()

    if request.method == "POST":
        if ya_evaluo:
            if evaluacion_actual_completa(sesion):
                avanzar_al_siguiente_pitch_o_ranking(sesion)
            return redirect("pantalla_espera")

        claridad = int(request.POST.get("score_claridad", 0))
        creatividad = int(request.POST.get("score_creatividad", 0))
        viabilidad = int(request.POST.get("score_viabilidad", 0))
        equipo = int(request.POST.get("score_equipo", 0))
        presentacion = int(request.POST.get("score_presentacion", 0))
        comentario = (request.POST.get("comment") or "").strip()
        reflexion = (request.POST.get("reflection") or "").strip()

        Evaluacion.objects.create(
            sesion=sesion,
            grupo_evaluador=grupo_evaluador,
            grupo_evaluado=grupo_objetivo,
            claridad=claridad,
            creatividad=creatividad,
            viabilidad=viabilidad,
            equipo=equipo,
            presentacion=presentacion,
            comentario=comentario,
            reflexion=reflexion or None,
        )

        otorgar_tokens_peer_review(grupo_evaluador)

        grupo_evaluador.listo_f5 = True
        grupo_evaluador.save(update_fields=["listo_f5"])

        if evaluacion_actual_completa(sesion):
            avanzar_al_siguiente_pitch_o_ranking(sesion)

        return redirect("pantalla_espera")

    return render(request, "peer_review.html", {
        "session": sesion,
        "evaluator_team": grupo_evaluador,
        "grupo_objetivo": grupo_objetivo,
        "mi_equipo_presenta": False,
        "ya_evaluo": ya_evaluo,
        "criteria": criteria,
    })



def registrarprofesor(request):
    if request.method == "POST":
        email = request.POST.get("email")
        facultad = request.POST.get("facultad")

        if email and facultad:
            usuario = Usuario.objects.create(password="temp")

            Profesor.objects.create(
                usuario_idusuario=usuario,
                emailprofesor=email,
                facultad=facultad
            )

            messages.success(request, "Profesor registrado correctamente.")
            return redirect("registrarprofesor")

    profesores = Profesor.objects.all().order_by("emailprofesor")

    return render(request, "registrarprofesor.html", {
        "profesores": profesores
    })


def listar_profesores(request):
    profesores = Profesor.objects.all().order_by('-idprofesor')
    return render(request, 'listar_profesores.html', {'profesores': profesores})



@require_http_methods(["POST"])
def eliminar_alumno(request, idalumno):
    alumno = get_object_or_404(Alumno, idalumno=idalumno)
    try:
        with transaction.atomic():
            alumno.delete()
        messages.success(request, f"Alumno '{alumno.nombrealumno}' eliminado correctamente.")
    except Exception as e:
        messages.error(request, f"Ocurrió un error al eliminar: {e}")
    return redirect("registraralumnos")

def finalizar_mision(request):
    request.session.pop("grupo_id", None)
    return redirect("perfiles")

def reflexion(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if grupo and grupo.sesion:
        borrar_fotos_lego_sesion(grupo.sesion)    

    if not acceso_permitido(grupo, "reflexion"):
        return redirect("pantalla_espera")

    return render(request, "reflexion.html", {"grupo": grupo})
def leer_filas_archivo(archivo):
    """Lee un .xlsx (openpyxl) o .csv (csv nativo) y devuelve una lista de
    diccionarios {encabezado: valor}, usando '' para celdas vacias.
    Reemplaza a pandas para no depender de pandas/numpy en produccion."""
    nombre = archivo.name.lower()

    if nombre.endswith(".xlsx"):
        wb = openpyxl.load_workbook(archivo, read_only=True, data_only=True)
        ws = wb.active
        iterador = ws.iter_rows(values_only=True)
        try:
            encabezados = [
                str(c).strip() if c is not None else "" for c in next(iterador)
            ]
        except StopIteration:
            return []
        filas = []
        for fila in iterador:
            if fila is None or all(v is None for v in fila):
                continue
            filas.append(
                {
                    clave: ("" if valor is None else valor)
                    for clave, valor in zip(encabezados, fila)
                }
            )
        return filas

    if nombre.endswith(".csv"):
        archivo.seek(0)
        texto = io.TextIOWrapper(archivo, encoding="utf-8-sig", newline="")
        return [
            {clave: (valor if valor is not None else "") for clave, valor in fila.items()}
            for fila in csv.DictReader(texto)
        ]

    raise ValueError("Formato no soportado. Usa .xlsx o .csv.")


def leer_alumnos_desde_archivo(archivo):
    return leer_filas_archivo(archivo)


def crear_alumnos_en_sesion(df, profesor, sesion):
    alumnos_creados = []

    for row in df:
        alumno = Alumno.objects.create(
            profesor_idprofesor=profesor,
            sesion=sesion,
            emailalumno=row.get("Correo", ""),
            rutalumno=row.get("RUT", ""),
            nombrealumno=row.get("Nombre", ""),
            apellidopaternoalumno=row.get("Apellido Paterno", ""),
            apellidomaternoalumno=row.get("Apellido Materno", ""),
            carreraalumno=row.get("Carrera", ""),
        )
        alumnos_creados.append(alumno)

    return alumnos_creados

def generar_codigo_grupo_profesor():
    while True:
        codigo = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Grupo.objects.filter(codigoacceso=codigo).exists():
            return codigo

def crear_grupos_para_alumnos(sesion, alumnos, max_por_grupo=8, cantidad_grupos_manual=None):
    if not alumnos:
        return 0

    if cantidad_grupos_manual:
        cantidad_grupos = max(1, int(cantidad_grupos_manual))
    else:
        cantidad_grupos = ceil(len(alumnos) / max_por_grupo)

    grupos = []

    for i in range(cantidad_grupos):
        grupo = Grupo.objects.create(
            sesion=sesion,
            nombregrupo=f"Grupo {i + 1}",
            tokensgrupo=10,
            etapa=1,
            codigoacceso=generar_codigo_grupo_profesor(),
        )
        grupos.append(grupo)

    for index, alumno in enumerate(alumnos):
        grupo = grupos[index % len(grupos)]
        alumno.grupo = grupo
        alumno.save(update_fields=["grupo"])

    return len(grupos)

def crear_sesion(request):
    profesor = Profesor.objects.first()

    if not profesor:
        messages.warning(request, "Primero debes registrar un profesor.")
        return redirect("registrarprofesor")

    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()
        email_profesor = (request.POST.get("email_profesor") or "").strip()
        facultad = (request.POST.get("facultad") or "").strip()

        modo_creacion = request.POST.get("modo_creacion", "recomendado")
        archivo = request.FILES.get("archivo_excel")

        cantidad_sesiones = int(request.POST.get("cantidad_sesiones") or 1)
        grupos_por_sesion = int(request.POST.get("grupos_por_sesion") or 1)

        if not nombre:
            messages.error(request, "Debes darle un nombre a la sesión.")
            return render(request, "crear_sesion.html")

        if not email_profesor:
            messages.error(request, "Debes ingresar el correo del profesor.")
            return render(request, "crear_sesion.html")

        if not facultad:
            messages.error(request, "Debes seleccionar una facultad.")
            return render(request, "crear_sesion.html")

        if not archivo:
            messages.error(request, "Debes subir el archivo de estudiantes.")
            return render(request, "crear_sesion.html")

        try:
            df = leer_alumnos_desde_archivo(archivo)

            if not df:
                messages.error(request, "El archivo no tiene estudiantes.")
                return render(request, "crear_sesion.html")

            sesiones_creadas = []

            with transaction.atomic():

                profesor.emailprofesor = email_profesor
                profesor.facultad = facultad
                profesor.save()

                if modo_creacion == "dividir_dos":
                    cantidad_sesiones = 2
                    grupos_por_sesion = None

                elif modo_creacion == "personalizado":
                    cantidad_sesiones = max(1, cantidad_sesiones)
                    grupos_por_sesion = max(1, grupos_por_sesion)

                else:
                    cantidad_sesiones = 1
                    grupos_por_sesion = None

                total_alumnos = len(df)
                inicio = 0

                for numero_sesion in range(1, cantidad_sesiones + 1):
                    alumnos_en_esta_sesion = total_alumnos // cantidad_sesiones

                    if numero_sesion <= total_alumnos % cantidad_sesiones:
                        alumnos_en_esta_sesion += 1

                    fin = inicio + alumnos_en_esta_sesion
                    df_sesion = df[inicio:fin]
                    inicio = fin

                    if cantidad_sesiones == 1:
                        nombre_sesion = nombre
                    else:
                        nombre_sesion = f"{nombre} - Sala {numero_sesion}"

                    sesion = Sesion.objects.create(
                        profesor=profesor,
                        nombre=nombre_sesion,
                        fase_actual="f1_bienvenida",
                        timer_corriendo=False,
                        segundos_restantes=0,
                    )

                    alumnos = crear_alumnos_en_sesion(df_sesion, profesor, sesion)

                    crear_grupos_para_alumnos(
                        sesion,
                        alumnos,
                        cantidad_grupos_manual=grupos_por_sesion
                    )

                    sesiones_creadas.append({
                        "sesion": sesion,
                        "grupos": Grupo.objects.filter(sesion=sesion)
                        .prefetch_related("alumno_set")
                        .order_by("idgrupo"),
                    })

                messages.success(request, "Sesión creada correctamente.")

            return render(request, "crear_sesion.html", {
                "sesiones_creadas": sesiones_creadas,
            })

        except Exception as e:
            messages.error(request, f"No se pudo procesar la sesión: {e}")
            return render(request, "crear_sesion.html")

    return render(request, "crear_sesion.html")

def listar_sesiones(request):
    profesor = Profesor.objects.first()

    if not profesor:
        messages.warning(request, "Aún no hay profesores registrados.")
        return redirect("registrarprofesor")

    sesiones = Sesion.objects.filter(profesor=profesor).order_by("-fecha_creacion")

    sesiones_info = []

    for sesion in sesiones:
        sesiones_info.append({
            "sesion": sesion,
            "total_grupos": Grupo.objects.filter(sesion=sesion).count(),
            "total_alumnos": Alumno.objects.filter(sesion=sesion).count(),
        })

    return render(request, "listar_sesiones.html", {
        "sesiones_info": sesiones_info
    })

def otorgar_tokens_peer_review(grupo_evaluador: Grupo):

    if getattr(grupo_evaluador, "recompensa_peer_otorgada", False):
        return

    sesion = grupo_evaluador.sesion
    if not sesion:
        return

    qs = (
        Evaluacion.objects
        .filter(sesion=sesion, grupo_evaluador=grupo_evaluador)
        .annotate(
            total=(
                F("claridad")
                + F("creatividad")
                + F("viabilidad")
                + F("equipo")
                + F("presentacion")
            )
        )
        .order_by("-total", "grupo_evaluado_id")
    )

    if not qs.exists():
        return

    mejor_eval = qs.first()
    grupo_premiado = mejor_eval.grupo_evaluado

    grupo_premiado.tokensgrupo = (grupo_premiado.tokensgrupo or 0) + 2
    grupo_premiado.save()

    grupo_evaluador.recompensa_peer_otorgada = True
    grupo_evaluador.save()


def ranking_view(request):
    grupo_id = request.session.get("grupo_id")
    if not grupo_id:
        messages.error(request, "No pudimos identificar tu grupo.")
        return redirect("registro")

    grupo_actual = get_object_or_404(Grupo, pk=grupo_id)
    sesion = grupo_actual.sesion

    if not sesion:
        messages.error(request, "Tu grupo no está asociado a ninguna sesión.")
        return redirect("registro")

    grupos = (
        Grupo.objects
        .filter(sesion=sesion)
        .order_by("-tokensgrupo", "idgrupo")
    )

    rankings = []
    last_tokens = None
    current_rank = 0
    position = 0

    for g in grupos:
        position += 1
        tokens = g.tokensgrupo or 0

        if tokens != last_tokens:
            current_rank = position
            last_tokens = tokens

        rankings.append({
            "team_name": g.nombregrupo or f"Grupo {g.idgrupo}",
            "tokens": tokens,
            "is_me": g.idgrupo == grupo_actual.idgrupo,
            "rank": current_rank,
        })

    context = {
        "session": sesion,
        "grupo": grupo_actual,
        "rankings": rankings,
    }
    return render(request, "ranking.html", context)

@never_cache
def mision_cumplida_view(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        messages.error(request, "No pudimos identificar tu grupo.")
        return redirect("registro")

    if not acceso_permitido(grupo, "mision_cumplida"):
        return redirect("pantalla_espera")

    if not peer_review_completado(grupo):
        return redirect("peer_review")

    return render(request, "mision_cumplida.html", {
        "grupo": grupo,
    })

def preview_pantalla_profesor(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    plantilla_por_fase = {
        "lobby": "pantalla_espera_preview.html",

        "f1_bienvenida": "pantalla_inicio.html",
        "f1_conocidos": "conocidos.html",
        "f1_pre_sopa": "trabajoenequipo.html",
        "f1_sopa": "minijuego1.html",

        "f2_transicion": "transiciondesafio.html",
        "f2_tematicas": "tematicas.html",
        "f2_transicion_empatia": "transicionempatia.html",
        "f2_bubblemap": "bubblemap.html",

        "f3_transicion_creatividad": "transicioncreatividad.html",
        "f3_lego": "lego.html",

        "f4_transicion_comunicacion": "transicioncomunicacion.html",
        "f4_construccion_pitch": "pitch.html",
        "f4_orden_pitch": "orden_presentacion.html",
        "f4_presentacion_pitch": "presentar_pitch.html",

        "f5_transicion_apoyo": "transicionapoyo.html",
        "f5_evaluacion_pitch": "peer_review.html",

        "f6_ranking": "ranking.html",
        "reflexion": "reflexion.html",
    }

    template_name = plantilla_por_fase.get(sesion.fase_actual, "pantalla_espera_preview.html")

    grupo_dummy = Grupo.objects.filter(sesion=sesion).order_by("idgrupo").first()

    if not grupo_dummy:
        grupo_dummy = Grupo(
            sesion=sesion,
            nombregrupo="Grupo preview",
            tokensgrupo=10,
        )

    context = {
        "grupo": grupo_dummy,
        "preview_profesor": True,
    }

    return render(request, template_name, context)

def admin_desafios(request):
    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "editar_desafio":
            desafio_id = request.POST.get("desafio_id")
            desafio = get_object_or_404(Desafio, iddesafio=desafio_id)

            desafio.nombredesafio = request.POST.get("nombre", "").strip()
            desafio.summary = request.POST.get("summary", "").strip()
            desafio.descripciondesafio = request.POST.get("descripcion", "").strip()
            desafio.activo = bool(request.POST.get("activo"))

            tematica_id = request.POST.get("tematica_id")
            if tematica_id:
                desafio.tematica = Tematica.objects.filter(idtematica=tematica_id).first()

            if request.FILES.get("imagen_desafio"):
                desafio.imagen_desafio = request.FILES.get("imagen_desafio")

            desafio.save()
            messages.success(request, "Desafío actualizado correctamente.")
            return redirect("admin_desafios")

        if accion == "crear_desafio":
            nombre = request.POST.get("nombre", "").strip()
            summary = request.POST.get("summary", "").strip()
            descripcion = request.POST.get("descripcion", "").strip()
            tematica_id = request.POST.get("tematica_id")

            tematica = Tematica.objects.filter(idtematica=tematica_id).first()

            if nombre and tematica:
                desafio = Desafio.objects.create(
                    tematica=tematica,
                    nombredesafio=nombre,
                    summary=summary,
                    descripciondesafio=descripcion,
                    activo=True,
                    orden=tematica.desafios.count() + 1
                )

                if request.FILES.get("imagen_desafio"):
                    desafio.imagen_desafio = request.FILES.get("imagen_desafio")
                    desafio.save()

                messages.success(request, "Desafío creado correctamente.")
            else:
                messages.error(request, "Debes completar nombre y temática.")

            return redirect("admin_desafios")

        if accion == "eliminar_desafio":
            desafio_id = request.POST.get("desafio_id")
            desafio = get_object_or_404(Desafio, iddesafio=desafio_id)

            if Grupo.objects.filter(desafio_elegido=desafio).exists():
                messages.warning(request, "No se puede eliminar porque ya fue elegido por grupos. Puedes desactivarlo.")
            else:
                desafio.delete()
                messages.success(request, "Desafío eliminado correctamente.")

            return redirect("admin_desafios")

    desafios = []

    for desafio in Desafio.objects.select_related("tematica").all().order_by("tematica__orden", "orden"):
        grupos_desafio = Grupo.objects.filter(desafio_elegido=desafio)

        if not grupos_desafio.exists():
            grupos_desafio = Grupo.objects.filter(desafio_id_externo=str(desafio.iddesafio))

        desafios.append({
            "id": desafio.iddesafio,
            "nombre": desafio.nombredesafio,
            "summary": desafio.summary,
            "descripcion": desafio.descripciondesafio,
            "activo": desafio.activo,
            "tematica_id": desafio.tematica.idtematica if desafio.tematica else "",
            "tematica": desafio.tematica.title if desafio.tematica else "Sin temática",
            "total_usos": grupos_desafio.count(),
            "grupos": grupos_desafio.order_by("-idgrupo")[:10],
            "imagen": desafio.imagen_desafio.url if desafio.imagen_desafio else "",
        })

    return render(request, "admin_desafios.html", {
        "desafios": desafios,
        "tematicas": Tematica.objects.filter(activa=True).order_by("orden", "title"),
    })


@require_POST
def eliminar_profesor(request, profesor_id):
    profesor = get_object_or_404(Profesor, idprofesor=profesor_id)

    alumnos_asociados = Alumno.objects.filter(profesor_idprofesor=profesor).count()
    sesiones_asociadas = Sesion.objects.filter(profesor=profesor).count()

    if alumnos_asociados > 0 or sesiones_asociadas > 0:
        messages.warning(
            request,
            f"No se puede eliminar directamente. Tiene {alumnos_asociados} alumnos y {sesiones_asociadas} sesiones asociadas. "
            f"Usa eliminación forzada si quieres borrar todo lo relacionado."
        )
        return redirect("registrarprofesor")

    try:
        with transaction.atomic():
            usuario = profesor.usuario_idusuario
            profesor.delete()
            if not Profesor.objects.filter(usuario_idusuario=usuario).exists():
                usuario.delete()
        messages.success(request, "Profesor eliminado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar: {e}")

    return redirect("registrarprofesor")


@require_POST
def eliminar_profesor_forzado(request, profesor_id):
    profesor = get_object_or_404(Profesor, idprofesor=profesor_id)

    Alumno.objects.filter(profesor_idprofesor=profesor).delete()
    Sesion.objects.filter(profesor=profesor).delete()

    profesor.delete()

    messages.success(request, "Profesor y datos asociados eliminados correctamente.")
    return redirect("registrarprofesor")

def guardar_imagen_tematica(request_file):

    if not request_file:
        return ""

    nombre_webp, contenido_webp = convertir_imagen_a_webp(
        request_file,
        max_size=(1400, 900),
        quality=80,
    )

    ruta = default_storage.save(f"tematicas/{nombre_webp}", contenido_webp)

    return settings.MEDIA_URL + ruta


def admin_tematicas(request):
    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "crear_tematica":
            title = request.POST.get("title", "").strip()
            hero = request.POST.get("hero", "").strip()
            chips_raw = request.POST.get("chips", "").strip()
            accent = request.POST.get("accent", "#3b82f6").strip()

            if title and hero:
                slug_base = slugify(title)
                slug = slug_base
                contador = 1

                while Tematica.objects.filter(slug=slug).exists():
                    contador += 1
                    slug = f"{slug_base}-{contador}"

                image = guardar_imagen_tematica(request.FILES.get("image_file"))

                tematica = Tematica.objects.create(
                    slug=slug,
                    title=title,
                    hero=hero,
                    chips=[c.strip() for c in chips_raw.split(",") if c.strip()],
                    accent=accent,
                    image=image,
                    activa=True,
                    orden=Tematica.objects.count() + 1
                )

                if request.POST.get("crear_desafio_ahora"):
                    nombre = request.POST.get("desafio_nombre", "").strip()
                    summary = request.POST.get("desafio_summary", "").strip()
                    desc = request.POST.get("desafio_desc", "").strip()

                    if nombre:
                        Desafio.objects.create(
                            tematica=tematica,
                            nombredesafio=nombre,
                            summary=summary,
                            descripciondesafio=desc,
                            activo=True,
                            orden=tematica.desafios.count() + 1
                        )

                messages.success(request, "Temática creada correctamente.")
            else:
                messages.error(request, "Debes completar nombre y descripción de la temática.")

            return redirect("admin_tematicas")

        if accion == "editar_tematica":
            tematica_id = request.POST.get("tematica_id")
            tematica = get_object_or_404(Tematica, idtematica=tematica_id)

            tematica.title = request.POST.get("title", "").strip()
            tematica.hero = request.POST.get("hero", "").strip()
            tematica.chips = [c.strip() for c in request.POST.get("chips", "").split(",") if c.strip()]
            tematica.accent = request.POST.get("accent", "#3b82f6").strip()
            tematica.activa = bool(request.POST.get("activa"))

            nueva_imagen = guardar_imagen_tematica(request.FILES.get("image_file"))
            if nueva_imagen:
                tematica.image = nueva_imagen

            tematica.save()
            messages.success(request, "Temática actualizada correctamente.")
            return redirect("admin_tematicas")

        if accion == "eliminar_tematica":
            tematica_id = request.POST.get("tematica_id")
            tematica = get_object_or_404(Tematica, idtematica=tematica_id)

            if tematica.desafios.exists():
                messages.warning(request, "No se puede eliminar porque tiene desafíos asociados. Elimina o reasigna esos desafíos primero.")
            else:
                tematica.delete()
                messages.success(request, "Temática eliminada correctamente.")

            return redirect("admin_tematicas")

    tematicas = []

    for tematica in Tematica.objects.all().order_by("orden", "title"):
        grupos_tematica = Grupo.objects.filter(tema_elegido=tematica.slug)

        desafios = []
        for desafio in tematica.desafios.all().order_by("orden", "nombredesafio"):
            usos = Grupo.objects.filter(desafio_elegido=desafio).count()

            if usos == 0:
                usos = Grupo.objects.filter(desafio_id_externo=str(desafio.iddesafio)).count()

            desafios.append({
                "id": desafio.iddesafio,
                "nombre": desafio.nombredesafio,
                "total_usos": usos,
            })

        desafios = sorted(desafios, key=lambda x: x["total_usos"], reverse=True)

        tematicas.append({
            "id": tematica.idtematica,
            "slug": tematica.slug,
            "title": tematica.title,
            "hero": tematica.hero,
            "chips_texto": ", ".join(tematica.chips or []),
            "accent": tematica.accent,
            "image": tematica.image,
            "activa": tematica.activa,
            "total_usos": grupos_tematica.count(),
            "total_desafios": tematica.desafios.count(),
            "desafios": desafios,
        })

    return render(request, "admin_tematicas.html", {
        "tematicas": tematicas,
    })

def admin_desafio_info(request, desafio_id):
    desafio = get_object_or_404(Desafio, iddesafio=desafio_id)

    grupos = Grupo.objects.filter(
        desafio_elegido=desafio
    ).select_related("sesion").order_by("-idgrupo")

    if not grupos.exists():
        grupos = Grupo.objects.filter(
            desafio_id_externo=str(desafio.iddesafio)
        ).select_related("sesion").order_by("-idgrupo")

    return render(request, "admin_desafio_info.html", {
        "desafio": desafio,
        "grupos": grupos,
    })

def limpiar_fotos_lego_por_desafio(desafio):
    if not desafio:
        return

    grupos_con_foto = (
        Grupo.objects
        .filter(desafio_elegido=desafio)
        .exclude(foto_lego="")
        .exclude(foto_lego__isnull=True)
        .order_by("-idgrupo")
    )

    fotos_a_borrar = grupos_con_foto[7:]

    for grupo in fotos_a_borrar:
        if grupo.foto_lego:
            ruta = grupo.foto_lego.path

            if os.path.exists(ruta):
                os.remove(ruta)

            grupo.foto_lego = None
            grupo.save(update_fields=["foto_lego"])

def borrar_foto_lego_grupo(grupo):

    if grupo.foto_lego:
        try:
            grupo.foto_lego.delete(save=False)
        except Exception:
            pass

        grupo.foto_lego = None
        grupo.save(update_fields=["foto_lego"])


def borrar_fotos_lego_sesion(sesion):

    grupos = Grupo.objects.filter(
        sesion=sesion,
        foto_lego__isnull=False,
    ).exclude(foto_lego="")

    for grupo in grupos:
        borrar_foto_lego_grupo(grupo)

def admin_ruleta(request):
    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "guardar_todo":
            ids = request.POST.getlist("opcion_id")

            opciones_temporales = []

            for opcion_id in ids:
                opciones_temporales.append({
                    "id": int(opcion_id),
                    "titulo": request.POST.get(f"titulo_{opcion_id}", "").strip(),
                    "emoji": request.POST.get(f"emoji_{opcion_id}", "").strip(),
                    "descripcion": request.POST.get(f"descripcion_{opcion_id}", "").strip(),
                    "tokens": int(request.POST.get(f"tokens_{opcion_id}") or 0),
                    "porcentaje": int(request.POST.get(f"porcentaje_{opcion_id}") or 0),
                    "activa": request.POST.get(f"activa_{opcion_id}") == "on",
                })

            activas = [o for o in opciones_temporales if o["activa"]]
            total_porcentaje = sum(o["porcentaje"] for o in activas)

            if len(activas) > 8:
                messages.error(request, "No se puede guardar. La ruleta permite máximo 8 opciones activas.")
                return redirect("admin_ruleta")

            if total_porcentaje != 100:
                messages.error(request, f"No se puede guardar. Las opciones activas suman {total_porcentaje}%. Deben sumar exactamente 100%.")
                return redirect("admin_ruleta")

            with transaction.atomic():
                for data in opciones_temporales:
                    opcion = RuletaLegoOpcion.objects.get(idopcion=data["id"])
                    opcion.titulo = data["titulo"]
                    opcion.emoji = data["emoji"]
                    opcion.descripcion = data["descripcion"]
                    opcion.tokens = data["tokens"]
                    opcion.porcentaje = data["porcentaje"]
                    opcion.activa = data["activa"]
                    opcion.save()

            messages.success(request, "Ruleta guardada correctamente.")
            return redirect("admin_ruleta")

        if accion == "crear":
            if RuletaLegoOpcion.objects.count() >= 8:
                messages.error(request, "No se puede crear otra opción. La ruleta permite máximo 8 opciones.")
                return redirect("admin_ruleta")

            titulo = request.POST.get("titulo", "").strip()
            emoji = request.POST.get("emoji", "").strip()
            descripcion = request.POST.get("descripcion", "").strip()
            tokens = int(request.POST.get("tokens") or 0)
            porcentaje = int(request.POST.get("porcentaje") or 0)

            codigo_base = slugify(titulo)
            codigo = codigo_base
            contador = 1

            while RuletaLegoOpcion.objects.filter(codigo=codigo).exists():
                contador += 1
                codigo = f"{codigo_base}-{contador}"

            RuletaLegoOpcion.objects.create(
                codigo=codigo,
                emoji=emoji,
                titulo=titulo,
                descripcion=descripcion,
                tokens=tokens,
                porcentaje=porcentaje,
                activa=False,
                orden=RuletaLegoOpcion.objects.count() + 1
            )

            messages.success(request, "Opción creada como inactiva. Ajusta la ruleta completa y luego presiona Guardar ruleta completa.")
            return redirect("admin_ruleta")

        if accion == "eliminar":
            opcion = get_object_or_404(RuletaLegoOpcion, idopcion=request.POST.get("opcion_id"))
            opcion.delete()
            messages.success(request, "Opción eliminada. Revisa que la ruleta activa siga sumando 100%.")
            return redirect("admin_ruleta")

    opciones = RuletaLegoOpcion.objects.all().order_by("orden", "titulo")
    total_porcentaje = sum(o.porcentaje for o in opciones if o.activa)
    total_activas = sum(1 for o in opciones if o.activa)

    return render(request, "admin_ruleta.html", {
        "opciones": opciones,
        "total_porcentaje": total_porcentaje,
        "total_activas": total_activas,
    })

def admin_tiempos(request):
    if request.method == "POST":
        ids = request.POST.getlist("tiempo_id")

        for tiempo_id in ids:
            tiempo = get_object_or_404(TiempoFase, idtiempo=tiempo_id)
            tiempo.segundos = int(request.POST.get(f"segundos_{tiempo_id}") or 60)
            tiempo.activo = request.POST.get(f"activo_{tiempo_id}") == "on"
            tiempo.save(update_fields=["segundos", "activo"])

        messages.success(request, "Tiempos actualizados correctamente.")
        return redirect("admin_tiempos")

    tiempos = TiempoFase.objects.all().order_by("orden", "nombre")

    return render(request, "admin_tiempos.html", {
        "tiempos": tiempos,
    })

def ver_como_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, idgrupo=grupo_id)

    request.session["grupo_id"] = grupo.idgrupo
    request.session["sesion_id"] = grupo.sesion.idsesion

    request.session["modo_profesor"] = True 

    return redirect("pantalla_espera")