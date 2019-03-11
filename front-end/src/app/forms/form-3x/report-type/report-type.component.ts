import { Component, EventEmitter, ElementRef, HostListener, OnInit, Input, Output, ViewChild, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { form3x } from '../../../shared/interfaces/FormsService/FormsService';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { ValidateComponent } from '../../../shared/partials/validate/validate.component';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { form3x_data, Icommittee_form3x_reporttype, form3XReport} from '../../../shared/interfaces/FormsService/FormsService';


@Component({
  selector: 'f3x-report-type',
  templateUrl: './report-type.component.html',
  styleUrls: ['./report-type.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class ReportTypeComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  public committeeReportTypes: any = null;
  public frmReportType: FormGroup;
  public reportTypeSelected: string = '';
  public isValidType: boolean = false;
  public optionFailed: boolean = false;
  public screenWidth: number = 0;
  public reportType: string = null;
  public tooltipPosition: string = 'right';
  public tooltipLeft: string = 'auto';

  private _formType: string = null;
  private _form3xDetails: any = null;

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _messageService: MessageService,
    private _formService:FormsService,
    private _activatedRoute: ActivatedRoute
  ) {
    this._messageService.clearMessage();
  }

  ngOnInit(): void {

    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this._formService
      .getreporttypes(this._formType)
      .subscribe(res => {
        if (res) {
         this.committeeReportTypes = res.report_type;
        }
      });


    this.screenWidth = window.innerWidth;

    if(this.screenWidth < 768) {
      this.tooltipPosition = 'bottom';
      this.tooltipLeft = '0';
    } else if (this.screenWidth >= 768) {
      this.tooltipPosition = 'right';
      this.tooltipLeft = 'auto';
    }

    this.frmReportType = this._fb.group({
      reportTypeRadio: ['', Validators.required]

    });
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
   * TODO:
   * Get the regularReport and specialReport variables working.
   */

  /**
   * Updates the type selected.
   *
   * @param      {Object}  e   The event object.
   */
  public updateTypeSelected(e): void {
    if(e.target.checked) {
      this.reportTypeSelected = this.frmReportType.get('reportTypeRadio').value;
      this.optionFailed = false;
      this.reportType = this.reportTypeSelected;

      this.status.emit({
        reportTypeRadio: this.reportTypeSelected
      });
    } else {
      this.reportTypeSelected = '';
      this.optionFailed = true;
    }
  }

  /**
   * Validates the type selected form.
   *
   */
  public doValidateReportType() {
    if (this.frmReportType.get('reportTypeRadio').value) {
        this.optionFailed = false;
        this.isValidType = true;
        // this._form_3x_details = JSON.parse(localStorage.getItem('form_3x_details'));

        //this._form_3x_details.reason = this.frmType.get('reportTypeRadio').value;

        // setTimeout(() => {
        //   localStorage.setItem('form_3x_details', JSON.stringify(this._form_3x_details));
        // }, 100);

        this.status.emit({
          form: this.frmReportType,
          direction: 'next',
          step: 'step_2',
          previousStep: 'step_1'
        });

        //this.saveReport();
        return 1;
    } else {
      this.optionFailed = true;
      this.isValidType = false;

      this.status.emit({
        form: this.frmReportType,
        direction: 'next',
        step: 'step_2',
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

  public cancel(): void {
    this._router.navigateByUrl('/dashboard');
  }

}
