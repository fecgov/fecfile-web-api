import { SchedHMessageServiceService } from './../../../sched-h-service/sched-h-message-service.service';
import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { ChangeDetectorRef, Component, OnInit, SimpleChanges, ViewEncapsulation, Input } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbTooltipConfig, NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
import { Observable, Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { ContactsService } from 'src/app/contacts/service/contacts.service';
import { ReportsService } from 'src/app/reports/service/report.service';
import { FormsService } from '../../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../../shared/services/MessageService/message.service';
import { MultiStateValidator } from '../../../../shared/utils/forms/validation/multistate.validator';
import { UtilService } from '../../../../shared/utils/util.service';
import { TransactionsMessageService } from '../../../transactions/service/transactions-message.service';
import { TransactionsService } from '../../../transactions/service/transactions.service';
import { AbstractScheduleParentEnum } from '../../individual-receipt/abstract-schedule-parent.enum';
import { IndividualReceiptService } from '../../individual-receipt/individual-receipt.service';
import { ReportTypeService } from '../../report-type/report-type.service';
import { F3xMessageService } from '../../service/f3x-message.service';
import { SchedEService } from '../sched-e.service';
import { TypeaheadService } from './../../../../shared/partials/typeahead/typeahead.service';
import { DialogService } from './../../../../shared/services/DialogService/dialog.service';
import { ContributionDateValidator } from './../../../../shared/utils/forms/validation/contribution-date.validator';
import { IndividualReceiptComponent } from './../../individual-receipt/individual-receipt.component';
import { ScheduleActions } from './../../individual-receipt/schedule-actions.enum';

@Component({
  selector: 'app-sched-e',
  templateUrl: './sched-e.component.html',
  styleUrls: ['./sched-e.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe],
  encapsulation: ViewEncapsulation.None
})
export class SchedEComponent extends IndividualReceiptComponent implements OnInit {


  @Input() transactionData: any;
  @Input() transactionDataForChild: any;
  @Input() parentTransactionModel: any;

  public hideCandidateState = false;
  public coverageStartDate = '';
  public coverageEndDate = '';
  private _currentAggregate = null;
  private _reportId;
  public candOfficeStatesByTransactionType: any;
  public displayCandStateField = false;
  private _minStateSelectionForMultistate = 6;

  public supportOpposeTypes = [
    { 'code': 'S', 'description': 'Support' },
    { 'code': 'O', 'description': 'Oppose' }
  ];

  private prepopulatedMemoText = 'Multistate independent expenditure, publicly distributed or disseminated in the following states: ';
  public selectedStates: string;
  private multistateMemoTextDelimiter = ' - ';

  private _schedEonDestroy$ = new Subject();
  _originalExpenditureAggregate: any;
  _originalExpenditureAmount: any;

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
    private _multistateValidator: MultiStateValidator,
    private _changeDetector: ChangeDetectorRef,
    private _schedEService: SchedEService,
    _schedHMessageServiceService:SchedHMessageServiceService) {
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
      _reportsService,
      _schedHMessageServiceService
    );

    _messageService.getMessage().takeUntil(this._schedEonDestroy$).subscribe(message => {
      if (message && message.parentFormPopulated && message.component === this.abstractScheduleComponent) {
        this.populateChildData();
      }
    });

    _messageService.getPopulateChildComponentMessage().takeUntil(this._schedEonDestroy$).subscribe(message => {
      if (message && message.populateChildForEdit && message.transactionData && message.component === this.abstractScheduleComponent) {
        this.populateFormForEdit(message.transactionData);
      }
    });

    _messageService.getRollbackChangesMessage().takeUntil(this._schedEonDestroy$).subscribe(message => {
      if (message && message.rollbackChanges) {
        this.rollbackIfSaveFailed();
      }
    })
  }

  get electionCode() {
    if (this.frmIndividualReceipt && this.frmIndividualReceipt.get('election_code')) {
      return this.frmIndividualReceipt.get('election_code').value;
    }
    return null;
  }

  get electionYear() {
    if (this.frmIndividualReceipt && this.frmIndividualReceipt.get('cand_election_year')) {
      return this.frmIndividualReceipt.get('cand_election_year').value;
    }
    return null;
  }

  get officeSought() {
    if (this.frmIndividualReceipt && this.frmIndividualReceipt.get('cand_office')) {
      return this.frmIndividualReceipt.get('cand_office').value;
    }
    return null;
  }


/*   public ngOnChanges(changes: SimpleChanges) {
    this.formType = '3X';
    super.ngOnChanges(changes);
  } */


  public ngOnInit() {
    this.loaded = false;
    this.formFieldsPrePopulated = true;
    this.formType = '3X';
    this._parentTransactionModel = this.parentTransactionModel;
    super.ngOnInit();
    this.abstractScheduleComponent = AbstractScheduleParentEnum.schedEComponent;
    this._reportId = this._activatedRoute.snapshot.queryParams.reportId;
    this._reportsService.getCoverageDates(this._reportId).subscribe(res => {
      if (res) {
        this.coverageStartDate = this._utilService.formatDate(res.cvg_start_date);
        this.coverageEndDate = this._utilService.formatDate(res.cvg_end_date);
      }
    })

  }

  

  public ngOnDestroy(): void {
    this._schedEonDestroy$.next(true);
    super.ngOnDestroy();
  }

  /**Add any child specific initializations, validators here */
  private populateChildData() {
    if (this.frmIndividualReceipt.controls['disbursement_date']) {
      if (this.memoCode) {
        this.frmIndividualReceipt.controls['disbursement_date'].setValidators([Validators.required]);
      } else {
        this.frmIndividualReceipt.controls['disbursement_date'].setValidators([this._contributionDateValidator.contributionDate(this.coverageStartDate, this.coverageEndDate), Validators.required]);
      }
      // this.frmIndividualReceipt.controls['disbursement_date'].setValidators([Validators.required]);
      this.frmIndividualReceipt.controls['disbursement_date'].updateValueAndValidity();
    }

    if (this.frmIndividualReceipt.controls['election_other_description']) {
      this.frmIndividualReceipt.controls['election_other_description'].clearValidators();
      // this.frmIndividualReceipt.controls['election_other_description'].setValidators[();
      this.frmIndividualReceipt.controls['election_other_description'].updateValueAndValidity();
    }

    if(!this.entityTypes || (this.entityTypes && this.entityTypes.length === 0)){
      this.entityTypes = [{ entityType: "ORG", entityTypeDescription: "Organization", group: "org-group"}, { entityType: "IND", entityTypeDescription: "Individual", group: "ind-group"}];
    }
    
    //TODO -- currently for some of the forms api is sending entityTypes as null. Setting it here based on transaction type until that is fixed
    if (this.transactionType === 'IE_CC_PAY' || this.transactionType === 'IE_PMT_TO_PROL') {
      let entityItem = { entityType: "ORG", entityTypeDescription: "Organization", group: "org-group", selected: true };
      this.handleEntityTypeChange(entityItem);
      this.selectedEntityType = entityItem;
    }
    else if (this.transactionType === 'IE_STAF_REIM' || this.transactionType === 'IE_PMT_TO_PROL_MEMO') {
      let entityItem = { entityType: "IND", entityTypeDescription: "Individual", group: "ind-group", selected: true };
      this.handleEntityTypeChange(entityItem);
      this.selectedEntityType = entityItem;
    }

    //for multistate, append some pretext to the memo field
    // let candOfficeTypes = this._utilService.deepClone(this.candidateOfficeTypes);
    if (this.transactionType === 'IE_MULTI') {
      this.frmIndividualReceipt.patchValue({ memo_text_states: this.prepopulatedMemoText }, { onlySelf: true });
      this.candOfficeStatesByTransactionType = this.candidateOfficeTypes.filter(element => element.code === 'P');
      this.displayCandStateField = true;
      if (this.frmIndividualReceipt.controls['cand_office_state']) {
        this.frmIndividualReceipt.controls['cand_office_state'].clearValidators();
        this.frmIndividualReceipt.controls['cand_office_state'].setValidators([Validators.required, Validators.maxLength(2)]);
      }
      if (this.frmIndividualReceipt.controls['cand_office_district']) {
        this.frmIndividualReceipt.controls['cand_office_district'].clearValidators();
      }
      if (this.frmIndividualReceipt.controls['multi_state_options']) {
        this.frmIndividualReceipt.controls['multi_state_options'].setValidators([this._multistateValidator.multistateSelection(this._minStateSelectionForMultistate), Validators.required]);
      }
      this.frmIndividualReceipt.updateValueAndValidity();
      this._changeDetector.detectChanges();
    }
    else {
      this.candOfficeStatesByTransactionType = this.candidateOfficeTypes;
      this._changeDetector.detectChanges();
    }
    
    //if memo transaction, populate candidate information 
    if(this.transactionType.endsWith('_MEMO')){
      this.populateCandidateInfoFromParent();
    }
  }
  populateCandidateInfoFromParent() {
    if(this._parentTransactionModel && this.frmIndividualReceipt){
      this.frmIndividualReceipt.patchValue({cand_last_name:this._parentTransactionModel.candLastName},{onlySelf:true});
      this.frmIndividualReceipt.patchValue({cand_first_name:this._parentTransactionModel.candFirstName},{onlySelf:true});
      this.frmIndividualReceipt.patchValue({cand_middle_name:this._parentTransactionModel.candMiddleName},{onlySelf:true});
      this.frmIndividualReceipt.patchValue({cand_prefix:this._parentTransactionModel.candPrefix},{onlySelf:true});
      this.frmIndividualReceipt.patchValue({cand_suffix:this._parentTransactionModel.candSuffix},{onlySelf:true});
      this.frmIndividualReceipt.patchValue({cand_last_name:this._parentTransactionModel.candLastName},{onlySelf:true});
      this.frmIndividualReceipt.patchValue({payee_cmte_id:this._parentTransactionModel.candFECId},{onlySelf:true});
      this.frmIndividualReceipt.patchValue({beneficiary_cand_id:this._parentTransactionModel.benificiaryCandId},{onlySelf:true});
      this.frmIndividualReceipt.patchValue({cand_office:this._parentTransactionModel.candOffice},{onlySelf:true});
      this.frmIndividualReceipt.patchValue({cand_office_state:this._parentTransactionModel.candOfficeState},{onlySelf:true});
      this.frmIndividualReceipt.patchValue({cand_office_district:this._parentTransactionModel.candOfficeDistrict},{onlySelf:true});
      this.frmIndividualReceipt.patchValue({cand_election_year:this._parentTransactionModel.candElectionYear},{onlySelf:true});
      this.frmIndividualReceipt.patchValue({support_oppose_code:this._parentTransactionModel.candSupportOpposeFlag},{onlySelf:true});
      this.frmIndividualReceipt.patchValue({election_other_description:this._parentTransactionModel.candElectionOtherDesc},{onlySelf:true});
      this.frmIndividualReceipt.patchValue({election_code:this._parentTransactionModel.candElectionCode},{onlySelf:true});

      if(this._parentTransactionModel.candOffice){
        if(this._parentTransactionModel.candOffice === 'P'){
          this.frmIndividualReceipt.controls['cand_office_state'].clearValidators();
          this.frmIndividualReceipt.controls['cand_office_state'].updateValueAndValidity();
          this.frmIndividualReceipt.controls['cand_office_district'].clearValidators();
          this.frmIndividualReceipt.controls['cand_office_district'].updateValueAndValidity();
        }
        else if(this._parentTransactionModel.candOffice === 'S'){
          this.frmIndividualReceipt.controls['cand_office_district'].clearValidators();
          this.frmIndividualReceipt.controls['cand_office_district'].updateValueAndValidity();
        }
      }
    }
  }

  populateFormForEdit(trx: any) {
    //split memoText for IE_MULTI
    this._originalExpenditureAmount = trx.expenditure_amount;
    this._originalExpenditureAggregate = trx.expenditure_aggregate;

    this.updateDateValidators();

    if (trx.transaction_type_identifier === 'IE_MULTI') {
      let memoText = trx.memo_text.substring(trx.memo_text.indexOf(this.multistateMemoTextDelimiter.trim()) + 1).trim();
      let memoTextStates = trx.memo_text.substring(0, trx.memo_text.indexOf(this.multistateMemoTextDelimiter));
      this.frmIndividualReceipt.patchValue({ memo_text: memoText }, { onlySelf: true });
      this.frmIndividualReceipt.patchValue({ memo_text_states: memoTextStates }, { onlySelf: true });

      let statesText = memoTextStates.substring(memoTextStates.indexOf(': ') + 1);
      statesText = statesText.replace(/\s/g, "");
      let states = statesText.split(',');

      this.frmIndividualReceipt.patchValue({ multi_state_options: states }, { onlySelf: true });
    }

    this.frmIndividualReceipt.patchValue({ expenditure_aggregate: this._decimalPipe.transform(this._convertAmountToNumber(trx.expenditure_aggregate), '.2-2') }, { onlySelf: true })
    if (this.frmIndividualReceipt.controls['cand_office']) {
      this.updateOfficeSoughtValidations(this.frmIndividualReceipt.controls['cand_office'].value);
    }
    if (this.hiddenFields && this.hiddenFields.length > 0) {
      this._utilService.addOrEditObjectValueInArray(this.hiddenFields,'hidden','completing_entity_id',trx.completing_entity_id);
      this._utilService.addOrEditObjectValueInArray(this.hiddenFields,'hidden','payee_entity_id',trx.payee_entity_id);
    }
  }

  public isFieldVisible(colName: string): boolean {
    if (colName === 'election_other_description') {
      if (this.electionCode !== 'O') {
        return false;
      }
    } else if (colName === 'cand_office_state') {
      if (this.officeSought === 'P' && this.transactionType !== 'IE_MULTI') {
        return false;
      }
    } else if (colName === 'cand_office_district') {
      if ((this.officeSought === 'P' || this.officeSought === 'S') || (this.transactionType === 'IE_MULTI')) {
        return false;
      }
    }

    return true;
  }

  public handleOfficeSoughtChangeForSchedE($event, col) {
    this.updateOfficeSoughtFields($event, col);
  }

  private updateOfficeSoughtFields($event: any, col: any) {
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
    if (this.scheduleAction === ScheduleActions.edit) {
      this.frmIndividualReceipt.patchValue({
        expenditure_aggregate:
          this._decimalPipe.transform(this._originalExpenditureAggregate - this._originalExpenditureAmount +
            this._convertAmountToNumber(this.frmIndividualReceipt.controls['expenditure_amount'].value), '.2-2')
      }, { onlySelf: true });
    }
    else if (this.transactionType.endsWith('_MEMO')){
      this.frmIndividualReceipt.patchValue({
        expenditure_aggregate:
          this._decimalPipe.transform(this._convertAmountToNumber(this.frmIndividualReceipt.controls['expenditure_amount'].value), '.2-2')
      }, { onlySelf: true });
    }
    else  {
      this._schedEService.getAggregate(this.frmIndividualReceipt.value).subscribe(res => {

        this._currentAggregate = "0";

        if (res && res.ytd_amount) {
          this._currentAggregate = res.ytd_amount;
        }
        this.frmIndividualReceipt.patchValue({
          expenditure_aggregate:
            this._decimalPipe.transform(currentExpenditureAmount + this._convertAmountToNumber(this._currentAggregate), '.2-2')
        }, { onlySelf: true });
      }, error => {
        this.frmIndividualReceipt.patchValue({
          expenditure_aggregate:
            this._decimalPipe.transform(currentExpenditureAmount, '.2-2')
        }, { onlySelf: true });
      });
    }
     
  }

  private _convertAmountToNumber(amount: string) {
    if (amount) {
      return Number(this.removeCommas(amount));
    }
    return 0;
  }

  public handleOnBlurEvent($event: any, col: any) {
    super.handleOnBlurEvent($event, col);
    this.updateYTDAmount();
  }

  private updateOfficeSoughtForHouse(col: any) {
    this.updateOfficeSoughtValidations('H');
  }

  private updateOfficeSoughtForSenate(col: any) {
    this.updateOfficeSoughtValidations('S');
  }

  private updateOfficeSoughtForPresident(col: any) {
    this.updateOfficeSoughtValidations('P');
  }

  private updateOfficeSoughtValidations(office: string) {
    if (office === 'H') {
      this.frmIndividualReceipt.controls['cand_office_state'].clearValidators();
      this.frmIndividualReceipt.controls['cand_office_state'].setValidators([Validators.required, Validators.maxLength(2)]);
      this.frmIndividualReceipt.controls['cand_office_district'].clearValidators();
      this.frmIndividualReceipt.controls['cand_office_district'].setValidators([Validators.required, Validators.maxLength(2)]);
      this.frmIndividualReceipt.updateValueAndValidity();
    }
    else if (office === 'S') {
      this.frmIndividualReceipt.controls['cand_office_state'].clearValidators();
      this.frmIndividualReceipt.controls['cand_office_state'].setValidators([Validators.required, Validators.maxLength(2)]);
      this.frmIndividualReceipt.controls['cand_office_district'].clearValidators();
      this.frmIndividualReceipt.updateValueAndValidity();

      // also clear any district fields
      this.frmIndividualReceipt.patchValue({ 'cand_office_district': null }, { onlySelf: true });
    }
    //TODO -- below logic is very confusing. try to clean this up . 
    else if (office === 'P') {
      if(this.transactionType === 'IE_MULTI' && this.scheduleAction === ScheduleActions.edit) {
        this.frmIndividualReceipt.controls['cand_office_district'].clearValidators();
        this.frmIndividualReceipt.updateValueAndValidity();
        // also clear any district fields
        this.frmIndividualReceipt.patchValue({ 'cand_office_district': null }, { onlySelf: true });
      }

      else if(this.transactionType === 'IE_MULTI' && this.scheduleAction !== ScheduleActions.edit){
        // this.frmIndividualReceipt.controls['cand_office_state'].clearValidators();
        this.frmIndividualReceipt.controls['cand_office_district'].clearValidators();
        this.frmIndividualReceipt.updateValueAndValidity();
        
        // also clear any district & state fields
        this.frmIndividualReceipt.patchValue({ 'cand_office_state': null }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ 'cand_office_district': null }, { onlySelf: true });
      }
      else {
        this.frmIndividualReceipt.controls['cand_office_state'].clearValidators();
        this.frmIndividualReceipt.controls['cand_office_district'].clearValidators();
        this.frmIndividualReceipt.updateValueAndValidity();
        
        // also clear any district & state fields
        this.frmIndividualReceipt.patchValue({ 'cand_office_state': null }, { onlySelf: true });
        this.frmIndividualReceipt.patchValue({ 'cand_office_district': null }, { onlySelf: true });
      }
     
    }
  }

  public handleSelectedIndividual($event: NgbTypeaheadSelectItemEvent, col: any) {
    super.handleSelectedIndividual($event, col);
    this._utilService.addOrEditObjectValueInArray(this.hiddenFields,'hidden','payee_entity_id',$event.item.entity_id);
  }

  public handleSelectedOrg($event: NgbTypeaheadSelectItemEvent, col: any) {
    super.handleSelectedOrg($event, col);
    this._utilService.addOrEditObjectValueInArray(this.hiddenFields,'hidden','payee_entity_id',$event.item.entity_id);
  }

  public handleSelectedCandidate($event: NgbTypeaheadSelectItemEvent, col: any) {
    super.handleSelectedCandidate($event, col);

    //also populate election year here since the variable name is different
    this._utilService.addOrEditObjectValueInArray(this.hiddenFields,'hidden','cand_entity_id',$event.item.entity_id);
    if ($event && $event.item && $event.item.cand_office) {
      this.updateOfficeSoughtFields({ code: $event.item.cand_office }, col);
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

    this._utilService.addOrEditObjectValueInArray(this.hiddenFields,'hidden','completing_entity_id',$event.item.entity_id);
  }


  public handleElectionCodeChange($event: any, col: any) {
    super.handleElectionCodeChange($event, col);
    this.updateYTDAmount();
  }

  public handleMultiStateChange(statesArray: any[], col: any) {
    this.selectedStates = statesArray.reduce(this._concatenateStates, '');

    this.frmIndividualReceipt.patchValue({ 'memo_text_states': this.prepopulatedMemoText + this.selectedStates }, { onlySelf: true });
  }

  private _concatenateStates(currentConcatenatedValue: string, currentState: any) {
    if (currentConcatenatedValue === '') {
      currentConcatenatedValue = currentState.code;
    } else {
      currentConcatenatedValue = currentConcatenatedValue + ", " + currentState.code;
    }
    return currentConcatenatedValue;
  }

  public dateChange(fieldName: string) {

    //Remove valdiations from the other date field if one is present
    if (fieldName === 'disbursement_date' && this.frmIndividualReceipt.controls[fieldName] && this.frmIndividualReceipt.controls[fieldName].value) {
      this.frmIndividualReceipt.controls['dissemination_date'].clearValidators();
      this.frmIndividualReceipt.controls['dissemination_date'].updateValueAndValidity();
    }
    else if (fieldName === 'dissemination_date' && this.frmIndividualReceipt.controls[fieldName] && this.frmIndividualReceipt.controls[fieldName].value) {
      this.frmIndividualReceipt.controls['disbursement_date'].clearValidators();
      this.frmIndividualReceipt.controls['disbursement_date'].setValidators([this._contributionDateValidator.contributionDate(this.coverageStartDate, this.coverageEndDate)]);
      this.frmIndividualReceipt.controls['disbursement_date'].updateValueAndValidity();
    }
    else if ((this.frmIndividualReceipt.controls['dissemination_date'] && this.frmIndividualReceipt.controls['disbursement_date']) &&
     (!this.frmIndividualReceipt.controls['dissemination_date'].value && !this.frmIndividualReceipt.controls['disbursement_date'].value)) {
      this.frmIndividualReceipt.controls['disbursement_date'].setValidators([this._contributionDateValidator.contributionDate(this.coverageStartDate, this.coverageEndDate), Validators.required]);
      this.frmIndividualReceipt.controls['dissemination_date'].setValidators([Validators.required]);
      this.frmIndividualReceipt.controls['disbursement_date'].updateValueAndValidity();
      this.frmIndividualReceipt.controls['dissemination_date'].updateValueAndValidity();

    }
  }

  /**
   * This method will run through the dateChange event on both fields and based on which fields are present
   * it will update the validators. 
   */
  private updateDateValidators() {
    this.dateChange('disbursement_date');
    this.dateChange('dissemination_date');
  }

  private removeCommas(amount: string): string {
    return amount.toString().replace(new RegExp(',', 'g'), '');
  }

  public saveOnly() {
    this.addSchedESpecificMetadata();
    super.saveOnly();
    this.rollbackIfSaveFailed();
  }

  public updateOnly() {
    this.addSchedESpecificMetadata();
    super.updateOnly();
  }

  public saveForAddSub() {
    this.addSchedESpecificMetadata();
    super.saveForAddSub();
  }

  public saveAndReturnToParent() {
    this.addSchedESpecificMetadata();
    super.saveAndReturnToParent();
  }

  public returnToParent(scheduleAction: ScheduleActions) {
    this.addSchedESpecificMetadata();
    super.returnToParent(scheduleAction);
  }

  private addSchedESpecificMetadata() {
    if(this.hiddenFields && this.electionCode && this.electionYear){
      this._utilService.addOrEditObjectValueInArray(this.hiddenFields, 'hidden','full_election_code', this.electionCode[0] + this.electionYear);

    }
  }


  private rollbackIfSaveFailed() {
    if (this._rollbackAfterUnsuccessfulSave) {
      if (this.transactionType === 'IE_MULTI') {
        let originalMemoText = (this.frmIndividualReceipt.controls['memo_text'].value).split('-');
        if (originalMemoText && originalMemoText.length > 1) {
          originalMemoText = originalMemoText[1];
          this.frmIndividualReceipt.patchValue({ memo_text: originalMemoText }, { onlySelf: true });
        }
      }
    }
  }


  /**
   * Search for Candidate when first name input value changes.
   */
  searchCandLastName = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          let result = this._typeaheadService.getContacts(searchText, 'cand_last_name');
          if (this.transactionType === 'IE_MULTI') {
            result = result.map(contacts => contacts.filter(element => element.cand_office === 'P'))
          }
          return result;
        } else {
          return Observable.of([]);
        }
      })
    );

  /**
   * Search for Candidate when first name input value changes.
   */
  searchCandFirstName = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          let result = this._typeaheadService.getContacts(searchText, 'cand_first_name');
          if (this.transactionType === 'IE_MULTI') {
            result = result.map(contacts => contacts.filter(element => element.cand_office === 'P'))
          }
          return result;
        } else {
          return Observable.of([]);
        }
      })
    );

  /**
   * Search for Committee Payees when Committee ID input value changes.
   */
  searchPayeeCommitteeId = (text$: Observable<string>) =>
  text$.pipe(
    debounceTime(500),
    distinctUntilChanged(),
    switchMap(searchText => {
      const searchTextUpper = searchText.toUpperCase();

      if (
        searchTextUpper === 'C' ||
        searchTextUpper === 'C0' ||
        searchTextUpper === 'C00' ||
        searchTextUpper === 'C000'
      ) {
        return Observable.of([]);
      }

      if (searchText) {
        let result = this._typeaheadService.getContacts(searchText, 'payee_cmte_id');
          if (this.transactionType === 'IE_MULTI') {
            result = result.map(contacts => contacts.filter(element => element.cand_office === 'P'))
          }
          return result;
      } else {
        return Observable.of([]);
      }
    })
  );

  formatterPayeeCommitteeId = (x: { payee_cmte_id: string }) => {
    if (typeof x !== 'string') {
      return x.payee_cmte_id;
    } else {
      return x;
    }
  };

    /**
   * Format a Candidate Entity to display in the Payee Committee ID type ahead.
   *
   * @param result formatted item in the typeahead list
   */
  public formatTypeaheadPayeeCommitteeId(result: any) {
    const payeeCmteID = result.payee_cmte_id ? result.payee_cmte_id.trim() : '';
    const candidateId = result.beneficiary_cand_id ? result.beneficiary_cand_id.trim() : '';
    const lastName = result.cand_last_name ? result.cand_last_name.trim() : '';
    const firstName = result.cand_first_name ? result.cand_first_name.trim() : '';
    let office = result.cand_office ? result.cand_office.toUpperCase().trim() : '';
    if (office) {
      if (office === 'P') {
        office = 'Presidential';
      } else if (office === 'S') {
        office = 'Senate';
      } else if (office === 'H') {
        office = 'House';
      }
    }
    const officeState = result.cand_office_state ? result.cand_office_state.trim() : '';
    const officeDistrict = result.cand_office_district ? result.cand_office_district.trim() : '';

    return `${payeeCmteID}, ${candidateId}, ${lastName}, ${firstName}, ${office},
      ${officeState}, ${officeDistrict}`;
  }
}
