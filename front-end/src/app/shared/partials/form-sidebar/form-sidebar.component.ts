import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'form-sidebar',
  templateUrl: './form-sidebar.component.html',
  styleUrls: ['./form-sidebar.component.scss']
})
export class FormSidebarComponent implements OnInit {

  @Input() sidebarLinks: any = [];
  @Input() title: string = '';

  public itemSelected: string = '';

  constructor() { }

  ngOnInit(): void {
    console.log('form-sidebar: ');
  }

  public selectItem(item): void {
    this.itemSelected = item.getAttribute('value');
  }
}
