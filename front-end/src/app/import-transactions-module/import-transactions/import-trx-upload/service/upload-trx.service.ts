import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from 'src/environments/environment';

import * as S3 from 'aws-sdk/clients/s3';
import * as AWS from 'aws-sdk/global';
import { Observable, BehaviorSubject } from 'rxjs';
import { AWSError } from 'aws-sdk/global';
import { ManagedUpload } from 'aws-sdk/clients/s3';
import { CookieService } from 'ngx-cookie-service';
import { map } from 'rxjs/operators';
import { SelectObjectContentEventStream } from 'aws-sdk/clients/s3';
import { StreamingEventStream } from 'aws-sdk/lib/event-stream/event-stream';
import { ERROR_COMPONENT_TYPE } from '@angular/compiler';
import { UploadFileModel } from '../../model/upload-file.model';

/**
 * A service for uploading a transaction files to AWS.
 * TODO Consider changing this to a common service with contacts.
 */
@Injectable({
  providedIn: 'root'
})
export class UploadTrxService {
  private readonly TRANSACTIONS_PATH = 'transactions/';

  /**
   * Constructor will obtain credentials for AWS S3 Bucket.
   * @param _http
   */
  constructor(private _http: HttpClient,
    private _cookieService: CookieService) {
    AWS.config.region = environment.awsRegion;
    AWS.config.credentials = new AWS.CognitoIdentityCredentials({
      IdentityPoolId: environment.awsIdentityPoolId
    });
    this.bucket = new S3({});
  }

  public progressPercent = 0;
  public progressPercentSubject = new BehaviorSubject<number>(this.progressPercent);

  private bucket: S3;
  private readonly bucketName = 'fecfile-filing-frontend';

  /**
   * Upload the file to AWS S3 bucket.
   */
  public uploadFile(uploadFile: UploadFileModel, committeeId: string): Observable<any> {
    this.progressPercent = 0;
    const params = {
      Bucket: this.bucketName,
      // Key: this.TRANSACTIONS_PATH + committeeId + '/' + uploadFile.fecFileName,
      // TODO API not ready for committee in path.  Remove temporarily.
      Key: this.TRANSACTIONS_PATH + uploadFile.fecFileName,
      Metadata: {
        'committee-id': committeeId,
        'check-sum': uploadFile.checkSum,
        'user-file-name': uploadFile.fileName
      },
      Body: uploadFile.file,
      ACL: 'public-read',
      ContentType: uploadFile.file.type
    };

    // Bind the function to the 'this' for this component as it will
    // be called from a callback function where its 'this' is not the component this.
    const _setPercentage = this._setPercentage.bind(this);

    return Observable.create(observer => {
      this.bucket
        .upload(params)
        .on('httpUploadProgress', function(evt: S3.ManagedUpload.Progress) {
          // console.log(evt.loaded + ' of ' + evt.total + ' Bytes');
          const progressPercent = Math.trunc((evt.loaded / evt.total) * 100);
          // console.log('progressPercent = ' + progressPercent);
          _setPercentage(progressPercent);
        })
        .send(function(err: AWSError, data: ManagedUpload.SendData) {
          if (err) {
            console.log('There was an error uploading your file: ', err);
            _setPercentage(0);
            observer.next(false);
            observer.complete();
          } else {
            // console.log('Successfully uploaded file.', data);
            _setPercentage(100);
            observer.next(data);
            observer.complete();
          }
        });
    });
  }

  /**
   * Inform client of progress of file upload.
   *
   * @param progressPercent
   */
  private _setPercentage(progressPercent: number) {
    this.progressPercentSubject.next(progressPercent);
  }

  /**
   * Provide an observable for client to subscribe for file upload progress updates.
   */
  public getProgressPercent(): Observable<any> {
    return this.progressPercentSubject.asObservable();
  }

  /**
   * Get objects from the S3 bucket in the transactions/committee folder.
   */
  public listObjects(committeeId: string) {
    const params = {
      Bucket: this.bucketName,
      // MaxKeys: 20,
      Prefix: this.TRANSACTIONS_PATH + committeeId
    };

    return Observable.create(observer => {
      this.bucket.listObjectsV2(params, function(err, data) {
        // this.bucket.listObjectVersions(params, function (err, data) {
        if (err) {
          console.log(err, err.stack);
        } else {
          console.log(data);
          observer.next(data);
          observer.complete();
        }
      });
    });
  }

  /**
   * Read a CSV file from S3 given a limited number of records.
   *
   * @param file
   * @returns an Observable containing an array of the header fields names.
   */
  public readCsvRecords(file: File, numberOfRecords: number, committeeId: string): Observable<any> {
    let records = [];

    const params = {
      Bucket: this.bucketName,
      // Key: file.name,
      Key: this.TRANSACTIONS_PATH + committeeId + '/' + file.name,
      ExpressionType: 'SQL',
      Expression: 'select * from s3object s limit ' + numberOfRecords,
      InputSerialization: {
        CSV: {
          FileHeaderInfo: 'USE'
        }
      },
      OutputSerialization: {
        // CSV: {
        //   FieldDelimiter: ',',
        //   RecordDelimiter: '\n'
        // }
        JSON: {
          RecordDelimiter: ','
        }
      }
    };

    return Observable.create(observer => {
      this.bucket.selectObjectContent(params, async function(err, data) {
        if (err) {
          observer.next(ERROR_COMPONENT_TYPE);
          observer.complete();
        }
        const events: SelectObjectContentEventStream = data.Payload;
        if (Array.isArray(events)) {
          for await (const event of events) {
            // Check the top-level field to determine which event this is.
            if (event.Records) {
              console.log('Records:', event.Records.Payload.toString());

              // const records = event.Records.Payload.decode('utf-8');
              // print(records)

              const payload = event.Records.Payload;

              // trim last char if it is a comma.
              const payLoadStr = payload.toString().replace(/\,$/, '');
              // if (payLoadStr) {
              //   const lastchar = payLoadStr.substring(payLoadStr.length - 2, payLoadStr.length - 1);
              //   if (lastchar === ',') {
              //     payLoadStr = payLoadStr.substring(0, payLoadStr.length - 2);
              //   }
              // }
              const jsonString = `[ ${payLoadStr} ]`;
              records = JSON.parse(jsonString);
              // records = headerRecord.split(',');
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
        observer.next(records);
        observer.complete();
      });
    });
  }

  /**
   * Invokes the api to import DCF file from S3 and validate and import. 
   */
  public importDcfFile(fileName: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/import/fecfile';

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
}
