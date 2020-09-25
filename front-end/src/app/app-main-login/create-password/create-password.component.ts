import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { ManageUserService } from './../../admin/manage-user/service/manage-user-service/manage-user.service';
import { Component, OnInit } from '@angular/core';
import { FormGroup, FormBuilder, FormControl, Validators } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { mustMatch } from 'src/app/shared/utils/forms/validation/must-match.validator';
import { of } from 'rxjs';
import { NgbPanelChangeEvent } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-create-password',
  templateUrl: './create-password.component.html',
  styleUrls: ['./create-password.component.scss']
})
export class CreatePasswordComponent implements OnInit {

  public show = true;
  form: FormGroup;
  passwordAccordionExpanded: boolean = false;
  cmteDetailsAccordionExpanded: boolean = false;
  userEmail: any;

  get password() {
    if (this.form && this.form.get('password')) {
      return this.form.get('password').value;
    }
    return null;
  }

  constructor(private router: Router,
    private _fb: FormBuilder,
    private _activatedRoute: ActivatedRoute,
    private _manageUserService: ManageUserService, 
    private _messageService: MessageService) { }

  ngOnInit() {
    this.initForm();
    this.userEmail = this._activatedRoute.snapshot.queryParams.email;
  }

  public toggleAccordion($event: NgbPanelChangeEvent, acc, accordionType: string) {
    if (accordionType === 'passwordAccordion') {
      if (acc.isExpanded($event.panelId)) {
        this.passwordAccordionExpanded = true;
      }
      else {
        this.passwordAccordionExpanded = false;
      }
    }
    else if (accordionType === 'cmteDetailsAccordion') {
      if (acc.isExpanded($event.panelId)) {
        this.cmteDetailsAccordionExpanded = true;
      }
      else {
        this.cmteDetailsAccordionExpanded = false;
      }
    }
  }



  private initForm() {
    const passwordRegex = '(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[$@$!%*?&])[A-Za-z\\d$@$!%*?&]{8,}';
    this.form = this._fb.group({
      password: new FormControl(null, [Validators.required, 
        Validators.pattern(new RegExp(passwordRegex))]),
      confirmPassword: new FormControl(null, [Validators.required]),
    }, { validator: [mustMatch('password', 'confirmPassword')] });
  }

  public showPassword() {
    this.show = !this.show;
  }

  public submit() {
    // of({
    //   "password_created": true,
    //   "personal_key": "6cc3697b-7d15-4360-bebf-7a4d08d5b921"
    // })
    this._manageUserService.createPassword(this.form.value.password)
      .subscribe((resp:any) => {
        if(resp && resp.password_created){
          this.router.navigate(['/showPersonalKey']).then(success => {
            this._messageService.sendMessage({action:'sendPersonalKey', key: resp.personal_key});
          })
        }
      })
  }

}
