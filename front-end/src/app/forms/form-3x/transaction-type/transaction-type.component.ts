import { Component, EventEmitter, Input, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { forkJoin, of, interval } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { form3x_data } from '../../../shared/interfaces/FormsService/FormsService';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';

@Component({
  selector: 'f3x-transaction-type',
  templateUrl: './transaction-type.component.html',
  styleUrls: ['./transaction-type.component.scss'],
  providers: [NgbTooltipConfig],
  encapsulation: ViewEncapsulation.None
})
export class TransactionTypeComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() selectedOptions: any = {};
  @Input() formOptionsVisible: boolean = false;

  public frmOption: FormGroup;
  public optionFailed: boolean = false;
  public showForm: boolean = false;

  constructor(
    private _fb: FormBuilder,
    private _config: NgbTooltipConfig,
    private _formService: FormsService,
    private _messageService: MessageService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this.frmOption = this._fb.group({
      optionRadio: ['', Validators.required]
    });
  }

  ngDoCheck(): void {
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
    console.log('doValidateOption: ');
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

  /**
   * Goes to the previous step.
   */
  public previousStep(): void {
    this._messageService
      .sendMessage({
        'validateMessage': {
          'validate': {},
          'showValidateBar': false
        }
      });

    this.status.emit({
      form: {},
      direction: 'previous',
      step: 'step_1'
    });
  }
}
