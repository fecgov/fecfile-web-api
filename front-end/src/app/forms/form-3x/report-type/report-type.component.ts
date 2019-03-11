import { Component, EventEmitter, ElementRef, HostListener, OnInit, Input, Output, ViewChild, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { form3x } from '../../../shared/interfaces/FormsService/FormsService';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { ValidateComponent } from '../../../shared/partials/validate/validate.component';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { form3x_data, Icommittee_form3x_reporttype, form3XReport} from '../../../shared/interfaces/FormsService/FormsService';


@Component({
  selector: 'f3x-report-type',
  templateUrl: './report-type.component.html',
  styleUrls: ['./report-type.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class ReportTypeComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  public committeeReportTypes: any = null;
  public frmReportType: FormGroup;
  public fromDateSelected: boolean = false;
  public reportTypeSelected: string = '';
  public isValidType: boolean = false;
  public optionFailed: boolean = false;
  public screenWidth: number = 0;
  public reportType: string = null;
  public toDateSelected: boolean = false;
  public tooltipPosition: string = 'right';
  public tooltipLeft: string = 'auto';

  private _formType: string = null;
  private _form3xDetails: any = null;

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _messageService: MessageService,
    private _formService:FormsService,
    private _activatedRoute: ActivatedRoute
  ) {
    this._messageService.clearMessage();
  }

  ngOnInit(): void {

    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this._formService
      .getreporttypes(this._formType)
      .subscribe(res => {
        if (res) {
         this.committeeReportTypes = res.report_type;
        }
      });

    this._messageService
      .clearMessage();

    this.screenWidth = window.innerWidth;

    if(this.screenWidth < 768) {
      this.tooltipPosition = 'bottom';
      this.tooltipLeft = '0';
    } else if (this.screenWidth >= 768) {
      this.tooltipPosition = 'right';
      this.tooltipLeft = 'auto';
    }

    this.frmReportType = this._fb.group({
      reportTypeRadio: ['', Validators.required]
    });

    this._form3xDetails = {
      cmteId: '',
      reportId: '',
      formType: '3x',
      electionCode: '',
      reportType: '',
      regularSpecialReportInd: '',
      stateOfElection: '',
      electionDate: '',
      cvgStartDate: '',
      cvgEndDate: '',
      dueDate: '',
      amend_Indicator: '',
      coh_bop: '0'
    };
  }

  ngDoCheck(): void {
    this._messageService
      .getMessage()
      .subscribe(res => {
        if (typeof res.form === 'string') {
          if (res.form === '3x') {
            console.log('res: ', res);
            if (typeof res.toDate === 'string') {
              if (res.toDate.length >= 1) {
                this.toDateSelected = true;
              }
            }
            if (typeof res.fromDate === 'string') {
              if (res.fromDate.length >= 1) {
                this.fromDateSelected = true;
              }
            }
          }
        }
      });
  }

  @HostListener('window:resize', ['$event'])
  onResize(event) {
    this.screenWidth = event.target.innerWidth;

    if(this.screenWidth < 768) {
      this.tooltipPosition = 'bottom';
      this.tooltipLeft = '0';
    } else if (this.screenWidth >= 768) {
      this.tooltipPosition = 'right';
      this.tooltipLeft = 'auto';
    }
  }

  /**
   * TODO:
   * Get the regularReport and specialReport variables working.
   */

  /**
   * Updates the type selected.
   *
   * @param      {Object}  e   The event object.
   */
  public updateTypeSelected(e): void {
    if(e.target.checked) {
      this.reportTypeSelected = this.frmReportType.get('reportTypeRadio').value;
      this.optionFailed = false;
      this.reportType = this.reportTypeSelected;

      this.status.emit({
        reportTypeRadio: this.reportTypeSelected
      });
    } else {
      this.reportTypeSelected = '';
      this.optionFailed = true;
    }
  }

  /**
   * Validates the type selected form.
   *
   */
  public doValidateReportType() {
    if (this.frmReportType.get('reportTypeRadio').value) {
        this.optionFailed = false;
        this.isValidType = true;

        this.status.emit({
          form: this.frmReportType,
          direction: 'next',
          step: 'step_2',
          previousStep: 'step_1'
        });

        //this.saveReport();
        return 1;
    } else {
      this.optionFailed = true;
      this.isValidType = false;

      this.status.emit({
        form: this.frmReportType,
        direction: 'next',
        step: 'step_2',
        previousStep: ''
      });

      return 0;
    }
  }

  public toggleToolTip(tooltip): void {
    if (tooltip.isOpen()) {
      tooltip.close();
    } else {
      tooltip.open();
    }
  }

  public cancel(): void {
    this._router.navigateByUrl('/dashboard');
  }

}
