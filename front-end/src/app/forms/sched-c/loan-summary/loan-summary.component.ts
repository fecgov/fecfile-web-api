import { ReportTypeService } from './../../form-3x/report-type/report-type.service';
import { TransactionsService } from './../../transactions/service/transactions.service';
import { Component, Input, OnInit, ViewEncapsulation, ViewChild, OnDestroy, Output, EventEmitter, SimpleChanges  } from '@angular/core';
import { PaginationInstance } from 'ngx-pagination';
import { ModalDirective } from 'ngx-bootstrap/modal';
import { LoanModel } from '../model/loan.model';
import { SortableColumnModel } from '../../../shared/services/TableService/sortable-column.model';
import { LoanService, GetLoanResponse } from '../../sched-c/service/loan.service';
import { TableService } from '../../../shared/services/TableService/table.service';
import { UtilService } from '../../../shared/utils/util.service';
import { LoanMessageService } from '../../sched-c/service/loan-message.service';
import { Subscription } from 'rxjs/Subscription';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from '../../../shared/services/DialogService/dialog.service';
import { CONTEXT_NAME } from '@angular/compiler/src/render3/view/util';
import { ScheduleActions } from '../../form-3x/individual-receipt/schedule-actions.enum';
import { TransactionModel } from '../../transactions/model/transaction.model';

export enum ActiveView {
  loanSummary = 'loanSummary',
  recycleBin = 'recycleBin',
  edit = 'edit'
}

export enum loanSumarysActions {
  add = 'add',
  edit = 'edit'
}

@Component({
  selector: 'app-loansummary',
  templateUrl: './loan-summary.component.html',
  styleUrls: ['./loan-summary.component.scss'],
  encapsulation: ViewEncapsulation.None,
  /* animations: [
    trigger('fadeInOut', [
      transition(':enter', [style({ opacity: 0 }), animate(500, style({ opacity: 1 }))]),
      transition(':leave', [animate(0, style({ opacity: 0 }))])
    ])
  ] */
})
export class LoanSummaryComponent implements OnInit, OnDestroy {
  @ViewChild('columnOptionsModal')
  public columnOptionsModal: ModalDirective;

  @Input()
  public formType: string;

  @Input()
  public reportId: string;

  @Input()
  public tableType: string;

  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  //TODO-ZS -- change "any" to LoanModel when using actual data
  public LoanModel: Array<any>;

  public totalAmount: number;
  public LoanView = ActiveView.loanSummary;
  public recycleBinView = ActiveView.recycleBin;
  public bulkActionDisabled = true;
  public bulkActionCounter = 0;

  // ngx-pagination config
  public maxItemsPerPage = 100;
  public directionLinks = false;
  public autoHide = true;
  public config: PaginationInstance;
  public numberOfPages = 0;

  //private filters: ContactFilterModel;
  // private keywords = [];
  private firstItemOnPage = 0;
  private lastItemOnPage = 0;

  // Local Storage Keys
  private readonly loanSortableColumnsLSK = 'Loan.ctn.sortableColumn';
  private readonly recycleSortableColumnsLSK = 'Loan.recycle.sortableColumn';
  private readonly loanCurrentSortedColLSK = 'Loan.ctn.currentSortedColumn';
  private readonly recycleCurrentSortedColLSK = 'Loan.recycle.currentSortedColumn';
  private readonly loanPageLSK = 'Loan.ctn.page';
  private readonly recyclePageLSK = 'Loan.recycle.page';
  private readonly filtersLSK = 'Loan.filters';

  /**.
   * Array of columns to be made sortable.
   */
  private sortableColumns: SortableColumnModel[] = [];

  /**
   * A clone of the sortableColumns for reverting user
   * column options on a Cancel.
   */
  private cloneSortableColumns: SortableColumnModel[] = [];

  /**
   * Identifies the column currently sorted by name.
   */
  private currentSortedColumnName: string;

  /**
   * Subscription for messags sent from the parent component to show the PIN Column
   * options.
   */
  private showPinColumnsSubscription: Subscription;

  /**
   * Subscription for running the keyword and filter search
   * to the Loan obtained from the server.
   */
  private keywordFilterSearchSubscription: Subscription;

  private columnOptionCount = 0;
  private maxColumnOption = 5;
  public allLoanSelected: boolean;
  public currentPageNumber: number = 1;
  private _loanSummaryRefreshDataSubscription: Subscription;

  constructor(
    private _LoanService: LoanService,
    private _LoanMessageService: LoanMessageService,
    private _tableService: TableService,
    private _utilService: UtilService,
    private _dialogService: DialogService,
    private _transactionService: TransactionsService,
    private _reportTypeService: ReportTypeService
  ) {
    this.showPinColumnsSubscription = this._LoanMessageService.getShowPinColumnMessage().subscribe(message => {
      this.showPinColumns();
    });

    this.keywordFilterSearchSubscription = this._LoanMessageService
      .getDoKeywordFilterSearchMessage()
      .subscribe(message => {
        this.getPage(this.config.currentPage);
      });

    this._loanSummaryRefreshDataSubscription = this._LoanMessageService
      .getLoanSummaryRefreshMessage()
      .subscribe(message => {
        this.loadPage(message);
      });
  }
  /**
   * Initialize the component.
   */
  public ngOnInit(): void {
    //intentionally left blank as component intitialized in ngOnChanges()
  }

  public ngOnChanges(changes: SimpleChanges): void {
    // If Report ID is not provided by parent component, get it from local storage.
    if (!this.reportId || this.reportId === '0') {
      this.reportId = this._reportTypeService.getReportIdFromStorage(this.formType);
    }
    this.loadPage();
  }

  private loadPage(message: any = null) {
    const paginateConfig: PaginationInstance = {
      id: 'forms__ctn-table-pagination',
      itemsPerPage: 10,
      currentPage: this.currentPageNumber
    };
    this.config = paginateConfig;
    // this.config.currentPage = 1;
    this.tableType = ActiveView.loanSummary;
    this.getCachedValues();
    this.cloneSortableColumns = this._utilService.deepClone(this.sortableColumns);
    for (const col of this.sortableColumns) {
      if (col.checked) {
        this.columnOptionCount++;
      }
    }
    this.getPage(this.config.currentPage, message);
  }

  public goToPage(pageEvent: any) {
    //console.log(pageEvent);
    this.currentPageNumber = pageEvent;
  }

  /**
   * A method to run when component is destroyed.
   */
  public ngOnDestroy(): void {
    this.setCachedValues();
    this.showPinColumnsSubscription.unsubscribe();
    this.keywordFilterSearchSubscription.unsubscribe();
    this._loanSummaryRefreshDataSubscription.unsubscribe();
  }

  /**
   * The Loan for a given page.
   *
   * @param page the page containing the Loan to get
   */
  public getPage(page: number, message: any = null): void {
    this.bulkActionCounter = 0;
    this.bulkActionDisabled = true;
    //console.log(" getPage this.tableType", this.tableType)
    switch (this.tableType) {
      case this.LoanView:
        this.getLoanPage(page, message);
        break;
      default:
        break;
    }
  }

  /**
   * The Loan for a given page.
   *
   * @param page the page containing the Loan to get
   */
  public getLoanPage(page: number, message: any = null): void {
    this.config.currentPage = page;

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

    const serverSortColumnName = this._LoanService.mapToSingleServerName(this.currentSortedColumnName);

    this._LoanService
      .getLoan(message)
      //TODO : ZS -- change resType back to  GetLoanResponse once service is fixed
      .subscribe((res: any) => {
        // res=this.tempApiResponse;
        //console.log(" getLoanPage res =", res)
        this.LoanModel = [];

        // fixes an issue where no items shown when current page != 1 and new filter
        // result has only 1 page.
        if (res.totalPages === 1) {
          this.config.currentPage = 1;
        }

        //TODO - ZS -- this is temporary fix to map fields to the right attributes until service response is fixed
        res.forEach(element => {
          //set name
          if (element.entity_type === 'IND') {
            element.name = `${element.last_name}, ${element.first_name}`;
          } else if (element.entity_type === 'ORG') {
            element.name = element.entity_name;
          }

          //add endorser and c1 check flags to decide whether to show or not in expansion accordion.
          if (element.child && element.child.length > 0) {
            let c1childArray = element.child.filter(cElement => {
              return cElement.transaction_type_identifier === 'SC1';
            });
            if (c1childArray.length > 0) {
              element.hasC1 = true;
            }

            let c2childArray = element.child.filter(cElement => {
              return cElement.transaction_type_identifier === 'SC2';
            });
            if (c2childArray.length > 0) {
              element.hasC2 = true;
            }
          }
        });

        this._LoanService.addUIFileds(res);
        this._LoanService.mockApplyFilters(res);
        const LoanModelL = this._LoanService.mapFromServerFields(res);
        this.LoanModel = LoanModelL;

        this.config.totalItems = res.totalloansCount ? res.totalloansCount : 0;
        this.numberOfPages = res.totalPages;
        this.allLoanSelected = false;
      });
  }

  public goToC1(loan: any) {
    const c1Exists = this._LoanService.c1Exists(loan);
    const c1EmitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c1',
      action: c1Exists ? ScheduleActions.edit : ScheduleActions.add,
      transactionDetail: {
        transactionModel: {
          transactionId: loan.transaction_id
        }
      }
    };
    this.status.emit(c1EmitObj);
  }

  public goToEndorserSummary(loan: any) {
    const c1EmitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c_es',
      action: ScheduleActions.add,
      transactionDetail: {
        transactionModel: {
          endorser: {
            back_ref_transaction_id: loan.transaction_id
          }
        }
      }
    };
    this.status.emit(c1EmitObj);
  }

  public editLoanRepayment(payment: any) {
    const loanRepaymentEmitObj: any = {
      form: {},
      direction: 'next', //TODO-zs -- does this need to be changed?
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c_loan_payment',
      action: ScheduleActions.edit,
      transactionDetail: {
        transactionModel: {
          backRefTransactionId: payment.back_ref_transaction_id,
          transactionId: payment.transaction_id,
          entityId: payment.entity_id,
          apiCall: payment.api_call,
          transactionTypeIdentifier: payment.transaction_type_identifier,
          date: payment.expenditure_date,
          amount: payment.expenditure_amount,
          purposeDescription: payment.expenditure_purpose,
          memoText: payment.memo_text
        }
      }
    };
    this.status.emit(loanRepaymentEmitObj);
  }

  public deleteLoanRepayment(payment: any) {
    payment.transactionId = payment.transaction_id; //TODO - clean this.
    this._dialogService
      .confirm(
        'You are about to delete this transaction ' + payment.transaction_id + '.',
        ConfirmModalComponent,
        'Caution!'
      )
      .then(res => {
        if (res === 'okay') {
          this._transactionService
            .trashOrRestoreTransactions('3X', 'trash', payment.report_id, [payment])
            .subscribe(res => {
              this.getPage(this.config.currentPage);
              this._dialogService.confirm(
                'Transaction has been successfully deleted. ' + payment.transaction_id,
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

    // TODO this could be done client side or server side.
    // call server for page data in new direction
    // this.getPage(this.config.currentPage);
    this.LoanModel = this._LoanService.sortLoan(this.LoanModel, this.currentSortedColumnName, direction);
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
   * Determine if the column is to be visible in the table.
   *
   * @param colName
   * @returns true if visible
   */
  public isColumnVisible(colName: string): boolean {
    const sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      return sortableCol.visible;
    } else {
      return false;
    }
  }

  /**
   * Set the visibility of a column in the table.
   *
   * @param colName the name of the column to make shown
   * @param visible is true if the columns should be shown
   */
  public setColumnVisible(colName: string, visible: boolean) {
    const sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      sortableCol.visible = visible;
    }
  }

  /**
   * Set the checked property of a column in the table.
   * The checked is true if the column option settings
   * is checked for the column.
   *
   * @param colName the name of the column to make shown
   * @param checked is true if the columns should be shown
   */
  private setColumnChecked(colName: string, checked: boolean) {
    const sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      sortableCol.checked = checked;
    }
  }

  /**
   *
   * @param colName Determine if the checkbox column option should be disabled.
   */
  public disableOption(colName: string): boolean {
    const sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      if (!sortableCol.checked && this.columnOptionCount > this.maxColumnOption - 1) {
        return true;
      }
    }
    return false;
  }

  /**
   * Toggle the visibility of a column in the table.
   *
   * @param colName the name of the column to toggle
   * @param e the click event
   */
  public toggleVisibility(colName: string, e: any) {
    if (!this.sortableColumns) {
      return;
    }

    // only permit 5 checked at a time
    if (e.target.checked === true) {
      this.columnOptionCount = 0;
      for (const col of this.sortableColumns) {
        if (col.checked) {
          this.columnOptionCount++;
        }
        if (this.columnOptionCount > 5) {
          this.setColumnChecked(colName, false);
          e.target.checked = false;
          this.columnOptionCount--;
          return;
        }
      }
    } else {
      this.columnOptionCount--;
    }

    this.applyDisabledColumnOptions();
  }

  /**
   * Disable the unchecked column options if the max is met.
   */
  private applyDisabledColumnOptions() {
    if (this.columnOptionCount > this.maxColumnOption - 1) {
      for (const col of this.sortableColumns) {
        col.disabled = !col.checked;
      }
    } else {
      for (const col of this.sortableColumns) {
        col.disabled = false;
      }
    }
  }

  /**
   * Save the columns to show selected by the user.
   */
  public saveColumnOptions() {
    for (const col of this.sortableColumns) {
      this.setColumnVisible(col.colName, col.checked);
    }
    this.cloneSortableColumns = this._utilService.deepClone(this.sortableColumns);
    this.columnOptionsModal.hide();
  }

  /**
   * Cancel the request to save columns options.
   */
  public cancelColumnOptions() {
    this.columnOptionsModal.hide();
    this.sortableColumns = this._utilService.deepClone(this.cloneSortableColumns);
  }

  /**
   * Toggle checking all types.
   *
   * @param e the click event
   */
  public toggleAllTypes(e: any) {
    const checked = e.target.checked ? true : false;
    for (const col of this.sortableColumns) {
      this.setColumnVisible(col.colName, checked);
    }
  }

  /**
   * Determine if pagination should be shown.
   */
  public showPagination(): boolean {
    if (this.config.totalItems > this.config.itemsPerPage) {
      return true;
    }
    // otherwise, no show.
    return false;
  }

  public printLoan(loan) {
    this._reportTypeService.printPreview('transaction_table_screen', '3X', loan.transaction_id);
  }

  /**
   * View all Loan selected by the user.
   */
  public viewAllSelected(): void {
    alert('View all Loan is not yet supported');
  }

  /**
   * Print all Loan selected by the user.
   */
  public printAllSelected(): void {
    alert('Print all Loan is not yet supported');
  }

  /**
   * Export all Loan selected by the user.
   */
  public exportAllSelected(): void {
    alert('Export all Loan is not yet supported');
  }

  /**
   * Link all Loan selected by the user.
   */
  public linkAllSelected(): void {
    alert('Link multiple loan requirements have not been finalized');
  }

  /**
   * Trash the transaction selected by the user.
   *
   * @param trx the Transaction to trash
   */
  public trashLoan(loan: any): void {
    this._dialogService
      .confirm(
        'You are about to delete this transaction ' + loan.transaction_id + '.',
        ConfirmModalComponent,
        'Caution!'
      )
      .then(res => {
        if (res === 'okay') {
          this._LoanService.deleteLoan(loan).subscribe(res => {
            this.getPage(this.config.currentPage);
            this._dialogService.confirm(
              'Transaction has been successfully deleted. ' + loan.transaction_id,
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
    const selectedTransactions: Array<any> = [];
    for (const trx of this.LoanModel) {
      if (trx.selected) {
        selectedTransactions.push({
          transactionId: trx.transaction_id,
          reportId: this.reportId
        });
        trxIds += trx.transaction_id + ', ';
      }
    }
    if (trxIds.length > 2) {
      trxIds = trxIds.substr(0, trxIds.length - 2);
    }

    this._dialogService
      .confirm('You are about to delete these transactions.   ' + trxIds, ConfirmModalComponent, 'Caution!')
      .then(res => {
        if (res === 'okay') {
          this._transactionService
            .trashOrRestoreTransactions(this.formType, 'trash', this.reportId, selectedTransactions)
            .subscribe((res: any) => {
              this.getPage(this.config.currentPage);
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

  /**
   * Determine the item range shown by the server-side pagination.
   */
  public determineItemRange(): string {
    let start = 0;
    let end = 0;
    // this.numberOfPages = 0;
    this.config.currentPage = this._utilService.isNumber(this.config.currentPage) ? this.config.currentPage : 1;

    if (!this.LoanModel) {
      return '0';
    }

    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0 && this.LoanModel.length > 0) {
      // this.calculateNumberOfPages();

      if (this.config.currentPage === this.numberOfPages) {
        // end = this.LoanModel.length;
        end = this.config.totalItems;
        start = (this.config.currentPage - 1) * this.config.itemsPerPage + 1;
      } else {
        end = this.config.currentPage * this.config.itemsPerPage;
        start = end - this.config.itemsPerPage + 1;
      }
      // // fix issue where last page shown range > total items (e.g. 11-20 of 19).
      // if (end > this.LoanModel.length) {
      //   end = this.LoanModel.length;
      // }
    }
    this.firstItemOnPage = start;
    this.lastItemOnPage = end;
    return start + ' - ' + end;
  }

  /**
   * Show the option to select/deselect columns in the table.
   */
  public showPinColumns() {
    this.applyDisabledColumnOptions();
    this.columnOptionsModal.show();
  }

  /**
   * Check/Uncheck all Loan in the table.
   */
  public changeAllLoanSummrysSelected() {
    this.bulkActionCounter = 0;

    let loansExist = false;
    for (const loan of this.LoanModel) {
      loansExist = true;
      loan.selected = this.allLoanSelected;
      if (this.allLoanSelected) {
        this.bulkActionCounter++;
      }
    }
    if (loansExist) {
      this.bulkActionDisabled = !this.allLoanSelected;
    } else {
      this.bulkActionDisabled = true;
    }
  }

  /**
   * Check if the view to show is Loan.
   */
  public isLoanSummryViewActive() {
    return this.tableType === this.LoanView ? true : false;
  }

  /**
   * Check if the view to show is Recycle Bin.
   */
  public isRecycleBinViewActive() {
    return this.tableType === this.recycleBinView ? true : false;
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
      this.allLoanSelected = false;
      if (this.bulkActionCounter > 0) {
        this.bulkActionCounter--;
      }
    }

    this.bulkActionDisabled = this.bulkActionCounter > 1 ? false : true;
  }

  /**
   * Get cached values from session.
   */
  private getCachedValues() {
    this.applyFiltersCache();
    switch (this.tableType) {
      case this.LoanView:
        this.applyColCache(this.loanSortableColumnsLSK);
        this.applyCurrentSortedColCache(this.loanCurrentSortedColLSK);
        this.applyCurrentPageCache(this.loanPageLSK);
        break;
      case this.recycleBinView:
        this.applyColCache(this.recycleSortableColumnsLSK);
        this.applyColumnsSelected();
        this.applyCurrentSortedColCache(this.recycleCurrentSortedColLSK);
        this.applyCurrentPageCache(this.recyclePageLSK);
        break;
      default:
        break;
    }
  }

  /**
   * Columns selected in the PIN dialog from the Loan view
   * need to be applied to the Recycling Bin table.
   */
  private applyColumnsSelected() {
    const key = this.loanSortableColumnsLSK;
    const sortableColumnsJson: string | null = localStorage.getItem(key);
    if (localStorage.getItem(key) != null) {
      const ctnCols: SortableColumnModel[] = JSON.parse(sortableColumnsJson);
      for (const col of ctnCols) {
        this._tableService.getColumnByName(col.colName, this.sortableColumns).visible = col.visible;
      }
    }
  }

  /**
   * Apply the filters from the cache.
   */
  private applyFiltersCache() {
    const filtersJson: string | null = localStorage.getItem(this.filtersLSK);
  }

  /**
   * Get the column and their settings from the cache and apply it to the component.
   * @param key the key to the value in the local storage cache
   */
  private applyColCache(key: string) {
    const sortableColumnsJson: string | null = localStorage.getItem(key);
    if (localStorage.getItem(key) != null) {
      this.sortableColumns = JSON.parse(sortableColumnsJson);
    } else {
      // Just in case cache has an unexpected issue, use default.
      this.setSortableColumns();
    }
  }

  /**
   * Get the current sorted column from the cache and apply it to the component.
   * @param key the key to the value in the local storage cache
   */
  private applyCurrentSortedColCache(key: string) {
    const currentSortedColumnJson: string | null = localStorage.getItem(key);
    let currentSortedColumnL: SortableColumnModel = null;
    if (currentSortedColumnJson) {
      currentSortedColumnL = JSON.parse(currentSortedColumnJson);

      // sort by the column direction previously set
      this.currentSortedColumnName = this._tableService.setSortDirection(
        currentSortedColumnL.colName,
        this.sortableColumns,
        currentSortedColumnL.descending
      );
    } else {
      this.setSortDefault();
    }
  }

  /**
   * Get the current page from the cache and apply it to the component.
   * @param key the key to the value in the local storage cache
   */
  private applyCurrentPageCache(key: string) {
    const currentPageCache: string = localStorage.getItem(key);
    if (currentPageCache) {
      if (this._utilService.isNumber(currentPageCache)) {
        this.config.currentPage = this._utilService.toInteger(currentPageCache);
      } else {
        this.config.currentPage = 1;
      }
    } else {
      this.config.currentPage = 1;
    }
  }

  /**
   * Retrieve the cahce values from local storage and set the
   * component's class variables.
   */
  private setCachedValues() {
    switch (this.tableType) {
      case this.LoanView:
        this.setCacheValuesforView(this.loanSortableColumnsLSK, this.loanCurrentSortedColLSK, this.loanPageLSK);
        this.loanPageLSK;
        break;
      case this.recycleBinView:
        this.setCacheValuesforView(
          this.recycleSortableColumnsLSK,
          this.recycleCurrentSortedColLSK,
          this.recyclePageLSK
        );
        this.recyclePageLSK;
        break;
      default:
        break;
    }
  }

  /**
   * Set the currently sorted column and current page in the cache.
   *
   * @param columnsKey the column settings key for the cache
   * @param sortedColKey currently sorted column key for the cache
   * @param pageKey current page key from the cache
   */
  private setCacheValuesforView(columnsKey: string, sortedColKey: string, pageKey: string) {
    // shared between ctn and recycle tables
    localStorage.setItem(columnsKey, JSON.stringify(this.sortableColumns));

    const currentSortedCol = this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);
    localStorage.setItem(sortedColKey, JSON.stringify(this.sortableColumns));

    if (currentSortedCol) {
      localStorage.setItem(sortedColKey, JSON.stringify(currentSortedCol));
    }
    localStorage.setItem(pageKey, this.config.currentPage.toString());
  }

  /**
   * Set the Table Columns model.
   */
  private setSortableColumns(): void {
    const defaultSortColumns = [
      'name',
      'loan_amount_original',
      'loan_payment_to_date',
      'loan_balance',
      'loan_due_date'
    ];
    const otherSortColumns = [];

    this.sortableColumns = [];
    for (const field of defaultSortColumns) {
      this.sortableColumns.push(new SortableColumnModel(field, false, true, true, false));
    }

    for (const field of otherSortColumns) {
      this.sortableColumns.push(new SortableColumnModel(field, false, false, false, true));
    }

    //this.sortableColumns.push(new SortableColumnModel('deletedDate', false, true, false, false));
  }

  public editLoanPayment(loan: any) {
    this._goToLoan(loan);
  }

  private _goToLoan(loan: any) {
    const loanRepaymentEmitObj: any = {
      form: {},
      direction: 'next', //TODO-zs -- does this need to be changed?
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c',
      action: ScheduleActions.edit,
      transactionDetail: {
        transactionModel: {
          transaction_id: loan.transaction_id,
          entityId: loan.entity_id
        }
      }
    };
    this.status.emit(loanRepaymentEmitObj);
  }

  public goToLoanRepayment(loan: any) {
    const loanRepaymentEmitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c_loan_payment',
      action: ScheduleActions.add,
      transactionDetail: {
        transactionModel: {
          transactionId: loan.transaction_id,
          entityId: loan.entity_id,
          entryScreenScheduleType: 'sched_c_ls'
        }
      }
    };
    this.status.emit(loanRepaymentEmitObj);
  }

  /**
   * Set the UI to show the default column sorted in the default direction.
   */
  private setSortDefault(): void {
    // this.currentSortedColumnName = this._tableService.setSortDirection('name',
    //   this.sortableColumns, false);

    // this.currentSortedColumnName = this._tableService.setSortDirection('default',
    //   this.sortableColumns, false);

    // When default, the backend will sort by name and loan date
    this.currentSortedColumnName = 'default';
  }

  private calculateNumberOfPages(): void {
    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0) {
      if (this.LoanModel && this.LoanModel.length > 0) {
        this.numberOfPages = this.LoanModel.length / this.config.itemsPerPage;
        this.numberOfPages = Math.ceil(this.numberOfPages);
      }
    }
  }
}
