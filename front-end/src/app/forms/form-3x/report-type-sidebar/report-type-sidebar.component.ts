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
      if (this.selectedReport.hasOwnProperty('report_type_desciption')) {
        if (typeof this.selectedReport.report_type_desciption === 'string') {
          this._reportTypeDescription = this.selectedReport.report_type_desciption;
        }
      }
      const newReportSelected = this._previousReportTypeDescription !==
        this._reportTypeDescription;

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
                    console.log('dates[0].cvg_start_date: ', dates[0].cvg_start_date);
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

                  // if (Array.isArray(dates)) {
                  //   if (dates.length > 0) {
                  //     if (dates[0].cvg_start_date) {
                  //       this.fromDate = dates[0].cvg_start_date.replace('2018', 2019);
                  //     }
                  //     if (dates[0].cvg_end_date) {
                  //       this.toDate = dates[0].cvg_end_date.replace('2018', 2019);
                  //     }
                  //     if (dates[0].due_date) {
                  //       this.dueDate = dates[0].due_date;
                  //     }
                  //   }
                  // }
                }
              }
            }
          } else {
            this.fromDate = '';
            this.toDate = '';
            if (this.selectedReport.hasOwnProperty('election_state')) {
              this.electionStates =  this.selectedReport.election_state;
            }

            if (this._selectedElectionDates !== null) {
              this.fromDate = this._selectedElectionDates.fromDate;
              this.toDate = this._selectedElectionDates.toDate;
            }
          }
        } // isArray(this.selectedReport.election_state)

        this._previousReportTypeDescription = this._reportTypeDescription;

        // smahal: until API exists to get fromDate from the previous filing
        // when from date is null, allow null from date to go through.
        // if (this.fromDate && this.toDate) {
        if ((this.fromDate && this.toDate) || (!this.fromDate && this.toDate)) {
          let message: any = null;

          if (this._selectedState && this._selectedElectionDate) {
            message = {
              'form': '3x',
              'selectedState': this._selectedState,
              'selectedElectionDate': this._selectedElectionDate,
              'toDate': this.toDate,
              'fromDate': this.fromDate,
              'dueDate': this.dueDate,
              'reportTypeDescription': this._reportTypeDescription,
              'regular_special_report_ind': this.selectedReport.regular_special_report_ind
            };

            // setTimeout was causing a loop between several components.
            // setTimeout(() => {
              // this.status.emit(message);
            // }, 100);
            // this.status.emit(message);

          } else if (!this._selectedState && !this._selectedElectionDate) {
            message = {
              'form': '3x',
              'toDate': this.toDate,
              'fromDate': this.fromDate,
              'dueDate': this.dueDate,
              'reportTypeDescription': this._reportTypeDescription,
              'regular_special_report_ind': this.selectedReport.regular_special_report_ind
            };
          }
          this.status.emit(message);
        } else {
          this.status.emit({
              'form': '3x',
              'toDate': '',
              'fromDate': '',
              'dueDate': '',
              'reportTypeDescription': '',
              'regular_special_report_ind': ''
          });
        }
      } // hasOwnProperty('election_state')

      if (localStorage.getItem('form_3X_report_type') !== null) {
        const form3xReportType: any = JSON.parse(localStorage.getItem('form_3X_report_type'));

        console.log('form3xReportType: ', form3xReportType);

        // The local storage report is saved when next button is clicked.
        // If user returns to step 1 and selects a different report, do not
        // proceed setting the fields.
        if (!this.checkSelectedMatchesSpecial(form3xReportType)) {
          return;
        }

        if (form3xReportType.hasOwnProperty('regular_special_report_ind')) {
          if (typeof form3xReportType.regular_special_report_ind === 'string') {
            if (form3xReportType.regular_special_report_ind === 'S') {
              console.log('special report selected: ');
              let selectedState: any = null;

              selectedState = this.selectedReport.election_state.find(el => {
                return el.state === form3xReportType.election_state;
              });

              if (selectedState) {
                if (selectedState.hasOwnProperty('dates')) {
                  if (Array.isArray(selectedState.dates)) {
                    this.electionDates = selectedState.dates;
                  }
                }
              }

              if (this.electionDates) {
                this.electionDates.forEach(el => {
                  if (el.cvg_start_date) {
                    el.cvg_start_date = el.cvg_start_date.replace('2018', '2019');
                  }
                  el.cvg_end_date = el.cvg_end_date.replace('2018', '2019');
                  el.due_date = el.due_date.replace('2018', '2019');
                  el.election_date = el.election_date.replace('2018', '2019');
                });
              }

              this.fromDate = this._deFormatDate(form3xReportType.cvgStartDate);
              this.toDate = this._deFormatDate(form3xReportType.cvgEndDate);

              this.selectedElectionState = form3xReportType.election_state;
              this.selectedElecetionDate = form3xReportType.election_date;
            }
          }
        }
      }
    }
  }


  /**
   * Check if the selected Report matches the Report from local storage.
   * 
   * @param form3xReportType the F3X Report Type from local storage.
   * @returns true if the report type from storage matches the selected report type.
   */
  private checkSelectedMatchesSpecial(form3xReportType: any): boolean {
    if (form3xReportType.hasOwnProperty('reportType')) {
      if (typeof form3xReportType.reportType === 'string') {
        if (form3xReportType.reportType === this.selectedReport.reportType) {
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
