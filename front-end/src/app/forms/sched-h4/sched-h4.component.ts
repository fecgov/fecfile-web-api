import { Component, OnInit, OnDestroy, OnChanges, Output, EventEmitter, Input, SimpleChanges, ViewEncapsulation } from '@angular/core';
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
import { style, animate, transition, trigger } from '@angular/animations';
import { PaginationInstance } from 'ngx-pagination';
import { SortableColumnModel } from 'src/app/shared/services/TableService/sortable-column.model';
import { TableService } from 'src/app/shared/services/TableService/table.service';
import { SchedH4Service } from './sched-h4.service';


@Component({
  selector: 'app-sched-h4',
  templateUrl: './sched-h4.component.html',
  styleUrls: ['./sched-h4.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe],
  encapsulation: ViewEncapsulation.None,
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate(500, style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate(0, style({ opacity: 0 }))
      ])
    ])
  ]
})
export class SchedH4Component extends AbstractSchedule implements OnInit, OnDestroy, OnChanges {
  @Input() transactionTypeText: string;
  @Input() transactionType: string;
  @Input() scheduleAction: ScheduleActions;
  @Input() scheduleType: string;
  @Output() status: EventEmitter<any>;

  public formType: string;  
  public showPart2: boolean;
  public loaded = false;
  public schedH4: FormGroup;
   
  public h4Subscription: Subscription;
  public h4Sum: any;
  public saveHRes: any;

  public tableConfig: any;
   
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
    private _schedH4Service: SchedH4Service,
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
    _schedH4Service;
  }


  public ngOnInit() {
    
    // temp code - waiting until dynamic forms completes and loads the formGroup
    // before rendering the static fields, otherwise validation error styling
    // is not working (input-error-field class).  If dynamic forms deliver,
    // the static fields, then remove this or set a flag when formGroup is ready
    setTimeout(() => {
      this.loaded = true;
    }, 2000);

    this.formType = this._actRoute.snapshot.paramMap.get('form_id');
    this.getH4Sum(this.getReportId());
    
    //this.setSchedH4();

    this.tableConfig = {
      itemsPerPage: 8,
      currentPage: 1,
      totalItems: 10
    };

    //this.setDefaultValues();

    console.log("this.transactionType: ", this.transactionType);
    if(this.transactionType === 'ALLOC_H4_RATIO') {
      this.transactionType = 'ALLOC_EXP_DEBT'
    }

    this.setSchedH4();

  }

  pageChanged(event){
    this.tableConfig.currentPage = event;
  }

  public ngOnChanges(changes: SimpleChanges) {
    // OnChanges() can be triggered before OnInit().  Ensure formType is set.
    this.formType = '3X';    
  }

  public ngOnDestroy(): void {
    super.ngOnDestroy();
  }

  setDefaultValues() {
    this.schedH4.patchValue({ratio_code:'n'}, { onlySelf: true });
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

  public setSchedH4() {
    this.schedH4 = new FormGroup({     
      type: new FormControl('ALLOC_EXP', Validators.required)      
    });
  }

  public selectTypeChange(e) { 
    const receiptObj: any = {};
    receiptObj['transaction_type_identifier'] = e.currentTarget.value;
    localStorage.setItem(`form_${this.formType}_receipt`, JSON.stringify(receiptObj));   
  }
 
  public getH4Sum(reportId: string) {
    
    this.h4Subscription = this._schedH4Service.getSummary(reportId).subscribe(res =>
      {        
        if(res) {          
          this.h4Sum =  res;         
          this.tableConfig.totalItems = res.length;           
        }
      });        
  }
 
  public returnToSum(): void {
    this.transactionType = 'ALLOC_H4_SUM';
    this.getH4Sum(this.getReportId());
  }

  public returnToAdd(): void {
    this.transactionType = 'ALLOC_EXP_DEBT'; //'ALLOC_H4_RATIO';    
  }
  
}

