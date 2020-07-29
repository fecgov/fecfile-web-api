import { FormsService } from './../../services/FormsService/forms.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { AuthService } from './../../services/AuthService/auth.service';
import { ManageUserService } from './../../../admin/manage-user/service/manage-user-service/manage-user.service';
import { ReportTypeService } from './../../../forms/form-3x/report-type/report-type.service';
import { ActivatedRoute, Router } from '@angular/router';
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
import { ConfirmModalComponent, ModalHeaderClassEnum } from '../confirm-modal/confirm-modal.component';
import { ReportsService } from '../../../reports/service/report.service';

@Component({
  selector: 'app-sign-and-submit',
  templateUrl: './sign-and-submit.component.html',
  styleUrls: ['./sign-and-submit.component.scss'], 
  providers: [NgbTooltipConfig], 
  encapsulation:ViewEncapsulation.None
})
export class SignAndSubmitComponent implements OnInit, OnDestroy{

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

  public showFooter: boolean = false;
  public form: FormGroup;
  
  public submissionDateToolTipText : string = 'Placeholder text';
  public tooltipPlaceholder : string = 'Placeholder text';
  private onDestroy$ = new Subject();
  public saveSuccessful = false;
  public editMode: boolean;

  public username: string = '';
  accordionExpanded: boolean = false;
  modalRef: any;
  public submitterInfo: any = {};

  private phonePipe:PhonePipe = new PhonePipe();
  committeeDetailsFromLocalStorage: any;
  _form_details: any;

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
    private _authService: AuthService,
    private _activatedRoute: ActivatedRoute,
    private _router: Router,
    private _dialogService: DialogService,
    private _reportService: ReportsService,
    private _formsService: FormsService

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
    this.editMode = this._activatedRoute.snapshot.queryParams.edit === 'false' ? false : true;

    //if @Inputs are null, they will be present in the route data, so get them from there. 
    this.initForm();
    this.populateInputsFromRouteIfNeeded();
    // if(this.scheduleAction === ScheduleActions.edit){
      this.populateForm();
    // }
    
    if(localStorage.getItem('committee_details')){
      this.username = JSON.parse(localStorage.getItem('committee_details')).committeeid;
      this._cd.detectChanges();
    }
    this.populateFormMetadata();
    this.populateTreasurerToolTipText();
    this.populateSubmitterInfo();
    this.loggedInUserRole = this._authService.getUserRole();
  }
  
  populateInputsFromRouteIfNeeded() {

    if(this.formType !== '1M'){
      this.showFooter = true;
    }

    if(!this.formTitle){
      this.getTitleAndFormTypeByRouteParam(this._activatedRoute.snapshot.paramMap.get('form_id'));
    }
    if(!this.emailsOnFile || (this.emailsOnFile && this.emailsOnFile.length === 0)){
      this.getEmailsOnFileFromLocalStorage();
    }
    if(!this.reportId){
      this.reportId = this._activatedRoute.snapshot.queryParams.reportId;
    }
    if(!this.scheduleAction){
      this.scheduleAction = ScheduleActions.add;
    }
    if(!this.formData){
      
      this.formData = this.getReportInfo().subscribe(res => {
        this.formData.additionalEmail1 = this.formData.confirmAdditionalEmail1 = res.additionalemail1;
        this.formData.additionalEmail2 = this.formData.confirmAdditionalEmail2 = res.additionalemail2;
        this.populateForm();
      });
      
    }

    if(!this.formType){

    }
  }

  getReportInfo(): Observable<any> {
    if(localStorage.getItem(`form_${this.formType}_report_type`)){
      return of(JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`)));
    }
    else{
      return this.getReportInfoFromApi(this.formType);
    };
  }

  getReportInfoFromApi(formType: any): Observable<any> {
    return this._reportService.getReportInfo(formType,this.reportId);
  }

  getEmailsOnFileFromLocalStorage() {
    if(localStorage.getItem('committee_details')){
      this.committeeDetailsFromLocalStorage = JSON.parse(localStorage.getItem('committee_details'));
      this.emailsOnFile = [];
      if(this.committeeDetailsFromLocalStorage.email_on_file){
        this.emailsOnFile.push(this.committeeDetailsFromLocalStorage.email_on_file);
      }
      if(this.committeeDetailsFromLocalStorage.email_on_file_1){
        this.emailsOnFile.push(this.committeeDetailsFromLocalStorage.email_on_file_1);
      }
    }
  }

  getTitleAndFormTypeByRouteParam(formType: string) {
    switch(formType){
      case '3X':
        if(localStorage.getItem('form_3X_report_type')){
          const reportObj: any = JSON.parse(localStorage.getItem('form_3X_report_type'));
          this.formTitle = `Form 3X / ${reportObj.reporttype} (${reportObj.reporttypedescription})  `;
        }
        if(!this.formType){
          this.formType = '3X';
        }
        break;
      case '99':
        if(localStorage.getItem('form_99_details')){
          const reportObj: any = JSON.parse(localStorage.getItem('form_99_details'));
          this.formTitle = 'Form 99 / Miscellaneous Reports to the FEC';
        }
        if(!this.formType){
          this.formType = '99';
        }
        break;
    }
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
    if(!this.confirmAdditionalEmail1 || !this.confirmAdditionalEmail2 || !this.confirmAdditionalEmail1.valid || !this.confirmAdditionalEmail2.valid){
      return false;
    }
    else{
      return (this.confirmAdditionalEmail1 && this.confirmAdditionalEmail1.value && this.confirmAdditionalEmail1.valid) || (this.confirmAdditionalEmail2 && this.confirmAdditionalEmail2.value && this.confirmAdditionalEmail2.valid);
    }
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
    if(this.formType === '99'){
      this._messageService.sendMessage({action:'print', formType:'F99'});
    }
    else{
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
  }

  public populateForm() {
    // this.form.patchValue({sign: this.formData.sign},{onlySelf:true});
    // this.form.patchValue({submission_date: this.formData.submission_date},{onlySelf:true});
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
      saveObj.formType = this.formType;
      this.saveEmails(saveObj);
    }
  }

  private saveEmails(saveObj: any) {

    if(this.formType === '1M'){
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
          // this._cd.detectChanges();
        }
      });
    }

    else{
      this._reportTypeService.saveAdditionalEmails(saveObj, this.scheduleAction).subscribe(res =>{
          // of({saveObj}).subscribe(res => {
        this.additionalEmailsArray = [];
        if(saveObj.additionalEmail1){
          this.additionalEmailsArray.push(saveObj.additionalEmail1);
        }
        if(saveObj.additionalEmail2){
          this.additionalEmailsArray.push(saveObj.additionalEmail2);
        }
      })
    }

  }

  public removeEmail(email:string){
    this.additionalEmailsArray.splice(this.additionalEmailsArray.indexOf(email),1);
    let saveObj :any = {};
    saveObj.additionalEmail1 = this.additionalEmailsArray[0];
    if(!saveObj.additionalEmail1){
      saveObj.additionalEmail1 = '';
    }
    saveObj.additionalEmail2 = this.additionalEmailsArray[1];
    if(!saveObj.additionalEmail2){
      saveObj.additionalEmail2 = '';
    }
    saveObj.formType = this.formType;
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

  submit(){
    if(this.formType === '1M'){
      let saveObj = this.form.value;
      saveObj.submission_date = this.datePipe.transform(this.today,'yyyy-MM-dd');
      saveObj.reportId = this.reportId ;
      this._f1mService.saveForm(saveObj,ScheduleActions.add, 'submit').subscribe(res =>{
        this.modalRef.close();
        this._messageService.sendMessage({action:'showStep5', data: res});
      });
    }
    else if(this.formType === '3X' || this.formType === '99'){
      this.submit3xOr99();
    }
  }

  public submit3xOr99(): void {
    if (this.editMode) {
      // let doSubmitFormSaved: boolean = false;
      if (this.formType === '3X') {
        let formSaved: any = JSON.parse(localStorage.getItem(`form_${this.formType}_saved_backup`));
        this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type_backup`));

        if (this._form_details === null || typeof this._form_details === 'undefined') {
          this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
        }
        // doSubmitFormSaved = formSaved;
      } 
      else if (this.formType === '99') {
        let formSaved: any = JSON.parse(localStorage.getItem(`form_${this.formType}_saved`));
        this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_details`));
        // doSubmitFormSaved = formSaved.form_saved;
      }

      // if (this.formType === '99') {
      //   this._form_details.file = '';

      //   if (this._form_details.additional_email_1 === '') {
      //     this._form_details.additional_email_1 = '-';
      //   }

      //   if (this._form_details.additional_email_2 === '') {
      //     this._form_details.additional_email_2 = '-';
      //   }
      // }

      // this.validateAdditionalEmails();

      // if (!this.additionalEmail1Invalid && !this.additionalEmail2Invalid) {
        // if (this.formType === '99') {
          // localStorage.setItem(`form_${this.formType}_details`, JSON.stringify(this._form_details));
          // localStorage.setItem(`form_${this.formType}_report_type_backup`, JSON.stringify(this._form_details));
        // }

        // if (this.frmSignee.invalid) {
        //   if (this.frmSignee.get('agreement').value) {
        //     this.signFailed = false;
        //   } else {
        //     this.signFailed = true;
        //   }
        // } else if (this.frmSignee.valid) {
          // this.signFailed = false;

          // if (!doSubmitFormSaved) {
            if (this.formType === '99') {
              this._formsService.Signee_SaveForm({}, this.formType).subscribe(
                saveResponse => {
                  if (saveResponse) {
                    this._formsService.submitForm({}, this.formType).subscribe(res => {
                      if (res) {
                        //console.log(' response = ', res);
                        // this.status.emit({
                        //   form: this.frmSignee,
                        //   direction: 'next',
                        //   step: 'step_5',
                        //   fec_id: res.fec_id,
                        //   previousStep: this._step
                        // });

                        const frmSaved: any = {
                          saved: true
                        };
      
                        // localStorage.setItem('form_3X_saved', JSON.stringify(frmSaved)); ?? is this needed?
      
                        this._router.navigate(['/forms/form/99'], { queryParams: { step: 'step_6', edit: this.editMode, 
                                              fec_id: res.fec_id } });
      
                        this._messageService.sendMessage({
                          form_submitted: true
                        });
                        // this._messageService.sendMessage({
                        //   form_submitted: true
                        // });

                        // this._messageService.sendMessage({
                        //   validateMessage: {
                        //     validate: 'All required fields have passed validation.',
                        //     showValidateBar: true
                        //   }
                        // });
                      }
                    });
                  }
                },
                error => {
                  //console.log('error: ', error);
                }
              );
            } else if (this.formType === '3X') {
              this._reportTypeService.signandSaveSubmitReport(this.formType, 'Submitted').subscribe(res => {
                if (res) {
                  const frmSaved: any = {
                    saved: true
                  };

                  localStorage.setItem('form_3X_saved', JSON.stringify(frmSaved));

                  this._router.navigate(['/forms/form/3X'], { queryParams: { step: 'step_6', edit: this.editMode, 
                                        fec_id: res.fec_id } });

                  this._messageService.sendMessage({
                    form_submitted: true
                  });
                } else {
                  this._router.navigate(['/forms/form/3X'], { queryParams: { step: 'step_6', edit: this.editMode } });
                  this._messageService.sendMessage({
                    form_submitted: false
                  });
                }
              });
            }
            // upto here
          // } else {
          //   this._messageService.sendMessage({
          //     validateMessage: {
          //       validate: '',
          //       showValidateBar: false
          //     }
          //   });
          //   if (this.formType === '99') {
          //     this._formsService.submitForm({}, this.formType).subscribe(res => {
          //       if (res) {
          //         //console.log(' response = ', res);
          //         this.status.emit({
          //           form: this.frmSignee,
          //           direction: 'next',
          //           step: 'step_5',
          //           fec_id: res.fec_id,
          //           previousStep: this._step
          //         });


          //         this._messageService.sendMessage({
          //           form_submitted: true
          //         });
          //       }
          //     });
          //   } else if (this.formType === '3X') {
          //     this._reportTypeService.signandSaveSubmitReport(this.formType, 'Submitted').subscribe(res => {
          //       if (res) {
          //         //console.log(' response = ', res);
          //         this.fec_id = res.fec_id;
          //         /*this.frmSaved = true;
          
          //               let formSavedObj: any = {
          //                 'saved': this.frmSaved
          //               };*/

          //         /*this.status.emit({
          //                 form: this.frmSignee,
          //                 direction: 'next',
          //                 step: 'step_5',
          //                 previousStep: this._step
          //               });*/
          //         this._router.navigate(['/forms/form/3X'], { queryParams: { step: 'step_6', edit: this.editMode,
          //         fec_id: res.fec_id } });
          //         //this._router.navigate(['/submitform/3X']);

          //         this._messageService.sendMessage({
          //           form_submitted: true
          //         });
          //       }
          //     });
          //   }
          // }
        // }
      // }
    } else {
      if (this.formType === '3X') {
        this._dialogService
          .confirm(
            'This report has been filed with the FEC. If you want to change, you must Amend the report',
            ConfirmModalComponent,
            'Warning',
            true,
            ModalHeaderClassEnum.warningHeader,
            null,
            'Return to Reports'
          )
          .then(res => {
            if (res === 'okay') {
              this.ngOnInit();
            } else if (res === 'cancel') {
              this._router.navigate(['/reports']);
            }
          });
      } else if (this.formType === '99') {
        this._dialogService
          .newReport(
            'This report has been filed with the FEC. If you want to change, you must file a new report.',
            ConfirmModalComponent,
            'Warning',
            true,
            false,
            true
          )
          .then(res => {
            if (res === 'okay') {
              this.ngOnInit();
            } else if (res === 'NewReport') {
              localStorage.removeItem('form_99_details');
              localStorage.removeItem('form_99_saved');
              this._setF99Details();
              this._router.navigate(['/forms/form/99'], { queryParams: { step: 'step_1', refresh: true } });
            }
          });
      }
    }
  }

  public previous(){
    if (this.formType === '99') {
      this._router.navigate([],{relativeTo:this._activatedRoute, queryParams: {step:'step_3'}, queryParamsHandling:'merge'});
    } else if (this.formType === '3X') {
      this._router.navigate([`/forms/form/${this.formType}`], { queryParams: { step: 'step_2', edit: this.editMode } });
    }
  }

  private _setF99Details(): void {
    // if (this.committee_details) {
    //   if (this.committee_details.committeeid) {
    //     this._form99Details = this.committee_details;

    //     this._form99Details.reason = '';
    //     this._form99Details.text = '';
    //     this._form99Details.signee = `${this.committee_details.treasurerfirstname} ${this.committee_details.treasurerlastname}`;
    //     this._form99Details.additional_email_1 = '-';
    //     this._form99Details.additional_email_2 = '-';
    //     this._form99Details.created_at = '';
    //     this._form99Details.is_submitted = false;
    //     this._form99Details.id = '';

    //     let formSavedObj: any = {
    //       saved: false
    //     };
    //     localStorage.setItem(`form_99_details`, JSON.stringify(this._form99Details));
    //     localStorage.setItem(`form_99_saved`, JSON.stringify(formSavedObj));
    //   }
    // }
  }
}

