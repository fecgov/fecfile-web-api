import { CookieService } from 'ngx-cookie-service';

import { Injectable , ChangeDetectionStrategy } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { environment } from 'src/environments/environment';
import { map } from 'rxjs/operators';
import { DatePipe } from '@angular/common';

@Injectable({
  providedIn: 'root'
})
export class SchedEService {

  private _datePipe: DatePipe;

  constructor(private _http: HttpClient,
    private _cookieService: CookieService) {
      this._datePipe = new DatePipe('en-US');
  }

  public getAggregate(formData: any, formType: string): Observable<any> {
    let allRequiredFieldsPresent = false;
    if(formData.dissemination_date || formData.disbursement_date){
      if(formData.cand_office && formData.cand_office === 'P'){
        if(formData.election_code && formData.cand_election_year){
          allRequiredFieldsPresent = true;
        }
      }
      else if(formData.cand_office && formData.cand_office === 'S'){
        if(formData.election_code && formData.cand_election_year && formData.cand_office_state){
          allRequiredFieldsPresent = true;
        }
      }
      else if(formData.cand_office && formData.cand_office === 'H'){
        if(formData.election_code && formData.cand_election_year && formData.cand_office_state && formData.cand_office_district){
          allRequiredFieldsPresent = true;
        }
      }
    }


    if (allRequiredFieldsPresent) {
      const token: string = JSON.parse(this._cookieService.get('user'));
      let httpOptions = new HttpHeaders();
      const url = '/se/get_sched_e_ytd_amount';

      httpOptions = httpOptions.append('Content-Type', 'application/json');
      httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

      let params = new HttpParams();
      params = params.append('cand_office', formData.cand_office);

      if ((formData.cand_office === 'S' || formData.cand_office === 'H')) {
        params = params.append('cand_state', formData.cand_office_state);
      }

      if (formData.cand_office === 'H') {
        params = params.append('cand_district', formData.cand_office_district);
      }

      params = params.append('election_code', `${formData.election_code}${formData.cand_election_year}`);
      
      if(formData.dissemination_date){
        params = params.append('dissemination_date', this._datePipe.transform(formData.dissemination_date, 'MM/dd/yyyy'));
      }
      if(formData.disbursement_date){
        params = params.append('disbursement_date', this._datePipe.transform(formData.disbursement_date, 'MM/dd/yyyy'));
      }

      params = params.append('form_type', `F${formType}`);

      return this._http
        .get(
          `${environment.apiUrl}${url}`,
          {
            headers: httpOptions,
            params
          }
        )
        .pipe(map(res => {
          if (res) {
            //console.log('get_outstanding_loans API res: ', res);

            return res;
          }
          return false;
        }));

    }
    else{
      return Observable.of({'ytd_amount':"0"});
    }
  }

}
