import { Component, EventEmitter, ElementRef, HostListener, OnInit, Output, ViewChild, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { Router, NavigationEnd } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { form3x } from '../../../shared/interfaces/FormsService/FormsService';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { ValidateComponent } from '../../../shared/partials/validate/validate.component';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { form3x_data, Icommittee_form3x_reporttype} from '../../../shared/interfaces/FormsService/FormsService';
import { forkJoin, of, interval } from 'rxjs';


@Component({
  selector: 'f3x-report-type',
  templateUrl: './report-type.component.html',
  styleUrls: ['./report-type.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class ReportTypeComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @ViewChild('mswCollapse') mswCollapse;

  public frmReportType: FormGroup;
  public typeSelected: string = '';
  public isValidType: boolean = false;
  public optionFailed: boolean = false;
  public screenWidth: number = 0;
  public tooltipPosition: string = 'right';
  public tooltipLeft: string = 'auto';

  private _form_3x_details: form3x;
  private _newForm: boolean = false;
  private _previousUrl: string = null;
  public reporttypes: any = {};

  public committee_form3x_reporttypes: Icommittee_form3x_reporttype[];

  public sidebarLinks: any = {};
  public selectedOptions: any = [];
  public searchField: any = {};
  public cashOnHand: any = {};

  public frm: any;
  public direction: string;
  public previousStep: string = '';
  private _step: string = '';
  private _form_type: string = '';
  private step: string = "";
  private next_step: string = "Step-2";

  public showForm: boolean = true;

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _messageService: MessageService,
    private _formService:FormsService
  ) {
    this._messageService.clearMessage();
  }

  ngOnInit(): void {

    console.log("accessing form service call side bar ...");

   this._formService
    .get_form3x_reporttype()
     .subscribe(res => {
      console.log(' getspecialreporttypes res: ', res);
      this.committee_form3x_reporttypes = <Icommittee_form3x_reporttype[]> res;
      console.log(' this.committee_form3x_reporttypes: ', this.committee_form3x_reporttypes);
     });


    console.log("this.committee_form3x_reporttypes = ",this.committee_form3x_reporttypes);

    this._form_3x_details = JSON.parse(localStorage.getItem('form_3X_details'));

    this.screenWidth = window.innerWidth;

    if(this.screenWidth < 768) {
      this.tooltipPosition = 'bottom';
      this.tooltipLeft = '0';
    } else if (this.screenWidth >= 768) {
      this.tooltipPosition = 'right';
      this.tooltipLeft = 'auto';
    }

    this._setForm();

    this._router
      .events
      .subscribe(e => {
        if(e instanceof NavigationEnd) {
          this._previousUrl = e.url;
          if(this._previousUrl === '/forms/form/3X?step=step_5') {
            this._form_3x_details = JSON.parse(localStorage.getItem('form_3X_details'));

            this.typeSelected = '';

            this._setForm();
          }
        }
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

  private _setForm(): void {
    this.frmReportType = this._fb.group({
      reportTypeRadio: ["", Validators.required]

    });
  }

  /**
   * Updates the type selected.
   *
   * @param      {<type>}  val     The value
   */
  public updateTypeSelected(e): void {
    if(e.target.checked) {
      this.typeSelected = e.target.value;
      this.optionFailed = false;
    } else {
      this.typeSelected = '';
      this.optionFailed = true;
    }
    // this.frmType.controls['reportTypeRadio'].setValue(val);
  }

  /**
   * Validates the type selected form.
   *
   */
  public doValidatereportType() {
    if (this.frmReportType.get('reportTypeRadio').value) {
        this.optionFailed = false;
        this.isValidType = true;
        this._form_3x_details = JSON.parse(localStorage.getItem('form_3x_details'));

        //this._form_3x_details.reason = this.frmType.get('reportTypeRadio').value;

        setTimeout(() => {
          localStorage.setItem('form_3x_details', JSON.stringify(this._form_3x_details));
        }, 100);

        console.log(" report-type.component doValidateType");

        this.status.emit({
          form: this.frmReportType,
          direction: 'next',
          step: 'step_2',
          previousStep: 'step_1'
        });

        console.log(" report-type.component After status.emit");
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

  public frmTypeValid() {
    return this.isValidType;
  }

  public cancel(): void {
    this._router.navigateByUrl('/dashboard');
  }
  public Savadata(): void {

   /* console.log("this.direction=",this.direction);

    if(this.frm && this.direction) {
      if(this.direction === 'next') {
        if(this.frm.valid) {
          this.step = this.next_step;

          this._router.navigate(['/forms/form/3X'], { queryParams: { step: this.step } });
        } else if(this.frm === 'preview') {
          this.step = this.next_step;

          this._router.navigate(['/forms/form/3X'], { queryParams: { step: this.step } });
        }
      } else if(this.direction === 'previous') {
        this.step = this.next_step;

        this._router.navigate(['/forms/form/3X'], { queryParams: { step: this.next_step; } });
      }
    }*/
    localStorage.setItem('form_3X_details.printpriview_fileurl', "");
    this._router.navigateByUrl('/forms/form/3X?step=step_2');
  }

}
