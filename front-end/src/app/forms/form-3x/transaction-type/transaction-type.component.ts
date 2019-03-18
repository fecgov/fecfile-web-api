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

  public frmOption: FormGroup;
  public frmSubmitted: boolean = false;
  public optionFailed: boolean = false;
  public parentOptionFailed: boolean = false;
  public showForm: boolean = false;
  public searchField: any = {};
  public childOptions: any = [];
  public mainTransactionCategory: any = [];

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
      optionRadio: ['', Validators.required]
    });
  }

  ngDoCheck(): void {
    if (Array.isArray(this.selectedOptions)) {
      if (this.selectedOptions.length >= 1) {
        this.showForm = true;
      }
    }
    if (this.transactionType) {
      this._setTransactionCategories();
    }
  }
  /**
   * Validates the form on submit.
   *
   * @return     {Boolean}  A boolean indicating weather or not the form can be submitted.
   */
  public doValidateOption(): boolean {
    console.log('doValidateOption: ');
    console.log('this.frmOption: ', this.frmOption);
    this.frmSubmitted = true;
    console.log('this.frmSubmitted: ', this.frmSubmitted);
    if (this.childOptions.length >= 1) {
      this.parentOptionFailed = false;
      if (this.frmOption.invalid) {
        this.optionFailed = true;
        return false;
      } else {
        this.optionFailed = false;
        return true;
      }
    } else {
      this.parentOptionFailed = true;
    }
  }

  /**
   * Updates the status of any form erros when a radio button is clicked.
   *
   * @param      {Object}  e       The event object.
   */
  public updateStatus(e): void {
    if (e.target.checked) {
      this.optionFailed = false;
    } else {
      this.optionFailed = true;
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

  private _setTransactionCategories(): void {
    this.mainTransactionCategory = this.transactionCategories.filter(el => (el.value === this.transactionType));

    this.childOptions = this.mainTransactionCategory[0].options;

    this.parentOptionFailed = false;
    this.optionFailed = false;
  }
}
