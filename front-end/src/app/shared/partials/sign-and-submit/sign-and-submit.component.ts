import { ChangeDetectionStrategy, Component, Input, OnDestroy, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { Subject } from 'rxjs';
import { ScheduleActions } from 'src/app/forms/form-3x/individual-receipt/schedule-actions.enum';
import { F1mService } from './../../../f1m-module/f1m/f1m-services/f1m.service';
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
  @Input() emailsOnFile: any;
  @Input() reportId: string; 
  
  public form: FormGroup;
  public tooltipPlaceholder : string = 'Placeholder text';
  public scheduleAction: ScheduleActions;
  private onDestroy$ = new Subject();
  public saveSuccessful = false;


  constructor(
    public _config: NgbTooltipConfig,
    private _fb: FormBuilder, 
    private _f1mService: F1mService,
    private _cd: ChangeDetectorRef
    ) {
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
      additionalEmail2: new FormControl(null, [Validators.email, Validators.maxLength(100)]),
      confirmAdditionalEmail2: new FormControl(null, [Validators.email, Validators.maxLength(100)]),
      filingPassword: new FormControl(null, [Validators.required, Validators.maxLength(100)]),
    },{validator:[mustMatch('additionalEmail1','confirmAdditionalEmail1'),mustMatch('additionalEmail2','confirmAdditionalEmail2')]});

  }

  public printPreview(){
    alert('Not implemented yet');
  }

  public updateInfo(){
    if(this.form.valid){
      this.scheduleAction = ScheduleActions.add;
      const saveObj = this.form.value;
      saveObj.reportId = this.reportId;
      this._f1mService.saveForm(saveObj,this.scheduleAction, 'saveSignatureAndEmail').subscribe(res=>{
        this.saveSuccessful = true;
        this._cd.detectChanges();
      });
    }
  }

}

