from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# Create your models here.
class Pregunta(models.Model):
    enunciado = models.TextField()

class Respuesta(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    texto = models.TextField()
    es_correcta = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.pregunta.id}, {self.texto}, {self.es_correcta}" 

class ConfiguracionExamen(models.Model):
    tiempo = models.IntegerField(help_text="Tiempo en minutos")
    calificacion_maxima = models.IntegerField(help_text="Calificación máxima")
    numero_preguntas = models.IntegerField(help_text="Número total de preguntas")

    def __str__(self):
        return f"Configuración: {self.numero_preguntas} preguntas, {self.tiempo} minutos"

class Intento(models.Model):
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField(default=timezone.now)
    puntuacion = models.FloatField(null=True, blank=True)  # Asegúrate de permitir nulos

    def __str__(self):
        return f"Intento {self.pk} por {self.usuario} en {self.fecha_hora}"
    
    def calcular_puntuacion(self):
        configuracion = ConfiguracionExamen.objects.first()
        if not configuracion:
            return 0
        total_preguntas = configuracion.numero_preguntas
        aciertos = self.respuestaintento_set.filter(es_correcta=True).count()
        return (configuracion.calificacion_maxima * aciertos) / total_preguntas

class RespuestaIntento(models.Model):
    intento = models.ForeignKey(Intento, on_delete=models.CASCADE)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    respuesta_seleccionada = models.ForeignKey(Respuesta, on_delete=models.CASCADE)
    es_correcta = models.BooleanField()

    def __str__(self):
        return f"Respuesta {self.respuesta_seleccionada} para {self.pregunta} en {self.intento}"

class HistorialIntentos(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField(default=timezone.now)
    aciertos = models.IntegerField()
    fallos = models.IntegerField()
    nota = models.FloatField()

    def __str__(self):
        return f"Intento de {self.usuario.username} el {self.fecha_hora}"