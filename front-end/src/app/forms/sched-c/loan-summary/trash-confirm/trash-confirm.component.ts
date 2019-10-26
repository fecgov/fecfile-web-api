import { Component, OnInit, Input, ViewChild } from '@angular/core';
import { ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { LoanModel } from '../../model/loan.model';

@Component({
  selector: 'app-trash-confirm',
  templateUrl: './trash-confirm.component.html',
  styleUrls: ['./trash-confirm.component.scss']
})
export class TrashConfirmComponent implements OnInit {

  @Input()
  public modalTitle: string;

  @Input()
  public message: string;

  @Input()
  public isShowCancel = true;

  @Input()
  public headerClass: string;

  @ViewChild('modalParent')
  public modalParent: ConfirmModalComponent;

  public Loans: Array<LoanModel>;


  public constructor() { }

  public ngOnInit() {
    this.modalParent.modalTitle = this.modalTitle;
    this.modalParent.message = this.message;
    this.modalParent.isShowCancel = this.isShowCancel;
    this.modalParent.headerClass = this.headerClass;
  }

}