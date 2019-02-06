import { Component, EventEmitter, Input, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { FormBuilder, FormGroup, FormControl, NgForm, Validators } from '@angular/forms';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { f3xTransactionTypes } from '../../../shared/interfaces/FormsService/FormsService';

@Component({
  selector: 'f3x-individual-receipt',
  templateUrl: './individual-receipt.component.html',
  styleUrls: ['./individual-receipt.component.scss'],
  providers: [NgbTooltipConfig],
  encapsulation: ViewEncapsulation.None
})
export class IndividualReceiptComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() selectedOptions: any = {};
  @Input() formOptionsVisible: boolean = false;

  public formFields: any = [];
  public frmIndividualReceipt: FormGroup;
  public formVisible: boolean = false;
  public states: any = [];
  public transactionCategories: any = [];
  public transactionTypes: any = [];

  private _formType: string = '';
  private _types: any = [];

  constructor(
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _formService: FormsService,
    private _activatedRoute: ActivatedRoute,
    private _config: NgbTooltipConfig,
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this._http
     .get<f3xTransactionTypes>('http://localhost:3000/data')
     .subscribe(res => {
       this.formFields = res[0].formFields;

       this.states = res[1].states;

       this.transactionCategories = res[2].transactionCategories;
     });

    this._formService
      .getTransactionCategories(this._formType)
      .subscribe(res => {
        this._types = res.data.transactionCategories;
      });

      this.frmIndividualReceipt = this._fb.group({
        transactionCategory: ['', [
          Validators.required
        ]],
        transactionType: ['', [
          Validators.required
        ]]
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

  public transactionCategorySelected(e): void {
    if(typeof e !== 'undefined') {
      const selectedValue: string = e.value;
      const selectedType: string = e.type;
      let selectedIndex: number = 0;
      let childIndex: number = 0;

      this.frmIndividualReceipt.setValue({
        transactionCategory: selectedValue,
        transactionType: ''
      });

      this._types.findIndex((el, index) => {
        if(el.text === selectedType) {
          selectedIndex = index;
        }
      });
      this._types[selectedIndex].options.findIndex((el, index) => {
        if(el.value === selectedValue) {
          childIndex = index;
        }
      });

      this.transactionTypes = this._types[selectedIndex].options[childIndex].options;
    } else {
      this.frmIndividualReceipt.setValue({
        transactionCategory: '',
        transactionType: ''
      });
    }
  }

  public transactionTypeSelected(e): void {
    console.log('transactionTypeSelected: ');
    if(typeof e !== 'undefined') {
      const selectedValue: string = e.value;
      const selectedType: string = e.type;

      console.log('this.frmIndividualReceipt: ', this.frmIndividualReceipt);
    } else {

    }
  }
}
