import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';

@Component({
  selector: 'app-transaction-categories',
  templateUrl: './transaction-categories.component.html',
  styleUrls: ['./transaction-categories.component.scss'],
  providers: [NgbTooltipConfig]
})
export class TransactionCategoriesComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() title = '';

  public additionalItemSelected = '';
  public additionalOptions: Array<any> = [];
  public cashOnHand: any = {};
  public currentStep = 'step_2';
  public itemSelected = '';
  public loadingData = true;
  public searchField: any = {};
  public steps: any = {};
  public step = '';
  public transactionCategories: any = [];

  private _formType = '';
  private _indexOfItemSelected: number = null;

  constructor(
    private _config: NgbTooltipConfig,
    private _formService: FormsService,
    private _http: HttpClient,
    private _activatedRoute: ActivatedRoute
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this._formService
      .getTransactionCategories(this._formType)
      .subscribe(res => {
        this.cashOnHand = res.data.cashOnHand;

        this.transactionCategories = res.data.transactionCategories;

        this.searchField = res.data.transactionSearchField;
      });
  }

  public selectItem(item): void {
    console.log('selectItem: ');
    this.itemSelected = item.getAttribute('value');

    this.additionalOptions = [];

    this.transactionCategories.findIndex((el, index) => {
      if (el.value === this.itemSelected) {
        this._indexOfItemSelected = index;
      }
    });

    if (localStorage.getItem(`form_${this._formType}_transactionType`) === null) {
      localStorage.setItem(`form_${this._formType}_transactionType`, JSON.stringify({
        'category': this.itemSelected,
        'type': ''
      }));
    }
  }

  public selectedAdditionalOption(additionalItem): void {
    let additionalItemIndex: number = null;
    const transactionType: any = JSON.parse(localStorage.getItem(`form_${this._formType}_transactionType`));

    this.additionalItemSelected = additionalItem.getAttribute('value');

    transactionType.type = this.additionalItemSelected;

    localStorage.setItem(`form_${this._formType}_transactionType`, JSON.stringify(transactionType));

    this.transactionCategories[this._indexOfItemSelected].options.findIndex((el, index) => {
      if (this.additionalItemSelected === el.value) {
        additionalItemIndex = index;
      }
    });

    this.additionalOptions = this.transactionCategories[this._indexOfItemSelected].options[additionalItemIndex].options;

    this.status.emit({
      form: 'transactionCategories',
      additionalOptions: this.additionalOptions,
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2'
    });
  }
}
