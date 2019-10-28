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
import { SchedH2Service } from './sched-h2.service';


@Component({
  selector: 'app-sched-h2',
  templateUrl: './sched-h2.component.html',
  styleUrls: ['./sched-h2.component.scss'],
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
export class SchedH2Component extends AbstractSchedule implements OnInit, OnDestroy, OnChanges {
  @Input() transactionTypeText: string;
  @Input() transactionType: string;
  @Input() scheduleAction: ScheduleActions;
  @Input() scheduleType: string;
  @Output() status: EventEmitter<any>;

  public formType: string;  
  public showPart2: boolean;
  public loaded = false;
  public schedH2: FormGroup;
   
  public h2Subscription: Subscription;
  public h2Sum: any;
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
    private _schedH2Service: SchedH2Service,
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
    _schedH2Service;
  }


  public ngOnInit() {
    
    // temp code - waiting until dynamic forms completes and loads the formGroup
    // before rendering the static fields, otherwise validation error styling
    // is not working (input-error-field class).  If dynamic forms deliver,
    // the static fields, then remove this or set a flag when formGroup is ready
    setTimeout(() => {
      this.loaded = true;
    }, 2000);

    this.getH2Sum(this.getReportId());
    
    this.setSchedH2();

    this.tableConfig = {
      itemsPerPage: 8,
      currentPage: 1,
      totalItems: 10
    };

    this.setDefaultValues();

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
    this.schedH2.patchValue({ratio_code:'n'}, { onlySelf: true });
  }

  public getReportId(): string {

    const reportId = localStorage.getItem('reportId');
    return reportId ? reportId : '0';
  }

  public setSchedH2() {
    this.schedH2 = new FormGroup({      
      activity_event_name: new FormControl('', [Validators.maxLength(40), Validators.required]),
      date: new FormControl(''),
      select_activity_function: new FormControl('', Validators.required),
      fundraising: new FormControl('', Validators.required),
      direct_cand_support: new FormControl('', Validators.required),
      ratio_code: new FormControl('', Validators.required),
      federal_percent: new FormControl('', [Validators.min(0), Validators.max(100), Validators.required]),
      non_federal_percent: new FormControl('', [Validators.min(0), Validators.max(100), Validators.required])
    });
  }
  
  public clearFormValues() {
    this.schedH2.reset();
  }

  public saveAndAddMore(): void {
    this.doValidate();    
  }

  public doValidate() {
    
    this.schedH2.patchValue({ fundraising: this.schedH2.get('select_activity_function').value === 'f' ? true : false }, { onlySelf: true });
    this.schedH2.patchValue({ direct_cand_support: this.schedH2.get('select_activity_function').value === 'd' ? true : false }, { onlySelf: true });

    const formObj = this.schedH2.getRawValue();

    formObj['report_id'] = 0;
    formObj['transaction_type_identifier'] = "ALLOC_H2_RATIO";
    
    formObj['federal_percent'] = ((this.schedH2.get('federal_percent').value) / 100).toFixed(2);
    formObj['non_federal_percent'] = ((this.schedH2.get('non_federal_percent').value) / 100).toFixed(2);
    
    const serializedForm = JSON.stringify(formObj);

    if(this.schedH2.status === 'VALID' && 
        (this.schedH2.get('federal_percent').value + this.schedH2.get('non_federal_percent').value) === 100) {

      this.saveH2Ratio(serializedForm);      
      this.schedH2.reset();
    }
  }

  public getH2Sum(reportId: string) {
    
    this.h2Subscription = this._schedH2Service.getSummary(reportId).subscribe(res =>
      {        
        if(res) {          
          this.h2Sum =  res;         
          this.tableConfig.totalItems = res.length;           
        }
      });        
  }

  public saveH2Ratio(ratio: any) {
    
    this._schedH2Service.saveH2Ratio(ratio).subscribe(res => {
      if (res) {        
        this.saveHRes = res;
      }
    });
  }
 
  public returnToSum(): void {
    this.transactionType = 'ALLOC_H2_SUM';
    this.getH2Sum(this.getReportId());
  }

  public returnToAdd(): void {
    this.transactionType = 'ALLOC_H2_RATIO';    
  }
  
}

