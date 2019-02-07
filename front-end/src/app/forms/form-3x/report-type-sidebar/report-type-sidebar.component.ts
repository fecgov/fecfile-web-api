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
  @Input() title: string = '';
  @Input() specialreports: boolean = false;
  @Input() regularreports: boolean = false;
  @Input() selectedreporttype:  selectedReportType;
  @Input() selectedstate:  selectedReportType;
  @Input() electiondates:  selectedElectionDate={};
  //@Input() electiondates:  any ={};
  @Input() fromDate:  string='';
  @Input() toDate:  string='';
  @Input() electiontoDatedates: string='';
  @Input() cashOnHand: any = {};

  public itemSelected: string = '';
  public additionalItemSelected: string = '';
  public additionalOptions: Array<any> = [];
  //public electionState:string ='';
  //public electionDates: Array<eleectionStateDate> = [];
  public electionDates: selectedElectionDate = {};
  public electionStates: any = {};

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

  constructor(
    private _config: NgbTooltipConfig,
    private _formService: FormsService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {


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

  ngDoCheck(): void
  {
    this.fromDate="01/23/2019";
    this.toDate="02/23/2019";
    this._currentReportType= localStorage.getItem('form3XReportInfo.reportType');
    console.log (" ReportTypeSidebarComponent ngDoCheck this.electiondates = ", this.electiondates);
    console.log (" ReportTypeSidebarComponent ngDoCheck this.electiondates = ", this.electiondates);
  }

  ngOnChanges(): void
  {
    this.fromDate="01/23/2019";
    this.toDate="02/23/2019";
    console.log (" ReportTypeSidebarComponent ngOnChanges reporttype = ", this.selectedreporttype);
    console.log (" ReportTypeSidebarComponent ngOnChanges this.electiondates", this.electiondates);
    if (this.electiondates !== null && this.electiondates !== undefined )
    {
      this.fromDate="01/23/2019";
      this.toDate="02/23/2019";
    }
    console.log (" ReportTypeSidebarComponent ngOnChanges fromdate = ", this.fromdate);
    console.log (" ReportTypeSidebarComponent ngOnChanges fromtodatedate = ", this.todate);
  }

  selectStateChange(value: string): void
  {

    this.fromDate="01/23/2019";
    this.toDate="02/23/2019";
    
    console.log( " ReportTypeSidebarComponent selectStateChange elction state value =", value);
    localStorage.setItem('form3XReportInfo.state', value);
    if (this.selectedreporttype !== null || this.selectedreporttype !== undefined)
    {
      this.electionStates=this.selectedreporttype.election_state
      this.electiondates  = this.electionStates.find( x => x.state === value);
    
      console.log( "ReportTypeSidebarComponent selectStateChange this.electionDates", this.electiondates);
      //localStorage.setItem('form3xSelectedReportType', JSON.stringify(this.reporttype));
    }

    console.log( "ReportTypeSidebarComponent selectStateChange this.electiondates.dates", this.electiondates);

    
       
    this.status.emit({
      electiondates: this.electiondates
    });
  }

  selectElectionDateChange(value: string): void
  {
    console.log( " ReportTypeSidebarComponent selectElectionDateChange elction date value =", value);

  }
}
