import { Component, OnInit, ViewChild, ViewEncapsulation } from '@angular/core';
import { NgbActiveModal, NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';

/**
 * Using NG Boostrap this configuration makes 
 * it so this confirm modal component can be used 
 * across multiple components.
 */

@Component({
  selector: 'ngbd-modal-content',
  templateUrl: './confirm-modal.component.html',
  styleUrls: ['./confirm-modal.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class ConfirmModalComponent implements OnInit {

  constructor(
    private _modalService: NgbModal,
    public activeModal: NgbActiveModal
  ) { }

  ngOnInit(): void {
  }
}
