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
    if (Array.isArray(this.selectedOptions)) {
      if (this.selectedOptions.length >= 1) {
        this.showForm = true;
      }
    }

    if (localStorage.getItem(`form_${this._formType}_transaction_type`) !== null) {
      const transactionObj: any = JSON.parse(localStorage.getItem(`form_${this._formType}_transaction_type`));

      if (transactionObj.hasOwnProperty('parentTransactionTypeValue')) {
        if (typeof transactionObj.parentTransactionTypeValue === 'string') {
          this.transactionType = transactionObj.parentTransactionTypeValue;
        }
      }

      if (transactionObj.hasOwnProperty('secondaryTransactionType')) {
        if (typeof transactionObj.secondaryTransactionType === 'string') {
          this.secondaryTransactionType = transactionObj.secondaryTransactionType;
        }
      }

      if (this.transactionType) {
        this.mainTransactionCategory = this.transactionCategories.filter(el => (el.value === this.transactionType));
        if (Array.isArray(this.mainTransactionCategory)) {
          if (Array.isArray(this.mainTransactionCategory[0].options)) {
            const childItem: any = this.mainTransactionCategory[0].options.filter(el => (el.value === this.secondaryTransactionType));
          }
        }
      }
    }

    if (this.transactionType) {
      this._setParentTransactionCategories();
    }
  }
  /**
   * Validates the form on submit.
   *
   * @return     {Boolean}  A boolean indicating weather or not the form can be submitted.
   */
  public doValidateOption(): boolean {
    this.frmSubmitted = true;
    if (this.frmOption.valid) {
      this.secondaryTransactionTypeFailed = false;
      this.childOptionFailed = false;

      this.status.emit({
        form: this.frmOption,
        direction: 'next',
        step: 'step_3',
        previousStep: 'step_2'
      });

      return true;
    } else {
      return false;
    }
  }

  /**
   * Sets the secondary transaction type.
   *
   * @param      {Object} The event object.
   */
  public setSecondaryTransactionType(e): void {
    const secondaryTransactionType: string = e.target.getAttribute('data-value');

    if (secondaryTransactionType) {
      this.secondaryTransactionType = secondaryTransactionType;

      this.secondaryTransactionTypeFailed =  false;
      const childItem: any = this.mainTransactionCategory[0].options.filter(el => (el.value === secondaryTransactionType));

      if (childItem) {
        this.childOptions = childItem[0].options;
      }

      if (localStorage.getItem(`form_${this._formType}_transaction_type`) !== null) {
        let trasnsactionObj: any = JSON.parse(localStorage.getItem(`form_${this._formType}_transaction_type`));

        trasnsactionObj['secondaryTransactionType'] = secondaryTransactionType;

        localStorage.setItem(`form_${this._formType}_transaction_type`, JSON.stringify(trasnsactionObj));
      }
    }
  }

  /**
   * Sets the child transaction type.
   *
   * @param      {Object}  e       The event object.
   */
  public setChildTransactionType(e): void {
    const childTransactionType: string = e.target.getAttribute('data-value');

    if (childTransactionType) {
      this.childOptionFailed = false;
      if (localStorage.getItem(`form_${this._formType}_transaction_type`) !== null) {
        let trasnsactionObj: any = JSON.parse(localStorage.getItem(`form_${this._formType}_transaction_type`));

        trasnsactionObj['childTransactionType'] = childTransactionType;

        localStorage.setItem(`form_${this._formType}_transaction_type`, JSON.stringify(trasnsactionObj));
      }
    }
  }

  /**
   * Sets the parent transaction categories.
   */
  private _setParentTransactionCategories(): void {
    //console.log('_setParentTransactionCategories: ');

    this.mainTransactionCategory = this.transactionCategories.filter(el => (el.value === this.transactionType));

    //if (localStorage.getItem(`form_${this._formType}_transaction_type`) === null) {
      const parentTransactionTypeText: string = this.mainTransactionCategory[0].text;
      const parentTransactionTypeValue: string = this.mainTransactionCategory[0].value;
      const transactionObj: any = {
        parentTransactionTypeText,
        parentTransactionTypeValue
      };

      //console.log('inside here');

      localStorage.setItem(`form_${this._formType}_transaction_type`, JSON.stringify(transactionObj));

      this.transactionType = null;
    //}
    this.secondaryTransactionType = '';
    this.secondaryOptions = '';
    this.childOptionType = '';

    this.secondaryOptions = this.mainTransactionCategory[0].options;

    this.parentOptionFailed = false;
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
