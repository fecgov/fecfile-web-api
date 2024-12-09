## About this project

The Federal Election Commission (FEC) is the independent regulatory agency
charged with administering and enforcing the federal campaign finance law.
The FEC has jurisdiction over the financing of campaigns for the U.S. House,
Senate, Presidency and the Vice Presidency.

This project will provide a web application for filling out FEC campaign
finance information. The project code is distributed across these repositories:

- [fecfile-web-app](https://github.com/fecgov/fecfile-web-app): this is the browser-based front-end developed in Angular
- [fecfile-web-api](https://github.com/fecgov/fecfile-web-api): RESTful endpoint supporting the front-end
- [fecfile-api-proxy](https://github.com/fecgov/fecfile-api-proxy): Reverse proxy for API for IP blocking and rate limiting
- [fecfile-validate](https://github.com/fecgov/fecfile-validate): data validation rules and engine

---

## Set up

### Prerequisites

Software necessary to run the application locally

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Docker basic usage.

When running docker-compose you will need to be in the root directory of the project. The reason for this is that docker-compose looks for docker-compose.yml to be in the same directory where it's run. You will also need at least 3GB of memory allocated for docker during the build.

### Run the fecfile web API application

`docker-compose up -d`

You should set the following environment variables in the shell where you are running 'docker-compose up -d'.
Proper values for the development variables are shown here as an example

```
export DATABASE_URL="postgres://postgres:postgres@db/postgres"
export FECFILE_TEST_DB_NAME="postgres"
export DJANGO_SECRET_KEY="If_using_test_db_use_secret_key_in_cloud.gov"
export FEC_API="https://api.open.fec.gov/v1/"
# Note - this API key has a very low rate limit -
# For a better key, reach out to a team member or get one at https://api.open.fec.gov/developers/
export FEC_API_KEY="DEMO_KEY"
```

By default EFO services will be mocked
To integrate with EFO, set the following environment variables:

```
# Test EFO Services (for test filings):
export MOCK_EFO=False
export FEC_FILING_API="EFO_get_this_from_team_member"
export FEC_FILING_API_KEY="EFO_get_this_from_team_member"
```

### Shut down the containers

`docker-compose down`

### see all running containers

`docker ps`

### running commands in a running container

`docker-compose exec <container name> <command>`

# Deployment (FEC team only)

[Deployment instructions...](https://github.com/fecgov/fecfile-web-api/wiki/Deployment)

## Technical Environment Plan

The fecfile-web-api is our system's backend while the fecfile-web-app is the single-page angular app. The fecfile-web-api is deployed as a cloud.gov application per environment (dev, stage, test, and prod). Each cloud.gov fecfile-web-api application has at least two instances running. Similarly, the fecfile-web-app is deployed as a cloud.gov application per environment (dev, stage, test, and prod). There are also at least two instances running per cloud.gov fecfile-web-app application.

The following events occur for fecfile-web-api and fecfile-web-app independently of each other:

- When a branch is merged into the develop branch, it is deployed to the dev environment on cloud.gov
  - The Dev environment is used for the bulk of sprint integration and QA testing
- When a release is cut (creating a release tag in git), that release is deployed to the stage environment on cloud.gov.
  - The Stage environment is used for final deployment preparation, integration testing, and final QA testing.
- When the release is merged into the main branch, it is deployed to the test and prod environments on cloud.gov
  - The Test environment will be used by alpha users.
  - The Production environment will be used by end users once the application launches.

## Additional developer notes

This section covers a few topics we think might help developers after setup.

### Git Secrets

Set up git secrets to protect oneself from committing sensitive information such as passwords to the repository.

- First install AWS git-secret utility in your PATH so it can be run at the command line: https://github.com/awslabs/git-secrets#installing-git-secrets
- Once you have git-secrets installed, run the fecfile-web-api/install-git-secrets-hook.sh shell script in the root directory of your cloned fecfile-web-api repo to install the pre-commit hooks.
  NOTE: The pre-commit hook is installed GLOBALLY by default so commits to all cloned repositories on your computer will be scanned for sensitive data. See the comments at the top of the script for local install options.
- See git-secrets README for more features: https://github.com/awslabs/git-secrets#readme

### Code formatting

[Black](https://github.com/psf/black) is the Python code formatter used on the project.

- Install using `pip install black`.
- If using vscode, add (or update) the following section of your settings.json to the following so that code is formatted on save:

```
"[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
}
```

- To format a specific file or directory manually, use `black <file_or_directory>`

### Commit local code changes to origin daily

As a best practice policy, please commit any feature code changes made during the day to origin each evening before signing off for the day.

### Google-style inline documentation

The project is using the Google Python Style Guide as the baseline to keep code style consistent across project repositories.
See here for comment style rules: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings

### Snyk security scanning

A Snyk online account has been set up for FEC to monitor the FECFile Online GitHub repositories. The management of vulnerability alerts will be handled as a weekly rotating task performed by a developer who will log into the [Snyk Dashboard](https://app.snyk.io/org/fecfile/projects) (Invitation link [here](https://app.snyk.io/invite/link/accept?invite=93042de6-4eca-4bb5-bf76-9c2e9f895e24&utm_source=link_invite&utm_medium=referral&utm_campaign=product-link-invite&from=link_invite)) and perform the following tasks:

1. Review the vulnerability reports for each of the FECFile Online GitHub repository.
2. Write up a ticket (1 for each vulnerable package, ok to combine per package if multiple found on the same day) to remediate the vulnerability.
3. Point and mark each ticket with the following tags: "security", "high priority".
4. Ticket title should contain the deadline (Critical/high: 30 days, Medium: 60 days, Low: 90 days)
5. Move each new ticket into the sprint that will be deployed before the deadline.
6. Update weekly assignment log with tickets created or "None".

The weekly assignment log can be found in the Google drive 🔒 [here](https://docs.google.com/spreadsheets/d/1SNMOyGS4JAKgXQ0RhhzoX7M2ib1vm14dD0LxWNpssP4) 🔒
