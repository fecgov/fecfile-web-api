# End to End Testing in Protractor

## Setup and Environment

By default, the URL confgiured in protractor.conf.js is http://localhost:4200/ so that it works 
out of the box in our CI environment. Most developers will want to modify this using an enviornment
variable:
```shell
export FECFILE_URL=http://localhost/
```
