import { MessageService } from './../../../shared/services/MessageService/message.service';
import { LoanService } from './../service/loan.service';
import { UtilService } from './../../../shared/utils/util.service';
import { Component, OnInit, ViewChild, AfterViewChecked } from '@angular/core';
import { NgForm, Validators } from '@angular/forms';
import { CookieService } from 'ngx-cookie-service';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ScheduleActions } from '../../form-3x/individual-receipt/schedule-actions.enum';
import { environment } from '../../../../environments/environment';
import { map } from 'rxjs/operators';
import { ContributionDateValidator } from 'src/app/shared/utils/forms/validation/contribution-date.validator';
import { Router } from '@angular/router';

@Component({
  selector: 'app-loanpayment',
  templateUrl: './loanpayment.component.html',
  styleUrls: ['./loanpayment.component.scss']
})
export class LoanpaymentComponent implements OnInit {

  tooltipPlaceholder: string = 'Language to be provided by RAD';
  selectedEntity = 'IND';
  cvgStartDate: string;
  cvgEndDate: string;
  states: any = [];
  entityTypes: any = [{ code: 'IND', description: 'Individual' }, { code: 'ORG', description: 'Organization' }]

  constructor(private _cookieService: CookieService,
    private _http: HttpClient,
    private utilService: UtilService,
    private _contributionDateValidator: ContributionDateValidator,
    private _loanService: LoanService, 
    private _receiptService: LoanService, 
    private _messageService: MessageService, 
    private _router: Router) { }

  @ViewChild('f') form: NgForm;



  ngOnInit() {
    this.setupCustomDateValidator();
    this.getStates();
  }

  private getStates() {
    this._loanService.getStates().subscribe(res => {
      this.states = res;
    });
  }

  private setupCustomDateValidator() {
    setTimeout(() => {
      const formInfo = JSON.parse(localStorage.getItem('form_3X_report_type'));
      this.cvgStartDate = formInfo.cvgStartDate;
      this.cvgEndDate = formInfo.cvgEndDate;
      this.form.controls['expenditure_date'].setValidators([
        this._contributionDateValidator.contributionDate(this.cvgStartDate, this.cvgEndDate),
        Validators.required
      ]);
      this.form.controls['expenditure_date'].updateValueAndValidity();
    }, 0);
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

  private removeCommas(amount:string): string{
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

      const transactionType: any = JSON.parse(localStorage.getItem(`form_${formType}_transaction_type`));
      // const receipt: any = JSON.parse(localStorage.getItem(`form_${formType}_receipt`));

      const formData: FormData = new FormData();
      let httpOptions = new HttpHeaders();
      httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
      
      if (reportType.hasOwnProperty('reportId')) {
        formData.append('report_id', reportType.reportId);
      } else if (reportType.hasOwnProperty('reportid')) {
        formData.append('report_id', reportType.reportid);
      }

      formData.append('cmte_id', committeeDetails.committeeid);
      // formData.append('street_1',this.form.value.street1);
      // formData.append('street_2',this.form.value.street2);
      // formData.append('city',this.form.value.city);
      // formData.append('state',this.form.value.state);
      // formData.append('zip',this.form.value.zip);
      // formData.append('expenditure_purpose',this.form.value.expenditurePurposeDescription);
      // formData.append('memo_text',this.form.value.memoDescription);
      // formData.append('last_name',this.form.value.lastName);
      // formData.append('first_name',this.form.value.firstName);
      // formData.append('middle_name',this.form.value.middleInitial);
      // formData.append('prefix',this.form.value.prefix);
      // formData.append('suffix',this.form.value.suffix);
      // formData.append('entity_type', this.form.value.entity);
      // formData.append('entity_name', this.form.value.bankName);
      formData.append('transaction_type_identifier','OPEXP');
      
      
      // With Edit Report Functionality
      // if (reportType.hasOwnProperty('reportId')) {
        // } else if (reportType.hasOwnProperty('reportid')) {
          //   formData.append('report_id', reportType.reportid);
          // }
          console.log();
          
          for (const [key, value] of Object.entries(form)) {
            if (value !== null) { 
              if (typeof value === 'string') {
                formData.append(key, value);
              }
            }
          }
      formData.append('expenditure_date',this.utilService.formatDate(this.form.value.expenditure_date));
      formData.append('expenditure_amount',this.removeCommas(this.form.value.expenditure_amount));
      if(this.form.value.memoCode){
        formData.append('memo_code','X'); 
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
                this._router.navigate([`/forms/form/${formType}`], {
                  queryParams: { step: 'loansummary', reportId: reportType.reportId }
                });
                return res;
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

}
