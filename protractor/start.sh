#cd to root dir of project
#npm install
#npm run webdriver-manager
#run our test
node .\node_modules\protractor\bin\protractor .\src\e2e\config.js
#node node_modules/.bin/protractor src/e2e/config.js
##if protractor is installed globally then 
#node protractor src/e2e/config.js

# how to take baseurl as argument
#node node_modules/.bin/protractor src/e2e/config.js --baseUrl="app url"
# how to execute diffrent suites
#node node_modules/.bin/protractor src/e2e/config.js --baseUrl="app url" --suite="name of the suite"

##allure reporter installation
#https://www.npmjs.com/package/jasmine-allure-reporter
# allure commands
#if allure is installed locally as dev dependecies 
# node_modules/.bin/allure serve <report-source-folder>
 .\node_modules\.bin\allure serve .\allure-results\
#if allure is installed globally
# allure serve <report-source-folder>

