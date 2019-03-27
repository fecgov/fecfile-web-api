module.exports = {
    //form99menuitem: element(by.xpath("//div[@class='sidebar__nav--header']//button[@type='button']")),
   //form99menuitem: element(by.xpath("//div[@class='sidebar__nav--header']//button[@type='button']")),
    form99menuitem: element(by.xpath("//i[@class='up-arrow-icon']")),
    form99: element(by.xpath("//a[contains(text(),'Miscellaneous Report to the FEC (F99)')]")),
    form99RadioButton: element(by.xpath("//input[@id='msm-radio']")), 
    from99ReasonRadioNext: element(by.xpath("//div[@class='forms__btn-container']//button[@type='submit'][contains(text(),'Next')]")),
    form99ReasonTextArea: element(by.xpath("//textarea[@placeholder='Enter text here...']")),
    form99ReasonTextSave: element(by.xpath("//button[contains(text(),'Save & Continue')]")),
    from99ReasonTextNext: element(by.xpath("//button[@type='button'][contains(text(),'Next')]")),
    from99SigneeCertify: element(by.xpath("//input[@id='agreement']")),
    from99SigneeSubmit: element(by.xpath("//button[contains(text(),'Submit')]")),
    

}