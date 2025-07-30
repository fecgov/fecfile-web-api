from django.core.management.base import BaseCommand
from enum import Enum


class Levels(Enum):
    ERROR = 1
    SUCCESS = 2
    WARNING = 3
    NOTICE = 4
    SQL_FIELD = 5
    SQL_COLTYPE = 6
    SQL_KEYWORD = 7
    SQL_TABLE = 8
    HTTP_INFO = 9
    HTTP_SUCCESS = 10
    HTTP_REDIRECT = 11
    HTTP_NOT_MODIFIED = 12
    HTTP_BAD_REQUEST = 13
    HTTP_NOT_FOUND = 14
    HTTP_SERVER_ERROR = 15
    MIGRATE_HEADING = 16
    MIGRATE_LABEL = 17
    ERROR_OUTPUT = 18


class FECCommand(BaseCommand):
    command_name = "FECCommand"

    def handle(self, *args, **options):
        self.verbosity = options["verbosity"]
        try:
            self.log(f"STARTING {self.command_name} command", Levels.NOTICE)
            self.command(*args, **options)
            self.log(f"FINISHED {self.command_name} command", Levels.NOTICE)
        except Exception:
            self.log(f"FAILED to execute {self.command_name} command", Levels.ERROR)
            raise

    def command(self, *args, **options):
        """
        The actual logic of the command. Subclasses must implement
        this method.
        """
        raise NotImplementedError(
            "subclasses of FECCommand must provide a command() method"
        )

    def log(self, msg, level: Levels):
        match level:
            case Levels.ERROR:
                self.stderr.write(self.style.ERROR(msg))
            case Levels.SUCCESS:
                if self.verbosity > 0:
                    self.stdout.write(self.style.SUCCESS(msg))
            case Levels.WARNING:
                if self.verbosity > 0:
                    self.stdout.write(self.style.WARNING(msg))
            case Levels.NOTICE:
                if self.verbosity > 0:
                    self.stdout.write(self.style.NOTICE(msg))
            case Levels.SQL_FIELD:
                if self.verbosity > 0:
                    self.stdout.write(self.style.SQL_FIELD(msg))
            case Levels.SQL_COLTYPE:
                if self.verbosity > 0:
                    self.stdout.write(self.style.SQL_COLTYPE(msg))
            case Levels.SQL_KEYWORD:
                if self.verbosity > 0:
                    self.stdout.write(self.style.SQL_KEYWORD(msg))
            case Levels.SQL_TABLE:
                if self.verbosity > 0:
                    self.stdout.write(self.style.SQL_TABLE(msg))
            case Levels.HTTP_INFO:
                if self.verbosity > 0:
                    self.stdout.write(self.style.HTTP_INFO(msg))
            case Levels.HTTP_SUCCESS:
                if self.verbosity > 0:
                    self.stdout.write(self.style.HTTP_SUCCESS(msg))
            case Levels.HTTP_REDIRECT:
                if self.verbosity > 0:
                    self.stdout.write(self.style.HTTP_REDIRECT(msg))
            case Levels.HTTP_NOT_MODIFIED:
                if self.verbosity > 0:
                    self.stdout.write(self.style.HTTP_NOT_MODIFIED(msg))
            case Levels.HTTP_BAD_REQUEST:
                if self.verbosity > 0:
                    self.stdout.write(self.style.HTTP_BAD_REQUEST(msg))
            case Levels.HTTP_NOT_FOUND:
                if self.verbosity > 0:
                    self.stdout.write(self.style.HTTP_NOT_FOUND(msg))
            case Levels.HTTP_SERVER_ERROR:
                if self.verbosity > 0:
                    self.stdout.write(self.style.HTTP_SERVER_ERROR(msg))
            case Levels.MIGRATE_HEADING:
                if self.verbosity > 0:
                    self.stdout.write(self.style.MIGRATE_HEADING(msg))
            case Levels.MIGRATE_LABEL:
                if self.verbosity > 0:
                    self.stdout.write(self.style.MIGRATE_LABEL(msg))
            case Levels.ERROR_OUTPUT:
                if self.verbosity > 0:
                    self.stderr.write(self.style.ERROR_OUTPUT(msg))
