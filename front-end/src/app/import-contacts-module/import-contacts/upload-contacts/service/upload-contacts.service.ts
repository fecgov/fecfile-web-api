import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { environment } from 'src/environments/environment';

import * as S3 from 'aws-sdk/clients/s3';
import * as AWS from 'aws-sdk/global';
import { Observable, Subject, BehaviorSubject } from 'rxjs';
import { AWSError } from 'aws-sdk/global';
import { ManagedUpload, SelectObjectContentEventStream } from 'aws-sdk/clients/s3';
import { StreamingEventStream } from 'aws-sdk/lib/event-stream/event-stream';
import { ERROR_COMPONENT_TYPE } from '@angular/compiler';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';


/**
 * A service for uploading a file to AWS.
 */
@Injectable({
  providedIn: 'root'
})
export class UploadContactsService {

  private readonly CONTACTS_PATH = 'contacts/';

  /**
   * Constructor will obtain credentials for AWS S3 Bucket.
   * @param _http
   */
  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService) {

    AWS.config.region = environment.awsRegion;
    AWS.config.credentials = new AWS.CognitoIdentityCredentials({
      IdentityPoolId: environment.awsIdentityPoolId,
    });
    this.bucket = new S3({});
  }

  public progressPercent: number;
  public progressPercentSubject = new BehaviorSubject<number>(this.progressPercent);

  private bucket: S3;
  private readonly bucketName = 'fecfile-filing-frontend';

  /**
   * Upload the file to AWS S3 bucket.
   */
  public uploadFile(file: File, checkSum: string, committeeId: string): Observable<any> {

    // let committeeId = null;
    // if (localStorage.getItem('committee_details') !== null) {
    //   const cmteDetails: any = JSON.parse(localStorage.getItem(`committee_details`));
    //   committeeId = cmteDetails.committeeid;
    // }

    // Metadata: { 'committee-id': committeeId, 'check-sum': checkSum },
    this.progressPercent = 0;
    const params = {
      Bucket: this.bucketName,
      Key: this.CONTACTS_PATH + committeeId + '/' + file.name,
      Metadata: { 'committee-id': committeeId },
      Body: file,
      ACL: 'public-read',
      ContentType: file.type
    };

    // Bind the function to the 'this' for this component as it will
    // be called from a callback function where its 'this' is not the component this.
    const _setPercentage = this._setPercentage.bind(this);
    // const _uploadComplete = this.uploadComplete.bind(this);
    // const listObjects = this.listObjects.bind(this);
    // const getObject = this.getObject.bind(this);
    // const _readFileHeader = this._readFileHeader.bind(this);

    return Observable.create(observer => {
      this.bucket.upload(params).on('httpUploadProgress', function (evt: S3.ManagedUpload.Progress) {
        // console.log(evt.loaded + ' of ' + evt.total + ' Bytes');
        const progressPercent = Math.trunc((evt.loaded / evt.total) * 100);
        // console.log('progressPercent = ' + progressPercent);
        // this.progressPercentSubject.next(this.progressPercent);
        _setPercentage(progressPercent);
      }).send(function (err: AWSError, data: ManagedUpload.SendData) {
        if (err) {
          console.log('There was an error uploading your file: ', err);
          _setPercentage(0);
          // return false;
          // return Observable.of(false);
          observer.next(false);
          observer.complete();
          // throw (err);
          // return;
        } else {
          // console.log('Successfully uploaded file.', data);
          _setPercentage(100);
          // return Observable.of(_readFileHeader(file));
          // _readFileHeader(file);
          // return true;
          observer.next(data);
          observer.complete();

          // _uploadComplete(file.name).subscribe((res: any) => {
          //   console.log();
          // });

          // getObject(file);
          // listObjects();
        }
      });
    });
  }

  /**
   * Inform the backend the upload is complete.
   */
  public uploadComplete(fileName: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/contact/upload';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.fileName = fileName;

    // if (fileName === 'test_new.csv') {
    //   return this._http
    //     .get('assets/mock-data/import-contacts/upload_response2.json', {
    //       headers: httpOptions
    //     })
    //     .pipe(
    //       map(res => {
    //         if (res) {
    //           return res;
    //         }
    //         return false;
    //       })
    //     );
    // } else {
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
   * Read the CSV file header record uploaded to AWS.
   * 
   * @param file
   * @returns an Observable containing an array of the header fields names.
   */
  public readCsvFileHeader(file: File): Observable<any> {

    let headerFields = [];

    const params = {
      Bucket: this.bucketName,
      Key: file.name,
      ExpressionType: 'SQL',
      Expression: 'select * from s3object s limit 1',
      InputSerialization: {
        CSV: {
          FileHeaderInfo: 'NONE'
        }
      },
      OutputSerialization: {
        CSV: {
          FieldDelimiter: ',',
          RecordDelimiter: '\n'
        },
      }
    };

    return Observable.create(observer => {
      this.bucket.selectObjectContent(params, function (err, data) {
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

  /**
   * Read the JSON file uploaded to AWS and get property names.
   *
   * @param file
   * @returns an Observable containing an array of the header fields names.
   */
  public readJsonFilePropertyNames(file: File): Observable<any> {

    const headerFields = [];

    const params = {
      Bucket: this.bucketName,
      Key: file.name,
      ExpressionType: 'SQL',
      Expression: 'select s[0] from s3object s',
      InputSerialization: {
        JSON: {
          Type: 'LINES'
        }
      },
      OutputSerialization: {
        JSON: {
          RecordDelimiter: '\n'
        }
      }
    };

    return Observable.create(observer => {
      this.bucket.selectObjectContent(params, function (err, data) {
        if (err) {
          observer.next(ERROR_COMPONENT_TYPE);
          observer.complete();
          return;
        }
        const events: SelectObjectContentEventStream = data.Payload;
        if (Array.isArray(events)) {
          for (const event of events) {
            // Check the top-level field to determine which event this is.
            if (event.Records) {
              const jsonString = event.Records.Payload.toString();
              // console.log('JSON Obj:', jsonString);
              const json = JSON.parse(jsonString);
              Object.keys(json._1).forEach(key => {
                headerFields.push(key);
              });
            }
          }
        }
        observer.next(headerFields);
        observer.complete();
      });
    });
  }

  // public listObjects(): Observable<any> {
  public listObjects(committeeId: string) {

    const params = {
      Bucket: this.bucketName,
      // MaxKeys: 20,
      // Delimiter: this.CONTACTS_PATH + committeeId
      Prefix: this.CONTACTS_PATH + committeeId
    };

    return Observable.create(observer => {
      this.bucket.listObjectsV2(params, function (err, data) {
        // this.bucket.listObjectVersions(params, function (err, data) {

        if (err) {
          console.log(err, err.stack);
          // observer.complete();
        } else {
          console.log(data);
          observer.next(data);
          observer.complete();
        }
      });
    });
  }

  public getHeadObject(key: string) {

    const params = {
      Bucket: this.bucketName,
      Key: key,
      // ExpectedBucketOwner: 'fa57b28b4ce851da0b7769a3e23fca76b8dd4139846d60a4266c70a6849a5bfc'
    };

    return Observable.create(observer => {
      this.bucket.headObject(params, function (err, data) {
        if (err) {
          observer.next(data);
          observer.complete();
        } else {
          // console.log(data);
          observer.next(data);
          observer.complete();
        }
      });
    });
  }

  public checkUploadProcessing(): Observable<any> {
    let httpOptions = new HttpHeaders();
    httpOptions = httpOptions.append('Content-Type', 'application/json');
    const params = new HttpParams();

    return this._http
      .get('assets/mock-data/import-contacts/duplicates_even.json', {
        headers: httpOptions,
        params
      })
      .pipe(
        map(res => {
          if (res) {
            res = 25;
            return res;
          }
          return false;
        })
      );
  }

}
