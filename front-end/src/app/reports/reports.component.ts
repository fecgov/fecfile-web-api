import { Component, OnInit } from '@angular/core';
import { IReport } from './report';
import { ReportService } from './reports.service';


@Component({
  selector: 'app-reports',
  templateUrl: './reports.component.html',
  styleUrls: ['./reports.component.scss'],
  providers:[ReportService]
})

export class ReportsComponent implements OnInit {
  reports: IReport[];
  
  constructor(private _reportService:ReportService){ 
  }
  
  /*trackById(index:number, reports:IReport[]): string{
    return reports[[]].id;
  }*/
 
  
  ngOnInit() {
    console.log("accessing service call...");
    this._reportService.getReports()
      .subscribe(res => this.reports = <IReport[]> res);
    console.log(this.reports)
  }
}
