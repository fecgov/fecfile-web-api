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
  public filterDateFrom = new Date();
  public filterDateTo = new Date();
  public filterMemoCode = false;

  constructor(
    private _formService: FormsService,
    private _transactionsMessageService: TransactionsMessageService,
    private _orderByPipe: OrderByPipe
  ) {
    // this._orderByPipe = new OrderByPipe();
  }


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
                  s.selected = false;
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

  public toggleTypeFilterItem() {
    this.isHideTypeFilter = !this.isHideTypeFilter;
  }

  public toggleDateFilterItem() {
    this.isHideDateFilter = !this.isHideDateFilter;
  }

  public toggleAmountFilterItem() {
    this.isHideAmountFilter = !this.isHideAmountFilter;
  }

  public toggleStateFilterItem() {
    this.isHideStateFilter = !this.isHideStateFilter;
  }

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
    for (const c of this.transactionCategories) {
      if (c.selected) {
        filterCategories.push(c.text); // TODO use c.code with backend
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
    for (const t of this.transactionCategories) {
      t.selected = false;
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

            // First node is the group or types (not checkable)
            // 3rd node is the type checkable
            for (const node1 of res.data.transactionCategories) {
              const categoryGroup: any = {};
              categoryGroup.text = node1.text;
              categoryGroup.options = [];

              for (const node2 of node1.options) {
                for (const option of node2.options) {
                  option.selected = false;
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

}
