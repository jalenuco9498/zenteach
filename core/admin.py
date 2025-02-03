from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import Usuario, Servicio, Reserva, Horario,EstadoHorario,EstadoReserva,EstadoServicio,TipoUsuario
@admin.register(TipoUsuario)
class TipoUsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'fecha_registro')
    search_fields = ('nombre', 'descripcion')

@admin.register(EstadoServicio)
class EstadoServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'fecha_registro')
    search_fields = ('nombre', 'descripcion')

@admin.register(EstadoReserva)
class EstadoReservaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'fecha_registro')
    search_fields = ('nombre', 'descripcion')

@admin.register(EstadoHorario)
class EstadoHorarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'fecha_registro')
    search_fields = ('nombre', 'descripcion')
    
@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'full_name', 'tipo_usuario', 'fecha_registro', 'is_active')
    list_filter = ('tipo_usuario', 'is_staff', 'is_active', 'fecha_registro')
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('tipo_usuario_id',)}),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-fecha_registro',)

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Nombre completo'

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'duracion', 'mostrar_precio', 'estado_servicio', 'total_reservas', 'acciones')
    list_filter = ('estado_servicio', 'duracion')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('estado_servicio',)
    ordering = ('nombre',)

    def mostrar_precio(self, obj):
        return format_html(
            '<span style="color: green; font-weight: bold;">${}</span>',
            '{:,.0f}'.format(float(obj.precio))
        )
    mostrar_precio.short_description = 'Precio'

    def total_reservas(self, obj):
        count = obj.reservas.count()
        activas = obj.reservas.filter(
            estado__in=['pendiente', 'confirmada'],
            fecha_hora__gte=timezone.now()
        ).count()
        return format_html(
            '<span title="Total: {}">{} ({} activas)</span>',
            count, count, activas
        )
    total_reservas.short_description = 'Reservas'

    def acciones(self, obj):
        return format_html(
            '<a class="button" href="{}">Editar</a>&nbsp;'
            '<a class="button" href="{}">Ver Reservas</a>',
            f'/admin/core/servicio/{obj.id}/change/',
            f'/admin/core/reserva/?servicio__id__exact={obj.id}'
        )
    acciones.short_description = 'Acciones'

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'servicio', 'fecha_hora', 'estado_coloreado', 'tiempo_espera', 'creada')
    list_filter = ('estado_reserva', 'fecha_hora', 'servicio')
    search_fields = ('usuario__username', 'usuario__email', 'servicio__nombre')
    date_hierarchy = 'fecha_hora'
    readonly_fields = ('creada',)
    ordering = ('-fecha_hora',)
    actions = ['confirmar_reservas', 'cancelar_reservas']

    def estado_coloreado(self, obj):
        estados = {
            'pendiente': ('#FFA500', 'En espera de confirmación'),
            'confirmada': ('#28A745', 'Confirmada'),
            'cancelada': ('#DC3545', 'Cancelada')
        }
        color, texto = estados.get(obj.estado, ('#6C757D'))
        return format_html(
            '<span style="color: white; background-color: {}; padding: 5px 10px; '
            'border-radius: 15px; font-weight: 500;">{}</span>',
            color, texto
        )
    estado_coloreado.short_description = 'Estado'

    def tiempo_espera(self, obj):
        if obj.estado == 'pendiente':
            tiempo = timezone.now() - obj.creada
            horas = tiempo.total_seconds() / 3600
            if horas < 1:
                return format_html('<span style="color: green;">Reciente</span>')
            elif horas < 24:
                return format_html(
                    '<span style="color: orange;">{} horas</span>',
                    '{:.1f}'.format(horas)
                )
            else:
                return format_html(
                    '<span style="color: red;">{} días</span>',
                    '{:.0f}'.format(horas/24)
                )
        return "-"
    tiempo_espera.short_description = 'Tiempo en espera'

    def confirmar_reservas(self, request, queryset):
        updated = queryset.filter(estado='pendiente').update(estado='confirmada')
        self.message_user(
            request,
            'Se {} confirmado {} reserva{}'.format(
                "ha" if updated == 1 else "han",
                updated,
                "" if updated == 1 else "s"
            )
        )
    confirmar_reservas.short_description = "Confirmar reservas seleccionadas"

    def cancelar_reservas(self, request, queryset):
        updated = queryset.filter(estado='pendiente').update(estado='cancelada')
        self.message_user(
            request,
            'Se {} cancelado {} reserva{}'.format(
                "ha" if updated == 1 else "han",
                updated,
                "" if updated == 1 else "s"
            )
        )
    cancelar_reservas.short_description = "Cancelar reservas seleccionadas"

@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hora_inicio', 'hora_fin', 'estado_horario', 'estado', 'reservas_en_horario')
    list_filter = ('estado_horario', 'fecha')
    date_hierarchy = 'fecha'
    list_editable = ('estado_horario',)
    ordering = ('fecha', 'hora_inicio')

    def estado(self, obj):
        color = 'green' if obj.disponible else 'red'
        texto = 'Disponible' if obj.disponible else 'No disponible'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, texto
        )
    estado.short_description = 'Estado'

    def reservas_en_horario(self, obj):
        count = Reserva.objects.filter(
            fecha_hora__date=obj.fecha,
            fecha_hora__hour__gte=obj.hora_inicio.hour,
            fecha_hora__hour__lt=obj.hora_fin.hour
        ).count()
        color = 'red' if count > 0 else 'green'
        return format_html(
            '<span style="color: {};">{} reserva{}</span>',
            color, count, 's' if count != 1 else ''
        )
    reservas_en_horario.short_description = 'Reservas'

