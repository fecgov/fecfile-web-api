import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, EventEmitter, Input, OnDestroy, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { NgbTooltipConfig, NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
import { Observable, Subscription, Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { FormsService } from '../../shared/services/FormsService/forms.service';
import { MessageService } from '../../shared/services/MessageService/message.service';
import { alphaNumeric } from '../../shared/utils/forms/validation/alpha-numeric.validator';
import { UtilService } from '../../shared/utils/util.service';
import { ContactModel } from '../model/contacts.model';
import { ContactsMessageService } from '../service/contacts-message.service';
import { ContactsService } from '../service/contacts.service';

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
  @Input() scheduleAction: ContactActions = ContactActions.add;
  @Input() transactionToEdit: ContactModel;


  public checkBoxVal: boolean = false;
  public frmContact: FormGroup;
  public formFields: any = [];
  public formVisible: boolean = false;
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
  public editScheduleAction: ContactActions = ContactActions.edit;
  public addScheduleAction: ContactActions = ContactActions.add;
  public isEditViewActive: boolean;

  private _formType: string = '';
  private _transactionTypePrevious: string = null;
  private _contributionAggregateValue = 0.0;
  private _selectedEntity: any;
  private _contributionAmountMax: number;
  private _entityType: string = 'IND';
  private readonly _childFieldNamePrefix = 'child*';
  private _contactToEdit: ContactModel;
  private _loading: boolean = false;
  private _selectedChangeWarn: any;
  private onDestroy$ = new Subject();

  constructor(
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _contactsService: ContactsService,
    private _config: NgbTooltipConfig,
    private _router: Router,
    private _utilService: UtilService,
    private _messageService: MessageService,
    private _decimalPipe: DecimalPipe,
    private _typeaheadService: TypeaheadService,
    private _dialogService: DialogService,
    private _contactsMessageService: ContactsMessageService,
    private _formsService: FormsService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';

    this._contactsMessageService.getPopulateFormMessage().takeUntil(this.onDestroy$)
    .subscribe(message => {
      this.populateFormForEditOrView(message);
    });

    this._contactsMessageService.getLoadFormFieldsMessage().takeUntil(this.onDestroy$)
    .subscribe(message => {
    });
  }

  ngOnInit(): void {
    this._selectedEntity = null;
    this._contactToEdit = null;
    
    localStorage.removeItem('contactsaved');
    
    this._messageService.clearMessage();


    this.getFormFields();

    this._entityType = 'IND';
    this.frmContact = this._fb.group({});
    if (this.selectedOptions) {
      if (this.selectedOptions.length >= 1) {
        this.formVisible = true;
      }
    }
  }

  // tslint:disable-next-line:use-life-cycle-interface
  public ngDoCheck(): void {
    if (this.frmContact.dirty) {
      if (this.frmContact.valid) {
        const isSaved = JSON.parse(localStorage.getItem('contactsaved'));
        if(isSaved) {
          if (!isSaved.saved) {
            this.frmContact.markAsDirty();
            this.frmContact.markAsTouched();
          } else {
            this.frmContact.markAsUntouched();
            this.frmContact.markAsPristine();
          }
        }
      } else {
        this.frmContact.markAsTouched();
        localStorage.setItem('contactsaved', JSON.stringify({ saved: false }));
      }
    } else {
      this.frmContact.markAsPristine();
      this.frmContact.markAsUntouched();
    }
  }

  public ngOnDestroy(): void {
    this._messageService.clearMessage();
    this.onDestroy$.next(true);
  }

  public debug(obj: any): void {
    console.log('obj: ', obj);
  }


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

    this.frmContact = new FormGroup(formGroup);

    // SET THE DEFAULT HERE
    if (this.frmContact.get('entity_type')) {
      const entityTypeVal = this.frmContact.get('entity_type').value;
      if (!entityTypeVal) {
        this.frmContact.patchValue({ entity_type: this._entityType }, { onlySelf: true });
      }
    }

    // get form data API is passing X for memo code value.
    // Set it to null here until it is checked by user where it will be set to X.
    //this.frmContact.controls['memo_code'].setValue(null);

    this.populateFormForEditOrView(this.transactionToEdit);
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
        this.frmContact.patchValue({ [col.name]: this._selectedEntity[col.name] }, { onlySelf: true });
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
      ` selected from the dropdwon.  Go to the Contacts page to edit a Contributor.`;

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
  
   /*public handleStateChange(stateOption: any, col: any) {
    console.log("handleStateChange stateOption", stateOption);
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
            console.log(" handleStateChange stateCode", stateCode);
          }
        }
      }
      
      this.frmContact.patchValue({ state: stateCode }, { onlySelf: true });
    }
  }*/


  /*public handleStateChange(stateOption: any, col: any) {
   
    if (this._selectedEntity) {
      // this.showWarn(col.text);
      this.frmContact.patchValue({ state: this._selectedEntity.state }, { onlySelf: true });
    } else {
      this.frmContact.patchValue({ state: stateOption.code }, { onlySelf: true });
    }
  } commented on 10052019*/


  public handleStateChange(stateOption: any, col: any) {
      if (this._selectedEntity) {
        this.showWarn(col.text, 'state');
        this.frmContact.patchValue({ state: this._selectedEntity.state }, { onlySelf: true });
      } else {
        this.frmContact.patchValue({ state: stateOption.code }, { onlySelf: true });
     }
  }

  private showWarn(fieldLabel: string, name: string) {
    if (this._selectedChangeWarn[name] === name) {
        return;
    }

    //const message = `Please note that if you update contact information it will be updated in the Contacts file.`;
    //this._dialogService.confirm(message, ConfirmModalComponent, 'Warning!', false).then(res => {});

    this._selectedChangeWarn[name] = name;
  }

  public handleCandOfficeChange(candOfficeOption: any, col: any) {

    if (this._selectedEntity) {
      //this.showWarn(col.text);
      //this.frmContact.patchValue({ candOffice: this._selectedEntity.candOffice}, { onlySelf: true });
      this.frmContact.patchValue({ office_Sought: this._selectedEntity.name }, { onlySelf: true });
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
      //this.frmContact.patchValue({ candOffice: officeCode }, { onlySelf: true });
      
      this.frmContact.patchValue({ office_Sought: candOfficeOption.code }, { onlySelf: true });
    }
  }
  
  public handleOfficeStateChange(officeStateOption: any, col: any) {

    if (this._selectedEntity) {
      //this.showWarn(col.text);
      //this.frmContact.patchValue({ candOfficeState: this._selectedEntity.candOfficeState}, { onlySelf: true });
      this.frmContact.patchValue({ Office_State: this._selectedEntity.name }, { onlySelf: true });
    } else {
      /*
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
      
      this.frmContact.patchValue({ candOfficeState: officeStateCode }, { onlySelf: true });
      */
      this.frmContact.patchValue({ Office_State: officeStateOption.code }, { onlySelf: true });
    }
  }

  /*public handleTypeChange(entityOption: any, col: any) {
    console.log("handleTypeChange entityOption", entityOption);
    if (this._selectedEntity) {
      //this.showWarn(col.text);
      this.frmContact.patchValue({ entityType: this._selectedEntity.entityType }, { onlySelf: true });
    } else {
      let entityCode = null;
      if (entityOption.$ngOptionLabel) {
        entityCode = entityOption.$ngOptionLabel;
        if (entityCode) {
          entityCode = entityCode.trim();
          if (entityCode.length > 1) {
            entityCode = entityCode.substring(0, 3 );
            console.log(" handleTypeChange entityCode", entityCode);
            this.frmContact.patchValue({ entityType: entityCode }, { onlySelf: true });
            this._entityType = entityCode;
            this.loadDynamiceFormFields();
          }
        }
      }
     
    }
  }*/

  public handleTypeChange(entityOption: any, col: any) {
    console.log(" handleTypeChange entityOption", entityOption);
    this._entityType = entityOption.code;
    if (this._selectedEntity) {
      // this.showWarn(col.text);
      this.frmContact.patchValue({ entity_type: this._selectedEntity.entity_type }, { onlySelf: true });
    } else {
      this.loadDynamiceFormFields();
      this.frmContact.patchValue({ entity_type: entityOption.code }, { onlySelf: true });

      if(this.scheduleAction === ContactActions.edit) {
        if((this.transactionToEdit.entity_type === 'IND' || this.transactionToEdit.entity_type === 'CAN')
          && (entityOption.code === 'COM' || entityOption.code === 'ORG')) {
          this.frmContact.patchValue({ entity_name: '' }, { onlySelf: true });
        }else if((this.transactionToEdit.entity_type === 'COM' || this.transactionToEdit.entity_type === 'ORG')
          && (entityOption.code === 'IND' || entityOption.code === 'CAN')) {
          this.frmContact.patchValue({ last_name: '' }, { onlySelf: true });
        }
      }
    }
  }

  public handleEntityTypeChange(item: any, col: any, entityType: any) {
    // Set the selectedEntityType for the toggle method to check.
    for (const entityTypeObj of this.entityTypes) {
      if (entityTypeObj.entityType === item.entityType) {
        entityTypeObj.selected = true;
        //this.selectedEntityType = entityTypeObj;
        this._entityType = entityTypeObj;
      } else {
        entityTypeObj.selected = false;
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
   * @deprecated
   */
  public receiveTypeaheadData(contact: any, fieldName: string): void {

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
    this.frmContact.patchValue({ entity_type: contact.entity_type }, { onlySelf: true });
    this.frmContact.patchValue({ zip_code: contact.zip_code }, { onlySelf: true });
    this.frmContact.patchValue({ occupation: contact.occupation }, { onlySelf: true });
    this.frmContact.patchValue({ employer: contact.employer }, { onlySelf: true });

    this.frmContact.patchValue({ phoneNumber: contact.phoneNumber }, { onlySelf: true });
    this.frmContact.patchValue({ candOffice: contact.candOffice }, { onlySelf: true });
    this.frmContact.patchValue({ candOfficeState: contact.candOfficeState }, { onlySelf: true });
    this.frmContact.patchValue({ candOfficeDistrict: contact.candOfficeDistrict }, { onlySelf: true });

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
   * Populate the fields in the form with the values from the selected contact.
   *
   * @param $event The mouse event having selected the contact from the typeahead options.
   */
  public handleSelectedOrgItem($event: NgbTypeaheadSelectItemEvent) {
    const contact = $event.item;
    this._selectedEntity = this._utilService.deepClone(contact);
    //this.frmContact.patchValue({ type: contact.type }, { onlySelf: true });
    this.frmContact.patchValue({ last_name: contact.entity_name }, { onlySelf: true });
    this.frmContact.patchValue({ street_1: contact.street_1 }, { onlySelf: true });
    this.frmContact.patchValue({ street_2: contact.street_2 }, { onlySelf: true });
    this.frmContact.patchValue({ city: contact.city }, { onlySelf: true });
    this.frmContact.patchValue({ state: contact.state }, { onlySelf: true });
    this.frmContact.patchValue({ zip_code: contact.zip_code }, { onlySelf: true });
    this.frmContact.patchValue({ entity_type: contact.entity_type }, { onlySelf: true });
    this.frmContact.patchValue({ phoneNumber: contact.phoneNumber }, { onlySelf: true });
  }

  public handleSelectedItem($event: NgbTypeaheadSelectItemEvent) {
    const contact = $event.item;
    this._selectedEntity = this._utilService.deepClone(contact);
    //this.frmContact.patchValue({ type: contact.type }, { onlySelf: true });
    this.frmContact.patchValue({ last_name: contact.last_name }, { onlySelf: true });
    this.frmContact.patchValue({ first_name: contact.first_name }, { onlySelf: true });
    this.frmContact.patchValue({ middle_name: contact.middle_name }, { onlySelf: true });
    this.frmContact.patchValue({ prefix: contact.prefix }, { onlySelf: true });
    // TODO: Workaround backend column-name typo. Should be removed later FNE-1974
    this.frmContact.patchValue({ prefix: contact.preffix }, { onlySelf: true });
    this.frmContact.patchValue({ suffix: contact.suffix }, { onlySelf: true });
    this.frmContact.patchValue({ street_1: contact.street_1 }, { onlySelf: true });
    this.frmContact.patchValue({ street_2: contact.street_2 }, { onlySelf: true });
    this.frmContact.patchValue({ city: contact.city }, { onlySelf: true });
    this.frmContact.patchValue({ state: contact.state }, { onlySelf: true });
    this.frmContact.patchValue({ zip_code: contact.zip_code }, { onlySelf: true });
    this.frmContact.patchValue({ entity_type: contact.entity_type }, { onlySelf: true });
    this.frmContact.patchValue({ occupation: contact.occupation }, { onlySelf: true });
    this.frmContact.patchValue({ employer: contact.employer }, { onlySelf: true });

    //this.frmContact.patchValue({ phoneNumber: contact.phoneNumber }, { onlySelf: true });
    //this.frmContact.patchValue({ candOffice: contact.candOffice }, { onlySelf: true });
    //this.frmContact.patchValue({ candOfficeState: contact.candOfficeState }, { onlySelf: true });
    //this.frmContact.patchValue({ candOfficeDistrict: contact.candOfficeDistrict }, { onlySelf: true });


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
    this._contactsService.getContactsDynamicFormFields().subscribe(res => {
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
                this._setForm(res.data.individualFormFields);
              }
            }

            if (res.data.hasOwnProperty('committeeFormFields')) {
              if (Array.isArray(res.data.committeeFormFields)) {
                this.committeeFormFields = res.data.committeeFormFields;
                //this.formFields = res.data.committeeFormFields;
                //this._setForm(res.data.committeeFormFields);
              }
            }

            if (res.data.hasOwnProperty('organizationFormFields')) {
              if (Array.isArray(res.data.organizationFormFields)) {
                this.organizationFormFields = res.data.organizationFormFields;
                //this.formFields = res.data.organizationFormFields;
                //this._setForm(res.data.organizationFormFields);
              }
            }

            if (res.data.hasOwnProperty('candidateFormFields')) {
              if (Array.isArray(res.data.candidateFormFields)) {
                this.candidateFormFields = res.data.candidateFormFields;
                //this.formFields = res.data.candidateFormFields;
                //this._setForm(res.data.candidateFormFields);
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

            if (res.data.hasOwnProperty('addEntityTypes')) {
              if (Array.isArray(res.data.addEntityTypes)) {
                this.entityTypes = res.data.addEntityTypes;
              }
            }
          
            if(this.scheduleAction === ContactActions.edit) {
          
              if (res.data.hasOwnProperty('editEntityTypes')) {
                if (Array.isArray(res.data.addEntityTypes)) {
                  this.entityTypes = res.data.editEntityTypes;
                }

                if (res.data.hasOwnProperty('individualFormFields') && this.transactionToEdit.entity_type === 'IND') {
                  if (Array.isArray(res.data.individualFormFields)) {
                    this.individualFormFields = res.data.individualFormFields;
                    this.formFields = res.data.individualFormFields;
                    this._setForm(res.data.individualFormFields);
                  }
                }

                if (res.data.hasOwnProperty('committeeFormFields') && this.transactionToEdit.entity_type === 'COM') {
                  if (Array.isArray(res.data.committeeFormFields)) {
                    this.committeeFormFields = res.data.committeeFormFields;
                    this.formFields = res.data.committeeFormFields;
                    this._setForm(res.data.committeeFormFields);
                  }
                }

                if (res.data.hasOwnProperty('organizationFormFields') && this.transactionToEdit.entity_type === 'ORG') {
                  if (Array.isArray(res.data.organizationFormFields)) {
                    this.organizationFormFields = res.data.organizationFormFields;
                    this.formFields = res.data.organizationFormFields;
                    this._setForm(res.data.organizationFormFields);
                  }
                }

                if (res.data.hasOwnProperty('candidateFormFields') && this.transactionToEdit.entity_type === 'CAN') {
                  if (Array.isArray(res.data.candidateFormFields)) {
                    this.candidateFormFields = res.data.candidateFormFields;
                    this.formFields = res.data.candidateFormFields;
                    this._setForm(res.data.candidateFormFields);
                  }
                }
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
          } // typeof res.data
        } // res.hasOwnProperty('data')
      } // res
    });
  }

  private populateFormForEditOrView(editOrView: any) {
    // The action here is the same as the this.scheduleAction
    // using the field from the message in case there is a race condition with Input().
    if (editOrView !== null) {
      if (editOrView) { //.transactionModel) {
        const formData: ContactModel = editOrView; //.transactionModel;

        this.hiddenFields.forEach(el => {
          if (el.name === 'id') {
            el.value = formData.id;
          }
        });

        const nameArray = formData.name.split(',');
        /*
        const firstName = nameArray[1] ? nameArray[1] : null;
        const lastName = nameArray[0] ? nameArray[0] : null;
        const middleName = nameArray[2] ? nameArray[2] : null;
        const prefix = nameArray[3] ? nameArray[3] : null;
        const suffix = nameArray[4] ? nameArray[4] : null;
        */

        const firstName = nameArray[1] ? nameArray[1].trim() : '';
        const lastName = nameArray[0] ? nameArray[0].trim() : '';
        const middleName = nameArray[2] ? nameArray[2].trim() : '';
        const prefix = nameArray[3] ? nameArray[3].trim() : '';
        const suffix = nameArray[4] ? nameArray[4].trim() : '';

        this.frmContact.patchValue({ first_name: firstName }, { onlySelf: true });
        this.frmContact.patchValue({ last_name: lastName }, { onlySelf: true });
        this.frmContact.patchValue({ middle_name: middleName }, { onlySelf: true });
        this.frmContact.patchValue({ prefix: prefix }, { onlySelf: true });
        this.frmContact.patchValue({ Prefix: prefix }, { onlySelf: true });
        this.frmContact.patchValue({ suffix: suffix }, { onlySelf: true });

        this.frmContact.patchValue({ entity_type: formData.entity_type }, { onlySelf: true });
        this.frmContact.patchValue({ street_1: formData.street1 }, { onlySelf: true });
        this.frmContact.patchValue({ street_2: formData.street2 }, { onlySelf: true });
        this.frmContact.patchValue({ city: formData.city }, { onlySelf: true });
        this.frmContact.patchValue({ state: formData.state }, { onlySelf: true });
        this.frmContact.patchValue({ zip_code: formData.zip }, { onlySelf: true });

        this.frmContact.patchValue({ employer: formData.employer }, { onlySelf: true });
        this.frmContact.patchValue({ occupation: formData.occupation }, { onlySelf: true });

        this.frmContact.patchValue({ phone_number: formData.phoneNumber }, { onlySelf: true });
        this.frmContact.patchValue({ candOffice: formData.candOffice }, { onlySelf: true });
        this.frmContact.patchValue({ candOfficeState: formData.candOfficeState }, { onlySelf: true });
        this.frmContact.patchValue({ candOfficeDistrict: formData.candOfficeDistrict }, { onlySelf: true });
      
        this.frmContact.patchValue({ entity_name: formData.name }, { onlySelf: true });
        
        this.frmContact.patchValue({ candCmteId: formData.candCmteId }, { onlySelf: true });
        this.frmContact.patchValue({ officeSought: formData.officeSought }, { onlySelf: true });

        this.frmContact.patchValue({ candidate_id: formData.candCmteId }, { onlySelf: true });
        this.frmContact.patchValue({ office_Sought: formData.candOffice }, { onlySelf: true });
        this.frmContact.patchValue({ Office_State: formData.candOfficeState }, { onlySelf: true });

        this.frmContact.patchValue({ commitee_id: formData.candCmteId }, { onlySelf: true });

        //this.frmContact.patchValue({ candOfficeState: formData.candOfficeState }, { onlySelf: true });
        //this.frmContact.patchValue({ candOfficeDistrict: formData.candOfficeDistrict }, { onlySelf: true });
      }
    }
  }

  /*public selectTypeChange(e): void {
    this._entityType = e.target.value;
    this.loadDynamiceFormFields();
    console.log('selectTypeChange this._entityType = ', this._entityType);
  }*/

  public loadDynamiceFormFields(): void {
    if (this._entityType === 'IND') {
      this.formFields = this.individualFormFields;
    } else if (this._entityType === 'ORG') {
      this.formFields = this.organizationFormFields;
    } else if (this._entityType === 'COM') {
      this.formFields = this.committeeFormFields;
    } else if (this._entityType === 'CAN') {
      this.formFields = this.candidateFormFields;
    }
    this._setForm(this.formFields);
  }

  public cancelStepWithWarning(): void {
     this._dialogService.confirm(
         '', ConfirmModalComponent, '', true)
         .then(res => {
           if (res === 'okay' ? true : false ) {
             if (this.scheduleAction !== this.editScheduleAction) {
               this.frmContact.reset();
               this._router.navigate([`/contacts`]);
             } else {
               this.status.emit({
                 editView: false
               });
             }
           }
         });


  }

  public cancelStep(): void {

            if (this.scheduleAction !== this.editScheduleAction) {
              this.frmContact.reset();
              this._router.navigate([`/contacts`]);
            } else {
              this.status.emit({
                editView: false
              });
            }

  }


  public viewContacts(): void {
    if (this.frmContact.dirty) {
      this.doValidateContact('viewContacts');
    } else {
    this._router.navigate([`/contacts`]);
    }
  }

  public saveAndAddMore(): void {
    this.doValidateContact('saveAndAddMore');
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
      contactObj.entity_type = this._entityType;

      if(this.scheduleAction === ContactActions.edit) {
        contactObj.id = this.transactionToEdit.id;
        contactObj.entity_type = this.frmContact.get('entity_type').value;
      }

      if(this.frmContact.get('commitee_id')) {
        contactObj.candCmteId = this.frmContact.get('commitee_id').value;
      }

      localStorage.setItem('contactObj', JSON.stringify(contactObj));
      this._contactsService.saveContact(this.scheduleAction).subscribe(res => {
        if (res) {
          console.log('_contactsService.saveContact res', res);
          this._contactToEdit = null;
          this.frmContact.reset();
          this._selectedEntity = null;
          localStorage.removeItem(contactObj);
          localStorage.setItem('contactsaved', JSON.stringify({ saved: true }));
          //window.scrollTo(0, 0);

          if(this.scheduleAction === ContactActions.edit) {
            this.status.emit({
              editView: false
            });
          }
          if (callFrom === 'viewContacts') {
            this._router.navigate([`/contacts`]);
          }}
      });
    } else {
      this.frmContact.markAsDirty();
      this.frmContact.markAsTouched();
      localStorage.setItem('contactsaved', JSON.stringify({ saved: false }));
      if (callFrom === 'viewContacts') {
        this._router.navigate([`/contacts`]);
      }
      window.scrollTo(0, 0);
    }
  }

  /**
   * Determines ability for a person to leave a page with a form on it.
   *
   * @return     {boolean}  True if able to deactivate, False otherwise.
   */
  public async canDeactivate(): Promise<boolean> {
    console.log('value for contact back', this._formsService.HasUnsavedData('contact'))
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
 }
}
