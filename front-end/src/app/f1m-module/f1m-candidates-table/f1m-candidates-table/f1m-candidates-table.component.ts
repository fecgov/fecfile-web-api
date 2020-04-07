import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-f1m-candidates-table',
  templateUrl: './f1m-candidates-table.component.html',
  styleUrls: ['./f1m-candidates-table.component.scss']
})
export class F1mCandidatesTableComponent implements OnInit {

  @Input() candidatesData :any;
  
  constructor() { }

  ngOnInit() {
  }

}
