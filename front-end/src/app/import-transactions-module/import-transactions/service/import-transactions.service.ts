import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ImportTransactionsService {

  constructor(private _http: HttpClient) { }


  public getSpecAndTemplate(fileName: string): Observable<any> {

    const url = '/contact/template';
    // add this once API is ready const url = '/transactions/template';
    let params = new HttpParams();
    params = params.append('fileName', fileName);

    return this._http.get(`${environment.apiUrl}${url}`, { responseType: 'blob' }).pipe(
      map((res: any) => {
        if (res) {
          return res;
        }
        return false;
      })
    );
  }
}
