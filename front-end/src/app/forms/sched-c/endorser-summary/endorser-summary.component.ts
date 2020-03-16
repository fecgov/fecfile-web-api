import { Component, Input, OnInit, ViewEncapsulation, ViewChild, OnDestroy, Output, EventEmitter, SimpleChanges , ChangeDetectionStrategy } from '@angular/core';
import { style, animate, transition, trigger } from '@angular/animations';
import { PaginationInstance } from 'ngx-pagination';
import { ModalDirective } from 'ngx-bootstrap/modal';
import { LoanModel } from '../model/loan.model';
import { SortableColumnModel } from '../../../shared/services/TableService/sortable-column.model';
import { LoanService, GetLoanResponse } from '../../sched-c/service/loan.service';
import { TableService } from '../../../shared/services/TableService/table.service';
import { UtilService } from '../../../shared/utils/util.service';
import { LoanMessageService } from '../../sched-c/service/loan-message.service';
import { Subscription } from 'rxjs/Subscription';
import { DialogService } from '../../../shared/services/DialogService/dialog.service';
import { CONTEXT_NAME } from '@angular/compiler/src/render3/view/util';
import { ScheduleActions } from '../../form-3x/individual-receipt/schedule-actions.enum';
import { ConfirmModalComponent, ModalHeaderClassEnum } from '../../../shared/partials/confirm-modal/confirm-modal.component';

export enum ActiveView {
  endorserSummary = 'endorserSummary',
  recycleBin = 'recycleBin',
  edit = 'edit'
}

export enum loanSumarysActions {
  add = 'add',
  edit = 'edit'
}

@Component({
  selector: 'app-loanendorsersummary',
  templateUrl: './endorser-summary.component.html',
  styleUrls: ['./endorser-summary.component.scss'],
  encapsulation: ViewEncapsulation.None,
  /* animations: [
    trigger('fadeInOut', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate(500, style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate(0, style({ opacity: 0 }))
      ])
    ])
  ] */
})
export class EndorserSummaryComponent implements OnInit , OnDestroy {

  @ViewChild('columnOptionsModal')
  public columnOptionsModal: ModalDirective;

  @Input()
  public formType: string;

  @Input()
  public reportId: string;

  @Input()
  public tableType: string;

  @Input()
  public transactionDetail: any;


  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  //TODO-ZS -- change "any" to endorserModel when using actual data
  public endorserModel: Array<any>;

  public totalAmount: number;
  public endorserView = ActiveView.endorserSummary
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
  private readonly endorserSortableColumnsLSK =
    'endorser.ctn.sortableColumn';
  private readonly recycleSortableColumnsLSK =
    'endorser.recycle.sortableColumn';
  private readonly endorserCurrentSortedColLSK =
    'endorser.ctn.currentSortedColumn';
  private readonly recycleCurrentSortedColLSK =
    'endorser.recycle.currentSortedColumn';
  private readonly endorserPageLSK =
    'endorser.ctn.page';
  private readonly recyclePageLSK =
    'endorser.recycle.page';
  private readonly filtersLSK =
    'endorser.filters';

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


  private columnOptionCount = 0;
  private maxColumnOption = 5;
  public allEndorserSelected: boolean;
  public currentPageNumber: number = 1;

  constructor(
    private _LoanService: LoanService,
    private _LoanMessageService: LoanMessageService,
    private _tableService: TableService,
    private _utilService: UtilService,
    private _dialogService: DialogService,
  ) {

  }
  /**
   * Initialize the component.
   */
  public ngOnInit(): void {
    const paginateConfig: PaginationInstance = {
      id: 'forms__ctn-table-pagination',
      itemsPerPage: 10,
      currentPage: this.currentPageNumber
    };
    this.config = paginateConfig;
    this.tableType = ActiveView.endorserSummary;
    this.getCachedValues();
    this.cloneSortableColumns = this._utilService.deepClone(this.sortableColumns);

    for (const col of this.sortableColumns) {
      if (col.checked) {
        this.columnOptionCount++;
      }
    }


    this.getPage(this.config.currentPage);
  }

  public ngOnChanges(changes:SimpleChanges){
    //console.log('this.ngOnChanges is called');
    this.ngOnInit();
  }

  public goToPage(pageEvent: any){
    //console.log(pageEvent);
    this.currentPageNumber = pageEvent;
  }

  /**
   * A method to run when component is destroyed.
   */
  public ngOnDestroy(): void {
    this.setCachedValues();
  }

  /**
   * Get cached values from session.
   */
  private getCachedValues() {
    this.applyFiltersCache();
    switch (this.tableType) {
      case this.endorserView:
        this.applyColCache(this.endorserSortableColumnsLSK);
        this.applyCurrentSortedColCache(this.endorserCurrentSortedColLSK);
        this.applyCurrentPageCache(this.endorserPageLSK);
        break;
      default:
        break;
    }
  }


  /**
	 * The endorser for a given page.
	 *
	 * @param page the page containing the endorser to get
	 */
  public getPage(page: number): void {

    this.bulkActionCounter = 0;
    this.bulkActionDisabled = true;
    //console.log(" getPage this.tableType", this.tableType)
    switch (this.tableType) {
      case this.endorserView:
        this.getendorserPage(page);
        break;
      default:
        break;
    }
  }


  
  /**
	 * The endorser for a given page.
	 *
	 * @param page the page containing the endorser to get
	 */
  public getendorserPage(page: number): void {

    this.config.currentPage = page;

    let sortedCol: SortableColumnModel =
      this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);

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

    const serverSortColumnName = this._LoanService.
      mapToSingleServerName(this.currentSortedColumnName);

    this._LoanService.getEndorsers(this.transactionDetail.endorser.back_ref_transaction_id)
    //TODO : ZS -- change resType back to  GetEndorserResponse once service is fixed
      .subscribe((res: any) => {

        // res=this.tempApiResponse;
        //console.log(" getEndorserPage res =", res)
        this.endorserModel = [];

        // fixes an issue where no items shown when current page != 1 and new filter
        // result has only 1 page.
        if (res.totalPages === 1) {
          this.config.currentPage = 1;
        }


        //TODO - ZS -- this is temporary fix to map fields to the right attributes until service response is fixed
        res.forEach(element => {
            element.name = `${element.last_name}, ${element.first_name}`;
        });
        this._LoanService.addUIFileds(res);
        this._LoanService.mockApplyFilters(res);
        // const EndorserModelL = this._LoanService.mapFromServerFields(res);
        this.endorserModel = res;

      

        this.config.totalItems = res.totalendorsersCount ? res.totalendorsersCount : 0;
        this.numberOfPages = res.totalPages;
        this.allEndorserSelected = false;
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
    this.endorserModel = this._LoanService.sortEndorser(this.endorserModel, this.currentSortedColumnName, direction);
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
   * View all Endorser selected by the user.
   */
  public viewAllSelected(): void {
    alert('View all Endorser is not yet supported');
  }


  /**
   * Print all Endorser selected by the user.
   */
  public printAllSelected(): void {
    alert('Print all Endorser is not yet supported');
  }


  /**
   * Export all Endorser selected by the user.
   */
  public exportAllSelected(): void {
    alert('Export all Endorser is not yet supported');
  }


  /**
   * Link all Endorser selected by the user.
   */
  public linkAllSelected(): void {
    alert('Link multiple endorser requirements have not been finalized');
  }


  /**
   * Trash all Endorser selected by the user.
   */
  public trashAllSelected(): void {
    /* let conIds = '';
     const selectedEndorser: Array<endorserModel> = [];
     for (const con of this.endorserModel) {
       if (con.selected && con.activeTransactionsCnt === 0) {
         selectedEndorser.push(con);
         conIds += con.id + ', ';
       }
     }
 
     conIds = conIds.substr(0, conIds.length - 2);
 
     this._dialogService
       .confirm('You are about to delete these Endorser.   ' + conIds, ConfirmModalComponent, 'Warning!')
       .then(res => {
         if (res === 'okay') {
           this._EndorserService
             .trashOrRestoreEndorser('trash', selectedEndorser)
             .subscribe((res: GetEndorserResponse) => {
               this.getEndorserPage(this.config.currentPage);
 
               let afterMessage = '';
               if (selectedEndorser.length === 1) {
                 afterMessage = `Transaction ${selectedEndorser[0].id}
                   has been successfully deleted and sent to the recycle bin.`;
               } else {
                 afterMessage = 'Transactions have been successfully deleted and sent to the recycle bin.   ' + conIds;
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
       });*/

  }



  /**
   * Determine the item range shown by the server-side pagination.
   */
  public determineItemRange(): string {

    let start = 0;
    let end = 0;
    // this.numberOfPages = 0;
    this.config.currentPage = this._utilService.isNumber(this.config.currentPage) ?
      this.config.currentPage : 1;

    if (!this.endorserModel) {
      return '0';
    }

    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0
      && this.endorserModel.length > 0) {
      // this.calculateNumberOfPages();

      if (this.config.currentPage === this.numberOfPages) {
        // end = this.endorserModel.length;
        end = this.config.totalItems;
        start = (this.config.currentPage - 1) * this.config.itemsPerPage + 1;
      } else {
        end = this.config.currentPage * this.config.itemsPerPage;
        start = (end - this.config.itemsPerPage) + 1;
      }
      // // fix issue where last page shown range > total items (e.g. 11-20 of 19).
      // if (end > this.endorserModel.length) {
      //   end = this.endorserModel.length;
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
   * Check/Uncheck all Endorser in the table.
   */
  public changeAllendorserSummarysSelected() {

    // TODO Iterating over the trsnactionsModel and setting the selected prop
    // works when we have server-side pagination as the model will only contain
    // Endorser for the current page.

    // Until the server is ready for pagination,
    // we are getting the entire set of tranactions (> 500)
    // and must only count and set the selected prop for the items
    // on the current page.

    this.bulkActionCounter = 0;
    // for (const t of this.endorserModel) {
    //   t.selected = this.allEndorserSelected;
    //   if (this.allEndorserSelected) {
    //     this.bulkActionCounter++;
    //   }
    // }

    // TODO replace this with the commented code above when server pagination is ready.
    for (let i = (this.firstItemOnPage - 1); i <= (this.lastItemOnPage - 1); i++) {
      this.endorserModel[i].selected = this.allEndorserSelected;
      if (this.allEndorserSelected) {
        this.bulkActionCounter++;
      }
    }
    this.bulkActionDisabled = !this.allEndorserSelected;
  }


  /**
   * Check if the view to show is Endorser.
   */
  public isendorserSummaryViewActive() {
    return this.tableType === this.endorserView ? true : false;
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
      this.allEndorserSelected = false;
      if (this.bulkActionCounter > 0) {
        this.bulkActionCounter--;
      }
    }

    // Contact View shows bulk action when more than 1 checked
    // Recycle Bin shows delete action when 1 or more checked.
    const count = this.isendorserSummaryViewActive() ? 1 : 0;
    this.bulkActionDisabled = (this.bulkActionCounter > count) ? false : true;
  }



  /**
   * Columns selected in the PIN dialog from the Endorser view
   * need to be applied to the Recycling Bin table.
   */
  private applyColumnsSelected() {
    const key = this.endorserSortableColumnsLSK;
    const sortableColumnsJson: string | null = localStorage.getItem(key);
    if (localStorage.getItem(key) != null) {
      const ctnCols: SortableColumnModel[] = JSON.parse(sortableColumnsJson);
      for (const col of ctnCols) {
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
      case this.endorserView:
        this.setCacheValuesforView(this.endorserSortableColumnsLSK,
          this.endorserCurrentSortedColLSK, this.endorserPageLSK);
        this.endorserPageLSK
        break;
      case this.recycleBinView:
        this.setCacheValuesforView(this.recycleSortableColumnsLSK,
          this.recycleCurrentSortedColLSK, this.recyclePageLSK);
        this.recyclePageLSK
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

    // shared between ctn and recycle tables
    localStorage.setItem(columnsKey,
      JSON.stringify(this.sortableColumns));

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

    const defaultSortColumns = ['name', 'contribution_amount', 'employer', 'occupation'];
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

  public editEndorser(endorser:any){
    this._goToEndorser(endorser);
  }

  public goToC1() {
    const c1EmitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c1',
      action: this.transactionDetail.c1Exists ? ScheduleActions.edit: ScheduleActions.add,
      transactionDetail: {
        transactionModel: {
          transactionId: this.transactionDetail.endorser.back_ref_transaction_id,
        }
      }
    };
    this.status.emit(c1EmitObj);
  }


  private _goToEndorser(endorser:any) {
    const endorserRepaymentEmitObj: any = {
      form: {},
      direction: 'next', 
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c_en',
      action: ScheduleActions.edit,
      transactionDetail: {
        transactionModel : {
          transactionId: endorser.transaction_id, 
          entityId: endorser.entity_id, 
          endorser, 
          entryScreenScheduleType:'sched_c_es'
        }
      }
    };
    this.status.emit(endorserRepaymentEmitObj);
  }
  

  /**
   * Set the UI to show the default column sorted in the default direction.
   */
  private setSortDefault(): void {
    // this.currentSortedColumnName = this._tableService.setSortDirection('name',
    //   this.sortableColumns, false);

    // this.currentSortedColumnName = this._tableService.setSortDirection('default',
    //   this.sortableColumns, false);

    // When default, the backend will sort by name and endorser date
    this.currentSortedColumnName = 'default';
  }


  private calculateNumberOfPages(): void {
    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0) {
      if (this.endorserModel && this.endorserModel.length > 0) {
        this.numberOfPages = this.endorserModel.length / this.config.itemsPerPage;
        this.numberOfPages = Math.ceil(this.numberOfPages);
      }
    }
  }

  /**
   * Trash the transaction selected by the user.
   *
   * @param trx the Transaction to trash
   */
  public trashEndorser(endorser: any): void {
    this._dialogService
      .confirm('You are about to delete this transaction ' + endorser.transaction_id + '.', ConfirmModalComponent, 'Caution!')
      .then(res => {
        if (res === 'okay') {
          this._LoanService.deleteEndorser(endorser).subscribe(res => {
            this.getPage(this.config.currentPage);
            this._dialogService.confirm(
              'Transaction has been successfully deleted. ' + endorser.transaction_id,
              ConfirmModalComponent,
              'Success!',
              false,
              ModalHeaderClassEnum.successHeader
            );
          })
        } else if (res === 'cancel') {
        }
      });
  }


}