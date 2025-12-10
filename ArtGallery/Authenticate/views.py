from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import RegisterSerializer
from .models import Painting
from django.contrib.auth import authenticate
from django.utils import timezone


# 1) REGISTER
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Tạo 10 khung tranh mặc định
            print(f"🎨 Creating 10 frames for user: {user.username}")
            for i in range(1, 11):
                painting = Painting.objects.create(
                    owner=user,
                    frame_number=i,
                    title=f'Frame {i}',
                    description='',
                    visibility='private',
                    has_image=False
                )
                print(f"   ✅ Created Frame {i} (ID: {painting.id})")
            print(f"🎉 Successfully created 10 frames for user: {user.username}")
            
            return Response(
                {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 2) LOGIN → return access + refresh token + USER DATA
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, email=email, password=password)

        if not user:
            return Response({"message": "Invalid credentials"}, status=400)

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "accessToken": str(refresh.access_token),
                "refreshToken": str(refresh),
                "expiresIn": 3600,
                "user": {  # ✅ THÊM USER DATA
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            },
            status=200
        )


# 3) REFRESH TOKEN
class RefreshTokenView(TokenRefreshView):
    pass


# 4) LOGOUT → revoke refresh token
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refreshToken")
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Logged out"}, status=200)

        except Exception:
            return Response({"message": "Invalid token"}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint for keep-alive services
    """
    return Response({
        "status": "ok",
        "timestamp": timezone.now().isoformat(),
        "message": "Server is running"
    })