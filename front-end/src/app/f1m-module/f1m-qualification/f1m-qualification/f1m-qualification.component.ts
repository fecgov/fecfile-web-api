import { ChangeDetectionStrategy, ChangeDetectorRef, Component, EventEmitter, Input, OnDestroy, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
import { Observable, Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { TypeaheadService } from '../../../shared/partials/typeahead/typeahead.service';
import { ScheduleActions } from './../../../forms/form-3x/individual-receipt/schedule-actions.enum';
import { ApiService } from './../../../shared/services/APIService/api.service';
import { F1mService } from './../../f1m/f1m-services/f1m.service';

@Component({
  selector: 'app-f1m-qualification',
  templateUrl: './f1m-qualification.component.html',
  styleUrls: ['./f1m-qualification.component.scss'],
  // changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None
})
export class F1mQualificationComponent implements  OnInit , OnDestroy{
  
  
  @Input() candidateNumber:number;
  @Input() qualificationData: any;
  @Input() reportId: string;
  @Input() scheduleAction:ScheduleActions
  @Output() addCandidateEvent: EventEmitter<any> = new EventEmitter();

  private onDestroy$ = new Subject();
  
  public form:FormGroup;
  public formPart2:FormGroup;
  public formFields :any = [];
  public subTransactionTableType: any;
  public subTransactions: any;
  public subTransactionInfo: any;
  public width = '23px';
  public tooltipPlaceholder = 'Placeholder text';
  public showPart2:boolean = false;
  public isEditCandidateMode: boolean = false;


  public candidate_offices=[];
  public states=[];

  constructor(
    private _fb: FormBuilder,
    private _typeaheadService: TypeaheadService,
    private _apiService: ApiService,
    public cd: ChangeDetectorRef,
    private _messageService: MessageService,
    private _f1mService: F1mService
  ) { 
      this._messageService.getMessage().takeUntil(this.onDestroy$).subscribe(message =>{
        if(message && message.formType === 'f1m-qualification' && message.action ==='resetAndIncrement'){
          this.resetFormAndIncrementCandidate();
        }
        else if(message && message.formType === 'f1m-qualification' && message.action === 'showPart2'){
          this.showPart2 = true;
          this.setRegistrationDate();
          this.setRequirementsMetDate();
          this.cd.detectChanges();
        }
        else if(message && message.formType === 'f1m-qualification' && message.action === 'editCandidate'){
          this.editCandidate(message.candidate);
        }
        else if(message && message.formType === 'f1m-qualification' && message.action === 'trashCandidate'){
          this.trashCandidate(message.candidate);
        }
        else if(message && message.action ==='disableFields'){
          if(this.form){
            this.form.disable();
            this.formPart2.disable();
          }
        }
        else if(message && message.action === 'refreshScreen' && message.qualificationData){
          this.qualificationData = message.qualificationData;
          this.cd.detectChanges();
        }
      });
  }

  public ngOnInit() {
    this.initStates();
    this.initCandidateOffices();
    this.initForm();
    this.initiFormPart2();
  }

  ngOnDestroy(){
    this._messageService.clearMessage();
    this.onDestroy$.next(true);
  }


  private initStates() {
    this._apiService.getStates().subscribe((resp : any) => {
      if(resp && resp.data && resp.data.states){
        this.states = resp.data.states;
        this.cd.detectChanges();
      }
    });
  }
  
  private initCandidateOffices() {
    this._apiService.getOfficesSought().subscribe((resp : any)=>{
      if(resp && resp.data && resp.data.officeSought){
        this.candidate_offices = resp.data.officeSought;
        this.cd.detectChanges();
      }
    });       
  }

  public addCandidate(){
    if(this.isEditCandidateMode){
      this.addCandidateEvent.emit({action:'update'});
    }
    else{
      this.addCandidateEvent.emit({action:'create'});
    }
  }

  public editCandidate(candidate: any) {
    this.isEditCandidateMode = true;
    this.cd.detectChanges();
    this.populateCandidateData(candidate);
    this.cd.detectChanges();
  }

  public trashCandidate(candidate: any) {
    // this._f1mService.trashCandidate
    // this.isEditCandidateMode = true;
    // this.cd.detectChanges();
    // this.populateCandidateData(candidate);
    // this.cd.detectChanges();
  }

  private populateCandidateData(candidate: any) {
    this.form.patchValue({ candidate_id: candidate.candidate_id }, { onlySelf: true });
    this.form.patchValue({ cand_last_name: candidate.cand_last_name }, { onlySelf: true });
    this.form.patchValue({ cand_first_name: candidate.cand_first_name }, { onlySelf: true });
    this.form.patchValue({ cand_middle_name: candidate.cand_middle_name }, { onlySelf: true });
    this.form.patchValue({ cand_prefix: candidate.cand_prefix }, { onlySelf: true });
    this.form.patchValue({ cand_suffix: candidate.cand_suffix }, { onlySelf: true });
    this.form.patchValue({ cand_office: candidate.cand_office }, { onlySelf: true });
    this.form.patchValue({ cand_office_state: candidate.cand_office_state }, { onlySelf: true });
    this.form.patchValue({ cand_office_district: candidate.cand_office_district }, { onlySelf: true });
    this.form.patchValue({ contribution_date: candidate.contribution_date }, { onlySelf: true });
    this.form.patchValue({ candidate_number: candidate.candidate_number }, { onlySelf: true });
  }

  private resetFormAndIncrementCandidate() {
    this.form.reset();
    this.candidateNumber++;
    this.form.patchValue({candidate_number:this.candidateNumber.toString()},{onlySelf:true});
  }

  public isShowChildTransactions(){
    return true;
  }

  public dateChanged(dateType: string){
    if(dateType === 'fifty_first_contributor_date'){
      this.setRequirementsMetDate()
    }
  }

  /**
   * This method should get the next available candidate_number based on the current candidates in the array
   * This is used in case if there are any gaps in candidate numbers due to deletion of a candidate from 
   * middle of the array
   * 
   */
  public getNextCandidateNumber(): number{
    let counter:number = 1;
    if(this.qualificationData.candidates && this.qualificationData.candidates.length > 0){
      this.qualificationData.candidates.sort((a,b) => a.candidate_number > b.candidate_number ? 1 : -1);
      this.qualificationData.candidates.forEach(candidate => {
        if(Number(candidate.candidate_number) === counter){
          counter++;
        }
        else{
          return counter;
        }
      });
    }
    return counter;
  }

  public initForm() {
    this.form = this._fb.group({
      candidate_id: new FormControl(null, [Validators.required, Validators.maxLength(9)]),
      cand_last_name: new FormControl(null, [Validators.required, Validators.maxLength(30)]),
      cand_first_name: new FormControl(null, [Validators.required, Validators.maxLength(20)]),
      cand_middle_name: new FormControl(null, [Validators.maxLength(20)]),
      cand_prefix: new FormControl(null, [ Validators.maxLength(10)]),
      cand_suffix: new FormControl(null, [ Validators.maxLength(10)]),
      cand_office: new FormControl(null, [Validators.required, Validators.maxLength(100)]),
      cand_office_state: new FormControl(null, [Validators.required, Validators.maxLength(100)]),
      cand_office_district: new FormControl(null, [Validators.required, Validators.maxLength(2)]),
      contribution_date: new FormControl(null, [Validators.required, Validators.maxLength(100)]),
      candidate_number: new FormControl(this.candidateNumber.toString())
    });
  }

  initiFormPart2() {
    this.formPart2 = this._fb.group({
      registration_date: new FormControl({value:null, disabled:true}, [Validators.required]),
      fifty_first_contributor_date: new FormControl(null, [Validators.required]),
      requirements_met_date: new FormControl({value:null, disabled:true}, [Validators.required])
    });
  }


  private setRequirementsMetDate() {
    this._f1mService.getDates('get_cmte_met_req_date', this.reportId ,this.formPart2.value.fifty_first_contributor_date).subscribe(res => {
      if(this.formPart2){
        this.formPart2.patchValue({requirements_met_date:res.requirements_met_date},{onlySelf:true});
      }
    });
  }


  private setRegistrationDate() {
    this._f1mService.getDates('get_original_reg_date').subscribe(res => {
      if(this.formPart2){
        this.formPart2.patchValue({registration_date:res.registration_date},{onlySelf:true});
        this.cd.detectChanges();
      }
    });
  }

  public cancel(){
    this.form.reset();
    this.isEditCandidateMode = false;
  }

  /**
   * Search for entities when Candidate ID input value changes.
   */
  searchCandidateId = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if(searchText.length === 0){
          this.clearCandidateInfo();
        }
        else if (searchText.length < 3) {
          return Observable.of([]);
        } else {
          const searchTextUpper = searchText.toUpperCase();
          return this._typeaheadService.getContacts(searchTextUpper, 'cand_id');
        }
      })
    );

    /**
   * Search for Candidates when last name input value changes.
   */
  searchCandLastName = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'cand_last_name');
        } else {
          this.clearCandidateInfo();
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
          return this._typeaheadService.getContacts(searchText, 'cand_first_name');
        } else {
          this.clearCandidateInfo();
          return Observable.of([]);
        }
      })
    );

    /**
   * format the value to display in the input field once selected from the typeahead.
   *
   * For some reason this gets called for all typeahead fields despite the binding in the
   * template to the Candidate ID field.  In these cases return x to retain the value in the
   * input for the other typeahead fields.
   */
  formatterCandidateId = (x: { beneficiary_cand_id: string }) => {
    if (typeof x !== 'string') {
      return x.beneficiary_cand_id;
    } else {
      return x;
    }
  };

    /**
   * format the value to display in the input field once selected from the typeahead.
   *
   * For some reason this gets called for all typeahead fields despite the binding in the
   * template to the last name field.  In these cases return x to retain the value in the
   * input for the other typeahead fields.
   */
  formatterCandLastName = (x: { cand_last_name: string }) => {
    if (typeof x !== 'string') {
      return x.cand_last_name;
    } else {
      return x;
    }
  };

  /**
   * format the value to display in the input field once selected from the typeahead.
   *
   * For some reason this gets called for all typeahead fields despite the binding in the
   * template to the first name field.  In these cases return x to retain the value in the
   * input for the other typeahead fields.
   */
  formatterCandFirstName = (x: { cand_first_name: string }) => {
    if (typeof x !== 'string') {
      return x.cand_first_name;
    } else {
      return x;
    }
  };


/**
   * Populate the fields in the form with the values from the selected Candidate.
   *
   * @param $event The mouse event having selected the contact from the typeahead options.
   */
  public handleSelectedCandidate($event: NgbTypeaheadSelectItemEvent) {
    // preventDefault this is used so NgbTypeAhead doesn't automatically save the whole object on modal close
    $event.preventDefault(); 
    const entity = $event.item;
    
    this.form.patchValue({'cand_last_name':entity.cand_last_name}, {onlySelf:true});
    this.form.patchValue({'cand_first_name':entity.cand_first_name}, {onlySelf:true});
    this.form.patchValue({'cand_middle_name':entity.cand_middle_name}, {onlySelf:true});
    this.form.patchValue({'cand_prefix':entity.cand_prefix}, {onlySelf:true});
    this.form.patchValue({'cand_suffix':entity.cand_suffix}, {onlySelf:true});
    this.form.patchValue({'candidate_id':entity.beneficiary_cand_id}, {onlySelf:true});
    this.form.patchValue({'cand_office':entity.cand_office}, {onlySelf:true});
    this.form.patchValue({'cand_office_state':entity.cand_office_state}, {onlySelf:true});
    this.form.patchValue({'cand_office_district':entity.cand_office_district}, {onlySelf:true});
  }

   /**
   * Format an entity to display in the Candidate ID type ahead.
   *
   * @param result formatted item in the typeahead list
   */
  public formatTypeaheadCandidateId(result: any) {
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

    return `${candidateId}, ${lastName}, ${firstName}, ${office}, ${officeState}, ${officeDistrict}`;
  }


   /**
   * Format an entity to display in the Candidate type ahead field.
   *
   * @param result formatted item in the typeahead list
   */
  public formatTypeaheadCandidate(result: any) {
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

    return `${lastName}, ${firstName}, ${office}, ${officeState}, ${officeDistrict}`;
  }

  clearCandidateInfo(){
    this.form.controls['candidate_id'].reset();
    this.form.controls['cand_last_name'].reset();
    this.form.controls['cand_first_name'].reset();
    this.form.controls['cand_middle_name'].reset();
    this.form.controls['cand_prefix'].reset();
    this.form.controls['cand_suffix'].reset();
    this.form.controls['cand_office'].reset();
    this.form.controls['cand_office_state'].reset();
    this.form.controls['cand_office_district'].reset();
  }
























}
