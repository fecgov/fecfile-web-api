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
import { SchedH2Service } from '../sched-h2/sched-h2.service';

@Component({
  selector: 'app-sched-h5',
  templateUrl: './sched-h5.component.html',
  styleUrls: ['./sched-h5.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe]
})
export class SchedH5Component extends AbstractSchedule implements OnInit, OnDestroy, OnChanges {
  @Input() transactionTypeText: string;
  @Input() transactionType: string;
  @Input() scheduleAction: ScheduleActions;
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

  protected staticFormFields = [
    {
      childForm: false,
      childFormTitle: null,
      colClassName: 'col col-md-4',
      seperator: false,
      cols: [
        {
          name: 'coord_expenditure_yn',
          value: null,
          validation: {
            required: true
          }
        },
        {
          preText: null,
          setEntityIdTo: 'entity_id',
          isReadonly: false,
          entityGroup: 'org-group',
          toggle: true,
          inputGroup: false,
          inputIcon: '',
          text: 'Organization Name',
          infoIcon: false,
          infoText: 'Request language from RAD',
          name: 'designated_com_id',
          type: 'text',
          value: null,
          scroll: false,
          height: '30px',
          width: '200px',
          validation: {
            required: true,
            max: 9,
            alphaNumeric: true
          }
        },
        {
          preText: null,
          setEntityIdTo: 'entity_id',
          isReadonly: false,
          entityGroup: 'org-group',
          toggle: true,
          inputGroup: false,
          inputIcon: '',
          text: 'Organization Name',
          infoIcon: false,
          infoText: 'Request language from RAD',
          name: 'designated_com_name',
          type: 'text',
          value: null,
          scroll: false,
          height: '30px',
          width: '200px',
          validation: {
            required: true,
            max: 200,
            alphaNumeric: true
          }
        },
        {
          name: 'subordinate_com_id',
          value: null,
          validation: {
            required: true,
            max: 9,
            alphaNumeric: true
          }
        },
        {
          name: 'subordinate_com_name',
          value: null,
          validation: {
            required: true,
            max: 200,
            alphaNumeric: true
          }
        },
        {
          name: 'street_1_co_exp',
          value: null,
          validation: {
            required: true,
            max: 34,
            alphaNumeric: true
          }
        },
        {
          name: 'street_2_co_exp',
          value: null,
          validation: {
            required: false,
            max: 34,
            alphaNumeric: true
          }
        },
        {
          name: 'city_co_exp',
          value: null,
          validation: {
            required: true,
            max: 30,
            alphaNumeric: true
          }
        },
        {
          name: 'state_co_exp',
          value: null,
          validation: {
            required: true,
            max: 2,
            alphaNumeric: true
          }
        },
        {
          name: 'zip_co_exp',
          value: null,
          validation: {
            required: true,
            max: 10,
            alphaNumeric: true
          }
        }
      ]
    }
  ];

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
    _reportsService: ReportsService
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
    this._setTransactionDetail();
    console.log();

    // temp code - waiting until dynamic forms completes and loads the formGroup
    // before rendering the static fields, otherwise validation error styling
    // is not working (input-error-field class).  If dynamic forms deliver,
    // the static fields, then remove this or set a flag when formGroup is ready
    setTimeout(() => {
      this.loaded = true;
    }, 2000);

    //this._getFormFields();

    this.setH5();
    this.setCategory();
    this.setActivityOrEventIdentifier();

    this.setH5Sum();
    this.setH5SumP();
  }

  public ngOnChanges(changes: SimpleChanges) {
    // OnChanges() can be triggered before OnInit().  Ensure formType is set.
    this.formType = '3X';
    this.showPart2 = false;
    this._setTransactionDetail();
  }

  public ngOnDestroy(): void {
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

  public setH5() {

    this.schedH5 = new FormGroup({
      account_name: new FormControl('', [Validators.maxLength(40), Validators.required]),
      date: new FormControl(''),
      total_tmount_of_transfer: new FormControl(''),
      category: new FormControl('')
      // activity_event_name: new FormControl(''),
      // amount: new FormControl(''),
      // total_amount: new FormControl('')
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
    this.transactionType = 'ALLOC_H5_SUM';
  }

  public returnToAdd(): void {
    this.transactionType = 'ALLOC_H5_RATIO';
  }

  //to test for privous
  public resetTransactionType() {
    this.transactionType = '';
  }

  public selectCategoryChange(e) {

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
  }

  public setH5Sum() {
    this.h5Sum = [
      {
        "transfer_type": "GOTV",
        "account_name": "Farmington Country Club Gala",
        "date": "04/21/2016",
        "transfer_amount": "21309.42"
      },
      {
        "transfer_type": "voter_ID",
        "account_name": "Chicago's Men's Rotary Club",
        "date": "04/21/2016",
        "transfer_amount": "21309.42"
      },
      {
        "transfer_type": "voter_registration",
        "account_name": "Chicago's Men's Rotary Club",
        "date": "03/20/2016",
        "transfer_amount": "3394.99"

      },
      {
        "transfer_type": "voter_ID",
        "account_name": "Trenton Rally",
        "date": "03/14/2016",
        "transfer_amount": "5209.44"
      }

    ]
  }

  public setH5SumP() {
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
  }

}
