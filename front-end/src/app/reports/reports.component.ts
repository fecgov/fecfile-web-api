import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { IReport } from './report';
import { ReportService } from './reports.service';

import { SessionService } from '../shared/services/SessionService/session.service';
import { ApiService } from '../shared/services/APIService/api.service';
import { MessageService } from '../shared/services/MessageService/message.service';
import { HeaderComponent } from '../shared/partials/header/header.component';
import { SidebarComponent } from '../shared/partials/sidebar/sidebar.component';
import { FormsComponent } from '../forms/forms.component';

@Component({
  selector: 'app-reports',
  templateUrl: './reports.component.html',
  styleUrls: ['./reports.component.scss'],
  encapsulation: ViewEncapsulation.None,
  providers:[ReportService,MessageService]
})

export class ReportsComponent implements OnInit {
  reports: IReport[];
  public showSideBar: boolean = true;
  public showLegalDisclaimer: boolean = false;

  constructor(
    private _reportService:ReportService,
    private _sessionService: SessionService,
    private _apiService: ApiService,
    private _modalService: NgbModal
    /*rivate _messageService: MessageService*/
    ){}
  
  /*trackById(index:number, reports:IReport[]): string{
    return reports[[]].id;
  }*/
 
  public toggleSideNav(): void {
    if (this.showSideBar) {
      this.showSideBar = false;
    } else if (!this.showSideBar) {
      this.showSideBar = true;
    }
}
  ngOnInit() {
    console.log("accessing service call...");
    this._reportService.getReports()
      .subscribe(res => this.reports = <IReport[]> res);
    console.log(this.reports)
  }

  public open(): void{
    this.showLegalDisclaimer = !this.showLegalDisclaimer;
  }

}
