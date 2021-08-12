import csv
import json


from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q


from rest_framework.views import APIView
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.settings import api_settings

from rest_framework_csv import renderers as r

from django_filters import rest_framework as filters

from djoser.views import UserCreateView as DjoserUserCreateView
from djoser.views import UserViewSet as DjoserUserViewSet
from djoser.utils import login_user, login

from djoser.permissions import CurrentUserOrAdmin

from .models import Union, Society, Transaction, Account, User
from .serializers import (UnionSerializer, SocietySerializer, 
                        TransactionSerializer, AccountSerializer, UserPasswordResetSerializer,
                        TransactionCSVSerializer, UserSerializer)

# Create your views here.


def index(request):
    return JsonResponse({'message': 'Welcome to KoboCredit api'})


class TransactionsFilter(filters.FilterSet):
    union = filters.NumberFilter(field_name='society__union',
                                 lookup_expr='exact')
    created_start = filters.DateFilter(field_name='created', lookup_expr='date__gte')
    created_end = filters.DateFilter(field_name='created', lookup_expr='date__lte')
    
                                 

    class Meta:
        model = Transaction
        fields = ['union', 'created', 'member', 'secretary', 'account', 'society']


class UnionsFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name', lookup_expr='iexact')

    class Meta:
        model = Union
        fields = ['name']


class UsersFilter(filters.FilterSet):
    union = filters.NumberFilter(field_name='mem_societies__union',
                                 method='filter_by_union')

    def filter_by_union(self, queryset, name, value):
        return queryset.filter(Q(mem_societies__union=value) | 
                               Q(sec_societies__union=value)).distinct()

    class Meta:
        model = User
        fields = ['union']


class RegistrationView(DjoserUserCreateView):

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # fetch user based on serializer data
        user = User.objects.get(**serializer.data)
        # create token from user data
        token, _ = Token.objects.get_or_create(user=user)
        # attach token to user data
        data = {**serializer.data, 'token': token.key}
        # return reesponse
        return Response(data, status=status.HTTP_201_CREATED)


class UserPasswordResetView(generics.GenericAPIView):
    '''
        For Resetting User password
        endpoint: /api/auth/set_password
        params: { user_to_update, 'password' }
    '''
    serializer_class = UserPasswordResetSerializer
    permission_classes = (CurrentUserOrAdmin, )
    
    def post(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # get user object of user_to_update
        user = User.objects.get(id=serializer.data['user_to_update'])
        # set the password and save
        user.set_password(serializer.data['password'])
        user.save()
        
        return Response(status.HTTP_204_NO_CONTENT)

class UserViewSet(DjoserUserViewSet):
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UsersFilter
    # queryset = User.objects.all()

    def get_queryset(self):
        # apparently user_list only returns whole list for admins 
        # and not regular users. This fixes that
        if self.action == 'list':
            return User.objects.all()

        return super().get_queryset()

class UserUpdateViewSet(viewsets.ModelViewSet):
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UsersFilter
    queryset = User.objects.all()
    serializer_class = UserSerializer
    def get_queryset(self):
        # apparently user_list only returns whole list for admins 
        # and not regular users. This fixes that
        if self.action == 'list':
            return User.objects.all()

        return super().get_queryset()


class UnionViewSet(viewsets.ModelViewSet):
    '''
    get:
    Return a list of all existing unions

    post:
    Create a new Union

    retrieve:
    Returns a given union

    create:
    Create a new union instance
    '''

    serializer_class = UnionSerializer
    queryset = Union.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UnionsFilter


class SocietyViewSet(viewsets.ModelViewSet):
    '''
    get:
    Return a list of all societies

    post:
    Create a new Society

    retrieve:
    Returns a given society

    create:
    Create a new society instance
    '''
    serializer_class = SocietySerializer
    queryset = Society.objects.all()
    # filter_backends = (filters.DjangoFilterBackend,)
    # filterset_fields = ('union', )


class TransactionViewSet(viewsets.ModelViewSet):
    '''
    get:
    Return a list of all transactions

    post:
    Create a new Transaction

    retrieve:
    Returns a given transaction

    create:
    Create a new transaction instance
    '''
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TransactionsFilter


class AccountViewSet(viewsets.ModelViewSet):
    '''
    get:
    Return a list of all accounts

    post:
    Create a new Account

    retrieve:
    Returns a given account instance

    create:
    Create a new account instance
    '''
    serializer_class = AccountSerializer
    queryset = Account.objects.all()


class TransactionCSVView(generics.ListAPIView):
    serializer_class = TransactionCSVSerializer
    queryset = Transaction.objects.all()
    renderer_classes = (r.CSVRenderer, ) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TransactionsFilter

    # def list(self, request, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     return Response(status.HTTP_204_NO_CONTENT)

# class ProductViewSet(viewsets.ModelViewSet):
#     serializer_class = ProductSerializer
#     queryset = Product.objects.all()
#     parser_classes = (MultiPartParser, FormParser,)
#     filter_backends = (filters.SearchFilter,)
#     search_fields = ('name', 'code', 'manufacturer__name',)


# class APIKeyViewSet(viewsets.ModelViewSet):
#     serializer_class = APIKeySerializer
#     queryset = APIKey.objects.all()

#     def get_queryset(self):
#         return APIKey.objects.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         """ sets APIKey user to logged in user """
#         serializer.save(user=self.request.user)
