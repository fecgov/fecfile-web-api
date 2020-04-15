import { SignAndSubmitComponent } from './../../shared/partials/sign-and-submit/sign-and-submit.component';
import { ScheduleActions } from './../../forms/form-3x/individual-receipt/schedule-actions.enum';
import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { F1mQualificationComponent } from './../f1m-qualification/f1m-qualification/f1m-qualification.component';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, ViewChild } from '@angular/core';
import { F1mAffiliationComponent } from './../f1m-affiliation/f1m-affiliation/f1m-affiliation.component';
import { F1mService } from './f1m-services/f1m.service';
import { DialogService } from '../../shared/services/DialogService/dialog.service';
import { ConfirmModalComponent, ModalHeaderClassEnum } from '../../shared/partials/confirm-modal/confirm-modal.component';

@Component({
  selector: 'app-f1m',
  templateUrl: './f1m.component.html',
  styleUrls: ['./f1m.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class F1mComponent implements OnInit {

  @ViewChild(F1mAffiliationComponent) affiliationComp : F1mAffiliationComponent;
  @ViewChild(F1mQualificationComponent) qualificationComp : F1mQualificationComponent;
  @ViewChild(SignAndSubmitComponent) signAndSubmitComp : SignAndSubmitComponent;

  public currentStep: string = 'step_1';
  public step: string = 'step_1';
  public type: any;
  public partyType : string = '';
  public scheduleAction = ScheduleActions.add;

  public editMode = 'false';
  public reportId = "";
  public step2data: any;
  public candidateNumber = 1;
  public treasurerData: any = {};
  public affiliationData: any = {};
  public emailsOnFile:any = []; 

  public qualificationData={
    type:'qualification',
    candidates: []
  };

  constructor(
    private _cd: ChangeDetectorRef,
    private _f1mService: F1mService,
    private _dialogService: DialogService, 
    private _messageService:MessageService
    ) { }

  public ngOnInit() {
    this.getPartyType();
  }

  public getPartyType() {
    if(window.localStorage.committeeDetails){
      const committeeData = JSON.parse(window.localStorage.committeeDetails);
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

  public saveAndContinue() {
    if(this.type === 'affiliation'){
      // if(this.f1mAffiliationComp.form.valid){
        this.step2data = this.affiliationComp.form.value;
        // this.step2data.step = this.step;
        console.log(this.step2data);
        this._f1mService.saveForm(this.step2data, this.scheduleAction, 'saveAffiliation').subscribe(res => {
          this.reportId = res.reportId;
          this.setTreasurerInfo(res);
          this.setAffiliationInfo(res);
          this.emailsOnFile.push(res.email_1);
          this.emailsOnFile.push(res.email_2);
          this.next();
        });
      // }
    }
    else if(this.type === 'qualification'){
      // if(this.qualificationComp.form.valid){
      if(!this.qualificationComp.showPart2){
        if(this.qualificationData.candidates.length < 5){
          this.step2data = this.qualificationComp.form.value;
          console.log(this.step2data);
          this._f1mService.saveForm(this.step2data, this.scheduleAction, 'saveQualification').subscribe(res => {
            this.qualificationData.candidates.push(this.step2data);
            this.reportId = res.reportId;
            this.continueToPart2();
            // this.next();
          });
        }
        else{
          this._messageService.sendMessage({formType:'f1m-qualification', action:'showPart2'});
          this.refreshScreen();
        }
      }
      else{
        this._f1mService.saveForm(null,null,null).subscribe(res => {
          this.reportId = res.reportId;
          this.next();
        });
      }
      // }
    }
  }



  private setAffiliationInfo(res: any) {
    this.affiliationData.affiliation_date = res.affiliation_date;
    this.affiliationData.committee_id = res.committee_id;
    this.affiliationData.committee_name = res.committee_name;
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
            this._f1mService.saveForm(saveObj,this.scheduleAction, 'submit').subscribe(res =>{
              alert('Successfully submitted');
            })
          }
          
        });
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
        break;
      case 'step_2':
        this.step = 'step_1';
        break;
      default:
        break;
    }
    this.refreshScreen();
  }
}