import { animate, style, transition, trigger } from '@angular/animations';
import { CurrencyPipe, DatePipe, DecimalPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, EventEmitter, Input, OnChanges, OnDestroy, OnInit, Output, SimpleChanges, ViewEncapsulation , ChangeDetectionStrategy } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { Subscription, Subject } from 'rxjs';
import { ContactsService } from 'src/app/contacts/service/contacts.service';
import { ReportsService } from 'src/app/reports/service/report.service';
import { ConfirmModalComponent, ModalHeaderClassEnum } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { FormsService } from 'src/app/shared/services/FormsService/forms.service';
import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { ContributionDateValidator } from 'src/app/shared/utils/forms/validation/contribution-date.validator';
import { UtilService } from 'src/app/shared/utils/util.service';
import { AbstractSchedule } from '../form-3x/individual-receipt/abstract-schedule';
import { AbstractScheduleParentEnum } from '../form-3x/individual-receipt/abstract-schedule-parent.enum';
import { IndividualReceiptService } from '../form-3x/individual-receipt/individual-receipt.service';
import { ScheduleActions } from '../form-3x/individual-receipt/schedule-actions.enum';
import { ReportTypeService } from '../form-3x/report-type/report-type.service';
import { F3xMessageService } from '../form-3x/service/f3x-message.service';
import { SchedHMessageServiceService } from '../sched-h-service/sched-h-message-service.service';
import { SchedHServiceService } from '../sched-h-service/sched-h-service.service';
import { TransactionModel } from '../transactions/model/transaction.model';
import { TransactionsMessageService } from '../transactions/service/transactions-message.service';
import { GetTransactionsResponse, TransactionsService } from '../transactions/service/transactions.service';
import { SchedH2Service } from './sched-h2.service';


@Component({
  selector: 'app-sched-h2',
  templateUrl: './sched-h2.component.html',
  styleUrls: ['./sched-h2.component.scss'],
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
export class SchedH2Component extends AbstractSchedule implements OnInit, OnDestroy, OnChanges {
  @Input() transactionTypeText: string;
  @Input() transactionType: string;
  @Input() scheduleAction: ScheduleActions;
  @Input() scheduleType: string;
  @Input() transactionData: any;

  @Output() status: EventEmitter<any>;

  public formType: string;  
  public showPart2: boolean;
  public loaded = false;
  public schedH2: FormGroup;
   
  public h2Subscription: Subscription;
  public h2Sum: any;
  public saveHRes: any;

  public tableConfig: any;
  public receiptDateErr = false;

  public cvgStartDate: any;
  public cvgEndDate: any;

  public isSubmit = false;

  public transaction_id: string;


  public cloned = false;
  populateFormForEdit: Subscription;

  public fedRatio: number;
  public nonfedRatio: number;
  private _H2onDestroy$ = new Subject();

  public restoreSubscription: Subscription;
  public trashSubscription: Subscription;

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
    private _actRoute: ActivatedRoute,
    private _schedH2Service: SchedH2Service,
    private _individualReceiptService: IndividualReceiptService,
    private _uService: UtilService,
    private _decPipe: DecimalPipe,
    private _tranMessageService: TransactionsMessageService,
    private _datePipe: DatePipe,
    private _schedHMessageServiceService: SchedHMessageServiceService,
    private _schedHService: SchedHServiceService,
    private _tranService: TransactionsService,
    private _dlService: DialogService,
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
      _schedHMessageServiceService
    );
    _schedH2Service;
    _individualReceiptService;
    _uService;
    _decPipe;
    _datePipe;
    _tranService;
    _dlService;

    this._tranMessageService
      .getEditTransactionMessage()
      .takeUntil(this._H2onDestroy$)
      .subscribe((trx: TransactionModel) => {
        //console.log(trx.transactionTypeIdentifier + 'tranc iden');
        if (trx.transactionTypeIdentifier === 'ALLOC_H2_RATIO') {
          this.editH2(trx);
        }
      });

    this._schedHMessageServiceService.getpopulateHFormForEditMessage()
    .takeUntil(this._H2onDestroy$)
    .subscribe(p => {
      if(p.scheduleType === 'Schedule H2' || p.scheduleType === 'sched_h2'){
        let res = this._schedHService.getSchedule(p.transactionDetail.transactionModel).subscribe(res => {
          if(res && res.length === 1){
            this.editH2(res[0]);
          }
        });
      }
    })

    this.restoreSubscription = this._tranMessageService
        .getRestoreTransactionsMessage()
        .subscribe(
          message => {
            if(message.scheduleType === 'Schedule H2') {
              this.getH2Sum(this._individualReceiptService.getReportIdFromStorage(this.formType));
            }
          }
        )

    this.trashSubscription = this._tranMessageService
        .getRemoveHTransactionsMessage()
        .subscribe(
          message => {
            if(message.scheduleType === 'Schedule H2') {
              this.getH2Sum(this._individualReceiptService.getReportIdFromStorage(this.formType));
            }
          }
        )
  }


  public ngOnInit() {
    this.abstractScheduleComponent = AbstractScheduleParentEnum.schedH2Component;
    // temp code - waiting until dynamic forms completes and loads the formGroup
    // before rendering the static fields, otherwise validation error styling
    // is not working (input-error-field class).  If dynamic forms deliver,
    // the static fields, then remove this or set a flag when formGroup is ready
    setTimeout(() => {
      this.loaded = true;
    }, 2000);

    //this.getH2Sum(this.getReportId());
    //this.getH2Sum(this._individualReceiptService.getReportIdFromStorage(this.formType));
    
    this.setSchedH2();

    this.tableConfig = {
      itemsPerPage: 8,
      currentPage: 1,
      totalItems: 10
    };

    this.setDefaultValues();

    this.formType = this._actRoute.snapshot.paramMap.get('form_id');

    this.schedH2.patchValue({ select_activity_function: ''}, { onlySelf: true });
    this.sendPopulateMessageIfApplicable();
   
  }

  pageChanged(event){
    this.tableConfig.currentPage = event;
  }

  public ngOnChanges(changes: SimpleChanges) {
    // OnChanges() can be triggered before OnInit().  Ensure formType is set.
    this.formType = '3X';

    if(this.transactionType === 'ALLOC_H2_SUM') {
      this.getH2Sum(this._individualReceiptService.getReportIdFromStorage(this.formType));
    }
  }

  ngDoCheck() {
    //TODO -- memory consumption, need to contain in an if statement or not do it in ngDoCheck
    this.status.emit({
      otherSchedHTransactionType: this.transactionType
    });
    if(!this.schedH2.get('ratio_code').value) {
      this.schedH2.patchValue({ratio_code:'n'}, { onlySelf: true });
    }
  }

  public ngOnDestroy(): void {

    this._H2onDestroy$.next(true);
    this.restoreSubscription.unsubscribe();
    this.trashSubscription.unsubscribe();
    super.ngOnDestroy();
  }

  setDefaultValues() {
    this.schedH2.patchValue({ratio_code:'n'}, { onlySelf: true });
  }

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

  public setSchedH2() {
    this.schedH2 = new FormGroup({      
      activity_event_name: new FormControl('', [Validators.maxLength(90), Validators.required]),
      receipt_date: new FormControl(''),
      select_activity_function: new FormControl('', Validators.required),
      //fundraising: new FormControl('', Validators.required),
      //direct_cand_support: new FormControl('', Validators.required),
      ratio_code: new FormControl(''),
      federal_percent: new FormControl('', [Validators.min(0), Validators.max(100), Validators.required]),
      non_federal_percent: new FormControl('', [Validators.min(0), Validators.max(100), Validators.required])
    });
  }
  
  public clearFormValues() {
    this.schedH2.reset();
    if(this.scheduleAction === ScheduleActions.edit) {
      this.scheduleAction = ScheduleActions.add
    }
    this.cloned = false;
  }

  public saveAndAddMore(): void {
    this.isSubmit = true;
    this.doValidate();    
  }

  public doValidate() {
    if(this.schedH2.status === 'VALID') {
    
    //this.schedH2.patchValue({ fundraising: this.schedH2.get('select_activity_function').value === 'f' ? true : false }, { onlySelf: true });
    //this.schedH2.patchValue({ direct_cand_support: this.schedH2.get('select_activity_function').value === 'd' ? true : false }, { onlySelf: true });

    const formObj = this.schedH2.getRawValue();

    //formObj['report_id'] = 0;
    formObj['report_id'] = this._individualReceiptService.getReportIdFromStorage(this.formType);
    formObj['transaction_type_identifier'] = "ALLOC_H2_RATIO";

    formObj['fundraising'] = this.schedH2.get('select_activity_function').value === 'f' ? true : false ;
    formObj['direct_cand_support'] = this.schedH2.get('select_activity_function').value === 'd' ? true : false;
    
    formObj['federal_percent'] = ((this.schedH2.get('federal_percent').value) / 100).toFixed(2);
    formObj['non_federal_percent'] = ((this.schedH2.get('non_federal_percent').value) / 100).toFixed(2);

    if(this.scheduleAction === ScheduleActions.edit) {
      formObj['transaction_id'] = this.transaction_id
    };
    
    const serializedForm = JSON.stringify(formObj);

    this.isSubmit = true;

    //if(this.schedH2.status === 'VALID') {
      //&& (this.schedH2.get('federal_percent').value + this.schedH2.get('non_federal_percent').value) === 100) {

      this.saveH2Ratio(serializedForm, this.scheduleAction);
      this.schedH2.reset();
      this.isSubmit = false;
    }else {
      this.schedH2.markAsDirty();
      this.schedH2.markAsTouched();
    }
  }

  public getH2Sum(reportId: string) {
    
    this.h2Subscription = this._schedH2Service.getSummary(reportId).subscribe(res =>
      {        
        if(res) {
          this.h2Sum = [];
          this.h2Sum =  res;         
          this.tableConfig.totalItems = res.length;           
        }
      });        
  }

  public saveH2Ratio(ratio: any, scheduleAction) {
    
    this._schedH2Service.saveH2Ratio(ratio, scheduleAction).subscribe(res => {
      if (res) {        
        this.saveHRes = res;
      }
    });
  }
 
  public returnToSum(): void {
    this.isSubmit = true;
    if(this.schedH2.pristine) {
      this.transactionType = 'ALLOC_H2_SUM';
      this.getH2Sum(this._individualReceiptService.getReportIdFromStorage(this.formType));
    }else {
      if(this.schedH2.status === 'VALID') {

        this.saveAndAddMore();

        if( this.scheduleAction === ScheduleActions.edit) {
          this.scheduleAction = ScheduleActions.add;
        }

        this.isSubmit = false;

        this.schedH2.reset();

        this.transactionType = 'ALLOC_H2_SUM';

        this.receiptDateErr = false;

        this.getH2Sum(this._individualReceiptService.getReportIdFromStorage(this.formType));
      }else {
        //this.isSubmit = true;
        if((this.schedH2.get('activity_event_name').value === '' ||
            this.schedH2.get('activity_event_name').value === null)  &&
            this.schedH2.get('select_activity_function').value === null &&
            this.schedH2.get('federal_percent').value === null &&
            this.schedH2.get('non_federal_percent').value === null &&
            this.schedH2.get('receipt_date').value === null) {
          this.transactionType = 'ALLOC_H2_SUM';
          this.getH2Sum(this._individualReceiptService.getReportIdFromStorage(this.formType));
        }else {
          this._dlService
          .confirm('You have unsaved changes! If you leave, your changes will be lost.', ConfirmModalComponent, 'Caution!')
          .then(res => {
            if (res === 'okay') {
              this.schedH2.reset();
              this.transactionType = 'ALLOC_H2_SUM';
              this.receiptDateErr = false;
              this.getH2Sum(this._individualReceiptService.getReportIdFromStorage(this.formType));
              //this.isSubmit = true;
              this.schedH2.markAsDirty();
              this.schedH2.markAsTouched();
              window.scrollTo(0, 0);
            } else if (res === 'cancel') {
            }
          });
        }
      }

    }

  }

  public returnToAdd(): void {
    this.transactionType = 'ALLOC_H2_RATIO';

    this.receiptDateErr = false;
    this.isSubmit = false;
  }

  public receiptDateChanged(receiptDate: string) {

    const formInfo = JSON.parse(localStorage.getItem('form_3X_report_type'));
    this.cvgStartDate = formInfo.cvgStartDate;
    this.cvgEndDate = formInfo.cvgEndDate;

    let startDate =  new Date(this.cvgStartDate);
    startDate.setDate(startDate.getDate() - 1);

    if ((!this._uService.compareDatesAfter((new Date(receiptDate)), new Date(this.cvgEndDate)) ||
      this._uService.compareDatesAfter((new Date(receiptDate)), startDate))) {
      this.receiptDateErr = true;
      this.schedH2.controls['receipt_date'].setErrors({'incorrect': true});  
    } else {
      this.receiptDateErr = false;
    }

  }
 
  public handleFedPercentFieldKeyup(e) {
    if(e.target.value <= 100) {
      this.schedH2.patchValue({ non_federal_percent:
        this._decPipe.transform(Number(100 - e.target.value), '.2-2')}, { onlySelf: true });
    }else {
      this.schedH2.patchValue({ non_federal_percent: 0}, { onlySelf: true });
    }
  }

  public handleNonFedPercentFieldKeyup(e) {
    if(e.target.value <= 100) {
      this.schedH2.patchValue({ federal_percent:
        this._decPipe.transform(Number(100 - e.target.value), '.2-2')}, { onlySelf: true });
    }else {
      this.schedH2.patchValue({ federal_percent: 0}, { onlySelf: true }); 
    }
  }

  public handleOnFedBlurEvent(e) {
    if(e.target.value <= 100) {
      this.schedH2.patchValue({ non_federal_percent:
        this._decPipe.transform(Number(100 - e.target.value), '.2-2')}, { onlySelf: true });
      this.schedH2.patchValue({ federal_percent:
        this._decPipe.transform(Number(e.target.value), '.2-2')}, { onlySelf: true });
    }else {
      this.schedH2.patchValue({ non_federal_percent: 0}, { onlySelf: true });
    }
    this.setRatioCodeWithValueChange(e.target.value);
  }

  public handleOnNonFedBlurEvent(e) {
    if(e.target.value <= 100) {
      this.schedH2.patchValue({ federal_percent:
        this._decPipe.transform(Number(100 - e.target.value), '.2-2')}, { onlySelf: true });
      this.schedH2.patchValue({ non_federal_percent:
        this._decPipe.transform(e.target.value, '.2-2')}, { onlySelf: true });
    }else {
      this.schedH2.patchValue({ federal_percent: 0}, { onlySelf: true });
    }
    this.setRatioCodeWithValueChange(e.target.value); 
  }

  public editH2(item: any) {
    this.returnToAdd();
    this.scheduleAction = ScheduleActions.edit;

    this.transaction_id = item.transaction_id;

    this.schedH2.patchValue({ activity_event_name: item.activity_event_name}, { onlySelf: true });
    this.schedH2.patchValue({ receipt_date: item.receipt_date}, { onlySelf: true });
    this.schedH2.patchValue({ select_activity_function: item.event_type  === 'fundraising' ? 'f' : 'd'}, { onlySelf: true });
    this.schedH2.patchValue({ ratio_code: item.ratio_code}, { onlySelf: true });
    this.schedH2.patchValue({ federal_percent: this._decPipe.transform(item.federal_percent * 100, '.2-2')}, { onlySelf: true });
    this.schedH2.patchValue({ non_federal_percent: this._decPipe.transform(item.non_federal_percent * 100, '.2-2')}, { onlySelf: true });

    this.fedRatio = item.federal_percent * 100;
    this.nonfedRatio = item.non_federal_percent * 100;

    /* for all transaction edit
    this.transaction_id = item.transactionId;

    this.schedH2.patchValue({ activity_event_name: item.activity_event_name}, { onlySelf: true });
    this.schedH2.patchValue({ receipt_date: item.date}, { onlySelf: true });
    this.schedH2.patchValue({ select_activity_function: item.entityType  === 'fundraising' ? 'f' : 'd'}, { onlySelf: true });
    this.schedH2.patchValue({ ratio_code: 's'}, { onlySelf: true });
    this.schedH2.patchValue({ federal_percent: this._decPipe.transform(item.federalPercent * 100, '.2-2')}, { onlySelf: true });
    this.schedH2.patchValue({ non_federal_percent: this._decPipe.transform(item.nonfederalPercent * 100, '.2-2')}, { onlySelf: true });
    */

  }

  public saveEdit() {
    if(this.schedH2.status === 'VALID') {
      this.fedRatio = 0;
      this.nonfedRatio = 0;
      this.returnToSum();
    }else {
      this.schedH2.markAsDirty();
      this.schedH2.markAsTouched();
      this.isSubmit = true;
    }
  }

  public cancelReturnToSum(): void {

    if( this.scheduleAction === ScheduleActions.edit) {
      this.scheduleAction = ScheduleActions.add;
    }

    this.isSubmit = false;

    this.schedH2.reset();

    this.transactionType = 'ALLOC_H2_SUM';

    this.receiptDateErr = false;

    this.getH2Sum(this._individualReceiptService.getReportIdFromStorage(this.formType));

    this.cloned = false;

  }

  public cloneH2(item: any) {
    this.returnToAdd();
    this.scheduleAction = ScheduleActions.edit;
    this.cloned = true;

    this.transaction_id = item.transaction_id;

    this.schedH2.patchValue({ activity_event_name: item.activity_event_name}, { onlySelf: true });

    const today: any = new Date();
    this.schedH2.patchValue({ receipt_date: this._datePipe.transform(today, 'yyyy-MM-dd')}, { onlySelf: true });

    this.schedH2.patchValue({ select_activity_function: item.event_type  === 'fundraising' ? 'f' : 'd'}, { onlySelf: true });
    this.schedH2.patchValue({ ratio_code: item.ratio_code }, { onlySelf: true });

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
              this.getH2Sum(trx.report_id);
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

  public setRatioCodeWithValueChange(ratio: number) {
    if(this.schedH2.get('ratio_code').value === 's' &&
       (this.schedH2.get('federal_percent').value !== this.fedRatio ||
       this.schedH2.get('non_federal_percent').value !== this.nonfedRatio)
    ) {
        this.schedH2.patchValue({ratio_code:'r'}, { onlySelf: true });
    }else if(this.schedH2.get('ratio_code').value === 'r' &&
      Number(this.schedH2.get('federal_percent').value) === this.fedRatio &&
      Number(this.schedH2.get('non_federal_percent').value) === this.nonfedRatio) {
        this.schedH2.patchValue({ratio_code:'s'}, { onlySelf: true });
    }
  }

  public printTransaction(trx: any): void {
    this._reportTypeService.printPreview('transaction_table_screen', '3X', trx.transaction_id);
  }
}

