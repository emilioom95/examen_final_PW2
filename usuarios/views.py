from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import render


def home(request):
    data = {}
    return render(request, 'examen/inicio.html', data)