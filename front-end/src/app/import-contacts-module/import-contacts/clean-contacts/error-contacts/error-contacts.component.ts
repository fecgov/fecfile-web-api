import { Component, OnInit, ViewEncapsulation, ChangeDetectionStrategy, OnDestroy, Output, EventEmitter, Input } from '@angular/core';
import { ImportContactsService } from '../../service/import-contacts.service';
import { PaginationInstance } from 'ngx-pagination';
import { NgbModal, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { UtilService } from 'src/app/shared/utils/util.service';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { ErrorContactModel } from '../../model/error-contact.model';

@Component({
  selector: 'app-error-contacts',
  templateUrl: './error-contacts.component.html',
  styleUrls: ['./error-contacts.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class ErrorContactsComponent implements OnInit {

  @Input()
  public errorContacts: Array<any>;

  constructor(public activeModal: NgbActiveModal) { }

  ngOnInit() {
  }

  public proceed() {
    // TODO emitback to parent
    this.activeModal.dismiss();
  }

}
