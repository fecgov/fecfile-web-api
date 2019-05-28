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
  public formSubmitted: boolean = false;
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
      this.formFields = res.data.formFields;
      this._setForm(this.formFields);
      this.states = res.data.states;
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

    fields.forEach(el => {
      el.cols.forEach(e => {
        if (
          e.name !== 'LineNumber' &&
          e.name !== 'TransactionId' &&
          e.name !== 'TransactionTypeCode' &&
          e.name !== 'BackReferenceTranIdNumber' &&
          e.name !== 'BackReferenceSchedName'
        ) {
          formGroup[e.name] = new FormControl(e.value || null, this._mapValidators(e.validation));
        }
      });
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
          formValidators.push(Validators.min(validators[validation]));
        }
      }
    }

    return formValidators;
  }

  /**
   * Checks for hidden fields.
   *
   * @param      {number}  i       The current index for the item.
   * @param      {any}     item    The item.
   */
  public hasHiddenFields(i: number, item: any): void {
    let skipRow: any = null;
    if (item.hasOwnProperty('cols')) {
      if (Array.isArray(item.cols)) {
        skipRow = item.cols.findIndex(
          el =>
            el.name === 'LineNumber' ||
            el.name === 'TransactionId' ||
            el.name === 'TransactionTypeCode' ||
            el.name === 'BackReferenceTranIdNumber' ||
            el.name === 'BackReferenceSchedName'
        );

        if (skipRow === 0) {
          item['hiddenFields'] = true;
        } else {
          item['hiddenFields'] = false;
        }

        return item;
      }
    }
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
   * Vaidates the form on submit.
   */
  public doValidateReceipt() {
    this.formSubmitted = true;
    if (this.frmIndividualReceipt.valid) {
      this.formSubmitted = false;
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
          console.log('res: ', res);

          this._individualReceiptService.getSchedA(this._formType, res).subscribe(resp => {
            console.log('resp: ', resp);
          });

          this.frmIndividualReceipt.reset();
          this.formSubmitted = false;
          window.scrollTo(0, 0);
        }
      });
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
