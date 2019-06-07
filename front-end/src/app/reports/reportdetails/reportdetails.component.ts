import { Component, Input, OnInit, ViewEncapsulation, ViewChild, OnDestroy } from '@angular/core';
import { style, animate, transition, trigger } from '@angular/animations';
import { PaginationInstance } from 'ngx-pagination';
import { ModalDirective } from 'ngx-bootstrap/modal';
import { SortableColumnModel } from '../../shared/services/TableService/sortable-column.model';
import { TableService } from '../../shared/services/TableService/table.service';
import { UtilService } from '../../shared/utils/util.service';
import { ActiveView } from '../reportheader/reportheader.component';
import { ReportsMessageService } from '../service/reports-message.service';
import { Subscription } from 'rxjs/Subscription';
import { ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { GetReportsResponse } from '../../reports/service/report.service';
import { reportModel } from '../model/report.model';
import { ReportsService } from '../service/report.service';
import { ReportFilterModel } from '../model/report-filter.model';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { form99, form3XReport, form99PrintPreviewResponse, form3xReportTypeDetails} from '../../shared/interfaces/FormsService/FormsService';

@Component({
  selector: 'app-reportdetails',
  templateUrl: './reportdetails.component.html',
  styleUrls: ['./reportdetails.component.scss'],
  encapsulation: ViewEncapsulation.None,
  animations: [
		trigger('fadeInOut', [
			transition(':enter', [
				style({opacity:0}),
				animate(500, style({opacity:1})) 
      ]),
				transition(':leave', [
				animate(10, style({opacity:0})) 
			])
		])
	]
})
export class ReportdetailsComponent implements OnInit, OnDestroy {


  @ViewChild('columnOptionsModal')
  public columnOptionsModal: ModalDirective;

  /*@ViewChild('trashModal')
  public trashModal: TrashConfirmComponent;*/

  @Input()
  public view: string; 

  @Input()
  public formType: string;

  @Input()
  public tableType: string;

  @Input()
  public existingReportId: number;

  // @ViewChild('modalBody')
  // public modalBody;

 
  
  private filters: ReportFilterModel;

  public reportsModel: Array<reportModel>;
  //public filterReportsModel: Array<reportModel>;
  //public totalAmount: number;
  public reportsView = ActiveView.reports;
  public recycleBinView = ActiveView.recycleBin;
  public bulkActionDisabled = true;
  public bulkActionCounter = 0;
  //public existingReportId: string;

  // ngx-pagination config
  public maxItemsPerPage = 100;
  public directionLinks = false;
  public autoHide = true;
  public config: PaginationInstance;
  public numberOfPages = 0;
 

  // private keywords = [];
  private firstItemOnPage = 0;
  private lastItemOnPage = 0;


  // Local Storage Keys
  private readonly reportSortableColumnsLSK =
    'reports.rpt.sortableColumn';
  private readonly recycleSortableColumnsLSK =
    'reports.recycle.sortableColumn';
  private readonly reportCurrentSortedColLSK =
    'reports.rpt.currentSortedColumn';
  private readonly recycleCurrentSortedColLSK =
    'reports.recycle.currentSortedColumn';
  private readonly reportPageLSK =
    'reports.rpt.page';
  private readonly recyclePageLSK =
    'reports.recycle.page';
  private readonly filtersLSK =
    'reports.filters';

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
   * to the reports obtained from the server.
   */
  private keywordFilterSearchSubscription: Subscription;

  private columnOptionCount = 0;
  private readonly maxColumnOption = 5;
  private allReportsSelected: boolean;

  constructor(
    private _ReportsService: ReportsService,
    private _reportsMessageService: ReportsMessageService,
    private _tableService: TableService,
    private _utilService: UtilService,
    private _dialogService: DialogService,
    private _activatedRoute: ActivatedRoute,
    private _router: Router
  ) {
    this.showPinColumnsSubscription = this._reportsMessageService.getShowPinColumnMessage()
      .subscribe(
        message => {
          this.showPinColumns();
        }
      );

    this.keywordFilterSearchSubscription = this._reportsMessageService.getDoKeywordFilterSearchMessage()
      .subscribe(
        (filters: ReportFilterModel) => {
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

    const paginateConfig: PaginationInstance = {
      id: 'forms__trx-table-pagination',
      itemsPerPage: 30,
      currentPage: 1
    };
    this.config = paginateConfig;

    this.getCachedValues();
    this.cloneSortableColumns = this._utilService.deepClone(this.sortableColumns);

    for (const col of this.sortableColumns) {
      if (col.checked) {
        this.columnOptionCount++;
      }
    }

    if (this.view !== localStorage.getItem("Reports.view")){
      localStorage.setItem("Reports.view",this.view);
      this.config.currentPage=1;
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
	 * The Reports for a given page.
	 *
	 * @param page the page containing the reports to get
	 */
  public getPage(page: number): void {

    this.bulkActionCounter = 0;
    this.bulkActionDisabled = true;

    switch (this.tableType) {
      case this.reportsView:
        this.getReportsPage(page);
        break;
      case this.recycleBinView:
        this.getReportsPage(page);
        break;
      default:
        break;
    }
  }


  /**
	 * The Reports for a given page.
	 *
	 * @param page the page containing the reports to get
	 */
  /*public getReportsPage(page: number): void {

    // this.config.currentPage = page;

    const sortedCol: SortableColumnModel =
      this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);

    this._reportsService.getFormReports(this.formType, page, this.config.itemsPerPage,
      this.currentSortedColumnName, sortedCol.descending, this.filters)
      .subscribe((res: GetReportsResponse) => {
        this.reportsModel = [];

        this._reportsService.mockAddUIFileds(res);
        this._reportsService.mockApplyRestoredReport(res);
        this._reportsService.mockApplyTrashedReport(res);
        this._reportsService.mockApplyFilters(res, this.filters, this.reportsView);

        const reportsModelL = this._reportsService.mapFromServerFields(res.reports);

        this.reportsModel = this._reportsService.sortReports(
          reportsModelL, this.currentSortedColumnName, sortedCol.descending);

        this.totalAmount = res.totalAmount;
        this.config.totalItems = res.totalReportCount;
        this.allReportsSelected = false;

        // This is called in the template.  However, with mock data there may be a race condition
        // where this method isn't called until after the current page logic
        // following it is called.  So it is added here. Remove it later if not needed.
        // Test where current page > 1.  The filter to produce a result of 1 page.
        // Make sure the page range it for page 1 and not > 1.
        this.determineItemRange();

        // If a row was deleted, the current page may be greated than the last page
        // as result of the delete.
        this.config.currentPage = (page > this.numberOfPages && this.numberOfPages !== 0)
          ? this.numberOfPages : page;
      });
  }

*/


/**
	 * The Reports for a given page.
	 * 
	 * @param page the page containing the reports to get
	 */
	public getReportsPage(page: number) : void {

    this.config.currentPage = page;

    const sortedCol: SortableColumnModel =
    this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);

    console.log("view",this.view);
    console.log("existingReportId",this.existingReportId);
  
    this._ReportsService.getReports (this.view, page, this.config.itemsPerPage,
      this.currentSortedColumnName, sortedCol.descending,  this.filters, this.existingReportId)
      
      .subscribe((res: GetReportsResponse) => {
   
        this.reportsModel = [];
        this._ReportsService.mockApplyFilters(res, this.filters);
        const reportsModelL = this._ReportsService.mapFromServerFields(res.reports);
        console.log(" getReportsPage reportsModelL", reportsModelL);

        this.config.totalItems = this.reportsModel.length;
        this.reportsModel = this._ReportsService.sortReports(
          reportsModelL, this.currentSortedColumnName, sortedCol.descending);
        
        console.log(" getReportsPage this.reportsModel= ", this.reportsModel);
      
        this.allReportsSelected = false;
      });

      
  }  

  

  /**
	 * The Reports for the recycling bin.
	 *
	 * @param page the page containing the reports to get
	 */
 /* public getRecyclingPage(page: number): void {

    this.calculateNumberOfPages();

    const sortedCol: SortableColumnModel =
      this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);

    this._reportsService.getUserDeletedReports(this.formType)
      .subscribe((res: GetReportsResponse) => {

        this._reportsService.mockAddUIFileds(res);
        this._reportsService.mockApplyTrashedRecycleBin(res);
        this._reportsService.mockApplyFilters(res, this.filters, this.recycleBinView);
        const reportsModelL = this._reportsService.mapFromServerFields(res.reports);

        this.reportsModel = this._reportsService.sortReports(
          reportsModelL, this.currentSortedColumnName, sortedCol.descending);

        this.config.totalItems = res.totalReportCount;

        // This is called in the template.  However, with mock data there may be a race condition
        // where this method isn't called until after the current page logic
        // following it is called.  So it is added here. Remove it later if not needed.
        // Test where current page > 1.  The filter to produce a result of 1 page.
        // Make sure the page range it for page 1 and not > 1.
        this.determineItemRange();

        // If a row was deleted, the current page may be greated than the last page
        // as result of the delete.
        this.config.currentPage = (page > this.numberOfPages && this.numberOfPages !== 0)
          ? this.numberOfPages : page;
      });
  }*/


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

    // only permit 7 checked at a time
    if (e.target.checked === true) {
      this.columnOptionCount = 0;
      for (const col of this.sortableColumns) {
        if (col.checked) {
          this.columnOptionCount++;
        }
        if (this.columnOptionCount > 7) {
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
   * View all reports selected by the user.
   */
  public viewAllSelected(): void {
    alert('View all reports is not yet supported');
  }


  /**
   * Print all reports selected by the user.
   */
  public printAllSelected(): void {
    alert('Print all reports is not yet supported');
  }


  /**
   * Export all reports selected by the user.
   */
  public exportAllSelected(): void {
    alert('Export all reports is not yet supported');
  }


  /**
   * Link all reports selected by the user.
   */
  public linkAllSelected(): void {
    alert('Link multiple report requirements have not been finalized');
  }


  /**
   * Trash all reports selected by the user.
   */
  /*public trashAllSelected(): void {

    const selectedReports: Array<ReportModel> = [];
    for (const trx of this.reportsModel) {
      if (trx.selected) {
        selectedReports.push(trx);
      }
    }
    // this.trashModal.reports = selectedReports;
    const dataMap: Map<string, any> = new Map([['reports.,selectedReports]]);

    this._dialogService
      .confirm('You are about to delete these reports ',
        TrashConfirmComponent,
        'Caution!', null, null, dataMap)
      .then(res => {
        if (res === 'okay') {
          let i = 1;
          for (const trx of selectedReports) {
            this._reportsService.trashReport(trx)
              .subscribe((res: GetReportsResponse) => {
                // on last delete get page and show success
                if (i === selectedReports.length) {
                  this.getReportsPage(this.config.currentPage);
                  this._dialogService
                    .confirm('reports.' +
                        ' have been successfully deleted and sent to the recycle bin',
                      TrashConfirmComponent, 'Success!', false, ModalHeaderClassEnum.successHeader, dataMap);
                }
              });
              i++;
          }
        } else if (res === 'cancel') {
        }
      });
  }*/


  /**
   * Clone the report selected by the user.
   *
   * @param report the Report to clone
   */
  public cloneReport(): void {
    alert('Clone report is not yet supported');
  }


  /**
   * Link the report selected by the user.
   *
   * @param report the Report to link
   */
  public linkReport(): void {
    alert('Link requirements have not been finalized');
  }


  /**
   * View the report selected by the user.
   *
   * @param report the Report to view
   */
  public viewReport(): void {
    alert('View report is not yet supported');
  }


  /**
   * Edit the report selected by the user.
   *
   * @param report the Report to edit
   */
  public editReport(report:reportModel): void {

    if (report.form_type==='F99'){
      this._ReportsService.getReportInfo(report.form_type, report.report_id)
      .subscribe((res: form99) => {
        console.log("getReportInfo res =", res)
        localStorage.setItem('form_99_details', JSON.stringify(res));
        //return false;
      });
      console.log(new Date().toISOString());
      setTimeout(() => 
      {
        this._router.navigate(['/forms/form/99'], { queryParams: { step: 'step_1'} });  
        console.log(new Date().toISOString());
      },
      1500);

    }
    else if (report.form_type==='F3X'){
      this._ReportsService.getReportInfo(report.form_type, report.report_id)
      .subscribe((res: form3xReportTypeDetails) => {
        console.log("getReportInfo res =", res)
        localStorage.setItem('form_3X_details', JSON.stringify(res[0]));
        localStorage.setItem(`form_3X_report_type`, JSON.stringify(res[0]));

        //return false;
      });
      console.log(new Date().toISOString());
      setTimeout(() => 
      {
        this._router.navigate([`/forms/transactions/3X/${report.report_id}`], { queryParams: { step: 'step_4'} });
        console.log(new Date().toISOString());
      },
      1500);
    }
  }


  /**
   * Trash the report selected by the user.
   *
   * @param trx the Report to trash
   */
  /*public trashReport(trx: ReportModel): void {

    this._dialogService
      .confirm('You are about to trash report ' + trx.reportId + '.',
        ConfirmModalComponent,
        'Caution!')
      .then(res => {
        if (res === 'okay') {
          this._reportsService.trashReport(trx)
            .subscribe((res: GetReportsResponse) => {
              this.getReportsPage(this.config.currentPage);
              this._dialogService
                .confirm('Report ' + trx.reportId +
                    ' has been successfully deleted and sent to the recycle bin',
                  ConfirmModalComponent, 'Success!', false, ModalHeaderClassEnum.successHeader);
            });
        } else if (res === 'cancel') {
        }
      });
  }
*/

  /**
   * Restore a trashed report from the recyle bin.
   *
   * @param trx the Report to restore
   */
  /*public restoreReport(trx: ReportModel): void {

    this._dialogService
      .confirm('You are about to restore report ' + trx.reportId + '.',
        ConfirmModalComponent,
        'Caution!')
      .then(res => {
        if (res === 'okay') {
          this._reportsService.restoreReport(trx)
            .subscribe((res: GetReportsResponse) => {
              this.getRecyclingPage(this.config.currentPage);
              this._dialogService
                .confirm('Report ' + trx.reportId + ' has been restored!',
                  ConfirmModalComponent, 'Success!', false, ModalHeaderClassEnum.successHeader);
            });
        } else if (res === 'cancel') {
        }
      });
  }*/


  /**
   * Delete selected reports from the the recyle bin.
   *
   * @param trx the Report to delete
   */
  /*public deleteRecyleBin(): void {

    let beforeMessage = '';
    const selectedReports: Array<ReportModel> = [];
    for (const trx of this.reportsModel) {
      if (trx.selected) {
        selectedReports.push(trx);
      }
    }

    if (selectedReports.length === 1) {
      beforeMessage = 'Are you sure you want to permanently delete Report ' +
        selectedReports[0].reportId + '?';
    } else {
      beforeMessage = 'Are you sure you want to permanently delete these reports?';
    }

    this._dialogService
      .confirm(beforeMessage,
        ConfirmModalComponent,
        'Caution!')
      .then(res => {
        if (res === 'okay') {
          this._reportsService.deleteRecycleBinReport(selectedReports)
            .subscribe((res: GetReportsResponse) => {
              this.getRecyclingPage(this.config.currentPage);

              let afterMessage = '';
              if (selectedReports.length === 1) {
                  afterMessage = `Report ${selectedReports[0].reportId} has been successfully deleted`;
              } else {
                afterMessage = 'reports.have been successfully deleted.';
              }
              this._dialogService
                .confirm(afterMessage,
                  ConfirmModalComponent, 'Success!', false, ModalHeaderClassEnum.successHeader);
           });
        } else if (res === 'cancel') {
        }
      });
  }*/



  /**
   * Determine the item range shown by the server-side pagination.
   */
  public determineItemRange(): string {

    let start = 0;
    let end = 0;
    this.numberOfPages = 0;
    this.config.currentPage = this._utilService.isNumber(this.config.currentPage) ?
      this.config.currentPage : 1;

    if (!this.reportsModel) {
      return;
    }

    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0
      && this.reportsModel.length > 0) {
      this.calculateNumberOfPages();

      if (this.config.currentPage === this.numberOfPages) {
        end = this.reportsModel.length;
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
   * Check/Uncheck all reports in the table.
   */
  public changeAllReportsSelected() {

    // TODO Iterating over the trsnactionsModel and setting the selected prop
    // works when we have server-side pagination as the model will only contain
    // reports for the current page.

    // Until the server is ready for pagination,
    // we are getting the entire set of tranactions (> 500)
    // and must only count and set the selected prop for the items
    // on the current page.

    this.bulkActionCounter = 0;
    // for (const t of this.reportsModel) {
    //   t.selected = this.allReportsSelected;
    //   if (this.allReportsSelected) {
    //     this.bulkActionCounter++;
    //   }
    // }


    //Commented by Mahendra@04/16/2019
    // TODO replace this with the commented code above when server pagination is ready.
    for (let i = (this.firstItemOnPage - 1); i <= (this.lastItemOnPage - 1); i++) {
      this.reportsModel[i].selected = this.allReportsSelected;
      if (this.allReportsSelected) {
        this.bulkActionCounter++;
      }
    }
    this.bulkActionDisabled = !this.allReportsSelected;
  }


  /**
   * Check if the view to show is Reports.
   */
  public isReportViewActive() {
    return this.tableType === this.reportsView ? true : false;
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
      this.allReportsSelected = false;
      if (this.bulkActionCounter > 0) {
        this.bulkActionCounter--;
      }
    }

    // Report View shows bulk action when more than 1 checked
    // Recycle Bin shows delete action when 1 or more checked.
    const count = this.isReportViewActive() ? 1 : 0;
    this.bulkActionDisabled = (this.bulkActionCounter > count) ? false : true;
  }


  /**
   * Get cached values from session.
   */
  private getCachedValues() {
    this.applyFiltersCache();
    switch (this.tableType) {
      case this.reportsView:
        this.applyColCache(this.reportSortableColumnsLSK);
        this.applyCurrentSortedColCache(this.reportCurrentSortedColLSK);
        this.applyCurrentPageCache(this.reportPageLSK);
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
   * Columns selected in the PIN dialog from the reports view
   * need to be applied to the Recycling Bin table.
   */
  private applyColumnsSelected() {
    const key = this.reportSortableColumnsLSK;
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
    if (this._utilService.isNumber(currentPageCache)) {
      this.config.currentPage = this._utilService.toInteger(currentPageCache);
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
      case this.reportsView:

        this.setCacheValuesforView(this.reportSortableColumnsLSK,
          this.reportCurrentSortedColLSK, this.reportPageLSK);
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
 /**
   * Set the Table Columns model.
   */
  private setSortableColumns() : void {
    // sort column names must match the domain model names
    let defaultSortColumns = ['form_type', 'status', 'fec_id', 'amend_ind', 'cvg_start_date', 'cvg_end_date', 'report_type_desc','filed_date', 'last_update_date'];

    /*let otherSortColumns = ['street', 'city', 'state', 'zip', 'aggregate', 'purposeDescription',  
      'contributorEmployer', 'contributorOccupation', 'memoCode', 'memoText',];*/

    this.sortableColumns = [];
    for (let field of defaultSortColumns) {
      this.sortableColumns.push(new SortableColumnModel(field, false, true, true, false));
    }  
    /*for (let field of otherSortColumns) {
      this.sortableColumns.push(new SortableColumnModel(field, false, false, false, true));
    }*/


  }


  /**
   * Set the UI to show the default column sorted in the default direction.
   */
  private setSortDefault(): void {
    //this.currentSortedColumnName = this._tableService.setSortDirection('form_type',
      //this.sortableColumns, false);
    this.currentSortedColumnName = this._tableService.setSortDirection('last_update_date',
      this.sortableColumns, true);
  }


  private calculateNumberOfPages() : void {

    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0) {
      if (this.reportsModel && this.reportsModel.length > 0) {
        this.numberOfPages =  this.reportsModel.length / this.config.itemsPerPage;
        this.numberOfPages = Math.ceil(this.numberOfPages);
      }
    }
  }

  public getErrors(){
   alert('Get Errors functionality is not yet implemented.');
  }

  public isStatusFailed(status:string):boolean{
    if (status==='Failed')
      return true;
    else 
      return false;  
  }
}
