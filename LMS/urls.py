"""
URL configuration for LMS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/users/', include('accounts.api.urls')),
    path('api/v1/roles/', include('permissions.api.urls')),
    path('api/v1/uploads/', include('info_bridge.apis.urls')),
    path('api/v1/locations/', include('locations.apis.urls')),
    path('api/v1/leads/', include('leads.apis.urls')),
    path('api/v1/notifications/', include('notifications.apis.urls'))

]
