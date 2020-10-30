# from django.db.models import fields
from django.db.models.expressions import Value
from django.http import request
from rest_framework import serializers

from google.oauth2 import id_token
from google.auth.transport import Request, requests
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.serializers import SerializerMetaclass

from .models import User
from .register import register_social_user


MAX_PASSWORD_LENGTH = 68
MIN_PASSWORD_LENGTH = 8


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        max_length=MAX_PASSWORD_LENGTH, min_length=MIN_PASSWORD_LENGTH, write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password')

    def validate(self, attrs):
        email = attrs.get('email', '')
        username = attrs.get('username', '')

        # TODO: Validate Password using regexs

        if not username.isalnum():
            raise serializers.ValidationError(
                'Username must contain only alphanumeric characters')

        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)




class GoogleSocialAuthSerializer(serializers.Serializer):
    token = serializers.CharField()

    GOOGLE_CLIENT_ID = "145123241245-qeld4bjknovdn7b4ppag2m5so0t6e9lm.apps.googleusercontent.com"
    # GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")

    def validate_auth_token(self, auth_token):
        try:
            idinfo = id_token.verify_oauth2_token(auth_token, requests.Request(), self.GOOGLE_CLIENT_ID)
        except ValueError:
            raise AuthenticationFailed(
                'Invalid Token. Try again'
            )

        userid = idinfo['sub']
        email = idinfo['email']
        name = idinfo['name']

        return register_social_user(
            provider='google', user_id=userid, email=email, name=name
        )