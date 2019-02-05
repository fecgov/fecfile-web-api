import { Component, EventEmitter, Input, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { f3xTransactionTypes } from '../../../shared/interfaces/FormsService/FormsService';

@Component({
  selector: 'f3x-individual-receipt',
  templateUrl: './individual-receipt.component.html',
  styleUrls: ['./individual-receipt.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class IndividualReceiptComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() selectedOptions: any = {};
  @Input() formOptionsVisible: boolean = false;

  public formFields: any = [];
  public formVisible: boolean = false;
  public states: any = [];

  constructor(
    private _http: HttpClient
  ) { }

  ngOnInit(): void {
    console.log('individual receipt component: ');

    this._http
     .get<f3xTransactionTypes>('http://localhost:3000/data')
     .subscribe(res => {
       console.log('res: ', res);
       this.formFields = res[0].formFields;

       this.states = res[1].states;

       console.log('this.states: ', this.states);
     });
  }

  ngDoCheck(): void {
    if (this.selectedOptions) {
      if (this.selectedOptions.length >= 1) {
        this.formVisible = true;
      }
    }
  }

  public isArray(item: Array<any>): boolean {
    return Array.isArray(item);
  }

  public previous(): void {

  }
}
