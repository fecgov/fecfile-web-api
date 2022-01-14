import {browser, by, element, protractor} from 'protractor';
import {CommonWorkflows} from '../common-flows.e2e-spec';
import contactPage from "./contact.po";

describe('contact management', () => {
    let flows: CommonWorkflows;

    beforeEach(() => {
        flows = new CommonWorkflows();
        //TODO: We need to workout why this is necessary to get protractor working on more than one app page
        browser.ignoreSynchronization = true;
    });


    describe('view contacts', () => {

        it('should display the manage contact screen', async () => {
            await flows.gotoContacts();
            await expect( contactPage.getAddNewButton().getText()).toMatch('Add New');
            return
        });

        // TODO: This test is very close to working but the Angular synchronization issue is causing problems
        xit('should support adding new contacts', async () => {
            await flows.gotoContacts();
            await expect( contactPage.getAddNewButton().getText()).toMatch('Add New');

            contactPage.getAddNewButton().click();
            await browser.wait(protractor.ExpectedConditions.visibilityOf(contactPage.getSaveAddMoreButton()));
            await expect( contactPage.getSaveAddMoreButton().getText()).toMatch('Save');

            await contactPage.fillSampleContact();
            await contactPage.getSaveAddMoreButton().click();
            await expect( contactPage.getSaveAddMoreButton().getText()).toMatch('Save');
            await contactPage.getViewContactsButton().click()

            await browser.wait(protractor.ExpectedConditions.visibilityOf(contactPage.getPageTitle()))

            await expect ( element(by.xpath( "//a[contains(.,'Smith')]"  )).getText()  ).toMatch ("Joe");

            return
        });



    });
});
