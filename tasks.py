import os
import json
import git
import sys
import cfenv
import threading
import time

from invoke import task

env = cfenv.AppEnv()

APP_NAME = "fecfile-web-api"
MIGRATOR_APP_NAME = "fecfile-api-migrator"  # THE APP WITH THIS NAME WILL GET DELETED!
WEB_SERVICES_NAME = "fecfile-web-services"
SCHEDULER_NAME = "fecfile-scheduler"
PROXY_NAME = "fecfile-api-proxy"
ORG_NAME = "fec-fecfile"


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
        print("The current configuration does not require a deployment to cloud.gov.")
        return None
    print(f"Detected space {space}")
    return space


DEPLOY_RULES = (
    ("prod", lambda _, branch: branch == "main"),
    ("test", lambda _, branch: branch == "release/test"),
    ("stage", lambda _, branch: branch.startswith("release/sprint")),
    ("dev", lambda _, branch: branch == "feature/1957"),
)


def _login_to_cf(ctx, space):
    # Set api
    api = "https://api.fr.cloud.gov"
    ctx.run(f"cf api {api}", echo=True)
    # Authenticate
    user_var_name = f"$FEC_CF_USERNAME_{space.upper()}"
    pass_var_name = f"$FEC_CF_PASSWORD_{space.upper()}"

    login_command = f'cf auth "{user_var_name}" "{pass_var_name}"'
    result = ctx.run(login_command, echo=True, warn=True)
    if result.return_code != 0:
        print("\n\nError logging into cloud.gov.")
        print("Please check your authentication environment variables:")

        print(f"You must set the {user_var_name} and {pass_var_name} environment ")
        print("variables with space-deployer service account credentials")
        print("")
        print(
            "If you don't have a service account, you can create one with the"
            " following commands:"
        )
        print(f"   cf login -u [email-address] -o {ORG_NAME} -a api.fr.cloud.gov --sso")
        print(f"   cf target -o {ORG_NAME} -s {space}")
        print(
            "   cf create-service cloud-gov-service-account space-deployer"
            " [my-service-account-name]"
        )
        print("   cf create-service-key  [my-server-account-name] [my-service-key-name]")
        print("   cf service-key  [my-server-account-name] [my-service-key-name]")

        exit(1)


def _do_deploy(ctx, space, app):
    manifest_filename = f"manifests/manifest-{space}.yml"
    existing_deploy = ctx.run(f"cf app {app}", echo=True, warn=True)
    print("\n")

    cmd = "push --strategy rolling" if existing_deploy.ok else "push"
    new_deploy = ctx.run(
        f"cf {cmd} {app} -f {manifest_filename}",
        echo=True,
        warn=True,
    )
    return new_deploy


def _print_help_text():
    help_text = """
    Usage:
    invoke deploy [--space SPACE] [--branch BRANCH] [--login] [--help]

    --space SPACE    If provided, the SPACE space in cloud.gov will be targeted
                     for deployment.
                     Either --space or --branch must be provided
                     Allowed values are dev, stage, test, and prod.


    --branch BRANCH  Name of the branch to use for deployment. Will auto-detect
                     the git branch in the current directory by default
                     Either --space or --branch must be provided

    --login          If this flag is set, deploy with attempt to login to a
                     service account specified in the environemnt variables
                     $FEC_CF_USERNAME_[SPACE] and $FEC_CF_PASSWORD_[SPACE]

    --help           If set, display help/usage text and exit

    """
    print(help_text)


def _rollback(ctx, app):
    print("Build failed!")
    # Check if there are active deployments
    app_guid = ctx.run(f"cf app {app} --guid", hide=True, warn=True)
    app_guid_formatted = app_guid.stdout.strip()
    status = ctx.run(
        f'cf curl "/v3/deployments?app_guids={app_guid_formatted}&status_values=ACTIVE"',
        hide=True,
        warn=True,
    )
    active_deployments = json.loads(status.stdout).get("pagination").get("total_results")
    # Try to roll back
    if active_deployments > 0:
        print("Attempting to roll back any deployment in progress...")
        # Show the in-between state
        ctx.run(f"cf app {app}", echo=True, warn=True)
        cancel_deploy = ctx.run(f"cf cancel-deployment {app}", echo=True, warn=True)
        if cancel_deploy.ok:
            print("Successfully cancelled deploy. Check logs.")
        else:
            print("Unable to cancel deploy. Check logs.")


def _delete_migrator_app(ctx, space):
    print("Deleting migrator app...")

    existing_migrator_app = ctx.run(f"cf app {MIGRATOR_APP_NAME}", echo=True, warn=True)
    if not existing_migrator_app.ok:
        print("No migrator app detected.  There is nothing to delete.")
        return True

    if MIGRATOR_APP_NAME == APP_NAME:
        print(f"Possible error: could result in deleting main app - {APP_NAME}")
        print("Canceling migrator app deletion attempt.")
        return False

    delete_app = ctx.run(f"cf delete {MIGRATOR_APP_NAME} -f", echo=True, warn=True)
    if not delete_app.ok:
        print("Failed to delete migrator app.")
        print(f'Stray migrator app remains on {space}: "{MIGRATOR_APP_NAME}"')
        return False
    print("Migrator app deleted successfully.")
    return True


def _check_for_migrations(ctx, space):
    print("Checking if migrator app is up...")
    app_guid = ctx.run(f"cf app {MIGRATOR_APP_NAME} --guid", hide=True, warn=True)
    if not app_guid.ok:
        print("Migrator not found, ok to continue.")
        return False

    print("Migrator app found!")
    app_guid_formatted = app_guid.stdout.strip()

    print("Checking if migrator app is running migrations...\n")
    ctx.run(f"cf tasks {MIGRATOR_APP_NAME}", hide=False, warn=True)
    task_status = ctx.run(
        f'cf curl "/v3/apps/{app_guid_formatted}/tasks?states=RUNNING"',
        hide=True,
        warn=True,
    )
    active_tasks = json.loads(task_status.stdout).get("pagination").get("total_results")

    if active_tasks > 0:
        print("\nMigrator app is running migrations.\n")
        return True

    print("Migrator app is up, but not running migrations\n")
    return True


def _print_recent_migrator_logs(ctx):
    statements_to_log = "\\|".join(
        [
            "Apply all migrations:",
            "Running migrations:",
            "No migrations to apply\\.",
            "Applying .*\\.\\.\\.",
            "MIGRATION_LOG",
        ]
    )
    grep_filter = f"grep 'Run Migrations' | grep '{statements_to_log}'"
    ctx.run(
        f"cf logs --recent {MIGRATOR_APP_NAME} | {grep_filter}",
        echo=True,
        warn=True,
    )


def _print_migrations_summary(ctx):
    task = "django-backend/manage.py showmigrations --list --traceback --verbosity 3"
    show_migrations_cmd = ctx.run(
        f"cf rt {MIGRATOR_APP_NAME} --command '{task}' --name 'Migration Summary' --wait",
        echo=True,
        warn=True,
    )
    time.sleep(3)

    if not show_migrations_cmd.ok:
        print("Failed to run showmigrations command.  Check logs.")
        return False
    ctx.run(
        f"cf logs --recent {MIGRATOR_APP_NAME} | grep 'Migration Summary'",
        echo=True,
        warn=True,
    )
    return True


def _run_migrations(ctx, space):
    print("Running migrations...")

    # Start migrator app
    manifest_filename = f"manifests/manifest-{space}.yml"
    migrator = ctx.run(
        f"cf push {MIGRATOR_APP_NAME} -f {manifest_filename}",
        echo=True,
        warn=True,
    )
    if not migrator.ok:
        print("Failed to spin up migrator app.  Check logs.")
        return False

    # Heartbeat thread
    # Prints an in-progress message every minute to keep circleci step from timing out
    heartbeat_stop_event = threading.Event()

    def heartbeat():
        minutes_elapsed = 0
        while not heartbeat_stop_event.is_set():
            minutes_elapsed += 1
            print(f"Migration in progress... ({minutes_elapsed} minutes elapsed)")

            # Check every second for the stop event
            for _ in range(60):
                if _ != 0 and _ % 10 == 0:
                    _print_recent_migrator_logs(ctx)
                if heartbeat_stop_event.is_set():
                    _print_recent_migrator_logs(ctx)
                    break
                time.sleep(1)

    heartbeat_thread = threading.Thread(target=heartbeat)
    heartbeat_thread.daemon = True  # Daemonize thread to allow program exit
    heartbeat_thread.start()

    # Run migrations
    task = "django-backend/manage.py migrate --no-input --traceback --verbosity 3"
    migrations = ctx.run(
        f"cf rt {MIGRATOR_APP_NAME} --command '{task}' --name 'Run Migrations' --wait",
        echo=True,
        warn=True,
    )

    # Stop heartbeat
    heartbeat_stop_event.set()
    heartbeat_thread.join()

    if not migrations.ok:
        print("Failed to run migrations.  Check logs.")
        return False

    print("Migration process has finished successfully.")
    return True


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
    ctx.run("cf version", echo=True)

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

    # Check for running migations
    migrations_in_progress = _check_for_migrations(ctx, space)

    if migrations_in_progress:
        print("Not clear to safely run migrations, cancelling deploy.\n")
        print("Check logs for more information.\n")
        print("Retry when migrations have finished.")
        sys.exit(1)

    # Runs migrations
    # tasks.py does not continue until the migrations task has completed
    migrations_successful = _run_migrations(ctx, space)
    if not migrations_successful:
        print("Migrations failed.")
        print("Check logs for more information.\nCanceling deploy...")
        _print_migrations_summary(ctx)
        sys.exit(1)

    for app in [APP_NAME, WEB_SERVICES_NAME, SCHEDULER_NAME]:
        new_deploy = _do_deploy(ctx, space, app)
        if not new_deploy.ok:
            _rollback(ctx, app)
            _print_migrations_summary(ctx)
            return sys.exit(1)

    _print_migrations_summary(ctx)

    migrator_app_deleted = _delete_migrator_app(ctx, space)
    if not migrator_app_deleted:
        print("Failed to delete the migrator app.")
        print("Check logs for more information.\nCanceling deploy...")
        sys.exit(1)

    # set any in-progress report submissions to FAILED
    task = "django-backend/manage.py fail_open_submissions"
    task_name = "Fail non-terminal report submissions"
    ctx.run(
        f"cf rt {APP_NAME} --command '{task}' --name '{task_name}'",
        echo=True,
    )

    # Allow proxy to connect to api via internal route
    add_network_policy = ctx.run(
        f"cf add-network-policy {PROXY_NAME} {APP_NAME}",
        echo=True,
        warn=True,
    )
    if not add_network_policy.ok:
        print(
            "Unable to add network policy. Make sure the proxy app is deployed.\n"
            "For more information, check logs."
        )

        # Fail the build because the api will be down until the proxy can connect
        return sys.exit(1)

    # Needed for CircleCI
    return sys.exit(0)
