import { Component, EventEmitter, Input, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { DialogService } from '../../../shared/services/DialogService/dialog.service';
import { ConfirmModalComponent } from '../../../shared/partials/confirm-modal/confirm-modal.component';

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
  @Input() step: string = '';

  public itemSelected: string = null;
  public receiptsTotal: number = 0.0;

  private _formType: string = '';

  constructor(
    private _config: NgbTooltipConfig,
    private _http: HttpClient,
    private _activatedRoute: ActivatedRoute,
    private _messageService: MessageService,
    private _router: Router,
    private _formsService: FormsService,
    private _dialogService: DialogService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
  }

  ngDoCheck(): void {
    this._messageService.getMessage().subscribe(res => {
      if (res) {
        if (res.hasOwnProperty('formType')) {
          if (typeof res.formType === 'string') {
            if (res.formType === this._formType) {
              if (res.hasOwnProperty('totals')) {
                if (typeof res.totals === 'object') {
                  if (res.totals.hasOwnProperty('Receipts')) {
                    if (typeof res.totals.Receipts === 'number') {
                      this.receiptsTotal = res.totals.Receipts;
                      const totals: any = {
                        receipts: this.receiptsTotal
                      };
                      localStorage.setItem(`form_${this._formType}_totals`, JSON.stringify(totals));
                    }
                  }
                }
              }
            }
          }
        }
      }
    });

    if (this.receiptsTotal === 0 && localStorage.getItem(`form_${this._formType}_totals`) !== null) {
      const totals: any = JSON.parse(localStorage.getItem(`form_${this._formType}_totals`));

      if (totals.hasOwnProperty('receipts')) {
        if (typeof totals.receipts === 'number') {
          this.receiptsTotal = totals.receipts;
        }
      }
    }
  }

  ngOnDestroy(): void {
    this._messageService.clearMessage();
  }

  /**
   * Sets the selected item.
   *
   * @param      {Object}  e  The event object.
   */
  public selectItem(e): void {
    this.itemSelected = e.target.value;

    this.status.emit({
      form: this._formType,
      transactionCategory: e.target.value
    });

    this._messageService.sendMessage({
      form: this._formType,
      transactionCategory: e.target.value
    });

    if (
      localStorage.getItem('Transaction_Table_Screen') === 'Yes' ||
      localStorage.getItem('Summary_Screen') === 'Yes' ||
      localStorage.getItem('Receipts_Entry_Screen') === 'Yes'
    ) {
      this._router.navigate([`/forms/form/${this._formType}`], {
        queryParams: { step: 'step_2', transactionCategory: e.target.value }
      });
    }
  }

  public viewSummary(): void {
    console.log(" Form3x viewSummary clicked ...!")    
    localStorage.setItem('Summary_Screen', 'Yes');
    localStorage.setItem(`form_${this._formType}_summary_screen`, 'Yes');
    this._router.navigate([`/forms/form/${this._formType}`], { queryParams: { step: 'financial_summary' } });
  }

  public signandSubmit(): void {
    console.log(" Form3x signandSubmit clicked ...!")
    this._router.navigate([`/signandSubmit/${this._formType}`]);
  }

  /**
   * Determines ability for a person to leave a page with a form on it.
   *
   * @return     {boolean}  True if able to deactivate, False otherwise.
   */
  public async canDeactivate(): Promise<boolean> {
    if (this._formsService.formHasUnsavedData(this._formType)) {
      let result: boolean = null;
      console.log(' form not saved...');
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
      console.log('Not any unsaved data...');
      return true;
    }
  }
}
