import {
  Component,
  EventEmitter,
  ElementRef,
  Input,
  OnInit,
  Output,
  ViewEncapsulation,
  ViewChild,
  OnDestroy,
  HostListener
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
import { Observable, Subscription, interval, timer } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, delay, pairwise } from 'rxjs/operators';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { TransactionModel } from '../../transactions/model/transaction.model';
import { F3xMessageService } from '../service/f3x-message.service';
import { ScheduleActions } from './schedule-actions.enum';
import { hasOwnProp } from 'ngx-bootstrap/chronos/utils/type-checks';

@Component({
  selector: 'f3x-individual-receipt',
  templateUrl: './individual-receipt.component.html',
  styleUrls: ['./individual-receipt.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe],
  encapsulation: ViewEncapsulation.None
})
export class IndividualReceiptComponent implements OnInit, OnDestroy {
  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() selectedOptions: any = {};
  @Input() formOptionsVisible = false;
  @Input() transactionTypeText = '';
  @Input() transactionType = '';
  @Input() scheduleAction: ScheduleActions = null;

  /**
   * Subscription for pre-populating the form for view or edit.
   */
  private _populateFormSubscription: Subscription;
  private _clearFormSubscription: Subscription;

  public checkBoxVal = false;
  public cvgStartDate: string = null;
  public cvgEndDate: string = null;
  public frmIndividualReceipt: FormGroup;
  public formFields: any = [];
  public formVisible = false;
  public hiddenFields: any = [];
  public memoCode = false;
  public memoCodeChild = false;
  public testForm: FormGroup;
  public titles: any = [];
  public states: any = [];
  public entityTypes: any = [];
  public selectedEntityType: any;

  private _formType = '';
  private _reportType: any = null;
  private _types: any = [];
  private _transaction: any = {};
  private _transactionType: string = null;
  private _transactionTypePrevious: string = null;
  private _formSubmitted = false;
  private _contributionAggregateValue = 0.0;
  private _contributionAggregateValueChild = 0.0;
  private _contributionAmount = '';
  private _contributionAmountChlid = '';
  private readonly _memoCodeValue: string = 'X';
  private _selectedEntity: any;
  // private _isSelectedEntityAggregate: boolean;
  private _isSelectedEntityAggregateChild: boolean;
  private _selectedEntityChild: any;
  private _selectedChangeWarn: any;
  private _selectedChangeWarnChild: any;
  private _contributionAmountMax: number;
  private _transactionToEdit: TransactionModel;
  private readonly _childFieldNamePrefix = 'child*';
  private _readOnlyMemoCode: boolean;
  private _readOnlyMemoCodeChild: boolean;
  private _entityTypeDefault: any;

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
    private _typeaheadService: TypeaheadService,
    private _dialogService: DialogService,
    private _f3xMessageService: F3xMessageService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';

    this._populateFormSubscription = this._f3xMessageService.getPopulateFormMessage().subscribe(message => {
      this._populateFormForEditOrView(message);
    });

    this._clearFormSubscription = this._f3xMessageService.getInitFormMessage().subscribe(message => {
      this._clearFormValues();
    });
  }

  ngOnInit(): void {
    this._selectedEntity = null;
    this._selectedChangeWarn = null;
    this._selectedEntityChild = null;
    this._selectedChangeWarnChild = null;
    // this._isSelectedEntityAggregate = false;
    this._readOnlyMemoCode = false;
    this._readOnlyMemoCodeChild = false;
    this._transactionToEdit = null;
    this._contributionAggregateValue = 0.0;
    this._contributionAggregateValueChild = 0.0;
    this._contributionAmount = '';
    this._contributionAmountChlid = '';
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify({ saved: true }));
    localStorage.setItem('Receipts_Entry_Screen', 'Yes');

    this._messageService.clearMessage();

    this._reportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));

    if (this._reportType === null || typeof this._reportType === 'undefined') {
      this._reportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type_backup`));
    }

    this.frmIndividualReceipt = this._fb.group({});
  }

  ngDoCheck(): void {
    // TODO consider changes this to ngOnChanges()

    // this._populatePurposeForEarmark();

    // this._listenForDateChange();

    if (this.selectedOptions) {
      if (this.selectedOptions.length >= 1) {
        this.formVisible = true;
      }
    }

    this._getTransactionType();

    this._validateContributionDate();

    if (localStorage.getItem(`form_${this._formType}_report_type`) !== null) {
      this._reportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));

      if (typeof this._reportType === 'object') {
        if (this._reportType.hasOwnProperty('cvgEndDate') && this._reportType.hasOwnProperty('cvgStartDate')) {
          if (typeof this._reportType.cvgStartDate === 'string' && typeof this._reportType.cvgEndDate === 'string') {
            this.cvgStartDate = this._reportType.cvgStartDate;
            this.cvgEndDate = this._reportType.cvgEndDate;
          }
        }
      }
    }

    if (this.frmIndividualReceipt) {
      if (Array.isArray(this.frmIndividualReceipt.controls)) {
        if (this.frmIndividualReceipt.controls['contribution_date']) {
          if (this.cvgStartDate === null && this.cvgEndDate === null && this._reportType === null) {
            if (localStorage.getItem(`form_${this._formType}_report_type`) !== null) {
              this._reportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));
              if (this._reportType.hasOwnProperty('cvgEndDate') && this._reportType.hasOwnProperty('cvgStartDate')) {
                if (
                  typeof this._reportType.cvgStartDate === 'string' &&
                  typeof this._reportType.cvgEndDate === 'string'
                ) {
                  this.cvgStartDate = this._reportType.cvgStartDate;
                  this.cvgEndDate = this._reportType.cvgEndDate;

                  this.frmIndividualReceipt.controls['contribution_date'].setValidators([
                    contributionDate(this.cvgStartDate, this.cvgEndDate),
                    Validators.required
                  ]);

                  this.frmIndividualReceipt.controls['contribution_date'].updateValueAndValidity();
                }
              }
            }
          }
        }
      }
    }
  }

  ngOnDestroy(): void {
    this._messageService.clearMessage();
    this._populateFormSubscription.unsubscribe();
    this._clearFormSubscription.unsubscribe();
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
    let memoCodeValue = null;
    this._readOnlyMemoCode = false;
    this._readOnlyMemoCodeChild = false;

    fields.forEach(el => {
      if (el.hasOwnProperty('cols') && el.cols) {
        el.cols.forEach(e => {
          formGroup[e.name] = new FormControl(e.value || null, this._mapValidators(e.validation, e.name));
          if (this.isFieldName(e.name, 'contribution_amount')) {
            if (e.validation) {
              this._contributionAmountMax = e.validation.max ? e.validation.max : 0;
            }
          }
          if (this.isFieldName(e.name, 'memo_code')) {
            memoCodeValue = e.value;
            if (memoCodeValue === this._memoCodeValue) {
              this._readOnlyMemoCode = true;
              const isChildForm = e.name.startsWith(this._childFieldNamePrefix) ? true : false;
              if (isChildForm) {
                this.memoCodeChild = true;
              } else {
                this.memoCode = true;
              }
            }
          }
        });
      }
    });

    this.frmIndividualReceipt = new FormGroup(formGroup);

    // When coming from Reports where this component is not a child
    // as it is in F3X component, the form data must be set in this way
    // to avoid race condition
    if (this._transactionToEdit) {
      this._setFormDataValues();
    }

    // get form data API is passing X for memo code value.
    // Set it to value from dynamic forms as some should be checked and disabled by default.
    if (this.memoCode) {
      this.frmIndividualReceipt.controls['memo_code'].setValue(this._memoCodeValue);
    }
    if (this.memoCodeChild) {
      this.frmIndividualReceipt.controls[this._childFieldNamePrefix + 'memo_code'].setValue(this._memoCodeValue);
    }
  }

  /**
   * Check if the name of a field in the form matches the nameString for
   * child and non-child forms.
   *
   * @param fieldName name of the field from te dynamic form API
   * @param nameString string of the name field to check against the fieldName
   */
  public isFieldName(fieldName: string, nameString: string): boolean {
    return fieldName === nameString || fieldName === this._childFieldNamePrefix + nameString;
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
    if (this.isFieldName(fieldName, 'zip_code')) {
      formValidators.push(alphaNumeric());
    } else if (this.isFieldName(fieldName, 'contribution_date')) {
      this._reportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));
      if (this._reportType !== null) {
        const cvgStartDate: string = this._reportType.cvgStartDate;
        const cvgEndDate: string = this._reportType.cvgEndDate;

        formValidators.push(contributionDate(cvgStartDate, cvgEndDate));
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
      if (this.memoCodeChild) {
        this.frmIndividualReceipt.controls['child*contribution_date'].setValidators([Validators.required]);

        this.frmIndividualReceipt.controls['child*contribution_date'].updateValueAndValidity();
      } else {
        if (this.frmIndividualReceipt.controls['child*contribution_date']) {
          this.frmIndividualReceipt.controls['child*contribution_date'].setValidators([
            contributionDate(cvgStartDate, cvgEndDate),
            Validators.required
          ]);

          this.frmIndividualReceipt.controls['child*contribution_date'].updateValueAndValidity();
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

      // Do same as above for child amount
      if (this.frmIndividualReceipt.controls['child*contribution_amount']) {
        this.frmIndividualReceipt.controls['child*contribution_amount'].setValidators([
          floatingPoint(),
          Validators.required
        ]);

        this.frmIndividualReceipt.controls['child*contribution_amount'].updateValueAndValidity();
      }

      if (this.frmIndividualReceipt.controls['child*contribution_aggregate']) {
        this.frmIndividualReceipt.controls['child*contribution_aggregate'].setValidators([floatingPoint()]);

        this.frmIndividualReceipt.controls['child*contribution_aggregate'].updateValueAndValidity();
      }
    }
  }

  /**
   * Updates the contribution aggregate field once contribution ammount is entered.
   *
   * @param      {Object}  e         The event object.
   * @param      {string}  fieldName The name of the field
   */
  public contributionAmountChange(e: any, fieldName: string): void {
    const isChildForm = fieldName.startsWith(this._childFieldNamePrefix) ? true : false;
    let contributionAmount: string = e.target.value;

    // default to 0 when no value
    contributionAmount = contributionAmount ? contributionAmount : '0';

    // remove commas
    contributionAmount = contributionAmount.replace(/,/g, ``);

    // determine if negative, truncate if > max
    contributionAmount = this.transformAmount(contributionAmount, this._contributionAmountMax);

    let contributionAggregate: string = null;
    if (isChildForm) {
      this._contributionAmountChlid = contributionAmount;
      contributionAggregate = String(this._contributionAggregateValueChild);
    } else {
      this._contributionAmount = contributionAmount;
      contributionAggregate = String(this._contributionAggregateValue);
    }

    const contributionAmountNum = parseFloat(contributionAmount);
    const aggregateTotal: number = contributionAmountNum + parseFloat(contributionAggregate);
    const aggregateValue: string = this._decimalPipe.transform(aggregateTotal, '.2-2');
    const amountValue: string = this._decimalPipe.transform(contributionAmountNum, '.2-2');

    if (isChildForm) {
      this.frmIndividualReceipt.patchValue({ 'child*contribution_amount': amountValue }, { onlySelf: true });
      this.frmIndividualReceipt.patchValue({ 'child*contribution_aggregate': aggregateValue }, { onlySelf: true });
    } else {
      this.frmIndividualReceipt.patchValue({ contribution_amount: amountValue }, { onlySelf: true });
      this.frmIndividualReceipt.patchValue({ contribution_aggregate: aggregateValue }, { onlySelf: true });
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
    if (!col) {
      return;
    }
    if (!col.name) {
      return;
    }
    if ($event.key) {
      const key = $event.key.toUpperCase();
      if (
        // TODO add more keys, home, insert, end, print, pause, etc
        key === 'F12' ||
        key === 'TAB' ||
        key === 'ENTER' ||
        key === 'SHIFT' ||
        key === 'ALT' ||
        key === 'CONTROL' ||
        key === 'ARROWRIGHT' ||
        key === 'CAPSLOCK' ||
        key === 'PAGEUP' ||
        key === 'PAGEDOWN' ||
        key === 'ESCAPE' ||
        key === 'ARROWUP' ||
        key === 'ARROWLEFT' ||
        key === 'ARROWDOWN'
      ) {
        return;
      }
    }
    if (
      col.name === 'last_name' ||
      col.name === 'first_name' ||
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
        this.showWarn(col.text, col.name);
      }
    } else if (
      col.name === this._childFieldNamePrefix + 'street_1' ||
      col.name === this._childFieldNamePrefix + 'street_2' ||
      col.name === this._childFieldNamePrefix + 'city' ||
      col.name === this._childFieldNamePrefix + 'state' ||
      col.name === this._childFieldNamePrefix + 'zip_code' ||
      col.name === this._childFieldNamePrefix + 'employer' ||
      col.name === this._childFieldNamePrefix + 'occupation'
    ) {
      if (this._selectedEntityChild) {
        this.showWarn(col.text, col.name);
      }
    } else if (this.isFieldName(col.name, 'contribution_amount')) {
      this.contributionAmountKeyup($event);
    } else {
      return null;
    }
  }

  /**
   * Show a warning indicating fields may not be changed for entities loaded from the database.
   *
   * @param fieldLabel Field Label to show in the message
   */
  private showWarn(fieldLabel: string, name: string) {
    const isChildForm = name.startsWith(this._childFieldNamePrefix) ? true : false;

    // only show on first key
    if (isChildForm) {
      if (this._selectedChangeWarnChild[name] === name) {
        return;
      }
    } else {
      if (this._selectedChangeWarn[name] === name) {
        return;
      }
    }

    const message = `Please note that if you update contact information it will be updated in the Contacts file.`;
    this._dialogService.confirm(message, ConfirmModalComponent, 'Warning!', false).then(res => {});

    if (isChildForm) {
      this._selectedChangeWarnChild[name] = name;
    } else {
      this._selectedChangeWarn[name] = name;
    }
  }

  /**
   * Updates vaprivate _memoCode variable.
   *
   * @param      {Object}  e      The event object.
   */
  public memoCodeChange(e, fieldName: string): void {
    const { checked } = e.target;
    const isChildForm = fieldName.startsWith(this._childFieldNamePrefix) ? true : false;

    if (isChildForm) {
      if (checked) {
        this.memoCodeChild = checked;
        this.frmIndividualReceipt.controls['child*memo_code'].setValue(this._memoCodeValue);
        this.frmIndividualReceipt.controls['child*contribution_date'].setValidators([Validators.required]);

        this.frmIndividualReceipt.controls['child*contribution_date'].updateValueAndValidity();
      } else {
        this._validateContributionDate();
        this.memoCodeChild = checked;
        this.frmIndividualReceipt.controls['child*memo_code'].setValue(null);
        this.frmIndividualReceipt.controls['child*contribution_date'].setValidators([
          contributionDate(this.cvgStartDate, this.cvgEndDate),
          Validators.required
        ]);

        this.frmIndividualReceipt.controls['contribution_date'].updateValueAndValidity();
      }
    } else {
      if (checked) {
        this.memoCode = checked;
        this.frmIndividualReceipt.controls['memo_code'].setValue(this._memoCodeValue);
        this.frmIndividualReceipt.controls['contribution_date'].setValidators([Validators.required]);

        this.frmIndividualReceipt.controls['contribution_date'].updateValueAndValidity();
      } else {
        this._validateContributionDate();
        this.memoCode = checked;
        this.frmIndividualReceipt.controls['memo_code'].setValue(null);
        this.frmIndividualReceipt.controls['contribution_date'].setValidators([
          contributionDate(this.cvgStartDate, this.cvgEndDate),
          Validators.required
        ]);

        this.frmIndividualReceipt.controls['contribution_date'].updateValueAndValidity();
      }
    }
  }

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
    const isChildForm = col.name.startsWith(this._childFieldNamePrefix) ? true : false;

    if (isChildForm) {
      if (this._selectedEntityChild) {
        this.showWarn(col.text, this._childFieldNamePrefix + 'state');
      }
    } else {
      if (this._selectedEntity) {
        this.showWarn(col.text, 'state');
      }
    }

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
    if (isChildForm) {
      this.frmIndividualReceipt.patchValue({ 'child*state': stateCode }, { onlySelf: true });
    } else {
      this.frmIndividualReceipt.patchValue({ state: stateCode }, { onlySelf: true });
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
        } else if (field === this._childFieldNamePrefix + 'contribution_date') {
          receiptObj[field] = this._utilService.formatDate(this.frmIndividualReceipt.get(field).value);
        } else if (field === 'memo_code') {
          if (this.memoCode) {
            receiptObj[field] = this.frmIndividualReceipt.get(field).value;
            console.log('memo code val ' + receiptObj[field]);
          }
        } else if (field === this._childFieldNamePrefix + 'memo_code') {
          if (this.memoCodeChild) {
            receiptObj[field] = this.frmIndividualReceipt.get(field).value;
            console.log('child memo code val ' + receiptObj[field]);
          }
        } else if (field === 'last_name' ||
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
          // receiptObj[field] = this._selectedEntity[field];
          // } else {
          // TODO Possible defect with typeahead setting field as the entity object
          // rather than the string defined by the inputFormatter();
          // If an object is received, find the value on the object by fields type
          // otherwise use the string value.  This is not desired and this patch
          // should be removed if the issue is resolved.
          const typeAheadField = this.frmIndividualReceipt.get(field).value;
          if (typeAheadField && typeof typeAheadField !== 'string') {
            receiptObj[field] = typeAheadField[field];
          } else {
            receiptObj[field] = typeAheadField;
          }
          // }
        } else if (field === 'contribution_amount') {
          receiptObj[field] = this._contributionAmount;
        } else if (field === this._childFieldNamePrefix + 'contribution_amount') {
          receiptObj[field] = this._contributionAmountChlid;
        } else {
          receiptObj[field] = this.frmIndividualReceipt.get(field).value;
        }
      }

      // There is a race condition with populating hiddenFields
      // and receiving transaction data to edit from the message service.
      // If editing, set transaction ID at this point to avoid race condition issue.
      if (this._transactionToEdit) {
        this.hiddenFields.forEach((el: any) => {
          if (el.name === 'transaction_id') {
            el.value = this._transactionToEdit.transactionId;
          }
        });
      }

      this.hiddenFields.forEach(el => {
        receiptObj[el.name] = el.value;
      });

      // If entity ID exist, the transaction will be added to the existing entity by the API
      // Otherwise it will create a new Entity.
      if (this._selectedEntity) {
        receiptObj.entity_id = this._selectedEntity.entity_id;
      }

      // TODO do we need to save child entity?
      if (this._selectedEntityChild) {
        receiptObj['child*entity_id'] = this._selectedEntityChild.entity_id;
      }

      localStorage.setItem(`form_${this._formType}_receipt`, JSON.stringify(receiptObj));

      this._receiptService.saveSchedule(this._formType, this.scheduleAction).subscribe(res => {
        if (res) {
          this._transactionToEdit = null;

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

          this._contributionAmount = '';
          this._contributionAmountChlid = '';
          this._contributionAggregateValue = 0.0;
          this._contributionAggregateValueChild = 0.0;
          const contributionAggregateValue: string = this._decimalPipe.transform(
            this._contributionAggregateValue,
            '.2-2'
          );

          if (this.frmIndividualReceipt.contains('contribution_aggregate')) {
            this.frmIndividualReceipt.controls['contribution_aggregate'].setValue(contributionAggregateValue);
          }

          if (this.frmIndividualReceipt.controls['child*contribution_aggregate']) {
            const contributionAggregateValueChild: string = this._decimalPipe.transform(
              this._contributionAggregateValueChild,
              '.2-2'
            );
            if (this.frmIndividualReceipt.contains('child*contribution_aggregate')) {
              this.frmIndividualReceipt.controls['child*contribution_aggregate'].setValue(
                contributionAggregateValueChild
              );
            }
          }

          this._formSubmitted = true;
          this.memoCode = false;
          this.memoCodeChild = false;
          this.frmIndividualReceipt.reset();
          this.frmIndividualReceipt.controls['memo_code'].setValue(null);
          this._selectedEntity = null;
          this._selectedChangeWarn = null;
          this._selectedEntityChild = null;
          this._selectedChangeWarnChild = null;

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
    this._clearFormValues();
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
    this._clearFormValues();
    let reportId = this._getReportIdFromStorage();
    console.log('reportId', reportId);

    if (!reportId) {
      reportId = '0';
    }
    localStorage.setItem(`form_${this._formType}_view_transaction_screen`, 'Yes');
    localStorage.setItem('Transaction_Table_Screen', 'Yes');

    this._router.navigate([`/forms/form/${this._formType}`], {
      queryParams: { step: 'transactions', reportId: reportId }
    });
  }

  public printPreview(): void {
    this._reportTypeService.printPreview('individual_receipt', this._formType);
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
   * Populate the fields in the form with the values from the selected contact.
   *
   * @param $event The mouse event having selected the contact from the typeahead options.
   */
  public handleSelectedItem($event: NgbTypeaheadSelectItemEvent) {

    // FNE-1438 Need to detect if tab key caused the event. And don't load if true.
    // TODO need a way to determine if key was tab.

    const contact = $event.item;
    this._selectedEntity = this._utilService.deepClone(contact);
    this._selectedChangeWarn = {};
    // this._isSelectedEntityAggregate = false;
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

    // If date is selected, get the aggregate.
    if (this.frmIndividualReceipt.contains('contribution_date')) {
      const dateValue = this.frmIndividualReceipt.get('contribution_date').value;
      if (dateValue) {
        this._getContributionAggregate(dateValue);
      }
    }
  }

  /**
   * Populate the fields in the form with the values from the selected contact.
   *
   * @param $event The mouse event having selected the contact from the typeahead options.
   */
  // TODO use this when ready to handle both child and non-child - currently on child is calling it.
  public handleSelectedEntity_NEW($event: NgbTypeaheadSelectItemEvent, fieldName: string) {
    const entity = $event.item;

    const isChildForm = fieldName.startsWith(this._childFieldNamePrefix) ? true : false;

    if (isChildForm) {
      this._selectedEntityChild = this._utilService.deepClone(entity);
      this._selectedChangeWarnChild = {};
      this._isSelectedEntityAggregateChild = false;
    } else {
      this._selectedEntity = this._utilService.deepClone(entity);
      this._selectedChangeWarn = {};
      // this._isSelectedEntityAggregate = false;
    }

    if (isChildForm) {
      if (fieldName === this._childFieldNamePrefix + 'entity_name') {
        this.frmIndividualReceipt.patchValue({ 'child*donor_cmte_id': entity.cmte_id }, { onlySelf: true });
      }
      if (fieldName === this._childFieldNamePrefix + 'donor_cmte_id') {
        this.frmIndividualReceipt.patchValue({ 'child*entity_name': entity.cmte_name }, { onlySelf: true });
      }

      if (fieldName === this._childFieldNamePrefix + 'donor_cmte_name') {
        this.frmIndividualReceipt.patchValue({ 'child*donor_cmte_id': entity.cmte_id }, { onlySelf: true });
      }
      if (fieldName === this._childFieldNamePrefix + 'donor_cmte_id') {
        this.frmIndividualReceipt.patchValue({ 'child*donor_cmte_name': entity.cmte_name }, { onlySelf: true });
      }

      this.frmIndividualReceipt.patchValue({ 'child*street_1': entity.street_1 }, { onlySelf: true });
      this.frmIndividualReceipt.patchValue({ 'child*street_2': entity.street_2 }, { onlySelf: true });
      this.frmIndividualReceipt.patchValue({ 'child*city': entity.city }, { onlySelf: true });
      this.frmIndividualReceipt.patchValue({ 'child*state': entity.state }, { onlySelf: true });
      this.frmIndividualReceipt.patchValue({ 'child*zip_code': entity.zip_code }, { onlySelf: true });
      this.frmIndividualReceipt.patchValue({ 'child*occupation': entity.occupation }, { onlySelf: true });
      this.frmIndividualReceipt.patchValue({ 'child*employer': entity.employer }, { onlySelf: true });
    } else {
      if (fieldName === 'first_name' || fieldName === 'last_name') {
        // populate individual name fields
        this.frmIndividualReceipt.patchValue({ last_name: entity.last_name }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ first_name: entity.first_name }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ middle_name: entity.middle_name }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ prefix: entity.prefix }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ suffix: entity.suffix }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ street_1: entity.street_1 }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ street_2: entity.street_2 }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ city: entity.city }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ state: entity.state }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ zip_code: entity.zip_code }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ occupation: entity.occupation }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ employer: entity.employer }, { onlySelf: true });
      } else if (fieldName === 'entity_name' || fieldName === 'donor_cmte_id') {
        // populate org/committee fields
        if (fieldName === 'entity_name') {
          this.frmIndividualReceipt.patchValue({ donor_cmte_id: entity.cmte_id }, { onlySelf: true });
        }
        if (fieldName === 'donor_cmte_id') {
          this.frmIndividualReceipt.patchValue({ entity_name: entity.cmte_name }, { onlySelf: true });
        }
        this.frmIndividualReceipt.patchValue({ street_1: entity.street_1 }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ street_2: entity.street_2 }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ city: entity.city }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ state: entity.state }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ zip_code: entity.zip_code }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ occupation: entity.occupation }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ employer: entity.employer }, { onlySelf: true });
      }
    }
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

  public checkForMemoCode(fieldName: string) {
    const isChildForm = fieldName.startsWith(this._childFieldNamePrefix) ? true : false;
    if (isChildForm) {
      return this.memoCodeChild;
    } else {
      return this.memoCode;
    }
  }

  public doContributionDateChange(fieldName: string) {
    console.log('date has changed!');
    const isChildForm = fieldName.startsWith(this._childFieldNamePrefix) ? true : false;
    if (this.frmIndividualReceipt.contains('contribution_date')) {
      const dateValue = this.frmIndividualReceipt.get('contribution_date').value;
      if (!dateValue) {
        return;
      }
      if (this._selectedEntity) {
        if (this._selectedEntity.entity_id) {
          const contribDate =
            this._utilService.formatDate(dateValue);
          this._getContributionAggregate(contribDate);
        }
      }
    }
  }

  /**
   * Obtain the Report ID from local storage.
   */
  private _getReportIdFromStorage() {
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

  private getFormFields(): void {
    console.log('get transaction type form fields ' + this.transactionType);
    this._receiptService.getDynamicFormFields(this._formType, this.transactionType).subscribe(res => {
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
            if (res.data.hasOwnProperty('entityTypes')) {
              if (Array.isArray(res.data.entityTypes)) {
                this.entityTypes = res.data.entityTypes;
                if (this.entityTypes) {
                  for (const field of this.entityTypes) {
                    // If API sets selected to true it can be used to set the default.
                    // If none are set, use the first.
                    if (field.selected) {
                      this.selectedEntityType = field;
                    }
                  }
                  if (!this.selectedEntityType) {
                    if (this.entityTypes.length > 0) {
                      this.selectedEntityType = this.entityTypes[0];
                    }
                  }
                }
                this._entityTypeDefault = this.selectedEntityType;
                this.frmIndividualReceipt.patchValue(
                  { entity_type: this.selectedEntityType.entityTypeDescription },
                  { onlySelf: true }
                );
              }
            }
          } // typeof res.data
        } // res.hasOwnProperty('data')
      } // res
    });
  }

  public handleEntityTypeChange(entityTypeCode: any, col: any, entityType: any) {
    for (const entityTypeObj of this.entityTypes) {
      if (entityTypeObj.entityType === entityTypeCode) {
        entityTypeObj.selected = true;
        this.selectedEntityType = entityTypeObj;
        this.frmIndividualReceipt.patchValue({ entity_type: entityTypeCode }, { onlySelf: true });
      } else {
        entityTypeObj.selected = false;
      }
    }

    // set validations based on the selected org type
    if (this.selectedEntityType.group === 'org-group') {
      this.frmIndividualReceipt.controls['last_name'].setValidators([Validators.nullValidator]);
      this.frmIndividualReceipt.controls['last_name'].updateValueAndValidity();
      this.frmIndividualReceipt.controls['first_name'].setValidators([Validators.nullValidator]);
      this.frmIndividualReceipt.controls['first_name'].updateValueAndValidity();

      this.frmIndividualReceipt.controls['entity_name'].setValidators([Validators.required]);
      this.frmIndividualReceipt.controls['entity_name'].updateValueAndValidity();
    } else {
      this.frmIndividualReceipt.controls['last_name'].setValidators([Validators.required]);
      this.frmIndividualReceipt.controls['last_name'].updateValueAndValidity();
      this.frmIndividualReceipt.controls['first_name'].setValidators([Validators.required]);
      this.frmIndividualReceipt.controls['first_name'].updateValueAndValidity();

      this.frmIndividualReceipt.controls['entity_name'].setValidators([Validators.nullValidator]);
      this.frmIndividualReceipt.controls['entity_name'].updateValueAndValidity();
    }
  }

  private _populateFormForEditOrView(editOrView: any) {
    // The action here is the same as the this.scheduleAction
    // using the field from the message in case there is a race condition with Input().
    if (editOrView !== null) {
      if (editOrView.transactionModel) {
        const formData: TransactionModel = editOrView.transactionModel;

        this._transactionToEdit = formData;

        // TODO property names are not the same in TransactionModel
        // as they are when the selectedEntity is populated from
        // the auto-lookup / core/autolookup_search_contacts API.
        // Mapping may need to be added here.  See transactions service
        // mapToServerFields(model: TransactionModel) as it may
        // be used or cloned to a mapping method in the contact.service.
        this._selectedEntity = formData;
        this._selectedChangeWarn = {};

        // TODO need to handle child data once passed
        this._selectedEntityChild = editOrView.childTransactionModel ? editOrView.childTransactionModel : null;
        this._selectedChangeWarnChild = {};

        this.transactionType = formData.transactionTypeIdentifier;

        this._setFormDataValues();
      }
    }
  }

  /**
   * When editing a transaction, set the form values.
   */
  private _setFormDataValues() {
    const formData = this._transactionToEdit;

    const nameArray = formData.name.split(',');
    const firstName = nameArray[1] ? nameArray[1].trim() : null;
    const lastName = nameArray[0] ? nameArray[0].trim() : null;
    const middleName = nameArray[2] ? nameArray[2].trim() : null;
    const prefix = nameArray[3] ? nameArray[3].trim() : null;
    const suffix = nameArray[4] ? nameArray[4].trim() : null;

    const amountString = formData.amount ? formData.amount.toString() : '';
    this._contributionAmount = amountString;

    // TODO How will this work when transaction was from a form with child like Earmark Receipts?
    // this._contributionAmountChlid = formData.?????;

    this.frmIndividualReceipt.patchValue({ first_name: firstName }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ last_name: lastName }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ middle_name: middleName }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ prefix: prefix }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ suffix: suffix }, { onlySelf: true });

    this.frmIndividualReceipt.patchValue({ street_1: formData.street }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ street_2: formData.street2 }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ city: formData.city }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ state: formData.state }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ zip_code: formData.zip }, { onlySelf: true });

    this.frmIndividualReceipt.patchValue({ employer: formData.contributorEmployer }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ occupation: formData.contributorOccupation }, { onlySelf: true });

    this.frmIndividualReceipt.patchValue({ contribution_date: formData.date }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ contribution_amount: formData.amount }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ contribution_aggregate: formData.aggregate }, { onlySelf: true });

    if (formData.memoCode === this._memoCodeValue) {
      this.memoCode = true;
      this.frmIndividualReceipt.patchValue({ memo_code: this._memoCodeValue }, { onlySelf: true });
    }

    if (formData['child*memoCode'] === this._memoCodeValue) {
      this.memoCode = true;
      this.frmIndividualReceipt.patchValue({ 'child*memo_code': this._memoCodeValue }, { onlySelf: true });
    }

    this.frmIndividualReceipt.patchValue({ purpose_description: formData.purposeDescription }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ memo_text: formData.memoText }, { onlySelf: true });
  }

  /**
   * Determine if the field should be shown when the org type is toggled.
   */
  public isToggleShow(col: any) {
    if (!this.selectedEntityType) {
      return true;
    }
    if (!col.toggle) {
      return true;
    }
    if (this.selectedEntityType.group === col.entityGroup || !col.entityGroup) {
      return true;
    } else {
      return false;
    }
  }

  public isMemoCodeReadOnly(fieldName: string) {
    if (this.isFieldName(fieldName, 'memo_code')) {
      const isChildField = fieldName.startsWith(this._childFieldNamePrefix) ? true : false; 
      if (isChildField) { 
        return this._readOnlyMemoCodeChild;
      } else {
        return this._readOnlyMemoCode;
      }
    }
    return false;
  }

  private _clearFormValues(): void {
    this._selectedEntity = null;
    this._selectedEntityChild = null;
    this._selectedChangeWarn = {};
    this._selectedChangeWarnChild = {};
    this._contributionAggregateValue = 0.0;
    this._contributionAggregateValueChild = 0.0;
    this.memoCode = false;
    this.memoCodeChild = false;
    this._readOnlyMemoCode = false;
    this._readOnlyMemoCodeChild = false;
    this.frmIndividualReceipt.reset();

    if (this.frmIndividualReceipt.contains('entity_type')) {
      this.selectedEntityType = this._entityTypeDefault;
      this.frmIndividualReceipt.patchValue(
        { entity_type: this.selectedEntityType.entityTypeDescription },
        { onlySelf: true }
      );
    }
  }

  /**
   * Auto populate parent purpose with child names fields or child purpose
   * with parent name fields
   */
  public populatePurpose(fieldName: string) {

    if (this.transactionType !== 'EAR_REC') {
      return;
    }
    const isChildField = fieldName.startsWith(this._childFieldNamePrefix) ? true : false;
    if (isChildField) {
      if (!this.frmIndividualReceipt.contains('purpose_description')) {
        return;
      }
    } else {
      if (!this.frmIndividualReceipt.contains('child*purpose_description')) {
        return;
      }
    }
    if (isChildField) {
      const childPrefix = this._childFieldNamePrefix;
      let lastName = '';
      // type ahead fields need to be checked for objects
      if (this.frmIndividualReceipt.contains(childPrefix + 'last_name')) {
        const lastNameObject = this.frmIndividualReceipt.get(childPrefix + 'last_name').value;

        if (lastNameObject && typeof lastNameObject !== 'string') {
          // it's an object as a result of the ngb-typeahead
          lastName = lastNameObject[childPrefix + 'last_name'];
        } else {
          lastName = lastNameObject;
          lastName = lastName && typeof lastName === 'string' ? lastName.trim() : '';
        }
      }

      let firstName = '';
      if (this.frmIndividualReceipt.contains(childPrefix + 'first_name')) {
        const firstNameObject = this.frmIndividualReceipt.get(childPrefix + 'first_name').value;;

        if (firstNameObject && typeof firstNameObject !== 'string') {
          // it's an object as a result of the ngb-typeahead
          firstName = firstNameObject[childPrefix + 'first_name'];
        } else {
          firstName = firstNameObject;
          firstName = firstName && typeof firstName === 'string' ? firstName.trim() : '';
        }
      }

      let prefix = '';
      if (this.frmIndividualReceipt.contains(childPrefix + 'prefix')) {
        prefix = this.frmIndividualReceipt.get(childPrefix + 'prefix').value;
        prefix = prefix && typeof prefix === 'string' ? prefix.trim() : '';
      }
      let middleName = '';
      if (this.frmIndividualReceipt.contains(childPrefix + 'middle_name')) {
        middleName = this.frmIndividualReceipt.get(childPrefix + 'middle_name').value;
        middleName = middleName && typeof middleName === 'string' ? middleName.trim() : '';
      }
      let suffix = '';
      if (this.frmIndividualReceipt.contains(childPrefix + 'suffix')) {
        suffix = this.frmIndividualReceipt.get(childPrefix + 'suffix').value;
        suffix = suffix && typeof suffix === 'string' ? suffix.trim() : '';
      }

      let purpose = 'Earmarked for';
      const nameArray = [];
      if (prefix) {
        nameArray.push(prefix);
      }
      if (firstName) {
        nameArray.push(firstName);
      }
      if (middleName) {
        nameArray.push(middleName);
      }
      if (lastName) {
        nameArray.push(lastName);
      }
      if (suffix) {
        nameArray.push(suffix);
      }
      for (const field of nameArray) {
        purpose += ' ' + field;
      }

      console.log('purpose is: ' + purpose);
      this.frmIndividualReceipt.patchValue({ 'child*purpose_description': purpose },
      { onlySelf: true });
    } else {
      let lastName = '';
      // type ahead fields need to be checked for objects
      if (this.frmIndividualReceipt.contains('last_name')) {
        const lastNameObject = this.frmIndividualReceipt.get('last_name').value;

        if (lastNameObject && typeof lastNameObject !== 'string') {
          // it's an object as a result of the ngb-typeahead
          lastName = lastNameObject.last_name;
        } else {
          lastName = lastNameObject;
          lastName = lastName && typeof lastName === 'string' ? lastName.trim() : '';
        }
      }

      let firstName = '';
      if (this.frmIndividualReceipt.contains('first_name')) {
        const firstNameObject = this.frmIndividualReceipt.get('first_name').value;;

        if (firstNameObject && typeof firstNameObject !== 'string') {
          // it's an object as a result of the ngb-typeahead
          firstName = firstNameObject.first_name;
        } else {
          firstName = firstNameObject;
          firstName = firstName && typeof firstName === 'string' ? firstName.trim() : '';
        }
      }

      let prefix = '';
      if (this.frmIndividualReceipt.contains('prefix')) {
        prefix = this.frmIndividualReceipt.get('prefix').value;
        prefix = prefix && typeof prefix === 'string' ? prefix.trim() : '';
      }
      let middleName = '';
      if (this.frmIndividualReceipt.contains('middle_name')) {
        middleName = this.frmIndividualReceipt.get('middle_name').value;
        middleName = middleName && typeof middleName === 'string' ? middleName.trim() : '';
      }
      let suffix = '';
      if (this.frmIndividualReceipt.contains('suffix')) {
        suffix = this.frmIndividualReceipt.get('suffix').value;
        suffix = suffix && typeof suffix === 'string' ? suffix.trim() : '';
      }

      // const purpose = `Earmarked for ${prefix} ${firstName} ${middleName} ${lastName} ${suffix}`;
      let purpose = 'Earmarked for';
      const nameArray = [];
      if (prefix) {
        nameArray.push(prefix);
      }
      if (firstName) {
        nameArray.push(firstName);
      }
      if (middleName) {
        nameArray.push(middleName);
      }
      if (lastName) {
        nameArray.push(lastName);
      }
      if (suffix) {
        nameArray.push(suffix);
      }
      for (const field of nameArray) {
        purpose += ' ' + field;
      }

      console.log('purpose is: ' + purpose);
      this.frmIndividualReceipt.patchValue({ 'child*purpose_description': purpose },
      { onlySelf: true });
    }
  }

  private _getContributionAggregate(contribDate: string) {
    const reportId = this._getReportIdFromStorage();
    this._receiptService.getContributionAggregate(reportId, this._selectedEntity.entity_id,
        this.transactionType, contribDate).subscribe(res => {
      // Add the UI val for Contribution Amount to the Contribution Aggregate for the
      // Entity selected from the typeahead list.

      let contributionAmount = this.frmIndividualReceipt.get('contribution_amount').value;
      contributionAmount = contributionAmount ? contributionAmount : 0;
      // remove commas
      if (typeof contributionAmount === 'string') {
        contributionAmount = contributionAmount.replace(/,/g, ``);
      }

      // TODO make this a class variable for contributionAmountChange() to add to.
      let contributionAggregate: string = String(res.contribution_aggregate);
      contributionAggregate = contributionAggregate ? contributionAggregate : '0';

      const total: number = parseFloat(contributionAmount) + parseFloat(contributionAggregate);
      const value: string = this._decimalPipe.transform(total, '.2-2');

      console.log(`contributionAMount: + ${contributionAmount} + contributionAggregate:
          ${contributionAggregate} = ${total}`);
      console.log(`value = ${value}`);

      this.frmIndividualReceipt.patchValue({ contribution_aggregate: value }, { onlySelf: true });

      // Store the entity aggregate to be added to the contribution amount
      // if it changes in the UI.  See contributionAmountChange();
      this._contributionAggregateValue = parseFloat(contributionAggregate);
    });
  }

  // Use this when ready to handle both child and non-child
  private _getContributionAggregate_NEW(contributionDate: string, fieldName: string) {
    console.log('transaction type from input is ' + this.transactionType);
    const isChildForm = fieldName.startsWith(this._childFieldNamePrefix) ? true : false;

    let entityId = null;
    if (isChildForm) {
      entityId = this._selectedEntityChild.entity_id;
    } else {
      entityId = this._selectedEntity.entity_id;
    }

    const reportId = this._getReportIdFromStorage();
    this._receiptService.getContributionAggregate(reportId, entityId,
      this.transactionType, contributionDate).subscribe(res => {
      // Add the UI val for Contribution Amount to the Contribution Aggregate for the
      // Entity selected from the typeahead list.

      // TODO make this 1 method code for child/non-child with variable for the distinction
      if (isChildForm) {
        let contributionAmount = this.frmIndividualReceipt.get('child*contribution_amount').value;
        contributionAmount = contributionAmount ? contributionAmount : 0;

        // TODO make this a class variable for contributionAmountChange() to add to.
        let contributionAggregate: string = String(res.contribution_aggregate);
        contributionAggregate = contributionAggregate ? contributionAggregate : '0';

        const total: number = parseFloat(contributionAmount) + parseFloat(contributionAggregate);
        const value: string = this._decimalPipe.transform(total, '.2-2');

        console.log(`child contributionAMount: + ${contributionAmount} + contributionAggregate:
            ${contributionAggregate} = ${total}`);
        console.log(`value = ${value}`);

        this.frmIndividualReceipt.patchValue({ 'child*contribution_aggregate': value }, { onlySelf: true });

        // Store the entity aggregate to be added to the contribution amount
        // if it changes in the UI.  See contributionAmountChange();
        this._contributionAggregateValueChild = parseFloat(contributionAggregate);
      } else {
        // Add the UI val for Contribution Amount to the Contribution Aggregate for the
        // Entity selected from the typeahead list.

        let contributionAmount = this.frmIndividualReceipt.get('contribution_amount').value;
        contributionAmount = contributionAmount ? contributionAmount : 0;

        // TODO make this a class variable for contributionAmountChange() to add to.
        let contributionAggregate: string = String(res.contribution_aggregate);
        contributionAggregate = contributionAggregate ? contributionAggregate : '0';

        const total: number = parseFloat(contributionAmount) + parseFloat(contributionAggregate);
        const value: string = this._decimalPipe.transform(total, '.2-2');

        console.log(`contributionAMount: + ${contributionAmount} + contributionAggregate:
            ${contributionAggregate} = ${total}`);
        console.log(`value = ${value}`);

        this.frmIndividualReceipt.patchValue({ contribution_aggregate: value }, { onlySelf: true });

        // Store the entity aggregate to be added to the contribution amount
        // if it changes in the UI.  See contributionAmountChange();
        this._contributionAggregateValue = parseFloat(contributionAggregate);
      }

      // TODO need to handle child form apart from non-child
    });
  }
}
