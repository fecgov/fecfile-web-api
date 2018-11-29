import { Component, EventEmitter, ElementRef, HostListener, OnInit, Output, ViewChild, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { form99 } from '../../../shared/interfaces/FormsService/FormsService';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { ValidateComponent } from '../../../shared/partials/validate/validate.component';

@Component({
  selector: 'app-type',
  templateUrl: './type.component.html',
  styleUrls: ['./type.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class TypeComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @ViewChild('mswCollapse') mswCollapse;

  public frmType: FormGroup;
  public typeSelected: string = '';
  public isValidType: boolean = false;
  public typeFailed: boolean = false;
  public screenWidth: number = 0;
  public tooltipPosition: string = 'right';
  public tooltipLeft: string = 'auto';

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

    this.screenWidth = window.innerWidth;

    if(this.screenWidth < 768) {
      this.tooltipPosition = 'bottom';
      this.tooltipLeft = '0';
    } else if (this.screenWidth >= 768) {
      this.tooltipPosition = 'right';
      this.tooltipLeft = 'auto';
    }

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

  @HostListener('window:resize', ['$event'])
  onResize(event) {
    this.screenWidth = event.target.innerWidth;

    if(this.screenWidth < 768) {
      this.tooltipPosition = 'bottom';
      this.tooltipLeft = '0';
    } else if (this.screenWidth >= 768) {
      this.tooltipPosition = 'right';
      this.tooltipLeft = 'auto';
    }
  }  

  /**
   * Updates the type selected.
   *
   * @param      {<type>}  val     The value
   */
  public updateTypeSelected(e): void {
    console.log('typeSelected: ');
    console.log('e: ', e);
    if(e.target.checked) {
      this.typeSelected = e.target.value;
      this.typeFailed = false;
    } else {
      this.typeSelected = '';
      this.typeFailed = true;
    }
    // this.frmType.controls['reasonTypeRadio'].setValue(val);
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

  public toggleToolTip(tooltip): void {
    if (tooltip.isOpen()) {
      tooltip.close();
    } else {
      tooltip.open();
    }      
  }  

  public frmTypeValid() {
    return this.isValidType;
  }

  public cancel(): void {
    this._router.navigateByUrl('/dashboard');
  }

}
