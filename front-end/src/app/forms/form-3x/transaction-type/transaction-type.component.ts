import { Component, EventEmitter, Input, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { form3x_data } from '../../../shared/interfaces/FormsService/FormsService';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { TransactionTypeService } from './transaction-type.service';

@Component({
  selector: 'f3x-transaction-type',
  templateUrl: './transaction-type.component.html',
  styleUrls: ['./transaction-type.component.scss'],
  providers: [NgbTooltipConfig],
  encapsulation: ViewEncapsulation.None
})
export class TransactionTypeComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() selectedOptions: any = {};
  @Input() transactionType: string = '';
  @Input() formOptionsVisible: boolean = false;
  @Input() transactionCategories: any = [];

  public childOptions: any = [];
  public childOptionType: string = '';
  public childOptionFailed: boolean = false;
  public frmOption: FormGroup;
  public frmSubmitted: boolean = false;
  public parentOptionFailed: boolean = false;
  public showForm: boolean = false;
  public searchField: any = {};
  public secondaryOptions: any = [];
  public mainTransactionCategory: any = [];
  public secondaryTransactionType: string = '';
  public secondaryTransactionTypeFailed : boolean = false;

  private _formType: string = '';
  private _transactionCategory: string = '';
  private _transactionCategories: any = [];

  constructor(
    private _fb: FormBuilder,
    private _config: NgbTooltipConfig,
    private _activatedRoute: ActivatedRoute,
    private _formService: FormsService,
    private _messageService: MessageService,
    private _transactionTypeService: TransactionTypeService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this.frmOption = this._fb.group({
      secondaryTransactionType: ['', Validators.required],
      childTransactionType: ['', Validators.required]
    });
  }

  ngDoCheck(): void {
    if (this.transactionType) {
      this.parentOptionFailed = false;
    }

    if (this.secondaryTransactionType) {
      this.secondaryTransactionTypeFailed = false;
    }

    if (this.childOptionType) {
      this.childOptionFailed = false;
    }

    if (this.transactionType && localStorage.getItem(`form_${this._formType}_temp_transaction_type`) === null) {
      this._setSecondaryTransactionCategories();
    } else if (this.transactionType && localStorage.getItem(`form_${this._formType}_temp_transaction_type`) !== null) {
      const transactionObj: any = JSON.parse(localStorage.getItem(`form_${this._formType}_temp_transaction_type`));

      if (transactionObj.mainTransactionTypeText !== this.transactionType) {
        this._setSecondaryTransactionCategories();
      }
    }
  }

  /**
   * Validates the form on submit.
   */
  public doValidateOption() {
    if (this.frmOption.valid) {

      if (localStorage.getItem(`form_${this._formType}_temp_transaction_type`) !== null) {
        const transObj: any = JSON.parse(localStorage.getItem(`form_${this._formType}_temp_transaction_type`));

        window.localStorage.setItem(`form_${this._formType}_transaction_type`, JSON.stringify(transObj));

        window.localStorage.removeItem(`form_${this._formType}_temp_transaction_type`);
      }

      this.status.emit({
        form: this.frmOption,
        direction: 'next',
        step: 'step_3',
        previousStep: 'step_2'
      });
      return 1;
    } else {
      if (!this.transactionType) {
        this.parentOptionFailed = true;
      } else {
        this.parentOptionFailed = false;
      }

      if (!this.secondaryTransactionType) {
        this.secondaryTransactionTypeFailed = true;
      } else {
        this.secondaryTransactionTypeFailed = false;
      }

      if (this.childOptions.length >= 1) {
        if (!this.childOptionType) {
          this.childOptionFailed = true;
        } else {
          this.childOptionFailed = false;
        }
      }

      return 0;
    }
  }

  /**
   * Updates the type selected when radio button clicked.
   *
   * @param      {Object}  e       The event object.
   */
  public updateTypeSelected(e): void {
    const type: string = e.target.getAttribute('data-type');

    if (type === 'secondaryTransactionType') {
      const val: string = this.frmOption.controls['secondaryTransactionType'].value;

      this.secondaryTransactionType = val;

      this.secondaryTransactionTypeFailed = true;

      if (localStorage.getItem(`form_${this._formType}_temp_transaction_type`) !== null) {
        const tempObj: any = JSON.parse(localStorage.getItem(`form_${this._formType}_temp_transaction_type`));

        window.localStorage.removeItem(`form_${this._formType}_temp_transaction_type`);

        tempObj.secondaryTransactionType = val;

        window.localStorage.setItem(`form_${this._formType}_temp_transaction_type`, JSON.stringify(tempObj));

        this._setChildTransactionCategories();
      }
    } else if (type === 'childTransactionType') {
      const val: string = this.frmOption.controls['childTransactionType'].value;

      this.childOptionType = val;

      this.childOptionFailed = false;

      if (localStorage.getItem(`form_${this._formType}_temp_transaction_type`) !== null) {
        const tempObj: any = JSON.parse(localStorage.getItem(`form_${this._formType}_temp_transaction_type`));

        window.localStorage.removeItem(`form_${this._formType}_temp_transaction_type`);

        tempObj.childTransactionType = val;

        window.localStorage.setItem(`form_${this._formType}_temp_transaction_type`, JSON.stringify(tempObj));
      }
    }
  }

  /**
   * Sets the secondary transaction categories.
   */
  private _setSecondaryTransactionCategories(): void {
    this.mainTransactionCategory = this.transactionCategories.filter(el => (el.value === this.transactionType));
    const mainTransactionTypeText: string = this.mainTransactionCategory[0].text;
    const mainTransactionTypeValue: string = this.mainTransactionCategory[0].value;
    const transactionObj: any = {
      mainTransactionTypeText,
      mainTransactionTypeValue,
      'secondaryTransactionType': '',
      'childTransactionType': ''
    };

    localStorage.setItem(`form_${this._formType}_temp_transaction_type`, JSON.stringify(transactionObj));

    this.secondaryOptions = this.mainTransactionCategory[0].options;

    this.transactionType = null;

    if (this.childOptionType) {
      this.childOptionType = '';
      this.childOptions = [];
    }

    if (this.secondaryTransactionType) {
      this.secondaryTransactionType = '';
    }
  }

  /**
   * Sets the child transaction categories.
   */
  private _setChildTransactionCategories(): void {
    const childOptionObj: any = this.secondaryOptions.filter(el => (this.secondaryTransactionType === el.value));

    if (typeof childOptionObj === 'object') {
      if (childOptionObj[0].hasOwnProperty('options')) {
        if (Array.isArray(childOptionObj[0].options)) {
          this.childOptions = childOptionObj[0].options;
        }
      }
    }
  }

  /**
   * Goes to the previous step.
   */
  public previousStep(): void {
    this.status.emit({
      form: {},
      direction: 'previous',
      step: 'step_1'
    });
  }
}
