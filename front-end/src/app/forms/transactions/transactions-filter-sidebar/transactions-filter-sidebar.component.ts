import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { style, animate, transition, trigger, state } from '@angular/animations';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { TransactionsMessageService } from '../service/transactions-message.service';
import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';
import { filter } from 'rxjs/operators';

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
  public filterDateFrom: Date;
  public filterDateTo: Date;
  public filterMemoCode = false;

  private readonly filtersLSK = 'transactions.filters';
  private cachedFilters: any = [];

  constructor(
    private _formService: FormsService,
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

    if (this.formType) {

      this.applyFiltersCache();
      this.getCategoryTypes();

      // TODO using this service to get states until available in another API.
      this._formService
        .getDynamicFormFields(this.formType, 'Individual Receipt')
          .subscribe(res => {

            let statesExist = false;
            if (res.data) {
              if (res.data.states) {
                statesExist = true;
                for (const s of res.data.states) {
                  // check for states selected in the filter cache
                  if (this.cachedFilters.filterStates) {
                    s.selected = (this.cachedFilters.filterStates.includes(s.code)) ? true : false;
                    this.isHideStateFilter = false;
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
   */
  public applyFilters() {
    const filters: any = {};
    // filters.show = true;
    filters.formType = this.formType;
    filters.search = this.searchFilter;

    const filterStates = [];
    for (const s of this.states) {
      if (s.selected) {
        filterStates.push(s.code);
      }
    }
    filters.filterStates = filterStates;

    const filterCategories = [];
    for (const category of this.transactionCategories) {
      if (category.options) {
        for (const option of category.options) {
          if (option.selected) {
            filterCategories.push(option.text); // TODO use code with backend
          }
        }
      }
    }
    filters.filterCategories = filterCategories;

    filters.filterAmountMin = this.filterAmountMin;
    filters.filterAmountMax = this.filterAmountMax;

    filters.filterDateFrom = this.filterDateFrom;
    filters.filterDateTo = this.filterDateTo;

    if (this.filterMemoCode) {
      filters.filterMemoCode = this.filterMemoCode;
    }

    this._transactionsMessageService.sendApplyFiltersMessage(filters);
  }


  /**
   * Clear all filter values.
   */
  public clearFilters() {
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
    this._formService
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
                    option.selected = (this.cachedFilters.filterCategories.includes(option.text)) ? true : false;
                    this.isHideTypeFilter = false;
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
   * Get the filters from the cache.
   */
  private applyFiltersCache() {
    const filtersJson: string | null = localStorage.getItem(this.filtersLSK);
    if (filtersJson != null) {
      this.cachedFilters = JSON.parse(filtersJson);
    } else {
      // Just in case cache has an unexpected issue, use default.
      this.cachedFilters = [];
    }
  }

}
