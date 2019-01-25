import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { forkJoin, of, interval } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { form3x_data } from '../../../shared/interfaces/FormsService/FormsService';

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
  private _step: string = '';
  private _form_type: string = '';

  public specialreports: boolean = false;
  public regularreports: boolean = false;
  public reporttypeindicator: any = '';
  public loadingreportData: boolean = true;
  public reporttypes: any = [];

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
    this.specialreports=true;
    this.regularreports=false;

    this._formService
      .getreporttypes(this._form_type)
      .subscribe(res => {
        this.reporttypeindicator  = res.report_type.find( x => {
          return x.default_disp_ind === 'Y' ;
        });
        //}).regular_special_report_ind;

        if (typeof this.reporttypeindicator !== 'undefined') {
          this.reporttypeindicator = this.reporttypeindicator.regular_special_report_ind;
        }
    });

     if (this.reporttypeindicator === 'S') {
       this.specialreports=true;
       this.regularreports=false;
     } else {
       this.specialreports=false;
       this.regularreports=true;
     }
    this._formService
      .getTransactionCategories(this._form_type)
      .subscribe(res => {
        console.log(' getTransactionCategories resp: ', res);
        this.cashOnHand = res.data.cashOnHand;

        this.transactionCategories = res.data.transactionCategories;

        this.searchField = res.data.transactionSearchField;
      });


    this.loadingData = false;
    this._form_type = this._activatedRoute.snapshot.paramMap.get('form_id');

    this.step = this._activatedRoute.snapshot.queryParams.step;

    this._router
      .events
      .subscribe(val => {
        if(val) {
          if(val instanceof NavigationEnd) {
            if(val.url.indexOf('/forms/form/3X') === -1) {
              localStorage.removeItem(`form_${this._form_type}_details`);
              localStorage.removeItem(`form_${this._form_type}_saved`);
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
