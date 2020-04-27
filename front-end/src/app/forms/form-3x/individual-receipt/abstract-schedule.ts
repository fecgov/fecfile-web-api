import { entityTypes } from './entity-types-json';
import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { EventEmitter, Input, OnChanges, OnDestroy, OnInit, SimpleChanges } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, ValidationErrors, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ModalDismissReasons, NgbTooltipConfig, NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
import { Observable, Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { ContactsService } from 'src/app/contacts/service/contacts.service';
import { reportModel } from 'src/app/reports/model/report.model';
import { ReportsService } from 'src/app/reports/service/report.service';
import { ConfirmModalComponent, ModalHeaderClassEnum } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { validateAggregate } from 'src/app/shared/utils/forms/validation/aggregate.validator';
import { validateAmount, validateContributionAmount } from 'src/app/shared/utils/forms/validation/amount.validator';
import { ContributionDateValidator } from 'src/app/shared/utils/forms/validation/contribution-date.validator';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { alphaNumeric } from '../../../shared/utils/forms/validation/alpha-numeric.validator';
import { floatingPoint } from '../../../shared/utils/forms/validation/floating-point.validator';
import { UtilService } from '../../../shared/utils/util.service';
import { CoordinatedExpenditureCCFields } from '../../sched-f-core/coordinated-expenditure-cc-fields';
import { CoordinatedExpenditurePayrollFields } from '../../sched-f-core/coordinated-expenditure-payroll-fields';
import { CoordinatedExpenditureStaffFields } from '../../sched-f-core/coordinated-expenditure-staff-fields';
import { CoordinatedPartyExpenditureFields } from '../../sched-f-core/coordinated-party-expenditure-fields';
import { CoordinatedPartyExpenditureVoidFields } from '../../sched-f-core/coordinated-party-expenditure-void-fields';
import { CoordinatedExpenditureCcMemoFields } from '../../sched-f-core/memo/coordinated-expenditure-cc-memo-fields';
import { CoordinatedExpenditurePayrollMemoFields } from '../../sched-f-core/memo/coordinated-expenditure-Payroll-memo-fields';
import { CoordinatedExpenditureStaffMemoFields } from '../../sched-f-core/memo/coordinated-expenditure-staff-memo-fields';
import { SchedHMessageServiceService } from '../../sched-h-service/sched-h-message-service.service';
import { TransactionModel } from '../../transactions/model/transaction.model';
import { TransactionsMessageService } from '../../transactions/service/transactions-message.service';
import { GetTransactionsResponse, TransactionsService } from '../../transactions/service/transactions.service';
import { ReportTypeService } from '../report-type/report-type.service';
import { F3xMessageService } from '../service/f3x-message.service';
import { AbstractScheduleParentEnum } from './abstract-schedule-parent.enum';
import { IndividualReceiptService } from './individual-receipt.service';
import { ScheduleActions } from './schedule-actions.enum';



export enum SaveActions {
  saveOnly = 'saveOnly',
  saveForReturnToParent = 'saveForReturnToParent',
  saveForReturnToNewParent = 'saveForReturnToNewParent',
  saveForAddSub = 'saveForAddSub',
  saveForEditSub = 'saveForEditSub',
  updateOnly = 'updateOnly',
  saveForReturnToSummary = 'saveForReturnToSUmmary'
}

export abstract class AbstractSchedule implements OnInit, OnDestroy, OnChanges {

  @Input() transactionData: any;
  @Input() transactionDataForChild: any;
  @Input() populateHiddenFieldsMessageObj: any;
  @Input() populateFieldsMessageObj: any;
  @Input() returnToGlobalAllTransaction: boolean;

  mainTransactionTypeText = '';
  transactionTypeText = '';
  transactionType = '';
  scheduleAction: ScheduleActions = null;
  scheduleType = '';
  forceChangeSwitch = 0;
  status: EventEmitter<any> = new EventEmitter<any>();


  public editMode = true;
  public checkBoxVal = false;
  public cvgStartDate: string = null;
  public cvgEndDate: string = null;
  public frmIndividualReceipt: FormGroup;
  public formFields: any = [];
  public hiddenFields: any = [];
  public memoCode = false;
  public memoCodeChild = false;
  public testForm: FormGroup;
  public titles: any = [];
  public states: any = [];
  public levinAccounts: any = [];
  public electionTypes: any = [];
  public candidateOfficeTypes: any = [];
  public entityTypes: any = [];
  public activityEventTypes: any = [];
  public activityEventNames: any = null;
  public subTransactionInfo: any;
  public multipleSubTransactionInfo: any[] = [];
  public selectedEntityType: any;
  public subTransactions: any[];
  public subTransactionsTableType: string;
  public formType = '';
  public editScheduleAction: ScheduleActions = ScheduleActions.edit;
  public addScheduleAction: ScheduleActions = ScheduleActions.add;
  public addSubScheduleAction: ScheduleActions = ScheduleActions.addSubTransaction;
  public memoDropdownSize = null;
  public totalAmountReadOnly: boolean;
  public returnToDebtSummary = false;
  public returnToDebtSummaryInfo: any;
  public viewScheduleAction: ScheduleActions = ScheduleActions.view;
  public reattributionTransactionId: string;
  public redesignationTransactionId: string;
  public isAggregate: boolean = true;
  private _maxReattributableOrRedesignatableAmount: string;

  protected abstractScheduleComponent: AbstractScheduleParentEnum;
  protected isInit = false;
  protected formFieldsPrePopulated = false;
  protected staticFormFields = null;
  protected _prePopulateFromSchedDData: any;
  protected _prePopulateFromSchedLData: any;
  protected _parentTransactionModel: TransactionModel;
  protected _rollbackAfterUnsuccessfulSave = false;
  protected _prePopulateFromSchedHData: any;
  protected _prePopulateFromSchedPARTNData : any;

  /**
   * For toggling between 2 screens of Sched F Debt Payment.
   */
  public showPart2: boolean;

  /**
   * Indicates the Form Group is loaded.  Used by "hybrid" parent classes of this base class
   * having both "static" and "dynamic" form fields as found in Sched F Debt Payment.
   */
  public loaded = false;

  private _reportType: any = null;
  private _cloned = false;
  private _types: any = [];
  private _transaction: any = {};
  private _transactionType: string = null;
  private _transactionTypePrevious: string = null;
  protected _transactionCategory = '';
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
  private _isShowWarn: boolean;
  private _contributionAmountMax: number;
  protected _transactionToEdit: TransactionModel;
  private readonly _childFieldNamePrefix = 'child*';
  private _readOnlyMemoCode: boolean;
  private _readOnlyMemoCodeChild: boolean;
  private _entityTypeDefault: any;
  private _employerOccupationRequired: boolean;
  private _prePopulateFieldArray: Array<any>;
  private _committeeDetails: any;
  private _cmteTypeCategory: string;
  private _completedCloning: boolean = false;
  private _outstandingDebtBalance: number;
  private _scheduleHBackRefTransactionId: string;
  private reattrbutionTransaction: any;
  private readonly childNeededWarnText = 'Please note that this transaction usually includes memo transactions that support the' +
  ' parent transaction. You can add the memo transactions at a later date.';
  private candidateAssociatedWithPayeeTransactionTypes = [
    "IE_VOID",
    "IE_CC_PAY",
    "IE_STAF_REIM",
    "IE_PMT_TO_PROL",
    "IE_MULTI",
    "IE",
    "IE_B4_DISSE",
    "IE_CC_PAY_MEMO",
    "IE_STAF_REIM_MEMO",
    "IE_PMT_TO_PROL_MEMO",
    "COEXP_PARTY",
    "COEXP_CC_PAY",
    "COEXP_STAF_REIM",
    "COEXP_PMT_PROL",
    "COEXP_PARTY_VOID",
    "COEXP_CC_PAY_MEMO",
    "COEXP_STAF_REIM_MEMO",
    "COEXP_PMT_PROL_MEMO",
    "COEXP_PARTY_DEBT"
  ];
  private staticEntityTypes =  [{entityType: "IND", entityTypeDescription: "Individual", group: "ind-group", selected: false}, {entityType: "ORG", entityTypeDescription: "Organization", group: "org-group", selected: false}];
  
  //this dummy subject is used only to let the activatedRoute subscription know to stop upon ngOnDestroy.
  //there is no unsubscribe() for activateRoute . 
  private onDestroy$ = new Subject();

  public priviousTransactionType = '';
  public currentTransactionType = '';

  constructor(
    private _http: HttpClient,
    protected _fb: FormBuilder,
    private _formService: FormsService,
    protected _receiptService: IndividualReceiptService,
    private _contactsService: ContactsService,
    protected _activatedRoute: ActivatedRoute,
    private _config: NgbTooltipConfig,
    private _router: Router,
    protected _utilService: UtilService,
    private _messageService: MessageService,
    private _currencyPipe: CurrencyPipe,
    protected _decimalPipe: DecimalPipe,
    protected _reportTypeService: ReportTypeService,
    protected _typeaheadService: TypeaheadService,
    private _dialogService: DialogService,
    private _f3xMessageService: F3xMessageService,
    private _transactionsMessageService: TransactionsMessageService,
    protected _contributionDateValidator: ContributionDateValidator,
    private _transactionsService: TransactionsService,
    protected _reportsService: ReportsService,
    protected _schedHMessageServce: SchedHMessageServiceService

  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';

    this._f3xMessageService.getPopulateFormMessage().takeUntil(this.onDestroy$).subscribe(message => {
      if (message.hasOwnProperty('key')) {
        // See message sender for mesage properties
        switch (message.key) {
          case 'fullForm':
            // only load form for the AbstractSchudule parent in the view
            if (this.abstractScheduleComponent === message.abstractScheduleComponent) {
              this._checkForReturnToDebtSummary(message);
              this._prePopulateFormForEditOrView(message.transactionModel);
            }
            break;
          case 'field':
            // set the field array to class variable to be referenced once the formGroup
            // has been loaded by the get dynamic fields API call.
            if (message) {
              if (message.fieldArray) {
                this._prePopulateFieldArray = message.fieldArray;
              }
            }
            break;
          case 'prePopulateFromSchedD':
            // set class variable '_prePopulateFromSchedDData' to be referenced once the formGroup
            // has been loaded by the get dynamic fields API call.
            if (message) {
              if (message.prePopulateFromSchedD) {
                // only load form for the AbstractSchudule parent in the view
                if (this.abstractScheduleComponent === message.abstractScheduleComponent) {
                  // Patch fix for sched F payment - It does not have the subTransactionInfo
                  // when determining action so force it here.
                  this.scheduleAction = ScheduleActions.addSubTransaction;
                  this._prePopulateFromSchedDData = message.prePopulateFromSchedD;
                  if (this._prePopulateFromSchedDData) {
                    // set the max paymen allowed on a debt.
                    const balanceAtBegin = this._prePopulateFromSchedDData.beginning_balance ?
                      this._prePopulateFromSchedDData.beginning_balance : 0;
                    const incurredAmount = this._prePopulateFromSchedDData.incurred_amount ?
                      this._prePopulateFromSchedDData.incurred_amount : 0;
                    const paymentAmount = this._prePopulateFromSchedDData.payment_amount ?
                      this._prePopulateFromSchedDData.payment_amount : 0;
                    this._outstandingDebtBalance = (balanceAtBegin + incurredAmount) - paymentAmount;
                  }
                  this._checkForReturnToDebtSummary(message);
                }
              }
            }
            break;
          case 'prePopulateFromSchedL':
            // set class variable '_prePopulateFromSchedLData' to be referenced once the formGroup
            // has been loaded by the get dynamic fields API call.
            if (message) {
              if (message.prePopulateFromSchedL) {
                // only load form for the AbstractSchudule parent in the view
                if (this.abstractScheduleComponent === message.abstractScheduleComponent) {
                  // Patch fix for sched F payment - It does not have the subTransactionInfo
                  // when determining action so force it here.
                  this.scheduleAction = ScheduleActions.addSubTransaction;
                  this._prePopulateFromSchedLData = message.prePopulateFromSchedL;
                }
              }
            }
            break;
          case 'prePopulateFromSchedH':
            // set class variable '_prePopulateFromSchedHData' to be referenced once the formGroup
            // has been loaded by the get dynamic fields API call.
            if (message) {
              if (message.prePopulateFromSchedH) {
                // only load form for the AbstractSchudule parent in the view
                if (this.abstractScheduleComponent === message.abstractScheduleComponent) {
                  this.scheduleAction = ScheduleActions.addSubTransaction;
                  this._prePopulateFromSchedHData = message.prePopulateFromSchedH;
                }
              }
            }
            break;
          case 'prePopulateFromSchedPARTN':
            if (message) {
              if (message.prePopulateFromSchedPARTN) {
                if (this.abstractScheduleComponent === message.abstractScheduleComponent) {
                  this.scheduleAction = ScheduleActions.addSubTransaction;
                  this._prePopulateFromSchedPARTNData = message.prePopulateFromSchedPARTN;
                }
              }
            }
              break;
          default:
            //console.log('message key not supported: ' + message.key);
        }
      }
    });

    this._f3xMessageService.getPopulateHiddenFieldsMessage().takeUntil(this.onDestroy$).subscribe(message => {
      if (this.abstractScheduleComponent === message.abstractScheduleComponent) {
        if (message.reattributionTransactionId) {
          let clearTransactionToEditObj = this.scheduleAction !== ScheduleActions.edit;
          this.clearFormValues(clearTransactionToEditObj);
          this.populateDataForReattribution(message);
        }
        if (message.redesignationTransactionId) {
          
          this.populateDataForRedesignation(message);
        }
      }
    });

    this._f3xMessageService.getPopulateFieldsMessage().takeUntil(this.onDestroy$).subscribe(message => {
      if (this.abstractScheduleComponent === message.abstractScheduleComponent) {
        if(message.fieldArray){
          this._prePopulateFormField(message.fieldArray);
        }
      }
    })

    this._f3xMessageService.getClearFormValuesForRedesignationMessage().takeUntil(this.onDestroy$).subscribe(message => {
      if (this.abstractScheduleComponent === message.abstractScheduleComponent) {
        this.clearFormValuesForRedesignation();
      }
    })

    this._f3xMessageService.getParentModelMessage().takeUntil(this.onDestroy$).subscribe(message => {
      this._parentTransactionModel = message;
    });

    this._f3xMessageService.getInitFormMessage().takeUntil(this.onDestroy$).subscribe(message => {
      this.clearFormValues();
      this.removeAllValidators();
      // For unsaved changes warning, OnChanges() not called when transaction type 
      // is same as previous. Removed saved property here to handle that case.
      localStorage.removeItem(`form_${this.formType}_saved`);
    });

    this._f3xMessageService.getLoadFormFieldsMessage().takeUntil(this.onDestroy$).subscribe(message => {
      if (this.abstractScheduleComponent === message.abstractScheduleComponent) {
        this._getFormFields();
        this._validateTransactionDate();
      }
    });

    _activatedRoute.queryParams.takeUntil(this.onDestroy$).subscribe(p => {
      this._transactionCategory = p.transactionCategory;
      this._cloned = p.cloned || p.cloned === 'true' ? true : false;
    });
  }

  private populateDataForRedesignation(message: any) {
    this.redesignationTransactionId = message.redesignationTransactionId;
    this._maxReattributableOrRedesignatableAmount = message.maxAmount;
    if(this.transactionData){
      this._f3xMessageService.sendPopulateFormMessage(this.transactionData);
    }
    if(this.frmIndividualReceipt && this.frmIndividualReceipt.controls['expenditure_amount']){
      this.frmIndividualReceipt.controls['expenditure_amount'].setValidators([Validators.required,validateContributionAmount(Number(this._maxReattributableOrRedesignatableAmount))]);
      this.frmIndividualReceipt.controls['expenditure_amount'].updateValueAndValidity();
    }
    if(this.frmIndividualReceipt && this.frmIndividualReceipt.controls['memo_text']){
      this.frmIndividualReceipt.patchValue({memo_text:'MEMO: Redesignated'},{onlySelf:true});
      this.frmIndividualReceipt.get('memo_text').disable();
    }
    if(this.frmIndividualReceipt && this.frmIndividualReceipt.controls['memo_code']){
      this.frmIndividualReceipt.get('memo_code').disable();
    }
  }

  private populateDataForReattribution(message: any) {
    this.reattributionTransactionId = message.reattributionTransactionId;
    this._maxReattributableOrRedesignatableAmount = message.maxAmount;
    this.reattrbutionTransaction = message.reattributionTransaction;
    if(this.frmIndividualReceipt && this.frmIndividualReceipt.controls['contribution_amount']){
      this.frmIndividualReceipt.controls['contribution_amount'].setValidators([Validators.required,validateContributionAmount(Number(this._maxReattributableOrRedesignatableAmount))]);
      this.frmIndividualReceipt.controls['contribution_amount'].updateValueAndValidity();
    }
    /* const purposeDescriptionFormField = this.findFormField('purpose_description');
    if(purposeDescriptionFormField.isReadonly){
      this._prePopulateFieldArray = [{name:'purpose_description', value:this.reattrbutionTransaction.purposeDescription}];
    } */

    if(this.frmIndividualReceipt && this.frmIndividualReceipt.controls['memo_text']){
      this.frmIndividualReceipt.patchValue({memo_text:'MEMO: Reattribution'},{onlySelf:true});
      this.frmIndividualReceipt.get('memo_text').disable();
    }
    if(this.frmIndividualReceipt && this.frmIndividualReceipt.controls['memo_code']){
      this.frmIndividualReceipt.get('memo_code').disable();
    }
    this.clearEntityIdFromHiddenFields();
  }
  
  private clearEntityIdFromHiddenFields() {
    if (this.hiddenFields && this.hiddenFields.length > 0) {
      let entityIdField = this.hiddenFields.find(element => element.name === 'entity_id');
      entityIdField.value = null;
    }
  }

  public ngOnInit(): void {
    this._selectedEntity = null;
    this._selectedChangeWarn = null;
    this._selectedEntityChild = null;
    this._selectedChangeWarnChild = null;
    this._selectedCandidate = null;
    this._selectedCandidateChangeWarn = null;
    this._selectedCandidateChild = null;
    this._selectedCandidateChangeWarnChild = null;
    this._isShowWarn = true;
    this._readOnlyMemoCode = false;
    this._readOnlyMemoCodeChild = false;
    this._transactionToEdit = null;
    this._contributionAggregateValue = 0.0;
    this._contributionAggregateValueChild = 0.0;
    this._contributionAmount = '';
    this._contributionAmountChlid = '';
    this._employerOccupationRequired = false;
    this.memoDropdownSize = null;
    this.totalAmountReadOnly = true;
    this._completedCloning = false;
    this.returnToDebtSummary = false;
    this._outstandingDebtBalance = null;

    if (localStorage.getItem('committee_details') !== null) {
      this._committeeDetails = JSON.parse(localStorage.getItem('committee_details'));
      if (this._committeeDetails.cmte_type_category !== null) {
        this._cmteTypeCategory = this._committeeDetails.cmte_type_category;
      }
    }

    if (localStorage.getItem('committee_details') !== null) {
      this._committeeDetails = JSON.parse(localStorage.getItem('committee_details'));
      if (this._committeeDetails.cmte_type_category !== null) {
        this._cmteTypeCategory = this._committeeDetails.cmte_type_category;
      }
    }

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

    this.isInit = true;
  }

  public ngOnChanges(changes: SimpleChanges) {

    localStorage.removeItem(`form_${this.formType}_saved`);

    if (this.checkComponent(changes)) {
      if (this.editMode) {
        if(this._activatedRoute.snapshot.queryParams.reportId){
          if(this.formType !== '24'){
            this._reportsService.getCoverageDates(this._activatedRoute.snapshot.queryParams.reportId).subscribe(res => {
              this.cvgStartDate = this._utilService.formatDate(res.cvg_start_date);
              this.cvgEndDate = this._utilService.formatDate(res.cvg_end_date);
              this._prepareForm();
              // added check to avoid script error
              if (this.frmIndividualReceipt && this.frmIndividualReceipt.controls['contribution_date']) {
                this.frmIndividualReceipt.controls['contribution_date'].setValidators([
                  this._contributionDateValidator.contributionDate(this.cvgStartDate, this.cvgEndDate),
                  Validators.required
                ]);
              }
            });
          } else{
            this._prepareForm();
          }
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

    if (changes && changes.transactionType) {
      this.priviousTransactionType = changes.transactionType.previousValue;
      this.currentTransactionType = changes.transactionType.currentValue;
    }
  }
  checkComponent(changes: SimpleChanges): boolean {

    // Some components pass null explicitly to force the form page to load even without
    // @Input() changes (SchedFComponent, H3, H5).  If changes === null proceed with page load.
    if (!changes) {
      return true;
    }

    if (changes && changes.transactionType && changes.transactionType.currentValue !== '' && changes.transactionType.currentValue === this.transactionType) {

      //schedE is set up differently, causing ngOnChange to fire everytime, so need to explicily check the component against the transactionType to prevent
      //unnecessary calls. This may need to be cleaned up later. 
      if (this.abstractScheduleComponent === AbstractScheduleParentEnum.schedEComponent) {
        if (!changes.transactionType.currentValue.startsWith('IE')) {
          return false;
        }
        return true;
      }
      return true;
    }
    return false;
  }

  public ngOnDestroy(): void {
    this._messageService.clearMessage();
    localStorage.removeItem('form_3X_saved');
    this.onDestroy$.next(true);
  }

  private _prepareForm() {
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

  private _prepareForUnsavedChanges(): void {
    this.frmIndividualReceipt.valueChanges.takeUntil(this.onDestroy$)
      .subscribe(val => {
      if (this.frmIndividualReceipt.dirty) {
        localStorage.setItem(`form_${this.formType}_saved`, JSON.stringify({ saved: false }));
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
    let memoCodeValue = null;
    this._readOnlyMemoCode = false;
    this._readOnlyMemoCodeChild = false;
    this._employerOccupationRequired = false;

    memoCodeValue = this.mapValidatorsForAllFields(fields, formGroup, memoCodeValue);

    this.frmIndividualReceipt = new FormGroup(formGroup);

    if (this.abstractScheduleComponent === AbstractScheduleParentEnum.schedFComponent ||
      this.abstractScheduleComponent === AbstractScheduleParentEnum.schedFCoreComponent) {
      this.loaded = true;
    }

    // When coming from Reports where this component is not a child
    // as it is in F3X component, the form data must be set in this way
    // to avoid race condition
    if (this._transactionToEdit) {
      this._setFormDataValues(
        this._transactionToEdit.transactionId,
        this._transactionToEdit.apiCall,
        this._transactionToEdit.reportId
      );
    }

    // get form data API is passing X for memo code value.
    // Set it to value from dynamic forms as some should be checked and disabled by default.
    this._setMemoCodeForForm();

    if (this.frmIndividualReceipt.get('election_code')) {
      this.frmIndividualReceipt.patchValue({ election_code: null }, { onlySelf: true });
    }
    // selects are defaulting to value = "Select" - set to null.
    if (this.frmIndividualReceipt.contains('activity_event_type')) {
      this.frmIndividualReceipt.patchValue({ activity_event_type: null }, { onlySelf: true });
    }
    if (this.frmIndividualReceipt.contains('activity_event_identifier')) {
      this.frmIndividualReceipt.patchValue({ activity_event_identifier: null }, { onlySelf: true });
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

    if (this.scheduleAction === ScheduleActions.add) {
      this.frmIndividualReceipt.patchValue(
        { beginning_balance: this._decimalPipe.transform(0, '.2-2') },
        { onlySelf: true }
      );
      this.frmIndividualReceipt.patchValue(
        { payment_amount: this._decimalPipe.transform(0, '.2-2') },
        { onlySelf: true }
      );
      this.frmIndividualReceipt.patchValue(
        { balance_at_close: this._decimalPipe.transform(0, '.2-2') },
        { onlySelf: true }
      );
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

    if (this.scheduleAction === ScheduleActions.view) {
      this.frmIndividualReceipt.disable();
    }

    //once the parent is initialized, send message to any child subscriptions to perform any applicable actions
    if (this.frmIndividualReceipt && this.frmIndividualReceipt.controls) {
      this._messageService.sendMessage({ parentFormPopulated: true, component: this.abstractScheduleComponent });
      this._prepareForUnsavedChanges();
    }
  }

  private mapValidatorsForAllFields(fields: any, formGroup: any, memoCodeValue: any) {
    fields.forEach(el => {
      if (el.hasOwnProperty('cols') && el.cols) {
        el.cols.forEach(e => {
          formGroup[e.name] = new FormControl(e.value || null, this._mapValidators(e.validation, e.name, e.value));
          if (this.isFieldName(e.name, 'contribution_amount') ||
            this.isFieldName(e.name, 'expenditure_amount') ||
            this.isFieldName(e.name, 'total_amount') ||
            this.isFieldName(e.name, 'incurred_amount')) {
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
              }
              else {
                this.memoCode = true;
              }
            }
            if (isChildForm) {
              this._readOnlyMemoCodeChild = e.isReadonly;
            }
            else {
              this._readOnlyMemoCode = e.isReadonly;
            }
          }
        });
      }
    });
    return memoCodeValue;
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

    if (this.isFieldName(fieldName, 'zip_code') || this.isFieldName(fieldName, 'subordinate_cmte_zip')) {
      formValidators.push(alphaNumeric());
    } else if (this.isFieldName(fieldName, 'contribution_date') || this.isFieldName(fieldName, 'expenditure_date')) {
      this._reportType = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
      if (this._reportType !== null) {
        const cvgStartDate: string = this._reportType.cvgStartDate;
        const cvgEndDate: string = this._reportType.cvgEndDate;
        if (!this.reattributionTransactionId && !this.redesignationTransactionId) {
          formValidators.push(this._contributionDateValidator.contributionDate(cvgStartDate, cvgEndDate));
        }
      }
    } else if (this.isFieldName(fieldName, 'expenditure_amount') ||
      this.isFieldName(fieldName, 'contribution_amount') ||
      this.isFieldName(fieldName, 'total_amount')) {
      // Debt payments need a validation to prevent exceeding the incurred debt
      if (this.transactionType === 'OPEXP_DEBT' ||
        this.transactionType === 'ALLOC_EXP_DEBT' ||
        this.transactionType === 'ALLOC_FEA_DISB_DEBT' ||
        this.transactionType === 'OTH_DISB_DEBT' ||
        this.transactionType === 'FEA_100PCT_DEBT_PAY' ||
        this.transactionType === 'COEXP_PARTY_DEBT' ||
        this.transactionType === 'IE_B4_DISSE' ||
        this.transactionType === 'OTH_REC_DEBT') {
        if (this._outstandingDebtBalance !== null) {
          if (this._outstandingDebtBalance >= 0) {
            formValidators.push(validateContributionAmount(this._outstandingDebtBalance));
          }
        }
      }

      // if redesignation or reattribution, validate to prevent exceeding the original amount
      if((this.reattributionTransactionId || this.redesignationTransactionId) && this._maxReattributableOrRedesignatableAmount){
        formValidators.push(validateContributionAmount(Number(this._maxReattributableOrRedesignatableAmount)));
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

    else if (this.isFieldName(fieldName, 'expenditure_purpose')) {
      // Expenditure  description is required for H4/H6
      if (
        this.transactionType === 'ALLOC_EXP' ||
        this.transactionType === 'ALLOC_EXP_CC_PAY' ||
        this.transactionType === 'ALLOC_EXP_CC_PAY_MEMO' ||
        this.transactionType === 'ALLOC_EXP_STAF_REIM' ||
        this.transactionType === 'ALLOC_EXP_STAF_REIM_MEMO' ||
        this.transactionType === 'ALLOC_EXP_PMT_TO_PROL' ||
        this.transactionType === 'ALLOC_EXP_PMT_TO_PROL_MEMO' ||
        this.transactionType === 'ALLOC_EXP_VOID' ||
        this.transactionType === 'ALLOC_FEA_DISB' ||
        this.transactionType === 'ALLOC_FEA_CC_PAY' ||
        this.transactionType === 'ALLOC_FEA_CC_PAY_MEMO' ||
        this.transactionType === 'ALLOC_FEA_STAF_REIM' ||
        this.transactionType === 'ALLOC_FEA_STAF_REIM_MEMO' ||
        this.transactionType === 'ALLOC_FEA_VOID'
      ) {
        formValidators.push(Validators.required);
      }
    }

    if (validators) {
      for (const validation of Object.keys(validators)) {
        if (validation === 'required') {
          if (validators[validation]) {
            // occuaption and employer will be required dpending on aggregate
            if (fieldName !== 'employer' && fieldName !== 'occupation' && fieldName !== 'expenditure_purpose') {
              if (fieldName === 'incurred_amount' && this.scheduleAction === ScheduleActions.edit) {
                // not required but not optinal when editing
              } else {
                formValidators.push(Validators.required);
              }
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

  private _checkDebtPaymentExceeded(e: any) {
    if (this.isFieldName(e.name, 'expenditure_amount')) {
      if (this.transactionType === 'OPEXP_DEBT') {
        //console.log();
        // this.form.controls['expenditure_amount'].setValidators([validateAmount(), validateContributionAmount(this.outstandingLoanBalance)]);
        // formValidators.push(this._contributionDateValidator.contributionDate(cvgStartDate, cvgEndDate));
      }
    }
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
        if(this.frmIndividualReceipt.controls[dateField]){
          this.frmIndividualReceipt.controls[dateField].setValidators([Validators.required]);
          this.frmIndividualReceipt.controls[dateField].updateValueAndValidity();
        }
      } else {
        if (this.frmIndividualReceipt && this.frmIndividualReceipt.controls[dateField]) {
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
        if (this.frmIndividualReceipt && this.frmIndividualReceipt.controls['child*' + dateField]) {
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
   * Apply the validation rules when aggregate changes.
   */
  private _listenForAggregateChanges(): void {
    if (this.frmIndividualReceipt.get('contribution_aggregate') != null) {
      this.frmIndividualReceipt.get('contribution_aggregate').valueChanges.takeUntil(this.onDestroy$)
        .subscribe(val => {
          // All validators are replaced here.  Currently the only validator functions
          // for employer and occupation is the validateAggregate().  The max length is enforced
          // in the template as an element attribute max.
          // If additoanl validators need to be added here, there is no replace function in ng,
          // they must be cleared and all set in an array again. Onc solution is to
          // store the validators in a class variable array, add this function to the array, and set the
          // controls's setValidator() using the full array.  Or just get the validations from the
          // dynamic form fields again in this.formFields[].

          if(this.frmIndividualReceipt && this.selectedEntityType && this.selectedEntityType.entityType === 'IND'){
            const employerControl = this.frmIndividualReceipt.get('employer');
            employerControl.setValidators([validateAggregate(val, true, 'employer')]);
            employerControl.updateValueAndValidity();
  
            const occupationControl = this.frmIndividualReceipt.get('occupation');
            occupationControl.setValidators([validateAggregate(val, true, 'occupation')]);
            occupationControl.updateValueAndValidity();
          }
        });


        //also update employer and occupation validations whenever entity_type changes, since these validations
        //are only required for entity_type === 'IND'
      if(this.frmIndividualReceipt.get('entity_type') !== null){
        this.frmIndividualReceipt.get('entity_type').valueChanges.takeUntil(this.onDestroy$)
        .subscribe(val => {
          if(this.frmIndividualReceipt && this.frmIndividualReceipt.controls['entity_type']){
            if(this.frmIndividualReceipt.controls['entity_type'].value === 'ORG'){
              const employerControl = this.frmIndividualReceipt.get('employer');
              employerControl.clearValidators();
              employerControl.updateValueAndValidity();
    
              const occupationControl = this.frmIndividualReceipt.get('occupation');
              occupationControl.clearValidators();
              occupationControl.updateValueAndValidity();
            }
            else if(this.frmIndividualReceipt.controls['entity_type'].value === 'IND'){
  
              //if ind, then check apply validators based on contribution_aggregate value
              if(this.frmIndividualReceipt && this.frmIndividualReceipt.controls['contribution_aggregate'] && this.frmIndividualReceipt.controls['contribution_aggregate'].value){
                const employerControl = this.frmIndividualReceipt.get('employer');
                employerControl.setValidators([validateAggregate(this.frmIndividualReceipt.controls['contribution_aggregate'].value, true, 'employer')]);
                employerControl.updateValueAndValidity();
      
                const occupationControl = this.frmIndividualReceipt.get('occupation');
                occupationControl.setValidators([validateAggregate(this.frmIndividualReceipt.controls['contribution_aggregate'].value, true, 'occupation')]);
                occupationControl.updateValueAndValidity();
              }
            } 
          }
          
        });
      }
    } else if (this.frmIndividualReceipt.get('expenditure_amount') != null) {
      this.frmIndividualReceipt.get('expenditure_amount').valueChanges.takeUntil(this.onDestroy$)
        .subscribe(value => {
          const expenditurePurposeDesc = this.frmIndividualReceipt.get('expenditure_purpose');
          expenditurePurposeDesc.setValidators([validateAggregate(value, true, 'expenditure_purpose')]);
          expenditurePurposeDesc.updateValueAndValidity();
        });
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
      this.isAggregate,
      this._selectedEntity,
      this._transactionToEdit,
      this.transactionType,
      transactionDate
    );
    this.frmIndividualReceipt.patchValue({ contribution_aggregate: aggregateValue }, { onlySelf: true });
  }

  public handleOnBlurEvent($event: any, col: any) {
    if (this.isFieldName(col.name, 'contribution_amount') || this.isFieldName(col.name, 'expenditure_amount')) {
      this.contributionAmountChange($event, col.name, col.validation.dollarAmountNegative);
    } else if (this.isFieldName(col.name, 'total_amount') || this.isFieldName(col.name, 'incurred_amount')) {
      if (this.isFieldName(col.name, 'total_amount') && this.totalAmountReadOnly) {
        return;
      }
      this._formatAmount($event, col.name, col.validation.dollarAmountNegative);
      if (col.name === 'total_amount') {
        this._getFedNonFedPercentage();
      }
      if (col.name === 'incurred_amount') {
        this._adjustDebtBalanceAtClose();
      }
    } else {
      this.populatePurpose(col.name);
    }
  }

  private _adjustDebtBalanceAtClose() {
    if (this.transactionType !== 'DEBT_TO_VENDOR' && this.transactionType !== 'DEBT_BY_VENDOR') {
      return;
    }
    if (
      !this.frmIndividualReceipt.contains('beginning_balance') ||
      !this.frmIndividualReceipt.contains('incurred_amount') ||
      !this.frmIndividualReceipt.contains('payment_amount') ||
      !this.frmIndividualReceipt.contains('balance_at_close')
    ) {
      return;
    }

    let beginningBalance = this.frmIndividualReceipt.get('beginning_balance').value;
    if (beginningBalance) {
      if (typeof beginningBalance === 'string') {
        beginningBalance = beginningBalance.replace(/,/g, ``);
      }
    } else {
      beginningBalance = 0;
    }

    let incurredAmount = this.frmIndividualReceipt.get('incurred_amount').value;
    if (incurredAmount) {
      if (typeof incurredAmount === 'string') {
        incurredAmount = incurredAmount.replace(/,/g, ``);
      }
    } else {
      incurredAmount = 0;
    }

    let paymentAmount = this.frmIndividualReceipt.get('payment_amount').value;
    if (paymentAmount) {
      if (typeof paymentAmount === 'string') {
        paymentAmount = paymentAmount.replace(/,/g, ``);
      }
    } else {
      paymentAmount = 0;
    }

    beginningBalance = parseFloat(beginningBalance);
    incurredAmount = parseFloat(incurredAmount);
    paymentAmount = parseFloat(paymentAmount);
    const balanceAtClose = beginningBalance + incurredAmount - paymentAmount;

    this._formatAmount({ target: { value: balanceAtClose.toString() } }, 'balance_at_close', false);
  }

  /**
   * H4 and H6 will populate readonly fields using the user provided payment and activity.
   * Call the API to calculate the fed, non-fed and activity YTD values.
   */
  private _getFedNonFedPercentage() {
    if (
      this.transactionType !== 'ALLOC_FEA_DISB_DEBT' &&
      this.transactionType !== 'ALLOC_EXP_DEBT' &&
      this.transactionType !== 'ALLOC_EXP' &&
      this.transactionType !== 'ALLOC_EXP_CC_PAY' &&
      this.transactionType !== 'ALLOC_EXP_CC_PAY_MEMO' &&
      this.transactionType !== 'ALLOC_EXP_STAF_REIM' &&
      this.transactionType !== 'ALLOC_EXP_STAF_REIM_MEMO' &&
      this.transactionType !== 'ALLOC_EXP_PMT_TO_PROL' &&
      this.transactionType !== 'ALLOC_EXP_PMT_TO_PROL_MEMO' &&
      this.transactionType !== 'ALLOC_EXP_VOID' &&
      this.transactionType !== 'ALLOC_FEA_DISB' &&
      this.transactionType !== 'ALLOC_FEA_CC_PAY' &&
      this.transactionType !== 'ALLOC_FEA_CC_PAY_MEMO' &&
      this.transactionType !== 'ALLOC_FEA_STAF_REIM' &&
      this.transactionType !== 'ALLOC_FEA_STAF_REIM_MEMO' &&
      this.transactionType !== 'ALLOC_FEA_VOID'
    ) {
      return;
    }

    // reset all pre-populated values
    this.frmIndividualReceipt.patchValue({ fed_share_amount: null }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ non_fed_share_amount: null }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ activity_event_amount_ytd: null }, { onlySelf: true });

    if (!this.frmIndividualReceipt.contains('total_amount')) {
      return;
    }

    let totalAmount = this.frmIndividualReceipt.get('total_amount').value;
    if (!totalAmount) {
      return;
    }
    if (typeof totalAmount === 'string') {
      totalAmount = totalAmount.replace(/,/g, ``);
    }

    let activityEvent = null;
    if (this.frmIndividualReceipt.contains('activity_event_type')) {
      activityEvent = this.frmIndividualReceipt.get('activity_event_type').value;
    }

    let activityEventName = null;
    if (this.frmIndividualReceipt.contains('activity_event_identifier')) {
      activityEventName = this.frmIndividualReceipt.get('activity_event_identifier').value;
    }

    if(this.subTransactionInfo){
      if (
        this.subTransactionInfo.subTransactionType === 'ALLOC_EXP_CC_PAY_MEMO' ||
        this.subTransactionInfo.subTransactionType === 'ALLOC_EXP_STAF_REIM_MEMO' ||
        this.subTransactionInfo.subTransactionType === 'ALLOC_EXP_PMT_TO_PROL_MEMO' ||
        this.subTransactionInfo.subTransactionType === 'ALLOC_FEA_CC_PAY_MEMO' ||
        this.subTransactionInfo.subTransactionType === 'ALLOC_FEA_STAF_REIM_MEMO'
      ) {
        activityEvent = this.frmIndividualReceipt.get('activity_event_type').value;

        if(activityEvent === 'DC' || activityEvent === 'DF') {
          activityEventName = this.frmIndividualReceipt.get('activity_event_identifier').value;
        }
      }
    }

    if (!activityEvent) {
      return;
    }

    if ((activityEvent === 'DC' || activityEvent === 'DF') && !activityEventName) {
      return;
    }

    const reportId = this._receiptService.getReportIdFromStorage(this.formType);

    let transactionId = '0';
    if (this.scheduleAction === ScheduleActions.edit) {
      transactionId = this._transactionToEdit.transactionId;
    }

    let scheduleHBackRefTransactionId = '';

    if (this._transactionToEdit && this._transactionToEdit.hasOwnProperty('backRefTransactionId')) {
      scheduleHBackRefTransactionId = this._transactionToEdit.backRefTransactionId;
    } else {
      scheduleHBackRefTransactionId = '';
    }

    if (this._scheduleHBackRefTransactionId) {
      scheduleHBackRefTransactionId = this._scheduleHBackRefTransactionId;
    }


    this._receiptService
      .getFedNonFedPercentage(totalAmount, activityEvent, activityEventName, this.transactionType, reportId, transactionId, scheduleHBackRefTransactionId)
      .subscribe(
        res => {
          if (res) {
            if (res.fed_share) {
              this._formatAmount({ target: { value: res.fed_share.toString() } }, 'fed_share_amount', false);
              this._formatAmount({ target: { value: res.fed_share.toString() } }, 'federal_share', false);
            }
            if (res.nonfed_share) {
              this._formatAmount({ target: { value: res.nonfed_share.toString() } }, 'non_fed_share_amount', false);
              this._formatAmount({ target: { value: res.nonfed_share.toString() } }, 'levin_share', false);
            }
            if (res.aggregate_amount !== null) {
              // forced aggregation
              totalAmount  = this.convertAmountToNumber(totalAmount);
              const aggregatedResponse = this.convertAmountToNumber(res.aggregate_amount);
              let newAggregate: number;
              if (this.scheduleAction === ScheduleActions.edit) {
                // get the initial aggregation indicator during load
                const initialAggregateInd: boolean = this._utilService.aggregateIndToBool(this._transactionToEdit.aggregation_ind);
                if ( (initialAggregateInd && this.isAggregate) || (!initialAggregateInd && !this.isAggregate)) {
                  // if initial and current aggregation flags remain the same
                  // lets patch the response from API
                  newAggregate = aggregatedResponse;
                } else if (initialAggregateInd && !this.isAggregate) {
                  // if initial was aggregated and now unaggregated
                  // un-aggregate now
                  newAggregate = aggregatedResponse - totalAmount;
                } else if (!initialAggregateInd && this.isAggregate) {
                  // if initial was un-aggregated and now aggregated
                  // aggregate now
                  newAggregate = aggregatedResponse + totalAmount;
                }
              } else {
                // if new transaction API responds with aggregate + current amount
                if (this.isAggregate) {
                  totalAmount = 0;
                }
              newAggregate = res.aggregate_amount - totalAmount;
              }

              this._formatAmount(
                { target: { value: newAggregate.toString() } },
                'activity_event_amount_ytd',
                false
              );
            }
          }
        },
        errorRes => { }
      );
  }

  /**
   * Present user with H1/H2 required before making Debt payment.
   */
  private _handleNoH1H2(activityEventScheduleType: string) {
    // Default to H1 if not provided
    if (!activityEventScheduleType) {
      activityEventScheduleType = 'sched_h1';
    }

    // Hard Coding DF/DC  => H2 for now.  Once dynamic forms provides schedule in activityEventTypes
    // const activityEventType = this.frmIndividualReceipt.get('activity_event_type').value;
    // const scheduleName = (activityEventType === 'DF' || activityEventType === 'DC') ? 'H2' : 'H1';
    // const scheduleType = (activityEventType === 'DF' || activityEventType === 'DC') ? 'sched_h2' : 'sched_h1';

    // const scheduleName = activityEventScheduleType === 'sched_h1' ? 'H1' : 'H2';
    // const scheduleType = activityEventScheduleType;

    let scheduleName = activityEventScheduleType === 'sched_h1' ? 'H1' : 'H2';
    let scheduleType = activityEventScheduleType;

    if (activityEventScheduleType === 'sched_h6') {
      scheduleName = 'H1';
      scheduleType = 'sched_h1';
    }

    const message =
      `Please add Schedule ${scheduleName} before proceeding with adding the ` +
      `amount.  Schedule ${scheduleName} is required to correctly allocate the federal and non-federal portions of the transaction.`;
    this._dialogService.confirm(message, ConfirmModalComponent, 'Warning!', false).then(res => {
      if (res === 'okay') {
        const emitObj: any = {
          form: this.frmIndividualReceipt,
          direction: 'next',
          step: 'step_3',
          previousStep: 'step_2',
          scheduleType: scheduleType,
          action: ScheduleActions.add
        };
        if (scheduleType === 'sched_h2') {
          emitObj.transactionType = 'ALLOC_H2_RATIO';
          emitObj.transactionTypeText = 'Allocation Ratios';
        }
        this.status.emit(emitObj);
      } else if (res === 'cancel') {
      }
    });
  }

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
      this._contributionAmount = String(contributionAmountNum);
    }

    const amountValue: string = this._decimalPipe.transform(contributionAmountNum, '.2-2');
    const patch = {};
    patch[fieldName] = amountValue;
    if (this.frmIndividualReceipt) {
      this.frmIndividualReceipt.patchValue(patch, { onlySelf: true });
    }
  }

  /**
   * Handle a change to the Activity Event select.
   */
  public handleActivityEventTypeChange($event: any, col: any) {
    // reset activity_event_identifier whenever the type changes
    this.frmIndividualReceipt.patchValue({ activity_event_identifier: null }, { onlySelf: true });
    this.activityEventNames = null;

    if (!$event) {
      this._resetFedNonFed();
      this.totalAmountReadOnly = true;
      return;
    }

    if ($event.hasOwnProperty('hasValue')) {
      if ($event.hasValue === false) {
        if ($event.hasOwnProperty('scheduleType')) {
          this._handleNoH1H2($event.scheduleType);
        } else {
          this._handleNoH1H2(null);
        }
      }
    }

    if ($event.activityEventTypes) {
      this.activityEventNames = $event.activityEventTypes;
      // make required
      // NOTE: Any new validations from the dynamic forms API will need to
      // be added back as this rebuilds the validators for the FormControl.
      // Currently the only relevent one is "required" true/fase.
      if (this.frmIndividualReceipt.contains('activity_event_identifier')) {
        const activityControl = this.frmIndividualReceipt.get('activity_event_identifier');
        activityControl.setValidators([Validators.required]);
        activityControl.updateValueAndValidity();
      }
    } else {
      // remove required
      if (this.frmIndividualReceipt.contains('activity_event_identifier')) {
        const activityControl = this.frmIndividualReceipt.get('activity_event_identifier');
        activityControl.setValidators([Validators.nullValidator]);
        activityControl.updateValueAndValidity();
      }
    }

    let eventTypeVal = null;
    if (this.frmIndividualReceipt.contains('activity_event_type')) {
      eventTypeVal = this.frmIndividualReceipt.get('activity_event_type').value;
    }

    // Don't allow a total amount to be entered if the required activity event and activity name
    // are not set.  For event types requiring the 2nd dropdown, activityEventNames will have data.
    if (!eventTypeVal) {
      this._resetFedNonFed();
      this.totalAmountReadOnly = true;
    } else {
      if (this.activityEventNames) {
        let activityEventIdentifier = null;
        if (this.frmIndividualReceipt.contains('activity_event_identifier')) {
          activityEventIdentifier = this.frmIndividualReceipt.get('activity_event_identifier').value;
        }
        if (activityEventIdentifier) {
          this._getFedNonFedPercentage();
          this.totalAmountReadOnly = false;
        } else {
          this._resetFedNonFed();
          this.totalAmountReadOnly = true;
        }
      } else {
        this._getFedNonFedPercentage();
        this.totalAmountReadOnly = false;
      }
    }
  }

  public handleActivityEventNameChange($event: any, col: any) {
    if (!$event) {
      this._resetFedNonFed();
      this.totalAmountReadOnly = true;
    } else {
      this._getFedNonFedPercentage();
      this.totalAmountReadOnly = false;
    }
  }

  private _resetFedNonFed() {
    this.frmIndividualReceipt.patchValue({ fed_share_amount: null }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ non_fed_share_amount: null }, { onlySelf: true });
    this.frmIndividualReceipt.patchValue({ activity_event_amount_ytd: null }, { onlySelf: true });
  }

  /**
   * Determine if fields is read only.  If it should
   * be read only return true else null.  Null will
   * remove HTML attribute readonly whereas setting it to
   * false will not remove readonly from DOM and fields remains in readonly.
   */
  public isFieldReadOnly(col: any) {
    if (col.type === 'text' && col.isReadonly) {
      return true;
    }
    if (col.type === 'date' && col.isReadonly) {
      return true;
    }
    if (col.name === 'total_amount') {
      return this._isTotalAmountReadOnly(col);
    }
    return null;
  }

  public isSelectFieldReadOnly(col: any) {
    if (col.type === 'select' && col.isReadonly) {
      if (this.frmIndividualReceipt.get(col.name)) {
        this.frmIndividualReceipt.get(col.name).disable();
      }
      return true;
    }
    return null;
  }

  /**
   * Return true if readonly else null to remove readonly attribute from DOM.
   */
  private _isTotalAmountReadOnly(col: any): boolean {
    if (col.name !== 'total_amount') {
      return null;
    }
    // Must be H4 or H6
    if (this.transactionType !== 'ALLOC_FEA_DISB_DEBT' && this.transactionType !== 'ALLOC_EXP_DEBT') {
      return null;
    }
    return this.totalAmountReadOnly ? true : null;
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

    const isScheduleF = (this.abstractScheduleComponent === AbstractScheduleParentEnum.schedFCoreComponent)
                          || (this.abstractScheduleComponent === AbstractScheduleParentEnum.schedFComponent);

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

    if (isScheduleF) {
      if (this.frmIndividualReceipt.get('expenditure_date')) {
        transactionDate = this.frmIndividualReceipt.get('expenditure_date').value;
      }
    } else {
      if (this.frmIndividualReceipt.get('contribution_date')) {
        transactionDate = this.frmIndividualReceipt.get('contribution_date').value;
      }
    }
    const aggregateValue: string = this._receiptService.determineAggregate(
      this._contributionAggregateValue,
      contributionAmountNum,
      this.scheduleAction,
      this.isAggregate,
      this._selectedEntity,
      this._transactionToEdit,
      this.transactionType,
      transactionDate
    );

    if (isChildForm) {
      this.frmIndividualReceipt.patchValue({ 'child*contribution_aggregate': aggregateValue }, { onlySelf: true });
    } else {
      if (isScheduleF) {
        this.frmIndividualReceipt.patchValue({ aggregate_general_elec_exp: aggregateValue }, { onlySelf: true });
      } else {
        this.frmIndividualReceipt.patchValue({ contribution_aggregate: aggregateValue }, { onlySelf: true });
      }
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
      // Not sure if this is needed for preventing excessive calls.
      // Removed for now to get working for sched_h.
      this._transactionTypePrevious = this.transactionType;
      // reload dynamic form fields
      this._getFormFields();
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
      if (!this.redesignationTransactionId) {
        this.handleFormFieldKeyupCandidate($event, col);
      }
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

    if (this._isShowWarn) {
      this._isShowWarn = false;
      const message = `Please note that if you update contact information it will be updated in the Contacts file. ` +
        `Please acknowledge this change by clicking the OK button.`;
      this._dialogService.confirm(message, ConfirmModalComponent, 'Warning!', true)
        .then(res => {
          if (res === 'okay') {
          } else if (res === 'cancel') {
            if (this._selectedEntity) {
              if (this.frmIndividualReceipt.get(name)) {
                const patch = {};
                patch[name] = this._selectedEntity[name];
                this.frmIndividualReceipt.patchValue(patch, { onlySelf: true });
              }
            }
          }
        });
    }

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

    if (this._isShowWarn) {
      this._isShowWarn = false;
      const message = `Please note that if you update contact information it will be updated in the Contacts file. ` +
        `Please acknowledge this change by clicking the OK button.`;
      this._dialogService.confirm(message, ConfirmModalComponent, 'Warning!', true)
        .then(res => {
          if (res === 'okay') {
          } else if (res === 'cancel') {
            if (this.frmIndividualReceipt.get(name)) {
              if (this._selectedCandidate) {
                const patch = {};
                patch[name] = this._selectedCandidate[name];
                this.frmIndividualReceipt.patchValue(patch, { onlySelf: true });
              }
            }
          }
        });
    }

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
      if (this._selectedEntity && col.name !== 'cand_office_state') {
        this.showWarn(col.text, 'state');
      } else if (this._selectedCandidate ) {
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
      if (this._selectedCandidate ) {
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
        const patch = {};
        patch[description] = null;
        this.frmIndividualReceipt.patchValue(patch, { onlySelf: true });
      }
    } else {
      if (this.frmIndividualReceipt.contains(description)) {
        this.frmIndividualReceipt.controls[description].setValidators([Validators.nullValidator]);
        this.frmIndividualReceipt.controls[description].updateValueAndValidity();
        const patch = {};
        patch[description] = this.getElectionTypeDescription(item.electionType);
        this.frmIndividualReceipt.patchValue(patch, { onlySelf: true });
      }
    }
  }


  private getElectionTypeDescription(electionCode: string): string {
    if (this.electionTypes) {
      const electionType = this.electionTypes.find(element => element.electionType === electionCode);
      if (electionType) {
        return electionType.electionTypeDescription;
      }
    }
    return null;
  }

  private getElectionTypeCode(electionTypeDescription: string): string {
    if (this.electionTypes) {
      const electionType = this.electionTypes.find(element => element.electionTypeDescription === electionTypeDescription);
      if (electionType) {
        return electionType.electionType;
      }
    }
    return null;
  }

  /**
   * Vaidates the form on submit.
   * @param saveAction - determines which saveAction flow it is
   * @param navigateToViewTransactions - boolean flag to determine whether to navigate to transactions table after save sucessfully completes or not
   * @param printAfterSave - boolean flag to determine whether to print the currently being saved transaction after saving.
   *                       - this is used when printing a single transaction from form entry screen. Printing should actually save the current form
   *                       - and then if this flag is true, print the transaction. 
   */
  private _doValidateReceipt(saveAction: SaveActions, navigateToViewTransactions = false, printAfterSave = false): Observable<any> {
    // TODO because parent is saved automatically when user clicks add child, we
    // may not want to save it if unchanged.  Check form status for untouched.

    if (this.frmIndividualReceipt.valid) {
      const receiptObj: any = {};

      for (const field in this.frmIndividualReceipt.controls) {
        if (
          field === 'contribution_date' ||
          field === 'expenditure_date'
        ) {
          receiptObj[field] = this._utilService.formatDate(this.frmIndividualReceipt.get(field).value);
        } else if (field === 'disbursement_date' ||
          field === 'dissemination_date') {
          if (this.frmIndividualReceipt.get(field).value) {
            receiptObj[field] = this._utilService.formatDate(this.frmIndividualReceipt.get(field).value);
          }
        } else if (field === this._childFieldNamePrefix + 'contribution_date') {
          receiptObj[field] = this._utilService.formatDate(this.frmIndividualReceipt.get(field).value);
        } else if (field === 'memo_code') {
          if (this.memoCode) {
            receiptObj[field] = this.frmIndividualReceipt.get(field).value;
            //console.log('memo code val ' + receiptObj[field]);
          }
        } else if (field === this._childFieldNamePrefix + 'memo_code') {
          if (this.memoCodeChild) {
            receiptObj[field] = this.frmIndividualReceipt.get(field).value;
            //console.log('child memo code val ' + receiptObj[field]);
          }
        }
        // TODO: Incomplete FNE-1984
        /*else if (this.isFieldName(field, 'purpose_description') || this.isFieldName(field, 'expenditure_purpose')) {
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
        }*/
        else if (
          field === 'last_name' ||
          field === 'first_name' ||
          field === 'cand_last_name' ||
          field === 'cand_first_name' ||
          this.isFieldName(field, 'cmte_id') ||
          this.isFieldName(field, 'cmte_name') ||
          this.isFieldName(field, 'designating_cmte_name') ||
          this.isFieldName(field, 'subordinate_cmte_name') ||
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
        } else if (
          field === 'donor_cmte_id' ||
          field === 'payee_cmte_id' ||
          field === 'beneficiary_cmte_id' ||
          field === 'designating_cmte_id' ||
          field === 'subordinate_cmte_id'
        ) {
          // added this condition as formControl value is entire entity object
          // when we perform auto lookup.
          const typeAheadField = this.frmIndividualReceipt.get(field).value;
          if (typeAheadField && typeof typeAheadField !== 'string') {
            receiptObj[field] = typeAheadField['cmte_id'];
            if (field === 'payee_cmte_id') {
              receiptObj[field] = typeAheadField['payee_cmte_id'];
            }
          } else {
            receiptObj[field] = typeAheadField;
          }
        } else if (field === 'contribution_amount' || field === 'expenditure_amount') {
          if (this._contributionAmount === '') {
            let amountValue = this.frmIndividualReceipt.get(field).value;
            amountValue = amountValue.replace(/,/g, ``);
            this._contributionAmount = amountValue.toString();
          }
          receiptObj[field] = this._contributionAmount;
        } else if (field === this._childFieldNamePrefix + 'contribution_amount') {
          receiptObj[field] = this._contributionAmountChlid;
        } else if (
          field === 'beginning_balance' ||
          field === 'incurred_amount' ||
          field === 'balance_at_close' ||
          field === 'payment_amount' ||
          field === 'total_amount' ||
          field === 'fed_share_amount' ||
          field === 'non_fed_share_amount' ||
          field === 'activity_event_amount_ytd' ||
          field === 'aggregate_general_elec_exp' ||

          //for sched e YTD field
          field === 'expenditure_aggregate' ||

          // for H6 fields name
          field === 'federal_share' ||
          field === 'levin_share'
        ) {
          // fed_share_amount, non_fed_share_amount, activity_event_amount_ytd
          // Amounts in numeric format shoud be supported by the API.
          // The individual-receipt.service is currently only passing string values
          // to in the request.  TODO Why is this?  Remove the check or allow numerics and
          // then remove this block of code.
          let amountVal = null;
          if (this.frmIndividualReceipt.get(field).value) {
            amountVal = this.frmIndividualReceipt.get(field).value;
            if (amountVal) {
              amountVal = amountVal.toString();
              amountVal = amountVal.replace(/,/g, ``);
            }
          }
          receiptObj[field] = amountVal;
        } else if (field === 'levin_account_id') {
          receiptObj[field] = this.frmIndividualReceipt.get(field).value.toString();
        } else if (field === 'election_code' && this.frmIndividualReceipt 
                    && this.frmIndividualReceipt.get(field) && this.frmIndividualReceipt.get(field).value) {
          receiptObj[field] = this.frmIndividualReceipt.get(field).value[0];
        } else {
          receiptObj[field] = this.frmIndividualReceipt.get(field).value;
        }

        this.populateSchedFChildData(field, receiptObj);

      }

      // for each entity ID comes from the dynamic form fields as setEntityIdTo.
      // If setEntityIdTo not sent by API, default to entity_id.
      if (this._transactionToEdit) {
        this.hiddenFields.forEach((el: any) => {
          if (el.name === 'transaction_id') {
            el.value = this._transactionToEdit.transactionId;
            // If Transaction Id is present, setting Action to Edit, unless its a redesignation
            if (!this.redesignationTransactionId) {
              this.scheduleAction = ScheduleActions.edit;
            }
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
      if (
        this._parentTransactionModel &&
        this._parentTransactionModel.transactionId &&
        this.scheduleAction === ScheduleActions.addSubTransaction
      ) {
        receiptObj.back_ref_transaction_id = this._parentTransactionModel.transactionId;
      } 
      //else block is added for printing scenario from form entry screen for memos and child transactions
      //since printing the transaction "saves" it and changes the schedule action from add to edit. there fore
      //above block of code would not work since the schedule actio would not be addSubTransaction anymore
      else if(this.scheduleAction === ScheduleActions.edit && this._transactionToEdit && this._transactionToEdit.backRefTransactionId){
        receiptObj.back_ref_transaction_id = this._transactionToEdit.backRefTransactionId;
      }

      if (this.reattributionTransactionId) {
        receiptObj['reattribution_id'] = this.reattributionTransactionId;
        receiptObj['isReattribution'] = "true";

        let reattributionField = this.hiddenFields.find(element => element.name === "reattribution_report_id");
        if (this.scheduleAction === ScheduleActions.edit && !reattributionField) {
          receiptObj.reattribution_report_id = this._transactionToEdit.reportId.toString();
        }
      }
      if (this.redesignationTransactionId) {
        receiptObj['redesignation_id'] = this.redesignationTransactionId;
        receiptObj['isRedesignation'] = "true";

        let redesignationField = this.hiddenFields.find(element => element.name === "redesignation_report_id");
        if (this.scheduleAction === ScheduleActions.edit && !redesignationField) {
          receiptObj.redesignation_report_id = this._transactionToEdit.reportId.toString();
        }
      }

      // set the forced aggregation indicator
      receiptObj['aggregation_ind'] = this.isAggregate ? 'Y' : 'N';

      localStorage.setItem(`form_${this.formType}_receipt`, JSON.stringify(receiptObj));

      //if the reportId is present in the queryParams, that is the one that should be used instead
      //of using from local storage as it can very easily cause inconsistencies.
      let reportId = null;
      if (
        this._activatedRoute &&
        this._activatedRoute.snapshot &&
        this._activatedRoute.snapshot.queryParams &&
        this._activatedRoute.snapshot.queryParams.reportId
      ) {
        reportId = this._activatedRoute.snapshot.queryParams.reportId;
      }

      this._rollbackAfterUnsuccessfulSave = false;
      this._receiptService.saveSchedule(this.formType, this.scheduleAction, reportId).subscribe(res => {
        if (res) {

          const reportId = this._receiptService.getReportIdFromStorage(this.formType);
          this._reportsService
            .updateReportDate(new reportModel({ report_id: reportId }))
            .subscribe((resUpdateReportDate: any) => {
              //console.log(resUpdateReportDate);
            });
          this._receiptService.getSchedule(this.formType, res).subscribe(resp => {
            const message: any = {
              formType: this.formType,
              totals: resp
            };

            this._messageService.sendMessage(message);
          });

          this._contributionAmount = '';
          this._contributionAmountChlid = '';
          this._contributionAggregateValue = 0.0;
          this._contributionAggregateValueChild = 0.0;
          const contributionAggregateValue: string = this._decimalPipe.transform(
            this._contributionAggregateValue,
            '.2-2'
          );

          

          // Replace this with clearFormValues() if possible or break it into
          // 2 methods so 1 may be called here so as not to miss init vars.
          
          //only reset form if saving is NOT because of a print action.
          if(!printAfterSave){
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
            this.resetFormAttributes();
          }
          //if saving because of a print action, schedule action needs to be changed from add to edit for the next time.
          //also save the current POST response's metadata into the _transactionToEdit object for 'edit' flow
          else{
            if(!this._transactionToEdit){
              this._transactionToEdit = new TransactionModel({});
              this._transactionsService.mapSchedDatabaseRowToModel(this._transactionToEdit,res);
            }
            this.scheduleAction = ScheduleActions.edit;
          }
          // Replace this with clearFormValues() if possible - END

          localStorage.removeItem(`form_${this.formType}_receipt`);
          localStorage.setItem(`form_${this.formType}_saved`, JSON.stringify({ saved: true }));
          window.scrollTo(0, 0);

          let transactionId = null;
          if (res.hasOwnProperty('transaction_id')) {
            transactionId = res.transaction_id;
          } else {
            //console.log('schedA save has no transaction_id property');
          }

          // UI allows for returning to parent from unsaved child.  If this is the case switch
          // saveAction from saveForEditSub to saveForAddSub.
          if (saveAction === SaveActions.saveForEditSub) {
            let editChild = false;
            if (res) {
              if (res.hasOwnProperty('child')) {
                if (Array.isArray(res.child)) {
                  if (res.child.length > 0) {
                    if (res.child[0].hasOwnProperty('transaction_id')) {
                      if (res.child[0].transaction_id) {
                        editChild = true;
                      }
                    }
                  }
                }
              }
            }
            if (!editChild) {
              saveAction = SaveActions.saveForAddSub;
            }
          }

          // If save is for user click addChild, we are saving parent on behalf of the user
          // before presenting a new sub tran to add.  Save parent id and emit to show new child form.

          if (saveAction === SaveActions.saveForAddSub) {
            if (this.scheduleAction === ScheduleActions.add || this.scheduleAction === ScheduleActions.edit) {
              this._parentTransactionModel = this._transactionsService.mapFromServerSchedFields([res])[0];
              this._f3xMessageService.sendParentModelMessage(this._parentTransactionModel);
            }

            // If the child is a sub-schedule, send a message containing the parent transaction model.
            if (this.subTransactionInfo) {
              if (this.subTransactionInfo.scheduleType && this.subTransactionInfo.subScheduleType) {
                if (this.subTransactionInfo.scheduleType !== this.subTransactionInfo.subScheduleType) {
                  this._f3xMessageService.sendParentModelMessage(this._parentTransactionModel);
                }
              }
            }

            const addSubTransEmitObj: any = {
              form: this.frmIndividualReceipt,
              direction: 'next',
              step: 'step_3',
              previousStep: 'step_2',
              mainTransactionTypeText: this.mainTransactionTypeText,
              transactionTypeText: this.subTransactionInfo.subTransactionTypeDescription,
              transactionType: this.subTransactionInfo.subTransactionType,
              apiCall: this.subTransactionInfo.api_call,
              scheduleType: this.subTransactionInfo.subScheduleType,
              action: ScheduleActions.addSubTransaction
            };

            this._scheduleHBackRefTransactionId = transactionId;

            // If going to a payment for a debt accessed from the Summary, user must be returned to
            // Summary on cancel/save of Debt.  Therefore, summary details must be passed to payment.
            if (this.transactionType === 'DEBT_TO_VENDOR' || this.transactionType === 'DEBT_BY_VENDOR') {
              addSubTransEmitObj.returnToDebtSummary = true;
              addSubTransEmitObj.returnToDebtSummaryInfo = {
                transactionType: this.transactionType,
                transactionTypeText: this.transactionTypeText
              };
            }

            const prePopulateFieldArray = this._checkForPurposePrePopulate(res);
            if (prePopulateFieldArray) {
              addSubTransEmitObj.prePopulateFieldArray = prePopulateFieldArray;
            } else if (this.subTransactionInfo) {
              if (this.subTransactionInfo.scheduleType === 'sched_d' && this.subTransactionInfo.isParent === true) {
                addSubTransEmitObj.prePopulateFromSchedD = res;
              } else if (
                this.subTransactionInfo.scheduleType === 'sched_a' &&
                this.subTransactionInfo.isParent === true
              ) {
                if (this.subTransactionInfo.subTransactionType === 'LEVIN_PARTN_MEMO') {
                  if (res.hasOwnProperty('levin_account_id')) {
                    addSubTransEmitObj.prePopulateFromSchedL = res;
                    /*this.frmIndividualReceipt.controls['levin_account_id'].setValue(
                        res.levin_account_id
                      );*/
                  }
                }
              }else if(
                (this.subTransactionInfo.scheduleType === 'sched_h4' ||
                 this.subTransactionInfo.scheduleType === 'sched_h6') &&
                this.subTransactionInfo.isParent === true
              ){
                addSubTransEmitObj.prePopulateFromSchedH = res;
              }else if(
                this.subTransactionInfo.scheduleType === 'PARTN_REC' &&
                this.subTransactionInfo.isParent === true
              ){
                addSubTransEmitObj.prePopulateFromSchedPARTN = res;
              }
            }

            if (this.abstractScheduleComponent === AbstractScheduleParentEnum.schedFCoreComponent) {
              this.showPart2 = false;
            }
            this.status.emit(addSubTransEmitObj);
          } else if (saveAction === SaveActions.saveForEditSub) {
            this._progressToChild(ScheduleActions.edit, res);
          } else if (saveAction === SaveActions.saveForReturnToParent) {
            //TODO -- this is a flag that was being used to "track" whether cloning transaction was completed or not. 
            //it was initially only set for saveAction === SaveActions.updateOnly. But it should most likely be set to true for all
            //save actions if the save is successful, so the "cloning" process can be cleared. However, since its risky to change in all
            //places, changing it in the only other place that can possibly be triggered so far in the application.
            this._completedCloning = true;

            this.returnToParent(ScheduleActions.edit);
          } else if (saveAction === SaveActions.saveForReturnToNewParent) {
            this.returnToParent(ScheduleActions.add);
          } else if (saveAction === SaveActions.updateOnly) {
            if (this.isShedH4OrH6TransactionType(this.transactionType)) {
              this.goH4OrH6Summary(this.transactionType);
            } else if (
              this.returnToDebtSummary &&
              (this.transactionType === 'DEBT_TO_VENDOR' || this.transactionType === 'DEBT_BY_VENDOR')
            ) {
              this._goDebtSummary();
            } else if (
              this.returnToDebtSummary &&
              (this.transactionType === 'OPEXP_DEBT' ||
                this.transactionType === 'ALLOC_EXP_DEBT' ||
                this.transactionType === 'ALLOC_FEA_DISB_DEBT' ||
                this.transactionType === 'OTH_DISB_DEBT' ||
                this.transactionType === 'FEA_100PCT_DEBT_PAY' ||
                this.transactionType === 'COEXP_PARTY_DEBT' ||
                this.transactionType === 'IE_B4_DISSE' ||
                this.transactionType === 'OTH_REC_DEBT'
              )
            ) {
              this.returnToParent(this.editScheduleAction);
            } else {
              this._completedCloning = true;
              this.viewTransactions();
            }
          } else if (saveAction === SaveActions.saveForReturnToSummary) {
            if (this.isShedH4OrH6TransactionType(this.transactionType)) {
              this.goH4OrH6Summary(this.transactionType);
            }
          } else {
            if (saveAction === SaveActions.saveOnly) {
              // sched D subtran must have payee fields pre-poulated after saving one
              // and presenting new one to save.
              if (this.subTransactionInfo) {
                if (this.subTransactionInfo.scheduleType === 'sched_d' && this.subTransactionInfo.isParent === false) {
                  this._prePopulateFromSchedDData = res;
                  this._prePopulateFromSchedD(this._prePopulateFromSchedDData);
                } else if (
                  this.subTransactionInfo.scheduleType === 'sched_a' &&
                  this.subTransactionInfo.isParent === false
                ) {
                  if (this.subTransactionInfo.subTransactionType === 'LEVIN_PARTN_MEMO') {
                    this._prePopulateFromSchedLData = res;
                    this._prePopulateFromSchedL(this._prePopulateFromSchedLData);
                  }
                }else if (
                    this.subTransactionInfo.subTransactionType === 'ALLOC_EXP_CC_PAY_MEMO' ||
                    this.subTransactionInfo.subTransactionType === 'ALLOC_EXP_STAF_REIM_MEMO' ||
                    this.subTransactionInfo.subTransactionType === 'ALLOC_EXP_PMT_TO_PROL_MEMO' ||
                    this.subTransactionInfo.subTransactionType === 'ALLOC_FEA_CC_PAY_MEMO' ||
                    this.subTransactionInfo.subTransactionType === 'ALLOC_FEA_STAF_REIM_MEMO') {
                  this._prePopulateFromSchedHData = res;
                  this._prePopulateFromSchedH(this._prePopulateFromSchedHData);
                }else if (this.subTransactionInfo.subTransactionType === 'PARTN_MEMO') {
                  this._prePopulateFromSchedPARTNData = res;
                  this._prePopulateFromSchedPARTN(this._prePopulateFromSchedPARTNData);
                }
              }
              if (this.abstractScheduleComponent === AbstractScheduleParentEnum.schedFComponent ||
                this.abstractScheduleComponent === AbstractScheduleParentEnum.schedFCoreComponent) {
                this.showPart2 = false;
              }
              if(navigateToViewTransactions){
                this.viewTransactions();
              }
            }

            if(!printAfterSave){
              let resetParentId = true;
              if (this.subTransactionInfo) {
                if (this.subTransactionInfo.isParent === false) {
                  resetParentId = false;
                }
              }
              if (resetParentId) {
                this._parentTransactionModel = null;
                this.subTransactions = [];
              }
            }
          }
          // setting default action to add/addSub when we save transaction
          // as it should not be for edit after save. (unless save is happening through print, 
          // in which case it should stay on the same screen)
          if(!printAfterSave){
            if (!this.isEarmark()) {
              if (this._isSubOfParent()) {
                this.scheduleAction = ScheduleActions.addSubTransaction;
              } else {
                this.scheduleAction = ScheduleActions.add;
              }
            }
          }
        }
        //if save is happening due to a print action, then print the transaction as well after save. 
        if(printAfterSave){
          this._reportTypeService.printPreview('individual_receipt', this.formType,res.transaction_id,res.report_id);
        }
      }, error => {
        this._rollbackAfterUnsuccessfulSave = true;
        this._messageService.sendRollbackChangesMessage({ rollbackChanges: true });
      });
    } else {
      this.frmIndividualReceipt.markAsDirty();
      this.frmIndividualReceipt.markAsTouched();
      localStorage.setItem(`form_${this.formType}_saved`, JSON.stringify({ saved: false }));
      window.scrollTo(0, 0);

      const invalid = [];
      Object.keys(this.frmIndividualReceipt.controls).forEach(key => {
        if (this.frmIndividualReceipt.get(key).invalid) {
          invalid.push(key);
          console.error('invalid form field on submit = ' + key);
        }
      });

      return Observable.of('invalid');
    }
  }
  private resetFormAttributes() {
    this._transactionToEdit = null;
    this._formSubmitted = true;
    this.memoCode = false;
    this.memoCodeChild = false;
    this.frmIndividualReceipt.reset();
    this._prepopulateDefaultPurposeText();
    this._setMemoCodeForForm();
    this._selectedEntity = null;
    this._selectedChangeWarn = null;
    this._selectedEntityChild = null;
    this._selectedChangeWarnChild = null;
    this._selectedCandidate = null;
    this._selectedCandidateChangeWarn = null;
    this._selectedCandidateChild = null;
    this._selectedCandidateChangeWarnChild = null;
    this._isShowWarn = true;
    this.activityEventNames = null;
    this.reattributionTransactionId = null;
    this.redesignationTransactionId = null;
  }

  _prepopulateDefaultPurposeText() {
    const purposeFormField = this.findFormFieldContaining('purpose');
    if (purposeFormField && purposeFormField.preText && purposeFormField.value && purposeFormField.preText === purposeFormField.value) {
      const patch = {};
      patch[purposeFormField.name] = purposeFormField.preText;
      this.frmIndividualReceipt.patchValue(patch, { onlySelf: true });
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
    if(this.frmIndividualReceipt.status === 'INVALID') {
      this.viewTransactions();
    }else {
      if(this._cloned) {
        this._cloned = false;
      }

      if (!this.frmIndividualReceipt.dirty) {
        this.clearFormValues();
        this.returnToParent(ScheduleActions.edit);
      } else {
        this._doValidateReceipt(SaveActions.saveForReturnToParent);
      }
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
    if (this._findHiddenField('name', 'show_memo_warning') &&
      this._findHiddenField('name', 'show_memo_warning').value) {
      if (!this.frmIndividualReceipt.valid) {
        return;
      }
      this._dialogService.confirm(this.childNeededWarnText, ConfirmModalComponent, 'Warning !!!', false).then(
        res => {
          if (res === 'okay') {
            this._doValidateReceipt(SaveActions.saveOnly);
          } else {
            //used by sched f
            this.showPart2 = true;
            return;
          }
        });
    } else {
      this._doValidateReceipt(SaveActions.saveOnly);
    }
  }

  public updateOnly(): void {
    this._doValidateReceipt(SaveActions.updateOnly);
  }

  private _progressToChild(scheduleAction: ScheduleActions, res: any): void {
    let childTransactionId = null;
    let childTransaction = null;
    let apiCall = null;
    if (res.hasOwnProperty('child')) {
      if (Array.isArray(res.child)) {
        if (res.child.length > 0) {
          childTransaction = res.child[0];
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
      // Need a better way to pass a fully populated child TransactionModel.
      // Until then mapping for additional fields will be done here field by field.
      if (childTransaction) {
        let prefix = '';
        if (childTransaction.hasOwnProperty('contribution_amount')) {
          prefix = 'contribution_';
        } else if (childTransaction.hasOwnProperty('expenditure_amount')) {
          prefix = 'expenditure_';
        }
        transactionModel.amount = childTransaction[prefix + 'amount'];
        transactionModel.date = childTransaction[prefix + 'date'];
        transactionModel.aggregate = childTransaction[prefix + 'aggregate'];
        transactionModel.memoCode = childTransaction.memo_code;
        transactionModel.entityId = childTransaction.entity_id;
      }

      this.memoCode = false;
      this.memoCodeChild = false;
      const emitObj: any = {
        form: {},
        direction: 'next',
        step: 'step_3',
        previousStep: 'step_2',
        mainTransactionTypeText: this.mainTransactionTypeText,
        transactionTypeText: this.subTransactionInfo.subTransactionTypeDescription,
        transactionType: this.subTransactionInfo.subTransactionType,
        action: scheduleAction,
        scheduleType: this.subTransactionInfo.subScheduleType
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
    this.clearFormValues();
    // this._f3xMessageService.sendParentModelMessage({key:'setParentTransactionModel', model:this._parentTransactionModel});
    let transactionModel = this._parentTransactionModel;
    if (!transactionModel) {
      transactionModel = new TransactionModel({});
    }
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
      mainTransactionTypeText: this.mainTransactionTypeText,
      transactionTypeText: this.subTransactionInfo.transactionTypeDescription,
      transactionType: this.subTransactionInfo.transactionType,
      action: scheduleAction,
      scheduleType: this.subTransactionInfo.scheduleType
    };
    if (scheduleAction === ScheduleActions.edit) {
      emitObj.transactionDetail = { transactionModel: transactionModel };
    }
    if (
      (transactionModel.transactionTypeIdentifier === 'DEBT_TO_VENDOR' ||
        transactionModel.transactionTypeIdentifier === 'DEBT_BY_VENDOR') &&
      this.returnToDebtSummary
    ) {
      emitObj.returnToDebtSummary = true;
      emitObj.returnToDebtSummaryInfo = this.returnToDebtSummaryInfo;
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

  protected _setSetEntityIdTo(userSelectedEntity: any, col: any) {
    if (col.setEntityIdTo) {
      userSelectedEntity.setEntityIdTo = col.setEntityIdTo;
    }
  }

  /**
   * Determines ability for a person to leave a page with a form on it.
   *
   * @return     {boolean}  True if able to deactivate, False otherwise.
   */
  public async canDeactivate(): Promise<boolean> {
    if (this._formService.formHasUnsavedData(this.formType)) {
      let result: boolean = null;
      result = await this._dialogService.confirm('', ConfirmModalComponent).then(res => {
        let val: boolean = null;

        if (res === 'okay') {
          val = true;
        } else if (res === 'cancel') {
          val = false;
        }

        return val;
      });

      return result;
    } else {
      return true;
    }
  }

  /**
   * Goes to the previous step.
   */
  public previousStep(): void {
    this.canDeactivate().then(result => {
      if (result === true) {
        localStorage.removeItem(`form_${this.formType}_saved`);
        this.clearFormValues();
        this.status.emit({
          form: {},
          direction: 'previous',
          step: 'step_2'
        });
      }
    });
  }

  /**
   * Save the current transaction if valid  and show transactions
   * if invalid show unsaved confirmation and navigate accordingly
   */
  public saveOrWarn(): void {
    if (this.frmIndividualReceipt.valid) {
      // if form is valid check if transactionId exists
      // if exists do not check/show warning for child trx required
      // else check for the warning flag and show popup, on ok save and view transaction else return to the page
      if (this.isShowChildRequiredWarn()) {
        this._dialogService.confirm(this.childNeededWarnText, ConfirmModalComponent, 'Warning !!!', false).then(
          res => {
            if (res === 'okay') {
              this._doValidateReceipt(SaveActions.saveOnly, true);
              // this.viewTransactions();
            } else {
              this.showPart2 = true;
              return;
            }
          });
      } else {
        this._doValidateReceipt(SaveActions.saveOnly, true);
        // this.viewTransactions();
      }
    } else {
      this._dialogService.confirm('', ConfirmModalComponent, '', true).then(res => {
        if (res === 'okay' ? true : false) {
          this.viewTransactions();
        }
      });
    }
  }
  /**
   * Navigate to the Transactions.
   */
  public viewTransactions(): void {
    if (!this._cloned || this._completedCloning) {
      this.clearFormValues();
      let reportId = this._receiptService.getReportIdFromStorage(this.formType);
      //console.log('reportId', reportId);

      if (!reportId) {
        reportId = '0';
      }
      localStorage.setItem(`form_${this.formType}_view_transaction_screen`, 'Yes');
      localStorage.setItem('Transaction_Table_Screen', 'Yes');
      this._transactionsMessageService.sendLoadTransactionsMessage(reportId);

      if(this.returnToGlobalAllTransaction){
        this.goToGlobalAllTransactions();        
      }
      else{
        this._router.navigate([`/forms/form/${this.formType}`], {
          queryParams: {
            step: 'transactions',
            reportId: reportId,
            edit: this.editMode,
            transactionCategory: this._transactionCategory
          }
        });
      }
    } else {
      let reportId = this._receiptService.getReportIdFromStorage(this.formType);
      /*
      if (!reportId && this._activatedRoute && this._activatedRoute.snapshot && 
        this._activatedRoute.snapshot.queryParams && this._activatedRoute.snapshot.queryParams.reportId){
           reportId = this._activatedRoute.snapshot.queryParams.reportId
      }
      else{
        reportId = '0';
      }
      */
      if (!reportId) {
        if (
          this._activatedRoute &&
          this._activatedRoute.snapshot &&
          this._activatedRoute.snapshot.queryParams &&
          this._activatedRoute.snapshot.queryParams.reportId
        ) {
          reportId = this._activatedRoute.snapshot.queryParams.reportId;
        } else {
          reportId = '0';
        }
      }
      this._dialogService
        .confirm(
          'You are about to delete this transaction ' + this._transactionToEdit.transactionId + '.',
          ConfirmModalComponent,
          'Caution!'
        )
        .then(res => {
          if (res === 'okay') {
            this._transactionsService
              .trashOrRestoreTransactions(this.formType, 'trash', reportId, [this._transactionToEdit])
              .subscribe((res: GetTransactionsResponse) => {
                this._dialogService
                  .confirm(
                    'Transaction has been successfully deleted and sent to the recycle bin. ' +
                    this._transactionToEdit.transactionId,
                    ConfirmModalComponent,
                    'Success!',
                    false,
                    ModalHeaderClassEnum.successHeader
                  )
                  .then(response => {
                    if (
                      response === 'okay' ||
                      response === 'cancel' ||
                      response === ModalDismissReasons.BACKDROP_CLICK ||
                      response === ModalDismissReasons.ESC
                    ) {
                      if(this.returnToGlobalAllTransaction){
                        this.goToGlobalAllTransactions();
                      }
                      else{
                        this._router.navigate([`/forms/form/${this.formType}`], {
                          queryParams: {
                            step: 'transactions',
                            reportId: reportId,
                            edit: this.editMode,
                            transactionCategory: this._transactionCategory,
                            refresh: 1
                          }
                        });
                      }
                    }
                  });
              });
          } else if (res === 'cancel') {
          }
        });
    }
  }

  private goToGlobalAllTransactions() {
    this._router.navigate([`/forms/form/global`], {
      queryParams: {
        step: 'transactions',
        allTransactions: true,
        transactionCategory: this._transactionCategory
      }
    });
  }

  /**
   * This method should be used to print the current transaction from form entry screen. 
   * It should first save the current transaction if form is valid and based on the printAfterSave
   * flag, should print the transaction as well. 
   */
  public printCurrentTransaction(): void{
    this._doValidateReceipt(SaveActions.saveOnly,false,true);
  }

  public printPreview(): void {
    this._reportTypeService.printPreview('individual_receipt', this.formType);
  }
  public ImportTransactions(): void {
    alert('Import transaction is not yet supported');
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
    const cmteName = result.cmte_name ? result.cmte_name.trim() : '';
    return `${name},${cmteName},${street1}, ${street2}`;
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
    this.slectedCandidate(entity, col);
  }

  private slectedCandidate(entity: any, col: any) {
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

    this._isShowWarn = true;

    const fieldNames = [];
    fieldNames.push('cand_last_name');
    fieldNames.push('cand_first_name');
    fieldNames.push('cand_middle_name');
    fieldNames.push('cand_prefix');
    fieldNames.push('cand_suffix');
    fieldNames.push('cand_office');
    fieldNames.push('cand_office_state');
    fieldNames.push('cand_office_district');
    // fieldNames.push('cand_election_year');  -- commenting this as per business requirements. This should not be autopopulated
    fieldNames.push('beneficiary_cand_id');
    fieldNames.push('payee_cmte_id');
    this._patchFormFields(fieldNames, entity, namePrefix);
    // setting Beneficiary Candidate Entity Id to hidden variable
    const beneficiaryCandEntityIdHiddenField = this._findHiddenField('name', 'beneficiary_cand_entity_id');
    if (beneficiaryCandEntityIdHiddenField) {
      beneficiaryCandEntityIdHiddenField.value = entity.beneficiary_cand_entity_id;
    }

    if (this.abstractScheduleComponent === AbstractScheduleParentEnum.schedFComponent ||
      this.abstractScheduleComponent === AbstractScheduleParentEnum.schedFCoreComponent) {
      if (this.frmIndividualReceipt.contains('expenditure_date')) {
        if (this._selectedCandidate) {
          if (this._selectedCandidate.beneficiary_cand_id) {
            const dateValue = this.frmIndividualReceipt.get('expenditure_date').value;
            const expenditureDate = this._utilService.formatDate(dateValue);
            this._getSchedFDebtPaymentAggregate(
              this._selectedCandidate.beneficiary_cand_id,
              expenditureDate,
              this._selectedCandidate.beneficiary_cand_entity_id
            );
          }
        }
      }
    }
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

    this._isShowWarn = true;

    const fieldNames = [];
    fieldNames.push('last_name');
    fieldNames.push('first_name');
    fieldNames.push('middle_name');
    fieldNames.push('prefix');
    // TODO: Should be removed later FNE-1974
    fieldNames.push('preffix');
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

  protected _patchFormFields(fieldNames: string[], entity: any, namePrefix: string) {
    if (fieldNames) {
      for (const fieldName of fieldNames) {
        const patch = {};
        // TODO: Should be removed later FNE-1974
        if (fieldName === 'preffix') {
          console.warn('Fix this issue backend Column-name preffix')
          patch[namePrefix + 'prefix'] = entity[fieldName];
        } else {
          patch[namePrefix + fieldName] = entity[fieldName];
        }
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

    if(entity.cmte_id) {
      this._typeaheadService.getContactsExpand(entity.cmte_id).subscribe(
        res => {
          if(res) {
            const entity = res[0];
            this.slectedCandidate(entity, col);
          }
        }
      )
    }

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

    this._isShowWarn = true;

    // These field names map to the same name in the form
    const fieldNames = [];
    fieldNames.push('street_1');
    fieldNames.push('street_2');
    fieldNames.push('city');
    fieldNames.push('state');
    fieldNames.push('zip_code');
    fieldNames.push('occupation');
    fieldNames.push('employer');
    if (this.isCandidateAssociatedWithPayee()) {
      fieldNames.push('cand_last_name');
      fieldNames.push('cand_first_name');
      fieldNames.push('cand_middle_name');
      fieldNames.push('cand_suffix');
      fieldNames.push('cand_prefix');
      fieldNames.push('cand_office');
      fieldNames.push('cand_office_state');
      fieldNames.push('cand_office_district');
      fieldNames.push('payee_cmte_id');
    }
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
  isCandidateAssociatedWithPayee(): boolean {
    if (this.candidateAssociatedWithPayeeTransactionTypes.includes(this.transactionType)) {
      return false;
    }
    return true;
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

  searchPrefix = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'prefix');
        } else {
          return Observable.of([]);
        }
      })
    );

  searchSuffix = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'suffix');
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
        if (searchText.length === 0) {
          this.clearOrgData();
        }
        if (searchText) {
          if(this.transactionType === 'TRIB_REC'
            || this.transactionType === 'TRIB_RECNT_REC'
            || this.transactionType === 'TRIB_NP_RECNT_ACC'
            || this.transactionType === 'TRIB_NP_HQ_ACC'
            || this.transactionType === 'TRIB_NP_CONVEN_ACC'
            || this.transactionType === 'OPEXP_HQ_ACC_TRIB_REF'
            || this.transactionType === 'OPEXP_CONV_ACC_TRIB_REF'
            || this.transactionType === 'OTH_DISB_NP_RECNT_TRIB_REF'
            || this.transactionType === 'PAC_NON_FED_REC'
            || this.transactionType === 'PAC_NON_FED_RET'
            //|| this.transactionType === 'ALLOC_EXP'
            //|| this.transactionType === 'ALLOC_EXP_CC_PAY'

            || this.transactionType === 'PARTN_REC'
            || this.transactionType === 'BUS_LAB_NON_CONT_ACC'
            || this.transactionType === 'OTH_REC'

            || this.transactionType === 'ALLOC_EXP'
            || this.transactionType === 'ALLOC_EXP_CC_PAY'
            || this.transactionType === 'ALLOC_EXP_CC_PAY_MEMO'
            || this.transactionType === 'ALLOC_EXP_STAF_REIM'
            || this.transactionType === 'ALLOC_EXP_STAF_REIM_MEMO'
            || this.transactionType === 'ALLOC_EXP_PMT_TO_PROL'
            || this.transactionType === 'ALLOC_EXP_PMT_TO_PROL_MEMO'
            || this.transactionType === 'ALLOC_EXP_VOID'

            || this.transactionType === 'ALLOC_FEA_DISB'
            || this.transactionType === 'ALLOC_FEA_CC_PAY'
            || this.transactionType === 'ALLOC_FEA_CC_PAY_MEMO'
            || this.transactionType === 'ALLOC_FEA_STAF_REIM'
            || this.transactionType === 'ALLOC_FEA_STAF_REIM_MEMO'
            || this.transactionType === 'ALLOC_FEA_VOID'

            || this.transactionType === 'LEVIN_VOTER_REG'
            || this.transactionType === 'LEVIN_VOTER_ID'
            || this.transactionType === 'LEVIN_GOTV'
            || this.transactionType === 'LEVIN_GEN'
            || this.transactionType === 'LEVIN_OTH_DISB'

            || this.transactionType === 'LEVIN_ORG_REC'
            || this.transactionType === 'LEVIN_PARTN_REC'
            || this.transactionType === 'LEVIN_NON_FED_REC'
            || this.transactionType === 'LEVIN_TRIB_REC'
            || this.transactionType === 'LEVIN_OTH_REC'

            || this.transactionType === 'OPEXP'
            || this.transactionType === 'OPEXP_CC_PAY'
            || this.transactionType === 'OPEXP_STAF_REIM'
            || this.transactionType === 'OPEXP_PMT_TO_PROL'
            || this.transactionType === 'OPEXP_VOID'

            || this.transactionType === 'IE'
            || this.transactionType === 'IE_MULTI'
            || this.transactionType === 'IE_STAF_REIM_MEMO'
            || this.transactionType === 'IE_CC_PAY'
            || this.transactionType === 'IE_CC_PAY_MEMO'
            || this.transactionType === 'IE_STAF_REIM'
            || this.transactionType === 'IE_PMT_TO_PROL'
            || this.transactionType === 'IE_VOID'

            || this.transactionType === 'OTH_DISB'
            || this.transactionType === 'OTH_DISB_CC_PAY'
            || this.transactionType === 'OTH_DISB_STAF_REIM'
            || this.transactionType === 'OTH_DISB_PMT_TO_PROL'
            || this.transactionType === 'OTH_DISB_RECNT'
            || this.transactionType === 'OTH_DISB_NP_RECNT_ACC'
            || this.transactionType === 'OTH_DISB_VOID'
            || this.transactionType === 'OPEXP_HQ_ACC_OP_EXP_NP'
            || this.transactionType === 'OPEXP_CONV_ACC_OP_EXP_NP'
            || this.transactionType === 'OPEXP_HQ_ACC_TRIB_REF'
            || this.transactionType === 'OPEXP_CONV_ACC_TRIB_REF'
            || this.transactionType === 'OTH_DISB_NP_RECNT_TRIB_REF'

            || this.transactionType === 'FEA_100PCT_PAY'
            || this.transactionType === 'FEA_CC_PAY'
            || this.transactionType === 'FEA_STAF_REIM'
            || this.transactionType === 'FEA_PAY_TO_PROL'
            || this.transactionType === 'FEA_VOID'

            || this.transactionType === 'DEBT_BY_VENDOR'
            || this.transactionType === 'DEBT_TO_VENDOR'
          ){
            return this._typeaheadService.getContacts(searchText, 'entity_name', false, 'OFF');
          }else if(this.transactionType === 'CON_EAR_DEP_MEMO'
            || this.transactionType === 'CON_EAR_UNDEP_MEMO'
            || this.transactionType === 'CONT_TO_CAN'
            || this.transactionType === 'CONT_VOID') {
            return this._typeaheadService.getContacts(searchText, 'entity_name', true);
          }else {
            return this._typeaheadService.getContacts(searchText, 'entity_name');
          }
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
   * TODO: Rename 'preffix' to 'prefix'. It's 'preffix' in database now.
   */
  formatterPrefix = (x: { preffix: string }) => {
    if (typeof x !== 'string') {
      return x.preffix;
    } else {
      return x;
    }
  };

  formatterSuffix = (x: { suffix: string }) => {
    if (typeof x !== 'string') {
      return x.suffix;
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
    if(fieldName.includes('memo_code') && (this.redesignationTransactionId || this.reattrbutionTransaction)){
      return true;
    }
    else{
      const isChildForm = fieldName.startsWith(this._childFieldNamePrefix) ? true : false;
      if (isChildForm) {
        return this.memoCodeChild;
      } else {
        return this.memoCode;
      }
    }
  }

  /**
   * Apply business rules when date changes.
   *
   * @param fieldName the date field name in the form.
   */
  public dateChange(fieldName: string) {
    //console.log('date has changed!');

    if (this.reattributionTransactionId || this.redesignationTransactionId) {
      this.handleDateChangeForReattributionOrRedesignation(fieldName);
    }
    else {

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
          if (this.abstractScheduleComponent === AbstractScheduleParentEnum.schedFComponent ||
            this.abstractScheduleComponent === AbstractScheduleParentEnum.schedFCoreComponent) {
            if (fieldName === 'expenditure_date') {
              if (this._selectedCandidate) {
                if (this._selectedCandidate.beneficiary_cand_id) {
                  const expenditureDate = this._utilService.formatDate(dateValue);
                  this._getSchedFDebtPaymentAggregate(
                    this._selectedCandidate.beneficiary_cand_id,
                    expenditureDate,
                    this._selectedCandidate.beneficiary_cand_entity_id
                  );
                }
              }
            }
          } else {
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
    }
  }


  /**
   * This method handles date change logic for reattributions.
   * @param fieldName 
   */
  protected handleDateChangeForReattributionOrRedesignation(fieldName: string) {
    // clear current validators for the dateField and add reattribtionValdiator
    this.frmIndividualReceipt.controls[fieldName].clearValidators();
    this.frmIndividualReceipt.controls[fieldName].setValidators([Validators.required]);
    if (this.frmIndividualReceipt.contains(fieldName)) {
      const dateValue = this.frmIndividualReceipt.get(fieldName).value;
      if (!dateValue) {
        return;
      }
      this.frmIndividualReceipt.controls[fieldName].setErrors(null);
      this._receiptService.getReportIdByTransactionDate(this._utilService.formatDate(dateValue)).subscribe(res => {
        if (res) {
          if (res.reportId) {
            if (res.status && res.status !== 'Filed') {
              this.getContributionAggregate(dateValue, fieldName);
              let elementName = null;
              if (this.reattributionTransactionId) {
                elementName = 'reattribution_report_id'
              }
              else if (this.redesignationTransactionId) {
                elementName = 'redesignation_report_id'
              }
              if (elementName) {
                let field = this.hiddenFields.find(element => element.name === elementName);
                if (field) {
                  field.value = res.reportId.toString();
                }
                else {
                  this.hiddenFields.push({ type: 'hidden', name: elementName, value: res.reportId.toString() });
                }
              }
            }
            else if (res.status && res.status === 'Filed') {
              this.frmIndividualReceipt.controls[fieldName].setErrors({ reportFiled: true });
            }
          }
          else {
            this.frmIndividualReceipt.controls[fieldName].setErrors({ reportNotFound: true });
          }
        }
      })

    }
  }

  private getContributionAggregate(dateValue: any, fieldName: string) {
    if (this._selectedEntity) {
      if (this._selectedEntity.entity_id) {
        const contribDate = this._utilService.formatDate(dateValue);
        if (fieldName === 'contribution_date') {
          this._getContributionAggregate(contribDate, this._selectedEntity.entity_id, null);
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
  //       //console.log('this._selectedEntityId = ' + this._selectedEntityId);
  //       return true;
  //     }
  //   }
  //   return null;
  // }

  private _getFormFields(): void {
    //console.log('get transaction type form fields ' + this.transactionType);

    // init some of the dynamic form data for each call.
    // TODO may need to add others.
    this.subTransactionInfo = null;
    this.multipleSubTransactionInfo = null;
    this.subTransactions = [];
    this.memoDropdownSize = null;
    this.totalAmountReadOnly = true;
    const levinText = 'LEVIN';
    const staticTranTypes = [
      'ALLOC_H2_SUM',
      'ALLOC_H1',
      'ALLOC_H2_RATIO',
      'ALLOC_H3_RATIO',
      'ALLOC_H3_SUM',
      'ALLOC_H3_SUM_P',
      'ALLOC_H5_RATIO',
      'ALLOC_H5_SUM',
      'ALLOC_H5_SUM_P',
      'ALLOC_H4_TYPES',
      'ALLOC_H6_TYPES',
      'LA_ENTRY',
      'LB_ENTRY',
      'LA_SUM',
      'LB_SUM',
      'L_SUM',
      'ALLOC_H4_SUM',
      'ALLOC_H6_SUM'
    ];
    // var a = [1,2,3];
    // Do not call dynaic form for statis transaction types
    if (staticTranTypes.indexOf(this.transactionType) !== -1) {
      return;
    }

    if (this.transactionType.startsWith(levinText)) {
      this._receiptService.getLevinAccounts().subscribe(res => {
        if (res) {
          this.levinAccounts = res;
        }else {
          this._dialogService
          .confirm(
            'You must first create the Levin account in the Profile Account screen.',
            ConfirmModalComponent,
            'Warning!',
            false
            )
          .then(res => {
            if (res === 'okay') {
              this._router.navigate(['/account']);
            } else if (res === 'cancel') {
            }
          });
        }
      });
    }
    this._receiptService.getDynamicFormFields(this.formType, this.transactionType).takeUntil(this.onDestroy$)
      .subscribe(res => {
        res = this._hijackFormFields(res);
        if (res) {
          if (res.hasOwnProperty('data')) {
            if (typeof res.data === 'object') {
              if (res.data.hasOwnProperty('formFields')) {
                if (Array.isArray(res.data.formFields)) {
                  // If fields are pre-populated for "static" forms, append any additional fields
                  // from the API as with SF.
                  if (this.formFieldsPrePopulated) {
                    if (this.staticFormFields) {
                      if (this.staticFormFields.length > 0) {
                        for (const field of this.staticFormFields) {
                          res.data.formFields.push(field);
                        }
                      }
                    }
                  }
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

              if (res.data.hasOwnProperty('committeeTypeEvents')) {
                if (Array.isArray(res.data.committeeTypeEvents)) {
                  const committeeTypeEvents = res.data.committeeTypeEvents;
                  if (this._cmteTypeCategory) {
                    for (const committeeTypeEvent of committeeTypeEvents) {
                      if (this._cmteTypeCategory === committeeTypeEvent.committeeTypeCategory) {
                        this.activityEventTypes = committeeTypeEvent.eventTypes;
                      }

                      if (
                        (this.transactionType === 'ALLOC_FEA_DISB' ||
                          this.transactionType === 'ALLOC_FEA_DISB_DEBT' ||
                          this.transactionType === 'ALLOC_FEA_CC_PAY' ||
                          this.transactionType === 'ALLOC_FEA_CC_PAY_MEMO' ||
                          this.transactionType === 'ALLOC_FEA_STAF_REIM' ||
                          this.transactionType === 'ALLOC_FEA_STAF_REIM_MEMO' ||
                          this.transactionType == 'ALLOC_FEA_VOID') &&
                        'H6' === committeeTypeEvent.committeeTypeCategory
                      ) {
                        this.activityEventTypes = committeeTypeEvent.eventTypes;
                      }
                    }
                  }
                }
              }

              if (res.data.hasOwnProperty('titles')) {
                if (Array.isArray(res.data.titles)) {
                  this.titles = res.data.titles;
                }
              }
              if (res.data.hasOwnProperty('entityTypes')) {
                // TODO entityTypes are not returned by dynamic forms API for some.
                // If propery exists but is null use hard coded default until API returns.
                if (!res.data.entityTypes) {
                  res.data.entityTypes = this.entityTypes;
                  if(!res.data.entityTypes || res.data.entityTypes.length === 0){
                    res.data.entityTypes = this.staticEntityTypes;

                    //also need to choose which option should be selected by default based on the form fields present
                    //for now logic being used is if the formFields has 'entity_name' field present, its a org, otherwise its ind
                    // this.applyDefaultEntity();
                    this.applyDefaultEntity(res);
                  }
                }
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
                  if(this.transactionType === 'LEVIN_INDV_REC') {
                    this.selectedEntityType.entityType = 'IND';
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
                      // Fix an issue where previous transaction type is passed.
                      for (const hiddenField of this.hiddenFields) {
                        if ('transaction_type_identifier' === hiddenField.name) {
                          if ((hiddenField.value = this.transactionType)) {
                            this.multipleSubTransactionInfo = res.data.subTransactions;
                          }
                        }
                      }
                    }
                  }
                }
              }
            } // typeof res.data
          } // res.hasOwnProperty('data')
        } // res
        this._prePopulateFormField(this._prePopulateFieldArray);
        this._prePopulateFieldArray = null;

        let apiCall: string = this._findHiddenField('name', 'api_call');
        apiCall = apiCall ? apiCall : '';

        let { schedDSubTran, schedLSubTran, schedHSubTran } = this.determineSubTransactionType();

        // If Data for sched D, H or L sub-tran has been received by the message service,
        // pre-populate the formGroup now that the dynamic form API call is complete.
        this.populateDataForSchedDSubTransaction(schedDSubTran);
        this.populateDataForSchedLSubTransaction(schedLSubTran);
        this.populateDataForSchedHSubTransaction(schedHSubTran);

        this.sendPopulateMessageIfApplicable();
      });

  }

  /**
   * This method is being used as a patch fix until API is fixed to return default/selected entity type array
   * @param res 
   */
  private applyDefaultEntity(res: any) {
    let defaultEntityisOrg: boolean = false;
    if (this.findFormField('entity_name')) {
      defaultEntityisOrg = true;
    }
    res.data.entityTypes.forEach(element => {
      if (element.entityType === 'ORG') {
        if (defaultEntityisOrg) {
          element.selected = true;
        }
        else {
          element.selected = false;
        }
      }
      else if (element.entityType === 'IND') {
        if (defaultEntityisOrg) {
          element.selected = false;
        }
        else {
          element.selected = true;
        }
      }
    });
  }

  private populateDataForSchedHSubTransaction(schedHSubTran: boolean) {
    if (this._prePopulateFromSchedHData &&
      schedHSubTran &&
      this.scheduleAction === ScheduleActions.addSubTransaction) {
      this._prePopulateFromSchedH(this._prePopulateFromSchedHData);
      this._prePopulateFromSchedHData = null;
    }
  }

  private populateDataForSchedLSubTransaction(schedLSubTran: boolean) {
    if (this._prePopulateFromSchedLData &&
      schedLSubTran &&
      this.scheduleAction === ScheduleActions.addSubTransaction) {
      this._prePopulateFromSchedL(this._prePopulateFromSchedLData);
      this._prePopulateFromSchedLData = null;
    }
  }

  private determineSubTransactionType() {
    let schedDSubTran = false;
    let schedLSubTran = false;
    let schedHSubTran = false;
    if (this.subTransactionInfo) {
      if (this.subTransactionInfo.scheduleType === 'sched_d' && this.subTransactionInfo.isParent === false) {
        schedDSubTran = true;
      }
      else if (this.subTransactionInfo.scheduleType === 'sched_a' && this.subTransactionInfo.isParent === false) {
        if (this.subTransactionInfo.subTransactionType === 'LEVIN_PARTN_MEMO') {
          schedLSubTran = true;
          /*if (res.hasOwnProperty('levin_account_id')) {
            prePopulateFieldArray.push({ name: 'levin_account_id', value: res.levin_account_id });
          }*/
        }
      }
      else if (this.subTransactionInfo.subTransactionType === 'ALLOC_EXP_CC_PAY_MEMO' ||
        this.subTransactionInfo.subTransactionType === 'ALLOC_EXP_STAF_REIM_MEMO' ||
        this.subTransactionInfo.subTransactionType === 'ALLOC_EXP_PMT_TO_PROL_MEMO' ||
        this.subTransactionInfo.subTransactionType === 'ALLOC_FEA_CC_PAY_MEMO' ||
        this.subTransactionInfo.subTransactionType === 'ALLOC_FEA_STAF_REIM_MEMO') {
        schedHSubTran = true;
      }
    }
    return { schedDSubTran, schedLSubTran, schedHSubTran };
  }

  private populateDataForSchedDSubTransaction(schedDSubTran: boolean) {
    if (this._prePopulateFromSchedDData &&
      schedDSubTran &&
      this.scheduleAction === ScheduleActions.addSubTransaction) {
      this._prePopulateFromSchedD(this._prePopulateFromSchedDData);
      this._prePopulateFromSchedDData = null;
    }
  }

  /**
   * For overriding form fields from API with front end version.
   *
   * @param res
   */
  private _hijackFormFields(res: any): any {
    //console.log('Hijack for : ' + this.transactionType);
    switch (this.transactionType) {
      case 'COEXP_PARTY':
        res = new CoordinatedPartyExpenditureFields().coordinatedPartyExpenditureFields;
        break;
      case 'COEXP_CC_PAY':
        res = new CoordinatedExpenditureCCFields().coordinatedExpenditureCCFields;
        break;
      case 'COEXP_STAF_REIM':
        res = new CoordinatedExpenditureStaffFields().coordinatedExpenditureStaffFields;
        break;
      case 'COEXP_PMT_PROL':
        res = new CoordinatedExpenditurePayrollFields().coordinatedExpenditurePayrollFields;
        break;
      case 'COEXP_PARTY_VOID':
        res = new CoordinatedPartyExpenditureVoidFields().coordinatedPartyExpenditureVoidFields;
        break;
      case 'COEXP_CC_PAY_MEMO':
        res = new CoordinatedExpenditureCcMemoFields().coordinatedExpenditureCCMemoFields;
        this.loaded = false;
        this.showPart2 = true;
        break;
      case 'COEXP_STAF_REIM_MEMO':
        res = new CoordinatedExpenditureStaffMemoFields().coordinatedExpenditureStaffMemoFields;
        this.loaded = false;
        this.showPart2 = true;
        break;
      case 'COEXP_PMT_PROL_MEMO':
        res = new CoordinatedExpenditurePayrollMemoFields().coordinatedExpenditurePayrollMemoFields;
        this.loaded = false;
        this.showPart2 = true;
        break;
      default:
    }
    return res;
  }

  /**
   * Toggle fields in the form depending on entity type.
   */
  public handleEntityTypeChange(item: any) {
    // Set the selectedEntityType for the toggle method to check.
    for (const entityTypeObj of this.entityTypes) {
      if (entityTypeObj.entityType === item.entityType) {
        entityTypeObj.selected = true;
        this.selectedEntityType = entityTypeObj;
      } else {
        entityTypeObj.selected = false;
      }
    }

    /*
    if (item) {
      this.toggleValidationIndOrg(item.group);
    }
    */
  }

  /**
   * Sched D Debt Payments (Sub-transactions) will be auto-populated with
   * fields from the main Sched D.
   *
   * @param schedDData
   */
  protected _prePopulateFromSchedD(schedDData: any) {
    let fieldArray = [];
    if (schedDData.hasOwnProperty('entity_type')) {
      const entityType = schedDData.entity_type;
      if (!entityType) {
        return;
      }
      if (typeof entityType !== 'string') {
        return;
      }

      let hiddenFieldEntityId = null;
      if (schedDData.hasOwnProperty('entity_id')) {
        hiddenFieldEntityId = schedDData.entity_id;
      }
      this.hiddenFields.push({
        'type': 'hidden',
        'name': 'entity_id',
        'value': schedDData.entity_id
      });

      this._prePopulateFormFieldHelper(schedDData, 'entity_type', fieldArray);
      if (entityType === 'ORG') {
        fieldArray = this._prePopulateFormFieldHelper(schedDData, 'entity_name', fieldArray);
      } else if (entityType === 'IND') {
        fieldArray = this._prePopulateFormFieldHelper(schedDData, 'last_name', fieldArray);
        fieldArray = this._prePopulateFormFieldHelper(schedDData, 'first_name', fieldArray);
        fieldArray = this._prePopulateFormFieldHelper(schedDData, 'middle_name', fieldArray);
        fieldArray = this._prePopulateFormFieldHelper(schedDData, 'prefix', fieldArray);
        fieldArray = this._prePopulateFormFieldHelper(schedDData, 'suffix', fieldArray);
      } else {
        // invalid type
      }
      fieldArray = this._prePopulateFormFieldHelper(schedDData, 'street_1', fieldArray);
      fieldArray = this._prePopulateFormFieldHelper(schedDData, 'street_2', fieldArray);
      fieldArray = this._prePopulateFormFieldHelper(schedDData, 'city', fieldArray);
      fieldArray = this._prePopulateFormFieldHelper(schedDData, 'state', fieldArray);
      fieldArray = this._prePopulateFormFieldHelper(schedDData, 'zip_code', fieldArray);

      if (this.entityTypes) {
        if (Array.isArray(this.entityTypes)) {
          for (const entityTypeObj of this.entityTypes) {
            if (entityTypeObj.entityType === entityType) {
              entityTypeObj.selected = true;
              this.selectedEntityType = entityTypeObj;
            } else {
              entityTypeObj.selected = false;
            }
          }
          this.handleEntityTypeChange(this.selectedEntityType);
        }
      }
    }
    this._prePopulateFormField(fieldArray);
  }

  /**
   * Sched L Account ID will be auto-populated for child transaction
   *
   * @param schedLData
   */
  protected _prePopulateFromSchedL(schedLData: any) {
    const fieldArray = [];
    if (schedLData.hasOwnProperty('levin_account_id')) {
      this._prePopulateFormFieldHelper(schedLData, 'levin_account_id', fieldArray);
    }
    this._prePopulateFormField(fieldArray);
  }

  protected _prePopulateFromSchedH(schedHData: any) {
    let fieldArray = [];
    if (schedHData.hasOwnProperty('activity_event_type')) {
      const activityEventType = schedHData.activity_event_type;
      if (!activityEventType) {
        return;
      }
      if (typeof activityEventType !== 'string') {
        return;
      }

      this._prePopulateFormFieldHelper(schedHData, 'activity_event_type', fieldArray);

      if (schedHData.hasOwnProperty('activity_event_identifier')) {
        const entityEventIdentifier = schedHData.activity_event_identifier;
        if(activityEventType === 'DF' || activityEventType === 'DC') {
          this.activityEventNames = entityEventIdentifier;
          this._prePopulateFormFieldHelper(schedHData, 'activity_event_identifier', fieldArray);
        }
      }
    }
    this.totalAmountReadOnly = false;
    this._prePopulateFormField(fieldArray);
  }

  protected _prePopulateFromSchedPARTN(schedPARTNData: any) {
    let fieldArray = [];
    if (schedPARTNData.hasOwnProperty('contribution_date')) {
      const contributionDate = schedPARTNData.contribution_date;
      if (!contributionDate) {
        return;
      }
      this._prePopulateFormFieldHelper(schedPARTNData, 'contribution_date', fieldArray);
    }
    this.totalAmountReadOnly = false;
    this._prePopulateFormField(fieldArray);
  }

  /**
   * Helper method for pre-populating an array to apply field values to the form.
   *
   * @param data
   * @param fieldName
   * @param fieldArray
   */
  private _prePopulateFormFieldHelper(data: any, fieldName: string, fieldArray: Array<any>) {
    if (!fieldArray || !fieldName || !data) {
      return;
    }
    if (!Array.isArray(fieldArray)) {
      fieldArray = [];
    }
    if (data.hasOwnProperty(fieldName)) {
      fieldArray.push({ name: fieldName, value: data[fieldName] });
    }
    return fieldArray;
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

  protected _prePopulateFormForEditOrView(transactionDetail: any) {
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

        this._isShowWarn = true;

        // set the flag for sched f core components to hide second page
        if (this.abstractScheduleComponent === AbstractScheduleParentEnum.schedFCoreComponent) {
          if (formData.transactionTypeIdentifier.startsWith('COEXP') && formData.transactionTypeIdentifier.endsWith('MEMO')) {
            this.showPart2 = true;
          }
          else{
            this.showPart2 = false;
          }
        }
        // this.transactionType = formData.transactionTypeIdentifier;
        this._setFormDataValues(formData.transactionId, formData.apiCall, formData.reportId);
      }
    }
  }

  /**
   * Set the values from the API in the form.
   *
   * @param transactionId
   */
  private _setFormDataValues(transactionId: string, apiCall: string, reportId: string) {
    if (!reportId) {
      reportId = this._receiptService.getReportIdFromStorage(this.formType);
    }
    this.subTransactions = [];
    this._receiptService.getDataSchedule(reportId, transactionId, apiCall).takeUntil(this.onDestroy$)
      .subscribe(res => {
        if (Array.isArray(res)) {
          for (const trx of res) {
            if (trx.hasOwnProperty('transaction_id')) {
              if (trx.transaction_id === transactionId) {
                if (trx.hasOwnProperty('child')) {
                  if (Array.isArray(trx.child)) {
                    if (trx.child.length > 0) {
                      this._parentTransactionModel = this._transactionsService.mapFromServerSchedFields([trx])[0];
                      this.subTransactions = trx.child;
                      if (this.subTransactionInfo) {
                        this.subTransactionsTableType = this.subTransactionInfo.scheduleType;
                      }
                      for (const subTrx of this.subTransactions) {
                        //console.log('sub tran id ' + subTrx.transaction_id);
                      }
                    }
                  }
                } else {
                  if (trx.hasOwnProperty('back_ref_transaction_id')) {
                    if (trx.back_ref_transaction_id) {
                      this._getParentFromChild(reportId, trx, apiCall);
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
                    if (this.frmIndividualReceipt) {
                      if (this.frmIndividualReceipt.get(prop)) {
                        if (this.frmIndividualReceipt.get(prop)) {
                          if (this.isFieldName(prop, 'contribution_aggregate')) {
                            this._contributionAggregateValue = trx[prop];
                          } else if (this.isFieldName(prop, 'aggregate_general_elec_exp')) {
                            this._contributionAggregateValue = trx[prop];
                          }
                          if (this.isFieldName(prop, 'activity_event_type')) {
                            if (trx[prop] !== null || trx[prop] !== 'Select') {
                              this.totalAmountReadOnly = false;
                              if (this.activityEventTypes) {
                                for (const activityEvent of this.activityEventTypes) {
                                  if (trx[prop] === activityEvent.eventType) {
                                    if (activityEvent.scheduleType === 'sched_h2' && activityEvent.hasValue === true) {
                                      this.activityEventNames = activityEvent.activityEventTypes;
                                    }
                                  }
                                }
                              }
                            }
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
                          if (this.isFieldName(prop, 'election_code')) {
                            if (trx.election_code !== 'O') {
                              trx[prop] = this.getElectionTypeCode(trx.election_other_description);
                            }
                          }
                          if(this.isFieldName(prop,'memo_text')){
                            if(this.redesignationTransactionId){
                              trx[prop] = 'MEMO: Redesignated';
                            }
                          }
                          const patch = {};
                          patch[prop] = trx[prop];
                          this.frmIndividualReceipt.patchValue(patch, { onlySelf: true });
                        }
                      }
                    }
                    if (prop === 'entity_id') {
                      this._selectedEntity = {};
                      this._selectedEntity.entity_id = trx[prop];
                      this._selectedEntity.entity_name = null;
                      this._selectedEntity.first_name = null;
                      this._selectedEntity.last_name = null;
                      this._selectedEntity.middle_name = null;
                      // TODO: Should be removed later FNE-1974
                      this._selectedEntity.preffix = null;
                      // this._selectedEntity.prefix = null;
                      this._selectedEntity.suffix = null;
                      if (this._selectedEntity.entity_id) {
                        if (typeof this._selectedEntity.entity_id === 'string') {
                          if (this._selectedEntity.entity_id.startsWith('IND')) {
                            this._selectedEntity.entity_type = 'IND';
                            this._selectedEntity.first_name = trx.first_name;
                            this._selectedEntity.last_name = trx.last_name;
                            this._selectedEntity.middle_name = trx.middle_name;
                            // TODO: Should be removed later FNE-1974
                            this._selectedEntity.preffix = trx.preffix;
                            // this._selectedEntity.prefix = trx.preffix;
                            this._selectedEntity.suffix = trx.suffix;
                          } else if (this._selectedEntity.entity_id.startsWith('ORG')) {
                            this._selectedEntity.entity_type = 'ORG';
                            this._selectedEntity.entity_name = trx.entity_name;
                          }
                        }
                      }
                      this._selectedEntity.city = trx.city;
                      this._selectedEntity.employer = trx.employer;
                      this._selectedEntity.occupation = trx.occupation;
                      this._selectedEntity.street_1 = trx.street_1;
                      this._selectedEntity.street_2 = trx.street_2;
                      this._selectedEntity.state = trx.state;
                      this._selectedEntity.zip_code = trx.zip_code;
                    }
                    if (prop === 'beneficiary_cand_entity_id') {
                      this._selectedCandidate = {};
                      this._selectedCandidate.entity_id = trx[prop];
                      this._selectedCandidate.cand_first_name = trx.cand_first_name;
                      this._selectedCandidate.cand_last_name = trx.cand_last_name;
                      this._selectedCandidate.cand_middle_name = trx.cand_middle_name;
                      this._selectedCandidate.cand_office = trx.cand_office;
                      this._selectedCandidate.cand_office_district = trx.cand_office_district;
                      this._selectedCandidate.cand_office_state = trx.cand_office_state;
                      this._selectedCandidate.cand_prefix = trx.cand_prefix;
                      this._selectedCandidate.cand_suffix = trx.cand_suffix;
                      this._selectedCandidate.city = null;
                      this._selectedCandidate.entity_type = 'CAN';
                      this._selectedCandidate.payee_cmte_id = trx.payee_cmte_id;
                      this._selectedCandidate.ref_cand_cmte_id = null;
                      this._selectedCandidate.state = null;
                      this._selectedCandidate.street_1 = null;
                      this._selectedCandidate.street_2 = null;
                      this._selectedCandidate.zip_code = null;
                      this._selectedCandidate.beneficiary_cand_id = trx.beneficiary_cand_id;
                    }
                    if (prop === 'entity_type') {
                      if (this.entityTypes) {
                        for (const field of this.entityTypes) {
                          field.selected = false;
                          if (trx[prop] === field.entityType) {
                            field.selected = true;
                            this.selectedEntityType = field;
                            this.frmIndividualReceipt.patchValue(
                              { entity_type: this.selectedEntityType.entityType },
                              { onlySelf: true }
                            );
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
                    // TODO add for _selectedCandidate
                  }
                  // set forced aggregation indicator
                  if (prop === 'aggregation_ind' ) {
                    if (trx[prop] == null || trx[prop] === 'Y') {
                      this.isAggregate = true;
                    } else {
                      this.isAggregate = false;
                    }
                  }
                }
                // loop through props again now that aggregate should be set
                // and apply contributionAmountChange() formatting, setting, etc.
                for (const prop in trx) {
                  if (trx.hasOwnProperty(prop)) {
                    if (this.isFieldName(prop, 'contribution_amount') || this.isFieldName(prop, 'expenditure_amount')) {
                      const amount = trx[prop] ? trx[prop] : 0;
                      this.contributionAmountChange({ target: { value: amount.toString() } }, prop, false);
                    } else if (
                      this.isFieldName(prop, 'total_amount') ||
                      this.isFieldName(prop, 'beginning_balance') ||
                      this.isFieldName(prop, 'incurred_amount') ||
                      this.isFieldName(prop, 'payment_amount') ||
                      this.isFieldName(prop, 'balance_at_close') ||
                      this.isFieldName(prop, 'fed_share_amount') ||
                      this.isFieldName(prop, 'non_fed_share_amount') ||
                      this.isFieldName(prop, 'activity_event_amount_ytd') ||
                      this.isFieldName(prop, 'aggregate_general_elec_exp')
                    ) {
                      const amount = trx[prop] ? trx[prop] : 0;
                      if (this.frmIndividualReceipt && this.frmIndividualReceipt.controls['total_amount'] && this.scheduleAction === 'edit' && this._cloned) {
                        this.frmIndividualReceipt.patchValue({ total_amount: null }, { onlySelf: true });
                      } else {
                        this._formatAmount({ target: { value: amount.toString() } }, prop, false);
                      }
                    }
                  }
                }
                this._validateTransactionDate();
                this._calculateDebtAmountFields(trx);
              }
            }
            //once data is set, send a message to any child components that may want to set additional specific fields
            this._messageService.sendPopulateChildComponentMessage({ populateChildForEdit: true, transactionData: trx, component: this.abstractScheduleComponent });

            if (this.redesignationTransactionId) {
              this._f3xMessageService.sendClearFormValuesForRedesignationMessage({ abstractScheduleComponent: AbstractScheduleParentEnum.schedMainComponent });
            }
            
          }


          // move the payment button into view if flag is set.
          if (this._transactionToEdit && this._transactionToEdit.scrollDebtPaymentButtonIntoView) {
            let button = document.getElementById('jfMemoDropdown');
            if (button === null) {
              button = document.getElementById('addSingleChildButton');
            }
            if (button !== null) {
              button.scrollIntoView();
            }
          }
        }
      });
  }

  private _calculateDebtAmountFields(trx: any) {
    if (trx.transaction_type_identifier !== 'DEBT_TO_VENDOR' && trx.transaction_type_identifier !== 'DEBT_BY_VENDOR') {
      return;
    }

    // TODO this should come from the API
    let paymentAmount = 0.0;
    for (const subTrx of this.subTransactions) {
      if (subTrx.hasOwnProperty('expenditure_amount')) {
        if (subTrx.expenditure_amount) {
          paymentAmount = paymentAmount + subTrx.expenditure_amount;
        }
      } else if (subTrx.hasOwnProperty('contribution_amount')) {
        if (subTrx.contribution_amount) {
          paymentAmount = paymentAmount + subTrx.contribution_amount;
        }
      } else if (subTrx.hasOwnProperty('total_amount')) {
        if (subTrx.total_amount) {
          paymentAmount = paymentAmount + subTrx.total_amount;
        }
      } else if (subTrx.hasOwnProperty('total_fed_levin_amount')) {
        if (subTrx.total_fed_levin_amount) {
          paymentAmount = paymentAmount + subTrx.total_fed_levin_amount;
        }
      }
    }
    this._formatAmount({ target: { value: paymentAmount.toString() } }, 'payment_amount', false);

    // Beginning balance + Incurred amount - Payment Amount = Balance at close
    let incurredAmount = 0;
    if (trx.hasOwnProperty('incurred_amount')) {
      if (trx.incurred_amount) {
        incurredAmount = trx.incurred_amount;
      }
    }
    const balanceAtClose = trx.beginning_balance + incurredAmount - paymentAmount;
    this._formatAmount({ target: { value: balanceAtClose.toString() } }, 'balance_at_close', false);
  }

  /**
   * When a child transaction is selected for editing from the main table as opposed to editing
   * from the parent sub-transaction table, the parent information needs to be obtained from the
   * API.  It is need for returning to the parent from the child.
   * @param reportId
   * @param childTrx
   * @param apiCall
   */
  private _getParentFromChild(reportId: string, childTrx: any, apiCall: string) {
    // There is a bug the apiCall value is incorrect when where a parent-child have different schedules
    // as with Sched_D.  Temporary path is to hard code the apiCall based on the trnasactionID 1st to chars.
    // TODO add back_ref_api_call to child transaction in the getSched API and pass it here.

    const backRefTransactionId = childTrx.back_ref_transaction_id;
    if (backRefTransactionId.startsWith('SD')) {
      apiCall = '/sd/schedD';
    }

    this._receiptService.getDataSchedule(reportId, backRefTransactionId, apiCall).subscribe(res => {
      if (Array.isArray(res)) {
        for (const parentTrx of res) {
          if (parentTrx.hasOwnProperty('transaction_id')) {
            if (parentTrx.transaction_id === backRefTransactionId) {
              const modelArray = this._transactionsService.mapFromServerSchedFields([parentTrx]);
              if (modelArray) {
                if (modelArray.length > 0) {
                  this._parentTransactionModel = modelArray[0];
                  this._setDebtPaymentValidations(parentTrx, childTrx);
                }
              }
            }
          }
        }
      }
    });
  }

  /**
   * On an edit, now that the incurred amount from the parent is obtained, set the validation
   * for exceeding max debt payment when editing a payment.
   * @param parentTrx debt/parent transaction to the payment
   * @param childTrx payment/child transaction on the Debt
   */
  private _setDebtPaymentValidations(parentTrx: any, childTrx: any) {

    // Payment transactions have different payment field names.
    // OPEXP has expenditure_amount
    // ALLOC_EXP_DEBT has total_amount
    // ALLOC_FEA_DISB_DEBT has total_amount
    // OTH_DISB_DEBT has expenditure_amount
    // FEA_100PCT_DEBT_PAY has expenditure_amount
    // COEXP_PARTY_DEBT has expenditure_amount
    // IE_B4_DISSE_MEMO not yet developed

    let amountField: string;
    if (this.frmIndividualReceipt.get('expenditure_amount')) {
      amountField = 'expenditure_amount';
    } else if (this.frmIndividualReceipt.get('total_amount')) {
      amountField = 'total_amount';
    }

    if (this.frmIndividualReceipt.get(amountField)) {
      if (parentTrx.hasOwnProperty('incurred_amount') &&
        parentTrx.hasOwnProperty('payment_amount')) {
        const incurredAmount = parentTrx.incurred_amount ? parentTrx.incurred_amount : 0;
        const paymentAmount = parentTrx.payment_amount ? parentTrx.payment_amount : 0;
        // Because this is edit on a payment, back out the current payment amount
        // from the sum of payment before calculating the balance.
        this._outstandingDebtBalance = incurredAmount - (paymentAmount - childTrx[amountField]);
        const expAmtformField: any = this.findFormField(amountField);
        const validations: Array<any> = this._mapValidators(expAmtformField.validation,
          expAmtformField.name, expAmtformField.value);

        this.frmIndividualReceipt.controls[amountField].setValidators(validations);
        this.frmIndividualReceipt.controls[amountField].updateValueAndValidity();
      }
    }
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
   * Determine if the field should be shown.
   */
  public isToggleShow(col: any) {
    if (col.name === 'activity_event_identifier') {
      if (this.activityEventNames) {
        return true;
      } else {
        return false;
      }
    } else {
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
  }

  public showHideEntityType(entityTypeGroup: string) { }

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

  public clearFormValues(clearTransactionToEdit: boolean = true): void {
    
    if(clearTransactionToEdit){
      this._transactionToEdit = null;
    }

    this._selectedEntity = null;
    this._selectedEntityChild = null;
    this._selectedChangeWarn = {};
    this._selectedChangeWarnChild = {};

    this._selectedCandidate = null;
    this._selectedCandidateChangeWarn = null;
    this._selectedCandidateChild = null;
    this._selectedCandidateChangeWarnChild = null;

    this._isShowWarn = true;

    this._contributionAggregateValue = 0.0;
    this._contributionAggregateValueChild = 0.0;
    this.reattributionTransactionId = null;
    this.redesignationTransactionId = null;
    // this._outstandingDebtBalance = null;
    this.memoCode = false;
    this.memoCodeChild = false;
    this._readOnlyMemoCode = false;
    this._readOnlyMemoCodeChild = false;
    if (this.frmIndividualReceipt) {
      this.frmIndividualReceipt.reset();
      this._prepopulateDefaultPurposeText();
    }
    if (this.frmIndividualReceipt && this.frmIndividualReceipt.contains('entity_type')) {
      this.selectedEntityType = this._entityTypeDefault;
      if(this.selectedEntityType){
        this.frmIndividualReceipt.patchValue({ entity_type: this.selectedEntityType.entityType }, { onlySelf: true });
      }
    }
    this.memoDropdownSize = null;
    this.activityEventNames = null;

    this.showPart2 = false;
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
    // Purpose description is pre-populatng for Individual Receipt
    // Added below condition on 01/10/2020.
    if (!this.subTransactionInfo) {
      return;
    }
    if (
      !this.subTransactionInfo.isEarmark &&
      !this.subTransactionInfo.isParent &&
      // this.transactionType !== 'EAR_REC' &&
      // this.transactionType !== 'CON_EAR_UNDEP' &&
      // this.transactionType !== 'CON_EAR_DEP_1'
      this.transactionType !== 'ALLOC_EXP' &&
      this.transactionType !== 'ALLOC_EXP_CC_PAY' &&
      this.transactionType !== 'ALLOC_EXP_CC_PAY_MEMO' &&
      this.transactionType !== 'ALLOC_EXP_STAF_REIM' &&
      this.transactionType !== 'ALLOC_EXP_STAF_REIM_MEMO' &&
      this.transactionType !== 'ALLOC_EXP_PMT_TO_PROL' &&
      this.transactionType !== 'ALLOC_EXP_PMT_TO_PROL_MEMO' &&
      this.transactionType !== 'ALLOC_EXP_VOID' &&
      this.transactionType !== 'ALLOC_FEA_DISB' &&
      this.transactionType !== 'ALLOC_FEA_CC_PAY' &&
      this.transactionType !== 'ALLOC_FEA_CC_PAY_MEMO' &&
      this.transactionType !== 'ALLOC_FEA_STAF_REIM' &&
      this.transactionType !== 'ALLOC_FEA_STAF_REIM_MEMO' &&
      this.transactionType !== 'ALLOC_FEA_VOID'
    ) {
      return;
    }
    const isChildField = fieldName.startsWith(this._childFieldNamePrefix) ? true : false;
    if (isChildField) {
      if (!this.frmIndividualReceipt.get('child*purpose_description')) {
        return;
      }
    } else {
      if (!this.frmIndividualReceipt.get('purpose_description')) {
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

      //const purposePre = 'Earmarked for';
      const purposePre = '';
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

      //console.log('purpose is: ' + purpose);
      if (purpose !== purposePre) {
        this.frmIndividualReceipt.patchValue({ 'child*purpose_description': purpose }, { onlySelf: true });
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

      //const purposePre = 'Earmarked for';
      const purposePre = '';
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

      //console.log('purpose is: ' + purpose);
      if (purpose !== purposePre && !this.subTransactionInfo.isParent) {
        this.frmIndividualReceipt.patchValue({ purpose_description: purpose }, { onlySelf: true });
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
          this.isAggregate,
          this._selectedEntity,
          this._transactionToEdit,
          this.transactionType,
          transactionDate
        );

        this.frmIndividualReceipt.patchValue({ contribution_aggregate: aggregateValue }, { onlySelf: true });
      });
  }

  /**
   * Get the aggregate for Schedule F Debt Payment.  It is similar to _getContributionAggregate().
   * @param candidateId the Candidate ID
   * @param expenditureDate the date of the expenditure from the form
   * @param candidateEntityId the Entity ID for the Candidate
   * @param expenditureAmount the expenditure amount from the form
   */
  private _getSchedFDebtPaymentAggregate(
    candidateId: number,
    expenditureDate: string,
    candidateEntityId: string,
    expenditureAmount?: string
  ) {
    if (!candidateId || !expenditureDate) {
      return;
    }

    this._receiptService.getSchedFPaymentAggregate(candidateId, expenditureDate).subscribe(res => {
      const contributionAmountNum = this._convertFormattedAmountToDecimal(null);

      let contributionAggregate: string = String(res.aggregate_general_elec_exp);
      contributionAggregate = contributionAggregate ? contributionAggregate : '0';
      this._contributionAggregateValue = parseFloat(contributionAggregate);

      let transactionDate = null;
      if (this.frmIndividualReceipt.get('expenditure_date')) {
        transactionDate = this.frmIndividualReceipt.get('expenditure_date').value;
      }

      // Sched F Payment uses Candidate Entity ID for aggregate calc.
      // Pass it in the Entity ID of the Transaction Model.
      // Clone used to not adversely impact processing on this._transactionToEdit
      let transactionToEditClone = null;
      if (this._transactionToEdit && this.scheduleAction === ScheduleActions.edit) {
        transactionToEditClone = this._utilService.deepClone(this._transactionToEdit);
        transactionToEditClone.entityId = candidateEntityId;
      }

      const aggregateValue: string = this._receiptService.determineAggregate(
        this._contributionAggregateValue,
        contributionAmountNum,
        this.scheduleAction,
        this.isAggregate,
        this._selectedCandidate,
        transactionToEditClone,
        this.transactionType,
        transactionDate
      );

      this.frmIndividualReceipt.patchValue({ aggregate_general_elec_exp: aggregateValue }, { onlySelf: true });
    });
  }

  /**
   * Office types may be hard coded as they are never expected to Change for now.
   */
  private _getCandidateOfficeTypes() {
    this._contactsService.getContactsDynamicFormFields().subscribe(res => {
      if (res) {
        //console.log('getFormFields res =', res);
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

  // private _checkForSchedDPrePopulate(): Array<any> {
  //   const prePopulateFieldArray = null;
  //   if (this.frmIndividualReceipt.contains('entity_type')) {
  //     const entityType = this.frmIndividualReceipt.get('entity_type').value;
  //     if (entityType === 'ORG') {
  //       prePopulateFieldArray.push({ name: 'entity_type', value: entityType });
  //       if (this.frmIndividualReceipt.contains('entity_name')) {
  //         const val = this.frmIndividualReceipt.get('entity_name').value;
  //         prePopulateFieldArray.push({ name: 'entity_name', value: val });
  //       }
  //     } else if (entityType === 'IND') {

  //     } else {
  //       // invalid type
  //     }
  //   }

  //   return prePopulateFieldArray;
  // }

  /**
   * Populate the purpose description for child with parent entity.
   */
  private _checkForPurposePrePopulate(res: any): Array<any> {
    let prePopulateFieldArray = null;
    if (this.subTransactionInfo) {
      // TODO the parent of memo child transaction could have a property added to subTransactionInfo
      // to indicate it is a memo, similar to isEarMark.  For now using transaction_type
      // until API is provide transfer memo indicator.
      if ((this.subTransactionInfo.isEarmark && this.subTransactionInfo.isParent) ||
        (res.transaction_type_identifier === 'JF_TRAN' ||
          res.transaction_type_identifier === 'JF_TRAN_NP_RECNT_ACC' ||
          res.transaction_type_identifier === 'JF_TRAN_NP_CONVEN_ACC' ||
          res.transaction_type_identifier === 'JF_TRAN_NP_HQ_ACC')) {
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
        if (res.transaction_type_identifier !== 'JF_TRAN' &&
          res.transaction_type_identifier !== 'JF_TRAN_NP_RECNT_ACC' &&
          res.transaction_type_identifier !== 'JF_TRAN_NP_CONVEN_ACC' &&
          res.transaction_type_identifier !== 'JF_TRAN_NP_HQ_ACC') {
          if (res.hasOwnProperty('contribution_amount')) {
            const amountValue: string = this._decimalPipe.transform(parseFloat(res.contribution_amount), '.2-2');
            prePopulateFieldArray.push({ name: 'contribution_amount', value: amountValue });
            prePopulateFieldArray.push({ name: 'expenditure_amount', value: amountValue });
          } else if (res.hasOwnProperty('expenditure_amount')) {
            const amountValue: string = this._decimalPipe.transform(parseFloat(res.expenditure_amount), '.2-2');
            prePopulateFieldArray.push({ name: 'contribution_amount', value: amountValue });
            prePopulateFieldArray.push({ name: 'expenditure_amount', value: amountValue });
          }
        }

        if (this.subTransactionInfo.subTransactionType === 'EAR_MEMO' ||
          this.subTransactionInfo.subTransactionType === 'EAR_REC_RECNT_ACC_MEMO' ||
          this.subTransactionInfo.subTransactionType === 'EAR_REC_CONVEN_ACC_MEMO' ||
          this.subTransactionInfo.subTransactionType === 'EAR_REC_HQ_ACC_MEMO' ||
          this.subTransactionInfo.subTransactionType === 'PAC_EAR_MEMO') {
          prePopulateFieldArray.push({ name: 'purpose_description', value: 'Total earmarked through conduit.' });
        } else {
          prePopulateFieldArray.push({ name: 'purpose_description', value: earmarkMemoPurpose });
        }

        prePopulateFieldArray.push({ name: 'expenditure_purpose', value: earmarkMemoPurpose });
      } /* else if (this.subTransactionInfo.subTransactionType === 'LEVIN_PARTN_MEMO') {
          if (res.hasOwnProperty('levin_account_id')) {
            prePopulateFieldArray.push({ name: 'levin_account_id', value: res.levin_account_id });
          }
      }*/
      else if (this.subTransactionInfo.subTransactionType === 'PARTN_MEMO') {
        prePopulateFieldArray = [];
        if (res.hasOwnProperty('contribution_date')) {
          prePopulateFieldArray.push({ name: 'contribution_date', value: res.contribution_date });
        }
      }
    }
    return prePopulateFieldArray;
  }

  /**
   * Find a Form Field object by name.
   */
  public findFormField(name: string): any {
    if (!name || !this.formFields) {
      return null;
    }
    const fields = this.formFields;
    for (const el of fields) {
      if (el.hasOwnProperty('cols') && el.cols) {
        for (const e of el.cols) {
          if (e.name === name) {
            return e;
          }
        }
      }
    }
    return null;
  }

  public findFormFieldContaining(name: string): any {
    if (!name || !this.formFields) {
      return null;
    }
    const fields = this.formFields;
    for (const el of fields) {
      if (el.hasOwnProperty('cols') && el.cols) {
        for (const e of el.cols) {
          if (e.name.includes(name)) {
            return e;
          }
        }
      }
    }
    return null;
  }

  public isShedH4OrH6TransactionType(transactionType: string): boolean {
    if (
      transactionType === 'ALLOC_EXP' ||
      transactionType === 'ALLOC_EXP_CC_PAY' ||
      //transactionType === 'ALLOC_EXP_CC_PAY_MEMO' ||
      transactionType === 'ALLOC_EXP_STAF_REIM' ||
      //transactionType === 'ALLOC_EXP_STAF_REIM_MEMO' ||
      transactionType === 'ALLOC_EXP_PMT_TO_PROL' ||
      //transactionType === 'ALLOC_EXP_PMT_TO_PROL_MEMO' ||
      transactionType === 'ALLOC_EXP_VOID' ||
      transactionType === 'ALLOC_FEA_DISB' ||
      transactionType === 'ALLOC_FEA_CC_PAY' ||
      //transactionType === 'ALLOC_FEA_CC_PAY_MEMO' ||
      transactionType === 'ALLOC_FEA_STAF_REIM' ||
      //transactionType === 'ALLOC_FEA_STAF_REIM_MEMO' ||
      transactionType === 'ALLOC_FEA_VOID'
    ) {
      return true;
    } else {
      return false;
    }
  }

  private _checkForReturnToDebtSummary(message: any) {
    this.returnToDebtSummary = false;
    if (message.returnToDebtSummary) {
      this.returnToDebtSummary = true;
      this.returnToDebtSummaryInfo = message.returnToDebtSummaryInfo;
    }
  }

  /**
   * If originated from Debt Summary, return there otherwise go to the transactions.
   */
  public cancel(): void {

    this.canDeactivate().then(result => {
      if (result === true) {
        localStorage.removeItem(`form_${this.formType}_saved`);
        if (
          this.returnToDebtSummary &&
          (this.transactionType === 'DEBT_TO_VENDOR' || this.transactionType === 'DEBT_BY_VENDOR')
        ) {
          this._goDebtSummary();
        } else if (
          this.returnToDebtSummary &&
          (this.transactionType === 'OPEXP_DEBT' ||
            this.transactionType === 'ALLOC_EXP_DEBT' ||
            this.transactionType === 'ALLOC_FEA_DISB_DEBT' ||
            this.transactionType === 'OTH_DISB_DEBT' ||
            this.transactionType === 'FEA_100PCT_DEBT_PAY' ||
            this.transactionType === 'COEXP_PARTY_DEBT' ||
            this.transactionType === 'IE_B4_DISSE' ||
            this.transactionType === 'OTH_REC_DEBT'
          )
        ) {
          this.returnToParent(this.editScheduleAction);
        } else {
          //this.viewTransactions();
          if(!this.priviousTransactionType) {
            this.viewTransactions();
          }else {
            if(this.currentTransactionType.endsWith('MEMO')) {
              this.returnToParent(this.editScheduleAction);
            }else {
              this.viewTransactions();
            }
          }
        }
      }
    });
  }

  private _goDebtSummary(): void {
    const emitObj: any = {
      form: this.frmIndividualReceipt,
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      action: ScheduleActions.add,
      transactionType: this.returnToDebtSummaryInfo.transactionType,
      transactionTypeText: this.returnToDebtSummaryInfo.transactionTypeText,
      scheduleType: 'sched_d_ds'
    };
    this.status.emit(emitObj);
  }

  public goH4OrH6Summary(transactionType: string) {
    if(!this.priviousTransactionType || this.priviousTransactionType.endsWith('MEMO')) {
      this.viewTransactions();
    }else {
      if (
        transactionType === 'ALLOC_EXP' ||
        transactionType === 'ALLOC_EXP_CC_PAY' ||
        transactionType === 'ALLOC_EXP_CC_PAY_MEMO' ||
        transactionType === 'ALLOC_EXP_STAF_REIM' ||
        transactionType === 'ALLOC_EXP_STAF_REIM_MEMO' ||
        transactionType === 'ALLOC_EXP_PMT_TO_PROL' ||
        transactionType === 'ALLOC_EXP_PMT_TO_PROL_MEMO' ||
        transactionType === 'ALLOC_EXP_VOID'
      ) {
        const emitObj: any = {
          form: this.frmIndividualReceipt,
          direction: 'next',
          step: 'step_3',
          previousStep: 'step_2',
          transactionType: 'ALLOC_H4_SUM',
          action: ScheduleActions.add,
          transactionTypeText: 'H4 Transaction List'
        };
        this.status.emit(emitObj);
      }

      if (
        transactionType === 'ALLOC_FEA_DISB' ||
        transactionType === 'ALLOC_FEA_CC_PAY' ||
        transactionType === 'ALLOC_FEA_CC_PAY_MEMO' ||
        transactionType === 'ALLOC_FEA_STAF_REIM' ||
        transactionType === 'ALLOC_FEA_STAF_REIM_MEMO' ||
        transactionType === 'ALLOC_FEA_VOID'
      ) {
        const emitObj: any = {
          form: this.frmIndividualReceipt,
          direction: 'next',
          step: 'step_3',
          previousStep: 'step_2',
          transactionType: 'ALLOC_H6_SUM',
          action: ScheduleActions.add,
          transactionTypeText: 'H6 Transaction List'
        };
        this.status.emit(emitObj);
      }
    }
  }

  public saveForReturnToSummary(): void {
    if (this.frmIndividualReceipt.pristine) {
      this.goH4OrH6Summary(this.transactionType);
    } else {
      if ((this.frmIndividualReceipt.touched || this.frmIndividualReceipt.dirty) && this.frmIndividualReceipt.invalid) {
        this._dialogService
          .confirm(
            'You have unsaved changes! If you leave, your changes will be lost.',
            ConfirmModalComponent,
            'Caution!'
          )
          .then(res => {
            if (res === 'okay') {
              this.goH4OrH6Summary(this.transactionType);
            } else if (res === 'cancel') {
            }
          });
      } else if (this.frmIndividualReceipt.valid) {
        this._doValidateReceipt(SaveActions.saveForReturnToSummary);
      }
    }
  }
  protected convertAmountToNumber(amount: string) {
    if (amount) {
      return Number(this.abstractRemoveCommas(amount));
    }
    return 0;
  }

  protected abstractRemoveCommas(amount: string): string {
    return amount.toString().replace(new RegExp(',', 'g'), '');
  }


  private clearOrgData() {
    // These field names map to the same name in the form
    const fieldNames = [];
    fieldNames.push('street_1');
    fieldNames.push('street_2');
    fieldNames.push('city');
    fieldNames.push('state');
    fieldNames.push('zip_code');

    for (const orgField of fieldNames) {
      const orgPv = {};
      orgPv[orgField] = null;
      this.frmIndividualReceipt.patchValue(orgPv, { onlySelf: true });
    }

  }

  protected getFormValidationErrors() {
    Object.keys(this.frmIndividualReceipt.controls).forEach(key => {
      const controlErrors: ValidationErrors = this.frmIndividualReceipt.get(key).errors;
      if (controlErrors != null) {
        Object.keys(controlErrors).forEach(keyError => {
          console.error('Key control: ' + key + ', keyError: ' + keyError + ', err value: ', controlErrors[keyError]);
        });
      }
    });
  }

  protected clearFormValuesForRedesignation() {
    if (this.frmIndividualReceipt) {
      if(this.scheduleAction === ScheduleActions.add){
        if (this.frmIndividualReceipt.controls['expenditure_date']) {
          this.frmIndividualReceipt.controls['expenditure_date'].reset();
        }
        if (this.frmIndividualReceipt.controls['expenditure_amount']) {
          this.frmIndividualReceipt.controls['expenditure_amount'].reset();
        }
        if (this.frmIndividualReceipt.controls['election_code']) {
          this.frmIndividualReceipt.controls['election_code'].reset();
        }
        if (this.frmIndividualReceipt.controls['election_year']) {
          this.frmIndividualReceipt.controls['election_year'].reset();
        }
        if (this.frmIndividualReceipt.controls['election_other_description']) {
          this.frmIndividualReceipt.controls['election_other_description'].reset();
        }

        if(this._transactionToEdit){
          this._transactionToEdit.transactionId = null;
        }

      }
      if (this.frmIndividualReceipt.controls['expenditure_amount']) {
        this.frmIndividualReceipt.controls['expenditure_amount'].setValidators([Validators.required,floatingPoint(),validateAmount(),validateContributionAmount(Number(this._maxReattributableOrRedesignatableAmount))]);
        this.frmIndividualReceipt.controls['expenditure_amount'].updateValueAndValidity();
      }
    }
    
  }

  private isShowChildRequiredWarn() {
    const transactionId = this._findHiddenField('name', 'transaction_id');
    if (transactionId && transactionId.length > 0) {
      return false;
    }

    if (this._findHiddenField('name', 'show_memo_warning') &&
      this._findHiddenField('name', 'show_memo_warning').value) {
      return true;
    }
    return false;
  }

  private populateSchedFChildData(field: string, receiptObj: any) {
      // Possible issue : Populating data from parent when  sched f child is created can cause in consistencies
      // data from child and parent can be out of sync when the parent is edited
      // backend should take care of the updates if parent is modified
    if (null == this.subTransactionInfo) {
      return;
    }
    if (this.abstractScheduleComponent === AbstractScheduleParentEnum.schedFCoreComponent && !this.subTransactionInfo.isParent) {
      switch (field) {
        case 'coordinated_exp_ind' :
          receiptObj[field] = this._parentTransactionModel.coordinatedExpInd;
          break;
        case 'designating_cmte_id':
          receiptObj[field] = this._parentTransactionModel.designatingCmteId;
          break;
        case 'designating_cmte_name':
          receiptObj[field] = this._parentTransactionModel.designatingCmteName;
          break;
        case 'subordinate_cmte_id':
          receiptObj[field] = this._parentTransactionModel.subordinateCmteId;
          break;
        case 'subordinate_cmte_name':
          receiptObj[field] = this._parentTransactionModel.subordinateCmteName;
          break;
        case 'subordinate_cmte_street_1':
          receiptObj[field] = this._parentTransactionModel.subordinateCmteStreet_1;
          break;
        case 'subordinate_cmte_street_2':
          receiptObj[field] = this._parentTransactionModel.subordinateCmteStreet_2;
          break;
        case 'subordinate_cmte_city':
          receiptObj[field] = this._parentTransactionModel.subordinateCmteCity;
          break;
        case 'subordinate_cmte_state':
          receiptObj[field] = this._parentTransactionModel.subordinateCmteState;
          break;
        case 'subordinate_cmte_zip':
          receiptObj[field] = this._parentTransactionModel.subordinateCmteZip;
          break;
        default:
      }
    }
  }
  
  protected removeAllValidators() {
    if(this.frmIndividualReceipt && this.frmIndividualReceipt.controls){
      for (const key in this.frmIndividualReceipt.controls) {
        this.frmIndividualReceipt.get(key).clearValidators();
        this.frmIndividualReceipt.get(key).updateValueAndValidity();
      }
    }
  }

  protected sendPopulateMessageIfApplicable(){
    if((this.scheduleAction === ScheduleActions.edit || this.scheduleAction === ScheduleActions.view) && this.transactionData){
      //check schedules 
      if(this.scheduleType.startsWith('sched_h')){
        this._schedHMessageServce.sendpopulateHFormForEditMessage(this.transactionData);
      }
      this._f3xMessageService.sendPopulateFormMessage(this.transactionData);
    }
    if(this.transactionDataForChild){
      this._f3xMessageService.sendPopulateFormMessage(this.transactionDataForChild);
      let { schedDSubTran, schedLSubTran, schedHSubTran } = this.determineSubTransactionType();
      if(schedDSubTran){
        this.populateDataForSchedDSubTransaction(true);
        this.updateDebtPaymentAmountFieldValidator();
      }
      else if(schedHSubTran){
        this.populateDataForSchedHSubTransaction(true);
        this.updateDebtPaymentAmountFieldValidator();
      }
      else if(schedLSubTran){
        this.populateDataForSchedLSubTransaction(true);
        this.updateDebtPaymentAmountFieldValidator();
      }
    }
    if(this.populateHiddenFieldsMessageObj){
      this._f3xMessageService.sendPopulateHiddenFieldsMessage(this.populateHiddenFieldsMessageObj);
    }
    if(this.populateFieldsMessageObj){
      this.removePurposeFromObjIfNotApplicableForPrepopulation()
      this._f3xMessageService.sendPopulateFieldsMessage(this.populateFieldsMessageObj);
    }
  }
  
  removePurposeFromObjIfNotApplicableForPrepopulation() {
    const purposeDescriptionFormField = this.findFormField('purpose_description');
    if (!purposeDescriptionFormField.isReadonly && this.populateFieldsMessageObj && this.populateFieldsMessageObj.fieldArray){
      this.populateFieldsMessageObj.fieldArray = this.populateFieldsMessageObj.fieldArray.filter(item => item.name !== 'purpose_description');
    }
  }
  
  updateDebtPaymentAmountFieldValidator() {
    if (this.frmIndividualReceipt && this.frmIndividualReceipt.controls['expenditure_amount']){
      this.frmIndividualReceipt.controls['expenditure_amount'].setValidators([floatingPoint,Validators.required, validateContributionAmount(this._outstandingDebtBalance)]);
      this.frmIndividualReceipt.controls['expenditure_amount'].updateValueAndValidity();
    }
  }

  public toggleAggregation(): void {

    let dateField: string;
    // checking for expenditure_date in form parameter
    // If expenditure_date is not found setting contribution_date and contribution_amount
    if (this.frmIndividualReceipt.controls['expenditure_date']) {
      dateField = 'expenditure_date';
    } else {
      dateField = 'contribution_date';
    }
    // schedule H4/H6
    if (this.frmIndividualReceipt.controls['incurred_amount'] || this.frmIndividualReceipt.controls['total_amount']) {
      this.isAggregate = !this.isAggregate;
      this.forceAggregateSchedH();
      return;
    }
    const contributionAmountNum = this._convertFormattedAmountToDecimal(null);
    let transactionDate = null;
    if (this.frmIndividualReceipt.get(dateField)) {
      transactionDate = this.frmIndividualReceipt.get(dateField).value;
    }

    // toggle isAggregate
    this.isAggregate = !this.isAggregate;

    const aggregateValue: string = this._receiptService.determineAggregate(
        this._contributionAggregateValue,
        contributionAmountNum,
        this.scheduleAction,
        this.isAggregate,
        this._selectedEntity,
        this._transactionToEdit,
        this.transactionType,
        transactionDate
    );

    if (AbstractScheduleParentEnum.schedFCoreComponent === this.abstractScheduleComponent ||
        AbstractScheduleParentEnum.schedFComponent === this.abstractScheduleComponent) {
      this.frmIndividualReceipt.patchValue({ aggregate_general_elec_exp: aggregateValue }, { onlySelf: true });
    } else {
      this.frmIndividualReceipt.patchValue({contribution_aggregate: aggregateValue}, {onlySelf: true});
    }
  }

  /**
   *  Show/Hide forced aggregation button
   *  Return true to show else false
   */
  public isShowForceAggregate(): boolean {
    if (this.transactionType) {
      // exclusion
      if (this.transactionType.endsWith('CON_EAR_DEP')) {
        return false;
      }
    }
    return true;
  }

  private forceAggregateSchedH() {
    // find the amount field name
    let fieldName;
    if (this.frmIndividualReceipt.controls['incurred_amount']) {
      fieldName = 'incurred_amount';
    } else if (this.frmIndividualReceipt.controls['total_amount']) {
      fieldName = 'total_amount';
    }
    if (this.isFieldName(fieldName, 'total_amount') && this.totalAmountReadOnly) {
      return;
    }

    // will take care of forced aggregation now
    if (fieldName === 'total_amount') {
      this._getFedNonFedPercentage();
      return;
    }

    if (fieldName === 'incurred_amount') {
      // TODO: has nothing to do with aggregation
      // Verify and remove
      // this._adjustDebtBalanceAtClose();
    }

  }

  public cancelEditEarMarkTrx() {
    if(!this.priviousTransactionType) {
      this.viewTransactions();
    }else {
      if(this.currentTransactionType.endsWith('MEMO')) {
        this.saveAndReturnToParent();
      }else {
        this.saveForEditEarmark();
      }
    }
  }
}
