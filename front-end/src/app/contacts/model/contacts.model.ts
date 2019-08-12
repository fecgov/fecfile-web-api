export class ContactModel {
    type: string;
    name: string;
    id: string;
    street1: string;
    street2: string;
    city: string;
    state: string;
    zip: string;
    employer: string;
    occupation: string;
    selected: boolean;
    constructor(contact: any) {
        this.type = contact.type ? contact.type : '';
        this.name = contact.name ? contact.name : '';
        this.id = contact.id ? contact.id : '';
        this.street1 = contact.street1 ? contact.street1 : '';
        this.street2 = contact.street2 ? contact.street2 : '';
       // this.street1 = contact.street2 ? contact.street2 : '';
        this.city = contact.city ? contact.city : '';
        this.state = contact.state ? contact.state : '';
        this.zip = contact.zip ? contact.zip : '';
        this.employer = contact.employer ? contact.employer : '';
        this.occupation = contact.occupation ? contact.occupation : '';
        this.selected = contact.selected;
    }
}
