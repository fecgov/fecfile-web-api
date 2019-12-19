import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-sched-h5-tbd',
  templateUrl: './sched-h5.component.html',
  styleUrls: ['./sched-h5.component.scss']
})
export class SchedH5Component_TOBEDELETED implements OnInit {
  transferCategories = [
    { id: 1, name: 'Voter Registration' },
    { id: 2, name: 'Voter ID' },
    { id: 3, name: 'GOTV' },
    { id: 4, name: 'Generic Campaign Activity' },
  ];

  constructor() { }

  ngOnInit() {
  }

  public load_summary(){
    
  }
}
