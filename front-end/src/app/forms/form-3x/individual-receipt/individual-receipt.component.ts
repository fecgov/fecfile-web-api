import {
  Component,
  EventEmitter,
  ElementRef,
  Input,
  OnInit,
  Output,
  OnChanges,
  Renderer,
  SimpleChanges,
  ViewEncapsulation,
  ViewChild
} from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { FormBuilder, FormGroup, FormControl, NgForm, Validators } from '@angular/forms';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../../environments/environment';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { UtilService } from '../../../shared/utils/util.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { IndividualReceiptService } from './individual-receipt.service';
import { f3xTransactionTypes } from '../../../shared/interfaces/FormsService/FormsService';
import { alphaNumeric } from '../../../shared/utils/forms/validation/alpha-numeric.validator';
import { floatingPoint } from '../../../shared/utils/forms/validation/floating-point.validator';
import { contributionDate } from '../../../shared/utils/forms/validation/contribution-date.validator';

@Component({
  selector: 'f3x-individual-receipt',
  templateUrl: './individual-receipt.component.html',
  styleUrls: ['./individual-receipt.component.scss'],
  providers: [NgbTooltipConfig],
  encapsulation: ViewEncapsulation.None
})
export class IndividualReceiptComponent implements OnInit {
  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() selectedOptions: any = {};
  @Input() formOptionsVisible: boolean = false;
  @Input() transactionTypeText = '';

  public formFields: any = [];
  public frmIndividualReceipt: FormGroup;
  public hiddenFields: any = [];
  public testForm: FormGroup;
  public formVisible: boolean = false;
  public states: any = [];

  private _formType: string = '';
  private _reportType: any = {};
  private _types: any = [];
  private _transaction: any = {};
  private _transactionType: string = null;

  constructor(
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _formService: FormsService,
    private _receiptService: IndividualReceiptService,
    private _activatedRoute: ActivatedRoute,
    private _config: NgbTooltipConfig,
    private _router: Router,
    private _utilService: UtilService,
    private _messageService: MessageService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this._messageService.clearMessage();

    this._reportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));

    this.frmIndividualReceipt = this._fb.group({});

    this._receiptService.getDynamicFormFields(this._formType, 'Individual Receipt').subscribe(res => {
      if (res) {
        // this.formFields = res.data.formFields;
        // this.hiddenFields = res.data.hiddenFields;
        // this.states = res.data.states;

        this.formFields = res.formFields;
        this.hiddenFields = res.hiddenFields;
        this.states = res.states;

        if (this.formFields.length >= 1) {
          this._setForm(this.formFields);
        }
      }
    });
  }

  ngDoCheck(): void {
    if (this.selectedOptions) {
      if (this.selectedOptions.length >= 1) {
        this.formVisible = true;
      }
    }

    this._validateContributionDate();

    this._getTransactionType();
  }

  ngOnDestroy(): void {
    this._messageService.clearMessage();
  }

  /**
   * Generates the dynamic form after all the form fields are retrived.
   *
   * @param      {Array}  fields  The fields
   */
  private _setForm(fields: any): void {
    const formGroup: any = [];

    fields.forEach(el => {
      if (el.hasOwnProperty('cols')) {
        el.cols.forEach(e => {
          formGroup[e.name] = new FormControl(e.value || null, this._mapValidators(e.validation, e.name));
        });
      }
    });

    this.frmIndividualReceipt = new FormGroup(formGroup);
  }

  /**
   * Sets the form field valition requirements.
   *
   * @param      {Object} validators  The validators.
   * @param      {String} fieldName The name of the field.
   * @return     {Array}  The validations in an Array.
   */
  private _mapValidators(validators: any, fieldName: string): Array<any> {
    const formValidators = [];

    /**
     * Adds alphanumeric validation for the zip code field.
     */
    if (fieldName === 'ContributorZip') {
      formValidators.push(alphaNumeric());
    }

    if (validators) {
      for (const validation of Object.keys(validators)) {
        if (validation === 'required') {
          if (validators[validation]) {
            formValidators.push(Validators.required);
          }
        } else if (validation === 'min') {
          if (validators[validation] !== null) {
            formValidators.push(Validators.minLength(validators[validation]));
          }
        } else if (validation === 'max') {
          if (validators[validation] !== null) {
            formValidators.push(Validators.maxLength(validators[validation]));
          }
        } else if (validation === 'dollarAmount') {
          if (validators[validation] !== null) {
            formValidators.push(floatingPoint());
          }
        }
      }
    }

    return formValidators;
  }

  /**
   * Validates the contribution date selected.
   */
  private _validateContributionDate(): void {
    this._reportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));

    if (this._reportType !== null) {
      const cvgStartDate: string = this._reportType.cvgStartDate;
      const cvgEndDate: string = this._reportType.cvgEndDate;

      if (this.frmIndividualReceipt.controls['contribution_date']) {
        this.frmIndividualReceipt.controls['contribution_date'].setValidators([
          contributionDate(cvgStartDate, cvgEndDate),
          Validators.required
        ]);

        this.frmIndividualReceipt.controls['contribution_date'].updateValueAndValidity();
      }
    }
  }

  /**
   * Gets the transaction type.
   */
  private _getTransactionType(): void {
    const transactionType: any = JSON.parse(localStorage.getItem(`form_${this._formType}_transaction_type`));

    if (typeof transactionType === 'object') {
      if (transactionType !== null) {
        if (transactionType.hasOwnProperty('mainTransactionTypeValue')) {
          this._transactionType = transactionType.mainTransactionTypeValue;
        }
      }
    }
  }

  /**
   * Vaidates the form on submit.
   */
  public doValidateReceipt() {
    if (this.frmIndividualReceipt.valid) {
      const receiptObj: any = {};

      for (const field in this.frmIndividualReceipt.controls) {
        if (field === 'contribution_date') {
          receiptObj[field] = this._utilService.formatDate(this.frmIndividualReceipt.get(field).value);
        } else {
          receiptObj[field] = this.frmIndividualReceipt.get(field).value;
        }
      }

      this.hiddenFields.forEach(el => {
        receiptObj[el.name] = el.value;
      });

      localStorage.setItem(`form_${this._formType}_receipt`, JSON.stringify(receiptObj));

      this._receiptService.saveSchedule(this._formType).subscribe(res => {
        if (res) {
          console.log('res: ', res);
          this._receiptService.getSchedule(this._formType, res).subscribe(resp => {
            const message: any = {
              formType: this._formType,
              totals: resp
            };

            this._messageService.sendMessage(message);
          });

          this._receiptService
            .aggregateAmount(
              res.report_id,
              res.transaction_type,
              res.contribution_date,
              res.entity_id,
              res.contribution_amount
            )
            .subscribe(resp => {
              console.log('resp: ', resp);
            });

          this.frmIndividualReceipt.reset();

          localStorage.removeItem(`form_${this._formType}_receipt`);

          window.scrollTo(0, 0);
        }
      });
    } else {
      this.frmIndividualReceipt.markAsDirty();
      this.frmIndividualReceipt.markAsTouched();
      window.scrollTo(0, 0);
    }
  }

  /**
   * Goes to the previous step.
   */
  public previousStep(): void {
    this.status.emit({
      form: {},
      direction: 'previous',
      step: 'step_2'
    });
  }

  /**
   * Navigate to the Transactions.
   */
  public viewTransactions(): void {
    let reportId = '0';
    const form3XReportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));
    console.log('viewTransactions form3XReportType', form3XReportType);

    if (typeof form3XReportType === 'object' && form3XReportType !== null) {
      if (form3XReportType.hasOwnProperty('reportId')) {
        reportId = form3XReportType.reportId;
      } else if (form3XReportType.hasOwnProperty('reportid')) {
        reportId = form3XReportType.reportid;
      }
    }

    console.log('reportId', reportId);

    if (!reportId) {
      reportId = '0';
      // reportId = '431';
      // reportId = '1206963';
    }
    console.log(`View Transactions for form ${this._formType} where reportId = ${reportId}`);

    this._router.navigate([`/forms/transactions/${this._formType}/${reportId}`]);
  }
}
