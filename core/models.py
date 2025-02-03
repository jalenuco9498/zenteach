from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    TIPO_USUARIO = (
        ('docente', 'Docente'),
        ('admin', 'Administrador')
    )
    tipo = models.CharField(max_length=10, choices=TIPO_USUARIO, default='docente')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.tipo})"

class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    duracion = models.IntegerField(help_text="Duración en minutos")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

class Reserva(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reservas')
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='reservas')
    fecha_hora = models.DateTimeField()
    estado = models.CharField(max_length=10, default='pendiente')
    creada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.servicio.nombre} - {self.fecha_hora}"

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fecha_hora']

class Horario(models.Model):
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.fecha} {self.hora_inicio}-{self.hora_fin}"

    class Meta:
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

class Recurso(models.Model):
    TIPO_RECURSO = (
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('documento', 'Documento')
    )
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=10, choices=TIPO_RECURSO)
    url = models.URLField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='recursos')

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Recurso"
        verbose_name_plural = "Recursos"