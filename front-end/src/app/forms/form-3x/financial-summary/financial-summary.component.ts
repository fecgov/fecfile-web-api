import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';

@Component({
  selector: 'f3x-financial-summary',
  templateUrl: './financial-summary.component.html',
  styleUrls: ['./financial-summary.component.scss']
})
export class FinancialSummaryComponent implements OnInit {

  public categoryId: string = '';
  public column: string = '';
  public isDesc: boolean = null;
  public tab1Data: any = {};
  public viewMode: string = '';

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

  public sort(property: string): void {
    this.isDesc = !this.isDesc; //change the direction
    this.column = property;
    let direction = this.isDesc ? 1 : -1;

    this.tab1Data.rows.sort(function(a, b){
        if(a[property] < b[property]){
            return -1 * direction;
        }
        else if( a[property] > b[property]){
            return 1 * direction;
        }
        else{
            return 0;
        }
    });
  }

}
