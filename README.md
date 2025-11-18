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

You can find the set up instructions for the backend of this project in our [wiki](https://github.com/fecgov/fecfile-web-api/wiki/Local-Setup).

## Local testing

Local testing instructions can also be found within the [wiki](https://github.com/fecgov/fecfile-web-api/wiki/Local-Testing).

### Running unit tests locally
Drop into the API container with:
```
docker exec -it fecfile-api bash -H
```

You can then run unit tests with:
```
python3 manage.py test [-k <test name>]
```

### Monitoring containers
```
docker stats
```

#### Viewing logs
View logs for a single container:
```
docker logs <container ID> [-f]
```

View logs for all containers:
```
docker compose logs [-f]
```

To view only the error logs:
```
docker logs <container ID> [-f] 1>/dev/null
```

To view only the access logs:
```
docker logs <container-id> [-f] 2>/dev/null
```

The `-f` (follow) flag causes the command to continue to output log messages as they occur until the user issues a break.


# Deployment (FEC team only)

[Deployment instructions](https://github.com/fecgov/fecfile-web-api/wiki/Deployment)

See also: [Technical Design](https://github.com/fecgov/fecfile-web-api/wiki/Technical-Design)

## Additional developer notes

Once the web API application is running, you may go to http://localhost:8080/ to see the API documentation.

See [Additional Developer Notes](https://github.com/fecgov/fecfile-web-api/wiki/Additional-Developer-Notes).
