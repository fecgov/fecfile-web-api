import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';

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
  public tab2Data: any = {};
  public tab3Data: any = {};
  public viewMode: string = '';

  constructor(
    private _config: NgbTooltipConfig,
    private _http: HttpClient
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this.viewMode = 'tab1';

    this._http
     .get('http://localhost:3000/data')
     .subscribe(res => {
       if(res) {
         this.tab1Data = res[0];
         this.tab2Data = res[1];
         this.tab3Data = res[2];
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
