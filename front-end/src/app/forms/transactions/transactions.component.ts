import { Component, OnInit, ViewEncapsulation, ViewChild } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { style, animate, transition, trigger } from '@angular/animations';
import { TransactionModel } from './model/transaction.model';
import { PaginationInstance } from 'ngx-pagination';
import { TransactionsTableComponent } from './transactions-table/transactions-table.component';

export enum ActiveView {
  transactions = "1",
  recycleBin = "2"
}

@Component({
  selector: 'app-transactions',
  templateUrl: './transactions.component.html',
  styleUrls: ['./transactions.component.scss'],
  encapsulation: ViewEncapsulation.None,
  animations: [
		trigger('fadeInOut', [
			transition(':enter', [
				style({opacity:0}),
				animate(500, style({opacity:1})) 
      ]),
				transition(':leave', [
				animate(10, style({opacity:0})) 
			])
		])
	]
})
export class TransactionsComponent implements OnInit {

  // TODO receiving circular dependency warning when compiling
  // after adding this child component.
  @ViewChild(TransactionsTableComponent)
  public transactionsTableComponent: TransactionsTableComponent; 

  

  public transactionsModel: Array<TransactionModel>;
  public deletedTransactionsModel: Array<TransactionModel>;
  public totalAmount: number;
  private _formType: string = '';
  public formType: string = '';
  public appliedFilterNames: Array<string> = [];
  public view: string = ActiveView.transactions;
  public transactionsView = ActiveView.transactions;
  public recycleBinView = ActiveView.recycleBin;
  public pinColumns: boolean = false;



  // ngx-pagination config
  public maxItemsPerPage: number = 100;
  public directionLinks: boolean = false;
  public autoHide: boolean = true;	
  public config: PaginationInstance;
  

  constructor(
    private _activatedRoute: ActivatedRoute,
  ) { }


  /**
   * Initialize the component.
   */
  public ngOnInit(): void {

    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.formType = this._formType;
    console.log("transactions for form " + this._formType);

    // push an applied filter for test
    this.appliedFilterNames.push("Filter " + this.appliedFilterNames.length + 1);
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
    this.transactionsTableComponent.showPinColumns();
  }


  /**
   * Check if the view to show is Transactions.
   */
  public isTransactionViewActive() {
    return this.view == this.transactionsView ? true : false;
  }


  /**
   * Check if the view to show is Recycle Bin.
   */
  public isRecycleBinViewActive() {
    return this.view == this.recycleBinView ? true : false;
  }  

}
