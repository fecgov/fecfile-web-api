import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { selectedElectionState, selectedElectionDate, selectedReportType } from '../../../shared/interfaces/FormsService/FormsService';
import { ReportTypeMessageService, ReportTypeDateEnum } from '../report-type/report-type-message.service';
import { Subscription } from 'rxjs/Subscription';

@Component({
  selector: 'report-type-sidebar',
  templateUrl: './report-type-sidebar.component.html',
  styleUrls: ['./report-type-sidebar.component.scss'],
  providers: [NgbTooltipConfig]
})
export class ReportTypeSidebarComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() specialReports: boolean = false;
  @Input() regularReports: boolean = false;
  @Input() selectedReport: any = null;
  @Input() selectedreporttype:  selectedReportType;

  public dueDate: string = null;
  public electionStates: any = null;
  public electionDates: any = null;
  public frmReportSidebar: FormGroup;
  public fromDate: string = null;
  public toDate: string = null;
  public selectedElectionState: string = null;
  public selectedElecetionDate: string = null;

  private _reportTypeDescription: string = null;
  private _previousReportTypeDescription: string = null;
  private _selectedElectionDates: any = null;
  private _selectedState: string = null;
  private _selectedElectionDate: string = null;

  constructor(
    private _fb: FormBuilder,
    private _config: NgbTooltipConfig,
    private _formService: FormsService,
    private _messageService: MessageService,
    private _reportTypeMessageService: ReportTypeMessageService,
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this.frmReportSidebar = this._fb.group({});
  }

  ngDoCheck(): void {
    if (this.selectedReport !== null) {
      console.log('this.selectedReport: ', this.selectedReport);
      if (this.selectedReport.hasOwnProperty('report_type_desciption')) {
        if (typeof this.selectedReport.report_type_desciption === 'string') {
          this._reportTypeDescription = this.selectedReport.report_type_desciption;
        }
      }
      const newReportSelected = this._previousReportTypeDescription !==
        this._reportTypeDescription;

      if (this.selectedReport.hasOwnProperty('regular_special_report_ind')) {
        if (typeof this.selectedReport.regular_special_report_ind === 'string') {
          if (this.selectedReport.regular_special_report_ind === 'S') {
            if (this.selectedReport.hasOwnProperty('election_state')) {
              if (Array.isArray(this.selectedReport.election_state)) {
                if (this.selectedReport.election_state.length === 1) {
                  const electionState: any = this.selectedReport.election_state[0];

                  this.fromDate = '';
                  this.toDate = '';
                  if (electionState.hasOwnProperty('state') && electionState.hasOwnProperty('state')) {
                    this.electionStates = [];
                    this.electionStates[0] = {
                      'state': electionState.state,
                      'state_description': electionState.state_description,
                    };
                  }
                } else {
                  this.fromDate = '';
                  this.toDate = '';
                  if (this.selectedReport.hasOwnProperty('election_state')) {
                    this.electionStates =  this.selectedReport.election_state;
                  }                    
                }
              } // Array.isArray(this.selectedReport.election_state)
            } // this.selectedReport.hasOwnProperty('election_state')
          } else {
            if (this.selectedReport.hasOwnProperty('election_state')) {
              if (Array.isArray(this.selectedReport.election_state)) {
                if (this.selectedReport.election_state.length === 1) {
                  // Apply the dates from the newly selected report
                  // Don't set the dates if the change trigger is from the date itself.
                  if (newReportSelected) {
                    this.fromDate = '';
                    this.toDate = '';
                    this._selectedElectionDates = null;
                    if (this.selectedReport.election_state[0]['dates']) {
                      if (Array.isArray(this.selectedReport.election_state[0].dates)) {
                        let dates: any = this.selectedReport.election_state[0].dates;

                        if (Array.isArray(dates)) {
                          if (
                            typeof dates[0].cvg_start_date === 'string' && dates[0].cvg_start_date !== null && 
                            typeof dates[0].cvg_end_date === 'string' && dates[0].cvg_end_date !== null &&
                            typeof dates[0].due_date === 'string' && dates[0].due_date.length !== null
                          ) {
                            this.fromDate = dates[0].cvg_start_date.replace('2018', 2019);
                            this.toDate = dates[0].cvg_end_date.replace('2018', 2019);
                            this.dueDate = dates[0].due_date;                      
                          }
                        }
                      }
                    }
                  }
                } // this.selectedReport.election_state.length === 1
              } // Array.isArray(this.selectedReport.election_state)
            } // this.selectedReport.hasOwnProperty('election_state')              
          } // this.selectedReport.regular_special_report_ind === 'S' 
        } // typeof this.selectedReport.regular_special_report_ind === 'string'
      } // this.selectedReport.hasOwnProperty('regular_special_report_ind')      

    } // this.selectedReport !== null
  }


  /**
   * Check if the selected Report matches the Report from local storage.
   * 
   * @param form3XReportType the F3X Report Type from local storage.
   * @returns true if the report type from storage matches the selected report type.
   */
  private checkSelectedMatchesSpecial(form3XReportType: any): boolean {
    if (form3XReportType.hasOwnProperty('reportType')) {
      if (typeof form3XReportType.reportType === 'string') {
        if (form3XReportType.reportType === this.selectedReport.reportType) {
          return true;
        }
      }
    }
    return false;
  }


  /**
   * Changes format of date from yyyy-m-d to m/d/yyyy.
   *
   * TODO put in utilService
   *
   * @param      {string}  date    The date
   * @return     {string}  The new formatted date.
   */
  private _deFormatDate(date: string): string {
    try {
      const dateArr = date.split('/');
      const month: string = dateArr[0];
      const day: string = dateArr[1];
      const year: string = dateArr[2].replace('2018', '2019');

      return `${year}-${month}-${day}`;
    } catch (e) {
      return '';
    }
  }

  public selectStateChange(e): void {
    let selectedVal: string = e.target.value;
    let selectedState: any = null;

    this._selectedState = selectedVal;

    if (selectedVal !== '0') {
      if (this.selectedReport.hasOwnProperty('election_state')) {
        selectedState = this.selectedReport.election_state.find(el => {
          return el.state === selectedVal;
        });

        if (selectedState.hasOwnProperty('dates')) {
          if (Array.isArray(selectedState.dates)) {
            this.electionDates = selectedState.dates;
          }
        }
      }
    }
  }

  public selectElectionDateChange(e): void {
    console.log('selectElectionDateChange: ');
    const selectedOption: any = e.target[e.target.selectedIndex];

    this._selectedElectionDate =  e.target.value;

    this._selectedElectionDates = {
      'fromDate': selectedOption.getAttribute('data-startdate'),
      'toDate': selectedOption.getAttribute('data-enddate'),
      'dueDate': selectedOption.getAttribute('data-duedate')
    };

    this.fromDate = selectedOption.getAttribute('data-startdate');
    this.toDate = selectedOption.getAttribute('data-enddate');
    this.dueDate = selectedOption.getAttribute('data-duedate');

    this._selectedElectionDate = e.target.value;
  }

  public fromDateChange(date: string) {
    this.fromDate = date;

    // This is an undesirable way to fix a issue with timing change detection
    setTimeout(() => {
      this._reportTypeMessageService.sendDateChangeMessage(
        {
          name: ReportTypeDateEnum.fromDate,
          date: date
        }
      );
    }, 200);
  }

  public toDateChange(date: string) {
    this.toDate = date;

    // This is an undesirable way to fix a issue with timing change detection
    setTimeout(() => {
      this._reportTypeMessageService.sendDateChangeMessage(
        {
          name: ReportTypeDateEnum.toDate,
          date: date
        }
      );
    }, 200);
  }
}
