import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { forkJoin, of, interval } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { form3x_data } from '../../../shared/interfaces/FormsService/FormsService';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';

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
  public sidebarLinks: any = {};
  public selectedOptions: any = [];
  public searchField: any = {};
  public cashOnHand: any = {};

  public frm: any;
  public direction: string;
  public previousStep: string = '';
  private _step: string = '';
  private _form_type: string = '';

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
    this._formService
      .getTransactionCategories()
      .subscribe(res => {
        console.log('resp: ', res);

        this.sidebarLinks = res.data.transactionCategories;

        this.searchField = res.data.transactionSearchField;

        this.step = this.currentStep;

        this.loadingData = false;
      });
      console.log("step = ",this.step);

    //this.step = this.currentStep;
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
    console.log("canContinue...");

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
