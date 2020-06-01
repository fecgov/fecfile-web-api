import { Injectable , ChangeDetectionStrategy } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../environments/environment';
import { map } from 'rxjs/operators';
import { SchedH6Model } from './sched-h6.model';

@Injectable({
  providedIn: 'root'
})
export class SchedH6Service {

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
  ) { }

  public getSummary(
      reportId: string,
      page: number,
      itemsPerPage: number,
      sortColumnName: string,
      descending: boolean
    ): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    const url = '/sh6/schedH6';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let params = new HttpParams();
    params = params.append('report_id', reportId);
    params = params.append('report_id', reportId);
    params = params.append('page', page.toString());
    params = params.append('itemsPerPage', itemsPerPage.toString());
    params = params.append('sortColumnName', sortColumnName);
    params = params.append('descending', `${descending}`);
    
    return this._http
      .get<{items: any[], totalItems: number}>(
        `${environment.apiUrl}${url}`,      
        {
          params,
          headers: httpOptions
        }
      )
      .pipe(map(res => {
        if (res) {
          return {
            items: this.mapFromServerFields(res.items),
            totalItems: res.totalItems
          };
        } else {
          return {
            items: null,
            totalItems: 0
          };
        }
      })
      );
  }

  public mapFromServerFields(serverData: any) {
    if (!serverData || !Array.isArray(serverData)) {
      return;
    }

    const modelArray: any = [];

    for (const row of serverData) {
      const model = new SchedH6Model({});

      model.cmte_id = row.cmte_id;
      model.report_id = row.report_id;
      model.transaction_type_identifier = row.transaction_type_identifier;
      model.transaction_id = row.transaction_id;
      model.back_ref_transaction_id = row.back_ref_transaction_id;
      model.activity_event_identifier = row.activity_event_identifier;
      model.activity_event_type = row.activity_event_type;
      model.expenditure_date = row.expenditure_date;
      model.expenditure_purpose = row.expenditure_purpose;
      model.fed_share_amount = row.fed_share_amount;
      model.non_fed_share_amount = row.non_fed_share_amount;
      model.levin_share = row.levin_share;
      model.memo_code = row.memo_code;
      model.first_name = row.first_name;
      model.last_name = row.last_name;
      model.entity_name = row.entity_name;
      model.entity_type = row.entity_type;
      model.aggregation_ind = row.aggregation_ind;

      modelArray.push(model);

    }

    return modelArray;
  }
   
}