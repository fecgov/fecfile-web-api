import { Component, EventEmitter, ElementRef, HostListener, OnInit, Input, Output, ViewChild, ViewEncapsulation } from '@angular/core';
import { ReportdetailsComponent } from '../reportdetails/reportdetails.component';
import { FormsService } from '../../shared/services/FormsService/forms.service';
import { ActivatedRoute } from '@angular/router';
import { TransactionsMessageService } from '../service/reports-message.service';
import { animate, style, transition, trigger } from '@angular/animations';
import { TransactionFilterModel } from '../model/report-filter.model';
import { Subscription } from 'rxjs/Subscription';


export enum ActiveView {
  reports = "reports",
  recycleBin = "recycleBin"
}


//@Output() status: EventEmitter<any> = new EventEmitter<any>();
@Component({
  selector: 'app-reportheader',
  templateUrl: './reportheader.component.html',
  styleUrls: ['./reportheader.component.scss'],
  encapsulation: ViewEncapsulation.None,
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate(500, style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate(10, style({ opacity: 0 }))
      ])
    ])
  ]
})

export class ReportheaderComponent implements OnInit {

public currentYear:number =0;
public reportsView = ActiveView.reports;
public showSideBar: boolean = false;
public existingReportId: string = "";
public view: string = ActiveView.reports;
public transactionsView = ActiveView.reports;
public recycleBinView = ActiveView.recycleBin;
public isShowFilters = false;
public searchText = '';
public searchTextArray = [];

/**
 * Subscription for applying filters to the transactions obtained from
 * the server.
 */
private applyFiltersSubscription: Subscription;

private filters: TransactionFilterModel = new TransactionFilterModel();
private readonly filtersLSK = 'transactions.filters';

  constructor(
    private _formService: FormsService,
    private _activeRoute: ActivatedRoute,
    private _transactionsMessageService: TransactionsMessageService,
  ) { }

  ngOnInit() {

    var dateObj = new Date();
    this.currentYear = dateObj.getUTCFullYear();
    
    
    if (localStorage.getItem('form3XReportInfo.showDashBoard')==="Y"){
      this._formService.removeFormDashBoard("3X");
    }

    this._activeRoute
        .params
        .subscribe( params => {
          this.existingReportId = params.reportId;
          console.log("parameters found...")
       });
       this.existingReportId = localStorage.getItem('Existing_Report_id');
       localStorage.removeItem('Existing_Report_id');
    console.log(" ReportheaderComponent this.existingReportId =", this.existingReportId);    

    //this.formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    // If the filter was open on the last visit in the user session, open it.
    const filtersJson: string | null = localStorage.getItem(this.filtersLSK);
    let filters: TransactionFilterModel;
    if (filtersJson != null) {
      filters = JSON.parse(filtersJson);
      if (filters.keywords) {
        if (filters.keywords.length > 0) {
          this.searchTextArray = filters.keywords;
          filters.show = true;
        }
      }
    } else {
      filters = new TransactionFilterModel();
    }
    if (filters.show === true) {
      this.showFilters();
    }

  }

  private showFilter() : void {
    if (this.showSideBar){
        this.showSideBar=false;
    } else
    {
      this.showSideBar=true;
    }
  }

    private recycleReports() : void {
    alert("Recycle report is not yet supported");
  }

  /**
   * A method to run when component is destroyed.
   */
  public ngOnDestroy(): void {
    this.applyFiltersSubscription.unsubscribe();
  }


  /**
   * Search transactions.
   */
  public search() {

    // Don't allow more than 12 filters
    if (this.searchTextArray.length > 12) {
      return;
    }

    // TODO emit search message to the table transactions component
    if (this.searchText) {
      this.searchTextArray.push(this.searchText);
      this.searchText = '';
    }
    this.doSearch();
    this.showFilters();
  }


  /**
   * Clear the search filters
   */
  public clearSearch() {
    this.searchTextArray = [];
    this.searchText = '';
    this.doSearch();
  }


  /**
   * Remove the search text from the array.
   * 
   * @param index index in the array
   */
  public removeSearchText(index: number) {
    this.searchTextArray.splice(index, 1);
    this.doSearch();
  }


  /**
   * Show the table of transactions in the recycle bin for the user.
   */
  public showRecycleBin() {
    this.view = ActiveView.recycleBin;
  }


  /**
   * Show the table of form transactions.
   */
  public showTransactions() {
    this.view = ActiveView.reports;
  }


  /**
   * Show the option to select/deselect columns in the table.
   */
  public showPinColumns() {
    console.log(" reort header showPinColumns ...");
    this.showTransactions();
    this._transactionsMessageService.sendShowPinColumnMessage('show the Pin Col');
  }


  /**
   * Import transactions from an external file.
   */
  public doImport() {
    alert('Import transactions is not yet supported');
  }


  /**
   * Show filter options for transactions.
   */
  public showFilters() {
    this.isShowFilters = true;
  }


  /**
   * Show the categories and hide the filters.
   */
  public showCategories() {
    this.isShowFilters = false;
  }


  /**
   * Check if the view to show is Transactions.
   */
  public isTransactionViewActive() {
    return this.view === this.transactionsView ? true : false;
  }


  /**
   * Check if the view to show is Recycle Bin.
   */
  public isRecycleBinViewActive() {
    return this.view === this.recycleBinView ? true : false;
  }


  /**
   * Send a message to the subscriber to run the search.
   */
  private doSearch() {
    this.filters.keywords = this.searchTextArray;
    this._transactionsMessageService.sendDoKeywordFilterSearchMessage(this.filters);
  }
}
