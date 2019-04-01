import { Component, EventEmitter, Input, OnInit, Output, ViewChild, ElementRef, ViewChildren, QueryList } from '@angular/core';
import { style, animate, transition, trigger, state } from '@angular/animations';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { TransactionsMessageService } from '../service/transactions-message.service';
import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';
import { filter } from 'rxjs/operators';
import { TransactionFilterModel } from '../model/transaction-filter.model';
import { ValidationErrorModel } from '../model/validation-error.model';
import { TransactionsService } from '../service/transactions.service';
import { TransactionsFilterTypeComponent } from './filter-type/transactions-filter-type.component';
import { ActiveView } from '../transactions.component';


/**
 * A component for filtering transactions located in the sidebar.
 */
@Component({
  selector: 'app-transactions-filter',
  templateUrl: './transactions-filter.component.html',
  styleUrls: ['./transactions-filter.component.scss'],
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
export class TransactionsFilterComponent implements OnInit {

  @Input()
  public formType: string;

  @Input()
  public view: ActiveView;

  @Input()
  public title = '';

  @ViewChildren('categoryElements')
  private categoryElements: QueryList<TransactionsFilterTypeComponent>;

  public isHideTypeFilter: boolean;
  public isHideDateFilter: boolean;
  public isHideDeletedDateFilter: boolean;
  public isHideAmountFilter: boolean;
  public isHideStateFilter: boolean;
  public isHideMemoFilter: boolean;
  public transactionCategories: any = [];
  public states: any = [];
  public filterCategoriesText = '';
  public filterAmountMin: number;
  public filterAmountMax: number;
  public filterDateFrom: Date = null;
  public filterDateTo: Date = null;
  public filterDeletedDateFrom: Date = null;
  public filterDeletedDateTo: Date = null;
  public filterMemoCode = false;
  public dateFilterValidation: ValidationErrorModel;
  public delDateFilterValidation: ValidationErrorModel;
  public amountFilterValidation: ValidationErrorModel;

  // TODO put in a transactions constants ts file for multi component use.
  private readonly filtersLSK = 'transactions.filters';
  private cachedFilters: TransactionFilterModel = new TransactionFilterModel();
  private msEdge = true;
  private transactionsView = ActiveView.transactions;
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

    this.filterDateFrom = null;
    this.filterDateTo = null;
    this.filterDeletedDateFrom = null;
    this.filterDeletedDateTo = null;
    this.filterAmountMin = null;
    this.filterAmountMax = null;

    this.isHideTypeFilter = true;
    this.isHideDateFilter = true;
    this.isHideDeletedDateFilter = true;
    this.isHideAmountFilter = true;
    this.isHideStateFilter = true;
    this.isHideMemoFilter = true;

    this.initValidationErrors();

    if (this.formType) {
      this.applyFiltersCache();
      this.getCategoryTypes();
      this.getStates();
    }
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
    this.isHideDateFilter = !this.isHideDateFilter;
  }


  /**
   * Toggle visibility of the Deleted Date filter
   */
  public toggleDeletedDateFilterItem() {
    this.isHideDeletedDateFilter = !this.isHideDeletedDateFilter;
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

    const typeMatches: Array<TransactionsFilterTypeComponent> =
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

    filters.filterDateFrom = this.filterDateFrom;
    filters.filterDateTo = this.filterDateTo;
    if (this.filterDateFrom !== null) {
      modified = true;
    }
    if (this.filterDateTo !== null) {
      modified = true;
    }


    filters.filterDeletedDateFrom = this.filterDeletedDateFrom;
    filters.filterDeletedDateTo = this.filterDeletedDateTo;
    if (this.filterDeletedDateFrom !== null) {
      modified = true;
    }
    if (this.filterDeletedDateTo !== null) {
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
    for (const category of this.transactionCategories) {
      if (category.options) {
        for (const option of category.options) {
          option.selected = false;
        }
      }
    }
    this.filterAmountMin = null;
    this.filterAmountMax = null;
    this.filterDateFrom = null;
    this.filterDateTo = null;
    this.filterDeletedDateFrom = null;
    this.filterDeletedDateTo = null;
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
  private getCategoryTypes() {
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
  private getStates() {
    // TODO using this service to get states until available in another API.
    this._transactionsService
      .getStates(this.formType, 'Individual Receipt')
        .subscribe(res => {

          let statesExist = false;
          if (res.data) {
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
          } else {
            this.states = [];
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

        this.filterAmountMin = this.cachedFilters.filterAmountMin;
        this.filterAmountMax = this.cachedFilters.filterAmountMax;
        this.isHideAmountFilter = !(this.filterAmountMin > 0 && this.filterAmountMax > 0);

        this.filterDateFrom = this.cachedFilters.filterDateFrom;
        this.filterDateTo = this.cachedFilters.filterDateTo;
        this.isHideDateFilter = (this.filterDateFrom && this.filterDateTo) ? false : true;

        this.filterDeletedDateFrom = this.cachedFilters.filterDeletedDateFrom;
        this.filterDeletedDateTo = this.cachedFilters.filterDeletedDateTo;
        this.isHideDeletedDateFilter = (this.filterDeletedDateFrom && this.filterDeletedDateTo)
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
    this.delDateFilterValidation = new ValidationErrorModel(null, false);
    this.amountFilterValidation = new ValidationErrorModel(null, false);
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

    this.filterDateTo = this.handleDateAsSpaces(this.filterDateTo);
    this.filterDateFrom = this.handleDateAsSpaces(this.filterDateFrom);
    this.filterDeletedDateTo = this.handleDateAsSpaces(this.filterDeletedDateTo);
    this.filterDeletedDateFrom = this.handleDateAsSpaces(this.filterDeletedDateFrom);

    this.initValidationErrors();
    if (this.filterDateFrom !== null && (this.filterDateTo === null)) {
      this.dateFilterValidation.isError = true;
      this.dateFilterValidation.message = 'To Date is required';
      this.isHideDateFilter = false;
      return false;
    }
    if (this.filterDateTo !== null && this.filterDateFrom === null) {
      this.dateFilterValidation.isError = true;
      this.dateFilterValidation.message = 'From Date is required';
      this.isHideDateFilter = false;
      return false;
    }
    if (this.filterDateFrom > this.filterDateTo) {
      this.dateFilterValidation.isError = true;
      this.dateFilterValidation.message = 'From Date must preceed To Date';
      this.isHideDateFilter = false;
      return false;
    }

    if (this.filterDeletedDateFrom !== null && this.filterDeletedDateTo === null) {
      this.delDateFilterValidation.isError = true;
      this.delDateFilterValidation.message = 'To Deleted Date is required';
      this.isHideDeletedDateFilter = false;
      return false;
    }
    if (this.filterDeletedDateTo !== null && this.filterDeletedDateFrom === null) {
      this.delDateFilterValidation.isError = true;
      this.delDateFilterValidation.message = 'From Deleted Date is required';
      this.isHideDeletedDateFilter = false;
      return false;
    }
    if (this.filterDeletedDateFrom > this.filterDeletedDateTo) {
      this.delDateFilterValidation.isError = true;
      this.delDateFilterValidation.message = 'From Deleted Date must preceed To Deleted Date';
      this.isHideDeletedDateFilter = false;
      return false;
    }

    if (this.filterAmountMin !== null && this.filterAmountMax === null) {
      this.amountFilterValidation.isError = true;
      this.amountFilterValidation.message = 'Maximum Amount is required';
      this.isHideAmountFilter = false;
      return false;
    }
    if (this.filterAmountMax !== null && this.filterAmountMin === null) {
      this.amountFilterValidation.isError = true;
      this.amountFilterValidation.message = 'Minimum Amount is required';
      this.isHideAmountFilter = false;
      return false;
    }
    if (this.filterAmountMin > this.filterAmountMax) {
      this.amountFilterValidation.isError = true;
      this.amountFilterValidation.message = 'Maximum is less than Minimum';
      this.isHideAmountFilter = false;
      return false;
    }

    return true;
  }

}
