import { Component, EventEmitter, Input, OnInit, Output, ViewChild, ElementRef, ViewChildren, QueryList } from '@angular/core';
import { style, animate, transition, trigger, state } from '@angular/animations';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { TransactionsMessageService } from 'src/app/forms/transactions/service/transactions-message.service';
import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';
import { filter, race } from 'rxjs/operators';
import { TransactionFilterModel } from '../model/report-filter.model';
import { ValidationErrorModel } from '../model/validation-error.model';
import { TransactionsService } from '../service/report.service';
import { ReportsFilterTypeComponent } from './filter-type/reports-filter-type.component';
import { ActiveView } from '../reportheader/reportheader.component';


/**
 * A component for filtering transactions located in the sidebar.
 */
@Component({
  selector: 'app-reportsidebar',
  templateUrl: './reportsidebar.component.html',
  styleUrls: ['./reportsidebar.component.scss'],
  providers: [NgbTooltipConfig, OrderByPipe],
  animations: [
    trigger('openClose', [
      state('open', style({
        'max-height': '500px', // Set high to handle multiple scenarios.
        backgroundColor: 'white',
      })),
      state('closed', style({
        'max-height': '0',
        overflow: 'hidden',
        display: 'none',
        backgroundColor: '#AEB0B5'
      })),
      transition('open => closed', [
        animate('.25s ease')
      ]),
      transition('closed => open', [
        animate('.5s ease')
      ]),
    ]),
    trigger('openCloseScroll', [
      state('open', style({
        'max-height': '500px', // Set high to handle multiple scenarios.
        backgroundColor: 'white',
        'overflow-y': 'scroll'
      })),
      state('closed', style({
        'max-height': '0',
        overflow: 'hidden',
        display: 'none',
        backgroundColor: '#AEB0B5'
      })),
      state('openNoAnimate', style({
        'max-height': '500px',
        backgroundColor: 'white',
        'overflow-y': 'scroll'
      })),
      state('closedNoAnimate', style({
        'max-height': '0',
        overflow: 'hidden',
        display: 'none',
        backgroundColor: '#AEB0B5'
      })),
      transition('open => closed', [
        animate('.25s ease')
      ]),
      transition('closed => open', [
        animate('.5s ease')
      ]),
    ]),
  ]
})
export class ReportsidebarComponent implements OnInit {

  @Input()
  public formType: string;

  @Input()
  public view: ActiveView;

  @Input()
  public title = '';

  @ViewChildren('categoryElements')
  private categoryElements: QueryList<ReportsFilterTypeComponent>;

  public isHideTypeFilter: boolean;
  public isHideCvgDateFilter: boolean;
  public isHideFiledDateFilter: boolean;
  public isHideAmountFilter: boolean;
  public isHideStateFilter: boolean;
  public isHideMemoFilter: boolean;
  public transactionCategories: any = [];
  public states: any = [];
  public filterCategoriesText = '';
  public filterAmountMin: number;
  public filterAmountMax: number;
  public filterCvgDateFrom: Date = null;
  public filterCvgDateTo: Date = null;
  public filterFiledDateFrom: Date = null;
  public filterFiledDateTo: Date = null;
  public filterMemoCode = false;
  public dateFilterValidation: ValidationErrorModel;
  public filedDateFilterValidation: ValidationErrorModel;
  public cvgDateFilterValidation: ValidationErrorModel;
  public amountFilterValidation: ValidationErrorModel;
  public isHideFormFilter: boolean;
  public isHideReportFilter: boolean;
  public isHideStatusFilter: boolean;
  public isHideAmendmentIndicatorFilter: boolean;
  public forms: any = [];
  public reports: any = [];
  public amendmentindicators: any = [];
  public statuss: any = [];

  // TODO put in a transactions constants ts file for multi component use.
  private readonly filtersLSK = 'transactions.filters';
  private cachedFilters: TransactionFilterModel = new TransactionFilterModel();
  private msEdge = true;
  private reportsView = ActiveView.reports
  private recycleBinView = ActiveView.recycleBin;

  constructor(
    private _transactionsService: TransactionsService,
    private _transactionsMessageService: TransactionsMessageService
  ) {}


  /**
   * Initialize the component.
   */
  public ngOnInit(): void {

    this.msEdge = this.isEdge();

    this.filterCvgDateFrom = null;
    this.filterCvgDateTo = null;
    this.filterFiledDateFrom = null;
    this.filterFiledDateTo = null;
    this.filterAmountMin = null;
    this.filterAmountMax = null;

    this.isHideTypeFilter = true;
    this.isHideCvgDateFilter = true;
    this.isHideFiledDateFilter = true;
    this.isHideAmountFilter = true;
    this.isHideStateFilter = true;
    this.isHideMemoFilter = true;
    this.isHideFormFilter = true;
    this.isHideReportFilter = true;
    this.isHideStatusFilter = true;
    this.isHideAmendmentIndicatorFilter = true;

    this.initValidationErrors();

    this.applyFiltersCache();
    //this.getCategoryTypes();
    //this.getStates();
    this.getReports();
    this.getForms();
    this.getStatuss();
    this.getAmendmentIndicators();
  }


  /**
   * Toggle visibility of the Type filter
   */
  public toggleTypeFilterItem() {
    this.isHideTypeFilter = !this.isHideTypeFilter;
  }


  /**
   * Toggle visibility of the Date filter
   */
  public toggleDateFilterItem() {
    this.isHideCvgDateFilter = !this.isHideCvgDateFilter;
  }


  /**
   * Toggle visibility of the Deleted Date filter
   */
  public toggleDeletedDateFilterItem() {
    this.isHideFiledDateFilter = !this.isHideFiledDateFilter;
  }


  /**
   * Toggle visibility of the Amount filter
   */
  public toggleAmountFilterItem() {
    this.isHideAmountFilter = !this.isHideAmountFilter;
  }


  /**
   * Toggle visibility of the State filter
   */
  public toggleStateFilterItem() {
    this.isHideStateFilter = !this.isHideStateFilter;
  }

  public toggleFormFilterItem() {
    this.isHideFormFilter = !this.isHideFormFilter;
  }

  public toggleReportFilterItem() {
    this.isHideReportFilter = !this.isHideReportFilter;
  }

  public toggleStatusFilterItem() {
    this.isHideStatusFilter = !this.isHideStatusFilter;
  }
  
  public toggleAmendmentIndicatorFilterItem() {
    this.isHideAmendmentIndicatorFilter = !this.isHideAmendmentIndicatorFilter;
  }

  /**
   * Toggle visibility of the Memo filter
   */
  public toggleMemoFilterItem() {
    this.isHideMemoFilter = !this.isHideMemoFilter;
  }


  /**
   * Toggle the direction of the filter collapsed or expanded
   * depending on the hidden state.
   *
   * @returns string of the class to apply
   */
  public toggleFilterDirection(isHidden: boolean) {
    return isHidden ? 'up-arrow-icon' : 'down-arrow-icon';
  }


  /**
   * Determine the state for scrolling.  The category tye wasn't displaying 
   * properly in edge with animation.  If edge, don't apply the state with animation.
   */
  public determineScrollState(isHide: boolean) {
    if (this.msEdge) {
      return !isHide ? 'openNoAnimate' : 'closedNoAnimate';
    } else {
      return !isHide ? 'open' : 'closed';
    }
  }


  /**
   * Scroll to the Category Type in the list that contains the
   * value from the category search input.
   */
  public scrollToType(): void {

    this.clearHighlightedTypes();

    if (this.filterCategoriesText === undefined ||
      this.filterCategoriesText === null ||
      this.filterCategoriesText === '') {
        return;
    }

    const typeMatches: Array<ReportsFilterTypeComponent> =
      this.categoryElements.filter(el => {
        return el.categoryType.text.toString().toLowerCase()
          .includes(this.filterCategoriesText.toLowerCase());
      });

    if (typeMatches.length > 0) {
      const scrollEl = typeMatches[0];
      if (this.msEdge) {
        scrollEl.elRef.nativeElement.scrollIntoView();
      } else {
        scrollEl.elRef.nativeElement.scrollIntoView(
          { behavior: 'smooth', block: 'center', inline: 'start' }
        );
      }
    }

    // TODO check if sequence is guaranteed to be preserved.
    for (const type of typeMatches) {
      type.categoryType.highlight = 'selected_row';
    }
  }


  /**
   * Determine if the browser is MS Edge.
   *
   * TODO put in util service
   */
  private isEdge(): boolean {
    const ua = window.navigator.userAgent;
    const edge = ua.indexOf('Edge/');
    if (edge > 0) {
      // Edge (IE 12+) => return version number
      // return parseInt(ua.substring(edge + 5, ua.indexOf('.', edge)), 10);
      return true;
    }
    return false;
  }


  /**
   * Send filter values to the table transactions component.
   * Set the filters.show to true indicating the filters have been altered.
   */
  public applyFilters() {

    if (!this.validateFilters()) {
      return;
    }

    const filters = new TransactionFilterModel();
    let modified = false;
    filters.formType = this.formType;

    // states
    const filterStates = [];
    for (const s of this.states) {
      if (s.selected) {
        filterStates.push(s.code);
        modified = true;
      }
    }
    filters.filterStates = filterStates;

    const filterForms = [];
    for (const f of this.forms) {
      if (f.selected) {
        filterForms.push(f.form_type);
        modified = true;
      }
    }
    filters.filterForms = filterForms;

    const filterReports = [];
    for (const r of this.reports) {
      if (r.selected) {
        filterReports.push(r.rpt_type);
        modified = true;
      }
    }
    filters.filterReports = filterReports;
 
    const filterAmendmentIndicators = [];
    for (const a of this.amendmentindicators) {
      if (a.selected) {
        filterAmendmentIndicators.push(a.amendmentindicator_cd);
        modified = true;
      }
    }
    filters.filterAmendmentIndicators = filterAmendmentIndicators

    const filterStatuss = [];
    for (const s of this.statuss) {
      if (s.selected) {
        filterStatuss.push(s.status_cd);
        modified = true;
      }
    }
    filters.filterStatuss =filterStatuss;

    // type/category
    const filterCategories = [];
    // if (this.filterCategoriesText.length > 0) {
    //   modified = true;
    //   filterCategories.push(this.filterCategoriesText);
    // }
    for (const category of this.transactionCategories) {
      if (category.options) {
        for (const option of category.options) {
          if (option.selected) {
            modified = true;
            // TODO use code with backend
            filterCategories.push(option.text);
          }
        }
      }
    }
    filters.filterCategories = filterCategories;
    // filters.filterCategoriesText = this.filterCategoriesText;

    filters.filterAmountMin = this.filterAmountMin;
    filters.filterAmountMax = this.filterAmountMax;

    if (this.filterAmountMin !== null) {
      modified = true;
    }
    if (this.filterAmountMax !== null) {
      modified = true;
    }

    filters.filterCvgDateFrom = this.filterCvgDateFrom;
    filters.filterCvgDateTo = this.filterCvgDateTo;
    if (this.filterCvgDateFrom !== null) {
      modified = true;
    }
    if (this.filterCvgDateTo !== null) {
      modified = true;
    }


    filters.filterFiledDateFrom = this.filterFiledDateFrom;
    filters.filterFiledDateTo = this.filterFiledDateTo;
    if (this.filterFiledDateFrom !== null) {
      modified = true;
    }
    if (this.filterFiledDateTo !== null) {
      modified = true;
    }

    if (this.filterMemoCode) {
      filters.filterMemoCode = this.filterMemoCode;
      modified = true;
    }

    filters.show = modified;
    this._transactionsMessageService.sendApplyFiltersMessage(filters);
  }


  /**
   * Clear all filter values.
   */
  public clearFilters() {

    this.initValidationErrors();

    // clear the scroll to input
    this.filterCategoriesText = '';
    this.clearHighlightedTypes();


    for (const s of this.states) {
      s.selected = false;
    }
    for (const f of this.forms) {
      f.selected = false;
    }
    for (const r of this.reports) {
      r.selected = false;
    }
    for (const s of this.statuss) {
      s.selected = false;
    }
    for (const a of this.amendmentindicators) {
      a.selected = false;
    }
    for (const category of this.transactionCategories) {
      if (category.options) {
        for (const option of category.options) {
          option.selected = false;
        }
      }
    }
    this.filterAmountMin = null;
    this.filterAmountMax = null;
    this.filterCvgDateFrom = null;
    this.filterCvgDateTo = null;
    this.filterFiledDateFrom = null;
    this.filterFiledDateTo = null;
    this.filterMemoCode = false;

    this.applyFilters();
  }


  /**
   * Check if the view to show is Recycle Bin.
   */
  public isRecycleBinViewActive() {
    return this.view === this.recycleBinView ? true : false;
  }


  /**
   * Clear any hightlighted types as result of the scroll to input.
   */
  private clearHighlightedTypes() {
    for (const el of this.categoryElements.toArray()) {
      el.categoryType.highlight = '';
    }
  }


  /**
   * Get the Category Types from the server for populating
   * filter options on Type.
   */

  /*private getCategoryTypes() {
    this._transactionsService
    .getTransactionCategories(this.formType)
      .subscribe(res => {

        let categoriesExist = false;
        const categoriesGroupArray = [];
        if (res.data) {
          if (res.data.transactionCategories) {
            categoriesExist = true;

            // 1st node is the group of types (not checkable).
            // 2nd node is ignored.
            // 3rd node is the type checkable.
            for (const node1 of res.data.transactionCategories) {
              const categoryGroup: any = {};
              categoryGroup.text = node1.text;
              categoryGroup.options = [];

              for (const node2 of node1.options) {
                for (const option of node2.options) {
                  if (this.cachedFilters.filterCategories) {
                    // check for categories selected in the filter cache
                    // TODO scroll to first check item
                    if (this.cachedFilters.filterCategories.includes(option.text)) {
                      option.selected = true;
                      this.isHideTypeFilter = false;
                    } else {
                      option.selected = false;
                    }
                  }
                  categoryGroup.options.push(option);
                }
              }
              if (categoryGroup.options.length > 0) {
                categoriesGroupArray.push(categoryGroup);
              }
            }
          }
        }
        if (categoriesExist) {
          this.transactionCategories = categoriesGroupArray;
          // this.transactionCategories = this._orderByPipe.transform(
          //   res.data.transactionCategories, {property: 'text', direction: 1});
        } else {
          this.transactionCategories = [];
        }
    });
  }


  /**
   * Get US State Codes and Values.
   */

   /*
  private getStates() {
    console.log(" In getStates Report Data received... !");
    // TODO using this service to get states until available in another API.
    this._transactionsService
      .getStates('3X', 'Individual Receipt')
        .subscribe(res => {
          let statesExist = false;
          if (res.data) {
            console.log("Report Data received... !");
            if (res.data.states) {
              statesExist = true;
              for (const s of res.data.states) {
                // check for states selected in the filter cache
                // TODO scroll to first check item
                if (this.cachedFilters.filterStates) {
                  if (this.cachedFilters.filterStates.includes(s.code)) {
                    s.selected = true;
                    this.isHideStateFilter = false;
                  } else {
                    s.selected = false;
                  }
                }
              }
            }
          }
          if (statesExist) {
            this.states = res.data.states;
            console.log("Report this.states = ", this.states);
          } else {
            this.states = [];
            console.log("Report this.states = ", this.states);
          }
        });
  } */


  private getForms() {
    //console.log(" In getForms Report Data received... !");
    // TODO using this service to get forms until available in another API.
    this._transactionsService
      .getFormTypes()
        .subscribe(res => {
          let formsExist = false;
          if (res) {
             console.log("getForms Data received...res !", res);
             formsExist = true;
              for (const s of res) {
                // check for forms selected in the filter cache
                // TODO scroll to first check item
                if (this.cachedFilters.filterForms) {
                  if (this.cachedFilters.filterForms.includes(s.code)) {
                    s.selected = true;
                    this.isHideStateFilter = false;
                  } else {
                    s.selected = false;
                  }
              }
            }
          }
          if (formsExist) {
            this.forms = res;
            console.log("Report this.forms = ", this.forms);
          } else {
            this.forms = [];
            console.log("Report this.forms = ", this.forms);
          }
        });
  }

  private getReports() {
    console.log(" In getReports Report Data received... !");
    // TODO using this service to get reports until available in another API.
    this._transactionsService
      .getReportTypes()
        .subscribe(res => {
          let reportsExist = false;
          if (res) {
            console.log("Report Data received... !");
             reportsExist = true;
              for (const s of res) {
                // check for reports selected in the filter cache
                // TODO scroll to first check item
                if (this.cachedFilters.filterReports) {
                  if (this.cachedFilters.filterReports.includes(s.code)) {
                    s.selected = true;
                    this.isHideStateFilter = false;
                  } else {
                    s.selected = false;
                  }
                }
            }
          }
          if (reportsExist) {
            this.reports = res;
            console.log("Report this.reports = ", this.reports);
          } else {
            this.reports = [];
            console.log("Report this.reports = ", this.reports);
          }
        });
  }
 
  private getStatuss() {
    console.log(" In getStatuss Report Data received... !");
    // TODO using this service to get reports until available in another API.
    this._transactionsService
      .getStatuss()
        .subscribe(res => {
          let StatussExist = false;
          if (res.data) {
            console.log("Report Data received... !");
            StatussExist = true;
              for (const s of res.data) {
                // check for reports selected in the filter cache
                // TODO scroll to first check item
                if (this.cachedFilters.filterStatuss) {
                  if (this.cachedFilters.filterStatuss.includes(s.code)) {
                    s.selected = true;
                    this.isHideStatusFilter = false;
                  } else {
                    s.selected = false;
                 }
              }
            }
          }
          if (StatussExist) {
            this.statuss = res.data;
            console.log("Report this.statuss = ", this.statuss);
          } else {
            this.statuss = [];
            console.log("Report this.statuss = ", this.statuss);
          }
        });
  }

  private getAmendmentIndicators() {
    console.log(" In getAmendmentIndicators Report Data received... !");
    // TODO using this service to get reports until available in another API.
    this._transactionsService
      .getAmendmentIndicators()
        .subscribe(res => {
          let amendmentindicatorsExist = false;
          if (res.data) {
            console.log("Report Data received... !");
              amendmentindicatorsExist = true;
              for (const s of res.data) {
                // check for reports selected in the filter cache
                // TODO scroll to first check item
                if (this.cachedFilters.filterAmendmentIndicators) {
                  if (this.cachedFilters.filterAmendmentIndicators.includes(s.code)) {
                    s.selected = true;
                    this.isHideStateFilter = false;
                  } else {
                    s.selected = false;
                  }
                }
            }
          }
          if (amendmentindicatorsExist) {
            this.amendmentindicators = res.data;
            console.log("Report this.amendmentindicators = ", this.amendmentindicators);
          } else {
            this.amendmentindicators = [];
            console.log("Report this.amendmentindicators = ", this.amendmentindicators);
          }
        });
  }


  /**
   * Get the filters from the cache.
   */
  private applyFiltersCache() {
    const filtersJson: string | null = localStorage.getItem(this.filtersLSK);
    if (filtersJson != null) {
      this.cachedFilters = JSON.parse(filtersJson);
      if (this.cachedFilters) {
        this.filterCategoriesText = this.cachedFilters.filterCategoriesText;
        if (this.filterCategoriesText) {
          this.isHideTypeFilter = !(this.filterCategoriesText.length > 0);
        }

        this.filterCvgDateFrom = this.cachedFilters.filterCvgDateFrom;
        this.filterCvgDateTo = this.cachedFilters.filterCvgDateTo;
        this.isHideCvgDateFilter = (this.filterCvgDateFrom && this.filterCvgDateTo) ? false : true;

        this.filterFiledDateFrom = this.cachedFilters.filterFiledDateFrom;
        this.filterFiledDateTo = this.cachedFilters.filterFiledDateTo;
        this.isHideFiledDateFilter = (this.filterFiledDateFrom && this.filterFiledDateTo)
          ? false : true;

        this.filterMemoCode = this.cachedFilters.filterMemoCode;
        this.isHideMemoFilter = !this.filterMemoCode;
        // Note state and type apply filters are handled after server call to get values.

      }
    } else {
      // Just in case cache has an unexpected issue, use default.
      this.cachedFilters = new TransactionFilterModel();
    }
  }


  /**
   * Initialize validation errors to their defaults.
   */
  private initValidationErrors() {
    this.dateFilterValidation = new ValidationErrorModel(null, false);
    this.filedDateFilterValidation = new ValidationErrorModel(null, false);
    this.cvgDateFilterValidation = new ValidationErrorModel(null, false);
    //this.amountFilterValidation = new ValidationErrorModel(null, false);
  }


  /**
   * Some browsers (Chrome) set date to "" when click x to delete input.
   * If empty string, set to null to sinplify condition checks.
   */
  private handleDateAsSpaces(date: any) {
    return date === '' ? null : date;
  }


  /**
   * Validate the filter settings.  Set the the validation error model
   * to true with a message if invalid.
   *
   * @returns true if valid.
   */
  private validateFilters(): boolean {

    this.filterCvgDateTo = this.handleDateAsSpaces(this.filterCvgDateTo);
    this.filterCvgDateFrom = this.handleDateAsSpaces(this.filterCvgDateFrom);
    this.filterFiledDateTo = this.handleDateAsSpaces(this.filterFiledDateTo);
    this.filterFiledDateFrom = this.handleDateAsSpaces(this.filterFiledDateFrom);

    this.initValidationErrors();
    if (this.filterCvgDateFrom !== null && (this.filterCvgDateTo === null)) {
      this.dateFilterValidation.isError = true;
      this.dateFilterValidation.message = 'To Date is required';
      this.isHideCvgDateFilter = false;
      return false;
    }
    if (this.filterCvgDateTo !== null && this.filterCvgDateFrom === null) {
      this.dateFilterValidation.isError = true;
      this.dateFilterValidation.message = 'From Date is required';
      this.isHideCvgDateFilter = false;
      return false;
    }
    if (this.filterCvgDateFrom > this.filterCvgDateTo) {
      this.dateFilterValidation.isError = true;
      this.dateFilterValidation.message = 'From Date must preceed To Date';
      this.isHideCvgDateFilter = false;
      return false;
    }

    if (this.filterFiledDateFrom !== null && this.filterFiledDateTo === null) {
      this.filedDateFilterValidation.isError = true;
      this.filedDateFilterValidation.message = 'To Deleted Date is required';
      this.isHideFiledDateFilter = false;
      return false;
    }
    if (this.filterFiledDateTo !== null && this.filterFiledDateFrom === null) {
      this.filedDateFilterValidation.isError = true;
      this.filedDateFilterValidation.message = 'From Deleted Date is required';
      this.isHideFiledDateFilter = false;
      return false;
    }
    if (this.filterFiledDateFrom > this.filterFiledDateTo) {
      this.filedDateFilterValidation.isError = true;
      this.filedDateFilterValidation.message = 'From Filed Date must preceed To Filed Date';
      this.isHideFiledDateFilter = false;
      return false;
    }

     return true;
  }

}
