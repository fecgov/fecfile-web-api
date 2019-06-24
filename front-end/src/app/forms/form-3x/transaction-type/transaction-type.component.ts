import { Component, EventEmitter, Input, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { NgbPanelChangeEvent } from '@ng-bootstrap/ng-bootstrap';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { form3x_data } from '../../../shared/interfaces/FormsService/FormsService';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { TransactionTypeService } from './transaction-type.service';
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';

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
  @Input() transactionCategory: string = null;
  @Input() formOptionsVisible: boolean = false;
  @Input() transactionCategories: any = [];

  public frmOption: FormGroup;
  public frmSubmitted: boolean = false;
  public showForm: boolean = false;
  public searchField: any = {};
  public secondaryOptions: any = [];
  public transactionType: string = null;
  public transactionTypeText: string = null;
  public transactionTypeFailed : boolean = false;
  public transactionCategorySelected: boolean = false;
  public tranasctionCategoryVal: string = '';

  private _formType: string = '';
  private _mainTransactionCategory: any = [];
  private _transactionCategory: string = '';
  private _transactionCategories: any = [];

  constructor(
    private _fb: FormBuilder,
    private _config: NgbTooltipConfig,
    private _activatedRoute: ActivatedRoute,
    private _formService: FormsService,
    private _messageService: MessageService,
    private _transactionTypeService: TransactionTypeService,
    private _reportTypeService: ReportTypeService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this.frmOption = this._fb.group({
      secondaryOption: ['', Validators.required]
    });
  }

  ngDoCheck(): void {
    if (this.transactionCategory) {
      this.transactionCategorySelected = false;
    }

    if (this.transactionType) {
      this.transactionTypeFailed = false;
    }

    if (this.transactionCategory && localStorage.getItem(`form_${this._formType}_temp_transaction_type`) === null) {
      this._setSecondaryTransactionCategories();
    } else if (this.transactionCategory && localStorage.getItem(`form_${this._formType}_temp_transaction_type`) !== null) {
      const transactionObj: any = JSON.parse(localStorage.getItem(`form_${this._formType}_temp_transaction_type`));

      if (transactionObj.mainTransactionTypeText !== this.transactionCategory) {
        this._setSecondaryTransactionCategories();
      }
    }
  }

  /**
   * Validates the form on submit.
   */
  public doValidateOption() {
    this.frmSubmitted = true;

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
        previousStep: 'step_2',
        transactionTypeText: this.transactionTypeText
      });
      return 1;
    } else {

      if (!this.tranasctionCategoryVal) {
        this.transactionCategorySelected = false;
      } else {
        this.transactionCategorySelected = true;
      }

      if (!this.transactionType && this.tranasctionCategoryVal) {
        this.transactionTypeFailed = true;
      } else {
        this.transactionTypeFailed = false;
      }

      window.scrollTo(0, 0);

      return 0;
    }
  }

  /**
   * Resets transaction type selected on panel close.
   *
   * @param      {Boolean}  opened  The opened
   */
  public pannelChange(opened: boolean): void {
    if (opened) { // panel is closed
      this.transactionType = '';
      this.transactionTypeText = '';
      this.frmOption.controls['secondaryOption'].setValue('');
      this.transactionCategorySelected = true;
      this.transactionTypeFailed = true;      
    }
  }

  /**
   * Updates the type selected when radio button clicked.
   *
   * @param      {Object}  e            The event object.
   * @param      {Object}  childOption  The child option selected
   *                                    from the selectedOptions.
   */
  public updateTypeSelected(e, childOption): void {
    const val: string = e.target.value;

    this.transactionType = val;
    this.transactionTypeText = childOption.text;

    this.frmOption.controls['secondaryOption'].setValue(val);

    this.transactionTypeFailed = false;
  }


  /**
   * Sets the secondary transaction categories.
   */
  private _setSecondaryTransactionCategories(): void {
    this._mainTransactionCategory = this.transactionCategories.filter(el => (el.value === this.transactionCategory));
    const mainTransactionTypeText: string = this._mainTransactionCategory[0].text;
    const mainTransactionTypeValue: string = this._mainTransactionCategory[0].value;
    const transactionObj: any = {
      mainTransactionTypeText,
      mainTransactionTypeValue,
      'transactionType': '',
      'childTransactionType': ''
    };

    localStorage.setItem(`form_${this._formType}_temp_transaction_type`, JSON.stringify(transactionObj));

    this.secondaryOptions = this._mainTransactionCategory[0].options;

    this.transactionCategorySelected = true;

    this.transactionTypeFailed = false;

    if (this.transactionCategory) {
      this.tranasctionCategoryVal = this.transactionCategory;

      this.transactionCategory = '';
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
  public printPreview(): void {
    console.log("Calling F3X printPreview ...");
    this._reportTypeService
    .printPreviewPdf('3X','PrintPreviewPDF')
    .subscribe(res => {
      if(res) {
            console.log("Accessing SignComponent printPriview res ...",res);
            if (res.printpriview_fileurl !== null) {
              window.open(res.printpriview_fileurl, '_blank');
            }
          }
        },
        (error) => {
          console.log('error: ', error);
        });
      }
}
