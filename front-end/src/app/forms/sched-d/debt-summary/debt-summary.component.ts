import {
  Component,
  OnInit,
  ViewEncapsulation,
  Output,
  EventEmitter,
  Input,
  SimpleChanges,
  OnChanges
, ChangeDetectionStrategy } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';
import { PaginationInstance } from 'ngx-pagination';
import { TableService } from 'src/app/shared/services/TableService/table.service';
import { UtilService } from 'src/app/shared/utils/util.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { SortableColumnModel } from 'src/app/shared/services/TableService/sortable-column.model';
import { DebtSummaryService, GetDebtsResponse } from './service/debt-summary.service';
import { DebtSummaryModel } from './model/debt-summary.model';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { TransactionsService, GetTransactionsResponse } from '../../transactions/service/transactions.service';
import { ReportTypeService } from '../../form-3x/report-type/report-type.service';
import { TransactionModel } from '../../transactions/model/transaction.model';
import { mockChildPayments } from './mock.json';

export enum DebtSumarysActions {
  add = 'add',
  edit = 'edit'
}

@Component({
  selector: 'app-debt-summary',
  templateUrl: './debt-summary.component.html',
  styleUrls: ['./debt-summary.component.scss'],
  encapsulation: ViewEncapsulation.None,
  providers: [DebtSummaryService],
  /* animations: [
    trigger('fadeInOut', [
      transition(':enter', [style({ opacity: 0 }), animate(500, style({ opacity: 1 }))]),
      transition(':leave', [animate(0, style({ opacity: 0 }))])
    ])
  ] */
})
export class DebtSummaryComponent implements OnInit, OnChanges {
  @Input()
  public forceChangeDetection: Date;

  @Input()
  public transactionType: string;

  @Input()
  public transactionTypeText: string;

  @Output()
  public status: EventEmitter<any> = new EventEmitter<any>();

  public debtModel: Array<DebtSummaryModel>;
  public totalAmount: number;
  public bulkActionDisabled = true;
  public bulkActionCounter = 0;
  public formType = '3X';

  // ngx-pagination config
  public pageSizes: number[] = [2, 10,20,50];
  public maxItemsPerPage: number = this.pageSizes[0];
  public paginationControlsMaxSize: number = 10; 
  public directionLinks: boolean = false;
  public autoHide: boolean = true;
  public config: PaginationInstance;
  public numberOfPages: number = 0;
  public pageNumbers: number[] = [];
  public gotoPage: number = 1;

  private firstItemOnPage = 0;
  private lastItemOnPage = 0;
  public allDebtSelected: boolean;

  /**
   * Array of columns to be made sortable.
   */
  private sortableColumns: SortableColumnModel[] = [];

  /**
   * Identifies the column currently sorted by name.
   */
  private currentSortedColumnName: string;

  /**
   * Component constructor with service dependency service injections.
   *
   * @param _tableService
   * @param _utilService
   * @param _dialogService
   */
  constructor(
    private _tableService: TableService,
    private _utilService: UtilService,
    private _dialogService: DialogService,
    private _debtSummaryService: DebtSummaryService,
    private _transactionsService: TransactionsService
  ) {
  }

  /**
   * Initialize the component.
   */
  ngOnInit() {
    const paginateConfig: PaginationInstance = {
      id: 'forms__debt-summ-table-pagination',
      itemsPerPage: this.maxItemsPerPage,
      currentPage: 1
    };
    this.config = paginateConfig;

    // TODO decide if sort settings are needed after leaving page.
    // Not supporting cachedVals as of original impl
    this.setSortableColumns();
    // this.getCachedValues();
    // this.cloneSortableColumns = this._utilService.deepClone(this.sortableColumns);

    //this.getDebtSummaries();

    this.getPage(this.config.currentPage);
  }

    /**
	 * The records for a given page.
	 *
	 * @param page the page containing the records to get
	 */
  public getPage(page: number): void {

    this.bulkActionCounter = 0;
    this.bulkActionDisabled = true;
    this.gotoPage = page;

    this.getDebtSummaries(page);
  }

  /**
   * onChange for maxItemsPerPage.
   *
   * @param pageSize the page size to get
   */
  public onMaxItemsPerPageChanged(pageSize: number): void {
    this.config.currentPage = 1;
    this.gotoPage = 1;
    this.config.itemsPerPage = pageSize;
    this.getPage(this.config.currentPage);
  }

  /**
   * onChange for gotoPage.
   *
   * @param page the page to get
   */
  public onGotoPageChange(page: number): void {
    if (this.config.currentPage == page) {
      return;
    }
    this.config.currentPage = page;
    this.getPage(this.config.currentPage);
  }

  /**
	 * Determine if pagination should be shown.
	 */
  public showPagination(): boolean {
    if (!this.autoHide) {
      return true;
    }
    if (this.config.totalItems > this.config.itemsPerPage) {
      return true;
    }
    // otherwise, no show.
    return false;
  }  

  /**
   * Determine the item range shown by the server-side pagination.
   */
  public determineItemRange(): string {
    let range: {
      firstItemOnPage: number, lastItemOnPage: number, itemRange: string
    } = this._utilService.determineItemRange(this.config, this.debtModel);

    this.firstItemOnPage = range.firstItemOnPage;
    this.lastItemOnPage = range.lastItemOnPage;
    return range.itemRange;
  }

  /**
   * Get the debt summary data onChange.
   *
   * @param changes
   */
  public ngOnChanges(changes: SimpleChanges) {
    // const paginateConfig: PaginationInstance = {
    //   id: 'forms__debt-summ-table-pagination',
    //   itemsPerPage: this.maxItemsPerPage,
    //   currentPage: 1
    // };
    // this.config = paginateConfig;

    //this.getDebtSummaries(1);
  }

  /**
   * Get the Debt Summaries for the Report
   */
  public getDebtSummaries(page: number): void {
    this.config.currentPage = page;

    this.debtModel = [];
    this.bulkActionCounter = 0;
    this.bulkActionDisabled = true;

    let sortedCol: SortableColumnModel = this._tableService.getColumnByName(
      this.currentSortedColumnName,
      this.sortableColumns
    );

    if (!sortedCol) {
      this.setSortDefault();
      sortedCol = this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);
    }

    if (sortedCol) {
      if (sortedCol.descending === undefined || sortedCol.descending === null) {
        sortedCol.descending = false;
      }
    } else {
      sortedCol = new SortableColumnModel('', false, false, false, false);
    }

    const serverSortColumnName = this._debtSummaryService.
      mapToSingleServerName(this.currentSortedColumnName);

    this._debtSummaryService.getDebts(
      this.transactionType,
      page,
      this.config.itemsPerPage,
      serverSortColumnName,
      sortedCol.descending
    ).subscribe((response: any) => {
      const pagedResponse = this._utilService.pageResponse(response, this.config);
      this.debtModel = pagedResponse.items;
      this.pageNumbers = pagedResponse.pageNumbers;
      this.allDebtSelected = false;
    });
  }

  /**
   * Check/Uncheck all Debts in the table.
   */
  public changeAllDebtSummarysSelected() {
    this.bulkActionCounter = 0;
    let debtsExist = false;
    for (const debt of this.debtModel) {
      debtsExist = true;
      debt.selected = this.allDebtSelected;
      if (this.allDebtSelected) {
        this.bulkActionCounter++;
      }
    }
    if (debtsExist) {
      this.bulkActionDisabled = !this.allDebtSelected;
    } else {
      this.bulkActionDisabled = true;
    }
  }

  /**
   * Check for multiple rows checked in the table
   * and disable/enable the bulk action button
   * accordingly.
   *
   * @param the event payload from the click
   */
  public checkForMultiChecked(e: any): void {
    if (e.target.checked) {
      this.bulkActionCounter++;
    } else {
      this.allDebtSelected = false;
      if (this.bulkActionCounter > 0) {
        this.bulkActionCounter--;
      }
    }
    this.bulkActionDisabled = this.bulkActionCounter > 1 ? false : true;
  }

  /**
   * Set the UI to show the default column sorted in the default direction.
   */
  private setSortDefault(): void {
    this.currentSortedColumnName = 'default';
  }

  /**
   * Wrapper method for the table service to set the class for sort column styling.
   *
   * @param colName the column to apply the class
   * @returns string of classes for CSS styling sorted/unsorted classes
   */
  public getSortClass(colName: string): string {
    return this._tableService.getSortClass(colName, this.currentSortedColumnName, this.sortableColumns);
  }

  /**
   * Change the sort direction of the table column.
   *
   * @param colName the column name of the column to sort
   */
  public changeSortDirection(colName: string): void {
    this.currentSortedColumnName = this._tableService.changeSortDirection(colName, this.sortableColumns);
    const direction = this._tableService.getBinarySortDirection(colName, this.sortableColumns);
    this.debtModel = this._debtSummaryService.sortDebtSummary(this.debtModel, this.currentSortedColumnName, direction);
  }

  /**
   * Get the SortableColumnModel by name.
   *
   * @param colName the column name in the SortableColumnModel.
   * @returns the SortableColumnModel matching the colName.
   */
  public getSortableColumn(colName: string): SortableColumnModel {
    for (const col of this.sortableColumns) {
      if (col.colName === colName) {
        return col;
      }
    }
    return new SortableColumnModel('', false, false, false, false);
  }

  /**
   * Set the Table Columns model.
   */
  private setSortableColumns(): void {
    const defaultSortColumns = [
      'name',
      'paymentDate',
      'beginningBalance',
      'incurredAmt',
      'paymentAmt',
      'closingBalance'
    ];
    const otherSortColumns = [];

    this.sortableColumns = [];
    for (const field of defaultSortColumns) {
      this.sortableColumns.push(new SortableColumnModel(field, false, true, true, false));
    }

    for (const field of otherSortColumns) {
      this.sortableColumns.push(new SortableColumnModel(field, false, false, false, true));
    }
  }

  /**
   * Print a Debt.
   */
  public printDebt(debt: DebtSummaryModel): void {
    alert('Print Debt is not yet supported');
  }

  /**
   * Print all Debts selected by the user.
   */
  public printAllSelected(): void {
    alert('Print all Debts is not yet supported');
  }

  /**
   * Export all Debts selected by the user.
   */
  public exportAllSelected(): void {
    alert('Export all Debts is not yet supported');
  }

  /**
   * Show edit for a debt transaction.
   */
  public editDebt(debt: DebtSummaryModel, payment: boolean) {
    const emptyValidForm = {};

    const transactionModel: any = {
      transactionId: debt.transactionId,
      type: debt.transactionTypeDescription,
      transactionTypeIdentifier: debt.transactionTypeIdentifier,
      apiCall: '/sd/schedD' // should come from API
    };
    if (payment) {
      transactionModel.scrollDebtPaymentButtonIntoView = true;
    }

    this.status.emit({
      form: emptyValidForm,
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      action: DebtSumarysActions.edit,
      scheduleType: 'sched_d',
      mainTransactionTypeText: 'Loans and Debts',
      returnToDebtSummary: true,
      returnToDebtSummaryInfo: {
        transactionType: this.transactionType,
        transactionTypeText: this.transactionTypeText
      },
      transactionDetail: {
        transactionModel: transactionModel
      }
    });
  }

  public editDebtPayment(debtPayment: DebtSummaryModel) {
    const emptyValidForm = {};
    this.status.emit({
      form: emptyValidForm,
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      action: DebtSumarysActions.edit,
      scheduleType: debtPayment.scheduleType,
      mainTransactionTypeText: 'Loans and Debts',
      returnToDebtSummary: true,
      returnToDebtSummaryInfo: {
        transactionType: this.transactionType,
        transactionTypeText: this.transactionTypeText
      },
      transactionDetail: {
        transactionModel: {
          transactionId: debtPayment.transactionId,
          type: debtPayment.transactionTypeDescription,
          transactionTypeIdentifier: debtPayment.transactionTypeIdentifier,
          apiCall: debtPayment.apiCall,
          date: debtPayment.paymentDate,
          amount: debtPayment.paymentAmt,
          memoCode: debtPayment.memoCode,
          aggregate: debtPayment.aggregate,
          entityId: debtPayment.entityId
        }
      }
    });
  }

  /**
   * Trash the transaction selected by the user.
   *
   * @param debt the Transaction to trash
   */
  public trashDebt(debt: DebtSummaryModel): void {
    const trx = new TransactionModel({});
    trx.transactionId = debt.transactionId;
    this._dialogService
      .confirm(
        'You are about to delete this transaction ' + debt.transactionId + '.',
        ConfirmModalComponent,
        'Caution!'
      )
      .then(res => {
        if (res === 'okay') {
          this._debtSummaryService.deleteDebt(debt).subscribe((res2: any) => {
            this.getDebtSummaries(this.config.currentPage);
            this._dialogService.confirm(
              'Transaction has been successfully deleted and sent to the recycle bin. ' + debt.transactionId,
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

  /**
   * Trash the debt payment.
   *
   * @param payment the payment to trash
   */
  public trashDebtPayment(payment: DebtSummaryModel): void {
    const trx = new TransactionModel({});
    trx.transactionId = payment.transactionId;
    this._dialogService
      .confirm(
        'You are about to delete this transaction ' + payment.transactionId + '.',
        ConfirmModalComponent,
        'Caution!'
      )
      .then(res => {
        if (res === 'okay') {
          this._transactionsService
            .trashOrRestoreTransactions('3X', 'trash', payment.reportId, [trx])
            .subscribe((res: GetTransactionsResponse) => {
              this.getDebtSummaries(this.config.currentPage);
              this._dialogService.confirm(
                'Transaction has been successfully deleted and sent to the recycle bin. ' + payment.transactionId,
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

  /**
   * Trash all Loans selected by the user.
   */
  public trashAllSelected(): void {
    let trxIds = '';
    let reportId = null;
    const selectedTransactions: Array<any> = [];
    for (const trx of this.debtModel) {
      if (trx.selected) {
        reportId = trx.reportId;
        selectedTransactions.push({
          transactionId: trx.transactionId,
          reportId: trx.reportId
        });
        trxIds += trx.transactionId + ', ';
      }
    }
    if (trxIds.length > 2) {
      trxIds = trxIds.substr(0, trxIds.length - 2);
    }

    this._dialogService
      .confirm('You are about to delete these transactions.   ' + trxIds, ConfirmModalComponent, 'Caution!')
      .then(res => {
        if (res === 'okay') {
          this._transactionsService
            .trashOrRestoreTransactions(this.formType, 'trash', reportId, selectedTransactions)
            .subscribe((res: any) => {
              this.getDebtSummaries(this.config.currentPage);
              let afterMessage = '';
              if (selectedTransactions.length === 1) {
                afterMessage = `Transaction ${selectedTransactions[0].transactionId}
                has been successfully deleted and sent to the recycle bin.`;
              } else {
                afterMessage = 'Transactions have been successfully deleted and sent to the recycle bin.   ' + trxIds;
              }

              this._dialogService.confirm(
                afterMessage,
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
}
