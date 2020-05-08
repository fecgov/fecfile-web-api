import { TypeaheadService } from './../typeahead/typeahead.service';
import { MessageService } from './../../services/MessageService/message.service';
import { ChangeDetectionStrategy, Component, Input, OnDestroy, OnInit, ChangeDetectorRef, OnChanges, SimpleChanges } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { NgbTooltipConfig, NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
import { Subject, Observable } from 'rxjs';
import { ScheduleActions } from 'src/app/forms/form-3x/individual-receipt/schedule-actions.enum';
import { F1mService } from './../../../f1m-module/f1m/f1m-services/f1m.service';
import { mustMatch } from './../../utils/forms/validation/must-match.validator';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-sign-and-submit',
  templateUrl: './sign-and-submit.component.html',
  styleUrls: ['./sign-and-submit.component.scss'], 
  providers: [NgbTooltipConfig]
})
export class SignAndSubmitComponent implements OnInit, OnDestroy, OnChanges{

 

  @Input() formTitle:string;
  @Input() emailsOnFile: any;
  @Input() reportId: string; 
  @Input() scheduleAction: ScheduleActions;
  @Input() formData: any;

  
  public form: FormGroup;
  public tooltipPlaceholder : string = 'Placeholder text';
  private onDestroy$ = new Subject();
  public saveSuccessful = false;

  public username: string = '';

  constructor(
    public _config: NgbTooltipConfig,
    private _fb: FormBuilder, 
    private _f1mService: F1mService,
    public _cd: ChangeDetectorRef,
    private _messageService:MessageService, 
    private _typeaheadService: TypeaheadService
    ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';

    this._messageService.getMessage().takeUntil(this.onDestroy$).subscribe(message =>{
      if(message && message.action ==='disableFields'){
        if(this.form){
          this.form.disable();
        }
      }
    });
   }



  ngOnInit() {
    this.initForm();
    if(this.scheduleAction === ScheduleActions.edit){
      this.populateForm();
    }
    
    if(localStorage.getItem('committee_details')){
      this.username = JSON.parse(localStorage.getItem('committee_details')).committeeid;
      this._cd.detectChanges();
    }
    
  }

  maskCharacters($event){
    let str = $event.item;
    console.log(str);
  }

  ngOnDestroy(){
    this.onDestroy$.next(true);
  }


  ngOnChanges(changes:SimpleChanges): void {
    console.log('changes' + changes);
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

  public populateForm() {
    this.form.patchValue({sign: this.formData.sign},{onlySelf:true});
    this.form.patchValue({submission_date: this.formData.submission_date},{onlySelf:true});
    this.form.patchValue({additionalEmail1: this.formData.additionalEmail1},{onlySelf:true});
    this.form.patchValue({confirmAdditionalEmail1: this.formData.confirmAdditionalEmail1},{onlySelf:true});
    this.form.patchValue({additionalEmail1: this.formData.additionalEmail1},{onlySelf:true});
    this.form.patchValue({confirmAdditionalEmail2: this.formData.confirmAdditionalEmail2},{onlySelf:true});
  }

  public updateInfo(){
    if(this.isFormValidForUpdating()){
      this.scheduleAction = ScheduleActions.add;
      const saveObj = this.form.value;
      saveObj.reportId = this.reportId;
      this._f1mService.saveForm(saveObj,this.scheduleAction, 'saveSignatureAndEmail').subscribe(res=>{
        this.saveSuccessful = true;
        this._cd.detectChanges();
      });
    }
  }

  private isFormValidForUpdating(): boolean{
    return (this.form && this.form.controls && this.form.controls['sign'].valid && this.form.controls['submission_date'].valid && this.form.controls['additionalEmail1'].valid 
    && this.form.controls['confirmAdditionalEmail1'].valid && this.form.controls['additionalEmail2'].valid  && this.form.controls['confirmAdditionalEmail2'].valid );
  }

  /**
   * Search for entities/contacts when last name input value changes.
   */
  searchLastName = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'last_name');
        } else {
          return Observable.of([]);
        }
      })
    );

  formatterLastName = (x: { last_name: string }) => {
    if (typeof x !== 'string') {
      return x.last_name;
    } else {
      return x;
    }
  };

  public handleSelectedIndividual($event: NgbTypeaheadSelectItemEvent) {
    $event.preventDefault();
    this.form.patchValue({'sign':`${$event.item.first_name} ${$event.item.last_name}`}, {onlySelf:true});
    this._cd.detectChanges();
  }

  public formatTypeaheadItem(result: any) {
    const lastName = result.last_name ? result.last_name.trim() : '';
    const firstName = result.first_name ? result.first_name.trim() : '';
    const middleName = result.middle_name ? result.middle_name.trim() : '';
    const prefix = result.prefix ? result.prefix.trim() : '';
    const suffix = result.suffix ? result.suffix.trim() : '';

    return `${lastName}, ${firstName}, ${middleName}, ${prefix}, ${suffix}`;
  }

  public usernameOnBlur(){
    this.username = JSON.parse(localStorage.getItem('committee_details')).committeeid; 
    this._cd.detectChanges();
  }
}

