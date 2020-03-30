import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { environment } from 'src/environments/environment';

// require('aws-sdk/dist/aws-sdk');
// import * as AWS from 'aws-sdk/global';
import * as S3_CLIENT from 'aws-sdk/clients/s3';

// var AWS = require('aws-sdk');
// declare var AWS: any;


@Injectable({
  providedIn: 'root'
})
export class UploadContactsService {

  constructor(private _http: HttpClient) { }


  public uploadFileAWS_InsecureVeresion(file: File) {

    // export ACCESS_KEY='AKIAJDBAPRMS4PNKDREQ'
    // export SECRET_KEY='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'

    const contentType = file.type;
    const bucket = new S3_CLIENT(
      {
        accessKeyId: 'AKIAJDBAPRMS4PNKDREQ',
        secretAccessKey: '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',
        region: 'us-east-1'
      }
    );
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


  public uploadFile(file: File) {

    // const aws = AWS;

    const formData = new FormData();
    formData.append('file', file, file.name);
    const url = '/core/upload-contacts';

    return this._http
      .post(`${environment.apiUrl}${url}`, formData)
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
