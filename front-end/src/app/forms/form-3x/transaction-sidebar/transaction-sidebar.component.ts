import { Subscription } from 'rxjs/Subscription';
import { HttpClient } from '@angular/common/http';
import { Component, EventEmitter, Input, OnInit, Output, ViewChild, ViewEncapsulation , ChangeDetectionStrategy } from '@angular/core';
import { FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbTooltipConfig, NgbTypeahead } from '@ng-bootstrap/ng-bootstrap';
import { Observable, Subject } from 'rxjs';
import 'rxjs/add/operator/takeUntil';
import { debounceTime, distinctUntilChanged, filter, map, merge } from 'rxjs/operators';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';
import { TransactionTypeService } from '../../../forms/form-3x/transaction-type/transaction-type.service';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from '../../../shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from '../../../shared/services/DialogService/dialog.service';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { CashOnHandModel } from '../../transactions/model/cashOnHand.model';
import { TransactionsMessageService } from './../../transactions/service/transactions-message.service';

const transactionCategoryOptions = [];

@Component({
  selector: 'transaction-sidebar',
  templateUrl: './transaction-sidebar.component.html',
  styleUrls: ['./transaction-sidebar.component.scss'],
  providers: [NgbTooltipConfig],
  encapsulation: ViewEncapsulation.None
})
export class TransactionSidebarComponent implements OnInit {
  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() transactionCategories: any = [];
  @Input() transactionsCategoriesMainData : any;
  @Input() step: string = '';
  @Input() formType:string = '';

  public editMode: boolean;
  public itemSelected: string = '';
  public typeaheadValue: string = '';
  public receiptsTotal: number = 0.0;
  public frmOption: FormGroup;
  public transactionType: string = null;
  public transactionTypeText: string = null;
  public cashOnHandTotal: number = 0.0;
  public disbursementsTotal: number = 0.0;
  public loansanddebtsTotal: number = 0.0;
  public othersTotal: number = 0.0;
  public reportId: number;
  public allTransactions: boolean = false;

  private _formType: string = '';
  public transactionCategory: string = '';
  _mainTransactionCategory: any;
  secondaryOptions: any;
  transactionCategorySelected: boolean;
  transactionTypeFailed: boolean;
  tranasctionCategoryVal: string;

  public cashOnHand: CashOnHandModel;

  private onDestroy$ = new Subject();
  routesSubscription: Subscription;

  constructor(
    private _config: NgbTooltipConfig,
    private _http: HttpClient,
    private _transactionTypeService: TransactionTypeService,
    private _activatedRoute: ActivatedRoute,
    private _messageService: MessageService,
    private _router: Router,
    private _formsService: FormsService,
    private _dialogService: DialogService,
    private _typeaheadService: TypeaheadService,
    private _transactionMessageService: TransactionsMessageService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';

    this.routesSubscription = _activatedRoute.queryParams.takeUntil(this.onDestroy$).subscribe(p => {
      if (p.transactionCategory) {
        this.itemSelected = p.transactionCategory;
      }

      if (p.allTransactions === true || p.allTransactions === 'true') {
        this.allTransactions = true;
      } else {
        this.allTransactions = false;
      }
    });
  }

  @ViewChild('instance') instance: NgbTypeahead;
  focus$ = new Subject<string>();
  click$ = new Subject<string>();

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.editMode = this._activatedRoute.snapshot.queryParams.edit === 'false' ? false : true;
    this.reportId = this._activatedRoute.snapshot.queryParams.reportId ? this._activatedRoute.snapshot.queryParams.reportId : 0;
    this._transactionTypeService.getTransactionCategories(this._formType).takeUntil(this.onDestroy$).subscribe(res => {
    if (res) {
        this.transactionCategories = res.data.transactionCategories;
        this.cashOnHand = res.data.cashOnHand;
        // this.reportId = res.data.id ? res.data.id : 0;
      }
      for (
        let transactionCategorieIndex = 0;
        transactionCategorieIndex < this.transactionCategories.length;
        transactionCategorieIndex++
      ) {
        for (
          let transactionCategoryOptionIndex = 0;
          transactionCategoryOptionIndex < this.transactionCategories[transactionCategorieIndex].options.length;
          transactionCategoryOptionIndex++
        ) {
          for (
            let transactionCategoryOptionOptionsIndex = 0;
            transactionCategoryOptionOptionsIndex <
            this.transactionCategories[transactionCategorieIndex].options[transactionCategoryOptionIndex].options
              .length;
            transactionCategoryOptionOptionsIndex++
          ) {
            transactionCategoryOptions.push(
              this.transactionCategories[transactionCategorieIndex].options[transactionCategoryOptionIndex].options[
                transactionCategoryOptionOptionsIndex
              ]
            );
          }
        }
      }
    })
  }

  ngDoCheck(): void {
    this._messageService.getMessage().takeUntil(this.onDestroy$).subscribe(res => {
      if (res) {
        if (res.hasOwnProperty('formType')) {
          if (typeof res.formType === 'string') {
            if (res.formType === this._formType) {
              if (res.hasOwnProperty('totals')) {
                if (typeof res.totals === 'object') {
                  if (res.totals.hasOwnProperty('Receipts')) {
                    if (typeof res.totals.Receipts === 'number') {
                      this.receiptsTotal = res.totals.Receipts;
                      this.cashOnHandTotal = res.totals.COH;
                      const totals: any = {
                        receipts: this.receiptsTotal,
                        cashOnHand: this.cashOnHandTotal
                      };
                      localStorage.setItem(`form_${this._formType}_totals`, JSON.stringify(totals));
                    }
                  }
                }
              }
            }
          }
        }

        if (res.hasOwnProperty('formType')) {
          if (typeof res.formType === 'string') {
            if (res.formType === this._formType) {
              if (res.hasOwnProperty('totals')) {
                if (typeof res.totals === 'object') {
                  if (res.totals.hasOwnProperty('Disbursements')) {
                    if (typeof res.totals.Disbursements === 'number') {
                      this.disbursementsTotal = res.totals.Disbursements;
                      const totals: any = {
                        receipts: this.receiptsTotal,
                        cashOnHand: this.cashOnHandTotal,
                        disbursements: this.disbursementsTotal
                      };
                      localStorage.setItem(`form_${this._formType}_totals`, JSON.stringify(totals));
                    }
                  }
                }
              }
            }
          }
        }

        if (res.hasOwnProperty('formType')) {
          if (typeof res.formType === 'string') {
            if (res.formType === this._formType) {
              if (res.hasOwnProperty('totals')) {
                if (typeof res.totals === 'object') {
                  if (res.totals.hasOwnProperty('Loans/Debts')) {
                    if (typeof res.totals['Loans/Debts'] === 'number') {
                      this.loansanddebtsTotal = res.totals['Loans/Debts'];
                      const totals: any = {
                        receipts: this.receiptsTotal,
                        cashOnHand: this.cashOnHandTotal,
                        disbursements: this.disbursementsTotal,
                        loansanddebtsTotal: this.loansanddebtsTotal
                      };
                      localStorage.setItem(`form_${this._formType}_totals`, JSON.stringify(totals));
                    }
                  }
                }
              }
            }
          }
        }

        if (this.transactionCategory && localStorage.getItem(`form_${this._formType}_temp_transaction_type`) === null) {
          this._setSecondaryTransactionCategories();
        } else if (
          this.transactionCategory &&
          localStorage.getItem(`form_${this._formType}_temp_transaction_type`) !== null
        ) {
          const transactionObj: any = JSON.parse(localStorage.getItem(`form_${this._formType}_temp_transaction_type`));

          if (transactionObj.mainTransactionTypeText !== this.transactionCategory) {
            this._setSecondaryTransactionCategories();
          }
        }
      }
    });

    if (this.receiptsTotal === 0 && localStorage.getItem(`form_${this._formType}_totals`) !== null) {
      const totals: any = JSON.parse(localStorage.getItem(`form_${this._formType}_totals`));

      if (totals.hasOwnProperty('receipts')) {
        if (typeof totals.receipts === 'number') {
          this.receiptsTotal = totals.receipts;
          this.cashOnHandTotal = totals.cashOnHand;
        }
      }
    }

    if (this.itemSelected === '') {
      this.itemSelected = 'receipts';
    }
  }

  ngOnDestroy(): void {
    this.onDestroy$.next(true);
    this.routesSubscription.unsubscribe();
    this._messageService.clearMessage();
  }

  /**
   * Sets the secondary transaction categories.
   */
  private _setSecondaryTransactionCategories(): void {
    this._mainTransactionCategory = this.transactionCategories.filter(el => el.value === this.transactionCategory);
    const mainTransactionTypeText: string = this._mainTransactionCategory[0].text;
    const mainTransactionTypeValue: string = this._mainTransactionCategory[0].value;
    const transactionObj: any = {
      mainTransactionTypeText,
      mainTransactionTypeValue,
      transactionType: '',
      childTransactionType: ''
    };

    localStorage.setItem(`form_${this._formType}_temp_transaction_type`, JSON.stringify(transactionObj));

    this.secondaryOptions = this._mainTransactionCategory[0].options;
    this.transactionCategorySelected = true;

    this.transactionTypeFailed = false;

    if (this.transactionCategory) {
      this.tranasctionCategoryVal = this.transactionCategory;

      this.transactionCategory = '';
    }
  }

  searchByType = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(200),
      distinctUntilChanged(),
      merge(this.focus$),
      merge(this.click$.pipe(filter(() => !this.instance.isPopupOpen()))),
      map(term =>
        term === ''
          ? transactionCategoryOptions
          : transactionCategoryOptions.filter(v => v.text.toLowerCase().indexOf(term.toLowerCase()) > -1)
      )
    );

  formatter = (x: { text: string }) => x.text;

  /**
   * Sets the selected item.
   *
   * @param      {Object}  e  The event object.
   */
  public selectItem(transactionCategoryValue: string): void {
    if (this.editMode) {
      this.itemSelected = transactionCategoryValue;

      this.status.emit({
        form: this._formType,
        transactionCategory: transactionCategoryValue
      });

      this._messageService.sendMessage({
        form: this._formType,
        transactionCategory: transactionCategoryValue
      });

      if (
        localStorage.getItem('Transaction_Table_Screen') === 'Yes' ||
        localStorage.getItem('Summary_Screen') === 'Yes' ||
        localStorage.getItem('Receipts_Entry_Screen') === 'Yes' ||
        localStorage.getItem('Reports_Edit_Screen') === 'Yes'
      ) {
        let queryParamsMap: any = { step: 'step_2', transactionCategory: transactionCategoryValue };
        if (this._activatedRoute.snapshot.queryParams && this._activatedRoute.snapshot.queryParams.reportId) {
          queryParamsMap.reportId = this._activatedRoute.snapshot.queryParams.reportId;
        }

        this.canDeactivate().then(result => {
          if (result === true) {
            localStorage.removeItem(`form_${this._formType}_saved`);
            this._router.navigate([`/forms/form/${this._formType}`], {
              queryParams: queryParamsMap
            });
          }
        });
      }
    } else {
      this._dialogService
        .confirm(
          'This report has been filed with the FEC. If you want to change, you must Amend the report',
          ConfirmModalComponent,
          'Warning',
          true,
          ModalHeaderClassEnum.warningHeader,
          null,
          'Return to Reports'
        )
        .then(res => {
          if (res === 'okay') {
            this.ngOnInit();
          } else if (res === 'cancel') {
            this._router.navigate(['/reports']);
          }
        });
    }
  }

  public goToAllTransactions() {
    this.canDeactivate().then(result => {
      if (result === true) {
        localStorage.removeItem(`form_${this._formType}_saved`);
        // go to different tab
        let transactionCategory = this._activatedRoute.snapshot.queryParams.transactionCategory;

        if (!transactionCategory) {
          if (localStorage.getItem('form_3X_temp_transaction_type') !== null) {
            const form3xTransactionType = JSON.parse(localStorage.getItem('form_3X_temp_transaction_type'));
            if (form3xTransactionType !== null) {
              transactionCategory = form3xTransactionType.mainTransactionTypeValue;
            }
          } else if (localStorage.getItem('form_3X_transaction_type') !== null) {
            const form3xTransactionType = JSON.parse(localStorage.getItem('form_3X_transaction_type'));
            if (form3xTransactionType !== null) {
              transactionCategory = form3xTransactionType.mainTransactionTypeValue;
            }
          }
        }
        // for filed reports transactionCategory is undefined
        // if undefined navigate to receipts tab default
        if (!transactionCategory) {
          transactionCategory = 'receipts';
        }
        this._transactionMessageService.sendLoadDefaultTabMessage({
          step: 'transactions',
          reportId: this.reportId,
          edit: this.editMode,
          transactionCategory: transactionCategory
        });
      }
    });
  }

  public selectedTypeAheadValue(e): void {
    if (this.editMode && e) {
      for (
        let transactionCategorieIndex = 0;
        transactionCategorieIndex < this.transactionCategories.length;
        transactionCategorieIndex++
      ) {
        for (
          let transactionCategoryOptionIndex = 0;
          transactionCategoryOptionIndex < this.transactionCategories[transactionCategorieIndex].options.length;
          transactionCategoryOptionIndex++
        ) {
          for (
            let transactionCategoryOptionOptionsIndex = 0;
            transactionCategoryOptionOptionsIndex <
            this.transactionCategories[transactionCategorieIndex].options[transactionCategoryOptionIndex].options
              .length;
            transactionCategoryOptionOptionsIndex++
          ) {
            if (
              e.text ===
              this.transactionCategories[transactionCategorieIndex].options[transactionCategoryOptionIndex].options[
                transactionCategoryOptionOptionsIndex
              ].text
            ) {
              this.itemSelected = this.transactionCategories[transactionCategorieIndex].value;
              this.status.emit({
                form: this._formType,
                transactionCategory: this.transactionCategories[transactionCategorieIndex].value
              });

              this._messageService.sendMessage({
                form: this._formType,
                transactionCategory: this.transactionCategories[transactionCategorieIndex].value
              });
              if (
                localStorage.getItem('Transaction_Table_Screen') === 'Yes' ||
                localStorage.getItem('Summary_Screen') === 'Yes' ||
                localStorage.getItem('Receipts_Entry_Screen') === 'Yes'
              ) {
                this._router.navigate([`/forms/form/${this._formType}`], {
                  queryParams: {
                    step: 'step_2',
                    edit: this.editMode,
                    transactionCategory: this.transactionCategories[transactionCategorieIndex].value,
                    transactionSubCategoryType: this.transactionCategories[transactionCategorieIndex].options[
                      transactionCategoryOptionIndex
                    ].value,
                    transactionSubCategory: this.transactionCategories[transactionCategorieIndex].options[
                      transactionCategoryOptionIndex
                    ].options[transactionCategoryOptionOptionsIndex].value,
                    transactionSubCategoryText: this.transactionCategories[transactionCategorieIndex].options[
                      transactionCategoryOptionIndex
                    ].options[transactionCategoryOptionOptionsIndex].text
                  }
                });
              }
              break;
            }
          }
        }
      }
    } else {
      this._dialogService
        .confirm(
          'This report has been filed with the FEC. If you want to change, you must Amend the report',
          ConfirmModalComponent,
          'Warning',
          true,
          ModalHeaderClassEnum.warningHeader,
          null,
          'Return to Reports'
        )
        .then(res => {
          if (res === 'okay') {
            this.ngOnInit();
          } else if (res === 'cancel') {
            this._router.navigate(['/reports']);
          }
        });
    }
  }

  public viewSummary(): void {
    this.canDeactivate().then(result => {
      if (result === true) {
        localStorage.removeItem(`form_${this._formType}_saved`);
        localStorage.setItem('Summary_Screen', 'Yes');
        localStorage.setItem(`form_${this._formType}_summary_screen`, 'Yes');
        this._router.navigate([`/forms/form/${this._formType}`], {
          queryParams: { step: 'financial_summary', edit: this.editMode }
        });
      }
    });
  }

  public signandSubmit(): void {
    this._router.navigate([`/signandSubmit/${this._formType}`], { queryParams: { edit: this.editMode } });
  }

  public updateTypeSelected(e): void {
    if (this.editMode) {
      const val: string = e.target.value;

      this.transactionType = val;
      this.transactionTypeText = e.target.value.text;

      this.frmOption.controls['secondaryOption'].setValue(val);

      this.transactionTypeFailed = false;
    } else {
      this._dialogService
        .confirm(
          'This report has been filed with the FEC. If you want to change, you must Amend the report',
          ConfirmModalComponent,
          'Warning',
          true,
          ModalHeaderClassEnum.warningHeader,
          null,
          'Return to Reports'
        )
        .then(res => {
          if (res === 'okay') {
            this.ngOnInit();
          } else if (res === 'cancel') {
            this._router.navigate(['/reports']);
          }
        });
    }
  }

  /**
   * Determines ability for a person to leave a page with a form on it.
   *
   * @return     {boolean}  True if able to deactivate, False otherwise.
   */
  public async canDeactivate(): Promise<boolean> {
    if (this._formsService.formHasUnsavedData(this._formType)) {
      let result: boolean = null;
      result = await this._dialogService.confirm('', ConfirmModalComponent).then(res => {
        let val: boolean = null;

        if (res === 'okay') {
          val = true;
        } else if (res === 'cancel') {
          val = false;
        }

        return val;
      });

      return result;
    } else {
      return true;
    }
  }
}
