module.exports = {
    loginusername: element(by.id('login-committee-id')),
    loginpassword: element(by.id('login-password')),
    loginbutton: element(by.xpath("//button[@type='submit']")),
    logout: element(by.xpath("//a[contains(text(),'Logout')]")),
    logoutdropdownmenu: element(by.buttonText('Profile')),//element(by.className("btn btn-link dropdown-toggle")),
    forgotcommitteeid: element(by.className("forgot-committee-id-link link")),
    forgotpassword: element(by.className("forgot-password-link link")),
    }