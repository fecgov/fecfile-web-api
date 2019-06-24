import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../../environments/environment';
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';
import { FinancialSummaryService } from '../financial-summary/financial-summary.service';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';

@Component({
  selector: 'f3x-financial-summary',
  templateUrl: './financial-summary.component.html',
  styleUrls: ['./financial-summary.component.scss'],
  providers: [NgbTooltipConfig]
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
  public reportId: string='';

  private _formType: string='';
  constructor(
    private _config: NgbTooltipConfig,
    private _http: HttpClient,
    private _financialSummaryService: FinancialSummaryService,
    private _reportTypeService: ReportTypeService,
    private _activatedRoute: ActivatedRoute,
    private _router: Router,
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this.viewMode = 'tab1';
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
   
    this._financialSummaryService
    .getSummaryDetails('3X')
    .subscribe(res => {
      if(res) {
            console.log("Accessing FinancialSummaryComponent res ...",res);
            
            this.tab1Data=res["Total Raised"];
            this.tab2Data=res["Total Spent"];
            this.tab3Data=res["Cash summary"];

            console.log("Accessing FinancialSummaryComponent this.tab1Data ...",this.tab1Data);
            console.log("Accessing FinancialSummaryComponent this.tab2Data ...",this.tab2Data);
            console.log("Accessing FinancialSummaryComponent this.tab3Data ...",this.tab3Data);

          }
        },
        (error) => {
          console.log('error: ', error);
        });


        const form3XReportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));

        if (typeof form3XReportType === 'object' && form3XReportType !== null) {
          if (form3XReportType.hasOwnProperty('reportId')) {
            this.reportId = form3XReportType.reportId;
          } else if (form3XReportType.hasOwnProperty('reportid')) {
            this.reportId = form3XReportType.reportid;
          }
        }      
        console.log(" FinancialSummaryComponent this.reportId = ", this.reportId );
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
  
  public printPreview(): void {
    this._reportTypeService
    .printPreviewPdf('3X', "PrintPreviewPDF")
    .subscribe(res => {
      if(res) {
            console.log("Accessing FinancialSummaryComponent printPriview res ...",res);
           
            if (res['results.pdf_url'] !== null) {
              console.log("res['results.pdf_url'] = ",res['results.pdf_url']);
              window.open(res.results.pdf_url, '_blank');
            }
          }
        },
        (error) => {
          console.log('error: ', error);
        });/*  */

  }
  public viewTransactions(): void {
        this._router.navigate([`/forms/transactions/${this._formType}/${this.reportId}`]);
  }
  
}
