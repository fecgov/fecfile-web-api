import { validateAmount } from 'src/app/shared/utils/forms/validation/amount.validator';
import { ReportTypeService } from './../../form-3x/report-type/report-type.service';
import { MessageService } from './../../../shared/services/MessageService/message.service';
import { LoanService } from './../service/loan.service';
import { UtilService } from './../../../shared/utils/util.service';
import { Component, OnInit, ViewChild, AfterViewChecked, Input, ChangeDetectorRef, Output, EventEmitter } from '@angular/core';
import { NgForm, Validators } from '@angular/forms';
import { CookieService } from 'ngx-cookie-service';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ScheduleActions } from '../../form-3x/individual-receipt/schedule-actions.enum';
import { environment } from '../../../../environments/environment';
import { map } from 'rxjs/operators';
import { ContributionDateValidator } from 'src/app/shared/utils/forms/validation/contribution-date.validator';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { validateContributionAmount } from '../../../shared/utils/forms/validation/amount.validator';

@Component({
  selector: 'app-loanpayment',
  templateUrl: './loanpayment.component.html',
  styleUrls: ['./loanpayment.component.scss']
})
export class LoanpaymentComponent implements OnInit {

  @Input() transactionDetail: any;
  @Input() scheduleAction: ScheduleActions = ScheduleActions.add;
  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  tooltipPlaceholder: string = 'Language to be provided by RAD';
  selectedEntity = 'IND';
  cvgStartDate: string;
  cvgEndDate: string;
  states: any = [];
  entityTypes: any = [{ code: 'IND', description: 'Individual' }, { code: 'ORG', description: 'Organization' }];
  outstandingLoanBalance: number;

  constructor(private _cookieService: CookieService,
    private _http: HttpClient,
    private utilService: UtilService,
    private _contributionDateValidator: ContributionDateValidator,
    private _loanService: LoanService,
    private _receiptService: LoanService,
    private _messageService: MessageService,
    private _reportTypeService: ReportTypeService,
    private _router: Router, 
    private changeDetectorRef: ChangeDetectorRef) { }



  @ViewChild('f') form: NgForm;



  ngOnInit() {
    this.initializeForm();
    this.getStates();
  }
  
  
  private getLoanRepaymentData() {
    
    const reportId: string = this._reportTypeService.getReportIdFromStorage('3X').toString();
    this._loanService.getDataSchedule(reportId, this.transactionDetail.transactionId).subscribe(res => {
      res = res[0];
      this.form.control.patchValue({ 'last_Name': res.last_name });
      this.form.control.patchValue({ 'first_Name': res.first_name });
      this.form.control.patchValue({ 'middle_Name': res.middle_name });
      this.form.control.patchValue({ 'suffix': res.suffix });
      this.form.control.patchValue({ 'prefix': res.prefix });
      this.form.control.patchValue({ 'street_1': res.street_1 });
      this.form.control.patchValue({ 'street_2': res.street_2 });
      this.form.control.patchValue({ 'city': res.city });
      this.form.control.patchValue({ 'zip': res.zip_code });
      this.form.control.patchValue({ 'state': res.state });
      this.form.control.patchValue({ 'entity_type': res.entity_type });

      this.outstandingLoanBalance = Number(res.loan_balance);
      
      //validators have to be set after getting current loan metadata to enfore max contribution amount
      this.setupValidators();

    })

  }

  private getStates() {
    this._loanService.getStates().subscribe(res => {
      this.states = res;
    });
  }

  private initializeForm() {
    setTimeout(() => {
      this.getLoanRepaymentData();
    }, 0);
  }

  private setupValidators() {
    const formInfo = JSON.parse(localStorage.getItem('form_3X_report_type'));
    this.cvgStartDate = formInfo.cvgStartDate;
    this.cvgEndDate = formInfo.cvgEndDate;
    this.form.controls['expenditure_date'].setValidators([
      this._contributionDateValidator.contributionDate(this.cvgStartDate, this.cvgEndDate),
      Validators.required
    ]);
    this.form.controls['expenditure_date'].updateValueAndValidity();

    this.form.controls['expenditure_amount'].setValidators([validateAmount(), validateContributionAmount(this.outstandingLoanBalance)]);
    this.form.controls['expenditure_amount'].updateValueAndValidity();
  }

  test(form) {
    console.log(form);
  }

  handleTypeChange(event, form: any) {
    console.log(event);
    form.entity = event.code;
  }

  validateForm() {
    if (this.form.valid) {
      return true;
    }
    else {
      this.markFormControlsAsTouched();
      return false;
    }
  }

  markFormControlsAsTouched() {
    for (let inner in this.form.controls) {
      this.form.control.get(inner).markAsDirty();
      this.form.control.get(inner).markAsTouched();
      this.form.control.get(inner).updateValueAndValidity();
    }
  }

  expenditureDateChanged(expenditureDate: string) {

    const formInfo = JSON.parse(localStorage.getItem('form_3X_report_type'));
    let cvgStartDate = formInfo.cvgStartDate;
    let cvgEndDate = formInfo.cvgEndDate;

    if ((!this.utilService.compareDatesAfter((new Date(expenditureDate)), new Date(cvgEndDate)) ||
      this.utilService.compareDatesAfter((new Date(expenditureDate)), new Date(cvgStartDate)))) {
      console.log('Date is invalid');
    } else {
      console.log('date is valid');
    }

  }

  private removeCommas(amount: string): string {
    return amount.replace(new RegExp(',', 'g'), '');

  }

  public saveLoanPayment(form: string, scheduleAction: ScheduleActions) {


    if (this.validateForm()) {

      let formType: string = '3X';
      scheduleAction = ScheduleActions.add;

      const token: string = JSON.parse(this._cookieService.get('user'));
      let url: string = '/sb/schedB';
      const committeeDetails: any = JSON.parse(localStorage.getItem('committee_details'));
      let reportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

      if (reportType === null || typeof reportType === 'undefined') {
        reportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
      }

      const formData: FormData = new FormData();
      let httpOptions = new HttpHeaders();
      httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

      if (reportType.hasOwnProperty('reportId')) {
        formData.append('report_id', reportType.reportId);
      } else if (reportType.hasOwnProperty('reportid')) {
        formData.append('report_id', reportType.reportid);
      }

      formData.append('cmte_id', committeeDetails.committeeid);
      formData.append('transaction_type_identifier', 'LOAN_REPAY_MADE');
      formData.append('back_ref_transaction_id', this.transactionDetail.transactionId);
      console.log();

      for (const [key, value] of Object.entries(this.form.controls)){
        if(value.value !== null){
          if(typeof value.value === 'string'){
            formData.append(key,value.value);
          }
        }
      }

      formData.set('expenditure_date', this.utilService.formatDate(this.form.value.expenditure_date));
      formData.set('expenditure_amount', this.removeCommas(this.form.value.expenditure_amount));
      if (this.form.value.memoCode) {
        formData.append('memo_code', 'X');
      }

      if (scheduleAction === ScheduleActions.add || scheduleAction === ScheduleActions.addSubTransaction) {
        return this._http
          .post(`${environment.apiUrl}${url}`, formData, {
            headers: httpOptions
          })
          .subscribe(res => {
            if (res) {
              console.log('success!!!')

              //update sidebar
              this._receiptService.getSchedule(formType, res).subscribe(resp => {
                const message: any = {
                  formType,
                  totals: resp
                };
                this._messageService.sendMessage(message);
              });


              //navigate to Loan Summary here
              this._goToLoanSummary();
              // return res;
            }
            console.log('success but no response.. failure?')
            return false;
          }
          );
      } else if (scheduleAction === ScheduleActions.edit) {
        return this._http
          .put(`${environment.apiUrl}${url}`, formData, {
            headers: httpOptions
          })
          .pipe(
            map(res => {
              if (res) {
                return res;
              }
              return false;
            })
          );
      } else {
        console.log('unexpected ScheduleActions received - ' + scheduleAction);
      }
    }
  }

  private _goToLoanSummary() {
    const loanRepaymentEmitObj: any = {
      form: {},
      direction: 'next',
      step: 'step_3',
      previousStep: 'step_2',
      scheduleType: 'sched_c_loan_summary',
      // action: ScheduleActions.add,
    };
    this.status.emit(loanRepaymentEmitObj);
  }

}
