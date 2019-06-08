import {
  Component,
  Input,
  OnInit,
  DoCheck,
  ViewEncapsulation} from '@angular/core';
import { FormBuilder, FormGroup, FormControl, Validators } from '@angular/forms';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { UtilService } from '../../../shared/utils/util.service';
import { IndividualReceiptService } from '../../form-3x/individual-receipt/individual-receipt.service';
import { form3xReportTypeDetails } from '../../../shared/interfaces/FormsService/FormsService';
import { alphaNumeric } from '../../../shared/utils/forms/validation/alpha-numeric.validator';
import { floatingPoint } from '../../../shared/utils/forms/validation/floating-point.validator';
import { TransactionModel } from '../model/transaction.model';
import { TransactionsMessageService } from '../service/transactions-message.service';
import { ReportsService } from 'src/app/reports/service/report.service';
import { contributionDate } from 'src/app/shared/utils/forms/validation/contribution-date.validator';

/**
 * A component for editing Transactions.  It is similar to the
 * IndividualRecepeiptComponent used for adding Transactions.
 */
@Component({
  selector: 'app-transactions-edit',
  templateUrl: './transactions-edit.component.html',
  styleUrls: ['./transactions-edit.component.scss'],
  providers: [NgbTooltipConfig],
  encapsulation: ViewEncapsulation.None
})
export class TransactionsEditComponent implements OnInit, DoCheck {

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
  public formVisible = false;
  public states: any = [];

  private _reportType: any = {};

  constructor(
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
    this.getFormFields();
  }

  ngDoCheck(): void {

    this._reportType = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
    if (this._reportType !== null) {

      // const cvgStartDate: string = this._reportType.cvgStartDate;
      // const cvgEndDate: string = this._reportType.cvgEndDate;

      // TODO why are these properties all lower case?
      // Because the report_type in localStorage does not have the
      // same object structure/property names as found in IndividualReceiptComponent.
      // TODO get these objects in sync. The date formats are different as well as
      // all lower case names.

      const cvgStartDate: string = this._reportType.cvgstartdate;
      const cvgEndDate: string = this._reportType.cvgenddate;

      const cvgStartDateDate: any = new Date(`${cvgStartDate}T01:00:00`);
      const startFormattedDate: string = `${(cvgStartDateDate.getMonth() + 1).toString().padStart(2, '0')}/${cvgStartDateDate
        .getDate()
        .toString()
        .padStart(2, '0')}/${cvgStartDateDate.getFullYear()}`;


      const cvgEndDateDate: any = new Date(`${cvgEndDate}T01:00:00`);
      const endFormattedDate: string = `${(cvgEndDateDate.getMonth() + 1).toString().padStart(2, '0')}/${cvgEndDateDate
        .getDate()
        .toString()
        .padStart(2, '0')}/${cvgEndDateDate.getFullYear()}`;

      if (this.frmIndividualReceipt.controls['ContributionDate']) {
        this.frmIndividualReceipt.controls['ContributionDate'].setValidators([
          contributionDate(startFormattedDate, endFormattedDate),
          Validators.required
        ]);

        this.frmIndividualReceipt.controls['ContributionDate'].updateValueAndValidity();
      }
    }
  }

  /**
   * Get the form field details from the server.
   */
  private getFormFields(): void {
    console.log(this.transactionToEdit);

    this.frmIndividualReceipt = this._fb.group({});

    // TODO check if same call is needed in validate.
    this._reportsService.getReportInfo(`F${this.formType}`, this.reportId)
      .subscribe((res: form3xReportTypeDetails) => {
        localStorage.setItem(`form_${this.formType}_report_type`, JSON.stringify(res[0]));
      });

    this._individualReceiptService.getDynamicFormFields(this.formType, 'Individual Receipt').subscribe(res => {
      if (res) {

        this._mapTransactionFieldToForm(res);

        this.formFields = res.data.formFields;
        this.hiddenFields = res.data.hiddenFields;

        console.log(this.formFields); // this.formFields.value

        this._setForm(this.formFields);

        this.states = res.data.states;


        // this._reportsService.getReportInfo(`F${this.formType}`, this.reportId)
        //   .subscribe((res: form3xReportTypeDetails) => {
        //     localStorage.setItem(`form_${this.formType}_report_type`, JSON.stringify(res[0]));

        //   this._reportType = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
        //   if (this._reportType !== null) {
        //     const cvgStartDate: string = this._reportType.cvgStartDate;
        //     const cvgEndDate: string = this._reportType.cvgEndDate;

        //     if (this.frmIndividualReceipt.controls['ContributionDate']) {
        //       this.frmIndividualReceipt.controls['ContributionDate'].setValidators([
        //         contributionDate(cvgStartDate, cvgEndDate),
        //         Validators.required
        //       ]);

        //       this.frmIndividualReceipt.controls['ContributionDate'].updateValueAndValidity();
        //     }
        //   }
        // });
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
      const receiptObj: any = {};

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

      receiptObj.transactionId = this.transactionToEdit.transactionId;

      localStorage.setItem(`form_${this.formType}_receipt`, JSON.stringify(receiptObj));

      this._reportsService.getReportInfo(`F${this.formType}`, this.reportId)
        .subscribe((res: form3xReportTypeDetails) => {
          localStorage.setItem(`form_${this.formType}_report_type`, JSON.stringify(res[0]));

          // TODO API call to save Transaction will need to vary depending on Transaction Type.
          // Only supporting Sched A at this time.

          this._individualReceiptService.putScheduleA(this.formType).subscribe(res2 => {
            if (res2) {
              this.frmIndividualReceipt.reset();

              localStorage.removeItem(`form_${this.formType}_receipt`);

              this.viewTransactions();
            }
          });

        });
    } else {
      this.frmIndividualReceipt.markAsDirty();
      this.frmIndividualReceipt.markAsTouched();
      window.scrollTo(0, 0);
    }
  }

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
