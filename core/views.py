from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import json
import pytz
from .forms import UserRegistrationForm
from .models import Servicio, Reserva, Usuario
from datetime import datetime

# Vistas principales
def home(request):
    servicios_destacados = Servicio.objects.filter(activo=True).annotate(
        total_reservas=Count('reservas')
    ).order_by('-total_reservas')[:3]
    return render(request, 'core/home.html', {
        'servicios_destacados': servicios_destacados
    })

@require_http_methods(["GET", "POST"])
def user_login(request):
    if request.user.is_authenticated:
        return redirect('profile')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'¡Bienvenido de vuelta, {user.get_full_name() or user.username}!')
                return redirect(request.GET.get('next', 'home'))
            else:
                messages.error(request, 'Tu cuenta está desactivada')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    return render(request, 'core/login.html')

@login_required
def user_logout(request):
    nombre = request.user.get_full_name() or request.user.username
    logout(request)
    messages.info(request, f'Hasta pronto, {nombre}')
    return redirect('home')

@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect('profile')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
         
            login(request, user)
            messages.success(request, f'¡Bienvenido a ZenTeach, {user.get_full_name() or user.username}!')
            return redirect('profile')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario')
    else:
        form = UserRegistrationForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def profile(request):
    now = timezone.now()
    # Obtener todas las reservas en una sola consulta
    todas_reservas = Reserva.objects.filter(
        usuario=request.user
    ).select_related('servicio').order_by('-fecha_hora')
    # Separar en activas e historial
    reservas_activas = [reserva for reserva in todas_reservas if reserva.fecha_hora >= now and reserva.estado in ['pendiente', 'confirmada']]
    historial_reservas = [reserva for reserva in todas_reservas if reserva.fecha_hora < now or reserva.estado == 'cancelada']
    # Estadísticas del usuario
    estadisticas = {
        'total_reservas': len(todas_reservas),
        'reservas_pendientes': sum(1 for r in reservas_activas if r.estado == 'pendiente'),
        'reservas_confirmadas': sum(1 for r in reservas_activas if r.estado == 'confirmada'),
        'reservas_completadas': sum(1 for r in reservas_activas if r.estado == 'confirmada'),
        'reservas_canceladas': sum(1 for r in todas_reservas if r.estado == 'cancelada'),
        'proxima_reserva': next((r for r in reservas_activas if r.fecha_hora > now), None),
        'servicios_favoritos': Servicio.objects.filter(
            reservas__usuario=request.user
        ).annotate(
            num_reservas=Count('reservas')
        ).order_by('-num_reservas')[:3]
    }
    context = {
        'user': request.user,
        'reservas_activas': reservas_activas,
        'historial_reservas': historial_reservas,
        'estadisticas': estadisticas,
        'ahora': now
    }
    return render(request, 'core/profile.html', context)



@login_required
def nueva_reserva(request):
    usuario = request.user.id
    servicios = Servicio.objects.all()
    fecha_actual = datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')
    context = {
        'fecha':fecha_actual,
        'usuario':usuario,
        'servicios':servicios
        
    }
    return render(request, "core/nueva_reserva.html",context)

@login_required
def guardar_reserva(request):
    if request.method == 'POST':
            fecha_hora = timezone.make_aware(datetime.fromisoformat(request.POST['fecha']), timezone.get_current_timezone())
            estado_reserva = request.POST['estado_reserva']
            usuario = Usuario.objects.get(pk=int(request.POST['usuario']))
            servicio = Servicio.objects.get(pk=int(request.POST['servicio']))

            reserva = Reserva(usuario=usuario, servicio=servicio, fecha_hora=fecha_hora, estado=estado_reserva)
            reserva.save()
            return redirect('home')
    else:
        print("Método de solicitud incorrecto (no es POST)")
     

@login_required
def reservar(request):
    try:
        # Obtener servicios activos y sus estadísticas
        servicios = Servicio.objects.filter(activo=True).annotate(
            reservas_totales=Count('reservas'),
            reservas_pendientes=Count('reservas', filter=Q(
                reservas__estado='pendiente',
                reservas__fecha_hora__gte=timezone.now()
            ))
        ).order_by('nombre')
        
        # Obtener próximas 24 horas para validación en frontend
        min_date = timezone.now()
        max_date = min_date + timedelta(days=30)
        context = {
            'servicios':servicios,
            'title': 'Reservar Servicio',
            'min_date': min_date.strftime('%Y-%m-%dT%H:%M'),
            'max_date': max_date.strftime('%Y-%m-%dT%H:%M'),
            'horario_inicio': '08:00',
            'horario_fin': '18:00'
        }
        return render(request, 'core/reservar.html', context)

    except Exception as e:
        messages.error(request, "Hubo un error al cargar los servicios")
        return redirect('home')

def validar_horario(fecha_hora):
    """Validar que el horario cumpla con las reglas de negocio"""
    try:
        fecha_hora_local = timezone.localtime(fecha_hora)
        now = timezone.now()
        # Validación de fecha pasada con margen de 5 minutos
        if fecha_hora_local < now - timedelta(minutes=5):
            raise ValidationError('No se pueden hacer reservas en el pasado')
        # Validar que no sea más de 30 días en el futuro
        if fecha_hora_local > now + timedelta(days=30):
            raise ValidationError('No se pueden hacer reservas con más de 30 días de anticipación')
        # Validar horario de atención (8 AM - 6 PM)
        hora = fecha_hora_local.hour
        minuto = fecha_hora_local.minute
        if hora < 8 or (hora >= 18 and minuto > 0):
            raise ValidationError('El horario de atención es de 8:00 AM a 6:00 PM')
        # Validar que no sea en fin de semana
        if fecha_hora_local.weekday() >= 5:
            raise ValidationError('No se atiende los fines de semana')
        # Validar que sea en intervalos de 30 minutos
        if minuto not in [0, 30]:
            raise ValidationError('Las reservas deben ser en intervalos de 30 minutos')
        return True
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f'Error al validar el horario: {str(e)}')

@login_required
def crear_reserva_api(request, servicio_id):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido'
        }, status=405)

    try:
        servicio = get_object_or_404(Servicio, id=servicio_id, activo=True)
        fecha_hora_str = request.POST.get('fecha_hora')
        if not fecha_hora_str:
            raise ValidationError('La fecha y hora son requeridas')
        fecha_hora = timezone.make_aware(datetime.fromisoformat(fecha_hora_str))
        validar_horario(fecha_hora)
        if Reserva.objects.filter(
            fecha_hora=fecha_hora,
            estado__in=['pendiente', 'confirmada']
        ).exists():
            raise ValidationError('El horario seleccionado no está disponible')
        reserva = Reserva.objects.create(
            usuario=request.user,
            servicio=servicio,
            fecha_hora=fecha_hora,
            estado='pendiente'
        )
        return JsonResponse({
            'success': True,
            'message': 'Reserva creada exitosamente. En espera de confirmación.',
            'reserva': {
                'id': reserva.id,
                'servicio': servicio.nombre,
                'fecha_hora': fecha_hora.isoformat(),
                'estado': 'pendiente',
                'duracion': servicio.duracion,
                'precio': float(servicio.precio)
            }
        })
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al procesar la reserva'
        }, status=500)

@login_required
def historial_reservas(request):
    now = timezone.now()
    reservas = Reserva.objects.filter(
        usuario=request.user
    ).select_related('servicio').order_by('-fecha_hora')
    context = {
        'reservas': reservas,
        'ahora': now
    }
    return render(request, 'core/mis_reservas.html', context)

@login_required
def admin():
     return redirect('admin')