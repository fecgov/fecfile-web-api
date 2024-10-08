# Devops

A module to support devops tasks for fecfile web api.

## Commands

This module contains several commands (and supporting utilities) to assist devops tasks:

### gen_and_stage_login_dot_gov_cert.py
This command is used to generate and stage the login dot gov cert.  The pk is stored in the credential service while the public cert is stored in s3.

This command can be executed as follows:
```
cf rt fecfile-web-api --command 'python django-backend/manage.py gen_and_stage_login_dot_gov_cert "<token>" <cf_space> <cf_creds_service_name>'
```

### install_login_dot_gov_cert.py
This command is used to install the staged the login dot gov cert.  This should be run after the public cert is uploaded via login.gov and activated.

This command can be executed as follows:
```
cf rt fecfile-web-api --command 'python django-backend/manage.py install_login_dot_gov_cert "<token>" <cf_space> <cf_creds_service_name>'
```

### backout_login_dot_gov_cert.py
This command is used to backout the login dot gov cert after the install cert command has been run.  This should be run only if we need to revert to the prior pk in the credential service.

This command can be executed as follows:
```
cf rt fecfile-web-api --command 'python django-backend/manage.py backout_login_dot_gov_cert "<token>" <cf_space> <cf_creds_service_name>'
```

### update_creds_service.py
This command is used to update the creds service with a json structure of key/value pairs.

This command can be executed as follows:
```
cf rt fecfile-web-api --command 'python django-backend/manage.py update_creds_service "<token>" <cf_space> <cf_creds_service_name> "<json_with_escaped_double_quotes_around_keys_and_values>"'
```

### gen_and_install_django_key.py
This command is used to generate and installed the Django secret key into the credential service.

This command can be executed as follows:
```
cf rt fecfile-web-api --command 'python django-backend/manage.py gen_and_install_django_key "<token>" <cf_space> <cf_creds_service_name>'
```

### clear_fallback_django_keys.py
This command is used to clear the fallback Django secret keys in the credential service.

This command can be executed as follows:
```
cf rt fecfile-web-api --command 'python django-backend/manage.py clear_fallback_django_keys "<token>" <cf_space> <cf_creds_service_name>'
```
