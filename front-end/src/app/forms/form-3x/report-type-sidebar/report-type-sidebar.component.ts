import { Component, EventEmitter, Input, OnDestroy, OnInit, Output, SimpleChanges } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { Subject } from 'rxjs';
import { Subscription } from 'rxjs/Subscription';
import { ConfirmModalComponent, ModalHeaderClassEnum } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { selectedReportType } from '../../../shared/interfaces/FormsService/FormsService';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { ApiService } from './../../../shared/services/APIService/api.service';


@Component({
  selector: 'report-type-sidebar',
  templateUrl: './report-type-sidebar.component.html',
  styleUrls: ['./report-type-sidebar.component.scss'],
  providers: [NgbTooltipConfig]
})
export class ReportTypeSidebarComponent implements OnInit, OnDestroy {
  
  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() specialReports: boolean = false;
  @Input() regularReports: boolean = false;
  @Input() selectedReport: any = null;
  @Input() selectedreporttype: selectedReportType;

  public editMode: boolean;
  public dueDate: string = null;
  public electionDate: string = null;
  public electionStates: any = null;
  public electionDates: any = null;
  public frmReportSidebar: FormGroup;
  public fromDate: string = null;
  public toDate: string = null;
  public selectedElectionState: string = null;
  public selectedElecetionDate: string = null;
  
  public states:any[];

  private _reportTypeDescription: string = null;
  public formType: string = null;
  private _newReportSelected: boolean = false;
  private _previousReportTypeDescription: string = null;
  private _previousReportSelected: string = null;
  private _previousStateSelected: string = null;
  private _reportType: string = null;
  private _selectedElectionDates: any = null;
  private _selectedState: string = null;
  private _selectedElectionDate: string = null;
  private messageSubscription : Subscription = null;
  private onDestroy$ = new Subject();
  public reportEditMode: boolean = false;


  // //This is a temporary solution to a bigger problem. During edit, after resetting the form based on message 
  // //service, ngonchange is resetting it back. this is used to make sure ngOnChange is not called the first 
  // //time in edit mode. 
  // public bypassNgOnChange : boolean = false;

  public messageDataForEdit: any = null;
  public semiAnnualStartDate: string;
  public semiAnnualEndDate: string;

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _config: NgbTooltipConfig,
    private _formService: FormsService,
    private _messageService: MessageService,
    private _dialogService: DialogService,
    private _activatedRoute: ActivatedRoute, 
    private _apiService: ApiService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';

    this.messageSubscription = this._messageService.getMessage().subscribe(message => {
      if(message && message.component === 'coverage-sidebar' && message.action === 'clearCoverageForm'){
        if(this.frmReportSidebar){
          this.dueDate = null;
          this.fromDate = null;
          this.toDate = null;
          this.electionDate = null;
          this._selectedState = null;
          this._selectedElectionDate = null;
          this.selectedElectionState = null;
          this.selectedElecetionDate = null;
          this.frmReportSidebar.reset();
        }
      }
    });

    this._messageService.getUpdateReportTypeMessage().takeUntil(this.onDestroy$).subscribe((message: any) => {
      if(message && message.currentReportData){
        this.reportEditMode = true;
        if(this.frmReportSidebar){
          this.populateDataForEdit(message);
          this.messageDataForEdit = message;
        }
      }
      message = null;
    });
    
  }

  private populateDataForEdit(message: any) {
    if(message && message.currentReportData){
      this.frmReportSidebar.controls['fromDate'].patchValue(message.currentReportData.currentStartDate);
      this.frmReportSidebar.controls['toDate'].patchValue(message.currentReportData.currentEndDate);
      this.frmReportSidebar.controls['dueDate'].patchValue(message.currentReportData.currentDueDate);
      this.frmReportSidebar.controls['election_date'].patchValue(message.currentReportData.currentElectionDate);
      this.frmReportSidebar.controls['state'].patchValue(message.currentReportData.currentElectionState);
      if(this.frmReportSidebar.controls['state'].value){
        this.frmReportSidebar.controls['fromDate'].enable();
        this.frmReportSidebar.controls['toDate'].enable();
        this.frmReportSidebar.controls['election_date'].enable();
      }
/*       if(this.formType.endsWith('3X')){
        this.populateDatesByState(message.currentReportData.currentElectionState);
      } */
      if(this.formType.endsWith('3L')){
        this.frmReportSidebar.controls['semiAnnualDatesOption'].patchValue(this.getSemiAnnualDateOptionByStartAndEndDates(null,message.currentReportData.currentSemiAnnualStartDate,message.currentReportData.currentSemiAnnualEndDate));
      }
      this.fromDate = message.currentReportData.currentStartDate;
      this.toDate = message.currentReportData.currentEndDate;
      this.electionDate = message.currentReportData.currentElectionDate;
      this.dueDate = message.currentReportData.currentDueDate;
      this.fromDateChange(message.currentReportData.currentStartDate);
    }
  }



  ngOnInit():void {
    this.formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.editMode = this._activatedRoute.snapshot.queryParams.edit === 'false' ? false : true;
    this.initForm();
    this.getAllStates();
  }

  getAllStates() {
    this._apiService.getStates().subscribe(data => {
      if(data && data.data && data.data.states){
        this.electionStates = data.data.states;
        this.electionStates.map(state => {
          state.state_description = state.name;
          state.state = state.code;
        })
      }
    });
    console.log()
  }

  public initForm() {
    this.frmReportSidebar = this._fb.group({
      state: new FormControl({value:null,disabled: false}),
      election_date: new FormControl({value:null,disabled: true}),
      fromDate: new FormControl({value:null,disabled: true},[Validators.required]),
      toDate: new FormControl({value:null,disabled: true},[Validators.required]),
      dueDate: new FormControl({value:null,disabled: false}),
      semiAnnualDatesOption: new FormControl(''),
      semiAnnualFromDate: new FormControl(),
      semiAnnualToDate: new FormControl()
    });
  }


   ngOnChanges(changes: SimpleChanges): void {

    if(changes && changes.selectedReport && changes.selectedReport.currentValue){
      if(this._activatedRoute.snapshot.queryParams.edit === 'true'){
        this.populateDataForEdit(this.messageDataForEdit);
      }
    }
    
    this.changeDataBasedOnSelectedReport(); 
    
    //this is being done only the first time the form loads for edit flow since ngONChange is resetting the value so setting it back.
    //TODO - there is a small bug in this that needs to be fixed for default reports (August and October) 
/*     if(this.messageDataForEdit){
      this.populateDataForEdit(this.messageDataForEdit);
      this.messageDataForEdit = null;
    } */
  }


  private changeDataBasedOnSelectedReport() {
    if(this.formType === '3L' || this.formType === '3X'){
      this.changeDataBasedOnSelectedReportFor3L();
    }
    else{
      if (this.selectedReport !== null) {
        // //console.log('this.selectedReport: ', this.selectedReport);
        if (this.selectedReport.hasOwnProperty('regular_special_report_ind')) {
          if (typeof this.selectedReport.regular_special_report_ind === 'string') {
            this._reportType = this.selectedReport.regular_special_report_ind;
          }
        }
        if (this.selectedReport.hasOwnProperty('report_type')) {
          if (typeof this.selectedReport.report_type === 'string') {
            if (this._previousReportSelected === null) {
              this._previousReportSelected = this.selectedReport.report_type;
            }
          }
          if (this._previousReportSelected !== this.selectedReport.report_type) {
            this._newReportSelected = true;
          }
        }
        if (this.selectedReport.hasOwnProperty('regular_special_report_ind')) {
          if (typeof this.selectedReport.regular_special_report_ind === 'string') {
            if (this.selectedReport.regular_special_report_ind === 'S') {
              // special reports
              if (this.selectedReport.hasOwnProperty('election_state')) {
                if (Array.isArray(this.selectedReport.election_state)) {
                  if (this.selectedReport.election_state.length === 1) {
                    const electionState: any = this.selectedReport.election_state[0];
                    if (!this.selectedElectionState && !this.selectedElecetionDate) {
                      if (this._newReportSelected) {
                        if (this.fromDate && this.toDate) {
                          this.toDate = '';
                          this.fromDate = '';
                          // this.frmReportSidebar.controls['toDate'].reset();
                          // this.frmReportSidebar.controls['fromDate'].reset();
                        }
                      }
                    }
                    if (electionState.hasOwnProperty('state') && electionState.hasOwnProperty('state')) {
                      this.electionStates = [];
                      this.electionStates[0] = {
                        state: electionState.state,
                        state_description: electionState.state_description
                      };
                    }
                  }
                  else {
                    if (this.selectedReport.hasOwnProperty('election_state')) {
                      this.electionStates = this.selectedReport.election_state;
                    }
                  }
                } // Array.isArray(this.selectedReport.election_state)
              } // this.selectedReport.hasOwnProperty('election_state')
            }
            else {
              // regular reports
              if (this.selectedReport.hasOwnProperty('election_state')) {
                if (Array.isArray(this.selectedReport.election_state)) {
                  if (this.selectedReport.election_state.length === 1) {
                    // Apply the dates from the newly selected report
                    // Don't set the dates if the change trigger is from the date itself.
                    // if (newReportSelected) {
                    if (this._newReportSelected) {
                      this.fromDate = '';
                      this.toDate = '';
                    }
                    this._selectedElectionDates = null;
                    if (this.selectedReport.election_state[0]['dates']) {
                      if (Array.isArray(this.selectedReport.election_state[0].dates)) {
                        let dates: any = this.selectedReport.election_state[0].dates;
                        if (Array.isArray(dates)) {
                          if(this.messageDataForEdit && this.messageDataForEdit.currentReportData.currentReportType === this.selectedReport.report_type){
  
                            this.fromDate = this.messageDataForEdit.currentReportData.currentStartDate;
                            this.toDate = this.messageDataForEdit.currentReportData.currentEndDate;
                            this.dueDate = this.messageDataForEdit.currentReportData.currentDueDate;
  
                            if(this.frmReportSidebar){
                              this.frmReportSidebar.controls['fromDate'].patchValue(this.fromDate);
                              this.frmReportSidebar.controls['toDate'].patchValue(this.toDate);
                              this.fromDateChange(this.fromDate);
                            }
                          }
  
                          else if (typeof dates[0].cvg_start_date === 'string' &&
                            dates[0].cvg_start_date !== null &&
                            typeof dates[0].cvg_end_date === 'string' &&
                            dates[0].cvg_end_date !== null &&
                            typeof dates[0].due_date === 'string' &&
                            dates[0].due_date.length !== null) {
                              this.fromDate = dates[0].cvg_start_date;
                              this.toDate = dates[0].cvg_end_date;
                              this.dueDate = dates[0].due_date;
  
                            if(this.frmReportSidebar){
                              this.frmReportSidebar.controls['fromDate'].patchValue(this.fromDate);
                              this.frmReportSidebar.controls['toDate'].patchValue(this.toDate);
                              this.fromDateChange(this.fromDate);
                            }
  
                          }
                        }
                      }
                    }
                    // }
                  }
                }
              }
            }
          }
        }
      }
    }
    
  }
  changeDataBasedOnSelectedReportFor3L() {
    if (this.selectedReport !== null) {
      if (this.selectedReport.hasOwnProperty('regular_special_report_ind')) {
        if (typeof this.selectedReport.regular_special_report_ind === 'string') {
          this._reportType = this.selectedReport.regular_special_report_ind;
        }
      }
      if (this.selectedReport.hasOwnProperty('report_type')) {
        if (typeof this.selectedReport.report_type === 'string') {
          if (this._previousReportSelected === null) {
            this._previousReportSelected = this.selectedReport.report_type;
          }
        }
        if (this._previousReportSelected !== this.selectedReport.report_type) {
          this._newReportSelected = true;
        }
      }
        if (this._newReportSelected) {
          this.fromDate = '';
          this.toDate = '';
          this.electionDate = '';
        }
        this._selectedElectionDates = null;

        //edit scenario
        if(this.messageDataForEdit && this.messageDataForEdit.currentReportData.currentReportType === this.selectedReport.report_type){

          this.fromDate = this.messageDataForEdit.currentReportData.currentStartDate;
          this.toDate = this.messageDataForEdit.currentReportData.currentEndDate;
          this.electionDate = this.messageDataForEdit.currentReportData.currentElectionDate;
          this.dueDate = this.messageDataForEdit.currentReportData.currentDueDate;
          this.disableCoverageDatesIfApplicable(true);
          this.populateSemiAnnualDates();

          if(this.frmReportSidebar){
            this.frmReportSidebar.controls['fromDate'].patchValue(this.fromDate);
            this.frmReportSidebar.controls['toDate'].patchValue(this.toDate);
            this.frmReportSidebar.controls['election_date'].patchValue(this.electionDate);
            this.fromDateChange(this.fromDate);
          }
        }

        //new report scenario
        else {
            this.fromDate = this.selectedReport.cvg_start_date;
            this.toDate = this.selectedReport.cvg_end_date;
            this.electionDate = this.selectedReport.election_date;
            this.dueDate = this.selectedReport.due_date;
            this.electionDate = this.selectedReport.election_date;
            this.disableCoverageDatesIfApplicable(false);
            this.populateSemiAnnualDates();

          if(this.frmReportSidebar){
            this.patchForDisabledField('fromDate',this.fromDate);
            this.patchForDisabledField('toDate',this.toDate);
            this.patchForDisabledField('state',null);
            this.patchForDisabledField('election_date',this.electionDate);
            this.patchForDisabledField('dueDate',this.dueDate);
            if(this.frmReportSidebar.controls['semiAnnualDatesOption'] && this.frmReportSidebar.controls['semiAnnualDatesOption'].value){
              let selectedSemiAnnualOption = this.selectedReport['semi-annual_dates'].filter(obj => obj.selected);
              if(selectedSemiAnnualOption && selectedSemiAnnualOption.length > 0){
                selectedSemiAnnualOption = selectedSemiAnnualOption[0];
                this.semiAnnualStartDate = selectedSemiAnnualOption.start_date;
                this.semiAnnualEndDate = selectedSemiAnnualOption.end_date;
                this.frmReportSidebar.controls['semiAnnualFromDate'].patchValue(this.semiAnnualStartDate);
                this.frmReportSidebar.controls['semiAnnualToDate'].patchValue(this.semiAnnualEndDate);
              }
            }
            if(this.dueDate){
              this.frmReportSidebar.controls['dueDate'].patchValue(this.dueDate);
            }

            this.fromDateChange(this.fromDate);
          }

        }
    }
  }

  patchForDisabledField(fieldName: string, value: any){
    let disabled = false;
    if(this.frmReportSidebar.controls[fieldName].status === 'DISABLED'){
      this.frmReportSidebar.controls[fieldName].enable();
      disabled = true;
    }
    this.frmReportSidebar.controls[fieldName].patchValue(value);
    if(disabled){
      this.frmReportSidebar.controls[fieldName].disable();
    }
  } 

  /**
   * retuns the index of element in dates array based on matching start and end dates, or returns null if none found
   * @param datesArray 
   * @param startDate 
   * @param endDate 
   */
  getSemiAnnualDateOptionByStartAndEndDates(datesArray: any[], startDate: string, endDate: string): string|null{
    if(datesArray && datesArray.length > 0 && startDate && endDate){
      
      let index = 0;
      let matchFound = false;
      for(let i = 0; i<datesArray.length; i++){
        if(datesArray[i].start_date === startDate && datesArray[i].end_date === endDate){
          index = i;
          matchFound = true;
          break;
        }
      }
      if(matchFound){
        return index.toString();
      }
    }
    //in case dates array is not passed in, check the month to get option, i.e. start Date's month = 01 and end Date month = 06, then option 0
    //else  start Date's month = 07 and end Date month = 12, then option 1
    else if(!datesArray && startDate && endDate){
      if(startDate.substr(5,2) === "01" && endDate.substr(5,2) === "06"){
        return "0";
      }
      else if(startDate.substr(5,2) === "07" && endDate.substr(5,2) === "12"){
        return "1";
      }
    }
    return null;
  }

  disableCoverageDatesIfApplicable(editFlag: boolean) {
    if(this.selectedReport && this.selectedReport.disableCoverageDates || (this.selectedReport.regular_special_report_ind === 'S' && !editFlag)){
      this.frmReportSidebar.controls['fromDate'].disable();
      this.frmReportSidebar.controls['toDate'].disable();
      if(this.selectedReport.regular_special_report_ind === 'S'){
        this.frmReportSidebar.controls['election_date'].disable();
      }
    }
    else{
      this.frmReportSidebar.controls['fromDate'].enable();
      this.frmReportSidebar.controls['toDate'].enable();
    }
  }

  populateSemiAnnualDates() {
    if(this.selectedReport && this.selectedReport['semi-annual_dates'] && this.selectedReport['semi-annual_dates'].length > 0 && !this.selectedReport['annual_dates_optional']){
      let index = 0;
      let matchFound = false;
      for(let i = 0; i<this.selectedReport['semi-annual_dates'].length; i++){
        if(this.selectedReport['semi-annual_dates'][i].selected){
          index = i;
          matchFound = true;
          break;
        }
      }
      if(matchFound){
        this.frmReportSidebar.controls['semiAnnualDatesOption'].patchValue((index).toString());
        this.frmReportSidebar.controls['semiAnnualDatesOption'].disable();
        this.semiAnnualStartDate = this.selectedReport['semi-annual_dates'][index].start_date;
        this.semiAnnualEndDate = this.selectedReport['semi-annual_dates'][index].end_date;
        this.frmReportSidebar.controls['semiAnnualFromDate'].patchValue(this.semiAnnualStartDate);
        this.frmReportSidebar.controls['semiAnnualToDate'].patchValue(this.semiAnnualEndDate);
      }else{
        this.frmReportSidebar.controls['semiAnnualDatesOption'].patchValue(null);
        this.frmReportSidebar.controls['semiAnnualDatesOption'].enable();
        this.semiAnnualStartDate = null;
        this.semiAnnualEndDate = null;
        this.frmReportSidebar.controls['semiAnnualFromDate'].patchValue(this.semiAnnualStartDate);
        this.frmReportSidebar.controls['semiAnnualToDate'].patchValue(this.semiAnnualEndDate);
      }
    }
  }

  /**
   * Check if the selected Report matches the Report from local storage.
   *
   * @param form3XReportType the F3X Report Type from local storage.
   * @returns true if the report type from storage matches the selected report type.
   */
  private checkSelectedMatchesSpecial(form3XReportType: any): boolean {
    if (form3XReportType.hasOwnProperty('reportType')) {
      if (typeof form3XReportType.reportType === 'string') {
        if (form3XReportType.reportType === this.selectedReport.reportType) {
          return true;
        }
      }
    }
    return false;
  }

  /**
   * Changes format of date from yyyy-m-d to m/d/yyyy.
   *
   * TODO put in utilService
   *
   * @param      {string}  date    The date
   * @return     {string}  The new formatted date.
   */
  private _deFormatDate(date: string): string {
    try {
      const dateArr = date.split('/');
      const month: string = dateArr[0];
      const day: string = dateArr[1];
      const year: string = dateArr[2].replace('2018', '2019');

      return `${year}-${month}-${day}`;
    } catch (e) {
      return '';
    }
  }

  /**
   * Executed when a special report has election state(s).
   *
   * @param      {Object}  e       The event object.
   */
  public selectStateChange(e): void {
    if(this.formType === '3L' || this.formType === '3X'){
      this.handleSelectStateChangeFor3L(e);
    }
    else{
      if (this.editMode) {
        let selectedStateStr =  this.frmReportSidebar.controls['state'].value;
        console.log(selectedStateStr);
        let selectedStateObj: any = null;
        // if (selectedStateStr !== '0') {
          if (this.selectedReport.hasOwnProperty('election_state')) {
            if (Array.isArray(this.selectedReport.election_state)) {
              if (this.selectedReport.election_state.length > 0) {
                selectedStateObj = this.selectedReport.election_state.find(el => {
                  return el.state === selectedStateStr;
                });
                
                if (selectedStateObj.hasOwnProperty('dates')) {
                  if (Array.isArray(selectedStateObj.dates)) {
                    this.electionDates = [];
                    this.electionDates = selectedStateObj.dates;
                  }
                }
              }
            }  
          } 
        // } 
      } else {
        this.showFiledWarning();
      }
    }
  }

  handleSelectStateChangeFor3L(e: any) {
    if(e && e.target.value){
      this.frmReportSidebar.controls['election_date'].enable();
      this.frmReportSidebar.controls['fromDate'].enable();
      this.frmReportSidebar.controls['toDate'].enable();
    }
    else{
      this.frmReportSidebar.controls['election_date'].disable();
      this.frmReportSidebar.controls['fromDate'].disable();
      this.frmReportSidebar.controls['toDate'].disable();
    }
    if (this.editMode) {
        this._messageService.sendMessage({action:'reportTypeSideBarUpdate', currentData:this.frmReportSidebar.value});
      } else {
        this.showFiledWarning();
      }
  }

  private populateDatesByState(state:string){
    if(this.selectedReport){
      let selectedStateObj = this.selectedReport.election_state.find(el => {
        return el.state === state;
      });
      if (selectedStateObj && selectedStateObj.hasOwnProperty('dates')) {
        if (Array.isArray(selectedStateObj.dates)) {
          this.electionDates = [];
          this.electionDates = selectedStateObj.dates;
        }
      }
    }
  }
  private showFiledWarning() {
    this._dialogService
      .confirm('This report has been filed with the FEC. If you want to change, you must Amend the report', ConfirmModalComponent, 'Warning', true, ModalHeaderClassEnum.warningHeader, null, 'Return to Reports')
      .then(res => {
        if (res === 'okay') {
          this.ngOnInit();
        }
        else if (res === 'cancel') {
          this._router.navigate(['/reports']);
        }
      });
  }

  /**
   * Executed when a special report has election date(s).
   *
   * @param      {Object}  e       The event object.
   */
  public selectElectionDateChange(e): void {
    if(this.formType === '3L' || this.formType === '3X'){
      this._messageService.sendMessage({action:'reportTypeSideBarUpdate', currentData:this.frmReportSidebar.value});
    }
    else{

      let _selectedElectionDate =  this.frmReportSidebar.controls['election_date'].value;
      let selectedElectionDateObj: any = null;
      // const selectedOption: any = e.target[e.target.selectedIndex];
  
      if(this.electionDates && this.electionDates.length > 0){
          selectedElectionDateObj = this.electionDates.find(el => {
          return el.election_date === _selectedElectionDate;
        });
      }
  
      this._selectedElectionDates = {
        fromDate: selectedElectionDateObj.cvg_start_date,
        toDate: selectedElectionDateObj.cvg_end_date,
        dueDate: selectedElectionDateObj.due_date
      };
  
      this.fromDate = this._selectedElectionDates.fromDate;
      this.toDate = this._selectedElectionDates.toDate;
      this.dueDate = this._selectedElectionDates.dueDate;
  
      /* this._messageService.sendMessage({
        type: this._formType,
        currentFormData : this.frmReportSidebar,
        selectedElectionDates:this._selectedElectionDates
      }); */
  
      this._selectedElectionDate = e.target.value;
  
      this.frmReportSidebar.patchValue({fromDate:this.fromDate});
      
      this.frmReportSidebar.patchValue({toDate:this.toDate});
      this.frmReportSidebar.patchValue({dueDate: this.dueDate});
      this.fromDateChange(this.fromDate);
      // this.toDateChange(this.toDate);
    }

  }

  public semiAnnualDateChange(event){
    if(event && event.target && event.target.value !== null && event.target.value !== undefined){
      const dateOption = this.selectedReport['semi-annual_dates'][Number(event.target.value)];
      this.frmReportSidebar.controls['semiAnnualFromDate'].patchValue(dateOption.start_date);
      this.frmReportSidebar.controls['semiAnnualToDate'].patchValue(dateOption.end_date);
      this._messageService.sendMessage({action:'reportTypeSideBarUpdate', currentData:this.frmReportSidebar.value});
    }
  }

  /**
   * Executed when from date field is changed.
   *
   * @param      {string}  date    The date
   */
  public fromDateChange(date: string) {
    if(this.formType === '3L' || this.formType === '3X'){
      this._messageService.sendMessage({action:'reportTypeSideBarUpdate', currentData:this.frmReportSidebar.value});
    }
    else{

      let message: any = {};
  
      // if (this.fromDate !== null) {
        //if (date !== this.fromDate) {
          message.action = 'coverageDatesUpdated'
          message.validDates = false;
          message.selectedFromDate = date;
          message.selectedToDate = this.frmReportSidebar.controls['toDate'].value;
          message.dueDate = this.dueDate;
          message.selectedState = this.frmReportSidebar.controls['state'].value;
          message.selectedElectionDate = this.frmReportSidebar.controls['election_date'].value;
          message.electionDates = [];
  
      this._messageService.sendMessage(message);
    }
  }

  /**
   * Executed when the to date field is changed.
   *
   * @param      {string}  date    The date
   */
  public toDateChange(date: string) {
    if(this.formType === '3L' || this.formType === '3X'){
      this._messageService.sendMessage({action:'reportTypeSideBarUpdate', currentData:this.frmReportSidebar.value});
    }
    else{
      let message: any = {};

      // if (this.toDate !== null) {
        // if (date !== this.fromDate) {
          message.action = 'coverageDatesUpdated'
          message.validDates = false;
          message.selectedToDate = date;
          message.selectedFromDate = this.frmReportSidebar.value.fromDate;
          message.dueDate = this.dueDate;
          message.selectedState = this.frmReportSidebar.value.state;
          message.selectedElectionDate = this.frmReportSidebar.value.election_date;
          message.electionDates = [];
  
      this._messageService.sendMessage(message);
    }
  }

  ngOnDestroy(): void {
    this.onDestroy$.next(true);
    this.messageSubscription.unsubscribe();
  }
  
}
