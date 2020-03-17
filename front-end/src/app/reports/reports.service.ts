import {Injectable, ChangeDetectionStrategy } from '@angular/core';
import {Http, Response} from '@angular/http';
import {IReport} from './report';
import {Observable} from 'rxjs/Observable';
import 'rxjs/add/operator/map';
import {environment} from '../../environments/environment';
import { ConditionalExpr } from '@angular/compiler';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';

@Injectable()
export class ReportService{
    private reportData: IReport[];

    constructor(
        private _http: HttpClient,
        private _cookieService: CookieService
      ) { }
    
    getReports(): Observable<any>
    {
        let token: string = JSON.parse(this._cookieService.get('user'));
        let httpOptions =  new HttpHeaders();
        /*let params = new HttpParams();*/
        let url: string = '';
        
        url = '/f99/get_form99list';    
                

        httpOptions = httpOptions.append('Content-Type', 'application/json');
        httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

        //console.log(`${environment.apiUrl}${url}`);
        
        return this._http
        .get(
        `${environment.apiUrl}${url}`,
        {
          headers: httpOptions
        }
      );

       
   }
}