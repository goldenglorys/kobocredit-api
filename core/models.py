from django.contrib.auth.models import AbstractUser, Group, PermissionsMixin
from django.db import models
from django.db.models import Q, Sum, Count, F, FloatField
from django.db.models.fields import BooleanField, CharField
from django.db.models.functions import Coalesce
from cloudinary.models import CloudinaryField
from django_extensions.db.fields import RandomCharField, AutoSlugField
from django_extensions.db.models import TimeStampedModel
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .utils import generate_qrcode
from cloudinary import CloudinaryResource
import cloudinary
from django.contrib.postgres.fields import JSONField
from django.utils.html import format_html
# Create your models here.


class User(AbstractUser):
    """ Custom User model """
    email = models.EmailField(unique=True, null=True)
    ref_num = RandomCharField(length=5, uppercase=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(null=True)
    phone_number = models.CharField(max_length=15)
    picture = CloudinaryField('image', help_text='Profile picture', null=True)
    qrcode = JSONField(default=dict)
    status = CharField(max_length=15, default='registered')
    bm_approval = BooleanField(max_length=15, default=False)
    hq_approval = BooleanField(max_length=15, default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def qrcode_img(self):
        print(self.qrcode)
        if self.qrcode:
            return format_html(f"<img src={self.qrcode['url']} />")
        return None

    qrcode_img.short_description = 'QRCode image'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def balances(self):
      data = []
      for society in self.mem_societies.all():
        soc_data = {}

        soc_data['society_id'] = society.id
        soc_data['society_name'] = society.name

        society_balances = society.union.accounts.annotate(
          #  Coalesce makes sure it returns 0 instead of None
          debit_amt=Coalesce(Sum('transactions__amount', filter=Q(
              transactions__action='debit',
              transactions__member=self)), 0),
          credit_amt=Coalesce(Sum('transactions__amount', filter=Q(
              transactions__action='credit',
              transactions__member=self)), 0),
          balance=F('credit_amt')-F('debit_amt')
        ).values('name', 'id', 'debit_amt', 'credit_amt', 'balance')

        soc_data['society_balances'] = list(society_balances)
        data.append(soc_data)

      return data



    def __str__(self):
        return self.username


class Account(models.Model):
    """ Accounts Model """
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name} Account"



class Union(models.Model):
    """ Cooperative Union Model """

    def slugify_function(self, content):
        ''' Create a slug field for union's ref number '''
        content = 'HQ_' + content.replace(' ', '_')
        content = content.replace('-', '_')
        return content.upper()

    name = models.CharField(max_length=200, unique=True)
    slug = AutoSlugField(populate_from=['name'])
    ref_number = AutoSlugField(
        populate_from=['name'], slugify_function=slugify_function)
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    website = models.CharField(max_length=255)
    accounts = models.ManyToManyField(Account, related_name='unions')
    manager = models.ForeignKey(User, limit_choices_to={
                                'groups__name': 'manager'},
                                related_name='m_unions',
                                null=True,
                                on_delete=models.SET_NULL)
    secretaries = models.ManyToManyField('User', limit_choices_to={
                                         'groups__name': 'secretary'},
                                         related_name='s_unions')
    society_managers = models.ManyToManyField('User', limit_choices_to={
                                         'groups__name': 'society_manager'},
                                         related_name='sm_unions')

    @property
    def members(self):
        # Get unique members
        members = User.objects.filter(mem_societies__union=self).exclude(
            groups__name__in=['secretary', 'manager', 'society_manager']).distinct()
        return members
        
        
        

    @property
    def stats(self):
        # neccessary queries
        union_members = User.objects.filter(
            mem_societies__union=self, groups__name='member').distinct()
        union_secretaries = User.objects.filter(
            sec_societies__union=self, groups__name='secretary').distinct()
        union_societies = Society.objects.filter(union=self)
        union_transactions = Transaction.objects.filter(society__union=self)

        #  total members count
        members_count = union_members.count()
        # total societies
        societies_count = union_societies.count()
        #  total credit gotten
        # transactions summary should only be calculate from active users
        total_dict = union_transactions.aggregate(
            credit=Sum('amount', filter=Q(
                action='credit', member__is_active=True)),
            debit=Sum('amount', filter=Q(
                action='debit', member__is_active=True))
        )

        total_credit = total_dict['credit']
        total_debit = total_dict['debit']
        # transaction summary stats
        trans_summary = self.accounts.annotate(
            #  Coalesce makes sure it returns 0 instead of None
            debit_amt=Coalesce(Sum('transactions__amount', filter=Q(
                transactions__action='debit',
                transactions__member__is_active=True)), 0),
            credit_amt=Coalesce(Sum('transactions__amount', filter=Q(
                transactions__action='credit',
                transactions__member__is_active=True)), 0),
            total_amt=F('credit_amt')-F('debit_amt')
        ).values('name', 'id', 'debit_amt', 'credit_amt', 'total_amt')

        # leaderboard
        top_secretaries = union_secretaries.annotate(
            credit=Coalesce(Sum('recordings__amount', filter=Q(
                recordings__action='credit',
                recordings__member__is_active=True)), 0),
            debit=Coalesce(Sum('recordings__amount', filter=Q(
                recordings__action='debit',
                recordings__member__is_active=True)), 0)
        ).order_by('-credit').values('first_name', 'last_name', 'credit', 'debit')[:5]

        top_societies = union_societies.annotate(
            credit=Coalesce(Sum('transactions__amount', filter=Q(
                transactions__action='credit',
                transactions__member__is_active=True)), 0),
            debit=Coalesce(Sum('transactions__amount', filter=Q(
                transactions__action='debit',
                transactions__member__is_active=True)), 0)
        ).order_by('-credit').values('name', 'credit', 'debit')[:5]
        # only include active members
        top_members = union_members.filter(is_active=True).annotate(
            debit_amt=Coalesce(Sum('transactions__amount', filter=Q(
                transactions__action='debit')), 0),
            credit_amt=Coalesce(Sum('transactions__amount', filter=Q(
                transactions__action='credit')), 0),
            amount=F('credit_amt')-F('debit_amt')
        ).order_by('-amount').values('first_name', 'last_name', 'amount', 'credit_amt', 'debit_amt')[:5]

        return {
            'members_count': members_count,
            'societies_count': societies_count,
            'total_credit': total_credit,
            'total_debit': total_debit,
            'trans_summary': trans_summary,
            'leaderboard': {
                'secretaries': top_secretaries,
                'societies': top_societies,
                'members': top_members
            }
        }

    def __str__(self):
        return f"{self.name} Headquarter"

    class Meta:
        verbose_name_plural = "Headquarter"


class Society(models.Model):
    """ Cooperative Society Model """

    def slugify_function(self, content):
        ''' Create a slugfield for society ref number '''
        content = 'BR_' + content.replace(' ', '_')
        content = content.replace('-', '_')
        return content.upper()

    name = models.CharField(max_length=200, unique=True)
    ref_number = AutoSlugField(
        populate_from=['union__name', ], separator='_',
        slugify_function=slugify_function)
    union = models.ForeignKey(
        Union, related_name='societies', on_delete=models.CASCADE)
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    website = models.CharField(max_length=255, blank=True, null=True)
    # mem_societies => refer to societies a user is a member of
    # sec_societies => refer to societies a user is a secretary in
    members = models.ManyToManyField('User', related_name='mem_societies', null=True)
    secretaries = models.ManyToManyField('User', limit_choices_to={
        'groups__name': 'secretary'}, related_name='sec_societies', null=True)
    society_manager = models.ForeignKey(User, limit_choices_to={
                                'groups__name': 'society_manager'},
                                related_name='man_societies',
                                null=True,
                                on_delete=models.SET_NULL)

    @property
    def balances(self):
        data = {}
        for account in self.union.accounts.all():
            credit_trans = Transaction.objects.filter(
                society=self, account=account, action='credit')
            debit_trans = Transaction.objects.filter(
                society=self, account=account, action='debit')

            credit_amt = 0
            debit_amt = 0

            if (credit_trans.count() > 0):
                credit_amt = Transaction.objects.filter(
                    society=self, account=account, action='credit').aggregate(Sum('amount'))['amount__sum']

            if (debit_trans.count() > 0):
                debit_amt = Transaction.objects.filter(
                    society=self, account=account, action='debit').aggregate(Sum('amount'))['amount__sum']

            bal = credit_amt - debit_amt
            data[account.name] = bal

        trans_summary = self.union.accounts.annotate(
            #  Coalesce makes sure it returns 0 instead of None
            debit_amt=Coalesce(Sum('transactions__amount', filter=Q(
                transactions__society=self,
                transactions__action='debit',
                transactions__member__is_active=True)), 0),
            credit_amt=Coalesce(Sum('transactions__amount', filter=Q(
                transactions__society=self,
                transactions__action='credit',
                transactions__member__is_active=True)), 0),
            balance=F('credit_amt')-F('debit_amt')
        ).values('name', 'id', 'debit_amt', 'credit_amt', 'balance')

        return [{
            'society_id': self.id,
            'society_name': self.name,
            'society_balances': trans_summary
        }]

    @property
    def stats(self):
        ''' Stats of each society including summary transaction '''
        
        #  total credit gotten
        total_dict = self.transactions.aggregate(
            credit=Sum('amount', filter=Q(
                action='credit', society=self)),
            debit=Sum('amount', filter=Q(
                action='debit', society=self))
        )

        members_count = self.members.count()
        secretaries_count = self.secretaries.count() 

        trans_summary = self.union.accounts.annotate(
            #  Coalesce makes sure it returns 0 instead of None
            debit_amt=Coalesce(Sum('transactions__amount', filter=Q(
                transactions__society=self,
                transactions__action='debit',
                transactions__member__is_active=True)), 0),
            credit_amt=Coalesce(Sum('transactions__amount', filter=Q(
                transactions__society=self,
                transactions__action='credit',
                transactions__member__is_active=True)), 0),
            total_amt=F('credit_amt')-F('debit_amt')
        ).values('name', 'id', 'debit_amt', 'credit_amt', 'total_amt')

        top_secretaries =  self.secretaries.annotate(
            credit=Coalesce(Sum('recordings__amount', filter=Q(
                recordings__society=self,
                recordings__action='credit',
                recordings__member__is_active=True)), 0),
            debit=Coalesce(Sum('recordings__amount', filter=Q(
                recordings__society=self,
                recordings__action='debit',
                recordings__member__is_active=True)), 0)
        ).order_by('-credit').values('first_name', 'last_name', 'credit', 'debit')[:5]
        # only include active members
        top_members = self.members.annotate(
            debit_amt=Coalesce(Sum('transactions__amount', filter=Q(
                transactions__society=self,
                transactions__action='debit')), 0),
            credit_amt=Coalesce(Sum('transactions__amount', filter=Q(
                transactions__society=self,
                transactions__action='credit')), 0),
            amount=F('credit_amt')-F('debit_amt')
        ).order_by('-amount').values('first_name', 'last_name', 'amount', 'credit_amt', 'debit_amt')[:5]

        return {
            'total_credit': total_dict['credit'],
            'total_debit': total_dict['debit'],
            'members_count': members_count,
            'secretaries_count': secretaries_count,
            'trans_summary': trans_summary,
            'leaderboard': {
                'secretaries': top_secretaries,
                'members': top_members
            }
        }

    def __str__(self):
        return f"{self.name} Branch"

    class Meta:
        verbose_name_plural = "Branches"


class Transaction(TimeStampedModel):
    """ Transaction Model """
    TRANSACTION_TYPES = (
        ('debit', 'debit'),
        ('credit', 'credit')
    )

    member = models.ForeignKey(
        User, related_name='transactions', on_delete=models.CASCADE)
    secretary = models.ForeignKey(User, limit_choices_to={
        'groups__name': 'secretary'}, related_name='recordings', null=True, on_delete=models.SET_NULL)
    society_manager = models.ForeignKey(User, limit_choices_to={
        'groups__name': 'society_manager'}, related_name='manager_recordings', null=True, on_delete=models.SET_NULL)
    society = models.ForeignKey(
        Society, related_name='transactions', on_delete=models.CASCADE)
    amount = models.FloatField()
    action = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    account = models.ForeignKey(
        'Account', related_name='transactions', on_delete=models.CASCADE)
    status = CharField(max_length=15, default='created')
    bm_approval = BooleanField(max_length=15, default=False)
    hq_approval = BooleanField(max_length=15, default=False)

    def __str__(self):
        return f'{self.action} from {self.member}'


@receiver(post_save, sender=User)
def add_user_to_group(sender, instance, created, **kwargs):
    ''' assigns member user status to newly registered users with no group '''
    mem_group = Group.objects.get(name="member")
    sec_group = Group.objects.get(name='secretary')

    if created:
        # if user is in charge of societies, add to sec group
        if (instance.sec_societies.all()):
            instance.groups.add(sec_group)
        # if user is a member of a societies, add to mem group
        if (instance.mem_societies.all()):
            instance.groups.add(mem_group)
        return




@receiver(post_save, sender=User)
def generate_user_qrcode(sender, instance, created, **kwargs):
    ''' Generates a QRcode for each created user'''
    if created:
        qrcode_info = generate_qrcode(instance)
        instance.qrcode = qrcode_info
        instance.save()


@receiver(post_save, sender=Union)
def create_union_default_society(sender, instance, created, **kwargs):
    ''' Creates a default society for Union Created based on the unions_name'''
    if created:
        Society.objects.create(union=instance, name=instance.name)


# @receiver(m2m_changed, sender=User.sec_societies.through)
# def add_user_to_secretary_group(sender, **kwargs):
#     ''' assigns secretary user status to users added to a society as secretary '''
#     instance = kwargs.pop('instance', None)
#     action = kwargs.pop('action', None)
#     sec_group = Group.objects.get(name='secretary')
#     print('signal  ==> ', {**kwargs})

#     if (action == 'post_add'):
#         sec_societies = instance.sec_societies.all()
#         # if user is a secretary, add him to secretary group
#         print(sec_societies)
#         if sec_societies.count() > 0:
#             print('hia')
#             if sec_group not in instance.groups.all():
#                 instance.groups.add(sec_group)
#             return
#         # if he isn't don't add
#         instance.groups.remove(sec_group)

#     return




# TODO
# Currently a user's role can be known through user.groups and user.sec_societies
# It is better to check user's role through length of user.sec_societies. If it is greater than 0
# then user is a secretary, else he is a normal member
# 
