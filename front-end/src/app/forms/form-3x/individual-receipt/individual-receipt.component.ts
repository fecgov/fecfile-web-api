import { Component, EventEmitter, Input, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { FormBuilder, FormGroup, FormControl, NgForm, Validators } from '@angular/forms';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../../environments/environment';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { UtilService } from '../../../shared/utils/util.service';
import { IndividualReceiptService } from './individual-receipt.service';
import { f3xTransactionTypes } from '../../../shared/interfaces/FormsService/FormsService';
import { alphanumeric } from '../../../shared/utils/forms/validation/alphaNumeric.validator';

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
  @Input() transactionTypeText = '';

  public formFields: any = [];
  public frmIndividualReceipt: FormGroup;
  public testForm: FormGroup;
  public formVisible: boolean = false;
  public states: any = [];

  private _formType: string = '';
  private _types: any = [];
  private _transaction: any = {};

  constructor(
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _formService: FormsService,
    private _individualReceiptService: IndividualReceiptService,
    private _activatedRoute: ActivatedRoute,
    private _config: NgbTooltipConfig,
    private _router: Router,
    private _utilService: UtilService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this.frmIndividualReceipt = this._fb.group({});

    this._individualReceiptService.getDynamicFormFields(this._formType, 'Individual Receipt').subscribe(res => {
      console.log('res: ', res);
      // this.formFields = res.data.formFields;
      this.formFields = res.formFields;
      this._setForm(this.formFields);
      this.states = res.states;

      // this.states = res.data.states;
    });
  }

  ngDoCheck(): void {
    if (this.selectedOptions) {
      if (this.selectedOptions.length >= 1) {
        this.formVisible = true;
      }
    }

    if (this.frmIndividualReceipt.touched || this.frmIndividualReceipt.dirty) {
      if (this.frmIndividualReceipt.invalid) {
        console.log('this.frmIndividualReceipt:', this.frmIndividualReceipt);
      }
    }
  }

  /**
   * Move the following template functions to utils.
   */

  /**
   * For testing from within template if object is a object.
   *
   * @param      {any}      obj     The object
   * @return     {boolean}  True if object, False otherwise.
   */
  public isObject(obj: any): boolean {
    return typeof obj === 'object' ? true : false;
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
   * Generates the dynamic form after all the form fields are retrived.
   *
   * @param      {Array}  fields  The fields
   */
  private _setForm(fields: any): void {
    const formGroup: any = [];

    fields.forEach(el => {
      if (el.hasOwnProperty('cols')) {
        el.cols.forEach(e => {
          formGroup[e.name] = new FormControl(e.value || null, this._mapValidators(e.validation));
        });
      }
    });

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

    if (validators) {
      for (const validation of Object.keys(validators)) {
        if (validation === 'required') {
          formValidators.push(Validators.required);
        } else if (validation === 'min') {
          formValidators.push(Validators.minLength(validators[validation]));
        } else if (validation === 'max') {
          formValidators.push(Validators.maxLength(validators[validation]));
        } else if (validation === 'dollarAmount') {
          const dollarRegEx: any = /^[+-]?\d+(\.\d+)?$/g;

          formValidators.push(Validators.pattern(dollarRegEx));
        } else if (validation === 'alphaNumeric') {
          formValidators.push(alphanumeric());
          // const alphaNumericRegEx: any = /^(([a-z]|[A-Z])+)$/gi;

          // formValidators.push(Validators.pattern(alphaNumericRegEx));
        } else if (validation === 'date') {
          const dateRegEx: any = /^(\d{4}\-\d{2}\-\d{2})/;

          formValidators.push(Validators.pattern(dateRegEx));
        }
      }
    }

    return formValidators;
  }

  /**
   * Vaidates the form on submit.
   */
  public doValidateReceipt() {
    if (this.frmIndividualReceipt.valid) {
      let receiptObj: any = {};

      for (const field in this.frmIndividualReceipt.controls) {
        if (field === 'ContributionDate') {
          receiptObj[field] = this._utilService.formatDate(this.frmIndividualReceipt.get(field).value);
        } else {
          receiptObj[field] = this.frmIndividualReceipt.get(field).value;
        }
      }

      localStorage.setItem(`form_${this._formType}_receipt`, JSON.stringify(receiptObj));

      this._individualReceiptService.saveScheduleA(this._formType).subscribe(res => {
        if (res) {
          this.frmIndividualReceipt.reset();
          window.scrollTo(0, 0);
        }
      });
    } else {
      this.frmIndividualReceipt.markAsDirty();
      this.frmIndividualReceipt.markAsTouched();
      window.scrollTo(0, 0);
    }
  }

  /**
   * Goes to the previous step.
   */
  public previousStep(): void {
    this.status.emit({
      form: {},
      direction: 'previous',
      step: 'step_2'
    });
  }
}
