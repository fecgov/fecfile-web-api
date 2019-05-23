import { Component, EventEmitter, ElementRef, Input, OnInit, Output } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import {
  selectedElectionState,
  selectedElectionDate,
  selectedReportType
} from '../../../shared/interfaces/FormsService/FormsService';
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
  @Input() selectedreporttype: selectedReportType;

  public dueDate: string = null;
  public electionStates: any = null;
  public electionDates: any = null;
  public frmReportSidebar: FormGroup;
  public fromDate: string = null;
  public toDate: string = null;
  public selectedElectionState: string = null;
  public selectedElecetionDate: string = null;

  private _reportTypeDescription: string = null;
  private _formType: string = null;
  private _newReportSelected: boolean = false;
  private _previousReportTypeDescription: string = null;
  private _previousReportSelected: string = null;
  private _previousStateSelected: string = null;
  private _reportType: string = null;
  private _selectedElectionDates: any = null;
  private _selectedState: string = null;
  private _selectedElectionDate: string = null;

  constructor(
    private _fb: FormBuilder,
    private _config: NgbTooltipConfig,
    private _formService: FormsService,
    private _messageService: MessageService,
    private _reportTypeMessageService: ReportTypeMessageService,
    private _activatedRoute: ActivatedRoute
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.frmReportSidebar = this._fb.group({});
  }

  ngDoCheck(): void {
    if (this.selectedReport !== null) {
      console.log('this.selectedReport: ', this.selectedReport);
      if (this.selectedReport.hasOwnProperty('regular_special_report_ind')) {
        if (typeof this.selectedReport.regular_special_report_ind === 'string') {
          this._reportType = this.selectedReport.regular_special_report_ind;
        }
      }

      if (this.selectedReport.hasOwnProperty('report_type')) {
        if (typeof this.selectedReport.report_type === 'string') {
          if (this._previousReportSelected === null) {
            this._previousReportSelected = this.selectedReport.report_type;
          }
        }

        if (this._previousReportSelected !== this.selectedReport.report_type) {
          this._newReportSelected = true;
        }
      }

      if (this.selectedReport.hasOwnProperty('regular_special_report_ind')) {
        if (typeof this.selectedReport.regular_special_report_ind === 'string') {
          if (this.selectedReport.regular_special_report_ind === 'S') {
            // special reports
            if (this.selectedReport.hasOwnProperty('election_state')) {
              if (Array.isArray(this.selectedReport.election_state)) {
                if (this.selectedReport.election_state.length === 1) {
                  const electionState: any = this.selectedReport.election_state[0];

                  if (!this.selectedElectionState && !this.selectedElecetionDate) {
                    if (this._newReportSelected) {
                      if (this.fromDate && this.toDate) {
                        this.toDate = '';
                        this.fromDate = '';
                      }
                    }
                  }

                  if (electionState.hasOwnProperty('state') && electionState.hasOwnProperty('state')) {
                    this.electionStates = [];
                    this.electionStates[0] = {
                      state: electionState.state,
                      state_description: electionState.state_description
                    };
                  }
                } else {
                  if (this.selectedElectionState && !this.selectedElecetionDate) {
                    this.selectedElectionState = null;

                    if (this._newReportSelected) {
                      if (this.fromDate && this.toDate) {
                        this.toDate = '';
                        this.fromDate = '';
                      }
                    }
                  }

                  if (this.selectedReport.hasOwnProperty('election_state')) {
                    this.electionStates = this.selectedReport.election_state;
                  }
                }
              } // Array.isArray(this.selectedReport.election_state)
            } // this.selectedReport.hasOwnProperty('election_state')
          } else {
            // regular reports
            if (this.selectedReport.hasOwnProperty('election_state')) {
              if (Array.isArray(this.selectedReport.election_state)) {
                if (this.selectedReport.election_state.length === 1) {
                  // Apply the dates from the newly selected report
                  // Don't set the dates if the change trigger is from the date itself.
                  // if (newReportSelected) {
                  if (this._newReportSelected) {
                    this.fromDate = '';
                    this.toDate = '';
                  }
                  this._selectedElectionDates = null;
                  if (this.selectedReport.election_state[0]['dates']) {
                    if (Array.isArray(this.selectedReport.election_state[0].dates)) {
                      let dates: any = this.selectedReport.election_state[0].dates;

                      if (Array.isArray(dates)) {
                        if (
                          typeof dates[0].cvg_start_date === 'string' &&
                          dates[0].cvg_start_date !== null &&
                          typeof dates[0].cvg_end_date === 'string' &&
                          dates[0].cvg_end_date !== null &&
                          typeof dates[0].due_date === 'string' &&
                          dates[0].due_date.length !== null
                        ) {
                          this.fromDate = dates[0].cvg_start_date;
                          this.toDate = dates[0].cvg_end_date;
                          this.dueDate = dates[0].due_date;

                          this._messageService.sendMessage({
                            form: true,
                            type: this._formType,
                            reportType: 'regular',
                            electionDates: [
                              {
                                cvg_end_date: this.toDate,
                                cvg_start_date: this.fromDate,
                                due_date: this.dueDate
                              }
                            ]
                          });
                        }
                      }
                    }
                  }
                  // }
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

    if (this._newReportSelected) {
      this._newReportSelected = false;
    }

    this._selectedState = selectedVal;
    this.selectedElectionState = this._selectedState;

    if (selectedVal !== '0') {
      if (this.selectedReport.hasOwnProperty('election_state')) {
        if (Array.isArray(this.selectedReport.election_state)) {
          if (this.selectedReport.election_state.length === 1) {
            selectedState = this.selectedReport.election_state[0];

            if (this._previousStateSelected === null) {
              this._previousStateSelected = selectedState.state;
            }

            if (selectedState.state === selectedVal) {
              if (selectedState.hasOwnProperty('dates')) {
                if (Array.isArray(selectedState.dates)) {
                  this.electionDates = [];
                  this.electionDates[0] = selectedState.dates[0];
                }
              }
            }
          } else if (this.selectedReport.election_state.length > 1) {
            selectedState = this.selectedReport.election_state.find(el => {
              return el.state === selectedVal;
            });

            if (this._previousStateSelected === null) {
              this._previousStateSelected = selectedState.state;
            }

            if (this._previousStateSelected !== null && this._previousStateSelected !== selectedState.state) {
              this.fromDate = '';
              this.toDate = '';
            }

            if (selectedState.hasOwnProperty('dates')) {
              if (Array.isArray(selectedState.dates)) {
                this.electionDates = selectedState.dates;
              }
            }
          } // this.selectedReport.election_state.length
        } // Array.isArray(this.selectedReport.election_state)
      } // this.selectedReport.hasOwnProperty('election_state')
    } // selectedVal !== '0'
  }

  public selectElectionDateChange(e): void {
    const selectedOption: any = e.target[e.target.selectedIndex];

    this._selectedElectionDate = e.target.value;

    const fromDate: string = selectedOption.getAttribute('data-startDate');
    const toDate: string = selectedOption.getAttribute('data-endDate');
    const dueDate: string = selectedOption.getAttribute('data-dueDate');

    this._selectedElectionDates = {
      fromDate: fromDate,
      toDate: toDate,
      dueDate: dueDate
    };

    this.fromDate = fromDate;
    this.toDate = toDate;
    this.dueDate = dueDate;

    this._messageService.sendMessage({
      form: true,
      type: this._formType,
      reportType: this._reportType,
      electionDates: this.electionDates
    });

    this._selectedElectionDate = e.target.value;
  }

  /**
   * Executed when from date field is changed.
   *
   * @param      {string}  date    The date
   */
  public fromDateChange(date: string) {
    console.log('formDateChange: ');
    console.log('date: ', date);

    if (this.fromDate !== null) {
      if (date !== this.fromDate) {
        console.log('Invalid date for report selected: ');
      } else {
        this.fromDate = date;
      }
    } else {
      this.fromDate = date;
    }

    this._messageService.sendMessage({
      form: true,
      type: this._formType,
      reportType: this._reportType,
      electionDates: [
        {
          cvg_end_date: this.toDate,
          cvg_start_date: this.fromDate,
          due_date: this.dueDate,
          election_date: this.selectedElecetionDate
        }
      ]
    });
  }

  /**
   * Executed when the to date field is changed.
   *
   * @param      {string}  date    The date
   */
  public toDateChange(date: string) {
    this.toDate = date;

    this._messageService.sendMessage({
      form: true,
      type: this._formType,
      reportType: 'special',
      electionDates: [
        {
          cvg_end_date: this.toDate,
          cvg_start_date: this.fromDate,
          due_date: this.dueDate,
          election_date: this.selectedElecetionDate
        }
      ]
    });
  }
}
