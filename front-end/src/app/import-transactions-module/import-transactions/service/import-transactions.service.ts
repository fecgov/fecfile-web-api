import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/environment';
import { CookieService } from 'ngx-cookie-service';

@Injectable({
  providedIn: 'root'
})
export class ImportTransactionsService {

  constructor(private _http: HttpClient, private _cookieService: CookieService) { }

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


  /**
   * Start processing the uploaded file of transactions.
   */
  public processingUploadedTransactions(fileName: string, checkSum: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/chk_csv_uploaded_in_db';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.fileName = fileName;
    request.checkSum = checkSum;

    // return this._http
    //   .post(`${environment.apiUrl}${url}`, request, {
    //     headers: httpOptions
    //   })
    //   .pipe(
    //     map(res => {
    //       if (res) {
    //         return res;
    //       }
    //       return false;
    //     })
    //   );
    let mockFile = '';
    switch (fileName) {
      case 'validation_error.csv':
        mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/validation_error.json';
        break;
      case 'duplicate_file.csv':
        mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/duplicate_file.json';
        break;
      case 'duplicate_file.csv':
        mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/duplicate_file.json';
        break;
      default:
        mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/success.json';
    }
    return this._http
      .get(mockFile, {
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
}
