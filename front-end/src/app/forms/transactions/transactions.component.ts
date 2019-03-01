import { animate, style, transition, trigger } from '@angular/animations';
import { Component, OnInit, ViewChild, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { TransactionsTableComponent } from './transactions-table/transactions-table.component';
import { TransactionsMessageService } from './service/transactions-message.service';

export enum ActiveView {
  transactions = 'transactions',
  recycleBin = 'recycleBin'
}

/**
 * The parent component for transactions.
 */
@Component({
  selector: 'app-transactions',
  templateUrl: './transactions.component.html',
  styleUrls: ['./transactions.component.scss'],
  encapsulation: ViewEncapsulation.None,
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate(500, style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate(10, style({ opacity: 0 }))
      ])
    ])
  ]
})
export class TransactionsComponent implements OnInit {

  public formType = '';
  public appliedFilterNames: Array<string> = [];
  public view: string = ActiveView.transactions;
  public transactionsView = ActiveView.transactions;
  public recycleBinView = ActiveView.recycleBin;


  constructor(
    private _activatedRoute: ActivatedRoute,
    private _transactionsMessageService: TransactionsMessageService,
  ) { }


  /**
   * Initialize the component.
   */
  public ngOnInit(): void {

    this.formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    console.log('transactions for form ' + this.formType);

    // push an applied filter for test
    this.appliedFilterNames.push('Filter ' + this.appliedFilterNames.length + 1);
  }


  /**
   * Show the table of transactions in the recycle bin for the user.
   */
  public showRecycleBin() {
    this.view = ActiveView.recycleBin;
  }


  /**
   * Show the table of form transactions.
   */
  public showTransactions() {
    this.view = ActiveView.transactions;
  }


  /**
   * Show the option to select/deselect columns in the table.
   */
  public showPinColumns() {
    this.showTransactions();
    this._transactionsMessageService.sendMessage('show the Pin Col');
  }


  /**
   * Import transactions from an external file.
   */
  public doImport() {
    alert('Import transactions is not yet supported');
  }


  /**
   * Show filter options for transactions.
   */
  public showFilters() {
    alert('Transaction filters are not yet supported');
  }


  /**
   * Navigate to the Categories component.
   */
  public navigateToCategories() {
    alert('Return to Categories is not yet supported');
  }


  /**
   * Check if the view to show is Transactions.
   */
  public isTransactionViewActive() {
    return this.view === this.transactionsView ? true : false;
  }


  /**
   * Check if the view to show is Recycle Bin.
   */
  public isRecycleBinViewActive() {
    return this.view === this.recycleBinView ? true : false;
  }

}
