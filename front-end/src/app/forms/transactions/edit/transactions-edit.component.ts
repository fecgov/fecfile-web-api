import {
  Component,
  EventEmitter,
  ElementRef,
  Input,
  OnInit,
  Output,
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
import { IndividualReceiptService } from '../../form-3x/individual-receipt/individual-receipt.service';
import { f3xTransactionTypes, form3xReportTypeDetails } from '../../../shared/interfaces/FormsService/FormsService';
import { alphaNumeric } from '../../../shared/utils/forms/validation/alpha-numeric.validator';
import { floatingPoint } from '../../../shared/utils/forms/validation/floating-point.validator';
import { TransactionModel } from '../model/transaction.model';
import { TransactionsMessageService } from '../service/transactions-message.service';
import { ReportsService } from 'src/app/reports/service/report.service';

@Component({
  selector: 'app-transactions-edit',
  templateUrl: './transactions-edit.component.html',
  styleUrls: ['./transactions-edit.component.scss'],
  providers: [NgbTooltipConfig],
  encapsulation: ViewEncapsulation.None
})
export class TransactionsEditComponent implements OnInit {
  // @Output() status: EventEmitter<any> = new EventEmitter<any>();
  // @Input() selectedOptions: any = {};
  // @Input() formOptionsVisible: boolean = false;
  // @Input() transactionTypeText = '';
  // @ViewChild('hiddenFields') hiddenFieldValues: ElementRef;

  @Input()
  public transactionToEdit: TransactionModel;

  @Input()
  public formType: string;

  @Input()
  public reportId: string;

  public formFields: any = [];
  public frmIndividualReceipt: FormGroup;
  public hiddenFields: any = [];
  public testForm: FormGroup;
  public formVisible: boolean = false;
  public states: any = [];

  private _types: any = [];
  private _transaction: any = {};

  constructor(
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _reportsService: ReportsService,
    private _individualReceiptService: IndividualReceiptService,
    private _config: NgbTooltipConfig,
    private _utilService: UtilService,
    private _transactionsMessageService: TransactionsMessageService,
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {

    console.log(this.transactionToEdit);


    this.frmIndividualReceipt = this._fb.group({});

    // const formVal = {value: [ContributorLastName : 'Jones']};
    // this.frmIndividualReceipt.setValue(formVal);


    this._individualReceiptService.getDynamicFormFields(this.formType, 'Individual Receipt').subscribe(res => {
      if (res) {

        this._mapTransactionFieldToForm(res);

        this.formFields = res.data.formFields;
        this.hiddenFields = res.data.hiddenFields;

        console.log(this.formFields); // this.formFields.value

        this._setForm(this.formFields);

        this.states = res.data.states;

        // this.frmIndividualReceipt.setValue({ContributorLastName: 'Jones'});
      }
    });
  }

  /**
   * The transactionModel has current values from the API.  Here they values will
   * be added to the form fields in order to display and allow for editing in the form.
   * 
   * @param res the form field response from the API.
   */
  private _mapTransactionFieldToForm(res: any) {
    const nameArray = this.transactionToEdit.name.split(',');

    // fields names must be mapped from transaction field names to formField names.
    res.data.formFields.forEach(el => {
      if (el.hasOwnProperty('cols')) {
        el.cols.forEach(e => {
          const fieldName = e.name;
          switch (fieldName) {
            case 'ContributorFirstName':
              e.value = nameArray[1] ? nameArray[1] : null;
              break;
            case 'ContributorLastName':
              e.value = nameArray[0] ? nameArray[0] : null;
              break;
            case 'ContributorMiddleName':
              e.value = nameArray[2] ? nameArray[2] : null;
              break;
            case 'ContributorPrefix':
              e.value = nameArray[3] ? nameArray[3] : null;
              break;
            case 'ContributorSuffix':
              e.value = nameArray[4] ? nameArray[4] : null;
              break;
              // TODO need API to return individual name fields
            case 'ContributorStreet1':
              e.value = this.transactionToEdit.street;
              break;
            case 'ContributorStreet2':
              e.value = this.transactionToEdit.street2;
              // TODO need API to provide street line 2
              break;
            case 'ContributorCity':
              e.value = this.transactionToEdit.city;
              break;
            case 'ContributorState':
              e.value = this.transactionToEdit.state;
              break;
            case 'ContributorZip':
              e.value = this.transactionToEdit.zip;
              break;
            case 'ContributionDate':
              e.value = this.transactionToEdit.date;
              break;
            case 'ContributionAmount':
              e.value = this.transactionToEdit.amount;
              break;
            case 'ContributionAggregate':
              e.value = this.transactionToEdit.aggregate;
              break;
            case 'ContributorEmployer':
              e.value = this.transactionToEdit.contributorEmployer;
              break;
            case 'ContributorOccupation':
              e.value = this.transactionToEdit.contributorOccupation;
              break;
            case 'MemoCode':
              e.value = this.transactionToEdit.memoCode;
              break;
            case 'MemoText':
              e.value = this.transactionToEdit.memoText;
              break;
            case 'ContributionPurposeDescription':
              e.value = this.transactionToEdit.purposeDescription;
              break;
            default:
              break;
          }
        });
      }
    });
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
          formGroup[e.name] = new FormControl(e.value || null, this._mapValidators(e.validation));
        });
      }
    });

    this.frmIndividualReceipt = new FormGroup(formGroup);
  }

  /**
   * Sets the form field valition requirements.
   *
   * @param      {Object}  validators  The validators
   * @return     {Array}  The validations in an Array.
   */
  private _mapValidators(validators): Array<any> {
    const formValidators = [];

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
        } else if (validation === 'alphaNumeric') {
          formValidators.push(alphaNumeric());
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
   * Vaidates the form on submit.
   */
  public doValidateReceipt() {
    if (this.frmIndividualReceipt.valid) {
      let receiptObj: any = {};

      for (const field in this.frmIndividualReceipt.controls) {
        if (field === 'ContributionDate') {
          receiptObj[field] = this._utilService.formatDate(this.frmIndividualReceipt.get(field).value);
        } else {
          receiptObj[field] = this.frmIndividualReceipt.get(field).value;
        }
      }

      this.hiddenFields.forEach(el => {
        receiptObj[el.name] = el.value;
      });

      localStorage.setItem(`form_${this.formType}_receipt`, JSON.stringify(receiptObj));

      this._reportsService.getReportInfo(`F${this.formType}`, this.reportId)
        .subscribe((res: form3xReportTypeDetails) => {
          localStorage.setItem(`form_3X_report_type`, JSON.stringify(res[0]));

          this._individualReceiptService.saveScheduleA(this.formType).subscribe(res => {
            if (res) {
              this.frmIndividualReceipt.reset();

              localStorage.removeItem(`form_${this.formType}_receipt`);

              window.scrollTo(0, 0);
            }
          });

        });
    } else {
      this.frmIndividualReceipt.markAsDirty();
      this.frmIndividualReceipt.markAsTouched();
      window.scrollTo(0, 0);
    }
  }

  // /**
  //  * Goes to the previous step.
  //  */
  // public previousStep(): void {
  //   this.status.emit({
  //     form: {},
  //     direction: 'previous',
  //     step: 'step_2'
  //   });
  // }

  /**
   * Navigate to the Transactions.
   */
  public viewTransactions(): void {

    this._transactionsMessageService.sendShowTransactionsMessage('');

    // let reportId = '0';
    // const form3XReportType = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));

    // if (typeof form3XReportType === 'object' && form3XReportType !== null) {
    //   if (form3XReportType.hasOwnProperty('reportId')) {
    //     reportId = form3XReportType.reportId;
    //   }
    // }

    // if (!reportId) {
    //   reportId = '0';
    // }
    // console.log(`View Transactions for form ${this.formType} where reportId = ${reportId}`);

    // this._router.navigate([`/forms/transactions/${this.formType}/${reportId}`]);
  }
}
