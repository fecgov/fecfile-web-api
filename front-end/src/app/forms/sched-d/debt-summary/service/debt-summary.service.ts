import { Injectable , ChangeDetectionStrategy } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { CookieService } from 'ngx-cookie-service';
import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from 'src/environments/environment';
import { ReportTypeService } from 'src/app/forms/form-3x/report-type/report-type.service';
import { DatePipe } from '@angular/common';
import { DebtSummaryModel } from '../model/debt-summary.model';

export interface GetDebtsResponse {
  items: DebtSummaryModel[];
  totalCount: number;
  totalPages: number;
}

/**
 * The service for Debt Summary
 */
@Injectable({
  providedIn: 'root'
})
export class DebtSummaryService {
  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
    private _datePipe: DatePipe,
    private _orderByPipe: OrderByPipe,
    private _reportTypeService: ReportTypeService
  ) {}

  /**
   * Get the Debts comprising the Debt Summary.
   */
  public getDebts(
      transactionType: string,
      page: number,
      itemsPerPage: number,
      sortColumnName: string,
      descending: boolean
    ): Observable<{items: any[], totalItems: number}> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/sd/schedD';
    const reportId: string = this._reportTypeService.getReportIdFromStorage('3X').toString();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let params = new HttpParams();
    params = params.append('report_id', reportId);
    params = params.append('page', page.toString());
    params = params.append('itemsPerPage', itemsPerPage.toString());
    params = params.append('sortColumnName', sortColumnName);
    params = params.append('descending', `${descending}`);

    // Getting the summary debts requires the transactionType for the transaction not the summary.
    if (transactionType) {
      if (transactionType === 'DEBT_OWN_BY_SUMMARY') {
        transactionType = 'DEBT_BY_VENDOR';
      } else if (transactionType === 'DEBT_OWN_TO_SUMMARY') {
        transactionType = 'DEBT_TO_VENDOR';
      }
      params = params.append('transaction_type_identifier', transactionType);
    }

    return this._http
      .get<{items: any[], totalItems: number}>(`${environment.apiUrl}${url}`, {
        headers: httpOptions,
        params
      })
      .pipe(
        map(res => {
          if (res) {
            return {
              items: this.mapFromServerFields(res.items),
              totalItems: res.totalItems
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

  public deleteDebt(debt: DebtSummaryModel): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/trash_restore_transactions';
    const reportId: string = this._reportTypeService.getReportIdFromStorage('3X').toString();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let params = new HttpParams();
    const request: any = {};
    const actions = [];
    actions.push({
      action: 'trash',
      report_id: debt.reportId && debt.reportId !== 'undefined' ? debt.reportId : reportId,
      transaction_id: debt.transactionId
    });
    request.actions = actions;

    return this._http
      .put(`${environment.apiUrl}${url}`, request, {
        headers: httpOptions
      })
      .pipe(
        map(res => {
          if (res) {
            //console.log('get_outstanding_loans API res: ', res);

            return res;
          }
          return false;
        })
      );
  }

  /**
   * Sort Debt summary items.
   *
   * @param array
   * @param sortColumnName
   * @param descending
   */
  public sortDebtSummary(array: any, sortColumnName: string, descending: boolean) {
    const direction = descending ? -1 : 1;
    this._orderByPipe.transform(array, { property: sortColumnName, direction: direction });
    return array;
  }

  /**
   * Map server fields from the response to the model.
   *
   * TODO The API should be changed to pass the property names expected by the front end.
   */
  public mapFromServerFields(serverData: any): DebtSummaryModel[] {
    if (!serverData || !Array.isArray(serverData)) {
      return;
    }
    const modelArray = [];
    for (const row of serverData) {
      const model = new DebtSummaryModel({});
      model.selected = false;
      model.toggleChild = false;
      model.apiCall = row.api_call;
      model.reportId = row.report_id;
      model.transactionTypeIdentifier = row.transaction_type_identifier;
      model.transactionTypeDescription = row.transaction_type_description;
      model.scheduleType = row.schedule_type;
      model.transactionId = row.transaction_id;
      model.backRefTransactionId = row.back_ref_transaction_id;
      model.child = this._mapChildFromServerFields(row.child);
      model.entityType = row.entity_type;
      model.entityId = row.entity_id;
      this._setDebtName(row);
      model.name = row.name;
      model.beginningBalance = row.beginning_balance ? row.beginning_balance : 0;
      model.incurredAmt = row.incurred_amount ? row.incurred_amount : 0;
      model.paymentAmt = row.payment_amount ? row.payment_amount : 0;
      model.closingBalance = row.balance_at_close ? row.balance_at_close : 0;
      modelArray.push(model);
    }
    return modelArray;
  }

  /**
   * Map server fields from the response to the model for the child payment.
   */
  private _mapChildFromServerFields(serverData: any): DebtSummaryModel[] {
    if (!serverData || !Array.isArray(serverData)) {
      return;
    }
    const modelArray = [];
    for (const row of serverData) {
      const model = new DebtSummaryModel({});
      model.selected = false;
      model.toggleChild = false;
      model.apiCall = row.api_call;
      model.transactionTypeIdentifier = row.transaction_type_identifier;
      model.transactionTypeDescription = row.transaction_type_description;
      model.reportId = row.report_id;
      model.scheduleType = row.schedule_type ? row.schedule_type : row.sched_type;
      model.transactionId = row.transaction_id;
      model.backRefTransactionId = row.back_ref_transaction_id;
      model.entityType = row.entity_type;
      model.entityId = row.entity_id;
      this._setDebtName(row);
      model.name = row.name;
      model.paymentAmt = row.expenditure_amount ? row.expenditure_amount : row.contribution_amount;
      model.paymentDate = row.expenditure_date ? row.expenditure_date : row.contribution_date;
      model.memoCode = row.memo_code;
      model.aggregate = row.aggregate_amt;
      modelArray.push(model);
    }
    return modelArray;
  }

  private _setDebtName(debt: any): void {
    const lastName = debt.last_name ? debt.last_name.trim() : '';
    const firstName = debt.first_name ? debt.first_name.trim() : '';
    const middleName = debt.middle_name ? debt.middle_name.trim() : '';
    const suffix = debt.suffix ? debt.suffix.trim() : '';
    const prefix = debt.prefix ? debt.prefix.trim() : '';

    if (debt.entity_type === 'IND' || debt.entity_type === 'CAN') {
      debt.name = `${lastName}, ${firstName}, ${middleName}, ${prefix}, ${suffix}`;
    } else {
      if (debt.hasOwnProperty('entity_name')) {
        debt.name = debt.entity_name;
      }
    }
  }

    /**
   * Map a single field name to its server field name equivalent.
   *
   * TODO Too many places where fields names are referenced when converting
   * from/to server names.  Need to consolidate.
   *
   * TODO The API should be changed to pass the property names expected by the front end.
   */
  public mapToSingleServerName(appFieldName: string) {

    // TODO map field names in constructor
    let name = '';

    // if (appFieldName === 'zip') {
    //   this._propertyNameConverterMap.get(appFieldName);
    // }

    name = appFieldName;
    switch (appFieldName) {
      case 'name':
        name = 'name';
        break;
      case 'entity_name':
        name = 'entity_name';
        break;  
      case 'entityType':
        name = 'entityType';
        break;
      case 'id':
        name = 'id';
        break;
      case 'street1':
        name = 'street1';
        break; 
      case 'street2':
        name = 'street2';
        break;         
      case 'city':
        name = 'city';
        break;         
      case 'state':
        name = 'state';
        break;                                
      case 'zip':
        name = 'zip';
        break;                        
      case 'employer':
        name = 'employer';
        break;
      case 'occupation':
        name = 'occupation';
        break;
      case 'phoneNumber':
        name = 'phoneNumber';
        break;  
      case 'entityName':
        name= 'entityName';
        break;
      case 'officeSought':
        name= 'officeSought';
        break;  
      case 'candOffice':
        name= 'candOffice';
        break;
      case 'candOfficeState':
        name= 'candOfficeState';
        break;
      case 'candOfficeDistrict':
        name= 'candOfficeDistrict';
        break;       
      case 'candCmteId':
        name= 'candCmteId';
        break;     
      case 'deletedDate':
        name= 'deletedDate';
        break;   
      case 'activeTransactionsCnt':
        name= 'activeTransactionsCnt';
        break;           
      default:
    }
    return name ? name : '';
  }
}
