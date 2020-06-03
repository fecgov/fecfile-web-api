import { ReportTypeService } from './../form-3x/report-type/report-type.service';
import { LoanService } from './../sched-c/service/loan.service';
import { Component, OnInit, Input, Output, EventEmitter, SimpleChanges, OnChanges, ViewEncapsulation , ChangeDetectionStrategy } from '@angular/core';
import { FormGroup, FormBuilder, FormControl, Validators } from '@angular/forms';
import { ScheduleActions } from '../form-3x/individual-receipt/schedule-actions.enum';
import { ContactsService } from 'src/app/contacts/service/contacts.service';
import { alphaNumeric } from 'src/app/shared/utils/forms/validation/alpha-numeric.validator';
import { Observable } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';
import { NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
import { SchedC1Service } from './service/sched-c1.service';
import { DecimalPipe } from '@angular/common';
import { Sections } from './sections.enum';
import { UtilService } from 'src/app/shared/utils/util.service';
import { validateAmount } from '../../shared/utils/forms/validation/amount.validator';

@Component({
  selector: 'app-sched-c1',
  templateUrl: './sched-c1.component.html',
  styleUrls: ['./sched-c1.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class SchedC1Component implements OnInit, OnChanges {
  @Input() formType: string;
  @Input() scheduleAction: ScheduleActions;
  @Input() forceChangeDetection: Date;
  @Input() transactionDetail: any;
  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  public c1Form: FormGroup;
  public sectionType: string;
  public states: any[];
  public readonly initialSection = Sections.initialSection;
  public readonly sectionA = Sections.sectionA;
  public readonly sectionB = Sections.sectionB;
  public readonly sectionC = Sections.sectionC;
  public readonly sectionD = Sections.sectionD;
  public readonly sectionE = Sections.sectionE;
  public readonly sectionF = Sections.sectionF;
  public readonly sectionG = Sections.sectionG;
  public readonly sectionH = Sections.sectionH;
  public readonly sectionI = Sections.sectionI;
  public file: any = null;
  public fileNameToDisplay: string = null;
  // TODO check requirements for each amount field.
  public _contributionAmountMax = 14;
  public existingData: any;
  public fieldLoanAmount = { name: 'loan_amount' };
  public c1EditMode = false;
  public currentC1Data: any;

  private _reportId;
  public editScheduleAction;

  constructor(
    private _fb: FormBuilder,
    private _contactsService: ContactsService,
    private _typeaheadService: TypeaheadService,
    private _schedC1Service: SchedC1Service,
    private _decimalPipe: DecimalPipe,
    private _utilService: UtilService,
    private _loanService: LoanService,
    private _reportTypeService: ReportTypeService
  ) { }

  public ngOnInit() {
    this.sectionType = Sections.initialSection;
    this._getStates();
    this._getExistingLoanData();
    this._setFormGroup();
  }

  private _getExistingLoanData() {
    const reportId: string = this._reportTypeService.getReportIdFromStorage('3X').toString();
    this._loanService.getDataSchedule(reportId, this.transactionDetail.transactionId).subscribe(res => {
      res = res[0];

      this._reportId = res.report_id;
      this.c1Form.patchValue({ lending_institution: res.entity_name });
      this.c1Form.patchValue({ mailing_address: res.street_2 ? `${res.street_1} ${res.street_2}` : res.street_1 });
      this.c1Form.patchValue({ city: res.city });
      this.c1Form.patchValue({ state: res.state });
      this.c1Form.patchValue({ zip: res.zip_code });
      this.c1Form.patchValue({ loan_amount: this._decimalPipe.transform(res.loan_amount_original, '.2-2') });
      this.c1Form.patchValue({ loan_intrest_rate: this._decimalPipe.transform(res.loan_intrest_rate, '.2-2')});
      this.c1Form.patchValue({ loan_incurred_date: res.loan_incurred_date });
      let element : any = document.getElementById('loan_due_date');
      if(res.loan_due_date){
        let temp = new Date(res.loan_due_date);
        if (isNaN(temp.getTime())) {
          this.c1Form.patchValue({ loan_due_date: res.loan_due_date });
        }
        else {
          this.c1Form.patchValue({ loan_due_date: this._utilService.formatDate(res.loan_due_date) });
        }
      }

      //if edit mode, check if a child c1 exists
      if(this.scheduleAction === ScheduleActions.edit){
        if(res.child && Array.isArray(res.child)){
          let c1 = res.child.filter(e => e.transaction_type_identifier === 'SC1');
          if(c1.length > 0){
            c1 = c1[0];
            this.c1EditMode = true;
            this.currentC1Data = c1;
            this._prepopulateEditFields(c1);
          }
        }
      }

    });
  }

  // private setInputType(loanData: any, element: HTMLInputElement) {
  //   let temp = new Date(loanData.loan_due_date);
  //   if (isNaN(temp.getTime())) {
  //     if (element) {
  //       // element.focus();
  //       // element.type = "text";
  //       // element.blur();
  //       this.changeInputType(element,'text');
  //     }
  //   }
  //   else {
  //     if (element) {
  //       // element.focus();
  //       // element.type = "date";
  //       // element.blur();
  //       this.changeInputType(element,'date');
  //     }
  //   }
  // }


  _prepopulateEditFields(c1: any) {
    this.c1Form.patchValue({original_loan_date:c1.original_loan_date});
    this.c1Form.patchValue({is_loan_restructured: c1.is_loan_restructured});
    this.c1Form.patchValue({credit_amount_this_draw: this._decimalPipe.transform(c1.credit_amount_this_draw, '.2-2') });
    this.c1Form.patchValue({total_outstanding_balance: this._decimalPipe.transform(c1.total_outstanding_balance, '.2-2') });
    this.c1Form.patchValue({other_parties_liable: c1.other_parties_liable});
    this.c1Form.patchValue({pledged_collateral_ind: c1.pledged_collateral_ind});
    this.c1Form.patchValue({pledge_collateral_desc: c1.pledge_collateral_desc});
    this.c1Form.patchValue({pledge_collateral_amount: this._decimalPipe.transform(c1.pledge_collateral_amount, '.2-2') });
    this.c1Form.patchValue({perfected_intrest_ind: c1.perfected_intrest_ind});
    this.c1Form.patchValue({future_income_desc: c1.future_income_desc});
    this.c1Form.patchValue({future_income_estimate: this._decimalPipe.transform(c1.future_income_estimate, '.2-2') });
    this.c1Form.patchValue({depository_account_location: c1.depository_account_location});
    this.c1Form.patchValue({depository_account_street_1: c1.depository_account_street_1});
    this.c1Form.patchValue({depository_account_street_2: c1.depository_account_street_2});
    this.c1Form.patchValue({depository_account_city: c1.depository_account_city});
    this.c1Form.patchValue({depository_account_state: c1.depository_account_state});
    this.c1Form.patchValue({depository_account_zip:c1.depository_account_zip});
    this.c1Form.patchValue({depository_account_auth_date : c1.depository_account_auth_date});
    this.c1Form.patchValue({future_income_ind : c1.future_income_ind});
    this.c1Form.patchValue({basis_of_loan_desc : c1.basis_of_loan_desc});
    this.c1Form.patchValue({treasurer_last_name : c1.treasurer_last_name});
    this.c1Form.patchValue({treasurer_first_name : c1.treasurer_first_name});
    this.c1Form.patchValue({treasurer_middle_name : c1.treasurer_middle_name});
    this.c1Form.patchValue({treasurer_prefix : c1.treasurer_prefix});
    this.c1Form.patchValue({treasurer_suffix : c1.treasurer_suffix});
    this.c1Form.patchValue({treasurer_signed_date : c1.treasurer_signed_date});
    this.c1Form.patchValue({treasurer_entity_id : c1.treasurer_entity_id});
    this.c1Form.patchValue({final_authorization : c1.final_authorization});
    this.c1Form.patchValue({authorized_last_name : c1.authorized_last_name});
    this.c1Form.patchValue({authorized_first_name : c1.authorized_first_name});
    this.c1Form.patchValue({authorized_middle_name : c1.authorized_middle_name});
    this.c1Form.patchValue({authorized_prefix : c1.authorized_prefix});
    this.c1Form.patchValue({authorized_suffix : c1.authorized_suffix});
    this.c1Form.patchValue({authorized_entity_id : c1.authorized_entity_id});
    this.c1Form.patchValue({authorized_entity_title : c1.authorized_entity_title});
    this.c1Form.patchValue({authorized_signed_date : c1.authorized_signed_date});
    if(c1.authorized_signed_date){
      this.c1Form.patchValue({final_authorization : true});
    }

  }

  public ngOnChanges(changes: SimpleChanges) {
    this._clearFormValues();
    if (this.scheduleAction === ScheduleActions.edit) {
      // TODO populate form using API response from schedC.
    }
  }

  public formatSectionType() {
    switch (this.sectionType) {
      case Sections.sectionA:
        return 'Section A';
      case Sections.sectionB:
        return 'Section B';
      case Sections.sectionC:
        return 'Section C';
      case Sections.sectionD:
        return 'Section D';
      case Sections.sectionE:
        return 'Section E';
      case Sections.sectionF:
        return 'Section F';
      case Sections.sectionG:
        return 'Section G';
      case Sections.sectionH:
        return 'Section H';
      case Sections.sectionI:
        return 'Section I';
      default:
        return '';
    }
  }

  /**
   * Validate section before proceeding to the next.
   */
  public showNextSection() {
    // Mark as touched if user clicks next on an untouched, invalid form
    // to display fields in error.
    this.c1Form.markAsTouched();

    switch (this.sectionType) {
      case Sections.initialSection:

        //disabled ng-select is showing valid = false as well as invalid=false
        //enable it right before proceeding forward
        this.c1Form.controls['state'].enable();
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionA;
        }
        break;
      case Sections.sectionA:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionB;
        }
        break;
      case Sections.sectionB:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionC;
        }
        break;
      case Sections.sectionC:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionD;
        }
        break;
      case Sections.sectionD:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionE;
        }
        break;
      case Sections.sectionE:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionF;
        }
        break;
      case Sections.sectionF:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionG;
        }
        break;
      case Sections.sectionG:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionH;
        }
        break;
      case Sections.sectionH:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionI;
        }
        break;
      default:
        this.sectionType = Sections.initialSection;
    }
  }

  /**
   * Show previous section.  No need to validate.
   */
  public showPreviousSection() {
    switch (this.sectionType) {
      case Sections.sectionA:
        //disable the state form control back. 
        this.c1Form.controls['state'].disable();
        this.sectionType = Sections.initialSection;
        break;
      case Sections.sectionB:
        this.sectionType = Sections.sectionA;
        break;
      case Sections.sectionC:
        this.sectionType = Sections.sectionB;
        break;
      case Sections.sectionD:
        this.sectionType = Sections.sectionC;
        break;
      case Sections.sectionE:
        this.sectionType = Sections.sectionD;
        break;
      case Sections.sectionF:
        this.sectionType = Sections.sectionE;
        break;
      case Sections.sectionG:
        this.sectionType = Sections.sectionF;
        break;
      case Sections.sectionH:
        this.sectionType = Sections.sectionG;
        break;
      case Sections.sectionI:
        this.sectionType = Sections.sectionH;
        break;
      default:
      // this.sectionType = Sections.initialSection;
    }
  }

  public cancel(){
    this._goToLoan();
  }

  private _checkSectionValid(): boolean {
    switch (this.sectionType) {
      case Sections.initialSection:
        return this._checkInitialSectionValid();
      case Sections.sectionA:
        return this._checkSectionAValid();
      case Sections.sectionB:
        return this._checkSectionBValid();
      case Sections.sectionC:
        return this._checkSectionCValid();
      case Sections.sectionD:
        return this._checkSectionDValid();
      case Sections.sectionE:
        return this._checkSectionEValid();
      case Sections.sectionF:
        return this._checkSectionFValid();
      case Sections.sectionG:
        return this._checkSectionGValid();
      case Sections.sectionH:
        return this._checkSectionHValid();
      default:
        return true;
    }
  }

  private _checkInitialSectionValid(): boolean {
    // comment out for ease of dev testing - add back later.
    if (!this._checkFormFieldIsValid('lending_institution')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('mailing_address')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('city')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('state')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('zip')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('loan_amount')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('loan_incurred_date')) {
      return false;
    }
    return true;
  }

  private _checkSectionAValid(): boolean {
    if (!this._checkFormFieldIsValid('is_loan_restructured')) {
      return false;
    }
    return true;
  }

  private _checkSectionBValid(): boolean {
    if (!this._checkFormFieldIsValid('credit_amount_this_draw')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('total_outstanding_balance')) {
      return false;
    }
    return true;
  }

  private _checkSectionCValid(): boolean {
    if (!this._checkFormFieldIsValid('other_parties_liable')) {
      return false;
    }
    return true;
  }

  private _checkSectionDValid(): boolean {
    if (!this._checkFormFieldIsValid('pledged_collateral_ind')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('pledge_collateral_desc')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('pledge_collateral_amount')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('perfected_intrest_ind')) {
      return false;
    }
    return true;
  }

  private _checkSectionEValid(): boolean {
    if (!this._checkFormFieldIsValid('future_income_ind')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('future_income_desc')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('future_income_estimate')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('depository_account_location')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('depository_account_street_1')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('depository_account_street_2')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('depository_account_city')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('depository_account_state')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('depository_account_zip')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('depository_account_auth_date')) {
      return false;
    }
    return true;
  }

  private _checkSectionFValid(): boolean {
    if (!this._checkFormFieldIsValid('basis_of_loan_desc')) {
      return false;
    }
    return true;
  }

  private _checkSectionGValid(): boolean {
    if (!this._checkFormFieldIsValid('treasurer_last_name')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('treasurer_first_name')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('treasurer_middle_name')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('treasurer_prefix')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('treasurer_suffix')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('treasurer_signed_date')) {
      return false;
    }
    return true;
  }

  private _checkSectionHValid(): boolean {
    return true;
  }

  private _checkSectionIValid(): boolean {
    if (!this._checkFormFieldIsValid('authorized_last_name')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('authorized_first_name')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('authorized_middle_name')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('authorized_prefix')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('authorized_suffix')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('authorized_entity_title')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('authorized_signed_date')) {
      return false;
    }

    return true;
  }

  /**
   * Returns true if the field is valid.
   * @param fieldName name of control to check for validity
   */
  private _checkFormFieldIsValid(fieldName: string): boolean {
    if (this.c1Form.get(fieldName)) {
      return this.c1Form.get(fieldName).valid;
    }
  }

  private _getStates() {
    this._contactsService.getStates().subscribe(res => {
      this.states = res;
    });
  }

  private _setFormGroup() {
    const alphaNumericFn = alphaNumeric();

    this.c1Form = this._fb.group({
      lending_institution: new FormControl(null, [Validators.required, Validators.maxLength(100)]),
      mailing_address: new FormControl(null, [Validators.required, Validators.maxLength(100)]),
      city: new FormControl(null, [Validators.required, Validators.maxLength(30)]),
      state: new FormControl({ value: '', disabled: true }),
      zip: new FormControl(null, [Validators.required, Validators.maxLength(9)]),
      loan_amount: new FormControl(null, [Validators.required, validateAmount()]),
      loan_intrest_rate: new FormControl(null, []),
      loan_incurred_date: new FormControl(null, [Validators.required]),
      original_loan_date: new FormControl(null, []),
      loan_due_date: new FormControl(null, []),
      is_loan_restructured: new FormControl(null, [Validators.required]),
      credit_amount_this_draw: new FormControl(null, [validateAmount()]),
      total_outstanding_balance: new FormControl(null, [validateAmount()]),
      other_parties_liable: new FormControl(null, [Validators.required]),
      pledged_collateral_ind: new FormControl(null, [Validators.required]),
      pledge_collateral_desc: new FormControl(null, [Validators.maxLength(100),]),
      pledge_collateral_amount: new FormControl(null, [validateAmount()]),
      perfected_intrest_ind: new FormControl(null),
      future_income_desc: new FormControl(null, [Validators.maxLength(100)]),
      future_income_estimate: new FormControl(null, [validateAmount()]),
      depository_account_location: new FormControl(null, [Validators.maxLength(200)]),
      depository_account_street_1: new FormControl(null, [Validators.maxLength(34)]),
      depository_account_street_2: new FormControl(null, [Validators.maxLength(34)]),
      depository_account_city: new FormControl(null, [Validators.maxLength(30)]),
      depository_account_state: new FormControl(null),
      depository_account_zip: new FormControl(null, [Validators.maxLength(9)]),
      depository_account_auth_date: new FormControl(null),
      future_income_ind: new FormControl(null, [Validators.required]),
      basis_of_loan_desc: new FormControl(null, [Validators.maxLength(100)]),
      treasurer_last_name: new FormControl(null, [Validators.required, Validators.maxLength(30)]),
      treasurer_first_name: new FormControl(null, [Validators.required, Validators.maxLength(20)]),
      treasurer_middle_name: new FormControl(null, [Validators.maxLength(20)]),
      treasurer_prefix: new FormControl(null, [Validators.maxLength(10)]),
      treasurer_suffix: new FormControl(null, [Validators.maxLength(10)]),
      treasurer_signed_date: new FormControl(null, [Validators.required]),
      treasurer_entity_id: new FormControl(null),
      file_upload: new FormControl(null),
      final_authorization: new FormControl(null, [Validators.requiredTrue]),
      authorized_last_name: new FormControl(null, [Validators.required, Validators.maxLength(30)]),
      authorized_first_name: new FormControl(null, [Validators.required, Validators.maxLength(20)]),
      authorized_middle_name: new FormControl(null, [Validators.maxLength(20)]),
      authorized_prefix: new FormControl(null, [Validators.maxLength(10)]),
      authorized_suffix: new FormControl(null, [Validators.maxLength(10)]),
      authorized_entity_id: new FormControl(null),
      authorized_entity_title: new FormControl(null, [Validators.required, Validators.maxLength(20)]),
      authorized_signed_date: new FormControl(null, [Validators.required])
    });
  }

  public printPreview() {
    this._reportTypeService.printPreview('transaction_table_screen', '3X', this.transactionDetail.transactionId);
  }

  public importTransactions() {
    alert('Import not yet implemented');
  }

  public finish() {
    if (this._checkSectionIValid()) {

      if (this.c1Form.valid) {
      const formData = {};
      this._prepareFormDataForApi(formData);
      this._schedC1Service.saveScheduleC1(this.formType, this.c1EditMode ? ScheduleActions.edit:ScheduleActions.add, formData).subscribe(res => {
        this._goToLoanSummary();
      });
      } else {
        alert('Form is invalid. Errors exist on previous screens. ')
        //console.log('Errors exist on previous screens.');
      }
    } else {
      this.c1Form.markAsTouched();
    }
  }

  private _goToLoanSummary() {
    const loanRepaymentEmitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c_ls',
    };
    this.status.emit(loanRepaymentEmitObj);
  }

  private _goToLoan() {
    const loanEmitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c',
    };
    this.status.emit(loanEmitObj);
  }

  private _prepareFormDataForApi(formData: any) {
    for (const field in this.c1Form.controls) {
      if (field === 'loan_amount' ||
        field === 'credit_amount_this_draw' ||
        field === 'total_outstanding_balance' ||
        field === 'pledge_collateral_amount' ||
        field === 'future_income_estimate'
      ) {
        let amount = this.c1Form.get(field).value;
        if(amount){
          amount = amount.toString().replace(/,/g, ``);
        }
        formData[field] = amount;
      }  else if (field === 'loan_incurred_date') {
        formData[field] = this._utilService.formatDate(this.c1Form.get(field).value);
      } else if(field === 'loan_due_date'){
        formData[field] = this.c1Form.get(field).value;
      }
      else if (field === 'treasurer_last_name' ||
      field === 'treasurer_first_name' ||
      field === 'authorized_last_name' ||
      field === 'authorized_first_name') {
        const typeAheadField = this.c1Form.get(field).value;
        let innerfield:string; 
        if(field.includes('last_name')){
          innerfield="last_name";
        }
        else if(field.includes('first_name')){
          innerfield="first_name";
        }

        if(typeAheadField && typeof typeAheadField !== 'string'){
          formData[field] = typeAheadField[innerfield];
        }
        else{
          formData[field] = this.c1Form.get(field).value;
        }
      }
       else {
        if (this.c1Form.contains(field)) {
          formData[field] = this.c1Form.get(field).value;
        }
      }
    }
    if(this.c1EditMode){
      formData['transaction_id'] = this.currentC1Data.transaction_id;
    }
    formData['back_ref_transaction_id'] = this.transactionDetail.transactionId;
  }
/* 
  private setLoanDueDateFormat(field: string, formData: any) {
    let temp = new Date(this.c1Form.get(field).value);
    if (isNaN(temp.getTime())) {
      formData[field] = this.c1Form.get(field).value;
    }
    else {
      formData[field] = this.c1Form.get(field).value;
      // formData[field] = this._utilService.formatDate(this.c1Form.get(field).value);
    }
  } */

  public uploadFile() {
    // TODO add file to form
    // Is this neeed or can it be added to form from the html template
  }

  private _clearFormValues() {
    if(this.c1Form){
      this.c1Form.reset();
    }
  }

  // type ahead start
  // type ahead start
  // type ahead start

  /**
   *
   * @param $event
   */
  public handleSelectedIndividual($event: NgbTypeaheadSelectItemEvent) {
    // TODO set entity id? in formGroup
    const entity = $event.item;
    this.c1Form.patchValue({ treasurer_last_name: entity.last_name }, { onlySelf: true });
    this.c1Form.patchValue({ treasurer_first_name: entity.first_name }, { onlySelf: true });
    this.c1Form.patchValue({ treasurer_middle_name: entity.middle_name }, { onlySelf: true });
    this.c1Form.patchValue({ treasurer_prefix: entity.preffix }, { onlySelf: true });
    this.c1Form.patchValue({ treasurer_suffix: entity.suffix }, { onlySelf: true });
    this.c1Form.patchValue({ treasurer_entity_id: entity.entity_id }, { onlySelf: true });
  }

  /**
  *
  * @param $event
  */
  public handleSelectedIndividualForFinalAuthorization($event: NgbTypeaheadSelectItemEvent) {
    // TODO set entity id? in formGroup
    const entity = $event.item;
    this.c1Form.patchValue({ authorized_last_name: entity.last_name }, { onlySelf: true });
    this.c1Form.patchValue({ authorized_first_name: entity.first_name }, { onlySelf: true });
    this.c1Form.patchValue({ authorized_middle_name: entity.middle_name }, { onlySelf: true });
    this.c1Form.patchValue({ authorized_prefix: entity.preffix }, { onlySelf: true });
    this.c1Form.patchValue({ authorized_suffix: entity.suffix }, { onlySelf: true });
    //this.c1Form.patchValue({ authorized_middle_suffix: entity.suffix }, { onlySelf: true });
    this.c1Form.patchValue({ authorized_entity_id: entity.entity_id }, { onlySelf: true });
  }

  /**
   * Format an entity to display in the type ahead.
   *
   * @param result formatted item in the typeahead list
   */
  public formatTypeaheadItem(result: any) {
    const lastName = result.last_name ? result.last_name.trim() : '';
    const firstName = result.first_name ? result.first_name.trim() : '';
    const street1 = result.street_1 ? result.street_1.trim() : '';
    const street2 = result.street_2 ? result.street_2.trim() : '';

    return `${lastName}, ${firstName}, ${street1}, ${street2}`;
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

  // type ahead end
  // type ahead end
  // type ahead end

  public setFile(e: any): void {
    if (e.target.files[0]) {
      this.c1Form.patchValue({ file_upload: e.target.files[0] }, { onlySelf: true });
    }
  }

  public handleOnBlurEvent($event: any, fieldName: string) {
    this._formatAmount($event, fieldName, false);
  }

  // These 2 methods are duplicated from AbstractSchedule and should be made as shared utility
  // methods.

  private _formatAmount(e: any, fieldName: string, negativeAmount: boolean) {
    let contributionAmount: string = e.target.value;

    // default to 0 when no value
    contributionAmount = contributionAmount ? contributionAmount : '0';

    // remove commas
    contributionAmount = contributionAmount.replace(/,/g, ``);

    // determine if negative, truncate if > max
    contributionAmount = this._transformAmount(contributionAmount, this._contributionAmountMax);

    let contributionAmountNum = parseFloat(contributionAmount);
    // Amount is converted to negative for Return / Void / Bounced
    if (negativeAmount) {
      contributionAmountNum = -Math.abs(contributionAmountNum);
      // this._contributionAmount = String(contributionAmountNum);
    }

    const amountValue: string = this._decimalPipe.transform(contributionAmountNum, '.2-2');
    const patch = {};
    patch[fieldName] = amountValue;
    this.c1Form.patchValue(patch, { onlySelf: true });
  }

  /**
   * Allow for negative sign and don't allow more than the max
   * number of digits.
   */
  private _transformAmount(amount: string, max: number): string {
    if (!amount) {
      return amount;
    } else if (amount.length > 0 && amount.length <= max) {
      return amount;
    } else {
      // Need to handle negative sign, decimal and max digits
      if (amount.substring(0, 1) === '-') {
        if (amount.length === max || amount.length === max + 1) {
          return amount;
        } else {
          return amount.substring(0, max + 2);
        }
      } else {
        const result = amount.substring(0, max + 1);
        return result;
      }
    }
  }
}
