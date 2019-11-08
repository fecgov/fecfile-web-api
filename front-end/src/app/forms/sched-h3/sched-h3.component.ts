import { Component, OnInit, OnDestroy, OnChanges, Output, EventEmitter, Input, SimpleChanges } from '@angular/core';
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
import { TransactionsService } from '../transactions/service/transactions.service';
import { HttpClient } from '@angular/common/http';
import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { ScheduleActions } from '../form-3x/individual-receipt/schedule-actions.enum';
import { AbstractSchedule } from '../form-3x/individual-receipt/abstract-schedule';
import { ReportsService } from 'src/app/reports/service/report.service';
import { TransactionModel } from '../transactions/model/transaction.model';
import { Observable, Subscription } from 'rxjs';
import { SchedH3Service } from './sched-h3.service';

@Component({
  selector: 'app-sched-h3',
  templateUrl: './sched-h3.component.html',
  styleUrls: ['./sched-h3.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe]
})
export class SchedH3Component extends AbstractSchedule implements OnInit, OnDestroy, OnChanges {
  @Input() transactionTypeText: string;
  @Input() transactionType: string;
  @Input() scheduleAction: ScheduleActions;
  @Output() status: EventEmitter<any>;

  public formType: string;
  public showPart2: boolean;
  public loaded = true; //false;

  public schedH3: FormGroup;
  public categories: any;
  public identifiers: any;
  public totalName: any;
  public showIdentiferSelect = false;
  public showIdentifer = false;
  public h3Sum: any;
  public h3SumP: any;
  public h3Entries = [];
  public h3Ratios: any;
  public showAggregateAmount = false;

  public h3Subscription: Subscription;
  public saveHRes: any;

  public h3TableConfig: any;
  public h3EntryTableConfig: any;

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
    private _schedH3Service: SchedH3Service,
    private _individualReceiptService: IndividualReceiptService
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
      _reportsService      
    );
    _schedH3Service;
    _individualReceiptService;
  }

  public ngOnInit() {
    this.formType = '3X';
    this.formFieldsPrePopulated = true;
    // this.formFields = this._staticFormFields;
    super.ngOnInit();
    this.showPart2 = false;
    //this.transactionType = 'OPEXP'; // 'INDV_REC';
    //this.transactionTypeText = 'Coordinated Party Expenditure Debt to Vendor';
    super.ngOnChanges(null);
    
    console.log();

    // temp code - waiting until dynamic forms completes and loads the formGroup
    // before rendering the static fields, otherwise validation error styling
    // is not working (input-error-field class).  If dynamic forms deliver,
    // the static fields, then remove this or set a flag when formGroup is ready
    setTimeout(() => {
      this.loaded = true;
    }, 2000);

    this.setH3();
    this.setCategory();
    //this.setActivityOrEventIdentifier();

    this.h3TableConfig = {
      itemsPerPage: 8,
      currentPage: 1,
      totalItems: 8
    };
    this.h3EntryTableConfig = {
      itemsPerPage: 3,
      currentPage: 1,
      totalItems: 3
    };
    

    this.setH3Sum();
    this.setH3SumP();

    this.formType = this._actRoute.snapshot.paramMap.get('form_id');

    this.h3Ratios = {};
    this.h3Ratios['child'] = [];
    
  }

  public ngOnChanges(changes: SimpleChanges) {
    // OnChanges() can be triggered before OnInit().  Ensure formType is set.
    this.formType = '3X';
    this.showPart2 = false;    
  }

  public ngOnDestroy(): void {
    super.ngOnDestroy();
  }

  pageChanged(event){
    this.h3TableConfig.currentPage = event;
  }
  entryPageChanged(event){
    this.h3EntryTableConfig.currentPage = event;
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

  public setH3() {

    this.schedH3 = new FormGroup({
      account_name: new FormControl('', [Validators.maxLength(40), Validators.required]),
      receipt_date: new FormControl(''),
      total_amount_transferred: new FormControl(''),
      category: new FormControl(''),
      activity_event_name: new FormControl(''),
      transferred_amount: new FormControl(''),
      aggregate_amount: new FormControl('')
    });
  }

  public setCategory() {

    this.categories = [
      {
        "id":"AD",
        "name":"Total Administrative"
      },
      {
        "id":"GV",
        "name":"Generic Voter Drive"
      },
      {
        "id":"EA",
        "name":"Exempt Activities"
      },
      {
        "id":"DF",
        "name":"Direct Fundraising"
      },
      {
        "id":"DC",
        "name":"Direct Candidate Support"
      },
      {
        "id":"PC",
        "name":"Public Communications Referring Only to Party(Made by PAC)"
      }
    ]

  }
  
  public setActivityOrEventIdentifier(category: string) {

    this.identifiers = [];
    this.h3Subscription = 
      this._schedH3Service.getActivityOrEventIdentifiers(category)
      .subscribe(res =>
        {
          if(res) {            
            this.identifiers = res;
          }
        }
      ); 

  }

  public getTotalAmount(activity_event_type: string) {

    this.schedH3.patchValue({total_tmount_of_transfer: 0}, { onlySelf: true });
    const reportId = this._individualReceiptService.getReportIdFromStorage(this.formType);
    this.h3Subscription = 
      this._schedH3Service.getTotalAmount(activity_event_type, reportId)
      .subscribe(res =>
        {
          if(res) {            
            this.schedH3.patchValue({aggregate_amount: res.aggregate_amount}, { onlySelf: true });
          }
        }
      ); 

    return;
  }

  public returnToSum(): void {
    this.transactionType = 'ALLOC_H3_SUM';    
  }

  public returnToAdd(): void {
    this.transactionType = 'ALLOC_H3_RATIO';    
  }

  //to test for privous
  public resetTransactionType() {
    this.transactionType = '';
  }

  public selectCategoryChange(e) {
    
    if(!this.schedH3.get('category').value) {
      this.showIdentifer = false;
    }else{
      this.showIdentifer = true;
    }
    
    if(this.schedH3.get('category').value === 'AD') {
      this.totalName = 'Administrative';
      this.showIdentiferSelect = false;
      this.showAggregateAmount = false;
    }else if(this.schedH3.get('category').value === 'GV') {
      this.totalName = 'Generic Voter Drive';
      this.showIdentiferSelect = false;
      this.showAggregateAmount = false;
    }else if(this.schedH3.get('category').value === 'EA') {
      this.totalName = 'Exempt Activities';
      this.showIdentiferSelect = false
      this.showAggregateAmount = false;
    }else if(this.schedH3.get('category').value === 'DF') {
      this.totalName = 'Activity or Event Identifier';
      this.setActivityOrEventIdentifier('fundraising');
      this.showIdentiferSelect = true;
      this.showAggregateAmount = true;
    }else if(this.schedH3.get('category').value === 'DC') {
      this.totalName = 'Activity or Event Identifier';
      this.setActivityOrEventIdentifier('direct_can_support');
      this.showIdentiferSelect = true;
      this.showAggregateAmount = true;
    }else if(this.schedH3.get('category').value === 'PC') {
      this.totalName = 'Public Communications';
      this.showIdentiferSelect = false;
      this.showAggregateAmount = false;
    }
    
  }

  public selectActivityOrEventChange(e) {
    const reportId = this._individualReceiptService.getReportIdFromStorage(this.formType);
    this._schedH3Service.getTotalAmount(this.schedH3.get('category').value, reportId);
  }

  public setH3Sum() {

    const reportId = this._individualReceiptService.getReportIdFromStorage(this.formType);
    
    //this.h3Subscription = this._schedH3Service.getSummary(this.getReportId()).subscribe(res =>
    this.h3Subscription = this._schedH3Service.getSummary(reportId).subscribe(res =>
      {        
        if(res) {          
          this.h3Sum =  res;         
          this.h3TableConfig.totalItems = res.length;
        }
      });   
    
  }

  public setH3SumP() {

    this.h3Subscription = this._schedH3Service.getBreakDown(this.getReportId()).subscribe(res =>
      {        
        if(res) {          
          this.h3SumP =  res;          
        }
      });     

  }

  public saveAndAddMore(): void {
    this.doValidate();    
  }

  public doValidate() {

    //this.h3Ratios = {};

    const reportId = this._individualReceiptService.getReportIdFromStorage(this.formType);
    
    this.h3Ratios['report_id'] = reportId;
    this.h3Ratios.transaction_type_identifier = 'TRAN_FROM_NON_FED_ACC';
    
    //this.h3Ratios.total_amount_transferred = this.schedH3.get('total_amount_transferred').value;

    const formObj = this.schedH3.getRawValue();

    const accountName = this.schedH3.get('account_name').value;
    const receipt_date = this.schedH3.get('receipt_date').value;
    
    const total_amount_transferred = Number(this.schedH3.get('total_amount_transferred').value) 
      + Number(this.schedH3.get('transferred_amount').value);
    this.h3Ratios.total_amount_transferred = total_amount_transferred;
 
    formObj['report_id'] = this.getReportId();
    formObj['transaction_type_identifier'] = 'TRAN_FROM_NON_FED_ACC';
    formObj['activity_event_type'] = this.schedH3.get('category').value;

    if(this.schedH3.status === 'VALID') {     
      this.h3Entries.push(formObj);
      this.h3EntryTableConfig.totalItems = this.h3Entries.length;
      this.h3Ratios.child.push(formObj);

      this.schedH3.reset();
      
      this.schedH3.patchValue({account_name: accountName}, { onlySelf: true });
      this.schedH3.patchValue({receipt_date: receipt_date}, { onlySelf: true });

      this.schedH3.patchValue({total_amount_transferred: total_amount_transferred}, { onlySelf: true });

      if(this.showAggregateAmount) {
        const aggregate_amount = Number(this.schedH3.get('aggregate_amount').value) + Number(this.schedH3.get('transferred_amount').value);
        this.schedH3.patchValue({aggregate_amount: aggregate_amount}, { onlySelf: true });
      }else {
        this.schedH3.patchValue({aggregate_amount: 0}, { onlySelf: true });
      }
      
      this.schedH3.patchValue({category: ''}, { onlySelf: true });
      this.showIdentifer = false;
    }
  }

  public saveH3Ratio(ratio: any) {
    
    this._schedH3Service.saveH3Ratio(ratio).subscribe(res => {
      if (res) {        
        this.saveHRes = res;
        this.h3Entries = [];
      }
    });
  }

  public addEntries() {
    const serializedForm = JSON.stringify(this.h3Ratios);
    this.saveH3Ratio(serializedForm);
  }

  //(keyup)="handleAmountKeyup($event, col)"
  public handleAmountKeyup(e: any) {
    let val = e.target.value;

    const total_amount_transferred = Number(this.schedH3.get('total_amount_transferred').value) 
      + Number(e.target.value);

    this.schedH3.patchValue({total_amount_transferred: total_amount_transferred}, { onlySelf: true });

    if(this.showAggregateAmount) {
      const aggregate_amount = Number(this.schedH3.get('aggregate_amount').value) + Number(e.target.value);
      this.schedH3.patchValue({aggregate_amount: aggregate_amount}, { onlySelf: true });
    }else {
      this.schedH3.patchValue({aggregate_amount: 0}, { onlySelf: true });
    }
  }

}
