import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { style, animate, transition, trigger, state } from '@angular/animations';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { TransactionsMessageService } from '../service/transactions-message.service';

@Component({
  selector: 'app-transactions-filter-sidebar',
  templateUrl: './transactions-filter-sidebar.component.html',
  styleUrls: ['./transactions-filter-sidebar.component.scss'],
  providers: [NgbTooltipConfig],
  animations: [
    trigger('openClose', [
      state('open', style({
        'max-height': '500px', // Set high to handle multiple scenarios.
        // height: 'auto',
        // opacity: 1,
        backgroundColor: 'white',
      })),
      state('closed', style({
        'max-height': '0',
        overflow: 'hidden',
        // height: '0',
        display: 'none',
        // opacity: 0.5,
        backgroundColor: '#AEB0B5'
      })),
      transition('open => closed', [
        animate('.25s')
      ]),
      transition('closed => open', [
        animate('.5s')
      ]),
    ]),
  ]
})
export class TransactionsFilterSidbarComponent implements OnInit {

  @Input()
  public formType: string;

  @Input()
  public title = '';

  public flyIn = false;

  public isHideTypeFilter: boolean;
  public isHideDateFilter: boolean;
  public isHideAmountFilter: boolean;
  public isHideStateFilter: boolean;
  public isHideMemoFilter: boolean;
  public transactionCategories: any = [];
  public states: any = [];
  public searchFilter = '';

  constructor(
    private _formService: FormsService,
    private _transactionsMessageService: TransactionsMessageService,
  ) {}

  public ngOnInit(): void {
    this.isHideTypeFilter = true;
    this.isHideDateFilter = true;
    this.isHideAmountFilter = true;
    this.isHideStateFilter = true;
    this.isHideMemoFilter = true;

    if (this.formType) {
      this._formService
      .getTransactionCategories(this.formType)
        .subscribe(res => {
          this.transactionCategories = res.data.transactionCategories;
        });

      // TODO need to pass in the dynamic transaction type.
      // Using default for dev purposes
      this._formService
        .getDynamicFormFields(this.formType, 'Individual Receipt')
          .subscribe(res => {
            this.states = res.data.states;
            this.transactionCategories = res.data.transactionCategories;
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
    return isHidden ? 'fa-chevron-up' : 'fa-chevron-down';
  }


  /**
   * Send filter values to the table transactions component.
   */
  public applyFilters() {
    const filters: any = {};
    filters.search = this.searchFilter;
    this._transactionsMessageService.sendApplyFiltersMessage(filters);
  }


  /**
   * Clear filters currently set.
   */
  public clearFilters() {
    this.searchFilter = '';
  }

}
