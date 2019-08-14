import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, identity } from 'rxjs';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { UtilService } from '../../../shared/utils/util.service';
import { environment } from '../../../../environments/environment';
import { ScheduleActions } from './schedule-actions.enum';

@Injectable({
  providedIn: 'root'
})
export class IndividualReceiptService {
  constructor(private _http: HttpClient, private _cookieService: CookieService, private _utilService: UtilService) {}

  /**
   * Gets the dynamic form fields.
   *
   * @param      {string}  formType         The form type
   * @param      {string}  transactionType  The transaction type
   */
  public getDynamicFormFields(formType: string, transactionType: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = `${environment.apiUrl}/core/get_dynamic_forms_fields`;
    let httpOptions = new HttpHeaders();
    let params = new HttpParams();
    let formData: FormData = new FormData();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('form_type', `F${formType}`);
    params = params.append('transaction_type', transactionType);

    return this._http.get(url, {
      headers: httpOptions,
      params
    });
  }

  /**
   * Saves a schedule.
   *
   * @param      {string}           formType  The form type
   * @param      {ScheduleActions}  scheduleAction  The type of action to save (add, edit)
   */
  public saveSchedule(formType: string, scheduleAction: ScheduleActions): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = '/sa/schedA';
    const committeeDetails: any = JSON.parse(localStorage.getItem('committee_details'));
    let reportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (reportType === null || typeof reportType === 'undefined') {
      reportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
    }

    const transactionType: any = JSON.parse(localStorage.getItem(`form_${formType}_transaction_type`));
    const receipt: any = JSON.parse(localStorage.getItem(`form_${formType}_receipt`));
    const formData: FormData = new FormData();

    let httpOptions = new HttpHeaders();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    /**
     * This has to be removed.
     * I'm not hard coding anything any more.
     * Or this has to be changed to just lower case.  This is not a
     * good practice at all.  Please do better then this.
     */
    formData.append('cmte_id', committeeDetails.committeeid);
    // With Edit Report Functionality
    if (reportType.hasOwnProperty('reportId')) {
      formData.append('report_id', reportType.reportId);
    } else if (reportType.hasOwnProperty('reportid')) {
      formData.append('report_id', reportType.reportid);
    }

    console.log();

    for (const [key, value] of Object.entries(receipt)) {
      if (value !== null) {
        if (typeof value === 'string') {
          formData.append(key, value);
        }
      }
    }

    if (scheduleAction === ScheduleActions.add) {
      return this._http
        .post(`${environment.apiUrl}${url}`, formData, {
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

  /**
   * Saves a schedule a using POST.  The POST API supports saving an existing
   * transaction.  Therefore, transaction_id is required in this API call.
   *
   * TODO consider modifying saveScheduleA() to support both POST and PUT.
   *
   * @param      {string}  formType  The form type
   */
  public putScheduleA(formType: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = '/sa/schedA';
    const committeeDetails: any = JSON.parse(localStorage.getItem('committee_details'));
    let reportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (reportType === null || typeof reportType === 'undefined') {
      reportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
    }

    const transactionType: any = JSON.parse(localStorage.getItem(`form_${formType}_transaction_type`));
    const receipt: any = JSON.parse(localStorage.getItem(`form_${formType}_receipt`));

    let httpOptions = new HttpHeaders();
    const formData: FormData = new FormData();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    // Needed for update but not for add
    formData.append('transaction_id', receipt.transactionId);

    formData.append('cmte_id', committeeDetails.committeeid);
    // With Edit Report Functionality
    if (reportType.hasOwnProperty('reportId')) {
      formData.append('report_id', reportType.reportId);
    } else if (reportType.hasOwnProperty('reportid')) {
      formData.append('report_id', reportType.reportid);
    }

    // formData.append('report_id', reportType.reportId);
    formData.append('transaction_type', '15');
    formData.append('line_number', '11AI');
    formData.append('first_name', receipt.ContributorFirstName);
    formData.append('last_name', receipt.ContributorLastName);
    formData.append('state', receipt.ContributorState);
    formData.append('city', receipt.ContributorCity);
    formData.append('zip_code', receipt.ContributorZip);
    formData.append('occupation', receipt.ContributorOccupation);
    formData.append('employer', receipt.ContributorEmployer);
    formData.append('contribution_amount', receipt.ContributionAmount);
    formData.append('contribution_date', receipt.ContributionDate);
    // formData.append('contribution_aggregate', receipt.ContributionAggregate);
    formData.append('entity_type', receipt.EntityType);
    if (receipt.ContributorMiddleName !== null) {
      if (typeof receipt.ContributorMiddleName === 'string') {
        formData.append('middle_name', receipt.ContributorMiddleName);
      }
    }
    if (receipt.ContributorPrefix !== null) {
      if (typeof receipt.ContributorPrefix === 'string') {
        formData.append('prefix', receipt.ContributorPrefix);
      }
    }
    if (receipt.ContributorSuffix !== null) {
      if (typeof receipt.ContributorSuffix === 'string') {
        formData.append('suffix', receipt.ContributorSuffix);
      }
    }
    formData.append('street_1', receipt.ContributorStreet1);
    if (receipt.ContributorStreet2 !== null) {
      if (typeof receipt.ContributorStreet2 === 'string') {
        formData.append('street_2', receipt.ContributorStreet2);
      }
    }
    if (receipt.MemoText !== null) {
      if (typeof receipt.MemoText === 'string') {
        formData.append('memo_text', receipt.MemoText);
      }
    }
    if (receipt.MemoCode !== null) {
      if (typeof receipt.MemoCode === 'string') {
        formData.append('memo_code', receipt.MemoCode);
      }
    }
    if (receipt.ContributionPurposeDescription !== null) {
      if (typeof receipt.ContributionPurposeDescription === 'string') {
        formData.append('purpose_description', receipt.ContributionPurposeDescription);
      }
    }
    // if (receipt.ContributionAggregate !== null) {
    //   if (typeof receipt.ContributionAggregate === 'string') {
    //     formData.append('contribution_aggregate', receipt.ContributionAggregate);
    //   }
    // }

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
  }

  /**
   * Gets the schedule after submitted.
   *
   * @param      {string}  formType  The form type
   * @param      {any}     receipt   The receipt
   */
  public getSchedule(formType: string, receipt: any): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = `${environment.apiUrl}/core/thirdNavTransactionTypes`;
    const data: any = JSON.stringify(receipt);
    let httpOptions = new HttpHeaders();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http.get(url, {
      headers: httpOptions,
      params: {
        report_id: receipt.report_id
      }
    });
  }

  // /**
  //  * Returns aggregate total for contributor.
  //  *
  //  * @param      {number}  reportId            The report identifier
  //  * @param      {string}  transactionType     The transaction type
  //  * @param      {string}  contributionDate    The contribution date
  //  * @param      {string}  entityId            The entity identifier
  //  * @param      {number}  contributionAmount  The contribution amount
  //  */
  // public aggregateAmount(
  //   reportId: number,
  //   transactionType: string,
  //   contributionDate: string,
  //   entityId: string,
  //   contributionAmount: number
  // ): Observable<any> {
  //   const token: string = JSON.parse(this._cookieService.get('user'));
  //   const url: string = `${environment.apiUrl}/sa/aggregate_amount`;
  //   const data: any = {
  //     report_id: reportId,
  //     transaction_type: transactionType,
  //     contribution_date: contributionDate,
  //     entity_id: entityId,
  //     contribution_amount: contributionAmount
  //   };
  //   let httpOptions = new HttpHeaders();

  //   httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

  //   return this._http
  //     .post(url, data, {
  //       headers: httpOptions
  //     })
  //     .pipe(
  //       map(res => {
  //         if (res) {
  //           console.log('res: ', res);
  //           return res;
  //         }
  //         return false;
  //       })
  //     );
  // }

  /**
   * Returns aggregate total for contributor.
   *
   * @param      {number}  reportId                   The report identifier
   * @param      {string}  entityId                   The entity identifier
   * @param      {string}  transactionTypeIdentifier  The transaction type
   */
  public getContributionAggregate(
    reportId: string,
    entityId: number,
    transactionTypeIdentifier: string
  ): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url = '/sa/contribution_aggregate';
    let httpOptions = new HttpHeaders();
    let params = new HttpParams();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('report_id', reportId);
    params = params.append('entity_id', entityId.toString());
    params = params.append('transaction_type_identifier', transactionTypeIdentifier);

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions,
      params
    });
  }

  public getOpexpMockData() {
    const res = JSON.parse(
      `
      {  
        "data":{  
           "formFields":[  
              {  
                 "childForm":false,
                 "childFormTitle":null,
                 "colClassName":"col col-md-4",
                 "seperator":true,
                 "cols":[  
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":null,
                       "infoIcon":false,
                       "infoText":null,
                       "name":"org_type",
                       "toggle":false,
               "entityGroup":null,
                       "type":"select",
                       "value":null,
                       "scroll":false,
                       "height":"30px",
                       "width":"98px",
                       "validation":{  
                          "required":true
                       }
                    }
                 ]
              },
              {  
                 "childForm":false,
                 "childFormTitle":null,
                 "colClassName":"col col-md-4",
                 "seperator":false,
                 "cols":[  
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":"Organization Name",
                       "infoIcon":false,
                       "infoText":null,
                       "name":"entity_name",
                       "toggle":true,
                       "entityGroup":"org-group",
                       "type":"text",
                       "value":null,
                       "scroll":false,
                       "height":"30px",
                       "width":"197px",
                       "validation":{  
                          "required":true,
                          "max":200,
                          "alphaNumeric":true
                       }
                    },
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":"Last Name",
                       "infoIcon":false,
                       "infoText":null,
                       "name":"last_name",
                       "toggle":true,
                       "entityGroup":"ind-group",
                       "type":"text",
                       "value":null,
                       "scroll":false,
                       "height":"30px",
                       "width":"197px",
                       "validation":{  
                          "required":true,
                          "max":30,
                          "alphaNumeric":true
                       }
                    },
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":"First Name",
                       "infoIcon":false,
                       "infoText":null,
                       "name":"first_name",
                       "entityGroup":"ind-group",
                       "toggle":true,
                       "type":"text",
                       "value":null,
                       "scroll":false,
                       "height":"30px",
                       "width":"197px",
                       "validation":{  
                          "required":true,
                          "max":20,
                          "alphaNumeric":true
                       }
                    },
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":"Middle Name",
                       "infoIcon":false,
                       "infoText":null,
                       "name":"middle_name",
                       "entityGroup":"ind-group",
                       "toggle":true,
                       "type":"text",
                       "value":null,
                       "scroll":false,
                       "height":"30px",
                       "width":"197px",
                       "validation":{  
                          "required":false,
                          "max":20,
                          "alphaNumeric":true
                       }
                    }
                 ]
              },
              {  
                 "childForm":false,
                 "childFormTitle":null,
                 "colClassName":"col col-md-4",
                 "seperator":true,
                 "cols":[  
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":"Prefix",
                       "infoIcon":false,
                       "infoText":null,
                       "name":"prefix",
                       "entityGroup":"ind-group",
                       "toggle":true,
                       "type":"text",
                       "value":null,
                       "scroll":false,
                       "height":"30px",
                       "width":"98.35px",
                       "validation":{  
                          "required":false,
                          "max":10,
                          "alphaNumeric":true
                       }
                    },
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":"Suffix",
                       "infoIcon":false,
                       "infoText":null,
                       "name":"suffix",
                       "entityGroup":"ind-group",
                       "toggle":true,
                       "type":"text",
                       "value":null,
                       "scroll":false,
                       "height":"30px",
                       "width":"98.35px",
                       "validation":{  
                          "required":false,
                          "max":10,
                          "alphaNumeric":true
                       }
                    }
                 ]
              },
              {  
                 "childForm":false,
                 "childFormTitle":null,
                 "colClassName":"col col-md-4",
                 "seperator":false,
                 "cols":[  
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":"Street 1",
                       "infoIcon":false,
                       "infoText":null,
                       "name":"street_1",
                       "toggle":false,
               "entityGroup":null,
                       "type":"text",
                       "value":null,
                       "scroll":false,
                       "height":"30px",
                       "width":"275px",
                       "validation":{  
                          "required":true,
                          "max":34,
                          "alphaNumeric":true
                       }
                    },
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":"Street 2",
                       "infoIcon":false,
                       "infoText":null,
                       "name":"street_2",
                       "toggle":false,
               "entityGroup":null,
                       "type":"text",
                       "value":null,
                       "scroll":false,
                       "height":"30px",
                       "width":"275px",
                       "validation":{  
                          "required":false,
                          "max":34,
                          "alphaNumeric":true
                       }
                    }
                 ]
              },
              {  
                 "childForm":false,
                 "childFormTitle":null,
                 "colClassName":"col col-md-4",
                 "seperator":true,
                 "cols":[  
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":"City",
                       "infoIcon":false,
                       "infoText":null,
                       "name":"city",
                       "toggle":false,
               "entityGroup":null,
                       "type":"text",
                       "value":null,
                       "scroll":false,
                       "height":"30px",
                       "width":"197px",
                       "validation":{  
                          "required":true,
                          "max":30,
                          "alphaNumeric":true
                       }
                    },
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":"State",
                       "infoIcon":false,
                       "infoText":null,
                       "name":"state",
                       "toggle":false,
               "entityGroup":null,
                       "type":"select",
                       "value":null,
                       "scroll":false,
                       "height":"30px",
                       "width":"98px",
                       "validation":{  
                          "required":true,
                          "max":2,
                          "alphaNumeric":true
                       }
                    },
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":"Zip Code",
                       "infoIcon":false,
                       "infoText":null,
                       "name":"zip_code",
                       "toggle":false,
               "entityGroup":null,
                       "type":"text",
                       "value":null,
                       "scroll":false,
                       "height":"30px",
                       "width":"98px",
                       "validation":{  
                          "required":true,
                          "max":10,
                          "alphaNumeric":true
                       }
                    }
                 ]
              },
              {  
                 "childForm":false,
                 "childFormTitle":null,
                 "colClassName":"col col-md-4",
                 "seperator":false,
                 "cols":[  
                    {  
                       "inputGroup":true,
                       "inputIcon":"calendar-icon",
                       "text":"Contribution Date",
                       "infoIcon":true,
                       "infoText":"Request language from RAD",
                       "name":"contribution_date",
                       "toggle":false,
               "entityGroup":null,
                       "type":"date",
                       "value":null,
                       "scroll":false,
                       "height":"30px",
                       "width":"154px",
                       "validation":{  
                          "required":true,
                          "max":null,
                          "date":true
                       }
                    }
                 ]
              },
              {  
                 "childForm":false,
                 "childFormTitle":null,
                 "colClassName":"col col-md-4",
                 "seperator":true,
                 "cols":[  
                    {  
                       "inputGroup":true,
                       "inputIcon":"dollar-sign-icon",
                       "text":"Contribution Amount",
                       "infoIcon":true,
                       "infoText":"Request language from RAD",
                       "name":"contribution_amount",
                       "toggle":false,
               "entityGroup":null,
                       "type":"text",
                       "value":null,
                       "scroll":false,
                       "height":"30px",
                       "width":"154px",
                       "validation":{  
                          "required":true,
                          "max":12,
                          "dollarAmount":true
                       }
                    },
                    {  
                       "inputGroup":true,
                       "inputIcon":"dollar-sign-icon",
                       "text":"Contribution Aggregate",
                       "infoIcon":true,
                       "infoText":"Request language from RAD",
                       "name":"contribution_aggregate",
                       "toggle":false,
               "entityGroup":null,
                       "type":"text",
                       "value":"0.00",
                       "scroll":false,
                       "height":"30px",
                       "width":"196px",
                       "validation":{  
                          "required":false,
                          "max":12,
                          "dollarAmount":true
                       }
                    },
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":"Memo Code",
                       "infoIcon":true,
                       "infoText":"Request language from RAD",
                       "name":"memo_code",
                       "toggle":false,
               "entityGroup":null,
                       "type":"checkbox",
                       "value":"X",
                       "scroll":false,
                       "height":"24px",
                       "width":"24px",
                       "validation":{  
                          "required":false,
                          "max":1,
                          "alphaNumeric":true
                       }
                    }
                 ]
              },
              {  
                 "childForm":false,
                 "childFormTitle":null,
                 "colClassName":"col col-md-5",
                 "seperator":false,
                 "cols":[  
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":"Contribution Purpose Description",
                       "infoIcon":true,
                       "infoText":"Request language from RAD",
                       "name":"purpose_description",
                       "toggle":false,
               "entityGroup":null,
                       "type":"text",
                       "value":null,
                       "scroll":true,
                       "height":"40px",
                       "width":"380px",
                       "validation":{  
                          "required":false,
                          "max":100,
                          "alphaNumeric":true
                       }
                    },
                    {  
                       "inputGroup":false,
                       "inputIcon":"",
                       "text":"Memo Text",
                       "infoIcon":true,
                       "infoText":"Request language from RAD",
                       "name":"memo_text",
                       "toggle":false,
               "entityGroup":null,
                       "type":"text",
                       "value":null,
                       "scroll":true,
                       "height":"40px",
                       "width":"380px",
                       "validation":{  
                          "required":false,
                          "max":100,
                          "alphaNumeric":true
                       }
                    }
                 ]
              }
           ],
           "hiddenFields":[  
              {  
                 "type":"hidden",
                 "name":"entity_type",
                 "value":"IND"
              },
              {  
                 "type":"hidden",
                 "name":"line_number",
                 "value":"11A"
              },
              {  
                 "type":"hidden",
                 "name":"transaction_id",
                 "value":null
              },
              {  
                 "type":"hidden",
                 "name":"back_ref_transaction_id",
                 "value":null
              },
              {  
                 "type":"hidden",
                 "name":"back_ref_sched_name",
                 "value":null
              },
              {  
                 "type":"hidden",
                 "name":"transaction_type_identifier",
                 "value":"INDV_REC"
              },
              {  
                 "type":"hidden",
                 "name":"transaction_type",
                 "value":"15"
              },
              {  
                 "type":"hidden",
                 "name":"default_org_type",
                 "value":"Individual"
              }
           ],
           "orgTypes":[  
              {  
                 "name":"Individual",
                 "code":"IND",
                 "group":"ind-group",
                 "selected":true
              },
              {  
                 "name":"Candidate",
                 "code":"CAN",
                 "group":"ind-group",
                 "selected":false
              },
              {  
                 "name":"Organization",
                 "code":"ORG",
                 "group":"org-group",
                 "selected":false
              }
           ],
           "states":[  
              {  
                 "name":"Alabama",
                 "code":"AL"
              },
              {  
                 "name":"Alaska",
                 "code":"AK"
              },
              {  
                 "name":"Arizona",
                 "code":"AZ"
              },
              {  
                 "name":"Arkansas",
                 "code":"AR"
              },
              {  
                 "name":"California",
                 "code":"CA"
              },
              {  
                 "name":"Colorado",
                 "code":"CO"
              },
              {  
                 "name":"Connecticut",
                 "code":"CT"
              },
              {  
                 "name":"Delaware",
                 "code":"DE"
              },
              {  
                 "name":"District Of Columbia",
                 "code":"DC"
              },
              {  
                 "name":"Florida",
                 "code":"FL"
              },
              {  
                 "name":"Georgia",
                 "code":"GA"
              },
              {  
                 "name":"Guam",
                 "code":"GU"
              },
              {  
                 "name":"Hawaii",
                 "code":"HI"
              },
              {  
                 "name":"Idaho",
                 "code":"ID"
              },
              {  
                 "name":"Illinois",
                 "code":"IL"
              },
              {  
                 "name":"Indiana",
                 "code":"IN"
              },
              {  
                 "name":"Iowa",
                 "code":"IA"
              },
              {  
                 "name":"Kansas",
                 "code":"KS"
              },
              {  
                 "name":"Kentucky",
                 "code":"KY"
              },
              {  
                 "name":"Louisiana",
                 "code":"LA"
              },
              {  
                 "name":"Maine",
                 "code":"ME"
              },
              {  
                 "name":"Maryland",
                 "code":"MD"
              },
              {  
                 "name":"Massachusetts",
                 "code":"MA"
              },
              {  
                 "name":"Michigan",
                 "code":"MI"
              },
              {  
                 "name":"Minnesota",
                 "code":"MN"
              },
              {  
                 "name":"Mississippi",
                 "code":"MS"
              },
              {  
                 "name":"Missouri",
                 "code":"MO"
              },
              {  
                 "name":"Montana",
                 "code":"MT"
              },
              {  
                 "name":"Nebraska",
                 "code":"NE"
              },
              {  
                 "name":"Nevada",
                 "code":"NV"
              },
              {  
                 "name":"New Hampshire",
                 "code":"NH"
              },
              {  
                 "name":"New Jersey",
                 "code":"NJ"
              },
              {  
                 "name":"New Mexico",
                 "code":"NM"
              },
              {  
                 "name":"New York",
                 "code":"NY"
              },
              {  
                 "name":"North Carolina",
                 "code":"NC"
              },
              {  
                 "name":"North Dakota",
                 "code":"ND"
              },
              {  
                 "name":"Ohio",
                 "code":"OH"
              },
              {  
                 "name":"Oklahoma",
                 "code":"OK"
              },
              {  
                 "name":"Oregon",
                 "code":"OR"
              },
              {  
                 "name":"Pennsylvania",
                 "code":"PA"
              },
              {  
                 "name":"Puerto Rico",
                 "code":"PR"
              },
              {  
                 "name":"Rhode Island",
                 "code":"RI"
              },
              {  
                 "name":"South Carolina",
                 "code":"SC"
              },
              {  
                 "name":"South Dakota",
                 "code":"SD"
              },
              {  
                 "name":"Tennessee",
                 "code":"TN"
              },
              {  
                 "name":"Texas",
                 "code":"TX"
              },
              {  
                 "name":"Utah",
                 "code":"UT"
              },
              {  
                 "name":"Vermont",
                 "code":"VT"
              },
              {  
                 "name":"Virginia",
                 "code":"VA"
              },
              {  
                 "name":"U.S. Virgin Islands",
                 "code":"VI"
              },
              {  
                 "name":"Washington",
                 "code":"WA"
              },
              {  
                 "name":"West Virginia",
                 "code":"WV"
              },
              {  
                 "name":"Wisconsin",
                 "code":"WI"
              },
              {  
                 "name":"Wyoming",
                 "code":"WY"
              },
              {  
                 "name":"Foreign Countries",
                 "code":"ZZ"
              },
              {  
                 "name":"American Samoa",
                 "code":"AS"
              },
              {  
                 "name":"Northern Mariana Islands",
                 "code":"MP"
              },
              {  
                 "name":"United States",
                 "code":"US"
              },
              {  
                 "name":"Armed Forces Americas",
                 "code":"AA"
              },
              {  
                 "name":"Armed Forces Europe",
                 "code":"AE"
              },
              {  
                 "name":"Armed Forces Pacific",
                 "code":"AP"
              }
           ],
           "titles":[  
              {  
                 "fieldset":true,
                 "colClassName":"col col-md-12 fieldset",
                 "label":"Contributor Information:"
              }
           ]
        }
     }
    `
    );
    return Observable.of(res);
  }
}
