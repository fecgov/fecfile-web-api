import { Component, EventEmitter, ElementRef, HostListener, OnInit, Input, Output, ViewChild, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { form3x } from '../../../shared/interfaces/FormsService/FormsService';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { ValidateComponent } from '../../../shared/partials/validate/validate.component';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { ReportTypeService } from './report-type.service';
import { form3x_data, Icommittee_form3x_reporttype, form3XReport} from '../../../shared/interfaces/FormsService/FormsService';


@Component({
  selector: 'f3x-report-type',
  templateUrl: './report-type.component.html',
  styleUrls: ['./report-type.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class ReportTypeComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() committeeReportTypes: any = [];

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

  private _dueDate: string = null;
  private _formType: string = null;
  private _form3xReportTypeDetails: any = null;
  private _fromDateSelected: string = null;
  private _reportTypeDescripton: string = null;
  private _selectedElectionState: string = null;
  private _selectedElectionDate: string = null;
  private _toDateSelected: string = null;

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _messageService: MessageService,
    private _formService: FormsService,
    private _reportTypeService: ReportTypeService,
    private _activatedRoute: ActivatedRoute
  ) {
    this._messageService.clearMessage();
  }

  ngOnInit(): void {

    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');

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

    this._form3xReportTypeDetails = {
      cmteId: '',
      reportId: '',
      formType: '3X',
      electionCode: '',
      reportType: '',
      reportTypeDescription: '',
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
            if (typeof res.toDate === 'string') {
              if (res.toDate.length >= 1) {
                this.toDateSelected = true;
                this._toDateSelected = res.toDate;
              } else {
                this.toDateSelected = false;
              }
            }
            if (typeof res.fromDate === 'string') {
              if (res.fromDate.length >= 1) {
                this._fromDateSelected = res.fromDate;
                this.fromDateSelected = true;
              } else {
                this.fromDateSelected = false;
              }
            }

            if (typeof res.selectedState === 'string') {
              if (res.selectedState.length >= 1) {
                this._selectedElectionState = res.selectedState;
              }
            } else {
              this._selectedElectionState = null;
            }

            if (typeof res.selectedElectionDate === 'string') {
              if (res.selectedElectionDate.length >= 1) {
                this._selectedElectionDate = res.selectedElectionDate;
              }
            } else {
              this._selectedElectionDate = null;
            }

            if (typeof res.dueDate === 'string') {
              if (res.dueDate.length >= 1) {
                this._dueDate = res.dueDate;
              }
            } else {
              this._dueDate = null;
            }

            if (typeof res.reportTypeDescription === 'string') {
              if (res.reportTypeDescription.length >= 1) {
                this._reportTypeDescripton = res.reportTypeDescription;
              }
            } else {
              this._reportTypeDescripton = null;
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

        this._form3xReportTypeDetails.reportType = this.frmReportType.get('reportTypeRadio').value;

        if (this._selectedElectionState !== null) {
          this._form3xReportTypeDetails.stateOfElection = this._selectedElectionState;
        }

        this._form3xReportTypeDetails.cvgStartDate = this._formatDate(this._fromDateSelected);
        this._form3xReportTypeDetails.cvgEndDate = this._formatDate(this._toDateSelected);
        this._form3xReportTypeDetails.dueDate = this._dueDate;
        this._form3xReportTypeDetails.reportTypeDescription = this._reportTypeDescripton;

        console.log('this._form3xReportTypeDetails: ', this._form3xReportTypeDetails);

        localStorage.setItem('Form_3X_Report_Type', JSON.stringify(this._form3xReportTypeDetails));

        this._reportTypeService
          .saveReport(this._formType)
          .subscribe(res => {
            if (res) {
              this.status.emit({
                form: this.frmReportType,
                direction: 'next',
                step: 'step_2',
                previousStep: 'step_1'
              });
            }
          });

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

  /**
   * Toggles the tooltip.
   *
   * @param      {Element}  tooltip  The tooltip
   */
  public toggleToolTip(tooltip): void {
    if (tooltip.isOpen()) {
      tooltip.close();
    } else {
      tooltip.open();
    }
  }

  /**
   * Cancels form 3x.
   */
  public cancel(): void {
    this._router.navigateByUrl('/dashboard');
  }


  /**
   * Changes format of date from m/d/yyyy to yyyy-m-d.
   *
   * @param      {string}  date    The date
   * @return     {string}  The new formatted date.
   */
  private _formatDate(date: string): string {
    const today = new Date(date);
    const year: number = today.getFullYear();
    const month: string = (1 + today.getMonth()).toString().padStart(2, '0');
    const day: string = today.getDate().toString().padStart(2, '0')

    return `${year}-${month}-${day}`;
  }

}
