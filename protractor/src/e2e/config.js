/*
read this file for more configuration options
https://github.com/angular/protractor/blob/master/lib/config.ts
*/

exports.config = {
  framework: 'jasmine2',
  directConnect: true, // this runs selenium server on the fly and it has faster execution + parallel execution efficiently
  //and tests are more stable with local server started instead of directConnection.
  baseUrl: 'http://localhost/',
  capabilities: {
    browserName: 'chrome',
    shardTestFiles: false,
    maxInstances: 1,
    chromeOptions: {
      args: [
        'disable-extensions',
        'disable-web-security',
        //'--start-fullscreen', // enable for Mac OS
        //'--headless', // start on background
        '--disable-gpu',
        '--window-size=2880,1800'
      ]
    },
    'moz:firefoxOptions': {
      args: ['--headless']
    }
  },
  jasmineNodeOpts: {
    defaultTimeoutInterval: 60000,
    isVerbose: true,
    showTiming: true,
    includeStackTrace: true,
    realtimeFailure: true,
    showColors: true
  },
  suites:{
    smoke: ['**/*.spec.js']
    //smoke: ['**/form99.spec.js' ]
   //smoke: ['**/login.spec.js']
  },
 
  onPrepare: function () {
    //browser.baseUrl
    browser.get(browser.baseUrl);
    var AllureReporter = require('jasmine-allure-reporter');
    jasmine.getEnv().addReporter(new AllureReporter());
    jasmine.getEnv().afterEach(function(done){
      browser.takeScreenshot().then(function (png) {
        allure.createAttachment('Screenshot', function () {
          return new Buffer(png, 'base64')
        }, 'image/png')();
        done();
      })
    });
  },
  beforeLaunch: ()=>{
    //browser u don't have this object at this point
  }
};