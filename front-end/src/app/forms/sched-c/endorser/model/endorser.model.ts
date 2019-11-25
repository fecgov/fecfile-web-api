export class EndorserModel {
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
    employer: string;
    occupation: string;
    contribution_amount:string;

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
        this.contribution_amount = contact.contribution_amount ? contact.contribution_amount : '';
        this.employer = contact.employer ? contact.employer : '';
        this.occupation = contact.occupation ? contact.occupation : '';

    }
}
