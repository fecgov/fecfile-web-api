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
} from '@angular/core';
import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { FormBuilder, FormGroup, FormControl, NgForm, Validators } from '@angular/forms';
import { NgbTooltipConfig, NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../environments/environment';
import { FormsService } from '../../shared/services/FormsService/forms.service';
import { UtilService } from '../../shared/utils/util.service';
import { MessageService } from '../../shared/services/MessageService/message.service';
import { LoanService } from '../sched-c/service/loan.service';
import { f3xTransactionTypes } from '../../shared/interfaces/FormsService/FormsService';
import { alphaNumeric } from '../../shared/utils/forms/validation/alpha-numeric.validator';
import { floatingPoint } from '../../shared/utils/forms/validation/floating-point.validator';
import { ReportTypeService } from '../../forms/form-3x/report-type/report-type.service';
import { Observable, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { LoanMessageService } from '../sched-c/service/loan-message.service';
import { LoanModel } from '../sched-c/model/loan.model';
//import { IndividualReceiptService } from '../../forms/form-3x/individual-receipt/individual-receipt.service';

export enum ActiveView {
  Loans = 'Loans',
  recycleBin = 'recycleBin',
  edit = 'edit'
}

export enum LoansActions {
  add = 'add',
  edit = 'edit'
}

@Component({
  selector: 'app-sched-c-loans',
  templateUrl: './loan.component.html',
  styleUrls: ['./loan.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe],
  encapsulation: ViewEncapsulation.None
})
export class LoanComponent implements OnInit, OnDestroy {
  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() selectedOptions: any = {};
  @Input() formOptionsVisible: boolean = false;
  @Input() transactionTypeText = '';
  @Input() transactionType = '';
  //@Input() scheduleAction: LoansActions = null;
  @Input() scheduleAction: LoansActions = LoansActions.add;

  /**
   * Subscription for pre-populating the form for view or edit.
   */
  private _populateFormSubscription: Subscription;
  private _loadFormFieldsSubscription: Subscription;

  public checkBoxVal: boolean = false;
  public frmLoan: FormGroup;
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
  public electionTypesSelected: any =[];
  public electionTypes: any =[];
  public secured: any =[];
  
  public entityType: string = 'IND';

  private _formType: string = '';
  private _transactionTypePrevious: string = null;
  private _contributionAggregateValue = 0.0;
  private _selectedEntity: any;
  private _contributionAmountMax: number;
  //private entityType: string = 'IND';
  private readonly _childFieldNamePrefix = 'child*';
  private _loanToEdit: LoanModel;
  private _loading: boolean = false;
  private _selectedChangeWarn: any;
  private _transactionTypeIdentifier= '';

  constructor(
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _LoansService: LoanService,
    private _config: NgbTooltipConfig,
    private _router: Router,
    private _utilService: UtilService,
    private _messageService: MessageService,
    private _decimalPipe: DecimalPipe,
    private _typeaheadService: TypeaheadService,
    private _dialogService: DialogService,
    private _LoanSumamrysMessageService: LoanMessageService,
    private _formsService: FormsService,
    private _receiptService: ReportTypeService,
    private _activatedRoute: ActivatedRoute
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';

    this._populateFormSubscription = this._LoanSumamrysMessageService.getPopulateFormMessage().subscribe(message => {
      this.populateFormForEditOrView(message);
      //this.getFormFields();
    });

    this._loadFormFieldsSubscription = this._LoanSumamrysMessageService.getLoadFormFieldsMessage().subscribe(message => {
      //this.getFormFields();
    });
  }

  ngOnInit(): void {
    this._selectedEntity = null;
    this._loanToEdit = null;
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    //this._transactionTypeIdentifier = this._activatedRoute.snapshot.paramMap.get('transactionTypeIdentifier');
    this._transactionTypeIdentifier= 'LOANS_OWED_BY_CMTE';

    console.log("this._transactionTypeIdentifier",  this._transactionTypeIdentifier)
    /*localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify({ saved: true }));
    localStorage.setItem('Receipts_Entry_Screen', 'Yes');*/
    
    //localStorage.removeItem('LoanSumamrysaved');
    
    this._messageService.clearMessage();

    /*this._reportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));

    if (this._reportType === null || typeof this._reportType === 'undefined') {
      this._reportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type_backup`));
    }*/

    this.getFormFields();

    this.entityType = 'IND';
    //this.loadDynamiceFormFields();
    //this.formFields = this.individualFormFields;
    //console.log(" this.formFields",  this.formFields);

    //this._setForm(this.formFields);
    this.frmLoan = this._fb.group({});
    if (this.selectedOptions) {
      if (this.selectedOptions.length >= 1) {
        this.formVisible = true;
      }
    }
  }

  public ngDoCheck(): void {}

  public ngOnDestroy(): void {
    this._messageService.clearMessage();
    this._populateFormSubscription.unsubscribe();
    //localStorage.removeItem('LoanSumamrysaved');
  }

  public debug(obj: any): void {
    console.log('obj: ', obj);
  }

  /**
   * Generates the dynamic form after all the form fields are retrived.
   *
   * @param      {Array}  fields  The fields
   */
  /*private _setForm(fields: any): void {
    const formGroup: any = [];
    fields.forEach(el => {
      if (el.hasOwnProperty('cols')) {
        el.cols.forEach(e => {
          formGroup[e.name] = new FormControl(e.value || null, this._mapValidators(e.validation, e.name));
        });
      }
    });

    this.frmLoan = new FormGroup(formGroup);

    // get form data API is passing X for memo code value.
    // Set it to null here until it is checked by user where it will be set to X.
    //this.frmLoan.controls['memo_code'].setValue(null);
  }*/

  private _setForm(fields: any): void {
    const formGroup: any = [];
    console.log('_setForm fields ', fields);
    fields.forEach(el => {
      if (el.hasOwnProperty('cols')) {
        el.cols.forEach(e => {
          formGroup[e.name] = new FormControl(e.value || null, this._mapValidators(e.validation, e.name));
        });
      }
    });

    this.frmLoan = new FormGroup(formGroup);

    // SET THE DEFAULT HERE
    if (this.frmLoan.get('entity_type')) {
      const entityTypeVal = this.frmLoan.get('entity_type').value;
      if (!entityTypeVal) {
        this.frmLoan.patchValue({ entity_type: this.entityType }, { onlySelf: true });
      }
    }

    // get form data API is passing X for memo code value.
    // Set it to null here until it is checked by user where it will be set to X.
    //this.frmLoan.controls['memo_code'].setValue(null);
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

  private formatAmountForAPI(contributionAmount): string {
   /*  // default to 0 when no value
    contributionAmount = contributionAmount ? contributionAmount : '0';
    // remove commas
    contributionAmount = contributionAmount.replace(/,/g, ``);
    // determine if negative, truncate if > max
    contributionAmount = this.transformAmount(contributionAmount, this._contributionAmountMax);
    return contributionAmount; */
    return "";
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

  /**
   * Gets the transaction type.
   */
  private _getTransactionType(): void {
   /*  const transactionType: any = JSON.parse(localStorage.getItem(`form_${this._formType}_transaction_type`));

    if (typeof transactionType === 'object') {
      if (transactionType !== null) {
        if (transactionType.hasOwnProperty('mainTransactionTypeValue')) {
          this._transactionType = transactionType.mainTransactionTypeValue;
        }
      }
    }

    if (this.transactionType) {
      if (this.transactionType !== this._transactionTypePrevious) {
        this._transactionTypePrevious = this.transactionType;
        // reload dynamic form fields
        this.getFormFields();
      }
    } */
  }

  public handleFormFieldKeyup($event: any, col: any) {
    /*if (!col) {
      return;
    }
    if (!col.name) {
      return;
    }
    if (
      col.name === 'middle_name' ||
      col.name === 'prefix' ||
      col.name === 'suffix' ||
      col.name === 'street_1' ||
      col.name === 'street_2' ||
      col.name === 'city' ||
      col.name === 'state' ||
      col.name === 'zip_code' ||
      col.name === 'employer' ||
      col.name === 'occupation'
    ) {
      if (this._selectedEntity) {
        this.frmLoan.patchValue({ [col.name]: this._selectedEntity[col.name] }, { onlySelf: true });
        //this.showWarn(col.text);
        this.showWarn(col.text, col.name);
      }
    } else {
      return null;
    }*/
  }

  /**
   * Show a warning indicating fields may not be changed for entities loaded from the database.
   *
   * @param fieldLabel Field Label to show in the message
   */
  /*private showWarn(fieldLabel: string) {
    const message =
      `Changes to ${fieldLabel} can't be edited when a Contributor is` +
      ` selected from the dropdwon.  Go to the Loan page to edit a Contributor.`;

    this._dialogService.confirm(message, ConfirmModalComponent, 'Caution!', false).then(res => {});
  }*/

  /**
   * Updates vaprivate _memoCode variable.
   *
   * @param      {Object}  e      The event object.
   */
  /*public memoCodeChange(e): void {
    const { checked } = e.target;

    if (checked) {
      this.memoCode = checked;
      this.frmLoan.controls['memo_code'].setValue(this._memoCodeValue);
      this.frmLoan.controls['contribution_date'].setValidators([Validators.required]);

      this.frmLoan.controls['contribution_date'].updateValueAndValidity();
    } else {
      this._validateContributionDate();
      this.memoCode = checked;
      this.frmLoan.controls['memo_code'].setValue(null);
      this.frmLoan.controls['contribution_date'].setValidators([
        contributionDate(this.cvgStartDate, this.cvgEndDate),
        Validators.required
      ]);

      this.frmLoan.controls['contribution_date'].updateValueAndValidity();
    }
  }*/

  /**
   * State select options are formatted " AK - Alaska ".  Once selected
   * the input field should display on the state code and the API must receive
   * only the state code.  When an optin is selected, the $ngOptionLabel
   * is received here having the state code - name format.  Parse it
   * for the state code.  This should be modified if possible.  Look into
   * options for ng-select and ng-option.
   *
   * NOTE: If the format of the option changes in the html template, the parsing
   * logic will most likely need to change here.
   *
   * @param stateOption the state selected in the dropdown.
   */
  
   /*public handleStateChange(stateOption: any, col: any) {
    console.log("handleStateChange stateOption", stateOption);
    if (this._selectedEntity) {
      //this.showWarn(col.text);
      this.frmLoan.patchValue({ state: this._selectedEntity.state }, { onlySelf: true });
    } else {
      let stateCode = null;
      if (stateOption.$ngOptionLabel) {
        stateCode = stateOption.$ngOptionLabel;
        if (stateCode) {
          stateCode = stateCode.trim();
          if (stateCode.length > 1) {
            stateCode = stateCode.substring(0, 2);
            console.log(" handleStateChange stateCode", stateCode);
          }
        }
      }
      
      this.frmLoan.patchValue({ state: stateCode }, { onlySelf: true });
    }
  }*/


  /*public handleStateChange(stateOption: any, col: any) {
   
    if (this._selectedEntity) {
      // this.showWarn(col.text);
      this.frmLoan.patchValue({ state: this._selectedEntity.state }, { onlySelf: true });
    } else {
      this.frmLoan.patchValue({ state: stateOption.code }, { onlySelf: true });
    }
  } commented on 10052019*/


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

    //const message = `Please note that if you update contact information it will be updated in the Loan file.`;
    //this._dialogService.confirm(message, ConfirmModalComponent, 'Warning!', false).then(res => {});

    this._selectedChangeWarn[name] = name;
  }

  public handleCandOfficeChange(candOfficeOption: any, col: any) {

    if (this._selectedEntity) {
      //this.showWarn(col.text);
      this.frmLoan.patchValue({ candOffice: this._selectedEntity.candOffice}, { onlySelf: true });
    } else {
      let officeCode = null;
      if (candOfficeOption.$ngOptionLabel) {
        officeCode = candOfficeOption.$ngOptionLabel;
        if (officeCode) {
          officeCode = officeCode.trim();
          if (officeCode.length > 1) {
            officeCode = officeCode.substring(0, 1);
          }
        }
      }
      
      this.frmLoan.patchValue({ candOffice: officeCode }, { onlySelf: true });
    }
  }
  
  public handleOfficeStateChange(officeStateOption: any, col: any) {

    if (this._selectedEntity) {
      //this.showWarn(col.text);
      this.frmLoan.patchValue({ candOfficeState: this._selectedEntity.candOfficeState}, { onlySelf: true });
    } else {
      let officeStateCode = null;
      if (officeStateOption.$ngOptionLabel) {
        officeStateCode = officeStateOption.$ngOptionLabel;
        if (officeStateCode) {
          officeStateCode = officeStateCode.trim();
          if (officeStateCode.length > 1) {
            officeStateCode = officeStateCode.substring(0, 2);
          }
        }
      }
      
      this.frmLoan.patchValue({ candOfficeState: officeStateCode }, { onlySelf: true });
    }
  }

  /*public handleTypeChange(entityOption: any, col: any) {
    console.log("handleTypeChange entityOption", entityOption);
    if (this._selectedEntity) {
      //this.showWarn(col.text);
      this.frmLoan.patchValue({ entityType: this._selectedEntity.entityType }, { onlySelf: true });
    } else {
      let entityCode = null;
      if (entityOption.$ngOptionLabel) {
        entityCode = entityOption.$ngOptionLabel;
        if (entityCode) {
          entityCode = entityCode.trim();
          if (entityCode.length > 1) {
            entityCode = entityCode.substring(0, 3 );
            console.log(" handleTypeChange entityCode", entityCode);
            this.frmLoan.patchValue({ entityType: entityCode }, { onlySelf: true });
            this.entityType = entityCode;
            this.loadDynamiceFormFields();
          }
        }
      }
     
    }
  }*/

  public handleTypeChange(entityOption: any, col: any) {
    console.log(" handleTypeChange entityOption", entityOption);
    this.entityType = entityOption.code;
    if (this._selectedEntity) {
      // this.showWarn(col.text);
      this.frmLoan.patchValue({ entity_type: this._selectedEntity.entity_type }, { onlySelf: true });
    } else {
      this.loadDynamiceFormFields();
      this.frmLoan.patchValue({ entity_type: entityOption.code }, { onlySelf: true });
    }
  }

  public handleEntityTypeChange(item: any, col: any, entityType: any) {
    // Set the selectedEntityType for the toggle method to check.
    for (const entityTypeObj of this.entityTypes) {
      if (entityTypeObj.entityType === item.entityType) {
        entityTypeObj.selected = true;
        //this.selectedEntityType = entityTypeObj;
        this.entityType = entityTypeObj;
      } else {
        entityTypeObj.selected = false;
      }
    }
  }
  public handleloansecuredChange(entityOption: any, col: any) {
    console.log(" handleloansecuredChange entityOption", entityOption);
    //this.entityType = entityOption.code;
    if (this._selectedEntity) {
      // this.showWarn(col.text);
      this.frmLoan.patchValue({ is_loan_secured: this._selectedEntity.is_loan_secured }, { onlySelf: true });
    } else {
      //this.loadDynamiceFormFields();
      this.frmLoan.patchValue({ is_loan_secured: entityOption.code }, { onlySelf: true });
    }
  }
  

  public electionTypeChanged(entityOption: any, col: any) {
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
   * @deprecated
   */
  public receiveTypeaheadData(loan: any, fieldName: string): void {

    if (fieldName === 'first_name') {
      this.frmLoan.patchValue({ last_name: loan.last_name }, { onlySelf: true });
      this.frmLoan.controls['last_name'].setValue({ last_name: loan.last_name }, { onlySelf: true });
    }

    if (fieldName === 'last_name') {
      this.frmLoan.patchValue({ first_name: loan.first_name }, { onlySelf: true });
      this.frmLoan.controls['first_name'].setValue({ first_name: loan.first_name }, { onlySelf: true });
    }

    this.frmLoan.patchValue({ middle_name: loan.middle_name }, { onlySelf: true });
    this.frmLoan.patchValue({ prefix: loan.prefix }, { onlySelf: true });
    this.frmLoan.patchValue({ suffix: loan.suffix }, { onlySelf: true });
    this.frmLoan.patchValue({ street_1: loan.street_1 }, { onlySelf: true });
    this.frmLoan.patchValue({ street_2: loan.street_2 }, { onlySelf: true });
    this.frmLoan.patchValue({ city: loan.city }, { onlySelf: true });
    this.frmLoan.patchValue({ state: loan.state }, { onlySelf: true });
    this.frmLoan.patchValue({ entity_type: loan.entity_type }, { onlySelf: true });
    this.frmLoan.patchValue({ zip_code: loan.zip_code }, { onlySelf: true });
   
    this.frmLoan.patchValue({ loan_amount_original: loan.loan_amount_original }, { onlySelf: true });
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
    this.frmLoan.patchValue({ memo_text: loan.memo_text }, { onlySelf: true });

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
   * Format an entity to display in the Committee ID type ahead.
   *
   * @param result formatted item in the typeahead list
   */
  public formatTypeaheadCommitteeId(result: any) {
    const street1 = result.street_1 ? result.street_1.trim() : '';
    const street2 = result.street_2 ? result.street_2.trim() : '';
    const name = result.cmte_id ? result.cmte_id.trim() : '';

    return `${name}, ${street1}, ${street2}`;
  }

  /**
   * Format an entity to display in the Candidate ID type ahead.
   *
   * @param result formatted item in the typeahead list
   */
  public formatTypeaheadCandidateId(result: any) {
    const candidateId = result.beneficiary_cand_id ? result.beneficiary_cand_id.trim() : '';
    const lastName = result.cand_last_name ? result.cand_last_name.trim() : '';
    const firstName = result.cand_first_name ? result.cand_first_name.trim() : '';
    let office = result.cand_office ? result.cand_office.toUpperCase().trim() : '';
    if (office) {
      if (office === 'P') {
        office = 'Presidential';
      } else if (office === 'S') {
        office = 'Senate';
      } else if (office === 'H') {
        office = 'House';
      }
    }
    const officeState = result.cand_office_state ? result.cand_office_state.trim() : '';
    const officeDistrict = result.cand_office_district ? result.cand_office_district.trim() : '';

    return `${candidateId}, ${lastName}, ${firstName}, ${office}, ${officeState}, ${officeDistrict}`;
  }

  /**
   * Format an entity to display in the Committee Name type ahead.
   *
   * @param result formatted item in the typeahead list
   */
  public formatTypeaheadCommitteeName(result: any) {
    const street1 = result.street_1 ? result.street_1.trim() : '';
    const street2 = result.street_2 ? result.street_2.trim() : '';
    const name = result.cmte_id ? result.cmte_name.trim() : '';

    return `${name}, ${street1}, ${street2}`;
  }

  /**
   * Format an entity to display in the Candidate type ahead field.
   *
   * @param result formatted item in the typeahead list
   */
  public formatTypeaheadCandidate(result: any) {
    const lastName = result.cand_last_name ? result.cand_last_name.trim() : '';
    const firstName = result.cand_first_name ? result.cand_first_name.trim() : '';
    let office = result.cand_office ? result.cand_office.toUpperCase().trim() : '';
    if (office) {
      if (office === 'P') {
        office = 'Presidential';
      } else if (office === 'S') {
        office = 'Senate';
      } else if (office === 'H') {
        office = 'House';
      }
    }
    const officeState = result.cand_office_state ? result.cand_office_state.trim() : '';
    const officeDistrict = result.cand_office_district ? result.cand_office_district.trim() : '';

    return `${lastName}, ${firstName}, ${office}, ${officeState}, ${officeDistrict}`;
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
   
    this.frmLoan.patchValue({ loan_amount_original: loan.loan_amount_original }, { onlySelf: true });
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
    this.frmLoan.patchValue({ memo_text: loan.memo_text }, { onlySelf: true });

  }

  public handleSelectedItem($event: NgbTypeaheadSelectItemEvent) {
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
   
    this.frmLoan.patchValue({ loan_amount_original: loan.loan_amount_original }, { onlySelf: true });
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
    this.frmLoan.patchValue({ memo_text: loan.memo_text }, { onlySelf: true });


    //this.frmLoan.patchValue({ phoneNumber: loan.phoneNumber }, { onlySelf: true });
    //this.frmLoan.patchValue({ candOffice: loan.candOffice }, { onlySelf: true });
    //this.frmLoan.patchValue({ candOfficeState: loan.candOfficeState }, { onlySelf: true });
    //this.frmLoan.patchValue({ candOfficeDistrict: loan.candOfficeDistrict }, { onlySelf: true });


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

    //const reportId = this.getReportIdFromStorage();
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
          return this._typeaheadService.getContacts(searchText, 'last_name');
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
          return this._typeaheadService.getContacts(searchText, 'first_name');
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
          return this._typeaheadService.getContacts(searchText, 'entity_name');
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
   * Search for entities when organization/entity_name input value changes.
   */
  searchCommitteeId = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        const searchTextUpper = searchText.toUpperCase();

        if (
          searchTextUpper === 'C' ||
          searchTextUpper === 'C0' ||
          searchTextUpper === 'C00' ||
          searchTextUpper === 'C000'
        ) {
          return Observable.of([]);
        }

        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'cmte_id');
        } else {
          return Observable.of([]);
        }
      })
    );

  /**
   * Search for entities when Candidate ID input value changes.
   */
  searchCandidateId = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText.length < 3) {
          return Observable.of([]);
        } else {
          const searchTextUpper = searchText.toUpperCase();
          return this._typeaheadService.getContacts(searchTextUpper, 'cand_id');
        }
      })
    )


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

  /**
   * format the value to display in the input field once selected from the typeahead.
   *
   * For some reason this gets called for all typeahead fields despite the binding in the
   * template to the committee ID field.  In these cases return x to retain the value in the
   * input for the other typeahead fields.
   */
  formatterCommitteeId = (x: { cmte_id: string }) => {
    if (typeof x !== 'string') {
      return x.cmte_id;
    } else {
      return x;
    }
  };

  /**
   * format the value to display in the input field once selected from the typeahead.
   *
   * For some reason this gets called for all typeahead fields despite the binding in the
   * template to the Candidate ID field.  In these cases return x to retain the value in the
   * input for the other typeahead fields.
   */
  formatterCandidateId = (x: { beneficiary_cand_id: string }) => {
    if (typeof x !== 'string') {
      return x.beneficiary_cand_id;
    } else {
      return x;
    }
  }

  /**
   * format the value to display in the input field once selected from the typeahead.
   *
   * For some reason this gets called for all typeahead fields despite the binding in the
   * template to the committee name field.  In these cases return x to retain the value in the
   * input for the other typeahead fields.
   */
  formatterCommitteeName = (x: { cmte_name: string }) => {
    if (typeof x !== 'string') {
      return x.cmte_name;
    } else {
      return x;
    }
  };

  private getFormFields(): void {
    this._LoansService.get_sched_c_loan_dynamic_forms_fields().subscribe(res => {
      if (res) {
        console.log('getFormFields res =', res);
        if (res.hasOwnProperty('data')) {
          if (typeof res.data === 'object') {
            /*if (res.data.hasOwnProperty('formFields')) {
                  if (Array.isArray(res.data.formFields)) {
                    this.formFields = res.data.formFields;

                    this._setForm(this.formFields);
                  }
                }*/
            if (res.data.hasOwnProperty('individualFormFields')) {
              if (Array.isArray(res.data.individualFormFields)) {
                this.individualFormFields = res.data.individualFormFields;
                this.formFields = res.data.individualFormFields;
                console.log("this.individualFormFields =", this.individualFormFields);
                this._setForm(res.data.individualFormFields);
              }
            }

            /*if (res.data.hasOwnProperty('committeeFormFields')) {
              if (Array.isArray(res.data.committeeFormFields)) {
                this.committeeFormFields = res.data.committeeFormFields;
              }
            }*/

            if (res.data.hasOwnProperty('OrganizationFormFields')) {
              if (Array.isArray(res.data.OrganizationFormFields)) {
                this.organizationFormFields = res.data.OrganizationFormFields;
                console.log("this.organizationFormFields =", this.organizationFormFields);
              }
            }

            /*if (res.data.hasOwnProperty('candidateFormFields')) {
              if (Array.isArray(res.data.candidateFormFields)) {
                this.candidateFormFields = res.data.candidateFormFields;
              }
            }*/

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

            /*if (res.data.hasOwnProperty('prefixes')) {
              if (Array.isArray(res.data.prefixes)) {
                this.prefixes = res.data.prefixes;
              }
            }

            if (res.data.hasOwnProperty('suffixes')) {
              if (Array.isArray(res.data.suffixes)) {
                this.suffixes = res.data.suffixes;
              }
            }*/

            if (res.data.hasOwnProperty('entityTypes')) {
              if (Array.isArray(res.data.entityTypes)) {
                this.entityTypes = res.data.entityTypes;
                console.log("this.entityTypes", this.entityTypes);
              }
            }

            if (res.data.hasOwnProperty('electionTypes')) {
              if (Array.isArray(res.data.electionTypes)) {
                this.electionTypes = res.data.electionTypes;
                console.log("this.electionTypes", this.electionTypes);
              }
            }
            
            if (res.data.hasOwnProperty('secured')) {
              if (Array.isArray(res.data.secured)) {
                this.secured = res.data.secured;
                console.log("this.secured", this.secured);
              }
            }

            

            /*if (res.data.hasOwnProperty('officeSought')) {
              if (Array.isArray(res.data.officeSought)) {
                this.officeSought = res.data.officeSought;
              }
            }

            if (res.data.hasOwnProperty('officeState')) {
              if (Array.isArray(res.data.officeState)) {
                this.officeState = res.data.officeState;
              }
            }*/

            if (res.data.hasOwnProperty('titles')) {
              if (Array.isArray(res.data.titles)) {
                this.titles = res.data.titles;
              }
            }

            this._loading = false;
          } // typeof res.data
        } // res.hasOwnProperty('data')
      } // res
    });
  }

  private populateFormForEditOrView(editOrView: any) {
    // The action here is the same as the this.scheduleAction
    // using the field from the message in case there is a race condition with Input().
    if (editOrView !== null) {
      if (editOrView.transactionModel) {
        const formData: LoanModel = editOrView.transactionModel;

        this.hiddenFields.forEach(el => {
          if (el.name === 'id') {
            el.value = formData.transaction_id;
          }
        });

        const nameArray = formData.name.split(',');
        const firstName = nameArray[1] ? nameArray[1] : null;
        const lastName = nameArray[0] ? nameArray[0] : null;
        const middleName = nameArray[2] ? nameArray[2] : null;
        const prefix = nameArray[3] ? nameArray[3] : null;
        const suffix = nameArray[4] ? nameArray[4] : null;

        this.frmLoan.patchValue({ first_name: firstName.trim() }, { onlySelf: true });
        this.frmLoan.patchValue({ last_name: lastName.trim() }, { onlySelf: true });
        this.frmLoan.patchValue({ middle_name: middleName.trim() }, { onlySelf: true });
        this.frmLoan.patchValue({ prefix: prefix.trim() }, { onlySelf: true });
        this.frmLoan.patchValue({ suffix: suffix.trim() }, { onlySelf: true });

        this.frmLoan.patchValue({ entity_type: formData.entity_type }, { onlySelf: true });
        this.frmLoan.patchValue({ street_1: formData.street1 }, { onlySelf: true });
        this.frmLoan.patchValue({ street_2: formData.street2 }, { onlySelf: true });
        this.frmLoan.patchValue({ city: formData.city }, { onlySelf: true });
        this.frmLoan.patchValue({ state: formData.state }, { onlySelf: true });
        this.frmLoan.patchValue({ zip_code: formData.zip }, { onlySelf: true });

        /*this.frmLoan.patchValue({ middle_name: loan.middle_name }, { onlySelf: true });
        this.frmLoan.patchValue({ prefix: loan.prefix }, { onlySelf: true });
        this.frmLoan.patchValue({ suffix: loan.suffix }, { onlySelf: true });
        this.frmLoan.patchValue({ street_1: loan.street_1 }, { onlySelf: true });
        this.frmLoan.patchValue({ street_2: loan.street_2 }, { onlySelf: true });
        this.frmLoan.patchValue({ city: loan.city }, { onlySelf: true });
        this.frmLoan.patchValue({ state: loan.state }, { onlySelf: true });
        this.frmLoan.patchValue({ entity_type: loan.entity_type }, { onlySelf: true });
        this.frmLoan.patchValue({ zip_code: loan.zip_code }, { onlySelf: true });
       
        this.frmLoan.patchValue({ loan_amount_original: loan.loan_amount_original }, { onlySelf: true });
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
        this.frmLoan.patchValue({ memo_text: loan.memo_text }, { onlySelf: true });*/
    
      }
    }
  }

  /*public selectTypeChange(e): void {
    this.entityType = e.target.value;
    this.loadDynamiceFormFields();
    console.log('selectTypeChange this.entityType = ', this.entityType);
  }*/

  public loadDynamiceFormFields(): void {
    console.log(" loadDynamiceFormFields this.entityType", this.entityType);
    if (this.entityType === 'IND') {
      this.formFields = this.individualFormFields;
    } else if (this.entityType === 'ORG') {
      this.formFields = this.organizationFormFields;
    }
    console.log(" loadDynamiceFormFields this.entityType", this.entityType);
    this._setForm(this.formFields);
  }

  public cancelStep(): void {
    this.frmLoan.reset();
    this._router.navigate([`/LoanSumamrys`]);
  }
  
  public viewLoan(): void {
    
    if (this.frmLoan.dirty || this.frmLoan.touched){
      localStorage.setItem('LoanSumamrysaved', JSON.stringify({ saved: false }));
    }
    this._router.navigate([`/LoanSumamrys`]);
  }

  public saveLoan(): void {
    if ( this.entityType === 'IND'){ 
      this.doValidateLoan();
      console.log("Accessing sched_c loans...");
      const addSubTransEmitObj: any = {
        form: {},
        direction: 'next',
        step: 'step_3',
        previousStep: 'step_2',
        scheduleType: 'sched_c',
        action: LoansActions.add
      };
      this.status.emit(addSubTransEmitObj);
      let reportId = this._receiptService.getReportIdFromStorage(this._formType);
      this._router.navigate([`/forms/form/${this._formType}`], {
              queryParams: { step: 'loansummary', reportId: reportId }
            });
     }else if(this.entityType === 'ORG'){
      const addSubTransEmitObj: any = {
        form: {},
        direction: 'next',
        step: 'step_3',
        previousStep: 'step_2',
        scheduleType: 'sched_c1',
        action: LoansActions.add
      };
      this.status.emit(addSubTransEmitObj);
      this._router.navigate([`/forms/form/${this._formType}`], {
        queryParams: { step: 'step_3' }
      });
     }
  }

  public loanRepayment(): void {
  }

  public AddLoanEndorser(): void {
    
  }
  
  public isFieldName(fieldName: string, nameString: string): boolean {
    return fieldName === nameString || fieldName === this._childFieldNamePrefix + nameString;
  }

  /**
   * Vaidates the form on submit.
   */
  public doValidateLoan() {
    console.log("doValidateLoan called");
    console.log("this.frmLoan.valid", this.frmLoan.valid);
    if (this.frmLoan.valid) {
      console.log("doValidateLoan loan valid");
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
        } else {
          LoanObj[field] = this.frmLoan.get(field).value;
        }
      }

      // There is a race condition with populating hiddenFields
      // and receiving transaction data to edit from the message service.
      // If editing, set transaction ID at this point to avoid race condition issue.
      /*if (this._loanToEdit) {
        this.hiddenFields.forEach((el: any) => {
          if (el.name === 'transaction_id') {
            el.value = this._loanToEdit.transaction_id;
          }
        });
      }

      this.hiddenFields.forEach(el => {
        LoanObj[el.name] = el.value;
      });*/

      // If entity ID exist, the transaction will be added to the existing entity by the API
      // Otherwise it will create a new Entity.
      if (this._selectedEntity) {
        LoanObj.entity_id = this._selectedEntity.entity_id;
      }
      LoanObj.entity_type = this.entityType;
      console.log("LoanObj =", JSON.stringify(LoanObj));

      localStorage.setItem('LoanObj', JSON.stringify(LoanObj));
      this._LoansService.saveSched_C(this.scheduleAction, this._transactionTypeIdentifier, this.entityType).subscribe(res => {
        if (res) {
          console.log('_LoansService.saveContact res', res);
          this._loanToEdit = null;
          this.frmLoan.reset();
          this._selectedEntity = null;
          localStorage.removeItem(LoanObj);
          /*if (callFrom === 'viewLoan') {
            this._router.navigate([`/LoanSumamrys`]);
          }*/
          localStorage.setItem('Loansaved', JSON.stringify({ saved: true }));
          //window.scrollTo(0, 0);
        }
      });
    } else {
      this.frmLoan.markAsDirty();
      this.frmLoan.markAsTouched();
      localStorage.setItem('Loansaved', JSON.stringify({ saved: false }));
      window.scrollTo(0, 0);
    }
  }

  /**
   * Determines ability for a person to leave a page with a form on it.
   *
   * @return     {boolean}  True if able to deactivate, False otherwise.
   */
  /*public async canDeactivate(): Promise<boolean> {
    if (this._formsService.HasUnsavedData('contact')) {
      let result: boolean = null;
      result = await this._dialogService
        .confirm('', ConfirmModalComponent)
        .then(res => {
          let val: boolean = null;

          if(res === 'okay') {
            val = true;
          } else if(res === 'cancel') {
            val = false;
          }

          return val;
        });

      return result;
    } else {
      return true;
  }
 }*/
}
