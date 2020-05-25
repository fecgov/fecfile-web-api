
/**
 * TODO There are redundent models for import contacts and add contacts.  These
 * should be consolidated in the future.
 */
export class ImportContactModel {
  id: string;
  committeeId: string;
  type: string;
  name: string;
  lastName: string;
  firstName: string;
  middleName: string;
  suffix: string;
  prefix: string;
  street: string;
  street2: string;
  city: string;
  state: string;
  zip: string;
  employer: string;
  occupation: string;
  candidateId: string;
  officeSought: string;
  officeState: string;
  district: string;
  multiCandidateCmteStatus: string;
  selected: boolean;

  constructor(contact: any) {
    this.id = contact.id ? contact.id : '';
    this.committeeId = contact.committeeId ? contact.committeeId : '';
    this.type = contact.type ? contact.type : '';
    this.name = contact.name ? contact.name : '';
    this.lastName = contact.lastName ? contact.lastName : '';
    this.firstName = contact.firstName ? contact.firstName : '';
    this.middleName = contact.middleName ? contact.middleName : '';
    this.suffix = contact.suffix ? contact.suffix : '';
    this.prefix = contact.prefix ? contact.prefix : '';
    this.street = contact.street ? contact.street : '';
    this.street2 = contact.street2 ? contact.street2 : '';
    this.city = contact.city ? contact.city : '';
    this.state = contact.state ? contact.state : '';
    this.zip = contact.zip ? contact.zip : '';
    this.employer = contact.employer ? contact.employer : '';
    this.occupation = contact.occupation ? contact.occupation : '';
    this.candidateId = contact.candidateId ? contact.candidateId : '';
    this.officeSought = contact.officeSought ? contact.officeSought : '';
    this.officeState = contact.officeState ? contact.officeState : '';
    this.district = contact.district ? contact.district : '';
    this.multiCandidateCmteStatus = contact.multiCandidateCmteStatus ?
      contact.multiCandidateCmteStatus : '';
    this.selected = contact.selected;
  }
}
