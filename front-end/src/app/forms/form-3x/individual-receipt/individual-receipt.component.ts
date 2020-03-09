import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, EventEmitter, Input, OnChanges, OnDestroy, OnInit, Output, SimpleChanges } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { Subject } from 'rxjs';
import 'rxjs/add/operator/takeUntil';
import { ContactsService } from 'src/app/contacts/service/contacts.service';
import { ReportsService } from 'src/app/reports/service/report.service';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { ContributionDateValidator } from 'src/app/shared/utils/forms/validation/contribution-date.validator';
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { UtilService } from '../../../shared/utils/util.service';
import { TransactionsMessageService } from '../../transactions/service/transactions-message.service';
import { TransactionsService } from '../../transactions/service/transactions.service';
import { F3xMessageService } from '../service/f3x-message.service';
import { AbstractSchedule } from './abstract-schedule';
import { AbstractScheduleParentEnum } from './abstract-schedule-parent.enum';
import { IndividualReceiptService } from './individual-receipt.service';
import { ScheduleActions } from './schedule-actions.enum';

export enum SaveActions {
  saveOnly = 'saveOnly',
  saveForReturnToParent = 'saveForReturnToParent',
  saveForReturnToNewParent = 'saveForReturnToNewParent',
  saveForAddSub = 'saveForAddSub',
  saveForEditSub = 'saveForEditSub',
  updateOnly = 'updateOnly'
}

@Component({
  selector: 'f3x-individual-receipt',
  templateUrl: './individual-receipt.component.html',
  styleUrls: ['./individual-receipt.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe]
  // encapsulation: ViewEncapsulation.None
})
export class IndividualReceiptComponent extends AbstractSchedule implements OnInit, OnDestroy, OnChanges {
  @Input() mainTransactionTypeText: string;
  @Input() transactionTypeText: string;
  @Input() transactionType: string;
  @Input() scheduleAction: ScheduleActions;
  @Output() status: EventEmitter<any>;

  private _onDestroy$ = new Subject();

  public formType: string;
  public cloned: boolean;
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

    _activatedRoute.queryParams.takeUntil(this._onDestroy$).subscribe(p => {
      this.cloned = p.cloned ? true : false;
    });
  }

  public ngOnInit() {
    this.formType = '3X';
    this.abstractScheduleComponent = AbstractScheduleParentEnum.schedMainComponent;
    localStorage.removeItem(`form_${this.formType}_saved`);
    super.ngOnInit();
  }

  public ngOnChanges(changes: SimpleChanges) {
    // OnChanges() can be triggered before OnInit().  Ensure formType is set.
    this.formType = '3X';
    if (this.mainTransactionTypeText === 'Loans and Debts') {
      this.mainTransactionTypeText = 'Debts';
    }

    super.ngOnChanges(changes);
  }

  public ngOnDestroy(): void {
    localStorage.removeItem(`form_${this.formType}_saved`);
    this._onDestroy$.next(true);
    super.ngOnDestroy();
  }
}