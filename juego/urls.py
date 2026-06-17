# juego/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    #NUEVO
    path(
        "sesion/<int:sesion_id>/dev/timer-10/",
        views.dev_timer_10_segundos,
        name="dev_timer_10_segundos"
        ),
        path(
        "dashboardadmin/preguntas-rompehielo/",
        views.admin_preguntas_rompehielo,
        name="admin_preguntas_rompehielo"
    ),
    path(
        "dashboardadmin/preguntas-rompehielo/<int:idpregunta>/editar/",
        views.admin_preguntas_rompehielo_editar,
        name="admin_preguntas_rompehielo_editar"
    ),
    path(
        "dashboardadmin/preguntas-rompehielo/<int:idpregunta>/toggle/",
        views.admin_preguntas_rompehielo_toggle,
        name="admin_preguntas_rompehielo_toggle"
    ),
    path(
        "dashboardadmin/preguntas-rompehielo/<int:idpregunta>/eliminar/",
        views.admin_preguntas_rompehielo_eliminar,
        name="admin_preguntas_rompehielo_eliminar"
    ),
    path("continuar-desde-mapa/", views.continuar_desde_mapa, name="continuar_desde_mapa"),
    path("sesion/<int:sesion_id>/fase-anterior/", views.profesor_fase_anterior, name="profesor_fase_anterior"),
    path("dashboardadmin/tiempos/", views.admin_tiempos, name="admin_tiempos"),
    path("dashboardadmin/ruleta/", views.admin_ruleta, name="admin_ruleta"),
    path("ver-grupo/<int:grupo_id>/", views.ver_como_grupo, name="ver_como_grupo"),
    path("dashboardadmin/desafios/<int:desafio_id>/info/", views.admin_desafio_info, name="admin_desafio_info"),
    path("profesores/", views.registrarprofesor, name="listar_profesores"),
    path("profesor/<int:profesor_id>/eliminar/", views.eliminar_profesor, name="eliminar_profesor"),
    path("profesor/<int:profesor_id>/eliminar-forzado/", views.eliminar_profesor_forzado, name="eliminar_profesor_forzado"),
    path("sesion/<int:sesion_id>/iniciar-timer-inicio-fase/", views.iniciar_timer_inicio_fase, name="iniciar_timer_inicio_fase"),
    path("bubblemap/otorgar-tokens/", views.otorgar_tokens_bubblemap, name="otorgar_tokens_bubblemap"),
    path("presentar-pitch/", views.presentar_pitch, name="presentar_pitch"),
    path("sesion/<int:sesion_id>/iniciar-presentacion/", views.iniciar_presentacion_pitch, name="iniciar_presentacion_pitch"),
    path("guardar-pitch/", views.guardar_pitch, name="guardar_pitch"),
    path("desbloquear-desafio/", views.desbloquear_desafio, name="desbloquear_desafio"),
    path("conocidos-modo/<str:modo>/", views.elegir_modo_conocidos, name="elegir_modo_conocidos"),
    path("conocidos-rapido/", views.conocidos_rapido, name="conocidos_rapido"),
    path("ruleta-lego-token/", views.aplicar_resultado_ruleta_lego, name="aplicar_resultado_ruleta_lego"),
    path("habilidades-intro/", views.habilidades_intro, name="habilidades_intro"),
    path('dashboardadmin/tematicas/', views.admin_tematicas, name='admin_tematicas'),
    path('dashboardadmin/desafios/', views.admin_desafios, name='admin_desafios'),
    path("sopa/registrar-palabra/", views.registrar_palabra_sopa, name="registrar_palabra_sopa"),
    path("grupo/<int:grupo_id>/listo-ranking/", views.marcar_listo_ranking, name="marcar_listo_ranking"),
    path("espera/", views.pantalla_espera, name="pantalla_espera"),
    path("cambiar-tematica/", views.cambiar_tematica, name="cambiar_tematica"),
    path("guardar-tematica/", views.guardar_tematica, name="guardar_tematica"),
    path("guardar-desafio/", views.guardar_desafio, name="guardar_desafio"),
    path("sesion/<int:sesion_id>/estado/", views.estado_sesion, name="estado_sesion"),
    path("sesion/<int:sesion_id>/actualizar-estado/", views.profesor_actualizar_estado, name="profesor_actualizar_estado"),
    path("sesion/<int:sesion_id>/siguiente-fase/", views.profesor_siguiente_fase, name="profesor_siguiente_fase"),
    path("finalizar-mision/", views.finalizar_mision, name="finalizar_mision"),
    path("grupo/<int:grupo_id>/listo/", views.marcar_grupo_listo, name="marcar_grupo_listo"),
    path("salir/", views.salir_grupo, name="salir_grupo"),
    path("sesion/<int:sesion_id>/control/", views.control_sesion, name="control_sesion"),
    path("sesion/<int:sesion_id>/preview/", views.preview_pantalla_profesor, name="preview_pantalla_profesor"),
    path("espera-eleccion/", views.espera_eleccion, name="espera_eleccion"),
    path(
    "sesion/<int:sesion_id>/sortear-orden/",
    views.profesor_sortear_orden_pitch,
    name="profesor_sortear_orden_pitch"
),


path(
    "sesion/<int:sesion_id>/estado-presentacion/",
    views.estado_presentacion_pitch,
    name="estado_presentacion_pitch",
),
path(
    "sesion/<int:sesion_id>/siguiente-grupo-pitch/",
    views.siguiente_grupo_pitch,
    name="siguiente_grupo_pitch",
),
    #NUEVO CIERRE 


    path('', views.perfiles, name='perfiles'),
    path('bienvenida/', views.bienvenida, name='bienvenida'),
    path('registro/', views.registro, name='registro'),
    path('lego/', views.lego, name='lego'),
    path('introducciones/', views.introducciones, name='introducciones'),
    path('pantalla_inicio/', views.pantalla_inicio, name='pantalla_inicio'),
    path('promptconocidos/', views.promptconocidos, name='promptconocidos'),
    path('conocidos/', views.conocidos, name='conocidos'),
    path('trabajoenequipo/', views.trabajoenequipo, name='trabajoenequipo'),
    path('minijuego1/', views.minijuego1, name='minijuego1'),
    path("sopa/completada/", views.sopa_completada, name="sopa_completada"),
    path('tematicas/', views.tematicas, name='tematicas'),
    path('desafios/', views.desafios, name='desafios'),
    path('bubblemap/', views.bubblemap, name='bubblemap'),
    path("orden-presentacion/", views.orden_presentacion_alumno, name="orden_presentacion_alumno"),
    path('pitch/', views.pitch, name='pitch'),
    path('presentar_pitch/', views.presentar_pitch, name='presentar_pitch'),
    path('dashboardprofesor/', views.dashboardprofesor, name='dashboardprofesor'),
    path('profesor/sesiones/', views.listar_sesiones, name='listar_sesiones'),
    path('profesor/sesiones/crear/', views.crear_sesion, name='crear_sesion'),
    path('registraralumnos/', views.registraralumnos, name='registraralumnos'),
    path('cargar-alumnos/', views.cargar_alumnos, name='cargar_alumnos'),
    path('agregar-alumnos/', views.agregar_alumno_manual, name='agregar_alumno_manual'),
    path('alumnos/eliminar/<int:idalumno>/', views.eliminar_alumno, name='eliminar_alumno'),
    path('dashboardadmin/', views.dashboardadmin, name='dashboardadmin'),
    path('registrarprofesor/', views.registrarprofesor, name='registrarprofesor'),
    path('agregardesafio/', views.agregardesafio, name='agregardesafio'),
    path('listardesafios/', views.lista_desafios, name='lista_desafios'),
    path('desafios/<int:iddesafio>/eliminar/', views.eliminar_desafio, name='eliminar_desafio'),
    path('transicionempatia/', views.transicionempatia, name='transicionempatia'),
    path('transicioncreatividad/', views.transicioncreatividad, name='transicioncreatividad'),
    path('transicioncomunicacion/', views.transicioncomunicacion, name='transicioncomunicacion'),
    path('transiciondesafio/', views.transiciondesafio, name='transiciondesafio'),
    path('transicionapoyo/', views.transicionapoyo, name='transicionapoyo'),
    path('registrargrupos/', views.registrargrupos, name='registrargrupos'),
    path('market/', views.market_view, name='market'),
    path('market/issue/<int:challenge_id>/', views.issue_challenge_view, name='issue_challenge'),
    path('peer-review/', views.peer_review_view, name='peer_review'),
    path("ranking/", views.ranking_view, name="ranking"),
    path('reflexion/', views.reflexion, name='reflexion'),
    path("mision-cumplida/", views.mision_cumplida_view, name="mision_cumplida"),

]

