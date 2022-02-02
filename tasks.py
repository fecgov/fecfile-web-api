import os
import json
import git
import sys
import cfenv

from invoke import task

env = cfenv.AppEnv()

APP_NAME = "fecfile-web-api"
ORG_NAME = "fec-fecfileonline-prototyping"


def _detect_prod(repo, branch):
    """Deploy to production if master is checked out and tagged."""
    if branch != 'master':
        return False
    try:
        # Equivalent to `git describe --tags --exact-match`
        repo.git().describe('--tags', '--exact-match')
        return True
    except git.exc.GitCommandError:
        return False


def _resolve_rule(repo, branch):
    """Get space associated with first matching rule."""
    for space, rule in DEPLOY_RULES:
        if rule(repo, branch):
            return space
    return None


def _detect_branch(repo):
    try:
        return repo.active_branch.name
    except TypeError:
        return None


def _detect_space(repo, branch=None):
    """Detect space from active git branch.

    :param str branch: Optional branch name override
    :returns: Space name if space is detected and confirmed, else `None`
    """
    space = _resolve_rule(repo, branch)
    if space is None:
        print('No space detected')
        return None
    print('Detected space {space}'.format(**locals()))
    return space


DEPLOY_RULES = (
    ('prod', _detect_prod),
    ('stage', lambda _, branch: branch.startswith('release')),
    ('dev', lambda _, branch: branch == 'develop'),
)


@task
def deploy(ctx, space=None, branch=None, login=None):
    """Deploy app to Cloud Foundry. Log in using credentials stored in
    `FEC_CF_USERNAME` and `FEC_CF_PASSWORD`; push to either `space` or the space
    detected from the name and tags of the current branch. Note: Must pass `space`
    or `branch` if repo is in detached HEAD mode, e.g. when running on Travis.
    """
    # Detect space
    repo = git.Repo('.')
    branch = branch or _detect_branch(repo)
    space = space or _detect_space(repo, branch)
    if space is None:
        return

    # Use production settings
    ctx.run(
        'cd django-backend && DJANGO_SETTINGS_MODULE=fecfiler.settings.production',
        echo=True
    )

    if login == 'True':
        # Set api
        api = 'https://api.fr.cloud.gov'
        ctx.run('cf api {0}'.format(api), echo=True)
        # Authenticate
        ctx.run('cf auth "$FEC_CF_USERNAME_{0}" "$FEC_CF_PASSWORD_{0}"'.format(
            space.upper()), echo=True
        )

    # Target space
    ctx.run('cf target -o {0} -s {1}'.format(ORG_NAME, space), echo=True)

    # Set deploy variables
    with open('.cfmeta', 'w') as fp:
        json.dump({'user': os.getenv('USER'), 'branch': branch}, fp)

    # Deploy app
    existing_deploy = ctx.run('cf app {0}'.format(APP_NAME), echo=True, warn=True)
    print("\n")
    cmd = 'push --strategy rolling' if existing_deploy.ok else 'push'
    new_deploy = ctx.run('cf {0} {1} -f manifest-{2}.yml'.format(cmd, APP_NAME, space),
        echo=True,
        warn=True
    )

    if not new_deploy.ok:
        print("Build failed!")
        # Check if there are active deployments
        app_guid = ctx.run('cf app {0} --guid'.format(APP_NAME), hide=True, warn=True)
        app_guid_formatted = app_guid.stdout.strip()
        status = ctx.run('cf curl "/v3/deployments?app_guids={}&status_values=ACTIVE"'.format(app_guid_formatted), hide=True, warn=True)
        active_deployments = json.loads(status.stdout).get("pagination").get("total_results")
        # Try to roll back
        if active_deployments > 0:
            print("Attempting to roll back any deployment in progress...")
            # Show the in-between state
            ctx.run('cf app {0}'.format(APP_NAME), echo=True, warn=True)
            cancel_deploy = ctx.run('cf cancel-deployment {0}'.format(APP_NAME), echo=True, warn=True)
            if cancel_deploy.ok:
                print("Successfully cancelled deploy. Check logs.")
            else:
                print("Unable to cancel deploy. Check logs.")

        # Fail the build
        return sys.exit(1)

    print("\nA new version of your application '{0}' has been successfully pushed!".format(APP_NAME))
    ctx.run('cf apps', echo=True, warn=True)

    # Needed by CircleCI
    return sys.exit(0)
