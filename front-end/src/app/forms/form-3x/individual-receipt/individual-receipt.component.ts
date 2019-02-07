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
  public testForm: FormGroup;
  public formVisible: boolean = false;
  public states: any = [];
  public transactionCategories: any = null;
  public transactionTypes: any = null;

  private _formType: string = '';
  private _types: any = [];
  private _transaction: any = {};

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

       this._setForm(this.formFields);

       this.states = res[1].states;

       this.transactionCategories = res[2].transactionCategories;
     });

    this._formService
      .getTransactionCategories(this._formType)
      .subscribe(res => {
        this._types = res.data.transactionCategories;
      });


    this.frmIndividualReceipt = this._fb.group({
      transactionCategory: [null, [
        Validators.required
      ]],
      transactionType: [null, [
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

  /**
   * Generates the dynamic form after all the form fields are retrived.
   *
   * @param      {Array}  fields  The fields
   */
  private _setForm(fields: any): void {
    const formGroup: any = [];

    fields.forEach((el) => {
      el.cols.forEach((e) => {
        formGroup[e.name] = new FormControl(e.value || null, this._mapValidators(e.validation));
      });
    });

    formGroup['transactionCategory'] = new FormControl(
       this._types['transactionCategory'] || null,
       [Validators.required]
    );

    formGroup['transactionType'] = new FormControl(
      this._types['transactionType'] || null,
      [Validators.required]
    );

    this.frmIndividualReceipt = new FormGroup(formGroup);
  }

  /**
   * Sets the form field valition requirements.
   *
   * @param      {Object}  validators  The validators
   * @return     {Array}  The validations in an Array.
   */
  private _mapValidators(validators): Array<any> {
    const formValidators = [];

    if(validators) {
      for(const validation of Object.keys(validators)) {
        if(validation === 'required') {
          formValidators.push(Validators.required);
        } else if(validation === 'min') {
          formValidators.push(Validators.min(validators[validation]));
        }
      }
    }

    return formValidators;
  }

  /**
   * Determines if element passed in from template is an array.
   *
   * @param      {<Array>}   item    The item
   * @return     {Boolean}  True if array, False otherwise.
   */
  public isArray(item: Array<any>): boolean {
    return Array.isArray(item);
  }

  /**
   * Sets the transaction category when selected and sets the child items for transaction type.
   *
   * @param      {Object}  e       { parameter_description }
   */
  public transactionCategorySelected(e): void {
    if(typeof e !== 'undefined') {
      const selectedValue: string = e.value;
      const selectedType: string = e.type;
      let selectedIndex: number = 0;
      let childIndex: number = 0;

      this._types['transactionCategory'] = selectedValue;

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

      this.frmIndividualReceipt.controls['transactionType'].setValue(null);
    }
  }

  public doValidateReceipt(): boolean {
    console.log('doValidate: ');
    console.log('this.frmIndividualReceipt: ', this.frmIndividualReceipt);

    if(this.frmIndividualReceipt.valid) {

    }
    return;
  }
}
