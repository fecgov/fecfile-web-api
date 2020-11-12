import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';

import * as S3 from 'aws-sdk/clients/s3';
import * as AWS from 'aws-sdk/global';
import { Observable, BehaviorSubject } from 'rxjs';
import { AWSError } from 'aws-sdk/global';
import { ManagedUpload } from 'aws-sdk/clients/s3';
import { CookieService } from 'ngx-cookie-service';

/**
 * A service for uploading a transaction files to AWS.
 * TODO Consider changing this to a common service with contacts.
 */
@Injectable({
  providedIn: 'root'
})
export class UploadTrxService {
  private readonly CONTACTS_PATH = 'transactions/';

  /**
   * Constructor will obtain credentials for AWS S3 Bucket.
   * @param _http
   */
  constructor() {
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
  public uploadFile(file: File, committeeId: string): Observable<any> {
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
}
