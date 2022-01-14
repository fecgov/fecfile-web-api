import {browser, by, element, protractor} from 'protractor';
import {CommonFlows} from '../common-flows.e2e-spec';

describe('contact management', () => {
    let flows: CommonFlows;

    beforeEach(() => {
        flows = new CommonFlows();
        browser.ignoreSynchronization = true;
    });


    describe('view contacts', () => {

        it('should display the manage contact screen', () => {
            flows.login();
        });


    });
});
