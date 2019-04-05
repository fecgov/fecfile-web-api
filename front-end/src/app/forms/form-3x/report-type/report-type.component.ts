import { Component, EventEmitter, ElementRef, HostListener, OnInit, Input, Output, ViewChild, ViewEncapsulation, OnDestroy, DoCheck } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { form3x } from '../../../shared/interfaces/FormsService/FormsService';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { ValidateComponent } from '../../../shared/partials/validate/validate.component';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { ReportTypeService } from './report-type.service';
import { ReportTypeMessageService, ReportTypeDateEnum } from './report-type-message.service';
import { form3x_data, Icommittee_form3x_reporttype, form3XReport} from '../../../shared/interfaces/FormsService/FormsService';
import { Subscription } from 'rxjs/Subscription';
import { Message } from '@angular/compiler/src/i18n/i18n_ast';


@Component({
  selector: 'f3x-report-type',
  templateUrl: './report-type.component.html',
  styleUrls: ['./report-type.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class ReportTypeComponent implements OnInit, OnDestroy, DoCheck {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() committeeReportTypes: any = [];
  @Input() selectedReportInfo: any = {};

  public frmReportType: FormGroup;
  public fromDateSelected = false;
  public reportTypeSelected = '';
  public isValidType = false;
  public optionFailed = false;
  public screenWidth = 0;
  public reportType: string = null;
  public toDateSelected = false;
  public tooltipPosition = 'right';
  public tooltipLeft = 'auto';

  private _dueDate: string = null;
  private _formType: string = null;
  private _form3xReportTypeDetails: any = null;
  private _fromDateSelected: string = null;
  private _reportTypeDescripton: string = null;
  private _selectedElectionState: string = null;
  private _selectedElectionDate: string = null;
  private _toDateSelected: string = null;
  private _fromDateUserModified: string = null;
  private _toDateUserModified: string = null;
  private dateChangeSubscription: Subscription;

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _messageService: MessageService,
    private _reportTypeMessageService: ReportTypeMessageService,
    private _formService: FormsService,
    private _reportTypeService: ReportTypeService,
    private _activatedRoute: ActivatedRoute
  ) {
    this._messageService.clearMessage();

    this.dateChangeSubscription = this._reportTypeMessageService.getDateChangeMessage()
      .subscribe(
        message => {
          if (!message) {
            return;
          }
          const dateName = message.name;
          switch (dateName) {
            case ReportTypeDateEnum.fromDate:
              this._fromDateUserModified = message.date;
              break;
            case ReportTypeDateEnum.toDate:
              this._toDateUserModified = message.date;
              break;
            default:
          }
        }
      );
  }

  ngOnInit(): void {

    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this.initUserModFields();

    if (localStorage.getItem(`form_${this._formType}_saved`) === null) {
      localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify(false));
    }

    this._messageService
      .clearMessage();

    this.screenWidth = window.innerWidth;

    if (this.screenWidth < 768) {
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

  ngOnDestroy(): void {
    this.dateChangeSubscription.unsubscribe();
  }

  ngDoCheck(): void {
    if (window.localStorage.getItem(`form_${this._formType}_reset_form`) !== null) {
      const resetForm: boolean = JSON.parse(window.localStorage.getItem(`form_${this._formType}_reset_form`));
    }

    if (Array.isArray(this.committeeReportTypes)) {
      if (this.committeeReportTypes.length >= 1) {
        if (!this.reportTypeSelected) {
          this.frmReportType.controls['reportTypeRadio'].setValue(this.committeeReportTypes[0].report_type);

          this.reportTypeSelected = this.committeeReportTypes[0].report_type;

          this.reportType = this.reportTypeSelected;

          if (this.committeeReportTypes.hasOwnProperty('dates')) {
            this._dueDate = this.committeeReportTypes[0].dates[0].due_date;
            this._fromDateSelected = this.committeeReportTypes[0].dates[0].cvg_start_date;
            this.fromDateSelected = true;
            this._toDateSelected = this.committeeReportTypes[0].dates[0].cvg_end_date;
            this.toDateSelected = true;
          }

          this.status.emit({
            'form': '3x',
            'reportTypeRadio': this.reportTypeSelected
          });

          this.optionFailed = false;
        }
      }
    }

    if (this.selectedReportInfo) {
      if (this.selectedReportInfo.hasOwnProperty('toDate')) {
        if (this._toDateUserModified) {
          this.selectedReportInfo.toDate = this._toDateUserModified;
        }
        if (typeof this.selectedReportInfo.toDate === 'string') {
          if (this.selectedReportInfo.toDate.length >= 1) {
            this._toDateSelected = this.selectedReportInfo.toDate;
            this.toDateSelected = true;
          } else {
            this.toDateSelected = false;
          }
        } else {
          this.toDateSelected = false;
        }
      }

      if (this.selectedReportInfo.hasOwnProperty('fromDate')) {
        if (this._fromDateUserModified) {
          this.selectedReportInfo.fromDate = this._fromDateUserModified;
        }
        if (typeof this.selectedReportInfo.fromDate === 'string') {
          if (this.selectedReportInfo.fromDate.length >= 1) {
            this._fromDateSelected = this.selectedReportInfo.fromDate;
            this.fromDateSelected = true;
          } else {
            this.fromDateSelected = false;
          }
        } else {
          this.fromDateSelected = false;
        }
      }

      if (this.selectedReportInfo.hasOwnProperty('selectedState')) {
        if (typeof this.selectedReportInfo.selectedState === 'string') {
          this._selectedElectionState = this.selectedReportInfo.selectedState;
        } else {
          this._selectedElectionState = null;
        }
      }

      if (this.selectedReportInfo.hasOwnProperty('selectedElectionDate')) {
        if (typeof this.selectedReportInfo.selectedElectionDate === 'string') {
          this._selectedElectionDate = this.selectedReportInfo.selectedElectionDate;
        } else {
          this._selectedElectionDate = null;
        }
      }

      if (this.selectedReportInfo.hasOwnProperty('dueDate')) {
        if (typeof this.selectedReportInfo.dueDate === 'string') {
          if (this.selectedReportInfo.dueDate.length >= 1) {
            this._dueDate = this.selectedReportInfo.dueDate;
          }
        } else {
          this._dueDate = null;
        }
      }

      if (this.selectedReportInfo.hasOwnProperty('reportTypeDescription')) {
        if (typeof this.selectedReportInfo.reportTypeDescription === 'string') {
          if (this.selectedReportInfo.reportTypeDescription.length >= 1) {
            this._reportTypeDescripton = this.selectedReportInfo.reportTypeDescription;
          }
        } else {
          this._reportTypeDescripton = null;
        }
      }
    }
  }


  @HostListener('window:resize', ['$event'])
  onResize(event) {
    this.screenWidth = event.target.innerWidth;

    if (this.screenWidth < 768) {
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
    if (e.target.checked) {
      this.initUserModFields();
      this.reportTypeSelected = this.frmReportType.get('reportTypeRadio').value;
      this.optionFailed = false;
      this.reportType = this.reportTypeSelected;
      const dataReportType: string = e.target.getAttribute('data-report-type');

      if (dataReportType !== 'S') {
        this.toDateSelected = true;
        this.fromDateSelected = true;
      } else {
        this.toDateSelected = false;
        this.fromDateSelected = false;
      }

      this.status.emit({
        'form': '3x',
        'reportTypeRadio': this.reportTypeSelected
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
    if (this.frmReportType.valid) {
        this.optionFailed = false;
        this.isValidType = true;

        this._form3xReportTypeDetails.reportType = this.frmReportType.get('reportTypeRadio').value;

        this._form3xReportTypeDetails.cvgStartDate = this._formatDate(this._fromDateSelected);
        this._form3xReportTypeDetails.cvgEndDate = this._formatDate(this._toDateSelected);
        this._form3xReportTypeDetails.dueDate = this._formatDate(this._dueDate);
        this._form3xReportTypeDetails.reportTypeDescription = this._reportTypeDescripton;
        this._form3xReportTypeDetails.election_state = this._selectedElectionState;
        this._form3xReportTypeDetails.election_date = this._formatDate(this._selectedElectionDate);
        this._form3xReportTypeDetails.regular_special_report_ind = this.selectedReportInfo.regular_special_report_ind;

        localStorage.setItem('form_3X_report_type', JSON.stringify(this._form3xReportTypeDetails));

        this._reportTypeService
          .saveReport(this._formType, 'Saved')
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
      window.scrollTo(0, 0);

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

  public log(val) {
    console.log('val: ', val);
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
    try {
      const dateArr = date.split('-');
      const month: string = dateArr[1];
      const day: string = dateArr[2];
      const year: string = dateArr[0].replace('2018', '2019');

      /// return `${year}-${month}-${day}`;

      return `${month}/${day}/${year}`;
    } catch (e) {
      return '';
    }
  }


  private initUserModFields() {
    this._fromDateUserModified = null;
    this._toDateUserModified = null;
  }
}
