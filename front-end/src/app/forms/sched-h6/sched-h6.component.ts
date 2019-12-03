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
import { SchedH6Service } from './sched-h6.service';
import { SchedH6Model } from './sched-h6.model';
import { AbstractScheduleParentEnum } from '../form-3x/individual-receipt/abstract-schedule-parent.enum';


@Component({
  selector: 'app-sched-h6',
  templateUrl: './sched-h6.component.html',
  styleUrls: ['./sched-h6.component.scss'],
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
export class SchedH6Component extends AbstractSchedule implements OnInit, OnDestroy, OnChanges {
  @Input() transactionTypeText: string;
  @Input() transactionType: string;
  @Input() scheduleAction: ScheduleActions;
  @Input() scheduleType: string;
  @Output() status: EventEmitter<any>;

  public formType: string;  
  public showPart2: boolean;
  public loaded = false;
  public schedH6: FormGroup;
   
  public h6Subscription: Subscription;
  public h6Sum: any;
  public saveHRes: any;

  public tableConfig: any;

  public showSelectType = true;

  public schedH6sModel: Array<SchedH6Model>;
  public schedH6sModelL: Array<SchedH6Model>;
   
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
    private _schedH6Service: SchedH6Service,
    private _individualReceiptService: IndividualReceiptService,
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
    _schedH6Service;
    _individualReceiptService;
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

    this.tableConfig = {
      itemsPerPage: 8,
      currentPage: 1,
      totalItems: 10
    };
 
    this.setSchedH6();

  }

  pageChanged(event){
    this.tableConfig.currentPage = event;
  }

  public ngOnChanges(changes: SimpleChanges) {
    // OnChanges() can be triggered before OnInit().  Ensure formType is set.
    this.formType = '3X';

    if(this.transactionType === 'ALLOC_H6_SUM') {
      this.getH6Sum(this._individualReceiptService.getReportIdFromStorage(this.formType));
    }
  }

  ngDoCheck() {
    this.status.emit({
      otherSchedHTransactionType: this.transactionType
    });
  }

  public ngOnDestroy(): void {
    super.ngOnDestroy();
  }

  setDefaultValues() {
    this.schedH6.patchValue({ratio_code:'n'}, { onlySelf: true });
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

  public setSchedH6() {
    this.schedH6 = new FormGroup({     
      type: new FormControl('', Validators.required)      
    });
  }

  public selectTypeChange(e) {    
    this.transactionType = e.currentTarget.value;
    console.log('99: ', this.transactionType);
  }
 
  public getH6Sum(reportId: string) {
    this.schedH6sModel = [];
    
    this.h6Subscription = this._schedH6Service.getSummary(reportId).subscribe(res =>
      {        
        if(res) {          
          //this.h6Sum =  res;
          this.schedH6sModelL = this.mapFromServerFields(res);
          this.schedH6sModel = this.mapFromServerFields(res);
          this.setArrow(this.schedH6sModel);

          this.schedH6sModel = this.schedH6sModel .filter(obj => obj.memo_code !== 'X');
          this.tableConfig.totalItems = this.schedH6sModel.length;
        }
      });        
  }
 
  public returnToSum(): void {
    this.transactionType = 'ALLOC_H6_SUM';
    this.getH6Sum(this._individualReceiptService.getReportIdFromStorage(this.formType));
  }

  public returnToAdd(): void {
    this.showSelectType = true;
    this.transactionType = "ALLOC_H6_TYPES"
    //this.transactionType = 'ALLOC_EXP_DEBT'; //'ALLOC_H6_RATIO';
  }

  public previousStep(): void {
    
    this.schedH6.reset();

    this.status.emit({
      form: {},
      direction: 'previous',
      step: 'step_2'
    });
  }

  public clickArrow(item: SchedH6Model) {
    if(item.arrow_dir === 'down') {
      let indexRep = this.schedH6sModel.indexOf(item);
      if (indexRep > -1) {
        const tmp: SchedH6Model = this.schedH6sModelL.find(function(obj) { return obj.back_ref_transaction_id === item.transaction_id});
        this.schedH6sModel.splice(indexRep + 1, 0, tmp);
        this.tableConfig.totalItems = this.schedH6sModel.length;
      }

      this.schedH6sModel.find(function(obj) { return obj.transaction_id === item.transaction_id}).arrow_dir = 'up';
      this.schedH6sModel.find(function(obj) { return obj.back_ref_transaction_id === item.transaction_id}).arrow_dir = 'show';
      
    }else if(item.arrow_dir === 'up') {
      //this.schedH6sModel = this.schedH6sModel.filter(obj => obj.memo_code !== 'X');
      this.schedH6sModel = this.schedH6sModel.filter(obj => obj.back_ref_transaction_id !== item.transaction_id);
      this.tableConfig.totalItems = this.schedH6sModel.length;

      this.schedH6sModel.find(function(obj) { return obj.transaction_id === item.transaction_id}).arrow_dir = 'down';
    }
   
  }

  public setArrow(items: SchedH6Model[]) {
    if(items) {
      for(const item of items) {        
        if(item.memo_code !== 'X' && this.schedH6sModel.find(function(obj) { return obj.back_ref_transaction_id === item.transaction_id})) {
            item.arrow_dir = 'down';           
        }        
      }
    }
    console.log('9: ', items);
  }

  public mapFromServerFields(serverData: any) {
    if (!serverData || !Array.isArray(serverData)) {
      return;
    }

    const modelArray: any = [];

    for (const row of serverData) {
      const model = new SchedH6Model({});      

      model.cmte_id = row.cmte_id;
      model.report_id = row.report_id;     
      model.transaction_type_identifier = row.transaction_type_identifier;
      model.transaction_id = row.transaction_id;
      model.back_ref_transaction_id = row.back_ref_transaction_id;
      model.activity_event_identifier = row.activity_event_identifier;
      model.activity_event_type = row.activity_event_type;
      model.expenditure_date = row.expenditure_date;
      model.fed_share_amount = row.fed_share_amount;
      model.non_fed_share_amount = row.non_fed_share_amount;
      model.levin_share = row.levin_share;
      model.memo_code = row.memo_code;
      model.first_name = row.first_name;
      model.last_name = row.last_name;
      model.entity_name = row.entity_name;
      model.entity_type = row.entity_type;

      modelArray.push(model);
    
    }

    console.log('91: ', modelArray);

    return modelArray;
  }
  
}

