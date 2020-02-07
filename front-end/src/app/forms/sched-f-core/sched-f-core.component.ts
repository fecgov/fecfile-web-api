import { Component, OnInit, Output, EventEmitter, Input, SimpleChanges, OnDestroy, OnChanges } from '@angular/core';
import {FormBuilder, Validators} from '@angular/forms';
import { FormsService } from 'src/app/shared/services/FormsService/forms.service';
import { IndividualReceiptService } from '../form-3x/individual-receipt/individual-receipt.service';
import { ContactsService } from 'src/app/contacts/service/contacts.service';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbTooltipConfig, NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
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
import { AbstractScheduleParentEnum } from '../form-3x/individual-receipt/abstract-schedule-parent.enum';
import { schedFstaticFormFields } from '../sched-f/static-form-fields.json';
import {Observable, Subscription} from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-sched-f-core',
  templateUrl: './sched-f-core.component.html',
  styleUrls: ['./sched-f-core.component.scss'],
  providers: [NgbTooltipConfig, CurrencyPipe, DecimalPipe]
})
export class SchedFCoreComponent extends AbstractSchedule implements OnInit, OnDestroy, OnChanges {
  // export class SchedFCoreComponent implements OnInit, OnDestroy, OnChanges {
  @Input() formType: string;
  @Input() transactionTypeText: string;
  @Input() transactionType: string;
  @Input() scheduleAction: ScheduleActions;
  @Output() status: EventEmitter<any>;

  public cloned: boolean;
  protected staticFormFields = schedFstaticFormFields;

  private isDesignatedFiler: boolean;
  private noValidationRequired = [];
  private validateDesignatedFiler = [];
  readonly optional  = '(Optional)'

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
      this.showPart2 = false;
    });
     _messageService.getMessage().subscribe(message => {
      if (message && message.parentFormPopulated) {
        console.log('Message from sub' + message);
      }
    });

  }

  public ngOnInit() {
    this.loaded = false;
    this.formFieldsPrePopulated = true;
    this.formType = '3X';
    this.abstractScheduleComponent = AbstractScheduleParentEnum.schedFCoreComponent;
    // set remove validators
    this.noValidationRequired.push('subordinate_cmte_id');
    this.noValidationRequired.push('subordinate_cmte_name');
    this.noValidationRequired.push('subordinate_cmte_street_2');
    this.noValidationRequired.push('subordinate_cmte_city');
    this.noValidationRequired.push('subordinate_cmte_state');
    this.noValidationRequired.push('subordinate_cmte_zip');
    this.noValidationRequired.push('subordinate_cmte_street_1');
    this.validateDesignatedFiler.push('designating_cmte_id');
    this.validateDesignatedFiler.push('designating_cmte_name');
    super.ngOnInit();
  }

  public ngOnChanges(changes: SimpleChanges) {
    // OnChanges() can be triggered before OnInit().  Ensure formType is set.
    this.formType = '3X';

    super.ngOnChanges(changes);
  }

  public ngOnDestroy(): void {
    this.noValidationRequired = [];
    this.validateDesignatedFiler = [];
    super.ngOnDestroy();
  }

  public saveAndReturnToParentDebt() {
    if (!this.frmIndividualReceipt.dirty) {
      this._setTransactionDetail();
    }
    this.saveAndReturnToParent();
  }

  /**
   * Proceed to 2nd part of the payment.
   */
  public next() {
    this.frmIndividualReceipt.markAsTouched();
    if (!this._checkFormFieldIsValid('designating_cmte_id') && this.isDesignatedFiler) {
      return;
    }
    if (!this._checkFormFieldIsValid('designating_cmte_name') && this.isDesignatedFiler) {
      return;
    }
    if (!this._checkFormFieldIsValid('coordinated_exp_ind')) {
      return;
    }
    this._setDesignatedValidators();
    this.showPart2 = true;
  }

  /**
   * Return to the first part of the payment.
   */
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
    // return true;
  }

  private _setDesignatedValidators() {
     if ( this.frmIndividualReceipt.contains('coordinated_exp_ind') &&
         this.frmIndividualReceipt.get('coordinated_exp_ind').value === 'Y' ) {
       this.onFilerChange('Y');
     } else {
       this.onFilerChange('N');
     }
  }
  private _setTransactionDetail() {

    if (this.scheduleAction === ScheduleActions.addSubTransaction) {
      this.clearFormValues();
    } else if (this.scheduleAction === ScheduleActions.edit) {
    }
  }

  /**
   * @override the Base class method.
   *
   * Determine if the field should be shown.
   * Don't show fields from the first screen by checking
   * the showPart2 for true.  If showPart2, determine which fields
   * to be shown based on the entity type selected.
   */
  public isToggleShow(col: any) {
    if (col.staticField) {
      return false;
    } else {
      if (!this.selectedEntityType) {
        return true;
      }
      if (!col.toggle) {
        return true;
      }
      if (this.selectedEntityType.group === col.entityGroup || !col.entityGroup) {
        return true;
      } else {
        return false;
      }
    }
  }

  private _patchSubordinateFormFields(fieldNames: any[], entity: any) {
    if (fieldNames) {
      for (const field of fieldNames) {
        const patch = {};
        patch[field.formName] = entity[field.entityFieldName];
        this.frmIndividualReceipt.patchValue(patch, { onlySelf: true });
      }
    }
  }

  /**
   * Handle user selection of Schedule F Designating or Subordinate Committee.
   * @param $event
   * @param name
   */
  public handleSelectedSFCommittee($event: NgbTypeaheadSelectItemEvent, name: string) {
    const entity = $event.item;

    const fieldNames = [];
    if (name === 'designating_cmte_id' || name === 'designating_cmte_name') {
      if (name === 'designating_cmte_id') {
        fieldNames.push({ formName: 'designating_cmte_name', entityFieldName: 'cmte_name' });
      } else {
        fieldNames.push({ formName: 'designating_cmte_id', entityFieldName: 'cmte_id' });
      }
    } else if (name === 'subordinate_cmte_id' || name === 'subordinate_cmte_name') {
      fieldNames.push({ formName: 'subordinate_cmte_id', entityFieldName: 'cmte_id' });
      fieldNames.push({ formName: 'subordinate_cmte_name', entityFieldName: 'cmte_name' });
      fieldNames.push({ formName: 'subordinate_cmte_street_1', entityFieldName: 'street_1' });
      fieldNames.push({ formName: 'subordinate_cmte_street_2', entityFieldName: 'street_2' });
      fieldNames.push({ formName: 'subordinate_cmte_state', entityFieldName: 'state' });
      fieldNames.push({ formName: 'subordinate_cmte_city', entityFieldName: 'city' });
      fieldNames.push({ formName: 'subordinate_cmte_zip', entityFieldName: 'zip_code' });
    }
    this._patchSubordinateFormFields(fieldNames, entity);
  }

  /**
   * Cancel the payment and return to the start or first part.
   */
  public cancelSFPayment() {
    this.showPart2 = false;
    this.clearFormValues();
    this.returnToParent(this.editScheduleAction);
  }

  /**
   * Search for Committee Payees when Committee ID input value changes.
   */
  searchPayeeCommitteeId = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        const searchTextUpper = searchText.toUpperCase();

        if (
          searchTextUpper === 'C' ||
          searchTextUpper === 'C0' ||
          searchTextUpper === 'C00' ||
          searchTextUpper === 'C000'
        ) {
          return Observable.of([]);
        }

        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'payee_cmte_id');
        } else {
          return Observable.of([]);
        }
      })
    );

  formatterPayeeCommitteeId = (x: { payee_cmte_id: string }) => {
    if (typeof x !== 'string') {
      return x.payee_cmte_id;
    } else {
      return x;
    }
  };

  /**
   * Format a Candidate Entity to display in the Payee Committee ID type ahead.
   *
   * @param result formatted item in the typeahead list
   */
  public formatTypeaheadPayeeCommitteeId(result: any) {
    const payeeCmteID = result.payee_cmte_id ? result.payee_cmte_id.trim() : '';
    const candidateId = result.beneficiary_cand_id ? result.beneficiary_cand_id.trim() : '';
    const lastName = result.cand_last_name ? result.cand_last_name.trim() : '';
    const firstName = result.cand_first_name ? result.cand_first_name.trim() : '';
    let office = result.cand_office ? result.cand_office.toUpperCase().trim() : '';
    if (office) {
      if (office === 'P') {
        office = 'Presidential';
      } else if (office === 'S') {
        office = 'Senate';
      } else if (office === 'H') {
        office = 'House';
      }
    }
    const officeState = result.cand_office_state ? result.cand_office_state.trim() : '';
    const officeDistrict = result.cand_office_district ? result.cand_office_district.trim() : '';

    return `${payeeCmteID}, ${candidateId}, ${lastName}, ${firstName}, ${office},
      ${officeState}, ${officeDistrict}`;
  }

  public saveForAddSubTempSchedF() {}
  public handleOnBlurEvent($event: any, col: any) {
    console.log('col %s %s', col,  this.frmIndividualReceipt.controls['expenditure_amount'].value);
    const expenditureAmount = this.convertAmountToNumber(this.frmIndividualReceipt.controls['expenditure_amount'].value);
    const contributionAggregateValue: string = this._decimalPipe.transform(
        expenditureAmount,
        '.2-2'
    );
    this.frmIndividualReceipt.patchValue(
        { aggregate_general_elec_exp: contributionAggregateValue}, { onlySelf: true });
    super.handleOnBlurEvent($event, col);
  }

  public updateOnly() {
    this.back();
    super.updateOnly();
  }
  public saveOnly(): void {
    this.back();
    super.saveOnly();
  }
  public onFilerChange(change): void {

    console.log('change %s', change);
    if (change === 'Y') {
      this.isDesignatedFiler = true;
      this.addValidator(this.validateDesignatedFiler,  this.isDesignatedFiler);
    } else {
      this.isDesignatedFiler = false;
      this.addValidator(this.validateDesignatedFiler,  this.isDesignatedFiler);
    }
    this.addValidator(this.noValidationRequired, false);
}
public addValidator( validators: Array<any>, set: boolean): void {
    if ( set ) {
      for (const filedName of validators) {
        this.frmIndividualReceipt.controls[filedName].setValidators([Validators.required]);
        this.frmIndividualReceipt.controls[filedName].updateValueAndValidity();
      }
    } else {
      for (const filedName of validators) {
        this.frmIndividualReceipt.controls[filedName].setValidators([]);
        this.frmIndividualReceipt.controls[filedName].updateValueAndValidity();
      }
    }
}
}
