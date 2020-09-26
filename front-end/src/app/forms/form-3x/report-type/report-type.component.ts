import { DatePipe } from '@angular/common';
import { Component, EventEmitter, HostListener, Input, OnDestroy, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';
import 'rxjs/add/operator/takeUntil';
import { Subscription } from 'rxjs/Subscription';
import { ConfirmModalComponent, ModalHeaderClassEnum } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { ReportsService } from '../../../reports/service/report.service';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { TransactionsMessageService } from '../../transactions/service/transactions-message.service';
import { UtilService } from './../../../shared/utils/util.service';
import { IndividualReceiptService } from './../individual-receipt/individual-receipt.service';
import { ReportTypeService } from './report-type.service';


@Component({
  selector: 'form-report-type',
  templateUrl: './report-type.component.html',
  styleUrls: ['./report-type.component.scss'],
  encapsulation: ViewEncapsulation.None,
  providers: [DatePipe]
})
export class ReportTypeComponent implements OnInit, OnDestroy {
  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() committeeReportTypes: any = [];
  @Input() formType :any;
  @Input() selectedReportInfo: any = null;

  public editMode: boolean;

  public reportEditMode: boolean = false;
  public currentReportDescription: string = '';
  public frmReportType: FormGroup;
  // public fromDateSelected: boolean = false;
  public reportTypeSelected: string = null;
  public isValidType: boolean = false;
  public optionFailed: boolean = false;
  public invalidDates: boolean = false;
  public screenWidth: number = 0;
  public reportType: string = null;
  // public toDateSelected = false;
  public tooltipPosition = 'right';
  public tooltipLeft = 'auto';
  public customFormValidation: any;
  public reportsLoading: boolean;

  private _committeeDetails: any = null;
  private _dueDate: string = null;
  private _daysUntilReportDue: number = null;
  private _formType: string = null;
  private _formReportTypeDetails: any = null;
  public fromDateSelected: string = null;
  public toDateSelected: string = null;
  private _reportTypeDescripton: string = null;
  private _selectedElectionState: string = null;
  private _selectedElectionDate: string = null;
  private _fromDateUserModified: string = null;
  private _toDateUserModified: string = null;
  private _dateChangeSubscription: Subscription;
  private onDestroy$ = new Subject();
  private  updateRptSubscription: Subscription  = null;
  invalidDatesServerValidation: boolean;

  public selectedState: string = null;
  public selectedElectionDate: string = null;
  public showSemiAnnualDates: boolean;
  public currentSemiAnnualDates: any[];
  public coverageDatesMissing: boolean = false;
  private selectedSemiAnnualDateObj: any;
  public stateMissing: boolean = false;
  public electionDateMissing: boolean = false;
  public showErrors: boolean = false;
  public semiAnnualStartDate: string;
  public semiAnnualEndDate: string;

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _messageService: MessageService,
    private _formService: FormsService,
    private _reportTypeService: ReportTypeService,
    private _activatedRoute: ActivatedRoute,
    private _dialogService: DialogService,
    private _datePipe: DatePipe,
    private  _reportService: ReportsService,
    private  _transactionsMessageService: TransactionsMessageService, 
    private _indReceiptService: IndividualReceiptService,
    private _utilService:UtilService
  ) {
    
    this._messageService.getUpdateReportTypeMessage().takeUntil(this.onDestroy$).subscribe(message => {
      if(message && message.currentReportData){
        this.reportEditMode = true;
        this.currentReportDescription = message.currentReportData.currentReportDescription;
        if(this.frmReportType){
          this.frmReportType.patchValue({'reportTypeRadio': message.currentReportData.currentReportType},{onlySelf:true});
          
          
          //populate coverage dates on the left 


          let currentReport: any = this.committeeReportTypes.filter((el: { report_type: any; }) => {
            return el.report_type === message.currentReportData.currentReportType;
          });

          //creating a deep copy
          let currentReportDeepCopy = JSON.parse(JSON.stringify(currentReport));


          if(currentReportDeepCopy && currentReportDeepCopy.length > 0){
            //this will simulate a click event and set dates and other params
            currentReportDeepCopy = currentReportDeepCopy[0];
            this.updateTypeSelectedForEdit(currentReportDeepCopy.report_type,currentReportDeepCopy.regular_special_report_ind);
          }
        }
      }
      // message = null;
    });

    this._messageService.getMessage().takeUntil(this.onDestroy$).subscribe(res => {
          if (res && res.action === 'coverageDatesUpdated') {
              this.setData(res);
          }
          else if(res && res.action === 'reportTypeSideBarUpdate'){
            //missing dates
            if(this.selectedReportInfo && !this.selectedReportInfo.disableCoverageDates && (!res.currentData.fromDate || !res.currentData.toDate)){
              this.coverageDatesMissing = true;
            }
            else{
              this.coverageDatesMissing = false;
            }
            
            //missing state or election date
            if(this.selectedReportInfo && this.selectedReportInfo.regular_special_report_ind === 'S'){
              //missing state
              if(!res.currentData.state){
                this.stateMissing = true;
              }
              else{
                this.stateMissing = false;
              }
              //missing electionDate
              if(!res.currentData.election_date){
                this.electionDateMissing = true;
              }
              else{
                this.electionDateMissing = false;
              }
            }
            this.setDataFor3L(res.currentData);
          }
    });
  }

  private setData(res: any) {
    this.fromDateSelected = res.selectedFromDate;
    this.toDateSelected = res.selectedToDate;
    this._dueDate = res.dueDate;
    this._selectedElectionDate = res.selectedElectionDate;
    this._selectedElectionState = res.selectedState;
    if (this.frmReportType) {
      if (!this.reportEditMode) {
        if (!this.fromDateSelected || !this.toDateSelected) {
          this.frmReportType.setErrors({ invalid: true });
        }
        else {
          this.frmReportType.setErrors(null);
        }
      }
    }
  }

  private setDataFor3L(res: any) {
    this.fromDateSelected = res.fromDate;
    this.toDateSelected = res.toDate;
    this._dueDate = res.dueDate;
    this._selectedElectionDate = res.election_date;
    this._selectedElectionState = res.state;
    this.semiAnnualStartDate = res.semiAnnualFromDate;
    this.semiAnnualEndDate = res.semiAnnualToDate;
  }

  ngOnInit(): void {
    this._messageService.clearMessage();

    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.editMode = this._activatedRoute.snapshot.queryParams.edit === 'false' ? false : true;

    this._committeeDetails = JSON.parse(localStorage.getItem('committee_details'));

    if (localStorage.getItem(`form_${this._formType}_saved`) === null) {
      localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify(false));
    }

    this._messageService.clearMessage();

    this.screenWidth = window.innerWidth;

    if (this.screenWidth < 768) {
      this.tooltipPosition = 'bottom';
      this.tooltipLeft = '0';
    } else if (this.screenWidth >= 768) {
      this.tooltipPosition = 'right';
      this.tooltipLeft = 'auto';
    }

    this.frmReportType = this._fb.group({
      reportTypeRadio: ['', Validators.required]
    });

    this._formReportTypeDetails = {
      cmteId: '',
      reportId: '',
      formType: '3X',
      electionCode: '',
      reportType: '',
      reportTypeDescription: '',
      regularSpecialReportInd: '',
      stateOfElection: '',
      electionDate: '',
      cvgStartDate: '',
      cvgEndDate: '',
      dueDate: '',
      amend_Indicator: '',
      coh_bop: '0',
      daysUntilDue: '',
      email1: '',
      email2: '',
      additionalEmail1: '',
      additionalEmail2: '',
      overDue: false
    };
 }

  ngDoCheck(): void {
    if (window.localStorage.getItem(`form_${this._formType}_reset_form`) !== null) {
      const resetForm: boolean = JSON.parse(window.localStorage.getItem(`form_${this._formType}_reset_form`));
    }

    if (Array.isArray(this.committeeReportTypes)) {
      if (this.committeeReportTypes.length >= 1) {
        if (!this.reportTypeSelected) {
          if (
            this._committeeDetails.hasOwnProperty('cmte_filing_freq') &&
            typeof this._committeeDetails.cmte_filing_freq === 'string'
          ) {
            this._setSelectedReport();
          }
        }
      }
    }


    this._setReportTypes();
  }

  @HostListener('window:resize', ['$event'])
  onResize(event: { target: { innerWidth: number; }; }) {
    this.screenWidth = event.target.innerWidth;

    if (this.screenWidth < 768) {
      this.tooltipPosition = 'bottom';
      this.tooltipLeft = '0';
    } else if (this.screenWidth >= 768) {
      this.tooltipPosition = 'right';
      this.tooltipLeft = 'auto';
    }
  }

  /**
   * Updates the type selected.
   *
   * @param      {Object}  e   The event object.
   */
  public updateTypeSelected(e: { target: { checked: any; getAttribute: { (arg0: string): string; (arg0: string): string; }; }; }, reportType:any): void {
    if(reportType){
      this.selectedReportInfo = reportType;
    }
    if (this.editMode) {
      if (e.target.checked) {

        //reset all validations flags
        this.coverageDatesMissing = this.electionDateMissing = this.stateMissing = this.showErrors = false;
        //also send a message to sidebar to reset form first, but only reset if newly selected value is different from old 
        if(this.selectedReportInfo.report_type !== reportType.report_type){
          this._messageService.sendMessage({action:'clearCoverageForm', component:'coverage-sidebar'});
        }
        this.fromDateSelected = null;
        this.toDateSelected = null;
        this.invalidDatesServerValidation = false;

        // for some reason selected radio button value is coming as 'on'
        // temporarily using id to set correct report type
        
        this.reportTypeSelected = e.target.getAttribute('id');
        this.optionFailed = false;
        this.reportType = this.reportTypeSelected;
        const dataReportType: string = e.target.getAttribute('data-report-type');

        this.setReportParams(dataReportType);
      } else {
        this.reportTypeSelected = '';
        this.optionFailed = true;
      }
    } else {
      this.showReportFiledWarning();
    }
  }

  /**
   * 
   * This is a copy of updateTypeSelected method used for 'edit' flow since it may not require an actual click event
   * @param reportType 
   * @param reportTypeRegularSpecialIndicator 
   */
  updateTypeSelectedForEdit(reportType: string, reportTypeRegularSpecialIndicator: string): void{
    if (this.editMode) {
       //also send a message to sidebar to reset form first
       this._messageService.sendMessage({action:'clearCoverageForm', component:'coverage-sidebar'});
       this.fromDateSelected = null;
       this.toDateSelected = null;
       this.invalidDatesServerValidation = false;

      this.reportTypeSelected = this.reportType = reportType;
      this.optionFailed = false;
      this.setReportParams(reportTypeRegularSpecialIndicator);
    } else {
      this.showReportFiledWarning();
    }
  }

  private showReportFiledWarning() {
    this._dialogService
      .confirm('This report has been filed with the FEC. If you want to change, you must Amend the report', ConfirmModalComponent, 'Warning', true, ModalHeaderClassEnum.warningHeader, null, 'Return to Reports')
      .then((res: string) => {
        if (res === 'okay') {
          this.ngOnInit();
        }
        else if (res === 'cancel') {
          this._router.navigate(['/reports']);
        }
      });
  }

  private setReportParams(dataReportType: string) {
    if(this.formType === '3L'){
      this.setReportParamsFor3L(dataReportType);
    }
    else{
      const currentReport: any = this.committeeReportTypes.filter((el: { report_type: string; }) => {
        return el.report_type === this.reportType;
      });
      if (dataReportType && dataReportType !== 'S') {
        // this.toDateSelected = true;
        // this.fromDateSelected = true;
        if (Array.isArray(currentReport)) {
          if (currentReport[0].hasOwnProperty('election_state')) {
            const electionState: any = currentReport[0].election_state;
            if (Array.isArray(electionState)) {
              if (electionState[0].hasOwnProperty('dates')) {
                const dates: any = electionState[0].dates;
                if (Array.isArray(dates)) {
                  if (dates[0].hasOwnProperty('cvg_start_date')) {
                    this.fromDateSelected = dates[0].cvg_start_date;
                  }
                  if (dates[0].hasOwnProperty('cvg_end_date')) {
                    this.toDateSelected = dates[0].cvg_end_date;
                  }
                  if (dates[0].hasOwnProperty('election_date')) {
                    this._selectedElectionDate = dates[0].election_date;
                  }
                  if (dates[0].hasOwnProperty('due_date')) {
                    this._dueDate = dates[0].due_date;
                  }
                }
              }
            }
          }
          this._reportTypeDescripton = currentReport[0].report_type_desciption;
        }
      }
      else {
        this.fromDateSelected = null;
        this.toDateSelected = null;
      }
      if (Array.isArray(currentReport)) {
        this._formReportTypeDetails = JSON.parse(JSON.stringify(currentReport[0]))
        if (window.localStorage.getItem(`form_${this._formType}_report_type`)) {
          window.localStorage.removeItem(`form_${this._formType}_report_type`);
        }
      }
      this.status.emit({
        form: this._formType,
        reportTypeRadio: this.reportTypeSelected
      });
    }
    
  }
  setReportParamsFor3L(dataReportType: string) {
    const currentReport: any = this.committeeReportTypes.filter((el: { report_type: string; }) => {
      return el.report_type === this.reportType;
    })[0];
    if (dataReportType && dataReportType !== 'S') {
        if (currentReport.hasOwnProperty('cvg_start_date')) {
          this.fromDateSelected = currentReport.cvg_start_date;
        }
        if (currentReport.hasOwnProperty('cvg_end_date')) {
          this.toDateSelected = currentReport.cvg_end_date;
        }
        /* if (dates[0].hasOwnProperty('election_date')) {
          this._selectedElectionDate = dates[0].election_date;
        } */
        if (currentReport.hasOwnProperty('due_date')) {
          this._dueDate = currentReport.due_date;
        }
        if (currentReport.hasOwnProperty('semi-annual_dates') && currentReport['semi-annual_dates'].length > 0){
          this.showSemiAnnualDates = true;
          this.currentSemiAnnualDates = currentReport['semi-annual_dates'];
          this.selectedSemiAnnualDateObj = this.currentSemiAnnualDates.filter(obj => obj.selected );
          if(this.selectedSemiAnnualDateObj && this.selectedSemiAnnualDateObj.length > 0){
            this.selectedSemiAnnualDateObj = this.selectedSemiAnnualDateObj[0];
            this.semiAnnualStartDate = this.selectedSemiAnnualDateObj.start_date;
            this.semiAnnualEndDate = this.selectedSemiAnnualDateObj.end_date;
          }else{
            this.semiAnnualStartDate = null;
            this.semiAnnualEndDate = null;
          }
          
        }else{
          this.showSemiAnnualDates = false;
        }
        this._reportTypeDescripton = currentReport.report_type_desciption;
    }
    else {
      this.fromDateSelected = null;
      this.toDateSelected = null;
      this.semiAnnualStartDate = null;
      this.semiAnnualEndDate = null;
    }
    if (currentReport) {
      this._formReportTypeDetails = JSON.parse(JSON.stringify(currentReport))
      if (window.localStorage.getItem(`form_${this._formType}_report_type`)) {
        window.localStorage.removeItem(`form_${this._formType}_report_type`);
      }
    }
    this.status.emit({
      form: this._formType,
      reportTypeRadio: this.reportTypeSelected
    });
  }

  /**
   * Validates the type selected form.
   *
   */
  public doValidateReportType() {
    if(!this.reportEditMode){
      if (this.frmReportType.valid && this.validationsPassed()) {
        if(this.formType ==='3X' || this.formType === '3L'){
          return this.handleForm(false,this.formType);
        }
        else if(this.formType === '24'){
          return this.handleForm24();
        }
      } 
      else {
        if(!this.frmReportType.value.reportTypeRadio){
          this.optionFailed = true;
        }
      }
    }
    //For Editing report 
    else{
      if (this.frmReportType.valid) {
        if(this.formType ==='3X' || this.formType === '3L'){
          return this.handleForm(true,this.formType);
        }
      } else {
        if (this.frmReportType.controls['reportTypeRadio'].invalid && !this.invalidDates) {
          this.invalidDates = false;
          this.optionFailed = true;
          this.isValidType = false;
          this.frmReportType.markAsDirty();
          window.scrollTo(0, 0);
  
          return 0;
        } else {
          this.invalidDates = true;
          this.optionFailed = false;
          this.isValidType = false;
  
          window.scrollTo(0, 0);
        }
      }
    }
  }

  validationsPassed() : boolean{
    if (this.optionFailed){
      this.showErrors = true;
      return false;
    }
    if (this.formType === '3X' && (!this.fromDateSelected || !this.toDateSelected)){
      this.showErrors = true;
      return false;
    }
    if (this.formType === '3L' && (this.coverageDatesMissing || this.electionDateMissing || this.stateMissing)){
      this.showErrors = true;
      return false;
    }
    
    return true;
  }
 


  
  private handleForm24(editMode: boolean = false) {
    this.optionFailed = false;
    this.isValidType = true;
    const committeeDetails: any = JSON.parse(localStorage.getItem('committee_details'));
    if(!this._formReportTypeDetails){
      this._formReportTypeDetails = {};
    }
    this._formReportTypeDetails.reportType = this.frmReportType.get('reportTypeRadio').value;
    this._formReportTypeDetails.reportTypeDescription = this._reportTypeDescripton;
    this._formReportTypeDetails.email1 = committeeDetails.email_on_file;
    this._formReportTypeDetails.email2 = committeeDetails.email_on_file_1;
    this._formReportTypeDetails.additionalEmail1 = '';
    this._formReportTypeDetails.additionalEmail2 = '';
    this._formReportTypeDetails.formType = '24';
    this._formReportTypeDetails.reportId = '';
    const today: any = new Date();

    if(editMode){
      this._formReportTypeDetails.report_id = this._activatedRoute.snapshot.queryParams.reportId;
    }
    
    window.localStorage.setItem(`form_${this._formType}_report_type`, JSON.stringify(this._formReportTypeDetails));
    this._reportTypeService.saveReport(this._formType, 'Saved',editMode).subscribe(res => {
      if (res) {
        let reportId = 0;
        if (Array.isArray(res) && !res[0].hasOwnProperty('create_date')) {
          reportId = res[0].report_id;
          this._formReportTypeDetails.reportId = reportId;
          window.localStorage.setItem(`form_${this._formType}_report_type`, JSON.stringify(this._formReportTypeDetails));
          return 0;
        }
        this.status.emit({
          form: this.frmReportType,
          direction: 'next',
          step: 'step_2',
          transactionCategory:'disbursements',
          previousStep: 'step_1',
          transactionDetail: {
            transactionModel: {reportId: res.reportid}
          }
        });
      }
    });
    return 0;
  }


  private handleForm(editMode: boolean = false, formType:string) {
    
    this.showErrors = true;
    this.optionFailed = false;
    this.isValidType = true;
    const committeeDetails: any = JSON.parse(localStorage.getItem('committee_details'));
    this._formReportTypeDetails.reportType = this.frmReportType.get('reportTypeRadio').value;
    this._formReportTypeDetails.cvgStartDate = this._datePipe.transform(this.fromDateSelected, 'MM/dd/yyyy');
    this._formReportTypeDetails.cvgEndDate = this._datePipe.transform(this.toDateSelected, 'MM/dd/yyyy');
    this._formReportTypeDetails.dueDate = this._datePipe.transform(this._dueDate, 'MM/dd/yyyy');
    this._formReportTypeDetails.reportTypeDescription = this._reportTypeDescripton;
    this._formReportTypeDetails.election_state = this._selectedElectionState;
    this._formReportTypeDetails.election_date = this._datePipe.transform(this._selectedElectionDate, 'MM/dd/yyyy');
    this._formReportTypeDetails.regular_special_report_ind = this.selectedReportInfo.regular_special_report_ind;
    this._formReportTypeDetails.daysUntilDue = this._calcDaysUntilReportDue(this._dueDate);
    this._formReportTypeDetails.email1 = committeeDetails.email_on_file;
    this._formReportTypeDetails.email2 = committeeDetails.email_on_file_1;
    this._formReportTypeDetails.additionalEmail1 = '';
    this._formReportTypeDetails.additionalEmail2 = '';
    this._formReportTypeDetails.formType = formType;
    this._formReportTypeDetails.reportId = '';
    if(this.semiAnnualStartDate){
      this._formReportTypeDetails.semi_annual_start_date = this._datePipe.transform(this.semiAnnualStartDate, 'MM/dd/yyyy');
    }
    if(this.semiAnnualEndDate){
      this._formReportTypeDetails.semi_annual_end_date = this._datePipe.transform(this.semiAnnualEndDate, 'MM/dd/yyyy');
    }
    const today: any = new Date();
    const formattedToday: any = this._datePipe.transform(today, 'MM/dd/yyyy');
    const reportDueDate: any = this._datePipe.transform(this._dueDate, 'MM/dd/yyyy');

    if(editMode){
      this._formReportTypeDetails.report_id = this._activatedRoute.snapshot.queryParams.reportId;
    }
    if (reportDueDate < formattedToday) {
      this._formReportTypeDetails.overDue = true;
    }
    else {
      this._formReportTypeDetails.overDue = false;
    }
    window.localStorage.setItem(`form_${this._formType}_report_type`, JSON.stringify(this._formReportTypeDetails));
    this._reportTypeService.saveReport(this._formType, 'Saved',editMode).subscribe(res => {
      if (res) {
        let reportId = 0;
        if(res.status && res.status === 'fail'){
          this.invalidDatesServerValidation = true;

          if (res.data && Array.isArray(res.data) && !res.data[0].hasOwnProperty('create_date')) {
            ({ res, reportId } = this.showReportExistsWarningMessage(res.data, reportId));
            return 0;
          }

        }
        else{
            if(res && res.hasOwnProperty('cvgstartdate')){
              res.cvgstartdate = this._utilService.formatDate(res.cvgstartdate)
            }
            if(res && res.hasOwnProperty('cvgenddate')){
              res.cvgenddate = this._utilService.formatDate(res.cvgenddate)
            }
            this._messageService.sendMessage({
              action: 'updateCurrentReportHeaderData',
              data: res
            });
            if (res.orphanedTransactionsExist){
              this.showOrphanTransactionsExistWarningMessage(res);
            }else{
              this.proceedToNextStep(res);
            }
          }
        }
    });
    return 0;
  }

  private showOrphanTransactionsExistWarningMessage(data:any) {
    this._dialogService
      .confirm('By changing this report, there now exist one or more transactions that are not tied to any report. In order to show those transactions, please ensure that there is a report created corresponding to those coverage dates', ConfirmModalComponent, 'Warning', true, ModalHeaderClassEnum.warningHeader, null, 'Return to Reports')
      .then((res: string) => {
        if (res === 'okay') {
          this.proceedToNextStep(data);
        }
        else if (res === 'cancel') {
          this._router.navigate(['/reports']);
        }
      });
  }

  private proceedToNextStep(res: any) {
    this.invalidDatesServerValidation = false;
    this.updateThirdNavAmounts(res);
    let step = 'step_2';
    if (this.reportEditMode) {
      step = 'transactions';
    }
    this.status.emit({
      form: this.frmReportType,
      direction: 'next',
      step: step,
      previousStep: 'step_1',
      transactionCategory: 'receipts'
    });
  }

  private showReportExistsWarningMessage(res: any, reportId: number) {
    res = res[0];
    reportId = res.report_id;
    this._formReportTypeDetails.reportId = reportId;
    window.localStorage.setItem(`form_${this._formType}_report_type`, JSON.stringify(this._formReportTypeDetails));
    const cvgStartDate: any = res.cvg_start_date;
    let datearray: any = cvgStartDate.split('-');
    const newcvgStartDate: string = datearray[1] + '/' + datearray[2] + '/' + datearray[0];
    const cvgEndDate: any = res.cvg_end_date;
    datearray = cvgEndDate.split('-');
    const newcvgEndDate: string = datearray[1] + '/' + datearray[2] + '/' + datearray[0];
    const alertStr: string = `The coverage dates entered overlap 
                    with ${res.report_type} [ ${newcvgStartDate} ${newcvgEndDate} ]`;
    let reportStatus = '';
    this._reportService.getReports('current', 1, 1, '', true, null, reportId).subscribe(reportRes => {
      if (reportRes) {
        if (reportRes.reports[0] && reportRes.reports[0].status) {
          reportStatus = reportRes.reports[0].status;
          //console.log('Report %s is already %s', reportId, reportStatus);
          this._dialogService
            .reportExist(alertStr, ConfirmModalComponent, 'Report already exists', true, false, true)
            .then((userRes: string) => {
              if (userRes === 'cancel') {
                // this.optionFailed = true;
                this.isValidType = false;
                window.scrollTo(0, 0);
                if(!this.reportEditMode){
                  this.resetReportScreenForms();
                }
                this.status.emit({
                  form: {},
                  direction: 'previous',
                  step: 'step_1'
                });
                return 0;
              }
              else if (userRes === 'ReportExist') {
                this._transactionsMessageService.sendLoadTransactionsMessage(reportId);
                if (reportStatus.toLowerCase() === 'saved') {
                  this._router.navigate([`/forms/form/${this._formType}`], {
                    queryParams: { step: 'transactions', reportId: reportId, edit: true, transactionCategory: 'receipts' }
                  });
                }
                else if (reportStatus.toLowerCase() === 'filed') {
                  // navigate to summary page of the filed report
                  this._router.navigate([`/forms/form/${this._formType}`], {
                    queryParams: { step: 'financial_summary', reportId: reportId, edit: false, transactionCategory: '' }
                  });
                }
                else {
                  // navigate away to the reports view
                  // this should not happen as a report with report id should be either saved or filed
                  //console.log('report type Existing_Report_id', reportId.toString());
                  const reporturl = '/reports?reportId=';
                  this._router.navigateByUrl(`${reporturl}{reportId}`);
                  localStorage.setItem('Existing_Report_id', reportId.toString());
                  //this._router.navigate(['/reports`'], { queryParams: { reportId: reportId} });
                  //localStorage.removeItem(`form_${this._formType}_saved`);
                  localStorage.removeItem('reports.filters');
                  localStorage.removeItem('Reports.view');
                }
              }
            });
        }
      }
    });
    return { res, reportId };
  }
  resetReportScreenForms() {
    this.frmReportType.reset();
    this.coverageDatesMissing = this.electionDateMissing = this.stateMissing = this.showErrors = false;
    this._messageService.sendMessage({action:'clearCoverageForm', component:'coverage-sidebar'});
  }

  private updateThirdNavAmounts(res: any) {
    this._indReceiptService.getSchedule(this.formType, res).subscribe(resp => {
      const message: any = {
        formType: this.formType,
        totals: resp
      };
      this._messageService.sendMessage(message);
    });
  }

  /**
   * Toggles the tooltip.
   *
   * @param      {Element}  tooltip  The tooltip
   */
  public toggleToolTip(tooltip: { isOpen: () => void; close: () => void; open: () => void; }): void {
    if (tooltip.isOpen()) {
      tooltip.close();
    } else {
      tooltip.open();
    }
  }

  /**
   * Cancels form 3x.
   */
  public cancel(): void {
    this._router.navigateByUrl('/dashboard');
  }

  /**
   * Sets the selected report when the report type screen first loads.
   */
  private _setSelectedReport(): void {
    if (Array.isArray(this.committeeReportTypes)) {
      if(this._activatedRoute.snapshot.queryParams.edit !== 'true'){
        if (this.committeeReportTypes.length >= 1) {
          if (!this.reportTypeSelected) {
            const currentReport: any = this.committeeReportTypes.filter(el => {
              if (el.hasOwnProperty('default_disp_ind')) {
                if (typeof el.default_disp_ind === 'string') {
                  if (el.default_disp_ind === 'Y') {
                    if (!this.selectedReportInfo.hasOwnProperty('report_type_desciption')) {
                      this._reportTypeDescripton = el.report_type_desciption;
                    }
  
                    return el;
                  }
                }
              }
            });
  
            
            
            if (Array.isArray(currentReport) && currentReport.length > 0) {
              //creating a deep clone of current report so it doesnt override committeeReportTypes
              const selectedReport: any = JSON.parse(JSON.stringify(currentReport[0]));
  
              this.frmReportType.controls['reportTypeRadio'].setValue(selectedReport.report_type);
  
              this.frmReportType.controls['reportTypeRadio'].markAsTouched();
              this.frmReportType.controls['reportTypeRadio'].markAsDirty();
  
              this.reportTypeSelected = selectedReport.report_type;
  
              this.reportType = this.reportTypeSelected;
  
              this.optionFailed = false;
  
              if (Array.isArray(selectedReport.election_state)) {
                if (selectedReport.election_state[0].hasOwnProperty('dates')) {
                  const electionState: any = selectedReport.election_state[0];
  
                  this._dueDate = electionState.dates[0].due_date;
                  this.fromDateSelected = electionState.dates[0].cvg_start_date;
                  // this.fromDateSelected = true;
                  this.toDateSelected = electionState.dates[0].cvg_end_date;
                  // this.toDateSelected = true;
                }
  
                this.status.emit({
                  form: this._formType,
                  reportTypeRadio: this.reportTypeSelected
                });
              }
            } // typeof currentReport
          }
        }
      }
      else{

      }
    }
  }

  /**
   * Sets the report types when the screen is loaded.
   */
  private _setReportTypes(): void {
    if (this.selectedReportInfo) {
      if (this.selectedReportInfo.hasOwnProperty('toDate')) {
        if (this._toDateUserModified) {
          this.selectedReportInfo.toDate = this._toDateUserModified;
        }
        if (typeof this.selectedReportInfo.toDate === 'string') {
          if (this.selectedReportInfo.toDate.length >= 1) {
            this.toDateSelected = this.selectedReportInfo.toDate;
            // this.toDateSelected = true;
          } else {
            // this.toDateSelected = false;
          }
        } else {
          // this.toDateSelected = false;
        }
      }

      if (this.selectedReportInfo.hasOwnProperty('fromDate')) {
        if (this._fromDateUserModified) {
          this.selectedReportInfo.fromDate = this._fromDateUserModified;
        }
        if (typeof this.selectedReportInfo.fromDate === 'string') {
          if (this.selectedReportInfo.fromDate.length >= 1) {
            this.fromDateSelected = this.selectedReportInfo.fromDate;
            // this.fromDateSelected = true;
          } else {
            // this.fromDateSelected = false;
          }
        } else {
          // this.fromDateSelected = false;
        }
      }

      if (this.selectedReportInfo.hasOwnProperty('selectedState')) {
        if (typeof this.selectedReportInfo.selectedState === 'string') {
          this._selectedElectionState = this.selectedReportInfo.selectedState;
        } else {
          this._selectedElectionState = null;
        }
      }

      if (this.selectedReportInfo.hasOwnProperty('selectedElectionDate')) {
        if (typeof this.selectedReportInfo.selectedElectionDate === 'string') {
          this._selectedElectionDate = this.selectedReportInfo.selectedElectionDate;
        } else {
          this._selectedElectionDate = null;
        }
      }

      if (this.selectedReportInfo.hasOwnProperty('dueDate')) {
        if (typeof this.selectedReportInfo.dueDate === 'string') {
          if (this.selectedReportInfo.dueDate.length >= 1) {
            this._dueDate = this.selectedReportInfo.dueDate;
          }
        } else {
          this._dueDate = null;
        }
      }

      if (this.selectedReportInfo.hasOwnProperty('reportTypeDescription')) {
        if (typeof this.selectedReportInfo.reportTypeDescription === 'string') {
          if (this.selectedReportInfo.reportTypeDescription.length >= 1) {
            this._reportTypeDescripton = this.selectedReportInfo.reportTypeDescription;
          }
        } else {
          this._reportTypeDescripton = null;
        }
      }
    }
  }

  /**
   * Calculates the days until report due.
   *
   * @param      {any}     reportDueDate  The report due date
   * @return     {number}  The days until report due.
   */
  private _calcDaysUntilReportDue(reportDueDate: any): number {
    if(reportDueDate){
      const oneDay: number = 24 * 60 * 60 * 1000;
      const today: any = new Date();
      today.setHours(0, 0, 0, 0);
  
      const dueDateArr = reportDueDate.split('-');
      let dueDate: any = '';
  
      const dueDateMonth = parseInt(dueDateArr[1]) - 1; // Month
      const dueDateDay = parseInt(dueDateArr[2]); // Day
      const dueDateYear = parseInt(dueDateArr[0]); // Year
      const modifiedReportDueDate = new Date(dueDateYear, dueDateMonth, dueDateDay);
  
      const formattedDateToday: any = this._datePipe.transform(today,'MM/dd/yyyy');
      const formattedDueDate: any = this._datePipe.transform(reportDueDate,'MM/dd/yyyy');
  
      dueDate = Math.round(Math.abs((today.getTime() - modifiedReportDueDate.getTime()) / oneDay));
  
      return dueDate;
    }
    return null;
  }

  /*
    This function is called while selecting a list from report screen
  */
  public optionsListClick(type: string): void {
    //console.log('report type selected: ', type);
    if(document.getElementById(type) != null) {
        document.getElementById(type).click();
        //console.log(type, ' report clicked');
    }
  }

  public cancelAndReturnToReport(){
    window.localStorage.setItem(`form_${this._formType}_report_type`, JSON.stringify(this._formReportTypeDetails));
    this._router.navigate([`/forms/form/${this.formType}`], {
      queryParams: { step: 'transactions', reportId: this._activatedRoute.snapshot.queryParams.reportId, edit: true, transactionCategory: 'receipts', isFiled: false}
    });
  }

  ngOnDestroy(): void {
    this._messageService.clearUpdateReportTypeMessage();
    this.onDestroy$.next(true);
  }
}
