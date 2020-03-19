import { Subscription } from 'rxjs/Subscription';
import { Component, EventEmitter, ElementRef, HostListener, OnInit, Output, ViewChild, ViewEncapsulation, ChangeDetectionStrategy, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { Router, ActivatedRoute, NavigationEnd } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { form99 } from '../../../shared/interfaces/FormsService/FormsService';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { ValidateComponent } from '../../../shared/partials/validate/validate.component';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
@Component({
  selector: 'f99-type',
  templateUrl: './type.component.html',
  styleUrls: ['./type.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class TypeComponent implements OnInit, OnDestroy {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @ViewChild('mswCollapse') mswCollapse;

  public frmType: FormGroup;
  public editMode: boolean;
  public reportId: number;
  public typeSelected: string = '';
  public isValidType: boolean = false;
  public typeFailed: boolean = false;
  public screenWidth: number = 0;
  public tooltipPosition: string = 'right';
  public tooltipLeft: string = 'auto';

  private committee_details: any = {};
  private _form99Details: form99;
  private _newForm: boolean = false;
  private _previousUrl: string = null;
  private _setRefresh: boolean = false;
  queryParamsSubscription: Subscription;
  routerEventsSubscription: Subscription;

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _messageService: MessageService,
    private _activatedRoute: ActivatedRoute,
    private _dialogService: DialogService
  ) {
    this._messageService.clearMessage();
    this.queryParamsSubscription = _activatedRoute.queryParams.subscribe(p => {
      if (p.refresh) {
        this._setRefresh = true;
        this.ngOnInit();
      }
      if (p.reportId) {
        this.reportId = p.reportId;
      }
    });
  }

  ngOnInit(): void {
    this._form99Details = null;
    this._form99Details = JSON.parse(localStorage.getItem('form_99_details'));
    this.committee_details = JSON.parse(localStorage.getItem('committee_details'));
    //console.log(" type this._form99Details =", this._form99Details)
    this.screenWidth = window.innerWidth;
    this.editMode = this._activatedRoute.snapshot.queryParams.edit === 'false' ? false : true;

    //console.log(" Type this.editMode = ", this.editMode);
    //console.log(" Type this._form99Details = ", this._form99Details);


    if(this.screenWidth < 768) {
      this.tooltipPosition = 'bottom';
      this.tooltipLeft = '0';
    } else if (this.screenWidth >= 768) {
      this.tooltipPosition = 'right';
      this.tooltipLeft = 'auto';
    }

    this._setForm();

    this.routerEventsSubscription = this._router
      .events
      .subscribe(e => {
        if(e instanceof NavigationEnd) {
          this._previousUrl = e.url;
          if(this._previousUrl === '/forms/form/99?step=step_5') {
            this._form99Details = JSON.parse(localStorage.getItem('form_99_details'));

            this.typeSelected = '';

            this._setForm();
          }
        }
      });
  }

  ngOnDestroy(): void {
    this.queryParamsSubscription.unsubscribe();
    this.routerEventsSubscription.unsubscribe();
  }

 /*ngAfterViewChecked(): void {
  this._form99Details = JSON.parse(localStorage.getItem('form_99_details'));
  //console.log(" ngAfterViewChecked type this._form99Details =", this._form99Details)
  this.screenWidth = window.innerWidth;

  if(this.screenWidth < 768) {
    this.tooltipPosition = 'bottom';
    this.tooltipLeft = '0';
  } else if (this.screenWidth >= 768) {
    this.tooltipPosition = 'right';
    this.tooltipLeft = 'auto';
  }

  this._setForm();
 } */
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
    if(this._form99Details) {
      if(this._form99Details.reason) {
        this.typeSelected = this._form99Details.reason;
        this.frmType = this._fb.group({
          reasonTypeRadio: [this._form99Details.reason, Validators.required]
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

  private _setF99Details(): void {
    if(this.committee_details) {
      if(this.committee_details.committeeid) {
        this._form99Details = this.committee_details;

        this._form99Details.reason = '';
        this._form99Details.text = '';
        this._form99Details.signee = `${this.committee_details.treasurerfirstname} ${this.committee_details.treasurerlastname}`;
        this._form99Details.additional_email_1 = '-';
        this._form99Details.additional_email_2 = '-';
        this._form99Details.created_at = '';
        this._form99Details.is_submitted = false;
        this._form99Details.id = '';

        let formSavedObj: any = {
          'saved': false
        };
        localStorage.setItem(`form_99_details`, JSON.stringify(this._form99Details));
        localStorage.setItem(`form_99_saved`, JSON.stringify(formSavedObj));
      }
    }
  }

  /**
   * Updates the type selected.
   *
   * @param      {<type>}  val     The value
   */
  public updateTypeSelected(e): void {
    if (this.editMode) {
      //if(e.target.checked) {
      this.typeSelected = e.target.value;
      this.typeFailed = false;
      /*} else {
        this.typeSelected = '';
        this.typeFailed = true;
      }*/
    } else {
      this._dialogService
        .newReport(
          'This report has been filed with the FEC. If you want to change, you must file a new report.',
          ConfirmModalComponent,
          'Warning',
          true, false, true
          )
        .then(res => {
          if (res === 'cancel' ||
          res === ModalDismissReasons.BACKDROP_CLICK ||
          res === ModalDismissReasons.ESC) {
            this._setForm();
            this._dialogService.checkIfModalOpen();
          } else if (res === 'NewReport') {
            //this._router.navigate(['/reports']);
            //this._router.navigate(['/forms/form/99'], { queryParams: { step: 1, edit: this.editMode } });
            this.editMode = true;
            localStorage.removeItem('form_99_details');
            localStorage.removeItem('form_99_saved');
            this._setF99Details();
            setTimeout(() => {
              this._router.navigate(['/forms/form/99'], { queryParams: { step: 'step_1', edit: this.editMode, refresh: true } });
            }, 500);
          }
        });
    }
    window.scrollTo(0, 0);

  }

  /**
   * Validates the type selected form.
   *
   */
  public doValidateType() {
    // get the selected F99 option, instead of defaulting
    let reasonType = this.typeSelected;
    if(!reasonType) {
      reasonType = this.frmType.get('reasonTypeRadio').value;
    }
    if (reasonType) {
        this.typeFailed = false;
        this.isValidType = true;
        this._form99Details = JSON.parse(localStorage.getItem('form_99_details'));

        this._form99Details.reason = reasonType;

        window.localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));

        this.status.emit({
          form: this.frmType,
          direction: 'next',
          step: 'step_2',
          previousStep: 'step_1',
          refresh: this._setRefresh,
          reportId: this.reportId,
          edit: this.editMode
        });

        return 1;
    } else {
      this.typeFailed = true;
      this.isValidType = false;

      this.status.emit({
        form: this.frmType,
        direction: 'next',
        step: 'step_1',
        previousStep: '',
        edit: this.editMode
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

  /*
    This function is called while selecting a list from report screen
  */
  public optionsListClick(type): void {
    //console.log("Selected report =", type);
    if(document.getElementById(type) != null) {
      document.getElementById(type).click();
      //console.log("Selected report clicked");
    }
  }

}
