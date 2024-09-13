
from django.urls import path
from accounts.api.views import UsersAPIView, LoginAPIView, CustomRefreshToken, LogoutView

app_name='accounts'

urlpatterns = [

    path('', UsersAPIView.as_view(), name='users'),
    path('login/', LoginAPIView.as_view(), name='user-login'),
    path('token/refresh/', CustomRefreshToken.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout')
]