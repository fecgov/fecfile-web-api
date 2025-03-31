from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Disable (or re-enable) a user with a given email.'

    def add_arguments(self, parser):
        # require either a UUID or email
        id_arg = parser.add_mutually_exclusive_group(required=True)
        id_arg.add_argument('--uuid', type=str,
                help='The UUID of the user to be disabled/enabled.')
        id_arg.add_argument('--email', type=str,
                help='The email address of the user to be disabled/enabled.')
        # add an --enable flag that defaults to false if not found
        parser.add_argument('-e', '--enable', action='store_true',
                help='Flag to instead (re-)enable the user.')

    def handle(self, *args, **options):
        user_model = get_user_model()

        try:
            # if they use both arguments, prefer UUID
            if options['uuid'] is not None:
                user = user_model.objects.get(id=options['uuid'])
            else:
                user = user_model.objects.get(email=options['email'])
        except user_model.DoesNotExist:
            raise CommandError('User does not exist')

        user.is_active = options['enable']
        user.save()

        self.stdout.write(self.style.SUCCESS(
            f'The is_active flag for user {user.id} has been set to: {user.is_active}'
        ))
