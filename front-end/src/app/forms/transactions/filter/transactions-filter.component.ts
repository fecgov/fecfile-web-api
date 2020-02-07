import { animate, state, style, transition, trigger } from '@angular/animations';
import { Component, Input, OnDestroy, OnInit, QueryList, ViewChildren } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { Subject } from 'rxjs';
import 'rxjs/add/operator/takeUntil';
import { Subscription } from 'rxjs/Subscription';
import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';
import { TransactionTypeService } from '../../form-3x/transaction-type/transaction-type.service';
import { FilterTypes } from "../enums/filterTypes.enum";
import { TransactionFilterModel } from '../model/transaction-filter.model';
import { ValidationErrorModel } from '../model/validation-error.model';
import { TransactionsMessageService } from '../service/transactions-message.service';
import { TransactionsService } from '../service/transactions.service';
import { ActiveView } from '../transactions.component';
import { TransactionsFilterTypeComponent } from './filter-type/transactions-filter-type.component';

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
      state(
        'open',
        style({
          'max-height': '500px', // Set high to handle multiple scenarios.
          backgroundColor: 'white'
        })
      ),
      state(
        'closed',
        style({
          'max-height': '0',
          overflow: 'hidden',
          display: 'none',
          backgroundColor: '#AEB0B5'
        })
      ),
      transition('open => closed', [animate('.25s ease')]),
      transition('closed => open', [animate('.5s ease')])
    ]),
    trigger('openCloseScroll', [
      state(
        'open',
        style({
          'max-height': '500px', // Set high to handle multiple scenarios.
          backgroundColor: 'white',
          'overflow-y': 'scroll'
        })
      ),
      state(
        'closed',
        style({
          'max-height': '0',
          overflow: 'hidden',
          display: 'none',
          backgroundColor: '#AEB0B5'
        })
      ),
      state(
        'openNoAnimate',
        style({
          'max-height': '500px',
          backgroundColor: 'white',
          'overflow-y': 'scroll'
        })
      ),
      state(
        'closedNoAnimate',
        style({
          'max-height': '0',
          overflow: 'hidden',
          display: 'none',
          backgroundColor: '#AEB0B5'
        })
      ),
      transition('open => closed', [animate('.25s ease')]),
      transition('closed => open', [animate('.5s ease')])
    ])
  ]
})
export class TransactionsFilterComponent implements OnInit, OnDestroy {
  @Input()
  public formType: string;

  @Input()
  public title = '';

  @ViewChildren('categoryElements')
  private categoryElements: QueryList<TransactionsFilterTypeComponent>;

  public isHideTypeFilter: boolean;
  public isHideDateFilter: boolean;
  public isHideDeletedDateFilter: boolean;
  public isHideAmountFilter: boolean;
  public isHideAggregateAmountFilter: boolean;
  public isHideStateFilter: boolean;
  public isHideMemoFilter: boolean;
  public isHideItemizationFilter: boolean;
  public isHideElectionCode: boolean;
  public isHideElectionYear: boolean;
  public isHideloanClosingBalanceFilter: boolean;
  public isHideScheduleFilter: boolean;
  public isHideDebtBeginningBalanceFilter: boolean;
  public transactionCategories: any = [];
  public states: any = [];
  public itemizations: any = [];
  public electionCodes: any = [
    { option: 'primary', selected: false },
    { option: 'general', selected: false },
    { option: 'other', selected: false }
  ];
  
  public filterCategoriesText = '';
  public filterAmountMin: number;
  public filterAmountMax: number;
  public filterLoanAmountMin: number;
  public filterLoanAmountMax: number;
  public filterAggregateAmountMin: number;
  public filterAggregateAmountMax: number;
  public filterLoanClosingBalanceMin: number;
  public filterLoanClosingBalanceMax: number;
  public filterDebtBeginningBalanceMin: number;
  public filterDebtBeginningBalanceMax: number;
  public filterDateFrom: Date = null;
  public filterDateTo: Date = null;
  public filterDeletedDateFrom: Date = null;
  public filterDeletedDateTo: Date = null;
  public filterMemoCode = false;
  public filterElectionCode = false;
  public filterElectionYearFrom: string;
  public filterElectionYearTo: string;
  public filterSchedule: string;

  public dateFilterValidation: ValidationErrorModel;
  public deletedDateFilterValidation: ValidationErrorModel;
  public amountFilterValidation: ValidationErrorModel;
  public aggregateAmountFilterValidation: ValidationErrorModel;
  public yearFilterValidation: ValidationErrorModel;
  public loanClosingBalanceFilterValidation: ValidationErrorModel;
  public debtBeginningBalanceFilterValidation: ValidationErrorModel;
  public transactionCategory: string = '';
  public editMode: boolean = false;
  
  private onDestroy$ = new Subject();

  /**
   * Subscription for removing selected filters.
   */
  private removeFilterSubscription: Subscription;

  /**
   * Subscription for switch filters for ActiveView of the traansaction table.
   */
  private switchFilterViewSubscription: Subscription;
  
  private clearAllFiltersSubscription: Subscription;

  // TODO put in a transactions constants ts file for multi component use.
  private readonly filtersLSK = 'transactions.filters';
  private cachedFilters: TransactionFilterModel = new TransactionFilterModel();
  private msEdge = true;
  private view = ActiveView.transactions;

  constructor(
    private _transactionsService: TransactionsService,
    private _transactionsMessageService: TransactionsMessageService,
    private _transactionTypeService: TransactionTypeService,
    private _activatedRoute: ActivatedRoute
  ) {
    this._transactionsMessageService
      .getRemoveFilterMessage()
      .takeUntil(this.onDestroy$)
      .subscribe((message: any) => {
        if (message) {
          if (message.removeAll) {
            this.clearFilters();
          } else {
            this.removeFilter(message);
          }
        }
      });

    this._transactionsMessageService
      .getSwitchFilterViewMessage()
      .takeUntil(this.onDestroy$)
      .subscribe((message: ActiveView) => {
        switch (message) {
          case ActiveView.transactions:
            this.view = message;
            break;
          case ActiveView.recycleBin:
            this.view = message;
            break;
          default:
            this.view = ActiveView.transactions;
            console.log('unexpected ActiveView received: ' + message);
        }
      });

    this._transactionsMessageService
    .getClearAllFiltersMessage()
    .takeUntil(this.onDestroy$)
    .subscribe(message => {
      this.clearAndApplyFilters();
    })

    _activatedRoute.queryParams.takeUntil(this.onDestroy$).subscribe(p => {
      this.transactionCategory = p.transactionCategory;
      if (p.edit === 'true' || p.edit === true) {
        this.editMode = true;
      }
      if (p.transactionCategory) {
        this.transactionCategory = p.transactionCategory;
      }
    });
  }

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
    this.filterLoanAmountMin = null;
    this.filterLoanAmountMax = null;
    this.filterAggregateAmountMin = null;
    this.filterAggregateAmountMax = null;
    this.filterLoanClosingBalanceMin = null;
    this.filterLoanClosingBalanceMax = null;
    this.filterDebtBeginningBalanceMin = null;
    this.filterDebtBeginningBalanceMax = null;

    this.isHideTypeFilter = true;
    this.isHideDateFilter = true;
    this.isHideDeletedDateFilter = true;
    this.isHideAmountFilter = true;
    this.isHideAggregateAmountFilter = true;
    this.isHideloanClosingBalanceFilter = true;
    this.isHideDebtBeginningBalanceFilter = true;
    this.isHideStateFilter = true;
    this.isHideMemoFilter = true;
    this.isHideItemizationFilter = true;
    this.isHideElectionCode = true;
    this.isHideElectionYear = true;
    this.isHideScheduleFilter = true;

    this.initValidationErrors();

    if (this.formType) {
      this.applyFiltersCache();
      this.getCategoryTypes();
      this.getStates();
      this.getItemizations();
    }
  }

 

  /**
   * A method to run when component is destroyed.
   */
  public ngOnDestroy(): void {
    this.onDestroy$.next(true);
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
   * Toggle visibility of the Balance at Close filter
   */
  public toggleBalanceAtCloseFilterItem() {
    this.isHideloanClosingBalanceFilter = !this.isHideloanClosingBalanceFilter;
  }

  /**
   * Toggle visibility of the Debt Beginning Balance filter
   */
  public toggleDebtBeginningBalanceFilterItem() {
    this.isHideDebtBeginningBalanceFilter = !this.isHideDebtBeginningBalanceFilter;
  }

  /**
   * Toggle visibility of the Aggregate Amount filter
   */
  public toggleAggregateAmountFilterItem() {
    this.isHideAggregateAmountFilter = !this.isHideAggregateAmountFilter;
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
   * Toggle visibility of the Schedule filter
   */
  public toggleScheduleFilterItem() {
    this.isHideScheduleFilter = !this.isHideScheduleFilter;
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

  public toggleItemizationFilterItem() {
    this.isHideItemizationFilter = !this.isHideItemizationFilter;
  }

  public toggleElectionCodeFilterItem() {
    this.isHideElectionCode = !this.isHideElectionCode;
  }

  public toggleElectionYearFilterItem() {
    this.isHideElectionYear = !this.isHideElectionYear;
  }

  /**
   * Determine the state for scrolling.  The category tye wasn't displaying
   * properly in edge with animation.  If edge, don't apply the state with animation.
   */
  public determineScrollState() {
    if (this.msEdge) {
      return !this.isHideTypeFilter ? 'openNoAnimate' : 'closedNoAnimate';
    } else {
      return !this.isHideTypeFilter ? 'open' : 'closed';
    }
  }

  public determineScrollItemization() {
    if (this.msEdge) {
      return !this.isHideItemizationFilter ? 'openNoAnimate' : 'closedNoAnimate';
    } else {
      return !this.isHideItemizationFilter ? 'open' : 'closed';
    }
  }

  /**
   * Scroll to the Category Type in the list that contains the
   * value from the category search input.
   */
  public scrollToType(): void {
    this.clearHighlightedTypes();

    if (
      this.filterCategoriesText === undefined ||
      this.filterCategoriesText === null ||
      this.filterCategoriesText === ''
    ) {
      return;
    }

    const typeMatches: Array<TransactionsFilterTypeComponent> = this.categoryElements.filter(el => {
      return el.categoryType.text
        .toString()
        .toLowerCase()
        .includes(this.filterCategoriesText.toLowerCase());
    });

    if (typeMatches.length > 0) {
      const scrollEl = typeMatches[0];
      if (this.msEdge) {
        scrollEl.elRef.nativeElement.scrollIntoView();
      } else {
        scrollEl.elRef.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'start' });
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
  public applyFilters(isClearKeyword: boolean) {
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

    filters.filterAmountMin = this.filterAmountMin;
    filters.filterAmountMax = this.filterAmountMax;
    filters.filterAggregateAmountMin = this.filterAggregateAmountMin;
    filters.filterAggregateAmountMax = this.filterAggregateAmountMax;
    filters.filterLoanAmountMin = this.filterLoanAmountMin;
    filters.filterLoanAmountMax = this.filterLoanAmountMax;
    filters.filterLoanClosingBalanceMin = this.filterLoanClosingBalanceMin;
    filters.filterLoanClosingBalanceMax = this.filterLoanClosingBalanceMax;
    filters.filterDebtBeginningBalanceMin = this.filterDebtBeginningBalanceMin;
    filters.filterDebtBeginningBalanceMax = this.filterDebtBeginningBalanceMax;

    if (this.filterAmountMin !== null) {
      modified = true;
    }
    if (this.filterAmountMax !== null) {
      modified = true;
    }
    if (this.filterAggregateAmountMin !== null) {
      modified = true;
    }
    if (this.filterAggregateAmountMax !== null) {
      modified = true;
    }
    if (this.filterLoanAmountMin !== null) {
      modified = true;
    }
    if (this.filterLoanAmountMax !== null) {
      modified = true;
    }
    if (this.filterLoanClosingBalanceMin !== null) {
      modified = true;
    }
    if (this.filterLoanClosingBalanceMax !== null) {
      modified = true;
    }
    if (this.filterDebtBeginningBalanceMin !== null) {
      modified = true;
    }
    if (this.filterDebtBeginningBalanceMax !== null) {
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

    if (this.filterElectionYearFrom && this.filterElectionYearTo) {
      filters.filterElectionYearFrom = this.filterElectionYearFrom;
      filters.filterElectionYearTo = this.filterElectionYearTo;
      modified = true;
    }
    console.log('itemizations = ', this.itemizations);
    const filterItemizations = [];
    for (const I of this.itemizations) {
      if (I.selected) {
        console.log('I.itemized', I.itemized);
        filterItemizations.push(I.itemized);
        console.log('itemization tag found...');
        modified = true;
      }
    }
    filters.filterItemizations = filterItemizations;
    console.log('filters.filterItemizations =', filters.filterItemizations);

    const filterElectionCodes = [];
    for (const I of this.electionCodes) {
      if (I.selected) {
        console.log('I.electionCode', I.option);
        filterElectionCodes.push(I.option);
        modified = true;
      }
    }
    filters.filterElectionCodes = filterElectionCodes;

    filters.filterSchedule = this.filterSchedule;

    filters.show = modified;
    this._transactionsMessageService.sendApplyFiltersMessage({ filters: filters, isClearKeyword: isClearKeyword });
  }

  /**
   * Clear all filter values.
   */
  private clearFilters() {
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

    for (const s of this.itemizations) {
      s.selected = false;
    }

    this.filterAmountMin = null;
    this.filterAmountMax = null;
    this.filterAggregateAmountMin = null;
    this.filterAggregateAmountMax = null;
    this.filterLoanAmountMin = null;
    this.filterLoanAmountMax = null;
    this.filterLoanClosingBalanceMin = null;
    this.filterLoanClosingBalanceMax = null;
    this.filterDebtBeginningBalanceMin = null;
    this.filterDebtBeginningBalanceMax = null;

    this.filterDateFrom = null;
    this.filterDateTo = null;
    this.filterDeletedDateFrom = null;
    this.filterDeletedDateTo = null;
    this.filterMemoCode = false;

    this.filterElectionCode = null;
    for (const s of this.electionCodes) {
      s.selected = false;
    }
    this.filterElectionYearFrom = null;
    this.filterElectionYearTo = null;
    this.filterSchedule = null;
  }

  /**
   * Clear all filter values and apply them by running the search.
   */
  public clearAndApplyFilters() {
    this.clearFilters();
    this.applyFilters(true);
  }

  /**
   * Check if the view to show is Transactions.
   */
  public isTransactionViewActive() {
    return this.view === ActiveView.transactions ? true : false;
  }

  /**
   * Check if the view to show is Recycle Bin.
   */
  public isRecycleBinViewActive() {
    return this.view === ActiveView.recycleBin ? true : false;
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
   /*  this._transactionTypeService.getTransactionCategories(this.formType).subscribe(res => {
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
                if (this.cachedFilters) {
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
    }); */
    this._transactionTypeService.getTransactionTypes(this.formType).subscribe(res => {
      let categoriesExist = false;
      let categoriesGroupArray = [];
        if (res) {
          categoriesExist = true;

          const receiptsArr = res.filter(obj => obj.categoryType === 'Receipts');
          const disbursementsArr = res.filter(obj => obj.categoryType === 'Disbursements');
          const loansAndDebtsArr = res.filter(obj => obj.categoryType === 'Loans and Debts');
          const otherArr = res.filter(obj => obj.categoryType === 'Other');

          categoriesGroupArray = [
            {text:'Receipts', options: receiptsArr},
            {text:'Disbursements', options: disbursementsArr},
            {text:'Loans and Debts', options: loansAndDebtsArr},
            {text:'Other', options: otherArr},
          ];


        }
      if (categoriesExist) {
        this.transactionCategories = categoriesGroupArray;
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
    // Passing INDV_REC as type but any should do as states are not specific to
    // transaction type.
    this._transactionsService.getStates(this.formType, 'INDV_REC').subscribe(res => {
      let statesExist = false;
      if (res.data) {
        if (res.data.states) {
          statesExist = true;
          for (const s of res.data.states) {
            // check for states selected in the filter cache
            // TODO scroll to first check item
            if (this.cachedFilters) {
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
      }
      if (statesExist) {
        this.states = res.data.states;
      } else {
        this.states = [];
      }
    });
  }

  private getItemizations() {
    // TODO using this service to get Itemizations until available in another API.
    this._transactionsService.getItemizations().subscribe(res => {
      let itemizationExist = false;
      if (res.data) {
        console.log('res.data', res.data);
        itemizationExist = true;
        for (const s of res.data) {
          // check for Itemizations selected in the filter cache
          // TODO scroll to first check item
          if (this.cachedFilters) {
            if (this.cachedFilters.filterItemizations) {
              if (this.cachedFilters.filterItemizations.includes(s.itemized)) {
                s.selected = true;
                this.isHideItemizationFilter = false;
              } else {
                s.selected = false;
              }
            }
          }
        }
      }
      if (itemizationExist) {
        this.itemizations = res.data;
        console.log('this.itemizations', this.itemizations);
      } else {
        this.itemizations = [];
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

        this.filterAggregateAmountMin = this.cachedFilters.filterAggregateAmountMin;
        this.filterAggregateAmountMax = this.cachedFilters.filterAggregateAmountMax;
        this.isHideAggregateAmountFilter = !(this.filterAggregateAmountMin > 0 && this.filterAggregateAmountMax > 0);

        this.filterLoanAmountMin = this.cachedFilters.filterLoanAmountMin;
        this.filterLoanAmountMax = this.cachedFilters.filterLoanAmountMax;
        this.isHideAmountFilter = !(this.filterLoanAmountMin > 0 && this.filterLoanAmountMax > 0);

        this.filterLoanClosingBalanceMin = this.cachedFilters.filterLoanClosingBalanceMin;
        this.filterLoanClosingBalanceMax = this.cachedFilters.filterLoanClosingBalanceMax;
        this.isHideloanClosingBalanceFilter = !(this.filterLoanClosingBalanceMin > 0 && this.filterLoanClosingBalanceMax > 0);

        this.filterDebtBeginningBalanceMin = this.cachedFilters.filterDebtBeginningBalanceMin;
        this.filterDebtBeginningBalanceMax = this.cachedFilters.filterDebtBeginningBalanceMax;
        this.isHideDebtBeginningBalanceFilter = !(this.filterDebtBeginningBalanceMin > 0 && this.filterDebtBeginningBalanceMax > 0);

        this.filterDateFrom = this.cachedFilters.filterDateFrom;
        this.filterDateTo = this.cachedFilters.filterDateTo;
        this.isHideDateFilter = this.filterDateFrom && this.filterDateFrom ? false : true;

        this.filterDeletedDateFrom = this.cachedFilters.filterDeletedDateFrom;
        this.filterDeletedDateTo = this.cachedFilters.filterDeletedDateTo;
        this.isHideDeletedDateFilter = this.filterDeletedDateFrom && this.filterDeletedDateFrom ? false : true;

        this.filterMemoCode = this.cachedFilters.filterMemoCode;
        this.isHideMemoFilter = !this.filterMemoCode;
        // Note state and type apply filters are handled after server call to get values.

        // TODO itenized was left out and needs to be added.
        this.itemizations = this.cachedFilters.filterItemizations;
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
    this.deletedDateFilterValidation = new ValidationErrorModel(null, false);
    this.amountFilterValidation = new ValidationErrorModel(null, false);
    this.aggregateAmountFilterValidation = new ValidationErrorModel(null, false);
    this.yearFilterValidation = new ValidationErrorModel(null, false);
    this.loanClosingBalanceFilterValidation = new ValidationErrorModel(null, false);
    this.debtBeginningBalanceFilterValidation = new ValidationErrorModel(null, false);
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

    if (this.filterDeletedDateFrom !== null && this.filterDeletedDateTo === null) {
      this.deletedDateFilterValidation.isError = true;
      this.deletedDateFilterValidation.message = 'To Date is required';
      this.isHideDeletedDateFilter = false;
      return false;
    }
    if (this.filterDeletedDateTo !== null && this.filterDeletedDateFrom === null) {
      this.deletedDateFilterValidation.isError = true;
      this.deletedDateFilterValidation.message = 'From Date is required';
      this.isHideDeletedDateFilter = false;
      return false;
    }
    if (this.filterDeletedDateFrom > this.filterDeletedDateTo) {
      this.deletedDateFilterValidation.isError = true;
      this.deletedDateFilterValidation.message = 'From Date must preceed To Date';
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

    if (this.filterAggregateAmountMin !== null && this.filterAggregateAmountMax === null) {
      this.aggregateAmountFilterValidation.isError = true;
      this.aggregateAmountFilterValidation.message = 'Maximum Aggregate Amount is required';
      this.isHideAggregateAmountFilter = false;
      return false;
    }
    if (this.filterAggregateAmountMax !== null && this.filterAggregateAmountMin === null) {
      this.aggregateAmountFilterValidation.isError = true;
      this.aggregateAmountFilterValidation.message = 'Minimum Aggregate Amount is required';
      this.isHideAggregateAmountFilter = false;
      return false;
    }
    if (this.filterAggregateAmountMin > this.filterAggregateAmountMax) {
      this.aggregateAmountFilterValidation.isError = true;
      this.aggregateAmountFilterValidation.message = 'Maximum is less than Minimum';
      this.isHideAggregateAmountFilter = false;
      return false;
    }

    if (this.filterLoanAmountMin !== null && this.filterLoanAmountMax === null) {
      this.amountFilterValidation.isError = true;
      this.amountFilterValidation.message = 'Maximum Amount is required';
      this.isHideAmountFilter = false;
      return false;
    }
    if (this.filterLoanAmountMax !== null && this.filterLoanAmountMin === null) {
      this.amountFilterValidation.isError = true;
      this.amountFilterValidation.message = 'Minimum Amount is required';
      this.isHideAmountFilter = false;
      return false;
    }
    if (this.filterLoanAmountMin > this.filterLoanAmountMax) {
      this.amountFilterValidation.isError = true;
      this.amountFilterValidation.message = 'Maximum is less than Minimum';
      this.isHideAmountFilter = false;
      return false;
    }

    if (this.filterLoanClosingBalanceMin !== null && this.filterLoanClosingBalanceMax === null) {
      this.loanClosingBalanceFilterValidation.isError = true;
      this.loanClosingBalanceFilterValidation.message = 'Maximum Amount is required';
      this.isHideloanClosingBalanceFilter = false;
      return false;
    }
    if (this.filterLoanClosingBalanceMax !== null && this.filterLoanClosingBalanceMin === null) {
      this.loanClosingBalanceFilterValidation.isError = true;
      this.loanClosingBalanceFilterValidation.message = 'Minimum Amount is required';
      this.isHideloanClosingBalanceFilter = false;
      return false;
    }
    if (this.filterLoanClosingBalanceMin > this.filterLoanClosingBalanceMax) {
      this.loanClosingBalanceFilterValidation.isError = true;
      this.loanClosingBalanceFilterValidation.message = 'Maximum is less than Minimum';
      this.isHideloanClosingBalanceFilter = false;
      return false;
    }
    
    if (this.filterDebtBeginningBalanceMin !== null && this.filterDebtBeginningBalanceMax === null) {
      this.debtBeginningBalanceFilterValidation.isError = true;
      this.debtBeginningBalanceFilterValidation.message = 'Maximum Amount is required';
      this.isHideDebtBeginningBalanceFilter = false;
      return false;
    }
    if (this.filterDebtBeginningBalanceMax !== null && this.filterDebtBeginningBalanceMin === null) {
      this.debtBeginningBalanceFilterValidation.isError = true;
      this.debtBeginningBalanceFilterValidation.message = 'Minimum Amount is required';
      this.isHideDebtBeginningBalanceFilter = false;
      return false;
    }
    if (this.filterDebtBeginningBalanceMin > this.filterDebtBeginningBalanceMax) {
      this.debtBeginningBalanceFilterValidation.isError = true;
      this.debtBeginningBalanceFilterValidation.message = 'Maximum is less than Minimum';
      this.isHideDebtBeginningBalanceFilter = false;
      return false;
    }

    if (
      this.filterElectionYearFrom !== null &&
      this.filterElectionYearFrom !== undefined &&
      (this.filterElectionYearTo === null || this.filterElectionYearTo === undefined)
    ) {
      this.amountFilterValidation.isError = true;
      this.amountFilterValidation.message = 'Election year from is required';
      this.isHideElectionYear = false;
      return false;
    }
    if (
      this.filterElectionYearTo !== null &&
      this.filterElectionYearTo !== undefined &&
      (this.filterElectionYearFrom === null || this.filterElectionYearFrom === undefined)
    ) {
      this.yearFilterValidation.isError = true;
      this.yearFilterValidation.message = 'Election year to is required';
      this.isHideElectionYear = false;
      return false;
    }

    let intfilterElectionYearFrom = parseInt(this.filterElectionYearFrom);
    let intfilterElectionYearTo = parseInt(this.filterElectionYearTo);
    if (intfilterElectionYearFrom > intfilterElectionYearTo) {
      this.yearFilterValidation.isError = true;
      this.yearFilterValidation.message = 'Maximum is less than Minimum';
      this.isHideElectionYear = false;
      return false;
    }
    if (
      this.filterElectionYearTo !== null &&
      this.filterElectionYearFrom !== null &&
      (this.filterElectionYearTo !== undefined && this.filterElectionYearFrom !== undefined) &&
      (!/^\d{4}$/.test(this.filterElectionYearFrom) || !/^\d{4}$/.test(this.filterElectionYearTo))
    ) {
      this.yearFilterValidation.isError = true;
      this.yearFilterValidation.message = 'Must be a valid year';
      this.isHideElectionYear = false;
      return false;
    }
    if (this.filterElectionYearTo !== null && this.filterElectionYearFrom !== null &&
      this.filterElectionYearTo !== undefined && this.filterElectionYearFrom !== undefined) {
      this.filterElectionYearFrom = this.filterElectionYearFrom.toString();
      this.filterElectionYearTo = this.filterElectionYearTo.toString();
    }
    if (this.filterElectionYearTo === '' && this.filterElectionYearFrom === '') {
      this.filterElectionYearFrom = null;
      this.filterElectionYearTo = null;
    }

    return true;
  }

  /**
   * Process the message received to remove the filter.
   *
   * @param message contains details on the filter to remove
   */
  private removeFilter(message: any) {
    if (message) {
      if (message.key) {
        switch (message.key) {
          case FilterTypes.state:
            for (const st of this.states) {
              if (st.code === message.value) {
                st.selected = false;
              }
            }
            break;
          case FilterTypes.category:
            for (const categoryGroup of this.transactionCategories) {
              for (const categoryType of categoryGroup.options) {
                if (categoryType.text === message.value) {
                  categoryType.selected = false;
                }
              }
            }
            break;
          case FilterTypes.date:
            this.filterDateFrom = null;
            this.filterDateTo = null;
            break;
          case FilterTypes.deletedDate:
            this.filterDeletedDateFrom = null;
            this.filterDeletedDateTo = null;
            break;
          case FilterTypes.amount:
            this.filterAmountMin = null;
            this.filterAmountMax = null;
            break;
          case FilterTypes.aggregateAmount:
            this.filterAggregateAmountMin = null;
            this.filterAggregateAmountMax = null;
            break;
          case FilterTypes.loanAmount:
            this.filterLoanAmountMin = null;
            this.filterLoanAmountMax = null;
            break;
          case FilterTypes.loanClosingBalance:
            this.filterLoanClosingBalanceMin = null;
            this.filterLoanClosingBalanceMax = null;
            break;
          case FilterTypes.debtBeginningBalance:
          this.filterDebtBeginningBalanceMin = null;
          this.filterDebtBeginningBalanceMax = null;
          break;
          case FilterTypes.memoCode:
            this.filterMemoCode = false;
            break;
          case FilterTypes.itemizations:
            for (const itemization of this.itemizations) {
              if (itemization.itemized === message.value) {
                itemization.selected = false;
              }
            }
            break;
          case FilterTypes.electionCodes:
            for (const electionCode of this.electionCodes) {
              if (electionCode.option === message.value) {
                electionCode.selected = false;
              }
            }
            break;
          case FilterTypes.electionYear:
            this.filterElectionYearFrom = null;
            this.filterElectionYearTo = null;
            break;
          case FilterTypes.schedule:
            this.filterSchedule = null;
            break;
          default:
            console.log('unexpected key for remove filter = ' + message.key);
        }
      }
    }
  }
}
