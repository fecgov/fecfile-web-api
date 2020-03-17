import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { map } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class ImportContactsService {

  constructor(private _http: HttpClient) { }

  public getDuplicates() {
    let httpOptions = new HttpHeaders();
    httpOptions = httpOptions.append('Content-Type', 'application/json');
    const params = new HttpParams();
    // TODO Using mock server data until API is integrated
    return this._http
      .get('assets/mock-data/import-contacts/duplicates.json', {
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
  }
}
