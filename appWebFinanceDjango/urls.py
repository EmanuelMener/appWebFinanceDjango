# appWebFinanceDjango/urls.py
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('appfinanceiro/', include('gestao_financeiro.urls')),  # Inclui as URLs do app financeiro
    path('login/', auth_views.LoginView.as_view(template_name='gestao_financeiro/login.html'), name='login'),  # Login customizado
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),  # Logout redirecionando para login
]


