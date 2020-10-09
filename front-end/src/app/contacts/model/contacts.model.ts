export class ContactModel {
    entity_type: string;
    id: string;
    name: string;
    entity_name: string;
    lastName: string;
    firstName: string;
    middleName: string;
    suffix: string;
    prefix: string;
    street1: string;
    street2: string;
    city: string;
    state: string;
    zip: string;
    phoneNumber: string;
    employer: string;
    occupation: string;
    officeSought: string;
    candOffice: string;
    candOfficeState: string;
    candOfficeDistrict: string;
    candCmteId: string;
    deletedDate: string;
    selected: boolean;
    activeTransactionsCnt: number;
    toggleLog: boolean;
    contactLog: any;
    transactions: any;
    constructor(contact: any) {
        this.entity_type = contact.entity_type ? contact.entity_type : '';
        this.id = contact.id ? contact.id : '';
        this.name = contact.name ? contact.name : '';
        this.entity_name = contact.entity_name ? contact.entity_name : '';
        this.lastName = contact.lastName ? contact.lastName : '';
        this.firstName = contact.firstName ? contact.firstName : '';
        this.middleName = contact.middleName ? contact.middleName : '';
        this.suffix = contact.suffix ? contact.suffix : '';
        this.prefix = contact.prefix ? contact.prefix : '';
        this.street1 = contact.street1 ? contact.street1 : '';
        this.street2 = contact.street2 ? contact.street2 : '';
        this.city = contact.city ? contact.city : '';
        this.state = contact.state ? contact.state : '';
        this.zip = contact.zip ? contact.zip : '';
        this.phoneNumber = contact.phoneNumber ? contact.phoneNumber : '';
        this.employer = contact.employer ? contact.employer : '';
        this.occupation = contact.occupation ? contact.occupation : '';
        this.officeSought = contact.officeSought ? contact.officeSought : '';
        this.candOffice = contact.candOffice ? contact.candOffice : '';
        this.candOfficeState = contact.candOfficeState ? contact.candOfficeState : '';
        this.candOfficeDistrict = contact.candOfficeDistrict ? contact.candOfficeDistrict : '';
        this.phoneNumber = contact.phoneNumber ? contact.phoneNumber : '';
        this.candCmteId = contact.candCmteId ? contact.candCmteId : '';
        this.deletedDate = contact.deletedDate ? contact.deletedDate : '';
        this.selected = contact.selected;
        this.activeTransactionsCnt = contact.active_transactions_cnt ? contact.active_transactions_cnt : 0;
        this.contactLog = null;
        this.toggleLog = false;
        this.transactions = null;
    }

    setContactLog(contactLog: any) {
        this.contactLog = contactLog;
    }
    getContactLog(): any {
        return this.contactLog;
    }
    setTransactions(transactions: any){
        this.transactions = transactions;
    }
    getTransactions(): any {
        return this.transactions;
    }
}
