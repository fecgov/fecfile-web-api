import { Component, EventEmitter, Input, OnInit, Output, ViewChild, ElementRef, ViewChildren, QueryList, OnChanges } from '@angular/core';
import { TransactionsService } from '../service/transactions.service';
import { TransactionsMessageService } from '../service/transactions-message.service';
import { TransactionModel } from '../model/transaction.model';

/**
 * A component for the Sub (Child) Transactions Table to be used across all forms
 * by transactions with multiple sub (child) transaction funtionality.
 */
@Component({
    selector: 'app-sub-transactions-table',
    templateUrl: './sub-transactions-table.component.html',
    styleUrls: ['./sub-transactions-table.component.scss'],
})
  export class SubTransactionsTableComponent implements OnInit, OnChanges {

  // @Input()
  // public reportId: string;

  // @Input()
  // public transactionId: string;

  @Input()
  public subTransactions: any[];

  public transactionsModel: Array<TransactionModel>;

  public constructor(
    private _transactionsMessageService: TransactionsMessageService
  ) { }

  /**
   * Init the component.
   */
  public ngOnInit(): void {
    this.subTransactions = [];
    this.transactionsModel = [];
  }

  /**
   * When input changes are made to subTransactions, populate it in the model and UI. 
   */
  public ngOnChanges(): void {
    this._populateTable();
  }

  private _populateTable() {

    const modelArray = [];
    for (const trx of this.subTransactions) {
      const model = new TransactionModel({});

      const lastName = trx.last_name ? trx.last_name.trim() : '';
      const firstName = trx.first_name ? trx.first_name.trim() : '';
      const middleName = trx.middle_name ? trx.middle_name.trim() : '';
      const suffix = trx.suffix ? trx.suffix.trim() : '';
      const prefix = trx.prefix ? trx.prefix.trim() : '';

      model.name = `${lastName}, ${firstName}, ${middleName}, ${prefix}, ${suffix}`;
      model.amount = trx.expenditure_amount ? trx.expenditure_amount : trx.contribution_amount;
      model.date = trx.expenditure_date ? trx.expenditure_date : trx.contribution_date;
      model.aggregate = trx.aggregate_amt;

      model.transactionTypeIdentifier = trx.transaction_type_identifier;
      model.transactionId = trx.transaction_id;

      modelArray.push(model);
    }
    this.transactionsModel = modelArray;
  }

  /**
   * Clone the transaction selected by the user.
   *
   * @param trx the Transaction to clone
   */
  public cloneTransaction(): void {
    alert('Clone transaction is not yet supported');
  }

  /**
   * Link the transaction selected by the user.
   *
   * @param trx the Transaction to link
   */
  public linkTransaction(): void {
    alert('Link requirements have not been finalized');
  }

  /**
   * View the transaction selected by the user.
   *
   * @param trx the Transaction to view
   */
  public viewTransaction(): void {
    alert('View transaction is not yet supported');
  }

  /**
   * Edit the transaction selected by the user.
   *
   * @param trx the Transaction to edit
   */
  public editTransaction(trx: TransactionModel): void {
    this._transactionsMessageService.sendEditTransactionMessage(trx);
  }
}
