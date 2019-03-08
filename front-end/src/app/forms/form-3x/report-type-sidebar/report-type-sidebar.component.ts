import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { selectedElectionState, selectedElectionDate, selectedReportType } from '../../../shared/interfaces/FormsService/FormsService';

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

  public electionStates: any = null;
  public electionDates: any = null;
  public fromDate: string = null;
  public toDate: string = null;

  private _selectedElectionDates: any = null;

  constructor(
    private _config: NgbTooltipConfig,
    private _formService: FormsService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {}

  ngDoCheck(): void {
    if (this.selectedReport !== null) {
      if (this.selectedReport.hasOwnProperty('election_state')) {
        if (Array.isArray(this.selectedReport.election_state)) {
          if (this.selectedReport.election_state.length === 1) {
            this.fromDate = '';
            this.toDate = '';
            this._selectedElectionDates = null;
            if (this.selectedReport.election_state[0]['dates']) {
              if (Array.isArray(this.selectedReport.election_state[0].dates)) {
                let dates: any = this.selectedReport.election_state[0].dates;

                if (Array.isArray(dates)) {
                  this.fromDate = dates[0].cvg_start_date;
                  this.toDate = dates[0].cvg_end_date;
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
      } // hasOwnProperty('election_state')
    }
  }


  public selectStateChange(e): void {
    console.log('selectedStateChange: ');
    let selectedVal: string = e.target.value;
    let selectedState: any = null;

    if (selectedVal !== '0') {
      if (this.selectedReport.hasOwnProperty('election_state')) {
        selectedState = this.selectedReport.election_state.find(el => {
          return el.state === selectedVal;
        });

        if (selectedState.hasOwnProperty('dates')) {
          if (Array.isArray(selectedState.dates)) {
            this.electionDates = selectedState.dates;
          }

          console.log('selectedState: ', selectedState);
        }
      }
    }
  }

  public electionDateChange(e): void {
    let selectedIndex: number = e.target.selectedIndex;
    let selectedOption: any = e.target[e.target.selectedIndex];

    this._selectedElectionDates = {
      'fromDate': selectedOption.getAttribute('data-startdate'),
      'toDate': selectedOption.getAttribute('data-enddate')
    };
  }
}
