import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';

@Component({
  selector: 'f3x-financial-summary',
  templateUrl: './financial-summary.component.html',
  styleUrls: ['./financial-summary.component.scss']
})
export class FinancialSummaryComponent implements OnInit {

  public viewMode: string = '';
  public tab1Data: any = {};

  constructor(
    private _http: HttpClient
  ) { }

  ngOnInit(): void {
    this.viewMode = 'tab1';

    this._http
     .get('http://localhost:3000/data')
     .subscribe(res => {
       console.log('res: ', res);
       if(res) {
         this.tab1Data = res[0];
       }
     });
  }

}
