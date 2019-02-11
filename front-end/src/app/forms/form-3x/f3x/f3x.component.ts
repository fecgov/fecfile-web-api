import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { forkJoin, of, interval } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { form3x_data, form3XReport } from '../../../shared/interfaces/FormsService/FormsService';
import { selectedElectionState, selectedElectionDate, selectedReportType } from '../../../shared/interfaces/FormsService/FormsService';

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
  public electionDates: selectedElectionDate = {};
  public electionStates: any = {};
  public form3xSelectedReportType: any = {};
  public selectedstate: string = '';
  public fromDate: string = '';
  public toDate: string = '';
  public selectedReportType: selectedReportType = {};
  public reportType: string = '';

  private _step: string = '';
  private _formType: string = '';
  //private _form3XReportDetails:  any = {};
  private _form3XReportDetails:  form3XReport={};
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
    this.specialreports=true;
    this.regularreports=false;

    this._form3XReportDetails.reportId='';
    this._form3XReportDetails.reportType='';
    this._form3XReportDetails.regularSpecialReportInd='';
    this._form3XReportDetails.stateOfElection='';
    this._form3XReportDetails.cvgStartDate='';
    this._form3XReportDetails.cvgEndDate='';
    this._form3XReportDetails.dueDate='';


    localStorage.setItem('form3XReportInfo', JSON.stringify(this._form3XReportDetails));

     /*localStorage.setItem('form3XReportInfo.reportId', this._form3XReportDetails.reportId);
    localStorage.setItem('form3XReportInfo.reportType', this._form3XReportDetails.reportType);
    localStorage.setItem('form3XReportInfo.regularSpecialReportInd', this._form3XReportDetails.regularSpecialReportInd);
    localStorage.setItem('form3XReportInfo.stateOfElection', this._form3XReportDetails.stateOfElection);
    localStorage.setItem('form3XReportInfo.cvgStartDate', this._form3XReportDetails.cvgStartDate);
    localStorage.setItem('form3XReportInfo.cvgEndDate', this._form3XReportDetails.cvgEndDate);
    localStorage.setItem('form3XReportInfo.dueDate', this._form3XReportDetails.dueDate);*/

    this._formService
      .getreporttypes(this._formType)
      .subscribe(res => {
        this.reporttypes  = res.report_type;
        localStorage.setItem('form3xReportTypes', JSON.stringify(this.reporttypes));
        console.log ("F3xComponent ngOnInit this.reporttypes",this.reporttypes)

    });


    this._formService
      .getTransactionCategories(this._formType)
      .subscribe(res => {
        console.log(' getTransactionCategories resp: ', res);
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


    //this._currentReportType= localStorage.getItem('form3XReportInfo.reportType');

    this.reporttypes=JSON.parse(localStorage.getItem('form3xReportTypes'));


    /*this.reporttypeindicator  = this.reporttypes.find( x => {
      return x.default_disp_ind === 'Y' ;*/

    this.reporttype=localStorage.getItem('form3XReportInfo.reportType');

    if ( typeof  this.reportType === 'undefined')
    {
      this.selectedReportType  = this.reporttypes.find( x => x.default_disp_ind === 'Y');

      if (this.selectedReportType !== null && this.selectedReportType !== undefined)
      {
        this.reportType  = this.selectedReportType.report_type;
        this.selectedReportType = this.reporttypes.find( x => x.report_type===this.reportType)
        this.reporttypeindicator= this.selectedReportType.regular_special_report_ind;
      }
      else
      {
        this.reportType  = this.reporttypes[0].report_type;

        this.selectedReportType = this.reporttypes.find( x => x.report_type===this.reportType)
        this.reporttypeindicator= this.selectedReportType.regular_special_report_ind;
        //this.reportType  = this.selectedReportType.report_type;
      }

      if (this.reporttypeindicator === 'S') {
        this.specialreports=true;
        this.regularreports=false;
      }
      else
      {
        this.specialreports=false;
        this.regularreports=true;
      }

    }
    else
    {
      if (this.selectedReportType !== null && this.selectedReportType !== undefined)
      {
       this.selectedReportType=JSON.parse(localStorage.getItem('form3xSelectedReportType'));
       if(this.selectedReportType !== null) {
         if (this.selectedReportType.regular_special_report_ind === 'S') {
            this.specialreports=true;
            this.regularreports=false;
            this.electionStates=this.selectedReportType.election_state
            this.fromDate="01/20/2019";
            this.fromDate="02/20/2019";

          } else {
            this.specialreports=false;
            this.regularreports=true;
            this.fromDate="01/20/2019";
            this.fromDate="02/20/2019";

          /*this.fromDate=this.electionStates[0].cvg_start_date;
          this.toDate=this.electionStates[0].cvg_end_date;*/

          }
        } else {
          this.specialreports=false;
          this.regularreports=true;
          this.fromDate="01/20/2019";
          this.fromDate="02/20/2019";
        }
     }
     else
     {
      this.reporttypes=JSON.parse(localStorage.getItem('form3xReportTypes'));
      if (typeof this.reporttypes !== null)
      {
        if (Array.isArray(this.reporttypes)) {
          this.reportType  = this.reporttypes[0].report_type;
        }
      }
      if (this.reporttypes !== null) {
          if (Array.isArray(this.reporttypes)) {
            this.selectedReportType = this.reporttypes.find( x => x.report_type===this.reportType)
          }
      }

      if (this.selectedReportType !== null) {
        if (typeof this.selectedReportType.regular_special_report_ind === 'string') {
          this.reporttypeindicator= this.selectedReportType.regular_special_report_ind;
        }
      }

      if (this.reporttypeindicator === 'S')
        {
          this.specialreports=true;
          this.regularreports=false;
        }
        else
        {
         this.specialreports=false;
         this.regularreports=true;
         this.fromDate="01/20/2019";
         this.fromDate="02/20/2019";
        }
     }


     }

    this.selectedstate = localStorage.getItem('form3XReportInfo.state');

    this.form3xSelectedReportType = JSON.parse(localStorage.getItem('form3xSelectedReportType'));

    if ( typeof  this.selectedReportType !== null)
    {
      if (this.selectedReportType !== null) {
        this.electionStates=this.selectedReportType.election_state;
        if (this.selectedstate === null || this.selectedstate === undefined)
        {
          this.electionDates  = this.electionStates[0];
        }
        else
        {
         this.electionDates  = this.electionStates.find( x => x.state === this.selectedstate);
        }
      }
      //localStorage.setItem('form3xSelectedReportType', JSON.stringify(this.reportType));
    }


    this.selectedstate = localStorage.getItem('form3XReportInfo.state');

    this.form3xSelectedReportType = JSON.parse(localStorage.getItem('form3xSelectedReportType'));

    /*if (this.selectedReportType !== null && this.form3xSelectedReportType !== undefined)
    {
      this.electionStates=this.selectedReportType.election_state;

      if (this.selectedstate !== null &&  this.selectedstate !== undefined)
      {
       this.electionDates  = this.electionStates.find( x => x.state === this.selectedstate);
      }
      else
      {
        this.electionDates  = this.electionStates[0].dates;
      }

      console.log( "F3xComponent ngDoCheck  this.electionStates", this.electionStates);
      console.log( "F3xComponent ngDoCheck  this.electionDates", this.electionDates);
      //localStorage.setItem('form3xSelectedReportType', JSON.stringify(this.reportType));
    }*/


    localStorage.setItem('form3xSelectedReportType', JSON.stringify(this.selectedReportType));

    /*this._currentReportType= localStorage.getItem('form3XReportInfo.reportType');
    console.log("F3X Componenets ngOnChanges this._currentReportTyp", this._currentReportType);  */
  }

  ngOnChanges(): void
  {

    this._currentReportType= localStorage.getItem('form3XReportInfo.reportType');


    this.reporttypes=JSON.parse(localStorage.getItem('form3xReportTypes'));
    this.reporttypeindicator  = this.reporttypes.find( x => {
      return x.default_disp_ind === 'Y' ;
    });
    //}).regular_special_report_ind;

    if (typeof this.reporttypeindicator !== 'undefined') {
      this.reporttypeindicator = this.reporttypeindicator.regular_special_report_ind;
    }

    this.selectedReportType=JSON.parse(localStorage.getItem('form3xSelectedReportType'));

    if (this.reportType === null || this.reportType === undefined)
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
        this.electionStates=this.form3xSelectedReportType.election_state

        this.fromDate=this.electionStates.cvg_start_date;
        this.toDate=this.electionStates.cvg_end_date;

      }
    }

    this.selectedstate = localStorage.getItem('form3XReportInfo.state');
    this.form3xSelectedReportType = JSON.parse(localStorage.getItem('form3xSelectedReportType'));

    if (this.selectedReportType !== null || this.form3xSelectedReportType !== undefined)
    {
      this.electionStates=this.selectedReportType.election_state

      if (this.selectedstate===null || this.selectedstate ===undefined)
      {
       this.electionDates  = this.electionStates.find( x => x.state === this.selectedstate);
      }
      else
      {
        this.electionDates  = this.electionStates[0].dates;
      }
      //localStorage.setItem('form3xSelectedReportType', JSON.stringify(this.reportType));
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

      if (typeof e.reportTypeRadio !== undefined) {
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
