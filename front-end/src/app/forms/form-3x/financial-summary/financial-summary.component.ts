import { HttpClient } from '@angular/common/http';
import { Component, OnDestroy, OnInit , ChangeDetectionStrategy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';
import { TransactionsMessageService } from '../../transactions/service/transactions-message.service';
import { FinancialSummaryService } from '../financial-summary/financial-summary.service';

@Component({
  selector: 'f3x-financial-summary',
  templateUrl: './financial-summary.component.html',
  styleUrls: ['./financial-summary.component.scss'],
  providers: [NgbTooltipConfig]
})
export class FinancialSummaryComponent implements OnInit, OnDestroy {
  public categoryId: string = '';
  public column: string = '';
  public direction: number = null;
  public isDesc: boolean = null;
  public tab1Data: any = {};
  public tab2Data: any = {};
  public tab3Data: any = {};
  public viewMode: string = '';
  public reportId: string = '';
  public step: string = '';
  public editMode: boolean;

  private _form3XReportType: any = {};

  private _formType: string = '';
  constructor(
    private _config: NgbTooltipConfig,
    private _http: HttpClient,
    private _financialSummaryService: FinancialSummaryService,
    private _transactionsMessageService: TransactionsMessageService,
    private _reportTypeService: ReportTypeService,
    private _activatedRoute: ActivatedRoute,
    private _router: Router
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this.viewMode = 'tab1';
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.step = this._activatedRoute.snapshot.queryParams.step;
    this.editMode = this._activatedRoute.snapshot.queryParams.edit === 'false' ? false : true;
    localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify({ saved: true }));
    //console.log('this.step = ', this.step);

    this._financialSummaryService.getSummaryDetails('3X').subscribe(
      res => {
        if (res) {
          //console.log('Accessing FinancialSummaryComponent res ...', res);
          this.tab1Data = res['Total Raised'];
          this.tab2Data = res['Total Spent'];
          this.tab3Data = res['Cash summary'];
        }
      },
      error => {
        //console.log('error: ', error);
      }
    );
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
    //console.log('FinancialSummaryComponent printPreview this._formType = ', this._formType);
    this._reportTypeService.printPreview('financial_screen', this._formType);
  }

  public viewTransactions(transactionCategory?: string): void {
    this._form3XReportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type`));

    if (this._form3XReportType === null || typeof this._form3XReportType === 'undefined') {
      this._form3XReportType = JSON.parse(localStorage.getItem(`form_${this._formType}_report_type_backup`));
    }

    if (typeof this._form3XReportType === 'object' && this._form3XReportType !== null) {
      if (this._form3XReportType.hasOwnProperty('reportId')) {
        this.reportId = this._form3XReportType.reportId;
      } else if (this._form3XReportType.hasOwnProperty('reportid')) {
        this.reportId = this._form3XReportType.reportid;
      }
    }
    //console.log(' FinancialSummaryComponent this.reportId = ', this.reportId);
    this._transactionsMessageService.sendLoadTransactionsMessage(this.reportId);
    this._router.navigate([`/forms/form/${this._formType}`], {
      queryParams: { step: 'transactions', reportId: this.reportId, edit: this.editMode, transactionCategory: transactionCategory }
    });
  }

  public all_Transactions(): void {
    this._router.navigate([`/forms/form/${this._formType}`], { queryParams: { step: 'step_2', edit: this.editMode } });
  }

  public expanded_Summary(): void {
    alert('This functionality not yet implemented...!');
  }

  public ImportTransactions(): void {
    alert('Import transaction is not yet supported');
  }
  
  /**
   * A method to run when component is destroyed.
   */
  public ngOnDestroy(): void {
    localStorage.removeItem('Summary_Screen');
    localStorage.removeItem(`form_${this._formType}_summary_screen`);
  }
}
