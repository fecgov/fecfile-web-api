let form99PageFunctions = require('../helpers/form99PageFunctions');
let LoginPageFunctions = require('../helpers/LoginPageFunctions');


describe('Form99 Test Suite',function(){

    beforeAll(function(done){
       // console.log('Hello beforeAll..');
        //browser.get('http://35.172.199.97/');
       // browser.restart();
        browser.get('http://35.172.199.97/');
        done();
    });

    beforeEach(function(done){
        //console.log("Hello beforEach");
        browser.waitForAngular();
        browser.sleep(5000);
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

    it('Click on Form99',function(){
        new LoginPageFunctions().Login('C01234567','test');
        browser.waitForAngular();
        new form99PageFunctions().clickOnForm99Menu();
    });

    it('Test Logout',function(){
        new LoginPageFunctions().Logout();
    });

   
    
});