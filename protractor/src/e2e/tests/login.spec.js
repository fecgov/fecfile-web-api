let LoginPageFunctions = require('../helpers/LoginPageFunctions');

describe('Login Test Suite',function(){

    beforeAll(function(done){
        //console.log('Hello beforeAll..');
        browser.get('http://dev-fecfile.efdev.fec.gov/');
        done();
    });

    beforeEach(function(done){
       // console.log("Hello beforEach");
        browser.waitForAngular();
        done();
    });
    afterAll(function(done){
        //console.log('Hello afterAll..');
        done()
    });
    afterEach(function(done){
       // console.log('Hello afterEach..');
        browser.sleep(5000);
        done();
    })

    it('Test Login',function(){
        new LoginPageFunctions().Login('C00690222','test');
        //browser.waitForAngular();
    });

    it('Test Logout',function(){
        new LoginPageFunctions().Logout();
    });

    it('Test Blank Credentials',function(){
        new LoginPageFunctions().checkInvalidCredentialsdError('','');
    });

    it('Test Invalid CommitteeId',function(){
        
        new LoginPageFunctions().checkInvalidCredentialsdError('','invalidpassword');
    });

    it('Test Invalid Password',function(){
        new LoginPageFunctions().checkInvalidCredentialsdError('C00690222','');
    });

    it('Test Forgot CommitteeId',function(){
        new LoginPageFunctions().ForgotCommitteeId();
    });

    it('Test Forgot Password',function(){
        new LoginPageFunctions().ForgotPassword();
    });

    it('Test New User Registration',function(){
        new LoginPageFunctions().NewUserRegistration();
    });
 

    
});