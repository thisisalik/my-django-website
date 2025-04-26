from django.contrib import admin
from django.urls import path, include  
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),

    # ✅ Add `next_page` to allow GET logout (redirect to login after logout)
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/accounts/login/'), name='logout'),

    path('', include('core.urls')),  
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
