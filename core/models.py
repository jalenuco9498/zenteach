from django.db import models
from django.contrib.auth.models import AbstractUser

class TipoUsuario(models.Model):
    nombre = models.CharField(max_length=10,  default='docente')
    descripcion = models.TextField(max_length=200)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre}"
    
class Usuario(AbstractUser):
    tipo_usuario = models.ForeignKey(TipoUsuario, on_delete=models.CASCADE, related_name='usuario', default=2)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.tipo_usuario})"
    
class EstadoServicio(models.Model):
    nombre = models.CharField(max_length=10,  default='pendiente')
    descripcion = models.TextField(max_length=200)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre}"

class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    duracion = models.IntegerField(help_text="Duración en minutos")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    estado_servicio = models.ForeignKey(EstadoServicio, on_delete=models.CASCADE, related_name='servicio')

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        
class EstadoReserva(models.Model):
    nombre = models.CharField(max_length=10,  default='pendiente')
    descripcion = models.TextField(max_length=200)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre}"
    
class Reserva(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reservas')
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='reservas')
    fecha_hora = models.DateTimeField()
    creada = models.DateTimeField(auto_now_add=True)
    estado_reserva = models.ForeignKey(EstadoReserva, on_delete=models.CASCADE, related_name='reserva')

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.servicio.nombre} - {self.fecha_hora}"

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fecha_hora']
        
class EstadoHorario(models.Model):
    nombre = models.CharField(max_length=10,  default='disponible')
    descripcion = models.TextField(max_length=200)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre}"
    
class Horario(models.Model):
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado_horario = models.ForeignKey(EstadoHorario, on_delete=models.CASCADE, related_name='horario')

    def __str__(self):
        return f"{self.fecha} {self.hora_inicio}-{self.hora_fin}"

    class Meta:
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"
