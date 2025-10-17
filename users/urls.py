from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import ChatTokenView, UserTypeView


urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("chat-token/", ChatTokenView.as_view(), name="chat_token"),
    path("me/type/", UserTypeView.as_view(), name="user_type"),
]
