import { Component, Input, NgZone, OnInit, Output, ViewEncapsulation, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { Observable, of } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { form99 } from '../../../shared/interfaces/FormsService/FormsService';
import { ApiService } from '../../../shared/services/APIService/api.service';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { TypeComponent } from '../type/type.component';
import { ReasonComponent } from '../reason/reason.component';
import { SignComponent } from '../../../shared/partials/sign/sign.component';
import { SubmitComponent } from '../../../shared/partials/submit/submit.component';

@Component({
  selector: 'app-form-99',
  templateUrl: './f99.component.html',
  styleUrls: ['./f99.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class F99Component implements OnInit {

  @Input() status: any;

  public frm: any;
  public direction: string;
  public editMode: boolean = true;
  public step: string = 'step_1';
  public currentStep: string = 'step_1';
  public previousStep: string = '';
  public isLoading: boolean = true;
  public committee_details: any = {};
  public showValidateBar: boolean = false;

  private _committeeDetails: any = {};
  private _form99Details: any = {};
  private _step: string = '';
  private _formType: string = '';
  private _form_submitted: boolean = false;

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

    this._router
      .events
      .subscribe(val => {
        if(val) {
          if(val instanceof NavigationEnd) {
            if(val.url.indexOf('/forms/form/99') === -1) {
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

    this._messageService
      .getMessage()
      .subscribe(res => {
        if(res.validateMessage) {
          //this.showValidateBar = res.validateMessage.showValidateBar;
        } else if (res.form_submitted) {
          this._form_submitted = true;

          this._form99Details = this.committee_details;
        }
      });
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

          this._router.navigate(['/forms/form/99'], { queryParams: { step: this.step, edit: this.editMode } });
        } else if (this.frm === 'preview') {
          this.step = this._step;

          this._router.navigate(['/forms/form/99'], { queryParams: { step: this.step, edit: this.editMode } });
        }
      } else if (this.direction === 'previous') {
        this.step = this._step;

        this._router.navigate(['/forms/form/99'], { queryParams: { step: this.step, edit: this.editMode } });
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
