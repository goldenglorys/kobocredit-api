from django.core.management.base import BaseCommand
from core.models import User
from core.utils import generate_qrcode

def populate_qrcode():
    users = User.objects.filter(qrcode={})
    for user in users:
        print ('Doing for ', user.username)
        qrcode_info = generate_qrcode(user)
        user.qrcode = qrcode_info
        user.save()

    return


class Command(BaseCommand):
    def handle(self, **options):
        populate_qrcode()
