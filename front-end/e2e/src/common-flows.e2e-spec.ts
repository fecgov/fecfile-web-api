import {browser, by, element, protractor} from 'protractor';
import {LoginPage} from './login/login.po';
import {DashboardPage} from './dashboard/dashboard.po';

export class CommonFlows {

    loginPage: LoginPage;
    dashboard: DashboardPage;

    constructor() {
        this.loginPage = new LoginPage();
        this.dashboard = new DashboardPage();
    }

    async login() {
        this.loginPage.navigateTo();
        browser.waitForAngular();

        this.loginPage.fillValidCredentials();

        return this.loginPage.getLoginBtn().click().then(() => {
            browser.wait(protractor.ExpectedConditions.visibilityOf(this.loginPage.getTwoFactorInstruction())).then(() => {
                this.loginPage.getTwoFactorInstruction().getText().then((t) => {
                    expect(t).toMatch('Please choose one of the three options for code verification');

                    this.loginPage.getTwoFactorEmailRadioButton().click();
                    this.loginPage.getTwoFactorSubmitButton().click()

                    browser.wait(protractor.ExpectedConditions.visibilityOf(this.loginPage.getTwoFactorSecurityTextBox())).then(() => {

                        this.loginPage.getTwoFactorSecurityTextBox().sendKeys('111111');
                        this.loginPage.getTwoFactorSecurtySubmitButton().click();

                        browser.wait(protractor.ExpectedConditions.visibilityOf(this.loginPage.getUsageWarningContinutButton())).then( () => {
                            this.loginPage.getUsageWarningContinutButton().click();

                            browser.wait(protractor.ExpectedConditions.visibilityOf(this.dashboard.getNavbar())).then( () => {
                                expect(this.dashboard.getNavbar().getText() ).toMatch('Dashboard')
                            });


                        })


                    });
                });

            })
        });
    }
}
