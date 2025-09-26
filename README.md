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

When running docker compose you will need to be in the root directory of the project. The reason for this is that docker compose looks for docker-compose.yml to be in the same directory where it's run. You will also need at least 3GB of memory allocated for docker during the build.

### Run the fecfile web API application

You will need to define a DJANGO_SECRET_KEY.  Locally you can just add something like this your rc file:
`export DJANGO_SECRET_KEY="thisismykey"`

Spin up the containers:
```
docker compose up -d
```

By default EFO services (print/upload) will be mocked.
To integrate with EFO, set the following environment variables:

```
# Test EFO Services (for test filings):
export MOCK_EFO_FILING=False
export EFO_FILING_API_KEY="EFO_get_this_from_team_member"
```

*Note* - the default PRODUCTION_OPEN_FEC_API_KEY and STAGE_OPEN_FEC_API_KEY key has a very low rate limit -
for a better key, reach out to a team member or get one at https://api.open.fec.gov/developers/

Go to http://localhost:8080/ to see the API documentation

### Shut down the containers
```
docker compose down
```

### see all running containers
```
docker ps
```

### running commands in a running container
```
docker compose exec <container name> <command>
```

# Deployment (FEC team only)

[Deployment instructions](https://github.com/fecgov/fecfile-web-api/wiki/Deployment)

See also: [Technical Design](https://github.com/fecgov/fecfile-web-api/wiki/Technical-Design)

## Additional developer notes

See [Additional Developer Notes](https://github.com/fecgov/fecfile-web-api/wiki/Additional-Developer-Notes).
