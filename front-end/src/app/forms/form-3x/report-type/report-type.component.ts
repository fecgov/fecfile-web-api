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
  @ViewChild('mswCollapse') mswCollapse;
  @Input() formRadioOptionsVisible: boolean = false;
  @Input() reportType:string ='';

  //@Input() reportTypeRadio: string ='';

  public frmReportType: FormGroup;
  public typeSelected: string = '';
  public isValidType: boolean = false;
  public optionFailed: boolean = false;
  public screenWidth: number = 0;
  public tooltipPosition: string = 'right';
  public tooltipLeft: string = 'auto';

  private _form_3x_details: form3x;
  private _newForm: boolean = false;
  private _previousUrl: string = null;

  //public committee_form3x_reporttypes: Icommittee_form3x_reporttype[];
  public committee_form3x_reporttypes: any = [];

  public sidebarLinks: any = {};
  public selectedOptions: any = [];
  public searchField: any = {};
  public cashOnHand: any = {};
  public typeSelectedId: string='';
  public reportTypeRadio: string ='';

  public frm: any;
  public direction: string;
  public previousStep: string = '';
  public reporttypes: any = [];
  public reporttype: any = {};
  public coverageDateNotSelected: boolean = true;

  private _step: string = '';
  private _form_type: string = '';
  private step: string = "";
  private next_step: string = "Step-2";
  private _form3XReportDetails:  form3XReport={};
  private _form3XReportInfo:  form3XReport={};

  public showForm: boolean = true;

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

    this._form_type = this._activatedRoute.snapshot.paramMap.get('form_id');

   this._formService
     .getreporttypes(this._form_type)
     .subscribe(res => {
      this.committee_form3x_reporttypes = res.report_type;
     });

     if (this.reporttype===null || typeof this.reporttype ==='undefined'){
      this.reportType=this.committee_form3x_reporttypes[0].report_type;
     }


    this._form_3x_details = JSON.parse(localStorage.getItem('form_3X_details'));

    this.screenWidth = window.innerWidth;

    if(this.screenWidth < 768) {
      this.tooltipPosition = 'bottom';
      this.tooltipLeft = '0';
    } else if (this.screenWidth >= 768) {
      this.tooltipPosition = 'right';
      this.tooltipLeft = 'auto';
    }

    this._setForm();

    this._router
      .events
      .subscribe(e => {
        if(e instanceof NavigationEnd) {
          this._previousUrl = e.url;
          if(this._previousUrl === '/forms/form/3X?step=step_5') {
            this._form_3x_details = JSON.parse(localStorage.getItem('form_3X_details'));

            this.typeSelected = '';

            this._setForm();
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

  ngDoCheck(): void {
    this.reporttype = localStorage.getItem('form3XReportInfo.reportType');
    this.reportType = localStorage.getItem('form3XReportInfo.reportType');


    this.reporttypes=JSON.parse(localStorage.getItem('form3xReportTypes'));
    this.reportType = localStorage.getItem('form3XReportInfo.reportType');

    if (this.reporttypes !== null && this.reporttypes !== undefined)
    {
      this.reporttype  = this.reporttypes.find( x => x.report_type === this.reportType);

      if (typeof this.reporttype !== 'undefined' && this.reporttype !== null && this.reporttype !== undefined){
        if (this.reporttype.regular_special_report_ind ==="R"){
          if (localStorage.getItem('form3XReportInfo.toDate') === "Invalid Date" || localStorage.getItem('form3XReportInfo.toDate') === "") {
            this.coverageDateNotSelected=true;
            } else if (localStorage.getItem('form3XReportInfo.fromDate') === "Invalid Date" || localStorage.getItem('form3XReportInfo.fromDate') === "" ) {
              this.coverageDateNotSelected=true;
              } else {
                this.coverageDateNotSelected=false;
                }
        } else if (this.reporttype.regular_special_report_ind==="S"){
          if (localStorage.getItem('form3XReportInfo.state') === "---" || localStorage.getItem('form3XReportInfo.state') === "" || localStorage.getItem('form3XReportInfo.state') === null) {
            this.coverageDateNotSelected=true;
          } else if (localStorage.getItem('form3XReportInfo.electionDate') === "---" || localStorage.getItem('form3XReportInfo.electionDate') === "" || localStorage.getItem('form3XReportInfo.electionDate') === null) {
            this.coverageDateNotSelected=true;
              } else if ((localStorage.getItem('form3XReportInfo.toDate')) === "Invalid Date" || localStorage.getItem('form3XReportInfo.toDate') === "" ) {
                  this.coverageDateNotSelected=true;
                  } else if ((localStorage.getItem('form3XReportInfo.fromDate')) === "Invalid Date" || localStorage.getItem('form3XReportInfo.fromDate') === "") {
                    this.coverageDateNotSelected=true;
                    } else {
                      this.coverageDateNotSelected=false
                    }
          }
        }
    }

  }

  private _setForm(): void {
    this.frmReportType = this._fb.group({
      reportTypeRadio: ["", Validators.required]

    });
  }

  /**
   * Updates the type selected.
   *
   * @param      {<type>}  val     The value
   */
  public updateTypeSelected(e): void {
    if(e.target.checked) {
      this.typeSelected = e.target.value;
      this.typeSelectedId = e.target.id;
      this.reportTypeRadio = e.target.id;
      this.optionFailed = false;
    } else {
      this.typeSelected = '';
      this.optionFailed = true;
      this.reportTypeRadio = '';
    }

    //this.reporttype=e.target.id;
    localStorage.setItem('form3XReportInfo.reportType', e.target.id);
    this.reporttype = localStorage.getItem('form3XReportInfo.reportType');
    this.reportType = localStorage.getItem('form3XReportInfo.reportType');


    this.reporttypes=JSON.parse(localStorage.getItem('form3xReportTypes'));

    if (this.reporttypes !== null && typeof this.reporttypes !== 'undefined')
    {
      this.reporttype  = this.reporttypes.find( x => x.report_type === e.target.id);
      localStorage.setItem('form3XReportInfo.reportType', this.reporttype.report_type);
      localStorage.setItem('form3xSelectedReportType', JSON.stringify(this.reporttype));
      localStorage.setItem('form3XReportInfo.reportDescription', this.reporttype.report_type_desciption);
      //localStorage.removeItem('form3XReportInfo.state');

      if (this.reporttype.regular_special_report_ind==="R"){
        this.coverageDateNotSelected=true;
        localStorage.setItem('form3XReportInfo.toDate', JSON.stringify(""));
        localStorage.setItem('form3XReportInfo.fromDate', JSON.stringify(""));
       } else if (this.reporttype.regular_special_report_ind==="S"){
          localStorage.setItem('form3XReportInfo.state', JSON.stringify("---"));
          localStorage.setItem('form3XReportInfo.electionDate', JSON.stringify("---"));
          localStorage.setItem('form3XReportInfo.toDate', JSON.stringify(""));
          localStorage.setItem('form3XReportInfo.fromDate', JSON.stringify(""));
          this.coverageDateNotSelected=true
        }
    }

    localStorage.setItem('form3XReportInfo.reportTypeSelected',"Y");

    this.status.emit({
      reportTypeRadio: e.target.id
    });
    // this.frmType.controls['reportTypeRadio'].setValue(val);
  }

  /**
   * Validates the type selected form.
   *
   */
  public doValidateReportType() {
    console.log('doValidateReportType: ');
    if (this.frmReportType.get('reportTypeRadio').value) {
        this.optionFailed = false;
        this.isValidType = true;
        this._form_3x_details = JSON.parse(localStorage.getItem('form_3x_details'));

        //this._form_3x_details.reason = this.frmType.get('reportTypeRadio').value;

        setTimeout(() => {
          localStorage.setItem('form_3x_details', JSON.stringify(this._form_3x_details));
        }, 100);

        this.status.emit({
          form: this.frmReportType,
          direction: 'next',
          step: 'step_2',
          previousStep: 'step_1'
        });

        this.saveReport();
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

  public doValidateOption(): boolean {
    if (this.frmReportType.invalid) {
      this.optionFailed = true;
      return false;
    } else {
      this.optionFailed = false;
      return true;
    }
  }

  public updateStatus(e): void {
    if (e.target.checked) {
      this.optionFailed = false;
    } else {
      this.optionFailed = true;
    }
  }

  public toggleToolTip(tooltip): void {
    if (tooltip.isOpen()) {
      tooltip.close();
    } else {
      tooltip.open();
    }
  }

  public frmTypeValid() {
    return this.isValidType;
  }

  public cancel(): void {
    this._router.navigateByUrl('/dashboard');
  }
  public saveReport(): void {
    var date1, date2;
    date1 = new Date(localStorage.getItem('form3XReportInfo.dueDate'));
    date2 = Date.now();
    var res = Math.abs(date1 - date2) / 1000;
    var days = Math.floor(res / 86400);

    let fromDateString: string ="";
    let toDateString: string ="";
    let dueDateString: string ="";

    if (typeof localStorage.getItem('form3XReportInfo.fromDate') !== 'undefined' &&  localStorage.getItem('form3XReportInfo.fromDate') !== null ){
      fromDateString = this.getDateInMMDDYYYYFormat(localStorage.getItem('form3XReportInfo.fromDate'));
    }
    else{
      fromDateString="";
    }


    if (typeof localStorage.getItem('form3XReportInfo.toDate') !== 'undefined' &&  localStorage.getItem('form3XReportInfo.toDate') !== null ){
      toDateString = this.getDateInMMDDYYYYFormat(localStorage.getItem('form3XReportInfo.toDate'));
    }
    else{
      toDateString="";
    }


    if (typeof localStorage.getItem('form3XReportInfo.dueDate') !== 'undefined' &&  localStorage.getItem('form3XReportInfo.dueDate') !== null ){
      dueDateString = this.getDateInMMDDYYYYFormat(localStorage.getItem('form3XReportInfo.dueDate'));
    }
    else{
      dueDateString="";
    }

    localStorage.setItem('form_3X_ReportInfo', JSON.stringify(this._form3XReportInfo));
    console.log ("form_3X_ReportInfo =...", JSON.parse(localStorage.getItem('form_3X_ReportInfo')));

    this._form3XReportInfo.cmteId='';
    this._form3XReportInfo.reportId='';
    this._form3XReportInfo.formType= "3X";
    this._form3XReportInfo.electionCode='';
    this._form3XReportInfo.reportType=localStorage.getItem('form3XReportInfo.reportType');
    this._form3XReportInfo.regularSpecialReportInd=localStorage.getItem('form3XReportInfo.rgularSpecialReportInd');
    this._form3XReportInfo.stateOfElection=localStorage.getItem('form3XReportInfo.state');
    this._form3XReportInfo.electionDate=this.getDateInMMDDYYYYFormat(localStorage.getItem('form3XReportInfo.electionDate'));
    this._form3XReportInfo.cvgStartDate=fromDateString
    this._form3XReportInfo.cvgEndDate=toDateString
    this._form3XReportInfo.dueDate=dueDateString
    this._form3XReportInfo.amend_Indicator='';
    this._form3XReportInfo.coh_bop="0";

    localStorage.setItem('form3XReportInfo.toDate', JSON.stringify(toDateString));  
    localStorage.setItem('form3XReportInfo.fromDate', JSON.stringify(fromDateString));  
    localStorage.setItem('form3XReportInfo.dueDate', JSON.stringify(dueDateString));  
    localStorage.setItem('form3XReportInfo.electionDate', JSON.stringify(this.getDateInMMDDYYYYFormat(localStorage.getItem('form3XReportInfo.electionDate'))));

    localStorage.setItem('form_3X_ReportInfo', JSON.stringify(this._form3XReportInfo));

    this._formService
     .saveReport(this._form_type)
     .subscribe(res => {
      if(res) {
        console.log(' saveReport res: ', res);
      }
    },
    (error) => {
      console.log('saveReport error: ', error);
    });


    localStorage.setItem('form3XReportInfo.showDashBoard',"Y");
    localStorage.setItem('form3XReportInfo.DashBoardLine1',"Form 3X | " + localStorage.getItem('form3XReportInfo.reportDescription') + " | " + fromDateString+ " - " + toDateString);
    localStorage.setItem('form3XReportInfo.DashBoardLine2',"due in " + days + " days | " + dueDateString);


    this._router.navigateByUrl('/forms/form/3X?step=step_2');

  }

  public getDateInMMDDYYYYFormat(value: string):string {
    let initial: string ="";
    console.log("getDateInMMDDYYYYFormat =",value);

    if (value !== null){
      
      /*let DateString = value;
      let DateObject = new Date(DateString);
      DateString = DateObject.toLocaleDateString();
      return DateString;*/

      /*var initial = 'dd/mm/yyyy'.split(/\//);
      console.log( [ initial[1], initial[0], initial[2] ].join('/')); //=> 'mm/dd/yyyy'
      // or in this case you could use*/
      initial =value.split(/\//).reverse().join('-');
      initial=[ initial[1], initial[0], initial[2] ].join('/');
      initial="04/05/2018";
      /*let newDate = new Date(initial);
      let newdate=newDate.getDate()+1;
      newdate.setDate(newdate.getDate() + 1);
      //return this.getFormattedDate(newdate)*/
      console.log("initial", value);

      var datatoday = new Date(value);
      var newdt = new Date(datatoday.setDate(datatoday.getDate() + 1));
      //var datatodays = datatoday.setDate(new Date(value).getDate() + 1);
      //var todate = new Date(datatodays);
      console.log("initial todate", newdt);
      console.log(" getDateInMMDDYYYYFormat todate = ", newdt)
      return this.getFormattedDate(newdt)

    }
    else
    {
      return "";
    }
  }
  public  getFormattedDate(date: Date) {
    let year = date.getFullYear();
    let month = (1 + date.getMonth()).toString().padStart(2, '0');
    let day = date.getDate().toString().padStart(2, '0');
  
    return month + '/' + day + '/' + year;
}
  // smahal: for dev only -
  public viewTransactions() {
    this._router.navigate(['/forms/transactions', this._form_type]);
  }

}
