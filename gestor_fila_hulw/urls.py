"""
URL configuration for gestor_fila_hulw project.
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = ([
    # 1. Redireciona a URL raiz ('') para a página de admin ('/admin/')
    path('', RedirectView.as_view(url='/admin/', permanent=True)),
    path("i18n/", include("django.conf.urls.i18n")),
    path("fila_cirurgica/", include("fila_cirurgica.urls")),
    path('externo/', include('externo.urls')),
    path("portal/", include("portal.urls", namespace="portal")),
    ]

    + i18n_patterns(
        path("admin/", admin.site.urls),
    )
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)