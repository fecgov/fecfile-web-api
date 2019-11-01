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

  public h3Subscription: Subscription;
  public saveHRes: any;

  public h3TableConfig: any;

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
    private _schedH3Service: SchedH3Service
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

    this.setH3Sum();
    this.setH3SumP();

    this.formType = this._actRoute.snapshot.paramMap.get('form_id');
    
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
      date: new FormControl(''),
      total_amount_transferred: new FormControl(''),
      category: new FormControl(''),
      activity_event_name: new FormControl(''),
      transferred_amount: new FormControl(''),
      total_amount: new FormControl('')
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

    this.h3Subscription = 
      this._schedH3Service.getActivityOrEventIdentifiers(category)
      .subscribe(res =>
        {
          if(res) {            
            this.identifiers = res;
          }
        }
      ); 
    /*  
    this.identifiers = [      
      {
        "id":"chicago_mens_rotary",
        "name":"Chicago Men's Rotary"
      },
      {
        "id":"detroid_mens_dinnner_club",
        "name":"Detroid Men's Dinnner Club"
      },
      {
        "id":"chicago_wommens_league",
        "name":"Chicago Women's League"
      },
      {
        "id":"junior_board_shop_of_tallahasse",
        "name":"Junior Board Shop of Tallahasse"
      }
    ]
    */
  }

  public getTotalAmount(activity_event_type: string) {

    this.schedH3.patchValue({total_tmount_of_transfer: 0}, { onlySelf: true });
    this.h3Subscription = 
      this._schedH3Service.getTotalAmount(activity_event_type)
      .subscribe(res =>
        {
          if(res) {            
            this.schedH3.patchValue({total_amount_transferred: res.total_amount_transferred}, { onlySelf: true });
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
      this.getTotalAmount('AD');      
      this.showIdentiferSelect = false
    }else if(this.schedH3.get('category').value === 'GV') {
      this.totalName = 'Generic Voter Drive';
      this.getTotalAmount('GV');
      this.showIdentiferSelect = false
    }else if(this.schedH3.get('category').value === 'EA') {
      this.totalName = 'Exempt Activities';
      this.getTotalAmount('EA');
      this.showIdentiferSelect = false
    }else if(this.schedH3.get('category').value === 'DF') {
      this.totalName = 'Activity or Event Identifier';
      this.setActivityOrEventIdentifier('fundraising');
      this.showIdentiferSelect = true
    }else if(this.schedH3.get('category').value === 'DC') {
      this.totalName = 'Activity or Event Identifier';
      this.setActivityOrEventIdentifier('direct_can_support');
      this.showIdentiferSelect = true;
    }else if(this.schedH3.get('category').value === 'PC') {
      this.totalName = 'Public Communications';
      this.getTotalAmount('PC');
      this.showIdentiferSelect = false
    }
    
  }

  public selectActivityOrEventChange(e) {
    this._schedH3Service.getTotalAmount(this.schedH3.get('category').value);
  }

  public setH3Sum() {
    
    this.h3Subscription = this._schedH3Service.getSummary(this.getReportId()).subscribe(res =>
      {        
        if(res) {          
          this.h3Sum =  res;         
          this.h3TableConfig.totalItems = res.length;
        }
      });
     
    /*  
    this.h3Sum = [
      {
        "transfer_type": "DF",
        "activity_event_name" : "Farmington Country Club Gala",
        "date": "04/21/2016",
        "amount": "21309.42",
        "aggregateAmount": "4509.21"
    },
    {
        "transfer_type": "DC",
        "activity_event_name" : "Chicago's Men's Rotary Club",
        "date": "04/21/2016",
        "amount": "21309.42",
        "aggregateAmount": "4509.21"
    },
    {
        "transfer_type": "AD",
        "activity_event_name" : "Chicago's Men's Rotary Club",
        "date": "03/20/2016",
        "amount": "3394.99",
        "aggregateAmount": "2340.92"
    },
    {
        "transfer_type": "GV",
        "activity_event_name" : "Trenton Rally",
        "date": "03/14/2016",
        "amount": "5209.44",
        "aggregateAmount": "2491.00"
    }
    
    ]
    */
   /*
   this.h3Sum = [
    {
        "cmte_id": "C00029447",
        "report_id": 1324002,
        "transaction_type_identifier": "TRAN_FROM_NON_FED_ACC",
        "transaction_id": "SH20191001000000559",
        "back_ref_transaction_id": "",
        "back_ref_sched_name": "",
        "account_name": "",
        "activity_event_type": "DF",
        "activity_event_name": "fund raising 20190919",
        "receipt_date": "2019-10-30",
        "total_amount_transferred": 60.0,
        "transferred_amount": 40.0,
        "memo_code": "",
        "memo_text": "",
        "delete_ind": null,
        "create_date": "2019-10-01T15:25:36.109899",
        "last_update_date": "2019-10-01T15:25:36.10991"
    },
    {
        "cmte_id": "C00029447",
        "report_id": 1324002,
        "transaction_type_identifier": "TRAN_FROM_NON_FED_ACC",
        "transaction_id": "SH20191001000000560",
        "back_ref_transaction_id": "",
        "back_ref_sched_name": "",
        "account_name": "",
        "activity_event_type": "DF",
        "activity_event_name": "fund raising 20190919",
        "receipt_date": "2019-10-30",
        "total_amount_transferred": 50.0,
        "transferred_amount": 10.0,
        "memo_code": "",
        "memo_text": "",
        "delete_ind": null,
        "create_date": "2019-10-01T15:25:56.800353",
        "last_update_date": "2019-10-01T15:25:56.800358"
    },
    {
        "cmte_id": "C00029447",
        "report_id": 1324002,
        "transaction_type_identifier": "TRAN_FROM_NON_FED_ACC",
        "transaction_id": "SH20191028000000635",
        "back_ref_transaction_id": "",
        "back_ref_sched_name": "",
        "account_name": "test111",
        "activity_event_type": "DC",
        "activity_event_name": "event1",
        "receipt_date": null,
        "total_amount_transferred": 200.0,
        "transferred_amount": 100.0,
        "memo_code": "",
        "memo_text": "",
        "delete_ind": null,
        "create_date": "2019-10-28T09:25:39.298349",
        "last_update_date": "2019-10-28T09:25:39.298555"
    },
    {
        "cmte_id": "C00029447",
        "report_id": 1324002,
        "transaction_type_identifier": "TRAN_FROM_NON_FED_ACC",
        "transaction_id": "SH20191029000000642",
        "back_ref_transaction_id": "",
        "back_ref_sched_name": "",
        "account_name": "test111",
        "activity_event_type": "DC",
        "activity_event_name": "event1",
        "receipt_date": null,
        "total_amount_transferred": 200.0,
        "transferred_amount": 100.0,
        "memo_code": "",
        "memo_text": "",
        "delete_ind": null,
        "create_date": "2019-10-28T21:30:19.447973",
        "last_update_date": "2019-10-28T21:30:19.448119"
    },
    {
      "cmte_id": "C00029447",
      "report_id": 1324002,
      "transaction_type_identifier": "TRAN_FROM_NON_FED_ACC",
      "transaction_id": "SH20191001000000559",
      "back_ref_transaction_id": "",
      "back_ref_sched_name": "",
      "account_name": "",
      "activity_event_type": "DF",
      "activity_event_name": "fund raising 20190919",
      "receipt_date": "2019-10-30",
      "total_amount_transferred": 60.0,
      "transferred_amount": 40.0,
      "memo_code": "",
      "memo_text": "",
      "delete_ind": null,
      "create_date": "2019-10-01T15:25:36.109899",
      "last_update_date": "2019-10-01T15:25:36.10991"
    },
    {
        "cmte_id": "C00029447",
        "report_id": 1324002,
        "transaction_type_identifier": "TRAN_FROM_NON_FED_ACC",
        "transaction_id": "SH20191001000000560",
        "back_ref_transaction_id": "",
        "back_ref_sched_name": "",
        "account_name": "",
        "activity_event_type": "DF",
        "activity_event_name": "fund raising 20190919",
        "receipt_date": "2019-10-30",
        "total_amount_transferred": 50.0,
        "transferred_amount": 10.0,
        "memo_code": "",
        "memo_text": "",
        "delete_ind": null,
        "create_date": "2019-10-01T15:25:56.800353",
        "last_update_date": "2019-10-01T15:25:56.800358"
    },
    {
        "cmte_id": "C00029447",
        "report_id": 1324002,
        "transaction_type_identifier": "TRAN_FROM_NON_FED_ACC",
        "transaction_id": "SH20191028000000635",
        "back_ref_transaction_id": "",
        "back_ref_sched_name": "",
        "account_name": "test111",
        "activity_event_type": "DC",
        "activity_event_name": "event1",
        "receipt_date": null,
        "total_amount_transferred": 200.0,
        "transferred_amount": 100.0,
        "memo_code": "",
        "memo_text": "",
        "delete_ind": null,
        "create_date": "2019-10-28T09:25:39.298349",
        "last_update_date": "2019-10-28T09:25:39.298555"
    },
    {
        "cmte_id": "C00029447",
        "report_id": 1324002,
        "transaction_type_identifier": "TRAN_FROM_NON_FED_ACC",
        "transaction_id": "SH20191029000000642",
        "back_ref_transaction_id": "",
        "back_ref_sched_name": "",
        "account_name": "test111",
        "activity_event_type": "DC",
        "activity_event_name": "event1",
        "receipt_date": null,
        "total_amount_transferred": 200.0,
        "transferred_amount": 100.0,
        "memo_code": "",
        "memo_text": "",
        "delete_ind": null,
        "create_date": "2019-10-28T21:30:19.447973",
        "last_update_date": "2019-10-28T21:30:19.448119"
    }
    ]
    */
  }

  public setH3SumP() {

    this.h3Subscription = this._schedH3Service.getBreakDown(this.getReportId()).subscribe(res =>
      {        
        if(res) {          
          this.h3SumP =  res;          
        }
      });
     
    /*  
    this.h3SumP = [
      {
        "activity_event_type": "AD",
        "sum": 8093320.00
      },
      {        
        "activity_event_type": "GV",
        "sum": 2037000.00
      },
      {        
        "activity_event_type": "EA",
        "sum":  502300.00
      },
      {        
        "activity_event_type": "DF",
        "sum":  43320301.00
      },
      {        
        "activity_event_type": "DC",
        "sum":  34507.78
      },
      {        
        "activity_event_type": "PC",
        "sum":  4200.00
      },
      {        
        "activity_event_type": "total",
        "sum":  52304200.00
      }
    ]
    */
  }

  public saveAndAddMore(): void {
    this.doValidate();    
  }

  public doValidate() {

    const formObj = this.schedH3.getRawValue();

    formObj['report_id'] = this.getReportId();
    formObj['transaction_type_identifier'] = 'TRAN_FROM_NON_FED_ACC';
    formObj['activity_event_type'] = this.schedH3.get('category').value;
    
    const serializedForm = JSON.stringify(formObj);

    
    if(this.schedH3.status === 'VALID') {
      this.saveH3Ratio(serializedForm);      
      this.schedH3.reset();
    }
  }

  public saveH3Ratio(ratio: any) {
    
    this._schedH3Service.saveH3Ratio(ratio).subscribe(res => {
      if (res) {        
        this.saveHRes = res;
      }
    });
  }

}
