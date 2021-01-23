import { Component, OnInit } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-upload-complete-message',
  templateUrl: './upload-complete-message.component.html',
  styleUrls: ['./upload-complete-message.component.scss']
})
export class UploadCompleteMessageComponent implements OnInit {
  constructor(public activeModal: NgbActiveModal) {}

  ngOnInit() {}

  continue() {
    this.activeModal.close('continue');
  }
}
