import { Component, EventEmitter, Input, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';

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
    private _router: Router
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    console.log("transactionCategories =", this.transactionCategories);
  }

  ngDoCheck(): void {
   
    console.log("check total receipts value...");
     this._messageService.getMessage().subscribe(res => {
      if (res) {
        console.log("res =", res);
        if (res.hasOwnProperty('formType')) {
          if (typeof res.formType === 'string') {
            if (res.formType === this._formType) {
              if (res.hasOwnProperty('totals')) {
                if (typeof res.totals === 'object') {
                  // console.log('res: ', res);
                  if (res.totals.hasOwnProperty('Receipts')) {
                    if (typeof res.totals.Receipts === 'number') {
                      this.receiptsTotal = res.totals.Receipts;
                      console.log("this.receiptsTotal", this.receiptsTotal);
                    }
                  }
                }
              }
            }
          }
        }
      }
    });
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

    if (localStorage.getItem('Transaction_Table_Screen') === 'Yes' || localStorage.getItem('Summary_Screen') === 'Yes'){
      this._router.navigate([`/forms/form/${this._formType}`], { queryParams: { step: 'step_2', transactionCategory: e.target.value} });
    }
    
  }
}
