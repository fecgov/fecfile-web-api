import { Component, EventEmitter, ElementRef, OnInit, Output, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { form99 } from '../../../shared/interfaces/FormsService/FormsService';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { ValidateComponent } from '../../../shared/partials/validate/validate.component';

@Component({
  selector: 'app-type',
  templateUrl: './type.component.html',
  styleUrls: ['./type.component.scss']
})
export class TypeComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @ViewChild('mswCollapse') mswCollapse;

  public frmType: FormGroup;
  public typeSelected: string = '';
  public isValidType: boolean = false;
  public typeFailed: boolean = false;

  private _form_99_details: form99;

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _messageService: MessageService
  ) {
    this._messageService.clearMessage();
  }

  ngOnInit(): void {
    this._form_99_details = JSON.parse(localStorage.getItem('form_99_details'));

    if(this._form_99_details) {
      if(this._form_99_details.reason) {
        this.typeSelected = this._form_99_details.reason;
        this.frmType = this._fb.group({
          reasonTypeRadio: [this._form_99_details.reason, Validators.required]
        });
      } else {
        this.frmType = this._fb.group({
          reasonTypeRadio: ['', Validators.required]
        });
      }
    } else {
      this.frmType = this._fb.group({
            reasonTypeRadio: ['', Validators.required]
          });
    }
  }

  /**
   * Updates the type selected.
   *
   * @param      {<type>}  val     The value
   */
  public updateTypeSelected(val: string): void {
    this.typeSelected = val;

    this.frmType.controls['reasonTypeRadio'].setValue(val);
  }

  /**
   * Validates the type selected form.
   *
   */
  public doValidateType() {
    if (this.frmType.get('reasonTypeRadio').value) {
        this.typeFailed = false;
        this.isValidType = true;
        this._form_99_details = JSON.parse(localStorage.getItem('form_99_details'));

        this._form_99_details.reason = this.frmType.get('reasonTypeRadio').value;

        setTimeout(() => {
          localStorage.setItem('form_99_details', JSON.stringify(this._form_99_details));
        }, 100);
        

        this.status.emit({
          form: this.frmType,
          direction: 'next',
          step: 'step_2',
          previousStep: 'step_1'
        });

        return 1;
    } else {
      this.typeFailed = true;
      this.isValidType = false;

      this.status.emit({
        form: this.frmType,
        direction: 'next',
        step: 'step_1',
        previousStep: ''
      });

      return 0;
    }
  }

  public frmTypeValid() {
    return this.isValidType;
  }

  public cancel(): void {
    this._router.navigateByUrl('/dashboard');
  }

}
