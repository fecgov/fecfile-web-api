import { DatePipe } from '@angular/common';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { CookieService } from 'ngx-cookie-service';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { map } from 'rxjs/operators';
import { FilterPipe } from 'src/app/shared/pipes/filter/filter.pipe';
import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';
import { ZipCodePipe } from 'src/app/shared/pipes/zip-code/zip-code.pipe';
import { environment } from 'src/environments/environment';
import { ReportFilterModel } from '../model/report-filter.model';
//import { ReportModel } from '../model/report.model';
import { reportModel } from '../model/report.model';

export interface GetReportsResponse {
  reports: reportModel[];
  totalreportsCount: number;
}
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
  //private mockTrashedTrxArray: Array<ReportModel> = [];
  /** The array of items restored from the recycle bin to be readded to the reports table. TODO rename */
  private mockRecycleBinArray = [];
  private mockReportId = 'TID12345';
  private mockReportIdRecycle = 'TIDRECY';

  // only for mock data - end
  // only for mock data - end
  // only for mock data - end

  // May only be needed for mocking server
  private _orderByPipe: OrderByPipe;
  private _filterPipe: FilterPipe;
  private _zipCodePipe: ZipCodePipe;
  private _datePipe: DatePipe;

  constructor(private _http: HttpClient, private _cookieService: CookieService) {
    this._orderByPipe = new OrderByPipe();
    this._filterPipe = new FilterPipe();
    this._zipCodePipe = new ZipCodePipe();
    this._datePipe = new DatePipe('en-US');
  }

  public getFormTypes(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url = '';
    let params = new HttpParams();

    url = '/core/get_FormTypes';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions
    });
  }

  public getReportTypes(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url = '';
    let params = new HttpParams();

    url = '/core/get_ReportTypes';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions
    });
  }
  public getStatuss(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url = '';
    let params = new HttpParams();

    url = '/core/get_Statuss';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions
    });
  }

  public getAllF24Reports() : Observable<any>{
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url = '';

    url = '/core/get_f24_reports';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions
    });
  }

  public getAmendmentIndicators(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url = '';
    let params = new HttpParams();

    url = '/core/get_AmendmentIndicators';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions
    });
  }

  public getParentReports(
    view: string,
    page: number,
    itemsPerPage: number,
    sortColumnName: string,
    descending: boolean,
    filter: ReportFilterModel,
    reportId: number
  ): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let params = new HttpParams();

    const url = '/f99/get_form99list';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('view', view);
    params = params.append('reportId', reportId.toString());

    return this._http.get<GetReportsResponse>(`${environment.apiUrl}${url}`, {
      headers: httpOptions,
      params
    })
    .pipe(map(res => {
      if (res) {
        this.mockApplyFilters(res, filter);
        const reportsModelL = this.mapFromServerFields(res.reports);
        let reports: reportModel[] = this.sortReports(
          reportsModelL,
          sortColumnName,
          descending
        );
        this.setAmendmentIndicator(reports);
        this.setAmendmentShow(reports);
        reports = reports.filter(report => {
          if (!report.superceded_report_id) {
            return true;
          }
          return false;
        })
        const totalItems = reports.length;
        const items = reports.slice((page - 1) * itemsPerPage, page * itemsPerPage);

        return {
          items: items,
          totalItems: totalItems
        };
      } else {
        return {
          items: null,
          totalItems: 0
        };
      }
    })
    );
  }

  public getChildReports(
    view: string,
    page: number,
    itemsPerPage: number,
    sortColumnName: string,
    descending: boolean,
    filter: ReportFilterModel,
    reportId: number,
    parentReportId: string
  ): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let params = new HttpParams();

    const url = '/f99/get_previous_amend_reports';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('view', view);
    params = params.append('reportId', reportId.toString());
    params = params.append('parentId', parentReportId.toString());

    return this._http.get<GetReportsResponse>(`${environment.apiUrl}${url}`, {
      headers: httpOptions,
      params
    })
    .pipe(map(res => {
      if (res) {
        this.mockApplyFilters(res, filter);
        const reportsModelL = this.mapFromServerFields(res.reports);
        let reports: reportModel[] = this.sortReports(
          reportsModelL,
          sortColumnName,
          descending
        );
        this.setAmendmentIndicator(reports);
        this.setAmendmentShow(reports);

        return {
          items: reports,
          totalItems: reports.length
        };
      } else {
        return {
          items: null,
          totalItems: 0
        };
      }
    })
    );
  }

  public getReports(
    view: string,
    page: number,
    itemsPerPage: number,
    sortColumnName: string,
    descending: boolean,
    filter: ReportFilterModel,
    reportId: number
  ): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let params = new HttpParams();

    const url = '/f99/get_form99list';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('view', view);
    params = params.append('reportId', reportId.toString());

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions,
      params
    });
  }
  
  public getTrashedReports(
    view: string,
    page: number,
    itemsPerPage: number,
    sortColumnName: string,
    descending: boolean,
    filter: ReportFilterModel,
    reportId: number
  ): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let params = new HttpParams();

    const url = '/core/get_all_trashed_reports';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('view', view);
    params = params.append('reportId', reportId.toString());

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions,
      params
    });
  }

  /**
   * Map server fields from the response to the model.
   */
  public mapFromServerFields(serverData: any) {
    if (!serverData || !Array.isArray(serverData)) {
      return;
    }

    const modelArray: any = [];

    for (const row of serverData) {
      const model = new reportModel({});
      model.form_type = row.form_type;
      model.status = row.status;
      model.report_id = row.report_id;
      model.fec_id = row.fec_id;
      model.amend_ind = row.amend_ind;
      model.cvg_start_date = row.cvg_start_date;
      model.cvg_end_date = row.cvg_end_date;
      model.last_update_date = row.last_update_date;
      model.report_type_desc = row.report_type_desc;
      model.filed_date = row.filed_date;
      model.deleteddate = row.deleteddate;
      model.delete_ind = row.delete_ind;
      model.amend_number = row.amend_number;
      model.previous_report_id = row.previous_report_id;
      model.superceded_report_id = row.superceded_report_id;
      model.amend_show = true;
      model.amend_max = row.amend_max;
      model.memo_text = row.memo_text;
      model.child_records_count = row.child_records_count;
      modelArray.push(model);
    }

    return modelArray;
  }

  /**
   *
   * @param array
   * @param sortColumnName
   * @param descending
   */
  public sortReports(array: any, sortColumnName: string, descending: boolean) {
    const direction = descending ? -1 : 1;
    this._orderByPipe.transform(array, { property: sortColumnName, direction: direction });
    return array;
  }

  public setAmendmentIndicator(reports: reportModel[]) {
    if(reports) {
      for(const report of reports) {        
        if(report.form_type !== 'F99') {
          if(report.amend_ind === 'N' && reports.find(function(obj) { return obj.previous_report_id === report.report_id})) {
          //&& this.reportsModel.filter(rp => rp.previous_report_id == report.report_id)) {
            report.amend_ind = 'Original';           
          }else if(report.amend_ind === 'A') {        
            report.amend_ind = report.amend_ind.concat(report.amend_number.toString());            
          }
        }        
      }
    }
  }

  public setAmendmentShow(reports: reportModel[]) {

    let reportId = 0;
    let next: reportModel;
    let max: reportModel;
    
    if(reports) {
      for(const report of reports) {
        report.amend_max = (report.child_records_count > 0 ? 'down' : '');

        if(report.amend_ind === 'Original') {
          report.amend_show = false;
          
          next = reports.find(function(obj) { return obj.previous_report_id === report.report_id});
          next.amend_show = false;

          while(next) {
            next.amend_show = false;
            max = next;
            next = reports.find(function(obj) { return obj.previous_report_id === next.report_id});
          }
 
          max.amend_show = true;
          max.amend_max = 'down'; //'up';
        }
      }
    }  }

  /**
   * Some data from the server is formatted for display in the UI.  Users will search
   * on the reformatted data.  For the search filter to work against the formatted data,
   * the server array must also contain the formatted data.  They will be added her.
   *
   * @param response the server data
   */
  public mockAddUIFileds(response: any) {
    for (const rep of response.reports) {
      rep.transaction_date_ui = this._datePipe.transform(rep.transaction_date, 'MM/dd/yyyy');
      rep.deleted_date_ui = this._datePipe.transform(rep.deleted_date, 'MM/dd/yyyy');
    }
  }

  /**
   * This method handles filtering the reports array and will be replaced
   * by a backend API.
   */
  public mockApplyFilters(response: any, filters: ReportFilterModel) {
    if (!response) {
      return;
    }

    if (!filters) {
      return;
    }

    let isFilter = false;

    if (filters.filterForms) {
      if (filters.filterForms.length > 0) {
        isFilter = true;
        const fields = ['form_type'];
        let filteredformArray = [];
        for (const form of filters.filterForms) {
          const filtered = this._filterPipe.transform(response.reports, fields, form);
          filteredformArray = filteredformArray.concat(filtered);
        }
        response.reports = filteredformArray;
      }
    }

    if (filters.filterReports) {
      if (filters.filterReports.length > 0) {
        isFilter = true;
        const fields = ['report_type'];
        let filteredreportArray = [];
        for (const report of filters.filterReports) {
          const filtered = this._filterPipe.transform(response.reports, fields, report);
          filteredreportArray = filteredreportArray.concat(filtered);
        }
        response.reports = filteredreportArray;
      }
    }

    if (filters.filterStatuss) {
      if (filters.filterStatuss.length > 0) {
        isFilter = true;
        const fields = ['status'];
        let filteredStatusArray = [];
        for (const status of filters.filterStatuss) {
          const filtered = this._filterPipe.transform(response.reports, fields, status);
          filteredStatusArray = filteredStatusArray.concat(filtered);
        }
        response.reports = filteredStatusArray;
      }
    }

    if (filters.filterAmendmentIndicators) {
      if (filters.filterAmendmentIndicators.length > 0) {
        isFilter = true;
        const fields = ['amend_ind'];
        let filteredAmendmentArray = [];
        for (const AmendmentIndicator of filters.filterAmendmentIndicators) {
          const filtered = this._filterPipe.transform(response.reports, fields, AmendmentIndicator);
          filteredAmendmentArray = filteredAmendmentArray.concat(filtered);
        }
        response.reports = filteredAmendmentArray;
      }
    }

    if (filters.filterCvgDateFrom && filters.filterCvgDateTo) {
      const cvgFromDate = new Date(filters.filterCvgDateFrom);
      const cvgToDate = new Date(filters.filterCvgDateTo);
      const filteredCvgDateArray = [];
      for (const rep of response.reports) {
        if (rep.cvg_start_date) {
          const repDate = new Date(rep.cvg_start_date);
          if (repDate >= cvgFromDate && repDate <= cvgToDate) {
            isFilter = true;
          } else {
            isFilter = false;
          }
        }

        if (isFilter) {
          if (rep.cvg_end_date) {
            const repDate = new Date(rep.cvg_end_date);
            if (repDate >= cvgFromDate && repDate <= cvgToDate) {
              isFilter = true;
            } else {
              isFilter = false;
            }
          }
        }

        if (isFilter) {
          filteredCvgDateArray.push(rep);
        }
      }
      response.reports = filteredCvgDateArray;
    }

    if (filters.filterFiledDateFrom && filters.filterFiledDateTo) {
      const filedFromDate = this._datePipe.transform(filters.filterFiledDateFrom, 'Mddyyyy');
      const filedToDate = this._datePipe.transform(filters.filterFiledDateTo, 'Mddyyyy');
      const filteredFiledDateArray = [];
      for (const rep of response.reports) {
        if (rep.status === 'Filed') {
          if (rep.filed_date) {
            //this fix is done till services send data in EST format
            let d = this.convertUtcToLocalDate(rep.filed_date);
            let repDate = this._datePipe.transform(d, 'Mddyyyy');
            if (repDate >= filedFromDate && repDate <= filedToDate) {
              isFilter = true;
            } else {
              isFilter = false;
            }
          }
        } else if (rep.status === 'Saved') {
          if (rep.last_update_date) {
            //const repDate =  this.getDateMMDDYYYYformat(new Date(rep.last_update_date));
            //this fix is done till services send data in EST format
            let d = this.convertUtcToLocalDate(rep.last_update_date);
            let repDate = this._datePipe.transform(d, 'Mddyyyy');
            if (repDate >= filedFromDate && repDate <= filedToDate) {
              isFilter = true;
            } else {
              isFilter = false;
            }
          }
        }

        if (isFilter) {
          filteredFiledDateArray.push(rep);
        }
      }

      response.reports = filteredFiledDateArray;
    }

    if (filters.filterDeletedDateFrom && filters.filterDeletedDateTo) {
      const deletedFromDate = new Date(filters.filterDeletedDateFrom);
      const deletedToDate = new Date(filters.filterDeletedDateTo);
      const filteredDeletedDateArray = [];

      for (const rep of response.reports) {
        if (rep.deleteddate) {
          let d = new Date(rep.deleteddate);
          d.setUTCHours(0, 0, 0, 0);
          //const repDate = this.getDateMMDDYYYYformat(d);
          const repDate = d;

          if (repDate >= deletedFromDate && repDate <= deletedToDate) {
            isFilter = true;
          } else {
            isFilter = false;
          }
        }

        if (isFilter) {
          filteredDeletedDateArray.push(rep);
        }
      }
      response.reports = filteredDeletedDateArray;
    }
  }
  convertUtcToLocalDate(val: Date): Date {
    var d = new Date(val); // val is in UTC
    var usaTime = new Date().toLocaleString('en-US', { timeZone: 'America/New_York' });
    var dateNy = new Date(usaTime);

    var newOffset = dateNy.getTimezoneOffset();
    var localOffset = (d.getTimezoneOffset() - newOffset) * 60000;
    var localTime = d.getTime() - localOffset;

    d.setTime(localTime);
    return d;
  }

  private getDateMMDDYYYYformat(dateValue: Date): string {
    var year = dateValue.getUTCFullYear() + '';
    var month = dateValue.getUTCMonth() + 1 + '';
    var day = dateValue.getUTCDate() + '';
    return month + day + year;
  }

  public getReportInfo(form_type: string, report_id: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let params = new HttpParams();
    let url: string = '';
    
    params = params.append('reportid', report_id);

    if (form_type === 'F99' || form_type === '99') {
      url = '/f99/get_f99_report_info';
    } else if (form_type === 'F3X' || form_type === '3X' || form_type === 'F24' || form_type === '24' || form_type === '3L' || form_type === 'F3L') {
      url = '/core/get_report_info';
    } else if(form_type === 'F1M'){
      url = '/f1M/form1M'
      params = params.delete('reportid');
      params=params.append('reportId', report_id);
    }


    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    //params = params.append('committeeid', committee_id);

    if (form_type === 'F99' || form_type === '99') {
      return this._http.get(`${environment.apiUrl}${url}`, {
        headers: httpOptions,
        params
      });
    } else {
      return this._http
        .get(`${environment.apiUrl}${url}`, {
          headers: httpOptions,
          params
        })
        .map((res: any[]) => {
          // report_type in local storage is set in the report-type component.
          // The field names and format must be in sync when report_type object is set in local
          // storage by the report-detail. Any transformations should be done here.
          if (res) {
            if (Array.isArray(res)) {
              const resp = res[0];
              if (resp.hasOwnProperty('cvgstartdate')) {
                resp.cvgStartDate = this._datePipe.transform(resp.cvgstartdate, 'MM/dd/yyyy');
                delete resp.cvgstartdate;
              }
              if (resp.hasOwnProperty('cvgenddate')) {
                resp.cvgEndDate = this._datePipe.transform(resp.cvgenddate, 'MM/dd/yyyy');
                delete resp.cvgenddate;
              }
            }
          }
          return res;
        });
    }
  }
  public trashOrRestoreReports(action: string, reports: Array<reportModel>) {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/trash_restore_report';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    const actions = [];
    for (const rpt of reports) {
      actions.push({
        action: action,
        id: rpt.report_id
      });
    }
    request.actions = actions;

    return this._http
      .put(`${environment.apiUrl}${url}`, request, {
        headers: httpOptions
      })
      .map(res => {
        if (res) {
          //console.log('Report Trash Restore response: ', res);
          return res;
        }
        return false;
      });
  }
  public deleteRecycleBinReport(reports: Array<reportModel>): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/delete_trashed_reports';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    const actions = [];
    for (const rep of reports) {
      actions.push({
        id: rep.report_id
      });
    }
    request.actions = actions;

    return this._http
      .post(`${environment.apiUrl}${url}`, request, {
        headers: httpOptions
      })
      .map(res => {
        return false;
      });
  }

  public amendReport(report: reportModel): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/create_amended_reports';
    
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const formData: FormData = new FormData();
    formData.append('report_id', report.report_id);

    return this._http
      .post(`${environment.apiUrl}${url}`, formData, {
        headers: httpOptions
      })
      .pipe(
        map(res => {
          if (res) {
            //console.log('amend res: ', res);
            return res;
          }
          return false;
        })
      );
  }

  public updateReportDate(report: reportModel) {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/new_report_update_date';

    // httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const formData: FormData = new FormData();
    formData.append('report_id', report.report_id);

    return this._http
      .put(`${environment.apiUrl}${url}`, formData, {
        headers: httpOptions
      })
      .map(res => {
        if (res) {
          // //console.log('Ypdate Report Date response: ', res);
          return res;
        }
        return false;
      });
  }

  public getCoverageDates(reportId: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url: string = '/core/get_coverage_dates';
    let params = new HttpParams();

    params = params.append('report_id', reportId);

    return this._http
      .get(
        `${environment.apiUrl}${url}`,
        {
          params,
          headers: httpOptions
        }
      );
  }

  public updateMemo(data: any): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();

    const url = '/core/reports_memo_text';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
        .put(`${environment.apiUrl}${url}`, data, {
          headers: httpOptions
        })
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
