import { Component, Input, OnInit, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { forkJoin, of, interval } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { form3x_data } from '../../../shared/interfaces/FormsService/FormsService';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
@Component({
  selector: 'f3x-transaction-type',
  templateUrl: './transaction-type.component.html',
  styleUrls: ['./transaction-type.component.scss'],
  providers: [NgbTooltipConfig],
  encapsulation: ViewEncapsulation.None
})
export class TransactionTypeComponent implements OnInit {

  @Input() selectedOptions: any = {};
  @Input() formOptionsVisible: boolean = false;

  public frmOption: FormGroup;
  public optionFailed: boolean = false;
  public showForm: boolean = false;

  constructor(
    private _fb: FormBuilder,
    private _config: NgbTooltipConfig,
    private _formService:FormsService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    console.log("transaction-type.component before this.frmOption ...");
    this.frmOption = this._fb.group({
      optionRadio: ['', Validators.required]
    });
    console.log("transaction-type.component after this.frmOption ...");
  }

  ngDoCheck(): void {
    console.log("transaction-type.component ngDoCheck...");
    if (this.selectedOptions) {
      this.showForm = true;
    }
  }
  /**
   * Validates the form on submit.
   *
   * @return     {Boolean}  A boolean indicating weather or not the form can be submitted.
   */
  public doValidateOption(): boolean {
    if (this.frmOption.invalid) {
      this.optionFailed = true;
      return false;
    } else {
      this.optionFailed = false;
      return true;
    }
  }

  /**
   * Updates the status of any form erros when a radio button is clicked.
   *
   * @param      {Object}  e       The event object.
   */
  public updateStatus(e): void {
    if (e.target.checked) {
      this.optionFailed = false;
    } else {
      this.optionFailed = true;
    }
  }

}
