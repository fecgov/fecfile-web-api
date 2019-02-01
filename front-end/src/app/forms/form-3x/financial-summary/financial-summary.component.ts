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
  public direction: number = null;
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
       if(res) {
         this.tab1Data = res[0];
       }
     });
  }

  /**
   * Toggles table column sorting.
   *
   * @param      {String}  property  The property to be sorted.
   */
  public sort(property: string): void {
    this.isDesc = !this.isDesc;
    this.column = property;
    this.direction = this.isDesc ? 1 : -1;
  }
}
