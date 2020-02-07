import { Component, HostListener, OnInit, NgZone, ViewChild, ViewEncapsulation, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { BehaviorSubject, Observable, of, Subject } from 'rxjs';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../environments/environment';
import { FormsService } from '../shared/services/FormsService/forms.service';
import { MessageService } from '../shared/services/MessageService/message.service';
import { DialogService } from '../shared/services/DialogService/dialog.service';
import { ValidateComponent } from '../shared/partials/validate/validate.component';
import { ConfirmModalComponent, ModalHeaderClassEnum } from '../shared/partials/confirm-modal/confirm-modal.component';

@Component({
  selector: 'app-forms',
  templateUrl: './forms.component.html',
  styleUrls: ['./forms.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class FormsComponent implements OnInit, OnDestroy {
  public formType: string = '';
  public closeResult: string = '';
  public canContinue: boolean = false;
  public showValidateBar: boolean = false;
  public confirmModal: BehaviorSubject<boolean> = new BehaviorSubject(false);

  private onDestroy$ = new Subject();

  private _openModal: any = null;
  private _step: string;
  private _editMode: boolean;

  constructor(
    private _activeRoute: ActivatedRoute,
    private _modalService: NgbModal,
    private _ngZone: NgZone,
    private _router: Router,
    private _messageService: MessageService,
    private _dialogService: DialogService,
    private _formsService: FormsService
  ) {

    _activeRoute.queryParams.takeUntil(this.onDestroy$).subscribe(p => {
      if (p.step) {
        this._step = p.step;
      }
      this._editMode = p.edit && p.edit === 'false' ? false : true;
    });
  }

  ngOnInit(): void {
    this._activeRoute.params.subscribe(params => {
      this.formType = params.form_id;
    });
  }

  ngOnDestroy(): void {
    this.onDestroy$.next(true);
  }


  /**
   * Determines ability for a person to leave a page with a form on it.
   *
   * @return     {boolean}  True if able to deactivate, False otherwise.
   */
  public async canDeactivate(): Promise<boolean> {
    if (this._formsService.formHasUnsavedData(this.formType) && this._editMode) {
      let result: boolean = null;
      console.log(' form not saved...');
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
    } else if (this._formsService.checkCanDeactivate()) {
      let result: boolean = null;
      console.log(' form not saved...');
      result = await this._dialogService
      .confirm(
        'FEC ID has not been generated yet. Please check the FEC ID under reports if you want to leave the page.',
        ConfirmModalComponent,
        'Warning',
        true,
        ModalHeaderClassEnum.warningHeader,
        null,
        'Leave page'
      ).then(res => {
        let val: boolean = null;

        if (res === 'okay') {
          val = false;
        } else if (res === 'cancel') {
          val = true;
        }

        return val;
      });

      return result;
    } else {
      console.log('Not any unsaved data...');
      return true;
    }
  }
}
