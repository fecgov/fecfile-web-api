# Mock Open FEC

A module to mock responses from OpenFEC with test data.

## Usage

An example of it's usage is in the openfec module's query_filings view:

```
def query_filings(self, request):
        query = request.query_params.get("query")
        form_type = request.query_params.get("form_type")
        if settings.MOCK_OPENFEC_REDIS_URL:
            # instead, get results from mock query_filing method
            #            |
            #            v
            response = query_filings(query, form_type)
            #            ^
            #            |
        else:
            # actually make request to openfec
```

## Setup

If `FLAG__COMMITTEE_DATA_SOURCE` is not set to `REDIS`, everything will hit openfec normally

Currently, the only backing is redis. Setting this to `REDIS` will automatically
configure `MOCK_OPENFEC_REDIS_URL` to the `REDIS_URL`
`FLAG__COMMITTEE_DATA_SOURCE = "REDIS"`

# Local Development

`MOCK_OPENFEC` is set to `REDIS` in the docker-compose.yml already, and the Dockerfile runs the load_committee_data command, so nothing is needed to use what's in committee_accounts.json.

If you want to change the data in the redis cache, you can modify `fecfiler/mock_openfec/management/commands/committee_data.json`, then from your docker instance's shell (I use `docker exec -it fecfile-api /bin/bash`) call `python manage.py load_committee_data`. This will load whatever you have in committee_data.json into redis to be used in this module

# Deployed Instances

Our deployed instaces work much the same. The difference is that when we load data into redis, we read it from s3. This means we can change the mock committee data by uploading a json file to the environment's s3 bucket and running the load_committee_data command with cloud foundry. This looks like:

```aws s3 cp committee-data.json s3://<bucket>/mock_committee_data.json --profile dev
cf rt fecfile-web-api --command "python django-backend/manage.py load_committee_data --s3" --name "load committee data"
```

Notice the `--s3` flag on the load_commmittee_data command

Here is documentation for provisioning yourself an access key to s3: https://cloud.gov/docs/services/s3/#interacting-with-your-s3-bucket-from-outside-cloudgov DO NOT use the same key the application is using to access s3. Provision one for yourself for tracability
You can get the aws cli here: https://aws.amazon.com/cli/
I'd recommend using `aws configure --profile <profile-name-for-environemnt>` to configure your credentials
