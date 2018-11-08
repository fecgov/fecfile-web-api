module.exports = {
    loginusername: element(by.id('login-committee-id')),
    loginpassword: element(by.id('login-password')),
    loginbutton: element(by.xpath("//button[@type='submit']")),
    logout: element(by.xpath("//a[@ng-reflect-router-link='/logout']")),
    logoutdropdownmenu: element(by.id("dropdownMenu")),
    forgotcommitteeid: element(by.className("forgot-committee-id-link link")),
    forgotpassword: element(by.className("forgot-password-link link")),
    }