/**
 * A model for the transactions filter properties.
 */
export class TransactionFilterModel {
  show: boolean;
  formType: string;
  filterStates: string[];
  fitlerReportTypes: string[];
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
  filterElectionYearFrom: string;
  filterElectionYearTo: string;
  filterElectionCodes: string[];
  filterLoanAmountMin: number;
  filterLoanAmountMax: number;
  filterLoanClosingBalanceMin: any;
  filterLoanClosingBalanceMax: any;
  filterSchedule: string;
  filterDebtBeginningBalanceMin: number;
  filterDebtBeginningBalanceMax: number;

  constructor() {}
}
