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
    """Deploy to production if main branch is checked out and tagged."""
    if branch != 'main':
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
        print('The current configuration does not require a deployment to cloud.gov.')
        return None
    print(f'Detected space {space}')
    return space


DEPLOY_RULES = (
    ('prod', _detect_prod),
    ('stage', lambda _, branch: branch.startswith('release')),
    ('dev', lambda _, branch: branch == 'develop'),
)


def _login_to_cf(ctx, space):
    # Set api
    api = "https://api.fr.cloud.gov"
    ctx.run(f"cf api {api}", echo=True)
    # Authenticate
    user_var_name = f'$FEC_CF_USERNAME_{space.upper()}'
    pass_var_name = f'$FEC_CF_PASSWORD_{space.upper()}'

    login_command = f'cf auth "{user_var_name}" "{pass_var_name}"'
    result = ctx.run(login_command, echo=True, warn=True)
    if result.return_code != 0:
        print("\n\nError logging into cloud.gov.")
        print("Please check your authentication environment variables:")

        print(f"You must set the {user_var_name} and {pass_var_name} environment ")
        print("variables with space-deployer service account credentials")
        print("")
        print("If you don't have a service account, you can create one with the following commands:")
        print(f"   cf login -u [email-address] -o {ORG_NAME} -a api.fr.cloud.gov --sso")
        print(f"   cf target -o {ORG_NAME} -s {space}")
        print("   cf create-service cloud-gov-service-account space-deployer [my-service-account-name]")
        print("   cf create-service-key  [my-server-account-name] [my-service-key-name]")
        print("   cf service-key  [my-server-account-name] [my-service-key-name]")

        exit(1)


def _do_deploy(ctx, space):

    manifest_filename = f"manifest-{space}.yml"
    existing_deploy = ctx.run(f"cf app {APP_NAME}", echo=True, warn=True)
    print("\n")

    cmd = "push --strategy rolling" if existing_deploy.ok else "push"
    new_deploy = ctx.run(
        f"cf {cmd} {APP_NAME} -f {manifest_filename}",
        echo=True,
        warn=True,
    )
    return new_deploy


def _print_help_text():
    help_text = """
    Usage:
    invoke deploy [--space SPACE] [--branch BRANCH] [--login] [--help]

    --space SPACE    If provided, the SPACE space in cloud.gov will be targeted for deployment.
                     Either --space or --branch must be provided
                     Allowed values are dev, stage, and prod.


    --branch BRANCH  Name of the branch to use for deployment. Will auto-detect
                     the git branch in the current directory by default
                     Either --space or --branch must be provided

    --login          If this flag is set, deploy with attempt to login to a
                     service account specified in the environemnt variables
                     $FEC_CF_USERNAME_[SPACE] and $FEC_CF_PASSWORD_[SPACE]

    --help           If set, display help/usage text and exit

    """
    print(help_text)


def _rollback(ctx):
    print("Build failed!")
    # Check if there are active deployments
    app_guid = ctx.run(f"cf app {APP_NAME} --guid", hide=True, warn=True)
    app_guid_formatted = app_guid.stdout.strip()
    status = ctx.run(
        f'cf curl "/v3/deployments?app_guids={app_guid_formatted}&status_values=ACTIVE"',
        hide=True,
        warn=True,
    )
    active_deployments = (
        json.loads(status.stdout).get("pagination").get("total_results")
    )
    # Try to roll back
    if active_deployments > 0:
        print("Attempting to roll back any deployment in progress...")
        # Show the in-between state
        ctx.run(f"cf app {APP_NAME}", echo=True, warn=True)
        cancel_deploy = ctx.run(
            f"cf cancel-deployment {APP_NAME}", echo=True, warn=True
        )
        if cancel_deploy.ok:
            print("Successfully cancelled deploy. Check logs.")
        else:
            print("Unable to cancel deploy. Check logs.")


@task
def deploy(ctx, space=None, branch=None, login=False, help=False):
    """Deploy app to Cloud Foundry.
    Log in using credentials stored per environment
    like `FEC_CF_USERNAME_DEV` and `FEC_CF_PASSWORD_DEV`;
    Push to either `space` or the space detected from the name and tags
    of the current branch.
    Note: Must pass `space` or `branch` if repo is in detached HEAD mode,
    e.g. when running on Circle.

    Example usage: invoke deploy --space dev
    """

    if help:
        _print_help_text()
        exit(0)

    # Detect space
    repo = git.Repo(".")
    branch = branch or _detect_branch(repo)
    space = space or _detect_space(repo, branch)
    if space is None:
        # this is not an error condition, it just means the current space/branch is not
        # a candidate for deployment. Return successful exit code
        return sys.exit(0)

    if login:
        _login_to_cf(ctx, space)

    # Target space
    ctx.run(f"cf target -o {ORG_NAME} -s {space}", echo=True)

    # Set deploy variables
    with open(".cfmeta", "w") as fp:
        json.dump({"user": os.getenv("USER"), "branch": branch}, fp)

    new_deploy = _do_deploy(ctx, space)

    if not new_deploy.ok:
        _rollback(ctx)
        return sys.exit(1)

    ctx.run("cf apps", echo=True, warn=True)
    print(f"A new version of your application '{APP_NAME}' has been successfully pushed!")

    # Needed for CircleCI
    return sys.exit(0)
