"""
URL configuration for gestor_fila_hulw project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from . import views

urlpatterns = (
    [
        # Inclui as URLs da app
        path("fila_cirurgica/", include("fila_cirurgica.urls")),
        path('', views.home, name='upload'),
        path("importar/pacientes/", views.processar_csv_pacientes,
            name="importar_pacientes"),
        path("importar/procedimentos/", views.home, name="importar_procedimentos"),
        path("importar/procedimentos-aghu/", views.processar_csv_procedimentos,
            name="importar_procedimentos-aghu"),
        path("importar/especialidades/", views.processar_csv_especialidades,
            name="importar_especialidades"),
        path("importar/especialidadesprocedimentos/", views.processar_csv_especialidades_procedimentos,
            name="importar_especialidades_procedimentos"),

        path("i18n/", include("django.conf.urls.i18n")),
    ]
    + i18n_patterns(
        path("admin/", admin.site.urls),
    )
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
