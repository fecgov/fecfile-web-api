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

    // this._messageService
    //   .getMessage()
    //   .subscribe(res => {
    //     console.log('transaction-component res: ', res);
    //     if (res) {

    //       if (typeof res === 'object') {
    //         if (typeof res.form === 'string') {
    //           if (res.form === '3x') {

    //             // console.log('res: ', res);
    //             this._transactionCategory = res.transactionType;
    //             this._setTransactionCategories();
    //           }
    //         }
    //       }
    //     }
    //   });
  }

  ngDoCheck(): void {
    if (Array.isArray(this.selectedOptions)) {
      if (this.selectedOptions.length >= 1) {
        this.showForm = true;
      }
    }
    if (this.transactionType) {
      console.log('transactionType: ', this.transactionType);

      this._setTransactionCategories();
    }
  }
  /**
   * Validates the form on submit.
   *
   * @return     {Boolean}  A boolean indicating weather or not the form can be submitted.
   */
  public doValidateOption(): boolean {
    console.log('doValidateOptions: ');
    if (this.childOptions.length >= 1) {
      this.parentOptionFailed = false;
      console.log('this.parentOptionFailed: ', this.parentOptionFailed);
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
