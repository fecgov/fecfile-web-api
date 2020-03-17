import { Component, EventEmitter, ElementRef, HostListener, OnInit, Input, Output, ViewChild, ViewEncapsulation , ChangeDetectionStrategy } from '@angular/core';
import { ReportdetailsComponent } from '../reportdetails/reportdetails.component';
import { FormsService } from '../../shared/services/FormsService/forms.service';
import { ActivatedRoute } from '@angular/router';
import { ReportsMessageService } from '../service/reports-message.service';
import { animate, style, transition, trigger } from '@angular/animations';
import { ReportFilterModel } from '../model/report-filter.model';
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
  /* animations: [
    trigger('fadeInOut', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate(500, style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate(10, style({ opacity: 0 }))
      ])
    ])
  ] */
})

export class ReportheaderComponent implements OnInit {

public currentYear:number =0;
public reportsView = ActiveView.reports;
public showSideBar: boolean = false;
public existingReportId: string = "";
public view: string = ActiveView.reports;
public recycleBinView = ActiveView.recycleBin;
public isShowFilters = false;
public searchText = '';
public searchTextArray = [];
public viewMode = '';

/**
 * Subscription for applying filters to the reports obtained from
 * the server.
 */
private applyFiltersSubscription: Subscription;

private filters: ReportFilterModel = new ReportFilterModel();
private readonly filtersLSK = 'reports.filters';
private activeRoutesSubscription :Subscription;

  constructor(
    private _formService: FormsService,
    private _activeRoute: ActivatedRoute,
    private _reportsMessageService: ReportsMessageService,
  ) {   this.applyFiltersSubscription = this._reportsMessageService.getApplyFiltersMessage()
    .subscribe(
      (filters: ReportFilterModel) => {
        this.filters = filters;
        this.doSearch();
      }
    );
   }

  ngOnInit() {

    var dateObj = new Date();
    this.currentYear = dateObj.getUTCFullYear();
    this.clearSearch();
    this.viewMode = 'tab1';
    
    if (localStorage.getItem('form3XReportInfo.showDashBoard')==="Y"){
      this._formService.removeFormDashBoard("3X");
      
    }

    this.activeRoutesSubscription = this._activeRoute
        .params
        .subscribe( params => {
          this.existingReportId = params.reportId;
       });
    this.existingReportId = localStorage.getItem('Existing_Report_id');
    if (this.existingReportId !== "") {
          localStorage.removeItem('Existing_Report_id');
          localStorage.removeItem('orm_99_details.org_fileurl');
          localStorage.removeItem('form99PrintPreviewResponse');
          localStorage.setItem(`form_3X_saved`, JSON.stringify(false));
        }
      

    //this.formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    // If the filter was open on the last visit in the user session, open it.
    const filtersJson: string | null = localStorage.getItem(this.filtersLSK);

 
    let filters: ReportFilterModel;
    if (filtersJson != null) {
      filters = JSON.parse(filtersJson);
      if (filters.keywords) {
        if (filters.keywords.length > 0) {
          this.searchTextArray = filters.keywords;
          filters.show = true;
        }
      }
    } else {
      filters = new ReportFilterModel();
    }
    if (filters.show === true) {
      this.showFilters();
    }

  }
 
  public showFilter() : void {

    if (this.showSideBar){
        this.showSideBar=false;
    } else
    {
      this.showSideBar=true;
    }
  }

  private recycleReports() : void {
    this.view = ActiveView.recycleBin;
  }

  public showReports() {
    this.view = ActiveView.reports;
  }

  /**
   * A method to run when component is destroyed.
   */
  public ngOnDestroy(): void {
    this.applyFiltersSubscription.unsubscribe();
    this.activeRoutesSubscription.unsubscribe();
  }


  /**
   * Search reports.
   */
  public search() {
    // Don't allow more than 12 filters
    if (this.searchTextArray.length > 12) {
      return;
    }

    // TODO emit search message to the table reports component
    if (this.searchText) {
      this.searchTextArray.push(this.searchText);
      this.searchText = '';
    }
    //this.showFilter(); mahendra
    this.showSideBar=true;
    this.doSearch();
  
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
   * Show the table of reports in the recycle bin for the user.
   */
  public showRecycleBin() {
    this.view = ActiveView.recycleBin;
  }


  /**
   * Show the table of form reports.
   */
  public showreports() {
    this.view = ActiveView.reports;
  }


  /**
   * Show the option to select/deselect columns in the table.
   */
  public showPinColumns() {

    this.showreports();
    this._reportsMessageService.sendShowPinColumnMessage('show the Pin Col');
  }


  /**
   * Import reports from an external file.
   */
  public doImport() {
    alert('Import reports is not yet supported');
  }


  /**
   * Show filter options for reports.
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
   * Check if the view to show is reports.
   */
  public isReportViewActive() {
    return this.view === this.reportsView ? true : false;
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
    this._reportsMessageService.sendDoKeywordFilterSearchMessage(this.filters);
  }
}
