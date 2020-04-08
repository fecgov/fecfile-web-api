import { Injectable } from '@angular/core';
import { of, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class F1mService {


  constructor(
    // private _http: HttpClient,
    // private _cookieService: CookieService,
    // private _reportTypeService: ReportTypeService,
    // private _activatedRoute: ActivatedRoute
    ) { }

    public saveForm(data:any) : Observable<any>{
      return of({reportId:'12345'});
    }

    public getReportInfo() :Observable<any>{
      return of({treasurerLastName:'Smith', treasurerFirstName:'John', treasurerMiddleName:'M', treasurerPrefix: 'Mr.', treasurerSuffix: 'II'});
    }


}





