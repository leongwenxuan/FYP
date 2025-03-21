"""
URL configuration for fypapp project.

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
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from fypapp import views

router = DefaultRouter()
router.register(r'issues', views.AccessibilityIssueViewSet)
router.register(r'issues/(?P<issue_pk>\d+)/comments', views.IssueCommentViewSet)

urlpatterns = [
    path('', views.home, name='home'),
    path('report/', views.report_issue, name='report_issue'),
    path('issues/', views.issue_list, name='issue_list'),
    path('issues/<int:pk>/', views.issue_detail, name='issue_detail'),
    path('routermap/', views.routermap, name='routermap'),
    path('profile/', views.profile, name='profile'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('api/transcribe-audio/', views.transcribe_audio, name='transcribe_audio'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)