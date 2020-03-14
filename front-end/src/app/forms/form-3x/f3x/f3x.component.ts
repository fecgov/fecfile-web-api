import { HttpClient } from '@angular/common/http';
import { Component, OnDestroy, OnInit, ViewEncapsulation , ChangeDetectionStrategy } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { Subject, Subscription } from 'rxjs';
import 'rxjs/add/operator/takeUntil';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { SchedHMessageServiceService } from '../../sched-h-service/sched-h-message-service.service';
import { SchedHServiceService } from '../../sched-h-service/sched-h-service.service';
import { AbstractScheduleParentEnum } from '../individual-receipt/abstract-schedule-parent.enum';
import { ScheduleActions } from '../individual-receipt/schedule-actions.enum';
import { ReportTypeService } from '../report-type/report-type.service';
import { F3xMessageService } from '../service/f3x-message.service';
import { TransactionTypeService } from '../transaction-type/transaction-type.service';
import { LoanMessageService } from './../../sched-c/service/loan-message.service';
import { TransactionModel } from './../../transactions/model/transaction.model';

@Component({
  selector: 'app-f3x',
  templateUrl: './f3x.component.html',
  styleUrls: ['./f3x.component.scss'],
  providers: [NgbTooltipConfig],
  encapsulation: ViewEncapsulation.None
})
export class F3xComponent implements OnInit, OnDestroy {
  public loadingData = false;
  public currentStep: string = 'step_1';
  public editMode: boolean = true;
  public step: string = '';
  public steps: any = {};
  public frm: any;
  public direction: string;
  public previousStep: string = '';
  public parentTransactionCategories: any = [];
  public reportsLoading: boolean = true;
  public reportTypes: any = [];
  public reportTypeIndicator: any = {};
  public reportType: any = null;
  public selectedReportType: any = {};
  public selectedReport: any = null;
  public regularReports: boolean = false;
  public specialReports: boolean = false;
  public selectedReportInfo: any = {};
  public transactionCategories: any = [];
  public transactionCategory: string = '';
  public transactionTypeText = '';
  public mainTransactionTypeText = '';
  public transactionType = '';
  public transactionTypeTextSchedF = '';
  public transactionTypeSchedF = '';
  public transactionTypeTextSchedFCore = '';
  public transactionTypeSchedFCore = '';
  public transactionTypeTextDebtSummary = '';
  public transactionTypeDebtSummary = '';
  public transactionDetailSchedC: any;
  public scheduleType = '';
  public isShowFilters = false;
  public formType: string = '';
  public scheduleAction: ScheduleActions;
  public scheduleCAction: ScheduleActions;
  public scheduleFAction: ScheduleActions;
  public scheduleFCoreAction: ScheduleActions;
  public forceChangeDetectionC1: Date;
  public forceChangeDetectionFDebtPayment: Date;
  public forceChangeDetectionDebtSummary: Date;

  public allTransactions: boolean = false;

  private _step: string = '';
  private _cloned: boolean = false;
  private _reportId: any;
  public loanPaymentScheduleAction: ScheduleActions;
  private showPart2: boolean;

  private onDestroy$ = new Subject();
  transactionData: any;
  transactionDataForChild: any;
  parentTransactionModel: any;
  populateHiddenFieldsMessageObj: any;
  populateFieldsMessageObj: any;
  queryParamsSubscription: Subscription;
  routerEventsSubscription:Subscription;

  constructor(
    private _reportTypeService: ReportTypeService,
    private _transactionTypeService: TransactionTypeService,
    private _formService: FormsService,
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _config: NgbTooltipConfig,
    private _router: Router,
    private _activatedRoute: ActivatedRoute,
    private _f3xMessageService: F3xMessageService,
    private _loanMessageService: LoanMessageService,
    private _schedHMessageServce: SchedHMessageServiceService,
    private _schedHService: SchedHServiceService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';

    this.queryParamsSubscription =_activatedRoute.queryParams.takeUntil(this.onDestroy$).subscribe(p => {
      this.transactionCategory = p.transactionCategory;
      if (p.edit === 'true' || p.edit === true) {
        this.editMode = true;
      }
      if (p.reportId && p.reportId !== '0') {
        this._reportId = p.reportId;
      }
      if (p.allTransactions === true || p.allTransactions === 'true') {
        this.allTransactions = true;
      } else {
        this.allTransactions = false;
      }

      //also clear the schedule type so the current component gets destroyed if leaving the form route
      if(p.step !== 'step_3'){
        this.scheduleType = null;
        this.transactionType = null;
      }
    });

    this._f3xMessageService.getParentModelMessage().takeUntil(this.onDestroy$).subscribe(message => {
        this.parentTransactionModel = message;
    });
  }

  ngOnInit(): void {
    this.scheduleAction = ScheduleActions.add;
    this.formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this.step = this._activatedRoute.snapshot.queryParams.step;
    this.editMode = this._activatedRoute.snapshot.queryParams.edit
      ? this._activatedRoute.snapshot.queryParams.edit
      : true;

    this._reportTypeService.getReportTypes(this.formType).subscribe(res => {
      if (typeof res === 'object') {
        if (Array.isArray(res.report_type)) {
          this.reportTypes = res.report_type;

          this.reportsLoading = false;

          this._setReports();
        }
      }
    });

    this._transactionTypeService.getTransactionCategories(this.formType).subscribe(res => {
      if (res) {
        this.transactionCategories = res.data.transactionCategories;
      }
    });
    localStorage.setItem('Receipts_Entry_Screen', 'Yes');
    this.routerEventsSubscription = this._router.events.takeUntil(this.onDestroy$).subscribe(val => {
      if (val) {
        if (val instanceof NavigationEnd) {
          if (
            val.url.indexOf(`/forms/form/${this.formType}`) === -1 &&
            val.url.indexOf(`/forms/transactions/${this.formType}`) === -1
          ) {
            if (localStorage.getItem(`form_${this.formType}_report_type`) !== null) {
              localStorage.setItem(
                `form_${this.formType}_saved_backup`,
                localStorage.getItem(`form_${this.formType}_saved`)
              );
              localStorage.setItem(
                `form_${this.formType}_report_type_backup`,
                localStorage.getItem(`form_${this.formType}_report_type`)
              );
              // //console.log(`form_${this._formType}_report_type_backup` + 'copied ');
              // //console.log(new Date().toISOString());
            }

            window.localStorage.removeItem(`form_${this.formType}_report_type`);
            window.localStorage.removeItem(`form_${this.formType}_transaction_type`);
            window.localStorage.removeItem(`form_${this.formType}_temp_transaction_type`);
            window.localStorage.removeItem(`form_${this.formType}_saved`);
          }
        } else {
          if (this._activatedRoute.snapshot.queryParams.step !== this.currentStep) {
            this.currentStep = this._activatedRoute.snapshot.queryParams.step;
            this.step = this._activatedRoute.snapshot.queryParams.step;
          }
          window.scrollTo(0, 0);
        }
      }
    });
  }

  ngOnDestroy(): void {
    this.onDestroy$.next(true);
    this.queryParamsSubscription.unsubscribe();
    this.routerEventsSubscription.unsubscribe();
  }

  ngDoCheck(): void {
    if (this._activatedRoute.snapshot.queryParams.step !== this.currentStep) {
      this.currentStep = this._activatedRoute.snapshot.queryParams.step;
      this.step = this._activatedRoute.snapshot.queryParams.step;
    }
  }

  /**
   * Sets the reports.
   */
  private _setReports(): void {
    if (
      typeof JSON.parse(localStorage.getItem(`form_${this.formType}_details`)) !== 'undefined' ||
      JSON.parse(localStorage.getItem(`form_${this.formType}_details`)) !== null
    ) {
      const form3XDetailsInstance = JSON.parse(localStorage.getItem(`form_${this.formType}_details`));

      if (typeof form3XDetailsInstance === 'object' && form3XDetailsInstance !== null) {
        if (form3XDetailsInstance.hasOwnProperty('regularspecialreportind')) {
          this.reportTypeIndicator = form3XDetailsInstance.regularspecialreportind;
        }

        if (form3XDetailsInstance.hasOwnProperty('reporttype')) {
          this.selectedReportType = form3XDetailsInstance.reporttype;
        }
      }

      if (this.reportTypeIndicator === 'S') {
        this.regularReports = false;
        this.specialReports = true;
      } else {
        this.specialReports = false;
        this.regularReports = true;
      }

      if (this.reportTypeIndicator === 'S') {
        this.regularReports = false;
        this.specialReports = true;
      } else {
        this.specialReports = false;
        this.regularReports = true;
      }
    } else if (typeof this.reportType === 'undefined' || this.reportType === null) {
      if (typeof this.reportTypes !== 'undefined' && this.reportTypes !== null) {
        this.selectedReportType = this.reportTypes.find(x => x.default_disp_ind === 'Y');
        if (typeof this.selectedReportType === 'object') {
          if (typeof this.selectedReportType.regular_special_report_ind === 'string') {
            this.reportTypeIndicator = this.selectedReportType.regular_special_report_ind;
          }
        } else {
          if (Array.isArray(this.reportTypes)) {
            this.reportType = this.reportTypes[0].report_type;
            this.selectedReportType = this.reportTypes.find(x => x.report_type === this.reportType);
            if (typeof this.selectedReportType === 'object') {
              this.reportTypeIndicator = this.selectedReportType.regular_special_report_ind;
            }
          }
        }
        if (typeof this.selectedReportType === 'object') {
          if (typeof this.selectedReportType.regular_special_report_ind === 'string') {
            if (this.selectedReportType.regular_special_report_ind === 'S') {
              this.regularReports = false;
              this.specialReports = true;
            } else {
              this.specialReports = false;
              this.regularReports = true;
            }
          }
        }
      } // typeof this.reportTypes
    } // typeof this.reportType
  }

  private _setCoverageDates(reportType: string): void {
    this.selectedReport = this.reportTypes.find(e => {
      return e.report_type === reportType;
    });

    if (typeof this.selectedReport === 'object') {
      this.reportTypeIndicator = this.selectedReport.regular_special_report_ind;
      if (typeof this.reportTypeIndicator === 'string') {
        if (this.reportTypeIndicator === 'S') {
          this.specialReports = true;
          this.regularReports = false;
        } else {
          this.regularReports = true;
          this.specialReports = false;
        }
      }
    }
  }

  /**
   * Get's message from child components to change the sidebar
   * in the view.
   */
  public switchSidebar(e: boolean): void {
    this.isShowFilters = e;
    //console.log('showfilters is ' + this.isShowFilters);
  }

  /**
   * Get's message from child components.
   *
   * @param      {Object}  e       The event object.
   */

  public onNotify(e: any): void {
    if (typeof e === 'object') {
      /**
       * This block indicates a user can move to the next
       * step or previous step in a form.
       */
      if (e.hasOwnProperty('form')) {
        if (typeof e.form === 'object') {
          this.frm = e.form;

          this.direction = e.direction;

          this.previousStep = e.previousStep;

          this._step = e.step;

          this.currentStep = e.step;

          this.transactionCategory = e.transactionCategory;

          // Pass Transaction Type to individual-receipt
          if (this.currentStep === 'step_3') {
            // Force reload form fields even if type did not change.
            // The original/typical method for informing the child component to get the
            // dynamic form fields is via change detection of the transactionType
            // detected by angular's ngDoCheck() implementation.  However, the form
            // need to be reloaded even when the type does not change as the form is
            // cleared of the memo default which varies by transaction type.
            // The solutionhere is to call the message service.  This may be the preferred
            // mechanism to use going forward.
            if (this.transactionType && this.transactionType === e.transactionType) {
              this._f3xMessageService.sendLoadFormFieldsMessage(AbstractScheduleParentEnum.schedMainComponent);
            }
            if (
              e.transactionDetail &&
              e.transactionDetail.transactionModel &&
              e.transactionDetail.transactionModel.cloned
            ) {
              this._cloned = true;
            } else {
              this._cloned = false;
            }

            if (e.showPart2 === false || e.showPart2 === 'false') {
              this.showPart2 = false;
            } else {
              this.showPart2 = null;
            }

            this.extractScheduleType(e);

            // Do this before setting scheduleAction to prevent change detection
            // in individual-receipt.component when sched F.
            // TODO add if else around schedules with component specific action
            // such as sched F and sched C.
            if (this._handleAddScheduleFDebtPayment(e)) {
              return;
            }

            if (e.action) {
              if (e.action in ScheduleActions) {
                this.scheduleAction = e.action;
              }
            }
            // default to add if not set.
            if (!this.scheduleAction) {
              this.scheduleAction = ScheduleActions.add;
            }

            if (this._handleScheduleC(e)) {
              return;
            }

            if (this._handleScheduleH(e)) {
              return;
            }

            if (this._handleScheduleL(e)) {
              return;
            }

            if (this._handleScheduleD(e)) {
              return;
            }

            // Coming from transactions, the event may contain the transaction data
            // with an action to allow for view or edit.
            let transactionTypeText = '';
            let transactionType = '';
            let mainTransactionTypeText = '';

            this.handleReattributionOrRedesignation(e);

            if (this.scheduleAction === ScheduleActions.edit) {
              // Sched C uses change detection for populating form for edit.
              // Have API add scheduleType to transactions table - using apiCall until then

              this.transactionCategories.filter(el => {
                if (el.value === this.transactionCategory) {
                  mainTransactionTypeText = el.text;
                }
              });
              if (!mainTransactionTypeText) {
                mainTransactionTypeText = e.mainTransactionTypeText ? e.mainTransactionTypeText : '';
              }

              let apiCall = null;
              if (e.transactionDetail) {
                if (e.transactionDetail.transactionModel) {
                  if (e.transactionDetail.transactionModel.hasOwnProperty('apiCall')) {
                    apiCall = e.transactionDetail.transactionModel.apiCall;
                  }
                }
              }
              if (apiCall === '/sc/schedC') {
                // use a schedC specific field to reduce unwanted change detection in Sched C.
                // this.step = 'loan';
                this.scheduleType = 'sched_c';
                this.scheduleCAction = ScheduleActions.edit;
                this.transactionDetailSchedC = e.transactionDetail.transactionModel;
              } else if (apiCall === '/sc/schedC1') {
                alert('edit C1 not yet supported');
              } else if (apiCall === '/sf/schedF') {
                if (this.scheduleType === 'sched_f_core') {
                  this._populateFormForEdit(e, AbstractScheduleParentEnum.schedFCoreComponent);
                  const transactionModel: TransactionModel = e.transactionDetail.transactionModel;
                  transactionTypeText = transactionModel.type;
                  transactionType = transactionModel.transactionTypeIdentifier;
                } else {
                  // force change to set show first page.
                  this.forceChangeDetectionFDebtPayment = new Date();
                  this._populateFormForEdit(e, AbstractScheduleParentEnum.schedFComponent);
                  const transactionModel: TransactionModel = e.transactionDetail.transactionModel;
                  transactionTypeText = transactionModel.type;
                  transactionType = transactionModel.transactionTypeIdentifier;
                }
              } else if (apiCall === '/se/schedE') {
                // force change to set show first page.
                // this.forceChangeDetectionFDebtPayment = new Date();
                this._populateFormForEdit(e, AbstractScheduleParentEnum.schedEComponent);
                const transactionModel: TransactionModel = e.transactionDetail.transactionModel;
                transactionTypeText = transactionModel.type;
                transactionType = transactionModel.transactionTypeIdentifier;
              } else {
                this._populateFormForEdit(e, AbstractScheduleParentEnum.schedMainComponent);
                const transactionModel: TransactionModel = e.transactionDetail.transactionModel;
                transactionTypeText = transactionModel.type;
                transactionType = transactionModel.transactionTypeIdentifier;
              }
            } else if (this.scheduleAction === ScheduleActions.view) {
              let apiCall = null;
              if (e.transactionDetail) {
                if (e.transactionDetail.transactionModel) {
                  if (e.transactionDetail.transactionModel.hasOwnProperty('apiCall')) {
                    apiCall = e.transactionDetail.transactionModel.apiCall;
                  }
                }
              }

              this._populateFormForView(e, AbstractScheduleParentEnum.schedMainComponent);
              const transactionModel: TransactionModel = e.transactionDetail.transactionModel;
              transactionTypeText = transactionModel.type;
              transactionType = transactionModel.transactionTypeIdentifier;
            } else {
              transactionTypeText = e.transactionTypeText ? e.transactionTypeText : '';
              transactionType = e.transactionType ? e.transactionType : '';
              mainTransactionTypeText = e.mainTransactionTypeText ? e.mainTransactionTypeText : '';
              // if (!mainTransactionTypeText) {
              //   mainTransactionTypeText = this._findMainTransactionTypeText(transactionType);
              // }
              if (
                e &&
                e.transactionDetail &&
                e.transactionDetail.transactionModel &&
                e.transactionDetail.transactionModel.isRedesignation
              ) {
                this._populateFormForEdit(e, AbstractScheduleParentEnum.schedMainComponent);
              }
              if (this.scheduleAction === ScheduleActions.addSubTransaction) {
                if (e.hasOwnProperty('prePopulateFieldArray') && Array.isArray(e.prePopulateFieldArray)) {
                  this._f3xMessageService.sendPopulateFormMessage({
                    key: 'field',
                    fieldArray: e.prePopulateFieldArray
                  });
                } else if (e.hasOwnProperty('prePopulateFromSchedD')) {
                  const component =
                    e.scheduleType === 'sched_e'
                      ? AbstractScheduleParentEnum.schedEComponent
                      : AbstractScheduleParentEnum.schedMainComponent;
                  const emitObject: any = {
                    key: 'prePopulateFromSchedD',
                    abstractScheduleComponent: component,
                    prePopulateFromSchedD: e.prePopulateFromSchedD
                  };
                  if (
                    (e.prePopulateFromSchedD.transaction_type_identifier === 'DEBT_TO_VENDOR' ||
                      e.prePopulateFromSchedD.transaction_type_identifier === 'DEBT_BY_VENDOR') &&
                    e.returnToDebtSummary
                  ) {
                    emitObject.returnToDebtSummary = true;
                    emitObject.returnToDebtSummaryInfo = e.returnToDebtSummaryInfo;
                  }
                  this._f3xMessageService.sendPopulateFormMessage(emitObject);
                  this.transactionDataForChild = emitObject;
                } else if (e.hasOwnProperty('prePopulateFromSchedL')) {
                  this._f3xMessageService.sendPopulateFormMessage({
                    key: 'prePopulateFromSchedL',
                    abstractScheduleComponent: AbstractScheduleParentEnum.schedMainComponent,
                    prePopulateFromSchedL: e.prePopulateFromSchedL
                  });
                }else if (e.hasOwnProperty('prePopulateFromSchedH')) {
                  this._f3xMessageService.sendPopulateFormMessage({
                    key: 'prePopulateFromSchedH',
                    abstractScheduleComponent: AbstractScheduleParentEnum.schedMainComponent,
                    prePopulateFromSchedH: e.prePopulateFromSchedH
                  });
                }
              }
            }
            this._setTransactionTypeBySchedule(
              transactionTypeText,
              transactionType,
              mainTransactionTypeText,
              this.scheduleType
            );
          }

          //transactionModel is being passed in so to leverage the reportId if present instead of getting from localStorage
          if (e && e.transactionDetail && e.transactionDetail.transactionModel) {
            this.canContinue(e.transactionDetail.transactionModel);
          } else {
            this.canContinue();
          }
        } else if (typeof e.form === 'string') {
          if (e.form === this.formType) {
            if (e.hasOwnProperty('reportTypeRadio')) {
              if (typeof e.reportTypeRadio === 'string') {
                this._setCoverageDates(e.reportTypeRadio);
              }
            } else if (e.hasOwnProperty('toDate') && e.hasOwnProperty('fromDate')) {
              this.selectedReportInfo = e;
            } else if (e.hasOwnProperty('transactionCategory')) {
              if (typeof e.transactionCategory === 'string') {
                this.transactionCategory = e.transactionCategory;
              }
            }
          }
        }
      } else if (e.hasOwnProperty('direction')) {
        if (typeof e.direction === 'string') {
          if (e.direction === 'previous') {
            this.direction = e.direction;

            this.previousStep = e.previousStep;

            this._step = e.step;
          }
        }
      } else if (e.hasOwnProperty('otherSchedHTransactionType')) {
        this.transactionType = e.otherSchedHTransactionType;

        if (this.transactionType === 'ALLOC_H4_SUM') {
          this.transactionTypeText = 'H4 Transaction List';
        } else if (this.transactionType === 'ALLOC_H4_TYPES') {
          this.transactionTypeText = 'H4 Entry';
        } else if (this.transactionType === 'ALLOC_EXP') {
          this.transactionTypeText = 'Allocated Federal / Non-Federal Expenditure';
        } else if (this.transactionType === 'ALLOC_EXP_CC_PAY') {
          this.transactionTypeText = 'Credit Card Payment for Allocated Expenditure';
        } else if (this.transactionType === 'ALLOC_EXP_CC_PAY_MEMO') {
          this.transactionTypeText = 'Credit Card Corresponding Memo';
        } else if (this.transactionType === 'ALLOC_EXP_STAF_REIM') {
          this.transactionTypeText = 'Staff Reimbursement for Allocated Expenditure';
        } else if (this.transactionType === 'ALLOC_EXP_STAF_REIM_MEMO') {
          this.transactionTypeText = 'Staff Reimbursement Corresponding Memo';
        } else if (this.transactionType === 'ALLOC_EXP_PMT_TO_PROL') {
          this.transactionTypeText = 'Payment to Payroll for Allocated Expenditure';
        } else if (this.transactionType === 'ALLOC_EXP_PMT_TO_PROL_MEMO') {
          this.transactionTypeText = 'Payroll Corresponding Memo';
        } else if (this.transactionType === 'ALLOC_EXP_VOID') {
          this.transactionTypeText = 'VOID';
        }

        if (this.transactionType === 'ALLOC_H6_SUM') {
          this.transactionTypeText = 'H6 Transaction List';
        } else if (this.transactionType === 'ALLOC_H6_TYPES') {
          this.transactionTypeText = 'H6 Entry';
        } else if (this.transactionType === 'ALLOC_FEA_DISB') {
          this.transactionTypeText = 'Allocated FEA Disbursement';
        } else if (this.transactionType === 'ALLOC_FEA_CC_PAY') {
          this.transactionTypeText = 'Credit Card Payment for Allocated FEA Payment';
        } else if (this.transactionType === 'ALLOC_FEA_CC_PAY_MEMO') {
          this.transactionTypeText = 'Credit Card Corresponding Memo';
        } else if (this.transactionType === 'ALLOC_FEA_STAF_REIM') {
          this.transactionTypeText = 'Staff Reimbursement for Allocated FEA Payment';
        } else if (this.transactionType === 'ALLOC_FEA_STAF_REIM_MEMO') {
          this.transactionTypeText = 'Staff Reimbursement Corresponding Memo';
        } else if (this.transactionType === 'ALLOC_FEA_VOID') {
          this.transactionTypeText = 'VOID';
        }
        // Levin Account Transaction Types
        if (this.transactionType === 'LEVIN_INDV_REC') {
          this.transactionTypeText = 'Schedule L-A Entry / Individual Receipt';
        } else if (this.transactionType === 'LEVIN_ORG_REC') {
          this.transactionTypeText = 'Schedule L-A Entry / Business Receipt';
        } else if (this.transactionType === 'LEVIN_PARTN_REC') {
          this.transactionTypeText = 'Schedule L-A Entry / Partnership Receipt';
          //} else if (this.transactionType === 'LEVIN_PARTN_MEMO') {
          //  this.transactionTypeText = 'Schedule L-A Entry / Partnership Receipt Memo';
        } else if (this.transactionType === 'LEVIN_PAC_REC') {
          this.transactionTypeText = 'Schedule L-A Entry / PAC Receipt';
        } else if (this.transactionType === 'LEVIN_NON_FED_REC') {
          this.transactionTypeText = 'Schedule L-A Entry / Non-Federal PAC Receipt';
        } else if (this.transactionType === 'LEVIN_TRIB_REC') {
          this.transactionTypeText = 'Schedule L-A Entry / Tribal Receipt';
        } else if (this.transactionType === 'LEVIN_OTH_REC') {
          this.transactionTypeText = 'Schedule L-A Entry / Other Receipt';
        } else if (this.transactionType === 'LEVIN_VOTER_REG') {
          this.transactionTypeText = 'Schedule L-B Entry / Voter Registration';
        } else if (this.transactionType === 'LEVIN_VOTER_ID') {
          this.transactionTypeText = 'Schedule L-B Entry / Voter ID';
        } else if (this.transactionType === 'LEVIN_GEN') {
          this.transactionTypeText = 'Schedule L-B Entry / Generic Campaign Activity';
        } else if (this.transactionType === 'LEVIN_OTH_DISB') {
          this.transactionTypeText = 'Schedule L-B Entry / Other Disbursement';
        } else if (this.transactionType === 'LEVIN_GOTV') {
          this.transactionTypeText = 'Schedule L-B Entry / Get out the Vote (GOTV)';
        }
      }
    }
  }

  private handleReattributionOrRedesignation(e: any) {
    if (e && e.transactionDetail && e.transactionDetail.transactionModel) {
      const transactionModel: TransactionModel = e.transactionDetail.transactionModel;
      e.transactionTypeText = transactionModel.type;
      e.transactionType = transactionModel.transactionTypeIdentifier;

      let reattributionId: string = null;
      let redesignationId: string = null;
      let maxAmount = transactionModel.amount;
      if(this.scheduleAction === ScheduleActions.edit){
        maxAmount = transactionModel.originalAmount;
      }
      if(transactionModel.isReattribution || transactionModel.isRedesignation){
        if (transactionModel.isReattribution) {
          if (this.scheduleAction === ScheduleActions.add) {
            reattributionId = transactionModel.reattribution_id;
          } else if (this.scheduleAction === ScheduleActions.edit) {
            reattributionId = transactionModel.transactionId;
          }
  
          const hiddenFieldsEmitObj = {
            abstractScheduleComponent: AbstractScheduleParentEnum.schedMainComponent,
            reattributionTransactionId: reattributionId,
            maxAmount: maxAmount,
            reattributionTransaction: transactionModel
          };
          this._f3xMessageService.sendPopulateHiddenFieldsMessage(hiddenFieldsEmitObj);
          const fieldArray = [{name:'purpose_description', value:transactionModel.purposeDescription}];
          const populateFieldsMessageObj = { abstractScheduleComponent: AbstractScheduleParentEnum.schedMainComponent, fieldArray };
          this._f3xMessageService.sendPopulateFieldsMessage(populateFieldsMessageObj);
          this.populateHiddenFieldsMessageObj = hiddenFieldsEmitObj;
          this.populateFieldsMessageObj = populateFieldsMessageObj;
        } else if (transactionModel.isRedesignation) {
          if (this.scheduleAction === ScheduleActions.add) {
            redesignationId = transactionModel.redesignation_id;
          } else if (this.scheduleAction === ScheduleActions.edit) {
            redesignationId = transactionModel.transactionId;
          }
          const hiddenFieldsEmitObj = {
            abstractScheduleComponent: AbstractScheduleParentEnum.schedMainComponent,
            redesignationTransactionId: redesignationId,
            maxAmount: maxAmount
          };
          this._f3xMessageService.sendPopulateHiddenFieldsMessage(hiddenFieldsEmitObj);
          this.populateHiddenFieldsMessageObj = hiddenFieldsEmitObj;
        }
      }
      else{
        this.populateHiddenFieldsMessageObj = null;
        this.populateFieldsMessageObj = null;
      }
    }
    else{
      this.populateHiddenFieldsMessageObj = null;
      this.populateFieldsMessageObj = null;
    }
  }

  /**
   * This method should extract the schedule type based on transactionTypeIdentifier in certain
   * cases. It was being defaulted to sched_a but in case of e.g. sched c, it should be extracted.
   * Additional use cases can be added to it
   * @param e
   */
  private extractScheduleType(e: any) {
    if (
      e.transactionDetail &&
      e.transactionDetail.transactionModel &&
      e.transactionDetail.transactionModel.transactionTypeIdentifier === 'LOAN_REPAY_MADE'
    ) {
      e.scheduleType = 'sched_c_loan_payment';
    }

    //TODO-Remove this elseif once transactions are moved to Disubursements
    if (e.scheduleType === 'Schedule E') {
      e.scheduleType = 'sched_e';
    }

    if (
      !e.scheduleType &&
      e.transactionDetail &&
      e.transactionDetail.transactionModel &&
      e.transactionDetail.transactionModel.apiCall === '/se/schedE'
    ) {
      e.scheduleType = 'sched_e';
    }

    if (e.scheduleType && e.transactionType) {
      if (
        (e.scheduleType === 'sched_f' &&
          (e.transactionType === 'COEXP_PARTY' ||
            e.transactionType === 'COEXP_CC_PAY' ||
            e.transactionType === 'COEXP_STAF_REIM' ||
            e.transactionType === 'COEXP_PMT_PROL')) ||
        e.transactionType === 'COEXP_PARTY_VOID' ||
        e.transactionType === 'COEXP_PMT_PROL_VOID' ||
        e.transactionType === 'COEXP_CC_PAY_MEMO' ||
        e.transactionType === 'COEXP_STAF_REIM_MEMO' ||
        e.transactionType === 'COEXP_PMT_PROL_MEMO'
      ) {
        // TODO: Workaround backend must be updated with correct transactionType for Coordinated Party Expenditure Void
        if (e.transactionType === 'COEXP_PMT_PROL_VOID') {
          e.transactionType = 'COEXP_PARTY_VOID';
        }
        e.scheduleType = 'sched_f_core';
      }
    }

    // extract shed_f_core based on transactionTypeIdentifier
    if (!e.scheduleType && e.transactionDetail && e.transactionDetail.transactionModel) {
      const tTypeIdentifier = e.transactionDetail.transactionModel.transactionTypeIdentifier;
      if (
        tTypeIdentifier === 'COEXP_PARTY' ||
        tTypeIdentifier === 'COEXP_CC_PAY' ||
        tTypeIdentifier === 'COEXP_STAF_REIM' ||
        tTypeIdentifier === 'COEXP_PMT_PROL' ||
        tTypeIdentifier === 'COEXP_PARTY_VOID' ||
        tTypeIdentifier === 'COEXP_PMT_PROL_VOID' ||
        tTypeIdentifier === 'COEXP_CC_PAY_MEMO' ||
        tTypeIdentifier === 'COEXP_STAF_REIM_MEMO' ||
        tTypeIdentifier === 'COEXP_PMT_PROL_MEMO'
      ) {
        e.scheduleType = 'sched_f_core';
      }
      if (tTypeIdentifier === 'COEXP_PARTY_DEBT') {
        e.scheduleType = 'sched_f';
      }
    }
    // default to sched_a ?
    this.scheduleType = e.scheduleType ? e.scheduleType : 'sched_a';

    /*    //Schedule H's need to be remapped too
     if(e.scheduleType === 'Schedule H3'){
      this.scheduleType = 'sched_h3';
      this.transactionType = 'ALLOC_H3_RATIO';
    } */
  }

  /**
   * Send a message the child component rather than sending data as input because
   * ngOnChanges fires when the form fields are changed, thereby reseting the
   * fields to the previous value.  Result is fields can't be changed.
   * @param e
   * @param schedule
   */
  private _populateFormForEdit(e: any, schedule: AbstractScheduleParentEnum) {
    e.transactionDetail.action = this.scheduleAction;
    const emitObject: any = {
      key: 'fullForm',
      abstractScheduleComponent: schedule,
      transactionModel: e.transactionDetail
    };
    // Checking by transaction_type_identifier as a saftey precaution.
    if (
      (e.transactionDetail.transactionModel.transactionTypeIdentifier === 'DEBT_TO_VENDOR' ||
        e.transactionDetail.transactionModel.transactionTypeIdentifier === 'DEBT_BY_VENDOR' ||
        e.transactionDetail.transactionModel.transactionTypeIdentifier === 'OPEXP_DEBT' ||
        e.transactionDetail.transactionModel.transactionTypeIdentifier === 'ALLOC_EXP_DEBT' ||
        e.transactionDetail.transactionModel.transactionTypeIdentifier === 'ALLOC_FEA_DISB_DEBT' ||
        e.transactionDetail.transactionModel.transactionTypeIdentifier === 'OTH_DISB_DEBT' ||
        e.transactionDetail.transactionModel.transactionTypeIdentifier === 'FEA_100PCT_DEBT_PAY' ||
        e.transactionDetail.transactionModel.transactionTypeIdentifier === 'COEXP_PARTY_DEBT' ||
        e.transactionDetail.transactionModel.transactionTypeIdentifier === 'IE' ||
        e.transactionDetail.transactionModel.transactionTypeIdentifier === 'OTH_REC_DEBT') &&
      e.returnToDebtSummary
    ) {
      emitObject.returnToDebtSummary = true;
      emitObject.returnToDebtSummaryInfo = e.returnToDebtSummaryInfo;
    }
    this._f3xMessageService.sendPopulateFormMessage(emitObject);

    
    this.storeTransactionDataForPopulatingFormForEdit(emitObject);
  }

  private storeTransactionDataForPopulatingFormForEdit(emitObject: any) {
    //there are some transactions/schedules that have their own method and object structure for populating data (i.e. H2),
    //and in those cases, the object it is already set up, so dont overwrite it. 
    if(this.scheduleType === 'sched_f'){
      this.transactionDataForChild = emitObject;
    }
    else if (this.scheduleType !== 'sched_h2' && this.scheduleType !== 'sched_h3' && this.scheduleType !== 'sched_h5') {
      this.transactionData = emitObject;
    }
  }

  /**
   * Handle Schedule C forms.
   * @returns true if schedule C and should stop processing
   */
  private _handleScheduleC(transaction: any): boolean {
    let transactionDetail = transaction.transactionDetail;
    let finish = false;
    if (
      this.scheduleType === 'sched_c' ||
      this.scheduleType === 'sched_c_ls' ||
      this.scheduleType === 'sched_c_loan_payment' ||
      this.scheduleType === 'sched_c1' ||
      this.scheduleType === 'sched_c_en' ||
      this.scheduleType === 'sched_c_es'
    ) {
      if (this.scheduleType === 'sched_c' || this.scheduleType === 'sched_c_en') {
        if (this.scheduleAction === ScheduleActions.add) {
          // this.forceChangeDetectionC = new Date();
          this.scheduleCAction = ScheduleActions.add;
        } else if ((this.scheduleAction = ScheduleActions.edit)) {
          // TODO once API provides scheduleType in transaction table object
          // move logic where dectecting schedC using apiCall here.
          // Could hard code a conversion from apiCall value to sched_c in the
          // transaction table component until then.
          this.scheduleCAction = ScheduleActions.edit;
        }
      } else if (this.scheduleType === 'sched_c_ls') {
        this.scheduleType = 'sched_c_ls';
        this.scheduleCAction = ScheduleActions.loanSummary;

        //send message to refresh data for loan summary
        let msg: any = {};
        if (transaction.reportId && transaction.reportId !== 'undefined') {
          msg.reportId = transaction.reportId;
        }
        this._loanMessageService.sendLoanSummaryRefreshMessage(msg);
      } else if (this.scheduleType === 'sched_c_loan_payment') {
        //this is being done in case loan payment is being accessed from transaction table,
        //a flag is needed to return back to the transaction table's 'disbursement tab'
        //upon clicking cancel, based on the current implementation of loan payments.
        if (transaction.previousStep === 'transactions') {
          transactionDetail.transactionModel.entryScreenScheduleType = transaction.previousStep;
        }

        //also loan payment needs to have a schedule action of its own, 'loanPaymentScheduleAction'
        //since a new payment can be "added" while "editing" the loan itself
        if (
          transaction &&
          transaction.transactionDetail &&
          transaction.transactionDetail.transactionModel &&
          transaction.transactionDetail.transactionModel.apiCall === '/sb/schedB' &&
          transaction.transactionDetail.transactionModel.transactionId
        ) {
          this.loanPaymentScheduleAction = ScheduleActions.edit;
        } else {
          this.loanPaymentScheduleAction = ScheduleActions.add;
        }
      } else if (this.scheduleType === 'sched_c1') {
        this.forceChangeDetectionC1 = new Date();
      }
      if (transactionDetail && transactionDetail.transactionModel) {
        this.canContinue(transactionDetail.transactionModel);
      } else {
        this.canContinue();
      }
      finish = true;
      //setting the transaction detail for @input in 'add' scenario for loan payment
      if (transactionDetail) {
        this.transactionDetailSchedC = transactionDetail.transactionModel;
      }
    }
    return finish;
  }

  /**
   * Handle Schedule H forms.
   * @returns true if schedule H and should stop processing
   */
  private _handleScheduleH(transaction: any): boolean {
    let transactionDetail = transaction.transactionDetail;
    let finish = false;

    if (this.scheduleType === 'Schedule H1') {
      this.transactionType = transactionDetail.transactionModel.transactionTypeIdentifier;
      this.scheduleAction = ScheduleActions.edit;
      this.scheduleType = 'sched_h1';
      finish = true; //since h1 is not extending abstract schedule, it is being handled differently
    } else if (this.scheduleType === 'Schedule H2') {
      this.scheduleAction = ScheduleActions.edit;
      this.transactionType = transactionDetail.transactionModel.transactionTypeIdentifier;
      this.scheduleType = 'sched_h2';
    } else if (this.scheduleType === 'Schedule H3') {
      this.scheduleAction = ScheduleActions.edit;
      this.transactionType = 'ALLOC_H3_RATIO';
      this.scheduleType = 'sched_h3';
    } else if (this.scheduleType === 'Schedule H4') {
      this.scheduleAction = ScheduleActions.edit;
      this.transactionType = transactionDetail.transactionModel.transactionTypeIdentifier;
      this.scheduleType = 'sched_h4';
    } else if (this.scheduleType === 'Schedule H5') {
      this.scheduleAction = ScheduleActions.edit;
      this.transactionType = transactionDetail.transactionModel.transactionTypeIdentifier;
      this.scheduleType = 'sched_h5';
    } else if (this.scheduleType === 'Schedule H6') {
      this.scheduleAction = ScheduleActions.edit;
      this.transactionType = transactionDetail.transactionModel.transactionTypeIdentifier;
      this.scheduleType = 'sched_h6';
    }

    this._schedHMessageServce.sendpopulateHFormForEditMessage(transaction);
    this.transactionData = transaction;
    if (transactionDetail && transactionDetail.transactionModel) {
      this.canContinue(transactionDetail.transactionModel);
    } else {
      this.canContinue();
    }

    return finish;
  }

  /**
   * Handle Schedule L forms.
   * @returns true if schedule L and should stop processing
   */
  private _handleScheduleL(transaction: any): boolean {
    let transactionDetail = transaction.transactionDetail;
    let finish = false;

    if (this.scheduleType === 'Schedule L-A' || this.scheduleType === 'Schedule L-B') {
      this.scheduleAction = ScheduleActions.edit;
      this.transactionType = transactionDetail.transactionModel.transactionTypeIdentifier;
      this.scheduleType = 'sched_L';
    }
    if (transactionDetail && transactionDetail.transactionModel) {
      this.canContinue(transactionDetail.transactionModel);
    } else {
      this.canContinue();
    }

    return finish;
  }

  /**
   * Special handling for Sched D.  For example, don't call dynamic forms for Summary.
   * @returns true if schedule D and should stop processing
   */
  private _handleScheduleD(e: any): boolean {
    let finish = false;
    if (this.scheduleType === 'sched_d_ds') {
      this.transactionTypeDebtSummary = e.transactionType;
      this.transactionTypeTextDebtSummary = e.transactionTypeText;
      this.forceChangeDetectionDebtSummary = new Date();
      this.canContinue();
      finish = true;
    }
    return finish;
  }

  /**
   * Handle Schedule F Debt Payment form.
   * @returns true if schedule F and should stop processing
   */
  private _handleAddScheduleFDebtPayment(e: any): boolean {
    let finish = false;
    if (this.scheduleType === 'sched_f') {
      if (e.action === ScheduleActions.addSubTransaction) {
        this.scheduleFAction = e.action;
        this.mainTransactionTypeText = e.mainTransactionTypeText ? e.mainTransactionTypeText : '';
        this.transactionTypeSchedF = e.transactionType ? e.transactionType : '';
        this.transactionTypeTextSchedF = e.transactionTypeText ? e.transactionTypeText : '';
        this.forceChangeDetectionFDebtPayment = new Date();
        if (this.scheduleFAction === ScheduleActions.addSubTransaction) {
          if (e.hasOwnProperty('prePopulateFromSchedD')) {
            const emitObject: any = {
              key: 'prePopulateFromSchedD',
              abstractScheduleComponent: AbstractScheduleParentEnum.schedFComponent,
              prePopulateFromSchedD: e.prePopulateFromSchedD
            };
            if (
              (e.prePopulateFromSchedD.transaction_type_identifier === 'DEBT_TO_VENDOR' ||
                e.prePopulateFromSchedD.transaction_type_identifier === 'DEBT_BY_VENDOR') &&
              e.returnToDebtSummary
            ) {
              emitObject.returnToDebtSummary = true;
              emitObject.returnToDebtSummaryInfo = e.returnToDebtSummaryInfo;
            }
            this._f3xMessageService.sendPopulateFormMessage(emitObject);
            this.transactionDataForChild = emitObject;
          }
        }
        this.canContinue();
        finish = true;
      }
    }
    return finish;
  }

  /**
   * If a schedule component will need to accept transactions types, for example when it
   * supports multiples, they may be set here as input into the schedule component.
   *
   * @param transactionTypeText
   * @param transactionType
   * @param scheduleType
   */
  private _setTransactionTypeBySchedule(
    transactionTypeText: string,
    transactionType: string,
    mainTransactionTypeText: string,
    scheduleType: string
  ) {
    if (!scheduleType) {
      this.transactionType = transactionType;
      this.transactionTypeText = transactionTypeText;
      return;
    }
    if (scheduleType.length === 0) {
      this.transactionType = transactionType;
      this.transactionTypeText = transactionTypeText;
      return;
    }
    if (scheduleType === 'sched_f_core') {
      this.transactionTypeSchedFCore = transactionType;
      this.transactionTypeTextSchedFCore = transactionTypeText;
      this.scheduleFCoreAction = this.scheduleAction;
    } else if (scheduleType.startsWith('sched_f') && scheduleType !== 'sched_f_core') {
      // this.transactionTypeSchedF = transactionType;
      // this.transactionTypeTextSchedF = transactionTypeText;
      // this.scheduleFAction = this.scheduleAction;
    } else if (scheduleType.startsWith('sched_c')) {
    } else {
      this.transactionType = transactionType;
      this.transactionTypeText = transactionTypeText;
      this.mainTransactionTypeText = mainTransactionTypeText;
    }
  }

  /**
   * Determines ability to continue.
   */
  public canContinue(transactionModel: any = null): void {
    let reportId = '';
    if (
      transactionModel &&
      transactionModel.reportId &&
      transactionModel.reportId !== '0' &&
      transactionModel.reportId !== 'undefined'
    ) {
      reportId = transactionModel.reportId.toString();
    } else if (this._activatedRoute.snapshot.queryParams && this._activatedRoute.snapshot.queryParams.reportId) {
      reportId = this._activatedRoute.snapshot.queryParams.reportId;
    }
    //if not present, only then fall back on localStorage
    //TODO-local storage is being used throughout the application to retain state and it should be changed as this can cause inconsistencies.
    //this is just a temp fix.
    else if (
      localStorage.getItem('reportId') &&
      localStorage.getItem('reportId') !== '0' &&
      localStorage.getItem('reportId') !== 'undefined'
    ) {
      reportId = localStorage.getItem('reportId');
    }

    if (this.frm && this.direction) {
      if (this._reportId) {
        localStorage.setItem(`reportId`, this._reportId);
      }

      let queryParamsObj: any = {
        step: this.step,
        edit: this.editMode,
        transactionCategory: this.transactionCategory
      };

      if (reportId) {
        queryParamsObj.reportId = reportId;
      }

      if (this.direction === 'next') {
        if (this.frm.valid) {
          this.step = this._step;
          queryParamsObj.step = this.step;
          queryParamsObj.showPart2 = this.showPart2;
          if (this._cloned) {
            queryParamsObj.cloned = this._cloned;
            this._router.navigate([`/forms/form/${this.formType}`], {
              queryParams: queryParamsObj
            });
          } else {
            this._router.navigate([`/forms/form/${this.formType}`], {
              queryParams: queryParamsObj
            });
          }
        } else if (this.frm === 'preview') {
          this.step = this._step;
          queryParamsObj.step = this.step;

          this._router.navigate([`/forms/form/${this.formType}`], {
            queryParams: queryParamsObj
          });
        }
      } else if (this.direction === 'previous') {
        this.step = this._step;
        queryParamsObj.step = this.step;

        this._router.navigate([`/forms/form/${this.formType}`], {
          queryParams: queryParamsObj
        });
      }
    }
  }

  private _populateFormForView(e: any, schedule: AbstractScheduleParentEnum) {
    e.transactionDetail.action = this.scheduleAction;
    const emitObject: any = {
      key: 'fullForm',
      abstractScheduleComponent: schedule,
      transactionModel: e.transactionDetail
    };

    this._f3xMessageService.sendPopulateFormMessage(emitObject);
  }

  private _findMainTransactionTypeText(transactionType: string): string {
    this.transactionCategories.forEach(cat => {
      cat.options.forEach(subCat => {
        // subCat.forEach(type)
        subCat.options.forEach(type => {
          if (type.value === transactionType) {
            return cat.text;
          }
        });
      });
    });
    return '';
  }
}
