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
  @Input() selectedReport: any = {};
  @Input() selectedreporttype:  selectedReportType;
  @Input() selectedstate:  selectedReportType;
  @Input() electiondates:  Array<selectedElectionDate> ;
  @Input() fromDate:  string='';
  @Input() toDate:  string='';
  @Input() electiontoDatedates: string='';
  @Input() cashOnHand: any = {};

  public itemSelected: string = '';
  public additionalItemSelected: string = '';
  public additionalOptions: Array<any> = [];
  //public electionState:string ='';
  //public electionDates: Array<eleectionStateDate> = [];
  public electionDates: selectedElectionState = {};
  public electionDates1: selectedElectionState = {};
  //public electionDates1: any = [];
  @Input() electiondates1:  Array<selectedElectionDate> ;

  public electionStates: Array<selectedElectionState> ;
  public stateSelectedElectionDates: any = {};;
  private _indexOfItemSelected: number = null;
  private _currentReportType: string ='';
  public loadingData: boolean = true;
  public steps: any = {};
  public sidebarLinks: any = {};
  public selectedOptions: any = [];
  public searchField: any = {};
  //public cashOnHand: any = {};
  public currentStep: string = 'step_2';
  public step: string = '';
  public fromdate: string = '';
  public todate: string = '';
  public reporttypes: any = {};
  public selectedReportType: any = {};
  public selectedState: string='';
  public electionDate: selectedElectionDate = {};
  public isDisabled: boolean=true;
  public electiondatesTmp: Array<selectedElectionDate> ;
  constructor(
    private _config: NgbTooltipConfig,
    private _formService: FormsService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    console.log('reportTypeSideBar: ');
    console.log('this.specialReports: ', this.specialReports);
    console.log('this.regularReports: ', this.regularReports);
  }

  ngDoCheck(): void {
    if (this.selectedReport) {
      console.log('report-type-sidebar: ');
      console.log('selectedReport: ', this.selectedReport);
    }
    // if (typeof this.selectedreporttype !== null && this.selectedreporttype !== null){
    //   if (typeof this.selectedreporttype.regular_special_report_ind !== 'undefined'){
    //     localStorage.setItem('form3XReportInfo.regularSpecialReportInd', this.selectedreporttype.regular_special_report_ind);
    //   }
    // }
  }

  public selectItem(item): void {
    this.itemSelected = item.getAttribute('value');

    this.additionalOptions = [];

    this.sidebarLinks.findIndex((el, index) => {
      if (el.value === this.itemSelected) {
        this._indexOfItemSelected = index;
      }
    });

    this.status.emit({
      additionalOptions: this.additionalOptions
    });
  }

  public selectedAdditionalOption(additionalItem): void {
    let additionalItemIndex: number = null;

    this.additionalItemSelected = additionalItem.getAttribute('value');
    this.sidebarLinks[this._indexOfItemSelected].options.findIndex((el, index) => {
      if (this.additionalItemSelected === el.value) {
        additionalItemIndex = index;
      }
    });

    this.additionalOptions = this.sidebarLinks[this._indexOfItemSelected].options[additionalItemIndex].options;

    this.status.emit({
      additionalOptions: this.additionalOptions
    });
  }

  public selectStateChange(value: string): void {
    console.log(" ReportTypeSidebarComponent selectStateChange state =", value);
    localStorage.setItem('form3XReportInfo.state', value);

    if (value !== "---"){
      for(var item in this.selectedreporttype) {
        if (item==="election_state"){
          for (var electionstate in this.selectedreporttype[item]){
            if (this.selectedreporttype[item][electionstate]["state"]===value) {
              this.electiondates= this.selectedreporttype[item][electionstate].dates;
              localStorage.removeItem('form3XReportInfo.electionDate');
              localStorage.removeItem('form3XReportInfo.dueDate');
              localStorage.removeItem('form3XReportInfo.toDate');
              localStorage.removeItem('form3XReportInfo.fromDate');
              this.isDisabled=false;
            }
          }
         }
      }

    /*  for (var item  in this.electiondates){
        if (item !== "election_date"){
          this.electiondatesTmp[item]["cvg_start_date"]  =  this.electiondates[item]["cvg_start_date"]
          this.electiondatesTmp[item]["cvg_end_date"]  =  this.electiondates[item]["cvg_end_date"]
          this.electiondatesTmp[item]["due_date"]  =  this.electiondates[item]["due_date"]
        } else {
          this.electiondatesTmp[item]["election_date"]  =  this.electiondates[item]["election_date"]
        }
      }*/
    }
    else {
      localStorage.removeItem('form3XReportInfo.electionDate');
      localStorage.removeItem('form3XReportInfo.dueDate');
      localStorage.removeItem('form3XReportInfo.toDate');
      localStorage.removeItem('form3XReportInfo.fromDate');
    }

    this.fromDate = "";
    this.toDate = "";



    this.status.emit({
      electiondates: this.electiondates
    });
  }

  ElectionDateChange(value: string): void
  {
    if ( typeof this.electiondates !== "undefined" &&  this.electiondates !== null)
    {
      if (value !== "---"){
        for(var prop in this.electiondates) {
           if (this.electiondates[prop]["election_date"] === value ){
              this.fromDate = this.electiondates[prop]["cvg_start_date"];
              this.toDate = this.electiondates[prop]["cvg_end_date"];
              let eletionDateString = this.electiondates[prop]["election_date"];
              let electionDateObject = new Date(eletionDateString);
              eletionDateString = electionDateObject.toLocaleDateString();
              localStorage.setItem('form3XReportInfo.dueDate', this.getDateInMMDDYYYYFormat(this.electiondates[prop]["due_date"]));
              localStorage.setItem('form3XReportInfo.toDate', this.getDateInMMDDYYYYFormat(this.electiondates[prop]["cvg_end_date"]));
              localStorage.setItem('form3XReportInfo.fromDate', this.getDateInMMDDYYYYFormat(this.electiondates[prop]["cvg_start_date"]));
              localStorage.setItem('form3XReportInfo.electionDate', this.getDateInMMDDYYYYFormat(this.electiondates[prop]["election_date"]));
            }
        }
      }
      else {
        localStorage.setItem('form3XReportInfo.electionDate', "---")
        localStorage.removeItem('form3XReportInfo.dueDate');
        localStorage.removeItem('form3XReportInfo.toDate');
        localStorage.removeItem('form3XReportInfo.fromDate');
      }
   }

      this.status.emit({
        electiondates: this.electiondates
      });
  }

  toDateChange(value: string): void{
    console.log("toDate ",value)
    localStorage.setItem('form3XReportInfo.toDate', this.getDateInMMDDYYYYFormat(value));
  }

  fromDateChange(value: string): void{
    console.log("fromDate ",value);
    localStorage.setItem('form3XReportInfo.fromDate', this.getDateInMMDDYYYYFormat(value));
  }

  getDateInMMDDYYYYFormat(value: string):string {
    let DateString = value;
    let DateObject = new Date(DateString);
    DateString = DateObject.toLocaleDateString();
    return DateString;
  }
}
