/**
 * A model for the transactions filter properties.
 */
export class ContactFilterModel {

    show: boolean;
    formType: string;
    filterStates: string[];
    filterTypes: string[];
    filterDeletedDateFrom: Date;
    filterDeletedDateTo: Date;
    keywords: string[] = [];
    selected: boolean;
    constructor() {
    }
}
