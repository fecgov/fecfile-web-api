import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {NgbActiveModal, NgbModal, NgbModalConfig} from '@ng-bootstrap/ng-bootstrap';

export enum SaveDialogAction {
  saveNone = 'none',
  saveReportMemo = 'report-memo-save',
}

@Component({
  selector: 'app-input-modal',
  templateUrl: './input-modal.component.html',
  styleUrls: ['./input-modal.component.scss']
})
export class InputModalComponent implements OnInit {

  titleText = 'Add Memo';
  saveAction = SaveDialogAction.saveNone ;
  inputContent: string;
  constructor(
      config: NgbModalConfig,
      private modalService: NgbModal,
      private activeModal: NgbActiveModal
  ) {  }

  ngOnInit() {
  }

  closeModal() {
    const dismissalData = {
      saveAction : SaveDialogAction.saveNone,
      content : '',
    };
    this.activeModal.dismiss(dismissalData);
  }

  save() {
    const saveData = {
      saveAction : this.saveAction,
      content : this.inputContent,
    };
    this.activeModal.close(saveData);
  }

  public setContent(content: string) {
    this.inputContent = content ? content : '';
  }
  public setSaveAction(saveAction: SaveDialogAction) {
    this.saveAction = saveAction;
  }
  public setDialogTitle(title: string) {
    this.titleText = title ? title : '';
  }
}
