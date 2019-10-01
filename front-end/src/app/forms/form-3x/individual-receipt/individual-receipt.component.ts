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
  HostListener,
  OnChanges
} from '@angular/core';
import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { FormBuilder, FormGroup, FormControl, NgForm, Validators, AbstractControl, ValidatorFn } from '@angular/forms';
import { NgbTooltipConfig, NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../../environments/environment';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { UtilService } from '../../../shared/utils/util.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { IndividualReceiptService } from './individual-receipt.service';
import { f3xTransactionTypes } from '../../../shared/interfaces/FormsService/FormsService';
import { alphaNumeric } from '../../../shared/utils/forms/validation/alpha-numeric.validator';
import { floatingPoint } from '../../../shared/utils/forms/validation/floating-point.validator';
import { validatePurposeInKindRequired, IN_KIND } from '../../../shared/utils/forms/validation/purpose.validator';
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';
import { Observable, Subscription, interval, timer } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, delay, pairwise } from 'rxjs/operators';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { ConfirmModalComponent, ModalHeaderClassEnum } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { TransactionModel } from '../../transactions/model/transaction.model';
import { F3xMessageService } from '../service/f3x-message.service';
import { ScheduleActions } from './schedule-actions.enum';
import { hasOwnProp } from 'ngx-bootstrap/chronos/utils/type-checks';
import { TransactionsMessageService } from '../../transactions/service/transactions-message.service';
import { ActiveView } from '../../transactions/transactions.component';
import { validateAggregate } from 'src/app/shared/utils/forms/validation/aggregate.validator';
import { validateAmount } from 'src/app/shared/utils/forms/validation/amount.validator';
import { ContributionDateValidator } from 'src/app/shared/utils/forms/validation/contribution-date.validator';
import { ContactsService } from 'src/app/contacts/service/contacts.service';
import { trigger, transition, style, animate, state } from '@angular/animations';
import { heLocale } from 'ngx-bootstrap';

export enum SaveActions {
  saveOnly = 'saveOnly',
  saveForReturnToParent = 'saveForReturnToParent',
  saveForReturnToNewParent = 'saveForReturnToNewParent',
  saveForAddSub = 'saveForAddSub',
  saveForEditSub = 'saveForEditSub',
  updateOnly = 'updateOnly'
}

@Component({
  selector: 'f3x-individual-receipt',
  templateUrl: './individual-receipt.component.html',
  styleUrls: ['./individual-receipt.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe]
  // encapsulation: ViewEncapsulation.None
})
export class IndividualReceiptComponent implements OnInit, OnDestroy, OnChanges {
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
  private _loadFormFieldsSubscription: Subscription;

  public editMode: boolean = true;
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
  public electionTypes: any = [];
  public candidateOfficeTypes: any = [];
  public entityTypes: any = [];
  public subTransactionInfo: any;
  public multipleSubTransactionInfo: any[] = [];
  public selectedEntityType: any;
  public subTransactions: any[];
  public formType = '';
  public editScheduleAction: ScheduleActions = ScheduleActions.edit;
  public addScheduleAction: ScheduleActions = ScheduleActions.add;
  public addSubScheduleAction: ScheduleActions = ScheduleActions.addSubTransaction;
  public memoDropdownSize = null;

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
  private _selectedEntityChild: any;
  private _selectedCandidate: any;
  private _selectedCandidateChild: any;
  private _selectedChangeWarn: any;
  private _selectedChangeWarnChild: any;
  private _selectedCandidateChangeWarn: any;
  private _selectedCandidateChangeWarnChild: any;
  private _contributionAmountMax: number;
  private _transactionToEdit: TransactionModel;
  private readonly _childFieldNamePrefix = 'child*';
  private _readOnlyMemoCode: boolean;
  private _readOnlyMemoCodeChild: boolean;
  private _entityTypeDefault: any;
  private _parentTransactionId: string;
  private _employerOccupationRequired: boolean;
  private prePopulateFieldArray: Array<any>;

  constructor(
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _formService: FormsService,
    private _receiptService: IndividualReceiptService,
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
    private _f3xMessageService: F3xMessageService,
    private _transactionsMessageService: TransactionsMessageService,
    private _contributionDateValidator: ContributionDateValidator
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';

    this._populateFormSubscription = this._f3xMessageService.getPopulateFormMessage().subscribe(message => {
      if (message.hasOwnProperty('key')) {
        // See message sender for mesage properties
        switch (message.key) {
          case 'fullForm':
            this._prePopulateFormForEditOrView(message.transactionModel);
            break;
          case 'field':
            // set the field array to class variable to be referenced once the formGroup
            // has been loaded by the get dynamic fields API call.
            if (message) {
              if (message.fieldArray) {
                this.prePopulateFieldArray = message.fieldArray;
              }
            }
            break;
          default:
            console.log('message key not supported: ' + message.key);
        }
      }
    });

    this._clearFormSubscription = this._f3xMessageService.getInitFormMessage().subscribe(message => {
      this._clearFormValues();
    });

    this._loadFormFieldsSubscription = this._f3xMessageService.getLoadFormFieldsMessage().subscribe(message => {
      this._getFormFields();
      this._validateTransactionDate();
    });
  }

  ngOnInit(): void {
    this._selectedEntity = null;
    this._selectedChangeWarn = null;
    this._selectedEntityChild = null;
    this._selectedChangeWarnChild = null;
    this._selectedCandidate = null;
    this._selectedCandidateChangeWarn = null;
    this._selectedCandidateChild = null;
    this._selectedCandidateChangeWarnChild = null;
    this._readOnlyMemoCode = false;
    this._readOnlyMemoCodeChild = false;
    this._transactionToEdit = null;
    this._contributionAggregateValue = 0.0;
    this._contributionAggregateValueChild = 0.0;
    this._contributionAmount = '';
    this._contributionAmountChlid = '';
    this._employerOccupationRequired = false;
    this.memoDropdownSize = null;

    this._getCandidateOfficeTypes();

    this.formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.editMode = this._activatedRoute.snapshot.queryParams.edit
      ? this._activatedRoute.snapshot.queryParams.edit
      : true;
    localStorage.setItem(`form_${this.formType}_saved`, JSON.stringify({ saved: true }));
    localStorage.setItem('Receipts_Entry_Screen', 'Yes');

    this._messageService.clearMessage();

    this._reportType = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));

    if (this._reportType === null || typeof this._reportType === 'undefined') {
      this._reportType = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type_backup`));
    }

    this.frmIndividualReceipt = this._fb.group({});
    // added check to avoid script error
    if (this.frmIndividualReceipt && this.frmIndividualReceipt.controls['contribution_date']) {
      this.frmIndividualReceipt.controls['contribution_date'].setValidators([
        this._contributionDateValidator.contributionDate(this.cvgStartDate, this.cvgEndDate),
        Validators.required
      ]);
    }
  }

  /**
   * Apply the validation rules when aggregate changes.
   */
  private _listenForAggregateChanges(): void {
    this.frmIndividualReceipt.get('contribution_aggregate').valueChanges.subscribe(val => {
      // All validators are replaced here.  Currently the only validator functions
      // for employer and occupation is the validateAggregate().  The max length is enforced
      // in the template as an element attribute max.
      // If additoanl validators need to be added here, there is no replace function in ng,
      // they must be cleared and all set in an array again. Onc solution is to
      // store the validators in a class variable array, add this function to the array, and set the
      // controls's setValidator() using the full array.  Or just get the validations from the
      // dynamic form fields again in this.formFields[].

      const employerControl = this.frmIndividualReceipt.get('employer');
      employerControl.setValidators([validateAggregate(val, true, 'employer')]);
      employerControl.updateValueAndValidity();

      const occupationControl = this.frmIndividualReceipt.get('occupation');
      occupationControl.setValidators([validateAggregate(val, true, 'occupation')]);
      occupationControl.updateValueAndValidity();
    });
  }

  public ngOnChanges() {
    if (this.editMode) {
      this._prepareForm();
      // added check to avoid script error
      if (this.frmIndividualReceipt && this.frmIndividualReceipt.controls['contribution_date']) {
        this.frmIndividualReceipt.controls['contribution_date'].setValidators([
          this._contributionDateValidator.contributionDate(this.cvgStartDate, this.cvgEndDate),
          Validators.required
        ]);
      }
    } else {
      this._dialogService
      .confirm(
        'This report has been filed with the FEC. If you want to change, you must Amend the report',
        ConfirmModalComponent,
        'Warning',
        true,
        ModalHeaderClassEnum.warningHeader,
        null,
        'Return to Reports'
      )
        .then(res => {
          if (res === 'okay') {
            this.ngOnInit();
          } else if (res === 'cancel') {
            this._router.navigate(['/reports']);
          }
        });
    }
  }

  private _prepareForm() {
    if (this.selectedOptions) {
      if (this.selectedOptions.length >= 1) {
        this.formVisible = true;
      }
    }

    this._getTransactionType();

    this._validateTransactionDate();

    if (localStorage.getItem(`form_${this.formType}_report_type`) !== null) {
      this._reportType = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));

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
            if (localStorage.getItem(`form_${this.formType}_report_type`) !== null) {
              this._reportType = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
              if (this._reportType.hasOwnProperty('cvgEndDate') && this._reportType.hasOwnProperty('cvgStartDate')) {
                if (
                  typeof this._reportType.cvgStartDate === 'string' &&
                  typeof this._reportType.cvgEndDate === 'string'
                ) {
                  this.cvgStartDate = this._reportType.cvgStartDate;
                  this.cvgEndDate = this._reportType.cvgEndDate;

                  this.frmIndividualReceipt.controls['contribution_date'].setValidators([
                    this._contributionDateValidator.contributionDate(this.cvgStartDate, this.cvgEndDate),
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
    this._loadFormFieldsSubscription.unsubscribe();
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
    this._employerOccupationRequired = false;

    fields.forEach(el => {
      if (el.hasOwnProperty('cols') && el.cols) {
        el.cols.forEach(e => {
          formGroup[e.name] = new FormControl(e.value || null, this._mapValidators(e.validation, e.name, e.value));
          if (this.isFieldName(e.name, 'contribution_amount') || this.isFieldName(e.name, 'expenditure_amount')) {
            if (e.validation) {
              this._contributionAmountMax = e.validation.max ? e.validation.max : 0;
            }
          }
          if (this.isFieldName(e.name, 'memo_code')) {
            const isChildForm = e.name.startsWith(this._childFieldNamePrefix) ? true : false;
            memoCodeValue = e.value;
            if (memoCodeValue === this._memoCodeValue) {
              if (isChildForm) {
                this.memoCodeChild = true;
              } else {
                this.memoCode = true;
              }
            }
            if (isChildForm) {
              this._readOnlyMemoCodeChild = e.isReadonly;
            } else {
              this._readOnlyMemoCode = e.isReadonly;
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
      this._setFormDataValues(this._transactionToEdit.transactionId, this._transactionToEdit.apiCall);
    }

    // get form data API is passing X for memo code value.
    // Set it to value from dynamic forms as some should be checked and disabled by default.
    this._setMemoCodeForForm();

    if (this.frmIndividualReceipt.get('election_code')) {
      this.frmIndividualReceipt.patchValue({ election_code: null }, { onlySelf: true });
    }
    const childElectCodeName = this._childFieldNamePrefix + 'election_code';
    if (this.frmIndividualReceipt.contains(childElectCodeName)) {
      const vo = {};
      vo[childElectCodeName] = null;
      this.frmIndividualReceipt.patchValue(vo, { onlySelf: true });
    }
    if (this._employerOccupationRequired) {
      this._listenForAggregateChanges();
    }

    // // Rather than set a flag as a check for setting up a change listener
    // // on the formGroup control field for purpose as done with the employerOccupation,
    // // iterate over the dynamic api form fields for the purpose.  The flag option
    // // can be fragile with forgetting to init the flag.  And with purpose, the value
    // // from the API is needed.
    // fields.forEach(el => {
    //   if (el.hasOwnProperty('cols') && el.cols) {
    //     el.cols.forEach((e:any) => {
    //     });
    //   }
    // });
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
  private _mapValidators(validators: any, fieldName: string, fieldValue: string): Array<any> {
    const formValidators = [];

    /**
     * For adding field specific validation that's custom.
     * This block adds zip code, and contribution date validation.
     * Required for occupation and employer will be dependent on aggregate.
     */
    if (this.isFieldName(fieldName, 'zip_code')) {
      formValidators.push(alphaNumeric());
    } else if (this.isFieldName(fieldName, 'contribution_date') || this.isFieldName(fieldName, 'expenditure_date')) {
      this._reportType = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
      if (this._reportType !== null) {
        const cvgStartDate: string = this._reportType.cvgStartDate;
        const cvgEndDate: string = this._reportType.cvgEndDate;

        formValidators.push(this._contributionDateValidator.contributionDate(cvgStartDate, cvgEndDate));
      }
    }
    // else if (this.isFieldName(fieldName, 'purpose_description')) {
    //   // Purpose description is required when prefix with In-kind #
    //   if (fieldValue) {
    //     if (fieldValue.trim().length > 0) {
    //       formValidators.push(validatePurposeInKindRequired(fieldName, fieldValue));
    //     }
    //   }
    // }

    if (validators) {
      for (const validation of Object.keys(validators)) {
        if (validation === 'required') {
          if (validators[validation]) {
            // occuaption and employer will be required dpending on aggregate
            if (fieldName !== 'employer' && fieldName !== 'occupation') {
              formValidators.push(Validators.required);
            } else {
              this._employerOccupationRequired = true;
            }
          }
        } else if (validation === 'min') {
          if (validators[validation] !== null) {
            formValidators.push(Validators.minLength(validators[validation]));
          }
        } else if (validation === 'max') {
          if (validators[validation] !== null) {
            if (
              fieldName !== 'contribution_amount' &&
              fieldName !== 'expenditure_amount' &&
              fieldName !== 'contribution_aggregate'
            ) {
              formValidators.push(Validators.maxLength(validators[validation]));
            } else {
              formValidators.push(validateAmount());
            }
          }
        } else if (validation === 'dollarAmount' || validation === 'dollarAmountNegative') {
          if (validators[validation] !== null) {
            formValidators.push(floatingPoint());
          }
        }
      }
    }
    return formValidators;
  }

  /**
   * Validates the transaction date selected.
   */
  private _validateTransactionDate(): void {
    let dateField: string;
    let amountField: string;
    // checking for expenditure_date in form parameter
    // If expenditure_date is not found setting contribution_date and contribution_amount
    if (this.frmIndividualReceipt) {
      if (this.frmIndividualReceipt.controls['expenditure_date']) {
        dateField = 'expenditure_date';
        amountField = 'expenditure_amount';
      } else {
        dateField = 'contribution_date';
        amountField = 'contribution_amount';
      }
    }

    this._reportType = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));

    if (this._reportType !== null) {
      const cvgStartDate: string = this._reportType.cvgStartDate;
      const cvgEndDate: string = this._reportType.cvgEndDate;

      if (this.memoCode) {
        this.frmIndividualReceipt.controls[dateField].setValidators([Validators.required]);

        this.frmIndividualReceipt.controls[dateField].updateValueAndValidity();
      } else {
        if (this.frmIndividualReceipt.controls[dateField]) {
          this.frmIndividualReceipt.controls[dateField].setValidators([
            this._contributionDateValidator.contributionDate(cvgStartDate, cvgEndDate),
            Validators.required
          ]);

          this.frmIndividualReceipt.controls[dateField].updateValueAndValidity();
        }
      }
      if (this.memoCodeChild) {
        this.frmIndividualReceipt.controls['child*' + dateField].setValidators([Validators.required]);

        this.frmIndividualReceipt.controls['child*' + dateField].updateValueAndValidity();
      } else {
        if (this.frmIndividualReceipt.controls['child*' + dateField]) {
          this.frmIndividualReceipt.controls['child*' + dateField].setValidators([
            this._contributionDateValidator.contributionDate(cvgStartDate, cvgEndDate),
            Validators.required
          ]);

          this.frmIndividualReceipt.controls['child*' + dateField].updateValueAndValidity();
        }
      }
    }

    if (this.frmIndividualReceipt) {
      if (this.frmIndividualReceipt.controls[amountField]) {
        this.frmIndividualReceipt.controls[amountField].setValidators([floatingPoint(), Validators.required]);

        this.frmIndividualReceipt.controls[amountField].updateValueAndValidity();
      }

      if (this.frmIndividualReceipt.controls['contribution_aggregate']) {
        this.frmIndividualReceipt.controls['contribution_aggregate'].setValidators([floatingPoint()]);

        this.frmIndividualReceipt.controls['contribution_aggregate'].updateValueAndValidity();
      }

      // Do same as above for child amount
      if (this.frmIndividualReceipt.controls['child*' + amountField]) {
        this.frmIndividualReceipt.controls['child*' + amountField].setValidators([
          floatingPoint(),
          Validators.required
        ]);

        this.frmIndividualReceipt.controls['child*' + amountField].updateValueAndValidity();
      }

      if (this.frmIndividualReceipt.controls['child*contribution_aggregate']) {
        this.frmIndividualReceipt.controls['child*contribution_aggregate'].setValidators([floatingPoint()]);

        this.frmIndividualReceipt.controls['child*contribution_aggregate'].updateValueAndValidity();
      }
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
    let dateField: string;
    let amountField: string;
    // checking for expenditure_date in form parameter
    // If expenditure_date is not found setting contribution_date and contribution_amount
    if (this.frmIndividualReceipt.controls['expenditure_date']) {
      dateField = 'expenditure_date';
      amountField = 'expenditure_amount';
    } else {
      dateField = 'contribution_date';
      amountField = 'contribution_amount';
    }
    if (isChildForm) {
      if (checked) {
        this.memoCodeChild = checked;
        this.frmIndividualReceipt.controls['child*memo_code'].setValue(this._memoCodeValue);
        this.frmIndividualReceipt.controls['child*' + dateField].setValidators([Validators.required]);

        this.frmIndividualReceipt.controls['child*' + dateField].updateValueAndValidity();
      } else {
        this._validateTransactionDate();
        this.memoCodeChild = checked;
        this.frmIndividualReceipt.controls['child*memo_code'].setValue(null);
        this.frmIndividualReceipt.controls['child*' + dateField].setValidators([
          this._contributionDateValidator.contributionDate(this.cvgStartDate, this.cvgEndDate),
          Validators.required
        ]);

        this.frmIndividualReceipt.controls[dateField].updateValueAndValidity();
      }
    } else {
      if (checked) {
        this.memoCode = checked;
        this.frmIndividualReceipt.controls['memo_code'].setValue(this._memoCodeValue);
        this.frmIndividualReceipt.controls[dateField].setValidators([Validators.required]);

        this.frmIndividualReceipt.controls[dateField].updateValueAndValidity();
      } else {
        this._validateTransactionDate();
        this.memoCode = checked;
        this.frmIndividualReceipt.controls['memo_code'].setValue(null);
        this.frmIndividualReceipt.controls[dateField].setValidators([
          this._contributionDateValidator.contributionDate(this.cvgStartDate, this.cvgEndDate),
          Validators.required
        ]);

        this.frmIndividualReceipt.controls[dateField].updateValueAndValidity();
      }
    }

    const contributionAmountNum = this._convertFormattedAmountToDecimal(null);
    let transactionDate = null;
    if (this.frmIndividualReceipt.get(dateField)) {
      transactionDate = this.frmIndividualReceipt.get(dateField).value;
    }
    const aggregateValue: string = this._receiptService.determineAggregate(
      this._contributionAggregateValue,
      contributionAmountNum,
      this.scheduleAction,
      this.memoCode,
      this._selectedEntity,
      this._transactionToEdit,
      this.transactionType,
      this._isSubOfParent(),
      transactionDate
    );
    this.frmIndividualReceipt.patchValue({ contribution_aggregate: aggregateValue }, { onlySelf: true });
  }

  /**
   * Updates the contribution aggregate field once contribution ammount is entered.
   *
   * @param      {Object}  e         The event object.
   * @param      {string}  fieldName The name of the field
   */
  public contributionAmountChange(e: any, fieldName: string, negativeAmount: boolean): void {
    const isChildForm = fieldName.startsWith(this._childFieldNamePrefix) ? true : false;
    let contributionAmount: string = e.target.value;

    // default to 0 when no value
    contributionAmount = contributionAmount ? contributionAmount : '0';

    // remove commas
    contributionAmount = contributionAmount.replace(/,/g, ``);

    // determine if negative, truncate if > max
    contributionAmount = this._transformAmount(contributionAmount, this._contributionAmountMax);

    let contributionAggregate: string = null;
    if (isChildForm) {
      this._contributionAmountChlid = contributionAmount;
      contributionAggregate = String(this._contributionAggregateValueChild);
    } else {
      this._contributionAmount = contributionAmount;
      contributionAggregate = String(this._contributionAggregateValue);
    }

    let contributionAmountNum = parseFloat(contributionAmount);
    // Amount is converted to negative for Return / Void / Bounced
    if (negativeAmount) {
      contributionAmountNum = -Math.abs(contributionAmountNum);
      this._contributionAmount = String(contributionAmountNum);
    }

    const amountValue: string = this._decimalPipe.transform(contributionAmountNum, '.2-2');

    if (isChildForm) {
      if (this.frmIndividualReceipt.get('expenditure_amount')) {
        this.frmIndividualReceipt.patchValue({ 'child*expenditure_amount': amountValue }, { onlySelf: true });
      } else {
        this.frmIndividualReceipt.patchValue({ 'child*contribution_amount': amountValue }, { onlySelf: true });
      }
    } else {
      if (this.frmIndividualReceipt.get('expenditure_amount')) {
        this.frmIndividualReceipt.patchValue({ expenditure_amount: amountValue }, { onlySelf: true });
      } else {
        this.frmIndividualReceipt.patchValue({ contribution_amount: amountValue }, { onlySelf: true });
      }
    }
    let transactionDate = null;
    if (this.frmIndividualReceipt.get('contribution_date')) {
      transactionDate = this.frmIndividualReceipt.get('contribution_date').value;
    }
    const aggregateValue: string = this._receiptService.determineAggregate(
      this._contributionAggregateValue,
      contributionAmountNum,
      this.scheduleAction,
      this.memoCode,
      this._selectedEntity,
      this._transactionToEdit,
      this.transactionType,
      this._isSubOfParent(),
      transactionDate
    );

    if (isChildForm) {
      this.frmIndividualReceipt.patchValue({ 'child*contribution_aggregate': aggregateValue }, { onlySelf: true });
    } else {
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
   * Gets the transaction type.
   */
  private _getTransactionType(): void {
    const transactionType: any = JSON.parse(localStorage.getItem(`form_${this.formType}_transaction_type`));

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
        this._getFormFields();
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
      if (this._isIgnoreKey($event.key)) {
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
      col.name === this._childFieldNamePrefix + 'entity_name' ||
      col.name === this._childFieldNamePrefix + 'donor_cmte_id' ||
      col.name === this._childFieldNamePrefix + 'beneficiary_cmte_id' ||
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
    } else if (this._isCandidateField(col)) {
      this.handleFormFieldKeyupCandidate($event, col);
    } else if (this.isFieldName(col.name, 'contribution_amount')) {
      this.contributionAmountKeyup($event);
    } else {
      return null;
    }
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

  public handleFormFieldKeyupCandidate($event: any, col: any) {
    if (!col) {
      return;
    }
    if (!col.name) {
      return;
    }
    if ($event.key) {
      if (this._isIgnoreKey($event.key)) {
        return;
      }
    }
    const isChildField = col.name.startsWith(this._childFieldNamePrefix) ? true : false;
    // if (
    //   this.isFieldName(col.name, 'cand_last_name') ||
    //   this.isFieldName(col.name, 'cand_first_name') ||
    //   this.isFieldName(col.name, 'cand_middle_name') ||
    //   this.isFieldName(col.name, 'cand_prefix') ||
    //   this.isFieldName(col.name, 'cand_suffix') ||
    //   this.isFieldName(col.name, 'cand_office') ||
    //   this.isFieldName(col.name, 'cand_office_state') ||
    //   this.isFieldName(col.name, 'cand_office_district')
    // ) {
    if (this._isCandidateField(col)) {
      if (isChildField) {
        if (this._selectedCandidateChild) {
          this.showWarnCandidate(col.text, col.name);
        }
      } else {
        if (this._selectedCandidate) {
          this.showWarnCandidate(col.text, col.name);
        }
      }
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
   * Show a warning indicating fields may not be changed for entities loaded from the database
   * for Candidate.
   *
   * @param fieldLabel Field Label to show in the message
   */
  private showWarnCandidate(fieldLabel: string, name: string) {
    const isChildForm = name.startsWith(this._childFieldNamePrefix) ? true : false;

    // only show on first key
    if (isChildForm) {
      if (this._selectedCandidateChangeWarnChild[name] === name) {
        return;
      }
    } else {
      if (this._selectedCandidateChangeWarn[name] === name) {
        return;
      }
    }

    const message = `Please note that if you update contact information it will be updated in the Contacts file.`;
    this._dialogService.confirm(message, ConfirmModalComponent, 'Warning!', false).then(res => {});

    if (isChildForm) {
      this._selectedCandidateChangeWarnChild[name] = name;
    } else {
      this._selectedCandidateChangeWarn[name] = name;
    }
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

  public customStateSearchFn(term: string, state: any) {
    term = term.toLowerCase();
    return state.name.toLowerCase().indexOf(term) > -1 || state.code.toLowerCase() === term;
  }

  /**
   * Handle warnings when state changes.
   */
  public handleStateChange(stateOption: any, col: any) {
    const isChildForm = col.name.startsWith(this._childFieldNamePrefix) ? true : false;

    if (isChildForm) {
      if (this._selectedEntityChild) {
        this.showWarn(col.text, this._childFieldNamePrefix + 'state');
      } else if (this._selectedCandidateChild) {
        this.showWarnCandidate(col.text, col.name);
      }
    } else {
      if (this._selectedEntity) {
        this.showWarn(col.text, 'state');
      } else if (this._selectedCandidate) {
        this.showWarnCandidate(col.text, col.name);
      }
    }
  }

  /**
   *
   * @param item
   * @param col
   */
  public handleCandOfficeChange(item: any, col: any) {
    const isChildForm = col.name.startsWith(this._childFieldNamePrefix) ? true : false;
    if (isChildForm) {
      if (this._selectedCandidateChild) {
        this.showWarnCandidate(col.text, col.name);
      }
    } else {
      if (this._selectedCandidate) {
        this.showWarnCandidate(col.text, col.name);
      }
    }
  }

  /**
   * Set the Election Code on the form when it changes in the UI.
   */
  public handleElectionCodeChange(item: any, col: any) {
    // TODO change template to use the ng-select inputs as done with
    // candidate office.

    const isChildForm = col.name.startsWith(this._childFieldNamePrefix) ? true : false;

    let fieldNamePrefix = '';
    if (isChildForm) {
      fieldNamePrefix = this._childFieldNamePrefix;
    }
    const description = fieldNamePrefix + 'election_other_description';

    // Description is required when Other is selected
    if (item.electionType === 'O') {
      if (this.frmIndividualReceipt.contains(description)) {
        this.frmIndividualReceipt.controls[description].setValidators([Validators.required]);
        this.frmIndividualReceipt.controls[description].updateValueAndValidity();
      }
    } else {
      if (this.frmIndividualReceipt.contains(description)) {
        this.frmIndividualReceipt.controls[description].setValidators([Validators.nullValidator]);
        this.frmIndividualReceipt.controls[description].updateValueAndValidity();
      }
    }
  }

  /**
   * Vaidates the form on submit.
   */
  private _doValidateReceipt(saveAction: SaveActions): Observable<any> {
    // TODO because parent is saved automatically when user clicks add child, we
    // may not want to save it if unchanged.  Check form status for untouched.

    if (this.frmIndividualReceipt.valid) {
      const receiptObj: any = {};

      for (const field in this.frmIndividualReceipt.controls) {
        if (field === 'contribution_date' || field === 'expenditure_date') {
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
        } else if (this.isFieldName(field, 'purpose_description') || this.isFieldName(field, 'expenditure_purpose')) {
          const preTextHiddenField = this._findHiddenField('name', 'pretext');
          let preText = '';
          if (preTextHiddenField) {
            preText = preTextHiddenField.value ? preTextHiddenField.value : '';
          }
          const purposeVal = this.frmIndividualReceipt.get(field).value;
          if (purposeVal) {
            receiptObj[field] = preText + this.frmIndividualReceipt.get(field).value;
          } else {
            receiptObj[field] = this.frmIndividualReceipt.get(field).value;
          }
        } else if (
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
        } else if (field === 'donor_cmte_id' || field === 'beneficiary_cmte_id') {
          // added this condition as some times we are getting entire json object
          // when we perform auto lookup.
          // TODO we might need to revisit to see if we need this condition
          const typeAheadField = this.frmIndividualReceipt.get(field).value;
          if (typeAheadField && typeof typeAheadField !== 'string') {
            receiptObj[field] = typeAheadField['cmte_id'];
          } else {
            receiptObj[field] = typeAheadField;
          }
        } else if (field === 'contribution_amount' || field === 'expenditure_amount') {
          receiptObj[field] = this._contributionAmount;
        } else if (field === this._childFieldNamePrefix + 'contribution_amount') {
          receiptObj[field] = this._contributionAmountChlid;
        } else {
          receiptObj[field] = this.frmIndividualReceipt.get(field).value;
        }
      }

      // for each entity ID comes from the dynamic form fields as setEntityIdTo.
      // If setEntityIdTo not sent by API, default to entity_id.
      if (this._transactionToEdit) {
        this.hiddenFields.forEach((el: any) => {
          if (el.name === 'transaction_id') {
            el.value = this._transactionToEdit.transactionId;
            // If Transaction Id is present, setting Action to Edit
            this.scheduleAction = ScheduleActions.edit;
          } else if (el.name === 'api_call') {
            el.value = this._transactionToEdit.apiCall;
          }
        });
      }

      this.hiddenFields.forEach(el => {
        receiptObj[el.name] = el.value;
      });

      // If entity ID exist, the transaction will be added to the existing entity by the API
      // Otherwise it will create a new Entity.  Since there may be more than 1 entity
      // saved in a form, entity IDs must be unique for each.  The name of the property

      this._setReceiptObjectEntityId(this._selectedEntity, receiptObj, false);
      this._setReceiptObjectEntityId(this._selectedEntityChild, receiptObj, true);
      this._setReceiptObjectEntityId(this._selectedCandidate, receiptObj, false);
      this._setReceiptObjectEntityId(this._selectedCandidateChild, receiptObj, true);

      if (this._transactionToEdit) {
        if (receiptObj['entity_id'] === null || receiptObj['entity_id'] === undefined) {
          receiptObj['entity_id'] = this._transactionToEdit.entityId;
        }
      }
      // There is a race condition with populating hiddenFields
      // and receiving transaction data to edit from the message service.
      // If editing, set transaction ID at this point to avoid race condition issue.
      // Two transactions one screen is messing up..
      // we might need to revisit to fix the two transactions one screen

      // set the back ref id for save on a sub tran.
      if (this._parentTransactionId && this.scheduleAction === ScheduleActions.addSubTransaction) {
        receiptObj.back_ref_transaction_id = this._parentTransactionId;
      }

      localStorage.setItem(`form_${this.formType}_receipt`, JSON.stringify(receiptObj));

      this._receiptService.saveSchedule(this.formType, this.scheduleAction).subscribe(res => {
        if (res) {
          this._transactionToEdit = null;
          // commented below condition to update summary (Third navigation)
          // irrespective of memo code condition
          //if (res.hasOwnProperty('memo_code')) {
          //if (typeof res.memo_code === 'object') {
          //if (res.memo_code === null) {
          this._receiptService.getSchedule(this.formType, res).subscribe(resp => {
            const message: any = {
              formType: this.formType,
              totals: resp
            };

            this._messageService.sendMessage(message);
          });
          //}
          //}
          //}

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

          // Replace this with clearForm() if possible
          this._formSubmitted = true;
          this.memoCode = false;
          this.memoCodeChild = false;
          this.frmIndividualReceipt.reset();
          this._setMemoCodeForForm();
          this._selectedEntity = null;
          this._selectedChangeWarn = null;
          this._selectedEntityChild = null;
          this._selectedChangeWarnChild = null;
          this._selectedCandidate = null;
          this._selectedCandidateChangeWarn = null;
          this._selectedCandidateChild = null;
          this._selectedCandidateChangeWarnChild = null;
          // Replace this with clearForm() if possible - END

          localStorage.removeItem(`form_${this.formType}_receipt`);
          localStorage.setItem(`form_${this.formType}_saved`, JSON.stringify({ saved: true }));
          window.scrollTo(0, 0);

          let transactionId = null;
          if (res.hasOwnProperty('transaction_id')) {
            transactionId = res.transaction_id;
          } else {
            console.log('schedA save has no transaction_id property');
          }

          // If save is for user click addChild, we are saving parent on behalf of the user
          // before presenting a new sub tran to add.  Save parent id and emit to show new child form.
          if (saveAction === SaveActions.saveForAddSub) {
            if (this.scheduleAction === ScheduleActions.add || this.scheduleAction === ScheduleActions.edit) {
              this._parentTransactionId = transactionId;
            }
            const addSubTransEmitObj: any = {
              form: {},
              direction: 'next',
              step: 'step_3',
              previousStep: 'step_2',
              transactionTypeText: this.subTransactionInfo.subTransactionTypeDescription,
              transactionType: this.subTransactionInfo.subTransactionType,
              apiCall: this.subTransactionInfo.api_call,
              action: ScheduleActions.addSubTransaction
            };
            const prePopulateFieldArray = this._checkForEarmarkPurposePrePopulate(res);
            if (prePopulateFieldArray) {
              addSubTransEmitObj.prePopulateFieldArray = prePopulateFieldArray;
            }
            this.status.emit(addSubTransEmitObj);
          } else if (saveAction === SaveActions.saveForEditSub) {
            this._progressToChild(ScheduleActions.edit, res);
          } else if (saveAction === SaveActions.saveForReturnToParent) {
            this.returnToParent(ScheduleActions.edit);
          } else if (saveAction === SaveActions.saveForReturnToNewParent) {
            this.returnToParent(ScheduleActions.add);
          } else if (saveAction === SaveActions.updateOnly) {
            this.viewTransactions();
          } else {
            // reset the parent ID if action is NOT for add sub transaction.
            // if (this.scheduleAction !== ScheduleActions.addSubTransaction) {
            let resetParentId = true;
            if (this.subTransactionInfo) {
              if (this.subTransactionInfo.isParent === false) {
                resetParentId = false;
              }
            }
            if (resetParentId) {
              this._parentTransactionId = null;
              this.subTransactions = [];
            }
          }
          // setting default action to add/addSub when we save transaction
          // as it should not be for edit after save.
          if (!this.isEarmark()) {
            if (this._isSubOfParent()) {
              this.scheduleAction = ScheduleActions.addSubTransaction;
            } else {
              this.scheduleAction = ScheduleActions.add;
            }
          }
        }
      });
    } else {
      this.frmIndividualReceipt.markAsDirty();
      this.frmIndividualReceipt.markAsTouched();
      localStorage.setItem(`form_${this.formType}_saved`, JSON.stringify({ saved: false }));
      window.scrollTo(0, 0);

      const invalid = [];
      const controls = this.frmIndividualReceipt.controls;
      for (const name in controls) {
        if (controls[name].invalid) {
          invalid.push(name);
          console.log('invalid form field on submit = ' + name);
        }
      }
      return Observable.of('invalid');
    }
  }

  /**
   * Used by Earmarks or any other transaction where the
   * "2 transactions / 1 screen" requirement is needed.
   */
  public saveAndReturnToNewParent(): void {
    this._doValidateReceipt(SaveActions.saveForReturnToNewParent);
  }

  /**
   * Save a child transaction and show its parent.  If the form has not been
   * changed (dirty) then don't save and just show parent.
   */
  public saveAndReturnToParent(): void {
    if (!this.frmIndividualReceipt.dirty) {
      this.returnToParent(ScheduleActions.edit);
    } else {
      this._doValidateReceipt(SaveActions.saveForReturnToParent);
    }
  }

  /**
   * Set CSS properties when the memo dropdown opens and closes.
   */
  public multipleMemoDropdownChanged(open: boolean) {
    if (open) {
      // TEMP hack for testing
      // this.multipleSubTransactionInfo.push(this.multipleSubTransactionInfo[0]);

      // 23 px for each item and add 40px for default.
      let size = this.multipleSubTransactionInfo ? this.multipleSubTransactionInfo.length : 0;
      size = size > 0 ? size * 23 + 40 : 0;
      this.memoDropdownSize = size + 'px';
    } else {
      this.memoDropdownSize = null;
    }
  }

  public saveForAddMemoSub(jfMemo: any): void {
    this.subTransactionInfo = jfMemo;
    this._doValidateReceipt(SaveActions.saveForAddSub);
  }

  public saveForAddSub(): void {
    this._doValidateReceipt(SaveActions.saveForAddSub);
  }

  public saveForAddEarmark(): void {
    this._doValidateReceipt(SaveActions.saveForAddSub);
  }

  public saveForEditEarmark(): void {
    this._doValidateReceipt(SaveActions.saveForEditSub);
  }

  public saveOnly(): void {
    this._doValidateReceipt(SaveActions.saveOnly);
  }

  public updateOnly(): void {
    this._doValidateReceipt(SaveActions.updateOnly);
  }

  private _progressToChild(scheduleAction: ScheduleActions, res: any): void {
    let childTransactionId = null;
    let apiCall = null;
    if (res.hasOwnProperty('child')) {
      if (Array.isArray(res.child)) {
        if (res.child.length > 0) {
          if (res.child[0].hasOwnProperty('transaction_id')) {
            childTransactionId = res.child[0].transaction_id;
          }
          if (res.child[0].hasOwnProperty('api_call')) {
            apiCall = res.child[0].api_call;
          }
        }
      }
    }

    if (childTransactionId && apiCall) {
      const transactionModel = new TransactionModel({});
      transactionModel.transactionId = childTransactionId;
      transactionModel.type = this.subTransactionInfo.subTransactionTypeDescription;
      transactionModel.transactionTypeIdentifier = this.subTransactionInfo.subTransactionType;
      transactionModel.apiCall = apiCall;
      this.memoCode = false;
      this.memoCodeChild = false;
      const emitObj: any = {
        form: {},
        direction: 'next',
        step: 'step_3',
        previousStep: 'step_2',
        transactionTypeText: this.subTransactionInfo.subTransactionTypeDescription,
        transactionType: this.subTransactionInfo.subTransactionType,
        action: scheduleAction
      };
      if (scheduleAction === ScheduleActions.edit) {
        emitObj.transactionDetail = { transactionModel: transactionModel };
      }
      this.status.emit(emitObj);
    }
  }

  /**
   * Return to the parent transaction from sub tran.
   */
  public returnToParent(scheduleAction: ScheduleActions): void {
    const transactionModel = new TransactionModel({});
    transactionModel.transactionId = this._parentTransactionId;
    transactionModel.type = this.subTransactionInfo.transactionTypeDescription;
    transactionModel.transactionTypeIdentifier = this.subTransactionInfo.transactionType;
    transactionModel.apiCall = this.subTransactionInfo.api_call;
    this.memoCode = false;
    this.memoCodeChild = false;
    const emitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      transactionTypeText: this.subTransactionInfo.transactionTypeDescription,
      transactionType: this.subTransactionInfo.transactionType,
      action: scheduleAction
    };
    if (scheduleAction === ScheduleActions.edit) {
      emitObj.transactionDetail = { transactionModel: transactionModel };
    }
    this.status.emit(emitObj);
  }

  private _setReceiptObjectEntityId(userSelectedEntity: any, receiptObj: any, isChild: boolean) {
    // added condition to check if entity_id already exist in receiptObj to avoid overriding entity ID's
    if (userSelectedEntity && !receiptObj.entity_id) {
      if (userSelectedEntity.setEntityIdTo) {
        receiptObj[userSelectedEntity.setEntityIdTo] = userSelectedEntity.entity_id;
      } else {
        receiptObj.entity_id = userSelectedEntity.entity_id;
      }
    }
  }

  private _setSetEntityIdTo(userSelectedEntity: any, col: any) {
    if (col.setEntityIdTo) {
      userSelectedEntity.setEntityIdTo = col.setEntityIdTo;
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
    let reportId = this._receiptService.getReportIdFromStorage(this.formType);
    console.log('reportId', reportId);

    if (!reportId) {
      reportId = '0';
    }
    localStorage.setItem(`form_${this.formType}_view_transaction_screen`, 'Yes');
    localStorage.setItem('Transaction_Table_Screen', 'Yes');
    this._transactionsMessageService.sendLoadTransactionsMessage(reportId);

    this._router.navigate([`/forms/form/${this.formType}`], {
      queryParams: { step: 'transactions', reportId: reportId }
    });
  }

  public printPreview(): void {
    this._reportTypeService.printPreview('individual_receipt', this.formType);
  }
  public ImportTransactions(): void {
    alert('Import transaction is not yet supported');
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
   * Populate the fields in the form with the values from the selected Candidate.
   *
   * @param $event The mouse event having selected the contact from the typeahead options.
   */
  public handleSelectedCandidate($event: NgbTypeaheadSelectItemEvent, col: any) {
    // FNE-1438 Need to detect if tab key caused the event. And don't load if true.
    // TODO need a way to determine if key was tab.

    const entity = $event.item;

    const isChildForm = col.name.startsWith(this._childFieldNamePrefix) ? true : false;
    let namePrefix = '';

    if (isChildForm) {
      this._selectedCandidateChild = this._utilService.deepClone(entity);
      this._setSetEntityIdTo(this._selectedCandidateChild, col);
      this._selectedCandidateChangeWarnChild = {};
      namePrefix = this._childFieldNamePrefix;
    } else {
      this._selectedCandidate = this._utilService.deepClone(entity);
      this._setSetEntityIdTo(this._selectedCandidate, col);
      this._selectedCandidateChangeWarn = {};
    }

    const fieldNames = [];
    fieldNames.push('cand_last_name');
    fieldNames.push('cand_first_name');
    fieldNames.push('cand_middle_name');
    fieldNames.push('cand_prefix');
    fieldNames.push('cand_suffix');
    fieldNames.push('cand_office');
    fieldNames.push('cand_office_state');
    fieldNames.push('cand_office_district');
    fieldNames.push('cand_election_year');
    fieldNames.push('beneficiary_cand_id');
    this._patchFormFields(fieldNames, entity, namePrefix);
    // setting Beneficiary Candidate Entity Id to hidden variable
    const beneficiaryCandEntityIdHiddenField = this._findHiddenField('name', 'beneficiary_cand_entity_id');
    if (beneficiaryCandEntityIdHiddenField) {
      beneficiaryCandEntityIdHiddenField.value = entity.beneficiary_cand_entity_id;
    }
    // for (const field of fieldNames) {
    //   const patch = {};
    //   patch[namePrefix + field] = entity[field];
    //   this.frmIndividualReceipt.patchValue(patch, { onlySelf: true });
    // }
  }

  /**
   * Populate the fields in the form with the values from the selected individual.
   *
   * @param $event The mouse event having selected the contact from the typeahead options.
   */
  public handleSelectedIndividual($event: NgbTypeaheadSelectItemEvent, col: any) {
    const entity = $event.item;

    const isChildForm = col.name.startsWith(this._childFieldNamePrefix) ? true : false;
    let namePrefix = '';

    if (isChildForm) {
      this._selectedEntityChild = this._utilService.deepClone(entity);
      this._setSetEntityIdTo(this._selectedEntityChild, col);
      this._selectedChangeWarnChild = {};
      namePrefix = this._childFieldNamePrefix;
    } else {
      this._selectedEntity = this._utilService.deepClone(entity);
      this._setSetEntityIdTo(this._selectedEntity, col);
      this._selectedChangeWarn = {};
    }

    const fieldNames = [];
    fieldNames.push('last_name');
    fieldNames.push('first_name');
    fieldNames.push('middle_name');
    fieldNames.push('prefix');
    fieldNames.push('suffix');
    fieldNames.push('street_1');
    fieldNames.push('street_2');
    fieldNames.push('city');
    fieldNames.push('state');
    fieldNames.push('zip_code');
    fieldNames.push('occupation');
    fieldNames.push('employer');
    this._patchFormFields(fieldNames, entity, namePrefix);

    // If date is selected, get the aggregate.
    if (this.frmIndividualReceipt.contains('contribution_date')) {
      const dateValue = this.frmIndividualReceipt.get('contribution_date').value;
      const contribDate = this._utilService.formatDate(dateValue);
      if (contribDate) {
        this._getContributionAggregate(contribDate, this._selectedEntity.entity_id, null);
      }
    }
  }

  private _patchFormFields(fieldNames: string[], entity: any, namePrefix: string) {
    if (fieldNames) {
      for (const fieldName of fieldNames) {
        const patch = {};
        patch[namePrefix + fieldName] = entity[fieldName];
        this.frmIndividualReceipt.patchValue(patch, { onlySelf: true });
      }
    }
  }

  /**
   * Populate the fields in the form with the values from the selected contact.
   *
   * @param $event The mouse event having selected the contact from the typeahead options.
   */
  // TODO use the factory method approach a done with individual to avoid hard coding
  // child name field prefix and it's let error prone.
  public handleSelectedOrg($event: NgbTypeaheadSelectItemEvent, col: any) {
    const entity = $event.item;

    const isChildForm = col.name.startsWith(this._childFieldNamePrefix) ? true : false;

    let namePrefix = '';
    if (isChildForm) {
      this._selectedEntityChild = this._utilService.deepClone(entity);
      this._setSetEntityIdTo(this._selectedEntityChild, col);
      this._selectedChangeWarnChild = {};
      namePrefix = this._childFieldNamePrefix;
    } else {
      this._selectedEntity = this._utilService.deepClone(entity);
      this._setSetEntityIdTo(this._selectedEntity, col);
      this._selectedChangeWarn = {};
    }

    // These field names map to the same name in the form
    const fieldNames = [];
    fieldNames.push('street_1');
    fieldNames.push('street_2');
    fieldNames.push('city');
    fieldNames.push('state');
    fieldNames.push('zip_code');
    fieldNames.push('occupation');
    fieldNames.push('employer');
    fieldNames.push('cand_last_name');
    fieldNames.push('cand_first_name');
    fieldNames.push('cand_middle_name');
    fieldNames.push('cand_suffix');
    fieldNames.push('cand_prefix');
    fieldNames.push('cand_office');
    fieldNames.push('cand_office_state');
    fieldNames.push('cand_office_district');
    this._patchFormFields(fieldNames, entity, namePrefix);
    // setting Beneficiary Candidate Entity Id to hidden variable
    const beneficiaryCandEntityIdHiddenField = this._findHiddenField('name', 'beneficiary_cand_entity_id');
    if (beneficiaryCandEntityIdHiddenField) {
      beneficiaryCandEntityIdHiddenField.value = entity.beneficiary_cand_entity_id;
    }
    // These fields names do not map to the same name in the form
    const fieldName = col.name;
    if (isChildForm) {
      if (fieldName === this._childFieldNamePrefix + 'entity_name') {
        if (this.frmIndividualReceipt.contains('child*donor_cmte_id')) {
          this.frmIndividualReceipt.patchValue({ 'child*donor_cmte_id': entity.cmte_id }, { onlySelf: true });
        }
        if (this.frmIndividualReceipt.contains('child*beneficiary_cmte_id')) {
          this.frmIndividualReceipt.patchValue({ 'child*beneficiary_cmte_id': entity.cmte_id }, { onlySelf: true });
        }
      }
      if (
        fieldName === this._childFieldNamePrefix + 'donor_cmte_id' ||
        fieldName === this._childFieldNamePrefix + 'beneficiary_cmte_id'
      ) {
        this.frmIndividualReceipt.patchValue({ 'child*entity_name': entity.cmte_name }, { onlySelf: true });
      }

      if (fieldName === this._childFieldNamePrefix + 'donor_cmte_name') {
        this.frmIndividualReceipt.patchValue({ 'child*donor_cmte_id': entity.cmte_id }, { onlySelf: true });
      }
      if (fieldName === this._childFieldNamePrefix + 'beneficiary_cmte_name') {
        this.frmIndividualReceipt.patchValue({ 'child*beneficiary_cmte_id': entity.cmte_id }, { onlySelf: true });
      }
      if (fieldName === this._childFieldNamePrefix + 'donor_cmte_id') {
        this.frmIndividualReceipt.patchValue({ 'child*donor_cmte_name': entity.cmte_name }, { onlySelf: true });
      }
      if (fieldName === this._childFieldNamePrefix + 'beneficiary_cmte_id') {
        this.frmIndividualReceipt.patchValue({ 'child*beneficiary_cmte_name': entity.cmte_name }, { onlySelf: true });
      }
    } else {
      if (fieldName === 'entity_name' || fieldName === 'donor_cmte_id' || fieldName === 'beneficiary_cmte_id') {
        // populate org/committee fields
        if (fieldName === 'entity_name') {
          if (this.frmIndividualReceipt.controls['donor_cmte_id']) {
            this.frmIndividualReceipt.patchValue({ donor_cmte_id: entity.cmte_id }, { onlySelf: true });
          } else if (this.frmIndividualReceipt.controls['beneficiary_cmte_id']) {
            this.frmIndividualReceipt.patchValue({ beneficiary_cmte_id: entity.cmte_id }, { onlySelf: true });
          }
        }
        if (fieldName === 'donor_cmte_id' || fieldName === 'beneficiary_cmte_id') {
          this.frmIndividualReceipt.patchValue({ entity_name: entity.cmte_name }, { onlySelf: true });
        }
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

  /**
   * Apply business rules when date changes.
   *
   * @param fieldName the date field ane in the form.
   */
  public dateChange(fieldName: string) {
    console.log('date has changed!');
    const isChildForm = fieldName.startsWith(this._childFieldNamePrefix) ? true : false;
    if (isChildForm) {
      if (this.frmIndividualReceipt.contains(this._childFieldNamePrefix + fieldName)) {
        const dateValue = this.frmIndividualReceipt.get(this._childFieldNamePrefix + fieldName).value;
        if (!dateValue) {
          return;
        }
        /*
          Memo transactions should not validate for transaction date
        */
        if (this.memoCode) {
          this.frmIndividualReceipt.controls[this._childFieldNamePrefix + fieldName].setValidators([
            Validators.required
          ]);
          this.frmIndividualReceipt.controls[this._childFieldNamePrefix + fieldName].updateValueAndValidity();
        }
        if (this._selectedEntityChild) {
          const entityId = this._selectedEntityChild.entity_id ? this._selectedEntityChild.entity_id : null;
          const cmteId = this._selectedEntityChild.cmte_id ? this._selectedEntityChild.cmte_id : null;
          const contribDate = this._utilService.formatDate(dateValue);
          if (fieldName === 'contribution_date') {
            this._getContributionAggregate(contribDate, entityId, cmteId);
          }
        }
      }
    } else {
      if (this.frmIndividualReceipt.contains(fieldName)) {
        const dateValue = this.frmIndividualReceipt.get(fieldName).value;
        if (!dateValue) {
          return;
        }
        /*
          Memo transactions should not validate for transaction date
        */
        if (this.memoCode) {
          this.frmIndividualReceipt.controls[fieldName].setValidators([Validators.required]);
          this.frmIndividualReceipt.controls[fieldName].updateValueAndValidity();
        }
        if (this._selectedEntity) {
          if (this._selectedEntity.entity_id) {
            const contribDate = this._utilService.formatDate(dateValue);
            if (fieldName === 'contribution_date') {
              this._getContributionAggregate(contribDate, this._selectedEntity.entity_id, null);
            }
          }
        }
      }
    }
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

  private _getFormFields(): void {
    console.log('get transaction type form fields ' + this.transactionType);

    // init some of the dynamic form data for each call.
    // TODO may need to add others.
    this.subTransactionInfo = null;
    this.multipleSubTransactionInfo = null;
    this.subTransactions = [];
    this.memoDropdownSize = null;

    this._receiptService.getDynamicFormFields(this.formType, this.transactionType).subscribe(res => {
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
            if (res.data.hasOwnProperty('electionTypes')) {
              if (Array.isArray(res.data.electionTypes)) {
                this.electionTypes = res.data.electionTypes;
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
                    // If none are set, default to first.
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
                // expecting default entity type to be IND
                this.toggleValidationIndOrg(this.selectedEntityType.entityType);
                this._entityTypeDefault = this.selectedEntityType;
                this.frmIndividualReceipt.patchValue(
                  { entity_type: this.selectedEntityType.entityType },
                  { onlySelf: true }
                );
              }
            }
            if (res.data.hasOwnProperty('subTransactions')) {
              if (Array.isArray(res.data.subTransactions)) {
                if (res.data.subTransactions.length > 0) {
                  this.subTransactionInfo = res.data.subTransactions[0];
                  if (res.data.subTransactions.length > 1) {
                    this.multipleSubTransactionInfo = res.data.subTransactions;
                  }
                }
              }
            }
          } // typeof res.data
        } // res.hasOwnProperty('data')
      } // res
      this._prePopulateFormField(this.prePopulateFieldArray);
      this.prePopulateFieldArray = null;
    });
  }

  /**
   * Toggle fields in the form depending on entity type.
   */
  public handleEntityTypeChange(item: any, col: any, entityType: any) {
    // Set the selectedEntityType for the toggle method to check.
    for (const entityTypeObj of this.entityTypes) {
      if (entityTypeObj.entityType === item.entityType) {
        entityTypeObj.selected = true;
        this.selectedEntityType = entityTypeObj;
      } else {
        entityTypeObj.selected = false;
      }
    }

    if (item) {
      this.toggleValidationIndOrg(item.group);
    }
  }

  /**
   * Pre-populate form fields with values from the pre-populate array.
   *
   * @param fieldArray an array of field names and values
   */
  private _prePopulateFormField(fieldArray: Array<any>) {
    if (!fieldArray) {
      return;
    }
    if (!Array.isArray(fieldArray)) {
      return;
    }
    for (const field of fieldArray) {
      if (field.hasOwnProperty('name') && field.hasOwnProperty('value')) {
        if (this.frmIndividualReceipt.get(field.name)) {
          const patch = {};
          patch[field.name] = field.value;
          this.frmIndividualReceipt.patchValue(patch, { onlySelf: true });
        }
      }
    }
  }

  private _prePopulateFormForEditOrView(transactionDetail: any) {
    if (transactionDetail) {
      // The action on the message is the same as the this.scheduleAction from parent.
      // using the field from the message in case there is a race condition with Input().
      // If not provided, default to edit.
      if (transactionDetail.action) {
        if (transactionDetail.action in ScheduleActions) {
          this.scheduleAction = transactionDetail.action;
        } else {
          this.scheduleAction = ScheduleActions.edit;
        }
      }
      if (transactionDetail.transactionModel) {
        const formData: TransactionModel = transactionDetail.transactionModel;

        // TODO this data will come from the API not the transaction table
        // may need to set it after API for race condition problem when come from Reports.
        // For now it is sufficient just to set it with the transactionId.
        this._transactionToEdit = formData;

        // TODO property names are not the same in TransactionModel
        // as they are when the selectedEntity is populated from
        // the auto-lookup / core/autolookup_search_contacts API.
        // Mapping may need to be added here.  See transactions service
        // mapToServerFields(model: TransactionModel) as it may
        // be used or cloned to a mapping method in the contact.service.

        // TODO need to get the entity from the look up service using entity_id
        // this._selectedEntity = formData;
        this._selectedChangeWarn = {};

        // TODO need to handle child data once passed
        // this._selectedEntityChild = editOrView.childTransactionModel ? editOrView.childTransactionModel : null;
        this._selectedChangeWarnChild = {};

        // TODO need to handle candidate from child form once data is passed.
        // this._selectedCandidate = null; Do we need the actual data set or just boolean if there is data
        // For edit we can always show warning so we might not need to set the selectedAutolookup warn fields
        this._selectedCandidateChangeWarn = {};
        // this._selectedCandidateChild = null;
        this._selectedCandidateChangeWarnChild = {};

        // this.transactionType = formData.transactionTypeIdentifier;
        this._setFormDataValues(formData.transactionId, formData.apiCall);
      }
    }
  }

  /**
   * Set the values from the API in the form.
   *
   * @param transactionId
   */
  private _setFormDataValues(transactionId: string, apiCall: string) {
    const reportId = this._receiptService.getReportIdFromStorage(this.formType);
    this.subTransactions = [];
    this._receiptService.getDataSchedule(reportId, transactionId, apiCall).subscribe(res => {
      if (Array.isArray(res)) {
        for (const trx of res) {
          if (trx.hasOwnProperty('transaction_id')) {
            if (trx.transaction_id === transactionId) {
              if (trx.hasOwnProperty('child')) {
                if (Array.isArray(trx.child)) {
                  if (trx.child.length > 0) {
                    this._parentTransactionId = transactionId;
                    this.subTransactions = trx.child;
                    for (const subTrx of this.subTransactions) {
                      console.log('sub tran id ' + subTrx.transaction_id);
                    }
                  }
                }
              }
              for (const prop in trx) {
                if (trx.hasOwnProperty(prop)) {
                  // add to hidden fields
                  for (const hiddenField of this.hiddenFields) {
                    if (prop === hiddenField.name) {
                      hiddenField.value = trx[prop];
                    }
                  }
                  if (this.frmIndividualReceipt.get(prop)) {
                    if (this.isFieldName(prop, 'contribution_aggregate')) {
                      this._contributionAggregateValue = trx[prop];
                    }
                    if (this.isFieldName(prop, 'memo_code')) {
                      const memoCodeValue = trx[prop];
                      if (memoCodeValue === this._memoCodeValue) {
                        const isChildField = prop.startsWith(this._childFieldNamePrefix) ? true : false;
                        if (isChildField) {
                          this.memoCodeChild = true;
                        } else {
                          this.memoCode = true;
                        }
                      }
                    }
                    if (this.isFieldName(prop, 'purpose_description')) {
                      const preTextHiddenField = this._findHiddenField('name', 'pretext');
                      let preText = '';
                      if (preTextHiddenField) {
                        preText = preTextHiddenField.value ? preTextHiddenField.value : '';
                      }
                      if (preText) {
                        // remove it from the input field.  It will be readded on save.
                        if (trx[prop]) {
                          if (typeof trx[prop] === 'string') {
                            if (trx[prop].startsWith(preText)) {
                              trx[prop] = trx[prop].replace(preText, '');
                            }
                          }
                        }
                      }
                    }
                    const patch = {};
                    patch[prop] = trx[prop];
                    this.frmIndividualReceipt.patchValue(patch, { onlySelf: true });
                  }
                  if (prop === 'entity_id') {
                    this._selectedEntity = {};
                    this._selectedEntity.entity_id = trx[prop];
                  }
                  if (prop === 'entity_type') {
                    if (this.entityTypes) {
                      for (const field of this.entityTypes) {
                        if (trx[prop] === field.entityType) {
                          field.selected = true;
                          this.selectedEntityType = field;
                          this.toggleValidationIndOrg(trx[prop]);
                          break;
                        }
                      }
                    }
                  }
                  if (prop === this._childFieldNamePrefix + 'entity_id') {
                    this._selectedEntityChild = {};
                    this._selectedEntityChild.entity_id = trx[prop];
                  }
                  // TODO add for _selectedCandidate abd _selectedCandidateChild
                }
              }
              // loop through props again now that aggregate should be set
              // and apply contributionAMountChange() formatting, setting, etc.
              for (const prop in trx) {
                if (trx.hasOwnProperty(prop)) {
                  if (this.isFieldName(prop, 'contribution_amount') || this.isFieldName(prop, 'expenditure_amount')) {
                    const amount = trx[prop] ? trx[prop] : 0;
                    this.contributionAmountChange({ target: { value: amount.toString() } }, prop, false);
                  }
                }
              }
              this._validateTransactionDate();
            }
          }
        }
      }
    });
  }

  /**
   * Determine if the child transactions should be shown.
   */
  public isShowChildTransactions(): boolean {
    if (this.subTransactionInfo) {
      if (this.subTransactionInfo.isEarmark) {
        return false;
      }
    }
    if (this._isParentOfSub()) {
      if (this.subTransactions) {
        if (this.subTransactions.length > 0) {
          return true;
        }
      }
    }
    return false;
  }

  /**
   * Returns true if the transaction type is a parent of
   * a parent/ sub-transaction relationship.  It will return false for
   *  1) transaction types that are sub-transactions of a parent
   *  2) transaction types that have NO parent / sub-transaction relationship
   */
  private _isParentOfSub(): boolean {
    if (this.subTransactionInfo) {
      if (this.subTransactionInfo.isParent === true) {
        return true;
      }
    }
    return false;
  }

  /**
   * Returns true if the transaction type is a sub-transaction of
   * a parent/ sub-transaction relationship.  It will return false for
   *  1) transaction types that are parents of a parent / sub-transaction relationship
   *  2) transaction types that have NO parent / sub-transaction relationship
   */
  private _isSubOfParent(): boolean {
    if (this.subTransactionInfo) {
      if (this.subTransactionInfo.isParent === false) {
        return true;
      }
    }
    return false;
  }

  public isEarmark(): boolean {
    if (this.subTransactionInfo) {
      if (this.subTransactionInfo.isEarmark) {
        return true;
      }
    }
    return false;
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

  public showHideEntityType(entityTypeGroup: string) {}

  // public isMemoCodeReadOnly(fieldName: string) {
  //   if (this.isFieldName(fieldName, 'memo_code')) {
  //     const isChildField = fieldName.startsWith(this._childFieldNamePrefix) ? true : false;
  //     if (isChildField) {
  //       return this._readOnlyMemoCodeChild;
  //     } else {
  //       return this._readOnlyMemoCode;
  //     }
  //   }
  //   return false;
  // }

  private _clearFormValues(): void {
    this._transactionToEdit = null;

    this._selectedEntity = null;
    this._selectedEntityChild = null;
    this._selectedChangeWarn = {};
    this._selectedChangeWarnChild = {};

    this._selectedCandidate = null;
    this._selectedCandidateChangeWarn = null;
    this._selectedCandidateChild = null;
    this._selectedCandidateChangeWarnChild = null;

    this._contributionAggregateValue = 0.0;
    this._contributionAggregateValueChild = 0.0;
    this.memoCode = false;
    this.memoCodeChild = false;
    this._readOnlyMemoCode = false;
    this._readOnlyMemoCodeChild = false;
    this.frmIndividualReceipt.reset();
    if (this.frmIndividualReceipt.contains('entity_type')) {
      this.selectedEntityType = this._entityTypeDefault;
      this.frmIndividualReceipt.patchValue({ entity_type: this.selectedEntityType.entityType }, { onlySelf: true });
    }
    this.memoDropdownSize = null;
  }

  private toggleValidationIndOrg(entityType: string) {
    if (entityType === 'ORG' || entityType === 'org-group') {
      if (this.frmIndividualReceipt.controls['last_name']) {
        this.frmIndividualReceipt.controls['last_name'].setValidators([Validators.nullValidator]);
        this.frmIndividualReceipt.controls['last_name'].updateValueAndValidity();
      }
      if (this.frmIndividualReceipt.controls['first_name']) {
        this.frmIndividualReceipt.controls['first_name'].setValidators([Validators.nullValidator]);
        this.frmIndividualReceipt.controls['first_name'].updateValueAndValidity();
      }
      if (this.frmIndividualReceipt.controls['entity_name']) {
        this.frmIndividualReceipt.controls['entity_name'].setValidators([Validators.required]);
        this.frmIndividualReceipt.controls['entity_name'].updateValueAndValidity();
      }
    } else {
      if (this.frmIndividualReceipt.controls['last_name']) {
        this.frmIndividualReceipt.controls['last_name'].setValidators([Validators.required]);
        this.frmIndividualReceipt.controls['last_name'].updateValueAndValidity();
      }
      if (this.frmIndividualReceipt.controls['first_name']) {
        this.frmIndividualReceipt.controls['first_name'].setValidators([Validators.required]);
        this.frmIndividualReceipt.controls['first_name'].updateValueAndValidity();
      }
      if (this.frmIndividualReceipt.controls['entity_name']) {
        this.frmIndividualReceipt.controls['entity_name'].setValidators([Validators.nullValidator]);
        this.frmIndividualReceipt.controls['entity_name'].updateValueAndValidity();
      }
    }
  }

  /**
   * Auto populate parent purpose with child names fields or child purpose
   * with parent name fields
   */
  public populatePurpose(fieldName: string) {
    if (
      this.transactionType !== 'EAR_REC' &&
      this.transactionType !== 'CON_EAR_UNDEP' &&
      this.transactionType !== 'CON_EAR_DEP_1'
    ) {
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
    const candPrefix = 'cand_';
    if (isChildField) {
      // populate parent purpose with child candidate fields
      const childPrefix = this._childFieldNamePrefix + candPrefix;
      let lastName = '';
      // type ahead fields need to be checked for objects
      if (this.frmIndividualReceipt.contains(childPrefix + 'last_name')) {
        const lastNameObject = this.frmIndividualReceipt.get(childPrefix + 'last_name').value;

        if (lastNameObject && typeof lastNameObject !== 'string') {
          // it's an object as a result of the ngb-typeahead
          lastName = lastNameObject[candPrefix + 'last_name'];
        } else {
          lastName = lastNameObject;
          lastName = lastName && typeof lastName === 'string' ? lastName.trim() : '';
        }
      }

      let firstName = '';
      if (this.frmIndividualReceipt.contains(childPrefix + 'first_name')) {
        const firstNameObject = this.frmIndividualReceipt.get(childPrefix + 'first_name').value;

        if (firstNameObject && typeof firstNameObject !== 'string') {
          // it's an object as a result of the ngb-typeahead
          firstName = firstNameObject[candPrefix + 'first_name'];
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

      const purposePre = 'Earmarked for';
      let purpose = purposePre;
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
      if (purpose !== purposePre) {
        this.frmIndividualReceipt.patchValue({ purpose_description: purpose }, { onlySelf: true });
      }
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
        const firstNameObject = this.frmIndividualReceipt.get('first_name').value;

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

      const purposePre = 'Earmarked for';
      let purpose = purposePre;
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
      if (purpose !== purposePre) {
        this.frmIndividualReceipt.patchValue({ 'child*purpose_description': purpose }, { onlySelf: true });
      }
    }
  }

  private _convertFormattedAmountToDecimal(formatedAmount: string): number {
    if (!formatedAmount) {
      if (this.frmIndividualReceipt.get('expenditure_amount')) {
        formatedAmount = this.frmIndividualReceipt.get('expenditure_amount').value;
      } else {
        formatedAmount = this.frmIndividualReceipt.get('contribution_amount').value;
      }
    }
    if (typeof formatedAmount === 'string') {
      // remove commas
      formatedAmount = formatedAmount.replace(/,/g, ``);
      return parseFloat(formatedAmount);
    } else {
      return formatedAmount;
    }
  }

  private _getContributionAggregate(contribDate: string, entityId: number, cmteId: string) {
    const reportId = this._receiptService.getReportIdFromStorage(this.formType);
    this._receiptService
      .getContributionAggregate(reportId, entityId, cmteId, this.transactionType, contribDate)
      .subscribe(res => {
        const contributionAmountNum = this._convertFormattedAmountToDecimal(null);

        let contributionAggregate: string = String(res.contribution_aggregate);
        contributionAggregate = contributionAggregate ? contributionAggregate : '0';
        this._contributionAggregateValue = parseFloat(contributionAggregate);

        let transactionDate = null;
        if (this.frmIndividualReceipt.get('contribution_date')) {
          transactionDate = this.frmIndividualReceipt.get('contribution_date').value;
        }
        const aggregateValue: string = this._receiptService.determineAggregate(
          this._contributionAggregateValue,
          contributionAmountNum,
          this.scheduleAction,
          this.memoCode,
          this._selectedEntity,
          this._transactionToEdit,
          this.transactionType,
          this._isSubOfParent(),
          transactionDate
        );

        this.frmIndividualReceipt.patchValue({ contribution_aggregate: aggregateValue }, { onlySelf: true });
      });
  }

  private _getContributionAggregateChild(contribDate: string, entityId: number, cmteId: string) {
    const reportId = this._receiptService.getReportIdFromStorage(this.formType);
    this._receiptService
      .getContributionAggregate(reportId, entityId, cmteId, this.transactionType, contribDate)
      .subscribe(res => {
        // Add the UI val for Contribution Amount to the Contribution Aggregate for the
        // Entity selected from the typeahead list.

        let contributionAmount = this.frmIndividualReceipt.get(this._childFieldNamePrefix + 'contribution_amount')
          .value;
        contributionAmount = contributionAmount ? contributionAmount : 0;
        // remove commas
        if (typeof contributionAmount === 'string') {
          contributionAmount = contributionAmount.replace(/,/g, ``);
        }

        // TODO make this a class variable for contributionAmountChange() to add to.
        const childAggregateName = this._childFieldNamePrefix + 'contribution_aggregate';
        let contributionAggregate: string = String(res[childAggregateName]);
        contributionAggregate = contributionAggregate ? contributionAggregate : '0';

        const total: number = parseFloat(contributionAmount) + parseFloat(contributionAggregate);
        const value: string = this._decimalPipe.transform(total, '.2-2');

        console.log(`contributionAMount: + ${contributionAmount} + contributionAggregate:
          ${contributionAggregate} = ${total}`);
        console.log(`value = ${value}`);

        const aggregateVO = {};
        aggregateVO[childAggregateName] = value;
        this.frmIndividualReceipt.patchValue(aggregateVO, { onlySelf: true });

        // Store the entity aggregate to be added to the contribution amount
        // if it changes in the UI.  See contributionAmountChange();
        this._contributionAggregateValue = parseFloat(contributionAggregate);
      });
  }

  /**
   * Office types may be hard coded as they are never expected to Change for now.
   */
  private _getCandidateOfficeTypes() {
    this._contactsService.getContactsDynamicFormFields().subscribe(res => {
      if (res) {
        console.log('getFormFields res =', res);
        if (res.hasOwnProperty('data')) {
          if (typeof res.data === 'object') {
            if (res.data.hasOwnProperty('officeSought')) {
              if (Array.isArray(res.data.officeSought)) {
                this.candidateOfficeTypes = res.data.officeSought;
              }
            }
          }
        }
      }
    });
  }

  private _setMemoCodeForForm() {
    if (this._readOnlyMemoCode) {
      this.frmIndividualReceipt.controls['memo_code'].setValue(this._memoCodeValue);
      const memoCntrol = this.frmIndividualReceipt.get('memo_code');
      memoCntrol.disable();
      this.memoCode = true;
    }
    if (this._readOnlyMemoCodeChild) {
      this.frmIndividualReceipt.controls[this._childFieldNamePrefix + 'memo_code'].setValue(this._memoCodeValue);
      const memoCntrol = this.frmIndividualReceipt.get(this._childFieldNamePrefix + 'memo_code');
      memoCntrol.disable();
      this.memoCodeChild = true;
    }
  }

  private _isCandidateField(col: any) {
    if (
      this.isFieldName(col.name, 'cand_last_name') ||
      this.isFieldName(col.name, 'cand_first_name') ||
      this.isFieldName(col.name, 'cand_middle_name') ||
      this.isFieldName(col.name, 'cand_prefix') ||
      this.isFieldName(col.name, 'cand_suffix') ||
      this.isFieldName(col.name, 'cand_office') ||
      this.isFieldName(col.name, 'cand_office_district')
    ) {
      return true;
    }
  }

  private _findHiddenField(property: string, value: any) {
    return this.hiddenFields.find((hiddenField: any) => hiddenField[property] === value);
  }

  /**
   * populate the purpose description for child with parent.
   */
  private _checkForEarmarkPurposePrePopulate(res: any): Array<any> {
    let prePopulateFieldArray = null;
    if (this.subTransactionInfo) {
      if (this.subTransactionInfo.isEarmark && this.subTransactionInfo.isParent) {
        let earmarkMemoPurpose = null;

        if (res.hasOwnProperty('entity_type')) {
          if (res.entity_type === 'IND' || res.entity_type === 'CAN') {
            const lastName = res.last_name ? res.last_name.trim() : '';
            const firstName = res.first_name ? res.first_name.trim() : '';
            const middleName = res.middle_name ? res.middle_name.trim() : '';
            const suffix = res.suffix ? res.suffix.trim() : '';
            const prefix = res.prefix ? res.prefix.trim() : '';
            earmarkMemoPurpose = `${lastName}, ${firstName}, ${middleName}, ${prefix}, ${suffix}`;
          } else {
            if (res.hasOwnProperty('entity_name')) {
              earmarkMemoPurpose = res.entity_name;
            }
          }
        }
        prePopulateFieldArray = [];
        prePopulateFieldArray.push({ name: 'purpose_description', value: earmarkMemoPurpose });
        prePopulateFieldArray.push({ name: 'expenditure_purpose', value: earmarkMemoPurpose });
      }
    }
    return prePopulateFieldArray;
  }
}
