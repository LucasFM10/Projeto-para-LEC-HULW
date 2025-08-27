from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "portal"

urlpatterns = [
    path("login/",  auth_views.LoginView.as_view(template_name="portal/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("", views.DashboardView.as_view(), name="dashboard"),

    path("fila/", views.FilaListView.as_view(), name="fila_list"),
    path("fila/nova/", views.FilaCreateView.as_view(), name="fila_create"),
    path("fila/<int:pk>/", views.FilaDetailView.as_view(), name="fila_detail"),
    path("fila/<int:pk>/editar/", views.FilaUpdateView.as_view(), name="fila_update"),
    path("fila/<int:pk>/historico/", views.FilaHistoryView.as_view(), name="fila_history"),
]
