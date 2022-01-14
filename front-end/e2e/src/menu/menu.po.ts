import { by, element } from 'protractor';

const menu = {
    getConstactMenuLinkElement : function() {
        return element(by.xpath( '//a[@href=\'#/contacts\']'  ))
    }
}

export default menu;
