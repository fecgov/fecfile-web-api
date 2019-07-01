import { Component, Input, OnInit, ViewEncapsulation, ViewChild, OnDestroy } from '@angular/core';
import { style, animate, transition, trigger } from '@angular/animations';
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
import { ConfirmModalComponent, ModalHeaderClassEnum } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { TransactionFilterModel } from '../model/transaction-filter.model';



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
      transition(':enter', [
        style({ opacity: 0 }),
        animate(500, style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate(0, style({ opacity: 0 }))
      ])
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
  public tableType: string;

  public transactionsModel: Array<TransactionModel>;
  public totalAmount: number;
  public transactionsView = ActiveView.transactions;
  public recycleBinView = ActiveView.recycleBin;
  public bulkActionDisabled = true;
  public bulkActionCounter = 0;

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


  // Local Storage Keys
  private readonly transactionSortableColumnsLSK =
    'transactions.trx.sortableColumn';
  private readonly recycleSortableColumnsLSK =
    'transactions.recycle.sortableColumn';
  private readonly transactionCurrentSortedColLSK =
    'transactions.trx.currentSortedColumn';
  private readonly recycleCurrentSortedColLSK =
    'transactions.recycle.currentSortedColumn';
  private readonly transactionPageLSK =
    'transactions.trx.page';
  private readonly recyclePageLSK =
    'transactions.recycle.page';
  private readonly filtersLSK =
    'transactions.filters';

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
   * to the transactions obtained from the server.
   */
  private keywordFilterSearchSubscription: Subscription;

  private columnOptionCount = 0;
  private readonly maxColumnOption = 5;
  private allTransactionsSelected: boolean;

  constructor(
    private _transactionsService: TransactionsService,
    private _transactionsMessageService: TransactionsMessageService,
    private _tableService: TableService,
    private _utilService: UtilService,
    private _dialogService: DialogService,
  ) {
    this.showPinColumnsSubscription = this._transactionsMessageService.getShowPinColumnMessage()
      .subscribe(
        message => {
          this.showPinColumns();
        }
      );

    this.keywordFilterSearchSubscription = this._transactionsMessageService.getDoKeywordFilterSearchMessage()
      .subscribe(
        (filters: TransactionFilterModel) => {

          if (filters) {
            this.filters = filters;
            if (filters.formType) {
              this.formType = filters.formType;
            }
          }
          this.getPage(this.config.currentPage);
        }
      );
  }


  /**
   * Initialize the component.
   */
  public ngOnInit(): void {

    // reportId is converted to String when used as @Input().  Convert back to Number.
    // If it can't be converted, make it 0.
    // this.reportId = isNaN(this.reportId) ? Number(this.reportId) : this.reportId;

    // if (typeof this.reportId === 'string') {
    //   this.reportId = Number(this.reportId);
    // }
    // this.reportId = isNaN(this.reportId) ? 0 : this.reportId;

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
    this.getPage(this.config.currentPage);
  }


  /**
   * A method to run when component is destroyed.
   */
  public ngOnDestroy(): void {
    this.setCachedValues();
    this.showPinColumnsSubscription.unsubscribe();
    this.keywordFilterSearchSubscription.unsubscribe();
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
        this.getTransactionsPage(page);
        break;
      case this.recycleBinView:
        this.getRecyclingPage(page);
        break;
      default:
        break;
    }
  }


  /**
	 * The Transactions for a given page.
	 *
	 * @param page the page containing the transactions to get
	 */
  public getTransactionsPage(page: number): void {

    this.config.currentPage = page;

    let sortedCol: SortableColumnModel =
      this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);

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

    // // temp fix for sprint 13 demo
    // if (this.currentSortedColumnName === 'default') {
    //   this.currentSortedColumnName = 'name';
    // }

    const serverSortColumnName = this._transactionsService.
      mapToSingleServerName(this.currentSortedColumnName);

    this._transactionsService.getFormTransactions(this.formType, this.reportId,
        page, this.config.itemsPerPage,
        serverSortColumnName, sortedCol.descending, this.filters)
      .subscribe((res: GetTransactionsResponse) => {
        this.transactionsModel = [];

        // // because the backend receives 'default' as the column name
        // // AND because 'default' is not a column known to this component in
        // // this.sortableColumns, we must tell it make the name column appear sorted.
        // // Ideally the columns name and direction sorted should come back in the response
        // // from the API call.  TODO do this in other sprint/release.
        // // Or change the API interface to accept a flag for default rather than using
        // // the column name.

        // if (this.currentSortedColumnName === 'default') {
        //   this.currentSortedColumnName = this._tableService.changeSortDirection('name', this.sortableColumns);
        // }

        this._transactionsService.addUIFileds(res);

        const transactionsModelL = this._transactionsService.mapFromServerFields(res.transactions);
        this.transactionsModel = transactionsModelL;

        this.totalAmount = res.totalAmount ? res.totalAmount : 0;
        this.config.totalItems = res.totalTransactionCount ? res.totalTransactionCount : 0;
        this.allTransactionsSelected = false;
      });
  }


  /**
	 * The Transactions for the recycling bin.
	 *
	 * @param page the page containing the transactions to get
	 */
  public getRecyclingPage(page: number): void {

    this.calculateNumberOfPages();

    let sortedCol: SortableColumnModel =
      this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);

    if (sortedCol) {
      if (sortedCol.descending === undefined || sortedCol.descending === null) {
        sortedCol.descending = false;
      }
    } else {
      sortedCol = new SortableColumnModel('', false, false, false, false);
    }

    // temp fix for sprint 13 demo
    if (this.currentSortedColumnName === 'default') {
      this.currentSortedColumnName = 'name';
    }

    const serverSortColumnName = this._transactionsService.
    mapToSingleServerName(this.currentSortedColumnName);

    this._transactionsService.getUserDeletedTransactions(this.formType, this.reportId,
      page, this.config.itemsPerPage,
      serverSortColumnName, sortedCol.descending, this.filters)
      .subscribe((res: GetTransactionsResponse) => {

        this._transactionsService.addUIFileds(res);
        this._transactionsService.mockApplyFilters(res, this.filters);
        const transactionsModelL = this._transactionsService.mapFromServerFields(res.transactions);

        this.transactionsModel = this._transactionsService.sortTransactions(
          transactionsModelL, this.currentSortedColumnName, sortedCol.descending);

        this.config.totalItems = res.totalTransactionCount;

        // If a row was deleted, the current page may be greated than the last page
        // as result of the delete.
        this.config.currentPage = (page > this.numberOfPages && this.numberOfPages !== 0)
          ? this.numberOfPages : page;
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
      if (!sortableCol.checked && this.columnOptionCount >
        (this.maxColumnOption - 1)) {
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
    if (this.columnOptionCount > (this.maxColumnOption - 1)) {
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
    const checked = (e.target.checked) ? true : false;
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
    alert('Print all transactions is not yet supported');
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
   * Trash all transactions selected by the user.
   */
  public trashAllSelected(): void {
    // alert('Trash all transactions is not yet supported');

    let trxIds = '';
    const selectedTransactions: Array<TransactionModel> = [];
    for (const trx of this.transactionsModel) {
      if (trx.selected) {
        selectedTransactions.push(trx);
        trxIds += trx.transactionId + ', ';
      }
    }

    // trxIds.trimRight();
    // trxIds = trxIds.trimRight();
    trxIds = trxIds.substr(0, trxIds.length - 2);

    this._dialogService
    .confirm('You are about to delete these transactions. ' + trxIds,
      ConfirmModalComponent,
      'Caution!')
    .then(res => {
      if (res === 'okay') {
        this._transactionsService.trashOrRestoreTransactions('trash', this.reportId, this.transactionsModel)
          .subscribe((res: GetTransactionsResponse) => {
            this.getTransactionsPage(this.config.currentPage);
            this._dialogService
              .confirm('Transaction has been successfully deleted and sent to the recycle bin. '
                + trxIds,
                ConfirmModalComponent, 'Success!', false, ModalHeaderClassEnum.successHeader);
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


  /**
   * Trash the transaction selected by the user.
   *
   * @param trx the Transaction to trash
   */
  public trashTransaction(trx: TransactionModel): void {

    this._dialogService
    .confirm('You are about to delete this transaction ' + trx.transactionId + '.',
      ConfirmModalComponent,
      'Caution!')
    .then(res => {
      if (res === 'okay') {
        this._transactionsService.trashOrRestoreTransactions('trash', this.reportId, [trx])
          .subscribe((res: GetTransactionsResponse) => {
            this.getTransactionsPage(this.config.currentPage);
            this._dialogService
              .confirm('Transaction has been successfully deleted and sent to the recycle bin.'
                + trx.transactionId,
                ConfirmModalComponent, 'Success!', false, ModalHeaderClassEnum.successHeader);
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
      .confirm('You are about to restore transaction ' + trx.transactionId + '.',
        ConfirmModalComponent,
        'Caution!')
      .then(res => {
        if (res === 'okay') {
          // this._transactionsService.restoreTransaction(trx)
          //   .subscribe((res: GetTransactionsResponse) => {
          this._transactionsService.trashOrRestoreTransactions('restore', this.reportId, [trx])
            .subscribe((res: GetTransactionsResponse) => {
              this.getRecyclingPage(this.config.currentPage);
              this._dialogService
                .confirm('Transaction ' + trx.transactionId + ' has been restored!',
                  ConfirmModalComponent, 'Success!', false, ModalHeaderClassEnum.successHeader);
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

    let beforeMessage = '';
    // if (this.bulkActionCounter === 1) {
    //   let id = '';
    //   for (const trx of this.transactionsModel) {
    //     if (trx.selected) {
    //       id = trx.transactionId;
    //     }
    //   }
    //   beforeMessage = (id !== '') ?
    //     'Are you sure you want to permanently delete Transaction ' + id + '?' :
    //     'Are you sure you want to permanently delete this Transaction?';
    // } else {
    //   beforeMessage = 'Are you sure you want to permanently delete these transactions?';
    // }

    const selectedTransactions: Array<TransactionModel> = [];
    for (const trx of this.transactionsModel) {
      if (trx.selected) {
        selectedTransactions.push(trx);
      }
    }

    if (selectedTransactions.length === 1) {
      beforeMessage = 'Are you sure you want to permanently delete Transaction ' +
        selectedTransactions[0].transactionId + '?';
    } else {
      beforeMessage = 'Are you sure you want to permanently delete these transactions?';
    }

    this._dialogService
      .confirm(beforeMessage,
        ConfirmModalComponent,
        'Caution!')
      .then(res => {
        if (res === 'okay') {
          this._transactionsService.deleteRecycleBinTransaction(selectedTransactions)
            .subscribe((res: GetTransactionsResponse) => {
              this.getRecyclingPage(this.config.currentPage);

              let afterMessage = '';
              if (selectedTransactions.length === 1) {
                  afterMessage = `Transaction ${selectedTransactions[0].transactionId} has been successfully deleted`;
              } else {
                afterMessage = 'Transactions have been successfully deleted.';
              }
              this._dialogService
                .confirm(afterMessage,
                  ConfirmModalComponent, 'Success!', false, ModalHeaderClassEnum.successHeader);
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
    this.numberOfPages = 0;
    this.config.currentPage = this._utilService.isNumber(this.config.currentPage) ?
      this.config.currentPage : 1;

    if (!this.transactionsModel) {
      return '0';
    }

    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0
      && this.transactionsModel.length > 0) {
      this.calculateNumberOfPages();

      if (this.config.currentPage === this.numberOfPages) {
        end = this.transactionsModel.length;
        start = (this.config.currentPage - 1) * this.config.itemsPerPage + 1;
      } else {
        end = this.config.currentPage * this.config.itemsPerPage;
        start = (end - this.config.itemsPerPage) + 1;
      }
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
    for (let i = (this.firstItemOnPage - 1); i <= (this.lastItemOnPage - 1); i++) {
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
    this.bulkActionDisabled = (this.bulkActionCounter > count) ? false : true;
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
        this._tableService.getColumnByName(col.colName,
          this.sortableColumns).visible = col.visible;
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
    const currentSortedColumnJson: string | null =
      localStorage.getItem(key);
    let currentSortedColumnL: SortableColumnModel = null;
    if (currentSortedColumnJson) {
      currentSortedColumnL = JSON.parse(currentSortedColumnJson);

      // sort by the column direction previously set
      this.currentSortedColumnName = this._tableService.setSortDirection(currentSortedColumnL.colName,
        this.sortableColumns, currentSortedColumnL.descending);
    } else {
      this.setSortDefault();
    }
  }


  /**
   * Get the current page from the cache and apply it to the component.
   * @param key the key to the value in the local storage cache
   */
  private applyCurrentPageCache(key: string) {
    const currentPageCache: string =
      localStorage.getItem(key);
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
        this.setCacheValuesforView(this.transactionSortableColumnsLSK,
          this.transactionCurrentSortedColLSK, this.transactionPageLSK);
        break;
      case this.recycleBinView:
        this.setCacheValuesforView(this.recycleSortableColumnsLSK,
          this.recycleCurrentSortedColLSK, this.recyclePageLSK);
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
  private setCacheValuesforView(columnsKey: string, sortedColKey: string,
    pageKey: string) {

    // shared between trx and recycle tables
    localStorage.setItem(columnsKey,
      JSON.stringify(this.sortableColumns));

    // shared between trx and recycle tables
    localStorage.setItem(this.filtersLSK,
      JSON.stringify(this.filters));

    const currentSortedCol = this._tableService.getColumnByName(
      this.currentSortedColumnName, this.sortableColumns);
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
    // sort column names must match the domain model names
    // Mahendra FNE-914
    // const defaultSortColumns = ['type', 'transactionId', 'name', 'date', 'amount'];

    // const defaultSortColumns = ['type', 'name', 'date', 'amount', 'aggregate'];
    // const otherSortColumns = ['transactionId', 'street', 'city', 'state', 'zip', 'purposeDescription',
    //   'contributorEmployer', 'contributorOccupation', 'memoCode', 'memoText'];

    const defaultSortColumns = ['type', 'name', 'date', 'amount', 'aggregate'];
    const otherSortColumns = ['transactionId', 'street', 'city', 'state', 'zip', 'purposeDescription',
      'contributorEmployer', 'contributorOccupation', 'memoCode', 'memoText'];

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
    // this.currentSortedColumnName = this._tableService.setSortDirection('name',
    //   this.sortableColumns, false);

    // this.currentSortedColumnName = this._tableService.setSortDirection('default',
    //   this.sortableColumns, false);

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
