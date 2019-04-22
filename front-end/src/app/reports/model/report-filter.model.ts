/**
 * A model for the transactions filter properties.
 */
export class ReportFilterModel {

    show: boolean;
    formType: string;
    filterStates: string[];
    filterCategoriesText: string;
    filterCategories: string[];
    filterAmountMin: number;
    filterAmountMax: number;
    filterDateFrom: Date;
    filterDateTo: Date;
    filterFiledDateFrom: Date;
    filterFiledDateTo: Date;
    filterCvgDateFrom: Date;
    filterCvgDateTo: Date;
    filterMemoCode: boolean;
    keywords: string[] = [];
    filterForms: string[];
    filterReports: string[];
    filterAmendmentIndicators: string[];
    filterStatuss: string[];
    constructor() {
    }
}
