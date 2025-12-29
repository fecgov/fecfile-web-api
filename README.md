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

Set up instructions are found in the [wiki](https://github.com/fecgov/fecfile-web-api/wiki/Local-Setup), including [instructions specific to the API](https://github.com/fecgov/fecfile-web-api/wiki/Local-setup#running-the-backend-locally) and an [overview of Docker usage](https://github.com/fecgov/fecfile-web-api/wiki/Local-setup#docker-basic-usage). 

## Local testing

Local testing instructions can also be found within the [wiki](https://github.com/fecgov/fecfile-web-api/wiki/Local-Testing).

# Deployment (FEC team only)

[Deployment instructions](https://github.com/fecgov/fecfile-web-api/wiki/Deployment)

See also: [Technical Design](https://github.com/fecgov/fecfile-web-api/wiki/Technical-Design)

## Additional developer notes

Once the web API application is running, you may go to http://localhost:8080/ to see the API documentation.

## Silk profiling (local/dev)

Enable Silk locally by setting `FECFILE_SILK_ENABLED=1` and restart the API. The UI is available at
`/silk/` and only `/api/` requests with the `x-silk-profile: 1` header are recorded.

When running Cypress from `fecfile-web-app`, set `FECFILE_WEB_API_DIR` to this repo's
`django-backend` directory so the after-spec hook can call the exporter.

To export Cypress profiling summaries manually, run:

```
python manage.py silk_export --run-id <uuid> --spec <specname> --outdir silk-artifacts
```

Artifacts are written to `silk-artifacts/<run-id>/` (per-spec summaries plus `index.json` and
`summary.json` for the full run).
