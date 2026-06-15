from django.db import models
from .image_utils import convertir_imagen_a_webp


class Alumno(models.Model):
    idalumno = models.AutoField(db_column='idAlumno', primary_key=True)
    profesor_idprofesor = models.ForeignKey('Profesor', models.DO_NOTHING, db_column='profesor_idProfesor')
    sesion = models.ForeignKey('Sesion', models.CASCADE, db_column='sesion_idSesion', null=True)
    emailalumno = models.CharField(db_column='emailAlumno', max_length=100, blank=True, null=True)
    rutalumno = models.CharField(db_column='rutAlumno', max_length=100, blank=True, null=True)
    nombrealumno = models.CharField(db_column='nombreAlumno', max_length=200, blank=True, null=True)
    apellidopaternoalumno = models.CharField(db_column='apellidoPaternoAlumno', max_length=100, blank=True, null=True)
    apellidomaternoalumno = models.CharField(db_column='apellidoMaternoAlumno', max_length=100, blank=True, null=True)
    carreraalumno = models.CharField(db_column='carreraAlumno', max_length=100, blank=True, null=True)
    grupo = models.ForeignKey('Grupo', models.DO_NOTHING, db_column='grupo_idGrupo', null=True, blank=True)
    class Meta:
        db_table = 'alumno'

class Tematica(models.Model):
    idtematica = models.AutoField(db_column='idTematica', primary_key=True)
    slug = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=150)
    hero = models.TextField(blank=True, null=True)
    chips = models.JSONField(default=list, blank=True)
    accent = models.CharField(max_length=20, default="#3b82f6")
    image = models.CharField(max_length=255, blank=True, null=True)
    activa = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'tematica'
        ordering = ['orden', 'title']

    def __str__(self):
        return self.title

class Desafio(models.Model):
    iddesafio = models.AutoField(db_column='idDesafio', primary_key=True)

    idadministrador_idadministrador = models.ForeignKey(
        'Idadministrador',
        models.DO_NOTHING,
        db_column='idadministrador_idAdministrador',
        null=True,
        blank=True
    )

    tematica = models.ForeignKey(
        'Tematica',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='desafios'
    )

    nombredesafio = models.CharField(db_column='nombreDesafio', max_length=150, blank=True, null=True)
    tokensdesafio = models.IntegerField(db_column='tokensDesafio', blank=True, null=True)
    descripciondesafio = models.TextField(db_column='descripcionDesafio', blank=True, null=True)

    imagen_desafio = models.ImageField(
        upload_to="desafios/",
        null=True,
        blank=True
    )

    summary = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        archivo_anterior = None

        if self.pk:
            anterior = type(self).objects.filter(pk=self.pk).first()
            if anterior and anterior.imagen_desafio:
                archivo_anterior = anterior.imagen_desafio.name

        if self.imagen_desafio and not self.imagen_desafio.name.lower().endswith(".webp"):
            nombre_webp, contenido_webp = convertir_imagen_a_webp(
                self.imagen_desafio,
                max_size=(1200, 1200),
                quality=80,
            )

            self.imagen_desafio.save(nombre_webp, contenido_webp, save=False)

        super().save(*args, **kwargs)

        if archivo_anterior and self.imagen_desafio and archivo_anterior != self.imagen_desafio.name:
            try:
                self.imagen_desafio.storage.delete(archivo_anterior)
            except Exception:
                pass

    class Meta:
        db_table = 'desafio'
        ordering = ['orden', 'nombredesafio']

    def __str__(self):
        return self.nombredesafio or "Desafío sin nombre"


class Desafiolego(models.Model):
    iddesafiolego = models.AutoField(db_column='idDesafioLego', primary_key=True)
    reto_idreto = models.ForeignKey('Reto', models.DO_NOTHING, db_column='reto_idReto')
    grupo_idgrupo = models.ForeignKey('Grupo', models.DO_NOTHING, db_column='grupo_idGrupo')

    class Meta:
        db_table = 'desafiolego'


class Encuesta(models.Model):
    idencuesta = models.AutoField(db_column='idEncuesta', primary_key=True)
    grupo_idgrupo = models.ForeignKey('Grupo', models.DO_NOTHING, db_column='grupo_idGrupo')
    fecha = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'encuesta'

class Grupo(models.Model):
    idgrupo = models.AutoField(db_column='idGrupo', primary_key=True)
    sesion = models.ForeignKey('Sesion', models.CASCADE, db_column='sesion_idSesion', null=True)
    nombregrupo = models.CharField(max_length=100, blank=True, null=True)
    usuario_idusuario = models.ForeignKey(
        'Usuario',
        models.DO_NOTHING,
        db_column='usuario_idUsuario',
        null=True,
        blank=True
    )
    tokensgrupo = models.IntegerField(blank=True, null=True, default=10)
    etapa = models.IntegerField(blank=True, null=True, default=1)
    codigoacceso = models.CharField(
        db_column='codigoAcceso',
        max_length=8,
        unique=True,
        blank=True,
        null=True
    )

    sopa_ganada = models.BooleanField(default=False)
    sopa_tiempo_segundos = models.PositiveIntegerField(null=True, blank=True)
    sopa_completada_en = models.DateTimeField(null=True, blank=True)
    orden_presentacion = models.PositiveIntegerField(null=True, blank=True)
    recompensa_peer_otorgada = models.BooleanField(default=False)

    foto_lego = models.ImageField(upload_to="legos/", null=True, blank=True)
    pitch_texto = models.TextField(null=True, blank=True)
    listo_ranking = models.BooleanField(default=False)

    # Sincro F2
    tema_elegido = models.CharField(max_length=80, blank=True, null=True)
    desafio_elegido = models.ForeignKey(
        'Desafio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grupos_que_lo_eligieron'
    )
    desafio_id_externo = models.CharField(max_length=50, blank=True, null=True)
    desafio_nombre = models.CharField(max_length=255, blank=True, null=True)
    desafio_descripcion = models.TextField(blank=True, null=True)

    listo_f2_tematicas = models.BooleanField(default=False)
    listo_f2_tematica = models.BooleanField(default=False)
    listo_f2_desafio = models.BooleanField(default=False)
    listo_f3_lego = models.BooleanField(default=False)
    lego_sin_foto = models.BooleanField(default=False)
    listo_lobby = models.BooleanField(default=False)
    listo_f1 = models.BooleanField(default=False)
    listo_f3 = models.BooleanField(default=False)
    listo_f4 = models.BooleanField(default=False)
    listo_f5 = models.BooleanField(default=False)
    listo_f6 = models.BooleanField(default=False)
    listo_f4_orden = models.BooleanField(default=False)
    listo_inicio_f3 = models.BooleanField(default=False)
    listo_f2 = models.BooleanField(default=False)
    listo_f2_empatia = models.BooleanField(default=False)
    bubble_tokens_otorgados = models.BooleanField(default=False)

    class Meta:
        db_table = 'grupo'

    def ajustar_tokens(self, cantidad):
        """Suma o resta tokens del grupo."""
        if self.tokensgrupo is None:
            self.tokensgrupo = 0

        self.tokensgrupo += cantidad

        if self.tokensgrupo < 0:
            self.tokensgrupo = 0

        self.save()

    def save(self, *args, **kwargs):
        archivo_anterior = None

        if self.pk:
            anterior = type(self).objects.filter(pk=self.pk).first()
            if anterior and anterior.foto_lego:
                archivo_anterior = anterior.foto_lego.name

        if self.foto_lego and not self.foto_lego.name.lower().endswith(".webp"):
            nombre_webp, contenido_webp = convertir_imagen_a_webp(
                self.foto_lego,
                max_size=(1000, 1000),
                quality=70,
            )

            self.foto_lego.save(nombre_webp, contenido_webp, save=False)

        super().save(*args, **kwargs)

        if archivo_anterior and self.foto_lego and archivo_anterior != self.foto_lego.name:
            try:
                self.foto_lego.storage.delete(archivo_anterior)
            except Exception:
                pass


class Idadministrador(models.Model):
    idadministrador = models.AutoField(db_column='idAdministrador', primary_key=True)
    usuario_idusuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='usuario_idUsuario')
    email = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'idadministrador'


class Mapaempatia(models.Model):
    idmapaempatia = models.AutoField(db_column='idMapaEmpatia', primary_key=True)
    desafio_iddesafio = models.ForeignKey(Desafio, models.DO_NOTHING, db_column='desafio_idDesafio')
    emociones = models.CharField(max_length=200, blank=True, null=True)
    gustos = models.CharField(max_length=200, blank=True, null=True)
    entorno = models.CharField(max_length=200, blank=True, null=True)
    necesidades = models.CharField(max_length=200, blank=True, null=True)
    limitaciones = models.CharField(max_length=200, blank=True, null=True)
    motivaciones = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'mapaempatia'


class Profesor(models.Model):
    idprofesor = models.AutoField(db_column='idProfesor', primary_key=True)
    usuario_idusuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='usuario_idUsuario')
    emailprofesor = models.CharField(max_length=100, blank=True, null=True)
    facultad = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'profesor'


class Reto(models.Model):
    idreto = models.AutoField(db_column='idReto', primary_key=True)
    desafio_iddesafio = models.ForeignKey(Desafio, models.DO_NOTHING, db_column='desafio_idDesafio', null=True, blank=True)
    nombrereto = models.CharField(db_column='nombreReto', max_length=90, blank=True, null=True)
    descripcionreto = models.CharField(db_column='descripcionReto', max_length=200, blank=True, null=True)
    recompensareto = models.CharField(db_column='recompensaReto', max_length=100, blank=True, null=True)
    costoreto = models.IntegerField(db_column='costoReto', blank=True, null=True)

    class Meta:
        db_table = 'reto'

class Retogrupo(models.Model):
    ESTADOS = (
        ('PEND', 'Pendiente'),
        ('COMP', 'Completado'),
        ('FALL', 'Fallado'),
    )

    idretogrupo = models.AutoField(primary_key=True)
    reto = models.ForeignKey(Reto, models.DO_NOTHING)
    grupo_emisor = models.ForeignKey(Grupo, models.DO_NOTHING, related_name='retos_enviados')
    grupo_receptor = models.ForeignKey(Grupo, models.DO_NOTHING, related_name='retos_recibidos')

    estado = models.CharField(max_length=4, choices=ESTADOS, default='PEND')
    tokens_costo = models.IntegerField(default=0)
    tokens_recompensa = models.IntegerField(default=0)
    tokens_penalizacion = models.IntegerField(default=0)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'retogrupo'


class Tokens(models.Model):
    idtokens = models.AutoField(db_column='idTokens', primary_key=True)
    grupo_idgrupo = models.ForeignKey(Grupo, models.DO_NOTHING, db_column='grupo_idGrupo')
    numtokens = models.IntegerField(db_column='numTokens', blank=True, null=True)

    class Meta:
        db_table = 'tokens'


class Usuario(models.Model):
    idusuario = models.AutoField(db_column='idUsuario', primary_key=True)
    password = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        db_table = 'usuario'

class Sesion(models.Model):
    idsesion = models.AutoField(primary_key=True)
    profesor = models.ForeignKey('Profesor', on_delete=models.CASCADE, db_column='profesor_idProfesor')
    nombre = models.CharField(max_length=120)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    grupo_presentando = models.ForeignKey(
    'Grupo',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='sesiones_como_presentador_actual'
)

    # Sincro
    fase_actual = models.CharField(max_length=40, default="f1_bienvenida")  
    timer_corriendo = models.BooleanField(default=False)
    segundos_restantes = models.IntegerField(default=0)
    timer_inicio_at = models.DateTimeField(null=True, blank=True)
    timer_fin_at = models.DateTimeField(null=True, blank=True)
    inicio_fase_habilitado = models.BooleanField(default=False)
    orden_sorteado = models.BooleanField(default=False)
    #Timer
    t_rompehielo = models.IntegerField(default=120)
    t_diferencias = models.IntegerField(default=300)
    t_empatia = models.IntegerField(default=300)
    t_creatividad = models.IntegerField(default=600)
    t_pitch_prep = models.IntegerField(default=300)
    t_pitch = models.IntegerField(default=90)
    t_tematicas = models.PositiveIntegerField(default=120)
    t_presentacion = models.PositiveIntegerField(default=90)

    

    class Meta:
        db_table = 'sesion'

    def __str__(self):
        return self.nombre

class Evaluacion(models.Model):
    idevaluacion = models.AutoField(primary_key=True)
    sesion = models.ForeignKey(
        Sesion,
        on_delete=models.CASCADE,
        related_name="evaluaciones"
    )
    grupo_evaluador = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name="evaluaciones_enviadas"
    )
    grupo_evaluado = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name="evaluaciones_recibidas"
    )
    claridad = models.IntegerField()
    creatividad = models.IntegerField()
    viabilidad = models.IntegerField()
    equipo = models.IntegerField()
    presentacion = models.IntegerField()
    comentario = models.TextField()
    reflexion = models.TextField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table = 'evaluacion'
        unique_together = ('sesion', 'grupo_evaluador', 'grupo_evaluado')

    def puntaje_total(self):
        return self.claridad + self.creatividad + self.viabilidad + self.equipo + self.presentacion

class PalabraSopaEncontrada(models.Model):
    sesion = models.ForeignKey('Sesion', on_delete=models.CASCADE, related_name='palabras_sopa')
    grupo = models.ForeignKey('Grupo', on_delete=models.CASCADE, related_name='palabras_sopa')
    palabra = models.CharField(max_length=80)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'palabra_sopa_encontrada'
        unique_together = ('sesion', 'grupo', 'palabra')

class BubbleMapRespuesta(models.Model):
    idrespuesta = models.AutoField(primary_key=True)
    sesion = models.ForeignKey('Sesion', on_delete=models.CASCADE, related_name='bubble_respuestas')
    grupo = models.ForeignKey('Grupo', on_delete=models.CASCADE, related_name='bubble_respuestas')
    desafio = models.ForeignKey('Desafio', on_delete=models.SET_NULL, null=True, blank=True, related_name='bubble_respuestas')

    tipo = models.CharField(max_length=50, blank=True, null=True)
    titulo = models.CharField(max_length=100, blank=True, null=True)
    texto = models.TextField(blank=True, null=True)

    relato = models.TextField(blank=True, null=True)
    link = models.TextField(blank=True, null=True)

    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bubblemap_respuesta'


class RuletaLegoOpcion(models.Model):
    idopcion = models.AutoField(primary_key=True)
    codigo = models.SlugField(max_length=80, unique=True)
    emoji = models.CharField(max_length=20, blank=True, null=True)
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    tokens = models.IntegerField(default=0)
    porcentaje = models.PositiveIntegerField(default=0)
    activa = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "ruleta_lego_opcion"
        ordering = ["orden", "titulo"]

    def __str__(self):
        return f"{self.emoji or ''} {self.titulo}"
    
class TiempoFase(models.Model):
    idtiempo = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=80, unique=True)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    segundos = models.PositiveIntegerField(default=60)
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "tiempo_fase"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return f"{self.nombre} - {self.segundos}s"