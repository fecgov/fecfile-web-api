import { Component, Input, OnDestroy, OnInit, ViewChild, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ModalDirective } from 'ngx-bootstrap/modal';
import { PaginationInstance } from 'ngx-pagination';
import { Subject } from 'rxjs';
import 'rxjs/add/operator/distinctUntilChanged';
import 'rxjs/add/operator/takeUntil';
import { Subscription } from 'rxjs/Subscription';
import { ConfirmModalComponent, ModalHeaderClassEnum } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { SortableColumnModel } from 'src/app/shared/services/TableService/sortable-column.model';
import { TableService } from 'src/app/shared/services/TableService/table.service';
import { UtilService } from 'src/app/shared/utils/util.service';
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';
import { IndividualReceiptService } from '../../form-3x/individual-receipt/individual-receipt.service';
import { TransactionTypeService } from '../../form-3x/transaction-type/transaction-type.service';
import { FilterTypes } from '../enums/filterTypes.enum';
import { TransactionFilterModel } from '../model/transaction-filter.model';
import { TransactionModel } from '../model/transaction.model';
import { TransactionsMessageService } from '../service/transactions-message.service';
import { GetTransactionsResponse, TransactionsService } from '../service/transactions.service';
import { ActiveView } from '../transactions.component';
import { AuthService} from '../../../shared/services/AuthService/auth.service';

const transactionCategoryOptions = [];

@Component({
  selector: 'app-transactions-table',
  templateUrl: './transactions-table.component.html',
  styleUrls: [
    './transactions-table.component.scss',
    '../../../shared/partials/confirm-modal/confirm-modal.component.scss'
  ],
  encapsulation: ViewEncapsulation.None,
  /* animations: [
    trigger('fadeInOut', [
      transition(':enter', [style({ opacity: 0 }), animate(500, style({ opacity: 1 }))]),
      transition(':leave', [animate(0, style({ opacity: 0 }))])
    ])
  ] */
})
export class TransactionsTableComponent implements OnInit, OnDestroy {
  @ViewChild('columnOptionsModal')
  public columnOptionsModal: ModalDirective;

  @Input()
  public formType: string;

  @Input()
  public reportId: string;

  @Input()
  public transactionId: string;

  @Input()
  public routeData: any;

  @Input()
  public tableType: string;

  public transactionsModel: Array<TransactionModel>;
  public totalAmount: number;
  public transactionsView = ActiveView.transactions;
  public recycleBinView = ActiveView.recycleBin;
  public bulkActionDisabled = true;
  public bulkActionCounter = 0;
  public pageReceivedTransactions: boolean = false;
  public pageReceivedReports: boolean = false;
  public transactionCategories: any = [];
  public transactionCategory: string = '';
  public committeeDetails: any;
  public editMode: boolean = false;

  // ngx-pagination config
  public pageSizes: number[] = UtilService.PAGINATION_PAGE_SIZES;
  public maxItemsPerPage: number = this.pageSizes[0];
  public paginationControlsMaxSize: number = 10;
  public directionLinks: boolean = false;
  public autoHide: boolean = true;
  public config: PaginationInstance;
  public numberOfPages: number = 0;
  public pageNumbers: number[] = [];
  public gotoPage: number = 1;

  private filters: TransactionFilterModel;
  // private keywords = [];
  private firstItemOnPage = 0;
  private lastItemOnPage = 0;
  private _form99Details: any = {};
  public _allTransactions: boolean = false;

  // Local Storage Keys
  private readonly transactionSortableColumnsLSK = 'transactions.trx.sortableColumn';
  private readonly recycleSortableColumnsLSK = 'transactions.recycle.sortableColumn';
  private readonly transactionCurrentSortedColLSK = 'transactions.trx.currentSortedColumn';
  private readonly recycleCurrentSortedColLSK = 'transactions.recycle.currentSortedColumn';
  private readonly transactionPageLSK = 'transactions.trx.page';
  private readonly recyclePageLSK = 'transactions.recycle.page';
  private readonly filtersLSK = 'transactions.filters';

  /**.
   * Array of columns to be made sortable.
   */
  private sortableColumns: SortableColumnModel[] = [];

  /**
   * A clone of the sortableColumns for reverting user
   * column options on a Cancel.
   */
  private cloneSortableColumns: SortableColumnModel[] = [];

  /**
   * Identifies the column currently sorted by name.
   */
  private currentSortedColumnName: string;

  /**
   * Subscription for messages sent from the parent component to show the PIN Column
   * options.
   */
  private showPinColumnsSubscription: Subscription;

  /**
   * Subscription for running the keyword and filter search
   * to the transactions obtained from the server.
   */
  private keywordFilterSearchSubscription: Subscription;

  private loadTransactionsSubscription: Subscription;

  private columnOptionCount = 0;
  private maxColumnOption = 6;
  public readonly maxColumnOptionReadOnly = 6;
  private allTransactionsSelected: boolean;
  private clonedTransaction: any;
  private _previousUrl: any;
  public apiError: boolean = false;

  private _filterToTransactionTypeMap: any =
    [
      { filterName: 'filterCategoriesText', options: ['receipts', 'disbursements', 'loans-and-debts', 'other'] },
      { filterName: 'filterAmountMin', options: ['receipts', 'disbursements', 'other'] },
      { filterName: 'filterAmountMax', options: ['receipts', 'disbursements', 'other'] },
      { filterName: 'filterLoanAmountMin', options: ['loans-and-debts'] },
      { filterName: 'filterLoanAmountMax', options: ['loans-and-debts'] },
      { filterName: 'filterAggregateAmountMin', options: ['receipts'] },
      { filterName: 'filterAggregateAmountMax', options: ['receipts'] },
      { filterName: 'filterLoanClosingBalanceMin', options: ['loans-and-debts'] },
      { filterName: 'filterLoanClosingBalanceMax', options: ['loans-and-debts'] },
      { filterName: 'filterDebtBeginningBalanceMin', options: ['loans-and-debts'] },
      { filterName: 'filterDebtBeginningBalanceMax', options: ['loans-and-debts'] },
      { filterName: 'filterDateFrom', options: ['receipts', 'disbursements', 'other'] },
      { filterName: 'filterDateTo', options: ['receipts', 'disbursements', 'other'] },
      { filterName: 'filterMemoCode', options: ['receipts', 'disbursements', 'loans-and-debts', 'other'] },
      { filterName: 'filterElectionCode', options: ['disbursements'] },
      { filterName: 'filterElectionYearFrom', options: ['disbursements'] },
      { filterName: 'filterElectionYearTo', options: ['disbursements'] },
      { filterName: 'filterSchedule', options: ['other'] },
      { filterName: 'states', options: ['receipts', 'disbursements', 'loans-and-debts', 'other'] }
    ];

  private _filterToTypeMap: any = [
    { filterName: 'filterAmountMin', filterType: FilterTypes.amount },
    { filterName: 'filterAmountMax', filterType: FilterTypes.amount },
    { filterName: 'filterLoanAmountMin', filterType: FilterTypes.loanAmount },
    { filterName: 'filterLoanAmountMax', filterType: FilterTypes.loanAmount },
    { filterName: 'filterAggregateAmountMin', filterType: FilterTypes.aggregateAmount },
    { filterName: 'filterAggregateAmountMax', filterType: FilterTypes.aggregateAmount },
    { filterName: 'filterLoanClosingBalanceMin', filterType: FilterTypes.loanClosingBalance },
    { filterName: 'filterLoanClosingBalanceMax', filterType: FilterTypes.loanClosingBalance },
    { filterName: 'filterDebtBeginningBalanceMin', filterType: FilterTypes.debtBeginningBalance },
    { filterName: 'filterDebtBeginningBalanceMax', filterType: FilterTypes.debtBeginningBalance },
    { filterName: 'filterDateFrom', filterType: FilterTypes.date },
    { filterName: 'filterDateTo', filterType: FilterTypes.date },
    { filterName: 'filterElectionCode', filterType: FilterTypes.electionCodes },
    { filterName: 'filterElectionYearFrom', filterType: FilterTypes.electionYear },
    { filterName: 'filterElectionYearTo', filterType: FilterTypes.electionYear },
    { filterName: 'filterSchedule', filterType: FilterTypes.schedule },
  ]

  //this dummy subject is used only to let the activatedRoute subscription know to stop upon ngOnDestroy.
  //there is no unsubscribe() for activateRoute but while cycling between 'Transactions' and 'Recycling Bin' views
  //subscriptions are piling up, causing a single api call to be made n+1 times. 
  private onDestroy$ = new Subject();
  loadDefaultReceiptsTabSubscription: Subscription;
  routerSubscription: Subscription;

  selectedFromMultiplePages: Array <TransactionModel> = [];

  constructor(
    private _transactionsService: TransactionsService,
    private _transactionsMessageService: TransactionsMessageService,
    private _tableService: TableService,
    private _utilService: UtilService,
    private _dialogService: DialogService,
    private _reportTypeService: ReportTypeService,
    private _router: Router,
    private _activatedRoute: ActivatedRoute,
    private _receiptService: IndividualReceiptService,
    private _transactionTypeService: TransactionTypeService,
    private _authService: AuthService,
  ) {

    const paginateConfig: PaginationInstance = {
      id: 'forms__trx-table-pagination',
      itemsPerPage: this.maxItemsPerPage,
      currentPage: 1
    };
    this.config = paginateConfig;

    this.showPinColumnsSubscription = this._transactionsMessageService.getShowPinColumnMessage().subscribe(message => {
      this.showPinColumns();
    });

    this.keywordFilterSearchSubscription = this._transactionsMessageService
      .getDoKeywordFilterSearchMessage()
      .subscribe((filters: TransactionFilterModel) => {
        if (filters) {
          this.filters = filters;
          if (filters.formType) {
            this.formType = filters.formType;
          }
        }
        this.getPage(1);
      });

    this.loadDefaultReceiptsTabSubscription = this._transactionsMessageService.getLoadDefaultTabMessage()
      .takeUntil(this.onDestroy$)
      .subscribe(p => {
        this.transactionCategory = p.transactionCategory;
        this.reportId = p.reportId;
        this._router.navigate([`/forms/form/${this.formType}`], {
          queryParams: {
            step: p.step,
            reportId: p.reportId,
            edit: p.edit,
            transactionCategory: p.transactionCategory,
            allTransactions: p.allTransactions
          }
        });
      })

    this.loadTransactionsSubscription = this._transactionsMessageService
      .getLoadTransactionsMessage()
      .subscribe((reportId: any) => {
        this.reportId = reportId;
        this.getPage(this.config.currentPage);
      });


    this.routerSubscription = _activatedRoute.queryParams.takeUntil(this.onDestroy$)
    .distinctUntilChanged().subscribe(p => {
      this.transactionCategory = p.transactionCategory;
      if (p.allTransactions === true || p.allTransactions === 'true') {
        this._allTransactions = true;
      } else {
        this._allTransactions = false;
      }
      this.getPage(1);
      this.clonedTransaction = {};
      this.setSortableColumns();
      if (p.edit === 'true' || p.edit === true) {
        this.editMode = true;
      }
      
    });
  }

  /**
   * Initialize the component.
   */
  public ngOnInit(): void {
    this.committeeDetails = JSON.parse(localStorage.getItem('committee_details'));
    this.pageReceivedTransactions = false;
    this.pageReceivedReports = false;

    this.getCachedValues();
    this.cloneSortableColumns = this._utilService.deepClone(this.sortableColumns);

    for (const col of this.sortableColumns) {
      if (col.checked) {
        this.columnOptionCount++;
      }
    }

    // If this does work send message from f3x when step is reports
    // If it does work, put get reportIdfrom stor in common service
    if (!this.reportId) {
      // this.reportId = this._getReportIdFromStorage();
    }
    if (this.reportId) {
      // this.getPage(this.config.currentPage);
    }

    // When coming from transaction route the reportId is not received
    // from the input perhaps due to the ngDoCheck in transactions-component.
    // TODO look at replacing ngDoCheck and reportId as Input()
    // with a message subscription service.
    /* if (this.routeData) {
      if (this.routeData.accessedByRoute) {
        if (this.routeData.reportId) {
          //console.log('reportId for transaction accessed directly by route is ' + this.routeData.reportId);
          this.reportId = this.routeData.reportId;
          this.getPage(this.config.currentPage);
        }
      }
    } */

    this._transactionTypeService.getTransactionCategories('3X').subscribe(res => {
      if (res) {
        this.transactionCategories = res.data.transactionCategories;
      }
      for (
        let transactionCategorieIndex = 0;
        transactionCategorieIndex < this.transactionCategories.length;
        transactionCategorieIndex++
      ) {
        for (
          let transactionCategoryOptionIndex = 0;
          transactionCategoryOptionIndex < this.transactionCategories[transactionCategorieIndex].options.length;
          transactionCategoryOptionIndex++
        ) {
          for (
            let transactionCategoryOptionOptionsIndex = 0;
            transactionCategoryOptionOptionsIndex <
            this.transactionCategories[transactionCategorieIndex].options[transactionCategoryOptionIndex].options
              .length;
            transactionCategoryOptionOptionsIndex++
          ) {
            transactionCategoryOptions.push(
              this.transactionCategories[transactionCategorieIndex].options[transactionCategoryOptionIndex].options[
              transactionCategoryOptionOptionsIndex
              ]
            );
          }
        }
      }
    });
    this.getPage(this.config.currentPage);
    this.applyDisabledColumnOptions();
  }

  /**
   * A method to run when component is destroyed.
   */
  public ngOnDestroy(): void {
    this.setCachedValues();
    this.showPinColumnsSubscription.unsubscribe();
    this.keywordFilterSearchSubscription.unsubscribe();
    this.loadTransactionsSubscription.unsubscribe();
    this.loadDefaultReceiptsTabSubscription.unsubscribe();
    this.routerSubscription.unsubscribe();
    this.onDestroy$.next(true);
  }

  /**
   * The Transactions for a given page.
   *
   * @param page the page containing the transactions to get
   */
  public getPage(page: number): void {
    this.bulkActionCounter = 0;
    this.bulkActionDisabled = true;
    this.gotoPage = page;

    switch (this.tableType) {
      case this.transactionsView:
      default:
        this.getTransactionsPage(page);
        break;
      case this.recycleBinView:
        this.getRecyclingPage(page);
        break;
    }
  }

  /**
   * onChange for maxItemsPerPage.
   *
   * @param pageSize the page size to get
   */
  public onMaxItemsPerPageChanged(pageSize: number): void {
    this.config.currentPage = 1;
    this.gotoPage = 1;
    this.config.itemsPerPage = pageSize;
    this.getPage(this.config.currentPage);
  }

  /**
   * onChange for gotoPage.
   *
   * @param page the page to get
   */
  public onGotoPageChange(page: number): void {
    if (this.config.currentPage == page) {
      return;
    }
    this.config.currentPage = page;
    this.getPage(this.config.currentPage);
  }

  getSubTransactions(transactionId, apiCall) {
    // const reportId = this._getReportIdFromStorage();
    this._receiptService.getDataSchedule(this.reportId, transactionId, apiCall).subscribe(res => {
      if (Array.isArray(res)) {
        for (const trx of res) {
          if (trx.hasOwnProperty('transaction_id')) {
            if (trx.transaction_id === transactionId) {
              if (trx.hasOwnProperty('child')) {
                for (const subTrx of trx.child) {
                  //console.log('sub tran id ' + subTrx.transaction_id);
                }
              }
            }
          }
        }
      }
    });
  }

  /**
   * The Transactions for a given page.
   *
   * @param page the page containing the transactions to get
   */
  public getTransactionsPage(page: number): void {
    if (!this.reportId && !this._allTransactions) {
      return;
    }
    this.config.currentPage = page;

    let sortedCol: SortableColumnModel = this._tableService.getColumnByName(
      this.currentSortedColumnName,
      this.sortableColumns
    );

    // smahal: quick fix for sortCol issue not retrived from cache
    if (!sortedCol) {
      this.setSortDefault();
      sortedCol = this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);
    }

    if (sortedCol) {
      if (sortedCol.descending === undefined || sortedCol.descending === null) {
        sortedCol.descending = false;
      }
    } else {
      sortedCol = new SortableColumnModel('', false, false, false, false);
    }

    const serverSortColumnName = this._transactionsService.mapToSingleServerName(this.currentSortedColumnName);

    let categoryType = 'receipts_tran';

    if (this.transactionCategory === 'disbursements') {
      categoryType = 'disbursements_tran';
    } else if (this.transactionCategory === 'loans-and-debts') {
      categoryType = 'loans_tran';
    } else if (this.transactionCategory === 'other') {
      categoryType = 'other_tran';
    }

    /* let categorySpecificColumns = localStorage.getItem(this.transactionSortableColumnsLSK) ? JSON.parse(localStorage.getItem(this.transactionSortableColumnsLSK)):null;
    let applicableFilters;
    if(this.filters && this.sortableColumns && categorySpecificColumns){
      applicableFilters = this._transactionsService.removeFilters(this.filters,this.sortableColumns, categorySpecificColumns);
    }
    else{
      applicableFilters = this.filters;
    } */

    let actualFilters: TransactionFilterModel = this.removeUnapplicableFilters(this.transactionCategory);

    this._transactionsService
      .getFormTransactions(
        this.formType,
        this.reportId,
        page,
        this.config.itemsPerPage,
        serverSortColumnName,
        sortedCol.descending,
        actualFilters,
        categoryType,
        false,
        this._allTransactions
      )
      .subscribe((res: GetTransactionsResponse) => {
        this.apiError = false;
        this.transactionsModel = [];

        // fixes an issue where no items shown when current page != 1 and new filter
        // result has only 1 page.
        if (res.totalPages === 1) {
          this.config.currentPage = 1;
        }

        this._transactionsService.addUIFileds(res);

        const transactionsModelL = this._transactionsService.mapFromServerFields(res.transactions);
        this.transactionsModel = transactionsModelL;

        this.setSelectedForMultiplyPages();

        if (this.clonedTransaction && this.clonedTransaction.hasOwnProperty('transaction_id')) {
          for (
            let transactionModelIndex = 0;
            transactionModelIndex < this.transactionsModel.length;
            transactionModelIndex++
          ) {
            if (this.transactionsModel[transactionModelIndex].transactionId === this.clonedTransaction.transaction_id) {
              this.transactionsModel[transactionModelIndex].cloned = true;
              this.editTransaction(this.transactionsModel[transactionModelIndex]);
            }
            // loop through any children as well
            else {
              if (this.transactionsModel[transactionModelIndex].child && this.transactionsModel[transactionModelIndex].child.length > 0) {
                for (let childTransactionModelIndex = 0;
                  childTransactionModelIndex < this.transactionsModel[transactionModelIndex].child.length;
                  childTransactionModelIndex++) {
                  if (this.transactionsModel[transactionModelIndex].child[childTransactionModelIndex].transactionId === this.clonedTransaction.transaction_id) {
                    this.transactionsModel[transactionModelIndex].child[childTransactionModelIndex].cloned = true;
                    this.editTransaction(this.transactionsModel[transactionModelIndex].child[childTransactionModelIndex]);
                  }
                }
              }
            }

          }
        }

        this.totalAmount = res.totalAmount ? res.totalAmount : 0;
        this.config.totalItems = res.totalTransactionCount ? res.totalTransactionCount : 0;
        this.numberOfPages = res.totalPages;

        this.pageNumbers = Array.from(new Array(this.numberOfPages), (x,i) => i+1);
        this.allTransactionsSelected = false;
      }, error => {
        //console.log('API Error occured: ' + error);
        this.apiError = true;
      });
  }

  /**
   * Any unapplicable filters that may not apply for current tab / view are removed
   * @param categoryType 
   */
  private removeUnapplicableFilters(categoryType: string) {
    let actualFilters: TransactionFilterModel = this._utilService.deepClone(this.filters);

    if (actualFilters) {
      let filterNames = this._filterToTransactionTypeMap.map(f => f.filterName);

      //for the four tabs
      for (let filter in actualFilters) {
        if (filter && filter.startsWith('filter') && actualFilters[filter]) { // do a possible null check?

          let applicableTransactions = [];
          this._filterToTransactionTypeMap.forEach(e => {
            if (e.filterName === filter) {
              applicableTransactions = e.options;
            }
          });
          if (applicableTransactions && applicableTransactions.length > 0 && !applicableTransactions.includes(categoryType)) {
            actualFilters[filter] = null;

            //clear the form on the screen for that filter & remove the tag
            this.filters[filter] = null;
            let filterType = this._filterToTypeMap.filter(e => e.filterName === filter);
            if (filterType && filterType.length > 0) {
              this._transactionsMessageService.sendRemoveTagMessage({ 'type': filterType[0].filterType });
            }

          }
        }
      }

      //for deleted_date based on view
      if (!this.isRecycleBinViewActive()) {
        actualFilters.filterDeletedDateFrom = null;
        actualFilters.filterDeletedDateTo = null;
        this._transactionsMessageService.sendRemoveTagMessage({
          'type': FilterTypes.deletedDate,
        })
      }
    }
    /*     this._transactionsMessageService.sendApplyFiltersMessage({
          filters: actualFilters, isClearKeyword: false
        }) */
    return actualFilters;
  }

  public changeTransactionCategory(transactionCategory) {

    //clear all filters first
    // this._transactionsMessageService.sendClearAllFiltersMessage({});

    this._router.navigate([`/forms/form/${this.formType}`], {
      queryParams: {
        step: this._activatedRoute.snapshot.queryParams.step,
        reportId: this._activatedRoute.snapshot.queryParams.reportId,
        edit: this._activatedRoute.snapshot.queryParams.edit,
        transactionCategory: transactionCategory,
        allTransactions: this._allTransactions
      }
    });

    this.selectedFromMultiplePages = [];
  }

  /**
   * The Transactions for the recycling bin.
   *
   * @param page the page containing the transactions to get
   */
  public getRecyclingPage(page: number): void {
    this.config.currentPage = page;

    let sortedCol: SortableColumnModel = this._tableService.getColumnByName(
      this.currentSortedColumnName,
      this.sortableColumns
    );

    // smahal: quick fix for sortCol issue not retrived from cache
    if (!sortedCol) {
      this.setSortDefault();
      sortedCol = this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);
    }

    if (sortedCol) {
      if (sortedCol.descending === undefined || sortedCol.descending === null) {
        sortedCol.descending = false;
      }
    } else {
      sortedCol = new SortableColumnModel('', false, false, false, false);
    }

    const serverSortColumnName = this._transactionsService.mapToSingleServerName(this.currentSortedColumnName);

    let categoryType = 'receipts_tran';

    if (this.transactionCategory === 'disbursements') {
      categoryType = 'disbursements_tran';
    } else if (this.transactionCategory === 'loans-and-debts') {
      categoryType = 'loans_tran';
    } else if (this.transactionCategory === 'other') {
      categoryType = 'other_tran';
    }

    this._transactionsService
      .getFormTransactions(
        this.formType,
        this.reportId,
        page,
        this.config.itemsPerPage,
        serverSortColumnName,
        sortedCol.descending,
        this.filters,
        categoryType,
        true,
        this._allTransactions
      )
      .subscribe((res: GetTransactionsResponse) => {
        this.transactionsModel = [];

        // fixes an issue where no items shown when current page != 1 and new filter
        // result has only 1 page.
        if (res.totalPages === 1) {
          this.config.currentPage = 1;
        }

        this._transactionsService.addUIFileds(res);

        // this.transactionsModel = res.transactions;

        const transactionsModelL = this._transactionsService.mapFromServerFields(res.transactions);
        this.transactionsModel = transactionsModelL;

        this.setSelectedForMultiplyPages();

        // handle non-numeric amounts
        // TODO handle this server side in API
        // for (const model of this.transactionsModel) {
        //   model.amount = model.amount ? model.amount : 0;
        //   model.aggregate = model.aggregate ? model.aggregate : 0;
        // }

        this.config.totalItems = res.totalTransactionCount ? res.totalTransactionCount : 0;
        this.numberOfPages = res.totalPages;

        this.pageNumbers = Array.from(new Array(this.numberOfPages), (x,i) => i+1);
        this.allTransactionsSelected = false;
      });
  }

  /**
   * Wrapper method for the table service to set the class for sort column styling.
   *
   * @param colName the column to apply the class
   * @returns string of classes for CSS styling sorted/unsorted classes
   */
  public getSortClass(colName: string): string {
    return this._tableService.getSortClass(colName, this.currentSortedColumnName, this.sortableColumns);
  }

  /**
   * Change the sort direction of the table column.
   *
   * @param colName the column name of the column to sort
   */
  public changeSortDirection(colName: string): void {
    this.currentSortedColumnName = this._tableService.changeSortDirection(colName, this.sortableColumns);

    // TODO this could be done client side or server side.
    // call server for page data in new direction
    this.getPage(this.config.currentPage);
  }

  /**
   * Get the SortableColumnModel by name.
   *
   * @param colName the column name in the SortableColumnModel.
   * @returns the SortableColumnModel matching the colName.
   */
  public getSortableColumn(colName: string): SortableColumnModel {
    for (const col of this.sortableColumns) {
      if (col.colName === colName) {
        return col;
      }
    }
    return new SortableColumnModel('', false, false, false, false);
  }

  /**
   * Determine if the column is to be visible in the table.
   *
   * @param colName
   * @returns true if visible
   */
  public isColumnVisible(colName: string): boolean {
    const sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      return sortableCol.visible;
    } else {
      return false;
    }
  }

  /**
   * Set the visibility of a column in the table.
   *
   * @param colName the name of the column to make shown
   * @param visible is true if the columns should be shown
   */
  public setColumnVisible(colName: string, visible: boolean) {
    const sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      sortableCol.visible = visible;
    }
  }

  /**
   * Set the checked property of a column in the table.
   * The checked is true if the column option settings
   * is checked for the column.
   *
   * @param colName the name of the column to make shown
   * @param checked is true if the columns should be shown
   */
  private setColumnChecked(colName: string, checked: boolean) {
    const sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      sortableCol.checked = checked;
    }
  }

  /**
   *
   * @param colName Determine if the checkbox column option should be disabled.
   */
  public disableOption(colName: string): boolean {
    const sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      if (!sortableCol.checked && this.columnOptionCount > this.maxColumnOption - 1) {
        return true;
      }
    }
    return false;
  }

  /**
   * Toggle the visibility of a column in the table.
   *
   * @param colName the name of the column to toggle
   * @param e the click event
   */
  public toggleVisibility(colName: string, e: any) {
    if (!this.sortableColumns) {
      return;
    }

    // only permit the max checked at a time
    if (e.target.checked === true) {
      this.columnOptionCount = 0;
      for (const col of this.sortableColumns) {
        if (col.checked) {
          this.columnOptionCount++;
        }
        if (this.columnOptionCount > this.maxColumnOptionReadOnly) {
          this.setColumnChecked(colName, false);
          e.target.checked = false;
          this.columnOptionCount--;
          return;
        }
      }
    } else {
      this.columnOptionCount--;
    }

    this.applyDisabledColumnOptions();
  }

  /**
   * Disable the unchecked column options if the max is met.
   */
  private applyDisabledColumnOptions() {
    if (this.columnOptionCount > this.maxColumnOption - 1) {
      for (const col of this.sortableColumns) {
        col.disabled = !col.checked;
      }
    } else {
      for (const col of this.sortableColumns) {
        col.disabled = false;
      }
    }
  }

  /**
   * Save the columns to show selected by the user.
   */
  public saveColumnOptions() {
    for (const col of this.sortableColumns) {
      this.setColumnVisible(col.colName, col.checked);
    }
    this.cloneSortableColumns = this._utilService.deepClone(this.sortableColumns);
    this.columnOptionsModal.hide();
  }

  /**
   * Cancel the request to save columns options.
   */
  public cancelColumnOptions() {
    this.columnOptionsModal.hide();
    this.sortableColumns = this._utilService.deepClone(this.cloneSortableColumns);
  }

  /**
   * Toggle checking all types.
   *
   * @param e the click event
   */
  public toggleAllTypes(e: any) {
    const checked = e.target.checked ? true : false;
    for (const col of this.sortableColumns) {
      this.setColumnVisible(col.colName, checked);
    }
  }

  /**
   * Determine if pagination should be shown.
   */
  public showPagination(): boolean {
    if (!this.autoHide) {
      return true;
    }
    if (this.config.totalItems > this.config.itemsPerPage) {
      return true;
    }
    // otherwise, no show.
    return false;
  }

  /**
   * View all transactions selected by the user.
   */
  public viewAllSelected(): void {
    alert('View all transactions is not yet supported');
  }

  /**
   * Print all transactions selected by the user.
   */
  public printAllSelected(): void {
    //alert('Print all transactions is not yet supported');
    //console.log('TransactionsTableComponent printAllSelected...!');

    let trxIds = '';
    const selectedTransactions: Array<TransactionModel> = [];
    let unItemizedCount = 0;
    let selectedCount = 0;
    let reportIdSet = new Set();
    //for (const trx of this.transactionsModel) {
    for (const trx of this.selectedFromMultiplePages) {
      if (trx.selected) {
        selectedCount++;
        // remove un-itemized  trxIds here when printing multiple
        reportIdSet.add(trx.reportId);
        
        //if multiple transactions from multiple reports are selected, then do not let them proceed. 
        if(reportIdSet.size > 1){
          this.showMultipleReportsWarn();
          return;
        }
        
        if (trx.itemized && trx.itemized === 'U') {
          unItemizedCount++;
          continue;
        }
        selectedTransactions.push(trx);
        trxIds += trx.transactionId + ', ';
      }
    }
    if ( selectedCount === unItemizedCount ) {
      this.showUnItemizedWarn();
    } else {

      trxIds = trxIds.substr(0, trxIds.length - 2);
      let reportId = null;
      if(reportIdSet && reportIdSet.size === 1){
        reportId = reportIdSet.values().next();
      }
      //this._reportTypeService.signandSaveSubmitReport(this.formType, 'Saved' );
      this._reportTypeService.printPreview('transaction_table_screen', '3X', trxIds, reportId.value);
    }
  }

  public printPreview(): void {
    //console.log('TransactionsTableComponent printPreview...!');

    this._reportTypeService.printPreview('transaction_table_screen', '3X');
  }

  /**
   * Export all transactions selected by the user.
   */
  public exportAllSelected(): void {
    alert('Export all transactions is not yet supported');
  }

  /**
   * Link all transactions selected by the user.
   */
  public linkAllSelected(): void {
    alert('Link multiple transaction requirements have not been finalized');
  }

  /**
   * Trash (send to Recycling Bin) all transactions selected by the user.
   */
  public trashAllSelected(): void {
    let trxIds = '';
    // let iseditable = true;
    let unEditableTypesArray = [];
    let linkedTransactionsArray = [];
    let filedTransactionsArray = [];
    const selectedTransactions: Array<TransactionModel> = [];
    //for (const trx of this.transactionsModel) {
    for (const trx of this.selectedFromMultiplePages) {
      if (trx.selected) {

        //this condition only applies to H1 and H2s
        if (this.transactionCategory === 'other' && !trx.isTrashable) {
          linkedTransactionsArray.push(trx.type);
        }

        if (!trx.iseditable) {
          unEditableTypesArray.push(trx.type);
        }

        if (trx.reportstatus === 'Filed'){
          filedTransactionsArray.push(`${trx.type} - ${trx.reportType}`);
        }
        
        selectedTransactions.push(trx);
        trxIds += trx.transactionId + ', ';
      }
    }

    if (unEditableTypesArray.length > 0 || linkedTransactionsArray.length > 0 || filedTransactionsArray.length > 0) {
      let message = '';
      if (unEditableTypesArray.length > 0) {
        message += "You cannot delete the following selected transaction types because they are auto-generated. ";
        let unEditableTypesSet = new Set(unEditableTypesArray);
        unEditableTypesSet.forEach(transactionType => {
          message += `    \n \u2022 ${transactionType}`;
        });
        message += `\n\n`;
      }

      if (linkedTransactionsArray.length > 0) {
        message += "You cannot delete the following selected transaction types because they are linked to other transactions. Please delete them first.";
        let linkedTransactionsSet = new Set(linkedTransactionsArray);
        linkedTransactionsSet.forEach(transactionType => {
          message += `    \n \u2022 ${transactionType}`;
        });
      } 

      if (filedTransactionsArray.length > 0) {
        message += "You cannot delete the following selected transaction types because the report(s) associated with them are already filed. If you want to change, you must Amend the report.";
        let filedTransactionsSet = new Set(filedTransactionsArray);
        filedTransactionsSet.forEach(transactionType => {
          message += `    \n \u2022 ${transactionType}`;
        });
      } 

      this._dialogService.confirm(
        message,
        ConfirmModalComponent,
        'Error!',
        false,
        ModalHeaderClassEnum.errorHeader
      );
    }
    else {
      trxIds = trxIds.substr(0, trxIds.length - 2);

      this._dialogService
        .confirm('You are about to delete these transactions.   ' + trxIds, ConfirmModalComponent, 'Caution!')
        .then(res => {
          if (res === 'okay') {
            this._transactionsService
              .trashOrRestoreTransactions(this.formType, 'trash', this.reportId, selectedTransactions)
              .subscribe((res: GetTransactionsResponse) => {
                this.getTransactionsPage(this.config.currentPage);

                let afterMessage = '';
                if (selectedTransactions.length === 1) {
                  afterMessage = `Transaction ${selectedTransactions[0].transactionId}
                    has been successfully deleted and sent to the recycle bin.`;
                } else {
                  afterMessage = 'Transactions have been successfully deleted and sent to the recycle bin.   ' + trxIds;
                }

                this._dialogService.confirm(
                  afterMessage,
                  ConfirmModalComponent,
                  'Success!',
                  false,
                  ModalHeaderClassEnum.successHeader
                );
              });

            for(const trx of selectedTransactions) {
              if(trx.scheduleType === 'Schedule H2' ||
                trx.scheduleType === 'Schedule H3' || trx.scheduleType === 'Schedule H4' ||
                trx.scheduleType === 'Schedule H5' || trx.scheduleType === 'Schedule H6') {
                  this._transactionsMessageService.sendRemoveHTransactionsMessage(trx)
                }
            }
          } else if (res === 'cancel') {
          }
        });
    }
  }

  /**
   * Clone the transaction selected by the user.
   *
   * @param trx the Transaction to clone
   */
  public cloneTransaction(trx: TransactionModel): void {
    this._transactionsService
      .cloneTransaction(trx.transactionId)
      .subscribe((cloneTransactionResponse: TransactionModel) => {
        if (cloneTransactionResponse[0] && cloneTransactionResponse[0].hasOwnProperty('transaction_id')) {
          this.getTransactionsPage(this.config.currentPage);
          this.clonedTransaction = cloneTransactionResponse[0];
        }
      });
  }

  /**
   * Link the transaction selected by the user.
   *
   * @param trx the Transaction to link
   */
  public linkTransaction(): void {
    alert('Link requirements have not been finalized');
  }

  /**
   * View the transaction selected by the user.
   *
   * @param trx the Transaction to view
   */
  public viewTransaction(trx: TransactionModel): void {
    //alert('View transaction is not yet supported');
    this._transactionsMessageService.sendViewTransactionMessage(trx);
  }

  /**
   * Edit the transaction selected by the user.
   *
   * @param trx the Transaction to edit
   */
  public editTransaction(trx: TransactionModel): void {
    this._transactionsMessageService.sendEditTransactionMessage(trx);
  }

   /**
   * Reattribute the transaction selected by the user.
   *
   * @param trx the Transaction to edit
   */
  public reattributeTransaction(trx: TransactionModel): void {
    this._transactionsMessageService.sendReattributeTransactionMessage(trx);
  }

  /**
   * Redesignate the transaction selected by the user.
   *
   * @param trx the Transaction to edit
   */
  public redesignateTransaction(trx: TransactionModel): void {
    this._transactionsMessageService.sendRedesignateTransactionMessage(trx);
  }

  public printTransaction(trx: TransactionModel): void {
    if (trx.itemized && (trx.itemized === 'U' || trx.itemized === 'u' )) {
    this.showUnItemizedWarn();
    } else {
      this._reportTypeService.printPreview('transaction_table_screen', '3X', trx.transactionId, trx.reportId);
    }
  }

  /**
   * Trash the transaction selected by the user.
   *
   * @param trx the Transaction to trash
   */
  public trashTransaction(trx: TransactionModel): void {
    this._dialogService
      .confirm('You are about to delete this transaction ' + trx.transactionId + '.', ConfirmModalComponent, 'Caution!')
      .then(res => {
        if (res === 'okay') {
          if (trx.child && trx.child.length > 0) {
            this._dialogService
              .confirm('WARNING: There are child transactions associated with this transaction. This action will delete all child transactions as well. Are you sure you want to continue? ', ConfirmModalComponent, 'Caution!')
              .then(res => {
                this.trashOrRestoreAfterConfirmation(res, trx);
              })
          }
          else {
            this.trashOrRestoreAfterConfirmation(res, trx);
          }
        } else if (res === 'cancel') {
        }
      });
  }

  private trashOrRestoreAfterConfirmation(res: any, trx: TransactionModel) {
    if (res === 'okay') {
      this._transactionsService
        .trashOrRestoreTransactions(this.formType, 'trash', this.reportId, [trx])
        .subscribe((res: GetTransactionsResponse) => {
          this.getTransactionsPage(this.config.currentPage);
          this._dialogService.confirm('Transaction has been successfully deleted and sent to the recycle bin. ' + trx.transactionId, ConfirmModalComponent, 'Success!', false, ModalHeaderClassEnum.successHeader);
        });
      if (trx.scheduleType === 'Schedule H1') {
        this._transactionsMessageService.sendRemoveH1TransactionsMessage(trx);
      }else if(trx.scheduleType === 'Schedule H2' ||
          trx.scheduleType === 'Schedule H3' || trx.scheduleType === 'Schedule H4' ||
          trx.scheduleType === 'Schedule H5' || trx.scheduleType === 'Schedule H6') {
        this._transactionsMessageService.sendRemoveHTransactionsMessage(trx)
      }
    }
    else if (res === 'cancel') {
    }
  }

  public showRow(trx: any, sched: string): boolean {
    let childArray;
    if (trx && trx.entityType === 'ORG' && (trx.transactionTypeIdentifier === 'LOANS_OWED_BY_CMTE' || trx.transactionTypeIdentifier === 'LOANS_OWED_TO_CMTE')) {
      if (trx.child && trx.child.length > 0) {
        childArray = trx.child.filter(element => {
          return element.scheduleType === sched
        });
        if (childArray.length > 0) {
          return true;
        }
      }
    }
    return false;
  }

  /**
   * Restore a trashed transaction from the recyle bin.
   *
   * @param trx the Transaction to restore
   */
  public restoreTransaction(trx: TransactionModel): void {
    this._dialogService
      .confirm('You are about to restore transaction ' + trx.transactionId + '.', ConfirmModalComponent, 'Caution!')
      .then(res => {
        if (res === 'okay') {
          // this._transactionsService.restoreTransaction(trx)
          //   .subscribe((res: GetTransactionsResponse) => {
          this._transactionsService
            .trashOrRestoreTransactions(this.formType, 'restore', this.reportId, [trx])
            .subscribe((res: GetTransactionsResponse) => {
              this.getRecyclingPage(this.config.currentPage);
              this._dialogService.confirm(
                'Transaction ' + trx.transactionId + ' has been restored!',
                ConfirmModalComponent,
                'Success!',
                false,
                ModalHeaderClassEnum.successHeader
              );
            });

          if (trx.scheduleType === 'Schedule H2' ||
              trx.scheduleType === 'Schedule H3' || trx.scheduleType === 'Schedule H4' ||
              trx.scheduleType === 'Schedule H5' || trx.scheduleType === 'Schedule H6') {
            this._transactionsMessageService.sendRestoreTransactionsMessage(trx);
          }
        } else if (res === 'cancel') {
        }
      });
  }

  /**
   * Delete selected transactions from the the recyle bin.
   *
   * @param trx the Transaction to delete
   */
  public deleteRecyleBin(): void {
    let trxIds = '';
    const selectedTransactions: Array<TransactionModel> = [];
    for (const trx of this.transactionsModel) {
      if (trx.selected) {
        selectedTransactions.push(trx);
        trxIds += trx.transactionId + ', ';
      }
    }
    trxIds = trxIds.substr(0, trxIds.length - 2);

    let beforeMessage = '';
    if (selectedTransactions.length === 1) {
      beforeMessage = `Are you sure you want to permanently delete
       Transaction ${selectedTransactions[0].transactionId}?`;
    } else {
      beforeMessage = 'Are you sure you want to permanently delete these transactions?   ' + trxIds;
    }

    this._dialogService.confirm(beforeMessage, ConfirmModalComponent, 'Caution!').then(res => {
      if (res === 'okay') {
        this._transactionsService
          .deleteRecycleBinTransaction(selectedTransactions)
          .subscribe((res: GetTransactionsResponse) => {
            this.getRecyclingPage(this.config.currentPage);

            let afterMessage = '';
            if (selectedTransactions.length === 1) {
              afterMessage = `Transaction ${selectedTransactions[0].transactionId} has been successfully deleted`;
            } else {
              afterMessage = 'Transactions have been successfully deleted.   ' + trxIds;
            }
            this._dialogService.confirm(
              afterMessage,
              ConfirmModalComponent,
              'Success!',
              false,
              ModalHeaderClassEnum.successHeader
            );
          });
      } else if (res === 'cancel') {
      }
    });
  }

  private _setF99Details(): void {
    if (this.committeeDetails) {
      if (this.committeeDetails.committeeid) {
        this._form99Details = this.committeeDetails;

        this._form99Details.reason = '';
        this._form99Details.text = '';
        this._form99Details.signee = `${this.committeeDetails.treasurerfirstname} ${this.committeeDetails.treasurerlastname}`;
        this._form99Details.additional_email_1 = '-';
        this._form99Details.additional_email_2 = '-';
        this._form99Details.created_at = '';
        this._form99Details.is_submitted = false;
        this._form99Details.id = '';

        let formSavedObj: any = {
          saved: false
        };
        localStorage.setItem(`form_99_details`, JSON.stringify(this._form99Details));
        localStorage.setItem(`form_99_saved`, JSON.stringify(formSavedObj));
      }
    }
  }

  public checkIfEditMode(trx: any = null) {
    if (this._authService.isReadOnly()) {
      return;
    }
    this._dialogService
      .confirm(
        'This report has been filed with the FEC. If you want to change, you must Amend the report',
        ConfirmModalComponent,
        'Warning',
        true,
        ModalHeaderClassEnum.warningHeader,
        null,
        'Return to Reports'
      )
      .then(res => {
        if (res === 'okay') {
        } else if (res === 'cancel') {
          this._router.navigate(['/reports']);
        }
      });
  }

  /**
   * Determine the item range shown by the server-side pagination.
   */
  public determineItemRange(): string {
    let start = 0;
    let end = 0;
    // this.numberOfPages = 0;
    this.config.currentPage = this._utilService.isNumber(this.config.currentPage) ? this.config.currentPage : 1;

    if (!this.transactionsModel) {
      return '0';
    }

    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0 && this.transactionsModel.length > 0) {
      // this.calculateNumberOfPages();

      if (this.config.currentPage === this.numberOfPages) {
        // end = this.transactionsModel.length;
        end = this.config.totalItems;
        start = (this.config.currentPage - 1) * this.config.itemsPerPage + 1;
      } else {
        end = this.config.currentPage * this.config.itemsPerPage;
        start = end - this.config.itemsPerPage + 1;
      }
      // // fix issue where last page shown range > total items (e.g. 11-20 of 19).
      // if (end > this.transactionsModel.length) {
      //   end = this.transactionsModel.length;
      // }
    }
    this.firstItemOnPage = start;
    this.lastItemOnPage = end;
    return start + ' - ' + end;
  }
      
  public showPageSizes(): boolean {
    if (this.config && this.config.totalItems && this.config.totalItems > 0){
      return true;
    }
    return false;
  }

  /**
   * Show the option to select/deselect columns in the table.
   */
  public showPinColumns() {
    this.applyDisabledColumnOptions();
    this.columnOptionsModal.show();
  }

  /**
   * Check/Uncheck all transactions in the table.
   */
  public changeAllTransactionsSelected() {
    // TODO Iterating over the trsnactionsModel and setting the selected prop
    // works when we have server-side pagination as the model will only contain
    // transactions for the current page.

    // Until the server is ready for pagination,
    // we are getting the entire set of tranactions (> 500)
    // and must only count and set the selected prop for the items
    // on the current page.

    this.bulkActionCounter = 0;
    for (const t of this.transactionsModel) {
       t.selected = this.allTransactionsSelected;
       if (this.allTransactionsSelected) {
         this.bulkActionCounter++;
       }
    }

    // TODO replace this with the commented code above when server pagination is ready.
    //for (let i = this.firstItemOnPage - 1; i <= this.lastItemOnPage - 1; i++) {
    //  this.transactionsModel[i].selected = this.allTransactionsSelected;
    //  if (this.allTransactionsSelected) {
    //    this.bulkActionCounter++;
    //  }
    //}
    this.bulkActionDisabled = !this.allTransactionsSelected;

    this.selectedForMultiplyPages();
  }

  /**
   * Check if the view to show is Transactions.
   */
  public isTransactionViewActive() {
    return this.tableType === this.transactionsView ? true : false;
  }

  /**
   * Check if the view to show is Recycle Bin.
   */
  public isRecycleBinViewActive() {
    return this.tableType === this.recycleBinView ? true : false;
  }

  /**
   * Check for multiple rows checked in the table
   * and disable/enable the bulk action button
   * accordingly.
   *
   * @param the event payload from the click
   */
  public checkForMultiChecked(e: any, trx :any): void {
    if (e.target.checked) {
      this.bulkActionCounter++;

      if(this.selectedFromMultiplePages
        .filter(obj => obj.transactionId === trx.transactionId).length === 0) {
        this.selectedFromMultiplePages.push(trx);
      }

    } else {
      this.allTransactionsSelected = false;
      if (this.bulkActionCounter > 0) {
        this.bulkActionCounter--;
      }

      this.selectedFromMultiplePages = this.selectedFromMultiplePages
        .filter(obj => obj.transactionId !== trx.transactionId);

    }

    // Transaction View shows bulk action when more than 1 checked
    // Recycle Bin shows delete action when 1 or more checked.
    const count = this.isTransactionViewActive() ? 1 : 0;
    this.bulkActionDisabled = this.bulkActionCounter > count ? false : true;

    this.bulkActionDisabled = this.selectedFromMultiplePages.length > 1 ? false : true;
  }

  /**
   * Determine if transactions may be trashed.
   * Transactions tied to a Filed Report may not be trashed.
   * Since all transactions are tied to a single report,
   * only 1 transaction with a reportstatus of FILED is necessary to check.
   * Loop through the array and if any are filed, none may be trashed.
   *
   * @returns true if Transactions are permitted to be trashed.
   */
  // TODO: in allTransaction table there are multiple reports
  public checkIfTrashable(trx: TransactionModel = null): boolean {
    if (!this.transactionsModel) {
      return false;
    }
    if (this.transactionsModel.length === 0) {
      return false;
    }
    if (trx === null) {
      for (const trxTrash of this.transactionsModel) {
        if (trxTrash.reportstatus.toUpperCase() === 'FILED') {
          return false;
        }
      }
    } else {
      return trx.iseditable;
    }
  }

  /**
   * Get cached values from session.
   */
  private getCachedValues() {
    /* this.applyFiltersCache();
    switch (this.tableType) {
      case this.transactionsView:
        this.applyColCache(this.transactionSortableColumnsLSK);
        this.applyCurrentSortedColCache(this.transactionCurrentSortedColLSK);
        this.applyCurrentPageCache(this.transactionPageLSK);
        break;
      case this.recycleBinView:
        this.applyColCache(this.recycleSortableColumnsLSK);
        this.applyColumnsSelected();
        this.applyCurrentSortedColCache(this.recycleCurrentSortedColLSK);
        this.applyCurrentPageCache(this.recyclePageLSK);
        break;
      default:
        break;
    } */
  }

  /**
   * Columns selected in the PIN dialog from the transactions view
   * need to be applied to the Recycling Bin table.
   */
  private applyColumnsSelected() {
    const key = this.transactionSortableColumnsLSK;
    const sortableColumnsJson: string | null = localStorage.getItem(key);
    if (localStorage.getItem(key) != null) {
      const trxCols: SortableColumnModel[] = JSON.parse(sortableColumnsJson);
      for (const col of trxCols) {
        const columnByName = this._tableService.getColumnByName(col.colName, this.sortableColumns)
        if (columnByName) {
          columnByName.visible = col.visible;
        }
      }
    }
  }

  /**
   * Apply the filters from the cache.
   */
  private applyFiltersCache() {
    const filtersJson: string | null = localStorage.getItem(this.filtersLSK);
    if (filtersJson != null) {
      this.filters = JSON.parse(filtersJson);
    } else {
      // Just in case cache has an unexpected issue, use default.
      this.filters = null;
    }
  }

  /**
   * Get the column and their settings from the cache and apply it to the component.
   * @param key the key to the value in the local storage cache
   */
  private applyColCache(key: string) {
    const sortableColumnsJson: string | null = localStorage.getItem(key);
    if (localStorage.getItem(key) != null) {
      this.sortableColumns = JSON.parse(sortableColumnsJson);
    } else {
      // Just in case cache has an unexpected issue, use default.
      this.setSortableColumns();
    }
  }

  /**
   * Get the current sorted column from the cache and apply it to the component.
   * @param key the key to the value in the local storage cache
   */
  private applyCurrentSortedColCache(key: string) {
    const currentSortedColumnJson: string | null = localStorage.getItem(key);
    let currentSortedColumnL: SortableColumnModel = null;
    if (currentSortedColumnJson) {
      currentSortedColumnL = JSON.parse(currentSortedColumnJson);

      // sort by the column direction previously set
      this.currentSortedColumnName = this._tableService.setSortDirection(
        currentSortedColumnL.colName,
        this.sortableColumns,
        currentSortedColumnL.descending
      );
    } else {
      this.setSortDefault();
    }
  }

  /**
   * Get the current page from the cache and apply it to the component.
   * @param key the key to the value in the local storage cache
   */
  private applyCurrentPageCache(key: string) {
    const currentPageCache: string = localStorage.getItem(key);
    if (currentPageCache) {
      if (this._utilService.isNumber(currentPageCache)) {
        this.config.currentPage = this._utilService.toInteger(currentPageCache);
      } else {
        this.config.currentPage = 1;
      }
    } else {
      this.config.currentPage = 1;
    }
  }

  /**
   * Retrieve the cahce values from local storage and set the
   * component's class variables.
   */
  private setCachedValues() {
    /* switch (this.tableType) {
      case this.transactionsView:
        this.setCacheValuesforView(
          this.transactionSortableColumnsLSK,
          this.transactionCurrentSortedColLSK,
          this.transactionPageLSK
        );
        break;
      case this.recycleBinView:
        this.setCacheValuesforView(
          this.recycleSortableColumnsLSK,
          this.recycleCurrentSortedColLSK,
          this.recyclePageLSK
        );
        break;
      default:
        break;
    } */
  }

  /**
   * Set the currently sorted column and current page in the cache.
   *
   * @param columnsKey the column settings key for the cache
   * @param sortedColKey currently sorted column key for the cache
   * @param pageKey current page key from the cache
   */
  private setCacheValuesforView(columnsKey: string, sortedColKey: string, pageKey: string) {
    // shared between trx and recycle tables
    localStorage.setItem(columnsKey, JSON.stringify(this.sortableColumns));

    // shared between trx and recycle tables
    localStorage.setItem(this.filtersLSK, JSON.stringify(this.filters));

    const currentSortedCol = this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);
    localStorage.setItem(sortedColKey, JSON.stringify(this.sortableColumns));

    if (currentSortedCol) {
      localStorage.setItem(sortedColKey, JSON.stringify(currentSortedCol));
    }
    localStorage.setItem(pageKey, this.config.currentPage.toString());
  }

  /**
   * Set the Table Columns model.
   */
  private setSortableColumns(): void {
    let defaultSortColumns = ['reportType','type', 'name', 'date', 'memoCode', 'amount', 'aggregate'];
    let otherSortColumns = [
      'transactionId',
      'street',
      'city',
      'state',
      'zip',
      'purposeDescription',
      'contributorEmployer',
      'contributorOccupation',
      'memoText'
    ];
    if (this.transactionCategory === 'disbursements') {
      defaultSortColumns = ['reportType','type', 'name', 'date', 'memoCode', 'amount', 'purposeDescription'];
      otherSortColumns = [
        'transactionId',
        'street',
        'city',
        'state',
        'zip',
        'memoText',
        'committeeId',
        'electionCode',
        'electionYear'
      ];
    } else if (this.transactionCategory === 'loans-and-debts') {
      defaultSortColumns = ['reportType','type', 'name', 'loanClosingBalance', 'loanIncurredDate'];
      otherSortColumns = [
        'transactionId',
        'street',
        'city',
        'state',
        'zip',
        'memoCode',
        'memoText',
        'purposeDescription',
        'loanBeginningBalance',
        'loanAmount',
        'loanDueDate',
        'loanIncurredAmt',
        'loanPaymentAmt',
        'loanPaymentToDate'
      ];
    } else if (this.transactionCategory === 'other') {
      defaultSortColumns = ['reportType','schedule', 'type', 'name', 'amount', 'date', 'memoCode', 'purposeDescription'];
      otherSortColumns = ['transactionId', 'street', 'city', 'state', 'zip', 'memoText', 'eventId'];
    }

    this.sortableColumns = [];
    for (const field of defaultSortColumns) {
      this.sortableColumns.push(new SortableColumnModel(field, false, true, true, false));
    }
    for (const field of otherSortColumns) {
      this.sortableColumns.push(new SortableColumnModel(field, false, false, false, true));
    }
    this.sortableColumns.push(new SortableColumnModel('deletedDate', false, true, false, false));
  }

  /**
   * Set the UI to show the default column sorted in the default direction.
   */
  private setSortDefault(): void {
    // When default, the backend will sort by name and transaction date
    this.currentSortedColumnName = 'default';
  }

  private calculateNumberOfPages(): void {
    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0) {
      if (this.transactionsModel && this.transactionsModel.length > 0) {
        this.numberOfPages = this.transactionsModel.length / this.config.itemsPerPage;
        this.numberOfPages = Math.ceil(this.numberOfPages);
      }
    }
  }

  public goToC1(trx: any) {
    trx.scheduleType = 'sched_c1';
    this.editTransaction(trx);
  }

  public goToEndorsersSummary(trx: any) {
    trx.scheduleType = "sched_c_es";
    trx.endorser = { back_ref_transaction_id: trx.transactionId };
    this.editTransaction(trx);
  }

  public goToLoanRepayment(trx: any) {
    trx.scheduleType = "sched_c_loan_payment"
    trx.backRefTransactionId = trx.transactionId;
    this.editTransaction(trx);
  }

  public goToDebtPayment(trx: any) {
    trx.scrollDebtPaymentButtonIntoView = true;
    this.editTransaction(trx);
  }

  private showUnItemizedWarn() {
    const WARN_MESSAGE = 'Unitemized Transactions will not be included in your report. Therefore, the transactions are not available for' +
        ' Print Preview';
    this._dialogService
        .confirm(WARN_MESSAGE , ConfirmModalComponent, 'Warning!', false)
        .then(res => {
          if (res === 'okay') {
          }
        });
  }

  private showMultipleReportsWarn() {
    const WARN_MESSAGE = 'Print functionality is not available for transactions from multiple reports. Please select all transacitons from the same report. ';
    this._dialogService
        .confirm(WARN_MESSAGE , ConfirmModalComponent, 'Error!', false)
        .then(res => {
          if (res === 'okay') {
          }
        });
  }

  private isPrintable(trx: any) {
    if (trx.itemized && trx.itemized === 'U' )  {
      return false;
    } else { return true; }
  }

  private isIKOUT(trx: any) {
    if(trx.transactionTypeIdentifier === 'IK_OUT' ||
      trx.transactionTypeIdentifier === 'PARTY_IK_OUT' ||
      trx.transactionTypeIdentifier === 'PAC_IK_OUT' ||
      trx.transactionTypeIdentifier === 'IK_BC_OUT' ||
      trx.transactionTypeIdentifier === 'PAC_IK_BC_OUT' ||
      trx.transactionTypeIdentifier === 'IK_TRAN_OUT' ||
      trx.transactionTypeIdentifier === 'IK_TRAN_FEA_OUT' ||
      trx.transactionTypeIdentifier === 'PARTY_IK_BC_OUT') {
        return true;
      }else {
        return false;
      }
  }

  private isForceItemizable(trx: TransactionModel): boolean {
    if (!this.editMode && !this._allTransactions) {
      return false;
    }
    if (trx) {
      if (trx.reportstatus.toUpperCase() === 'FILED') {
        return (trx.forceitemizable && trx.iseditable);
      }
      return trx.forceitemizable;
    } else {
      return false;
    }
  }

  private forceItemizationToggle(trx: TransactionModel): void {

    this._reportTypeService.forceItemizationToggle(trx).subscribe(res => {
      // on response reload the transaction table to get latest data
      this.apiError = false;
      this.getTransactionsPage(this.config.currentPage);

    }, error => {
      console.error('Error Toggling Itemization ');
      this.apiError = true;
    });
  }

  private getItemizationInd(trx: TransactionModel): string {
    return this.getCurrentItemizationStatus(trx) ? ' Unitemize' : ' Itemize';
  }
  private getCurrentItemizationStatus(trx: TransactionModel): boolean {
    if (trx && trx.itemized) {
      if (trx.itemized === 'U' || trx.itemized === 'FU') {
        return false;
      } else if (trx.itemized === 'FI' || trx.itemized === 'I') {
        return true;
      }
    } else {
      return true;
    }
  }

  private setSelectedForMultiplyPages() {
    for (
      let transactionModelIndex = 0;
      transactionModelIndex < this.transactionsModel.length;
      transactionModelIndex++
    ) {
      for(const trxMultPages of this.selectedFromMultiplePages) {
        if(trxMultPages.transactionId === this.transactionsModel[transactionModelIndex].transactionId && trxMultPages.selected)
        {
          this.transactionsModel[transactionModelIndex].selected = true;
        }
      }
    }

    this.bulkActionDisabled = this.selectedFromMultiplePages.length > 1 ? false : true;
  }

  private selectedForMultiplyPages() {
    for(
      let transactionModelIndex = 0;
      transactionModelIndex < this.transactionsModel.length;
      transactionModelIndex++
    ) {
      if(this.allTransactionsSelected) {
        if(this.selectedFromMultiplePages.filter(obj => obj.transactionId ===
              this.transactionsModel[transactionModelIndex].transactionId).length === 0)
        {
          this.selectedFromMultiplePages.push(this.transactionsModel[transactionModelIndex]);
        }

      }else {
        this.selectedFromMultiplePages = this.selectedFromMultiplePages.filter
          (obj => obj.transactionId !== this.transactionsModel[transactionModelIndex].transactionId);

        this.setSelectedForMultiplyPages();
      }
    }
  }

  /**
   * enables/disables edit/clone/trash actions on a transaction
   * @param trx
   * @return {boolean} true disabled trx action else false
   */
  private isDisabled(trx: TransactionModel): boolean {
    if (trx && trx.reportstatus) {
    return !trx.iseditable;
    } else {
      return true;
    }
  }
}
