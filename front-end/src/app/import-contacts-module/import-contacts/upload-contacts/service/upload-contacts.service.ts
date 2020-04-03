import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';

import * as S3 from 'aws-sdk/clients/s3';


@Injectable({
  providedIn: 'root'
})
export class UploadContactsService {

  constructor(private _http: HttpClient) { }


  /**
   * Upload the file to AWS S3 bucket.
   */
  public uploadFile(file: File) {

    const ENV = environment;
    let bucket: S3;
    if (ENV.name === 'local') {
      bucket = new S3(
        {
          accessKeyId: ENV.ACCESS_KEY,
          secretAccessKey: ENV.SECRET_KEY,
          region: 'us-east-1'
        }
      );
    } else {
      bucket = new S3(
        {
          region: 'us-east-1'
        }
      );
    }

    const contentType = file.type;
    const params = {
      Bucket: 'fecfile-filing-frontend',
      Key: file.name,
      Body: file,
      ACL: 'public-read',
      ContentType: contentType
    };
    bucket.upload(params, function (err, data) {
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
