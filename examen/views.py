from pyexpat.errors import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import HistorialIntentos, Pregunta, Respuesta, ConfiguracionExamen, Intento, RespuestaIntento

def crear_usuario(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'inicio.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('iniciar_examen')  # Redirige a la vista iniciar_examen
    else:
        form = AuthenticationForm()
    return render(request, 'inicio.html', {'form': form})

def iniciar_examen(request):
    configuracion = ConfiguracionExamen.objects.first()
    if not configuracion:
        # Manejar caso cuando no hay configuración de examen
        return render(request, 'examen/error.html', {'mensaje': 'Configuración del examen no encontrada.'})

    # Obtener un conjunto de preguntas basado en la configuración del examen
    preguntas = Pregunta.objects.order_by('?')[:configuracion.numero_preguntas]

    return render(request, 'examen/examen.html', {
        'preguntas': preguntas,
        'tiempo_limite': configuracion.tiempo
    })

@login_required
def guardar_resultado(request):
    if request.method == 'POST':
        # Crear un nuevo intento
        intento = Intento(usuario=request.user)
        intento.save()  # Guardar primero para obtener un ID válido

        # Procesar respuestas
        respuestas_procesadas = 0
        for pregunta_id, respuesta_id in request.POST.items():
            if pregunta_id.startswith('respuesta_'):
                pregunta_id = pregunta_id.split('_')[1]
                try:
                    pregunta = Pregunta.objects.get(id=pregunta_id)
                    respuesta = Respuesta.objects.get(id=respuesta_id)
                    es_correcta = respuesta.es_correcta
                    
                    # Crear una respuesta de intento
                    RespuestaIntento.objects.create(
                        intento=intento,
                        pregunta=pregunta,
                        respuesta_seleccionada=respuesta,
                        es_correcta=es_correcta
                    )
                    respuestas_procesadas += 1
                except (Pregunta.DoesNotExist, Respuesta.DoesNotExist) as e:
                    messages.error(request, f"Error al procesar la respuesta: {e}")
        
        if respuestas_procesadas == 0:
            messages.error(request, "No se procesaron respuestas. Verifica que hayas respondido todas las preguntas.")
            return redirect('examen')

        # Calcular y asignar la puntuación
        try:
            puntuacion = intento.calcular_puntuacion()  # Asegúrate de que este método devuelve un valor numérico
            intento.puntuacion = puntuacion
            intento.save()
        except Exception as e:
            messages.error(request, f"Error al calcular la puntuación: {e}")
            return redirect('examen')

        return redirect('resultado_examen')

    return redirect('inicio')

@login_required
def resultado_examen(request):
    # Obtener el intento del usuario actual
    intento = Intento.objects.filter(usuario=request.user).last()
    if not intento:
        # Manejo en caso de que no haya un intento para el usuario
        return render(request, 'resultado.html', {'mensaje': 'No se encontraron resultados.'})

    # Obtener las respuestas del intento y la puntuación
    respuestas_intento = RespuestaIntento.objects.filter(intento=intento)
    puntuacion = intento.puntuacion

    # Preparar datos para la plantilla
    preguntas_respuestas = {}
    for respuesta_intento in respuestas_intento:
        pregunta = respuesta_intento.pregunta
        if pregunta not in preguntas_respuestas:
            preguntas_respuestas[pregunta] = {
                'respuesta_correcta': pregunta.respuesta_set.get(es_correcta=True).texto,
                'respuesta_seleccionada': respuesta_intento.respuesta_seleccionada.texto,
                'es_correcta': respuesta_intento.es_correcta
            }

    return render(request, 'resultado.html', {
        'preguntas_respuestas': preguntas_respuestas,
        'puntuacion': puntuacion,
        'numero_intento': intento.id,  # Agrega el ID del intento
        'fecha_hora': intento.fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),  # Formato de fecha y hora
    })

def examen_view(request):
    pregunta_actual = Pregunta.objects.first()
    if not pregunta_actual:
        return render(request, 'error.html', {'message': 'No hay preguntas disponibles.'})
    return render(request, 'examen.html', {'pregunta_actual': pregunta_actual})

def examen(request):
    if request.method == 'POST':
        aciertos = 0
        total_preguntas = Pregunta.objects.count()
        for pregunta in Pregunta.objects.all():
            respuesta_id = request.POST.get(f"respuesta_{pregunta.id}")
            if respuesta_id:
                respuesta_seleccionada = Respuesta.objects.get(id=respuesta_id)
                if respuesta_seleccionada.es_correcta:
                    aciertos += 1
        calificacion_inicial = 20  # Suponiendo que 20 es la calificación base
        nota_final = (calificacion_inicial * aciertos) / total_preguntas
        intento = HistorialIntentos(
            usuario=request.user,
            fecha_hora=timezone.now(),
            aciertos=aciertos,
            fallos=total_preguntas - aciertos,
            nota=nota_final
        )
        intento.save()
        return redirect('resultado', intento_id=intento.id)
    else:
        preguntas = Pregunta.objects.all().prefetch_related('respuesta_set')
        context = {'preguntas': preguntas}
        return render(request, 'examen/examen.html', context)
