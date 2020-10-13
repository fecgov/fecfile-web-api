import { ScheduleActions } from './../individual-receipt/schedule-actions.enum';
import { Injectable , ChangeDetectionStrategy } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, identity, of } from 'rxjs';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';
import { form3xReportTypeDetails } from '../../../shared/interfaces/FormsService//FormsService';
import { DatePipe } from '@angular/common';
import {TransactionModel} from '../../transactions/model/transaction.model';


@Injectable({
  providedIn: 'root'
})
export class ReportTypeService {

  constructor(private _http: HttpClient, private _cookieService: CookieService) {
    this._datePipe = new DatePipe('en-US');
  }
  private _datePipe: DatePipe;
  /**
   * Gets the report types.
   *
   * @param      {string}  formType  The form type
   */
  public getReportTypes(formType: string): Observable<any> {

    /* if(formType === '3L'){
      return of(this.quarterlyElectionJSON);
    }
 */
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url: string = `/core/get_report_types?form_type=F${formType}`;
    let params = new HttpParams();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('form_type', `${formType}`);

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions
    });
  }

  /**
   * Saves a report.
   *
   * @param      {string}  formType  The form type
   */
  public saveReport(formType: string, access_type: string, editMode: boolean): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url: string = '/core/reports';

    let params = new HttpParams();
    let formData: FormData = new FormData();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let formReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (formReportType === null) {
      let form3xReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
    }

    formData.append('form_type', `F${formType}`);

    if(formReportType){

      if (formReportType.hasOwnProperty('reportType')) {
        formData.append('report_type', formReportType.reportType);
      } else if (formReportType.hasOwnProperty('reporttype')) {
        formData.append('report_type', formReportType.reporttype);
      }
  
      if (formReportType.hasOwnProperty('cvgStartDate')) {
        formData.append('cvg_start_dt', formReportType.cvgStartDate);
      } else if (formReportType.hasOwnProperty('cvgstartdate')) {
        formData.append('cvg_start_dt', formReportType.cvgstartdate);
      }
  
      if (formReportType.hasOwnProperty('cvgEndDate')) {
        formData.append('cvg_end_dt', formReportType.cvgEndDate);
      } else if (formReportType.hasOwnProperty('cvgenddate')) {
        formData.append('cvg_end_dt', formReportType.cvgenddate);
      }

      if (formReportType.hasOwnProperty('semi_annual_start_date')) {
        formData.append('semi_annual_start_date', formReportType.semi_annual_start_date);
      } 

      if (formReportType.hasOwnProperty('semi_annual_end_date')) {
        formData.append('semi_annual_end_date', formReportType.semi_annual_end_date);
      }
  
      if (formReportType.hasOwnProperty('cvgEndDate')) {
        formData.append('cvg_end_dt', formReportType.cvgEndDate);
      } else if (formReportType.hasOwnProperty('cvgenddate')) {
        formData.append('cvg_end_dt', formReportType.cvgenddate);
      }
  
      if (formReportType.hasOwnProperty('dueDate')) {
        formData.append('due_dt', formReportType.dueDate);
      } else if (formReportType.hasOwnProperty('duedate')) {
        formData.append('due_dt', formReportType.duedate);
      }
  
      if (formReportType.hasOwnProperty('amend_Indicator')) {
        if (typeof formReportType.amend_Indicator === 'string') {
          if (formReportType.amend_Indicator.length >= 1) {
            formData.append('amend_ind', formReportType.amend_Indicator);
          } else {
            formData.append('amend_ind', 'N');
          }
        }
      } else {
        formData.append('amend_ind', 'N');
      }
  
      if (formReportType.hasOwnProperty('coh_bop')) {
        if (typeof formReportType.coh_bop === 'string') {
          if (formReportType.coh_bop.length >= 1) {
            formData.append('coh_bop', formReportType.coh_bop);
          }
        } else {
          formData.append('coh_bop', '0');
        }
      } else {
        formData.append('coh_bop', '0');
      }
  
      if (typeof formReportType.electionCode === 'string') {
        if (formReportType.electionCode.length >= 1) {
          formData.append('election_code', formReportType.electionCode);
        }
      }
  
      if (formReportType.election_date !== null) {
        if (typeof formReportType.election_date === 'string') {
          if (formReportType.election_date.length >= 1) {
            formData.append('date_of_election', this._datePipe.transform(formReportType.election_date, 'MM/dd/yyyy'));
          }
        }
      }
  
      if (formReportType.election_state !== null) {
        if (typeof formReportType.election_state === 'string') {
          if (formReportType.election_state.length >= 1) {
            formData.append('state_of_election', formReportType.election_state);
          }
        }
      }
  
      if (formReportType.email1 !== null) {
        if (typeof formReportType.email1 === 'string') {
          if (formReportType.email1.length >= 1) {
            formData.append('email_1', formReportType.email1);
          }
        }
      }
  
      if (formReportType.email2 !== null) {
        if (typeof formReportType.email2 === 'string') {
          if (formReportType.email2.length >= 1) {
            formData.append('email_2', formReportType.email2);
          }
        }
      }
  
      if (formReportType.additionalEmail1 !== null) {
        if (typeof formReportType.additionalEmail1 === 'string') {
          if (formReportType.additionalEmail1.length >= 1) {
            formData.append('additional_email_1', formReportType.additionalEmail1);
          }
        }
      }
  
      if (formReportType.additionalEmail2 !== null) {
        if (typeof formReportType.additionalEmail2 === 'string') {
          if (formReportType.additionalEmail2.length >= 1) {
            formData.append('additional_email_2', formReportType.additionalEmail2);
          }
        }
      }
    }
    
    if (access_type === 'Saved') {
      formData.append('status', 'Saved');
    } else if (access_type === 'Submitted') {
      formData.append('status', 'Submitted');
    }

    if(!editMode){
      return this._http
        .post(`${environment.apiUrl}${url}`, formData, {
          headers: httpOptions
        })
        .pipe(
          map(res => {
            if (res) {
              if (localStorage.getItem(`form_${formType}_report_type`) !== null) {
                const reportObj: form3xReportTypeDetails = JSON.parse(
                  window.localStorage.getItem(`form_${formType}_report_type`)
                );
                if (res['reportid']) {
                  reportObj.reportId = res['reportid'];
                  window.localStorage.setItem(`form_${formType}_report_type`, JSON.stringify(reportObj));
                  localStorage.setItem(`reportId`, res['reportid']);
                }
              }
              return res;
            }
            return false;
          })
        );
    }
    else {
      formData.append('report_id',formReportType.report_id);
      return this._http
        .put(`${environment.apiUrl}${url}`, formData, {
          headers: httpOptions
        })
        .pipe(
          map(res => {
            if (res) {
              if (localStorage.getItem(`form_${formType}_report_type`) !== null) {
                const reportObj: form3xReportTypeDetails = JSON.parse(
                  window.localStorage.getItem(`form_${formType}_report_type`)
                );
                if (res['reportid']) {
                  reportObj.reportId = res['reportid'];
                  window.localStorage.setItem(`form_${formType}_report_type`, JSON.stringify(reportObj));
                  localStorage.setItem(`reportId`, res['reportid']);
                }
              }
              return res;
            }
            return false;
          })
        );
    }
  }

  saveAdditionalEmails(saveObj: any, scheduleAction: ScheduleActions) : Observable<any>{
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url = '/core/report/additionalEmails';

    let params = new HttpParams();
    let formData: FormData = new FormData();
    
    formData.append('reportId', saveObj.reportId);
    formData.append('formType', `F${saveObj.formType}`);
    formData.append('additionalEmail1', saveObj.additionalEmail1);
    formData.append('additionalEmail2', saveObj.additionalEmail2);

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);


    if (scheduleAction === ScheduleActions.add) {
      return this._http
        .post(`${environment.apiUrl}${url}`, formData, {
          headers: httpOptions
        }).pipe(map(data=>{
          this.updateLocalStorageWithEmails(data, saveObj.formType);
        }))
    } else if (scheduleAction === ScheduleActions.edit) {
      return this._http
        .put(`${environment.apiUrl}${url}`, formData, {
          headers: httpOptions
        })
    }
  }

  updateLocalStorageWithEmails(data: any, formType: string) {
    if(localStorage.getItem(`form_${formType}_report_type`)){
      let reportTypeObj = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));
      reportTypeObj.additionalemail1 = data.additionalEmail1;
      reportTypeObj.additionalemail2 = data.additionalEmail2;
      localStorage.setItem(`form_${formType}_report_type`, JSON.stringify(reportTypeObj));
    }
  }

  public signandSaveSubmitReport(formType: string, access_type: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url = '/core/reports';

    let params = new HttpParams();
    let formData: FormData = new FormData();
    //console.log('signandSaveSubmitReport called');
    //console.log('signandSaveSubmitReport formType = ', formType);
    //console.log('signandSaveSubmitReport access_type = ', access_type);

    // Adding CommitteeId and CommitteeName details to payload while submitting a report
    const committeeDetails: any = JSON.parse(localStorage.getItem('committee_details'));
    formData.append('committeeid', committeeDetails.committeeid);
    formData.append('committeename', committeeDetails.committeename);

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let form3xReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));


    if (form3xReportType === null) {
      //console.log('get backup object');
      form3xReportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));
      //console.log('backup object form3xReportType = ', form3xReportType);
    }

    localStorage.setItem('F3X_submit_backup', JSON.stringify(form3xReportType));
    //console.log('signandSaveSubmitReport access_type you reached here = ', access_type);
    formData.append('form_type', `F${formType}`);

    if(form3xReportType){

      if (form3xReportType.hasOwnProperty('reportid')) {
        formData.append('report_id', form3xReportType.reportid);
      } else if (form3xReportType.hasOwnProperty('reportId')) {
        formData.append('report_id', form3xReportType.reportId);
      }
  
      if (form3xReportType.hasOwnProperty('reportType')) {
        formData.append('report_type', form3xReportType.reportType);
      } else if (form3xReportType.hasOwnProperty('reporttype')) {
        formData.append('report_type', form3xReportType.reporttype);
      }
  
      if (form3xReportType.hasOwnProperty('cvgStartDate')) {
        formData.append('cvg_start_dt', this._datePipe.transform(form3xReportType.cvgStartDate, 'MM/dd/yyyy'));
      } else if (form3xReportType.hasOwnProperty('cvgstartdate')) {
        formData.append('cvg_start_dt', this._datePipe.transform(form3xReportType.cvgstartdate, 'MM/dd/yyyy'));
      }
  
      if (form3xReportType.hasOwnProperty('cvgEndDate')) {
        formData.append('cvg_end_dt', this._datePipe.transform(form3xReportType.cvgEndDate, 'MM/dd/yyyy'));
      } else if (form3xReportType.hasOwnProperty('cvgenddate')) {
        formData.append('cvg_end_dt', this._datePipe.transform(form3xReportType.cvgenddate, 'MM/dd/yyyy'));
      }
  
      if (form3xReportType.hasOwnProperty('dueDate')) {
        if (form3xReportType.dueDate !== null) {
          formData.append('due_dt', this._datePipe.transform(form3xReportType.dueDate, 'MM/dd/yyyy'));
        } else {
          formData.append('due_dt', null);
        }
      } else if (form3xReportType.hasOwnProperty('duedate')) {
        if (form3xReportType.duedate !== null) {
          formData.append('due_dt', this._datePipe.transform(form3xReportType.duedate, 'MM/dd/yyyy'));
        } else {
          formData.append('due_dt', null);
        }
      }
  
      //console.log('signandSaveSubmitReport access_type you reached here1 = ', access_type);
  
      if (form3xReportType.hasOwnProperty('amend_Indicator')) {
        if (typeof form3xReportType.amend_Indicator === 'string') {
          if (form3xReportType.amend_Indicator.length >= 1) {
            formData.append('amend_ind', form3xReportType.amend_Indicator);
          } else {
            formData.append('amend_ind', 'N');
          }
        }
      } else {
        formData.append('amend_ind', 'N');
      }
  
      if (form3xReportType.hasOwnProperty('coh_bop')) {
        if (typeof form3xReportType.coh_bop === 'string') {
          if (form3xReportType.coh_bop.length >= 1) {
            formData.append('coh_bop', form3xReportType.coh_bop);
          }
        } else {
          formData.append('coh_bop', '0');
        }
      } else {
        formData.append('coh_bop', '0');
      }
  
      if (form3xReportType.hasOwnProperty('electionCode')) {
        if (typeof form3xReportType.electionCode === 'string') {
          if (form3xReportType.electionCode.length >= 1) {
            formData.append('election_code', form3xReportType.electionCode);
          }
        }
      } else if (form3xReportType.hasOwnProperty('electioncode')) {
        if (typeof form3xReportType.electionCode === 'string') {
          if (form3xReportType.electionCode.length >= 1) {
            formData.append('election_code', form3xReportType.electionCode);
          }
        }
      }
  
      if (form3xReportType.election_date !== null) {
        if (typeof form3xReportType.election_date === 'string') {
          if (form3xReportType.election_date.length >= 1) {
            formData.append('date_of_election', form3xReportType.election_date);
          }
        }
      }
  
      if (form3xReportType.election_state !== null) {
        if (typeof form3xReportType.election_state === 'string') {
          if (form3xReportType.election_state.length >= 1) {
            formData.append('state_of_election', form3xReportType.election_state);
          }
        }
      }
  
      //console.log(' access_type =', access_type);
  
      if (form3xReportType.email1 !== null) {
        if (typeof form3xReportType.email1 === 'string') {
          if (form3xReportType.email1.length >= 1) {
            formData.append('email_1', form3xReportType.email1);
          }
        }
      }
  
      if (form3xReportType.email2 !== null) {
        if (typeof form3xReportType.email2 === 'string') {
          if (form3xReportType.email2.length >= 1) {
            formData.append('email_2', form3xReportType.email2);
          }
        }
      }
  
      if (form3xReportType.hasOwnProperty('additionalEmail1')) {
        if (typeof form3xReportType.additionalEmail1 === 'string') {
          if (form3xReportType.additionalEmail1.length >= 1) {
            formData.append('additional_email_1', form3xReportType.additionalEmail1);
          }
        }
      } else if (form3xReportType.hasOwnProperty('additionalemail1')) {
        if (typeof form3xReportType.additionalemail1 === 'string') {
          if (form3xReportType.additionalemail1.length >= 1) {
            formData.append('additional_email_1', form3xReportType.additionalemail1);
          }
        }
      }
  
      if (form3xReportType.hasOwnProperty('additionalEmail2')) {
        if (typeof form3xReportType.additionalEmail2 === 'string') {
          if (form3xReportType.additionalEmail2.length >= 1) {
            formData.append('additional_email_2', form3xReportType.additionalEmail2);
          }
        }
      } else if (form3xReportType.hasOwnProperty('additionalemail2')) {
        if (typeof form3xReportType.additionalemail2 === 'string') {
          if (form3xReportType.additionalemail2.length >= 1) {
            formData.append('additional_email_2', form3xReportType.additionalemail2);
          }
        }
      }
    }

    if (access_type === 'Saved') {
      formData.append('status', 'Saved');
    } else if (access_type === 'Submitted') {
      formData.append('status', 'Submitted');
    }

    //console.log('signandSaveSubmitReport formData = ', formData);

    if (access_type === 'Saved') {
      //console.log('signandSaveSubmitReport HTTP called with access_type = ', access_type);
      return this._http
        .put(`${environment.apiUrl}${url}`, formData, {
          headers: httpOptions
        })
        .pipe(
          map(res => {
            if (res) {
              //console.log('Form 3X save res = ', res);
              if (localStorage.getItem(`form_${formType}_report_type`) !== null) {
                const reportObj: form3xReportTypeDetails = JSON.parse(
                  window.localStorage.getItem(`form_${formType}_report_type`)
                );
                if (res['reportid']) {
                  reportObj.reportId = res['reportid'];
                  window.localStorage.setItem(`form_${formType}_report_type`, JSON.stringify(reportObj));
                }
              }
              return res;
            }
            return false;
          })
        );
    } else if (access_type === 'Submitted') {
      //console.log('signandSaveSubmitReport HTTP called with access_type = ', access_type);
      //console.log('submit Report form 3X submitted...');
      formData.append('call_from', 'Submit');
      //url = '/core/submit_report';
      url = '/core/create_json_builders';
      return this._http
        .post(`${environment.apiUrl}${url}`, formData, {
          headers: httpOptions
        })
        .pipe(
          map(res => {
            if (res) {
              //console.log('submit Report form 3X submitted res = ', res);
              /*localStorage.removeItem(`form_${formType}_saved_backup`);
              localStorage.removeItem(`form_${formType}_report_type_backup`);*/
              return res;
            }
            return false;
          })
        );
    }
  }

  public submitForm(formType: string, callFrom: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url: string = '/core/create_json_builders';
    //let url: string = '/core/create_json_builders_test';

    let params = new HttpParams();
    let formData: FormData = new FormData();
    //console.log('submitForm called');
    //console.log('submitForm formType = ', formType);
    //console.log('submitForm callFrom = ', callFrom);

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let form3xReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));
    //console.log(' submitForm form3xReportType = ', form3xReportType);

    if (form3xReportType === null) {
      //console.log('get backup object');
      form3xReportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
      if (form3xReportType === null) {
        form3xReportType = JSON.parse(localStorage.getItem('F3X_submit_backup'));
      }
    }

    // //console.log(' submitForm form3xReportType = ', form3xReportType);
    const committeeDetails: any = JSON.parse(localStorage.getItem('committee_details'));

    formData.append('call_from', callFrom);
    formData.append('committeeId', committeeDetails.committeeid);
    formData.append('password', 'test');
    formData.append('formType', `F${formType}`);

    /*if (form3xReportType.hasOwnProperty('amend_Indicator')) {
      if (typeof form3xReportType.amend_Indicator === 'string') {
        if (form3xReportType.amend_Indicator.length >= 1) {
          formData.append('newAmendIndicator', form3xReportType.amend_Indicator);
        } else {
          formData.append('newAmendIndicator', 'N');
        }
      }
    } else if (form3xReportType.hasOwnProperty('amend_indicator')) {
      if (typeof form3xReportType.amend_Indicator === 'string') {
        if (form3xReportType.amend_Indicator.length >= 1) {
          formData.append('newAmendIndicator', form3xReportType.amend_indicator);
        } else {
          formData.append('newAmendIndicator', 'N');
        }
      }
    }*/

    //console.log('form3xReportType: ', form3xReportType);
    formData.append('newAmendIndicator', 'N');
    if (form3xReportType !== null) {
      if (form3xReportType.hasOwnProperty('reportId')) {
        formData.append('reportSequence', form3xReportType.reportId);
        formData.append('report_id', form3xReportType.reportId);
      } else if (form3xReportType.hasOwnProperty('reportid')) {
        formData.append('reportSequence', form3xReportType.reportid);
        formData.append('report_id', form3xReportType.reportid);
      }

      if (form3xReportType.hasOwnProperty('email1')) {
        if (form3xReportType.email1 !== null) {
          if (typeof form3xReportType.email1 === 'string') {
            if (form3xReportType.email1.length >= 1) {
              formData.append('emailAddress1', form3xReportType.email1);
            }
          }
        }
      }

      if (form3xReportType.hasOwnProperty('reportType')) {
        formData.append('reportType', form3xReportType.reportType);
      } else if (form3xReportType.hasOwnProperty('reporttype')) {
        formData.append('reportType', form3xReportType.reporttype);
      }

      if (form3xReportType.hasOwnProperty('cvgStartDate')) {
        formData.append('coverageStartDate', this._datePipe.transform(form3xReportType.cvgStartDate, 'MM/dd/yyyy'));
      } else if (form3xReportType.hasOwnProperty('cvgstartdate')) {
        formData.append('coverageStartDate', this._datePipe.transform(form3xReportType.cvgstartdate, 'MM/dd/yyyy'));
      }

      if (form3xReportType.hasOwnProperty('cvgEndDate')) {
        formData.append('coverageEndDate', this._datePipe.transform(form3xReportType.cvgEndDate, 'MM/dd/yyyy'));
      } else if (form3xReportType.hasOwnProperty('cvgendeate')) {
        formData.append('coverageEndDate', this._datePipe.transform(form3xReportType.cvgenddate, 'MM/dd/yyyy'));
      }

      formData.append('originalFECId', '');
      formData.append('backDoorCode', '');

      if (form3xReportType.email2 !== null) {
        if (typeof form3xReportType.email2 === 'string') {
          if (form3xReportType.email2.length >= 1) {
            formData.append('emailAddress2', form3xReportType.email2);
          }
        }
      }
      formData.append('wait', 'True');

      return this._http.post(`${environment.apiUrl}${url}`, formData, {
        headers: httpOptions
      });
    }
  }

  /*public printPreviewPdf(formType: string, callFrom: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url: string = '/core/create_json_builders';
    //let url: string = '/core/create_json_builders_test';
    let formData: FormData = new FormData();

    //console.log('printForm formType = ', formType);

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let form3xReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (form3xReportType === null) {
      //console.log('get backup object');
      form3xReportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
      //console.log('backup object form3xReportType = ', form3xReportType);
    }

    if (form3xReportType.hasOwnProperty('reportId')) {
      formData.append('report_id', form3xReportType.reportId);
    } else if (form3xReportType.hasOwnProperty('reportid')) {
      formData.append('report_id', form3xReportType.reportid);
    }

    formData.append('form_type', `F${formType}`);
    formData.append('call_from', callFrom);

    return this._http.post(`${environment.apiUrl}${url}`, formData, {
      headers: httpOptions
    });
  }*/

  public printPreviewPdf(formType: string, callFrom: string, transactions?: string, reportId?:string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url: string = '/core/create_json_builders'; //Actual JSON file genaration URL
    //let url: string = '/core/create_json_builders_test';
    let formData: FormData = new FormData();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let form3xReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (form3xReportType === null)
    {
      form3xReportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
    }
    
    if(reportId){
      formData.append('report_id', reportId);
    } else if (form3xReportType.hasOwnProperty('reportId')) {
      formData.append('report_id', form3xReportType.reportId);
    } else if (form3xReportType.hasOwnProperty('reportid')) {   
      formData.append('report_id', form3xReportType.reportid);
    }

    formData.append('form_type', `F${formType}`);
    formData.append('call_from', callFrom);

    if ( typeof transactions !== 'undefined' ){
      if (transactions.length > 0){
        //console.log(" printPreviewPdf transactions =", transactions);
        //formData.append('transaction_id',  JSON.stringify(transactions.replace(' ','')));
        formData.append('transaction_id',  transactions.replace(' ',''));
      }
    }

    return this._http
      .post(`${environment.apiUrl}${url}`, formData, {
        headers: httpOptions
      });
   }

   public prepare_json_builders_data(formType: string,  transactions?:string, reportId?:string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url: string = '/core/prepare_json_builders_data';  //JSON builder data preparation URL

    let formData: FormData = new FormData();

    //console.log("prepare_json_builders_data formType = ", formType);
    //console.log("prepare_json_builders_data transactions=", transactions);

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let form3xReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (form3xReportType === null)
    {
      form3xReportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
      //console.log("prepare_json_builders_data backup object form3xReportType = ", form3xReportType);
    }
  
    if(reportId){
      formData.append('report_id', reportId);
    } else if (form3xReportType.hasOwnProperty('reportId')) {
      formData.append('report_id', form3xReportType.reportId);
      //console.log(" prepare_json_builders_data reportId found");
    } else if (form3xReportType.hasOwnProperty('reportid')) {   
      formData.append('report_id', form3xReportType.reportid);
      //console.log(" printPreprepare_json_builders_dataviewPdf reportid found");
    }

    if ( typeof transactions !== 'undefined' ){
      if (transactions.length > 0){
        //console.log("prepare_json_builders_data transactions =", transactions);
        //formData.append('transaction_id', JSON.stringify(transactions.replace(' ','')));
        formData.append('transaction_id',  transactions.replace(' ',''));
      }
    }
    return this._http
      .post(`${environment.apiUrl}${url}`, formData, {
        headers: httpOptions
      });
   }

   public printPreview(accessFrom: string, formType: string, transactions?: string, reportId?: string ): void {
    
    if (accessFrom !=='transaction_table_screen') {
      this.signandSaveSubmitReport(formType,'Saved');
    }

    if (typeof transactions === 'undefined') {
      this.prepare_json_builders_data(formType,undefined,reportId)
      .subscribe( res => {
        if (res) {
             if (res['Response']==='Success') {
                this.printPreviewPdf(formType, "PrintPreviewPDF", undefined,reportId)
                  .subscribe(res => {
                  if(res) {
                    if (res.hasOwnProperty('results')) {
                      if (res['results.pdf_url'] !== null) {
                        window.open(res.results.pdf_url, '_blank');
                      }
                    }
                  }
              },
              (error) => {
                console.error('error: ', error);
              });
            }       
        }
      },
        (error) => {
          console.error('error: ', error);
        });
    } else if (transactions !== 'undefined' && (transactions.length>0)) { 
      this.prepare_json_builders_data(formType, transactions, reportId)
      .subscribe( res => {
        if (res) {
             if (res['Response']==='Success') {
                    this.printPreviewPdf(formType, "PrintPreviewPDF",transactions, reportId)
                      .subscribe(res => {
                      if(res) {
                        if (res.hasOwnProperty('results')) {
                          if (res['results.pdf_url'] !== null) {
                            window.open(res.results.pdf_url, '_blank');
                          }
                        }
                      }
                  },
                  (error) => {
                    console.error('error: ', error);
                  });
                }       
        }
      },
        (error) => {
          console.log('error: ', error);
        });
    }
   
  }

  public getReportIdFromStorage(formType: string) {
    let reportId = '0';
    let form3XReportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (form3XReportType === null || typeof form3XReportType === 'undefined') {
      form3XReportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
    }

    //console.log('viewTransactions form3XReportType', form3XReportType);

    if (typeof form3XReportType === 'object' && form3XReportType !== null) {
      if (form3XReportType.hasOwnProperty('reportId')) {
        reportId = form3XReportType.reportId;
      } else if (form3XReportType.hasOwnProperty('reportid')) {
        reportId = form3XReportType.reportid;
      }
    }
    return reportId;
  }

  public forceItemizationToggle(trx: TransactionModel): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    // Assuming first two letters of a transaction ID would be the transaction type itself
    let transactionType = trx.transactionId.substring(0, 2).toLowerCase();
    // L-A and L-B transactions use A/B API
    if (transactionType.charAt(0) === 'l') {
      transactionType = 's' + transactionType.charAt(1);
    }
    let isItemized: boolean;
    if (trx.itemized) {
      if (trx.itemized === 'U' || trx.itemized === 'FU') {
        isItemized = false;
      } else {
        isItemized = true;
      }
    } else if (trx.itemized === null) {
      isItemized = true;
    }
    const toggleWay = isItemized ? 'unitemize' : 'itemize';
    const putURL: string = '/' + transactionType + '/force_' + toggleWay + '_' + transactionType + '?' ;
    const formData: FormData = new FormData();

    let httpOptions = new HttpHeaders();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
    formData.append('report_id', trx.reportId);
    formData.append('transaction_id', trx.transactionId);

    return this._http
        .put(`${environment.apiUrl}${putURL}`, formData, {
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

  }

  private monthlyElectionJSON = {
    "report_type": [
      {
        "report_type": "M2",
        "report_type_desciption": "February 20 Monthly - M2",
        "report_type_info": "In an election year/non-election year covers activity from January 1 thru January 31 and due on the 20th of February.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-01-01",
        "cvg_end_date": "2020-01-31",
        "due_date": "2020-02-20"
      },
      {
        "report_type": "M3",
        "report_type_desciption": "March 20 Monthly - M3",
        "report_type_info": "In an election year/non-election year covers activity from February 1 thru February 28 and due on the 20th of March.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-02-01",
        "cvg_end_date": "2020-02-29",
        "due_date": "2020-03-20"
      },
      {
        "report_type": "M4",
        "report_type_desciption": "April 20 Monthly - M4",
        "report_type_info": "In an election year/non-election year covers activity from March 1 thru March 31 and due on the 20th of April.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-03-01",
        "cvg_end_date": "2020-03-31",
        "due_date": "2020-04-20"
      },
      {
        "report_type": "M5",
        "report_type_desciption": "May 20 Monthly - M5",
        "report_type_info": "In an election year/non-election year covers activity from April 1 thru April 30 and due on the 20th of May.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-04-01",
        "cvg_end_date": "2020-04-30",
        "due_date": "2020-05-20"
      },
      {
        "report_type": "M6",
        "report_type_desciption": "June 20 Monthly - M6",
        "report_type_info": "In an election year/non-election year covers activity from May 1 thru May 31 and due on the 20th of June.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-05-01",
        "cvg_end_date": "2020-05-31",
        "due_date": "2020-06-20"
      },
      {
        "report_type": "M7S",
        "report_type_desciption": "July Monthly / Semi-Annual - M7S",
        "report_type_info": "Placeholder text for July Monthly / Semi-Annual",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-06-01",
        "cvg_end_date": "2020-06-30",
        "due_date": "2020-07-20",
        "semi-annual_dates": [
          {
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "selected": true
          },
          {
            "start_date": "2020-07-01",
            "end_date": "2020-12-31",
            "selected": false
          }
        ]
      },
      {
        "report_type": "MSA",
        "report_type_desciption": "Monthly Semi-Annual (MY) - MSA",
        "report_type_info": "Placeholder text for Monthly Semi-Annual",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": null,
        "cvg_end_date": null,
        "due_date": null,
        "disableCoverageDates": true,
        "semi-annual_dates": [
          {
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "selected": true
          },
          {
            "start_date": "2020-07-01",
            "end_date": "2020-12-31",
            "selected": false
          }
        ]
      },
      {
        "report_type": "M8",
        "report_type_desciption": "August 20 Monthly - M8",
        "report_type_info": "In an election year/non-election year covers activity from July 1 thru July 31 and due on the 20th of August.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-07-01",
        "cvg_end_date": "2020-07-31",
        "due_date": "2020-08-20"
      },
      {
        "report_type": "M9",
        "report_type_desciption": "September 20 Monthly - M9",
        "report_type_info": "In an election year/non-election year covers activity from August 1 thru August 31 and due on the 20th of September.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-08-01",
        "cvg_end_date": "2020-08-31",
        "due_date": "2020-09-20"
      },
      {
        "report_type": "M10",
        "report_type_desciption": "October 20 Monthly - M10",
        "report_type_info": "In an election year/non-election year covers activity from September 1 thru September 30 and due on the 20th of October.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-09-01",
        "cvg_end_date": "2020-09-30",
        "due_date": "2020-10-20"
      },
      {
        "report_type": "12G",
        "report_type_desciption": "12 Day Pre-General - 12G",
        "report_type_info": "Due 12 days before the election, covers activity from the close of books of the previous report filed through the 20th day before the general. A committee must file pre-primary reports only if the committee has made previously undisclosed contributions or  (...)",
        "regular_special_report_ind": "S",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-09-01",
        "cvg_end_date": "2020-09-30",
        "due_date": "2020-10-30"
      },
      {
        "report_type": "30G",
        "report_type_desciption": "30 Day Post-General - 30G",
        "report_type_info": "In an election year covers activity that occurred after the closing date of the last report through the 20th day after the general election.  The report is due 30 days after the election.",
        "regular_special_report_ind": "S",
        "default_disp_ind": "N",
        "cvg_start_date": "EFO",
        "cvg_end_date": "EFO",
        "due_date": "EFO"
      },
      {
        "report_type": "MYS",
        "report_type_desciption": "Monthly Year-End / Semi-Annual - MYS",
        "report_type_info": "Placeholder text for Monthly Year-End / Semi-Annual",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "EFO",
        "cvg_end_date": "EFO",
        "due_date": "EFO",
        "semi-annual_dates": [
          {
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "selected": false
          },
          {
            "start_date": "2020-07-01",
            "end_date": "2020-12-31",
            "selected": true
          }
        ]
      },
      {
        "report_type": "MSY",
        "report_type_desciption": "Monthly Semi-Annual (YE) - MSY",
        "report_type_info": "Placeholder text for Monthly Semi-Annual YE",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": null,
        "cvg_end_date": null,
        "due_date": null,
        "disableCoverageDates": true,
        "semi-annual_dates": [
          {
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "selected": false
          },
          {
            "start_date": "2020-07-01",
            "end_date": "2020-12-31",
            "selected": true
          }
        ]
      }
    ]
  };

  private monthlyNonElectionJSON  = {
    "report_type": [
      {
        "report_type": "M2",
        "report_type_desciption": "February 20 Monthly - M2",
        "report_type_info": "In an election year/non-election year covers activity from January 1 thru January 31 and due on the 20th of February.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-01-01",
        "cvg_end_date": "2020-01-31",
        "due_date": "2020-02-20"
      },
      {
        "report_type": "M3",
        "report_type_desciption": "March 20 Monthly - M3",
        "report_type_info": "In an election year/non-election year covers activity from February 1 thru February 28 and due on the 20th of March.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-02-01",
        "cvg_end_date": "2020-02-29",
        "due_date": "2020-03-20"
      },
      {
        "report_type": "M4",
        "report_type_desciption": "April 20 Monthly - M4",
        "report_type_info": "In an election year/non-election year covers activity from March 1 thru March 31 and due on the 20th of April.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-03-01",
        "cvg_end_date": "2020-03-31",
        "due_date": "2020-04-20"
      },
      {
        "report_type": "M5",
        "report_type_desciption": "May 20 Monthly - M5",
        "report_type_info": "In an election year/non-election year covers activity from April 1 thru April 30 and due on the 20th of May.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-04-01",
        "cvg_end_date": "2020-04-30",
        "due_date": "2020-05-20"
      },
      {
        "report_type": "M6",
        "report_type_desciption": "June 20 Monthly - M6",
        "report_type_info": "In an election year/non-election year covers activity from May 1 thru May 31 and due on the 20th of June.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-05-01",
        "cvg_end_date": "2020-05-31",
        "due_date": "2020-06-20"
      },
      {
        "report_type": "M7S",
        "report_type_desciption": "July Monthly / Semi-Annual - M7S",
        "report_type_info": "Placeholder text for July Monthly / Semi-Annual",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-06-01",
        "cvg_end_date": "2020-06-30",
        "due_date": "2020-07-20",
        "semi-annual_dates": [
          {
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "selected": true
          },
          {
            "start_date": "2020-07-01",
            "end_date": "2020-12-31",
            "selected": false
          }
        ]
      },
      {
        "report_type": "MSA",
        "report_type_desciption": "Monthly Semi-Annual (MY) - MSA",
        "report_type_info": "Placeholder text for Monthly Semi-Annual",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": null,
        "cvg_end_date": null,
        "due_date": null,
        "disableCoverageDates": true,
        "semi-annual_dates": [
          {
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "selected": true
          },
          {
            "start_date": "2020-07-01",
            "end_date": "2020-12-31",
            "selected": false
          }
        ]
      },
      {
        "report_type": "M8",
        "report_type_desciption": "August 20 Monthly - M8",
        "report_type_info": "In an election year/non-election year covers activity from July 1 thru July 31 and due on the 20th of August.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-07-01",
        "cvg_end_date": "2020-07-31",
        "due_date": "2020-08-20"
      },
      {
        "report_type": "M9",
        "report_type_desciption": "September 20 Monthly - M9",
        "report_type_info": "In an election year/non-election year covers activity from August 1 thru August 31 and due on the 20th of September.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-08-01",
        "cvg_end_date": "2020-08-31",
        "due_date": "2020-09-20"
      },
      {
        "report_type": "M10",
        "report_type_desciption": "October 20 Monthly - M10",
        "report_type_info": "In an election year/non-election year covers activity from September 1 thru September 30 and due on the 20th of October.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-09-01",
        "cvg_end_date": "2020-09-30",
        "due_date": "2020-10-20"
      },
      {
        "report_type": "M11",
        "report_type_desciption": "November 20 Monthly - M11",
        "report_type_info": "In an election year/non-election year covers activity from October 1 thru October 31 and due on the 20th of November.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-10-01",
        "cvg_end_date": "2020-10-31",
        "due_date": "2020-11-20"
      },
      {
        "report_type": "M12",
        "report_type_desciption": "December 20 Monthly - M12",
        "report_type_info": "In an election year/non-election year covers activity from November 1 thru November 30 and due on the 20th of December.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-11-01",
        "cvg_end_date": "2020-11-30",
        "due_date": "2020-12-20"
      },
      {
        "report_type": "MYS",
        "report_type_desciption": "Monthly Year-End / Semi-Annual - MYS",
        "report_type_info": "Placeholder text for Monthly Year-End / Semi-Annual",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-12-01",
        "cvg_end_date": "2020-12-31",
        "due_date": "???",
        "semi-annual_dates": [
          {
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "selected": false
          },
          {
            "start_date": "2020-07-01",
            "end_date": "2020-12-31",
            "selected": true
          }
        ]
      },
      {
        "report_type": "MSY",
        "report_type_desciption": "Monthly Semi-Annual (YE) - MSY",
        "report_type_info": "Placeholder text for Monthly Semi-Annual YE",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": null,
        "cvg_end_date": null,
        "due_date": null,
        "disableCoverageDates": true,
        "semi-annual_dates": [
          {
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "selected": false
          },
          {
            "start_date": "2020-07-01",
            "end_date": "2020-12-31",
            "selected": true
          }
        ]
      }
    ]
  };

  private quarterlyElectionJSON = {
    "report_type": [
      {
        "report_type": "Q1",
        "report_type_desciption": "April Quarterly - Q1",
        "report_type_info": "In an election year/non-election year covers activity from January 1 thru March 31 and due on the 20th of April.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-01-01",
        "cvg_end_date": "2020-03-31",
        "due_date": "2020-04-20"
      },
      {
        "report_type": "Q2S",
        "report_type_desciption": "July Quarterly / Semi-Annual - Q2S",
        "report_type_info": "Placeholder text for July Quarterly / Semi-Annual.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-04-01",
        "cvg_end_date": "2020-06-30",
        "due_date": "2020-07-20",
        "semi-annual_dates": [
          {
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "selected": true
          },
          {
            "start_date": "2020-07-01",
            "end_date": "2020-12-31",
            "selected": false
          }
        ]
      },
      {
        "report_type": "QSA",
        "report_type_desciption": "Quarterly / Semi-Annual (MY) - QSA",
        "report_type_info": "Placeholder text for Quarterly / Semi-Annual (MY).",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": null,
        "cvg_end_date": null,
        "due_date": null,
        "disableCoverageDates": true,
        "semi-annual_dates": [
          {
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "selected": true
          },
          {
            "start_date": "2020-07-01",
            "end_date": "2020-12-31",
            "selected": false
          }
        ]
      },
      {
        "report_type": "Q3",
        "report_type_desciption": "October Quarterly - Q3",
        "report_type_info": "In an election year/non-election year covers activity from Jul 1 thru September 30 and due on the 20th of October.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-07-01",
        "cvg_end_date": "2020-09-30",
        "due_date": "2020-10-20"
      },
      {
        "report_type": "QYS",
        "report_type_desciption": "Quarterly Year-End / Semi-Annual - QYS",
        "report_type_info": "Placeholder text for Quarterly Year-End / Semi-Annual.",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": "2020-10-01",
        "cvg_end_date": "2020-12-31",
        "due_date": "???",
        "semi-annual_dates": [
          {
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "selected": false
          },
          {
            "start_date": "2020-07-01",
            "end_date": "2020-12-31",
            "selected": true
          }
        ]
      },
      {
        "report_type": "QYE",
        "report_type_desciption": "Quarterly Semi-Annual (YE) - QYE",
        "report_type_info": "Placeholder text for Quarterly Semi-Annual (YE).",
        "regular_special_report_ind": "R",
        "default_disp_ind": "N",
        "cvg_start_date": null,
        "cvg_end_date": null,
        "due_date": null,
        "disableCoverageDates": true,
        "semi-annual_dates": [
          {
            "start_date": "2020-01-01",
            "end_date": "2020-06-30",
            "selected": false
          },
          {
            "start_date": "2020-07-01",
            "end_date": "2020-12-31",
            "selected": true
          }
        ]
      },
      {
        "report_type": "12C",
        "report_type_desciption": "12-Day Pre-Convention - 12C",
        "report_type_info": "Placeholder text for 12-Day Pre-Convention - 12C.",
        "regular_special_report_ind": "S",
        "default_disp_ind": "N",
        "cvg_start_date": null,
        "cvg_end_date": null,
        "due_date": null,
        "semi-annual_dates_optional": true,
        "semi-annual_dates": [
            {
              "start_date": "2020-01-01",
              "end_date": "2020-06-30",
              "selected": false
            },
            {
              "start_date": "2020-07-01",
              "end_date": "2020-12-31",
              "selected": false
            }
        ]
      },
      {
        "report_type": "12G",
        "report_type_desciption": "12-Day Pre-General - 12G",
        "report_type_info": "Placeholder text for 12-Day Pre-General - 12G.",
        "regular_special_report_ind": "S",
        "default_disp_ind": "N",
        "cvg_start_date": "EFO",
        "cvg_end_date": "EFO",
        "due_date": "EFO",
        "semi-annual_dates_optional": true,
        "semi-annual_dates": [
            {
              "start_date": "2020-01-01",
              "end_date": "2020-06-30",
              "selected": false
            },
            {
              "start_date": "2020-07-01",
              "end_date": "2020-12-31",
              "selected": false
            }
        ]
      },
      {
        "report_type": "12P",
        "report_type_desciption": "12-Day Pre-Primary - 12P",
        "report_type_info": "Placeholder text for 12-Day Pre-Primary - 12P.",
        "regular_special_report_ind": "S",
        "default_disp_ind": "N",
        "cvg_start_date": null,
        "cvg_end_date": null,
        "due_date": null,
        "semi-annual_dates_optional": true,
        "semi-annual_dates": [
            {
              "start_date": "2020-01-01",
              "end_date": "2020-06-30",
              "selected": false
            },
            {
              "start_date": "2020-07-01",
              "end_date": "2020-12-31",
              "selected": false
            }
        ]
      },
      {
        "report_type": "12R",
        "report_type_desciption": "12-Day Pre-Runoff - 12R",
        "report_type_info": "Placeholder text for 12-Day Pre-Runoff - 12R.",
        "regular_special_report_ind": "S",
        "default_disp_ind": "N",
        "cvg_start_date": null,
        "cvg_end_date": null,
        "due_date": null,
        "semi-annual_dates_optional": true,
        "semi-annual_dates": [
            {
              "start_date": "2020-01-01",
              "end_date": "2020-06-30",
              "selected": false
            },
            {
              "start_date": "2020-07-01",
              "end_date": "2020-12-31",
              "selected": false
            }
        ]
      },
      {
        "report_type": "12S",
        "report_type_desciption": "12-Day Pre-Special - 12S",
        "report_type_info": "Placeholder text for 12-Day Pre-Special - 12S.",
        "regular_special_report_ind": "S",
        "default_disp_ind": "N",
        "cvg_start_date": null,
        "cvg_end_date": null,
        "due_date": null,
        "semi-annual_dates_optional": true,
        "semi-annual_dates": [
            {
              "start_date": "2020-01-01",
              "end_date": "2020-06-30",
              "selected": false
            },
            {
              "start_date": "2020-07-01",
              "end_date": "2020-12-31",
              "selected": false
            }
        ]
      },
      {
        "report_type": "30G",
        "report_type_desciption": "30-Day Post-General - 30G",
        "report_type_info": "Placeholder text for 30-Day Post-General - 30G.",
        "regular_special_report_ind": "S",
        "default_disp_ind": "N",
        "cvg_start_date": "EFO",
        "cvg_end_date": "EFO",
        "due_date": "EFO",
        "semi-annual_dates_optional": true,
        "semi-annual_dates": [
            {
              "start_date": "2020-01-01",
              "end_date": "2020-06-30",
              "selected": false
            },
            {
              "start_date": "2020-07-01",
              "end_date": "2020-12-31",
              "selected": false
            }
        ]
      },
      {
        "report_type": "30R",
        "report_type_desciption": "30-Day Post-Runoff - 30R",
        "report_type_info": "Placeholder text for 30-Day Post-Runoff - 30R.",
        "regular_special_report_ind": "S",
        "default_disp_ind": "N",
        "cvg_start_date": null,
        "cvg_end_date": null,
        "due_date": null,
        "semi-annual_dates_optional": true,
        "semi-annual_dates": [
            {
              "start_date": "2020-01-01",
              "end_date": "2020-06-30",
              "selected": false
            },
            {
              "start_date": "2020-07-01",
              "end_date": "2020-12-31",
              "selected": false
            }
        ]
      },
      {
        "report_type": "30S",
        "report_type_desciption": "30-Day Post-Special - 30S",
        "report_type_info": "Placeholder text for 30-Day Post-Special - 30S.",
        "regular_special_report_ind": "S",
        "default_disp_ind": "N",
        "cvg_start_date": null,
        "cvg_end_date": null,
        "due_date": null,
        "semi-annual_dates_optional": true,
        "semi-annual_dates": [
            {
              "start_date": "2020-01-01",
              "end_date": "2020-06-30",
              "selected": false
            },
            {
              "start_date": "2020-07-01",
              "end_date": "2020-12-31",
              "selected": false
            }
        ]
      }
    ]
  };
}
