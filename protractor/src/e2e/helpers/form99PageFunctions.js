const form99Page = require('../pages/form99.page');

class form99PageFunctions {

 

    clickOnForm99Menu() {
        form99Page.form99menuitem.click();
        //expect(browser.getCurrentUrl()).toMatch('/dashboard');

    }

    
}

module.exports = form99PageFunctions;