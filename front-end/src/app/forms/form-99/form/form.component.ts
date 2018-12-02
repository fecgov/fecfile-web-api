import { Component, Input, NgZone, OnInit, Output, ViewEncapsulation, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
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
  templateUrl: './form.component.html',
  styleUrls: ['./form.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class FormComponent implements OnInit {

  @Input() status: any;

  public frm: any;
  public direction: string;
  public step: string = 'step_1';
  public currentStep: string = 'step_1';
  public previousStep: string = '';
  public isLoading: boolean = true;
  public committee_details: any = {};
  public showValidateBar: boolean = false;

  private _committee_details: any = {};
  private _form99_details: any = {};
  private _step: string = '';
  private _form_type: string = '';

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _activatedRoute: ActivatedRoute,
    private _apiService: ApiService,
    private _formService: FormsService,
    private _messageService: MessageService
  ) { }

  ngOnInit(): void {
    this._committee_details = JSON.parse(localStorage.getItem('committee_details'));
    this.committee_details = this._committee_details;

    this._form_type = this._activatedRoute.snapshot.paramMap.get('form_id');

    if(this._committee_details) {
      if(this._committee_details.committeeid) {
        this._form99_details = this.committee_details;

        this._form99_details.reason = '';
        this._form99_details.text = '';
        this._form99_details.signee = `${this.committee_details.treasurerfirstname} ${this.committee_details.treasurerlastname}`;
        this._form99_details.additional_email_1 = '-';
        this._form99_details.additional_email_2 = '-';
        this._form99_details.created_at = '';
        this._form99_details.is_submitted = false;  
           
        let formSavedObj: any = {
          'saved': false
        };          

        if(localStorage.getItem(`form_${this._form_type}_details`) === null) {
          localStorage.setItem(`form_${this._form_type}_details`, JSON.stringify(this._form99_details));
        }        

        if(localStorage.getItem(`form_${this._form_type}_saved`) === null) {
          localStorage.setItem(`form_${this._form_type}_saved`, JSON.stringify(formSavedObj));
        }  

        this.isLoading = false;
      }
    }

    this._router
      .events
      .subscribe(val => {
        if(val) {
          if(this._activatedRoute.snapshot.queryParams.step !== this.currentStep) {
            this.currentStep = this._activatedRoute.snapshot.queryParams.step;
            this.step = this._activatedRoute.snapshot.queryParams.step;
          }
          window.scrollTo(0, 0);
        }
      });
  
    this._messageService
      .getMessage()
      .subscribe(res => {
        if(res.validateMessage) {
          this.showValidateBar = res.validateMessage.showValidateBar;
        }
      });
  }

  ngDoCheck(): void {
    if(this.currentStep !== this._activatedRoute.snapshot.queryParams.step) {
      this.currentStep = this._activatedRoute.snapshot.queryParams.step;
      this.step = this._activatedRoute.snapshot.queryParams.step;      
    }
  }

  /**
   * Determines ability to continue.
   *
   */
  public canContinue(): void {
    if(this.frm && this.direction) {
      if(this.direction === 'next') {
        if(this.frm.valid) {
          this.step = this._step;

          this._router.navigate(['/forms/form/99'], { queryParams: { step: this.step } });
        } else if(this.frm === 'preview') {
          this.step = this._step;

          this._router.navigate(['/forms/form/99'], { queryParams: { step: this.step } });
        }
      } else if(this.direction === 'previous') {
        this.step = this._step;

        this._router.navigate(['/forms/form/99'], { queryParams: { step: this.step } });
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
