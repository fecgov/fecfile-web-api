import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { ContactsService } from 'src/app/contacts/service/contacts.service';
import { IndividualReceiptService } from 'src/app/forms/form-3x/individual-receipt/individual-receipt.service';
import { ReportTypeService } from 'src/app/forms/form-3x/report-type/report-type.service';
import { F3xMessageService } from 'src/app/forms/form-3x/service/f3x-message.service';
import { SchedHMessageServiceService } from 'src/app/forms/sched-h-service/sched-h-message-service.service';
import { TransactionsMessageService } from 'src/app/forms/transactions/service/transactions-message.service';
import { TransactionsService } from 'src/app/forms/transactions/service/transactions.service';
import { ReportsService } from 'src/app/reports/service/report.service';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';
import { AuthService } from 'src/app/shared/services/AuthService/auth.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { FormsService } from 'src/app/shared/services/FormsService/forms.service';
import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { ContributionDateValidator } from 'src/app/shared/utils/forms/validation/contribution-date.validator';
import { UtilService } from 'src/app/shared/utils/util.service';
import { IndividualReceiptComponent } from './../../../form-3x/individual-receipt/individual-receipt.component';

@Component({
  selector: 'app-f3l-form-entry',
  templateUrl: './form-entry.component.html',
  styleUrls: ['./form-entry.component.scss']
})
export class FormEntryComponent extends IndividualReceiptComponent implements OnInit {

  public reportDetails : any = null;
  public maximumThresholdAmount: any = null;

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
    _schedHMessageServce: SchedHMessageServiceService,
    _authService: AuthService) {
      super(_http,
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
         _schedHMessageServce,
        _authService);

      _messageService.getMessage().takeUntil(this.onDestroy$).subscribe(message => {
        if (message && message.parentFormPopulated) {
          this.setupAdditionalFormControls();
          
        }
      })

     }
     
     setupAdditionalFormControls() {
       this.getScheduleType();
       if(this.reportDetails && this.frmIndividualReceipt && this.frmIndividualReceipt.controls){
      
      let fieldName = '';
      if(this.scheduleType && this.scheduleType.endsWith('schedA')){
        fieldName = 'contribution_amount';
      }
      else if(this.scheduleType && this.scheduleType.endsWith('schedB')){
        fieldName = 'expenditure_amount';
      }

      // no coverage dates scenario
      if(this.frmIndividualReceipt.controls[fieldName]){
        if(!this.reportDetails.cvgStartDate && !this.reportDetails.cvgEndDate){
          this.frmIndividualReceipt.controls[fieldName].patchValue("0.00");
          this.frmIndividualReceipt.controls[fieldName].disable();
        }else{
          this.frmIndividualReceipt.controls[fieldName].enable();
        }
      }

      //no semi-annual dates scenario
      if(!this.reportDetails.semi_annual_start_date && !this.reportDetails.semi_annual_end_date){
        this.frmIndividualReceipt.controls[fieldName].patchValue("0");
        this.frmIndividualReceipt.controls['semi_annual_refund_bundled_amount'].disable();
      }else{
        this.frmIndividualReceipt.controls['semi_annual_refund_bundled_amount'].enable();
      }

      //employer is always required
      if(this.frmIndividualReceipt.controls['employer']){
        this.frmIndividualReceipt.controls['employer'].setValidators([Validators.required]);
        this.frmIndividualReceipt.controls['employer'].updateValueAndValidity();
      }

    }
  }

  getScheduleType() {
    let apiField = this.getHiddenField('api_call');
    if(apiField){
      this.scheduleType = apiField.value;
    }
  }

  

  ngOnInit() {
    // this.reportDetails = this.mockSemiAndQuarterly();
    this._reportsService.getReportInfo(this.formType,this._activatedRoute.snapshot.queryParams.reportId).subscribe(res => {
      if(res && res.length > 0){
        this.maximumThresholdAmount = res[0].maximumThresholdAmount;
        if(!localStorage.getItem(`form_${this.formType}_report_type`)){
          localStorage.setItem(`form_${this.formType}_report_type`, JSON.stringify(res[0]));
        }
        this.reportDetails = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
        super.ngOnInit();
      }
    })
  }
  
  trackByName(index, item) {
    return item.name;
  }
  
  trackByIndex(index, item) {
    return index.name;
  }
  
  public handleOnBlurEvent($event: any, col: any) {
    
    if (this.isFieldName(col.name, 'contribution_amount') || this.isFieldName(col.name, 'expenditure_amount') ||
    this.isFieldName(col.name, 'semi_annual_refund_bundled_amount')
    ) {
      this._formatAmount($event, col.name, col.validation.dollarAmountNegative);
      const amountEntered:Number = this.convertDataToNumber($event,col.validation.dollarAmountNegative);
        
        
      if(this.isFieldName(col.name, 'contribution_amount') || this.isFieldName(col.name, 'expenditure_amount')){
        if(this.isFieldName(col.name, 'contribution_amount')){
          this._contributionAmount = "";
        }
        if(amountEntered < this.maximumThresholdAmount){
            this.displayMonthlyQuarterlyThresholdWarning = true;
          }
          else{
            this.displayMonthlyQuarterlyThresholdWarning = false;
          }
        }
        else if(this.isFieldName(col.name, 'semi_annual_refund_bundled_amount')){
          if(amountEntered < this.maximumThresholdAmount){
            this.displaySemiAnnualThresholdWarning = true;
          }
          else{
            this.displaySemiAnnualThresholdWarning = false;
          }
        }
    } 
  }

  mockQuarterly(){
    let reportDetails : any = JSON.parse(localStorage.getItem('form_3L_report_type'));
    return reportDetails;
  }

  mockSemiAnnual(){
    let reportDetails : any = JSON.parse(localStorage.getItem('form_3L_report_type'));
    reportDetails.cvgEndDate = null;
    reportDetails.cvgStartDate = null;
    reportDetails.semiAnnualStartDate = "01/01/2020";
    reportDetails.semiAnnualEndDate = "06/30/2020";

    return reportDetails;
  }

  mockSemiAndQuarterly(){
    let reportDetails : any = JSON.parse(localStorage.getItem('form_3L_report_type'));
    reportDetails.semiAnnualStartDate = "01/01/2020";
    reportDetails.semiAnnualEndDate = "06/30/2020";
    return reportDetails;
  }


}
