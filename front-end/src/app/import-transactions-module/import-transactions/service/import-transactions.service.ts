import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { map, concatMap, switchMap, retry, share } from 'rxjs/operators';
import { Observable, timer, interval } from 'rxjs';
import { environment } from 'src/environments/environment';
import { CookieService } from 'ngx-cookie-service';
import { UploadFileModel } from '../model/upload-file.model';
import { UploadTrxService } from '../import-trx-upload/service/upload-trx.service';

@Injectable({
  providedIn: 'root'
})
export class ImportTransactionsService {
  private readonly bucketName = 'fecfile-filing-frontend';
  private readonly TRANSACTIONS_PATH = 'transactions/';

  constructor(private _http: HttpClient, private _cookieService: CookieService) {}

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

  public checkForValidationErrors(uploadFile: UploadFileModel): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/validate_import_transactions';

    const fileName = uploadFile.fileName;

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    // let committeeId = null;
    // if (localStorage.getItem('committee_details') !== null) {
    //   const cmteDetails: any = JSON.parse(localStorage.getItem(`committee_details`));
    //   committeeId = cmteDetails.committeeid;
    // }

    const request: any = {};
    // request.cmte_id = committeeId;
    request.filename = fileName;
    request.key = this.TRANSACTIONS_PATH + uploadFile.fecFileName;
    request.bkt_name = this.bucketName;

    // if (fileName === 'no-mock.csv') {
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
    // }

    // let mockFile = '';
    // switch (fileName) {
    //   case 'validation_error.csv':
    //     mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/validation_error.json';
    //     break;
    //   case 'validation_error.1.csv':
    //     mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/validation_error.json';
    //     break;
    //   case 'validation_error.2.csv':
    //     mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/validation_error.json';
    //     break;
    //   case 'success.csv':
    //     mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/success.json';
    //     break;
    //   default:
    //     mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/success.json';
    // }

    // return this._http
    //   .get(mockFile, {
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
  }

  public checkDuplicateFile(uploadFile: UploadFileModel): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/chk_csv_uploaded_in_db';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let committeeId = null;
    if (localStorage.getItem('committee_details') !== null) {
      const cmteDetails: any = JSON.parse(localStorage.getItem(`committee_details`));
      committeeId = cmteDetails.committeeid;
    }

    // get_comittee_id(request.user.username)
    //     file_name = request.data.get("file_name") #request.file_name
    //     md5 = request.data.get("md5hash") #request.md5hash
    //     fec_file_name = request.data.get("fecfilename")

    const request: any = {};
    // request.get_comittee_id = committeeId;
    request.file_name = uploadFile.fileName;
    request.md5hash = uploadFile.checkSum;
    request.fecfilename = uploadFile.fecFileName;

    // if (uploadFile.fileName === 'no-mock.csv') {
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
    // }

    // let mockFile = '';
    // switch (uploadFile.fileName) {
    //   case 'success.csv':
    //     mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/success.json';
    //     break;
    //   case 'duplicate_file.csv':
    //     mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/duplicate_file.json';
    //     break;
    //   default:
    //     mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/success.json';
    // }
    // return this._http
    //   .get(mockFile, {
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
  }

  /**
   * Get duplicates for the file and page.
   */
  public getDuplicates(fileName: string, page: number): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/contact/transaction/duplicate';

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

    // const mockFile = 'assets/mock-data/import-contacts/duplicates.2.json';
    // return this._http
    //   .get(mockFile, {
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
  }

  /**
   * Save contacts in the file no dupes detected.
   */
  public saveProceedNoDupes(uploadFile: UploadFileModel, transactionIncluded: boolean): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/queue_transaction_message';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.key = this.TRANSACTIONS_PATH + uploadFile.fecFileName;
    request.bkt_name = this.bucketName;
    // request.transaction_included = transactionIncluded;

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
    // return Observable.of(true);
  }

  /**
   * Save contacts in the file and ignore dupes if any.
   */
  public saveContactIgnoreDupes(uploadFile: UploadFileModel, transactionIncluded: boolean): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/contact/transaction/ignore/merge';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.fileName = uploadFile.fecFileName;
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
  public mergeAll(uploadFile: UploadFileModel, transactionIncluded: boolean): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/contact/transaction/merge/save';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.fileName = uploadFile.fecFileName;
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

    // const token: string = JSON.parse(this._cookieService.get('user'));
    // let httpOptions = new HttpHeaders();
    // const url = '/contact/transaction/merge/save';

    // httpOptions = httpOptions.append('Content-Type', 'application/json');
    // httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    // const mergeOptionArray = [];
    // for (const contact of uploadFile.contacts) {
    //   let dupeEntityId = null;
    //   if (contact.user_selected_option !== 'add') {
    //     for (const dupe of contact.contacts_from_db) {
    //       if (dupe.user_selected_value) {
    //         dupeEntityId = dupe.entity_id;
    //       }
    //     }
    //   }

    //   const mergeOption: any = {};
    //   mergeOption.user_selected_option = contact.user_selected_option;
    //   mergeOption.file_record_id = contact.entity_id;
    //   mergeOption.db_entity_id = dupeEntityId;

    //   mergeOptionArray.push(mergeOption);
    // }
    // const request: any = {};
    // request.fileName = uploadFile.fecFileName;
    // request.merge_options = mergeOptionArray;

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
  }

  /**
   * Save user selected merge option.
   * @param fileName
   * @param contacts
   */
  public saveUserMergeSelection(fileName: string, contact: any) {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/contact/transaction/merge/options';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let dupeEntityId = null;
    if (contact.user_selected_option !== 'add') {
      for (const dupe of contact.contacts_from_db) {
        if (dupe.user_selected_value) {
          dupeEntityId = dupe.entity_id;
        }
      }
    }

    const mergeOption: any = {};
    mergeOption.user_selected_option = contact.user_selected_option;
    mergeOption.file_record_id = contact.entity_id;
    mergeOption.db_entity_id = dupeEntityId;

    const request: any = {};
    request.fileName = fileName;
    request.merge_option = mergeOption;

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
    // return Observable.of(true);
  }

  /**
   * Cancel a single file from import.
   */
  public cancelImport(fileName: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = 'import-trx-cancel-file???'; //'/contact/cancel/import';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.fileName = fileName;

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
    return Observable.of(true);
  }

  /**
   * Cancel a single file from import.
   */
  public cancelImportAll(fileNames: Array<string>): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = 'import-trx-cancel-all???'; //'/contact/cancel/import';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.fileNames = fileNames;

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
    return Observable.of(true);
  }

  public pollForProgress_bitcoin() {
    return this._http.get('https://blockchain.info/ticker');
  }

  public pollForProgress(): Observable<number> {
    // return Observable.of(10);
    const mockUrl = 'assets/mock-data/import-transactions/progress.json';
    return timer(0, 1000).pipe(
      switchMap(() =>
        this._http.get<any>(mockUrl).map(response => {
          return response;
        })
      )
    );
    // , retry(), share();
  }

  public formatFecFileName(uploadFile: UploadFileModel, committeeId: string) {
    return `${uploadFile.formType}_${uploadFile.scheduleType}_Import_Transactions_${committeeId}.csv`;
  }
}
