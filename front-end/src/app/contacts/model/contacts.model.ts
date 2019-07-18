export class ContactModel {
    name: string;
    type: string;
    id: string;
    employer: string;
    occupation: string;
    selected: boolean;
    constructor(contact: any) {
        this.type = contact.type ? contact.type : '';
        this.name = contact.name ? contact.name : '';
        this.id = contact.id ? contact.id : '';
        this.employer = contact.employer ? contact.employer : '';
        this.occupation = contact.occupation ? contact.occupation : '';
        this.selected = contact.selected;
    }
}
