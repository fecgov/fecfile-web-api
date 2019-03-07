import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';

@Component({
  selector: 'app-transactions-filter-sidebar',
  templateUrl: './transactions-filter-sidebar.component.html',
  styleUrls: ['./transactions-filter-sidebar.component.scss'],
  providers: [NgbTooltipConfig]
})
export class TransactionsFilterSidbarComponent implements OnInit {

  @Input()
  public formType: string;

  @Input()
  public title = '';

  @Output()
  public status: EventEmitter<any> = new EventEmitter<any>();

  public isHideTypeFilter: boolean;
  public isHideDateFilter: boolean;
  public isHideAmountFilter: boolean;
  public isHideStateFilter: boolean;
  public isHideMemoFilter: boolean;
  public transactionCategories: any = [];
  public searchFilter = '';

  constructor(
    private _formService: FormsService,
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

  public applyFilters() {
    const filters: any = {};
    filters.search = this.searchFilter;
  }

}
