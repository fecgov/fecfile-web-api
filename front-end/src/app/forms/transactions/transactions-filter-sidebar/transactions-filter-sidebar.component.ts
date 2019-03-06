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

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() title = '';

  public isHideTypeFilter: boolean;
  public isHideDateFilter: boolean;
  public isHideAmountFilter: boolean;
  public isHideStateFilter: boolean;
  public isHideMemoFilter: boolean;

  constructor(
    private _config: NgbTooltipConfig,
  ) {}

  public ngOnInit(): void {
    this.isHideTypeFilter = true;
    this.isHideDateFilter = true;
    this.isHideAmountFilter = true;
    this.isHideStateFilter = true;
    this.isHideMemoFilter = true;
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

  public toggleFilterDirection(isHidden: boolean) {
    return isHidden ? 'fa-chevron-up' : 'fa-chevron-down';
  }
}
