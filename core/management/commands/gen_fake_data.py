import random
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from core.models import User, Account, Union, Society, Transaction

user_photos = [
    'https://randomuser.me/api/portraits/men/40.jpg'

]

def gen_fake_data():
    for x in range(1, 11):
        user, created = User.objects.get_or_create(username=f'member_{x}', email=f'member_{x}@gmail.com')
        secretary, _ = User.objects.get_or_create(
            username=f'secretary_{x}', email=f'secretary_{x}@gmail.com')
        
        user.set_password('starboy123')
        secretary.set_password('starboy123')

        user.first_name='Member'
        user.last_name= f'{x}'
        rand_int = random.choice(range(1,30))
        user.picture = f'https://randomuser.me/api/portraits/men/{rand_int}.jpg'

        secretary.first_name = 'Secretary'
        secretary.last_name = f'{x}'
        rand_int = random.choice(range(31, 60))
        secretary.picture = f'https://randomuser.me/api/portraits/men/{rand_int}.jpg'



        basic_group = Group.objects.get(name="member")
        secretary_group = Group.objects.get(name="secretary")
        user.groups.add(basic_group)
        if 'secretary' in secretary.username:
            secretary.groups.add(secretary_group)

        user.save()
        secretary.save()
        print(f'Created user member_{x}, {user.picture}')
        print(f'Created user secretary_{x}, {secretary.picture}')
    

    return


class Command(BaseCommand):
    def handle(self, **options):
        gen_fake_data()
