/**
 * A model for the transactions filter properties.
 */
export class TransactionFilterModel {

    show: boolean;
    formType: string;
    searchFilter: string;
    filterStates: string[];
    filterCategories: string[];
    filterAmountMin: number;
    filterAmountMax: number;
    filterDateFrom: Date;
    filterDateTo: Date;
    filterMemoCode: boolean;

    constructor() {
    }
}
