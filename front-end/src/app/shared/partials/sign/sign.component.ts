import { Component, EventEmitter, OnInit, Output, Input } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup, FormControl, NgForm, Validators } from '@angular/forms';
import { Subscription } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { form99 } from '../../interfaces/FormsService/FormsService';
import { FormsService } from '../../services/FormsService/forms.service';
import { MessageService } from '../../services/MessageService/message.service'

@Component({
  selector: 'app-sign',
  templateUrl: './sign.component.html',
  styleUrls: ['./sign.component.scss']
})
export class SignComponent implements OnInit {

  @Input() comittee_details;
  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  public committee_details: any = {};
  public form_type: string = '';
  public type_selected: string = '';
  public signFailed: boolean = false;
  public frmSaved: boolean = false;
  public frmSignee: FormGroup;
  public date_stamp: Date = new Date();
  public hideText: boolean = false;
  public showValidateBar: boolean = false;

  private _subscription: Subscription;
  private _additional_email_1: string = '';
  private _additional_email_2: string = '';
  private _form_details: any = {};
  private _step: string = '';

  constructor(
    private _activatedRoute: ActivatedRoute,
    private _fb: FormBuilder,
    private _formsService: FormsService,
    private _messageService: MessageService
  ) { }

  ngOnInit(): void {
    this.form_type = this._activatedRoute.snapshot.paramMap.get('form_id');

    this.committee_details = JSON.parse(localStorage.getItem('committee_details'));

    this._form_details = JSON.parse(localStorage.getItem(`form_${this.form_type}_details`));

    if(this._form_details) {
      if(this.form_type === '99') {
        this.type_selected = this._form_details.reason;
      }

      if(this._form_details.additional_email_1.length >= 1) {
        if(this._form_details.additional_email_1 === '-') {
          this._form_details.additional_email_1 = '';
        }
      }

      if(this._form_details.additional_email_2.length >= 1) {
        if(this._form_details.additional_email_2 === '-') {
          this._form_details.additional_email_2 = '';
        }
      }

      this.frmSignee = this._fb.group({
        signee: [`${this.committee_details.treasurerfirstname} ${this.committee_details.treasurerlastname}`, Validators.required],
        additional_email_1: [this._form_details.additional_email_1, Validators.email],
        additional_email_2: [this._form_details.additional_email_2, Validators.email],
        agreement: [false, Validators.requiredTrue]
      });
    } else {
      this.frmSignee = this._fb.group({
        signee: [`${this.committee_details.treasurerfirstname} ${this.committee_details.treasurerlastname}`, Validators.required],
        additional_email_1: ['', Validators.email],
        additional_email_2: ['', Validators.email],
        agreement: [false, Validators.requiredTrue]
      });
    }
  }

  ngDoCheck(): void {
    if(this.form_type === '99') {
      let form_99_details: any = JSON.parse(localStorage.getItem(`form_${this.form_type}_details`));
      if(form_99_details) {
        this.type_selected = form_99_details.reason;
      }
    }
  }

  /**
   * Validates the form.
   *
   */
  public validateForm(): void {
    this.showValidateBar = true;
    this._formsService
      .validateForm({}, this.form_type)
      .subscribe(res => {
        if(res) {
            this._messageService
              .sendMessage({
                'validateMessage': {
                  'validate': environment.validateSuccess,
                  'showValidateBar': true                  
                }
              });
        }
      },
      (error) => {
        this._messageService
          .sendMessage({
            'validateMessage': {
              'validate': error.error,
              'showValidateBar': true                  
            }            
          });
      });
  }

  /**
   * Saves a form.
   *
   */
  public saveForm(): void {
    this._form_details = JSON.parse(localStorage.getItem(`form_${this.form_type}_details`));

    if(this.frmSignee.controls.signee.valid && this.frmSignee.controls.additional_email_1.valid &&
      this.frmSignee.controls.additional_email_2.valid) {
      this._form_details.additional_email_1 = this.frmSignee.get('additional_email_1').value;
      this._form_details.additional_email_2 = this.frmSignee.get('additional_email_2').value;

      localStorage.setItem(`form_${this.form_type}_details`, JSON.stringify(this._form_details));
      
      this._formsService
        .saveForm({}, this.form_type)
        .subscribe(res => {
          if(res) {
            this.frmSaved = true;

            let formSavedObj: any = {
              'saved': this.frmSaved
            };

            localStorage.setItem(`form_${this.form_type}_saved`, JSON.stringify(formSavedObj));            
          }
        },
        (error) => {
          console.log('error: ', error);
        });
    }
  }

  /**
   * Submits a form.
   *
   */
  public doSubmitForm(): void {
    console.log('doSubmitForm: ');
    let formSaved: any = JSON.parse(localStorage.getItem(`form_${this.form_type}_saved`));
    this._form_details = JSON.parse(localStorage.getItem(`form_${this.form_type}_details`));
    this._form_details.file = '';

    localStorage.setItem(`form_${this.form_type}_details`, JSON.stringify(this._form_details));

    if(this.frmSignee.invalid) {
      this.signFailed = true;
    } else if(this.frmSignee.valid) {
      this.signFailed = false;

      if(!formSaved.form_saved) {
        this._formsService
          .saveForm({}, this.form_type)
          .subscribe(res => {
            if(res) {
              this._formsService
                .submitForm({}, this.form_type)
                .subscribe(res => {
                  if(res) {
                    this.status.emit({
                      form: this.frmSignee,
                      direction: 'next',
                      step: 'step_5',
                      previousStep: this._step
                    });

                    this._messageService
                      .sendMessage({
                        'form_submitted': true
                      });
                  }
                });              
            }
          },
          (error) => {
            console.log('error: ', error);
          });
      } else {
        this._messageService
          .sendMessage({
            'validateMessage': {
              'validate': '',
              'showValidateBar': false                  
            }            
          });            

        this._formsService
          .submitForm({}, this.form_type)
          .subscribe(res => {
            if(res) {
              this.status.emit({
                form: this.frmSignee,
                direction: 'next',
                step: 'step_5',
                previousStep: this._step
              });

              this._messageService
                .sendMessage({
                  'form_submitted': true
                });
            }
          });
      }
    }
  }

  public updateValidation(e): void {
    if(e.target.checked) {
      this.signFailed = false;
    }
  }

  public toggleToolTip(tooltip): void {
    if (tooltip.isOpen()) {
      tooltip.close();
    } else {
      tooltip.open();
    }      
  }

  /**
   * Goes to the previous step.
   *
   */
  public goToPreviousStep(): void {
    this.frmSaved = false;

    this.status.emit({
      form: {},
      direction: 'previous',
      step: 'step_3',
      previousStep: this._step
    });

    this._messageService
      .sendMessage({
        'validateMessage': {
          'validate': '',
          'showValidateBar': false                  
        }            
      });          
  }

}
