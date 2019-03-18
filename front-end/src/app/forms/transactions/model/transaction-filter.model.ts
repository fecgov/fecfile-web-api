/**
 * A model for the transactions filter properties.
 */
export class TransactionFilterModel {

    show: boolean;
    formType: string;
    filterStates: string[];
    filterCategoriesText: string;
    filterCategories: string[];
    filterAmountMin: number;
    filterAmountMax: number;
    filterDateFrom: Date;
    filterDateTo: Date;
    filterMemoCode: boolean;
    keywords = [];

    constructor() {
    }
}
