import { browser, by, element } from 'protractor';

export class LoginPage {
  navigateTo() {
    return browser.get('/');
  }

  getParagraphText() {
    return element(by.css('app-root h1')).getText();
  }

  getCommitteeIdLabel() {
    return element(by.css('label[for=login-committee-id]')).getText();
  }

  getForgotCommitteeIdLink() {
    return element(by.css('.forgot-committee-id-link'));
  }

  getCommitteeIdInput() {
    return element(by.css('.login-committee-id'));
  }

  getCommitteeIDInputError() {
    return browser.driver.findElement(by.css('.error__committee-id'));
  }

  getPasswordLabel() {
    return element(by.css('label[for=login-password]')).getText();
  }

  getForgotPasswordLink() {
    return element(by.css('.forgot-password-link'));
  }

  getPasswordInput() {
    return element(by.css('.login-password'));
  }

  getPasswordInputError() {
    return browser.driver.findElement(by.css('.error__password-error'));
  }

  getLoginBtn() {
    return element(by.css('.login__btn'));
  }

  getNeedToRegisterLink() {
    return element(by.css('.need-to-register-link'));
  }

  fillInvalidCredentials() {
    let testCredentials = {
      committeeId: 'test',
      password: 'test'
    };

    element(by.css('.login-committee-id')).sendKeys(testCredentials.committeeId);
    element(by.css('.login-password')).sendKeys(testCredentials.password);
  }

  getInvalidCredentialsError() {
    return element(by.css('.error'));
  }

  fillValidCredentials() {
    let testCredentials = {
      email: 'test@fec.gov',
      committeeId: 'C00601211',
      password: 'test'
    };

    element(by.css('.login-email-id')).sendKeys(testCredentials.email);
    element(by.css('.login-committee-id')).sendKeys(testCredentials.committeeId);
    element(by.css('.login-password ')).sendKeys(testCredentials.password);
  }

  getTwoFactorInstruction() {
    return  element(by.xpath("//div[@class='title-front-sub']"));
  }

  getTwoFactorEmailRadioButton() {
    return element(by.id('email'));
  }

  getTwoFactorSubmitButton() {
    return element(by.xpath("//button[contains(.,'Submit')]"))
  }

  getTwoFactorSecurityTextBox() {
    return element(by.xpath("//input[@formcontrolname = 'securityCode']"));
  }

  getTwoFactorSecurtySubmitButton() {
    return element(by.xpath("//button[contains(.,'Next')]"));
  }

  getUsageWarningContinutButton() {
    return element(by.xpath("//button[contains(.,'Continue')]"))
  }
}
