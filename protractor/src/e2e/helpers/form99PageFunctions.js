const form99Page = require('../pages/form99.page');

class form99PageFunctions {

 

    clickOnForm99Menu() {
        form99Page.form99menuitem.click();
        form99Page.form99.click();

        //expect(browser.getCurrentUrl()).toMatch('/dashboard');
       // browser.waitForAngular();
       // browser.sleep(2000);
        

    }

   SelectReasonType(){
    form99Page.form99RadioButton.click();
    browser.waitForAngular();
    browser.sleep(1000);
    form99Page.from99ReasonRadioNext.click();
    browser.waitForAngular();
    browser.sleep(1000);
   }

   InputReasonTextAndSave() {
    form99Page.form99ReasonTextArea.sendKeys("Reason Text from Automation")
    browser.waitForAngular();
    browser.sleep(1000);
    form99Page.form99ReasonTextSave.click();
    browser.sleep(1000);
    browser.waitForAngular();
    form99Page.from99ReasonTextNext.click();
    browser.waitForAngular();
    browser.sleep(1000);
    form99Page.from99SigneeCertify.click();
    browser.sleep(1000);
    form99Page.from99SigneeSubmit.click();
    browser.sleep(2000);
   }

  

}

module.exports = form99PageFunctions;