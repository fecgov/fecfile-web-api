import { Component, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { forkJoin, of, interval } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { form3x_data, form3XReport } from '../../../shared/interfaces/FormsService/FormsService';
import { selectedElectionState, selectedElectionDate, selectedReportType } from '../../../shared/interfaces/FormsService/FormsService';
import { MessageService } from '../../../shared/services/MessageService/message.service';

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
  public reportsLoading: boolean = true;
  public reportTypes: any = {};
  public reportTypeIndicator: any = {};
  public reportType: any = null;
  public selectedReportType: any = {};
  public selectedReport: any = {};
  public regularReports: boolean = false;
  public specialReports: boolean = false;

  private _step: string = '';
  private _formType: string = '';

  constructor(
    private _formService: FormsService,
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _config: NgbTooltipConfig,
    private _router: Router,
    private _activatedRoute: ActivatedRoute

  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this.step = this._activatedRoute.snapshot.queryParams.step;

    this._formService
      .getreporttypes(this._formType)
      .subscribe(res => {
        if (typeof res === 'object') {
          if (Array.isArray(res.report_type)) {
            this.reportTypes  = res.report_type;

            console.log('this.reportTypes: ', this.reportTypes);

            this.reportsLoading = false;

            this._setReports();
          }
        }
    });
  }

  ngDoCheck(): void {
    if(this._activatedRoute.snapshot.queryParams.step !== this.currentStep) {
      this.currentStep = this._activatedRoute.snapshot.queryParams.step;
      this.step = this._activatedRoute.snapshot.queryParams.step;
    }
  }

  /**
   * Sets the reports.
   */
  private _setReports(): void {
    if (typeof this.reportType === 'undefined' || this.reportType === null) {
      if (typeof this.reportTypes !== 'undefined' && this.reportTypes !== null) {
        this.selectedReportType  = this.reportTypes.find(x => x.default_disp_ind === 'Y');
        if (typeof this.selectedReportType === 'object') {
          if (typeof this.selectedReportType.regular_special_report_ind === 'string') {
            this.reportTypeIndicator = this.selectedReportType.regular_special_report_ind;
          }
        } else {
          if (Array.isArray(this.reportTypes)) {
            this.reportType  = this.reportTypes[0].report_type;
            this.selectedReportType = this.reportTypes.find(x => x.report_type===this.reportType);
            if (typeof this.selectedReportType === 'object') {
              this.reportTypeIndicator= this.selectedReportType.regular_special_report_ind;
            }
          }
        }
        if (typeof this.selectedReportType === 'object') {
          if (typeof this.selectedReportType.regular_special_report_ind === 'string') {
            if (this.selectedReportType.regular_special_report_ind === 'S') {
              this.specialReports = true;
            } else {
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

    console.log('this.selectedReport:', this.selectedReport);
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
      if (e.frm) {
        this.frm = e.form;

        this.direction = e.direction;

        this.previousStep = e.previousStep;

        this._step = e.step;

        this.currentStep = e.step;

        this.canContinue();
      } else if (typeof e.reportTypeRadio === 'string') {
        this._setCoverageDates(e.reportTypeRadio);
      }
    }
  }

  /**
   * Determines ability to continue.
   */
  public canContinue(): void {
    if(this.frm && this.direction) {
      if(this.direction === 'next') {
        if(this.frm.valid) {
          this.step = this._step;

          this._router.navigate(['/forms/form/3X'], { queryParams: { step: this.step } });
        } else if(this.frm === 'preview') {
          this.step = this._step;

          this._router.navigate(['/forms/form/3X'], { queryParams: { step: this.step } });
        }
      } else if(this.direction === 'previous') {
        this.step = this._step;

        this._router.navigate(['/forms/form/3X'], { queryParams: { step: this.step } });
      }
    }
  }
}
