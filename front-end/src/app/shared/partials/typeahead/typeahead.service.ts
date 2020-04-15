import { Injectable , ChangeDetectionStrategy } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class TypeaheadService {
  constructor(private _http: HttpClient, private _cookieService: CookieService) {}

  private readonly _childFieldNamePrefix = 'child*';

  /**
   * Get contacts starting with the search string by field name.
   * For example, search last_name startng with 'Jon' should return
   * contact with a Last Name of Jones, Jonston, Jonesby, etc.
   *
   * @param searchString the value keyed by the user to search with.
   * @param fieldName the field choosen by the user to search on.
   *  Possible fields are 'entity_name', 'first_name', 'last_name'.
   *
   */
  public getContacts(searchString: string, fieldName: string, expand?: boolean, global_search?: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url = '/core/autolookup_search_contacts';
    let httpOptions = new HttpHeaders();
    let params = new HttpParams();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    if (!searchString) {
      return;
    }

    if (
      fieldName === 'entity_name' ||
      fieldName === 'first_name' ||
      fieldName === 'last_name' ||
      fieldName === 'cmte_id' ||
      fieldName === 'payee_cmte_id' ||
      fieldName === 'cand_id' ||
      fieldName === 'cmte_name' ||
      fieldName === 'cand_first_name' ||
      fieldName === 'cand_last_name' ||
      fieldName === 'prefix' ||
      fieldName === 'suffix'
    ) {
      params = params.append(fieldName, searchString);
    } else if (
      fieldName === this._childFieldNamePrefix + 'cand_first_name' ||
      fieldName === this._childFieldNamePrefix + 'cand_last_name'
    ) {
      fieldName = fieldName.substring(6);
    } else {
      if (fieldName) {
        //console.log(`invalid field name for ${url} of ${fieldName}`);
      } else {
        //console.log(`invalid field name for ${url}`);
      }
      return Observable.of([]);
    }

    if(expand) {
      params = params.append('expand', 'true');
    }

    if(global_search) {
      params = params.append('global_search', global_search);
    }

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions,
      params
    });
  }

  public getContactsExpand(cmteId: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url = '/core/autolookup_expand';
    let httpOptions = new HttpHeaders();
    let params = new HttpParams();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    if (!cmteId) {
      return;
    }else {
      params = params.append('cmte_id', cmteId);
    }

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions,
      params
    });
  }
}
