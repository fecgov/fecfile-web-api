import { animate, style, transition, trigger } from '@angular/animations';
import { Component, OnInit, ViewEncapsulation, OnDestroy, Output, EventEmitter } from '@angular/core';
import { TransactionTypeService } from '../../form-3x/transaction-type/transaction-type.service';
import { ActivatedRoute } from '@angular/router';

/**
 * The parent component for transactions.
 */
@Component({
  selector: 'app-transactions-wrapper',
  templateUrl: './transactions-wrapper.component.html',
  styleUrls: ['./transactions-wrapper.component.scss'],
  encapsulation: ViewEncapsulation.None,
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [style({ opacity: 0 }), animate(500, style({ opacity: 1 }))]),
      transition(':leave', [animate(10, style({ opacity: 0 }))])
    ])
  ]
})
export class TransactionsWrapperComponent implements OnInit {
  public isShowFilters: boolean;
  public transactionCategories: any = [];
  public formType: string;
  public reportId: string;

  public constructor(
    private _transactionTypeService: TransactionTypeService,
    private _activatedRoute: ActivatedRoute
  ) {}

  /**
   * Initialize the component.
   */
  public ngOnInit(): void {
    this.isShowFilters = false;
    this.formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.reportId = this._activatedRoute.snapshot.paramMap.get('report_id');

    this._transactionTypeService.getTransactionCategories(this.formType).subscribe(res => {
      if (res) {
        this.transactionCategories = res.data.transactionCategories;
      }
    });
  }

  /**
   * Get's message from child components to change the sidebar
   * in the view.
   */
  public switchSidebar(e: boolean): void {
    this.isShowFilters = e;
    console.log('showfilters is ' + this.isShowFilters);
  }
}
