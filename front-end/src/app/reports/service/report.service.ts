import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { CookieService } from 'ngx-cookie-service';
import { environment } from 'src/environments/environment';
import { TransactionModel } from '../model/report.model';
import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';
import { FilterPipe, FilterTypeEnum } from 'src/app/shared/pipes/filter/filter.pipe';
import { ReportFilterModel } from '../model/report-filter.model';
import { DatePipe } from '@angular/common';
import { ZipCodePipe } from 'src/app/shared/pipes/zip-code/zip-code.pipe';
import { ActiveView } from '../reportheader/reportheader.component';

/*export interface GetTransactionsResponse {
  transactions: TransactionModel[];
  totalAmount: number;
  totalTransactionCount: number;
}*/

@Injectable({
  providedIn: 'root'
})
export class ReportsService {

  // only for mock data
  // only for mock data
  // only for mock data

  /** The array of items to show in the recycle bin. TODO rename it */
  private mockRestoreTrxArray = [];
  /** The array of items trashed from the transaction table to be added to the recyle bin */
  private mockTrashedTrxArray: Array<TransactionModel> = [];
  /** The array of items restored from the recycle bin to be readded to the transactions table. TODO rename */
  private mockRecycleBinArray = [];
  private mockTransactionId = 'TID12345';
  private mockTransactionIdRecycle = 'TIDRECY';

  // only for mock data - end
  // only for mock data - end
  // only for mock data - end


  // May only be needed for mocking server
  private _orderByPipe: OrderByPipe;
  private _filterPipe: FilterPipe;
  private _zipCodePipe: ZipCodePipe;
  private _datePipe: DatePipe;

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
  ) {
    
    this._orderByPipe = new OrderByPipe();
    this._filterPipe = new FilterPipe();
    this._zipCodePipe = new ZipCodePipe();
    this._datePipe = new DatePipe('en-US');
  }


  public getFormTypes(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let url = '';
    let params = new HttpParams();

    url = '/core/get_FormTypes';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
       .get(
          `${environment.apiUrl}${url}`,
          {
            headers: httpOptions
          }
       );
  }

  public getReportTypes(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let url = '';
    let params = new HttpParams();

    url = '/core/get_ReportTypes';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
       .get(
          `${environment.apiUrl}${url}`,
          {
            headers: httpOptions
          }
       );
  }
  public getStatuss(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let url = '';
    let params = new HttpParams();

    url = '/core/get_Statuss';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
       .get(
          `${environment.apiUrl}${url}`,
          {
            headers: httpOptions
          }
       );
  }
  public getAmendmentIndicators(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let url = '';
    let params = new HttpParams();

    url = '/core/get_AmendmentIndicators';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
       .get(
          `${environment.apiUrl}${url}`,
          {
            headers: httpOptions
          }
       );
  }
}
