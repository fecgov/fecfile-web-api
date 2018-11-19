import {Injectable} from '@angular/core';
import {Http, Response} from '@angular/http';
import {HttpClient} from '@angular/common/http';
import {IReport} from './report';
import {Observable} from 'rxjs/Observable';
import 'rxjs/add/operator/map';
import {environment} from '../../environments/environment';
import { ConditionalExpr } from '@angular/compiler';

@Injectable()
export class ReportService{
    private reportData: IReport[];
        constructor(private _httpClient: HttpClient)
        {
            console.log("you are here getReports():IReport[]...");
            
           
        }

        getReports(): Observable<IReport[]> {

            let reporturl=`${environment.apiUrl}/f99/fetch_f99_info`;
            return this._httpClient.get(reporturl)
            .map(res => {
                return <IReport[]> res.valueOf();
            })
        }    
   }