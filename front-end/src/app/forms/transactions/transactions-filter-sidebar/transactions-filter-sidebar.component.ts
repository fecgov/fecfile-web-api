import { Component, EventEmitter, Input, OnInit, Output, ViewChild, ElementRef } from '@angular/core';
import { style, animate, transition, trigger, state } from '@angular/animations';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { TransactionsMessageService } from '../service/transactions-message.service';
import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';
import { filter } from 'rxjs/operators';
import { TransactionFilterModel } from '../model/transaction-filter.model';
import { ValidationErrorModel } from '../model/validation-error.model';
import { TransactionsService } from '../service/transactions.service';


/**
 * A component for filtering transactions located in the sidebar.
 */
@Component({
  selector: 'app-transactions-filter-sidebar',
  templateUrl: './transactions-filter-sidebar.component.html',
  styleUrls: ['./transactions-filter-sidebar.component.scss'],
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
      transition('open => closed', [
        animate('.25s ease')
      ]),
      transition('closed => open', [
        animate('.5s ease')
      ]),
    ]),
  ]
})
export class TransactionsFilterSidbarComponent implements OnInit {

  @Input()
  public formType: string;

  @Input()
  public title = '';


  public isHideTypeFilter: boolean;
  public isHideDateFilter: boolean;
  public isHideAmountFilter: boolean;
  public isHideStateFilter: boolean;
  public isHideMemoFilter: boolean;
  public transactionCategories: any = [];
  public states: any = [];
  public searchFilter = '';
  public filterAmountMin = 0;
  public filterAmountMax = 0;
  public filterDateFrom: Date = null;
  public filterDateTo: Date = null;
  public filterMemoCode = false;
  public dateFilterValidation: ValidationErrorModel;
  public amountFilterValidation: ValidationErrorModel;

  // TODO put in a transactions constants ts file for multi component use.
  private readonly filtersLSK = 'transactions.filters';
  private cachedFilters: TransactionFilterModel = new TransactionFilterModel();

  constructor(
    private _transactionsService: TransactionsService,
    private _transactionsMessageService: TransactionsMessageService,
    private _orderByPipe: OrderByPipe
  ) {}


  /**
   * Initialize the component.
   */
  public ngOnInit(): void {



    this.isHideTypeFilter = true;
    this.isHideDateFilter = true;
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
    filters.searchFilter = this.searchFilter;
    modified = this.searchFilter.length > 0;

    const filterStates = [];
    for (const s of this.states) {
      if (s.selected) {
        filterStates.push(s.code);
        modified = true;
      }
    }
    filters.filterStates = filterStates;

    const filterCategories = [];
    for (const category of this.transactionCategories) {
      if (category.options) {
        for (const option of category.options) {
          if (option.selected) {
            modified = true;
            filterCategories.push(option.text); // TODO use code with backend
          }
        }
      }
    }
    filters.filterCategories = filterCategories;

    filters.filterAmountMin = this.filterAmountMin;
    filters.filterAmountMax = this.filterAmountMax;
    if (this.filterAmountMin > 0) {
      modified = true;
    }
    if (this.filterAmountMax > 0) {
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

    this.searchFilter = '';
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
    this.filterAmountMin = 0;
    this.filterAmountMax = 0;
    this.filterDateFrom = null;
    this.filterDateTo = null;
    this.filterMemoCode = false;
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
        this.searchFilter = this.cachedFilters.searchFilter;

        this.filterAmountMin = this.cachedFilters.filterAmountMin;
        this.filterAmountMax = this.cachedFilters.filterAmountMax;
        this.isHideAmountFilter = !(this.filterAmountMin > 0 && this.filterAmountMax > 0);

        this.filterDateFrom = this.cachedFilters.filterDateFrom;
        this.filterDateTo = this.cachedFilters.filterDateTo;
        this.isHideDateFilter = (this.filterDateFrom === null && this.filterDateFrom === null);

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
    this.amountFilterValidation = new ValidationErrorModel(null, false);
  }


  /**
   * Validate the filter settings.  Set the the validation error model
   * to true with a message if invalid.
   * 
   * @returns true if valid.
   */
  private validateFilters(): boolean {
    this.initValidationErrors();
    if (this.filterDateFrom !== null && this.filterDateTo === null) {
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

    if (this.filterAmountMin > 0 && this.filterAmountMax === 0) {
      this.amountFilterValidation.isError = true;
      this.amountFilterValidation.message = 'Maximum Amount is required';
      this.isHideAmountFilter = false;
      return false;
    }
    if (this.filterAmountMax > 0 && this.filterAmountMin === 0) {
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
