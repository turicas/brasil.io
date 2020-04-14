from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
    path('auth/', include('brasilio_auth.urls', namespace='brasilio_auth')),
    path('', include('core.urls', namespace='core')),
    path('markdownx/', include('markdownx.urls')),
]

urlpatterns += [
    path('django-rq/', include('django_rq.urls'))
]
