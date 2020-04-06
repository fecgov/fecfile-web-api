import { Component, OnInit, ViewChild, ViewEncapsulation, Input, HostListener } from '@angular/core';
import { NgbActiveModal, NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';

export enum ModalHeaderClassEnum {
  infoHeader = 'info-header',
  infoHeaderDark = 'info-header-dark',
  warningHeader = 'warning-header',
  successHeader = 'success-header',
  errorHeader = 'error-header'
}

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

  @Input()
  public modalTitle: string;

  @Input()
  public message: string;

  @Input()
  public isShowCancel = true;

  @Input()
  public isShowOK = true;
  
  @Input()
  public headerClass: string;

  @Input()
  public cancelTitle: string;

  public isShownewReport;
  public isShowReportExist;

  private defaultTitle = 'Warning';
  private defaultMessage = 'You have unsaved changes! If you leave, your changes will be lost.';
  private defaultHeaderClass = ModalHeaderClassEnum.warningHeader;
  
  @HostListener("document:keydown", ["$event"])
  handleKeyup(event: KeyboardEvent) {
      if (event.keyCode === 8) {
          event.preventDefault();
      }
  }

  constructor(
    private _modalService: NgbModal,
    public activeModal: NgbActiveModal
  ) { }

  ngOnInit(): void {
    if (!this.modalTitle) {
      this.modalTitle = this.defaultTitle;
    }
    if (!this.message) {
      this.message = this.defaultMessage;
    }
    if (!this.headerClass) {
      this.headerClass = this.defaultHeaderClass;
    }
    if (!this.cancelTitle) {
      this.cancelTitle = 'Cancel';
    }

  }

  /**
   * Determine the header class to apply to the modal header.
   */
  public determineHeaderClasses() {
    switch (this.headerClass) {
      case ModalHeaderClassEnum.successHeader:
        return {'success-header': true};
      case ModalHeaderClassEnum.infoHeader:
        return {'info-header': true};
      case ModalHeaderClassEnum.infoHeaderDark:
        return {'info-header-dark': true};  
      case ModalHeaderClassEnum.warningHeader:
        return {'warning-header': true};
      case ModalHeaderClassEnum.errorHeader:
        return {'error-header': true};
      default:
        return {'warning-header': true};
    }
  }
}
