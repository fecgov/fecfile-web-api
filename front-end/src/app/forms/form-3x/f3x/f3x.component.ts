import { TransactionModel } from './../../transactions/model/transaction.model';
import { Component, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { ReportTypeService } from '../report-type/report-type.service';
import { TransactionTypeService } from '../transaction-type/transaction-type.service';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import {
  form3x_data,
  form3XReport,
  form3xReportTypeDetails
} from '../../../shared/interfaces/FormsService/FormsService';
import {
  selectedElectionState,
  selectedElectionDate,
  selectedReportType
} from '../../../shared/interfaces/FormsService/FormsService';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { F3xMessageService } from '../service/f3x-message.service';
import { ScheduleActions } from '../individual-receipt/schedule-actions.enum';
import { AbstractScheduleParentEnum } from '../individual-receipt/abstract-schedule-parent.enum';

@Component({
  selector: 'app-f3x',
  templateUrl: './f3x.component.html',
  styleUrls: ['./f3x.component.scss'],
  providers: [NgbTooltipConfig],
  encapsulation: ViewEncapsulation.None
})
export class F3xComponent implements OnInit {
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
  public transactionType = '';
  public transactionTypeTextSchedF = '';
  public transactionTypeSchedF = '';
  public transactionDetailSchedC: any;
  public scheduleType = '';
  public isShowFilters = false;
  public formType: string = '';
  public scheduleAction: ScheduleActions;
  public scheduleCAction: ScheduleActions;
  public scheduleFAction: ScheduleActions;
  public forceChangeDetectionC1: Date;
  public forceChangeDetectionFDebtPayment: Date;

  public allTransactions: boolean = false;

  private _step: string = '';
  private _cloned: boolean = false;
  private _reportId: any;
  public loanPaymentScheduleAction: ScheduleActions;

  constructor(
    private _reportTypeService: ReportTypeService,
    private _transactionTypeService: TransactionTypeService,
    private _formService: FormsService,
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _config: NgbTooltipConfig,
    private _router: Router,
    private _activatedRoute: ActivatedRoute,
    private _f3xMessageService: F3xMessageService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
    _activatedRoute.queryParams.subscribe(p => {
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

    this._router.events.subscribe(val => {
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
              // console.log(`form_${this._formType}_report_type_backup` + 'copied ');
              // console.log(new Date().toISOString());
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
    console.log('showfilters is ' + this.isShowFilters);
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

            if (this._handleScheduleD()) {
              return;
            }

            // Coming from transactions, the event may contain the transaction data
            // with an action to allow for view or edit.
            let transactionTypeText = '';
            let transactionType = '';

            if (this.scheduleAction === ScheduleActions.edit) {
              // Sched C uses change detection for populating form for edit.
              // Have API add scheduleType to transactions table - using apiCall until then

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
                // force change to set show first page.
                this.forceChangeDetectionFDebtPayment = new Date();
                this._populateFormForEdit(e, AbstractScheduleParentEnum.schedFComponent);
              } else {
                this._populateFormForEdit(e, AbstractScheduleParentEnum.schedMainComponent);
                const transactionModel: TransactionModel = e.transactionDetail.transactionModel;
                transactionTypeText = transactionModel.type;
                transactionType = transactionModel.transactionTypeIdentifier;
              }
            } else {
              transactionTypeText = e.transactionTypeText ? e.transactionTypeText : '';
              transactionType = e.transactionType ? e.transactionType : '';

              if (this.scheduleAction === ScheduleActions.addSubTransaction) {
                if (e.hasOwnProperty('prePopulateFieldArray') && Array.isArray(e.prePopulateFieldArray)) {
                  this._f3xMessageService.sendPopulateFormMessage({
                    key: 'field',
                    fieldArray: e.prePopulateFieldArray
                  });
                } else if (e.hasOwnProperty('prePopulateFromSchedD')) {
                  this._f3xMessageService.sendPopulateFormMessage({
                    key: 'prePopulateFromSchedD',
                    abstractScheduleComponent: AbstractScheduleParentEnum.schedMainComponent,
                    prePopulateFromSchedD: e.prePopulateFromSchedD
                  });
                }
              }
            }
            this._setTransactionTypeBySchedule(transactionTypeText, transactionType, this.scheduleType);
          }
          this.canContinue();
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
      }
    }
  }

  /**
   * This method should extract the schedule type based on transactionTypeIdentifier in certain
   * cases. It was being defaulted to sched_a but in case of e.g. sched c, it should be extracted.
   * Additional use cases can be added to it
   * @param e
   */
  private extractScheduleType(e: any) {

    if (e.transactionDetail && e.transactionDetail.transactionModel &&
      e.transactionDetail.transactionModel.transactionTypeIdentifier === "LOAN_REPAY_MADE") {
      e.scheduleType = "sched_c_loan_payment";
    }

    //default to sched_a ?
    this.scheduleType = e.scheduleType ? e.scheduleType : 'sched_a';
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
    this._f3xMessageService.sendPopulateFormMessage({
      key: 'fullForm',
      abstractScheduleComponent: schedule,
      transactionModel: e.transactionDetail
    });
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
      } else if (this.scheduleType === 'sched_c_loan_payment') {
        //this is being done in case loan payment is being accessed from transaction table,
        //a flag is needed to return back to the transaction table's 'disbursement tab'
        //upon clicking cancel, based on the current implementation of loan payments.
        if (transaction.previousStep === 'transactions') {
          transactionDetail.transactionModel.entryScreenScheduleType = transaction.previousStep;
        }

        //also loan payment needs to have a schedule action of its own, 'loanPaymentScheduleAction'
        //since a new payment can be "added" while "editing" the loan itself
        if (transaction && transaction.transactionDetail && transaction.transactionDetail.transactionModel &&
          transaction.transactionDetail.transactionModel.apiCall === '/sb/schedB' && 
          transaction.transactionDetail.transactionModel.transactionId) {
          this.loanPaymentScheduleAction = ScheduleActions.edit;
        }
        else {
          this.loanPaymentScheduleAction = ScheduleActions.add;
        }


      } else if (this.scheduleType === 'sched_c1') {
        this.forceChangeDetectionC1 = new Date();
      }
      this.canContinue();
      finish = true;
      //setting the transaction detail for @input in 'add' scenario for loan payment
      if (transactionDetail) {
        this.transactionDetailSchedC = transactionDetail.transactionModel;
      }
    }
    return finish;
  }

  /**
   * Special handling for Sched D.  For example, don't call dynamic forms for Summary.
   * @returns true if schedule D and should stop processing
   */
  private _handleScheduleD(): boolean {
    let finish = false;
    if (this.scheduleType === 'sched_d_ds') {
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
        this.transactionTypeSchedF = e.transactionType ? e.transactionType : '';
        this.transactionTypeTextSchedF = e.transactionTypeText ? e.transactionTypeText : '';
        this.forceChangeDetectionFDebtPayment = new Date();
        if (this.scheduleFAction === ScheduleActions.addSubTransaction) {
          if (e.hasOwnProperty('prePopulateFromSchedD')) {
            this._f3xMessageService.sendPopulateFormMessage({
              key: 'prePopulateFromSchedD',
              abstractScheduleComponent: AbstractScheduleParentEnum.schedFComponent,
              prePopulateFromSchedD: e.prePopulateFromSchedD
            });
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
  private _setTransactionTypeBySchedule(transactionTypeText: string, transactionType: string, scheduleType: string) {
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
    if (scheduleType.startsWith('sched_f')) {
      // this.transactionTypeSchedF = transactionType;
      // this.transactionTypeTextSchedF = transactionTypeText;
      // this.scheduleFAction = this.scheduleAction;
    } else if (scheduleType.startsWith('sched_c')) {
    } else {
      this.transactionType = transactionType;
      this.transactionTypeText = transactionTypeText;
    }
  }

  /**
   * Determines ability to continue.
   */
  public canContinue(): void {
    if (this.frm && this.direction) {
      localStorage.setItem(`reportId`, this._reportId);
      if (this.direction === 'next') {
        if (this.frm.valid) {
          this.step = this._step;

          if (this._cloned) {
            this._router.navigate([`/forms/form/${this.formType}`], {
              queryParams: {
                step: this.step,
                edit: this.editMode,
                transactionCategory: this.transactionCategory,
                cloned: this._cloned
              }
            });
          } else {
            this._router.navigate([`/forms/form/${this.formType}`], {
              queryParams: { step: this.step, edit: this.editMode, transactionCategory: this.transactionCategory }
            });
          }
        } else if (this.frm === 'preview') {
          this.step = this._step;

          this._router.navigate([`/forms/form/${this.formType}`], {
            queryParams: { step: this.step, edit: this.editMode, transactionCategory: this.transactionCategory }
          });
        }
      } else if (this.direction === 'previous') {
        this.step = this._step;

        this._router.navigate([`/forms/form/${this.formType}`], {
          queryParams: { step: this.step, edit: this.editMode, transactionCategory: this.transactionCategory }
        });
      }
    }
  }
}
