import { SchedHServiceService } from './../sched-h-service/sched-h-service.service';
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
import { Observable, Subscription, Subject } from 'rxjs';
import { SchedH5Service } from './sched-h5.service';
import { style, animate, transition, trigger } from '@angular/animations';
import { AbstractScheduleParentEnum } from '../form-3x/individual-receipt/abstract-schedule-parent.enum';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import {AuthService} from '../../shared/services/AuthService/auth.service';
import { PaginationInstance } from 'ngx-pagination';

@Component({
  selector: 'app-sched-h5',
  templateUrl: './sched-h5.component.html',
  styleUrls: ['./sched-h5.component.scss'],
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
export class SchedH5Component extends AbstractSchedule implements OnInit, OnDestroy, OnChanges {
  @Input() transactionTypeText: string;
  @Input() transactionType: string;
  @Input() scheduleAction: ScheduleActions;
  @Input() scheduleType: string;
  @Input() transactionData: any;
  @Output() status: EventEmitter<any>;

  public formType: string;
  public showPart2: boolean;
  public loaded = true; //false;

  public schedH5: FormGroup;
  public categories: any;
  public identifiers: any;
  public totalName: any;
  public showIdentiferSelect = false;
  public showIdentifer = false;
  public h5Sum: any;
  public h5SumP: any;
  public saveHRes: any;
  public h5Subscription: Subscription;


  public h5Entries = [];
  public h5Ratios: any;

  public levinAccountsies: any;

  public receiptDateErr = false;

  public cvgStartDate: any;
  public cvgEndDate: any;

  public isSubmit = false;

  public transferredAmountErr = false;

  public isSaveAndAdd = false;

  public transaction_id: string;
  public h5EntrieEdit: any;
  public back_ref_transaction_id: string;

  public transferred_amount_edit = 0;
  public total_amount_edit = 0;
  public populateFormForEdit: Subscription;

  public saveAndAddDisabled = false;
  public getH1H2ExistSubscription: Subscription;

  public restoreSubscription: Subscription;
  public trashSubscription: Subscription;

  private _h5OnDestroy$ = new Subject();

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
    private _schedH5Service: SchedH5Service,
    private _individualReceiptService: IndividualReceiptService,
    private _uService: UtilService,
    private _formBuilder: FormBuilder,
    private _decPipe: DecimalPipe,
    private _tranService: TransactionsService,
    private _dlService: DialogService,
    private _schedHMessageServiceService: SchedHMessageServiceService,
    private _schedHService: SchedHServiceService,
    private _tranMessageService: TransactionsMessageService,
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
    _schedH5Service;
    _individualReceiptService;
    _uService;
    _formBuilder;
    _decPipe;
    _tranService;
    _dlService;
    _tranMessageService;

    const paginateConfig: PaginationInstance = {
      id: 'forms__sched-h5-table-pagination',
      itemsPerPage: this.maxItemsPerPage,
      currentPage: 1
    };
    this.config = paginateConfig;

    this.populateFormForEdit = this._schedHMessageServiceService.getpopulateHFormForEditMessage()
      .subscribe(p => {
        if (p.scheduleType === 'Schedule H5') {
          let res = this._schedHService.getSchedule(p.transactionDetail.transactionModel).subscribe(res => {
            if (res && res.length === 1) {
              this.editH5(res[0]);
            }
          });
        }
      })

    this.restoreSubscription = this._tranMessageService
      .getRestoreTransactionsMessage()
      .subscribe(
        message => {
          if (message.scheduleType === 'Schedule H5') {
            this.setH5Sum(this.config.currentPage);
          }
        }
      )

    this.trashSubscription = this._tranMessageService
      .getRemoveHTransactionsMessage()
      .subscribe(
        message => {
          if (message.scheduleType === 'Schedule H5') {
            this.setH5Sum(this.config.currentPage);
          }
        }
      )
  }

  public ngOnInit() {
    this.abstractScheduleComponent = AbstractScheduleParentEnum.schedH5Component;
    this.formType = '3X';
    this.formFieldsPrePopulated = true;
    // this.formFields = this._staticFormFields;
    super.ngOnInit();
    this.showPart2 = false;
    //this.transactionType = 'OPEXP'; // 'INDV_REC';
    //this.transactionTypeText = 'Coordinated Party Expenditure Debt to Vendor';
    super.ngOnChanges(null);
    this._setTransactionDetail();
    //console.log();

    // temp code - waiting until dynamic forms completes and loads the formGroup
    // before rendering the static fields, otherwise validation error styling
    // is not working (input-error-field class).  If dynamic forms deliver,
    // the static fields, then remove this or set a flag when formGroup is ready
    setTimeout(() => {
      this.loaded = true;
    }, 2000);

    //this._getFormFields();

    this.setH5(this.config.currentPage);
    this.setCategory();
    this.setActivityOrEventIdentifier();

    //this.setH5Sum();
    //this.setH5SumP();

    this.setLevinAccounts();

    this.h5Ratios = {};
    this.h5Ratios['child'] = [];

    this.getPage(this.config.currentPage);
  }

  public ngOnChanges(changes: SimpleChanges) {
    // OnChanges() can be triggered before OnInit().  Ensure formType is set.
    this.formType = '3X';
    this.showPart2 = false;
    this._setTransactionDetail();

    if (this.transactionType === 'ALLOC_H5_SUM') {
      this.setH5Sum(this.config.currentPage);
    }

    if (this.transactionType === 'ALLOC_H5_SUM_P') {
      this.setH5SumP();
    }
  }

  ngDoCheck() {
    this.status.emit({
      otherSchedHTransactionType: this.transactionType
    });
  }

  public ngOnDestroy(): void {
    this._h5OnDestroy$.next(true);
    this.populateFormForEdit.unsubscribe();
    this.restoreSubscription.unsubscribe();
    this.trashSubscription.unsubscribe();
    super.ngOnDestroy();
  }

  // public handleCheckboxChange($event: any, col: any) {
  //   const { checked } = $event.target;
  //   const patch = {};
  //   if (checked) {
  //     patch[col.name] = 'Y';
  //   } else {
  //     patch[col.name] = 'N';
  //   }
  //   this.frmIndividualReceipt.patchValue(patch, { onlySelf: true });
  // }

  public saveAndReturnToParentDebt() {
    this._setTransactionDetail();
    this.saveAndReturnToParent();
  }

  public getReportId(): string {

    const reportId = localStorage.getItem('reportId');
    return reportId ? reportId : '0';
  }

  public next() {
    // TODO add this in once the form fields are displaying red when in error.
    // check all page 1 for valid

    // if (!this._checkFormFieldIsValid('coord_expenditure_y')) {
    //   return;
    // }
    // if (!this._checkFormFieldIsValid('designated_com_id')) {
    //   return;
    // }
    // if (!this._checkFormFieldIsValid('designated_com_name')) {
    //   return;
    // }
    // if (!this._checkFormFieldIsValid('subordinate_com_id')) {
    //   return;
    // }
    // if (!this._checkFormFieldIsValid('subordinate_com_name')) {
    //   return;
    // }
    // if (!this._checkFormFieldIsValid('street_1_co_exp')) {
    //   return;
    // }
    // if (!this._checkFormFieldIsValid('street_2_co_exp')) {
    //   return;
    // }
    this.showPart2 = true;
  }

  public back() {
    this.showPart2 = false;
  }

  /**
   * Returns true if the field is valid.
   * @param fieldName name of control to check for validity
   */
  private _checkFormFieldIsValid(fieldName: string): boolean {
    if (this.frmIndividualReceipt.contains(fieldName)) {
      return this.frmIndividualReceipt.get(fieldName).valid;
    }
  }

  private _setTransactionDetail() {
    this.subTransactionInfo = {
      transactionType: 'DEBT_TO_VENDOR',
      transactionTypeDescription: 'Debt to Vendor',
      scheduleType: 'sched_d',
      subTransactionType: 'OPEXP_DEBT',
      subScheduleType: 'sched_b',
      subTransactionTypeDescription: 'Operating Expenditure Debt to Vendor',
      api_call: '/sd/schedD',
      isParent: false,
      isEarmark: false
    };

    if (this.scheduleAction === ScheduleActions.addSubTransaction) {
      this.clearFormValues();
    } else if (this.scheduleAction === ScheduleActions.edit) {
    }
  }

  /**a payload for h5
   * {
        "cmte_id": "C00029447",  <<
        "report_id": 1324002,  <<
        "transaction_type_identifier": "TRAN_FROM_NON_FED_ACC", <<
        "transaction_id": "SH20191001000000561",
        "account_name": "test_acct", <<
        "receipt_date": "2019-10-30", <<
        "total_amount_transferred": 50.0,
        "voter_registration_amount": null, <<
        "voter_id_amount": null,
        "gotv_amount": 50.0,
        "generic_campaign_amount": null,
        "memo_code": "",
        "memo_text": "",
        "create_date": "2019-10-01T18:47:13.391737",
        "last_update_date": "2019-10-01T18:47:13.391742"
    }
   */

  public saveH5(h5_obj: any) {

    this._schedH5Service.saveH5(h5_obj).subscribe(res => {
      if (res) {
        this.saveHRes = res;
        this.h5Entries = [];
        this.updateThirdNavAmounts(res);
      }
    });
  }

  public saveAndGetSummary(ratio: any, scheduleAction: any) {
    let page = 1;
    this.config.currentPage = page;
    const reportId = this._individualReceiptService.getReportIdFromStorage(this.formType);

    this._schedH5Service.saveAndGetSummary(
        ratio, 
        reportId, 
        scheduleAction,
        page,
        this.config.itemsPerPage,
        'default',
        false
      ).subscribe(res => {
        this.h5Entries = [];
        const pagedResponse = this._utilService.pageResponse(res, this.config);
        this.h5Sum = pagedResponse.items;
        this.pageNumbers = pagedResponse.pageNumbers;

      // Update third navigation totals
      const report = {
        'report_id': reportId
      };
      this.updateThirdNavAmounts(report);
    });
  }

  public saveAddMore(): void {
    //   this.doValidate();    
    // }

    // public doValidate() {

    // this.schedH2.patchValue({ fundraising: this.schedH2.get('select_activity_function').value === 'f' ? true : false }, { onlySelf: true });
    // this.schedH2.patchValue({ direct_cand_support: this.schedH2.get('select_activity_function').value === 'd' ? true : false }, { onlySelf: true });

    const accountName = this.schedH5.get('account_name').value;
    const receipt_date = this.schedH5.get('receipt_date').value;
    let memo_text = this.schedH5.get('memo_text').value;
    this.isSaveAndAdd = true;

    const reportId = this._individualReceiptService.getReportIdFromStorage(this.formType);

    this.h5Ratios['report_id'] = reportId;
    this.h5Ratios.transaction_type_identifier = 'TRAN_FROM_LEVIN_ACC';
    this.h5Ratios['account_name'] = this.schedH5.get('account_name').value;

    const formObj = this.schedH5.getRawValue();

    //const total_amount_transferred = +(this.schedH5.get('total_amount_transferred').value) 
    //      + (+this.schedH5.get('transferred_amount').value);
    const total_amount_transferred = this.convertFormattedAmountToDecimal(this.schedH5.get('total_amount_transferred').value) +
      this.convertFormattedAmountToDecimal(this.schedH5.get('transferred_amount').value)
    this.h5Ratios.total_amount_transferred = total_amount_transferred;

    //this.schedH5.patchValue({total_amount_transferred: total_amount_transferred}, { onlySelf: true });


    formObj['report_id'] = reportId;
    formObj['transaction_type_identifier'] = "TRAN_FROM_LEVIN_ACC";
    formObj['back_ref_transaction_id'] = this.back_ref_transaction_id;

    delete formObj.total_amount_transferred;

    const transferred_amount = this.convertFormattedAmountToDecimal(this.schedH5.get('transferred_amount').value);

    memo_text = memo_text ? memo_text : '';
    // set corresponding amount value
    if (this.schedH5.get('category').value === 'voter_id') {
      formObj['voter_id_amount'] = transferred_amount;
    } else if (this.schedH5.get('category').value === 'voter_registration') {
      formObj['voter_registration_amount'] = transferred_amount;
    } else if (this.schedH5.get('category').value === 'gotv') {
      formObj['gotv_amount'] = transferred_amount;
    } else if (this.schedH5.get('category').value === 'generic_campaign') {
      formObj['generic_campaign_amount'] = transferred_amount;
    }

    formObj['receipt_date'] = this.schedH5.get('receipt_date').value;

    formObj['transaction_id'] = this.transaction_id;

    formObj['memo_text'] = memo_text;

    const serializedForm = JSON.stringify(formObj);

    this.isSubmit = true;

    if (this.schedH5.status === 'VALID') {

      this.schedH5.patchValue({ total_amount_transferred: this._decPipe.transform(total_amount_transferred, '.2-2') }, { onlySelf: true });

      if (this.scheduleAction !== ScheduleActions.edit) {
        this.h5Entries.push(formObj);
        this.config.totalItems = this.h5Entries.length;
        this.h5Ratios.child.push(formObj);
      } else {
        this.h5EntrieEdit = formObj;
      }

      //this.schedH5.patchValue({category: ''}, { onlySelf: true });
      //this.schedH5.patchValue({transferred_amount: ''}, { onlySelf: true });

      this.isSubmit = false;

      this.schedH5.reset();
      this.schedH5.patchValue({ account_name: accountName }, { onlySelf: true });
      this.schedH5.patchValue({ receipt_date: receipt_date }, { onlySelf: true });
      this.schedH5.patchValue({ category: '' }, { onlySelf: true });
      this.schedH5.patchValue({ transferred_amount: '' }, { onlySelf: true });
      this.schedH5.patchValue({ total_amount_transferred: this._decPipe.transform(total_amount_transferred, '.2-2') }, { onlySelf: true });

      // this.saveH5(serializedForm);
      // this.schedH5.reset();

      // Note: Do after all patching to avoid form change detection which will set to false
      localStorage.setItem(`form_${this.formType}_saved`, JSON.stringify({ saved: true }));
    }
  }


  public setH5(page: number) {
    this.config.currentPage = page;

    this.schedH5 = new FormGroup({
      account_name: new FormControl('', [Validators.maxLength(40), Validators.required]),
      receipt_date: new FormControl('', Validators.required),
      total_amount_transferred: new FormControl(''),
      category: new FormControl('', Validators.required),
      transferred_amount: new FormControl('', Validators.required),
      memo_text: new FormControl(),
      // activity_event_name: new FormControl(''),
      // amount: new FormControl(''),
      // total_amount: new FormControl('')
    });
    this._prepareForUnsavedH5Changes();
  }

  private _prepareForUnsavedH5Changes(): void {
    this.schedH5.valueChanges.takeUntil(this._h5OnDestroy$).subscribe(val => {
      if (this.schedH5.dirty) {
        localStorage.setItem(`form_${this.formType}_saved`, JSON.stringify({ saved: false }));
      }
    });
  }

  public setCategory() {

    this.categories = [
      {
        "id": "voter_id",
        "name": "Voter ID"
      },
      {
        "id": "voter_registration",
        "name": "Voter Registration"
      },
      {
        "id": "generic_campaign",
        "name": "Generic Campaign Activities"
      },
      {
        "id": "gotv",
        "name": "GOTV"
      }

    ]

  }


  public setActivityOrEventIdentifier() {

    this.identifiers = [
      {
        "id": "chicago_mens_rotary",
        "name": "Chicago Men's Rotary"
      },
      {
        "id": "detroid_mens_dinnner_club",
        "name": "Detroid Men's Dinnner Club"
      },
      {
        "id": "chicago_wommens_league",
        "name": "Chicago Women's League"
      },
      {
        "id": "junior_board_shop_of_tallahasse",
        "name": "Junior Board Shop of Tallahasse"
      }
    ]

  }

  public returnToSum(): void {

    if (this.h5Ratios.child.length > 0) {
      this.addEntries();
    }

    if (this.scheduleAction === ScheduleActions.edit) {
      this.scheduleAction = ScheduleActions.add;
    }


    this.isSubmit = false;
    this.schedH5.reset();
    this.setH5(this.config.currentPage);

    this.h5Entries = [];
    this.schedH5.patchValue({ transferred_amount: 0 }, { onlySelf: true });

    this.schedH5 = this._formBuilder.group({
      category: ['']
    });

    this.receiptDateErr = false;

    this.transactionType = 'ALLOC_H5_SUM';
    //this.setH5Sum();
  }

  public returnToAdd(): void {
    this.setH5(this.config.currentPage);
    this.transactionType = 'ALLOC_H5_RATIO';
  }

  //to test for privous
  public resetTransactionType() {
    this.transactionType = '';
  }

  public selectCategoryChange(e) {

    this.isSaveAndAdd = false;

    this.schedH5.patchValue({ transferred_amount: '' }, { onlySelf: true });

    if (!this.schedH5.get('category').value) {
      this.showIdentifer = false;
    } else {
      this.showIdentifer = true;
    }

    if (this.schedH5.get('category').value === 'total_admin') {
      this.totalName = 'Administrative';
      this.showIdentiferSelect = false
    } else if (this.schedH5.get('category').value === 'generic_voter_drive') {
      this.totalName = 'Generic Voter Drive';
      this.showIdentiferSelect = false
    } else if (this.schedH5.get('category').value === 'exempt_activities') {
      this.totalName = 'Exempt Activities';
      this.showIdentiferSelect = false
    } else if (this.schedH5.get('category').value === 'direct_fundraising') {
      this.totalName = 'Activity or Event Identifier';
      this.showIdentiferSelect = true
    } else if (this.schedH5.get('category').value === 'direct_can_support') {
      this.totalName = 'Activity or Event Identifier';
      this.showIdentiferSelect = true
    } else if (this.schedH5.get('category').value === 'pac') {
      this.totalName = 'Public Communications';
      this.showIdentiferSelect = false
    }

    if (e.target.value !== '') {
      this._noH1H2Popup(e.target.value)
    }
  }

  public setH5Sum(page: number) {
    this.config.currentPage = page;
    this.h5Sum = [];

    const reportId = this._individualReceiptService.getReportIdFromStorage(this.formType);

    this.h5Subscription = this._schedH5Service.getSummary(
        reportId,
        page,
        this.config.itemsPerPage,
        'default',
        false
      ).subscribe(res => {
        const pagedResponse = this._utilService.pageResponse(res, this.config);
        this.h5Sum = pagedResponse.items;
        this.pageNumbers = pagedResponse.pageNumbers;
    });
  }

  public setH5SumP() {
    const reportId = this._individualReceiptService.getReportIdFromStorage(this.formType);

    this.h5Subscription = this._schedH5Service.getBreakDown(reportId).subscribe(res => {
      if (res) {

        this.h5SumP = [];

        this.h5SumP.push(
          {
            'category': 'Voter ID',
            'amount': +res[0].voter_id
          }, {
            'category': 'Voter Registration',
            'amount': +res[0].voter_registration
          }, {
            'category': 'Generic Campaign Activities',
            'amount': +res[0].generic_campaign
          }, {
            'category': 'GOTV',
            'amount': +res[0].gotv
          }, {
            'category': 'This Period (Total Amount of Transfer Received)',
            'amount': +res[0].total
          }
        );

        //this.h5SumP =  res;
      }
    });

    /*  
    this.h5SumP = [
      {
        "category": "Voter ID",
        "amount": 8093320.00
      },
      {
        "category": "Voter Registration",
        "amount": 2037000.00
      },
      {
        "category": "Generic Campaign Activities",
        "amount": 502300.00
      },
      {
        "category": "GOTV",
        "amount": 43320301.00
      },
      {
        "category": "Total Amount Transferred",
        "amount": 52304200.00
      }
    ]
    */
  }

  public setLevinAccounts() {

    this.h5Subscription = this._schedH5Service.getLevinAccounts().subscribe(res => {
      if (res) {
        this.levinAccountsies = res;
      }
    });

  }

  public addEntries() {
    //const serializedForm = JSON.stringify(this.h5Ratios);
    //this.saveH5(serializedForm);

    let serializedForm: any;
    if (this.scheduleAction === ScheduleActions.add) {
      serializedForm = JSON.stringify(this.h5Ratios);
    } else if (this.scheduleAction === ScheduleActions.edit) {
      serializedForm = JSON.stringify(this.h5EntrieEdit);
    }

    this.saveAndGetSummary(serializedForm, this.scheduleAction);
    this.schedH5.patchValue({ transferred_amount: 0 }, { onlySelf: true });
    this.h5Ratios = {};
    this.h5Ratios['child'] = [];
  }

  public receiptDateChanged(receiptDate: string) {

    const formInfo = JSON.parse(localStorage.getItem('form_3X_report_type'));
    this.cvgStartDate = formInfo.cvgStartDate;
    this.cvgEndDate = formInfo.cvgEndDate;

    let startDate = new Date(this.cvgStartDate);
    startDate.setDate(startDate.getDate() - 1);

    if ((!this._uService.compareDatesAfter((new Date(receiptDate)), new Date(this.cvgEndDate)) ||
      this._uService.compareDatesAfter((new Date(receiptDate)), startDate))) {
      this.receiptDateErr = true;
      this.schedH5.controls['receipt_date'].setErrors({ 'incorrect': true });
    } else {
      this.receiptDateErr = false;
    }

  }

  public handleOnBlurEvent($event: any, col: any) {

    let val = 0;
    if (this.schedH5.get('transferred_amount').value) {
      val = this.convertFormattedAmountToDecimal(this.schedH5.get('transferred_amount').value);
    }

    const entry = $event.target.value.replace(/,/g, ``);
    if (this.isNumber(entry)) {
      this.transferredAmountErr = false;
      //this.schedH5.patchValue({transferred_amount: this._decPipe.transform(
      //  this.convertFormattedAmountToDecimal(entry), '.2-2')}, { onlySelf: true });
      this.schedH5.patchValue({
        transferred_amount: this._decPipe.transform(
          this.convertFormattedAmountToDecimal(
            this.schedH5.get('transferred_amount').value), '.2-2')
      }, { onlySelf: true });
      this.schedH5.controls['transferred_amount'].setErrors(null);

      if (this.scheduleAction === ScheduleActions.edit) {
        this.schedH5.patchValue({
          total_amount_transferred: this._decPipe.transform(
            this.total_amount_edit - this.transferred_amount_edit + val, '.2-2')
        }, { onlySelf: true });
      }
    } else {
      this.transferredAmountErr = true
      this.schedH5.controls['transferred_amount'].setErrors({ 'incorrect': true });
    }
  }

  private convertFormattedAmountToDecimal(formatedAmount: string): number {
    if (!formatedAmount) {
      formatedAmount = '0'
    }
    if (typeof formatedAmount === 'string') {
      // remove commas
      formatedAmount = formatedAmount.replace(/,/g, ``);
      return parseFloat(formatedAmount);
    } else {
      return formatedAmount;
    }
  }

  private isNumber(value: string | number): boolean {
    return ((value != null) && !isNaN(Number(value.toString())));
  }

  public clearFormValues() {
    this.setH5(this.config.currentPage);
    this.h5Entries = [];
    this.h5Ratios = {};
    this.h5Ratios['child'] = [];
    this.transferredAmountErr = false;
    if (this.scheduleAction === ScheduleActions.edit) {
      this.scheduleAction = ScheduleActions.add;
    }
  }

  public editH5(item: any) {
    this.returnToAdd();
    this.scheduleAction = ScheduleActions.edit;

    this.transaction_id = item.transaction_id;
    this.back_ref_transaction_id = item.back_ref_transaction_id;

    this.setCategory();

    if (item.transfer_type === 'Voter ID') {
      this.schedH5.patchValue({ category: 'voter_id' }, { onlySelf: true });
    } else if (item.transfer_type === 'Voter Registration') {
      this.schedH5.patchValue({ category: 'voter_registration' }, { onlySelf: true });
    } else if (item.transfer_type === 'Generic Campaign') {
      this.schedH5.patchValue({ category: 'generic_campaign' }, { onlySelf: true });
    } else if (item.transfer_type === 'GOTV') {
      this.schedH5.patchValue({ category: 'gotv' }, { onlySelf: true });
    }

    this.schedH5.patchValue({ account_name: item.account_name }, { onlySelf: true });
    this.schedH5.patchValue({ receipt_date: item.receipt_date }, { onlySelf: true });
    this.schedH5.patchValue({ transferred_amount: this._decPipe.transform(item.transfer_amount, '.2-2') }, { onlySelf: true });
    this.schedH5.patchValue({ total_amount_transferred: this._decPipe.transform(item.total_amount_transferred, '.2-2') }, { onlySelf: true });
    this.schedH5.patchValue({ memo_text: item.memo_text }, { onlySelf: true });
    this.transferred_amount_edit = item.transfer_amount;
    this.total_amount_edit = item.total_amount_transferred;

  }

  public saveEdit() {
    if (this.schedH5.status === 'VALID') {
      this.saveAddMore();
      this.addEntries();
      this.returnToSum();
    } else {
      this.schedH5.markAsDirty();
      this.schedH5.markAsTouched();
      this.isSubmit = true;
    }
  }

  public editH5Sub(item: any) {

    this.setCategory();

    if (item.transfer_type === 'Voter ID') {
      this.schedH5.patchValue({ category: 'voter_id' }, { onlySelf: true });
    } else if (item.transfer_type === 'Voter Registration') {
      this.schedH5.patchValue({ category: 'voter_registration' }, { onlySelf: true });
    } else if (item.transfer_type === 'Generic Campaign Activities') {
      this.schedH5.patchValue({ category: 'generic_campaign' }, { onlySelf: true });
    } else if (item.transfer_type === 'GOTV') {
      this.schedH5.patchValue({ category: 'gotv' }, { onlySelf: true });
    }

    this.schedH5.patchValue({ category: item.category }, { onlySelf: true });

    this.schedH5.patchValue({ account_name: item.account_name }, { onlySelf: true });
    this.schedH5.patchValue({ receipt_date: item.receipt_date }, { onlySelf: true });
    this.schedH5.patchValue({
      transferred_amount: this._decPipe.transform(
        this.convertFormattedAmountToDecimal(item.transferred_amount), '.2-2')
    }, { onlySelf: true });
    this.schedH5.patchValue({ memo_text: item.meo_text }, { onlySelf: true });
    this.h5Entries = this.h5Entries.filter(obj => obj !== item);
    this.h5Ratios.child = this.h5Ratios.child.filter(obj => obj !== item);

    let sum = 0;
    this.h5Entries.forEach(obj => {
      sum += this.convertFormattedAmountToDecimal(obj.transferred_amount);
    })

    this.schedH5.patchValue({
      total_amount_transferred:
        this._decPipe.transform(sum, '.2-2')
    }, { onlySelf: true });

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
              //this.getTransactionsPage(this.config.currentPage);
              this.setH5Sum(this.config.currentPage);
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

  public trashSubTransaction(trx: any): void {
    this._dlService
      .confirm('You are about to delete this transaction.', ConfirmModalComponent, 'Caution!')
      .then(res => {
        if (res === 'okay') {
          this.h5Entries = this.h5Entries.filter(obj => obj !== trx);
          this.h5Ratios.child = this.h5Ratios.child.filter(obj => obj !== trx);
          this.config.totalItems = this.h5Entries.length;

          let sum = 0;
          this.h5Entries.forEach(obj => {
            sum += this.convertFormattedAmountToDecimal(obj.transferred_amount);
          })

          this.schedH5.patchValue({
            total_amount_transferred:
              this._decPipe.transform(sum, '.2-2')
          }, { onlySelf: true });

          this._dlService.confirm(
            'Transaction has been successfully deleted.',
            ConfirmModalComponent,
            'Success!',
            false,
            ModalHeaderClassEnum.successHeader
          );
        } else if (res === 'cancel') {
        }
      });
  }

  public goSummary(): void {
    this.canDeactivate().then(result => {
      if (result === true) {
        localStorage.removeItem(`form_${this.formType}_saved`);
        this.returnToSum();
      }
    });
  }

  public cancelReturnToSum(): void {
    this.canDeactivate().then(result => {
      if (result === true) {
        localStorage.removeItem(`form_${this.formType}_saved`);
        this.returnToSum();
      }
    });
  }

  private _noH1H2Popup(category: string) {

    let activityEventScheduleType = '';
    if (category === 'DC' || category === 'DF') {
      activityEventScheduleType = 'sched_h2'
    } else {
      activityEventScheduleType = 'sched_h1'
    }

    const report_id = this._individualReceiptService.getReportIdFromStorage(this.formType);

    this.getH1H2ExistSubscription = this._schedH5Service.getH1H2ExistStatus(report_id, category)
      .subscribe(res => {
        if (res) {
          if (res.count === 0) {

            this.saveAndAddDisabled = true;

            const scheduleName = activityEventScheduleType === 'sched_h1' ? 'H1' : 'H2';
            const scheduleType = activityEventScheduleType;

            const message =
              `Please add Schedule ${scheduleName} before proceeding with adding the ` +
              `amount.  Schedule ${scheduleName} is required to correctly allocate the federal and non-federal portions of the transaction.`;
            this._dlService.confirm(message, ConfirmModalComponent, 'Warning!', false).then(res => {
              if (res === 'okay') {
                const emitObj: any = {
                  form: this.frmIndividualReceipt,
                  direction: 'next',
                  step: 'step_3',
                  previousStep: 'step_2',
                  scheduleType: scheduleType,
                  action: ScheduleActions.add
                };
                if (scheduleType === 'sched_h2') {
                  emitObj.transactionType = 'ALLOC_H2_RATIO';
                  emitObj.transactionTypeText = 'Allocation Ratios';
                }
                this.status.emit(emitObj);
              } else if (res === 'cancel') {
              }
            });
          } else {
            this.saveAndAddDisabled = false;
          }
        }
      }
      )
  }

  public printTransaction(trx: any): void {
    this._reportTypeService.printPreview('transaction_table_screen', '3X', trx.transaction_id);
  }

  /**
   * The records for a given page.
   *
   * @param page the page containing the records to get
   */
  public getPage(page: number): void {
    switch (this.transactionType) {
      case 'ALLOC_H5_SUM':
        this.setH5Sum(page);
        break;
      case 'ALLOC_H5_RATIO':
        this.setH5(page);
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
    let items: any[];
    switch (this.transactionType) {
      case 'ALLOC_H5_SUM':
        items = this.h5Sum;
        break;
      case 'ALLOC_H5_RATIO':
        items = this.h5Entries;
        break;
    }

    let range: {
      firstItemOnPage: number, lastItemOnPage: number, itemRange: string
    } = this._utilService.determineItemRange(this.config, items);

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
