#!/usr/bin/env bash

GIT_DIR=$(git rev-parse --git-dir)

set -e

if ! git secrets --list | grep -q "patterns" ;
then
    printf "Commit failure\n\ngit secrets is not installed or has no installed patterns.  Have you run the API repo's install script?\n"
    exit 1
fi

git secrets --pre_commit_hook -- "$@";

# As of writing this script, these are the git config exceptions necessary to pass the git secrets check
#
# 	allowed = \\[https://amaral\\.northwestern\\.edu/resources/guides/pyenv-tutorial\\]\\(https://amaral\\.northwestern\\.edu/resources/guides/pyenv-tutorial\\)
# 	allowed = ENV POSTGRES_PASSWORD=postgres
# 	allowed = expected_params = \\{\"api_key\": \"FAKE-KEY\"\\}
# 	allowed = env.get_credential\\(\"DJANGO_SECRET_KEY\", get_random_string\\(50\\)\\)
# 	allowed = \"/api/v1/web-services/dot-fec/\", \\{\"report_id\": report.id, \"password\": \"123\"\\}