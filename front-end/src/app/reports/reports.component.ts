import { Component, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { ApiService } from '../shared/services/APIService/api.service';
import { FormsService } from '../shared/services/FormsService/forms.service';
import { MessageService } from '../shared/services/MessageService/message.service';
import { SessionService } from '../shared/services/SessionService/session.service';
import { IReport } from './report';
import { ReportService } from './reports.service';
import { Subject } from 'rxjs';


@Component({
  selector: 'app-reports',
  templateUrl: './reports.component.html',
  styleUrls: ['./reports.component.scss'],
  encapsulation: ViewEncapsulation.None,
  providers:[ReportService,MessageService]
})

export class ReportsComponent implements OnInit , OnDestroy{

  reports: IReport[];
  public showSideBar: boolean = true;
  public showLegalDisclaimer: boolean = false;

  private onDestroy$ = new Subject();

  constructor(
    private _reportService:ReportService,
    private _sessionService: SessionService,
    private _apiService: ApiService,
    private _modalService: NgbModal,
    private _formService: FormsService
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

    if (localStorage.getItem('form3XReportInfo.showDashBoard')==="Y"){
      this._formService.removeFormDashBoard("3X");
    }

    this._reportService.getReports()
    .takeUntil(this.onDestroy$)
      .subscribe(res => this.reports = <IReport[]> res);
    console.log(this.reports)
  }

  public open(): void{
    this.showLegalDisclaimer = !this.showLegalDisclaimer;
  }

  ngOnDestroy(): void {
    this.onDestroy$.next(true);
  }

}
