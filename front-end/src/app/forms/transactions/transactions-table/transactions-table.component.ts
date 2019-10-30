import { Component, Input, OnInit, ViewEncapsulation, ViewChild, OnDestroy } from '@angular/core';
import { style, animate, transition, trigger } from '@angular/animations';
import { ActivatedRoute, NavigationEnd, Router, NavigationStart, RoutesRecognized } from '@angular/router';
import { PaginationInstance } from 'ngx-pagination';
import { ModalDirective } from 'ngx-bootstrap/modal';
import { TransactionModel } from '../model/transaction.model';
import { SortableColumnModel } from 'src/app/shared/services/TableService/sortable-column.model';
import { TransactionsService, GetTransactionsResponse } from '../service/transactions.service';
import { TableService } from 'src/app/shared/services/TableService/table.service';
import { UtilService } from 'src/app/shared/utils/util.service';
import { ActiveView } from '../transactions.component';
import { TransactionsMessageService } from '../service/transactions-message.service';
import { Subscription } from 'rxjs/Subscription';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { TransactionFilterModel } from '../model/transaction-filter.model';
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';
import { environment } from 'src/environments/environment';
import { IndividualReceiptService } from '../../form-3x/individual-receipt/individual-receipt.service';
import { TransactionTypeService } from '../../form-3x/transaction-type/transaction-type.service';
import { ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { filter } from 'rxjs/operators';

const transactionCategoryOptions = [];

@Component({
  selector: 'app-transactions-table',
  templateUrl: './transactions-table.component.html',
  styleUrls: [
    './transactions-table.component.scss',
    '../../../shared/partials/confirm-modal/confirm-modal.component.scss'
  ],
  encapsulation: ViewEncapsulation.None,
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [style({ opacity: 0 }), animate(500, style({ opacity: 1 }))]),
      transition(':leave', [animate(0, style({ opacity: 0 }))])
    ])
  ]
})
export class TransactionsTableComponent implements OnInit, OnDestroy {
  @ViewChild('columnOptionsModal')
  public columnOptionsModal: ModalDirective;

  @Input()
  public formType: string;

  @Input()
  public reportId: string;

  @Input()
  public transactionId: string;

  @Input()
  public routeData: any;

  @Input()
  public tableType: string;

  public transactionsModel: Array<TransactionModel>;
  public totalAmount: number;
  public transactionsView = ActiveView.transactions;
  public recycleBinView = ActiveView.recycleBin;
  public bulkActionDisabled = true;
  public bulkActionCounter = 0;
  public pageReceivedTransactions: boolean = false;
  public pageReceivedReports: boolean = false;
  public transactionCategories: any = [];
  public transactionCategory: string = '';
  public committeeDetails: any;
  public editMode: boolean = false;

  // ngx-pagination config
  public maxItemsPerPage = 10;
  public directionLinks = false;
  public autoHide = true;
  public config: PaginationInstance;
  public numberOfPages = 0;

  private filters: TransactionFilterModel;
  // private keywords = [];
  private firstItemOnPage = 0;
  private lastItemOnPage = 0;
  private _form99Details: any = {};
  private _allTransactions: boolean = false;

  // Local Storage Keys
  private readonly transactionSortableColumnsLSK = 'transactions.trx.sortableColumn';
  private readonly recycleSortableColumnsLSK = 'transactions.recycle.sortableColumn';
  private readonly transactionCurrentSortedColLSK = 'transactions.trx.currentSortedColumn';
  private readonly recycleCurrentSortedColLSK = 'transactions.recycle.currentSortedColumn';
  private readonly transactionPageLSK = 'transactions.trx.page';
  private readonly recyclePageLSK = 'transactions.recycle.page';
  private readonly filtersLSK = 'transactions.filters';

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
   * Subscription for messages sent from the parent component to show the PIN Column
   * options.
   */
  private showPinColumnsSubscription: Subscription;

  /**
   * Subscription for running the keyword and filter search
   * to the transactions obtained from the server.
   */
  private keywordFilterSearchSubscription: Subscription;

  private loadTransactionsSubscription: Subscription;

  private columnOptionCount = 0;
  private maxColumnOption = 6;
  private readonly maxColumnOptionReadOnly = 6;
  private allTransactionsSelected: boolean;
  private clonedTransaction: any;
  private _previousUrl: any;

  constructor(
    private _transactionsService: TransactionsService,
    private _transactionsMessageService: TransactionsMessageService,
    private _tableService: TableService,
    private _utilService: UtilService,
    private _dialogService: DialogService,
    private _reportTypeService: ReportTypeService,
    private _router: Router,
    private _activatedRoute: ActivatedRoute,
    private _receiptService: IndividualReceiptService,
    private _transactionTypeService: TransactionTypeService
  ) {
    this.showPinColumnsSubscription = this._transactionsMessageService.getShowPinColumnMessage().subscribe(message => {
      this.showPinColumns();
    });

    this.keywordFilterSearchSubscription = this._transactionsMessageService
      .getDoKeywordFilterSearchMessage()
      .subscribe((filters: TransactionFilterModel) => {
        if (filters) {
          this.filters = filters;
          if (filters.formType) {
            this.formType = filters.formType;
          }
        }
        this.getPage(this.config.currentPage);
      });

    this.loadTransactionsSubscription = this._transactionsMessageService
      .getLoadTransactionsMessage()
      .subscribe((reportId: any) => {
        this.reportId = reportId;
        this.getPage(this.config.currentPage);
      });

    _activatedRoute.queryParams.subscribe(p => {
      this.transactionCategory = p.transactionCategory;
      this.getPage(1);
      this.clonedTransaction = {};
      this.setSortableColumns();
      if (p.edit === 'true' || p.edit === true) {
        this.editMode = true;
      }
      if (p.allTransactions === true || p.allTransactions === 'true') {
        this._allTransactions = true;
        this.ngOnInit();
        this.getPage(1);
      } else {
        this._allTransactions = false;
      }
    });
  }

  /**
   * Initialize the component.
   */
  public ngOnInit(): void {
    this.committeeDetails = JSON.parse(localStorage.getItem('committee_details'));
    this.pageReceivedTransactions = false;
    this.pageReceivedReports = false;

    const paginateConfig: PaginationInstance = {
      id: 'forms__trx-table-pagination',
      itemsPerPage: this.maxItemsPerPage,
      currentPage: 1
    };
    this.config = paginateConfig;
    // this.config.currentPage = 1;

    this.getCachedValues();
    this.cloneSortableColumns = this._utilService.deepClone(this.sortableColumns);

    for (const col of this.sortableColumns) {
      if (col.checked) {
        this.columnOptionCount++;
      }
    }

    // If this does work send message from f3x when step is reports
    // If it does work, put get reportIdfrom stor in common service
    if (!this.reportId) {
      // this.reportId = this._getReportIdFromStorage();
    }
    if (this.reportId) {
      this.getPage(this.config.currentPage);
    }

    // When coming from transaction route the reportId is not received
    // from the input perhaps due to the ngDoCheck in transactions-component.
    // TODO look at replacing ngDoCheck and reportId as Input()
    // with a message subscription service.
    if (this.routeData) {
      if (this.routeData.accessedByRoute) {
        if (this.routeData.reportId) {
          console.log('reportId for transaction accessed directly by route is ' + this.routeData.reportId);
          this.reportId = this.routeData.reportId;
          this.getPage(this.config.currentPage);
        }
      }
    }

    this._transactionTypeService.getTransactionCategories('3X').subscribe(res => {
      if (res) {
        this.transactionCategories = res.data.transactionCategories;
      }
      for (
        let transactionCategorieIndex = 0;
        transactionCategorieIndex < this.transactionCategories.length;
        transactionCategorieIndex++
      ) {
        for (
          let transactionCategoryOptionIndex = 0;
          transactionCategoryOptionIndex < this.transactionCategories[transactionCategorieIndex].options.length;
          transactionCategoryOptionIndex++
        ) {
          for (
            let transactionCategoryOptionOptionsIndex = 0;
            transactionCategoryOptionOptionsIndex <
            this.transactionCategories[transactionCategorieIndex].options[transactionCategoryOptionIndex].options
              .length;
            transactionCategoryOptionOptionsIndex++
          ) {
            transactionCategoryOptions.push(
              this.transactionCategories[transactionCategorieIndex].options[transactionCategoryOptionIndex].options[
                transactionCategoryOptionOptionsIndex
              ]
            );
          }
        }
      }
    });
    // this.getTransactionsPage(1);
  }

  // /**
  //  * Obtain the Report ID from local storage.
  //  */
  // private _getReportIdFromStorage() {
  //   let reportId = '0';
  //   let form3XReportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));

  //   if (form3XReportType === null || typeof form3XReportType === 'undefined') {
  //     form3XReportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type_backup`));
  //   }

  //   console.log('viewTransactions form3XReportType', form3XReportType);

  //   if (typeof form3XReportType === 'object' && form3XReportType !== null) {
  //     if (form3XReportType.hasOwnProperty('reportId')) {
  //       reportId = form3XReportType.reportId;
  //     } else if (form3XReportType.hasOwnProperty('reportid')) {
  //       reportId = form3XReportType.reportid;
  //     }
  //   }
  //   return reportId;
  // }

  // TODO: DANGER - this ngDoCheck() implementation can get is an infinite loop and should be replaced by a message service
  // public ngDoCheck(): void {
  //   const step: string = this._activatedRoute.snapshot.queryParams.step;
  //   const forceGet: string = this._activatedRoute.snapshot.queryParams.forceGet;

  //   // // TODO replace this with a message.  The report ID is needed when viewing transactions
  //   // // from the indv-recipt.
  //   // if (this.reportId !== undefined && !this.pageReceived) {
  //   //   this.getPage(this.config.currentPage);

  //   //   if (!this.pageReceived) {
  //   //     this.pageReceived = true;
  //   //   }
  //   // }
  //   // // Prevent looping
  //   // if (step !== 'transactions' && !this.routeData.reportId) {
  //   //   this.pageReceived = false;
  //   // }

  //   if (step === 'transactions') {
  //     // if (
  //     //   (this.reportId !== undefined && !this.pageReceivedTransactions) ||
  //     //   (this.reportId !== undefined && forceGet === 'true')
  //     // ) {
  //     if (this.reportId !== undefined && !this.pageReceivedTransactions) {
  //       this.getPage(this.config.currentPage);

  //       if (!this.pageReceivedTransactions) {
  //         this.pageReceivedTransactions = true;
  //       }
  //     }
  //   } else if (step === 'reports') {
  //     if (this.reportId !== undefined && !this.pageReceivedReports) {
  //       this.getPage(this.config.currentPage);

  //       if (!this.pageReceivedReports) {
  //         this.pageReceivedReports = true;
  //       }
  //     }
  //   } else {
  //     // console.log(`step ${step} not supported`);
  //     // if (this.transactionId) {
  //     //   this.getPage(this.config.currentPage);
  //     // }
  //   }
  // }

  /**
   * A method to run when component is destroyed.
   */
  public ngOnDestroy(): void {
    this.setCachedValues();
    this.showPinColumnsSubscription.unsubscribe();
    this.keywordFilterSearchSubscription.unsubscribe();
    this.loadTransactionsSubscription.unsubscribe();
  }

  /**
   * The Transactions for a given page.
   *
   * @param page the page containing the transactions to get
   */
  public getPage(page: number): void {
    this.bulkActionCounter = 0;
    this.bulkActionDisabled = true;

    switch (this.tableType) {
      case this.transactionsView:
      default:
        this.getTransactionsPage(page);
        break;
      case this.recycleBinView:
        this.getRecyclingPage(page);
        break;
    }
  }

  getSubTransactions(transactionId, apiCall) {
    // const reportId = this._getReportIdFromStorage();
    this._receiptService.getDataSchedule(this.reportId, transactionId, apiCall).subscribe(res => {
      if (Array.isArray(res)) {
        for (const trx of res) {
          if (trx.hasOwnProperty('transaction_id')) {
            if (trx.transaction_id === transactionId) {
              if (trx.hasOwnProperty('child')) {
                for (const subTrx of trx.child) {
                  console.log('sub tran id ' + subTrx.transaction_id);
                }
              }
            }
          }
        }
      }
    });
  }

  /**
   * The Transactions for a given page.
   *
   * @param page the page containing the transactions to get
   */
  public getTransactionsPage(page: number): void {
    if (!this.reportId && !this._allTransactions) {
      return;
    }
    this.config.currentPage = page;

    let sortedCol: SortableColumnModel = this._tableService.getColumnByName(
      this.currentSortedColumnName,
      this.sortableColumns
    );

    // smahal: quick fix for sortCol issue not retrived from cache
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

    const serverSortColumnName = this._transactionsService.mapToSingleServerName(this.currentSortedColumnName);

    let categoryType = 'receipts_tran';

    if (this.transactionCategory === 'disbursements') {
      categoryType = 'disbursements_tran';
    } else if (this.transactionCategory === 'loans-and-debts') {
      categoryType = 'loans_tran';
    } else if (this.transactionCategory === 'other') {
      categoryType = 'other_tran';
    }

    this._transactionsService
      .getFormTransactions(
        this.formType,
        this.reportId,
        page,
        this.config.itemsPerPage,
        serverSortColumnName,
        sortedCol.descending,
        this.filters,
        categoryType,
        false,
        this._allTransactions
      )
      .subscribe((res: GetTransactionsResponse) => {
        this.transactionsModel = [];

        // fixes an issue where no items shown when current page != 1 and new filter
        // result has only 1 page.
        if (res.totalPages === 1) {
          this.config.currentPage = 1;
        }

        this._transactionsService.addUIFileds(res);

        const transactionsModelL = this._transactionsService.mapFromServerFields(res.transactions);
        this.transactionsModel = transactionsModelL;

        if (this.clonedTransaction && this.clonedTransaction.hasOwnProperty('transaction_id')) {
          for (
            let transactionModelIndex = 0;
            transactionModelIndex < this.transactionsModel.length;
            transactionModelIndex++
          ) {
            if (this.transactionsModel[transactionModelIndex].transactionId === this.clonedTransaction.transaction_id) {
              this.transactionsModel[transactionModelIndex].cloned = true;
              this.editTransaction(this.transactionsModel[transactionModelIndex]);
            }
          }
        }

        this.totalAmount = res.totalAmount ? res.totalAmount : 0;
        this.config.totalItems = res.totalTransactionCount ? res.totalTransactionCount : 0;
        this.numberOfPages = res.totalPages;
        this.allTransactionsSelected = false;
      });
  }

  public changeTransactionCategory(transactionCategory) {
    this._router.navigate([], {
      queryParams: {
        step: this._activatedRoute.snapshot.queryParams.step,
        reportId: this._activatedRoute.snapshot.queryParams.reportId,
        edit: this._activatedRoute.snapshot.queryParams.edit,
        transactionCategory: transactionCategory,
        allTransactions: this._allTransactions
      }
    });
  }

  /**
   * The Transactions for the recycling bin.
   *
   * @param page the page containing the transactions to get
   */
  public getRecyclingPage(page: number): void {
    this.config.currentPage = page;

    let sortedCol: SortableColumnModel = this._tableService.getColumnByName(
      this.currentSortedColumnName,
      this.sortableColumns
    );

    // smahal: quick fix for sortCol issue not retrived from cache
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

    let categoryType = 'receipts_tran';

    if (this.transactionCategory === 'disbursements') {
      categoryType = 'disbursements_tran';
    } else if (this.transactionCategory === 'loans-and-debts') {
      categoryType = 'loans_tran';
    } else if (this.transactionCategory === 'other') {
      categoryType = 'other_tran';
    }

    this._transactionsService
      .getFormTransactions(
        this.formType,
        this.reportId,
        page,
        this.config.itemsPerPage,
        this.currentSortedColumnName,
        sortedCol.descending,
        this.filters,
        categoryType,
        true,
        this._allTransactions
      )
      .subscribe((res: GetTransactionsResponse) => {
        this.transactionsModel = [];

        // fixes an issue where no items shown when current page != 1 and new filter
        // result has only 1 page.
        if (res.totalPages === 1) {
          this.config.currentPage = 1;
        }

        this._transactionsService.addUIFileds(res);

        this.transactionsModel = res.transactions;

        // handle non-numeric amounts
        // TODO handle this server side in API
        // for (const model of this.transactionsModel) {
        //   model.amount = model.amount ? model.amount : 0;
        //   model.aggregate = model.aggregate ? model.aggregate : 0;
        // }

        this.config.totalItems = res.totalTransactionCount ? res.totalTransactionCount : 0;
        this.numberOfPages = res.totalPages;
        this.allTransactionsSelected = false;
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

    // TODO this could be done client side or server side.
    // call server for page data in new direction
    this.getPage(this.config.currentPage);
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

    // only permit the max checked at a time
    if (e.target.checked === true) {
      this.columnOptionCount = 0;
      for (const col of this.sortableColumns) {
        if (col.checked) {
          this.columnOptionCount++;
        }
        if (this.columnOptionCount > this.maxColumnOptionReadOnly) {
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

  /**
   * View all transactions selected by the user.
   */
  public viewAllSelected(): void {
    alert('View all transactions is not yet supported');
  }

  /**
   * Print all transactions selected by the user.
   */
  public printAllSelected(): void {
    //alert('Print all transactions is not yet supported');
    console.log('TransactionsTableComponent printAllSelected...!');

    let trxIds = '';
    const selectedTransactions: Array<TransactionModel> = [];
    for (const trx of this.transactionsModel) {
      if (trx.selected) {
        selectedTransactions.push(trx);
        trxIds += trx.transactionId + ', ';
      }
    }

    trxIds = trxIds.substr(0, trxIds.length - 2);
    //this._reportTypeService.signandSaveSubmitReport(this.formType, 'Saved' );
    this._reportTypeService.printPreview('transaction_table_screen', '3X', trxIds);
  }

  public printPreview(): void {
    console.log('TransactionsTableComponent printPreview...!');

    this._reportTypeService.printPreview('transaction_table_screen', '3X');
  }

  /**
   * Export all transactions selected by the user.
   */
  public exportAllSelected(): void {
    alert('Export all transactions is not yet supported');
  }

  /**
   * Link all transactions selected by the user.
   */
  public linkAllSelected(): void {
    alert('Link multiple transaction requirements have not been finalized');
  }

  /**
   * Trash (send to Recycling Bin) all transactions selected by the user.
   */
  public trashAllSelected(): void {
    let trxIds = '';
    const selectedTransactions: Array<TransactionModel> = [];
    for (const trx of this.transactionsModel) {
      if (trx.selected) {
        selectedTransactions.push(trx);
        trxIds += trx.transactionId + ', ';
      }
    }

    trxIds = trxIds.substr(0, trxIds.length - 2);

    this._dialogService
      .confirm('You are about to delete these transactions.   ' + trxIds, ConfirmModalComponent, 'Caution!')
      .then(res => {
        if (res === 'okay') {
          this._transactionsService
            .trashOrRestoreTransactions(this.formType, 'trash', this.reportId, selectedTransactions)
            .subscribe((res: GetTransactionsResponse) => {
              this.getTransactionsPage(this.config.currentPage);

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
   * Clone the transaction selected by the user.
   *
   * @param trx the Transaction to clone
   */
  public cloneTransaction(trx: TransactionModel): void {
    this._transactionsService
      .cloneTransaction(trx.transactionId)
      .subscribe((cloneTransactionResponse: TransactionModel) => {
        if (cloneTransactionResponse[0] && cloneTransactionResponse[0].hasOwnProperty('transaction_id')) {
          this.getTransactionsPage(this.config.currentPage);
          this.clonedTransaction = cloneTransactionResponse[0];
        }
      });
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

  public printTransaction(trx: TransactionModel): void {
    this._reportTypeService.printPreview('transaction_table_screen', '3X', trx.transactionId);
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
          this._transactionsService
            .trashOrRestoreTransactions(this.formType, 'trash', this.reportId, [trx])
            .subscribe((res: GetTransactionsResponse) => {
              this.getTransactionsPage(this.config.currentPage);
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

  /**
   * Restore a trashed transaction from the recyle bin.
   *
   * @param trx the Transaction to restore
   */
  public restoreTransaction(trx: TransactionModel): void {
    this._dialogService
      .confirm('You are about to restore transaction ' + trx.transactionId + '.', ConfirmModalComponent, 'Caution!')
      .then(res => {
        if (res === 'okay') {
          // this._transactionsService.restoreTransaction(trx)
          //   .subscribe((res: GetTransactionsResponse) => {
          this._transactionsService
            .trashOrRestoreTransactions(this.formType, 'restore', this.reportId, [trx])
            .subscribe((res: GetTransactionsResponse) => {
              this.getRecyclingPage(this.config.currentPage);
              this._dialogService.confirm(
                'Transaction ' + trx.transactionId + ' has been restored!',
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
   * Delete selected transactions from the the recyle bin.
   *
   * @param trx the Transaction to delete
   */
  public deleteRecyleBin(): void {
    let trxIds = '';
    const selectedTransactions: Array<TransactionModel> = [];
    for (const trx of this.transactionsModel) {
      if (trx.selected) {
        selectedTransactions.push(trx);
        trxIds += trx.transactionId + ', ';
      }
    }
    trxIds = trxIds.substr(0, trxIds.length - 2);

    let beforeMessage = '';
    if (selectedTransactions.length === 1) {
      beforeMessage = `Are you sure you want to permanently delete
       Transaction ${selectedTransactions[0].transactionId}?`;
    } else {
      beforeMessage = 'Are you sure you want to permanently delete these transactions?   ' + trxIds;
    }

    this._dialogService.confirm(beforeMessage, ConfirmModalComponent, 'Caution!').then(res => {
      if (res === 'okay') {
        this._transactionsService
          .deleteRecycleBinTransaction(selectedTransactions)
          .subscribe((res: GetTransactionsResponse) => {
            this.getRecyclingPage(this.config.currentPage);

            let afterMessage = '';
            if (selectedTransactions.length === 1) {
              afterMessage = `Transaction ${selectedTransactions[0].transactionId} has been successfully deleted`;
            } else {
              afterMessage = 'Transactions have been successfully deleted.   ' + trxIds;
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

  private _setF99Details(): void {
    if (this.committeeDetails) {
      if (this.committeeDetails.committeeid) {
        this._form99Details = this.committeeDetails;

        this._form99Details.reason = '';
        this._form99Details.text = '';
        this._form99Details.signee = `${this.committeeDetails.treasurerfirstname} ${this.committeeDetails.treasurerlastname}`;
        this._form99Details.additional_email_1 = '-';
        this._form99Details.additional_email_2 = '-';
        this._form99Details.created_at = '';
        this._form99Details.is_submitted = false;
        this._form99Details.id = '';

        let formSavedObj: any = {
          saved: false
        };
        localStorage.setItem(`form_99_details`, JSON.stringify(this._form99Details));
        localStorage.setItem(`form_99_saved`, JSON.stringify(formSavedObj));
      }
    }
  }

  public checkIfEditMode() {
    if (!this.editMode) {
      this._dialogService
        .confirm(
          'This report has been filed with the FEC. If you want to change, you must Amend the report',
          ConfirmModalComponent,
          'Warning',
          true,
          ModalHeaderClassEnum.warningHeader,
          null,
          'Return to Reports'
        )
        .then(res => {
          if (res === 'okay') {
          } else if (res === 'cancel') {
            this._router.navigate(['/reports']);
          }
        });
    }
  }

  /**
   * Determine the item range shown by the server-side pagination.
   */
  public determineItemRange(): string {
    let start = 0;
    let end = 0;
    // this.numberOfPages = 0;
    this.config.currentPage = this._utilService.isNumber(this.config.currentPage) ? this.config.currentPage : 1;

    if (!this.transactionsModel) {
      return '0';
    }

    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0 && this.transactionsModel.length > 0) {
      // this.calculateNumberOfPages();

      if (this.config.currentPage === this.numberOfPages) {
        // end = this.transactionsModel.length;
        end = this.config.totalItems;
        start = (this.config.currentPage - 1) * this.config.itemsPerPage + 1;
      } else {
        end = this.config.currentPage * this.config.itemsPerPage;
        start = end - this.config.itemsPerPage + 1;
      }
      // // fix issue where last page shown range > total items (e.g. 11-20 of 19).
      // if (end > this.transactionsModel.length) {
      //   end = this.transactionsModel.length;
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
   * Check/Uncheck all transactions in the table.
   */
  public changeAllTransactionsSelected() {
    // TODO Iterating over the trsnactionsModel and setting the selected prop
    // works when we have server-side pagination as the model will only contain
    // transactions for the current page.

    // Until the server is ready for pagination,
    // we are getting the entire set of tranactions (> 500)
    // and must only count and set the selected prop for the items
    // on the current page.

    this.bulkActionCounter = 0;
    // for (const t of this.transactionsModel) {
    //   t.selected = this.allTransactionsSelected;
    //   if (this.allTransactionsSelected) {
    //     this.bulkActionCounter++;
    //   }
    // }

    // TODO replace this with the commented code above when server pagination is ready.
    for (let i = this.firstItemOnPage - 1; i <= this.lastItemOnPage - 1; i++) {
      this.transactionsModel[i].selected = this.allTransactionsSelected;
      if (this.allTransactionsSelected) {
        this.bulkActionCounter++;
      }
    }
    this.bulkActionDisabled = !this.allTransactionsSelected;
  }

  /**
   * Check if the view to show is Transactions.
   */
  public isTransactionViewActive() {
    return this.tableType === this.transactionsView ? true : false;
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
      this.allTransactionsSelected = false;
      if (this.bulkActionCounter > 0) {
        this.bulkActionCounter--;
      }
    }

    // Transaction View shows bulk action when more than 1 checked
    // Recycle Bin shows delete action when 1 or more checked.
    const count = this.isTransactionViewActive() ? 1 : 0;
    this.bulkActionDisabled = this.bulkActionCounter > count ? false : true;
  }

  /**
   * Determine if transactions may be trashed.
   * Transactions tied to a Filed Report may not be trashed.
   * Since all transactions are tied to a single report,
   * only 1 transaction with a reportStatus of FILED is necessary to check.
   * Loop through the array and if any are filed, none may be trashed.
   *
   * @returns true if Transactions are permitted to be trashed.
   */
  public checkIfTrashable(): boolean {
    if (!this.transactionsModel) {
      return false;
    }
    if (this.transactionsModel.length === 0) {
      return false;
    }
    for (const trx of this.transactionsModel) {
      if (trx.reportStatus === 'FILED') {
        return false;
      }
    }
    return true;
  }

  /**
   * Get cached values from session.
   */
  private getCachedValues() {
    this.applyFiltersCache();
    switch (this.tableType) {
      case this.transactionsView:
        this.applyColCache(this.transactionSortableColumnsLSK);
        this.applyCurrentSortedColCache(this.transactionCurrentSortedColLSK);
        this.applyCurrentPageCache(this.transactionPageLSK);
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
   * Columns selected in the PIN dialog from the transactions view
   * need to be applied to the Recycling Bin table.
   */
  private applyColumnsSelected() {
    const key = this.transactionSortableColumnsLSK;
    const sortableColumnsJson: string | null = localStorage.getItem(key);
    if (localStorage.getItem(key) != null) {
      const trxCols: SortableColumnModel[] = JSON.parse(sortableColumnsJson);
      for (const col of trxCols) {
        this._tableService.getColumnByName(col.colName, this.sortableColumns).visible = col.visible;
      }
    }
  }

  /**
   * Apply the filters from the cache.
   */
  private applyFiltersCache() {
    const filtersJson: string | null = localStorage.getItem(this.filtersLSK);
    if (filtersJson != null) {
      this.filters = JSON.parse(filtersJson);
    } else {
      // Just in case cache has an unexpected issue, use default.
      this.filters = null;
    }
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
      case this.transactionsView:
        this.setCacheValuesforView(
          this.transactionSortableColumnsLSK,
          this.transactionCurrentSortedColLSK,
          this.transactionPageLSK
        );
        break;
      case this.recycleBinView:
        this.setCacheValuesforView(
          this.recycleSortableColumnsLSK,
          this.recycleCurrentSortedColLSK,
          this.recyclePageLSK
        );
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
    // shared between trx and recycle tables
    localStorage.setItem(columnsKey, JSON.stringify(this.sortableColumns));

    // shared between trx and recycle tables
    localStorage.setItem(this.filtersLSK, JSON.stringify(this.filters));

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
    let defaultSortColumns = ['type', 'name', 'date', 'memoCode', 'amount', 'aggregate'];
    let otherSortColumns = [
      'transactionId',
      'street',
      'city',
      'state',
      'zip',
      'purposeDescription',
      'contributorEmployer',
      'contributorOccupation',
      'memoText'
    ];
    if (this.transactionCategory === 'disbursements') {
      defaultSortColumns = ['type', 'name', 'date', 'memoCode', 'amount', 'purposeDescription'];
      otherSortColumns = [
        'transactionId',
        'street',
        'city',
        'state',
        'zip',
        'memoText',
        'committeeId',
        'electionCode',
        'electionYear'
      ];
    } else if (this.transactionCategory === 'loans-and-debts') {
      defaultSortColumns = ['type', 'name', 'loanClosingBalance', 'loanBalance'];
      otherSortColumns = [
        'transactionId',
        'street',
        'city',
        'state',
        'zip',
        'memoCode',
        'memoText',
        'purposeDescription',
        'loanBeginningBalance',
        'loanAmount',
        'loanClosingBalance',
        'loanDueDate',
        'loanIncurredAmt',
        'loanIncurredDate',
        'loanPaymentAmt',
        'loanPaymentToDate'
      ];
    } else if (this.transactionCategory === 'other') {
      // Schedule
      defaultSortColumns = ['', 'type', 'name', 'amount', 'date', 'memoCode', 'purposeDescription'];
      // Activity or Event Identifier
      otherSortColumns = ['transactionId', 'street', 'city', 'state', 'zip', 'memoText', '', ''];
    }

    this.sortableColumns = [];
    for (const field of defaultSortColumns) {
      this.sortableColumns.push(new SortableColumnModel(field, false, true, true, false));
    }
    for (const field of otherSortColumns) {
      this.sortableColumns.push(new SortableColumnModel(field, false, false, false, true));
    }
    this.sortableColumns.push(new SortableColumnModel('deletedDate', false, true, false, false));
  }

  /**
   * Set the UI to show the default column sorted in the default direction.
   */
  private setSortDefault(): void {
    // When default, the backend will sort by name and transaction date
    this.currentSortedColumnName = 'default';
  }

  private calculateNumberOfPages(): void {
    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0) {
      if (this.transactionsModel && this.transactionsModel.length > 0) {
        this.numberOfPages = this.transactionsModel.length / this.config.itemsPerPage;
        this.numberOfPages = Math.ceil(this.numberOfPages);
      }
    }
  }
}
