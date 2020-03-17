import { Component, OnInit, ViewEncapsulation, Input, ChangeDetectionStrategy, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { MessageService } from '../../services/MessageService/message.service';
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';
import { interval, Subscription } from 'rxjs';
import { FormsService } from '../../services/FormsService/forms.service';
import { DialogService } from '../../services/DialogService/dialog.service';
import { ConfirmModalComponent, ModalHeaderClassEnum } from '../confirm-modal/confirm-modal.component';
import { FormsComponent } from 'src/app/forms/forms.component';

@Component({
  selector: 'app-submit',
  templateUrl: './submit.component.html',
  styleUrls: ['./submit.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class SubmitComponent implements OnInit, OnDestroy {
  
  public form_type: string = '';
  @Input() public FEC_Id: string = '#####';

  private _reportId: number;
  private _subscription: Subscription;
  public checkStatus: boolean = true;
  messageSubscription: Subscription;
  routerSubscription: Subscription;
  constructor(
    private _activatedRoute: ActivatedRoute,
    private _router: Router,
    private _messageService: MessageService,
    private _reportTypeService: ReportTypeService,
    private _dialogService: DialogService,
    private _formsService: FormsService,
    private _formsComponent: FormsComponent
  ) {}

  ngOnInit() {
    this.form_type = this._activatedRoute.snapshot.paramMap.get('form_id');
     if (this._router.url.indexOf('step_6') > -1) {
      this.FEC_Id = this._activatedRoute.snapshot.queryParams.fec_id;
      // this._checkReportStatus();
    }
    //console.log('form submitted ...', this.form_type);

    this.messageSubscription = this._messageService.getMessage().subscribe(res => {
      this._reportId = res.id;
      //console.log('SubmitComponent res =', res);
      if (res.form_submitted) {
        if (this.form_type === '99') {
          localStorage.removeItem(`form_${this.form_type}_details`);
        } else if (this.form_type === '3X') {
          // Below code has been temporarily commented to not generate json files while submitting report - 02/06
          /*//console.log('Accessing SubmitComponent F3x submit Data Receiver API ');
          this._reportTypeService.submitForm('3X', 'Submit').subscribe(
            res => {
              if (res) {
                //console.log('Accessing SubmitComponent F3x submit res ...', res);
                if (res['status'] === 'Accepted') {
                  localStorage.removeItem(`form_${this.form_type}_report_type_backup`);
                  localStorage.removeItem(`form_${this.form_type}_report_type`);
                  localStorage.removeItem('F3X_submit_backup');
                  localStorage.removeItem(`form_${this.form_type}_saved`);

                  this.FEC_Id = res['submissionId'];
                }
              }
            },
            error => {
              //console.log('error: ', error);
            }
          );*/ /*  */
        }
      }
    });

    this.routerSubscription = this._router.events.subscribe(val => {
      if (val) {
        if (val instanceof NavigationEnd) {
          //console.log('val.url = ', val.url);
          if (val.url.indexOf('/forms/form/99') === -1 || val.url.indexOf('/forms/form/3X') === -1) {
            this._messageService.sendMessage({
              validateMessage: {
                validate: {},
                showValidateBar: false
              }
            });
          }
        }
      }
    });

    const source = interval(10000);
    this._subscription = source.subscribe(val => this._checkReportStatus());
  }

  public goToDashboard(): void {
    //if (!this.checkStatus) {
      this._router.navigateByUrl('dashboard');
    //} else {
    //  this._formsComponent.canDeactivate();
    //}
  }

  ngOnDestroy(): void {
    this.messageSubscription.unsubscribe();
    this.routerSubscription.unsubscribe();
    this._subscription.unsubscribe();
  }

  private _checkReportStatus() {
    // we need to revisit to see if we really need this code
    /*if (this._router.url.indexOf('step_5') > -1) {
      this._formsService.get_report_status(this.form_type, this._reportId).subscribe(
        res => {
          // if (res && res.fec_status === 'Accepted') {
          if (res && res.fec_status === 'Submitted') {
            this.FEC_Id = res.fec_id;
            this.checkStatus = false;
          } else {
            this.checkStatus = true;
          }
        },
        error => {
          //console.log('error: ', error);
        }
      );
    }*/
  }
}
