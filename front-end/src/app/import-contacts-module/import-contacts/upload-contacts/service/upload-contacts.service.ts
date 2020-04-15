import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';

import * as S3 from 'aws-sdk/clients/s3';
import * as AWS from 'aws-sdk/global';


@Injectable({
  providedIn: 'root'
})
export class UploadContactsService {

  constructor(private _http: HttpClient) {

    // AWS.config.region = 'us-east-1';
    // AWS.config.credentials = new AWS.CognitoIdentityCredentials({
    //   IdentityPoolId: 'us-east-1:f0f414b2-8e9f-4488-9cc1-34a5918a1a1d',
    // });

    AWS.config.region = environment.awsRegion;
    AWS.config.credentials = new AWS.CognitoIdentityCredentials({
      IdentityPoolId: environment.awsIdentityPoolId,
    });
    this.bucket = new S3({});
  }

  private bucket: S3;

  /**
   * Upload the file to AWS S3 bucket.
   */
  public uploadFile(file: File) {

    // const bucket = new S3(
    //     {
    //       accessKeyId: ENV.ACCESS_KEY,
    //       secretAccessKey: ENV.SECRET_KEY,
    //       region: 'us-east-1'
    //     }
    // );

    const contentType = file.type;
    const params = {
      Bucket: 'fecfile-filing-frontend',
      Key: file.name,
      Body: file,
      ACL: 'public-read',
      ContentType: contentType
    };
    this.bucket.upload(params, function (err: any, data: any) {
      if (err) {
        console.log('There was an error uploading your file: ', err);
        return false;
      }
      console.log('Successfully uploaded file.', data);
      return true;
    });


    // TODO keep this until sure we don't need progress update realtime
    // for upload progress
    // bucket.upload(params).on('httpUploadProgress', function (evt) {
    //   console.log(evt.loaded + ' of ' + evt.total + ' Bytes');
    // }).send(function (err, data) {
    //   if (err) {
    //     console.log('There was an error uploading your file: ', err);
    //     return false;
    //   }
    //   console.log('Successfully uploaded file.', data);
    //   return true;
    // });
  }
}
