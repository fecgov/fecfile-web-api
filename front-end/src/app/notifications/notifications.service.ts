import { Injectable, ChangeDetectionStrategy } from '@angular/core';
import { INotification } from './notification';
import { Observable } from 'rxjs/Observable';
import { map } from 'rxjs/operators';
import 'rxjs/add/operator/map';
import { environment } from '../../environments/environment';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { CookieService } from 'ngx-cookie-service';
import { analyzeAndValidateNgModules } from '@angular/compiler';
import { SortableColumnModel } from '../shared/services/TableService/sortable-column.model';

@Injectable({
  providedIn: 'root'
})
export class NotificationsService {
  private notificationData: INotification[];

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService
  ) { }

  getTotalCount(): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url: string = '/core/get_notifications_count';
    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http.get(`${environment.apiUrl}${url}`,
      {
        headers: httpOptions
      }
    );
  }

  getNotificationCounts(): Observable<{groupName: string, count: number}[]> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url: string = '/core/get_notifications_counts';
    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
    .get<{items: [{groupName: string, count: number}], totalItems: number}>(`${environment.apiUrl}${url}`,
      {
        headers: httpOptions
      }
    ).pipe(map(res => {
      return res.items;
    }));
  }
  
  getNotifications(
      view: string,
      sortColumn: SortableColumnModel,
      page: number,
      itemsPerPage: number
    ): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url: string = '/core/get_notifications';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.view = view;
    request.page = page;
    request.itemsPerPage = itemsPerPage;
    request.sortColumnName = sortColumn.colName;
    request.descending = sortColumn.descending;

    return this._http
      .post<{keys: {name: string, header: string}, items: [{}], totalItems: number}>(
        `${environment.apiUrl}${url}`,
        request,
        {
          headers: httpOptions
        }
      )
      .pipe(map(res => {
        if (res) {
          let records: Array<Map<string, string>> = [];
          for (let record of res.items) {
            let map = new Map<string, string>();
            for (var key in record) {
              map.set(key, record[key]);
            }
            records.push(map);
          }

          return {
            items: records,
            keys: res.keys,
            totalItems: res.totalItems
          };
        } else {
          return {
            items: null,
            keys: null,
            totalItems: 0
          };
        }
      })
      );
  }
}