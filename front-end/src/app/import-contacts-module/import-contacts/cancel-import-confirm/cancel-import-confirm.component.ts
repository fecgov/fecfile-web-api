import { Component, OnInit } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-cancel-import-confirm',
  templateUrl: './cancel-import-confirm.component.html',
  styleUrls: ['./cancel-import-confirm.component.scss']
})
export class CancelImportConfirmComponent implements OnInit {
  constructor(public activeModal: NgbActiveModal) {}

  message =
    'If you leave this page the importing process will be cancelled and no data will be added. ' +
    'Click Cancel to cancel the import or Continue if you want the import process to finish.';

  ngOnInit() {}

  cancel() {
    this.activeModal.close('cancel');
  }

  continue() {
    this.activeModal.close('continue');
  }
}
