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
import { ScheduleActions } from '../individual-receipt/individual-receipt.component';

@Component({
  selector: 'app-f3x',
  templateUrl: './f3x.component.html',
  styleUrls: ['./f3x.component.scss'],
  providers: [NgbTooltipConfig],
  encapsulation: ViewEncapsulation.None
})
export class F3xComponent implements OnInit {
  public currentStep: string = 'step_1';
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
  public isShowFilters = false;
  public formType: string = '';
  public scheduleAction: ScheduleActions;

  private _step: string = '';

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
  }

  ngOnInit(): void {
    this.formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this.step = this._activatedRoute.snapshot.queryParams.step;

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

  public onNotify(e): void {
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

          // Pass Transaction Type to individual-receipt
          if (this.currentStep === 'step_3') {
            this.transactionTypeText = e.transactionTypeText ? e.transactionTypeText : '';
            this.transactionType = e.transactionType ? e.transactionType : '';
            // Coming from transactions, the event may contain the transaction data
            // with an action to allow for view or edit.
            if (this.previousStep === 'transactions') {
              // message the child component rather than sending data as input because
              // ngOnChanges fires when the form fields are changed, thereby reseting the
              // fields to the previous value.  Result is fields can't be changed.
              this._f3xMessageService.sendPopulateFormMessage(e.editOrView);
              this.scheduleAction = e.editOrView.action;
            } else {
              this.scheduleAction = ScheduleActions.add;
            }
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
        // } else if (e.hasOwnProperty('showTransactionType')) {
        //   this.direction = e.direction;
        //   this.previousStep = e.previousStep;
        //   this._step = e.step;
        //   this.currentStep = e.step;
        //   this._router.navigate([`/forms/form/${this.formType}`], { queryParams: { step: this.step } });
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

  /**
   * Determines ability to continue.
   */
  public canContinue(): void {
    if (this.frm && this.direction) {
      if (this.direction === 'next') {
        if (this.frm.valid) {
          this.step = this._step;

          this._router.navigate([`/forms/form/${this.formType}`], { queryParams: { step: this.step } });
        } else if (this.frm === 'preview') {
          this.step = this._step;

          this._router.navigate([`/forms/form/${this.formType}`], { queryParams: { step: this.step } });
        }
      } else if (this.direction === 'previous') {
        this.step = this._step;

        this._router.navigate([`/forms/form/${this.formType}`], { queryParams: { step: this.step } });
      }
    }
  }
}
