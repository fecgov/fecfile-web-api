import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { forkJoin, of, interval } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { form3x_data, form3XReport } from '../../../shared/interfaces/FormsService/FormsService';
import { selectedElectionState, selectedElectionDate, selectedReportType } from '../../../shared/interfaces/FormsService/FormsService';
import { MessageService } from '../../../shared/services/MessageService/message.service';

@Component({
  selector: 'app-f3x',
  templateUrl: './f3x.component.html',
  styleUrls: ['./f3x.component.scss'],
  providers: [NgbTooltipConfig],
  encapsulation: ViewEncapsulation.None
})
export class F3xComponent implements OnInit {

  public currentStep: string = 'step_1';
  public step: string = '';
  public formOptionsVisible: boolean = false;
  public frmOption: FormGroup;
  public loadingData: boolean = true;
  public steps: any = {};
  public transactionCategories: any = {};
  public selectedOptions: any = [];
  public searchField: any = {};
  public cashOnHand: any = {};
  public frm: any;
  public direction: string;
  public previousStep: string = '';
  public specialreports: boolean = false;
  public regularreports: boolean = false;
  public reporttypeindicator: any = '';
  public loadingreportData: boolean = true;
  public reporttypes: any = [];
  public stateSelection: string ='';
  public formRadioOptionsVisible: boolean = false;
  public selectedreportTypeRadio: string = '';
  public reporttype: any = {};
  public electionDates: Array<selectedElectionDate>;
  public electionDate: selectedElectionDate = {};
  public electionStates: Array<selectedElectionState>;
  public electionState: selectedElectionState = {};
  public form3xSelectedReportType: any = {};
  public selectedstate: string = '';
  public fromDate: string = '';
  public toDate: string = '';
  public selectedReportType: selectedReportType = {};
 
  public reportType: string = '';

  private _step: string = '';
  private _formType: string = '';
  //private _form3XReportDetails:  any = {};
  private _form3XReportInfo:  form3XReport={};
  private _currentReportType: string='';
  
  
  
  constructor(
    private _formService: FormsService,
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _config: NgbTooltipConfig,
    private _router: Router,
    private _activatedRoute: ActivatedRoute

  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    console.log (" this._formType ",  this._formType );

    this._form3XReportInfo.cmteId='';
    this._form3XReportInfo.reportId='';
    this._form3XReportInfo.formType= this._formType;
    this._form3XReportInfo.reportType='';
    this._form3XReportInfo.regularSpecialReportInd='';
    this._form3XReportInfo.electionCode='';
    this._form3XReportInfo.stateOfElection='';
    this._form3XReportInfo.electionDate;
    this._form3XReportInfo.cvgStartDate='';
    this._form3XReportInfo.cvgEndDate='';
    this._form3XReportInfo.dueDate='';
    this._form3XReportInfo.amend_Indicator='';
    this._form3XReportInfo.coh_bop='';
   
  
    localStorage.setItem('form_3X_ReportInfo', JSON.stringify(this._form3XReportInfo));

    this._formService
      .getreporttypes(this._formType)
      .subscribe(res => {
        if ( typeof res.report_type !== 'undefined' &&  res.report_type !== null ){
          this.reporttypes  = res.report_type;
          localStorage.setItem('form3xReportTypes', JSON.stringify(this.reporttypes));
          console.log ("F3xComponent ngOnInit this.reporttypes",this.reporttypes)
        }  
    });

    
    this._formService
      .getTransactionCategories(this._formType)
      .subscribe(res => {
        console.log('getTransactionCategories resp: ', res);

          console.log ("res.data.cashOnHand res",res);
            this.cashOnHand = res.data.cashOnHand;   
            this.transactionCategories = res.data.transactionCategories;
            this.searchField = res.data.transactionSearchField;
      });

      if(localStorage.getItem(`form_${this._formType}_saved`) === null && this.step !== 'step_5') {
        localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify({'saved': false}));
      }

    this.loadingData = false;
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this.step = this._activatedRoute.snapshot.queryParams.step;

    this._router
      .events
      .subscribe(val => {
        if(val) {
          if(val instanceof NavigationEnd) {
            if(val.url.indexOf('/forms/form/3X') === -1) {
              localStorage.removeItem(`form_${this._formType}_details`);
              localStorage.removeItem(`form_${this._formType}_saved`);
            }
          } else {
            if(this._activatedRoute.snapshot.queryParams.step !== this.currentStep) {
              this.currentStep = this._activatedRoute.snapshot.queryParams.step;
              this.step = this._activatedRoute.snapshot.queryParams.step;
            }
            window.scrollTo(0, 0);
          }
        }
      });
  }

  ngDoCheck(): void {
    if(this._activatedRoute.snapshot.queryParams.step !== this.currentStep) {
      this.currentStep = this._activatedRoute.snapshot.queryParams.step;
      this.step = this._activatedRoute.snapshot.queryParams.step;
    }

    this.reporttypes=JSON.parse(localStorage.getItem('form3xReportTypes'));
    this.reporttype=localStorage.getItem('form3XReportInfo.reportType');
  
    if ( typeof  this.reportType === 'undefined' || this.reportType === null)
    {
      this.selectedReportType  = this.reporttypes.find( x => x.default_disp_ind === 'Y');

      if ( typeof this.selectedReportType !== 'undefined' || typeof this.selectedReportType !== null)
      {
        this.reporttypeindicator= this.selectedReportType.regular_special_report_ind;
      }
      else
      {
        this.reportType  = this.reporttypes[0].report_type;
        this.selectedReportType = this.reporttypes.find( x => x.report_type===this.reportType)
        this.reporttypeindicator= this.selectedReportType.regular_special_report_ind;
      }

      if (this.reporttypeindicator === 'S') {
        this.specialreports=true;
        this.regularreports=false;
        this.electionDate=this.selectedReportType.election_state[0].dates[0];
        this.fromDate=this.electionDate.cvg_start_date;
        this.toDate=this.electionDate.cvg_end_date;
        this.electionDates=this.selectedReportType.election_state[0].dates;
       
      } 
      else 
      { 
       
        this.specialreports=false;
        this.regularreports=true;
        this.electionDate=this.selectedReportType.election_state[0].dates[0];
        this.fromDate=this.electionDate.cvg_start_date;
        this.toDate=this.electionDate.cvg_end_date;
        localStorage.setItem('form3XReportInfo.toDate', this.electionDate.cvg_start_date);
        localStorage.setItem('form3XReportInfo.fromDate', this.electionDate.cvg_end_date);
      }
      
    }
    else
    {
      
      this.selectedReportType=JSON.parse(localStorage.getItem('form3xSelectedReportType'));
      if ( typeof this.selectedReportType !== 'undefined' ||  typeof this.selectedReportType !== null ) {
        this.selectedstate = localStorage.getItem('form3XReportInfo.state');
        if (this.selectedReportType !== null)
        {
          if (this.selectedReportType.regular_special_report_ind === 'S') 
          {
            this.specialreports=true;
            this.regularreports=false;
            this.electionStates=this.selectedReportType.election_state;
            this.electionDates=this.electionStates[0].dates;
            
          } 
          else 
          { 
            this.specialreports=false;
            this.regularreports=true;
            this.electionDate=this.selectedReportType.election_state[0].dates[0];
            this.fromDate=this.electionDate.cvg_start_date; 
            this.toDate=this.electionDate.cvg_end_date;
            localStorage.setItem('form3XReportInfo.toDate', this.electionDate.cvg_start_date);
            localStorage.setItem('form3XReportInfo.fromDate', this.electionDate.cvg_end_date);
            }
        }
        else
        {
          
          this.reporttypes=JSON.parse(localStorage.getItem('form3xReportTypes'));
          if ( typeof this.reporttypes !== 'undefined' && this.reporttypes !== null) {
            this.reportType  = this.reporttypes[0].report_type;
            this.selectedReportType = this.reporttypes.find( x => x.report_type===this.reportType)
            this.reporttypeindicator= this.selectedReportType.regular_special_report_ind;
          }
        }
       }
       else
       {
        this.reporttypes=JSON.parse(localStorage.getItem('form3xReportTypes'));
        if ( this.reporttypes !==undefined) {
         this.reportType  = this.reporttypes[0].report_type;
        }

        this.selectedReportType = this.reporttypes.find( x => x.report_type===this.reportType)
        this.reporttypeindicator= this.selectedReportType.regular_special_report_ind;
      
        if (this.reporttypeindicator === 'S') {
          this.specialreports=true;
          this.regularreports=false;
          this.electionDates=this.selectedReportType.election_state[0].dates;
          this.electionDate=this.selectedReportType.election_state[0].dates[0];
          if (  this.electionDates !== undefined) {
            this.fromDate=this.electionDate.cvg_start_date;
            this.toDate=this.electionDate.cvg_end_date;
          }
        } 
        else 
        {
         this.specialreports=false;
         this.regularreports=true;
         this.electionDate=this.selectedReportType.election_state[0].dates[0];
         if ( typeof this.electionDates !== 'undefined') {
          this.fromDate=this.electionDate.cvg_start_date;
          this.toDate=this.electionDate.cvg_end_date;
          localStorage.setItem('form3XReportInfo.toDate', this.electionDate.cvg_start_date);
          localStorage.setItem('form3XReportInfo.fromDate', this.electionDate.cvg_end_date);
         }
        }
       }
    }

    this.selectedstate = localStorage.getItem('form3XReportInfo.state');
    this.form3xSelectedReportType = JSON.parse(localStorage.getItem('form3xSelectedReportType'));
    if ( typeof  this.selectedReportType !== 'undefined' || this.selectedReportType !== null)
    {
      
      if (this.selectedReportType !== null)
      {
        this.electionStates=this.selectedReportType.election_state;
        if ( typeof this.selectedstate  === 'undefined' ||  this.selectedstate  === null)
        {
          this.electionDates  = this.selectedReportType.election_state[0].dates;
        }
        else
        {
          this.electionState = this.electionStates.find( x => x.state === this.selectedstate);
          this.electionDates  =  this.electionState.dates;
        }
      }
    }
    this.selectedstate = localStorage.getItem('form3XReportInfo.state');
    this.form3xSelectedReportType = JSON.parse(localStorage.getItem('form3xSelectedReportType'));
    localStorage.setItem('form3xSelectedReportType', JSON.stringify(this.selectedReportType));
    if (typeof this.form3xSelectedReportType !=='undefined' && this.form3xSelectedReportType !== null){
      localStorage.setItem('form3XReportInfo.reportDescription', this.selectedReportType.report_type_desciption);
    }
  }

  ngOnChanges(): void
  {
    this._currentReportType= localStorage.getItem('form3XReportInfo.reportType');
    this.reporttypes=JSON.parse(localStorage.getItem('form3xReportTypes'));
    this.reporttypeindicator  = this.reporttypes.find( x => {
      return x.default_disp_ind === 'Y' ;
    });

    if (typeof this.reporttypeindicator !== 'undefined') {
      this.reporttypeindicator = this.reporttypeindicator.regular_special_report_ind;
    }

    this.selectedReportType=JSON.parse(localStorage.getItem('form3xSelectedReportType'));

    if ( typeof this.reportType === 'undefined')
    {
     if (this.reporttypeindicator === 'S') {
       this.specialreports=true;
       this.regularreports=false;
     } else {
       this.specialreports=false;
       this.regularreports=true;
     }
    }
    else
    {
      if (this.selectedReportType.regular_special_report_ind === 'S') {
        this.specialreports=true;
        this.regularreports=false;
  
      } 
      else 
      {
        this.specialreports=false;
        this.regularreports=true;
       
      }
    }
    this.selectedstate = localStorage.getItem('form3XReportInfo.state');
    this.form3xSelectedReportType = JSON.parse(localStorage.getItem('form3xSelectedReportType'));
    if (typeof this.form3xSelectedReportType !== 'undefined')
    {
      this.electionStates=this.selectedReportType.election_state

      if (typeof this.selectedstate === 'undefined')
      {
       this.electionDates  = this.electionStates.find( x => x.state === this.selectedstate).dates;
      }
      else
      {
        this.electionDates  = this.electionStates[0].dates;
      }
    }
    this._currentReportType= localStorage.getItem('form3XReportInfo.reportType');
  }

  /**
   * Get's message from child components.
   *
   * @param      {Object}  e       The event object.
   */
  
  public onNotify(e): void {



    if (typeof e.additionalOptions !== 'undefined') {
      if (e.additionalOptions.length) {
        this.selectedOptions = e.additionalOptions;
        this.formOptionsVisible = true;
      } else {
        this.selectedOptions = null;
        this.formOptionsVisible = false;
      }
    }

      if (typeof e.reportTypeRadio !== 'undefined' && e.reportTypeRadio !== null ) {
        if (e.reportTypeRadio.length) {
          this.selectedreportTypeRadio = e.reportTypeRadio;
         }
         else
          {
          this.selectedreportTypeRadio = null;
        }
    }
    this._currentReportType= localStorage.getItem('form3XReportInfo.reportType');

    this.frm = e.form;

    this.direction = e.direction;

    this.previousStep = e.previousStep;

    this._step = e.step;

    this.currentStep = e.step;

    this.canContinue();
   }


   public canContinue(): void {

    if(this.frm && this.direction) {
      if(this.direction === 'next') {
        if(this.frm.valid) {
          this.step = this._step;

          this._router.navigate(['/forms/form/3X'], { queryParams: { step: this.step } });
        } else if(this.frm === 'preview') {
          this.step = this._step;

          this._router.navigate(['/forms/form/3X'], { queryParams: { step: this.step } });
        }
      } else if(this.direction === 'previous') {
        this.step = this._step;

        this._router.navigate(['/forms/form/3X'], { queryParams: { step: this.step } });
      }
    }

  }

 
}
