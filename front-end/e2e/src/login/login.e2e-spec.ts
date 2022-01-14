import {browser, protractor} from 'protractor';
import { LoginPage } from './login.po';
import { DashboardPage } from '../dashboard/dashboard.po';

describe('contact page', () => {
  let page: LoginPage;

  beforeEach(() => {
    page = new LoginPage();
    //TODO: We need to workout why this is necessary to get protractor working on more than one app page
    browser.ignoreSynchronization = true;
  });


  describe('view contacts', () => {

    describe('login page links', () => {
      xit('link for forgot committee id should contain text `Forgot Committee ID`', () => {
        page.navigateTo();
        expect(page.getForgotCommitteeIdLink().getText()).toEqual('Forgot Committee ID');
      });

      xit('link for forgot committee id should go to `https://www.fec.gov/data/`', () => {
        page.navigateTo();
        expect(page.getForgotCommitteeIdLink().getAttribute('href')).toEqual('https://www.fec.gov/data/');
      });

      it('link for forgot password should contain text `Forgot Password`', () => {
        page.navigateTo();
        expect(page.getForgotPasswordLink().getText()).toMatch('Forgot Password');
      });

      xit('link for forgot password should go to `https://test-webforms.fec.gov/psa/index.htm`', () => {
        page.navigateTo();
        expect(page.getForgotPasswordLink().getAttribute('href')).toEqual('https://test-webforms.fec.gov/psa/index.htm');
      });

      xit('link for do you need to register should contain text `Do you need to register your committee?`', () => {
        page.navigateTo();
        expect(page.getNeedToRegisterLink().getText()).toEqual('Do you need to register your committee?');
      });

      xit('link for do you need to register should go to `https://test-webforms.fec.gov/webforms/form1/index.htm`', () => {
        page.navigateTo();
        expect(page.getNeedToRegisterLink().getAttribute('href')).toEqual('https://test-webforms.fec.gov/webforms/form1/index.htm');
      });
    });

    describe('Login page form', () => {
      it('should display a label for committee id', () => {
        page.navigateTo();
        expect(page.getCommitteeIdLabel()).toEqual('Committee ID');
      });

      it('should be committee id input', () => {
        expect(page.getCommitteeIdInput()).toBeTruthy();
      });

      it('should display a label for password', () => {
        page.navigateTo();
        expect(page.getPasswordLabel()).toEqual('Password');
      });

      it('should be password input', () => {
        expect(page.getPasswordInput()).toBeTruthy();
      });

      it('there should be a login button with the text `Log In`', () => {
        page.navigateTo();
        expect(page.getLoginBtn().getText()).toEqual('Enter');
      });
    });


    describe('Login page form state', () => {
      xit('should display errors for empty fields', () => {
        page.navigateTo();

        page.getLoginBtn().click().then(() => {
          browser.waitForAngular();
          browser.sleep(1000);

          expect(page.getCommitteeIDInputError().getText()).toEqual('Please enter your committee id.');

          expect(page.getPasswordInputError().getText()).toEqual('Please enter your password.');
        });
      });

      xit('should display error for invalid credentials', () => {
        page.navigateTo();

        page.fillInvalidCredentials();

        page.getLoginBtn().click().then(() => {
          browser.waitForAngular();
          browser.sleep(1000);

          expect(page.getInvalidCredentialsError().getText()).toEqual('Invalid commitee id or password.');
        });
      });

      it('should login with correct credentials', () => {
        page.navigateTo();
        browser.waitForAngular();

        page.fillValidCredentials();

        page.getLoginBtn().click().then( () => {
          browser.wait(protractor.ExpectedConditions.visibilityOf(page.getTwoFactorInstruction())).then( () => {
            page.getTwoFactorInstruction().getText().then( (t) => {
              expect(t).toMatch('Please choose one of the three options for code verification');
            })
          })
        });
      });
    });
  });
});
