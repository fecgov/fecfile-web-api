import {browser, protractor} from 'protractor';
import {LoginPage} from './login/login.po';
import {DashboardPage} from './dashboard/dashboard.po';
import menu from './menu/menu.po'
import contactPage from './contact/contact.po'

export class CommonWorkflows {

    loginPage: LoginPage;
    dashboard: DashboardPage;

    constructor() {
        this.loginPage = new LoginPage();
        this.dashboard = new DashboardPage();
    }

    async login() {
        this.loginPage.navigateTo();

        // login page
        this.loginPage.fillValidCredentials();
        this.loginPage.getLoginBtn().click();

        // two factor choice page
        browser.wait(protractor.ExpectedConditions.visibilityOf(this.loginPage.getTwoFactorInstruction()));
        const t = await this.loginPage.getTwoFactorInstruction().getText();
        expect(t).toMatch('Please choose one of the three options for code verification');
        this.loginPage.getTwoFactorEmailRadioButton().click();
        this.loginPage.getTwoFactorSubmitButton().click();

        // enter two factor login token
        browser.wait(protractor.ExpectedConditions.visibilityOf(this.loginPage.getTwoFactorSecurityTextBox()));
        this.loginPage.getTwoFactorSecurityTextBox().sendKeys('111111');
        this.loginPage.getTwoFactorSecurtySubmitButton().click();

        // Click through gov usage warning
        browser.wait(protractor.ExpectedConditions.visibilityOf(this.loginPage.getUsageWarningContinutButton()));
        this.loginPage.getUsageWarningContinutButton().click();

        // Verify we get the dashboard page
        browser.wait(protractor.ExpectedConditions.visibilityOf(this.dashboard.getNavbar()));
        return  expect(this.dashboard.getNavbar().getText()).toMatch('Dashboard');
    }

    async gotoContacts() {
        await this.dashboard.getNavbar().getText().then( () => {
            //already logged in
        }).catch( () => {
            this.login();
        }).finally( async () => {
            await browser.wait(protractor.ExpectedConditions.visibilityOf(menu.getConstactMenuLinkElement())  );
            menu.getConstactMenuLinkElement().click()

            await browser.wait(protractor.ExpectedConditions.visibilityOf(contactPage.getPageTitle()))
            return expect(contactPage.getPageTitle().getText()).toMatch('Contacts')
        })
        return;
    }
}
