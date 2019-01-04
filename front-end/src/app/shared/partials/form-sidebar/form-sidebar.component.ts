import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'form-sidebar',
  templateUrl: './form-sidebar.component.html',
  styleUrls: ['./form-sidebar.component.scss']
})
export class FormSidebarComponent implements OnInit {

  @Input() sidebarLinks: any = [];

  constructor() { }

  ngOnInit(): void {
    console.log('form-sidebar: ');
    console.log('sidebarLinks: ', this.sidebarLinks);
  }

}
