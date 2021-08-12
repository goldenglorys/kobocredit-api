from django.core.management.base import BaseCommand


def print_hello():
    return print(' Hello ')


class Command(BaseCommand):
    def handle(self, **options):
        print_hello()

