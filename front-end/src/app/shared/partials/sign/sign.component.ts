import { Component, EventEmitter, OnInit, Output, Input } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup, FormControl, NgForm, Validators } from '@angular/forms';
import { Subscription } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { form99 } from '../../interfaces/FormsService/FormsService';
import { FormsService } from '../../services/FormsService/forms.service';
import { MessageService } from '../../services/MessageService/message.service'
import { DialogService } from '../../services/DialogService/dialog.service';
import { ConfirmModalComponent } from '../confirm-modal/confirm-modal.component';

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

  public _need_additional_email_2=false;

  constructor(
    private _activatedRoute: ActivatedRoute,
    private _fb: FormBuilder,
    private _formsService: FormsService,
    private _messageService: MessageService,
    private _dialogService: DialogService
  ) { }

  ngOnInit(): void {
    this.form_type = this._activatedRoute.snapshot.paramMap.get('form_id');

    this.committee_details = JSON.parse(localStorage.getItem('committee_details'));

    this._form_details = JSON.parse(localStorage.getItem(`form_${this.form_type}_details`));

    this._setForm();

    this._messageService
      .getMessage()
      .subscribe(res => {
        if(res.message) {
          if(res.message === 'New form99') {
            this._setForm();
          }
        }
      });  
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
   * Determines ability for a person to leave a page with a form on it.
   *
   * @return     {boolean}  True if able to deactivate, False otherwise.
   */
  public async canDeactivate(): Promise<boolean> {
    if (this.hasUnsavedData()) {
      let result: boolean = null;

      result = await this._dialogService
        .confirm('', ConfirmModalComponent)
        .then(res => {
          let val: boolean = null;

          if(res === 'okay') {
            val = true;
          } else if(res === 'cancel') {
            val = false;
          }

          return val;
        });

      return result;
    } else {
      return true;
    }
  }

  /**
   * Determines if form has unsaved data.
   * TODO: Move to service.
   *
   * @return     {boolean}  True if has unsaved data, False otherwise.
   */
  public hasUnsavedData(): boolean {
    let formSaved: any = JSON.parse(localStorage.getItem(`form_${this.form_type}_saved`)); 

    if(formSaved !== null) {
      let formStatus: boolean = formSaved.saved;

      if(!formStatus) {
        return true;
      }      
    }

    return false;
  }    

  private _setForm(): void {
    if(this._form_details) {
      if(this.form_type === '99') {
        this.type_selected = this._form_details.reason;
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

    this._messageService
      .clearMessage();
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
    let formSaved: boolean = JSON.parse(localStorage.getItem(`form_${this.form_type}_saved`));
    let formStatus: boolean = true;
    this._form_details = JSON.parse(localStorage.getItem(`form_${this.form_type}_details`));

    if(this.frmSignee.controls.signee.valid && this.frmSignee.controls.additional_email_1.valid &&
      this.frmSignee.controls.additional_email_2.valid) {
        console.log("getting additonal emails");
      this._form_details.additional_email_1 = this.frmSignee.get('additional_email_1').value;
      this._form_details.additional_email_2 = this.frmSignee.get('additional_email_2').value;

      localStorage.setItem(`form_${this.form_type}_details`, JSON.stringify(this._form_details));
      
      /*.saveForm({}, {}, this.form_type)*/
      console.log("Accessing Signee_SaveForm ...");
      this._formsService
        .Signee_SaveForm({}, this.form_type)
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
    let formSaved: any = JSON.parse(localStorage.getItem(`form_${this.form_type}_saved`));
    this._form_details = JSON.parse(localStorage.getItem(`form_${this.form_type}_details`));

    if(this.form_type === '99') {
      this._form_details.file = '';

      if(this._form_details.additional_email_1 === '') {
        this._form_details.additional_email_1 = '-';
      }

      if(this._form_details.additional_email_2 === '') {
        this._form_details.additional_email_2 = '-';
      }    
    }    

    localStorage.setItem(`form_${this.form_type}_details`, JSON.stringify(this._form_details));

    if(this.frmSignee.invalid) {
      if(this.frmSignee.get('agreement').value) {
        this.signFailed = false;
      } else {
        this.signFailed = true;
      }
    } else if(this.frmSignee.valid) {
      this.signFailed = false;

      if(!formSaved.form_saved) {
        this._formsService
          .saveForm({}, {}, this.form_type)
          .subscribe(res => {
            if(res) {

              //localStorage.setItem(`form_${this.form_type}_saved`, JSON.stringify({'saved': true}));
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

  public updateAdditionalEmail(e): void {
    if(e.target.value.length) {
     if(e.target.name === 'additional_email_1') {
       this._form_details = JSON.parse(localStorage.getItem(`form_${this.form_type}_details`));

       this._form_details.additional_email_1 = e.target.value;

       localStorage.setItem(`form_${this.form_type}_details`, JSON.stringify(this._form_details));
     } else if(e.target.name === 'additional_email_2') {
       this._form_details = JSON.parse(localStorage.getItem(`form_${this.form_type}_details`));

       this._form_details.additional_email_2 = e.target.value;

       localStorage.setItem(`form_${this.form_type}_details`, JSON.stringify(this._form_details));
     }
    }
  }

  public updateValidation(e): void {
    if(e.target.checked) {
      this.signFailed = false;
    } else if (!e.target.checked) {
      this.signFailed = true;
    }

    console.log('this.signFailed: ', this.signFailed);
  }

  public toggleToolTip(tooltip): void {
    if (tooltip.isOpen()) {
      tooltip.close();
    } else {
      tooltip.open();
    }      
  }

 
  public add_additional_email_2(): void {
    this._need_additional_email_2=true;
    console.log("2nd email needed");
  }
  public remove_additional_email_2(): void {
    this._need_additional_email_2=false;
    console.log("2nd email removed");
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
  public printPriview(): void {
    this._form_details = JSON.parse(localStorage.getItem(`form_${this.form_type}_details`));

   if(this.frmSignee.controls.signee.valid && this.frmSignee.controls.additional_email_1.valid &&
     this.frmSignee.controls.additional_email_2.valid) {
     
     this._form_details.additional_email_1 = this.frmSignee.get('additional_email_1').value;
     this._form_details.additional_email_2 = this.frmSignee.get('additional_email_2').value;

     localStorage.setItem(`form_${this.form_type}_details`, JSON.stringify(this._form_details));
     
     /*.saveForm({}, {}, this.form_type)*/
     console.log("Accessing Sign printPriview ...");
     this._formsService
       .PreviewForm_Preview_sign_Screen({}, this.form_type)
       .subscribe(res => {
         if(res) {
           console.log("Accessing Sign printPriview res ...",res);
         }
       },
       (error) => {
         console.log('error: ', error);
       });
   }
 }
}
