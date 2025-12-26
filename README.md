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

## Profiling runbook (Silk)

- Enable Silk locally: `export FECFILE_SILK_ENABLED=1`
- Mode A (Silk + Cypress): `export FECFILE_PROFILE_WITH_LOCUST=0` (SILKY_ANALYZE_QUERIES True)
- Mode B (Silk + Locust + Cypress): `export FECFILE_PROFILE_WITH_LOCUST=1` (SILKY_ANALYZE_QUERIES False)
- First-time setup: `python manage.py migrate` and `python manage.py collectstatic --no-input`
- Clear logs: `python manage.py silk_clear_request_log`
- Export artifacts: `python manage.py silk_export_profile --run-id <id> --outdir silk`
- Cypress tagging runbook: https://github.com/fecgov/fecfile-web-app/blob/feature/2709-silk-e2e/front-end/cypress/docs/README.silk.cy.md
- Meta runbook (pre-flight + outputs): https://github.com/fecgov/fecfile-web-app/blob/feature/2709-silk-e2e/front-end/cypress/docs/README.silk.meta.md
- Locust + Silk notes: `performance-testing/README.md`

# Deployment (FEC team only)

[Deployment instructions](https://github.com/fecgov/fecfile-web-api/wiki/Deployment)

See also: [Technical Design](https://github.com/fecgov/fecfile-web-api/wiki/Technical-Design)

## Additional developer notes

Once the web API application is running, you may go to http://localhost:8080/ to see the API documentation.
