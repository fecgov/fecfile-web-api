## About this project
The Federal Election Commission (FEC) is the independent regulatory agency
charged with administering and enforcing the federal campaign finance law.
The FEC has jurisdiction over the financing of campaigns for the U.S. House,
Senate, Presidency and the Vice Presidency.

This project will provide a web application for filling out FEC campaign
finance information. The project code is distributed across these repositories:
- [fecfile-web-app](https://github.com/fecgov/fecfile-web-app): this is the browser-based front-end developed in Angular
- [fecfile-web-api](https://github.com/fecgov/fecfile-web-api): RESTful endpoint supporting the front-end
- [fecfile-validate](https://github.com/fecgov/fecfile-validate): data validation rules and engine
- [fecfile-image-generator](https://github.com/fecgov/fecfile-image-generator): provides competed FEC forms in PDF format

---

## Set up

### Prerequisites
Software necessary to run the application locally

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)

### Docker basic usage.
When running docker-compose you will need to be in the root directory of the project. The reason for this is that docker-compose looks for docker-compose.yml to be in the same directory where it's run. You will also need at least 3GB of memory allocated for docker during the build.

### Run the front-end application
`docker-compose up -d`

You should set the following environment variables in the shell where you are running 'docker-compose up -d'.
Proper values for the development variables are shown here as an example
```
export DATABASE_URL = "postgres://postgres:postgres@0.0.0.0/postgres"
export FECFILE_TEST_DB_NAME = "postgres"
export SECRET_KEY = "If_using_test_db_use_secret_key_in_cloud.gov"
```
### Shut down the containers
`docker-compose down`
### see all running containers
`docker ps`
### running commands in a running container
`docker-compose exec <container name> <command>`


# Deployment (FEC team only)

### Create a feature branch
* Developer creates a feature branch and pushes to `origin`:

    ```
    git checkout develop
    git pull
    git checkout -b feature/my-feature develop
    # Work happens here
    git push --set-upstream origin feature/my-feature
    ```

* Developer creates a GitHub PR when ready to merge to `develop` branch
* Reviewer reviews and merges feature branch into `develop` via GitHub
* [auto] `develop` is deployed to `dev`

### Create a release branch
* Developer creates a release branch and pushes to `origin`:

    ```
    git checkout develop
    git pull
    git checkout -b release/sprint-# develop
    git push --set-upstream origin release/sprint-#
    ```

### Create and deploy a hotfix
* Developer makes sure their local main and develop branches are up to date:

   ```
   git checkout develop
   git pull
   git checkout main
   git pull
   ```

* Developer creates a hotfix branch, commits changes, and **makes a PR to the `main` and `develop` branches**:

    ```
    git checkout -b hotfix/my-fix main
    # Work happens here
    git push --set-upstream origin hotfix/my-fix
    ```

* Reviewer merges hotfix/my-fix branch into `develop` and `main`
* [auto] `develop` is deployed to `dev`. Make sure the build passes before deploying to `main`.
* Developer deploys hotfix/my-fix branch to main using **Deploying a release to production** instructions below

### Deploying a release to production
* Developer creates a PR in GitHub to merge release/sprint-# branch into the `main` branch
* Reviewer approves PR and merges into `main`
* Check CircleCI for passing pipeline tests
* If tests pass, continue
* Delete release/sprint-# branch
* In GitHub, go to `Code -> tags -> releases -> Draft a new release`
* Publish a new release using tag sprint-#, be sure to Auto-generate release notes
* Deploy `sprint-#` tag to production


## Additional developer notes
This section covers a few topics we think might help developers after setup.

### Git Secrets
Set up git secrets to protect oneself from committing sensitive information such as passwords to the repository.
- First install AWS git-secret utility in your PATH so it can be run at the command line: https://github.com/awslabs/git-secrets#installing-git-secrets
- Once you have git-secrets installed, run the fecfile-web-api/install-git-secrets-hook.sh shell script in the root directory of your cloned fecfile-web-api repo to install the pre-commit hooks.
NOTE: The pre-commit hook is installed GLOBALLY by default so commits to all cloned repositories on your computer will be scanned for sensitive data. See the comments at the top of the script for local install options.
- See git-secrets README for more features: https://github.com/awslabs/git-secrets#readme

### Commit local code changes to origin daily
As a best practice policy, please commit any feature code changes made during the day to origin each evening before signing off for the day.

### Google-style inline documentation
The project is using the Google Python Style Guide as the baseline to keep code style consistent across project repositories.
See here for comment style rules: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
