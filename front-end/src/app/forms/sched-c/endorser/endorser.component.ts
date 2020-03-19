import { validateAmount } from 'src/app/shared/utils/forms/validation/amount.validator';
import { LoanService } from './../service/loan.service';
import {
  Component,
  EventEmitter,
  ElementRef,
  Input,
  OnInit,
  Output,
  ViewEncapsulation,
  ViewChild,
  OnDestroy
, ChangeDetectionStrategy } from '@angular/core';
import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { FormBuilder, FormGroup, FormControl, NgForm, Validators } from '@angular/forms';
import { NgbTooltipConfig, NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../../environments/environment';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { UtilService } from '../../../shared/utils/util.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { EndorserService } from '../endorser/service/endorser.service';
import { f3xTransactionTypes } from '../../../shared/interfaces/FormsService/FormsService';
import { alphaNumeric } from '../../../shared/utils/forms/validation/alpha-numeric.validator';
import { floatingPoint } from '../../../shared/utils/forms/validation/floating-point.validator';
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';
import { Observable, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { ContactsMessageService } from '../../../contacts/service/contacts-message.service';
import { EndorserModel } from '../endorser/model/endorser.model';
import { ScheduleActions } from '../../form-3x/individual-receipt/schedule-actions.enum';
import { TypeaheadService } from '../../../shared/partials/typeahead/typeahead.service';
import { DialogService } from '../../../shared/services/DialogService/dialog.service';

export enum ActiveView {
  Endorsers = 'Endorsers',
  recycleBin = 'recycleBin',
  edit = 'edit'
}

export enum EndorsersActions {
  add = 'add',
  edit = 'edit'
}

@Component({
  selector: 'app-loanendorser',
  templateUrl: './endorser.component.html',
  styleUrls: ['./endorser.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe],
  encapsulation: ViewEncapsulation.None
})
export class EndorserComponent implements OnInit, OnDestroy {
  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() selectedOptions: any = {};
  @Input() formOptionsVisible: boolean = false;
  @Input() transactionTypeText = '';
  @Input() transactionType = '';
  @Input() transactionDetail: any;
  //@Input() scheduleAction: EndorsersActions = null;
  @Input() scheduleAction: ScheduleActions;

  /**
   * Subscription for pre-populating the form for view or edit.
   */
  private _populateFormSubscription: Subscription;
  private _loadFormFieldsSubscription: Subscription;

  public checkBoxVal: boolean = false;
  public endorserForm: FormGroup;
  public formFields: any = [];
  public formVisible: boolean = false;
  public hiddenFields: any = [];
  //public memoCode: boolean = false;
  public testForm: FormGroup;
  public titles: any = [];
  public states: any = [];
  public individualFormFields: any = [];
  public committeeFormFields: any = [];
  public organizationFormFields: any = [];
  public candidateFormFields: any = [];
  public prefixes: any = [];
  public suffixes: any = [];
  public entityTypes: any = [];
  public officeSought: any = [];
  public officeState: any = [];

  private _formType: string = '';
  private _transactionTypePrevious: string = null;
  private _contributionAggregateValue = 0.0;
  private _selectedEntity: any;
  private _contributionAmountMax: number;
  private _entityType: string = 'IND';
  private readonly _childFieldNamePrefix = 'child*';
  private _contactToEdit: EndorserModel;
  private _loading: boolean = false;
  private _selectedChangeWarn: any;
  private typeChangeEventOccured = false;
  private _employerOccupationRequired: boolean = false;

  constructor(
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _endorserService: EndorserService,
    private _config: NgbTooltipConfig,
    private _router: Router,
    private _utilService: UtilService,
    private _messageService: MessageService,
    private _decimalPipe: DecimalPipe,
    private _typeaheadService: TypeaheadService,
    private _dialogService: DialogService,
    private _contactsMessageService: ContactsMessageService,
    private _formsService: FormsService,
    private _loanservice: LoanService,
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';

/*     this._populateFormSubscription = this._contactsMessageService.getPopulateFormMessage().subscribe(message => {
      this.populateFormForEdit(message);
      //this.getFormFields();
    });

    this._loadFormFieldsSubscription = this._contactsMessageService.getLoadFormFieldsMessage().subscribe(message => {
      //this.getFormFields();
    }); */
  }

  ngOnInit(): void {
    this._contactToEdit = null;

    this._messageService.clearMessage();

    this.getFormFields();

    if(!this.scheduleAction){
      this.scheduleAction = ScheduleActions.add;
    }

    this.endorserForm = this._fb.group({});
    if (this.selectedOptions) {
      if (this.selectedOptions.length >= 1) {
        this.formVisible = true;
      }
    }

  }

  public ngDoCheck(): void { }

  public ngOnDestroy(): void {
    this._messageService.clearMessage();
    // this._populateFormSubscription.unsubscribe();
    //localStorage.removeItem('contactsaved');
  }

  public debug(obj: any): void {
    //console.log('obj: ', obj);
  }


  private _setForm(fields: any): void {
    const formGroup: any = [];
    this._employerOccupationRequired = false;
    //console.log('_setForm fields ', fields);
    fields.forEach(el => {
      if (el.hasOwnProperty('cols')) {
        el.cols.forEach(e => {
          formGroup[e.name] = new FormControl(e.value || null, this._mapValidators(e.validation, e.name));
        });
      }
    });



    this.endorserForm = new FormGroup(formGroup);

    if (this.scheduleAction === ScheduleActions.edit) {
      this.populateFormForEdit(this.transactionDetail.endorser);
    }
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
     * For adding field specific validation that's custom.
     * This block adds zip code, and contribution date validation.
     */
    if (fieldName === 'zip_code') {
      formValidators.push(alphaNumeric());
    }

    if (validators) {
      for (const validation of Object.keys(validators)) {
        if (validation === 'required' && validators[validation]) {

          //push validators for employer and occupation on amount change. 
          if (fieldName !== 'employer' && fieldName !== 'occupation') {
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
        }
      }
    }

    return formValidators;
  }


  public contributionAmountChange(e: any, fieldName: string, negativeAmount: boolean): void {
    // const isChildForm = fieldName.startsWith(this._childFieldNamePrefix) ? true : false;
    let contributionAmount: string = e.target.value;

    // default to 0 when no value
    contributionAmount = contributionAmount ? contributionAmount : '0';

    // remove commas
    contributionAmount = contributionAmount.replace(/,/g, ``);


    // Amount is converted to negative for Return / Void / Bounced
    let contributionAmountNum = parseFloat(contributionAmount);
    if (negativeAmount) {
      contributionAmountNum = -Math.abs(contributionAmountNum);
    }

    if (contributionAmountNum > 200) {
      this.endorserForm.controls['occupation'].setValidators([Validators.required]);
      this.endorserForm.controls['employer'].setValidators([Validators.required]);
      this.endorserForm.controls['occupation'].updateValueAndValidity();
      this.endorserForm.controls['employer'].updateValueAndValidity();
    }
    else {
      this.endorserForm.controls['occupation'].clearValidators();
      this.endorserForm.controls['employer'].clearValidators();
      this.endorserForm.controls['occupation'].updateValueAndValidity();
      this.endorserForm.controls['employer'].updateValueAndValidity();
    }


    const amountValue: string = this._decimalPipe.transform(contributionAmountNum, '.2-2');

    if (this.endorserForm.get('contribution_amount')) {
      this.endorserForm.patchValue({ contribution_amount: amountValue }, { onlySelf: true });


      if ("add" === this.scheduleAction) {
        this.endorserForm.patchValue({ contribution_amount: amountValue }, { onlySelf: true });
      }
      // else {
      //   //calculate balance and updated fields
      //   // let currentOutstandingBalance = this.currentLoanData.loan_balance;
      //   currentOutstandingBalance = parseFloat(currentOutstandingBalance.toString().replace(/,/g, ``));
      //   let currentLoanAmountFromDB = this.currentLoanData.loan_amount_original;
      //   let newOutstandingBalance = contributionAmountNum - currentLoanAmountFromDB + currentOutstandingBalance;
      //   this.frmLoan.patchValue({ loan_balance: this._decimalPipe.transform(newOutstandingBalance, '.2-2') }, { onlySelf: true });
      // }

    }
  }

  /**
  * Prevent user from keying in more than the max allowed by the API.
  * HTML max must allow for commas, decimals and negative sign and therefore
  * this is needed to enforce digit limitation.  This method will remove
  * non-numerics permitted by the floatingPoint() validator,
  * commas, decimals and negative sign, before checking the number of digits.
  *
  * Note: If this method is not desired, it may be replaced with a validation
  * on submit.  It is here to catch user error before submitting the form.
  */
  public contributionAmountKeyup(e: any) {
    let val = this._utilService.deepClone(e.target.value);
    val = val.replace(/,/g, ``);
    val = val.replace(/\./g, ``);
    val = val.replace(/-/g, ``);

    if (val) {
      if (val.length > this._contributionAmountMax) {
        e.target.value = e.target.value.substring(0, e.target.value.length - 1);
      }
    }
  }


  /**
   * Allow for negative sign and don't allow more than the max
   * number of digits.
   */
  private transformAmount(amount: string, max: number): string {
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

  public handleStateChange(stateOption: any, col: any) {
    if (this._selectedEntity) {
      this.showWarn(col.text, 'state');
      this.endorserForm.patchValue({ state: this._selectedEntity.state }, { onlySelf: true });
    } else {
      this.endorserForm.patchValue({ state: stateOption.code }, { onlySelf: true });
    }
  }

  private showWarn(fieldLabel: string, name: string) {
    if (this._selectedChangeWarn[name] === name) {
      return;
    }

    this._selectedChangeWarn[name] = name;
  }

  /**
   * @deprecated
   */
  public receiveTypeaheadData(contact: any, fieldName: string): void {

    if (fieldName === 'first_name') {
      this.endorserForm.patchValue({ last_name: contact.last_name }, { onlySelf: true });
      this.endorserForm.controls['last_name'].setValue({ last_name: contact.last_name }, { onlySelf: true });
    }

    if (fieldName === 'last_name') {
      this.endorserForm.patchValue({ first_name: contact.first_name }, { onlySelf: true });
      this.endorserForm.controls['first_name'].setValue({ first_name: contact.first_name }, { onlySelf: true });
    }

    this.endorserForm.patchValue({ middle_name: contact.middle_name }, { onlySelf: true });
    this.endorserForm.patchValue({ prefix: contact.prefix }, { onlySelf: true });
    this.endorserForm.patchValue({ suffix: contact.suffix }, { onlySelf: true });
    this.endorserForm.patchValue({ street_1: contact.street_1 }, { onlySelf: true });
    this.endorserForm.patchValue({ street_2: contact.street_2 }, { onlySelf: true });
    this.endorserForm.patchValue({ city: contact.city }, { onlySelf: true });
    this.endorserForm.patchValue({ state: contact.state }, { onlySelf: true });
    this.endorserForm.patchValue({ entity_type: contact.entity_type }, { onlySelf: true });
    this.endorserForm.patchValue({ zip_code: contact.zip_code }, { onlySelf: true });
    this.endorserForm.patchValue({ occupation: contact.occupation }, { onlySelf: true });
    this.endorserForm.patchValue({ employer: contact.employer }, { onlySelf: true });

    this.endorserForm.patchValue({ phoneNumber: contact.phoneNumber }, { onlySelf: true });
    this.endorserForm.patchValue({ candOffice: contact.candOffice }, { onlySelf: true });
    this.endorserForm.patchValue({ candOfficeState: contact.candOfficeState }, { onlySelf: true });
    this.endorserForm.patchValue({ candOfficeDistrict: contact.candOfficeDistrict }, { onlySelf: true });

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



  public handleSelectedItem($event: NgbTypeaheadSelectItemEvent) {
    const contact = $event.item;
    this._selectedEntity = this._utilService.deepClone(contact);
    this.endorserForm.patchValue({ last_name: contact.last_name }, { onlySelf: true });
    this.endorserForm.patchValue({ first_name: contact.first_name }, { onlySelf: true });
    this.endorserForm.patchValue({ middle_name: contact.middle_name }, { onlySelf: true });
    this.endorserForm.patchValue({ prefix: contact.preffix }, { onlySelf: true });
    this.endorserForm.patchValue({ suffix: contact.suffix }, { onlySelf: true });
    this.endorserForm.patchValue({ street_1: contact.street_1 }, { onlySelf: true });
    this.endorserForm.patchValue({ street_2: contact.street_2 }, { onlySelf: true });
    this.endorserForm.patchValue({ city: contact.city }, { onlySelf: true });
    this.endorserForm.patchValue({ state: contact.state }, { onlySelf: true });
    this.endorserForm.patchValue({ zip_code: contact.zip_code }, { onlySelf: true });
    this.endorserForm.patchValue({ entity_type: contact.entity_type }, { onlySelf: true });
    this.endorserForm.patchValue({ occupation: contact.occupation }, { onlySelf: true });
    this.endorserForm.patchValue({ employer: contact.employer }, { onlySelf: true });
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


  private getFormFields(): void {
    this._endorserService.get_sched_c_endorser_dynamic_forms_fields().subscribe(res => {
      if (res) {
        //console.log('getFormFields res =', res);
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

            this._loading = false;
          } // typeof res.data
        } // res.hasOwnProperty('data')
      } // res
    });
  }

  private populateFormForEdit(endorser: any) {
    if (endorser) {

      this.endorserForm.patchValue({ first_name: endorser.first_name }, { onlySelf: true });
      this.endorserForm.patchValue({ last_name: endorser.last_name }, { onlySelf: true });
      this.endorserForm.patchValue({ middle_name: endorser.middle_name }, { onlySelf: true });
      this.endorserForm.patchValue({ prefix: endorser.prefix }, { onlySelf: true });
      this.endorserForm.patchValue({ suffix: endorser.suffix }, { onlySelf: true });

      this.endorserForm.patchValue({ street_1: endorser.street_1 }, { onlySelf: true });
      this.endorserForm.patchValue({ street_2: endorser.street_2 }, { onlySelf: true });
      this.endorserForm.patchValue({ city: endorser.city }, { onlySelf: true });
      this.endorserForm.patchValue({ state: endorser.state }, { onlySelf: true });
      this.endorserForm.patchValue({ zip_code: endorser.zip_code }, { onlySelf: true });

      this.endorserForm.patchValue({ employer: endorser.employer }, { onlySelf: true });
      this.endorserForm.patchValue({ occupation: endorser.occupation }, { onlySelf: true });

      this.endorserForm.patchValue({ contribution_amount: this._decimalPipe.transform(endorser.contribution_amount, '.2-2') }
        , { onlySelf: true });
      ;

      if (this._selectedEntity) {
        this._selectedEntity.entity_id;
      }
      else {
        this._selectedEntity = {
          entity_id: this.transactionDetail.endorser.guarantor_entity_id
        }
      }

    }
  }

  public cancelStep(): void {
    this.endorserForm.reset();
    this.status.emit({
      form: {},
      direction: 'previous',
      step: 'step_3', 
      action:ScheduleActions.edit,
      scheduleType: this.transactionDetail.entryScreenScheduleType,
      transactionDetail: {
        transactionModel: this.transactionDetail
      }

    });
  }



  private _goToLoan(loan: any) {
    const loanRepaymentEmitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c',
      action: ScheduleActions.add, //TODO fix it later 
      transactionDetail: {
        transactionModel: {
          transactionId: loan ? loan.transaction_id : null,
          entityId: loan ? loan.entity_id : null
        }
      }
    };
    this.status.emit(loanRepaymentEmitObj);
  }


  public isFieldName(fieldName: string, nameString: string): boolean {
    return fieldName === nameString || fieldName === this._childFieldNamePrefix + nameString;
  }

  public saveEndorser(addmore: boolean = false) {
    if(!this.endorserForm.valid){
      this.endorserForm.markAsDirty();
      this.endorserForm.markAsTouched();
      window.scrollTo(0, 0);
      return ;
    }

    const hiddenFieldsObj = {
      back_ref_transaction_id: this.transactionDetail.endorser.back_ref_transaction_id,
      entity_id: this._selectedEntity ? this._selectedEntity.entity_id : null, 
      transaction_id: this.transactionDetail.endorser.transaction_id
    }
    let endorserObj = this._prepareDataForApiCall();


    this._loanservice.saveSched_C2(this.scheduleAction, endorserObj, hiddenFieldsObj).subscribe(res => {
      //console.log('success');
      //console.log(res);
      if (!addmore) {
        this.goToEndorserSummary();
      }
      else {
        this.endorserForm.reset();
      }
    }, error => {
      //console.log(error);

    });
  }

  _prepareDataForApiCall() {
    const endorserObj = this.endorserForm.value;
    endorserObj.contribution_amount = endorserObj.contribution_amount.replace(/,/g, ``);
    endorserObj.last_name = this._utilService.extractNameFromEntityObj('last_name', endorserObj.last_name);
    endorserObj.first_name = this._utilService.extractNameFromEntityObj('first_name', endorserObj.first_name);
    return endorserObj;
  }

  public goToEndorserSummary() {
    const loanRepaymentEmitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c_es',
      action: ScheduleActions.add, //TODO fix it later 
      transactionDetail: {
        transactionModel: {
          endorser:{
            transaction_id:this.transactionDetail.endorser.transaction_id,
            back_ref_transaction_id: this.transactionDetail.endorser.back_ref_transaction_id
          }, 
          c1Exists: this.transactionDetail.c1Exists
        }
      }
    };
    this.status.emit(loanRepaymentEmitObj);
  }


}
