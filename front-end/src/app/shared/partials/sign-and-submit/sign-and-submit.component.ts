import { AuthService } from './../../services/AuthService/auth.service';
import { ManageUserService } from './../../../admin/manage-user/service/manage-user-service/manage-user.service';
import { ReportTypeService } from './../../../forms/form-3x/report-type/report-type.service';
import { ActivatedRoute } from '@angular/router';
import { TypeaheadService } from './../typeahead/typeahead.service';
import { MessageService } from './../../services/MessageService/message.service';
import { ChangeDetectionStrategy, Component, Input, OnDestroy, OnInit, ChangeDetectorRef, OnChanges, SimpleChanges, ViewChild, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { NgbTooltipConfig, NgbTypeaheadSelectItemEvent, NgbModalConfig, NgbModal, NgbPanelChangeEvent } from '@ng-bootstrap/ng-bootstrap';
import { Subject, Observable, of } from 'rxjs';
import { ScheduleActions } from 'src/app/forms/form-3x/individual-receipt/schedule-actions.enum';
import { F1mService } from './../../../f1m-module/f1m/f1m-services/f1m.service';
import { mustMatch } from './../../utils/forms/validation/must-match.validator';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { DatePipe } from '@angular/common';
import { PhonePipe } from '../../pipes/phone-number/phone-number.pipe';
import { Roles } from '../../enums/Roles';

@Component({
  selector: 'app-sign-and-submit',
  templateUrl: './sign-and-submit.component.html',
  styleUrls: ['./sign-and-submit.component.scss'], 
  providers: [NgbTooltipConfig], 
  encapsulation:ViewEncapsulation.None
})
export class SignAndSubmitComponent implements OnInit, OnDestroy, OnChanges{

 @ViewChild('content') content:any;

  @Input() formTitle:string;
  @Input() emailsOnFile: any;
  @Input() reportId: string; 
  @Input() scheduleAction: ScheduleActions;
  @Input() formData: any;
  @Input() treasurerData:any;
  @Input() formType:any;

  public loggedInUserRole: Roles;

  public formMetaData:any = {};
  public treasurerToolTipText:string = '';

  checked = false;

  public additionalEmailsArray: any = [];
  public today:Date = new Date();

  
  public form: FormGroup;
  public tooltipPlaceholder : string = 'Placeholder text';
  private onDestroy$ = new Subject();
  public saveSuccessful = false;

  public username: string = '';
  accordionExpanded: boolean = false;
  modalRef: any;
  public submitterInfo: any = {};

  private phonePipe:PhonePipe = new PhonePipe();

  constructor(
    public _config: NgbTooltipConfig,
    private _fb: FormBuilder, 
    private _f1mService: F1mService,
    public _cd: ChangeDetectorRef,
    private _messageService:MessageService, 
    private _typeaheadService: TypeaheadService,
    config: NgbModalConfig, 
    private modalService: NgbModal,
    private datePipe: DatePipe,
    private _reportTypeService: ReportTypeService, 
    private _userService: ManageUserService,
    private _authService: AuthService

    ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
    
    config.backdrop = 'static';
    config.keyboard = false;

    this._messageService.getMessage().takeUntil(this.onDestroy$).subscribe(message =>{
      if(message && message.action ==='disableFields'){
        if(this.form){
          this.form.disable();
        }
      }
    });
   }

   get additionalEmail1() {
    if (this.form && this.form.get('additionalEmail1')) {
      return this.form && this.form.get('additionalEmail1');
    }
    return null;
  }

  get additionalEmail2() {
    if (this.form && this.form.get('additionalEmail2')) {
      return this.form && this.form.get('additionalEmail2');
    }
    return null;
  }

  get confirmAdditionalEmail1() {
    if (this.form && this.form.get('confirmAdditionalEmail1')) {
      return this.form && this.form.get('confirmAdditionalEmail1');
    }
    return null;
  }

  get confirmAdditionalEmail2() {
    if (this.form && this.form.get('confirmAdditionalEmail2')) {
      return this.form && this.form.get('confirmAdditionalEmail2');
    }
    return null;
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
    this.populateFormMetadata();
    this.populateTreasurerToolTipText();
    this.populateSubmitterInfo();
    this.loggedInUserRole = this._authService.getUserRole();
  }
  
  
  populateSubmitterInfo() {
    this._userService.getSignedInUserInfo().subscribe(res=>{
      if(res){
        this.submitterInfo = res;
        if(this.submitterInfo && this.submitterInfo.phone){
          this.submitterInfo.phone = this.phonePipe.transform(this.submitterInfo.phone, 'US');
        }
      }
    })
  }
  
  populateTreasurerToolTipText() {
    switch (this.formType) {
      case '1':
      case '1M':
      case '24':
      case '3':
      case '3X':
      case '3P':
      case '3L':
      case '6':
      case '8':
      case '4':
      case '13':
      case '99':
        this.treasurerToolTipText = 'Only a treasurer or assistant treasurer designated on a Form 1 (Statement of Organization) may sign the report. 104.14(a)';
        break;
      case '2':
        this.treasurerToolTipText = 'The candidate must sign and date the Form 2 (Statement of Candidacy)';
        break;
      case '5':
        this.treasurerToolTipText = 'FEC FORM 5 must be signed by the person making the independent expenditure, who must certify verifiably under penalty of perjury that the expenditure was not made in cooperation, consultation or concert with, or at the request or suggestion of any candidate or authorized committee or agent or a political party committee or its agents. 11 CFR 109.10(e)(1)(v) and (2).';
        break;
      case '7':
        this.treasurerToolTipText = 'Person Designated to sign the report. Title of the person must also be provided.';
        break;
      case '9':
        this.treasurerToolTipText = 'FEC Form 9 must be signed by the person making the electioneering communication, who is making a verified certification under penalty of perjury that the statement is correct.';
        break;
      case '13':
        this.treasurerToolTipText = 'The designated officer (see 11 CFR 104.21(b)) must sign and date the report.';
        break;
      default:
        break;
    }

  }

  public populateFormMetadata(){
    if (localStorage.getItem('committee_details') !== null) {
      this.formMetaData = JSON.parse(localStorage.getItem('committee_details'));
      if(this.formMetaData && this.formMetaData.email_on_file){
        // this.emailsOnFile.push(this.formMetaData.email_on_file);
      }
      if(this.formMetaData && this.formMetaData.email_on_file_1){
        // this.emailsOnFile.push(this.formMetaData.email_on_file_1);
      }
    }
  }

  ngOnDestroy(){
    this.onDestroy$.next(true);
  }

  isSaveBtnDisabled(){
    if(!this.confirmAdditionalEmail1.valid || !this.confirmAdditionalEmail2.valid){
      return false;
    }
    else{
      return (this.confirmAdditionalEmail1 && this.confirmAdditionalEmail1.value && this.confirmAdditionalEmail1.valid) || (this.confirmAdditionalEmail2 && this.confirmAdditionalEmail2.value && this.confirmAdditionalEmail2.valid);
    }
  }

  submit(){
    let saveObj = this.form.value;
    saveObj.submission_date = this.datePipe.transform(this.today,'yyyy-MM-dd');
    saveObj.reportId = this.reportId ;
    this._f1mService.saveForm(saveObj,ScheduleActions.add, 'submit').subscribe(res =>{
      this.modalRef.close();
      this._messageService.sendMessage({action:'showStep5', data: res});
    });
  }


  ngOnChanges(changes:SimpleChanges): void {
    console.log('changes' + changes);
  } 

  public initForm() {
    this.form = this._fb.group({
      submission_date: new FormControl(this.datePipe.transform(this.today,'yyyy-MM-dd'), [Validators.required, Validators.maxLength(100)]),
      additionalEmail1: new FormControl(null, [Validators.email, Validators.maxLength(100)]),
      confirmAdditionalEmail1: new FormControl(null, [Validators.email, Validators.maxLength(100)]),
      additionalEmail2: new FormControl(null, [Validators.email, Validators.maxLength(100)]),
      confirmAdditionalEmail2: new FormControl(null, [Validators.email, Validators.maxLength(100)]),
      filingPassword: new FormControl(null, [Validators.required, Validators.maxLength(100)]),
    },{validator:[mustMatch('additionalEmail1','confirmAdditionalEmail1'),mustMatch('additionalEmail2','confirmAdditionalEmail2')]});

  }

  public printPreview(){
    this._reportTypeService.printPreviewPdf(this.formType,'PrintPreviewPDF',undefined,this.reportId) .subscribe(res => {
        if(res) {
          if (res.hasOwnProperty('results')) {
            if (res['results.pdf_url'] !== null) {
              window.open(res.results.pdf_url, '_blank');
            }
          }
        }
    },
    (error) => {
      console.error('error: ', error);
    });
  }

  public populateForm() {
    this.form.patchValue({sign: this.formData.sign},{onlySelf:true});
    this.form.patchValue({submission_date: this.formData.submission_date},{onlySelf:true});
    this.form.patchValue({additionalEmail1: this.formData.additionalEmail1},{onlySelf:true});
    this.form.patchValue({confirmAdditionalEmail1: this.formData.confirmAdditionalEmail1},{onlySelf:true});
    this.form.patchValue({additionalEmail2: this.formData.additionalEmail2},{onlySelf:true});
    this.form.patchValue({confirmAdditionalEmail2: this.formData.confirmAdditionalEmail2},{onlySelf:true});
    if(this.formData.additionalEmail1){
      this.additionalEmailsArray.push(this.formData.additionalEmail1);
    }
    if(this.formData.additionalEmail2){
      this.additionalEmailsArray.push(this.formData.additionalEmail2);
    }
  }

  public updateInfo(){
    if(this.isFormValidForUpdating()){
      this.scheduleAction = ScheduleActions.add;
      const saveObj : any= {};
      saveObj.additionalEmail1 = this.additionalEmail1.value;
      saveObj.additionalEmail2 = this.additionalEmail2.value;
      saveObj.reportId = this.reportId;
      this.saveEmails(saveObj);
    }
  }

  private saveEmails(saveObj: any) {
    this._f1mService.saveForm(saveObj, this.scheduleAction, 'saveSignatureAndEmail').subscribe(res => {
      this.saveSuccessful = true;
      if (res) {
        this.additionalEmailsArray = [];
        if (res.additional_email_1) {
          this.additionalEmailsArray.push(res.additional_email_1);
        }
        if (res.additional_email_2) {
          this.additionalEmailsArray.push(res.additional_email_2);
        }
        this._cd.detectChanges();
      }
    });
  }

  public removeEmail(email:string){
    this.additionalEmailsArray.splice(this.additionalEmailsArray.indexOf(email),1);
    let saveObj :any = {};
    saveObj.additionalEmail1 = this.additionalEmailsArray[0];
    saveObj.additionalEmail2 = this.additionalEmailsArray[1];
    saveObj.reportId = this.reportId;
    this.saveEmails(saveObj);

    //also remove from form
    if(this.additionalEmail1.value === email){
      this.additionalEmail1.patchValue(null);
      this.confirmAdditionalEmail1.patchValue(null);
    }
    else if(this.additionalEmail2.value === email){
      this.additionalEmail2.patchValue(null);
      this.confirmAdditionalEmail2.patchValue(null);
    }
  }

  private isFormValidForUpdating(): boolean{
    return (this.form && this.form.controls['additionalEmail1'].valid && this.form.controls['confirmAdditionalEmail1'].valid && this.form.controls['additionalEmail2'].valid  && this.form.controls['confirmAdditionalEmail2'].valid );
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

  public open(content) {
    this.modalRef = this.modalService.open(content, { size: 'lg', centered: true, windowClass: 'custom-class' });
    
  }

  public openModal(){
    //first check permissions
    if(this.loggedInUserRole === Roles.Editor || this.loggedInUserRole === Roles.Reviewer){
      this._authService.showPermissionDeniedMessage();
    }
    else{
      this.open(this.content);
    }
  }

  public toggleAccordion($event:NgbPanelChangeEvent,acc){
    if(acc.isExpanded($event.panelId)){
      this.accordionExpanded = true;
    }
    else{
      this.accordionExpanded = false;
    }
  }
}

