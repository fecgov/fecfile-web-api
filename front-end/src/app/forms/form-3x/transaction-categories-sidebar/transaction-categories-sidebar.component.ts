import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';

@Component({
  selector: 'transaction-categories-sidebar',
  templateUrl: './transaction-categories-sidebar.component.html',
  styleUrls: ['./transaction-categories-sidebar.component.scss'],
  providers: [NgbTooltipConfig]
})
export class TransactionCategoriesSidbarComponent implements OnInit {

  @Input() transactionCategories: any = [];
  @Input() searchField: any = {};
  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() title: string = '';
  @Input() cashOnHand: any = {};


  public itemSelected: string = '';
  public additionalItemSelected: string = '';
  public additionalOptions: Array<any> = [];
  public loadingData: boolean = true;
  public steps: any = {};
  public currentStep: string = 'step_2';
  public step: string = '';

  private _indexOfItemSelected: number = null;

  constructor(
    private _config: NgbTooltipConfig,
    private _formService: FormsService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    console.log('cashOnHand: ', this.cashOnHand);
  }

  public selectItem(item): void {
    this.itemSelected = item.getAttribute('value');

    this.additionalOptions = [];

    this.transactionCategories.findIndex((el, index) => {
      if (el.value === this.itemSelected) {
        this._indexOfItemSelected = index;
      }
    });

    this.status.emit({
      additionalOptions: this.additionalOptions
    });
  }

  public selectedAdditionalOption(additionalItem): void {
    let additionalItemIndex: number = null;

    this.additionalItemSelected = additionalItem.getAttribute('value');
    this.transactionCategories[this._indexOfItemSelected].options.findIndex((el, index) => {
      if (this.additionalItemSelected === el.value) {
        additionalItemIndex = index;
      }
    });

    this.additionalOptions = this.transactionCategories[this._indexOfItemSelected].options[additionalItemIndex].options;

    this.status.emit({
      additionalOptions: this.additionalOptions
    });
  }
}
