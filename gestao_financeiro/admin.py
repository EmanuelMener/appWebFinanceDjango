from django.contrib import admin
from .models import Grupo, Transacao

admin.site.register(Transacao)


# Registrando o modelo Grupo para que apareça no painel de administração
admin.site.register(Grupo)
