# nxg_fec
The Federal Election Commission (FEC) is the independent regulatory agency
charged with administering and enforcing the federal campaign finance law.
The FEC has jurisdiction over the financing of campaigns for the U.S. House,
Senate, Presidency and the Vice Presidency.

Federal campaign finance law covers three broad subjects:

Public disclosure of funds raised and spent to influence federal elections
Explore campaign finance data  

### Project Directory Structure
```
 nxg_fec
   ├── django-backend
   ├── front-end
   └── selenium
```
#### `/nxg_fec`
This is the projects root. It contains all of the necessary files and directories to locally run the application

### `/django-backend`

Contains all files and directories to build the API used by the front end. Written in python3 currently runs Django framework version 1.11.18

### `/front-end`

Angular driven front end that makes api calls to the back end

### `/selenium`

This directory contains a java driven testing application.

#### Prerequisites
Software necessary to run the application locally

Docker version 18.06.1-ce  
docker-compose version 1.22.0
nodejs version 10.7.0
npm version 6.4.1

### Starting the application

To start the application in a unix environment run launcher.
The launcher will run through the following steps
- remove any angular dist and node_modules directories
- run npm install in the front-end directory
- shutdown any running docker instances
- remove all docker images
- build new docker images
- run docker containers in the background
- run django migrations
- print running containers.

### docker basic usage.
when running docker-compose you will need to be in the root directory of the project. The reason for this is that docker-compose looks for docker-compose.yml to be in the same directory where it's run. You will also need at least 3GB of memory allocated for docker during the build. 

# Build the application
` docker-compose build `
# Run the containers after being built
`docker-compose up --build`

You should set the following environment variables in the shell where you are running 'docker-compose up'.
Proper values for the development variables are shown here as an example
```
export FECFILE_DB_HOST=db
export FECFILE_DB_USERNAME=postgres
export FECFILE_DB_PASSWORD=postgres
export FECFILE_DB_NAME=postgres
```

# Shut down the containers
` docker-compose down `
# see all running containers
`docker ps`
# running commands in a running container
`docker compose exec <container name> <command>`


Container structure
```
        _____________________
        | Angular front end |
        |   Port "80:80"    |
        ---------------------
                  |
        _____________________
        | Django backed API |
        | Port "8080:8080"  |
        ---------------------
                  |
        _______________________
        | PostgreSQL Database |
        | Port "5432:5432"    |
        -----------------------
```

# Git Secrets
Set up git secrets to protect oneself from committing sensitive information
such as passwords to the repository.
- First install AWS git-secret utility in your PATH so it can be run at the
command line: https://github.com/awslabs/git-secrets#installing-git-secrets
- Once you have git-secrets installed, run the
fecfile-online/install-git-secrets-hook.sh shell script in the root
directory of your cloned fecfile-online repo to install the pre-commit hooks.
NOTE: The pre-commit hook is installed GLOBALLY by default so commits to all
cloned repositories on your computer will be scanned for sensitive data. See
the comments at the top of the script for local install options.
- See git-secrets README for more features:
https://github.com/awslabs/git-secrets#readme