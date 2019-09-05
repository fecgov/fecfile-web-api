export class TransactionModel {
  type: string;
  entityId: string;
  transactionId: string;
  backRefTransactionId: string;
  transactionTypeIdentifier: string;
  name: string;
  street: string;
  street2: string;
  city: string;
  state: string;
  zip: string;
  date: Date;
  amount: number;
  deletedDate: Date;
  aggregate: number;
  purposeDescription: string;
  contributorEmployer: string;
  contributorOccupation: string;
  memoCode: string;
  memoText: string;
  selected: boolean;
  itemized: string;
  reportStatus: string;

  constructor(transaction: any) {
    this.type = transaction.type ? transaction.type : '';
    this.entityId = transaction.entityId ? transaction.entityId : '';
    this.transactionId = transaction.transactionId ? transaction.transactionId : '';
    this.backRefTransactionId = transaction.backRefTransactionId ? transaction.backRefTransactionId : '';
    this.transactionTypeIdentifier = transaction.transactionTypeIdentifier ? transaction.transactionTypeIdentifier : '';
    this.name = transaction.name ? transaction.name : '';
    this.street = transaction.street ? transaction.street : '';
    this.street2 = transaction.street2 ? transaction.street2 : '';
    this.city = transaction.city ? transaction.city : '';
    this.state = transaction.state ? transaction.state : '';
    this.zip = transaction.zip ? transaction.zip : '';
    this.date = transaction.date ? transaction.date : null;
    this.amount = transaction.amount ? transaction.amount : null;
    this.deletedDate = transaction.deletedDate ? transaction.deletedDate : null;
    this.aggregate = transaction.aggregate ? transaction.aggregate : null;
    this.purposeDescription = transaction.purposeDescription ? transaction.purposeDescription : '';
    this.contributorEmployer = transaction.contributorEmployer ? transaction.contributorEmployer : '';
    this.contributorOccupation = transaction.contributorOccupation ? transaction.contributorOccupation : '';
    this.memoCode = transaction.memoCode ? transaction.memoCode : '';
    this.memoText = transaction.memoText ? transaction.memoText : '';
    this.selected = transaction.selected;
    this.itemized = transaction.itemized;
    this.reportStatus = transaction.reportStatus;
  }
}
