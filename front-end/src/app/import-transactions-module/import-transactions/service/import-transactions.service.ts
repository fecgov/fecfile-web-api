import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { map, concatMap, switchMap, retry, share } from 'rxjs/operators';
import { Observable, timer, interval } from 'rxjs';
import { environment } from 'src/environments/environment';
import { CookieService } from 'ngx-cookie-service';
import * as S3 from 'aws-sdk/clients/s3';
import * as AWS from 'aws-sdk/global';
import { AWSError } from 'aws-sdk/global';
import { SelectObjectContentEventStream } from 'aws-sdk/clients/s3';
import { StreamingEventStream } from 'aws-sdk/lib/event-stream/event-stream';
import { ERROR_COMPONENT_TYPE } from '@angular/compiler';

@Injectable({
  providedIn: 'root'
})
export class ImportTransactionsService {
  private bucket: S3;
  private readonly bucketName = 'fecfile-filing-frontend';

  constructor(private _http: HttpClient, private _cookieService: CookieService) {
    AWS.config.region = environment.awsRegion;
    AWS.config.credentials = new AWS.CognitoIdentityCredentials({
      IdentityPoolId: environment.awsIdentityPoolId
    });
    this.bucket = new S3({});
  }

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
  public processingUploadedTransactions(fileName: string, checkSum: string, formType: string): Observable<any> {
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

    const request: any = {};
    request.cmte_id = committeeId;
    request.filename = fileName;
    request.hash_value = checkSum;
    // TODO how will fornt end know schedule.  This should be determined by backend.
    request.fecfilename = `${formType}_ScheduleA_Import_Transactions_${committeeId}.csv`;

    if (fileName === 'no-mock.csv') {
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

    let mockFile = '';
    switch (fileName) {
      case 'validation_error.csv':
        mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/validation_error.json';
        break;
      case 'validation_error_2.csv':
        mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/validation_error.json';
        break;
      case 'success.csv':
        mockFile = 'assets/mock-data/import-transactions/chk_csv_uploaded_in_db/success.json';
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

    const mockFile = 'assets/mock-data/import-contacts/duplicates.2.json';
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

  /**
   * Save contacts in the file and ignore dupes if any.
   */
  public saveContactIgnoreDupes(fileName: string, transactionIncluded: boolean): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = 'import-trx-ignoredupes???'; // '/contact/ignore/merge';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.fileName = fileName;
    request.transaction_included = transactionIncluded;

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
   * Merge the user selections on all contacts in the import.
   */
  public mergeAll(fileName: string, transactionIncluded: boolean): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = 'import-trx-merge???'; // '/contact/merge/save';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.fileName = fileName;
    request.transaction_included = transactionIncluded;

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
   * Save user selected merge option.
   * @param fileName
   * @param contacts
   */
  public saveUserMergeSelection(fileName: string, contact: any) {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = 'import-trx-save-user-select???'; // '/contact/merge/options';

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

  /**
   * Read a CSV file from S3 given a limited number of records.
   *
   * @param file
   * @returns an Observable containing an array of the header fields names.
   */
  public readCsvRecords(file: File, numberOfRecords: number): Observable<any> {
    let headerFields = [];

    const params = {
      Bucket: this.bucketName,
      Key: file.name,
      ExpressionType: 'SQL',
      Expression: 'select * from s3object s limit ' + numberOfRecords,
      InputSerialization: {
        CSV: {
          FileHeaderInfo: 'NONE'
        }
      },
      OutputSerialization: {
        CSV: {
          FieldDelimiter: ',',
          RecordDelimiter: '\n'
        }
      }
    };

    return Observable.create(observer => {
      this.bucket.selectObjectContent(params, function(err, data) {
        if (err) {
          observer.next(ERROR_COMPONENT_TYPE);
          observer.complete();
        }
        const events: SelectObjectContentEventStream = data.Payload;
        if (Array.isArray(events)) {
          for (const event of events) {
            // Check the top-level field to determine which event this is.
            if (event.Records) {
              // console.log('Records:', event.Records.Payload.toString());
              const headerRecord = event.Records.Payload.toString();
              headerFields = headerRecord.split(',');
              // handle Records event
            } else if (event.Stats) {
              // handle Stats event
              // console.log(`Stats Processed ${event.Stats.Details.BytesProcessed} bytes`);
            } else if (event.Progress) {
              // handle Progress event
              // console.log('Progress:');
            } else if (event.Cont) {
              // handle Cont event
              // console.log('Cont:');
            } else if (event.End) {
              // handle End event
              // console.log('End:');
            }
          }
        }
        observer.next(headerFields);
        observer.complete();
      });
    });
  }
}
