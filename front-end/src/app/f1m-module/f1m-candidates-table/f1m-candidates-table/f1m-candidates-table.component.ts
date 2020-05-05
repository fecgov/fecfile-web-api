import { F1mService } from './../../f1m/f1m-services/f1m.service';
import { Router } from '@angular/router';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { Component, OnInit, Input, ChangeDetectorRef, Output, EventEmitter } from '@angular/core';
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
  @Input() reportId: string;

  
  constructor(public _messageService: MessageService,
    private _dialogService:DialogService, 
    private _router: Router,
    private _cd:ChangeDetectorRef, 
    private _f1mService: F1mService) { }

  ngOnInit() {
  }

  public editCandidate(candidate:any){
    this._messageService.sendMessage({
      formType : 'f1m-qualification', 
      action : 'editCandidate',
      candidate
    });
  }

  public trashCandidate(candidate:any){
    this._f1mService.trashCandidate(candidate, this.reportId).subscribe(res => {
      this._f1mService.getForm(this.reportId).subscribe(formData =>{
        this._messageService.sendMessage({action:'refreshScreen', qualificationData: formData});
        
      })
    });
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
