import { Component, Input, OnInit, ViewEncapsulation, ViewChild, OnDestroy , ChangeDetectionStrategy } from '@angular/core';
import { style, animate, transition, trigger } from '@angular/animations';
import { PaginationInstance } from 'ngx-pagination';
import { ModalDirective } from 'ngx-bootstrap/modal';
import { SortableColumnModel } from '../../shared/services/TableService/sortable-column.model';
import { TableService } from '../../shared/services/TableService/table.service';
import { UtilService } from '../../shared/utils/util.service';
import { ActiveView } from '../reportheader/reportheader.component';
import { ReportsMessageService } from '../service/reports-message.service';
import { Subscription } from 'rxjs/Subscription';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { GetReportsResponse } from '../../reports/service/report.service';
import { reportModel } from '../model/report.model';
import { ReportsService } from '../service/report.service';
import { ReportFilterModel } from '../model/report-filter.model';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { AuthService} from '../../shared/services/AuthService/auth.service';
import {
  form99,
  form3XReport,
  form99PrintPreviewResponse,
  form3xReportTypeDetails
} from '../../shared/interfaces/FormsService/FormsService';
import { TransactionsMessageService } from 'src/app/forms/transactions/service/transactions-message.service';
import { ReportTypeService } from '../../forms/form-3x/report-type/report-type.service';
import { FormsService } from '../../shared/services/FormsService/forms.service';
import {SaveDialogAction} from '../../shared/partials/input-modal/input-modal.component';
import {InputDialogService} from '../../shared/service/InputDialogService/input-dialog.service';
@Component({
  selector: 'app-reportdetails',
  templateUrl: './reportdetails.component.html',
  styleUrls: ['./reportdetails.component.scss'],
  encapsulation: ViewEncapsulation.None,
  /* animations: [
    trigger('fadeInOut', [
      transition(':enter', [style({ opacity: 0 }), animate(500, style({ opacity: 1 }))]),
      transition(':leave', [animate(10, style({ opacity: 0 }))])
    ])
  ] */
})
export class ReportdetailsComponent implements OnInit, OnDestroy {
  @ViewChild('columnOptionsModal')
  public columnOptionsModal: ModalDirective;

  /*@ViewChild('trashModal')
  public trashModal: TrashConfirmComponent;*/

  @Input()
  public view: string;

  @Input()
  public tableview: string;

  @Input()
  public formType: string;

  @Input()
  public tableType: string;

  @Input()
  public existingReportId: number;

  // @ViewChild('modalBody')
  // public modalBody;

  public filters: ReportFilterModel;

  public reportsModel: Array<reportModel>;
  //public filterReportsModel: Array<reportModel>;
  //public totalAmount: number;
  public reportsView = ActiveView.reports;
  public recycleBinView = ActiveView.recycleBin;
  public bulkActionDisabled = true;
  public bulkActionCounter = 0;
  public statusDescriptions = [];
  public getAmendmentIndicatorsDescriptions = [];
  public getReportTypesDescriptions = [];
  //public existingReportId: string;

  // ngx-pagination config
  public pageSizes: number[] = UtilService.PAGINATION_PAGE_SIZES;
  public maxItemsPerPage: number = this.pageSizes[0];
  public paginationControlsMaxSize: number = 10;
  public directionLinks: boolean = false;
  public autoHide: boolean = true;
  public config: PaginationInstance;
  public numberOfPages: number = 0;
  public pageNumbers: number[] = [];

  public reportID = 0;
  // private keywords = [];
  private firstItemOnPage = 0;
  private lastItemOnPage = 0;

  // Local Storage Keys
  private readonly reportSortableColumnsLSK = 'reports.rpt.sortableColumn';
  private readonly recycleSortableColumnsLSK = 'reports.recycle.sortableColumn';
  private readonly reportCurrentSortedColLSK = 'reports.rpt.currentSortedColumn';
  private readonly recycleCurrentSortedColLSK = 'reports.recycle.currentSortedColumn';
  private readonly reportPageLSK = 'reports.rpt.page';
  private readonly recyclePageLSK = 'reports.recycle.page';
  private readonly filtersLSK = 'reports.filters';

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
    private _reportsService: ReportsService,
    private _reportsMessageService: ReportsMessageService,
    private _tableService: TableService,
    private _utilService: UtilService,
    private _dialogService: DialogService,
    private _activatedRoute: ActivatedRoute,
    private _router: Router,
    private _reportTypeService: ReportTypeService,
    private _formsService: FormsService,
    private authService: AuthService,
    private inputDialogService: InputDialogService,
  ) {
    this.showPinColumnsSubscription = this._reportsMessageService.getShowPinColumnMessage().subscribe(message => {
      this.showPinColumns();
    });

    this.keywordFilterSearchSubscription = this._reportsMessageService
      .getDoKeywordFilterSearchMessage()
      .subscribe((filters: ReportFilterModel) => {
        if (filters) {
          this.filters = filters;
          if (filters.formType) {
            this.formType = filters.formType;
          }
        }
        this.getPage(this.config.currentPage);
      });
  }

  /**
   * Initialize the component.
   */
  public ngOnInit(): void {
    const paginateConfig: PaginationInstance = {
      id: 'forms__rep-table-pagination',
      itemsPerPage: this.maxItemsPerPage,
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

    if (this.view !== localStorage.getItem('Reports.view')) {
      localStorage.setItem('Reports.view', this.view);
      this.config.currentPage = 1;
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
    // localStorage.removeItem('Reports_Edit_Screen');
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
        this.getFilterNames();
        break;
      case this.recycleBinView:
        this.getRecyclingPage(page);
        break;
      default:
        break;
    }
  }

  /**
   * onChange for maxItemsPerPage.
   *
   * @param pageSize the page size to get
   */
  public onMaxItemsPerPageChanged(pageSize: number): void {
    this.config.currentPage = 1;
    this.config.itemsPerPage = pageSize;
    this.getPage(this.config.currentPage);
  }

  /**
   * onChange for gotoPage.
   *
   * @param page the page to get
   */
  public onGotoPageChange(page: number): void {
    this.config.currentPage = page;
    this.getPage(this.config.currentPage);
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
  public getReportsPage(page: number): void {
    this.config.currentPage = page;

    const sortedCol: SortableColumnModel = this._tableService.getColumnByName(
      this.currentSortedColumnName,
      this.sortableColumns
    );

    this._reportsService
      .getParentReports(
        this.view,
        page,
        this.config.itemsPerPage,
        this.currentSortedColumnName,
        sortedCol.descending,
        this.filters,
        this.existingReportId
      )

      .subscribe((res: GetReportsResponse) => {
        // this.reportsModel = [];
        // this._reportsService.mockApplyFilters(res, this.filters);
        // const reportsModelL = this._reportsService.mapFromServerFields(res.reports);

        // this.config.totalItems = this.reportsModel.length;
        // this.reportsModel = this._reportsService.sortReports(
        //   reportsModelL,
        //   this.currentSortedColumnName,
        //   sortedCol.descending
        // );

        // this.setAmendmentIndicator(this.reportsModel);
        // this.setAmendmentShow(this.reportsModel);

        // //console.log(' getReportsPage this.reportsModel= ', this.reportsModel);
        // this.config.totalItems = res.totalreportsCount ? res.totalreportsCount : 0;
        // this.numberOfPages =
        //   res.totalreportsCount > this.maxItemsPerPage ? Math.round(this.config.totalItems / this.maxItemsPerPage) : 1;
        
        // this.pageNumbers = Array.from(new Array(this.numberOfPages), (x,i) => i+1).sort((a, b) => b - a);
        // this.allReportsSelected = false;

        const pagedResponse = this._utilService.pageResponse(res, this.config);
        this.reportsModel = pagedResponse.items;
        this.pageNumbers = pagedResponse.pageNumbers;
      });
  }

  public getRecyclingPage(page: number): void {
    this.config.currentPage = page;

    const sortedCol: SortableColumnModel = this._tableService.getColumnByName(
      this.currentSortedColumnName,
      this.sortableColumns
    );

    this._reportsService
      .getTrashedReports(
        this.view,
        page,
        this.config.itemsPerPage,
        this.currentSortedColumnName,
        sortedCol.descending,
        this.filters,
        this.existingReportId
      )

      .subscribe((res: GetReportsResponse) => {
        this.reportsModel = [];
        this._reportsService.mockApplyFilters(res, this.filters);
        const reportsModelL = this._reportsService.mapFromServerFields(res.reports);
        //console.log(' getRecyclingPage reportsModelL', reportsModelL);

        this.config.totalItems = this.reportsModel.length;
        this.reportsModel = this._reportsService.sortReports(
          reportsModelL,
          this.currentSortedColumnName,
          sortedCol.descending
        );

        this.config.totalItems = res.totalreportsCount ? res.totalreportsCount : 0;
        this.numberOfPages =
          res.totalreportsCount > this.maxItemsPerPage ? Math.round(this.config.totalItems / this.maxItemsPerPage) : 1;

        this.pageNumbers = Array.from(new Array(this.numberOfPages), (x,i) => i+1).sort((a, b) => b - a);
        this.allReportsSelected = false;
      });
  }

  public getFilterNames() {
    this._reportsService.getStatuss().subscribe(res => {
      this.statusDescriptions = res.data;
    });
    this._reportsService.getAmendmentIndicators().subscribe(res => {
      this.getAmendmentIndicatorsDescriptions = res.data;
    });
    this._reportsService.getReportTypes().subscribe(res => {
      this.getReportTypesDescriptions = res;
    });
  }

  public displayStatusName(status: any) {
    if (this.statusDescriptions.length) {
      for (const statusName of this.statusDescriptions) {
        if (statusName.status_cd === status) {
          return statusName.status_desc;
        }
      }
    }
  }

  public displayAmendmentIndicator(amendmentIndicator: any) {
    if (this.getAmendmentIndicatorsDescriptions.length) {
      for (const amendmentIndicatorName of this.getAmendmentIndicatorsDescriptions) {
        if (amendmentIndicatorName.amend_ind === amendmentIndicator) {
          return amendmentIndicatorName.amendment_desc;
        }
      }
    }
  }
  
  public amendArrow(report: reportModel) {
    report.amend_max === 'up' ? this.reportsModel.find(function(obj) { return obj.report_id === report.report_id}).amend_max = 'down'
      : this.reportsModel.find(function(obj) { return obj.report_id === report.report_id}).amend_max = 'up';

    if (report.amend_max === 'down') {
      report.children = [];
      return;
    } 

    const sortedCol: SortableColumnModel = this._tableService.getColumnByName(
      this.currentSortedColumnName,
      this.sortableColumns
    );

    this._reportsService
      .getChildReports(
        this.view,
        this.config.currentPage,
        this.config.itemsPerPage,
        this.currentSortedColumnName,
        sortedCol.descending,
        this.filters,
        this.existingReportId,
        report.report_id
      )
      .subscribe((res: any) => { 
        report.children = res.items;
      });

    // let pre = report;
    // pre = this.reportsModel.find(function(obj) { return obj.report_id === pre.previous_report_id});

    // if(pre && report.amend_max === 'up') {
    //   this.reportsModel = this.reportsModel.filter(function(item) {
    //     return item !== pre
    //   })

    //   let indexReport = this.reportsModel.indexOf(report);
    //   if (indexReport > -1) {
    //     this.reportsModel.splice(indexReport + 1, 0, pre);
    //   }
    // }

    // while(pre) {
    //   let rop = pre;

    //   pre.amend_show = !pre.amend_show;
    //   pre = this.reportsModel.find(function(obj) { return obj.report_id === pre.previous_report_id});

    //   if(pre && report.amend_max === 'up') {
    //     this.reportsModel = this.reportsModel.filter(function(item) {
    //       return item !== pre
    //     })

    //     let indexRep = this.reportsModel.indexOf(rop);
    //     if (indexRep > -1) {
    //       this.reportsModel.splice(indexRep + 1, 0, pre);
    //     }
    //   }
    // }
    
  }

  public displayReportTypes(reportType: any) {
    if (this.getReportTypesDescriptions) {
      for (const reportTypeName of this.getReportTypesDescriptions) {
        if (reportTypeName.rpt_type === reportType) {
          return reportTypeName.rpt_type_desc;
        }
      }
    }
  }

  public removeTag(tagType: string, tagIndex: number) {
    switch (tagType) {
      case 'filterForms':
        this.filters.filterForms.splice(tagIndex, 1);
        this.getReportsPage(1);
        break;
      case 'filterReports':
        this.filters.filterReports.splice(tagIndex, 1);
        this.getReportsPage(1);
        break;
      case 'filterAmendmentIndicators':
        this.filters.filterAmendmentIndicators.splice(tagIndex, 1);
        this.getReportsPage(1);
        break;
      case 'filterStatuss':
        this.filters.filterStatuss.splice(tagIndex, 1);
        this.getReportsPage(1);
        break;
      case 'filterStatuss':
        this.filters.filterStatuss.splice(tagIndex, 1);
        this.getReportsPage(1);
        break;
      case 'filterCvgDate':
        this.filters.filterCvgDateFrom = null;
        this.filters.filterCvgDateTo = null;
        this.getReportsPage(1);
        break;
      case 'filterFiledDate':
        this.filters.filterFiledDateFrom = null;
        this.filters.filterFiledDateTo = null;
        this.getReportsPage(1);
      case 'filterDeletedDate':
        this.filters.filterDeletedDateFrom = null;
        this.filters.filterDeletedDateTo = null;
        this.getReportsPage(1);  
        break;
      default:

    }
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
  
  public printPreview(): void {
    this._reportTypeService.printPreview('transaction_table_screen', '3X');
  }

public printReport(report: reportModel): void{
    if (report.form_type === 'F99') {
      this._reportsService.getReportInfo(report.form_type, report.report_id).subscribe((res: form99) => {
        //console.log('getReportInfo res =', res);
        localStorage.setItem('form_99_details', JSON.stringify(res));
        let formSavedObj: any = {
          saved: true
        };
        localStorage.setItem('form_99_saved', JSON.stringify(formSavedObj));
      });
      setTimeout(() => {
        this._formsService.PreviewForm_Preview_sign_Screen({}, this.formType).subscribe(
          res => {
            if (res) {
              window.open(localStorage.getItem('form_99_details.printpriview_fileurl'), '_blank');
            }
          },
          error => {
            //console.log('error: ', error);
          }
        );
      }, 1500);
    } else if (report.form_type === 'F3X' || report.form_type === 'F24') {
      this._reportsService
        .getReportInfo(report.form_type, report.report_id)
        .subscribe((res: form3xReportTypeDetails) => {
          //console.log('getReportInfo res =', res);
          localStorage.setItem(`form_${report.form_type.substr(1)}_details`, JSON.stringify(res[0]));
          localStorage.setItem(`form_${report.form_type.substr(1)}_report_type`, JSON.stringify(res[0]));

          //return false;
        });
      setTimeout(() => {
        // this._router.navigate([`/forms/reports/3X/${report.report_id}`], { queryParams: { step: 'step_4' } });

        const formType =
          report.form_type && report.form_type.length > 2 ? report.form_type.substring(1, 3) : report.form_type;
          this._reportTypeService.printPreview('dashboard_report_screen', report.form_type.substr(1));
      }, 1500);
    }
  }

  public uploadReport(report: reportModel): void{
    if (report.form_type === 'F99') {
      this._reportsService.getReportInfo(report.form_type, report.report_id).subscribe((res: form99) => {
        //console.log('getReportInfo res =', res);
        localStorage.setItem('form_99_details', JSON.stringify(res));
        let formSavedObj: any = {
          saved: true
        };
        localStorage.setItem('form_99_saved', JSON.stringify(formSavedObj));
      });
      setTimeout(() => {
        this._router.navigate(['/forms/form/99'],{ queryParams: { step: 'step_4', edit:true, reportId: report.report_id} });
      }, 1500);
    } else if (report.form_type === 'F3X' || report.form_type === 'F24') {
      this._reportsService
        .getReportInfo(report.form_type, report.report_id)
        .subscribe((res: form3xReportTypeDetails) => {
          localStorage.setItem(`form_${report.form_type.substr(1)}_details`, JSON.stringify(res[0]));
          localStorage.setItem(`form_${report.form_type.substr(1)}_report_type`, JSON.stringify(res[0]));
        });

      setTimeout(() => {
        // this._router.navigate([`/forms/reports/3X/${report.report_id}`], { queryParams: { step: 'step_4' } });

        const formType =
          report.form_type && report.form_type.length > 2 ? report.form_type.substring(1, 3) : report.form_type;
          this._router.navigate([`/signandSubmit/${report.form_type.substr(1)}`], { queryParams: { step: 'step_4', edit:true, reportId: report.report_id} });

      }, 1500);
    } else if(report.form_type === 'F1M'){
      const formType = '1M';
        this._router.navigate([`/forms/form/${formType}`], {
          queryParams: { step: 'step_4', edit: true, reportId: report.report_id}
        });
    }
    
  }

  public downloadReport(report: reportModel): void{
    
    const imageNumber="201804139108073637"; // Todo in the production get the imagenumber from reports table
    const url=`https://www.fec.gov/data/filings/?data_type=processed&committee_id=${report.cmte_id}&beginning_image_number=${imageNumber}`;
    //console.log("downloadReport url = ", url);
    window.open(url, '_blank');

  }


  

  
  /**
   * Trash all reports selected by the user.
   */
  /*public trashAllSelected(): void {

    const selectedReports: Array<ReportModel> = [];
    for (const rep of this.reportsModel) {
      if (rep.selected) {
        selectedReports.push(rep);
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
          for (const rep of selectedReports) {
            this._reportsService.trashReport(rep)
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
  public viewReport(report: reportModel): void {
    if (report.form_type === 'F99') {
      this._reportsService.getReportInfo(report.form_type, report.report_id).subscribe((res: form99) => {
        localStorage.setItem('form_99_details', JSON.stringify(res));
        //return false;
      });
      setTimeout(() => {
        this._router.navigate(['/forms/form/99'], { queryParams: { step: 'step_1', edit: false } });
      }, 1500);
    } else if (report.form_type === 'F3X' || report.form_type === 'F24') {
      this._reportsService
        .getReportInfo(report.form_type, report.report_id)
        .subscribe((res: form3xReportTypeDetails) => {
          localStorage.setItem(`form_${report.form_type.substr(1)}_details`, JSON.stringify(res[0]));
          localStorage.setItem(`form_${report.form_type.substr(1)}_report_type`, JSON.stringify(res[0]));

          //return false;
        });
      setTimeout(() => {
        // this._router.navigate([`/forms/reports/3X/${report.report_id}`], { queryParams: { step: 'step_4' } });
        const isFiled = report.status.toUpperCase() === 'FILED';
        const formType =
          report.form_type && report.form_type.length > 2 ? report.form_type.substring(1, 3) : report.form_type;
          if (formType === '3X') {
            this._router.navigate([`/forms/form/${formType}`], {
              queryParams: { step: 'financial_summary', reportId: report.report_id, edit: false, isFiled: isFiled }
            });
          } else if(formType === '24'){
            this._router.navigate([`/forms/form/${formType}`], {
              queryParams: { step: 'transactions', reportId: report.report_id, edit: false, isFiled: isFiled, transactionCategory: 'disbursements' }
            });
          }
          else if(formType === 'F99') {
            this._router.navigate([`/forms/form/${formType}`], {
              queryParams: { step: 'step_1', reportId: report.report_id, edit: false, isFiled: isFiled }
            });
          }
      }, 1500);
    }
    else if(report.form_type === 'F1M'){
      const formType = '1M';
        this._router.navigate([`/forms/form/${formType}`], {
          queryParams: { step: 'step_2', edit: false, viewOnly:true, reportId: report.report_id}
        });
    }
  }

  /**
   * Edit the report selected by the user.
   *
   * @param report the Report to edit
   */
  public editReport(report: reportModel): void {
    localStorage.setItem('Reports_Edit_Screen', 'Yes');
    if (report.form_type === 'F99') {
      this._reportsService.getReportInfo(report.form_type, report.report_id).subscribe((res: form99) => {
        //console.log('getReportInfo res =', res);
        localStorage.setItem('form_99_details', JSON.stringify(res));
        //return false;
      });

      setTimeout(() => {
        this._router.navigate(['/forms/form/99'], { queryParams: { step: 'step_1', reportId: report.report_id } });
      }, 1500);
    } else if (report.form_type === 'F3X' || report.form_type === 'F3L') {
      this._reportsService
        .getReportInfo(report.form_type, report.report_id)
        .subscribe((res: form3xReportTypeDetails) => {
          //console.log('getReportInfo res =', res);
          localStorage.setItem(`form_${report.form_type.substring(1, 3)}_details`, JSON.stringify(res[0]));
          localStorage.setItem(`form_${report.form_type.substring(1, 3)}_report_type`, JSON.stringify(res[0]));

          //return false;
        });
      setTimeout(() => {
        // this._router.navigate([`/forms/reports/3X/${report.report_id}`], { queryParams: { step: 'step_4' } });

        const formType =
          report.form_type && report.form_type.length > 2 ? report.form_type.substring(1, 3) : report.form_type;
        this._router.navigate([`/forms/form/${formType}`], {
          queryParams: { step: 'transactions', reportId: report.report_id, edit: true, transactionCategory: 'receipts', isFiled: false  }
        });
      }, 1500);
    }
    else if(report.form_type === 'F1M'){
      const formType = '1M';
        this._router.navigate([`/forms/form/${formType}`], {
          queryParams: { step: 'step_2', edit: true, reportId: report.report_id}
        });
    }
    else if (report.form_type === 'F24') {
      this._reportsService
        .getReportInfo(report.form_type, report.report_id)
        .subscribe((res: form3xReportTypeDetails) => {
          localStorage.setItem('form_24_details', JSON.stringify(res[0]));
          localStorage.setItem(`form_24_report_type`, JSON.stringify(res[0]));
        });
      setTimeout(() => {
        const formType =
          report.form_type && report.form_type.length > 2 ? report.form_type.substring(1, 3) : report.form_type;
        this._router.navigate([`/forms/form/${formType}`], {
          queryParams: { step: 'transactions', reportId: report.report_id, edit: true, transactionCategory: 'disbursements', isFiled: false  }
        });
      }, 1500);
    }
  }

  /**
   * Trash the report selected by the user.
   *
   * @param rep the Report to trash
   */
  /*public trashReport(rep: ReportModel): void {

    this._dialogService
      .confirm('You are about to trash report ' + rep.reportId + '.',
        ConfirmModalComponent,
        'Caution!')
      .then(res => {
        if (res === 'okay') {
          this._reportsService.trashReport(rep)
            .subscribe((res: GetReportsResponse) => {
              this.getReportsPage(this.config.currentPage);
              this._dialogService
                .confirm('Report ' + rep.reportId +
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
   * @param rep the Report to restore
   */
  public restoreReport(rep: reportModel): void {
    this._dialogService
      .confirm('You are about to restore report ' + rep.report_id + '.', ConfirmModalComponent, 'Warning!')
      .then(res => {
        if (res === 'okay') {
          this._reportsService.trashOrRestoreReports('restore', [rep]).subscribe((res: GetReportsResponse) => {
            this.getRecyclingPage(this.config.currentPage);
            this._dialogService.confirm(
              'Report ' + rep.report_id + ' has been restored!',
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
   * Delete selected reports from the the recyle bin.
   *
   * @param rep the Report to delete
   */
  /*public deleteRecyleBin(): void {

    let beforeMessage = '';
    const selectedReports: Array<ReportModel> = [];
    for (const rep of this.reportsModel) {
      if (rep.selected) {
        selectedReports.push(rep);
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
    // this.numberOfPages = 0;
    this.config.currentPage = this._utilService.isNumber(this.config.currentPage) ? this.config.currentPage : 1;

    if (!this.reportsModel) {
      return '0';
    }

    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0 && this.reportsModel.length > 0) {
      // this.calculateNumberOfPages();

      if (this.config.currentPage === this.numberOfPages) {
        // end = this.contactsModel.length;
        end = this.config.totalItems;
        start = (this.config.currentPage - 1) * this.config.itemsPerPage + 1;
      } else {
        end = this.config.currentPage * this.config.itemsPerPage;
        start = end - this.config.itemsPerPage + 1;
      }
      // // fix issue where last page shown range > total items (e.g. 11-20 of 19).
      // if (end > this.contactsModel.length) {
      //   end = this.contactsModel.length;
      // }
    }

    this.firstItemOnPage = start;
    if (end > this.config.totalItems) {
      end = this.config.totalItems;
    }
    this.lastItemOnPage = end;
    return start + ' - ' + end;
  }
        
  public showPageSizes(): boolean {
    if (this.config && this.config.totalItems && this.config.totalItems > 0){
      return true;
    }
    return false;
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
    for (let i = this.firstItemOnPage - 1; i <= this.lastItemOnPage - 1; i++) {
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
    this.bulkActionDisabled = this.bulkActionCounter > count ? false : true;
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
      const repCols: SortableColumnModel[] = JSON.parse(sortableColumnsJson);
      for (const col of repCols) {
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
        this.setCacheValuesforView(this.reportSortableColumnsLSK, this.reportCurrentSortedColLSK, this.reportPageLSK);
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
    // shared between rep and recycle tables
    localStorage.setItem(columnsKey, JSON.stringify(this.sortableColumns));

    // shared between rep and recycle tables
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
  /**
   * Set the Table Columns model.
   */
  private setSortableColumns(): void {
    // sort column names must match the domain model names
    let defaultSortColumns = [
      'form_type',
      'status',
      'fec_id',
      'amend_ind',
      'cvg_start_date',
      'cvg_end_date',
      'report_type_desc',
      'filed_date',
      'last_update_date',
      'deleted_date',
    ];

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
    this.currentSortedColumnName = this._tableService.setSortDirection('last_update_date', this.sortableColumns, true);
  }

  private calculateNumberOfPages(): void {
    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0) {
      if (this.reportsModel && this.reportsModel.length > 0) {
        this.numberOfPages = this.reportsModel.length / this.config.itemsPerPage;
        this.numberOfPages = Math.ceil(this.numberOfPages);
      }
    }
  }

  public getErrors() {
    alert('Get Errors functionality is not yet implemented.');
  }

  public isStatusFailed(status: string): boolean {
    if (status === 'Failed') return true;
    else return false;
  }
  public trashAllSelected(): void {
    let repIds = '';
    const selectedReports: Array<reportModel> = [];
    for (const rep of this.reportsModel) {
      if (rep.selected) {
        selectedReports.push(rep);
        repIds += rep.report_id + ', ';
      }
    }

    repIds = repIds.substr(0, repIds.length - 2);

    this._dialogService
      .confirm('You are about to delete these reports.   ' + repIds, ConfirmModalComponent, 'Caution!')
      .then(res => {
        if (res === 'okay') {
          this._reportsService
            .trashOrRestoreReports('trash', selectedReports)
            .subscribe((res: GetReportsResponse) => {
              this.getReportsPage(this.config.currentPage);

              let afterMessage = '';
              if (selectedReports.length === 1) {
                afterMessage = `report ${selectedReports[0].report_id}
                  has been successfully deleted and sent to the recycle bin.`;
              } else {
                afterMessage = 'reports have been successfully deleted and sent to the recycle bin.   ' + repIds;
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

  public trashReport(rep: reportModel): void {
    this._dialogService
      .confirm('You are about to delete this report ' + rep.report_id + '.', ConfirmModalComponent, 'Warning!')
      .then(res => {
        if (res === 'okay') {
          this._reportsService.trashOrRestoreReports('trash', [rep]).subscribe((res: GetReportsResponse) => {
            //console.log("trashReport res =", res);
            if (res['result'] === 'success') {
              this.getReportsPage(this.config.currentPage);
              this._dialogService.confirm(
                'Report has been successfully deleted and sent to the recycle bin. ' + rep.report_id,
                ConfirmModalComponent,
                'Success!',
                false,
                ModalHeaderClassEnum.successHeader
              );
            } else
            {
              this.getReportsPage(this.config.currentPage);
              this._dialogService.confirm(
                'Report has not been successfully deleted and sent to the recycle bin. ' + rep.report_id,
                ConfirmModalComponent,
                'Warning!',
                false,
                ModalHeaderClassEnum.errorHeader
              );
            }
          });
          
        } else if (res === 'cancel') {
        }
      });
  }

  public restorereport(rep: reportModel): void {
    this._dialogService
      .confirm('You are about to restore report ' + rep.report_id + '.', ConfirmModalComponent, 'Caution!')
      .then(res => {
        if (res === 'okay') {
          // this._reportsService.restorereport(rep)
          //   .subscribe((res: GetReportsResponse) => {
          this._reportsService.trashOrRestoreReports('restore', [rep]).subscribe((res: GetReportsResponse) => {
            this.getRecyclingPage(this.config.currentPage);
            this._dialogService.confirm(
              'Report ' + rep.report_id + ' has been restored!',
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
  public deleteRecyleBin(): void {
    let repIds = '';
    const selectedReports: Array<reportModel> = [];
    for (const rep of this.reportsModel) {
      if (rep.selected) {
        selectedReports.push(rep);
        repIds += rep.report_id + ', ';
      }
    }
    repIds = repIds.substr(0, repIds.length - 2);

    let beforeMessage = '';
    if (selectedReports.length === 1) {
      beforeMessage = `Are you sure you want to permanently delete
       Report ${selectedReports[0].report_id}?`;
    } else {
      beforeMessage = 'Are you sure you want to permanently delete these Reports?   ' + repIds;
    }

    this._dialogService.confirm(beforeMessage, ConfirmModalComponent, 'Caution!').then(res => {
      if (res === 'okay') {
        this._reportsService.deleteRecycleBinReport(selectedReports).subscribe((res: GetReportsResponse) => {
          this.getRecyclingPage(this.config.currentPage);

          let afterMessage = '';
          if (selectedReports.length === 1) {
            afterMessage = `Report ${selectedReports[0].report_id} has been successfully deleted`;
          } else {
            afterMessage = 'Reports have been successfully deleted.   ' + repIds;
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

  public amendReport(report: reportModel): void {

    this._reportsService.amendReport(report).subscribe(res =>
      {        
        report = res;
        //console.log('new amend Res: ', report)
      
        if (report.form_type === 'F3X') {
        this._reportsService
          .getReportInfo(report.form_type, report.report_id)
          .subscribe((res: form3xReportTypeDetails) => {
            //console.log('getReportInfo res =', res);
            localStorage.setItem('form_3X_details', JSON.stringify(res[0]));
            localStorage.setItem(`form_3X_report_type`, JSON.stringify(res[0]));

            //return false;
          });
        setTimeout(() => {
          // this._router.navigate([`/forms/reports/3X/${report.report_id}`], { queryParams: { step: 'step_4' } });

          const formType =
            report.form_type && report.form_type.length > 2 ? report.form_type.substring(1, 3) : report.form_type;
          /*  
          this._router.navigate([`/forms/form/${formType}`], {
            queryParams: { step: 'reports', reportId: report.report_id }
            });
          */
          this._router.navigate([`/forms/form/${formType}`], {
            queryParams: { step: 'transactions', reportId: report.report_id, edit: true, transactionCategory: 'receipts'  }
          });
          }, 1500);
        }    
        else if (report.form_type === 'F1M') {
          const formType = '1M';
          this._router.navigate([`/forms/form/${formType}`], {
            queryParams: { step: 'step_2', reportId: report.report_id, edit:true}
          });
        }      
      }
    )    
  }
  public isUpload() {
    if (this.authService.isAdmin() ||
        this.authService.isCommitteeAdmin() ||
        this.authService.isBackupCommitteeAdmin()) {
        return true;
    }
    return false;
  }

  /**
   *
   * @param report
   */
  addMemo(report: reportModel, viewOnly : boolean = false) {
    const memoText = report.memo_text ? report.memo_text : '';
    const title = memoText ? 'Edit Memo' : 'Add Memo';
    const dialogData = {
      content: memoText,
      saveAction: SaveDialogAction.saveReportMemo,
      title: title,
      viewOnly
    };
    this.inputDialogService.openFormModal(dialogData).then((res) => {
      if (res.saveAction === SaveDialogAction.saveReportMemo) {
        const updateData = {
          report_id: report.report_id,
          memo_text: res.content
        };
        this._reportsService.updateMemo(updateData).subscribe(updateRes => {
          if (updateRes) {
            this.getReportsPage(this.config.currentPage);
          }
        });
      }
    }).catch((e) => {
      // clicked other than save
    });
  }
}
