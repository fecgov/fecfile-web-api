import {by, element} from 'protractor';

let testContact = [
    {text: 'Smith', xpath: "//input[@name='last_name']"},
    {text: 'Sidney', xpath: "//input[@name='first_name']"},
    {text: '1 Main Street', xpath: "//input[@name='street_1']"},
    {text: 'Fairview', xpath: "//input[@id='city']"},
    {text: 'NJ', xpath: "//ng-select[@id='state']//input"},
    {text: '08083', xpath: "//input[@name='zip_code']"},
    {text: 'Big Co', xpath: "//input[@name='employer']"},
    {text: 'Blacksmith', xpath: "//input[@name='occupation']"}
];

const contactPage = {
    testContact: testContact,

    getPageTitle: function () {
        return element(by.xpath("//header//h1[text()='Contacts ']"))
    },

    getAddNewButton: function () {
        return element(by.xpath("//button[contains(.,'Add New')]"))
    },

    getSaveAddMoreButton: function () {
        return element(by.id('contact-save-add-more-button'));
    },

    getViewContactsButton: function() {
        return element(by.xpath("//button[contains(.,'View Contacts')]"));
    },

    fillSampleContact: async function () {

        for (let i=0; i < testContact.length; i++) {
            await element(by.xpath(testContact[i].xpath)).sendKeys(testContact[i].text);
        }
        await element(by.xpath("//ng-select[@id='state']//input")).click()
        await element(by.xpath("//input[@name='zip_code']")).click()

        return;
    }

}

export default contactPage;
