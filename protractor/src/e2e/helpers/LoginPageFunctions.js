const loginPage = require('../pages/login.page');

class LoginPageFunctions {

 

    Login(logincommitteeid,password) {

        loginPage.loginusername.clear().sendKeys(logincommitteeid);
        loginPage.loginpassword.clear().sendKeys(password);
        loginPage.loginbutton.click();
        browser.waitForAngular();
        //console.warn(browser.getCurrentUrl());
        expect(browser.driver.getCurrentUrl()).toMatch('/dashboard');

    }

    Logout() {

        loginPage.logoutdropdownmenu.click(); 
        loginPage.logout.click();
        var logouttext = element(by.className('logged-out-msg'));
        expect(logouttext.getText()).toBe('You have successfully logged out of the FEC eFile application.'); 
        loginPage.loginusername.clear();
        loginPage.loginpassword.clear();
    }


     checkInvalidCredentialsdError(logincommitteeid,password){
        
      

         if (logincommitteeid.length > 0){
            loginPage.loginusername.clear().sendKeys(logincommitteeid);
         }

         if (password.length > 0){
            loginPage.loginpassword.clear().sendKeys(password);
         }
        
         loginPage.loginbutton.click();
         var committeiderror = element(by.className('error__committee-id'));
         var passworderror = element(by.className('error__password-error'));
         
        
         

            $('error__committee-id').isPresent().then(function(result) {
                if ( result ) {
                    //Whatever if it is true (displayed)
                    expect(committeiderror.getText()).toBe('Please enter your committee id.'); 
                }
            });
          
            $('error__password-error').isPresent().then(function(result) {
                if ( result ) {
                    //Whatever if it is true (displayed)
                    expect(passworderror.getText()).toBe('Please enter your password.');
                }
            });
        

     }

     ForgotCommitteeId(){
        browser.ignoreSynchronization = false;

         element(by.className("forgot-committee-id-link link")).click().then(function () {
                   
             browser.sleep(1000);
            browser.getAllWindowHandles().then(function (handles) {
                var newWindowHandle = handles[1]; // this is your new window
                browser.switchTo().window(newWindowHandle).then(function () {
                    // fill in the form here
                    expect(browser.getCurrentUrl()).toMatch('https://www.fec.gov/data/');
                    browser.driver.close();
                    browser.switchTo().window(handles[0]);
                });
            });
        });
        
        browser.ignoreSynchronization = true;
        browser.waitForAngular();
        //browser.sleep(1000);
      }

     ForgotPassword(){
        

        browser.ignoreSynchronization = false;

        element(by.className("forgot-password-link link")).click().then(function () {
           
           browser.sleep(2000);
           browser.getAllWindowHandles().then(function (handles) {
               var newWindowHandle = handles[1]; // this is your new window
               browser.switchTo().window(newWindowHandle).then(function () {
                   // fill in the form here
                   expect(browser.getCurrentUrl()).toMatch('https://test-webforms.fec.gov/psa/index.htm');
                   browser.driver.close();
                   browser.switchTo().window(handles[0]);
               });
           });
       });
       browser.ignoreSynchronization = true;
    }

    NewUserRegistration(){
        browser.ignoreSynchronization = false;

        element(by.className("need-to-register-link link")).click().then(function () {
           
           browser.sleep(2000);
           browser.getAllWindowHandles().then(function (handles) {
               var newWindowHandle = handles[1]; // this is your new window
               browser.switchTo().window(newWindowHandle).then(function () {
                   // fill in the form here
                   expect(browser.getCurrentUrl()).toMatch('https://test-webforms.fec.gov/webforms/form1/index.htm');
                   browser.driver.close();
                   browser.switchTo().window(handles[0]);
               });
           });
       });
       browser.ignoreSynchronization = true;    
    }
}

module.exports = LoginPageFunctions;