import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class UploadContactsService {

  constructor(private _http: HttpClient) { }

  public uploadFile(file: File) {

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
