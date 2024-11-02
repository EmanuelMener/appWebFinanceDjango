# gestao_financeiro/urls.py

from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('financeiro/', views.painel, name='painel'),
    path('financeiro/adicionar/', views.adicionar_transacao, name='adicionar_transacao'),
    path('financeiro/grupo/criar/', views.criar_grupo, name='criar_grupo'),
    path('financeiro/grupo/entrar/', views.entrar_grupo, name='entrar_grupo'),
    path('financeiro/grupo/<int:grupo_id>/', views.painel_grupo, name='painel_grupo'),
    path('extrato/', views.extrato_completo, name='extrato_completo'),  # Nova URL para o extrato completo

    # Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='gestao_financeiro/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),

]
