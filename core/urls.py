from django.urls import path, include
from core import views
from rest_framework import routers
from rest_framework.documentation import include_docs_urls

router = routers.DefaultRouter()
router.register(r'headquarters', views.UnionViewSet, 'headquarter')
router.register(r'branches', views.SocietyViewSet, 'branch')
router.register(r'transactions', views.TransactionViewSet, 'transaction')
router.register(r'accounts', views.AccountViewSet, 'account')

userRoute = routers.DefaultRouter()
userRoute.register(r'users', views.UserViewSet, 'users')

userRoute.register(r'update', views.UserUpdateViewSet, 'update')

urlpatterns = [
    path('drf-auth/', include('rest_framework.urls')),
    
    path('auth/', include(userRoute.urls)),

    path('auth/set_password/', views.UserPasswordResetView.as_view()),
    
    path('auth/', include('djoser.urls')),

    
    path('auth/register/', views.RegistrationView.as_view()),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
    path('export-transactions/', views.TransactionCSVView.as_view()),
    path('docs/', include_docs_urls(title='Kobo API Documentation')),
]

# consider using drf_ysg for documentation
