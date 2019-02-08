let form99PageFunctions = require('../helpers/form99PageFunctions');
let LoginPageFunctions = require('../helpers/LoginPageFunctions');


describe('Opem protractor website',function(){

    beforeAll(function(done){
       // console.log('Hello beforeAll..');
       // browser.get('http://dev-fecfile.efdev.fec.gov/');
        done();
    });

    beforeEach(function(done){
        //console.log("Hello beforEach");
        browser.waitForAngular();
        done();
    });
    afterAll(function(done){
        //console.log('Hello afterAll..');
        done()
    });
    afterEach(function(done){
        //console.log('Hello afterEach..');
        done();
    })

    it('Open Form99',function(){
        new LoginPageFunctions().Login('C00690222','test');
        browser.waitForAngular();
        new form99PageFunctions().clickOnForm99Menu();
    });

    it('Select Form99 ReasonType',function(){
        new form99PageFunctions().SelectReasonType();
        browser.waitForAngular();
    });

    it('Input Form99 ReasonType Text',function(){
        new form99PageFunctions().InputReasonTextAndSave();

        browser.waitForAngular();
    });

    it('Test Logout',function(){
         new LoginPageFunctions().Logout();
     });

   
    
});