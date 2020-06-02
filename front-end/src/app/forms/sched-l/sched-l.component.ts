import { SchedHMessageServiceService } from './../sched-h-service/sched-h-message-service.service';
import { Component, OnInit, OnDestroy, OnChanges, Output, EventEmitter, Input, SimpleChanges, ViewEncapsulation , ChangeDetectionStrategy } from '@angular/core';
import { IndividualReceiptComponent } from '../form-3x/individual-receipt/individual-receipt.component';
import { FormBuilder, FormGroup, FormControl, NgForm, Validators } from '@angular/forms';
import { FormsService } from 'src/app/shared/services/FormsService/forms.service';
import { IndividualReceiptService } from '../form-3x/individual-receipt/individual-receipt.service';
import { ContactsService } from 'src/app/contacts/service/contacts.service';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { UtilService } from 'src/app/shared/utils/util.service';
import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { ReportTypeService } from '../form-3x/report-type/report-type.service';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { F3xMessageService } from '../form-3x/service/f3x-message.service';
import { TransactionsMessageService } from '../transactions/service/transactions-message.service';
import { ContributionDateValidator } from 'src/app/shared/utils/forms/validation/contribution-date.validator';
import { TransactionsService, GetTransactionsResponse } from '../transactions/service/transactions.service';
import { HttpClient } from '@angular/common/http';
import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { ScheduleActions } from '../form-3x/individual-receipt/schedule-actions.enum';
import { AbstractSchedule } from '../form-3x/individual-receipt/abstract-schedule';
import { ReportsService } from 'src/app/reports/service/report.service';
import { TransactionModel } from '../transactions/model/transaction.model';
import { Observable, Subscription } from 'rxjs';
import { style, animate, transition, trigger } from '@angular/animations';
import { ActiveView } from '../transactions/transactions.component';
import { PaginationInstance } from 'ngx-pagination';
import { SortableColumnModel } from 'src/app/shared/services/TableService/sortable-column.model';
import { TableService } from 'src/app/shared/services/TableService/table.service';
import { SchedLService } from './sched-l.service';
import { SchedLModel } from './sched-l.model';
import { AbstractScheduleParentEnum } from '../form-3x/individual-receipt/abstract-schedule-parent.enum';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import {AuthService} from '../../shared/services/AuthService/auth.service';

@Component({
  selector: 'app-sched-l',
  templateUrl: './sched-l.component.html',
  styleUrls: ['./sched-l.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe],
  encapsulation: ViewEncapsulation.None,
  /* animations: [
    trigger('fadeInOut', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate(500, style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate(0, style({ opacity: 0 }))
      ])
    ])
  ] */
})
export class SchedLComponent extends AbstractSchedule implements OnInit, OnDestroy, OnChanges {
  @Input() mainTransactionTypeText: string;
  @Input() transactionTypeText: string;
  @Input() transactionType: string;
  @Input() scheduleAction: ScheduleActions;
  @Input() scheduleType: string;
  @Output() status: EventEmitter<any>;
  @Input() public tableType: string;
  public transactionsView = ActiveView.transactions;

  public formType: string;
  public showPart2: boolean;
  public loaded = false;
  public schedL: FormGroup;


  public lSubscription: Subscription;
  public lSum: any;
  public saveLRes: any;

  public showSelectType = true;

  public schedLsModel: Array<SchedLModel>;
  private clonedTransaction: any;
  public bulkActionDisabled = true;
  public bulkActionCounter = 0;
  private allTransactionsSelected: boolean;

  // ngx-pagination config
  public pageSizes: number[] = UtilService.PAGINATION_PAGE_SIZES;
  public maxItemsPerPage: number = this.pageSizes[0];
  public paginationControlsMaxSize: number = 10;
  public directionLinks: boolean = false;
  public autoHide: boolean = true;
  public config: PaginationInstance;
  public numberOfPages: number = 0;
  public pageNumbers: number[] = [];
  private firstItemOnPage = 0;
  private lastItemOnPage = 0;

  constructor(
    _http: HttpClient,
    _fb: FormBuilder,
    _formService: FormsService,
    _receiptService: IndividualReceiptService,
    _contactsService: ContactsService,
    _activatedRoute: ActivatedRoute,
    _config: NgbTooltipConfig,
    _router: Router,
    _utilService: UtilService,
    _messageService: MessageService,
    _currencyPipe: CurrencyPipe,
    _decimalPipe: DecimalPipe,
    _reportTypeService: ReportTypeService,
    _typeaheadService: TypeaheadService,
    _dialogService: DialogService,
    _f3xMessageService: F3xMessageService,
    _transactionsMessageService: TransactionsMessageService,
    _contributionDateValidator: ContributionDateValidator,
    _transactionsService: TransactionsService,
    _reportsService: ReportsService,
    private _tranService: TransactionsService,
    private _rt: Router,
    private _dlService: DialogService,
    private _actRoute: ActivatedRoute,
    private _schedLService: SchedLService,
    private _individualReceiptService: IndividualReceiptService,
    private _tranMessageService: TransactionsMessageService,
    _schedHMessageServiceService: SchedHMessageServiceService,
    _authService: AuthService,
  ) {
     super(
      _http,
      _fb,
      _formService,
      _receiptService,
      _contactsService,
      _activatedRoute,
      _config,
      _router,
      _utilService,
      _messageService,
      _currencyPipe,
      _decimalPipe,
      _reportTypeService,
      _typeaheadService,
      _dialogService,
      _f3xMessageService,
      _transactionsMessageService,
      _contributionDateValidator,
      _transactionsService,
      _reportsService,
      _schedHMessageServiceService,
      _authService,
    );
    _schedLService;
    _individualReceiptService;
    _tranMessageService;

    const paginateConfig: PaginationInstance = {
      id: 'forms__sched-l-table-pagination',
      itemsPerPage: this.maxItemsPerPage,
      currentPage: 1
    };
    this.config = paginateConfig;
  }


  public ngOnInit() {
    this.abstractScheduleComponent = AbstractScheduleParentEnum.schedLComponent;
    // temp code - waiting until dynamic forms completes and loads the formGroup
    // before rendering the static fields, otherwise validation error styling
    // is not working (input-error-field class).  If dynamic forms deliver,
    // the static fields, then remove this or set a flag when formGroup is ready
    setTimeout(() => {
      this.loaded = true;
    }, 2000);

    this.formType = this._actRoute.snapshot.paramMap.get('form_id');
    //this.getH4Sum(this._individualReceiptService.getReportIdFromStorage(this.formType));
    
    //this.setSchedH4();
    //this.setDefaultValues();

    /*
    //console.log("this.transactionType: ", this.transactionType);
    if(this.transactionType === 'ALLOC_H4_RATIO') {
      this.transactionType = 'ALLOC_EXP_DEBT'
    }
    */

    this.setSchedL();
    this.getPage(this.config.currentPage);
  }

  public ngOnChanges(changes: SimpleChanges) {
    // OnChanges() can be triggered before OnInit().  Ensure formType is set.
    this.formType = '3X';

    if (this.transactionType === 'LA_SUM' || this.transactionType === 'LB_SUM') {
      this.getTransactions(this._individualReceiptService.getReportIdFromStorage(this.formType), this.transactionType);
    }

    if (this.transactionType === 'L_SUM') {
      this.getSummary(this._individualReceiptService.getReportIdFromStorage(this.formType), '');
    }

  }

  ngDoCheck() {
    this.status.emit({
      otherSchedHTransactionType: this.transactionType
    });
  }

  public ngOnDestroy(): void {
    if (this.lSubscription) {
      this.lSubscription.unsubscribe();
    }
    super.ngOnDestroy();
  }

  /*setDefaultValues() {
    this.schedL.patchValue({levin_account_id: '6'}, { onlySelf: true });
  }*/

  public getReportId(): string {

    let report_id;
    let reportType: any = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
    if (reportType === null || typeof reportType === 'undefined') {
      reportType = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type_backup`));
    }

    if(reportType) {
      if (reportType.hasOwnProperty('reportId')) {
        report_id = reportType.reportId;
      } else if (reportType.hasOwnProperty('reportid')) {
        report_id = reportType.reportid;
      }
    }

    return report_id ? report_id : '0';

  }

  public setSchedL() {
    this.schedL = new FormGroup({
      type: new FormControl('', Validators.required)
    });
  }

  public selectTypeChange(transactionType) {
    this.transactionType = transactionType;
  }
 
  public getTransactions(reportId: string, levinType: string, page: number = 1) {
    this.config.currentPage = page;
    this.schedLsModel = [];
	
    this.lSubscription = this._schedLService.getTransactions(
        reportId, 
        levinType,
        page,
        this.config.itemsPerPage,
        'default',
        false
      ).subscribe(res => {
        const pagedResponse = this._utilService.pageResponse(res, this.config);
        this.schedLsModel = this.mapFromServerFields(pagedResponse.items);
        this.pageNumbers = pagedResponse.pageNumbers;
        this.setArrow(this.schedLsModel);
      });
  }

  public getSummary(reportId: string, levinAccountId: string) {
    this.lSubscription = this._schedLService.getSummary(reportId, levinAccountId).subscribe(res => {
        if (res) {
          this.lSum = [];
          this.lSum =  res;
        }
      });
    this._individualReceiptService.getLevinAccounts().subscribe(res => {
        if (res) {
          this.levinAccounts = res;
        }
      });
  }

  public getSummaryByLevinAccount(account: any): void {
    let levinAccountId = '';
    if (account && account.levin_account_id) {
      levinAccountId = account.levin_account_id;
    }
    this.getSummary(this._individualReceiptService.getReportIdFromStorage(this.formType), levinAccountId);

  }

  public returnToSum(): void {
    this.transactionType = 'LA_SUM';
    this.getTransactions(this._individualReceiptService.getReportIdFromStorage(this.formType), this.transactionType);
  }

  public returnToAdd(): void {
    this.showSelectType = true;
    this.transactionType = "ALLOC_H4_TYPES"

    //this.transactionType = 'ALLOC_EXP_DEBT'; //'ALLOC_H4_RATIO';
  }1

  public previousStep(): void {
    
    this.schedL.reset();

    this.status.emit({
      form: {},
      direction: 'previous',
      step: 'step_2'
    });
  }

  public clickArrow(item: SchedLModel) {
    if(item.arrow_dir === 'down') {
      let indexRep = this.schedLsModel.indexOf(item);
      if (indexRep > -1) {
        let tmp: Array<SchedLModel> = this.schedLsModel.filter(obj => obj.back_ref_transaction_id === item.transaction_id);
        for(let entry of tmp) {
          entry.arrow_dir = 'show';
          this.schedLsModel.splice(indexRep + 1, 0, entry);
          indexRep++;
        }
        this.config.totalItems = this.schedLsModel.length;
      }
      this.schedLsModel.find(function(obj) { return obj.transaction_id === item.transaction_id}).arrow_dir = 'up';

																												   
																															  
	  
    }else if(item.arrow_dir === 'up') {
      //this.schedH4sModel = this.schedH4sModel.filter(obj => obj.memo_code !== 'X');
      this.schedLsModel = this.schedLsModel.filter(obj => obj.back_ref_transaction_id !== item.transaction_id);
      this.config.totalItems = this.schedLsModel.length;

      this.schedLsModel.find(function(obj) { return obj.transaction_id === item.transaction_id}).arrow_dir = 'down';
    }
   
	 

  }

  public setArrow(items: SchedLModel[]) {
    if (items) {
      for (const item of items) {
        if (item.memo_code !== 'X' && this.schedLsModel.find(function(obj) { return obj.back_ref_transaction_id === item.transaction_id})) {
            item.arrow_dir = 'down';
        }
      }
    }

  }

  public mapFromServerFields(serverData: any) {
    if (!serverData || !Array.isArray(serverData)) {
      return;
    }
    const modelArray: any = [];
    for (const row of serverData) {
      const model = new SchedLModel({});
      this.mapDatabaseRowToModel(model, row);
      if (row.child) {
        const modelChildArray = [];
        for (const childRow of row.child) {
          const childModel = new SchedLModel({});
          this.mapDatabaseRowToModel(childModel, childRow);
          modelChildArray.push(childModel);
        }
        model.child = modelChildArray;
      }
      modelArray.push(model);
    }
    //console.log('91: ', modelArray);
    return modelArray;
  }

  public mapDatabaseRowToModel(model: SchedLModel, row: any) {
    model.cmte_id = row.cmte_id;
    model.report_id = row.report_id;
    model.transaction_type_identifier = row.transaction_type_identifier;
    model.transaction_id = row.transaction_id;
    model.tran_desc = row.tran_desc;
    model.back_ref_transaction_id = row.back_ref_transaction_id;
    model.levin_account_id = row.levin_account_id;
    model.levin_account_name = row.levin_account_name;
    model.contribution_date = row.contribution_date;
    model.expenditure_date = row.expenditure_date;
    model.contribution_amount = row.contribution_amount;
    model.expenditure_amount = row.expenditure_amount;
    if (row.contribution_date !== '') {
      model.date = row.contribution_date;
      model.amount = row.contribution_amount;
    } else if (row.expenditure_date !== '') {
      model.date = row.expenditure_date;
      model.amount = row.expenditure_amount;
    }
    model.aggregate = row.aggregate_amt;
    model.memo_code = row.memo_code;
    model.first_name = row.first_name;
    model.last_name = row.last_name;
    model.entity_name = row.entity_name;
    model.entity_type = row.entity_type;
    model.api_call = row.api_call;
  }

  public editTransaction(trx: any): void {
    this.scheduleAction = ScheduleActions.edit;
    trx.apiCall = trx.api_call;
    trx.backRefTransactionId = trx.back_ref_transaction_id;
    trx.transactionId = trx.transaction_id;
    trx.transactionTypeIdentifier = trx.transaction_type_identifier;
    this._tranMessageService.sendEditTransactionMessage(trx);
  }

  public printTransaction(trx: any): void {
    this._reportTypeService.printPreview('transaction_table_screen', '3X', trx.transaction_id);
  }

  public trashTransaction(trx: any): void {

    trx.report_id = this._individualReceiptService.getReportIdFromStorage(this.formType);
    trx.transactionId = trx.transaction_id;

    this._dlService
      .confirm('You are about to delete this transaction ' + trx.transaction_id + '.', ConfirmModalComponent, 'Caution!')
      .then(res => {
        if (res === 'okay') {
          this._tranService
            .trashOrRestoreTransactions(this.formType, 'trash', trx.report_id, [trx])
            .subscribe((res: GetTransactionsResponse) => {
              this.getTransactions(trx.report_id, this.transactionType);
              this._dlService.confirm(
                'Transaction has been successfully deleted and sent to the recycle bin. ' + trx.transaction_id,
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

  public cloneTransaction(trx: any): void {

    trx.reportId = this._individualReceiptService.getReportIdFromStorage(this.formType);
    trx.report_id = trx.reportId;
    trx.transactionId = trx.transaction_id;

    this._tranService
      .cloneTransaction(trx.transaction_id)
      .subscribe((cloneTransactionResponse: TransactionModel) => {
        if (cloneTransactionResponse[0] && cloneTransactionResponse[0].hasOwnProperty('transaction_id')) {
          this.clonedTransaction = cloneTransactionResponse[0];

          this.clonedTransaction.reportId = cloneTransactionResponse[0].report_id;

          this.editTransaction(this.clonedTransaction);

          this._rt.navigate([`/forms/form/3X`], {
            queryParams: { step: 'step_3', reportId: trx.reportId, edit: true, cloned: true, transactionCategory: 'other'}
          });
        }
      });
  }

  public checkIfTrashable(trx: any): boolean {
    if (this.schedLsModel.filter(obj => obj.back_ref_transaction_id === trx.transaction_id).length !== 0) {
      return false;
    }
    return true;
  }

  /**
   * Check for multiple rows checked in the table
   * and disable/enable the bulk action button
   * accordingly.
   *
   * @param the event payload from the click
   */
  public checkForMultiChecked(e: any): void {
    if (e.target.checked) {
      this.bulkActionCounter++;
    } else {
      this.allTransactionsSelected = false;
      if (this.bulkActionCounter > 0) {
        this.bulkActionCounter--;
      }
    }

    // Transaction View shows bulk action when more than 1 checked
    // Recycle Bin shows delete action when 1 or more checked.
    const count = this.isTransactionViewActive() ? 1 : 0;
    this.bulkActionDisabled = this.bulkActionCounter > count ? false : true;
  }

  /**
   * Check if the view to show is Transactions.
   */
  public isTransactionViewActive() {
    return this.tableType === this.transactionsView ? true : false;
  }

 /**
   * The records for a given page.
   *
   * @param page the page containing the records to get
   */
  public getPage(page: number): void {
    this.getTransactions(this._individualReceiptService.getReportIdFromStorage(this.formType), 
      this.transactionType, page);
  }

  /**
   * onChange for maxItemsPerPage.
   *
   * @param pageSize the page size to get
   */
  public onMaxItemsPerPageChanged(pageSize: number): void {
    this.config.currentPage = 1;
    this.config.itemsPerPage = pageSize;
    this.getPage(this.config.currentPage);
  }

  /**
   * onChange for gotoPage.
   *
   * @param page the page to get
   */
  public onGotoPageChange(page: number): void {
    this.config.currentPage = page;
    this.getPage(this.config.currentPage);
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
   * Determine the item range shown by the server-side pagination.
   */
  public determineItemRange(): string {
    let range: {
      firstItemOnPage: number, lastItemOnPage: number, itemRange: string
    } = this._utilService.determineItemRange(this.config, this.schedLsModel);

    this.firstItemOnPage = range.firstItemOnPage;
    this.lastItemOnPage = range.lastItemOnPage;
    return range.itemRange;
  }    

  public showPageSizes(): boolean {
    if (this.config && this.config.totalItems && this.config.totalItems > 0){
      return true;
    }
    return false;
  }
}

