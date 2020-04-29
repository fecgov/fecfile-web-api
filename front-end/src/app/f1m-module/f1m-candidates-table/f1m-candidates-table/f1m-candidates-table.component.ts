import { Router } from '@angular/router';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { Component, OnInit, Input, ChangeDetectorRef } from '@angular/core';
import { ScheduleActions } from '../../../forms/form-3x/individual-receipt/schedule-actions.enum';
import { ConfirmModalComponent } from '../../../shared/partials/confirm-modal/confirm-modal.component';
import { ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-f1m-candidates-table',
  templateUrl: './f1m-candidates-table.component.html',
  styleUrls: ['./f1m-candidates-table.component.scss']
})
export class F1mCandidatesTableComponent implements OnInit {

  @Input() candidatesData :any;
  @Input() step: string;
  @Input() scheduleAction: ScheduleActions;
  
  constructor(public _messageService: MessageService,
    private _dialogService:DialogService, 
    private _router: Router,
    private _cd:ChangeDetectorRef) { }

  ngOnInit() {
  }

  public editCandidate(candidate:any){
    this._messageService.sendMessage({
      formType : 'f1m-qualification', 
      action : 'editCandidate',
      candidate
    })
  }

  public trashCandidate(candidate:any){
    this._messageService.sendMessage({
      formType : 'f1m-qualification', 
      action : 'trashCandidate',
      candidate
    })
  }

  public checkIfEditMode() {
    if (this.scheduleAction === ScheduleActions.view) {
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
          if (res === 'cancel' || res === ModalDismissReasons.BACKDROP_CLICK || res === ModalDismissReasons.ESC) {
            // this.ngOnInit();
            this._dialogService.checkIfModalOpen();
          } else if (res === 'NewReport') {
            const formType = '1M';
            this._router.navigate([`/forms/form/${formType}`], {
              queryParams: { step: 'step_1'}
            });
            this._cd.detectChanges();
          }
        });
    }
  }

}
