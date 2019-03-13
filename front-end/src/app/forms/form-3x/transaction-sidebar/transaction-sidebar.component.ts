import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'transaction-sidebar',
  templateUrl: './transaction-sidebar.component.html',
  styleUrls: ['./transaction-sidebar.component.scss'],
  providers: [NgbTooltipConfig]
})
export class TransactionSidebarComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() transactionCategories: any = [];

  public additionalItemSelected: string = '';
  public additionalOptions: Array<any> = [];
  public cashOnHand: any = {};
  public currentStep: string = 'step_2';
  public itemSelected: string = '';
  // public transactionCategories: any = [];

  private _formType: string = '';

  constructor(
    private _config: NgbTooltipConfig,
    private _http: HttpClient,
    private _activatedRoute: ActivatedRoute
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
  }

  // public selectItem(e): void {
  //   console.log('selectItem: ');
  //   console.log('e: ', e.target.getAttribute('value'));
  //   this.itemSelected = '';
  //   // item.getAttribute('value');

  //   this.additionalOptions = [];

  //   this.transactionCategories.findIndex((el, index) => {
  //     if (el.value === this.itemSelected) {
  //       this._indexOfItemSelected = index;
  //     }
  //   });

  //   if(localStorage.getItem(`form_${this._formType}_transactionType`) === null) {
  //     localStorage.setItem(`form_${this._formType}_transactionType`, JSON.stringify({
  //       'category': this.itemSelected,
  //       'type': ''
  //     }));
  //   }
  // }
  public selectItem(e): void {
    console.log('selectItem: ');
    console.log('e: ', e);
  }
}
