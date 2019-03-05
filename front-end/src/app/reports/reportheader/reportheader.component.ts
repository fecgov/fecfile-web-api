import { Component, OnInit } from '@angular/core';
import { ReportdetailsComponent } from '../reportdetails/reportdetails.component';

export enum ActiveView {
  transactions = "transactions",
  recycleBin = "recycleBin"
}

@Component({
  selector: 'app-reportheader',
  templateUrl: './reportheader.component.html',
  styleUrls: ['./reportheader.component.scss']
})

export class ReportheaderComponent implements OnInit {

public reportsView = ActiveView.transactions;
  constructor() { }

  ngOnInit() {
  }

}
