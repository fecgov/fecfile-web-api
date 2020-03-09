export class DebtSummaryModel {
  apiCall: string;
  scheduleType: string;
  transactionId: string;
  backRefTransactionId: string;
  transactionTypeIdentifier: string;
  transactionTypeDescription: string;
  reportId: string;
  selected: boolean;
  toggleChild: boolean;
  child: DebtSummaryModel[] = [];
  entityType: string;
  name: string;
  paymentDate: Date;
  beginningBalance: any;
  incurredAmt: any;
  paymentAmt: any;
  closingBalance: any;
  memoCode: string;
  aggregate: number;
  entityId: string;

  constructor(debtSummary: any) {
    this.apiCall = debtSummary.apiCall ? debtSummary.apiCall : '';
    this.scheduleType = debtSummary.scheduleType ? debtSummary.scheduleType : '';
    this.transactionId = debtSummary.transactionId ? debtSummary.transactionId : '';
    this.backRefTransactionId = debtSummary.backRefTransactionId ? debtSummary.backRefTransactionId : '';
    this.transactionTypeIdentifier = debtSummary.transactionTypeIdentifier ? debtSummary.transactionTypeIdentifier : '';
    this.transactionTypeDescription = debtSummary.transactionTypeDescription
      ? debtSummary.transactionTypeDescription
      : '';
    this.name = debtSummary.name ? debtSummary.name : '';
    this.reportId = debtSummary.reportId ? debtSummary.reportId : '';
    this.selected = debtSummary.selected;
    this.toggleChild = debtSummary.toggleChild;
    this.child = debtSummary.child;
    this.entityType = debtSummary.entityType;
    this.name = debtSummary.name ? debtSummary.name : '';
    this.paymentDate = debtSummary.paymentDate;
    this.beginningBalance = debtSummary.beginningBalance;
    this.incurredAmt = debtSummary.incurredAmt;
    this.paymentAmt = debtSummary.paymentAmt;
    this.closingBalance = debtSummary.closingBalance;
    this.memoCode = debtSummary.memoCode;
    this.aggregate = debtSummary.aggregate;
    this.entityId = debtSummary.entityId;
  }
}
