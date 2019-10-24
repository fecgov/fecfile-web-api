import { Component, OnInit, OnDestroy, OnChanges, Output, EventEmitter, Input, SimpleChanges } from '@angular/core';
import { IndividualReceiptComponent } from '../form-3x/individual-receipt/individual-receipt.component';
import { FormBuilder } from '@angular/forms';
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

@Component({
  selector: 'app-sched-f',
  templateUrl: './sched-f.component.html',
  styleUrls: ['./sched-f.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe]
})
export class SchedFComponent extends AbstractSchedule implements OnInit, OnDestroy, OnChanges {
  @Input() transactionTypeText: string;
  @Input() transactionType: string;
  @Input() scheduleAction: ScheduleActions;
  @Output() status: EventEmitter<any>;

  public formType: string;
  public showPart2: boolean;
  public loaded = false;

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
    this.transactionType = 'OPEXP'; // 'INDV_REC';
    // this.transactionTypeText = 'Coordinated Party Expenditure Debt to Vendor';
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
  }

  public ngOnChanges(changes: SimpleChanges) {
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
}
