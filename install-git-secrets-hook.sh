#!/bin/bash
#
# This utility script configures the git-secrets pre-commit hook globally
# so that all repositories cloned to your computer will run the per-commit
# scan for sensitive data. Although discouraged, you may install git secrets
# locally to the fecfile-online repository only by running this script using
# the "--local" command line switch.
#
# To run, first install AWS git-secret utility in your PATH so it can
# be run at the command line:
# https://github.com/awslabs/git-secrets#installing-git-secrets
#
# Once you have git-secrets installed locally, run this script in the
# root directory of your cloned fecfile-online repo to install the
# pre-commit hooks globally.
#
# See git-secrets README for more features:
# https://github.com/awslabs/git-secrets#readme
#
# NOTE: When committing to the repo and getting blocked by a false positive,
# there are  2 options to fix the commit: (1) skip validation by adding the
# --no-verify switch to your commit or merge (https://github.com/awslabs/git-secrets#skipping-validation)
# or (2) Add an "allowed" rule to let the commit pass based on the file name
# and line number output by the rule that flagged the possible secret.
# e.g. git secrets --add --allowed --literal '.circleci/config.yml:82'
#

# Install the git hooks for the repostory
GLOBAL_TOKEN=
if [ "$1" == "--local" ] || [ "$1" == "-l" ]; then
    # Install only to the fecfile-online repo.
    git secrets --install
else
    # Install globally by modifying the ~/.gitconfig file and creating
    # the ~/.git-support/hooks directory.
    git secrets --install ${HOME}/.git-support
    git config --global core.hooksPath ${HOME}/.git-support/hooks
    GLOBAL_TOKEN="--global"
fi
git secrets --register-aws $GLOBAL_TOKEN

# Add general custom rules
git secrets --add $GLOBAL_TOKEN '(dbpasswd|dbuser|dbname|dbhost|api_key|apikey|key|api|password|user|guid|hostname|pw|auth)\s*[=:]\s*['"'"'0-9a-zA-Z_\/+!{}=-]{4,120}'
git secrets --add $GLOBAL_TOKEN '(DBPASSWD|DBUSER|DBNAME|DBHOST|API_KEY|APIKEY|KEY|API|PASSWORD|USER|GUID|HOSTNAME|PW|AUTH)\s*[=:]\s*['"'"'0-9a-zA-Z_\/+!{}=-]{4,120}'
git secrets --add $GLOBAL_TOKEN '(aws_access_key_id|aws_secret_access_key)\s*[=:]\s*['"'"'0-9a-zA-Z\/+]{20,42}'
git secrets --add $GLOBAL_TOKEN '(AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY)\s*[=:]\s*['"'"'0-9a-zA-Z\/+]{20,42}'

# Add rules targeting docker files
git secrets --add --literal $GLOBAL_TOKEN 'POSTGRES_PASSWORD'
git secrets --add --allowed --literal $GLOBAL_TOKEN 'POSTGRES_PASSWORD: postgres'

# Add rules targeting django-backend/fecfiler/settings.py
git secrets --add --literal $GLOBAL_TOKEN 'OTP_DEFAULT_PASSCODE'
git secrets --add --allowed --literal $GLOBAL_TOKEN 'OTP_DEFAULT_PASSCODE = "111111"'
git secrets --add --literal $GLOBAL_TOKEN 'API_LOGIN'
git secrets --add --allowed --literal $GLOBAL_TOKEN 'API_LOGIN = os.environ.get('"'"'API_LOGIN'"'"', None)'
git secrets --add --literal $GLOBAL_TOKEN 'API_PASSWORD'
git secrets --add --allowed --literal $GLOBAL_TOKEN 'API_PASSWORD = os.environ.get('"'"'API_PASSWORD'"'"', None)'
git secrets --add --literal $GLOBAL_TOKEN 'SECRET_KEY'
git secrets --add --allowed --literal $GLOBAL_TOKEN 'SECRET_KEY = '"'"'!0)(sp6(&$=_70&+_(zogh24=)@5&smwtuwq@t*v88tn-#m=)z'"'"''
git secrets --add --literal $GLOBAL_TOKEN ''"'"'USER'"'"''
git secrets --add --allowed --literal $GLOBAL_TOKEN ''"'"'USER'"'"': os.environ.get('"'"'FECFILE_DB_USER'"'"', '"'"'postgres'"'"')'
git secrets --add --literal $GLOBAL_TOKEN ''"'"'PASSWORD'"'"''
git secrets --add --allowed --literal $GLOBAL_TOKEN ''"'"'PASSWORD'"'"': os.environ.get('"'"'FECFILE_DB_PASSWORD'"'"', '"'"'postgres'"'"')'
git secrets --add --literal $GLOBAL_TOKEN 'AWS_SECRET_ACCESS_KEY'
git secrets --add --allowed --literal $GLOBAL_TOKEN 'AWS_SECRET_ACCESS_KEY = os.environ.get('"'"'SECRET_KEY'"'"', None)'

# Add rules to allow specific safe files that don't pass the above rule screens.
git secrets --add --allowed --literal $GLOBAL_TOKEN 'install-git-secrets-hook.sh:'
