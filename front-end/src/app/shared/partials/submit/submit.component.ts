import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { MessageService } from '../../services/MessageService/message.service';
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';
import { interval, Subscription } from 'rxjs';
import { FormsService } from '../../services/FormsService/forms.service';
import { DialogService } from '../../services/DialogService/dialog.service';
import { ConfirmModalComponent, ModalHeaderClassEnum } from '../confirm-modal/confirm-modal.component';

@Component({
  selector: 'app-submit',
  templateUrl: './submit.component.html',
  styleUrls: ['./submit.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class SubmitComponent implements OnInit {
  public form_type: string = '';
  public FEC_Id: string = '#####';

  private _reportId: number;
  private _subscription: Subscription;
  private _checkStatus: boolean = true;
  constructor(
    private _activatedRoute: ActivatedRoute,
    private _router: Router,
    private _messageService: MessageService,
    private _reportTypeService: ReportTypeService,
    private _dialogService: DialogService,
    private _formsService: FormsService
  ) {}

  ngOnInit() {
    this.form_type = this._activatedRoute.snapshot.paramMap.get('form_id');
    console.log('form submitted ...', this.form_type);

    this._messageService.getMessage().subscribe(res => {
      this._reportId = res.id;
      console.log('SubmitComponent res =', res);
      if (res.form_submitted) {
        if (this.form_type === '99') {
          localStorage.removeItem(`form_${this.form_type}_details`);
        } else if (this.form_type === '3X') {
          console.log('Accessing SubmitComponent F3x submit Data Receiver API ');
          this._reportTypeService.submitForm('3X', 'Submit').subscribe(
            res => {
              if (res) {
                console.log('Accessing SubmitComponent F3x submit res ...', res);
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
              console.log('error: ', error);
            }
          ); /*  */
        }
      }
    });

    this._router.events.subscribe(val => {
      if (val) {
        if (val instanceof NavigationEnd) {
          console.log('val.url = ', val.url);
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
    this._router.navigateByUrl('dashboard');
  }

  private _checkReportStatus() {
    if (this._router.url.indexOf('step_5') > -1) {
      this._formsService.get_report_status(this.form_type, this._reportId).subscribe(
        res => {
          if (res && res.fec_status === 'Accepted') {
            this.FEC_Id = res.fec_id;
            this._checkStatus = false;
          } else {
            this._checkStatus = true;
          }
        },
        error => {
          console.log('error: ', error);
        }
      );
    }
  }

  public async canDeactivate(): Promise<boolean> {
    if (this._checkStatus) {
      if (this._formsService.checkCanDeactivate()) {
        this._dialogService
          .confirm(
            'FEC ID has not been generated yet. Please check the FEC ID under reports if you want to leave the page.',
            ConfirmModalComponent,
            'Warning',
            true,
            ModalHeaderClassEnum.warningHeader,
            null,
            'Leave page'
          )
          .then(res => {
            if (res === 'okay') {
            } else if (res === 'cancel') {
              this.navigateToDashboard();
            }
          });
      }
    } else {
      return true;
    }
  }

  public navigateToDashboard(): void {
    this._router.navigateByUrl('/dashboard');
  }
}
