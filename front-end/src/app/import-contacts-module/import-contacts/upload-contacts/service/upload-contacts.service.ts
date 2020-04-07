import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';

import * as S3 from 'aws-sdk/clients/s3';
import * as AWS from 'aws-sdk/global';


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

      AWS.config.getCredentials(function (err) {
        if (err) {
          console.log(err.stack);
          // credentials not loaded
        } else {
          console.log('AK:', AWS.config.credentials.accessKeyId + 'ayuhahTFysyvsy');
          console.log('SK:', AWS.config.credentials.secretAccessKey + 'uhidijdijdoijd');

          bucket = new S3(
            {
              accessKeyId: AWS.config.credentials.accessKeyId,
              secretAccessKey: AWS.config.credentials.secretAccessKey,
              region: 'us-east-1'
            }
          );

          const contentType = file.type;
          const params = {
            Bucket: 'fecfile-filing-frontend',
            Key: file.name,
            Body: file,
            ACL: 'public-read',
            ContentType: contentType
          };
          bucket.upload(params, function (err2, data) {
            if (err2) {
              console.log('There was an error uploading your file: ', err2);
              return false;
            }
            console.log('Successfully uploaded file.', data);
            return true;
          });
        }
      });

      // bucket = new S3(
      //   {
      //     region: 'us-east-1'
      //   }
      // );
    }

    // const contentType = file.type;
    // const params = {
    //   Bucket: 'fecfile-filing-frontend',
    //   Key: file.name,
    //   Body: file,
    //   ACL: 'public-read',
    //   ContentType: contentType
    // };
    // bucket.upload(params, function (err, data) {
    //   if (err) {
    //     console.log('There was an error uploading your file: ', err);
    //     return false;
    //   }
    //   console.log('Successfully uploaded file.', data);
    //   return true;
    // });

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
