import { Component, EventEmitter, ElementRef, Input, OnInit, Output, SimpleChanges, ChangeDetectionStrategy, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators, FormControl } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import {
  selectedElectionState,
  selectedElectionDate,
  selectedReportType
} from '../../../shared/interfaces/FormsService/FormsService';
import { Subscription } from 'rxjs/Subscription';

import { ConfirmModalComponent, ModalHeaderClassEnum } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { Subject } from 'rxjs';

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
  public electionStates: any = null;
  public electionDates: any = null;
  public frmReportSidebar: FormGroup;
  public fromDate: string = null;
  public toDate: string = null;
  public selectedElectionState: string = null;
  public selectedElecetionDate: string = null;

  private _reportTypeDescription: string = null;
  private _formType: string = null;
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

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _config: NgbTooltipConfig,
    private _formService: FormsService,
    private _messageService: MessageService,
    private _dialogService: DialogService,
    private _activatedRoute: ActivatedRoute
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';

    this.messageSubscription = this._messageService.getMessage().subscribe(message => {
      if(message && message.component === 'coverage-sidebar' && message.action === 'clearCoverageForm'){
        if(this.frmReportSidebar){
          this.frmReportSidebar.reset();
        }
      }
    });

    this._messageService.getUpdateReportTypeMessage().takeUntil(this.onDestroy$).subscribe((message: any) => {
      if(message && message.currentReportData){
        this.reportEditMode = true;
        // this.currentReportDescription = message.currentReportData.currentReportDescription;
        if(this.frmReportSidebar){
          this.populateDataForEdit(message);
          this.messageDataForEdit = message;
          // this.bypassNgOnChange = true;
          
          
          
          //populate coverage dates on the left 


        /*   let currentReport: any = this.committeeReportTypes.filter((el: { report_type: any; }) => {
            return el.report_type === message.currentReportData.currentReportType;
          });

          //creating a deep copy
          let currentReportDeepCopy = JSON.parse(JSON.stringify(currentReport));


          if(currentReportDeepCopy && currentReportDeepCopy.length > 0){
            //this will simulate a click event and set dates and other params
            currentReportDeepCopy = currentReportDeepCopy[0];
            this.updateTypeSelectedForEdit(currentReportDeepCopy.report_type,currentReportDeepCopy.regular_special_report_ind);
          } */
        }
      }
      message = null;
    });
    
  }

  private populateDataForEdit(message: any) {
    this.frmReportSidebar.controls['fromDate'].patchValue(message.currentReportData.currentStartDate);
    this.frmReportSidebar.controls['toDate'].patchValue(message.currentReportData.currentEndDate);
    this.fromDate = message.currentReportData.currentStartDate;
    this.toDate = message.currentReportData.currentEndDate;
    this.fromDateChange(message.currentReportData.currentStartDate);
  }

/*   ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.editMode = this._activatedRoute.snapshot.queryParams.edit === 'false' ? false : true;
    this.frmReportSidebar = this._fb.group({});
  } */


  ngOnInit():void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.editMode = this._activatedRoute.snapshot.queryParams.edit === 'false' ? false : true;
    this.initForm();
  }

  public initForm() {
    this.frmReportSidebar = this._fb.group({
      state: new FormControl({value:null}),
      election_date: new FormControl({value:null}),
      fromDate: new FormControl({value:null},[Validators.required]),
      toDate: new FormControl({value:null},[Validators.required]),
      dueDate: new FormControl({value:null})
    });
  }


   ngOnChanges(changes: SimpleChanges): void {
 /*    if (this.selectedReport && this.selectedReport.hasOwnProperty('report_type')) {
      // if(!reportedit)
      if (typeof this.selectedReport.report_type === 'string') {
        if (this._previousReportSelected === null) {
          this._previousReportSelected = this.selectedReport.report_type;
        } else {
          this._previousReportSelected = changes.selectedReport.previousValue.report_type;
        }
      }

      if (this._previousReportSelected !== this.selectedReport.report_type) {
        this._newReportSelected = true;
        this.selectedElectionState = null;
        this.selectedElecetionDate = '';
        if (changes.selectedReport.currentValue.regular_special_report_ind === 'S') {
          if (this.fromDate) {
            this.fromDate = '';
          }
          if (this.toDate) {
            this.toDate = '';
          }
        }
      }
    } */
    /* if(changes && changes.selectedReport && changes.selectedReport.currentValue){
      if(this.bypassNgOnChange){
        this.bypassNgOnChange = false;
      }
      else{
        this.changeDataBasedOnSelectedReport();
      }
    } */

    this.changeDataBasedOnSelectedReport();
    
    //this is being done only the first time the form loads for edit flow since ngONChange is resetting the value so setting it back.
    //TODO - there is a small bug in this that needs to be fixed for default reports (August and October) 
/*     if(this.messageDataForEdit){
      this.populateDataForEdit(this.messageDataForEdit);
      this.messageDataForEdit = null;
    } */
  }

 ngDoCheck(): void {
/*     if(!this.reportEditMode){
     this.changeDataBasedOnSelectedReport(); // this.selectedReport !== null
   }  */
  } 

  private changeDataBasedOnSelectedReport() {
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
                        if (typeof dates[0].cvg_start_date === 'string' &&
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
    if (this.editMode) {
      let selectedStateStr =  this.frmReportSidebar.controls['state'].value;
      console.log(selectedStateStr);
      let selectedStateObj: any = null;
      if (selectedStateStr !== '0') {
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
      } 
    } else {
      this.showFiledWarning();
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

  /**
   * Executed when from date field is changed.
   *
   * @param      {string}  date    The date
   */
  public fromDateChange(date: string) {
    let message: any = {};

    // if (this.fromDate !== null) {
      //if (date !== this.fromDate) {
        message.action = 'coverageDatesUpdated'
        message.validDates = false;
        message.selectedFromDate = date;
        message.selectedToDate = this.frmReportSidebar.value.toDate;
        message.dueDate = this.dueDate;
        message.electionDates = [];
      /* } else {
        this.fromDate = date;

        message.validDates = true;
        message.electionDates.push({
          cvg_end_date: this.toDate,
          cvg_start_date: this.fromDate,
          due_date: this.dueDate,
          election_date: this.selectedElecetionDate
        });
      } */
    /* } else {
      this.fromDate = date;

      message.validDates = true;
      message.electionDates.push({
        cvg_end_date: this.toDate,
        cvg_start_date: this.fromDate,
        due_date: this.dueDate,
        election_date: this.selectedElecetionDate
      });
    } */

    this._messageService.sendMessage(message);
  }

  /**
   * Executed when the to date field is changed.
   *
   * @param      {string}  date    The date
   */
  public toDateChange(date: string) {
    let message: any = {};

    // if (this.toDate !== null) {
      // if (date !== this.fromDate) {
        message.action = 'coverageDatesUpdated'
        message.validDates = false;
        message.selectedToDate = date;
        message.selectedFromDate = this.frmReportSidebar.value.fromDate;
        message.dueDate = this.dueDate;
        message.electionDates = [];
      /* } else {
        this.toDate = date;

        message.validDates = true;
        message.electionDates.push({
          cvg_end_date: this.toDate,
          cvg_start_date: this.fromDate,
          due_date: this.dueDate,
          election_date: this.selectedElecetionDate
        });
      } */
    /* } else {
      this.toDate = date;

      message.validDates = true;
      message.electionDates.push({
        cvg_end_date: this.toDate,
        cvg_start_date: this.fromDate,
        due_date: this.dueDate,
        election_date: this.selectedElecetionDate
      });
    }  */

    this._messageService.sendMessage(message);
  }

  ngOnDestroy(): void {
    this.onDestroy$.next(true);
    this.messageSubscription.unsubscribe();
  }
  
}
