import { Component, Input, OnDestroy, OnInit, ViewEncapsulation , ChangeDetectionStrategy } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { Subject, Subscription } from 'rxjs';
import 'rxjs/add/operator/takeUntil';
import { ApiService } from '../../../shared/services/APIService/api.service';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';

@Component({
  selector: 'app-form-99',
  templateUrl: './f99.component.html',
  styleUrls: ['./f99.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class F99Component implements OnInit , OnDestroy{
  
  
  @Input() status: any;

  public frm: any;
  public direction: string;
  public editMode: boolean = true;
  public reportId: number;
  public step: string = 'step_1';
  public currentStep: string = 'step_1';
  public previousStep: string = '';
  public isLoading: boolean = true;
  public committee_details: any = {};
  public showValidateBar: boolean = false;
  public fec_id = '';

  private _committeeDetails: any = {};
  private _form99Details: any = {};
  private _step: string = '';
  private _formType: string = '';
  private _form_submitted: boolean = false;

  private onDestroy$ = new Subject();
  routerEventsSubscription: Subscription;
  

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _activatedRoute: ActivatedRoute,
    private _apiService: ApiService,
    private _formService: FormsService,
    private _messageService: MessageService
  ) { }

  ngOnInit(): void {
    this._committeeDetails = JSON.parse(localStorage.getItem('committee_details'));
    this.committee_details = this._committeeDetails;

    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this.step = this._activatedRoute.snapshot.queryParams.step;
    this.editMode = this._activatedRoute.snapshot.queryParams.edit ? this._activatedRoute.snapshot.queryParams.edit : true;

    if(this._committeeDetails) {
      if(this._committeeDetails.committeeid) {
        this._form99Details = this.committee_details;

        this._form99Details.reason = '';
        this._form99Details.text = '';
        this._form99Details.signee = `${this.committee_details.treasurerfirstname} ${this.committee_details.treasurerlastname}`;
        this._form99Details.additional_email_1 = '-';
        this._form99Details.additional_email_2 = '-';
        this._form99Details.created_at = '';
        this._form99Details.is_submitted = false;
        this._form99Details.id = '';

        let formSavedObj: any = {
          'saved': false
        };

        if(localStorage.getItem(`form_${this._formType}_details`) === null && this.step !== 'step_5') {
          localStorage.setItem(`form_${this._formType}_details`, JSON.stringify(this._form99Details));
        }

        if(localStorage.getItem(`form_${this._formType}_saved`) === null && this.step !== 'step_5') {
          localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify(formSavedObj));
        }

        this.isLoading = false;
      }
    }


    this.routerEventsSubscription = this._router.events.takeUntil(this.onDestroy$).subscribe(val => {
        if(val) {
          if(val instanceof NavigationEnd) {
            if(val.url.indexOf('/forms/form/99') === -1) {
              localStorage.removeItem(`form_${this._formType}_details`);
              localStorage.removeItem(`form_${this._formType}_saved`);
            }
          } else {
            if (this._activatedRoute.snapshot.queryParams.step !== this.currentStep) {
              this.currentStep = this._activatedRoute.snapshot.queryParams.step;
              this.step = this._activatedRoute.snapshot.queryParams.step;
              this.reportId = this._activatedRoute.snapshot.queryParams.reportId;
            }
            window.scrollTo(0, 0);
          }
        }
      });

    this._messageService
      .getMessage().takeUntil(this.onDestroy$)
      .subscribe(res => {
        if(res.validateMessage) {
        } else if (res.form_submitted) {
          this._form_submitted = true;

          this._form99Details = this.committee_details;
        }
        else if(res && res.action === 'updateForm99ReportId' && res.reportId){
          this.reportId = res.reportId;
          this._router.navigate([],{relativeTo:this._activatedRoute, queryParams: {reportId: this.reportId}, queryParamsHandling:'merge'});
        }
      });
  }

  ngOnDestroy(): void {
    this.onDestroy$.next(true);
    this.routerEventsSubscription.unsubscribe();
  }


  ngDoCheck(): void {
    if(this.currentStep !== this._activatedRoute.snapshot.queryParams.step) {
      this.currentStep = this._activatedRoute.snapshot.queryParams.step;
      this.step = this._activatedRoute.snapshot.queryParams.step;
    }

    if(this._form_submitted) {
      if(this.step === 'step_1') {
        this._form99Details.reason = '';
        this._form99Details.text = '';
        this._form99Details.signee = `${this.committee_details.treasurerfirstname} ${this.committee_details.treasurerlastname}`;
        this._form99Details.additional_email_1 = '-';
        this._form99Details.additional_email_2 = '-';
        this._form99Details.created_at = '';
        this._form99Details.is_submitted = false;
        this._form99Details.id = '';

        let formSavedObj: any = {
          'saved': false
        };

        if(localStorage.getItem(`form_${this._formType}_details`) === null) {
          localStorage.setItem(`form_${this._formType}_details`, JSON.stringify(this._form99Details));
        }

        if(localStorage.getItem(`form_${this._formType}_saved`) === null) {
          localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify(formSavedObj));
        }

        this._messageService
          .sendMessage({
            'message': 'New form99'
          });
      }
    }
  }

  /**
   * Determines ability to continue.
   *
   */
  public canContinue(): void {
    if (this.frm && this.direction) {
      if (this.direction === 'next') {
        if (this.frm.valid) {
          this.step = this._step;
          if (this.step === 'step_5') {
            this._router.navigate(['/forms/form/99'], { queryParams: { step: this.step, fec_id: this.fec_id,
            edit: this.editMode, refresh: this.editMode } });
          } else {
            this._router.navigate(['/forms/form/99'], { queryParams: { step: this.step, reportId: this.reportId,
            edit: this.editMode, refresh: this.editMode } });
          }
        } else if (this.frm === 'preview') {
          this.step = this._step;

          this._router.navigate(['/forms/form/99'], { queryParams: { step: this.step, reportId: this.reportId,
            edit: this.editMode, refresh: this.editMode } });
        }
      } else if (this.direction === 'previous') {
        this.step = this._step;

        this._router.navigate(['/forms/form/99'], { queryParams: { step: this.step, reportId: this.reportId,
          edit: this.editMode, refresh: this.editMode } });
      }
    }
  }

  /**
   * Get's message from child components.
   *
   * @param      {Object}  e       The event object.
   */
  public onNotify(e): void {
    this.frm = e.form;

    this.direction = e.direction;

    this.previousStep = e.previousStep;

    this._step = e.step;

    this.currentStep = e.step;

    this.fec_id = e.fec_id;

    if (e.refresh && e.edit !== false) {
      this.editMode = e.refresh;
    } else if (e.edit !== null) {
      this.editMode = e.edit;
    }

    if (e.reportId) {
      this.reportId = e.reportId;
    }

    this.canContinue();
  }

  /**
   * Cancels the form 99 entry.
   *
   */
  public cancel(): void {
    this._router.navigate(['./dashboard', ]);
  }
}
