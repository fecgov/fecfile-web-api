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
import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { FormBuilder, FormGroup, FormControl, NgForm, Validators } from '@angular/forms';
import { NgbTooltipConfig, NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../../environments/environment';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { UtilService } from '../../../shared/utils/util.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { IndividualReceiptService } from './individual-receipt.service';
import { f3xTransactionTypes } from '../../../shared/interfaces/FormsService/FormsService';
import { alphaNumeric } from '../../../shared/utils/forms/validation/alpha-numeric.validator';
import { floatingPoint } from '../../../shared/utils/forms/validation/floating-point.validator';
import { contributionDate } from '../../../shared/utils/forms/validation/contribution-date.validator';
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';
import { Observable } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';

@Component({
  selector: 'f3x-individual-receipt',
  templateUrl: './individual-receipt.component.html',
  styleUrls: ['./individual-receipt.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe],
  encapsulation: ViewEncapsulation.None
})
export class IndividualReceiptComponent implements OnInit {
  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() selectedOptions: any = {};
  @Input() formOptionsVisible: boolean = false;
  @Input() transactionTypeText = '';
  @Input() transactionType = '';

  public checkBoxVal: boolean = false;
  public frmIndividualReceipt: FormGroup;
  public formFields: any = [];
  public formVisible: boolean = false;
  public hiddenFields: any = [];
  public memoCode: boolean = false;
  public testForm: FormGroup;
  public titles: any = [];
  public states: any = [];

  private _formType: string = '';
  private _reportType: any = {};
  private _types: any = [];
  private _transaction: any = {};
  private _transactionType: string = null;
  private _formSubmitted: boolean = false;
  private readonly _contributionAggregateValue: number = 0.0;
  private readonly _memoCodeValue: string = 'X';
  private _selectedEntityId: number;

  constructor(
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _formService: FormsService,
    private _receiptService: IndividualReceiptService,
    private _activatedRoute: ActivatedRoute,
    private _config: NgbTooltipConfig,
    private _router: Router,
    private _utilService: UtilService,
    private _messageService: MessageService,
    private _currencyPipe: CurrencyPipe,
    private _decimalPipe: DecimalPipe,
    private _reportTypeService: ReportTypeService,
    private _typeaheadService: TypeaheadService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify({ saved: true }));
    localStorage.setItem('Receipts_Entry_Screen', 'Yes');

    this._messageService.clearMessage();

    this._reportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));

    if (this._reportType === null || typeof this._reportType === 'undefined') {
      this._reportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type_backup`));
    }

    this.frmIndividualReceipt = this._fb.group({});

    this._receiptService.getDynamicFormFields(this._formType, 'Individual Receipt').subscribe(res => {
      if (res) {
        if (res.hasOwnProperty('data')) {
          if (typeof res.data === 'object') {
            if (res.data.hasOwnProperty('formFields')) {
              if (Array.isArray(res.data.formFields)) {
                this.formFields = res.data.formFields;

                this._setForm(this.formFields);
              }
            }
            if (res.data.hasOwnProperty('hiddenFields')) {
              if (Array.isArray(res.data.hiddenFields)) {
                this.hiddenFields = res.data.hiddenFields;
              }
            }
            if (res.data.hasOwnProperty('states')) {
              if (Array.isArray(res.data.states)) {
                this.states = res.data.states;
              }
            }
            if (res.data.hasOwnProperty('titles')) {
              if (Array.isArray(res.data.titles)) {
                this.titles = res.data.titles;
              }
            }
          } // typeof res.data
        } // res.hasOwnProperty('data')
      } // res
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
    localStorage.removeItem('form_3X_saved');
  }

  public debug(obj: any): void {
    console.log('obj: ', obj);
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
    if (fieldName === 'zip_code') {
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

      if (this.memoCode) {
        this.frmIndividualReceipt.controls['contribution_date'].setValidators([Validators.required]);

        this.frmIndividualReceipt.controls['contribution_date'].updateValueAndValidity();
      } else {
        if (this.frmIndividualReceipt.controls['contribution_date']) {
          this.frmIndividualReceipt.controls['contribution_date'].setValidators([
            contributionDate(cvgStartDate, cvgEndDate),
            Validators.required
          ]);

          this.frmIndividualReceipt.controls['contribution_date'].updateValueAndValidity();
        }
      }
    }

    if (this.frmIndividualReceipt) {
      if (this.frmIndividualReceipt.controls['contribution_amount']) {
        this.frmIndividualReceipt.controls['contribution_amount'].setValidators([floatingPoint(), Validators.required]);

        this.frmIndividualReceipt.controls['contribution_amount'].updateValueAndValidity();
      }

      if (this.frmIndividualReceipt.controls['contribution_aggregate']) {
        this.frmIndividualReceipt.controls['contribution_aggregate'].setValidators([floatingPoint()]);

        this.frmIndividualReceipt.controls['contribution_aggregate'].updateValueAndValidity();
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
   * Updates vaprivate _memoCode variable.
   *
   * @param      {Object}  e      The event object.
   */
  public memoCodeChange(e): void {
    const { checked } = e.target;

    if (checked) {
      this.memoCode = checked;
    } else {
      this._validateContributionDate();
      this.memoCode = checked;
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
          if (field === 'memo_code') {
            if (this.memoCode) {
              receiptObj[field] = this.frmIndividualReceipt.get(field).value;
            }
          }
          if (field === 'last_name' || field === 'first_name') {
            // TODO Possible detfect with typeahead setting field as the entity object
            // rather than the string defined by the inputFormatter();
            // If an object is received, find the value on the object by fields type
            // otherwise use the string value.  This is not desired and this patch
            // should be removed if the issue is resolved.
            const typeAheadField = this.frmIndividualReceipt.get(field).value;
            if (typeof typeAheadField !== 'string') {
              receiptObj[field] = typeAheadField[field];
            } else {
              receiptObj[field] = typeAheadField;
            }
          } else {
            receiptObj[field] = this.frmIndividualReceipt.get(field).value;
          }
        }
      }

      this.hiddenFields.forEach(el => {
        receiptObj[el.name] = el.value;
      });

      // If entity ID exist, the transaction will be added to the existing entity by the API
      // Otherwise it will create a new Entity.
      if (this._selectedEntityId) {
        receiptObj.entity_id = this._selectedEntityId;
      }

      localStorage.setItem(`form_${this._formType}_receipt`, JSON.stringify(receiptObj));

      this._receiptService.saveSchedule(this._formType).subscribe(res => {
        if (res) {
          if (res.hasOwnProperty('memo_code')) {
            if (typeof res.memo_code === 'object') {
              if (res.memo_code === null) {
                this._receiptService.getSchedule(this._formType, res).subscribe(resp => {
                  const message: any = {
                    formType: this._formType,
                    totals: resp
                  };

                  this._messageService.sendMessage(message);
                });
              }
            }
          }

          const contributionAggregateValue: string = this._decimalPipe.transform(
            this._contributionAggregateValue,
            '.2-2'
          );

          this._formSubmitted = true;
          this.memoCode = false;
          this.frmIndividualReceipt.reset();
          this.frmIndividualReceipt.controls['contribution_aggregate'].setValue(contributionAggregateValue);
          this.frmIndividualReceipt.controls['memo_code'].setValue(this._memoCodeValue);
          this._selectedEntityId = null;

          localStorage.removeItem(`form_${this._formType}_receipt`);
          localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify({ saved: true }));
          window.scrollTo(0, 0);
        }
      });
    } else {
      this.frmIndividualReceipt.markAsDirty();
      this.frmIndividualReceipt.markAsTouched();
      localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify({ saved: false }));
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
    let reportId = this.getReportIdFromStorage();
    console.log('reportId', reportId);

    if (!reportId) {
      reportId = '0';
      // reportId = '431';
      // reportId = '1206963';
    }
    console.log(`View Transactions for form ${this._formType} where reportId = ${reportId}`);
    localStorage.setItem(`form_${this._formType}_view_transaction_screen`, 'Yes');
    localStorage.setItem('Transaction_Table_Screen', 'Yes');

    this._router.navigate([`/forms/transactions/${this._formType}/${reportId}`]);
  }

  public printPreview(): void {
    this._reportTypeService.signandSaveSubmitReport('3X', 'Saved');
    this._reportTypeService.printPreviewPdf('3X', 'PrintPreviewPDF').subscribe(
      res => {
        if (res) {
          console.log('Accessing FinancialSummaryComponent printPriview res ...', res);

          if (res['results.pdf_url'] !== null) {
            console.log("res['results.pdf_url'] = ", res['results.pdf_url']);
            window.open(res.results.pdf_url, '_blank');
          }
        }
      },
      error => {
        console.log('error: ', error);
      }
    ); /*  */
  }

  /**
   * @deprecated
   */
  public receiveTypeaheadData(contact: any, fieldName: string): void {
    console.log('entity selected by typeahead is ' + contact);

    if (fieldName === 'first_name') {
      this.frmIndividualReceipt.patchValue({ last_name: contact.last_name }, { onlySelf: true });
      this.frmIndividualReceipt.controls['last_name'].setValue({ last_name: contact.last_name }, { onlySelf: true });
    }

    if (fieldName === 'last_name') {
      this.frmIndividualReceipt.patchValue({ first_name: contact.first_name }, { onlySelf: true });
      this.frmIndividualReceipt.controls['first_name'].setValue({ first_name: contact.first_name }, { onlySelf: true });
    }

    this.frmIndividualReceipt.patchValue({ middle_name: contact.middle_name }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ prefix: contact.prefix }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ suffix: contact.suffix }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ street_1: contact.street_1 }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ street_2: contact.street_2 }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ city: contact.city }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ state: contact.state }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ zip_code: contact.zip_code }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ occupation: contact.occupation }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ employer: contact.employer }, { onlySelf: true });
  }

  /**
   * Format an entity to display in the type ahead.
   *
   * @param result formatted item in the typeahead list
   */
  public formatTypeaheadItem(result: any) {
    return `${result.last_name}, ${result.first_name}, ${result.street_1}, ${result.street_2}`;
  }

  /**
   * Populate the fields in the form with the values from the selected contact.
   *
   * @param $event The mouse event having selected the contact from the typeahead options.
   */
  public handleSelectedItem($event: NgbTypeaheadSelectItemEvent) {
    const contact = $event.item;

    this._selectedEntityId = contact.entity_id;
    this.frmIndividualReceipt.patchValue({ last_name: contact.last_name }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ first_name: contact.first_name }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ middle_name: contact.middle_name }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ prefix: contact.prefix }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ suffix: contact.suffix }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ street_1: contact.street_1 }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ street_2: contact.street_2 }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ city: contact.city }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ state: contact.state }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ zip_code: contact.zip_code }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ occupation: contact.occupation }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ employer: contact.employer }, { onlySelf: true });

    let transactionTypeIdentifier = '';
    // Use this if transaction_tye_identifier is to come from dynamic form data
    // currently it's called to early to detect type changes as it happens in step 1 / report type
    // for (const field of this.hiddenFields) {
    //   if (field.name === 'transaction_type_identifier') {
    //     transactionTypeIdentifier = field.value;
    //   }
    // }

    // default to indiv-receipt for sprint 17 - use input field in sprint 18.
    transactionTypeIdentifier = 'INDV_REC';
    console.log('transaction type from input is ' + this.transactionType);

    const reportId = this.getReportIdFromStorage();
    this._receiptService
      .getContributionAggregate(reportId, contact.entity_id, transactionTypeIdentifier)
      .subscribe(res => {
        this.frmIndividualReceipt.patchValue(
          { contribution_aggregate: res.contribution_aggregate },
          { onlySelf: true }
        );
      });
  }

  /**
   * Search for entities/contacts when last name input value changes.
   */
  searchLastName = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'last_name');
        } else {
          return Observable.of([]);
        }
      })
    );

  /**
   * Search for entities/contacts when first name input value changes.
   */
  searchFirstName = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'first_name');
        } else {
          return Observable.of([]);
        }
      })
    );

  /**
   * format the value to display in the input field once selected from the typeahead.
   *
   * For some reason this gets called for all typeahead fields despite the binding in the
   * template to the last name field.  In these cases return x to retain the value in the
   * input for the other typeahead fields.
   */
  formatterLastName = (x: { last_name: string }) => {
    if (typeof x !== 'string') {
      return x.last_name;
    } else {
      return x;
    }
  };

  /**
   * format the value to display in the input field once selected from the typeahead.
   *
   * For some reason this gets called for all typeahead fields despite the binding in the
   * template to the first name field.  In these cases return x to retain the value in the
   * input for the other typeahead fields.
   */
  formatterFirstName = (x: { first_name: string }) => {
    if (typeof x !== 'string') {
      return x.first_name;
    } else {
      return x;
    }
  };

  /**
   * Obtain the Report ID from local storage.
   */
  private getReportIdFromStorage() {
    let reportId = '0';
    let form3XReportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));

    if (form3XReportType === null || typeof form3XReportType === 'undefined') {
      form3XReportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type_backup`));
    }

    console.log('viewTransactions form3XReportType', form3XReportType);

    if (typeof form3XReportType === 'object' && form3XReportType !== null) {
      if (form3XReportType.hasOwnProperty('reportId')) {
        reportId = form3XReportType.reportId;
      } else if (form3XReportType.hasOwnProperty('reportid')) {
        reportId = form3XReportType.reportid;
      }
    }
    return reportId;
  }

  // Use this if the fields populated by the type-ahead should be disabled.
  // public isReadOnly(name: string, type: string) {
  //   if (name === 'contribution_aggregate' && type === 'text') {
  //     return true;
  //   }
  //   if (name === 'first_name' || name === 'last_name' || name === 'prefix') {
  //     if (this._selectedEntityId) {
  //       console.log('this._selectedEntityId = ' + this._selectedEntityId);
  //       return true;
  //     }
  //   }
  //   return null;
  // }
}
