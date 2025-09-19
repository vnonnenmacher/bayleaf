# users/views.py
import time, jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import timedelta
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class ChatTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class ChatTokenView(APIView):
    """
    POST /api/users/chat-token/
      body: { "email": "...", "password": "..." }
      resp: { "access_token": "...", "user_id": 123, "expires_in": 300 }
    The token is HS256-signed using SIMPLE_JWT.SIGNING_KEY and includes:
      aud=bayleaf-api, sub=user_id, user_id, scope=user.read, iat/exp
      (optional) role, patient_id if the user is a Patient
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = ChatTokenSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        email = s.validated_data["email"].strip()
        password = s.validated_data["password"]

        # Find user by email and check password (avoid backend assumptions)
        try:
            user = User.objects.get(email__iexact=email, is_active=True)
        except User.DoesNotExist:
            return Response({"detail": "invalid_credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.check_password(password):
            return Response({"detail": "invalid_credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Short lifetime for chat token (default to OBO seconds you already set)
        lifetime = int(getattr(settings, "BAYLEAF_OBO_LIFETIME_SECONDS", 300))
        now = int(time.time())
        exp = now + lifetime

        # Base claims
        claims = {
            "aud": getattr(settings, "BAYLEAF_AUDIENCE_API", "bayleaf-api"),
            "sub": str(user.id),
            "user_id": user.id,
            "scope": "user.read",
            "iat": now,
            "exp": exp,
        }
        iss = getattr(settings, "BAYLEAF_ISSUER", None)
        if iss:
            claims["iss"] = iss

        # Optional: enrich with role/patient_id if helpful to your Agent logs
        role = getattr(user, "role", None)  # adapt if you store roles differently
        if role:
            claims["role"] = role
        # If you keep Patient as a subclass of User, presence of patient is implicit
        try:
            from patients.models import Patient
            patient = Patient.objects.filter(user_ptr_id=user.id).first()
            if patient:
                claims["patient_id"] = str(patient.pid if hasattr(patient, "pid") else patient.id)
        except Exception:
            pass  # patients app may not be available in all environments

        # Sign with HS256 (no kid/JWKS). SimpleJWT is already configured with this key.
        tok = AccessToken()
        tok.set_exp(lifetime=timedelta(seconds=lifetime))
        tok["aud"] = getattr(settings, "BAYLEAF_AUDIENCE_API", "bayleaf-api")
        tok["sub"] = str(user.id)
        tok["user_id"] = user.id
        tok["scope"] = "user.read"
        iss = getattr(settings, "BAYLEAF_ISSUER", None)
        if iss:
            tok["iss"] = iss

        try:
            from patients.models import Patient
            patient = Patient.objects.filter(user_ptr_id=user.id).first()
            if patient:
                tok["patient_id"] = str(getattr(patient, "pid", patient.id))
        except Exception:
            pass

        return Response({"access_token": str(tok), "user_id": user.id, "expires_in": lifetime})
