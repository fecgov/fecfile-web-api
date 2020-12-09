import { UtilService } from 'src/app/shared/utils/util.service';
import { Component, EventEmitter, OnDestroy, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs/Subscription';
import { ReportsService } from 'src/app/reports/service/report.service';
import { ModalHeaderClassEnum } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { ReportTypeService } from '../../forms/form-3x/report-type/report-type.service';
import { TransactionTypeService } from '../../forms/form-3x/transaction-type/transaction-type.service';
import { ConfirmModalComponent } from '../../shared/partials/confirm-modal/confirm-modal.component';
import { IndividualReceiptService } from '../form-3x/individual-receipt/individual-receipt.service';
import { ScheduleActions } from '../form-3x/individual-receipt/schedule-actions.enum';
import { F3xMessageService } from '../form-3x/service/f3x-message.service';
import { FilterTypes } from './enums/filterTypes.enum';
import { TransactionFilterModel } from './model/transaction-filter.model';
import { TransactionModel } from './model/transaction.model';
import { TransactionsMessageService } from './service/transactions-message.service';

export enum ActiveView {
  transactions = 'transactions',
  recycleBin = 'recycleBin',
  edit = 'edit'
}

/**
 * The parent component for transactions.
 */
@Component({
  selector: 'app-transactions',
  templateUrl: './transactions.component.html',
  styleUrls: ['./transactions.component.scss'],
  encapsulation: ViewEncapsulation.None,
  /* animations: [
    trigger('fadeInOut', [
      transition(':enter', [style({ opacity: 0 }), animate(500, style({ opacity: 1 }))]),
      transition(':leave', [animate(10, style({ opacity: 0 }))])
    ])
  ] */
})
export class TransactionsComponent implements OnInit, OnDestroy {
  @Output() sidebarSwitch: EventEmitter<any> = new EventEmitter<any>();
  @Output() showTransaction: EventEmitter<any> = new EventEmitter<any>();

  public formType = '';
  public reportId = '0';
  public routeData: any;
  public previousReportId = '0';
  public view: ActiveView = ActiveView.transactions;
  public transactionsView = ActiveView.transactions;
  public recycleBinView = ActiveView.recycleBin;
  public editView = ActiveView.edit;
  public isShowFilters = false;
  public searchText = '';
  public searchTextArray = [];
  public tagArray: any = [];
  public transactionCategories: any = [];
  public showEditTransaction = false;

  public searchInputClass:string = '';

  public currentStep: string = 'step_1';
  public step: string = '';
  public steps: any = {};
  public frm: any;
  public direction: string;
  public previousStep: string = '';
  public parentTransactionCategories: any = [];
  public reportsLoading: boolean = true;
  public reportTypes: any = [];
  public reportTypeIndicator: any = {};
  public reportType: any = null;
  public selectedReportType: any = {};
  public selectedReport: any = null;
  public regularReports: boolean = false;
  public specialReports: boolean = false;
  public selectedReportInfo: any = {};
  public transactionCategory: string = '';
  public transactionTypeText = '';

  public allTransactions: boolean = false;

  private _step: string = '';
  private _formType: string = '';

  /**
   * Subscription for applying filters to the transactions obtained from
   * the server.
   */
  private applyFiltersSubscription: Subscription;

  /**
   * Subscription for showing the TransactionsEditComponent.
   */
  private editTransactionSubscription: Subscription;

  /**
   * Subscription for transactions to return to Debt Summary
   */
  private editDebtSummaryTransactionSubscription: Subscription;
  
  private removeFiltersSubscription: Subscription;

  /**
   * Subscription for showing all Transactions.
   */
  private showTransactionsSubscription: Subscription;

  public transactionToEdit: TransactionModel;

  private filters: TransactionFilterModel = new TransactionFilterModel();
  private readonly filtersLSK = 'transactions.filters';
  removeTagsSubscription: any;

  private viewTransactionSubscription: Subscription;
  private getReattributeTransactionSubscription: Subscription;
  private getRedesignateTransactionSubscription: Subscription;
  activatedRouteSubscription: Subscription;
  getMessageSubscription: Subscription;

  constructor(
    private _activatedRoute: ActivatedRoute,
    private _transactionsMessageService: TransactionsMessageService,
    private _transactionTypeService: TransactionTypeService,
    private _reportTypeService: ReportTypeService,
    private _router: Router,
    private _fb: FormBuilder,
    private _f3xMessageService: F3xMessageService,
    private _receiptService: IndividualReceiptService,
    private _messageService: MessageService,
    private _dialogService: DialogService,
    private _reportsService: ReportsService, 
    private _utilService: UtilService
  ) {

    this.formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.applyFiltersSubscription = this._transactionsMessageService
      .getApplyFiltersMessage()
      .subscribe((message: any) => {
        this.determineTags(message);

        if (message.isClearKeyword) {
          this.clearSearch();
        } else {
          this.doSearch();
        }
      });

    this.removeTagsSubscription = this._transactionsMessageService.getRemoveTagMessage()
      .subscribe((message: any) => {
        this.removeTagArrayItem(message.type);
      });

    this.editTransactionSubscription = this._transactionsMessageService
      .getEditTransactionMessage()
      .subscribe((trx: TransactionModel) => {
        this.transactionToEdit = trx;
        //console.log(trx.transactionTypeIdentifier + 'identifier for edit');
        this.showEdit();
      });

    this.getReattributeTransactionSubscription = this._transactionsMessageService
    .getReattributeTransactionMessage()
    .subscribe((trx: TransactionModel) => {
      this.transactionToEdit = trx;
      //console.log(trx.transactionTypeIdentifier + 'identifier for edit');
      this.showReattribute();
    });

    this.getRedesignateTransactionSubscription = this._transactionsMessageService
    .getRedesignateTransactionMessage()
    .subscribe((trx: TransactionModel) => {
      this.transactionToEdit = trx;
      //console.log(trx.transactionTypeIdentifier + 'identifier for edit');
      this.showRedesignate();
    });

    this.editDebtSummaryTransactionSubscription = this._transactionsMessageService
      .getEditDebtSummaryTransactionMessage()
      .subscribe((message: any) => {
        this.transactionToEdit = message.trx;
        this.showEdit(message.debtSummary);
      });

    this.showTransactionsSubscription = this._transactionsMessageService
      .getShowTransactionsMessage()
      .subscribe(message => {
        this.showTransactions();
      });

      this.activatedRouteSubscription = _activatedRoute.queryParams.subscribe(p => {
        this.transactionCategory = this._utilService.convertTransactionCategoryByForm(p.transactionCategory,this.formType);
        
      });

    this.viewTransactionSubscription = this._transactionsMessageService
      .getViewTransactionMessage()
      .subscribe((trx: TransactionModel) => {
        this.transactionToEdit = trx;
        this.showView();
      });

    this.getMessageSubscription = this._messageService.getMessage().subscribe(message => {
        if(message && message.action === 'clearGlobalAllTransactionsFlag'){
          this.allTransactions = false;
        }
        
      }); 
    }

  private removeFilterAndTag(message: any) {
    if (message.filterName === 'deletedDate') {
      this.removeDeletedDateFilter();
    }
  }

  /**
   * Initialize the component.
   */
  public ngOnInit(): void {
    this.showEditTransaction = false;
    if(this._activatedRoute.snapshot.queryParams.searchTransactions){
      this.searchInputClass = 'searchHighlight';
    }
    else{
      this.searchInputClass = '';
    }
    // this.formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.reportId = this._activatedRoute.snapshot.paramMap.get('report_id');
    const reportIdRoute = this._activatedRoute.snapshot.paramMap.get('report_id');
    this._step = this._activatedRoute.snapshot.paramMap.get('step');
    this.allTransactions = this._activatedRoute.snapshot.queryParams.allTransactions;

    //console.log('TransactionsComponent this._step', this._step);
    this.routeData = { accessedByRoute: true, formType: this.formType, reportId: reportIdRoute };

    //console.log('TransactionsComponent this._step', this._step);

    localStorage.removeItem(`form_${this.formType}_view_transaction_screen`);

    this._transactionTypeService.getTransactionCategories("F"+this.formType).subscribe(res => {
      if (res) {
        this.transactionCategories = res.data.transactionCategories;

        //console.log('this.transactionCategories: ', this.transactionCategories);
      }
    });

    // If the filter was open on the last visit in the user session, open it.
    const filtersJson: string | null = localStorage.getItem(this.filtersLSK);
    let filters: TransactionFilterModel;
    if (filtersJson !== null && filtersJson !== 'null') {
      filters = JSON.parse(filtersJson);
      if (filters) {
        if (filters.keywords) {
          if (filters.keywords.length > 0) {
            this.searchTextArray = filters.keywords;
            filters.show = true;
          }
        }
      }
    } else {
      filters = new TransactionFilterModel();
    }
    if (filters.show === true) {
      this.showFilters();
    }

  }

  public ngDoCheck(): void {
    this.reportId = this._activatedRoute.snapshot.queryParams.reportId;
    if (!this.reportId) {
      return;
    }
    if (this.reportId === '0') {
      return;
    }
    if (this.reportId === this.previousReportId) {
      return;
    }
    this.previousReportId = this.reportId;
    this._receiptService.getSchedule(this._formType, { report_id: this.reportId }).subscribe(resp => {
      const message: any = {
        formType: this.formType,
        totals: resp
      };

      this._messageService.sendMessage(message);
    });
  }

  /**
   * A method to run when component is destroyed.
   */
  public ngOnDestroy(): void {
    localStorage.removeItem('Transaction_Table_Screen');
    localStorage.removeItem(`form_${this.formType}_view_transaction_screen`);
    this.applyFiltersSubscription.unsubscribe();
    this.removeTagsSubscription.unsubscribe();
    this.editTransactionSubscription.unsubscribe();
    this.editDebtSummaryTransactionSubscription.unsubscribe();
    this.showTransactionsSubscription.unsubscribe();
    this.viewTransactionSubscription.unsubscribe();
    this.getRedesignateTransactionSubscription.unsubscribe();
    this.getReattributeTransactionSubscription.unsubscribe();
    this.getMessageSubscription.unsubscribe();
    this.activatedRouteSubscription.unsubscribe();
    localStorage.removeItem('transactions.filters');
  }

  public goToPreviousStep(): void {
    this._router.navigate([`/forms/form/${this.formType}`], {
      queryParams: { step: 'step_3' }
    });
  }

  /**
   * Based on the filter settings and search string, determine the "tags" to show.
   */
  private determineTags(message: any) {
    const filters = (this.filters = message.filters);

    // new and changed added filters should go at the end.
    // unchanged should appear in the beginning.

    if (filters.filterCategories.length > 0) {
      const categoryGroup = [];

      // is tag showing? Then modify it is the curr position
      let categoryTag = false;
      for (const tag of this.tagArray) {
        if (tag.type === FilterTypes.category) {
          categoryTag = true;
          for (const cat of filters.filterCategories) {
            categoryGroup.push(cat);
          }
          tag.group = categoryGroup;
        }
      }
      // If tag is not already showing, add it to the tag array.
      if (!categoryTag) {
        for (const cat of filters.filterCategories) {
          categoryGroup.push(cat);
        }
        this.tagArray.push({ type: FilterTypes.category, prefix: 'Type', group: categoryGroup });
      }
    } else {
      this.removeTagArrayItem(FilterTypes.category);
    }

    // Date
    if (filters.filterDateFrom && filters.filterDateTo) {
      const dateGroup = [];
      dateGroup.push({
        filterDateFrom: filters.filterDateFrom,
        filterDateTo: filters.filterDateTo
      });
      // is tag showing? Then modify it is the curr position
      let dateTag = false;
      for (const tag of this.tagArray) {
        if (tag.type === FilterTypes.date) {
          dateTag = true;
          tag.group = dateGroup;
        }
      }
      if (!dateTag) {
        this.tagArray.push({ type: FilterTypes.date, prefix: 'Date', group: dateGroup });
      }
    }

    // Date
    if (filters.filterDeletedDateFrom && filters.filterDeletedDateTo) {
      const dateGroup = [];
      dateGroup.push({
        filterDeletedDateFrom: filters.filterDeletedDateFrom,
        filterDeletedDateTo: filters.filterDeletedDateTo
      });
      // is tag showing? Then modify it is the curr position
      let deletedDateTag = false;
      for (const tag of this.tagArray) {
        if (tag.type === FilterTypes.deletedDate) {
          deletedDateTag = true;
          tag.group = dateGroup;
        }
      }
      if (!deletedDateTag) {
        this.tagArray.push({ type: FilterTypes.deletedDate, prefix: 'Deleted Date', group: dateGroup });
      }
    }

    // Amount
    if (this._isNotNullorUndefined(filters.filterAmountMin) && this._isNotNullorUndefined(filters.filterAmountMax)) {
      const amountGroup = [];
      amountGroup.push({
        filterAmountMin: filters.filterAmountMin,
        filterAmountMax: filters.filterAmountMax
      });
      let amtTag = false;
      for (const tag of this.tagArray) {
        if (tag.type === FilterTypes.amount) {
          amtTag = true;
          tag.group = amountGroup;
        }
      }
      if (!amtTag) {
        this.tagArray.push({ type: FilterTypes.amount, prefix: 'Amount', group: amountGroup });
      }
    }

    // Aggregate Amount
    if (this._isNotNullorUndefined(filters.filterAggregateAmountMin) && this._isNotNullorUndefined(filters.filterAggregateAmountMax)) {
      const amountGroup = [];
      amountGroup.push({
        filterAggregateAmountMin: filters.filterAggregateAmountMin,
        filterAggregateAmountMax: filters.filterAggregateAmountMax
      });
      let amtTag = false;
      for (const tag of this.tagArray) {
        if (tag.type === FilterTypes.aggregateAmount) {
          amtTag = true;
          tag.group = amountGroup;
        }
      }
      if (!amtTag) {
        this.tagArray.push({ type: FilterTypes.aggregateAmount, prefix: 'Aggregate Amount', group: amountGroup });
      }
    }

    // Loan Amount
    if (this._isNotNullorUndefined(filters.filterLoanAmountMin) && this._isNotNullorUndefined(filters.filterLoanAmountMax)) {
      const amountGroup = [];
      amountGroup.push({
        filterLoanAmountMin: filters.filterLoanAmountMin,
        filterLoanAmountMax: filters.filterLoanAmountMax
      });
      let amtTag = false;
      for (const tag of this.tagArray) {
        if (tag.type === FilterTypes.loanAmount) {
          amtTag = true;
          tag.group = amountGroup;
        }
      }
      if (!amtTag) {
        this.tagArray.push({ type: FilterTypes.loanAmount, prefix: 'Loan Amount', group: amountGroup });
      }
    }

    // Closing loan balance
    if (this._isNotNullorUndefined(filters.filterLoanClosingBalanceMin) && this._isNotNullorUndefined(filters.filterLoanClosingBalanceMax)) {
      const amountGroup = [];
      amountGroup.push({
        filterLoanClosingBalanceMin: filters.filterLoanClosingBalanceMin,
        filterLoanClosingBalanceMax: filters.filterLoanClosingBalanceMax
      });
      let amtTag = false;
      for (const tag of this.tagArray) {
        if (tag.type === FilterTypes.loanClosingBalance) {
          amtTag = true;
          tag.group = amountGroup;
        }
      }
      if (!amtTag) {
        this.tagArray.push({ type: FilterTypes.loanClosingBalance, prefix: 'Balance at close', group: amountGroup });
      }
    }

    // State
    if (this.filters.filterStates.length > 0) {
      const stateGroup = [];

      // is tag showing? Then modify it is the curr position
      // TODO put type strings in constants file as an enumeration
      // They are also used in the filter component as well.

      let stateTag = false;
      for (const tag of this.tagArray) {
        if (tag.type === FilterTypes.state) {
          stateTag = true;
          for (const cat of filters.filterStates) {
            stateGroup.push(cat);
          }
          tag.group = stateGroup;
        }
      }
      // If tag is not already showing, add it to the tag array.
      if (!stateTag) {
        for (const cat of filters.filterStates) {
          stateGroup.push(cat);
        }
        this.tagArray.push({ type: FilterTypes.state, prefix: null, group: stateGroup });
      }
    } else {
      this.removeTagArrayItem(FilterTypes.state);
    }

    // Memo Code
    if (this.filters.filterMemoCode) {
      // if memo tag showing, do nothing.  If not showing, add it.
      let memoTag = false;
      for (const tag of this.tagArray) {
        if (tag.type === FilterTypes.memoCode) {
          memoTag = true;
          break;
        }
      }
      if (!memoTag) {
        this.tagArray.push({ type: FilterTypes.memoCode, prefix: null, group: ['Memo Code'] });
      }
    }

    // Itemizations
    if (this.filters.filterItemizations) {
      if (this.filters.filterItemizations.length > 0) {
        const itemizedGroup = [];

        // is tag showing? Then modify it is the curr position
        // TODO put type strings in constants file as an enumeration
        // They are also used in the filter component as well.

        let itemizedTag = false;
        for (const tag of this.tagArray) {
          if (tag.type === FilterTypes.itemizations) {
            itemizedTag = true;
            for (const item of filters.filterItemizations) {
              itemizedGroup.push(item);
            }
            tag.group = itemizedGroup;
          }
        }
        // If tag is not already showing, add it to the tag array.
        if (!itemizedTag) {
          for (const item of filters.filterItemizations) {
            itemizedGroup.push(item);
          }
          this.tagArray.push({ type: FilterTypes.itemizations, prefix: 'Itemized', group: itemizedGroup });
        }
      } else {
        this.removeTagArrayItem(FilterTypes.itemizations);
      }
    }

    // Election codes
    if (this.filters.filterElectionCodes) {
      if (this.filters.filterElectionCodes.length > 0) {
        const electionCodesGroup = [];

        // is tag showing? Then modify it is the curr position
        // TODO put type strings in constants file as an enumeration
        // They are also used in the filter component as well.

        let electionsTag = false;
        for (const tag of this.tagArray) {
          if (tag.type === FilterTypes.electionCodes) {
            electionsTag = true;
            for (const item of filters.filterElectionCodes) {
              electionCodesGroup.push(item);
            }
            tag.group = electionCodesGroup;
          }
        }
        // If tag is not already showing, add it to the tag array.
        if (!electionsTag) {
          for (const item of filters.filterElectionCodes) {
            electionCodesGroup.push(item);
          }
          this.tagArray.push({ type: FilterTypes.electionCodes, prefix: 'Election code', group: electionCodesGroup });
        }
      } else {
        this.removeTagArrayItem(FilterTypes.electionCodes);
      }
    }

    // Election year
    if (this.filters.filterElectionYearFrom && this.filters.filterElectionYearTo) {
      const filterYearGroup = [];
      filterYearGroup.push({
        filterElectionYearFrom: filters.filterElectionYearFrom,
        filterElectionYearTo: filters.filterElectionYearTo
      });
      let filterYearTag = false;
      for (const tag of this.tagArray) {
        if (tag.type === FilterTypes.electionYear) {
          filterYearTag = true;
          tag.group = filterYearGroup;
        }
      }
      if (!filterYearTag) {
        this.tagArray.push({ type: FilterTypes.electionYear, prefix: 'Election year', group: filterYearGroup });
      }
    }

    // Schedule
    if (this.filters.filterSchedule) {
      // if memo tag showing, do nothing.  If not showing, add it.
      let scheduleTag = false;
      const scheduleGroup = [];
      for (const tag of this.tagArray) {
        if (tag.type === FilterTypes.schedule) {
          scheduleTag = true;
          scheduleGroup.push(filters.filterSchedule);
          break;
        }
      }
      if (!scheduleTag) {
        this.tagArray.push({ type: FilterTypes.schedule, prefix: 'Schedule', group: scheduleGroup });
      }
    }

    //console.log('tagArray: ' + JSON.stringify(this.tagArray));

    this.filters = filters;
  }

  /**
   * Search transactions.
   */
  public search() {

    this.searchInputClass = '';
    // Don't allow more than 12 filters
    if (this.searchTextArray.length > 12) {
      return;
    }

    // TODO emit search message to the table transactions component
    if (this.searchText) {
      this.searchTextArray.push(this.searchText);
      this.tagArray.push({ type: FilterTypes.keyword, prefix: null, group: [this.searchText] });
      this.searchText = '';
    }
    this.doSearch();
    this.showFilters();
  }

  /**
   * Clear the keyword search items
   */
  public clearSearch() {
    this.searchTextArray = [];
    this.tagArray = [];
    this.searchText = '';
    this.doSearch();
  }

  /**
   * Clear the keyword search items
   */
  public clearSearchAndFilters() {
    // send a message to remove the filters from UI.
    this._transactionsMessageService.sendRemoveFilterMessage({ removeAll: true });

    // And reset the filter model for the search.
    this.filters = new TransactionFilterModel();

    // then clear the keywords and run the search without filters or search keywords.
    this.clearSearch();
  }

  /**
   * Remove the search text from the array.
   *
   * @param index index in the array
   */
  public removeSearchText(tagText: string) {
    const index = this.searchTextArray.indexOf(tagText);
    if (index !== -1) {
      this.searchTextArray.splice(index, 1);
      this.doSearch();
    }
  }

  /**
   * Remove the state filter tag and inform the filter component to clear it.
   */
  public removeStateFilter(index: number, state: string) {
    this.filters.filterStates.splice(index, 1);
    this.removeFilter(FilterTypes.state, state);
  }

  /**
   * Remove the State filter tag and inform the filter component to clear it.
   */
  public removeCategoryFilter(index: number, category: string) {
    this.filters.filterCategories.splice(index, 1);
    this.removeFilter(FilterTypes.category, category);
  }

  /**
   * Remove the Date filter tag and inform the filter component to clear it.
   */
  public removeDateFilter() {
    this.filters.filterDateFrom = null;
    this.filters.filterDateTo = null;
    this.removeFilter('date', null);
  }

  /**
   * Remove the Date filter tag and inform the filter component to clear it.
   */
  public removeDeletedDateFilter() {
    this.filters.filterDeletedDateFrom = null;
    this.filters.filterDeletedDateTo = null;
    this.removeFilter('deletedDate', null);
  }

  /**
   * Remove the Amount filter tag and inform the filter component to clear it.
   */
  public removeAmountFilter() {
    this.filters.filterAmountMin = null;
    this.filters.filterAmountMax = null;
    this.removeFilter(FilterTypes.amount, null);
  }

  /**
   * Remove the Aggregate Amount filter tag and inform the filter component to clear it.
   */
  public removeAggregateAmountFilter() {
    this.filters.filterAggregateAmountMin = null;
    this.filters.filterAggregateAmountMax = null;
    this.removeFilter(FilterTypes.aggregateAmount, null);
  }

  /**
   * Remove the Loan Closing Balance filter tag and inform the filter component to clear it.
   */
  public removeLoanClosingBalanceFilter() {
    this.filters.filterLoanClosingBalanceMin = null;
    this.filters.filterLoanClosingBalanceMax = null;
    this.removeFilter(FilterTypes.loanClosingBalance, null);
  }

  /**
   * Remove the Loan Amount filter tag and inform the filter component to clear it.
   */
  public removeLoanAmountFilter() {
    this.filters.filterLoanAmountMin = null;
    this.filters.filterLoanAmountMax = null;
    this.removeFilter(FilterTypes.loanAmount, null);
  }

  public removeMemoFilter() {
    this.filters.filterMemoCode = false;
    this.removeFilter(FilterTypes.memoCode, null);
  }

  /**
   * Remove the Itemized filter tag and inform the filter component to clear it.
   */
  public removeItemizationsFilter(index: number, item: string) {
    this.filters.filterItemizations.splice(index, 1);
    this.removeFilter(FilterTypes.itemizations, item);
  }

  /**
   * Remove the election codes filter tag and inform the filter component to clear it.
   */
  public removeElectionCodesFilter(index: number, item: string) {
    this.filters.filterElectionCodes.splice(index, 1);
    this.removeFilter(FilterTypes.electionCodes, item);
  }

  /**
   * Remove the election year filter tag and inform the filter component to clear it.
   */
  public removeElectionYearFilter() {
    this.filters.filterElectionYearFrom = null;
    this.filters.filterElectionYearTo = null;
    this.removeFilter(FilterTypes.electionYear, null);
  }

  /**
   * Remove the schedule filter tag and inform the filter component to clear it.
   */
  public removeScheduleFilter() {
    this.filters.filterSchedule = null;
    this.removeFilter(FilterTypes.schedule, null);
  }

  /**
   * Inform the Filter Component to clear the filter settings for the given key/value.
   *
   * @param key
   * @param value
   */
  private removeFilter(key: string, value: string) {
    this._transactionsMessageService.sendRemoveFilterMessage({ key: key, value: value });
    this.doSearch();
  }

  /**
   * When a user clicks the close filter tag, delete the tag from the
   * tagsArray and inform the filter component to reset the filter setting.
   *
   * @param type filter type
   * @param index position in the array if the filter type can have multiples
   * @param tagText the text displayed on the tag
   */
  public removeTag(type: FilterTypes, index: number, tagText: string) {
    switch (type) {
      case FilterTypes.category:
        this.removeCategoryFilter(index, tagText);
        this.removeTagArrayGroupItem(type, index);
        break;
      case FilterTypes.state:
        this.removeStateFilter(index, tagText);
        this.removeTagArrayGroupItem(type, index);
        break;
      case FilterTypes.date:
        this.removeDateFilter();
        this.removeTagArrayItem(type);
        break;
      case FilterTypes.deletedDate:
          this.removeDeletedDateFilter();
          this.removeTagArrayItem(type);
          break;
      case FilterTypes.amount:
        this.removeAmountFilter();
        this.removeTagArrayItem(type);
        break;
      case FilterTypes.aggregateAmount:
        this.removeAggregateAmountFilter();
        this.removeTagArrayItem(type);
        break;
      case FilterTypes.loanAmount:
        this.removeLoanAmountFilter();
        this.removeTagArrayItem(type);
        break;
      case FilterTypes.loanClosingBalance:
        this.removeLoanClosingBalanceFilter();
        this.removeTagArrayItem(type);
        break;
      case FilterTypes.keyword:
        this.removeSearchText(tagText);
        this.removeSearchTagArrayItem(tagText);
        break;
      case FilterTypes.memoCode:
        this.removeMemoFilter();
        this.removeTagArrayItem(type);
        break;
      case FilterTypes.itemizations:
        this.removeItemizationsFilter(index, tagText);
        this.removeTagArrayGroupItem(type, index);
        break;
      case FilterTypes.electionCodes:
        this.removeElectionCodesFilter(index, tagText);
        this.removeTagArrayGroupItem(type, index);
        break;
      case FilterTypes.electionYear:
        this.removeElectionYearFilter();
        this.removeTagArrayItem(type);
        break;
      case FilterTypes.schedule:
        this.removeScheduleFilter();
        this.removeTagArrayItem(type);
        break;
      default:
        //console.log('unexpected type received for remove tag');
    }
  }

  /**
   * Remove the search keyword form the tagArray.
   */
  private removeSearchTagArrayItem(tagText: string) {
    let i = 0;
    for (const tag of this.tagArray) {
      if (tag.type === FilterTypes.keyword) {
        if (tag.group) {
          if (tag.group.length > 0) {
            if (tag.group[0] === tagText) {
              this.tagArray.splice(i, 1);
            }
          }
        }
      }
      i++;
    }
  }

  /**
   * Remove the entire object form the tagArray.
   */
  private removeTagArrayItem(type: FilterTypes) {
    let i = 0;
    let typeFound = false;
    for (const tag of this.tagArray) {
      if (tag.type === type) {
        typeFound = true;
        break;
      }
      i++;
    }
    if (typeFound) {
      this.tagArray.splice(i, 1);
    }
  }

  /**
   * An item in the tagsArray may have a group as an array where 1 item in the group array
   * is to be removed. If no group items exist after removing, the entire object
   * will be removed from the tagsArray.
   *
   * @param type filter type
   * @param index index of the group array to remove
   */
  private removeTagArrayGroupItem(type: FilterTypes, index: number) {
    let i = 0;
    for (const tag of this.tagArray) {
      if (tag.type === type) {
        if (tag.group) {
          if (tag.group.length > 0) {
            tag.group.splice(index, 1);
          }
        }
        // If no tags in the group, delete the item from the tagArray.
        if (tag.group.length === 0) {
          this.tagArray.splice(i, 1);
        }
        break;
      }
      i++;
    }
  }

  /**
   * Show the table of transactions in the recycle bin for the user.
   */
  public showRecycleBin() {
    this.view = ActiveView.recycleBin;

    // Inform the filter component of the view change
    this._transactionsMessageService.sendSwitchFilterViewMessage(ActiveView.recycleBin);
  }

  /**
   * Show the table of form transactions.
   */
  public showTransactions() {
    this.view = ActiveView.transactions;

    // Inform the filter component of the view change
    this._transactionsMessageService.sendSwitchFilterViewMessage(ActiveView.transactions);
  }

  /**
   * Show reattribute for a single transaction.
   */
  public showReattribute(debtSummary?: any) {
    const emptyValidForm = this._fb.group({});

    this.transactionToEdit.isReattribution = true;
    this.transactionToEdit.reattribution_id = this.transactionToEdit.transactionId;
    const emitObj: any = {
      form: emptyValidForm,
      direction: 'next',
      step: 'step_3',
      previousStep: 'transactions',
      action: ScheduleActions.add,
      transactionCategory: this.transactionCategory,
      scheduleType: this.transactionToEdit.scheduleType,
      transactionDetail: {
        transactionModel: this.transactionToEdit
      }
    };
    if (debtSummary) {
      if (debtSummary.returnToDebtSummary) {
        emitObj.returnToDebtSummary = debtSummary.returnToDebtSummary;
        emitObj.returnToDebtSummaryInfo = debtSummary.returnToDebtSummaryInfo;
      }
    }
    this.showTransaction.emit(emitObj);

    this.showCategories();
  }

    /**
   * Show redesignate for a single transaction.
   */
  public showRedesignate(debtSummary?: any) {
    const emptyValidForm = this._fb.group({});

    this.transactionToEdit.isRedesignation = true;
    this.transactionToEdit.redesignation_id = this.transactionToEdit.transactionId;
    const emitObj: any = {
      form: emptyValidForm,
      direction: 'next',
      step: 'step_3',
      previousStep: 'transactions',
      action: ScheduleActions.add,
      transactionCategory: this.transactionCategory,
      scheduleType: this.transactionToEdit.scheduleType,
      transactionDetail: {
        transactionModel: this.transactionToEdit
      }
    };
    this.showTransaction.emit(emitObj);
    this.showCategories();
  }

  /**
   * Show edit for a single transaction.
   */
  public showEdit(debtSummary?: any) {
    const emptyValidForm = this._fb.group({});

    const emitObj: any = {
      form: emptyValidForm,
      direction: 'next',
      step: 'step_3',
      previousStep: 'transactions',
      action: ScheduleActions.edit,
      transactionCategory: this.transactionCategory,
      scheduleType: this.transactionToEdit.scheduleType,
      transactionDetail: {
        transactionModel: this.transactionToEdit
      },
      formType: this.transactionToEdit.formType
    };
    if (debtSummary) {
      if (debtSummary.returnToDebtSummary) {
        emitObj.returnToDebtSummary = debtSummary.returnToDebtSummary;
        emitObj.returnToDebtSummaryInfo = debtSummary.returnToDebtSummaryInfo;
        emitObj.mainTransactionTypeText = 'Loans and Debts';
      }
    }
    if(this.transactionToEdit.mirrorReportId && !this.transactionToEdit.cloned){ //cloned check is done because the modal is already shown for clone before this point.
      this.handleMirrorTransactionIfApplicable(this.transactionToEdit,emitObj);
    }
    else{

      this.showTransaction.emit(emitObj);

      this.showCategories();
    }
  }

  handleMirrorTransactionIfApplicable(transactionToEdit: TransactionModel, emitObj: any) {
    let dialogMsg = '';
    let mirrorFormType = '';
    if(transactionToEdit.formType === 'F3X'){
      dialogMsg = `Please note that this change will not automatcally reflect in the F24 report. You will have to make this change separately in F24.`;
      mirrorFormType = 'F24';
    }
    else if(transactionToEdit.formType === 'F24'){
      dialogMsg = `Please note that if you update this transaction it will be updated in Form F3X. Please acknowledge this change by clicking the OK button.`;
      mirrorFormType = 'F3X';
    }

    this._dialogService
        .confirm(dialogMsg,ConfirmModalComponent, 'Warning!', true,ModalHeaderClassEnum.warningHeader,null,'Cancel')
        .then(res => {
          if (res === 'okay') {
            //make sure modifying is permitted based on mirrorReportId !== Filed/Submitted
            if(mirrorFormType === 'F3X'){
              this._reportsService
              .getReportInfo(mirrorFormType, transactionToEdit.mirrorReportId)
              .subscribe((res: any) => {
                if(res && res[0] && res[0].reportstatus === 'Submitted'){
                  this._dialogService
                  .confirm('This transaction cannot be modified since the mirrored transaction in Form 3X is already filed. You will have to amend that report', ConfirmModalComponent, 'Error!', false)
                  .then(res => {
                    if (res === 'okay') {
                    }
                  });
                }
                else{
                  this.showTransaction.emit(emitObj);
                  this.showCategories();
                }
              });
            }
            else{
              this.showTransaction.emit(emitObj);
              this.showCategories();
            }
            
          } else if (res === 'cancel') {
          }
        });
  }

  /**
   * Show the option to select/deselect columns in the table.
   */
  public showPinColumns() {
    this.showTransactions();
    this._transactionsMessageService.sendShowPinColumnMessage('show the Pin Col');
  }

  /**
   * Import transactions from an external file.
   */
  public doImport() {
    this._router.navigate(['/import-transactions']);
  }

  /**
   * Show filter options for transactions.
   */
  public showFilters() {
    this.isShowFilters = true;
    this.sidebarSwitch.emit(this.isShowFilters);
  }

  /**
   * Show the categories and hide the filters.
   */
  public showCategories() {
    this.isShowFilters = false;
    this.sidebarSwitch.emit(false);
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
   * Check if the view to show is Edit.
   */
  public isEditViewActive() {
    return this.view === this.editView ? true : false;
  }

  /**
   * Send a message to the subscriber to run the search.
   */
  private doSearch() {
    this.filters.keywords = this.searchTextArray;
    this._transactionsMessageService.sendDoKeywordFilterSearchMessage(this.filters);
  }

  public printPreview(): void {
    //console.log('TransactionsTableComponent printPreview...!');

    this._reportTypeService.printPreview('transaction_table_screen', this.formType);
  }

  /**
   * Returns true if a valid number, and if not a number returns true if not null or undefined. 
   * @param input 
   */
  private _isNotNullorUndefined(input: any){
    if(typeof input === "number"){
      return true;
    }
    else{
      return input !== null && input !== undefined;
    }
  }

  public showView() {
    const emptyValidForm = this._fb.group({});

    const emitObj: any = {
      form: emptyValidForm,
      direction: 'next',
      step: 'step_3',
      previousStep: 'transactions',
      action: ScheduleActions.view,
      transactionCategory: this.transactionCategory,
      scheduleType: this.transactionToEdit.scheduleType,
      transactionDetail: {
        transactionModel: this.transactionToEdit
      }
    };

    this.showTransaction.emit(emitObj);

    this.showCategories();
  }
}
