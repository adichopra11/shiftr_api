import os

from django.contrib import auth
from django.db.models import fields

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from google.oauth2 import id_token
from google.auth.transport import requests
from rest_framework.serializers import Serializer

from .models import User
from .register import register_social_user

from todo.models import Todo, TodoItem
from inventorymanagement.models import InventoryItem


MAX_PASSWORD_LENGTH = 68
MIN_PASSWORD_LENGTH = 8


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'phone_number',
            'profession',
            'auth_provider']


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        max_length=MAX_PASSWORD_LENGTH, min_length=MIN_PASSWORD_LENGTH, write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password',
                  'phone_number', 'profession')

    def validate(self, attrs):
        email = attrs.get('email', '')
        username = attrs.get('username', '')
        phone_number = attrs.get('phone_number', '0000000000')
        profession = attrs.get('profession', 'Unemployed')

        # TODO: Validate Password using regexs

        if not username.isalnum():
            raise serializers.ValidationError(
                'Username must contain only alphanumeric characters')

        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class EmailVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=555)

    class Meta:
        model = User
        fields = ['token']


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)
    username = serializers.CharField(max_length=255, read_only=True)
    password = serializers.CharField(
        max_length=MAX_PASSWORD_LENGTH, min_length=MIN_PASSWORD_LENGTH, write_only=True)
    tokens = serializers.SerializerMethodField()

    def get_tokens(self, obj):

        user = User.objects.get(email=obj['email'])

        return {
            'access': user.tokens()['access'],
            'refresh': user.tokens()['refresh']
        }

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'tokens']

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')

        user = auth.authenticate(email=email, password=password)

        if not user:
            raise AuthenticationFailed(
                'Invalid Credentials, try again.'
            )

        if not user.is_active:
            raise AuthenticationFailed(
                'Account Disabled. Contact admin'
            )

        if not user.is_verified:
            raise AuthenticationFailed(
                'Email Not verified')

        return {
            'email': user.email,
            'username': user.username,
            'tokens': user.tokens(),
        }


class GoogleSocialAuthSerializer(serializers.Serializer):
    token = serializers.CharField()
    phone_number = serializers.RegexField(
        regex=r'^\+?[0-9]{9,15}$', max_length=15)
    profession = serializers.CharField()

    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")

    def validate(self, data):
        try:
            idinfo = id_token.verify_oauth2_token(
                data["token"], requests.Request(), self.GOOGLE_CLIENT_ID)
        except ValueError:
            raise AuthenticationFailed(
                'Invalid Token. Try again'
            )

        userid = idinfo['sub']
        email = idinfo['email']
        name = idinfo['name']
        provider = 'google'

        return register_social_user(
            provider=provider,
            user_id=userid,
            email=email,
            name=name,
            phone_number=data["phone_number"],
            profession=data["profession"]
        )


class DashboardSerializer(serializers.Serializer):

    username = serializers.CharField()
    email = serializers.EmailField()
    profession = serializers.CharField()

    def validate(self, data):

        username = data["username"]
        email = data["email"]
        profession = data["profession"]

        user = User.objects.get(email=email)
        completed_todo_item = TodoItem.objects.filter(todo_list__owner=user, done=True).count()
        pending_todo_item = TodoItem.objects.filter(todo_list__owner=user, done=False).count()
        inventory = InventoryItem.objects.filter(owner=user).count()

        return {
            "username": username,
            "email": email,
            "profession": profession,
            "completed_todo": completed_todo_item,
            "pending_todo": pending_todo_item,
            "inventory": inventory,
        }
