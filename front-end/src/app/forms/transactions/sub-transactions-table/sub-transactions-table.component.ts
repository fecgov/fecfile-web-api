import {
  Component,
  EventEmitter,
  Input,
  OnInit,
  Output,
  ViewChild,
  ElementRef,
  ViewChildren,
  QueryList,
  OnChanges
} from '@angular/core';
import { TransactionsService, GetTransactionsResponse } from '../service/transactions.service';
import { TransactionsMessageService } from '../service/transactions-message.service';
import { TransactionModel } from '../model/transaction.model';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { IndividualReceiptService } from '../../form-3x/individual-receipt/individual-receipt.service';
import { trigger, transition, style, animate } from '@angular/animations';

/**
 * A component for the Sub (Child) Transactions Table to be used across all forms
 * by transactions with multiple sub (child) transaction funtionality.
 */
@Component({
  selector: 'app-sub-transactions-table',
  templateUrl: './sub-transactions-table.component.html',
  styleUrls: ['./sub-transactions-table.component.scss'],
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [style({ opacity: 0 }), animate(500, style({ opacity: 1 }))]),
      transition(':leave', [animate(0, style({ opacity: 0 }))])
    ])
  ]
})
export class SubTransactionsTableComponent implements OnInit, OnChanges {
  @Input()
  public formType: string;

  @Input()
  public subTransactions: any[];

  public transactionsModel: Array<TransactionModel>;

  public constructor(
    private _transactionsMessageService: TransactionsMessageService,
    private _transactionsService: TransactionsService,
    private _dialogService: DialogService,
    private _receiptService: IndividualReceiptService
  ) {}

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
    if (this.subTransactions) {
      for (const trx of this.subTransactions) {
        const model = new TransactionModel({});

        const lastName = trx.last_name ? trx.last_name.trim() : '';
        const firstName = trx.first_name ? trx.first_name.trim() : '';
        const middleName = trx.middle_name ? trx.middle_name.trim() : '';
        const suffix = trx.suffix ? trx.suffix.trim() : '';
        const prefix = trx.prefix ? trx.prefix.trim() : '';

        if (trx.entity_type === 'IND' || trx.entity_type === 'CAN') {
          model.name = `${lastName}, ${firstName}, ${middleName}, ${prefix}, ${suffix}`;
        } else {
          if (trx.hasOwnProperty('entity_name')) {
            model.name = trx.entity_name;
          }
        }

        model.amount = trx.expenditure_amount ? trx.expenditure_amount : trx.contribution_amount;
        model.date = trx.expenditure_date ? trx.expenditure_date : trx.contribution_date;
        model.aggregate = trx.contribution_aggregate;

        model.transactionTypeIdentifier = trx.transaction_type_identifier;
        model.transactionId = trx.transaction_id;
        model.backRefTransactionId = trx.back_ref_transaction_id;
        model.apiCall = trx.api_call;

        modelArray.push(model);
      }
    }
    this.transactionsModel = modelArray;
  }

  /**
   * Trash the transaction selected by the user.
   *
   * @param trx the Transaction to trash
   */
  public trashTransaction(trx: TransactionModel): void {
    this._dialogService
      .confirm('You are about to delete this transaction ' + trx.transactionId + '.', ConfirmModalComponent, 'Caution!')
      .then(res => {
        if (res === 'okay') {
          const reportId = this._receiptService.getReportIdFromStorage(this.formType);
          this._transactionsService
            .trashOrRestoreTransactions(this.formType, 'trash', reportId, [trx])
            .subscribe((res: GetTransactionsResponse) => {
              this._getSubTransactions(reportId, trx.backRefTransactionId, trx.apiCall);
              this._dialogService.confirm(
                'Transaction has been successfully deleted and sent to the recycle bin. ' + trx.transactionId,
                ConfirmModalComponent,
                'Success!',
                false,
                ModalHeaderClassEnum.successHeader
              );
            });
        } else if (res === 'cancel') {
        }
      });
  }

  private _getSubTransactions(reportId: string, transactionId: string, apiCall: string): void {
    this.transactionsModel = [];
    this._receiptService.getDataSchedule(reportId, transactionId, apiCall).subscribe(res => {
      if (Array.isArray(res)) {
        for (const trx of res) {
          if (trx.hasOwnProperty('transaction_id')) {
            if (trx.hasOwnProperty('child')) {
              if (Array.isArray(trx.child)) {
                if (trx.child.length > 0) {
                  this.subTransactions = trx.child;
                  this._populateTable();
                }
              }
            }
          }
        }
      }
    });
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
