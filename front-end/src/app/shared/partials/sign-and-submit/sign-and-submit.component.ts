import { ChangeDetectionStrategy, Component, Input, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { Subject } from 'rxjs';
import { mustMatch } from './../../utils/forms/validation/must-match.validator';

@Component({
  selector: 'app-sign-and-submit',
  templateUrl: './sign-and-submit.component.html',
  styleUrls: ['./sign-and-submit.component.scss'], 
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [NgbTooltipConfig]
})
export class SignAndSubmitComponent implements OnInit, OnDestroy {

  @Input() formTitle:string;
  
  public form: FormGroup;
  public tooltipPlaceholder : string = 'Placeholder text';
  public emailsOnFile : any = ['test1@fec.gov','test2@fec.gov'];
  private onDestroy$ = new Subject();

  constructor(
    public _config: NgbTooltipConfig,
    private _fb: FormBuilder) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
   }

  ngOnInit() {
    this.initForm();
  }

  ngOnDestroy(){
    this.onDestroy$.next(true);
  }

  public initForm() {
    this.form = this._fb.group({
      sign:new FormControl(null, [Validators.required, Validators.maxLength(100)]),
      submission_date: new FormControl(null, [Validators.required, Validators.maxLength(100)]),
      additionalEmail1: new FormControl(null, [Validators.email, Validators.maxLength(100)]),
      confirmAdditionalEmail1: new FormControl(null, [Validators.email, Validators.maxLength(100)]),
      additionalEmail2: new FormControl(null, [Validators.email, Validators.maxLength(9)]),
      confirmAdditionalEmail2: new FormControl(null, [Validators.email, Validators.maxLength(100)]),
      filingPassword: new FormControl(null, [Validators.required, Validators.maxLength(100)]),
    },{validator:[mustMatch('additionalEmail1','confirmAdditionalEmail1'),mustMatch('additionalEmail2','confirmAdditionalEmail2')]});

  }

  public printPreview(){
    alert('Not implemented yet');
  }

  public updateInfo(){
    alert('Not implemented yet');
  }

}
