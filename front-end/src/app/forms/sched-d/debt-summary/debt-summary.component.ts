import { Component, OnInit, ViewEncapsulation, Output, EventEmitter } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';
import { PaginationInstance } from 'ngx-pagination';
import { TableService } from 'src/app/shared/services/TableService/table.service';
import { UtilService } from 'src/app/shared/utils/util.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { SortableColumnModel } from 'src/app/shared/services/TableService/sortable-column.model';
import { DebtSummaryService } from './service/debt-summary.service';
import { DebtSummaryModel } from './model/debt-summary.model';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { TransactionsService } from '../../transactions/service/transactions.service';
import { ReportTypeService } from '../../form-3x/report-type/report-type.service';
import { TransactionModel } from '../../transactions/model/transaction.model';

// export enum ActiveView {
//   debtSummary = 'debtSummary',
//   recycleBin = 'recycleBin',
//   edit = 'edit'
// }

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
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [style({ opacity: 0 }), animate(500, style({ opacity: 1 }))]),
      transition(':leave', [animate(0, style({ opacity: 0 }))])
    ])
  ]
})
export class DebtSummaryComponent implements OnInit {
  @Output()
  public status: EventEmitter<any> = new EventEmitter<any>();

  public debtModel: Array<any>;
  public totalAmount: number;
  public bulkActionDisabled = true;
  public bulkActionCounter = 0;

  // ngx-pagination config
  public maxItemsPerPage = 100;
  public directionLinks = false;
  public autoHide = true;
  public config: PaginationInstance;
  public numberOfPages = 0;

  private firstItemOnPage = 0;
  private lastItemOnPage = 0;

  private allDebtSelected: boolean;
  private currentPageNumber = 1;

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
    private _transactionsService: TransactionsService,
    private _reportTypeService: ReportTypeService
  ) {}

  /**
   * Initialize the component.
   */
  ngOnInit() {
    const paginateConfig: PaginationInstance = {
      id: 'forms__debt-summ-table-pagination',
      itemsPerPage: 10,
      currentPage: this.currentPageNumber
    };
    this.config = paginateConfig;
    this.config.currentPage = 1;

    // TODO decide if sort settings are needed after leaving page.
    // Not supporting cachedVals as of original impl
    this.setSortableColumns();
    // this.getCachedValues();
    // this.cloneSortableColumns = this._utilService.deepClone(this.sortableColumns);

    this.getPage(this.config.currentPage);
  }

  /**
   * The Debt for a given page.
   *
   * @param page the page containing the Debt to get
   */
  public getPage(page: number): void {
    this.bulkActionCounter = 0;
    this.bulkActionDisabled = true;
    this.getDebtPage(page);
  }

  /**
   * The Debts for a given Debt Summary page.
   *
   * @param page the page containing the Debts to get
   */
  public getDebtPage(page: number): void {
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

    this._debtSummaryService
      .getDebts()
      // TODO define type as interface for res once res structure is known
      .subscribe((res: any) => {
        this.debtModel = [];

        // fixes an issue where no items shown when current page != 1 and new filter
        // result has only 1 page.
        // TODO not paginating yet
        // if (res.totalPages === 1) {
        //   this.config.currentPage = 1;
        // }

        // TODO - this is temporary fix to map fields to the right attributes until service response is fixed
        res.forEach((debt: any) => {
          const lastName = debt.last_name ? debt.last_name.trim() : '';
          const firstName = debt.first_name ? debt.first_name.trim() : '';
          const middleName = debt.middle_name ? debt.middle_name.trim() : '';
          const suffix = debt.suffix ? debt.suffix.trim() : '';
          const prefix = debt.prefix ? debt.prefix.trim() : '';

          if (debt.entity_type === 'IND' || debt.entity_type === 'CAN') {
            debt.name = `${lastName}, ${firstName}, ${middleName}, ${prefix}, ${suffix}`;
          } else {
            if (debt.hasOwnProperty('entity_name')) {
              debt.name = debt.entity_name;
            }
          }
        });

        const debtModelL = this._debtSummaryService.mapFromServerFields(res);
        this.debtModel = debtModelL;

        // this.config.totalItems = res.totalDebtsCount ? res.totalDebtsCount : 0;
        this.config.totalItems = this.debtModel ? this.debtModel.length : 0;
        this.numberOfPages = 1; // single page until decide on client or server side pagination // res.totalPages;
        this.allDebtSelected = false;
      });
  }

  /**
   * Check/Uncheck all Debts in the table.
   */
  public changeAllDebtSummarysSelected() {
    // TODO Iterating over the model and setting the selected prop
    // works when we have server-side pagination as the model will only contain
    // Debt for the current page.

    // Until the server is ready for pagination,
    // we are getting the entire set of tranactions (> 500)
    // and must only count and set the selected prop for the items
    // on the current page.

    this.bulkActionCounter = 0;
    // for (const t of this.DebtModel) {
    //   t.selected = this.allDebtSelected;
    //   if (this.allDebtSelected) {
    //     this.bulkActionCounter++;
    //   }
    // }

    // TODO replace this with the commented code above when server pagination is ready.
    for (let i = this.firstItemOnPage - 1; i <= this.lastItemOnPage - 1; i++) {
      this.debtModel[i].selected = this.allDebtSelected;
      if (this.allDebtSelected) {
        this.bulkActionCounter++;
      }
    }
    this.bulkActionDisabled = !this.allDebtSelected;
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

    // Contact View shows bulk action when more than 1 checked
    // Recycle Bin shows delete action when 1 or more checked.
    // const count = this.isDebtSummryViewActive() ? 1 : 0;
    // this.bulkActionDisabled = this.bulkActionCounter > count ? false : true;
  }

  /**
   * Set the UI to show the default column sorted in the default direction.
   */
  private setSortDefault(): void {
    // this.currentSortedColumnName = this._tableService.setSortDirection('name',
    //   this.sortableColumns, false);

    // this.currentSortedColumnName = this._tableService.setSortDirection('default',
    //   this.sortableColumns, false);

    // When default, the backend will sort by name and ???
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

    // TODO this could be done client side or server side.
    // call server for page data in new direction
    // this.getPage(this.config.currentPage);
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
   * Set the Table Columns model.
   */
  private setSortableColumns(): void {
    const defaultSortColumns = ['name', 'beginningBalance', 'incurredAmt', 'paymentAmt', 'closingBalance'];
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
   * Determine the item range shown by the server-side pagination.
   */
  public determineItemRange(): string {
    let start = 0;
    let end = 0;
    // this.numberOfPages = 0;
    this.config.currentPage = this._utilService.isNumber(this.config.currentPage) ? this.config.currentPage : 1;

    if (!this.debtModel) {
      return '0';
    }

    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0 && this.debtModel.length > 0) {
      // this.calculateNumberOfPages();

      if (this.config.currentPage === this.numberOfPages) {
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
   * Show edit for a debt transaction.
   */
  public editDebt(debt: DebtSummaryModel) {
    const emptyValidForm = {};
    this.status.emit({
      form: emptyValidForm,
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      action: DebtSumarysActions.edit,
      // transactionCategory: debt.transactionTypeIdentifier,
      scheduleType: 'sched_d',
      transactionDetail: {
        transactionModel: {
          transactionId: debt.transactionId,
          type: debt.transactionTypeIdentifier, // should come from API
          transactionTypeIdentifier: debt.transactionTypeIdentifier,
          apiCall: '/sd/schedD' // should come from API
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
          // const reportId: string = this._reportTypeService.getReportIdFromStorage('3X').toString();
          // this._transactionsService
          //   .trashOrRestoreTransactions('F3X', 'trash', reportId, [trx])
          this._debtSummaryService.deleteDebt(debt).subscribe((res2: any) => {
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
}
