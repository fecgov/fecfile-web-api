import { HttpClient } from '@angular/common/http';
import { Component, Input, OnInit } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { Subject, Subscription } from 'rxjs';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { AbstractScheduleParentEnum } from '../../form-3x/individual-receipt/abstract-schedule-parent.enum';
import { ScheduleActions } from '../../form-3x/individual-receipt/schedule-actions.enum';
import { ReportTypeService } from '../../form-3x/report-type/report-type.service';
import { F3xMessageService } from '../../form-3x/service/f3x-message.service';
import { TransactionTypeService } from '../../form-3x/transaction-type/transaction-type.service';
import { LoanMessageService } from '../../sched-c/service/loan-message.service';
import { SchedHMessageServiceService } from '../../sched-h-service/sched-h-message-service.service';
import { SchedHServiceService } from '../../sched-h-service/sched-h-service.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';

@Component({
  selector: 'app-f24',
  templateUrl: './f24.component.html',
  styleUrls: ['./f24.component.scss']
})
export class F24Component implements OnInit {


  @Input() jumpToTransaction: any;

  private currentStep: string = 'step_1';
  private editMode: boolean = true;
  public step: string = '';
  @Input() transactionData: any;
  private steps: any = {};
  private frm: any;
  private direction: string;
  private previousStep: string = '';
  private parentTransactionCategories: any = [];
  public reportsLoading: boolean = true;
  public showValidateBar: boolean = false;
  public reportTypes: any = [];
  private reportTypeIndicator: any = {};
  public reportType: any = null;
  public selectedReportType: any = {};
  private selectedReport: any = null;
  private regularReports: boolean = false;
  private specialReports: boolean = false;
  public selectedReportInfo: any = {};
  public transactionCategories: any = [];
  public transactionCategory: string = '';
  private transactionTypeText = '';
  @Input() mainTransactionTypeText = '';
  @Input() transactionType = '';
  private transactionTypeTextSchedF = '';
  private transactionTypeSchedF = '';
  private transactionTypeTextSchedFCore = '';
  private transactionTypeSchedFCore = '';
  private transactionTypeTextDebtSummary = '';
  private transactionTypeDebtSummary = '';
  private transactionDetailSchedC: any;
  private unused: any;
  private isShowFilters = false;
  public formType: string = '';
  @Input() scheduleAction: ScheduleActions;
  private scheduleCAction: ScheduleActions;
  private scheduleFAction: ScheduleActions;
  private scheduleFCoreAction: ScheduleActions;
  private forceChangeDetectionC1: Date;
  private forceChangeDetectionFDebtPayment: Date;
  private forceChangeDetectionDebtSummary: Date;
  private forceChangeDetectionH1: Date;
  public scheduleType: string = '';

  public allTransactions: boolean = false;

  private _step: string = '';
  private _cloned: boolean = false;
  private _reportId: any;
  private loanPaymentScheduleAction: ScheduleActions;

  private onDestroy$ = new Subject();
  @Input() transactionDataForChild: any;
  @Input() parentTransactionModel: any;
  private populateHiddenFieldsMessageObj: any;
  private populateFieldsMessageObj: any;
  private queryParamsSubscription: Subscription;
  private routerEventsSubscription: Subscription;
  private returnToGlobalAllTransaction: boolean;

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
    private _messageService: MessageService,
    private _loanMessageService: LoanMessageService,
    private _schedHMessageServce: SchedHMessageServiceService,
    private _schedHService: SchedHServiceService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';

    this.queryParamsSubscription = _activatedRoute.queryParams.takeUntil(this.onDestroy$).subscribe(p => {
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
      // No unsaved changes needed from transactions.
      if (p.step === 'transactions') {
        localStorage.removeItem(`form_${this.formType}_saved`);
      }

      //also clear the schedule type so the current component gets destroyed if leaving the form route
      if (p.step !== 'step_3') {
        // this.scheduleType = null;
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

    this.reportTypes = [
        {
          "report_type": 24,
          "report_type_desciption": "24 Hour",
          "report_type_info": "24 Hour Report"
        },
        {
          "report_type": 48,
          "report_type_desciption": "48 Hour",
          "report_type_info": "48 Hour Report"
        }
      ]
    ;

    this.transactionCategories = {
        "transactionCategories": [
          {
            "text": "Independent Expenditures",
            "value": "disbursements",
            "options": [
              {
                "text": "Contributions/Expenditures to Registered Filers",
                "name": "contributions-expenditures-to-registered-filers",
                "value": "contributions-expenditures-to-registered-filers",
                "infoIcon": "TRUE",
                "info": "Language will be provided by RAD",
                "options": [
                  {
                    "type": "radio",
                    "text": "Independent Expenditure",
                    "name": "contributions-expenditures-to-registered-filers",
                    "value": "IE",
                    "infoIcon": "TRUE",
                    "info": "Language will be provided by RAD",
                    "scheduleType": "sched_e"
                  }
                ]
              }
            ]
          }
        ],
        "cashOnHand": {
          "text": "Cash on Hand",
          "value": "cash-on-hand",
          "showCashOnHand": "true"
        },
        "steps": [
          {
            "text": "Type",
            "step": "step_1"
          },
          {
            "text": "Form",
            "step": "step_2"
          },
          {
            "text": "Preview",
            "step": "step_3"
          },
          {
            "text": "Sign",
            "step": "step_4"
          },
          {
            "text": "Submit",
            "step": "step_5"
          }
        ],
        "transactionSearchField": {
          "text": "transaction-search",
          "type": "text",
          "placeholder": "Search for transaction"
        }
    };
    this.transactionCategories = this.transactionCategories.transactionCategories;

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

    //jumpToTransaction is used to pass transaction info from the "Global" All Transactions component 
    //to "Report specific" All Transaction component. Idea is to first load the "Report specific" All Transaction component
    //from "Global" and then if a transaction is passed, then invoke onNotify with that data. 
    if(this.jumpToTransaction){
      this.returnToGlobalAllTransaction = true;
      this.onNotify(this.jumpToTransaction);
    }
    this._messageService.sendMessage({action:'updateHeaderInfo', data: {formType: 'F24'}});
  }

  ngOnDestroy(): void {
    this.onDestroy$.next(true);
    this.queryParamsSubscription.unsubscribe();
    this.routerEventsSubscription.unsubscribe();
    this._messageService.sendMessage({action:'updateHeaderInfo', data: {formType: null}});
  }

   /**
   * Get's message from child components to change the sidebar
   * in the view.
   */
  public switchSidebar(e: boolean): void {
    this.isShowFilters = e;
  }

  public onNotify(e: any): void {
    if (typeof e === 'object') {
      /**
       * This block indicates a user can move to the next
       * step or previous step in a form.
       */
      if (e.hasOwnProperty('form')) {
        if (typeof e.form === 'object') {
          let transactionModel : any = null;
          if(e.transactionDetail && e.transactionDetail.transactionModel){
            transactionModel = e.transactionDetail && e.transactionDetail.transactionModel;
          }

          this.frm = e.form;
          this.direction = e.direction;
          this.previousStep = e.previousStep;
          this._step = e.step;
          this.currentStep = e.step;
          this.transactionCategory = e.transactionCategory;



          this.handleIfStep3(e,transactionModel);

          if(transactionModel){
            this.canContinue(transactionModel);
          }else{
            this.canContinue();  
          }

        } else if (typeof e.form === 'string') {
          if (e.form === this.formType) {
            if (e.hasOwnProperty('transactionCategory')) {
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
      } 
    }
  }


  private handleIfStep3(e: any, transactionModel: any = null) {
    if (this.currentStep === 'step_3') {
      this.mainTransactionTypeText = 'Disbursements';

      if(transactionModel){
        this.transactionType = e.transactionDetail.transactionModel.transactionTypeIdentifier || '';
        this.transactionTypeText = e.transactionDetail.transactionModel.type || '';
      }

      this.setCloneFlag(e);
      this.setScheduleAction(e);
      this.scheduleType = 'sched_e';
      
      if (this.scheduleAction === ScheduleActions.edit || this.scheduleAction === ScheduleActions.view) {
        this._populateFormForEditOrView(e, AbstractScheduleParentEnum.schedEComponent);
        if(transactionModel){
          this.transactionType = e.transactionDetail.transactionModel.transactionTypeIdentifier || '';
          this.transactionTypeText = e.transactionDetail.transactionModel.type || '';
        }
      }
      else {
        this.transactionTypeText = e.transactionTypeText ? e.transactionTypeText : '';
        this.transactionType = e.transactionType ? e.transactionType : '';
      }
    }
  }


  private setScheduleAction(e: any) {
    if (e.action && e.action in ScheduleActions) {
      this.scheduleAction = e.action;
    }
    if (!this.scheduleAction) {
      this.scheduleAction = ScheduleActions.add;
    }

    //this is a workaround since for some reason, f24 component is not sending the scheduleAction to schedE component during ngOnChange trigger 
    this._messageService.sendMessage({action:'forceUpdateSchedEScheduleAction', scheduleAction: this.scheduleAction});
  }

   /**
   * Determines ability to continue.
   */
  private canContinue(transactionModel: any = null): void {
    let reportId = '';
    if (transactionModel && transactionModel.reportId && transactionModel.reportId !== '0' && transactionModel.reportId !== 'undefined') {
      reportId = transactionModel.reportId.toString();
    } else if (this._activatedRoute.snapshot.queryParams && this._activatedRoute.snapshot.queryParams.reportId) {
      reportId = this._activatedRoute.snapshot.queryParams.reportId;
    }

    if (this.frm && this.direction) {

      let queryParamsObj: any = {
        step: this.step,
        edit: this.editMode,
        transactionCategory: this.transactionCategory
      };
      

      if (reportId) {
        queryParamsObj.reportId = reportId;
      }

      if(this._activatedRoute.snapshot.queryParams.amendmentReportId){
        queryParamsObj.amendmentReportId = this._activatedRoute.snapshot.queryParams.amendmentReportId;
        if(this._step === 'transactions'){
          queryParamsObj.reportId = this._activatedRoute.snapshot.queryParams.amendmentReportId;
        }
      }

      if (this.direction === 'next') {
        if (this.frm.valid || this.frm === 'preview') {
          if (this._cloned) {
            queryParamsObj.cloned = this._cloned;
          }
          this.navigateToStep(queryParamsObj); 
        } 
      } else if (this.direction === 'previous') {
        this.navigateToStep(queryParamsObj);         
      }
    }
  }


  private navigateToStep(queryParamsObj: any) {
    this.step = this._step;
    queryParamsObj.step = this.step;
    this._router.navigate([`/forms/form/${this.formType}`], { queryParams: queryParamsObj });
  }

  private _populateFormForEditOrView(e: any, schedule: AbstractScheduleParentEnum) {
    e.transactionDetail.action = this.scheduleAction;
    const emitObject: any = {
      key: 'fullForm',
      abstractScheduleComponent: schedule,
      transactionModel: e.transactionDetail
    };
    this.transactionData = emitObject;
  }

  private setCloneFlag(e: any) {
    if (e.transactionDetail &&
      e.transactionDetail.transactionModel &&
      e.transactionDetail.transactionModel.cloned) {
      this._cloned = true;
    }
    else {
      this._cloned = false;
    }
  }
}
