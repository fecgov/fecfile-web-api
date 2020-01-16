import { ScheduleActions } from './../../individual-receipt/schedule-actions.enum';
import { Subscription } from 'rxjs';
import { ReportsService } from 'src/app/reports/service/report.service';
import { ContributionDateValidator } from './../../../../shared/utils/forms/validation/contribution-date.validator';
import { DialogService } from './../../../../shared/services/DialogService/dialog.service';
import { TypeaheadService } from './../../../../shared/partials/typeahead/typeahead.service';
import { ContactsService } from 'src/app/contacts/service/contacts.service';
import { IndividualReceiptComponent } from './../../individual-receipt/individual-receipt.component';
import { Component, OnInit, SimpleChanges, ViewEncapsulation } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormBuilder, Validators } from '@angular/forms';
import { FormsService } from '../../../../shared/services/FormsService/forms.service';
import { IndividualReceiptService } from '../../individual-receipt/individual-receipt.service';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbTooltipConfig, NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
import { UtilService } from '../../../../shared/utils/util.service';
import { MessageService } from '../../../../shared/services/MessageService/message.service';
import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { ReportTypeService } from '../../report-type/report-type.service';
import { F3xMessageService } from '../../service/f3x-message.service';
import { TransactionsMessageService } from '../../../transactions/service/transactions-message.service';
import { TransactionsService } from '../../../transactions/service/transactions.service';
import { SchedEService } from '../sched-e.service';
import { connectableObservableDescriptor } from 'rxjs/internal/observable/ConnectableObservable';

@Component({
  selector: 'app-sched-e',
  templateUrl: './sched-e.component.html',
  styleUrls: ['./sched-e.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe],
  encapsulation: ViewEncapsulation.None
})
export class SchedEComponent extends IndividualReceiptComponent implements OnInit {
  private messageSubscription: Subscription;

  public hideCandidateState = false;
  public coverageStartDate = '';
  public coverageEndDate = '';
  private _currentAggregate = null;
  private _reportId;
  
  public supportOpposeTypes = [
    {'code':'S', 'description':'Support'},
    {'code':'O', 'description':'Oppose'}
  ];

  constructor(_http: HttpClient,
    _fb: FormBuilder,
    _formService: FormsService,
    _receiptService: IndividualReceiptService,
    _contactsService: ContactsService,
    _activatedRoute: ActivatedRoute,
    _config: NgbTooltipConfig,
    _router: Router,
    _utilService: UtilService,
    _messageService: MessageService,
    _currencyPipe: CurrencyPipe,
    _decimalPipe: DecimalPipe,
    _reportTypeService: ReportTypeService,
    _typeaheadService: TypeaheadService,
    _dialogService: DialogService,
    _f3xMessageService: F3xMessageService,
    _transactionsMessageService: TransactionsMessageService,
    _contributionDateValidator: ContributionDateValidator,
    _transactionsService: TransactionsService,
    _reportsService: ReportsService, 
    private _schedEService: SchedEService) {
      super(
        _http,
        _fb,
        _formService,
        _receiptService,
        _contactsService,
        _activatedRoute,
        _config,
        _router,
        _utilService,
        _messageService,
        _currencyPipe,
        _decimalPipe,
        _reportTypeService,
        _typeaheadService,
        _dialogService,
        _f3xMessageService,
        _transactionsMessageService,
        _contributionDateValidator,
        _transactionsService,
        _reportsService
      );

      this.messageSubscription = _messageService.getMessage().subscribe(message => {

        if(message && message.parentFormPopulated){
          this._transactionToEdit = null; // this is being done because this is getting set back to parent transaction due to hierarchical issues. need to investigate further and fix cleanly. 
          this.populateChildData();
        }
      })
   }

   get electionCode(){
     if(this.frmIndividualReceipt && this.frmIndividualReceipt.get('election_code')){
       return this.frmIndividualReceipt.get('election_code').value;
     }
     return null;
   }
   
   get electionYear(){
    if(this.frmIndividualReceipt && this.frmIndividualReceipt.get('cand_election_year')){
      return this.frmIndividualReceipt.get('cand_election_year').value;
    }
    return null;
  }

   get officeSought(){
    if(this.frmIndividualReceipt && this.frmIndividualReceipt.get('cand_office')){
      return this.frmIndividualReceipt.get('cand_office').value;
    }
    return null;
   }
   
   public ngOnInit() {
/*     this.formType = '3X';
    this.abstractScheduleComponent = AbstractScheduleParentEnum.schedMainComponent; */

    super.ngOnInit();
    this._reportId = this._activatedRoute.snapshot.queryParams.reportId;
    this._reportsService.getCoverageDates(this._reportId).subscribe(res => {
      if(res){
        this.coverageStartDate = this._utilService.formatDate(res.cvg_start_date);
        this.coverageEndDate = this._utilService.formatDate(res.cvg_end_date);
      }
    })
    
  }

  /* public ngOnChanges(changes: SimpleChanges) {
    this.formType = '3X';
    super.ngOnChanges(changes);
  } */

  public ngOnDestroy(): void {
    super.ngOnDestroy();
    this.messageSubscription.unsubscribe();
  }

  /**Add any child specific initializations, validators here */
  private populateChildData() {
    if(this.frmIndividualReceipt.controls['disbursement_date']){
      if(this.memoCode){
        this.frmIndividualReceipt.controls['disbursement_date'].setValidators([Validators.required]);
      }else{
        this.frmIndividualReceipt.controls['disbursement_date'].setValidators([this._contributionDateValidator.contributionDate(this.coverageStartDate,this.coverageEndDate), Validators.required]);
      }
      // this.frmIndividualReceipt.controls['disbursement_date'].setValidators([Validators.required]);
      this.frmIndividualReceipt.controls['disbursement_date'].updateValueAndValidity();
    }


    //TODO -- currently for some of the forms api is sending entityTypes as null. Setting it here based on transaction type until that is fixed
    if(this.transactionType === 'IE_CC_PAY'){
      let entityItem = {entityType: "ORG", entityTypeDescription: "Organization", group: "org-group", selected: true};
      this.handleEntityTypeChange(entityItem);
      this.selectedEntityType = entityItem;
    }
  }


  public isFieldVisible(colName: string): boolean{
    if(colName === 'election_other_description'){
      if(this.electionCode  !== 'O'){
        return false;
      }
    }else if(colName === 'cand_office_state'){
      if(this.officeSought === 'P'){
        return false;
      }
    }else if(colName === 'cand_office_district'){
      if(this.officeSought === 'P' || this.officeSought === 'S'){
        return false;
      }
    }

    return true;
  }

  public handleOfficeSoughtChangeForSchedE($event, col){
    this.updateOfficeSoughtFields($event, col);  
  }

  private updateOfficeSoughtFields($event: any, col:any) {
    if ($event && $event.code === 'P') {
      //hide state and district and update validations
      this.updateOfficeSoughtForPresident(col);
    }
    else if ($event && $event.code === 'S') {
      //show state && hide district and update validations
      this.updateOfficeSoughtForSenate(col);
    }
    else if ($event && $event.code === 'H') {
      //show state and district and update validations
      this.updateOfficeSoughtForHouse(col);
    }

    //on any update to officeSought fields, YTD needs to be calculated and set. 
    this.updateYTDAmount();
  }

  private updateYTDAmount() {
    
    console.log('YTD is being recalculated ...');
    let currentExpenditureAmount = this._convertAmountToNumber(this.frmIndividualReceipt.controls['expenditure_amount'].value);
    this._schedEService.getAggregate(this.frmIndividualReceipt.value).subscribe(res => {

      this._currentAggregate = "0";

      if (res && res.ytd_amount) {
        this._currentAggregate = res.ytd_amount;
      }
      this.frmIndividualReceipt.patchValue({ expenditure_aggregate: 
        this._decimalPipe.transform(currentExpenditureAmount + this._convertAmountToNumber(this._currentAggregate), '.2-2') }, { onlySelf: true });
    }, error => {
      this.frmIndividualReceipt.patchValue({ expenditure_aggregate: 
      this._decimalPipe.transform(currentExpenditureAmount , '.2-2') }, { onlySelf: true });
    });
  }

  private _convertAmountToNumber(amount:string){
    if(amount){
      return Number(this.removeCommas(amount));
    }
    return 0;
  }

  public handleOnBlurEvent($event: any, col: any) {
    super.handleOnBlurEvent($event,col);
    this.updateYTDAmount();
  }

  private updateOfficeSoughtForHouse(col:any) {
    this.updateOfficeSoughtValidations('H', col);
  }

  private updateOfficeSoughtForSenate(col:any) {
    this.updateOfficeSoughtValidations('S', col);
  }

  private updateOfficeSoughtForPresident(col:any) {
    this.updateOfficeSoughtValidations('P', col);
  }
  
  private updateOfficeSoughtValidations(office:string, col:any) {
    if(office === 'H'){
      this.frmIndividualReceipt.controls['cand_office_state'].clearValidators();
      this.frmIndividualReceipt.controls['cand_office_state'].setValidators([Validators.required, Validators.maxLength(2)]);
      this.frmIndividualReceipt.controls['cand_office_district'].clearValidators();
      this.frmIndividualReceipt.controls['cand_office_district'].setValidators([Validators.required, Validators.maxLength(2)]);
      this.frmIndividualReceipt.updateValueAndValidity();
    }
    else if(office === 'S'){
      this.frmIndividualReceipt.controls['cand_office_state'].clearValidators();
      this.frmIndividualReceipt.controls['cand_office_state'].setValidators([Validators.required, Validators.maxLength(2)]);
      this.frmIndividualReceipt.controls['cand_office_district'].clearValidators();
      this.frmIndividualReceipt.updateValueAndValidity();

      // also clear any district fields
      this.frmIndividualReceipt.patchValue({'cand_office_district':null}, {onlySelf:true});
    }
    else if(office === 'P'){
      this.frmIndividualReceipt.controls['cand_office_state'].clearValidators();
      this.frmIndividualReceipt.controls['cand_office_district'].clearValidators();
      this.frmIndividualReceipt.updateValueAndValidity();

      // also clear any district & state fields
      this.frmIndividualReceipt.patchValue({'cand_office_state':null}, {onlySelf:true});
      this.frmIndividualReceipt.patchValue({'cand_office_district':null}, {onlySelf:true});
    }
  }

  public handleSelectedIndividual($event: NgbTypeaheadSelectItemEvent, col: any) {
    super.handleSelectedIndividual($event, col);
    this.hiddenFields.push({type:"hidden",name:"payee_entity_id", value:$event.item.entity_id});
  }

  public handleSelectedOrg($event: NgbTypeaheadSelectItemEvent, col: any) {
    super.handleSelectedOrg($event, col);
    // this.hiddenFields.push({type:"hidden",name:"payee_entity_id", value:$event.item.entity_id});
  }

  public handleSelectedCandidate($event: NgbTypeaheadSelectItemEvent, col: any) {
    super.handleSelectedCandidate($event,col);

    //also populate election year here since the variable name is different
    this.hiddenFields.push({type:"hidden",name:"cand_entity_id", value:$event.item.entity_id});
    if($event && $event.item && $event.item.cand_office){
      this.updateOfficeSoughtFields({code:$event.item.cand_office}, col);
    }
  }

   
  public handleCompletingSelectedIndividual($event: NgbTypeaheadSelectItemEvent, col: any) {

    const entity = $event.item;
    let namePrefix = 'completing_';
    const fieldNames = [];
    fieldNames.push('last_name');
    fieldNames.push('first_name');
    fieldNames.push('middle_name');
    fieldNames.push('prefix');
    fieldNames.push('suffix');
    this._patchFormFields(fieldNames, entity, namePrefix);

    this.hiddenFields.push({type:"hidden",name:"completing_entity_id", value:$event.item.entity_id});
  }
 

  public handleElectionCodeChange($event:any, col:any){
    super.handleElectionCodeChange($event, col);
    this.updateYTDAmount();
  }

  public handleMultiStateChange(statesArray:any[], col:any){
    let memoText = statesArray.reduce(this._concatenateStates,'');
    this.frmIndividualReceipt.patchValue({'memo_text':memoText},{onlySelf:true});
  }

  private _concatenateStates(currentConcatenatedValue: string, currentState:any){
    if(currentConcatenatedValue === ''){
      currentConcatenatedValue = currentState.code;
    }else{
      currentConcatenatedValue = currentConcatenatedValue + ", " + currentState.code;
    }
    return currentConcatenatedValue;
  }

  public dateChange(fieldName: string) {

    //Remove valdiations from the other date field if one is present
    if(fieldName === 'disbursement_date' && this.frmIndividualReceipt.controls[fieldName].value){
      this.frmIndividualReceipt.controls['dissemination_date'].clearValidators();
      this.frmIndividualReceipt.controls['dissemination_date'].updateValueAndValidity();
    }
    else if(fieldName === 'dissemination_date' && this.frmIndividualReceipt.controls[fieldName].value){
      this.frmIndividualReceipt.controls['disbursement_date'].clearValidators();
      this.frmIndividualReceipt.controls['disbursement_date'].setValidators([this._contributionDateValidator.contributionDate(this.coverageStartDate,this.coverageEndDate)]);
      this.frmIndividualReceipt.controls['disbursement_date'].updateValueAndValidity();
    }
    else if(!this.frmIndividualReceipt.controls['dissemination_date'].value && !this.frmIndividualReceipt.controls['disbursement_date'].value){
      this.frmIndividualReceipt.controls['disbursement_date'].setValidators([this._contributionDateValidator.contributionDate(this.coverageStartDate,this.coverageEndDate), Validators.required]);
      this.frmIndividualReceipt.controls['dissemination_date'].setValidators([Validators.required]);
      this.frmIndividualReceipt.controls['disbursement_date'].updateValueAndValidity();
      this.frmIndividualReceipt.controls['dissemination_date'].updateValueAndValidity();
      
    }
  }

  private removeCommas(amount: string): string {
    return amount.toString().replace(new RegExp(',', 'g'), '');
  }

  public saveOnly(){
   //add transactionTypeIdentifier until api is ready
   this.hiddenFields.push({type:"hidden",name:"transaction_type_identifier", value:this.transactionType});
   this.hiddenFields.push({type:"hidden",name:"full_election_code", value:this.electionCode + this.electionYear});
    super.saveOnly();
  }
  
  public saveForAddSub(){
    //add transactionTypeIdentifier until api is ready
   this.hiddenFields.push({type:"hidden",name:"transaction_type_identifier", value:this.transactionType});
   this.hiddenFields.push({type:"hidden",name:"full_election_code", value:this.electionCode + this.electionYear});

   //Also change the api for subtranscation until dynamic form fields are fixed.
  //  this.subTransactionInfo.api_call = "/se/schedE"

    super.saveForAddSub();
  }

  public saveAndReturnToParent(){
     //add transactionTypeIdentifier until api is ready
   this.hiddenFields.push({type:"hidden",name:"transaction_type_identifier", value:this.transactionType});
   this.hiddenFields.push({type:"hidden",name:"full_election_code", value:this.electionCode + this.electionYear});

   //Also change the api for subtranscation until dynamic form fields are fixed.
  //  this.subTransactionInfo.api_call = "/se/schedE";

    super.saveAndReturnToParent();
  }

  public returnToParent(scheduleAction: ScheduleActions){
     //add transactionTypeIdentifier until api is ready
     this.hiddenFields.push({type:"hidden",name:"transaction_type_identifier", value:this.transactionType});
     this.hiddenFields.push({type:"hidden",name:"full_election_code", value:this.electionCode + this.electionYear});
  
     //Also change the api for subtranscation until dynamic form fields are fixed.
    //  this.subTransactionInfo.api_call = "/se/schedE";

     super.returnToParent(scheduleAction);
   
  }
}
