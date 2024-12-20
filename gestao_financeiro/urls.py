# gestao_financeiro/urls.py

from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.painel, name='painel'),
    path('adicionar/', views.adicionar_transacao, name='adicionar_transacao'),
    path('criar/', views.criar_grupo, name='criar_grupo'),
    path('entrar/', views.entrar_grupo, name='entrar_grupo'),
    path('<int:grupo_id>/', views.painel_grupo, name='painel_grupo'),
    path('extrato/', views.extrato_completo, name='extrato_completo'),  # Nova URL para o extrato completo

    # Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='gestao_financeiro/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),

    path("importar_ofx/", views.importar_ofx, name="importar_ofx"),

    path('<int:grupo_id>/', views.detalhes_grupo, name='detalhes_grupo'),

    path('<int:transacao_id>/', views.editar_transacao, name='editar_transacao'),
    path('<int:transacao_id>/', views.apagar_transacao, name='apagar_transacao'),

    path('criar_conta/', views.criar_conta, name='criar_conta'),

]
