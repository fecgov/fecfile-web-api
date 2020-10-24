import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { environment } from 'src/environments/environment';

import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { DuplicateContactModel } from '../../../model/duplicate-contact.model';
import { ImportContactModel } from '../../../model/import-contact.model';

@Injectable({
  providedIn: 'root'
})
export class DuplicateContactsService {

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService
  ) { }

  /**
   * Get duplicates for the file and page.
   */
  public getDuplicates(fileName: string, page: number): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/contact/duplicate';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.fileName = fileName;
    request.page = page;
    request.itemsPerPage = 4;

    return this._http
      .post(`${environment.apiUrl}${url}`, request, {
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
   * Save contacts in the file and ignore dupes if any.
   */
  public saveContactIgnoreDupes(fileName: string, transactionIncluded: boolean): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/contact/ignore/merge';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.fileName = fileName;
    request.transaction_included = transactionIncluded;

    return this._http
      .post(`${environment.apiUrl}${url}`, request, {
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
   * Merge the user selections on all contacts in the import.
   */
  public mergeAll(fileName: string, transactionIncluded: boolean): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/contact/merge/save';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.fileName = fileName;
    request.transaction_included = transactionIncluded;

    return this._http
      .post(`${environment.apiUrl}${url}`, request, {
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
   * Save user selected merge option.
   * @param fileName
   * @param contacts 
   */
  public saveUserMergeSelection(fileName: string, contacts: Array<any>) {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/contact/merge/options';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const contactsToMerge = [];
    for (const contact of contacts) {
      // val set to true for a new contact else use entity ID.
      const val = contact.user_selected_option !== 'add' ? contact.entity_id : 'true';
      contactsToMerge.push({
        entity_id: contact.entity_id,
        selected: contact.user_selected_option,
        val: val
      });
    }

    const request: any = {};
    request.fileName = fileName;
    request.merge_option = contactsToMerge;

    return this._http
      .post(`${environment.apiUrl}${url}`, request, {
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
   * Cancel the import.
   */
  public cancelImport(fileName: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/contact/cancel/import';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.fileName = fileName;

    return this._http
      .post(`${environment.apiUrl}${url}`, request, {
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

  public getDuplicates_mock(page: number): Observable<any> {
    let httpOptions = new HttpHeaders();
    httpOptions = httpOptions.append('Content-Type', 'application/json');
    const params = new HttpParams();

    // TODO even pages return diff data just for change detection development - remove it when api is ready
    if (page % 2 === 0) {
      // TODO Using mock server data until API is integrated
      return this._http
        .get('assets/mock-data/import-contacts/duplicates_even.json', {
          headers: httpOptions,
          params
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
      // TODO Using mock server data until API is integrated
      return this._http
        .get('assets/mock-data/import-contacts/duplicates.2.json', {
          headers: httpOptions,
          params
        })
        .pipe(
          map((res: any) => {
            if (res) {
              res.duplicates = this.mapAllDupesFromServerFields(res.duplicates);
              return res;
            }
            return false;
          })
        );
    }
  }


  /**
   * Map server fields from the response to the model.
   *
   * TODO The API should be changed to pass the property names expected by the front end.
   */
  public mapAllDupesFromServerFields(serverData: any): Array<DuplicateContactModel> {
    const modelArray: Array<DuplicateContactModel> = [];
    if (!serverData || !Array.isArray(serverData)) {
      return null;
    }
    for (const row of serverData) {
      const model = new DuplicateContactModel(this._mapDupeFromServerFields(row));
      if (row.potentialDupes) {
        const potentialDupes = new Array<DuplicateContactModel>();
        for (const dupe of row.potentialDupes) {
          const dupeModel = new DuplicateContactModel(this._mapDupeFromServerFields(dupe));
          dupeModel.seq = dupe.seq;
          potentialDupes.push(dupeModel);
        }
        model.potentialDupes = potentialDupes;
      }
      modelArray.push(model);
    }
    return modelArray;
  }

  private _mapDupeFromServerFields(row: any): ImportContactModel {
    if (!row) {
      return null;
    }
    const model = new ImportContactModel({});
    model.id = row.contact_id;
    model.committeeId = row.committee_id;
    model.type = row.entity_type;
    model.name = row.entity_name;
    model.lastName = row.last_name;
    model.firstName = row.first_name;
    model.middleName = row.middle_name;
    model.prefix = row.prefix;
    model.suffix = row.suffix;
    model.street = row.street1;
    model.street2 = row.street2;
    model.city = row.city;
    model.state = row.state;
    model.zip = row.zip;
    model.employer = row.employer;
    model.occupation = row.occupation;
    model.candidateId = row.candidate_id;
    model.officeSought = row.office_sought;
    model.officeState = row.office_state;
    model.district = row.district;
    model.multiCandidateCmteStatus = row.multi_candidate_cmte_status;

    return model;
  }

}
