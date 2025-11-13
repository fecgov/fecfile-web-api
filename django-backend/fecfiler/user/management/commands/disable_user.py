from django.core.management.base import BaseCommand, CommandError
from fecfiler.user.utils import get_user_by_email_or_id, update_user_active_state


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
        email_or_id = options.get("email", options.get("uuid", ""))
        user = get_user_by_email_or_id(email_or_id)
        update_user_active_state(user, options.get("enable", False))

        self.stdout.write(self.style.SUCCESS(
            f'The is_active flag for user [{user.id} | {user.email}] '
            f'set to: {user.is_active}'
        ))
