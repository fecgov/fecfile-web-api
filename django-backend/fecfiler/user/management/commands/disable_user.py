from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Disable (or re-enable) a user with a given email.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str,
                help='The email address of the user to be disabled/enabled.')
        # add an --enable flag that defaults to false if not found
        parser.add_argument('-d', '--enable', action='store_true',
                help='Flag to instead (re-)enable the user.')

    def handle(self, *args, **options):
        User = get_user_model()

        try:
            user = User.objects.get(email=options['email'])
        except User.DoesNotExist:
            raise CommandError('User does not exist')

        user.is_active = options['enable']
        user.save()

        self.stdout.write(self.style.SUCCESS(
            f'The is_active flag for user [{user.email}] set to: {user.is_active}'
        ))
