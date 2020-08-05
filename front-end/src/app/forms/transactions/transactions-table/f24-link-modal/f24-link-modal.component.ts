import { Component, Input, OnInit } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ReportsService } from './../../../../reports/service/report.service';

@Component({
  selector: 'app-f24-link-modal',
  templateUrl: './f24-link-modal.component.html',
  styleUrls: ['./f24-link-modal.component.scss']
})
export class F24LinkModalComponent implements OnInit {

  @Input()
  public f24List;

  public selectedReportId;

  constructor(private _reportsService: ReportsService, 
    public activeModal: NgbActiveModal) {
   }

  ngOnInit() {
  }

  handleF24Select($event:any) {
    this.selectedReportId = $event.reportId;
  }

  closeModal() {
    this.activeModal.dismiss();
  }

  save() {
    this.activeModal.close(this.selectedReportId);
  }

}
