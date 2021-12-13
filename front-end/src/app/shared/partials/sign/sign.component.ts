import { Component, EventEmitter, OnInit, Output, Input, ViewEncapsulation, SimpleChanges, ChangeDetectionStrategy, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup, FormControl, NgForm, Validators } from '@angular/forms';
import { Subscription } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { form99 } from '../../interfaces/FormsService/FormsService';
import { FormsService } from '../../services/FormsService/forms.service';
import { MessageService } from '../../services/MessageService/message.service';
import { DialogService } from '../../services/DialogService/dialog.service';
import { ConfirmModalComponent, ModalHeaderClassEnum } from '../confirm-modal/confirm-modal.component';
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';
// import { loadElementInternal } from '@angular/core/src/render3/util';

@Component({
  selector: 'app-sign',
  templateUrl: './sign.component.html',
  styleUrls: ['./sign.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class SignComponent implements OnInit, OnDestroy {
  
  @Input() comittee_details;
  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  public committee_details: any = {};
  public editMode: boolean;
  public formType: string = '';
  public typeSelected: string = '';
  public signFailed: boolean = false;
  public frmSaved: boolean = false;
  public frmSignee: FormGroup;
  public date_stamp: Date = new Date();
  public hideText: boolean = false;
  public showValidateBar: boolean = false;
  private _printPriviewPdfFileLink: string = '';

  private _subscription: Subscription;
  private _additional_email_1: string = '';
  private _additional_email_2: string = '';
  private _confirm_email_1: string = '';
  private _confirm_email_2: string = '';
  private _form99Details: any = {};
  private _formType: string = '';
  private _setRefresh: boolean = false;

  private _form_details: any = {};
  private _step: string = '';

  public needAdditionalEmail_2 = false;

  public additionalEmail1Invalid = false;
  public additionalEmail2Invalid = false;
  public showAdditionalEmail1Warn = false;
  public showAdditionalEmail2Warn = false;
  public confirm_email_1: string = '';
  public confirm_email_2: string = '';
  public fec_id = '';
  queryParamsSubscription: Subscription;
  messageSubscription: Subscription;

  constructor(
    private _activatedRoute: ActivatedRoute,
    private _fb: FormBuilder,
    private _formsService: FormsService,
    private _messageService: MessageService,
    private _dialogService: DialogService,
    private _router: Router,
    private _reportTypeService: ReportTypeService
  ) {
    this.queryParamsSubscription  = _activatedRoute.queryParams.subscribe(p => {
      if (p.refresh) {
        this._setRefresh = true;
        this.ngOnInit();
      }
    });
  }

  ngOnInit(): void {
    this.formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.editMode = this._activatedRoute.snapshot.queryParams.edit === 'false' ? false : true;
    this.committee_details = JSON.parse(localStorage.getItem('committee_details'));
    //this.fec_id = this._activatedRoute.snapshot.queryParams.fec_id;

    if (this.formType === '3X') {
      this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type_backup`));
      if (this._form_details === null || typeof this._form_details === 'undefined') {
        this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
      }
    } else if (this.formType === '99') {
      this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_details`));
    }

    //console.log('this._form_details = ', this._form_details);

    this._setForm();

    this.messageSubscription = this._messageService.getMessage().subscribe(res => {
      if (res.message) {
        //console.log('res.message', res.message);
        if (res.message === 'New form99') {
          this._setForm();
        }
      }
    });
  }

  ngOnChanges(changes: SimpleChanges): void {
    //console.log(changes);
  }


  ngOnDestroy(): void {
    this.queryParamsSubscription.unsubscribe();
    this.messageSubscription.unsubscribe();
  }


  ngDoCheck(): void {
    if (this.formType === '99') {
      const form_99_details: any = JSON.parse(localStorage.getItem(`form_${this.formType}_details`));
      if (form_99_details) {
        this.typeSelected = form_99_details.reason;
      }
    } else if (this.formType === '3X') {
      let form_3X_report_type: any = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type_backup`));
      if (form_3X_report_type === null || typeof form_3X_report_type === 'undefined') {
        form_3X_report_type = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
      }

      if (form_3X_report_type) {
        if (form_3X_report_type.hasOwnProperty('reportType')) {
          this.typeSelected = form_3X_report_type.reportType + '(' + form_3X_report_type.reportTypeDescription + ')';
        } else if (form_3X_report_type.hasOwnProperty('reporttype')) {
          this.typeSelected = form_3X_report_type.reporttype + '(' + form_3X_report_type.reporttypedescription + ')';
        }
      }
    }
  }

  /**
   * Determines ability for a person to leave a page with a form on it.
   *
   * @return     {boolean}  True if able to deactivate, False otherwise.
   */
  public async canDeactivate(): Promise<boolean> {
    if (this.hasUnsavedData()) {
      let result: boolean = null;
      //console.log('true');
      result = await this._dialogService.confirm('', ConfirmModalComponent).then(res => {
        let val: boolean = null;

        if (res === 'okay') {
          val = true;
        } else if (res === 'cancel') {
          val = false;
        }

        return val;
      });

      return result;
    } else {
      //console.log('no unsaved data false');
      return true;
    }
  }

  /**
   * Determines if form has unsaved data.
   * TODO: Move to service.
   *
   * @return     {boolean}  True if has unsaved data, False otherwise.
   */
  public hasUnsavedData(): boolean {
    if (this.formType === '99') {
      let formSaved: any = JSON.parse(localStorage.getItem(`form_${this.formType}_saved`));

      if (formSaved !== null) {
        let formStatus: boolean = formSaved.saved;

        if (!formStatus) {
          return true;
        }
      }

      return false;
    } else if (this.formType === '3X') {
      let formSaved: any = JSON.parse(localStorage.getItem(`form_${this.formType}_saved_backup`));

      if (formSaved !== null) {
        let formStatus: boolean = formSaved.saved;

        if (!formStatus) {
          return true;
        }
      }

      return false;
    }
  }

  private _setForm(): void {
    if (this._form_details) {
      if (this.formType === '99') {
        this.typeSelected = this._form_details.reason;
        if (this._form_details.additional_email_1.length >= 1) {
          if (this._form_details.additional_email_1 === '-') {
            this._form_details.additional_email_1 = '';
          }
        }

        if (this._form_details.additional_email_2.length >= 1) {
          if (this._form_details.additional_email_2 === '-') {
            this._form_details.additional_email_2 = '';
          }
        }
      } else if (this.formType === '3X') {
        if (this._form_details) {
          if (this._form_details.hasOwnProperty('reportType')) {
            this.typeSelected = `${this._form_details.reportType} (${this._form_details.reportTypeDescription})`;
          } else if (this._form_details.hasOwnProperty('reporttype')) {
            this.typeSelected = `${this._form_details.reporttype} (${this._form_details.reporttypedescription})`;
          }
        }

        if (this._form_details.hasOwnProperty('additionalEmail1')) {
          if (this._form_details.additionalEmail1.length >= 1) {
            if (this._form_details.additionalEmail1 === '-') {
              this._form_details.additionalEmail1 = '';
            }
          }
        } else if (this._form_details.hasOwnProperty('additionalemail1')) {
          if (this._form_details.additionalemail1 !== null) {
            if (this._form_details.additionalemail1.length >= 1) {
              if (this._form_details.additionalemail1 === '-') {
                this._form_details.additionalemail1 = '';
              }
            }
          } else {
            this._form_details.additionalemail1 = '';
          }
        }

        if (this._form_details.hasOwnProperty('additionalEmail2')) {
          if (this._form_details.additionalEmail2.length >= 1) {
            if (this._form_details.additionalEmail2 === '-') {
              this._form_details.additionalEmail2 = '';
            }
          }
        } else if (this._form_details.hasOwnProperty('additionalemail2')) {
          if (this._form_details.additionalemail2 !== null) {
            if (this._form_details.additionalemail2.length >= 1) {
              if (this._form_details.additionalemail2 === '-') {
                this._form_details.additionalemail2 = '';
              }
            }
          } else {
            this._form_details.additionalemail2 = '';
          }
        }
      }
      if (this.formType === '99') {
        this.frmSignee = this._fb.group({
          signee: [
            `${this.committee_details.treasurerfirstname} ${this.committee_details.treasurerlastname}`,
            Validators.required
          ],
          additional_email_1: [this._form_details.additional_email_1, Validators.email],
          additional_email_2: [this._form_details.additional_email_2, Validators.email],
          confirm_email_1: [this._form_details.confirm_email_1, Validators.email],
          confirm_email_2: [this._form_details.confirm_email_2, Validators.email],
          agreement: [false, Validators.requiredTrue]
        });
      } else if (this.formType === '3X') {
        if (this._form_details.hasOwnProperty('additionalEmail1')) {
          this.frmSignee = this._fb.group({
            signee: [
              `${this.committee_details.treasurerfirstname} ${this.committee_details.treasurerlastname}`,
              Validators.required
            ],
            additional_email_1: [this._form_details.additionalEmail1, Validators.email],
            additional_email_2: [this._form_details.additionalEmail2, Validators.email],
            confirm_email_1: [this._form_details.additionalEmail1, Validators.email],
            confirm_email_2: [this._form_details.additionalEmail2, Validators.email],
            agreement: [false, Validators.requiredTrue]
          });
        } else if (this._form_details.hasOwnProperty('additionalemail1')) {
          this.frmSignee = this._fb.group({
            signee: [
              `${this.committee_details.treasurerfirstname} ${this.committee_details.treasurerlastname}`,
              Validators.required
            ],
            additional_email_1: [this._form_details.additionalemail1, Validators.email],
            additional_email_2: [this._form_details.additionalemail2, Validators.email],
            confirm_email_1: [this._form_details.additionalemail1, Validators.email],
            confirm_email_2: [this._form_details.additionalemail2, Validators.email],
            agreement: [false, Validators.requiredTrue]
          });
        }
      }
    } else {
      this.frmSignee = this._fb.group({
        signee: [
          `${this.committee_details.treasurerfirstname} ${this.committee_details.treasurerlastname}`,
          Validators.required
        ],
        additional_email_1: ['', Validators.email],
        additional_email_2: ['', Validators.email],
        confirm_email_1: ['', Validators.email],
        confirm_email_2: ['', Validators.email],
        agreement: [false, Validators.requiredTrue]
      });
    }

    this._messageService.clearMessage();
  }

  private _setF99Details(): void {
    if (this.committee_details) {
      if (this.committee_details.committeeid) {
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
          saved: false
        };
        localStorage.setItem(`form_99_details`, JSON.stringify(this._form99Details));
        localStorage.setItem(`form_99_saved`, JSON.stringify(formSavedObj));
      }
    }
  }

  /**
   * Validates the form.
   *
   */
  public validateForm(): void {
    this.showValidateBar = true;
    this._formsService.validateForm({}, this.formType).subscribe(
      res => {
        if (res) {
          this._messageService.sendMessage({
            validateMessage: {
              validate: environment.validateSuccess,
              showValidateBar: true
            }
          });
        }
      },
      error => {
        this._messageService.sendMessage({
          validateMessage: {
            validate: error.error,
            showValidateBar: true
          }
        });
      }
    );
  }

  /**
   * Saves a form.
   *
   */
  public saveForm(): void {
    if (this.editMode) {
      let formStatus: boolean = true;

      if (this.formType === '3X') {
        this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type_backup`));

        if (this._form_details === null || typeof this._form_details === 'undefined') {
          this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
        }

        const formSaved: boolean = JSON.parse(localStorage.getItem(`form_${this.formType}_saved_backup`));
      }
      if (this.formType === '99') {
        this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_details`));
        const formSaved: boolean = JSON.parse(localStorage.getItem(`form_${this.formType}_saved`));
      }

      this.additionalEmail1Invalid = false;
      this.additionalEmail2Invalid = false;

      if (
        this.frmSignee.controls.signee.valid &&
        this.frmSignee.controls.additional_email_1.valid &&
        this.frmSignee.controls.additional_email_2.valid
      ) {
        this.validateAdditionalEmails();

        if (!this.additionalEmail1Invalid && !this.additionalEmail2Invalid) {
          this.frmSaved = true;
          if (this.formType === '99') {
            this._form_details.additional_email_1 = this.frmSignee.get('additional_email_1').value;
            this._form_details.additional_email_2 = this.frmSignee.get('additional_email_2').value;
            this._form_details.confirm_email_1 = this.frmSignee.get('confirm_email_1').value;
            this._form_details.confirm_email_2 = this.frmSignee.get('confirm_email_2').value;
          } else if (this.formType === '3X') {
            if (this._form_details.hasOwnProperty('additionalEmail1')) {
              this._form_details.additionalEmail1 = this.frmSignee.get('additional_email_1').value;
            } else if (this._form_details.hasOwnProperty('additionalemail1')) {
              this._form_details.additionalemail1 = this.frmSignee.get('additional_email_1').value;
            }
            if (this._form_details.hasOwnProperty('additionalEmail2')) {
              this._form_details.additionalEmail2 = this.frmSignee.get('additional_email_2').value;
            } else if (this._form_details.hasOwnProperty('additionalemail2')) {
              this._form_details.additionalemail2 = this.frmSignee.get('additional_email_2').value;
            }
          }

          if (this.formType === '99') {
            localStorage.setItem(`form_${this.formType}_details`, JSON.stringify(this._form_details));
          } else if (this.formType === '3X') {
            localStorage.setItem(`form_${this.formType}_report_type_backup`, JSON.stringify(this._form_details));
          }

          if (this.formType === '3X') {
            this._reportTypeService.signandSaveSubmitReport(this.formType, 'Saved').subscribe(
              res => {
                if (res) {
                  this.frmSaved = true;

                  let formSavedObj: any = {
                    saved: this.frmSaved
                  };

                  localStorage.setItem(`form_${this.formType}_saved_backup`, JSON.stringify(formSavedObj));
                }
              },
              error => {
                //console.log('error: ', error);
              }
            );
          }
          if (this.formType === '99') {
            this._formsService.Signee_SaveForm({}, this.formType).subscribe(
              res => {
                if (res) {
                  this.frmSaved = true;

                  let formSavedObj: any = {
                    saved: this.frmSaved
                  };

                  localStorage.setItem(`form_${this.formType}_saved`, JSON.stringify(formSavedObj));
                }
              },
              error => {
                //console.log('error: ', error);
              }
            );
          }
        }
      }
      //console.log(' saveForm this.frmSaved =', this.frmSaved);
    } else {
      if (this.formType === '99') {
        this._dialogService
          .newReport(
            'This report has been filed with the FEC. If you want to change, you must file a new report.',
            ConfirmModalComponent,
            'Warning',
            true,
            false,
            true
          )
          .then(res => {
            if (res === 'okay') {
              this.ngOnInit();
            } else if (res === 'NewReport') {
              localStorage.removeItem('form_99_details');
              localStorage.removeItem('form_99_saved');
              this._setF99Details();
              this._router.navigate(['/forms/form/99'], { queryParams: { step: 'step_1', refresh: true } });
            }
          });
      } else if (this.formType === '3X') {
        this._dialogService
          .confirm(
            'This report has been filed with the FEC. If you want to change, you must Amend the report.',
            ConfirmModalComponent,
            'Warning',
            true,
            ModalHeaderClassEnum.warningHeader,
            null,
            'Return to Reports'
          )
          .then(res => {
            if (res === 'okay') {
              this.ngOnInit();
            } else if (res === 'cancel') {
              this._router.navigate(['/reports']);
            }
          });
      }
    }
  }

  /**
   * Submits a form.
   *
   */
  public doSubmitForm(): void {
    if (this.editMode) {
      let doSubmitFormSaved: boolean = false;
      if (this.formType === '3X') {
        let formSaved: any = JSON.parse(localStorage.getItem(`form_${this.formType}_saved_backup`));
        this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type_backup`));

        if (this._form_details === null || typeof this._form_details === 'undefined') {
          this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
        }

        doSubmitFormSaved = formSaved;
      } else if (this.formType === '99') {
        let formSaved: any = JSON.parse(localStorage.getItem(`form_${this.formType}_saved`));
        this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_details`));
        doSubmitFormSaved = formSaved.form_saved;
      }

      if (this.formType === '99') {
        this._form_details.file = '';

        if (this._form_details.additional_email_1 === '') {
          this._form_details.additional_email_1 = '-';
        }

        if (this._form_details.additional_email_2 === '') {
          this._form_details.additional_email_2 = '-';
        }
      }

      this.validateAdditionalEmails();

      if (!this.additionalEmail1Invalid && !this.additionalEmail2Invalid) {
        if (this.formType === '99') {
          localStorage.setItem(`form_${this.formType}_details`, JSON.stringify(this._form_details));
        } else if (this.formType === '3X') {
          localStorage.setItem(`form_${this.formType}_report_type_backup`, JSON.stringify(this._form_details));
        }

        if (this.frmSignee.invalid) {
          if (this.frmSignee.get('agreement').value) {
            this.signFailed = false;
          } else {
            this.signFailed = true;
          }
        } else if (this.frmSignee.valid) {
          this.signFailed = false;

          if (!doSubmitFormSaved) {
            if (this.formType === '99') {
              this._formsService.Signee_SaveForm({}, this.formType).subscribe(
                saveResponse => {
                  if (saveResponse) {
                    this._formsService.submitForm({}, this.formType).subscribe(res => {
                      if (res) {
                        //console.log(' response = ', res);
                        this.status.emit({
                          form: this.frmSignee,
                          direction: 'next',
                          step: 'step_5',
                          fec_id: res.fec_id,
                          previousStep: this._step
                        });

                        this._messageService.sendMessage({
                          form_submitted: true
                        });

                        this._messageService.sendMessage({
                          validateMessage: {
                            validate: 'All required fields have passed validation.',
                            showValidateBar: true
                          }
                        });
                      }
                    });
                  }
                },
                error => {
                  //console.log('error: ', error);
                }
              );
            } else if (this.formType === '3X') {
              this._reportTypeService.signandSaveSubmitReport(this.formType, 'Submitted').subscribe(res => {
                if (res) {
                  const frmSaved: any = {
                    saved: true
                  };

                  localStorage.setItem('form_3X_saved', JSON.stringify(frmSaved));

                  this._router.navigate(['/forms/form/3X'], { queryParams: { step: 'step_6', edit: this.editMode, 
                                        fec_id: res.fec_id } });

                  this._messageService.sendMessage({
                    form_submitted: true
                  });
                } else {
                  this._router.navigate(['/forms/form/3X'], { queryParams: { step: 'step_6', edit: this.editMode } });
                  this._messageService.sendMessage({
                    form_submitted: false
                  });
                }
              });
            }
            // upto here
          } else {
            this._messageService.sendMessage({
              validateMessage: {
                validate: '',
                showValidateBar: false
              }
            });
            if (this.formType === '99') {
              this._formsService.submitForm({}, this.formType).subscribe(res => {
                if (res) {
                  //console.log(' response = ', res);
                  this.status.emit({
                    form: this.frmSignee,
                    direction: 'next',
                    step: 'step_5',
                    fec_id: res.fec_id,
                    previousStep: this._step
                  });


                  this._messageService.sendMessage({
                    form_submitted: true
                  });
                }
              });
            } else if (this.formType === '3X') {
              this._reportTypeService.signandSaveSubmitReport(this.formType, 'Submitted').subscribe(res => {
                if (res) {
                  //console.log(' response = ', res);
                  this.fec_id = res.fec_id;
                  /*this.frmSaved = true;
          
                        let formSavedObj: any = {
                          'saved': this.frmSaved
                        };*/

                  /*this.status.emit({
                          form: this.frmSignee,
                          direction: 'next',
                          step: 'step_5',
                          previousStep: this._step
                        });*/
                  this._router.navigate(['/forms/form/3X'], { queryParams: { step: 'step_6', edit: this.editMode,
                  fec_id: res.fec_id } });
                  //this._router.navigate(['/submitform/3X']);

                  this._messageService.sendMessage({
                    form_submitted: true
                  });
                }
              });
            }
          }
        }
      }
    } else {
      if (this.formType === '3X') {
        this._dialogService
          .confirm(
            'This report has been filed with the FEC. If you want to change, you must Amend the report',
            ConfirmModalComponent,
            'Warning',
            true,
            ModalHeaderClassEnum.warningHeader,
            null,
            'Return to Reports'
          )
          .then(res => {
            if (res === 'okay') {
              this.ngOnInit();
            } else if (res === 'cancel') {
              this._router.navigate(['/reports']);
            }
          });
      } else if (this.formType === '99') {
        this._dialogService
          .newReport(
            'This report has been filed with the FEC. If you want to change, you must file a new report.',
            ConfirmModalComponent,
            'Warning',
            true,
            false,
            true
          )
          .then(res => {
            if (res === 'okay') {
              this.ngOnInit();
            } else if (res === 'NewReport') {
              localStorage.removeItem('form_99_details');
              localStorage.removeItem('form_99_saved');
              this._setF99Details();
              this._router.navigate(['/forms/form/99'], { queryParams: { step: 'step_1', refresh: true } });
            }
          });
      }
    }
  }

  public changeAdditionalEmail(e): void {
    this.frmSaved = false;
    this.clearWarnMsg();
  }

  public updateAdditionalEmail(e): void {
    this.frmSaved = false;
    this.clearWarnMsg();
    if (this.editMode) {
      if (e.target.value.length) {
        if (e.target.name === 'additional_email_1') {
          if (this.formType === '99') {
            this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_details`));
            this._form_details.additional_email_1 = e.target.value;
          } else if (this.formType === '3X') {
            this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type_backup`));

            if (this._form_details === null || typeof this._form_details === 'undefined') {
              this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
            }

            if (this._form_details.hasOwnProperty('additionalEmail1')) {
              this._form_details.additionalEmail1 = e.target.value;
            } else if (this._form_details.hasOwnProperty('additionalemail1')) {
              this._form_details.additionalemail1 = e.target.value;
            }
          }

          if (this.formType === '99') {
            localStorage.setItem(`form_${this.formType}_details`, JSON.stringify(this._form_details));
          } else if (this.formType === '3X') {
            localStorage.setItem(`form_${this.formType}_report_type_backup`, JSON.stringify(this._form_details));
          }

          if (this.formType === '99') {
            localStorage.setItem(
              `form_${this.formType}_saved`,
              JSON.stringify({
                saved: false
              })
            );
          } else if (this.formType === '3X') {
            localStorage.setItem(
              `form_${this.formType}_saved_backup`,
              JSON.stringify({
                saved: false
              })
            );
          }
        } else if (e.target.name === 'additional_email_2') {
          if (this.formType === '99') {
            this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_details`));
            this._form_details.additional_email_2 = e.target.value;
          } else if (this.formType === '3X') {
            this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type_backup`));
            if (this._form_details === null || typeof this._form_details === 'undefined') {
              this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
            }

            if (this._form_details.hasOwnProperty('additionalEmail2')) {
              this._form_details.additionalEmail2 = e.target.value;
            } else if (this._form_details.hasOwnProperty('additionalemail2')) {
              this._form_details.additionalemail2 = e.target.value;
            }
          }

          if (this.formType === '99') {
            localStorage.setItem(`form_${this.formType}_details`, JSON.stringify(this._form_details));
          } else if (this.formType === '3X') {
            localStorage.setItem(`form_${this.formType}_report_type_backup`, JSON.stringify(this._form_details));
          }

          if (this.formType === '99') {
            localStorage.setItem(
              `form_${this.formType}_saved`,
              JSON.stringify({
                saved: false
              })
            );
          } else if (this.formType === '3X') {
            localStorage.setItem(
              `form_${this.formType}_saved_backup`,
              JSON.stringify({
                saved: false
              })
            );
          }
        }
      } else {
        if (this.formType === '99') {
          localStorage.setItem(
            `form_${this.formType}_saved`,
            JSON.stringify({
              saved: true
            })
          );
        } else if (this.formType === '3X') {
          localStorage.setItem(
            `form_${this.formType}_saved_backup`,
            JSON.stringify({
              saved: true
            })
          );
        }
      }
    } else {
      this._dialogService
        .confirm(
          'This report has been filed with the FEC. If you want to change, you must Amend the report',
          ConfirmModalComponent,
          'Warning',
          true,
          ModalHeaderClassEnum.warningHeader,
          null,
          'Return to Reports'
        )
        .then(res => {
          if (res === 'okay') {
            this.ngOnInit();
          } else if (res === 'cancel') {
            this._router.navigate(['/reports']);
          }
        });
    }
  }

  public updateValidation(e): void {
    if (this.editMode) {
      this.frmSaved = false;
      this.clearWarnMsg();

      if (e.target.checked) {
        this.signFailed = false;
      } else if (!e.target.checked) {
        this.signFailed = true;
      }
    } else {
      if (this.formType === '99') {
        this._dialogService
          .newReport(
            'This report has been filed with the FEC. If you want to change, you must file a new report.',
            ConfirmModalComponent,
            'Warning',
            true,
            false,
            true
          )
          .then(res => {
            if (res === 'okay') {
              this.ngOnInit();
            } else if (res === 'NewReport') {
              localStorage.removeItem('form_99_details');
              localStorage.removeItem('form_99_saved');
              this._setF99Details();
              this._router.navigate(['/forms/form/99'], { queryParams: { step: 'step_1', refresh: true } });
            }
          });
      } else if (this.formType === '3X') {
        this._dialogService
          .confirm(
            'This report has been filed with the FEC. If you want to change, you must Amend the report.',
            ConfirmModalComponent,
            'Warning',
            true,
            ModalHeaderClassEnum.warningHeader,
            null,
            'Return to Reports'
          )
          .then(res => {
            if (res === 'okay') {
              this.ngOnInit();
            } else if (res === 'cancel') {
              this._router.navigate(['/reports']);
            }
          });
      }
    }
    //console.log('this.signFailed: ', this.signFailed);
  }

  public toggleToolTip(tooltip): void {
    if (tooltip.isOpen()) {
      tooltip.close();
    } else {
      tooltip.open();
    }
  }

  /**
   * Goes to the previous step.
   *
   */
  public goToPreviousStep(): void {
    if (this.formType === '99') {
      //console.log('im in previous');
      this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_details`));
      this._form_details['additional_email_1'] = '';
      this._form_details['additional_email_2'] = '';
      localStorage.setItem(`form_99_details`, JSON.stringify(this._form_details));
      this.frmSaved = false;
      //console.log('Email 1' +  this._form_details.additional_email_1);
      this.status.emit({
        form: {},
        direction: 'previous',
        step: 'step_3',
        previousStep: this._step,
        edit: this.editMode
      });

      this._messageService.sendMessage({
        validateMessage: {
          validate: '',
          showValidateBar: false
        }
      });
    } else if (this.formType === '3X') {
      this._router.navigate([`/forms/form/${this.formType}`], { queryParams: { step: 'step_2', edit: this.editMode } });
    }
  }
  public cancelStepWithWarning(): void {
    this._dialogService.confirm(
        '', ConfirmModalComponent, '', true)
        .then(res => {
          if (res === 'okay' ? true : false ) {
            //console.log('im here value of res:' + res);
            this.goToPreviousStep();
          }
        });


  }
  public getDirtyEmail(): boolean {
    if (this._form_details) {
      if (this.formType === '99') {
        if (this._form_details.additional_email_1.length <= 0) {
          //console.log(this._form_details.additional_email_1.length);
          return false;
        }
        //console.log(this._form_details.additional_email_1.length);
        return  true;
      }

    }
    return false;
  }
  public printPreview(): void {
    if (this.formType === '99') {
      this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_details`));
      const fileFromLocalStorage = localStorage.getItem('form_99_details.org_fileurl');
      if (
        this._form_details &&
        ((this._form_details.file && Object.entries(this._form_details.file).length === 0) || !this._form_details.file)
      ) {
        this._form_details.file = fileFromLocalStorage;
      }
    } else if (this.formType === '3X') {
      this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type_backup`));
      if (this._form_details === null || typeof this._form_details === 'undefined') {
        this._form_details = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
      }
    }

    if (
      this.frmSignee.controls.signee.valid &&
      this.frmSignee.controls.additional_email_1.valid &&
      this.frmSignee.controls.additional_email_2.valid
    ) {
      this.validateAdditionalEmails();

      if (!this.additionalEmail1Invalid && !this.additionalEmail2Invalid) {
        if (this.formType === '99') {
          this._form_details.additional_email_1 = this.frmSignee.get('additional_email_1').value;
          this._form_details.additional_email_2 = this.frmSignee.get('additional_email_2').value;
        } else if (this.formType === '3X') {
          if (this._form_details.hasOwnProperty('additionalEmail1')) {
            this._form_details.additionalEmail1 = this.frmSignee.get('additional_email_1').value;
          } else if (this._form_details.hasOwnProperty('additionalemail1')) {
            this._form_details.additionalemail1 = this.frmSignee.get('additional_email_1').value;
          }

          if (this._form_details.hasOwnProperty('additionalEmail2')) {
            this._form_details.additionalEmail2 = this.frmSignee.get('additional_email_2').value;
          } else if (this._form_details.hasOwnProperty('additionalemail2')) {
            this._form_details.additionalemail2 = this.frmSignee.get('additional_email_2').value;
          }
        }

        localStorage.setItem(`form_${this.formType}_details`, JSON.stringify(this._form_details));
        if (this.formType === '99') {
          this._formsService.PreviewForm_Preview_sign_Screen({}, this.formType).subscribe(
            res => {
              if (res) {
                window.open(localStorage.getItem('form_99_details.printpriview_fileurl'), '_blank');
              }
            },
            error => {
              //console.log('error: ', error);
            }
          );
        } else if (this.formType === '3X') {
          this._reportTypeService.printPreview('sign_and_submit', this.formType);
        }
      }
    } else {
      if (this.formType === '99') {
        this._formsService.PreviewForm_Preview_sign_Screen({}, this.formType).subscribe(
          res => {
            if (res) {
              window.open(localStorage.getItem('form_99_details.printpriview_fileurl'), '_blank');
            }
          },
          error => {
            //console.log('error: ', error);
          }
        );
      } else if (this.formType === '3X') {
        this._reportTypeService.printPreview('sign_and_submit', this.formType);
      }
    }
  }

  public clearWarnMsg(): void {
    //this.frmSaved=false;
    this.showAdditionalEmail1Warn = false;
    this.showAdditionalEmail2Warn = false;
    this.additionalEmail1Invalid = false;
    this.additionalEmail2Invalid = false;
  }

  public validateAdditionalEmails(): void {
    this.clearWarnMsg();

    if (this.frmSignee.get('additional_email_1').value !== '') {
      if (this.frmSignee.get('confirm_email_1').value === '') {
        this.additionalEmail1Invalid = true;
        this.showAdditionalEmail1Warn = true;
      } else {
        if (this.frmSignee.get('additional_email_1').value !== this.frmSignee.get('confirm_email_1').value) {
          this.additionalEmail1Invalid = true;
          this.showAdditionalEmail1Warn = true;
        } else {
          this.confirm_email_1 = this.frmSignee.get('confirm_email_1').value;
          this.additionalEmail1Invalid = false;
          this.showAdditionalEmail1Warn = true;
        }
      }
    }

    if (this.frmSignee.get('additional_email_2').value !== '') {
      if (this.frmSignee.get('confirm_email_2').value === '') {
        this.additionalEmail2Invalid = true;
        this.showAdditionalEmail2Warn = true;
      } else {
        if (this.frmSignee.get('additional_email_2').value !== this.frmSignee.get('confirm_email_2').value) {
          this.additionalEmail2Invalid = true;
          this.showAdditionalEmail2Warn = true;
        } else {
          this.confirm_email_2 = this.frmSignee.get('confirm_email_2').value;
          this.additionalEmail2Invalid = false;
          this.showAdditionalEmail2Warn = true;
        }
      }
    }
  }
}
