from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ConectaGo.models import ClientProfile, ProfessionalProfile
from django.db import transaction

class Command(BaseCommand):
    help = 'Delete users by username along with their related profiles'

    def add_arguments(self, parser):
        parser.add_argument('usernames', nargs='+', type=str, help='Usernames to delete')

    def handle(self, *args, **options):
        usernames = options['usernames']
        for username in usernames:
            try:
                with transaction.atomic():
                    user = User.objects.get(username=username)
                    ClientProfile.objects.filter(user=user).delete()
                    ProfessionalProfile.objects.filter(user=user).delete()
                    user.delete()
                    self.stdout.write(self.style.SUCCESS(f'Successfully deleted user and profiles for: {username}'))
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'User not found: {username}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error deleting user {username}: {str(e)}'))
