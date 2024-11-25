#!/usr/bin/env bash

set -e

GIT_DIR=$(git rev-parse --git-dir)

if ! git secrets --list | grep -q "patterns" ;
then
    printf "Commit failure\n\ngit secrets failed to run.  Is it installed?\n"
    exit 1
fi

git secrets --pre_commit_hook -- "$@";

# secrets_list = subprocess.run(['git', 'secrets', '--list'], capture_output=True)

# secrets_config = str(secrets_list.stdout)
# if not ("patterns =" in secrets_config and "provider " in secrets_config):
#     print("Commit failure\n\ngit secrets has no installed patterns.  Have you run the local install script?", file=sys.stderr)
#     exit(1)

# scan_results = subprocess.run(['git', 'secrets', '--pre_commit_hook', '--', '"$@"'])

# print("Returning with return code:", scan_results.returncode)
# exit(scan_results.returncode)