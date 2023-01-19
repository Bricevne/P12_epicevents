"""eventmanager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from rest_framework_nested import routers
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from crm_api import views

router = routers.SimpleRouter()
router.register(r'clients', views.ClientViewset, basename="client")
router.register(r'users', views.CustomUserViewset, basename="user")

clients_router = routers.NestedSimpleRouter(router, r'clients', lookup='client')
clients_router.register(r'contracts', views.ContractViewset, basename='project-contracts')

contracts_router = routers.NestedSimpleRouter(clients_router, r'contracts', lookup='contract')
contracts_router.register(r'events', views.EventViewset, basename='contract-events')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path(r'', include(router.urls)),
    path(r'', include(clients_router.urls)),
    path(r'', include(contracts_router.urls)),
]
