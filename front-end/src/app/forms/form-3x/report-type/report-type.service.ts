import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, identity } from 'rxjs';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';
import { form3xReportTypeDetails } from '../../../shared/interfaces/FormsService//FormsService';
import { DatePipe } from '@angular/common';


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
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url: string = '/core/get_report_types?form_type=F3X';
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
  public saveReport(formType: string, access_type: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url: string = '/core/reports';

    let params = new HttpParams();
    let formData: FormData = new FormData();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let form3xReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (form3xReportType === null) {
      let form3xReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
    }

    formData.append('form_type', `F${formType}`);

    if (form3xReportType.hasOwnProperty('reportType')) {
      formData.append('report_type', form3xReportType.reportType);
    } else if (form3xReportType.hasOwnProperty('reporttype')) {
      formData.append('report_type', form3xReportType.reporttype);
    }

    if (form3xReportType.hasOwnProperty('cvgStartDate')) {
      formData.append('cvg_start_dt', form3xReportType.cvgStartDate);
    } else if (form3xReportType.hasOwnProperty('cvgstartdate')) {
      formData.append('cvg_start_dt', form3xReportType.cvgstartdate);
    }

    if (form3xReportType.hasOwnProperty('cvgEndDate')) {
      formData.append('cvg_end_dt', form3xReportType.cvgEndDate);
    } else if (form3xReportType.hasOwnProperty('cvgenddate')) {
      formData.append('cvg_end_dt', form3xReportType.cvgenddate);
    }

    if (form3xReportType.hasOwnProperty('dueDate')) {
      formData.append('due_dt', form3xReportType.dueDate);
    } else if (form3xReportType.hasOwnProperty('duedate')) {
      formData.append('due_dt', form3xReportType.duedate);
    }

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

    if (typeof form3xReportType.electionCode === 'string') {
      if (form3xReportType.electionCode.length >= 1) {
        formData.append('election_code', form3xReportType.electionCode);
      }
    }

    if (form3xReportType.election_date !== null) {
      if (typeof form3xReportType.election_date === 'string') {
        if (form3xReportType.election_date.length >= 1) {
          formData.append('date_of_election', this._datePipe.transform(form3xReportType.election_date, 'MM/dd/yyyy'));
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

    if (access_type === 'Saved') {
      formData.append('status', 'Saved');
    } else if (access_type === 'Submitted') {
      formData.append('status', 'Submitted');
    }

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

    if (form3xReportType.additionalEmail1 !== null) {
      if (typeof form3xReportType.additionalEmail1 === 'string') {
        if (form3xReportType.additionalEmail1.length >= 1) {
          formData.append('additional_email_1', form3xReportType.additionalEmail1);
        }
      }
    }

    if (form3xReportType.additionalEmail2 !== null) {
      if (typeof form3xReportType.additionalEmail2 === 'string') {
        if (form3xReportType.additionalEmail2.length >= 1) {
          formData.append('additional_email_2', form3xReportType.additionalEmail2);
        }
      }
    }

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

  public signandSaveSubmitReport(formType: string, access_type: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url = '/core/reports';
    
    let params = new HttpParams();
    let formData: FormData = new FormData();
    console.log('signandSaveSubmitReport called');
    console.log('signandSaveSubmitReport formType = ', formType);
    console.log('signandSaveSubmitReport access_type = ', access_type);

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let form3xReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
    

    if (form3xReportType === null) {
      console.log('get backup object');
      form3xReportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));
      console.log('backup object form3xReportType = ', form3xReportType);
    }

    localStorage.setItem('F3X_submit_backup', JSON.stringify(form3xReportType));
    console.log('signandSaveSubmitReport access_type you reached here = ', access_type);
    formData.append('form_type', `F${formType}`);

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

    console.log('signandSaveSubmitReport access_type you reached here1 = ', access_type);

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

    console.log(' access_type =', access_type);

    if (access_type === 'Saved') {
      formData.append('status', 'Saved');
    } else if (access_type === 'Submitted') {
      formData.append('status', 'Submitted');
    }

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

    console.log('signandSaveSubmitReport formData = ', formData);

    if (access_type === 'Saved') {
      console.log('signandSaveSubmitReport HTTP called with access_type = ', access_type);
      return this._http
        .put(`${environment.apiUrl}${url}`, formData, {
          headers: httpOptions
        })
        .pipe(
          map(res => {
            if (res) {
              console.log('Form 3X save res = ', res);
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
      console.log('signandSaveSubmitReport HTTP called with access_type = ', access_type);
      console.log('submit Report form 3X submitted...');
      url = '/core/submit_report';
      return this._http
        .put(`${environment.apiUrl}${url}`, formData, {
          headers: httpOptions
        })
        .pipe(
          map(res => {
            if (res) {
              console.log('submit Report form 3X submitted res = ', res);
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
    console.log('submitForm called');
    console.log('submitForm formType = ', formType);
    console.log('submitForm callFrom = ', callFrom);

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let form3xReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));
    console.log(' submitForm form3xReportType = ', form3xReportType);

    if (form3xReportType === null) {
      console.log('get backup object');
      form3xReportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
      if (form3xReportType === null) {
        form3xReportType = JSON.parse(localStorage.getItem('F3X_submit_backup'));
      }
    }

    // console.log(' submitForm form3xReportType = ', form3xReportType);
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

    console.log('form3xReportType: ', form3xReportType);
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

    console.log('printForm formType = ', formType);

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let form3xReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (form3xReportType === null) {
      console.log('get backup object');
      form3xReportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
      console.log('backup object form3xReportType = ', form3xReportType);
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

  public printPreviewPdf(formType: string, callFrom: string, transactions?: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url: string = '/core/create_json_builders'; //Actual JSON file genaration URL
    //let url: string = '/core/create_json_builders_test';
    let formData: FormData = new FormData();

    console.log("printPreviewPdf formType = ", formType);
    console.log("printPreviewPdf callFrom = ", callFrom);
    console.log("printPreviewPdf transactions ==", transactions);

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let form3xReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (form3xReportType === null)
    {
      form3xReportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
      console.log(" printPreviewPdf backup object form3xReportType = ", form3xReportType);
    }
    
    if (form3xReportType.hasOwnProperty('reportId')) {
      console.log(" printPreviewPdf reportId found");
      formData.append('report_id', form3xReportType.reportId);
    } else if (form3xReportType.hasOwnProperty('reportid')) {   
      console.log(" printPreviewPdf reportid found");
      formData.append('report_id', form3xReportType.reportid);
    }

    formData.append('form_type', `F${formType}`);
    formData.append('call_from', callFrom);

    if ( typeof transactions !== 'undefined' ){
      if (transactions.length > 0){
        console.log(" printPreviewPdf transactions =", transactions);
        //formData.append('transaction_id',  JSON.stringify(transactions.replace(' ','')));
        formData.append('transaction_id',  transactions.replace(' ',''));
      }
    }

    return this._http
      .post(`${environment.apiUrl}${url}`, formData, {
        headers: httpOptions
      });
   }

   public prepare_json_builders_data(formType: string,  transactions?:string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url: string = '/core/prepare_json_builders_data';  //JSON builder data preparation URL

    let formData: FormData = new FormData();

    console.log("prepare_json_builders_data formType = ", formType);
    console.log("prepare_json_builders_data transactions=", transactions);

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let form3xReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (form3xReportType === null)
    {
      form3xReportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
      console.log("prepare_json_builders_data backup object form3xReportType = ", form3xReportType);
    }
  
  
    if (form3xReportType.hasOwnProperty('reportId')) {
      formData.append('report_id', form3xReportType.reportId);
      console.log(" prepare_json_builders_data reportId found");
    } else if (form3xReportType.hasOwnProperty('reportid')) {   
      formData.append('report_id', form3xReportType.reportid);
      console.log(" printPreprepare_json_builders_dataviewPdf reportid found");
    }

    if ( typeof transactions !== 'undefined' ){
      if (transactions.length > 0){
        console.log("prepare_json_builders_data transactions =", transactions);
        //formData.append('transaction_id', JSON.stringify(transactions.replace(' ','')));
        formData.append('transaction_id',  transactions.replace(' ',''));
      }
    }
    return this._http
      .post(`${environment.apiUrl}${url}`, formData, {
        headers: httpOptions
      });
   }

   public printPreview(accessFrom: string, formType: string, transactions?: string): void {
    
    if (accessFrom !=='transaction_table_screen') {
      this.signandSaveSubmitReport(formType,'Saved');
      console.log("printPreview Data saved successfully...!");
      console.log("printPreview transactions =", transactions);
    }

    if (typeof transactions === 'undefined') {
      console.log("No transactions data");
      console.log("formType", formType);
      this.prepare_json_builders_data(formType)
      .subscribe( res => {
        if (res) {
             console.log("Form 3X prepare_json_builders_data res = ", res);
             if (res['Response']==='Success') {
                    console.log(" Form 3X prepare_json_builders_data successfully processed...!");
                    this.printPreviewPdf(formType, "PrintPreviewPDF")
                      .subscribe(res => {
                      if(res) {
                        console.log("Form 3X  printPriview res ...",res);
                        if (res.hasOwnProperty('results')) {
                          if (res['results.pdf_url'] !== null) {
                            console.log("res['results.pdf_url'] = ",res['results.pdf_url']);
                            window.open(res.results.pdf_url, '_blank');
                          }
                        }
                      }
                  },
                  (error) => {
                    console.log('error: ', error);
                  });/*  */
                  }       
        }
      },
        (error) => {
          console.log('error: ', error);
        });/*  */
    } else if (transactions !== 'undefined' && (transactions.length>0)) { 
      console.log("transactions data");
      console.log("formType", formType);
      //var transactionsArray: Array<string> = transactions.split(",");
      this.prepare_json_builders_data(formType, transactions)
      .subscribe( res => {
        if (res) {
             console.log("Form 3X prepare_json_builders_data res = ", res);
             if (res['Response']==='Success') {
                    console.log(" Form 3X prepare_json_builders_data successfully processed...!");
                    this.printPreviewPdf(formType, "PrintPreviewPDF",transactions)
                      .subscribe(res => {
                      if(res) {
                        console.log("Form 3X  printPriview res ...",res);
                        if (res.hasOwnProperty('results')) {
                          if (res['results.pdf_url'] !== null) {
                            console.log("res['results.pdf_url'] = ",res['results.pdf_url']);
                            window.open(res.results.pdf_url, '_blank');
                          }
                        }
                      }
                  },
                  (error) => {
                    console.log('error: ', error);
                  });/*  */
                  }       
        }
      },
        (error) => {
          console.log('error: ', error);
        });/*  */
    }
   
  }

  public getReportIdFromStorage(formType: string) {
    let reportId = '0';
    let form3XReportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (form3XReportType === null || typeof form3XReportType === 'undefined') {
      form3XReportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
    }

    console.log('viewTransactions form3XReportType', form3XReportType);

    if (typeof form3XReportType === 'object' && form3XReportType !== null) {
      if (form3XReportType.hasOwnProperty('reportId')) {
        reportId = form3XReportType.reportId;
      } else if (form3XReportType.hasOwnProperty('reportid')) {
        reportId = form3XReportType.reportid;
      }
    }
    return reportId;
  }
}
