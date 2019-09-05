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
import { ContactsService } from '../service/contacts.service';
import { f3xTransactionTypes } from '../../shared/interfaces/FormsService/FormsService';
import { alphaNumeric } from '../../shared/utils/forms/validation/alpha-numeric.validator';
import { floatingPoint } from '../../shared/utils/forms/validation/floating-point.validator';
import { contributionDate } from '../../shared/utils/forms/validation/contribution-date.validator';
import { ReportTypeService } from '../../forms/form-3x/report-type/report-type.service';
import { Observable, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
//import { AddNewContactModel } from './model/add/new_contacts.model';
import { ContactsMessageService } from '../service/contacts-message.service';
import { ContactModel } from '../model/contacts.model';

export enum ContactActions {
  add = 'add',
  edit = 'edit'
}

@Component({
  selector: 'addnew_contacts.',
  templateUrl: './addnew_contacts.component.html',
  styleUrls: ['./addnew_contacts.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe],
  encapsulation: ViewEncapsulation.None
})
export class AddNewContactComponent implements OnInit, OnDestroy {
  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() selectedOptions: any = {};
  @Input() formOptionsVisible: boolean = false;
  @Input() transactionTypeText = '';
  @Input() transactionType = '';
  //@Input() scheduleAction: ContactActions = null;
  @Input() scheduleAction: ContactActions = ContactActions.add;

  /**
   * Subscription for pre-populating the form for view or edit.
   */
  private _populateFormSubscription: Subscription;
  private _loadFormFieldsSubscription: Subscription;

  public checkBoxVal: boolean = false;
  public cvgStartDate: string = null;
  public cvgEndDate: string = null;
  public frmContact: FormGroup;
  public formFields: any = [];
  public formVisible: boolean = false;
  public hiddenFields: any = [];
  public memoCode: boolean = false;
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
  private _reportType: any = null;
  private _types: any = [];
  private _transaction: any = {};
  private _transactionType: string = null;
  private _transactionTypePrevious: string = null;
  private _formSubmitted: boolean = false;
  private _contributionAggregateValue = 0.0;
  private _contributionAmount = '';
  private readonly _memoCodeValue: string = 'X';
  private _selectedEntity: any;
  private _contributionAmountMax: number;
  private _entityType: string = 'IND';
  private _loading: boolean =  true;
  private _selectedEntityChild: any;
  private _selectedChangeWarn: any;
  private _selectedChangeWarnChild: any;
  private readonly _childFieldNamePrefix = 'child*';
  private _contactToEdit: ContactModel;


  constructor(
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _formService: FormsService,
    private _contactsService: ContactsService,
    private _activatedRoute: ActivatedRoute,
    private _config: NgbTooltipConfig,
    private _router: Router,
    private _utilService: UtilService,
    private _messageService: MessageService,
    private _currencyPipe: CurrencyPipe,
    private _decimalPipe: DecimalPipe,
    private _reportTypeService: ReportTypeService,
    private _typeaheadService: TypeaheadService,
    private _dialogService: DialogService,
    private _contactsMessageService: ContactsMessageService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';

    this._populateFormSubscription = this._contactsMessageService.getPopulateFormMessage().subscribe(message => {
      this.populateFormForEditOrView(message);
      console.log(" Here Got form fieds...");
      this.getFormFields();
      });

    this._loadFormFieldsSubscription = this._contactsMessageService.getLoadFormFieldsMessage()
      .subscribe(message => {
        this.getFormFields();
        
    });   
 }

  ngOnInit(): void {
    this._selectedEntity = null;
    this._contributionAggregateValue = 0.0;
    this._contributionAmount = '';
    this._contactToEdit = null;
    /*this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify({ saved: true }));
    localStorage.setItem('Receipts_Entry_Screen', 'Yes');*/

    this._messageService.clearMessage();

    /*this._reportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));

    if (this._reportType === null || typeof this._reportType === 'undefined') {
      this._reportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type_backup`));
    }*/
   
    this.getFormFields();
    
    this._entityType = "IND";
    // this.loadDynamiceFormFields();
    this.formFields  =  this.individualFormFields;

    this.frmContact = this._fb.group({});
    if (this.selectedOptions) {
      if (this.selectedOptions.length >= 1) {
        this.formVisible = true;
      }
    }

 
  }

  ngDoCheck(): void {
  }
    

  ngOnDestroy(): void {
    this._messageService.clearMessage();
    this._populateFormSubscription.unsubscribe();
    localStorage.removeItem('contact_saved');
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
          /*if (e.name === 'contribution_amount') {
            if (e.validation) {
              this._contributionAmountMax = e.validation.max ? e.validation.max : 0;
            }
          }*/
        });
      }
    });

    this.frmContact = new FormGroup(formGroup);

    // get form data API is passing X for memo code value.
    // Set it to null here until it is checked by user where it will be set to X.
    //this.frmContact.controls['memo_code'].setValue(null);
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
   * Validates the contribution date selected.
   */
  private _validateContributionDate(): void {
    this._reportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));

    if (this._reportType !== null) {
      const cvgStartDate: string = this._reportType.cvgStartDate;
      const cvgEndDate: string = this._reportType.cvgEndDate;

      if (this.memoCode) {
        this.frmContact.controls['contribution_date'].setValidators([Validators.required]);

        this.frmContact.controls['contribution_date'].updateValueAndValidity();
      } else {
        if (this.frmContact.controls['contribution_date']) {
          this.frmContact.controls['contribution_date'].setValidators([
            contributionDate(cvgStartDate, cvgEndDate),
            Validators.required
          ]);

          this.frmContact.controls['contribution_date'].updateValueAndValidity();
        }
      }
    }

    if (this.frmContact) {
      if (this.frmContact.controls['contribution_amount']) {
        this.frmContact.controls['contribution_amount'].setValidators([floatingPoint(), Validators.required]);

        this.frmContact.controls['contribution_amount'].updateValueAndValidity();
      }

      if (this.frmContact.controls['contribution_aggregate']) {
        this.frmContact.controls['contribution_aggregate'].setValidators([floatingPoint()]);

        this.frmContact.controls['contribution_aggregate'].updateValueAndValidity();
      }
    }
  }

  /**
   * Updates the contribution aggregate field once contribution ammount is entered.
   *
   * @param      {Object}  e       The event object.
   */
  public contributionAmountChange(e: any): void {
    let contributionAmount: string = e.target.value;
    // default to 0 when no value
    contributionAmount = contributionAmount ? contributionAmount : '0';
    // remove commas
    contributionAmount = contributionAmount.replace(/,/g, ``);
    // determine if negative, truncate if > max
    contributionAmount = this.transformAmount(contributionAmount, this._contributionAmountMax);

    this._contributionAmount = contributionAmount;
    // this._contributionAmount = this.formatAmountForAPI(e.target.value)

    const contributionAggregate: string = String(this._contributionAggregateValue);

    const contributionAmountNum = parseFloat(contributionAmount);
    const aggregateTotal: number = contributionAmountNum + parseFloat(contributionAggregate);
    const aggregateValue: string = this._decimalPipe.transform(aggregateTotal, '.2-2');
    const amountValue: string = this._decimalPipe.transform(contributionAmountNum, '.2-2');

    this.frmContact.patchValue({ contribution_amount: amountValue }, { onlySelf: true });
    this.frmContact.patchValue({ contribution_aggregate: aggregateValue }, { onlySelf: true });
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
    // default to 0 when no value
    contributionAmount = contributionAmount ? contributionAmount : '0';
    // remove commas
    contributionAmount = contributionAmount.replace(/,/g, ``);
    // determine if negative, truncate if > max
    contributionAmount = this.transformAmount(contributionAmount, this._contributionAmountMax);
    return contributionAmount;
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
    const transactionType: any = JSON.parse(localStorage.getItem(`form_${this._formType}_transaction_type`));

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
    }
  }

  public handleFormFieldKeyup($event: any, col: any) {
  /*  if (!col) {
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
        this.frmContact.patchValue({ [col.name]: this._selectedEntity[col.name] }, { onlySelf: true });
        //this.showWarn(col.text);
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
  private showWarn(fieldLabel: string) {
    const message =
      `Changes to ${fieldLabel} can't be edited when a Contributor is` +
      ` selected from the dropdwon.  Go to the Contacts page to edit a Contributor.`;

    this._dialogService.confirm(message, ConfirmModalComponent, 'Caution!', false).then(res => {});
  }

  /**
   * Updates vaprivate _memoCode variable.
   *
   * @param      {Object}  e      The event object.
   */
  /*public memoCodeChange(e): void {
    const { checked } = e.target;

    if (checked) {
      this.memoCode = checked;
      this.frmContact.controls['memo_code'].setValue(this._memoCodeValue);
      this.frmContact.controls['contribution_date'].setValidators([Validators.required]);

      this.frmContact.controls['contribution_date'].updateValueAndValidity();
    } else {
      this._validateContributionDate();
      this.memoCode = checked;
      this.frmContact.controls['memo_code'].setValue(null);
      this.frmContact.controls['contribution_date'].setValidators([
        contributionDate(this.cvgStartDate, this.cvgEndDate),
        Validators.required
      ]);

      this.frmContact.controls['contribution_date'].updateValueAndValidity();
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
  public handleStateChange(stateOption: any, col: any) {
    if (this._selectedEntity) {
      //this.showWarn(col.text);
      this.frmContact.patchValue({ state: this._selectedEntity.state }, { onlySelf: true });
    } else {
      let stateCode = null;
      if (stateOption.$ngOptionLabel) {
        stateCode = stateOption.$ngOptionLabel;
        if (stateCode) {
          stateCode = stateCode.trim();
          if (stateCode.length > 1) {
            stateCode = stateCode.substring(0, 2);
          }
        }
      }
      this.frmContact.patchValue({ state: stateCode }, { onlySelf: true });
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
   * @deprecated
   */
  public receiveTypeaheadData(contact: any, fieldName: string): void {
    console.log('entity selected by typeahead is ' + contact);

    if (fieldName === 'first_name') {
      this.frmContact.patchValue({ last_name: contact.last_name }, { onlySelf: true });
      this.frmContact.controls['last_name'].setValue({ last_name: contact.last_name }, { onlySelf: true });
    }

    if (fieldName === 'last_name') {
      this.frmContact.patchValue({ first_name: contact.first_name }, { onlySelf: true });
      this.frmContact.controls['first_name'].setValue({ first_name: contact.first_name }, { onlySelf: true });
    }

    this.frmContact.patchValue({ middle_name: contact.middle_name }, { onlySelf: true });
    this.frmContact.patchValue({ prefix: contact.prefix }, { onlySelf: true });
    this.frmContact.patchValue({ suffix: contact.suffix }, { onlySelf: true });
    this.frmContact.patchValue({ street_1: contact.street_1 }, { onlySelf: true });
    this.frmContact.patchValue({ street_2: contact.street_2 }, { onlySelf: true });
    this.frmContact.patchValue({ city: contact.city }, { onlySelf: true });
    this.frmContact.patchValue({ state: contact.state }, { onlySelf: true });
    this.frmContact.patchValue({ zip_code: contact.zip_code }, { onlySelf: true });
    this.frmContact.patchValue({ occupation: contact.occupation }, { onlySelf: true });
    this.frmContact.patchValue({ employer: contact.employer }, { onlySelf: true });
    
    this.frmContact.patchValue({ phoneNumber: contact.phoneNumber }, { onlySelf: true });
    this.frmContact.patchValue({ officeSought: contact.officeSought}, { onlySelf: true });
    this.frmContact.patchValue({ officeState: contact.officeState }, { onlySelf: true });
    this.frmContact.patchValue({ district: contact.district }, { onlySelf: true });
    
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
    this._selectedEntity = this._utilService.deepClone(contact);
    this.frmContact.patchValue({ last_name: contact.last_name }, { onlySelf: true });
    this.frmContact.patchValue({ first_name: contact.first_name }, { onlySelf: true });
    this.frmContact.patchValue({ middle_name: contact.middle_name }, { onlySelf: true });
    this.frmContact.patchValue({ prefix: contact.prefix }, { onlySelf: true });
    this.frmContact.patchValue({ suffix: contact.suffix }, { onlySelf: true });
    this.frmContact.patchValue({ street_1: contact.street_1 }, { onlySelf: true });
    this.frmContact.patchValue({ street_2: contact.street_2 }, { onlySelf: true });
    this.frmContact.patchValue({ city: contact.city }, { onlySelf: true });
    this.frmContact.patchValue({ state: contact.state }, { onlySelf: true });
    this.frmContact.patchValue({ zip_code: contact.zip_code }, { onlySelf: true });
    this.frmContact.patchValue({ occupation: contact.occupation }, { onlySelf: true });
    this.frmContact.patchValue({ employer: contact.employer }, { onlySelf: true });

    this.frmContact.patchValue({ phoneNumber: contact.phoneNumber }, { onlySelf: true });
    this.frmContact.patchValue({ officeSought: contact.officeSought}, { onlySelf: true });
    this.frmContact.patchValue({ officeState: contact.officeState }, { onlySelf: true });
    this.frmContact.patchValue({ district: contact.district }, { onlySelf: true });

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
  /*private getReportIdFromStorage() {
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
  }*/

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

  private getFormFields(): void {
 
    console.log('get contact form fields ' + this.transactionType);
    this._contactsService.getContactsDynamicFormFields().subscribe(res => {
      if (res) {
             console.log("getFormFields res =", res );
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
                  }
                }
      
                if (res.data.hasOwnProperty('committeeFormFields')) {
                  if (Array.isArray(res.data.committeeFormFields)) {
                    this.committeeFormFields = res.data.committeeFormFields;
                }
                }   

                if (res.data.hasOwnProperty('organizationFormFields')) {
                  if (Array.isArray(res.data.organizationFormFields)) {
                    this.organizationFormFields = res.data.organizationFormFields;
                  }
                }   

                if (res.data.hasOwnProperty('candidateFormFields')) {
                  if (Array.isArray(res.data.candidateFormFields)) {
                    this.candidateFormFields = res.data.candidateFormFields;
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

                
                  if (res.data.hasOwnProperty('prefixes')) {
                  if (Array.isArray(res.data.prefixes)) {
                    this.prefixes = res.data.prefixes;
                  }
                } 

                if (res.data.hasOwnProperty('suffixes')) {
                  if (Array.isArray(res.data.suffixes)) {
                    this.suffixes = res.data.suffixes;
                  }
                }   

                if (res.data.hasOwnProperty('entityTypes')) {
                  if (Array.isArray(res.data.entityTypes)) {
                    this.entityTypes = res.data.entityTypes;
                  }
                }   
               
                if (res.data.hasOwnProperty('officeSought')) {
                  if (Array.isArray(res.data.officeSought)) {
                    this.officeSought = res.data.officeSought;
                  }
                }   

                if (res.data.hasOwnProperty('officeState')) {
                  if (Array.isArray(res.data.officeState)) {
                    this.officeState = res.data.officeState;
                  }
                }   

                if (res.data.hasOwnProperty('titles')) {
                  if (Array.isArray(res.data.titles)) {
                    this.titles = res.data.titles;
                  }
                }

                this._loading = false;
                console.log(new Date().toISOString());
      
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
        const formData: ContactModel = editOrView.transactionModel;

        this.hiddenFields.forEach(el => {
          if (el.name === 'id') {
            el.value = formData.id
          }
        });

        const nameArray = formData.name.split(',');
        const firstName = nameArray[1] ? nameArray[1] : null;
        const lastName = nameArray[0] ? nameArray[0] : null;
        const middleName = nameArray[2] ? nameArray[2] : null;
        const prefix = nameArray[3] ? nameArray[3] : null;
        const suffix = nameArray[4] ? nameArray[4] : null;

        this.frmContact.patchValue({ first_name: firstName.trim() }, { onlySelf: true });
        this.frmContact.patchValue({ last_name: lastName.trim() }, { onlySelf: true });
        this.frmContact.patchValue({ middle_name: middleName.trim() }, { onlySelf: true });
        this.frmContact.patchValue({ prefix: prefix.trim() }, { onlySelf: true });
        this.frmContact.patchValue({ suffix: suffix.trim() }, { onlySelf: true });
       
        this.frmContact.patchValue({ street_1: formData.street1 }, { onlySelf: true });
        this.frmContact.patchValue({ street_2: formData.street2 }, { onlySelf: true });
        this.frmContact.patchValue({ city: formData.city }, { onlySelf: true });
        this.frmContact.patchValue({ state: formData.state }, { onlySelf: true });
        this.frmContact.patchValue({ zip_code: formData.zip }, { onlySelf: true });

        this.frmContact.patchValue({ employer: formData.employer }, { onlySelf: true });
        this.frmContact.patchValue({ occupation: formData.occupation }, { onlySelf: true });

        this.frmContact.patchValue({ phoneNumber: formData.phoneNumber }, { onlySelf: true });
        this.frmContact.patchValue({ officeSought: formData.candOffice}, { onlySelf: true });
        this.frmContact.patchValue({ officeState: formData.candOfficeState }, { onlySelf: true });
        this.frmContact.patchValue({ district: formData.candOfficeState }, { onlySelf: true });
      }
    }
  }

  public selectTypeChange(e): void {
     this._entityType= e.target.value;
     this.loadDynamiceFormFields();
     console.log("selectTypeChange this._entityType = ", this._entityType);
  }

  public loadDynamiceFormFields(): void {
    if  (this._entityType === 'IND'){
      this.formFields  =  this.individualFormFields;
      this._setForm(this.formFields);
      } else if  (this._entityType === 'ORG'){
        this.formFields  =  this.organizationFormFields;
        this._setForm(this.formFields);
      } else if  (this._entityType === 'COM'){
        this.formFields  =  this.committeeFormFields;
        this._setForm(this.formFields);
      } else if  (this._entityType === 'CAN'){
        this.formFields  =  this.candidateFormFields;
        this._setForm(this.formFields);
      } 
  }

  public cancelStep(): void {
    this.frmContact.reset();
    this._router.navigate([`/contacts`]);
  }
  public saveAndExit(): void {
    this.doValidateContact("saveAndExit");
  }
  public saveAndAddMore(): void {
    this.doValidateContact("saveAndAddMore");
     //this._router.navigate([`/contacts`]);
  }

  public isFieldName(fieldName: string, nameString: string): boolean {
    return fieldName === nameString || fieldName === this._childFieldNamePrefix + nameString;
  }

  /**
   * Vaidates the form on submit.
   */
  public doValidateContact(callFrom: string) {

    if (this.frmContact.valid) {

      const contactObj: any = {};

      for (const field in this.frmContact.controls) {
         if (field === 'last_name' ||
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
          // contactObj[field] = this._selectedEntity[field];
          // } else {
          // TODO Possible defect with typeahead setting field as the entity object
          // rather than the string defined by the inputFormatter();
          // If an object is received, find the value on the object by fields type
          // otherwise use the string value.  This is not desired and this patch
          // should be removed if the issue is resolved.
          const typeAheadField = this.frmContact.get(field).value;
          if (typeAheadField && typeof typeAheadField !== 'string') {
            contactObj[field] = typeAheadField[field];
          } else {
            contactObj[field] = typeAheadField;
          }
          // }
         } else {
          contactObj[field] = this.frmContact.get(field).value;
        }
      }

      // There is a race condition with populating hiddenFields
      // and receiving transaction data to edit from the message service.
      // If editing, set transaction ID at this point to avoid race condition issue.
      if (this._contactToEdit) {
        this.hiddenFields.forEach((el: any) => {
          if (el.name === 'id') {
            el.value = this._contactToEdit.id;
          }
        });
      }

      this.hiddenFields.forEach(el => {
        contactObj[el.name] = el.value;
      });


      // If entity ID exist, the transaction will be added to the existing entity by the API
      // Otherwise it will create a new Entity.
      if (this._selectedEntity) {
        contactObj.entity_id = this._selectedEntity.entity_id;
      }
      contactObj.entity_type= this._entityType;

      localStorage.setItem('contactObj', JSON.stringify(contactObj));
      console.log("callFrom before saving=", callFrom);
      this._contactsService.saveContact(this.scheduleAction).subscribe(res => {
        if (res) {
          console.log("_contactsService.saveContact res", res);
          this._contactToEdit = null;
          this._formSubmitted = true;
          this.frmContact.reset();
          
          //this.frmContact.controls['memo_code'].setValue(null);
          this._selectedEntity = null;
          this._selectedChangeWarn = null;
          this._selectedEntityChild = null;
          this._selectedChangeWarnChild = null;

          localStorage.removeItem(contactObj);
          if (callFrom ==='saveAndExit'){
            this._router.navigate([`/contacts`]);
          }
          //localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify({ saved: true }));
          //window.scrollTo(0, 0);
        }
      });
    } else {
      this.frmContact.markAsDirty();
      this.frmContact.markAsTouched();
      //localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify({ saved: false }));
      window.scrollTo(0, 0);
    }
  }

}
