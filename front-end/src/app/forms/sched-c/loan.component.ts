import { IndividualReceiptService } from './../form-3x/individual-receipt/individual-receipt.service';
import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, EventEmitter, Input, OnChanges, OnDestroy, OnInit, Output, SimpleChanges, ViewEncapsulation } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbTooltipConfig, NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
import { Observable, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged, map, switchMap } from 'rxjs/operators';
import { ReportTypeService } from '../../forms/form-3x/report-type/report-type.service';
import { MessageService } from '../../shared/services/MessageService/message.service';
import { alphaNumeric } from '../../shared/utils/forms/validation/alpha-numeric.validator';
import { validateAmount } from '../../shared/utils/forms/validation/amount.validator';
import { UtilService } from '../../shared/utils/util.service';
import { ScheduleActions } from '../form-3x/individual-receipt/schedule-actions.enum';
import { LoanService } from '../sched-c/service/loan.service';
import { TransactionsMessageService } from '../transactions/service/transactions-message.service';
import { TypeaheadService } from './../../shared/partials/typeahead/typeahead.service';
import { ContributionDateValidator } from './../../shared/utils/forms/validation/contribution-date.validator';
import { F3xMessageService } from './../form-3x/service/f3x-message.service';

export enum ActiveView {
  Loans = 'Loans',
  recycleBin = 'recycleBin',
  edit = 'edit'
}

@Component({
  selector: 'app-sched-c-loans',
  templateUrl: './loan.component.html',
  styleUrls: ['./loan.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe],
  encapsulation: ViewEncapsulation.None
})
// TODO a lot of the methods here were copied from AbsractSchedule and need to be deleted if not used.
export class LoanComponent implements OnInit, OnDestroy, OnChanges {

  @Input() formType: string;
  @Input() scheduleAction: ScheduleActions = ScheduleActions.add;
  @Input() transactionDetail: any;
  @Input() forceChangeDetection: Date;
  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  /**
   * Subscription for pre-populating the form for view or edit.
   */

  private _clearFormSubscription: Subscription;

  public checkBoxVal = false;
  public frmLoan: FormGroup;
  public formFields: any = [];
  public formVisible = false;
  public hiddenFields: any = [];
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
  public electionTypesSelected: any = [];
  public electionTypes: any = [];
  public secured: any = [];
  public editScheduleAction: ScheduleActions = ScheduleActions.edit;
  public addScheduleAction: ScheduleActions = ScheduleActions.add;

  public entityType = 'IND';

  private _selectedEntity: any;
  private _contributionAmountMax = 12;
  private readonly _childFieldNamePrefix = 'child*';
  private _selectedChangeWarn: any;
  private _transactionId: string;
  private _transactionTypeIdentifier: string;
  private _transactionCategory: string;
  private cvgStartDate: string;
  private cvgEndDate: string;
  private currentLoanData: any; 0
  private _selectedEntityId: any;
  private typeChangeEventOccured = false;
  _routeListener: Subscription;
  private c1ExistsFlag: any;
  reportId: any;
  formView: boolean = false;
  routesSubscription: Subscription;
  constructor(
    private _loansService: LoanService,
    private _config: NgbTooltipConfig,
    private _router: Router,
    private _utilService: UtilService,
    private _messageService: MessageService,
    private _decimalPipe: DecimalPipe,
    private _typeaheadService: TypeaheadService,
    private _receiptService: ReportTypeService,
    private _transactionsMessageService: TransactionsMessageService,
    private _contributionDateValidator: ContributionDateValidator,
    private _f3xMessageService: F3xMessageService,
    private _activatedRoute: ActivatedRoute, 
    private _indReceiptService: IndividualReceiptService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
    this.routesSubscription = _activatedRoute.queryParams.subscribe(p => {
      this.formView = p.formView ? p.formView === 'true' : false;
    });
    this._clearFormSubscription = this._f3xMessageService.getInitFormMessage().subscribe(message => {
      if (this.frmLoan) {
        this.frmLoan.reset();
        this.setupForm();
      }
    });
    this.reportId = this._activatedRoute.snapshot.queryParams.reportId;
  }

  ngOnInit(): void {
    this.setupForm();
  }

  private setupForm() {
    this._selectedEntity = null;
    this._transactionTypeIdentifier = 'LOANS_OWED_BY_CMTE';
    this._transactionCategory = 'loans-and-debts';
    this._messageService.clearMessage();
    this.getFormFields();
    this.entityType = 'IND';
    if (this.formView) {
      this.frmLoan.disable();
    }

  }

  public ngOnChanges(changes: SimpleChanges): void {
    this.ngOnInit();
  }

  public ngOnDestroy(): void {
    this._messageService.clearMessage();
    this._clearFormSubscription.unsubscribe();
  }

  private _setForm(fields: any): void {
    const formGroup: any = [];
    fields.forEach(el => {
      if (el.hasOwnProperty('cols')) {
        el.cols.forEach(e => {
          formGroup[e.name] = new FormControl(e.value || null, this._mapValidators(e.validation, e.name));
        });
      }
    });

    this.frmLoan = new FormGroup(formGroup);

    if (this.scheduleAction === ScheduleActions.add) {
      this._clearFormValues();
      this.frmLoan.patchValue({ loan_balance: this._decimalPipe.transform(0, '.2-2') });
      this.frmLoan.patchValue({ loan_payment_to_date: this._decimalPipe.transform(0, '.2-2') });
    }

    this._setEntityTypeDefault();
  }

  private _setEntityTypeDefault() {
    if (this.frmLoan.get('entity_type')) {
      const entityTypeVal = this.frmLoan.get('entity_type').value;
      if (!entityTypeVal) {
        this.frmLoan.patchValue({ entity_type: this.entityType }, { onlySelf: true });
      }
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

    if (fieldName === 'zip_code') {
      formValidators.push(alphaNumeric());
    }


    //date validator is only applicable for "add" and not for edit. Also field is being disabled for edit. 
    if (fieldName === 'loan_incurred_date') {
      const formType = JSON.parse(localStorage.getItem('form_3X_report_type'));
      if(formType){
        this.cvgStartDate = formType.cvgStartDate;
        this.cvgEndDate = formType.cvgEndDate;
        if (this.scheduleAction === ScheduleActions.add) {
          formValidators.push(this._contributionDateValidator.contributionDate(this.cvgStartDate, this.cvgEndDate)); //TODO-ZS  -- do null checks. 
        }
      }
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
            if (fieldName === 'loan_amount_original') {
              formValidators.push(validateAmount());
            } else {
              formValidators.push(Validators.maxLength(validators[validation]));
            }
          }
        }
      }
    }

    return formValidators;
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
   * Updates the contribution aggregate field once contribution ammount is entered.
   *
   * @param      {Object}  e         The event object.
   * @param      {string}  fieldName The name of the field
   */
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

    const amountValue: string = this._decimalPipe.transform(contributionAmountNum, '.2-2');

    if (this.frmLoan.get('loan_amount_original')) {
      this.frmLoan.patchValue({ loan_amount_original: amountValue }, { onlySelf: true });


      if ("add" === this.scheduleAction) {
        this.frmLoan.patchValue({ loan_balance: amountValue }, { onlySelf: true });
      }
      else {
        //calculate balance and updated fields
        let currentOutstandingBalance = this.currentLoanData.loan_balance;
        currentOutstandingBalance = parseFloat(currentOutstandingBalance.toString().replace(/,/g, ``));
        let currentLoanAmountFromDB = this.currentLoanData.loan_amount_original;
        let newOutstandingBalance = contributionAmountNum - currentLoanAmountFromDB + currentOutstandingBalance;
        this.frmLoan.patchValue({ loan_balance: this._decimalPipe.transform(newOutstandingBalance, '.2-2') }, { onlySelf: true });
      }

    }
  }

  public dueDateChanged(event:any){
    let input = event.key;
    const e = new Event('input');
    if(this._isIgnoreKey(input)){
      return ; 
    }

    let element :any =  document.getElementById('loan_due_date');

      if(!input.match(/^[0-9]+$/) && element.type === "date"){
        element.type = "text";
        element.value = input;
        element.dispatchEvent(e);
        element.focus();
      }
      else if(input.match(/^[0-9]+$/) && element.type === "text"){
        element.type = "date";
      }
    element = null;
  }

  private _isIgnoreKey(key: string) {
    if (!key) {
      return true;
    }
    if (typeof key !== 'string') {
      return true;
    }
    const keyUpper = key.toUpperCase();
    if (
      // TODO add more keys, home, insert, end, print, pause, etc
      keyUpper === 'F12' ||
      keyUpper === 'TAB' ||
      keyUpper === 'ENTER' ||
      keyUpper === 'SHIFT' ||
      keyUpper === 'ALT' ||
      keyUpper === 'CONTROL' ||
      keyUpper === 'ARROWRIGHT' ||
      keyUpper === 'CAPSLOCK' ||
      keyUpper === 'PAGEUP' ||
      keyUpper === 'PAGEDOWN' ||
      keyUpper === 'ESCAPE' ||
      keyUpper === 'ARROWUP' ||
      keyUpper === 'ARROWLEFT' ||
      keyUpper === 'ARROWDOWN'
    ) {
      return true;
    } else {
      return false;
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
      this.frmLoan.patchValue({ state: this._selectedEntity.state }, { onlySelf: true });
    } else {
      this.frmLoan.patchValue({ state: stateOption.code }, { onlySelf: true });
    }
  }

  private showWarn(fieldLabel: string, name: string) {
    if (this._selectedChangeWarn[name] === name) {
      return;
    }
    this._selectedChangeWarn[name] = name;
  }


  public handleTypeChange(entityOption: any, col: any) {
    /*    this is just a flag to distinguish what caused the loadDynamicFormFields() method to be invoked,
    as it can be invoked during initial form population during edit or during change event
    on ngselect  */
    if(entityOption !== undefined) {
      this.typeChangeEventOccured = true;
      this.entityType = entityOption.code;
      this.frmLoan.patchValue({ entity_type: entityOption.code }, { onlySelf: true });
      if (this.scheduleAction === ScheduleActions.edit) {
        this._prePopulateFormForEdit(this.transactionDetail);
      }
      else {
        this.loadDynamiceFormFields();
      }
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
   * Format an entity to display in the Org type ahead.
   *
   * @param result formatted item in the typeahead list
   */
  public formatTypeaheadOrgItem(result: any) {
    const street1 = result.street_1 ? result.street_1.trim() : '';
    const street2 = result.street_2 ? result.street_2.trim() : '';
    const name = result.entity_name ? result.entity_name.trim() : '';

    return `${name}, ${street1}, ${street2}`;
  }


  /**
   * Populate the fields in the form with the values from the selected loan.
   *
   * @param $event The mouse event having selected the contact from the typeahead options.
   */
  public handleSelectedOrgItem($event: NgbTypeaheadSelectItemEvent) {
    const loan = $event.item;
    this._selectedEntity = this._utilService.deepClone(loan);
    //this.frmLoan.patchValue({ type: loan.type }, { onlySelf: true });
    this.frmLoan.patchValue({ middle_name: loan.middle_name }, { onlySelf: true });
    this.frmLoan.patchValue({ prefix: loan.prefix }, { onlySelf: true });
    this.frmLoan.patchValue({ suffix: loan.suffix }, { onlySelf: true });
    this.frmLoan.patchValue({ street_1: loan.street_1 }, { onlySelf: true });
    this.frmLoan.patchValue({ street_2: loan.street_2 }, { onlySelf: true });
    this.frmLoan.patchValue({ city: loan.city }, { onlySelf: true });
    this.frmLoan.patchValue({ state: loan.state }, { onlySelf: true });
    this.frmLoan.patchValue({ entity_type: loan.entity_type }, { onlySelf: true });
    this.frmLoan.patchValue({ zip_code: loan.zip_code }, { onlySelf: true });

    /* this.frmLoan.patchValue({ loan_amount_original: loan.loan_amount_original }, { onlySelf: true });
    this.frmLoan.patchValue({ election_code: loan.election_code }, { onlySelf: true });
    this.frmLoan.patchValue({ election_other_description: loan.election_other_description }, { onlySelf: true });
    this.frmLoan.patchValue({ is_loan_secured: loan.is_loan_secured }, { onlySelf: true });
    this.frmLoan.patchValue({ loan_amount_original: loan.loan_amount_original }, { onlySelf: true });
    this.frmLoan.patchValue({ loan_payment_to_date: loan.loan_payment_to_date }, { onlySelf: true });
    this.frmLoan.patchValue({ loan_balance: loan.loan_balance }, { onlySelf: true });
    this.frmLoan.patchValue({ loan_incurred_date: loan.loan_incurred_date }, { onlySelf: true });
    this.frmLoan.patchValue({ loan_due_date: loan.loan_due_date }, { onlySelf: true });
    this.frmLoan.patchValue({ loan_intrest_rate: loan.loan_intrest_rate }, { onlySelf: true });
    this.frmLoan.patchValue({ lender_cand_last_name: loan.lender_cand_last_name }, { onlySelf: true });
    this.frmLoan.patchValue({ lender_cand_first_name: loan.lender_cand_first_name }, { onlySelf: true });
    this.frmLoan.patchValue({ lender_cand_middle_name: loan.lender_cand_middle_name }, { onlySelf: true });

    this.frmLoan.patchValue({ lender_cand_prefix: loan.lender_cand_prefix }, { onlySelf: true });
    this.frmLoan.patchValue({ lender_cand_suffix: loan.lender_cand_suffix }, { onlySelf: true });
    this.frmLoan.patchValue({ lender_cand_office: loan.lender_cand_office }, { onlySelf: true });
    this.frmLoan.patchValue({ lender_cand_state: loan.lender_cand_state }, { onlySelf: true });
    this.frmLoan.patchValue({ lender_cand_district: loan.lender_cand_district }, { onlySelf: true });
    this.frmLoan.patchValue({ memo_code: loan.memo_code }, { onlySelf: true });
    this.frmLoan.patchValue({ memo_text: loan.memo_text }, { onlySelf: true }); */
  }

  public handleSelectedItem($event: NgbTypeaheadSelectItemEvent) {
    const loan = $event.item;
    this._selectedEntity = this._utilService.deepClone(loan);
    //this.frmLoan.patchValue({ type: loan.type }, { onlySelf: true });
    this.frmLoan.patchValue({ last_name: loan.last_name }, { onlySelf: true });
    this.frmLoan.patchValue({ first_name: loan.first_name }, { onlySelf: true });
    this.frmLoan.patchValue({ middle_name: loan.middle_name }, { onlySelf: true });
    this.frmLoan.patchValue({ prefix: loan.prefix }, { onlySelf: true });
    this.frmLoan.patchValue({ prefix: loan.preffix }, { onlySelf: true });
    this.frmLoan.patchValue({ suffix: loan.suffix }, { onlySelf: true });
    this.frmLoan.patchValue({ street_1: loan.street_1 }, { onlySelf: true });
    this.frmLoan.patchValue({ street_2: loan.street_2 }, { onlySelf: true });
    this.frmLoan.patchValue({ city: loan.city }, { onlySelf: true });
    this.frmLoan.patchValue({ state: loan.state }, { onlySelf: true });
    this.frmLoan.patchValue({ entity_type: loan.entity_type }, { onlySelf: true });
    this.frmLoan.patchValue({ zip_code: loan.zip_code }, { onlySelf: true });

    /* this.frmLoan.patchValue({ loan_amount_original: loan.loan_amount_original }, { onlySelf: true });
    this.frmLoan.patchValue({ election_code: loan.election_code }, { onlySelf: true });
    this.frmLoan.patchValue({ election_other_description: loan.election_other_description }, { onlySelf: true });
    this.frmLoan.patchValue({ loan_amount_original: loan.loan_amount_original }, { onlySelf: true });
    this.frmLoan.patchValue({ loan_payment_to_date: loan.loan_payment_to_date }, { onlySelf: true });
    this.frmLoan.patchValue({ loan_balance: loan.loan_balance }, { onlySelf: true });
    this.frmLoan.patchValue({ loan_incurred_date: loan.loan_incurred_date }, { onlySelf: true });
    this.frmLoan.patchValue({ loan_due_date: loan.loan_due_date }, { onlySelf: true });
    this.frmLoan.patchValue({ loan_intrest_rate: loan.loan_intrest_rate }, { onlySelf: true });
    this.frmLoan.patchValue({ lender_cand_last_name: loan.lender_cand_last_name }, { onlySelf: true });
    this.frmLoan.patchValue({ lender_cand_first_name: loan.lender_cand_first_name }, { onlySelf: true });
    this.frmLoan.patchValue({ lender_cand_middle_name: loan.lender_cand_middle_name }, { onlySelf: true });

    this.frmLoan.patchValue({ lender_cand_prefix: loan.lender_cand_prefix }, { onlySelf: true });
    this.frmLoan.patchValue({ lender_cand_suffix: loan.lender_cand_suffix }, { onlySelf: true });
    this.frmLoan.patchValue({ lender_cand_office: loan.lender_cand_office }, { onlySelf: true });
    this.frmLoan.patchValue({ lender_cand_state: loan.lender_cand_state }, { onlySelf: true });
    this.frmLoan.patchValue({ lender_cand_district: loan.lender_cand_district }, { onlySelf: true });
    this.frmLoan.patchValue({ memo_code: loan.memo_code }, { onlySelf: true });
    this.frmLoan.patchValue({ memo_text: loan.memo_text }, { onlySelf: true }); */

    let transactionTypeIdentifier = '';

    // default to indiv-receipt for sprint 17 - use input field in sprint 18.
    transactionTypeIdentifier = 'INDV_REC';

  }

  /**
   * Search for entities/LoanSumamrys when last name input value changes.
   */
  searchLastName = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          /*
          let result = this._typeaheadService.getContacts(searchText, 'last_name');

          let hasValue = false;
          result.pipe(map(contacts => {
            if(Array.isArray(contacts)) {
              if(contacts.length !== 0) {
                hasValue = true;
              }
            }
          }));

          if(hasValue) {
            result = result.pipe(map(contacts => contacts.filter(element => element.entity_type === 'IND' || element.entity_type === 'ORG')));
          }

          return result;
          */
         return this._typeaheadService.getContacts(searchText, 'last_name')
          .map(contacts => {
            if(contacts){
              let f = contacts.filter(con => con.entity_type === 'IND' || con.entity_type === 'ORG');
              return (f.length > 0) ? f : null;
            }
            else{
              return null;
            }
          });

        } else {
          return Observable.of([]);
        }
      })
    );

  /**
   * Search for entities/LoanSumamrys when first name input value changes.
   */
  searchFirstName = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          /*
          let result = this._typeaheadService.getContacts(searchText, 'first_name');

          let hasValue = false;
          result.pipe(map(contacts => {
            if(Array.isArray(contacts)) {
              if(contacts.length !== 0) {
                hasValue = true;
              }
            }
          }));

          if(hasValue) {
            result = result.pipe(map(contacts => contacts.filter(element => element.entity_type === 'IND' || element.entity_type === 'ORG')));
          }

          return result;
          */
         return this._typeaheadService.getContacts(searchText, 'first_name')
          .map(contacts => {
            if(contacts){
              let f = contacts.filter(con => con.entity_type === 'IND' || con.entity_type === 'ORG');
              return (f.length > 0) ? f : null;
            }
            else{
              return null;
            }
          });
        } else {
          return Observable.of([]);
        }
      })
    );

  /**
   * Search for Candidates when last name input value changes.
   */
  searchCandLastName = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'cand_last_name');
        } else {
          return Observable.of([]);
        }
      })
    );

  /**
   * Search for Candidate when first name input value changes.
   */
  searchCandFirstName = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'cand_first_name');
        } else {
          return Observable.of([]);
        }
      })
    );

  /**
   * Search for entities when organization/entity_name input value changes.
   */
  searchOrg = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          /*
          let result = this._typeaheadService.getContacts(searchText, 'entity_name');

          let hasValue = false;
          result.pipe(map(contacts => {
            if(Array.isArray(contacts)) {
              if(contacts.length !== 0) {
                hasValue = true;
              }
            }
          }));

          if(hasValue) {
            result = result.pipe(map(contacts => contacts.filter(element => element.entity_type === 'IND' || element.entity_type === 'ORG')));
          }

          return result;
          */

          return this._typeaheadService.getContacts(searchText, 'entity_name')
            .map(contacts => {
              if(contacts){
                let f = contacts.filter(con => con.entity_type === 'IND' || con.entity_type === 'ORG');
                return (f.length > 0) ? f : null;
              }else{
                return null;
              }
            });
        } else {
          return Observable.of([]);
        }
      })
    );

  /**
   * Search for entities when organization/entity_name input value changes.
   */
  searchCommitteeName = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'cmte_name');
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
   * format the value to display in the input field once selected from the typeahead.
   *
   * For some reason this gets called for all typeahead fields despite the binding in the
   * template to the last name field.  In these cases return x to retain the value in the
   * input for the other typeahead fields.
   */
  formatterCandLastName = (x: { cand_last_name: string }) => {
    if (typeof x !== 'string') {
      return x.cand_last_name;
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
  formatterCandFirstName = (x: { cand_first_name: string }) => {
    if (typeof x !== 'string') {
      return x.cand_first_name;
    } else {
      return x;
    }
  };

  /**
   * format the value to display in the input field once selected from the typeahead.
   *
   * For some reason this gets called for all typeahead fields despite the binding in the
   * template to the entity name field.  In these cases return x to retain the value in the
   * input for the other typeahead fields.
   */
  formatterOrgName = (x: { entity_name: string }) => {
    if (typeof x !== 'string') {
      return x.entity_name;
    } else {
      return x;
    }
  };


  private getFormFields(): void {
    this._loansService.get_sched_c_loan_dynamic_forms_fields().subscribe(res => {
      // TODO Temporarily hijacking the API response with JSON until ready.
      // res = schedCDynamicFormResponse;

      if (res) {
        if (res.hasOwnProperty('data')) {
          if (typeof res.data === 'object') {

            if (res.data.hasOwnProperty('individualFormFields')) {
              if (Array.isArray(res.data.individualFormFields)) {
                this.individualFormFields = res.data.individualFormFields;
                //console.log('this.individualFormFields =', this.individualFormFields);
              }
            }

            if (res.data.hasOwnProperty('OrganizationFormFields')) {
              if (Array.isArray(res.data.OrganizationFormFields)) {
                this.organizationFormFields = res.data.OrganizationFormFields;
                //console.log('this.organizationFormFields =', this.organizationFormFields);
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

            if (res.data.hasOwnProperty('entityTypes')) {
              if (Array.isArray(res.data.entityTypes)) {
                this.entityTypes = res.data.entityTypes;
                //console.log('this.entityTypes', this.entityTypes);
              }
            }

            if (res.data.hasOwnProperty('secured')) {
              if (Array.isArray(res.data.secured)) {
                this.secured = res.data.secured;
                //console.log('this.secured', this.secured);
              }
            }

            if (res.data.hasOwnProperty('titles')) {
              if (Array.isArray(res.data.titles)) {
                this.titles = res.data.titles;
              }
            }

          } // typeof res.data
        } // res.hasOwnProperty('data')


        //in some instances, transaction_id is being passed as 'transactionId'
        //TODO - need to combine/standardize the attribute names.
        if (this.transactionDetail && !this.transactionDetail.transaction_id && this.transactionDetail.transactionId) {
          this.transactionDetail.transaction_id = this.transactionDetail.transactionId;
        }

        if (this.scheduleAction === ScheduleActions.edit) {
          this._prePopulateFormForEdit(this.transactionDetail);
        }
        else if (this.scheduleAction === ScheduleActions.add) {
          this.formFields = this.individualFormFields; //set default
          this._setForm(this.individualFormFields);
        }
      } // res
    });
  }


  public loadDynamiceFormFields(): void {
    //console.log(' loadDynamiceFormFields this.entityType', this.entityType);
    if (this.entityType === 'IND') {
      this.formFields = this.individualFormFields;
    } else if (this.entityType === 'ORG') {
      this.formFields = this.organizationFormFields;
    }
    //console.log(' loadDynamiceFormFields this.entityType', this.entityType);
    this._setForm(this.formFields);
  }

  public cancelStep(): void {
    this._clearFormValues();
    this._router.navigate([`/LoanSumamrys`]);
  }

  public viewLoan(): void {
    if (this.frmLoan.dirty || this.frmLoan.touched) {
      localStorage.setItem('LoanSumamrysaved', JSON.stringify({ saved: false }));
    }
    this._router.navigate([`/LoanSumamrys`]);
  }

  public saveLoan(): void {
    const entityType = this.frmLoan.get('entity_type').value;
    if (entityType === 'IND') {
      this.doValidateLoan('loanSummary');
    } else if (entityType === 'ORG') {
      this.doValidateLoan('c1');
    }
  }


  private _goToC1() {
    const c1EmitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c1',
      action: this.scheduleAction,
      transactionDetail: {
        transactionModel: {
          transactionId: this._transactionId,
          entityId: this._selectedEntityId
        }
      }
    };
    this.status.emit(c1EmitObj);
  }

  public onSaveLoan(nextScreen: string = null): void {
    if (nextScreen) {
      this.doValidateLoan(nextScreen);
    } else {
      this.saveLoan();
    }
  }

  private _goToLoanRepayment() {
    const loanRepaymentEmitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c_loan_payment',
      action: ScheduleActions.add,
      transactionDetail: {
        transactionModel: {
          transactionId: this._transactionId,
          entityId: this._selectedEntityId,
          entryScreenScheduleType: 'sched_c',
        }
      }
    };
    this.status.emit(loanRepaymentEmitObj);
  }

  private _goToEndorser(): void {
    const endorserEmitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c_en',
      action: ScheduleActions.add,
      transactionDetail: {
        transactionModel: {
          endorser: {
            back_ref_transaction_id: this._transactionId,
          },
          entityId: this._selectedEntityId,
          entryScreenScheduleType: 'sched_c',
          transaction_id: this._transactionId,
          c1Exists: this.c1ExistsFlag
        }
      }
    };
    this.status.emit(endorserEmitObj);
  }

  public _goToEndorserSummary(): void {
    const endorserEmitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c_es',
      action: ScheduleActions.add,
      transactionDetail: {
        transactionModel: {
          transactionId: this._transactionId,
          entityId: this._selectedEntityId
        }
      }
    };
    this.status.emit(endorserEmitObj);
  }

  public isFieldName(fieldName: string, nameString: string): boolean {
    return fieldName === nameString || fieldName === this._childFieldNamePrefix + nameString;
  }

  /**
   * Vaidates the form on submit.
   */
  public doValidateLoan(nextScreen: string) {
    if (this.frmLoan.valid) {
      const LoanObj: any = {};

      for (const field in this.frmLoan.controls) {
        if (
          field === 'last_name' ||
          field === 'first_name' ||
          this.isFieldName(field, 'cmte_id') ||
          this.isFieldName(field, 'cmte_name') ||
          this.isFieldName(field, 'entity_name')
        ) {
          // if (this._selectedEntity) {
          // If the typeahead was used to load the entity into the form,
          // we don't allow users to make changes to the entity. Non-Typeahead
          // field (address, middle name, etc) are reset onKeyup.  Typeahead
          // fields must be reset here.  This is a known UI design issue with the
          // typeahead and not being able to disable fields because of add functionality.
          // We are tolerating this limitation where the user may change the last or
          // first name, it will reflect the change in the UI but won't be save to API.
          // LoanObj[field] = this._selectedEntity[field];
          // } else {
          // TODO Possible defect with typeahead setting field as the entity object
          // rather than the string defined by the inputFormatter();
          // If an object is received, find the value on the object by fields type
          // otherwise use the string value.  This is not desired and this patch
          // should be removed if the issue is resolved.
          const typeAheadField = this.frmLoan.get(field).value;
          if (typeAheadField && typeof typeAheadField !== 'string') {
            LoanObj[field] = typeAheadField[field];
          } else {
            LoanObj[field] = typeAheadField;
          }
          // }
        } else if (field === 'loan_amount_original' || field === 'loan_payment_to_date' || field === 'loan_balance') {
          let amount = LoanObj[field] = this.frmLoan.get(field);
          if (amount.value) {
            LoanObj[field] = amount.value.replace(/,/g, ``);
          }
        }
        else {
          LoanObj[field] = this.frmLoan.get(field).value;
        }
        //also add transactionId if available (edit route)
        if (this.scheduleAction === ScheduleActions.edit && this.transactionDetail) {
          if (this.transactionDetail.transaction_id) {
            LoanObj['transaction_id'] = this.transactionDetail.transaction_id;
          }
          //in some instances, transaction_id is being passed as 'transactionId'
          //TODO - need to combine/standardize the attribute names.
          else if (this.transactionDetail.transactionId) {
            LoanObj['transaction_id'] = this.transactionDetail.transactionId;
          }
        }
      }

      // If entity ID exist, the transaction will be added to the existing entity by the API
      // Otherwise it will create a new Entity.
      if (this._selectedEntity) {
        LoanObj.entity_id = this._selectedEntity.entity_id;
      }
      // LoanObj.entity_type = this.entityType;
      LoanObj['is_loan_secured'] = this.frmLoan.get('secured').value;
      //console.log('LoanObj =', JSON.stringify(LoanObj));

      localStorage.setItem('LoanObj', JSON.stringify(LoanObj));
      
      this._loansService
        .saveSched_C(this.scheduleAction, this._transactionTypeIdentifier, LoanObj.entity_type, this.reportId)
        .subscribe(res => {
          if (res) {

            this.updateThirdNavAmounts(res);
            //console.log('_LoansService.saveContact res', res);
            this.frmLoan.reset();
            this._selectedEntity = null;
            localStorage.removeItem(LoanObj);
            localStorage.setItem('Loansaved', JSON.stringify({ saved: true }));
            this._clearFormValues();
            this._transactionId = res.transaction_id;
            this._selectedEntityId = res.entity_id;
            if (nextScreen === 'loanSummary') {
              this._gotoSummary();
            } else if (nextScreen === 'loanRepayment') {
              this._goToLoanRepayment();
            } else if (nextScreen === 'c1') {
              this._goToC1();
            } else if (nextScreen === 'endorser') {
              this.c1ExistsFlag = this._loansService.c1Exists(this.currentLoanData);
              this._goToEndorser();
            }
          }
        });
    } else {
      this.frmLoan.markAsDirty();
      this.frmLoan.markAsTouched();
      localStorage.setItem('Loansaved', JSON.stringify({ saved: false }));
      window.scrollTo(0, 0);

      const invalid = [];
      const controls = this.frmLoan.controls;
      for (const name in controls) {
        if (controls[name].invalid) {
          invalid.push(name);
          //console.log('invalid form field on submit = ' + name);
        }
      }
    }
  }



  private updateThirdNavAmounts(res: any) {
    this._indReceiptService.getSchedule(this.formType, res).subscribe(resp => {
      const message: any = {
        formType: this.formType,
        totals: resp
      };
      this._messageService.sendMessage(message);
    });
  }

  private _gotoSummary() {
    const summaryEmitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c_ls',
      action: ScheduleActions.loanSummary
    };
    this.status.emit(summaryEmitObj);
  }


  public determineColClass(row: any, col: any) {
    if (col.name === 'election_other_description') {
      return 'col col-md-4';
    } else if (col.name === 'loan_intrest_rate') {
      return 'col col-md-4';
    } else if (col.name === 'secured') {
      return 'col col-md-4';
    }
    return row.colClassName;
  }

  public isToggleShow(col: any) {
    // don't show election description unless other is selected from dropdown.
    if (col.name === 'election_other_description') {
      let showOtherDesc = false;
      if (this.frmLoan.contains('election_code')) {
        if (this.frmLoan.get('election_code').value === 'O') {
          showOtherDesc = true;
        }
      }
      return showOtherDesc;
    }

    return true;
  }

  /**
   * Select elements width is set on the form-group level not the select element
   * as done with text and date fields.
   */
  public setSelectTypeWidth(col: any) {
    if (col.type === 'select') {
      return col.width;
    }
    return null;
  }

  private _prePopulateFormForEdit(transactionDetail: any) {

    const reportId = this._receiptService.getReportIdFromStorage(this.formType);
    this._loansService.getDataSchedule(reportId, transactionDetail.transaction_id).subscribe((res: any) => {
      //console.log();
      if (!res) {
        return;
      }
      let loanData = null;
      if (Array.isArray(res)) {
        if (res.length > 0) {
          loanData = res[0];
          this.currentLoanData = loanData;
        }
      }
      if (!loanData) {
        return;
      }

      let entityType = null;
      this._selectedEntity = { entity_id: loanData.entity_id };

      //Based on if its loading flow or Entity Type being changed from "IND" to "ORG" or vice-versa
      //entity type would be selected either from curent res data or from the ng-select value
      //If its through ng-select change event, this.typeChangeEventOccured would have been set to true
      if (this.typeChangeEventOccured) {
        entityType = this.entityType;
        this.typeChangeEventOccured = false; //reset back to false for next time
      }
      else {
        entityType = loanData.entity_type;
      }

      if (entityType === 'IND') {
        this.formFields = this.individualFormFields;
        this._setForm(this.individualFormFields);
        this._patchForm(loanData, 'last_name');
        this._patchForm(loanData, 'first_name');
        this._patchForm(loanData, 'middle_name');
        this._patchForm(loanData, 'prefix');
        this._patchForm(loanData, 'suffix');
      }

      if (entityType === 'ORG') {
        this.formFields = this.organizationFormFields;
        this._setForm(this.organizationFormFields);
        this._patchForm(loanData, 'entity_name');
      }

      this._patchForm(loanData, 'street_1');
      this._patchForm(loanData, 'street_2');
      this._patchForm(loanData, 'state');
      this._patchForm(loanData, 'city');
      this._patchForm(loanData, 'zip_code');



      this._patchForm(loanData, 'employer');
      this._patchForm(loanData, 'occupation');
      this._patchForm(loanData, 'election_code');
      this._patchForm(loanData, 'election_other_description');
      this._patchForm(loanData, 'loan_incurred_date');
      this._patchForm(loanData, 'memo_text');
      let element : any = document.getElementById('loan_due_date');
      if(loanData.loan_due_date){
        this.setInputType(loanData, element);
        this._patchForm(loanData, 'loan_due_date');
      }
      this._patchForm(loanData, 'loan_intrest_rate');
      this._patchForm(loanData, 'secured', 'is_loan_secured');

      this.frmLoan.patchValue({ loan_amount_original: this._decimalPipe.transform(loanData.loan_amount_original, '.2-2') })
      this.frmLoan.patchValue({ loan_payment_to_date: this._decimalPipe.transform(loanData.loan_payment_to_date, '.2-2') })
      this.frmLoan.patchValue({ loan_balance: this._decimalPipe.transform(loanData.loan_balance, '.2-2') })

      this.frmLoan.controls['loan_incurred_date'].disable();

      this.frmLoan.patchValue({ entity_type: entityType }, { onlySelf: true });
      this._selectedEntity.entity_type = entityType;
    });
  }

  private setInputType(loanData: any, element: any) {
    let temp = new Date(loanData.loan_due_date);
    if (isNaN(temp.getTime())) {
      if (element) {
        element.type = "text";
      }
    }
    else {
      if (element) {
        element.type = "date";
      }
    }
  }

  /**
   * API names from the GET differ from the POST / firm field names.  They
   * need to be mapped here.  TODO Have the API use the same names in GET/POST/PUT.
   * If no apiFieldName provided, it will assume to the formFieldName.
   */
  private _patchForm(res: any, formFieldName: string, apiFieldName?: string, ) {
    if (!formFieldName || !res) {
      return;
    }
    apiFieldName = !apiFieldName ? formFieldName : apiFieldName;
    if (res.hasOwnProperty(apiFieldName)) {
      const patch = {};
      patch[formFieldName] = res[apiFieldName];
      this.frmLoan.patchValue(patch, { onlySelf: true });
    }
  }

  private _clearFormValues(): void {
    if (this.frmLoan) {
      this.frmLoan.reset();
      this._selectedEntity = null;
      this._setEntityTypeDefault();
    }
  }

  /**
   * Determine if fields is read only.  If it should
   * be read only return true else null.  Null will
   * remove HTML attribute readonly whereas setting it to
   * false will not remove readonly from DOM and fields remain in readonly.
   */
  public isFieldReadOnly(col: any) {
    if (col.type === 'text' && col.isReadonly) {
      return true;
    }
    return null;
  }

  public handleOnBlurEvent($event: any, col: any) {
    if (this.isFieldName(col.name, 'loan_amount_original')) {
      this._formatAmount($event, col.name, col.validation.dollarAmountNegative);
    }
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
    this.frmLoan.patchValue(patch, { onlySelf: true });
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

  /**
 * Navigate to the Transactions.
 */
  public viewTransactions(): void {

    // TODO Do we need to add support for cloning as with AbstractSchedule?

    this._clearFormValues();
    let reportId = this._receiptService.getReportIdFromStorage(this.formType);
    //console.log('reportId', reportId);

    if (!reportId) {
      reportId = '0';
    }
    localStorage.setItem(`form_${this.formType}_view_transaction_screen`, 'Yes');
    localStorage.setItem('Transaction_Table_Screen', 'Yes');
    this._transactionsMessageService.sendLoadTransactionsMessage(reportId);

    // TODO when should editMode be true/false?
    this._router.navigate([`/forms/form/${this.formType}`], {
      queryParams: {
        step: 'transactions', reportId: reportId, edit: true,
        transactionCategory: this._transactionCategory
      }
    });
  }

}
