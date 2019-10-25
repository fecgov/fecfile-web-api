import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-sched-h1',
  templateUrl: './sched-h1.component.html',
  styleUrls: ['./sched-h1.component.scss']
})


export class SchedH1Component implements OnInit {

  constructor() { }

  ngOnInit() {
    localStorage.setItem('cmte_type_category', 'PAC')
    console.log(localStorage.getItem('cmte_type_category'));
  }

  isPac() {
    console.log(localStorage.getItem('cmte_type_category'));
    return localStorage.getItem('cmte_type_category') === 'PAC';
  }




}
