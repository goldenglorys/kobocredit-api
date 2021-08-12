import ast
from rest_flex_fields import FlexFieldsModelSerializer
from rest_framework import serializers
from .models import User, Union, Society, Transaction, Account
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from django.core import exceptions as django_exceptions
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from djoser.serializers import (UserCreateSerializer,
                                UserSerializer as DjoserUserSerializer)

from djoser.conf import settings
from django.utils.translation import ugettext_lazy as _


class CloudinaryFieldSerializer(serializers.FileField):
    ''' Serializer for cloudinary image '''

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        ''' return absolute url of image'''
        return value.url


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ('name', 'id')


class CustomUserCreateSerializer(UserCreateSerializer):
    picture = CloudinaryFieldSerializer()
    # mem & sec societies are many to many fields,
    # had to do this hack because data is sent as
    # form-data and not json, because of the profile picture
    mem_societies = serializers.CharField(default='[]')
    sec_societies = serializers.CharField(default='[]')
    man_societies = serializers.CharField(default='[]')
    # to know the union where the user creation occurs
    union = serializers.PrimaryKeyRelatedField(queryset=Union.objects.all(), write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "id",
                  "phone_number", "first_name",
                  "last_name", "password", "picture", "address",
                  "date_of_birth", 'mem_societies', 'sec_societies', 'man_societies', 'union')
        read_only_fields = ('id',)

        extra_kwargs = {
            'password': {'write_only': True},
        }
        # default pass for members is => kobopass123, it's set from
        # the frontend

    def validate_mem_societies(self, data):
        # convert string to list
        # i.e '[24, 29]' ==> [24, 29]
        # TODO: Write code to validate mem_societies sent
        list_data = ast.literal_eval(data)
        return list_data

    def validate_sec_societies(self, data):
        # convert string to list
        # i.e '[24, 29]' ==> [24, 29]
        # TODO: Write code to validate sec_societies sent
        list_data = ast.literal_eval(data)
        return list_data

    def validate(self, attrs):
        # remove mem_societies and sec_societies from attributes
        # as they can't be directly assigned to User
        mem_societies = attrs.pop('mem_societies')
        sec_societies = attrs.pop('sec_societies')
        man_societies = attrs.pop('man_societies')
        union =  attrs.pop('union', None)
        user = User(**attrs)
        password = attrs.get("password")

        try:
            validate_password(password, user)
        except django_exceptions.ValidationError as e:
            serializer_error = serializers.as_serializer_error(e)
            raise serializers.ValidationError(
                {"password": serializer_error["non_field_errors"]}
            )

        return {
            **attrs,
            'mem_societies': mem_societies,
            'sec_societies': sec_societies,
            'man_societies': ast.literal_eval(man_societies),
            'union': union
        }

    def perform_create(self, validated_data):
        print('validated data ==> ', validated_data)
        member_societies = validated_data.pop('mem_societies', [])
        secretary_societies = validated_data.pop('sec_societies', [])
        bmanager_societies = validated_data.pop('man_societies', [])
        union = validated_data.pop('union')

        
        
        with transaction.atomic():
            print('\n\nvalidated data ==> ', validated_data)
            # print(member_societies, secretary_societies, bmanager_societies, union)
            
            user = User.objects.create_user(**validated_data)

            
            # Get respective groups
            sec_group = Group.objects.get(name='secretary')
            mem_group = Group.objects.get(name='member')
            man_group = Group.objects.get(name='society_manager')
            # set member societies and secretary societies
            if (member_societies):
                # if mem_societies is passed across set it,
                # this is necessary when creating members
                user.groups.add(mem_group)
                user.mem_societies.set(member_societies)
            if (bmanager_societies):
                print(bmanager_societies)
                user.groups.add(man_group)
                user.man_societies.add(Society.objects.get(id=bmanager_societies))
                # union.society_managers.add(user)
                # society.society_manager.set(user)
            if (secretary_societies):
                print(secretary_societies)
                # if mem_societies is passed across set it,
                # this is necessary when creating secretaries
                user.groups.add(sec_group)
                user.sec_societies.set(secretary_societies)
                # add user to list of union secretaries
                union.secretaries.add(user)

                print('union sec => ', union.secretaries)
                print('sent secretaries', secretary_societies)

            return user


class AccountSerializer(FlexFieldsModelSerializer):

    class Meta:
        model = Account
        fields = ('name', 'id', )


class UserSerializer(FlexFieldsModelSerializer):
    groups = serializers.SerializerMethodField()
    qrcode = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()

    @classmethod
    def get_groups(self, obj):
        return [x.name for x in obj.groups.all()]

    @classmethod
    def get_qrcode(self, obj):
        if obj.qrcode.get('url', None):
            return obj.qrcode['url']
        return ''

    @classmethod
    def get_picture(self, obj):
        if not obj.picture:
            return ''
        if '.png' in obj.picture.url or '.jpg' in obj.picture.url:
            return obj.picture.url
        return f'{obj.picture.url}.jpg'

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'is_active', 'groups', 'qrcode',
                  'full_name', 'first_name', 'last_name', 'phone_number',
                  'date_of_birth', 'ref_num', 'picture', 'address', 'mem_societies', 'man_societies', 'sec_societies', 'date_joined', 'balances', 'bm_approval', 'hq_approval',)
        read_only_fields = ('id', 'date_of_birth',
                            'groups', 'qrcode', 'ref_num', 'full_name', 'picture', 'date_joined', 'balances',)
 
    expandable_fields = {
        'mem_societies': ('core.SocietySerializer',
                          {'fields': ['id', 'name'], 'many': True}),
        'sec_societies': ('core.SocietySerializer',
                          {'fields': ['id', 'name'], 'many': True}),
        'man_societies': ('core.SocietySerializer',
                          {'fields': ['id', 'name'], 'many': True}),
    }

class UnionSerializer(FlexFieldsModelSerializer):
    accounts = AccountSerializer(many=True)
    secretaries = UserSerializer(many=True)
    members = UserSerializer(many=True)
    society_managers = UserSerializer(many=True)
    groups = serializers.SerializerMethodField()

    @classmethod
    def get_groups(self, obj):
        # get all groups aside superuser group
        groups = Group.objects.exclude(name='superuser')
        return [{'id': x.id, 'name': x.name} for x in groups]

    class Meta:
        model = Union
        fields = ('id', 'name', 'slug', 'ref_number', 'address',
                  'phone_number', 'email', 'website', 'accounts', 'groups',
                  'manager', 'stats', 'secretaries', 'members', 'society_managers',)
        read_only_fields = ('id', 'slug', 'ref_number',
                            'secretaries', 'groups', 'members', 'stats', 'society_managers',)


class SocietySerializer(FlexFieldsModelSerializer):
    website = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Society
        fields = ('id', 'name', 'ref_number', 'union', 'address',
                  'phone_number', 'email', 'website', 'stats',
                  'members', 'secretaries', 'society_manager', 'balances',)
        read_only_fields = ('id', 'stats', 'ref_number')

    expandable_fields = {
        'members': (UserSerializer, {'many': True, 'fields':['id', 'picture', 'username', 'balances', 'full_name'],}),
        'secretaries': (UserSerializer, { 'many': True, 'fields': ['id', 'picture', 'username', 'balances', 'full_name'],}),
        'society_manager': (UserSerializer, {'fields': ['id', 'picture', 'username', 'balances', 'full_name'],}),
    }


class TransactionSerializer(FlexFieldsModelSerializer):

    class Meta:
        model = Transaction
        fields = ('member', 'secretary', 'society',
                  'amount', 'action', 'account', 'created','bm_approval', 'hq_approval',)

    xpandable_fields = {
        'member': (UserSerializer, {'source': 'member'}),
        'secretary': (UserSerializer, {'source': 'secretary'}),
        'society': (SocietySerializer, {'source': 'society'}),
        'account': (AccountSerializer, {'source': 'account'}),
    }
class TransactionCSVSerializer(FlexFieldsModelSerializer):

    class Meta:
        model = Transaction
        fields = ('member', 'secretary', 'society',
                  'amount', 'action', 'account', 'created', 'bm_approval', 'hq_approval',)
        read_only_fields = ('member', 'secretary', 'society',
                  'amount', 'action', 'account', 'created', 'bm_approval', 'hq_approval',)
        

    expandable_fields = {
        'member': (UserSerializer, {'source': 'member', 'fields': ['ref_num', 'full_name']}),
        'secretary': (UserSerializer, {'source': 'secretary', 'fields': ['ref_num', 'full_name']}),
        'society': (SocietySerializer, {'source': 'society', 'fields': ['id', 'name']}),
        'account': (AccountSerializer, {'source': 'account', 'fields': ['id', 'name']}),
    }




class TokenCreateSerializer(serializers.Serializer):
    password = serializers.CharField(required=False, style={"input_type": "password"})
    union = serializers.PrimaryKeyRelatedField(queryset=Union.objects.all())

    default_error_messages = {
        "invalid_credentials": settings.CONSTANTS.messages.INVALID_CREDENTIALS_ERROR,
        "inactive_account": settings.CONSTANTS.messages.INACTIVE_ACCOUNT_ERROR,
        "not_part_of_union": _("User does not belong to this headquarter")
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.fields[settings.LOGIN_FIELD] = serializers.CharField(required=False)

    def validate(self, attrs):
        union = attrs.get("union")
        password = attrs.get("password")
        params = {settings.LOGIN_FIELD: attrs.get(settings.LOGIN_FIELD)}
        self.user = authenticate(**params, password=password)
        if not self.user:
            self.user = User.objects.filter(**params).first()
            if self.user and not self.user.check_password(password):
                self.fail("invalid_credentials")

        
        # check to see if union is available
        # if not union:
        #     return self.fail("not_part_of_union")
        
        # if user is not part of union users return error
        # if not (
        #     (self.user in union.members) or
        #     (self.user in union.secretaries.all()) or
        #     (self.user == union.manager) or
        #     (self.user in union.society_managers.all())):
        #     return self.fail("not_part_of_union")

        
        if self.user and self.user.is_active:
            return attrs
        self.fail("invalid_credentials")



class UserPasswordResetSerializer(serializers.Serializer):
    ''' Serializer for handling users change of password.
        With this the secretary can change their password,
        also users can change their password
    '''
    password = serializers.CharField(required=False, style={"input_type": "password"})
    # the user whose password is to be changed
    user_to_update = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    # the logged in user trying to perform the password change
    auth_user = serializers.HiddenField( default= serializers.CurrentUserDefault())

    default_error_messages = {
        "unauthorized": _("You are not authorized to change this password")
    }

    def validate(self, attrs):
        user_to_update = attrs.get('user_to_update')
        auth_user = attrs.get('auth_user')

        # check if the user trying to effect the change is a manager
        is_manager = auth_user.groups.filter(name='manager').exists()
        
        # if auth_user is a manager, return attrs
        if is_manager:
            return attrs
        
        # check if user whose password is to be changed is the same as
        # logged in user
        if user_to_update == auth_user:
            return attrs

        self.fail('unauthorized')
        



