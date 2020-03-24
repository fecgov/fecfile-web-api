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
, ChangeDetectionStrategy } from '@angular/core';
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
  /* animations: [
    trigger('fadeInOut', [
      transition(':enter', [style({ opacity: 0 }), animate(500, style({ opacity: 1 }))]),
      transition(':leave', [animate(0, style({ opacity: 0 }))])
    ])
  ] */
})
export class SubTransactionsTableComponent implements OnInit, OnChanges {
  @Input()
  public formType: string;

  @Input()
  public subTransactionsTableType: string;

  @Input()
  public subTransactions: any[];

  @Input()
  public returnToDebtSummary: boolean;

  @Input()
  public returnToDebtSummaryInfo: any;

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
    if (!this.subTransactionsTableType) {
      this.subTransactionsTableType = 'sched_a';
    }
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

        // Amount comes from various API fields depending on the transaction type.
        // TODO they should be mapped to 1 front-end field.  Remove this once in place.
        model.amount = trx.expenditure_amount ? trx.expenditure_amount : trx.contribution_amount;
        const transactionType = trx.transaction_type_identifier;
        switch (transactionType) {
          case 'ALLOC_EXP_DEBT':
            model.amount = trx.total_amount;
            break;
          case 'ALLOC_FEA_DISB_DEBT':
            model.amount = trx.total_fed_levin_amount;
            break;
          case 'COEXP_PARTY_DEBT':
            model.amount = trx.expenditure_amount;
            // TODO API should provie schdule_type. Infer from transaction_type until then.
            if (!trx.schdule_type) {
              trx.schdule_type = 'sched_f';
            }
            model.scheduleType = trx.schdule_type;
            break;
          default:
        }

        if (
          transactionType === 'ALLOC_EXP_CC_PAY_MEMO' ||
          transactionType === 'ALLOC_EXP_STAF_REIM_MEMO' ||
          transactionType === 'ALLOC_EXP_PMT_TO_PROL_MEMO'
        ) {
          model.amount = trx.total_amount;
        }

        if (transactionType === 'ALLOC_FEA_CC_PAY_MEMO' || transactionType === 'ALLOC_FEA_STAF_REIM_MEMO') {
          model.amount = trx.total_fed_levin_amount;
        }

        model.date = trx.expenditure_date ? trx.expenditure_date : trx.contribution_date;
        model.aggregate = trx.contribution_aggregate;
        if (!model.aggregate && this.subTransactionsTableType === 'sched_e') {
          model.aggregate = trx.expenditure_aggregate;
        }
        if (!model.aggregate && this.subTransactionsTableType === 'sched_d') {
          model.aggregate = trx.aggregate_amt;
        }

        model.activityEventType = trx.activity_event_type;
        model.activityEventIdentifier = trx.activity_event_identifier;
        model.purpose = trx.purpose;
        model.fedShareAmount = trx.fed_share_amount;
        model.nonfedShareAmount = trx.non_fed_share_amount;

        if (transactionType === 'ALLOC_FEA_CC_PAY_MEMO' || transactionType === 'ALLOC_FEA_STAF_REIM_MEMO') {
          model.fedShareAmount = trx.federal_share;
          model.levinShare = trx.levin_share;
          model.purpose = trx.expenditure_purpose;
        }

        model.memoCode = trx.memo_code;
        model.memoText = trx.memo_text;
        model.type = trx.transaction_type_description;
        model.transactionTypeIdentifier = trx.transaction_type_identifier;
        model.transactionId = trx.transaction_id;
        model.backRefTransactionId = trx.back_ref_transaction_id;
        model.apiCall = trx.api_call;
        model.disbursementDate = trx.disbursement_date;
        model.disseminationDate = trx.dissemination_date;
        model.reportId = trx.report_id;

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
              // temp patch until sub transactions contain
              // back_ref_api_call or parent passes it as Input()
              let parentApiCall = trx.apiCall;
              if (trx.backRefTransactionId) {
                if (typeof trx.backRefTransactionId === 'string') {
                  if (trx.backRefTransactionId.startsWith('SD')) {
                    parentApiCall = '/sd/schedD';
                  }
                }
              }
              this._getSubTransactions(reportId, trx.backRefTransactionId, parentApiCall);
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
    if (this.isH4OrH6() === 'H4') {
      trx.apiCall = '/sh4/schedH4';
    } else if (this.isH4OrH6() === 'H6') {
      trx.apiCall = '/sh6/schedH6';
    } else if (this.isSchedF(trx)) {
      trx.apiCall = '/sf/schedF';
    }
    if (this.returnToDebtSummary) {
      const debtSummary = {
        returnToDebtSummary: this.returnToDebtSummary,
        returnToDebtSummaryInfo: this.returnToDebtSummaryInfo
      };
      this._transactionsMessageService.sendEditDebtSummaryTransactionMessage({ trx: trx, debtSummary: debtSummary });
    } else {
      this._transactionsMessageService.sendEditTransactionMessage(trx);
    }
  }

  public isH4OrH6(): string {
    if (this.subTransactions) {
      for (const trx of this.subTransactions) {
        const transactionType = trx.transaction_type_identifier;

        if (
          transactionType === 'ALLOC_EXP_CC_PAY_MEMO' ||
          transactionType === 'ALLOC_EXP_STAF_REIM_MEMO' ||
          transactionType === 'ALLOC_EXP_PMT_TO_PROL_MEMO'
        ) {
          return 'H4';
        }

        if (transactionType === 'ALLOC_FEA_CC_PAY_MEMO' || transactionType === 'ALLOC_FEA_STAF_REIM_MEMO') {
          return 'H6';
        }
      }
    }
  }

  private isSchedF(trx: TransactionModel) {
    if (trx) {
      if (
        trx.transactionTypeIdentifier === 'COEXP_CC_PAY_MEMO' ||
        trx.transactionTypeIdentifier === 'COEXP_STAF_REIM_MEMO' ||
        trx.transactionTypeIdentifier === 'COEXP_PMT_PROL_MEMO'
      ) {
        return true;
      }
    }
    return false;
  }
}
