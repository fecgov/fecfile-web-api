import { AuthService } from './../../shared/services/AuthService/auth.service';
import { ManageUserService } from './../../admin/manage-user/service/manage-user-service/manage-user.service';
import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { transition } from '@angular/animations';
import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { FormGroup, FormBuilder, FormControl, Validators } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class RegisterComponent implements OnInit {

  form: FormGroup;
  public phoneOptions: any[] = [{code:'V', desc:'Voice'},
                          {code:'T', desc:'Text'}]
  registerToken: any;

  constructor(private router: Router,
    private _fb: FormBuilder, 
    private _messageService: MessageService, 
    private _manageUserService: ManageUserService, 
    private _authService: AuthService,
    private _activateRoute: ActivatedRoute) { }



  ngOnInit() {
    this.registerToken = this._activateRoute.snapshot.queryParams.register_token;
    this.initForm();
  }

  private initForm() {
    this.form = this._fb.group({
      emailOrPhoneOption: new FormControl(null, [Validators.required]),
      email: new FormControl({ value: null, disabled: true }, [Validators.email, Validators.maxLength(100)]),
      voiceOrTextOption: new FormControl({ value: 'V', disabled: true }, []),
      phoneNumber: new FormControl({ value: null, disabled: true }, [])
    });
  }

  submit() {
    //submit();
    let formData : any = {};
    formData.register_token = this.registerToken;
    if(this.form.value.emailOrPhoneOption === 'email'){
      formData.id = 'EMAIL';
      formData.email = this.form.value.email;
    }
    else if(this.form.value.emailOrPhoneOption === 'phone'){
      if(this.form.value.voiceOrTextOption === 'V'){
        formData.id = 'CALL';
      }
      else if(this.form.value.voiceOrTextOption === 'T'){
        formData.id = 'TEXT';
      }
      formData.contact = this.form.value.phoneNumber;
    }

    this._manageUserService.authenticateUserWithRegToken(formData)
    .subscribe(message => {
      if(message){
        if(message.is_allowed){
          this._authService.doSignIn(message.token);
          this.router.navigate(['enterSecCode'],{queryParams:{registerToken:'dummy',option:this.form.value.emailOrPhoneOption}}).then(resp => {
            this._messageService.sendMessage({action:'sendSecurityCode', selectedOption:this.form.value.emailOrPhoneOption, data:this.form.value, entryPoint:'registration'});
          });
        }
      }
    })    
  }

  radioOptionChanged(event:any){
    if(event.target.value === 'email'){
      this.form.controls['voiceOrTextOption'].disable();
      this.form.controls['phoneNumber'].disable();
      this.form.controls['email'].enable();
    }
    else if(event.target.value === 'phone'){
      this.form.controls['voiceOrTextOption'].enable();
      this.form.controls['phoneNumber'].enable();
      this.form.controls['email'].disable();
    }
    else{
      this.form.controls['voiceOrTextOption'].disable();
      this.form.controls['phoneNumber'].disable();
      this.form.controls['email'].disable();
    }
  }

  public back(){
    this.router.navigate(['']);
  }

  public clear(){
    this.form.controls['voiceOrTextOption'].enable();
    this.form.controls['phoneNumber'].enable();
    this.form.controls['email'].enable();

    this.form.reset();

    this.form.controls['voiceOrTextOption'].disable();
    this.form.controls['phoneNumber'].disable();
    this.form.controls['email'].disable();

  }


}
