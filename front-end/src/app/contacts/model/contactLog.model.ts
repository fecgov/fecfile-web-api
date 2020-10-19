
export class ContactLogModel {
    entity_type: string;
    id: string;
    name: string;
    address: string;
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
    modifieddate: string;
    user: string;

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
        this.modifieddate = contact.modifieddate ? contact.modifieddate : '';
        this.user = contact.user ? contact.user : '';
        this.address = contact.address ? contact.address : '';
    }

    getModifedDate() {
        return this.modifieddate;
    }

    getUser() {
        return this.user;
    }

    getInfo() {
        if (this.entity_type === 'ORG' || this.entity_type === 'IND') {
            let result = '';
            result += this.address ? this.address : ' ';
            result += ' ,' + this.name ? this.name : '';
            return  result;
        }  else {
            return 'NA';
        }
    }
}
