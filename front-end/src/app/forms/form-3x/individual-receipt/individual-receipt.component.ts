import {
  Component,
  EventEmitter,
  ElementRef,
  Input,
  OnInit,
  Output,
  ViewEncapsulation,
  ViewChild,
  OnDestroy,
  HostListener,
  OnChanges,
  SimpleChanges
} from '@angular/core';
import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { FormBuilder, FormGroup, FormControl, NgForm, Validators, AbstractControl, ValidatorFn } from '@angular/forms';
import { NgbTooltipConfig, NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../../environments/environment';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { UtilService } from '../../../shared/utils/util.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { IndividualReceiptService } from './individual-receipt.service';
import { f3xTransactionTypes } from '../../../shared/interfaces/FormsService/FormsService';
import { alphaNumeric } from '../../../shared/utils/forms/validation/alpha-numeric.validator';
import { floatingPoint } from '../../../shared/utils/forms/validation/floating-point.validator';
import { validatePurposeInKindRequired, IN_KIND } from '../../../shared/utils/forms/validation/purpose.validator';
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';
import { Observable, Subscription, interval, timer } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, delay, pairwise } from 'rxjs/operators';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { TransactionModel } from '../../transactions/model/transaction.model';
import { F3xMessageService } from '../service/f3x-message.service';
import { ScheduleActions } from './schedule-actions.enum';
import { hasOwnProp } from 'ngx-bootstrap/chronos/utils/type-checks';
import { TransactionsMessageService } from '../../transactions/service/transactions-message.service';
import { ActiveView } from '../../transactions/transactions.component';
import { validateAggregate } from 'src/app/shared/utils/forms/validation/aggregate.validator';
import { validateAmount } from 'src/app/shared/utils/forms/validation/amount.validator';
import { ContributionDateValidator } from 'src/app/shared/utils/forms/validation/contribution-date.validator';
import { ContactsService } from 'src/app/contacts/service/contacts.service';
import { trigger, transition, style, animate, state } from '@angular/animations';
import { heLocale } from 'ngx-bootstrap';
import { TransactionsService } from '../../transactions/service/transactions.service';
import { AbstractSchedule } from './abstract-schedule';
import { ReportsService } from 'src/app/reports/service/report.service';
import { AbstractScheduleParentEnum } from './abstract-schedule-parent.enum';

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
  @Input() transactionTypeText: string;
  @Input() transactionType: string;
  @Input() scheduleAction: ScheduleActions;
  @Output() status: EventEmitter<any>;

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
    _activatedRoute.queryParams.subscribe(p => {
      this.cloned = p.cloned ? true : false;
    });
  }

  public ngOnInit() {
    this.formType = '3X';
    this.abstractScheduleComponent = AbstractScheduleParentEnum.schedMainComponent;
    localStorage.removeItem(`form_${this.formType}_saved`);
  }

  // tslint:disable-next-line:use-life-cycle-interface
  public ngDoCheck() {
    if (this.frmIndividualReceipt != null) {
      console.log(this.frmIndividualReceipt.dirty);
      if ( this.frmIndividualReceipt.dirty ) {
        localStorage.setItem(`form_${this.formType}_saved`, JSON.stringify({ saved: false }));
      }
    }

  }
  public ngOnChanges(changes: SimpleChanges) {
    // OnChanges() can be triggered before OnInit().  Ensure formType is set.
    this.formType = '3X';

    super.ngOnChanges(changes);
  }

  public ngOnDestroy(): void {
    localStorage.removeItem(`form_${this.formType}_saved`);
    super.ngOnDestroy();
  }
}
