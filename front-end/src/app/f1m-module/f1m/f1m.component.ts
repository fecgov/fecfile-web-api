import { ReportsService } from './../../reports/service/report.service';
import { ActivatedRoute, Router } from '@angular/router';
import { SignAndSubmitComponent } from './../../shared/partials/sign-and-submit/sign-and-submit.component';
import { ScheduleActions } from './../../forms/form-3x/individual-receipt/schedule-actions.enum';
import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { F1mQualificationComponent } from './../f1m-qualification/f1m-qualification/f1m-qualification.component';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, ViewChild, OnDestroy } from '@angular/core';
import { F1mAffiliationComponent } from './../f1m-affiliation/f1m-affiliation/f1m-affiliation.component';
import { F1mService } from './f1m-services/f1m.service';
import { DialogService } from '../../shared/services/DialogService/dialog.service';
import { ConfirmModalComponent, ModalHeaderClassEnum } from '../../shared/partials/confirm-modal/confirm-modal.component';
import { TitleCasePipe } from '@angular/common';

@Component({
  selector: 'app-f1m',
  templateUrl: './f1m.component.html',
  styleUrls: ['./f1m.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class F1mComponent implements OnInit, OnDestroy {


  @ViewChild(F1mAffiliationComponent) affiliationComp : F1mAffiliationComponent;
  @ViewChild(F1mQualificationComponent) qualificationComp : F1mQualificationComponent;
  @ViewChild(SignAndSubmitComponent) signAndSubmitComp : SignAndSubmitComponent;

  public currentStep: string = 'step_1';
  public step: string = 'step_1';
  public type: any;
  public partyType : string = '';
  public scheduleAction = ScheduleActions.add;
  public signAndSubmitData : any = null;
  public filingId : string = '######';

  public editMode = 'false';
  public reportId = "";
  public step2data: any;
  public candidateNumber = 1;
  public treasurerData: any = {};
  public affiliationData: any = {};
  public emailsOnFile:any = []; 

  public qualificationData : any = {
    type:'qualification',
    candidates: []
  };

  constructor(
    private _cd: ChangeDetectorRef,
    private _f1mService: F1mService,
    private _dialogService: DialogService, 
    private _messageService:MessageService, 
    private _activatedRoute: ActivatedRoute, 
    private _router: Router,
    private _reportsService: ReportsService,
    public titlecasePipe:TitleCasePipe
    ) { }

  public ngOnInit() {
    this.getPartyType();
    if(this._activatedRoute.snapshot.queryParams.edit){
      this._reportsService.getReportInfo('F1M', this._activatedRoute.snapshot.queryParams.reportId)
      .subscribe((res: any) => {
        this.type = res.establishmentType === 'A' ? 'affiliation' : 'qualification'
        this.step = this._activatedRoute.snapshot.queryParams.edit ? this._activatedRoute.snapshot.queryParams.step : 'step_2';
        this.scheduleAction = ScheduleActions.edit;
        this.reportId = res.reportId;
        this.refreshScreen();
        if(this.type === 'affiliation'){
          this.populateAffiliationData(res);
        }
        else if(this.type === 'qualification'){
          this.populateQualificationData(res);
        }
        this.populateSignAndSubmitData(res);
        
        if(this._activatedRoute.snapshot.queryParams.viewOnly && this._activatedRoute.snapshot.queryParams.viewOnly === 'true'){
          this.scheduleAction = ScheduleActions.view;
          this.updateQueryParams();
          this.setAffiliationInfo(res);
          this.setQualificationInfo(res);
          this.setTreasurerAndEmails(res);
          this._messageService.sendMessage({action:'disableFields'});
        }
        this.refreshScreen();
      })
    }
    
  }
  


  private populateQualificationData(data:any) {
    this.qualificationComp.qualificationData.candidates = data.candidates;
    this.qualificationComp.form.patchValue({candidate_number:(data.candidates.length + 1).toString()},{onlySelf:true});
    this.qualificationComp.formPart2.patchValue({registration_date: data.registration_date}, {onlySelf:true});
    this.qualificationComp.formPart2.patchValue({fifty_first_contributor_date: data.fifty_first_contributor_date}, {onlySelf:true});
    this.qualificationComp.formPart2.patchValue({requirements_met_date: data.requirements_met_date}, {onlySelf:true});
    this.refreshQualificationChildComponent();
    this.refreshScreen();
    
  }

  private populateAffiliationData(data:any) {
    this.affiliationComp.form.patchValue({affiliation_date: data.affiliation_date},{onlySelf:true});
    this.affiliationComp.form.patchValue({committee_id: data.committee_id},{onlySelf:true});
    this.affiliationComp.form.patchValue({committee_name: data.committee_name},{onlySelf:true});
    this.refreshAffiliationChildComponent();
    this.refreshScreen();
  }

  private populateSignAndSubmitData(res: any) {
    this.signAndSubmitData = {
      sign: res.sign_id,
      submission_date: res.submission_date,
      additionalEmail1: res.additional_email_1,
      confirmAdditionalEmail1: res.additional_email_1,
      additionalEmail2: res.additional_email_1,
      confirmAdditionalEmail2: res.additional_email_2,
    }
    this.refreshScreen();
    this.signAndSubmitComp.populateForm();
  }

  
  ngOnDestroy(): void {
    console.log('destroyed');
  }

  public getPartyType() {
    if(window.localStorage.committee_details){
      const committeeData = JSON.parse(window.localStorage.committee_details);
      if(committeeData){
        this.partyType = committeeData.cmte_type_category;
      }
    }
  }

  public changeStep($event) {
    if ($event) {
      if ($event.step) {
        this.step = $event.step;
      }
      if ($event.type) {
        this.type = $event.type;
      }
    }
    this.refreshScreen();
  }

  public refreshScreen() {
    this._cd.detectChanges();
  }

  public skip(){
    this._f1mService.saveForm(null,this.scheduleAction, 'saveQualification').subscribe(res =>{
      this.reportId = res.reportId;
      this.updateQueryParams();
      this.continueToPart2();
    });
  }

  public saveAndContinue(action:any) {
    if(this.type === 'affiliation'){
      this.saveAffiliationData();
    }
    else if(this.type === 'qualification'){
      if(!this.qualificationComp.showPart2){
        this.saveCurrentCandidate(action);
      }
      else{
        this.saveDates();
      }
    }
  }
  
  private saveAffiliationData() {
    if (this.affiliationComp.form.valid) {
      this.step2data = this.affiliationComp.form.value;
      if (this.scheduleAction === ScheduleActions.edit && this.reportId) {
        this.step2data.reportId = this.reportId;
      }
      this._f1mService.saveForm(this.step2data, this.scheduleAction, 'saveAffiliation').subscribe(res => {
        this.reportId = res.reportId;
        this.updateQueryParams();
        this.setAffiliationInfo(res);
        this.setTreasurerAndEmails(res);
        this.next();
      });
    }
  }

  private saveDates() {
    if(this.qualificationComp.formPart2.valid){
      this.step2data = this.qualificationComp.formPart2.getRawValue(); //.getRawValue() is used instead of .value to include disabled fields too
      this.step2data.reportId = this.reportId;
      this._f1mService.saveForm(this.step2data, this.scheduleAction, 'saveDates').subscribe(res => {
        this.reportId = res.reportId;
        this.setQualificationInfo(res);
        this.setTreasurerAndEmails(res);
        this.next();
      });
    }
    else{
      this.qualificationComp.formPart2.markAsDirty();
    }
  }

  private saveCurrentCandidate(action:any) {
    
    if (this.qualificationData.candidates.length < 5 || (action && action.action === 'update')) {
      if(this.qualificationComp.form.valid){
        this.step2data = this.qualificationComp.form.value;
        if (this.reportId) {
          this.step2data.reportId = this.reportId;
        }
        this.step2data.candidate_number = this.step2data.candidate_number.toString();
        let saveCandScheduleAction = action.action === 'update' ? ScheduleActions.edit : ScheduleActions.add;
        this._f1mService.saveForm(this.step2data, saveCandScheduleAction, 'saveCandidate').subscribe(res => {
          this.qualificationData.candidates = res.candidates;
          this.reportId = res.reportId;
          this.updateQueryParams();
          this._messageService.sendMessage({ formType: 'f1m-qualification', action: 'resetAndIncrement' });
          this.refreshQualificationChildComponent();
          this.refreshScreen();
        });
      }
      else {
        this.qualificationComp.form.markAsDirty()
      }
    }
    else {
      this._messageService.sendMessage({ formType: 'f1m-qualification', action: 'showPart2' });
      this.refreshScreen();
    }
  }

  updateQueryParams() {
    this._router.navigate([],{relativeTo:this._activatedRoute, queryParams: {reportId: this.reportId}, queryParamsHandling:'merge'});
  }


  private setTreasurerAndEmails(res: any) {
    this.setTreasurerInfo(res);
    this.emailsOnFile.push(res.email_1);
    this.emailsOnFile.push(res.email_2);
  }

  /**
   * This method refreshes the child component. 
   * Angular will not will not run change detection cycle since 
     qualificationData.candidates is not a new reference for the child input. 
    therefore, have to run the detection cycle in the child component manually.  
  */
  private refreshQualificationChildComponent() {
    this.qualificationComp.cd.detectChanges();
  }

  private refreshAffiliationChildComponent() {
    this.affiliationComp.cd.detectChanges();
  }

  private setAffiliationInfo(res: any) {
    this.affiliationData.affiliation_date = res.affiliation_date;
    this.affiliationData.committee_id = res.committee_id;
    this.affiliationData.committee_name = res.committee_name;
  }

  private setQualificationInfo(res:any){
    this.qualificationData.registration_date = res.registration_date;
    this.qualificationData.fifty_first_contributor_date = res.fifty_first_contributor_date;
    this.qualificationData.requirements_met_date = res.requirements_met_date;
  }

  private setTreasurerInfo(res: any) {
    this.treasurerData.treasurer_first_name = res.treasurer_first_name;
    this.treasurerData.treasurer_last_name = res.treasurer_last_name;
    this.treasurerData.treasurer_middle_name = res.treasurer_middle_name;
    this.treasurerData.treasurer_prefix = res.treasurer_prefix;
    this.treasurerData.treasurer_suffix = res.treasurer_suffix;
  }

  public continueToPart2(){
    this._messageService.sendMessage({formType:'f1m-qualification', action:'showPart2'});
    this.refreshScreen();
  }

  public signAndSubmit() {
    this.next();
  }

  public submit(){
    if(this.signAndSubmitComp.form.valid){
      this._dialogService
      .confirm(
        'I certify that I have examined this statement and to the best of my knowledge and belief it is true, correct, and complete.',
        ConfirmModalComponent,
        'Confirmation',
        true,
        ModalHeaderClassEnum.infoHeaderDark,
        null,
        'Cancel'
      )
        .then(res => {
          if (res === 'okay') {
            let saveObj = this.signAndSubmitComp.form.value;
            saveObj.reportId = this.reportId ;
            this._f1mService.saveForm(saveObj,ScheduleActions.add, 'submit').subscribe(res =>{
              this.filingId = res.fecFilingId;
              this.step = 'step_5';
              this.refreshScreen();
            })
          }
          
        });
    }
    else{
      this.signAndSubmitComp.form.markAsDirty();
    }
  }

  public next(){
    switch (this.step) {
      case 'step_1':
        this.step = 'step_2';
        break;
      case 'step_2':
        this.step = 'step_3';
        break;
      case 'step_3':
        this.step = 'step_4';
        break;
      case 'step_4':
        this.step = 'step_5';
        break;
      default:
        break;
    }
    this.refreshScreen();
  }

  public previous(){
    switch (this.step) {
      case 'step_5':
        this.step = 'step_4';
        break;
      case 'step_4':
        this.step = 'step_3';
        break;
      case 'step_3':
        this.step = 'step_2';
        if(this.type === 'qualification'){
          this.refreshScreen();
          this.refreshQualificationChildComponent();
          this.qualificationComp.showPart2 = true;
          this.refreshQualificationChildComponent();
        }
        break;
      case 'step_2':
        if(this.type === 'qualification' && this.qualificationComp && this.qualificationComp.showPart2){
          this.qualificationComp.showPart2 = false;
          this.refreshQualificationChildComponent();
        } 
        else{
          this.step = 'step_1';
        }
        break;
      default:
        break;
    }
    this.refreshScreen();
  }
}