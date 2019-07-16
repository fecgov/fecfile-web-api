/**
 * A model for the transactions filter properties.
 */
export class ContactFilterModel {

    show: boolean;
    formType: string;
    filterStates: string[];
    filterCategoriesText: string;
    filterCategories: string[];
    filterAmountMin: number;
    filterAmountMax: number;
    filterAggregateAmountMin: number;
    filterAggregateAmountMax: number;
    filterDateFrom: Date;
    filterDateTo: Date;
    filterDeletedDateFrom: Date;
    filterDeletedDateTo: Date;
    filterMemoCode: boolean;
    filterItemizations: string[];
    keywords: string[] = [];

    constructor() {
    }
}
